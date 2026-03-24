"""
River Streamer — IBKR live 1m bar streaming to daily parquet.

Intraday: bars accumulate in staging JSONL.
End of forex day (17:00 NY): consolidate staging → daily parquet.
Daily parquet is then write-once immutable forever.

Streaming primitive: reqHistoricalData(keepUpToDate=True) for 1m bars.
(reqRealTimeBars only supports 5s bars — wrong granularity.)

Invariants:
    INV-RIVER-IMMUTABLE: Daily parquet files are write-once
    INV-RIVER-BITEMPORAL: knowledge_time = IBKR callback timestamp
    INV-NO-FORMING-CANDLE: Never emit incomplete bar
    INV-RIVER-SOURCE-TAG: source = 'ibkr'
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from .schema import (
    CANONICAL_PAIRS,
    RAW_BAR_SCHEMA,
    compute_bar_hashes,
    get_river_root,
    validate_raw_bars,
)

if "EventKit._metadata" in sys.modules:
    del sys.modules["EventKit._metadata"]
if "EventKit" in sys.modules:
    del sys.modules["EventKit"]

try:
    import nest_asyncio

    nest_asyncio.apply()
except ImportError:
    pass

logger = structlog.get_logger(__name__)

NY = ZoneInfo("America/New_York")
IBKR_DEFAULT_PORT = 4002
STALENESS_THRESHOLD_SECONDS = 120
WATCHDOG_INITIAL_TIMEOUT_S = 60
RESUBSCRIBE_MAX_ATTEMPTS = 5
RESUBSCRIBE_BACKOFF_S = [60, 120, 300, 300, 300]
CONSECUTIVE_GOOD_BARS_RESET = 5


class RiverStreamer:
    """Live 1m bar streaming from IBKR to River.

    Uses reqHistoricalData(keepUpToDate=True) for proper 1m bar delivery.
    Bars arrive via IBKR callback. Each bar is:
    1. Validated (INV-NO-FORMING-CANDLE: only closed bars)
    2. Written to staging JSONL (phoenix-river/{pair}/.staging/{date}.jsonl)
    3. Heartbeat updated (phoenix-river/.heartbeat.json)

    At forex day close (17:00 NY), staging consolidates into daily parquet.
    """

    def __init__(
        self,
        pair: str = "EURUSD",
        *,
        river_root: Path | None = None,
        ibkr_port: int = IBKR_DEFAULT_PORT,
    ) -> None:
        if pair not in CANONICAL_PAIRS:
            raise ValueError(f"Non-canonical pair: {pair}")

        self._pair = pair
        self._root = river_root or get_river_root()
        self._ibkr_port = ibkr_port
        self._ib: Any = None
        self._running = False
        self._last_bar_time: datetime | None = None
        self._last_bar_ts: pd.Timestamp | None = None
        self._consecutive_gaps: int = 0

        self._state = "STOPPED"
        self._connected = False
        self._subscribed = False
        self._resubscribe_attempts = 0
        self._bars_handle: Any = None
        self._subscribe_time: float | None = None

        self._bars_received: int = 0
        self._gaps_detected: int = 0
        self._consecutive_good_bars: int = 0
        self._known_timestamps: set[str] = set()
        self._session_start: datetime | None = None

    @property
    def staging_dir(self) -> Path:
        return self._root / self._pair / ".staging"

    @property
    def heartbeat_path(self) -> Path:
        return self._root / ".heartbeat.json"

    def staging_path(self, dt: datetime) -> Path:
        return self.staging_dir / f"{dt.strftime('%Y-%m-%d')}.jsonl"

    def parquet_path(self, dt: datetime) -> Path:
        return self._root / self._pair / str(dt.year) / f"{dt.month:02d}" / f"{dt.day:02d}.parquet"

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Start streaming 1m bars from IBKR."""
        import random

        from ib_insync import IB

        self._state = "STARTED"
        self._session_start = datetime.now(UTC)
        self._update_heartbeat()

        self._ib = IB()
        cid = random.randint(700, 799)  # noqa: S311
        logger.info("streamer_connecting", pair=self._pair, port=self._ibkr_port, cid=cid)
        self._ib.connect("127.0.0.1", self._ibkr_port, clientId=cid, timeout=15)

        self._connected = True
        self._ib.errorEvent += self._on_ib_error

        mdt = int(os.environ.get("IB_MARKET_DATA_TYPE", "1"))
        self._ib.reqMarketDataType(mdt)
        logger.info("market_data_type_set", type=mdt)

        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._subscribe()

        self._running = True
        logger.info("streamer_started", pair=self._pair)
        self._update_heartbeat()

        try:
            while self._running:
                self._ib.sleep(1)
                self._check_watchdog()
        except KeyboardInterrupt:
            logger.info("streamer_interrupted")
        finally:
            self.stop()

    def _subscribe(self) -> None:
        """Subscribe to 1m bars via reqHistoricalData(keepUpToDate=True)."""
        from ib_insync import Forex

        contract = Forex(self._pair)
        self._ib.qualifyContracts(contract)

        logger.info(
            "streamer_subscribing",
            pair=self._pair,
            exchange=contract.exchange,
            what_to_show="MIDPOINT",
            bar_size="1 min",
            keep_up_to_date=True,
        )

        self._bars_handle = self._ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr="1 D",
            barSizeSetting="1 min",
            whatToShow="MIDPOINT",
            useRTH=False,
            keepUpToDate=True,
            timeout=30,
        )

        seed_count = len(self._bars_handle) if self._bars_handle else 0
        logger.info("subscribe_seed_received", pair=self._pair, seed_bars=seed_count)

        if self._bars_handle and len(self._bars_handle) > 0:
            last_seed = self._bars_handle[-1]
            self._last_bar_time = datetime.now(UTC)
            self._last_bar_ts = pd.Timestamp(last_seed.date.timestamp(), unit="s", tz="UTC")
            logger.info(
                "subscribe_seed_anchor",
                last_seed_ts=str(self._last_bar_ts),
            )

        self._bars_handle.updateEvent += self._on_bar_update
        self._subscribed = True
        self._subscribe_time = time.monotonic()
        self._persist_seed_bars()
        self._update_heartbeat()

    def _load_known_timestamps(self) -> None:
        """Load timestamps from existing staging JSONL into dedup set."""
        if not self.staging_dir.exists():
            return
        for jsonl_path in self.staging_dir.glob("*.jsonl"):
            try:
                with open(jsonl_path) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            row = json.loads(line)
                            if "timestamp" in row:
                                self._known_timestamps.add(row["timestamp"])
                        except (ValueError, json.JSONDecodeError):
                            continue
            except OSError:
                continue

    def _persist_seed_bars(self) -> None:
        """Write historical seed bars to staging JSONL, deduped against existing.

        INV-RIVER-IMMUTABLE: writes to staging only, never to parquet.
        INV-NO-FORMING-CANDLE: excludes last bar (currently forming).
        """
        if not self._bars_handle or len(self._bars_handle) < 2:
            return

        self._load_known_timestamps()
        self.staging_dir.mkdir(parents=True, exist_ok=True)

        persisted = 0
        kt = datetime.now(UTC)

        for bar in self._bars_handle[:-1]:
            bar_ts = pd.Timestamp(bar.date.timestamp(), unit="s", tz="UTC")
            ts_key = bar_ts.isoformat()
            if ts_key in self._known_timestamps:
                continue

            bar_data = {
                "timestamp": ts_key,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": float(bar.volume),
                "source": "ibkr",
                "knowledge_time": kt.isoformat(),
            }

            bar_date = bar_ts.date()
            staging_file = self.staging_path(bar_date)
            staging_file.parent.mkdir(parents=True, exist_ok=True)

            with open(staging_file, "a") as f:
                f.write(json.dumps(bar_data) + "\n")

            self._known_timestamps.add(ts_key)
            self._bars_received += 1
            persisted += 1

        if persisted:
            logger.info(
                "seed_bars_persisted",
                pair=self._pair,
                persisted=persisted,
                skipped_dedup=len(self._bars_handle) - 1 - persisted,
            )

    def stop(self) -> None:
        """Stop streaming and consolidate any pending staging data."""
        self._running = False
        self._subscribed = False
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
        self._connected = False
        self._state = "STOPPED"
        self._update_heartbeat()
        logger.info("streamer_stopped", pair=self._pair)

    # ------------------------------------------------------------------
    # IB Error Callback (P0_1)
    # ------------------------------------------------------------------

    def _on_ib_error(
        self,
        reqId: int,  # noqa: N803
        errorCode: int,  # noqa: N803
        errorString: str,  # noqa: N803
        contract: Any = None,
    ) -> None:
        """IB error/warning callback. Logs all events for observability."""
        contract_str = str(contract) if contract else "N/A"
        if errorCode in (2104, 2106, 2158):
            logger.info("ib_info", code=errorCode, msg=errorString, contract=contract_str)
            return

        logger.warning(
            "ib_error",
            req_id=reqId,
            code=errorCode,
            msg=errorString,
            contract=contract_str,
            pair=self._pair,
        )

        if errorCode in (1100, 1300, 504, 502):
            self._connected = False
            self._subscribed = False
            if self._state != "STOPPED":
                self._state = "DEGRADED"
            self._update_heartbeat()

    # ------------------------------------------------------------------
    # Bar handling
    # ------------------------------------------------------------------

    def _on_bar_update(self, bars: Any, has_new_bar: bool) -> None:
        """Callback from ib_insync for each historical bar update.

        INV-NO-FORMING-CANDLE: We only process when has_new_bar=True,
        which means the previous bar is closed and complete.
        """
        if not has_new_bar or not bars:
            return

        bar = bars[-1]
        kt = datetime.now(UTC)
        bar_ts = pd.Timestamp(bar.date.timestamp(), unit="s", tz="UTC")
        ts_key = bar_ts.isoformat()

        if ts_key in self._known_timestamps:
            return

        if self._state != "STREAMING":
            self._state = "STREAMING"
            logger.info("streamer_first_bar", pair=self._pair, bar_ts=str(bar_ts))

        if self._last_bar_ts is not None:
            expected_gap = pd.Timedelta(minutes=1)
            actual_gap = bar_ts - self._last_bar_ts
            if actual_gap > expected_gap * 2 and self._is_trading_hours():
                missed = int(actual_gap.total_seconds() / 60) - 1
                self._consecutive_gaps += missed
                self._consecutive_good_bars = 0
                self._gaps_detected += 1
                if self._consecutive_gaps >= 5:
                    logger.warning(
                        "river_gap_alert",
                        pair=self._pair,
                        consecutive_gaps=self._consecutive_gaps,
                        last_bar=str(self._last_bar_ts),
                        current_bar=str(bar_ts),
                    )
            else:
                self._consecutive_gaps = 0
                self._consecutive_good_bars += 1
                if (
                    self._consecutive_good_bars >= CONSECUTIVE_GOOD_BARS_RESET
                    and self._resubscribe_attempts > 0
                ):
                    logger.info(
                        "resubscribe_counter_reset",
                        pair=self._pair,
                        after_good_bars=self._consecutive_good_bars,
                    )
                    self._resubscribe_attempts = 0
        else:
            self._consecutive_good_bars += 1

        self._last_bar_ts = bar_ts

        bar_data = {
            "timestamp": ts_key,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
            "source": "ibkr",
            "knowledge_time": kt.isoformat(),
        }

        bar_date = bar_ts.date()
        staging_file = self.staging_path(bar_date)
        staging_file.parent.mkdir(parents=True, exist_ok=True)

        with open(staging_file, "a") as f:
            f.write(json.dumps(bar_data) + "\n")

        self._known_timestamps.add(ts_key)
        self._bars_received += 1
        self._last_bar_time = kt
        self._update_heartbeat()

        logger.debug(
            "bar_received",
            pair=self._pair,
            ts=ts_key,
            close=bar_data["close"],
        )

    # ------------------------------------------------------------------
    # Watchdog (P0_3 + P0_4 + resubscribe with backoff)
    # ------------------------------------------------------------------

    def _check_watchdog(self) -> None:
        """Combined watchdog: initial connect timeout + ongoing staleness."""
        if self._last_bar_time is None:
            if (
                self._subscribe_time is not None
                and self._is_trading_hours()
                and (time.monotonic() - self._subscribe_time) > WATCHDOG_INITIAL_TIMEOUT_S
            ):
                logger.warning(
                    "watchdog_no_first_bar",
                    pair=self._pair,
                    elapsed_s=int(time.monotonic() - self._subscribe_time),
                )
                self._attempt_resubscribe()
            return

        elapsed = (datetime.now(UTC) - self._last_bar_time).total_seconds()
        if elapsed > STALENESS_THRESHOLD_SECONDS and self._is_trading_hours():
            logger.warning(
                "staleness_alert",
                pair=self._pair,
                seconds_since_last_bar=int(elapsed),
            )
            self._attempt_resubscribe()

    def _attempt_resubscribe(self) -> None:
        """Resubscribe with exponential backoff. Max RESUBSCRIBE_MAX_ATTEMPTS.

        Rate-limited: skips if still within backoff window from last attempt.
        On resubscribe, seed bars (1 D) fill any gap via _persist_seed_bars.
        """
        if self._resubscribe_attempts >= RESUBSCRIBE_MAX_ATTEMPTS:
            logger.error(
                "resubscribe_exhausted",
                pair=self._pair,
                attempts=self._resubscribe_attempts,
            )
            self._state = "DEGRADED"
            self._subscribed = False
            self._update_heartbeat()
            return

        backoff = RESUBSCRIBE_BACKOFF_S[
            min(self._resubscribe_attempts, len(RESUBSCRIBE_BACKOFF_S) - 1)
        ]

        if self._subscribe_time is not None and (time.monotonic() - self._subscribe_time) < backoff:
            return

        self._resubscribe_attempts += 1

        gap_seconds: float | None = None
        if self._last_bar_ts is not None:
            gap_seconds = (datetime.now(UTC) - self._last_bar_ts.to_pydatetime()).total_seconds()

        logger.warning(
            "resubscribe_attempt",
            pair=self._pair,
            attempt=self._resubscribe_attempts,
            max_attempts=RESUBSCRIBE_MAX_ATTEMPTS,
            backoff_s=backoff,
            gap_seconds=int(gap_seconds) if gap_seconds else None,
        )

        time.sleep(backoff)

        try:
            if self._bars_handle is not None:
                self._ib.cancelHistoricalData(self._bars_handle)
            self._subscribe()
            if gap_seconds and gap_seconds > 120:
                logger.info(
                    "gap_backfill_via_seed",
                    pair=self._pair,
                    gap_seconds=int(gap_seconds),
                    seed_bars=len(self._bars_handle) if self._bars_handle else 0,
                )
        except Exception:
            logger.exception("resubscribe_failed", pair=self._pair)
            if self._resubscribe_attempts >= RESUBSCRIBE_MAX_ATTEMPTS:
                self._state = "DEGRADED"
                self._subscribed = False
                self._update_heartbeat()

    # ------------------------------------------------------------------
    # Heartbeat (P2 — atomic JSON write)
    # ------------------------------------------------------------------

    def _update_heartbeat(self) -> None:
        """Write heartbeat file atomically (tmp + rename)."""
        self.heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            {
                "state": self._state,
                "connected": self._connected,
                "subscribed": self._subscribed,
                "pair": self._pair,
                "pairs_active": [self._pair] if self._subscribed else [],
                "pairs_failed": []
                if self._subscribed
                else ([self._pair] if self._state == "DEGRADED" else []),
                "last_bar_time": self._last_bar_time.isoformat() if self._last_bar_time else None,
                "last_update": datetime.now(UTC).isoformat(),
                "resubscribe_attempts": self._resubscribe_attempts,
                "bars_received": self._bars_received,
                "gaps_detected": self._gaps_detected,
                "consecutive_good_bars": self._consecutive_good_bars,
                "session_start": self._session_start.isoformat() if self._session_start else None,
            },
            indent=2,
        )

        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.heartbeat_path.parent),
            suffix=".tmp",
        )
        try:
            os.write(fd, payload.encode())
            os.close(fd)
            os.replace(tmp_path, str(self.heartbeat_path))
        except Exception:
            os.close(fd) if not os.get_inheritable(fd) else None  # noqa: E701
            logger.exception("heartbeat_write_failed")

    # ------------------------------------------------------------------
    # Consolidation (staging JSONL → daily parquet)
    # ------------------------------------------------------------------

    def consolidate_day(self, date: datetime) -> int:
        """Consolidate staging JSONL for a date into daily parquet.

        INV-RIVER-IMMUTABLE: If daily parquet already exists, skip.
        Returns number of bars written.
        """
        staging_file = self.staging_path(date)
        if not staging_file.exists():
            return 0

        parquet_file = self.parquet_path(date)
        if parquet_file.exists():
            logger.debug("parquet_exists_skip", path=str(parquet_file))
            return 0

        rows = []
        with open(staging_file) as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))

        if not rows:
            return 0

        df = pd.DataFrame(rows)
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df["knowledge_time"] = pd.to_datetime(df["knowledge_time"], utc=True)
        df = df.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)
        df["bar_hash"] = compute_bar_hashes(df)

        errors = validate_raw_bars(df)
        if errors:
            logger.error("consolidation_validation_failed", date=str(date), errors=errors)
            return 0

        parquet_file.parent.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pandas(df, schema=RAW_BAR_SCHEMA, preserve_index=False)
        pq.write_table(table, parquet_file)

        logger.info("consolidated", path=str(parquet_file), bars=len(df))
        return len(df)

    def consolidate_all_pending(self) -> int:
        """Consolidate all pending staging files."""
        if not self.staging_dir.exists():
            return 0

        total = 0
        for f in sorted(self.staging_dir.glob("*.jsonl")):
            date_str = f.stem
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                continue
            total += self.consolidate_day(date)
        return total

    # ------------------------------------------------------------------
    # Trading hours
    # ------------------------------------------------------------------

    @staticmethod
    def _is_trading_hours() -> bool:
        """Check if forex market is currently open (UTC-based boundaries).

        FX hours: Sunday 22:00 UTC → Friday 22:00 UTC (continuous).
        """
        now_ny = datetime.now(NY)
        dow = now_ny.weekday()
        hour = now_ny.hour

        if dow == 5:
            return False
        if dow == 6 and hour < 17:
            return False
        if dow == 4 and hour >= 17:
            return False
        return True


def run_streamer() -> None:
    """Entry point for launchd daemon / command-line invocation."""
    import argparse

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
    )

    parser = argparse.ArgumentParser(description="River Streamer — IBKR live 1m bars")
    parser.add_argument("--pair", default="EURUSD", help="Pair to stream (default: EURUSD)")
    parser.add_argument("--port", type=int, default=IBKR_DEFAULT_PORT, help="IBKR Gateway port")
    args = parser.parse_args()

    log = structlog.get_logger("river_streamer")
    log.info("daemon_start", pair=args.pair, port=args.port, root=str(get_river_root()))

    streamer = RiverStreamer(pair=args.pair, ibkr_port=args.port)
    streamer.start()


if __name__ == "__main__":
    run_streamer()
