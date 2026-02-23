"""
River Writer — IBKR historical data → daily parquet files.

T0 capture: fetch all available 1m bars from IBKR for all 6 canonical pairs.
Evolves into T2 hardened writer.

Reference material: ~/nex/nex_lab/data/vendors/ibkr.py

Invariants:
    INV-RIVER-IMMUTABLE: Daily parquet files are write-once, never modified
    INV-RIVER-BITEMPORAL: Every bar carries knowledge_time
    INV-RIVER-SOURCE-TAG: source = 'ibkr' on all bars from this writer
"""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from ib_insync import IB

# EventKit namespace conflict on macOS — must precede ib_insync import
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

IBKR_PACING_SECONDS: int = 11
IBKR_DEFAULT_PORT: int = 4002


class RiverWriter:
    """Fetches 1m bars from IBKR and writes daily parquet files.

    Data path: RIVER_ROOT/{pair}/{year}/{mm}/{dd}.parquet
    Set RIVER_ROOT env var to override default (~/phoenix-river).
    Each daily file is write-once: if it already exists, it is skipped.

    Volume semantics (ICT_DATA_CONTRACT §7.2):
        IBKR MIDPOINT returns volume=-1 (no tick data for forex midpoint).
        This is preserved as-is — distinct from ghost bar volume=0.
    """

    def __init__(
        self,
        river_root: Path | None = None,
        ibkr_port: int = IBKR_DEFAULT_PORT,
    ) -> None:
        self._river_root = river_root or get_river_root()
        self._ibkr_port = ibkr_port
        self._last_request_time: float | None = None
        self._ib: IB | None = None

    def parquet_path(self, pair: str, dt: datetime) -> Path:
        return self._river_root / pair / str(dt.year) / f"{dt.month:02d}" / f"{dt.day:02d}.parquet"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def capture_all(self, lookback_days: int = 35) -> dict[str, int]:
        """Capture all 6 canonical pairs. Returns {pair: bars_written}."""
        results: dict[str, int] = {}
        self._connect()
        try:
            for pair in sorted(CANONICAL_PAIRS):
                self._apply_pacing()
                try:
                    results[pair] = self._capture_pair(pair, lookback_days)
                except Exception:
                    logger.exception("pair_capture_failed", pair=pair)
                    results[pair] = 0
                    self._reconnect()
        finally:
            self._disconnect()

        total = sum(results.values())
        logger.info("capture_all_complete", results=results, total_bars=total)
        return results

    # ------------------------------------------------------------------
    # Per-pair capture
    # ------------------------------------------------------------------

    def _capture_pair(self, pair: str, lookback_days: int) -> int:
        if pair not in CANONICAL_PAIRS:
            raise ValueError(f"Non-canonical pair: {pair}")

        end = datetime.now(UTC)
        start = end - timedelta(days=lookback_days)
        logger.info("pair_start", pair=pair, start=start.date(), end=end.date())

        df = self._fetch_bars(pair, start, end)
        if df is None or df.empty:
            logger.warning("no_bars", pair=pair)
            return 0

        df["source"] = "ibkr"
        df["knowledge_time"] = pd.Timestamp.now(tz="UTC")
        df["bar_hash"] = compute_bar_hashes(df)

        errors = validate_raw_bars(df)
        if errors:
            logger.error("validation_failed", pair=pair, errors=errors)
            raise ValueError(f"Validation failed for {pair}: {errors}")

        written = self._write_daily_partitions(pair, df)
        logger.info(
            "pair_complete",
            pair=pair,
            fetched=len(df),
            written=written,
            first=str(df["timestamp"].min()),
            last=str(df["timestamp"].max()),
        )
        return written

    # ------------------------------------------------------------------
    # IBKR data fetching
    # ------------------------------------------------------------------

    def _fetch_bars(
        self,
        pair: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame | None:
        """Fetch 1m bars in 2-day chunks (safe for IBKR 1m pacing)."""
        chunk_size = timedelta(days=2)
        chunks: list[pd.DataFrame] = []
        cur = end

        while cur > start:
            chunk_start = max(start, cur - chunk_size)
            duration = self._duration_str(chunk_start, cur)
            chunk = self._ibkr_request(pair, cur, duration)
            if chunk is not None and not chunk.empty:
                chunks.append(chunk)
                logger.info(
                    "chunk_ok",
                    pair=pair,
                    bars=len(chunk),
                    first=str(chunk["timestamp"].min()),
                    last=str(chunk["timestamp"].max()),
                )
            else:
                logger.debug("chunk_empty", pair=pair, end=str(cur))
            cur = chunk_start

        if not chunks:
            return None

        combined = pd.concat(chunks, ignore_index=True)
        start_ts = pd.Timestamp(start.replace(tzinfo=None), tz="UTC")
        combined = combined[combined["timestamp"] >= start_ts]
        return combined.sort_values("timestamp").drop_duplicates("timestamp").reset_index(drop=True)

    def _ibkr_request(
        self,
        pair: str,
        end_dt: datetime,
        duration: str,
    ) -> pd.DataFrame | None:
        from ib_insync import Forex

        if self._ib is None or not self._ib.isConnected():
            self._connect()
        assert self._ib is not None

        contract = Forex(pair)
        self._ib.qualifyContracts(contract)

        self._apply_pacing()
        try:
            bars = self._ib.reqHistoricalData(
                contract,
                endDateTime=end_dt,
                durationStr=duration,
                barSizeSetting="1 min",
                whatToShow="MIDPOINT",
                useRTH=False,
                formatDate=1,
                timeout=30,
            )
        except Exception:
            logger.exception("ibkr_request_error", pair=pair, duration=duration)
            return None

        if not bars:
            return None

        return pd.DataFrame(
            [
                {
                    "timestamp": pd.to_datetime(bar.date, utc=True),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    # IBKR MIDPOINT forex returns volume=-1 (no tick data).
                    # Preserve as-is: -1 means "IBKR no-data", 0 is reserved for ghost bars.
                    "volume": float(bar.volume),
                }
                for bar in bars
            ]
        )

    # ------------------------------------------------------------------
    # Parquet writing
    # ------------------------------------------------------------------

    def _write_daily_partitions(self, pair: str, df: pd.DataFrame) -> int:
        df = df.copy()
        df["_date"] = df["timestamp"].dt.date
        written = 0

        for date_val, group in df.groupby("_date"):
            path = self.parquet_path(pair, date_val)
            if path.exists():
                existing = pq.read_table(path).num_rows
                logger.debug("skip_existing", path=str(path), rows=existing)
                continue

            path.parent.mkdir(parents=True, exist_ok=True)
            out = group.drop(columns=["_date"]).sort_values("timestamp").reset_index(drop=True)
            table = pa.Table.from_pandas(out, schema=RAW_BAR_SCHEMA, preserve_index=False)
            pq.write_table(table, path)
            written += len(out)
            logger.info("written", path=str(path), bars=len(out))

        return written

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def _connect(self) -> None:
        import random

        from ib_insync import IB

        self._ib = IB()
        cid = random.randint(800, 899)  # noqa: S311
        logger.info("ibkr_connecting", port=self._ibkr_port, client_id=cid)
        self._ib.connect("127.0.0.1", self._ibkr_port, clientId=cid, timeout=15)
        if not self._ib.isConnected():
            raise ConnectionError("IBKR Gateway not reachable")
        logger.info("ibkr_connected")

    def _disconnect(self) -> None:
        if self._ib and self._ib.isConnected():
            self._ib.disconnect()
            logger.info("ibkr_disconnected")

    def _reconnect(self) -> None:
        self._disconnect()
        time.sleep(2)
        try:
            self._connect()
        except Exception:
            logger.exception("reconnect_failed")

    def _apply_pacing(self) -> None:
        if self._last_request_time is not None:
            elapsed = time.time() - self._last_request_time
            if elapsed < IBKR_PACING_SECONDS:
                wait = IBKR_PACING_SECONDS - elapsed
                logger.debug("pacing", wait=round(wait, 1))
                time.sleep(wait)
        self._last_request_time = time.time()

    @staticmethod
    def _duration_str(start: datetime, end: datetime) -> str:
        days = (end - start).days
        if days <= 1:
            return "1 D"
        if days <= 7:
            return f"{days} D"
        weeks = (days // 7) + 1
        return f"{weeks} W"


# ======================================================================
# T0 Capture Entry Point
# ======================================================================


def run_t0_capture() -> None:
    """T0: Capture all 6 canonical pairs from IBKR. Time-critical."""
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
    )
    log = structlog.get_logger("t0_capture")

    log.info("t0_capture_start", pairs=sorted(CANONICAL_PAIRS))
    writer = RiverWriter()
    results = writer.capture_all(lookback_days=35)

    log.info("t0_capture_summary")
    for pair, count in sorted(results.items()):
        status = "OK" if count > 0 else "EMPTY"
        log.info("pair_result", pair=pair, bars=count, status=status)

    total = sum(results.values())
    log.info("t0_done", total_bars=total, river_root=str(get_river_root()))


if __name__ == "__main__":
    run_t0_capture()
