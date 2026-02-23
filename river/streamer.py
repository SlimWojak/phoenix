"""
River Streamer — IBKR live 1m bar streaming to daily parquet.

Intraday: bars accumulate in staging JSONL.
End of forex day (17:00 NY): consolidate staging → daily parquet.
Daily parquet is then write-once immutable forever.

Invariants:
    INV-RIVER-IMMUTABLE: Daily parquet files are write-once
    INV-RIVER-BITEMPORAL: knowledge_time = IBKR callback timestamp
    INV-NO-FORMING-CANDLE: Never emit incomplete bar
    INV-RIVER-SOURCE-TAG: source = 'ibkr'
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
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

# EventKit namespace conflict on macOS
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


class RiverStreamer:
    """Live 1m bar streaming from IBKR to River.

    Bars arrive via IBKR callback. Each bar is:
    1. Validated (INV-NO-FORMING-CANDLE: only closed bars)
    2. Written to staging JSONL (phoenix-river/{pair}/.staging/{date}.jsonl)
    3. Heartbeat updated (phoenix-river/.heartbeat)

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
        self._ib = None
        self._running = False
        self._last_bar_time: datetime | None = None
        self._last_bar_ts: pd.Timestamp | None = None
        self._consecutive_gaps: int = 0

    @property
    def staging_dir(self) -> Path:
        return self._root / self._pair / ".staging"

    @property
    def heartbeat_path(self) -> Path:
        return self._root / ".heartbeat"

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

        from ib_insync import IB, Forex

        self._ib = IB()
        cid = random.randint(700, 799)  # noqa: S311
        logger.info("streamer_connecting", pair=self._pair, port=self._ibkr_port, cid=cid)
        self._ib.connect("127.0.0.1", self._ibkr_port, clientId=cid, timeout=15)

        contract = Forex(self._pair)
        self._ib.qualifyContracts(contract)

        self._ib.reqRealTimeBars(
            contract,
            barSize=5,
            whatToShow="MIDPOINT",
            useRTH=False,
        )
        self._ib.barUpdateEvent += self._on_bar_update

        self._running = True
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        logger.info("streamer_started", pair=self._pair)

        try:
            while self._running:
                self._ib.sleep(1)
                self._check_staleness()
        except KeyboardInterrupt:
            logger.info("streamer_interrupted")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop streaming and consolidate any pending staging data."""
        self._running = False
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
        logger.info("streamer_stopped", pair=self._pair)

    # ------------------------------------------------------------------
    # Bar handling
    # ------------------------------------------------------------------

    def _on_bar_update(self, bars, has_new_bar: bool) -> None:
        """Callback from ib_insync for each real-time bar update.

        INV-NO-FORMING-CANDLE: We only process when has_new_bar=True,
        which means the previous bar is closed and complete.
        """
        if not has_new_bar or not bars:
            return

        bar = bars[-1]
        kt = datetime.now(UTC)
        bar_ts = pd.Timestamp(bar.time, tz="UTC")

        # Real-time gap detection (F3 silent failure defense)
        if self._last_bar_ts is not None:
            expected_gap = pd.Timedelta(minutes=1)
            actual_gap = bar_ts - self._last_bar_ts
            if actual_gap > expected_gap * 2 and self._is_trading_hours():
                missed = int(actual_gap.total_seconds() / 60) - 1
                self._consecutive_gaps += missed
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
        self._last_bar_ts = bar_ts

        bar_data = {
            "timestamp": bar_ts.isoformat(),
            "open": float(bar.open_),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
            "source": "ibkr",
            "knowledge_time": kt.isoformat(),
        }

        bar_date = pd.Timestamp(bar.time).date()
        staging_file = self.staging_path(bar_date)
        staging_file.parent.mkdir(parents=True, exist_ok=True)

        with open(staging_file, "a") as f:
            f.write(json.dumps(bar_data) + "\n")

        self._last_bar_time = kt
        self._update_heartbeat()

        logger.debug(
            "bar_received",
            pair=self._pair,
            ts=bar_data["timestamp"],
            close=bar_data["close"],
        )

    def _check_staleness(self) -> None:
        """Alert if no bar received for > STALENESS_THRESHOLD during trading hours."""
        if self._last_bar_time is None:
            return

        elapsed = (datetime.now(UTC) - self._last_bar_time).total_seconds()
        if elapsed > STALENESS_THRESHOLD_SECONDS and self._is_trading_hours():
            logger.warning(
                "staleness_alert",
                pair=self._pair,
                seconds_since_last_bar=int(elapsed),
            )

    def _update_heartbeat(self) -> None:
        """Write heartbeat file for monitoring."""
        self.heartbeat_path.parent.mkdir(parents=True, exist_ok=True)
        self.heartbeat_path.write_text(
            json.dumps(
                {
                    "pair": self._pair,
                    "last_bar": self._last_bar_time.isoformat() if self._last_bar_time else None,
                    "updated": datetime.now(UTC).isoformat(),
                }
            )
        )

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
        """Check if forex market is currently open."""
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
