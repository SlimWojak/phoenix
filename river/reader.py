"""
River Reader — DuckDB query layer over immutable parquet files.

Returns MATERIALIZED_BAR_SCHEMA (10 columns: RAW + is_ghost).
Ghost bars are injected at query time for missing 1m slots during trading hours.

Invariants:
    INV-RIVER-CONTINUOUS: No gaps in materialized 1m series (ghosts flagged)
    INV-NO-FORMING-CANDLE: Never return incomplete current bar
    INV-RIVER-IBKR-PRIMACY: Execution venue data is authoritative for live
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import duckdb
import pandas as pd
import structlog

from .schema import CANONICAL_PAIRS, compute_bar_hashes, get_river_root

logger = structlog.get_logger(__name__)

NY = ZoneInfo("America/New_York")

VALID_TIMEFRAMES = {"1m", "5m", "15m", "1H", "4H", "1D"}
TF_MINUTES = {"1m": 1, "5m": 5, "15m": 15, "1H": 60, "4H": 240, "1D": 1440}


class RiverReader:
    """Read-only query layer over River parquet files.

    All reads go through DuckDB — zero server infrastructure.
    Ghost bars are injected into materialized views (is_ghost=True, volume=0).
    Higher timeframes derived from 1m via SQL aggregation.

    Volume semantics (ICT_DATA_CONTRACT §7.2):
        volume > 0  → real tick count (Dukascopy)
        volume = -1 → IBKR MIDPOINT (no tick data)
        volume = 0  → ghost bar (synthetic continuity)
    """

    def __init__(self, river_root: Path | None = None) -> None:
        self._root = river_root or get_river_root()

    def get_bars(
        self,
        pair: str,
        timeframe: str = "1m",
        start: datetime | pd.Timestamp | None = None,
        end: datetime | pd.Timestamp | None = None,
        *,
        inject_ghosts: bool = True,
    ) -> pd.DataFrame:
        """Return bars for a pair/timeframe range.

        Returns MATERIALIZED_BAR_SCHEMA (10 columns) with is_ghost added.
        INV-NO-FORMING-CANDLE: current incomplete bar is always excluded.
        """
        if pair not in CANONICAL_PAIRS:
            raise ValueError(f"Non-canonical pair: {pair}")
        if timeframe not in VALID_TIMEFRAMES:
            raise ValueError(f"Invalid timeframe: {timeframe}. Valid: {VALID_TIMEFRAMES}")

        raw = self._read_parquet(pair, start, end)
        if raw.empty:
            return self._empty_materialized()

        # INV-NO-FORMING-CANDLE: exclude current incomplete bar
        now = pd.Timestamp.now(tz="UTC").floor("min")
        raw = raw[raw["timestamp"] < now]
        if raw.empty:
            return self._empty_materialized()

        self._verify_hash_sample(raw)

        if timeframe == "1m":
            if inject_ghosts:
                return self._inject_ghosts(raw)
            raw["is_ghost"] = False
            return raw

        return self._aggregate(raw, timeframe, inject_ghosts)

    def get_gaps(
        self,
        pair: str,
        start: datetime | pd.Timestamp | None = None,
        end: datetime | pd.Timestamp | None = None,
    ) -> pd.DataFrame:
        """Return missing 1m bar timestamps during trading hours.

        Returns DataFrame with columns: [timestamp, gap_duration_min].
        Weekend gaps are excluded.
        """
        raw = self._read_parquet(pair, start, end)
        if raw.empty:
            return pd.DataFrame(columns=["timestamp", "gap_duration_min"])

        expected = self._expected_timestamps(
            raw["timestamp"].min(),
            raw["timestamp"].max(),
        )
        actual = set(raw["timestamp"])
        missing = sorted(expected - actual)

        if not missing:
            return pd.DataFrame(columns=["timestamp", "gap_duration_min"])

        gaps = []
        run_start = missing[0]
        prev = missing[0]
        for ts in missing[1:]:
            if ts - prev > pd.Timedelta(minutes=1):
                duration = int((prev - run_start).total_seconds() / 60) + 1
                gaps.append({"timestamp": run_start, "gap_duration_min": duration})
                run_start = ts
            prev = ts
        duration = int((prev - run_start).total_seconds() / 60) + 1
        gaps.append({"timestamp": run_start, "gap_duration_min": duration})

        return pd.DataFrame(gaps)

    def bar_count(self, pair: str) -> int:
        """Total raw bar count for a pair."""
        glob = str(self._root / pair / "**" / "*.parquet")
        con = duckdb.connect()
        try:
            result = con.execute(f"SELECT count(*) FROM read_parquet('{glob}')").fetchone()
            return result[0] if result else 0
        finally:
            con.close()

    def date_range(self, pair: str) -> tuple[pd.Timestamp | None, pd.Timestamp | None]:
        """First and last bar timestamps for a pair."""
        glob = str(self._root / pair / "**" / "*.parquet")
        con = duckdb.connect()
        try:
            result = con.execute(
                f"SELECT min(timestamp), max(timestamp) FROM read_parquet('{glob}')"
            ).fetchone()
            if result and result[0] is not None:
                first = pd.Timestamp(result[0])
                last = pd.Timestamp(result[1])
                if first.tz is None:
                    first = first.tz_localize("UTC")
                if last.tz is None:
                    last = last.tz_localize("UTC")
                return first, last
            return None, None
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Parquet reading via DuckDB
    # ------------------------------------------------------------------

    def _read_parquet(
        self,
        pair: str,
        start: datetime | pd.Timestamp | None,
        end: datetime | pd.Timestamp | None,
    ) -> pd.DataFrame:
        pair_dir = self._root / pair
        if not pair_dir.exists():
            return pd.DataFrame()

        glob = str(pair_dir / "**" / "*.parquet")
        con = duckdb.connect()
        try:
            clauses = []
            params: list = []
            if start is not None:
                clauses.append("timestamp >= ?")
                ts = pd.Timestamp(start) if not isinstance(start, pd.Timestamp) else start
                params.append(ts.tz_localize("UTC") if ts.tzinfo is None else ts)
            if end is not None:
                clauses.append("timestamp < ?")
                ts = pd.Timestamp(end) if not isinstance(end, pd.Timestamp) else end
                params.append(ts.tz_localize("UTC") if ts.tzinfo is None else ts)

            where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
            query = f"SELECT * FROM read_parquet('{glob}'){where} ORDER BY timestamp"

            df = con.execute(query, params).fetchdf()
            if not df.empty:
                if df["timestamp"].dt.tz is None:
                    df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
                else:
                    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
                if "knowledge_time" in df.columns:
                    if df["knowledge_time"].dt.tz is None:
                        df["knowledge_time"] = df["knowledge_time"].dt.tz_localize("UTC")
                    else:
                        df["knowledge_time"] = df["knowledge_time"].dt.tz_convert("UTC")
            return df
        finally:
            con.close()

    # ------------------------------------------------------------------
    # Hash verification (probabilistic corruption detection)
    # ------------------------------------------------------------------

    def _verify_hash_sample(self, df: pd.DataFrame, sample_pct: float = 0.01) -> None:
        """Verify bar_hash on a random sample. Catches disk corruption.

        Raises RuntimeError if any hash mismatch detected.
        """
        if df.empty or "bar_hash" not in df.columns:
            return
        real = df[df.get("is_ghost", pd.Series(False, index=df.index)) == False]  # noqa: E712
        if real.empty:
            return

        sample = real.sample(frac=sample_pct, random_state=42)
        if sample.empty:
            sample = real.head(1)

        recomputed = compute_bar_hashes(sample)
        mismatches = (sample["bar_hash"] != recomputed) & (sample["bar_hash"] != "")
        if mismatches.any():
            bad = sample[mismatches]
            logger.error("hash_mismatch", count=len(bad), first=str(bad.iloc[0]["timestamp"]))
            raise RuntimeError(
                f"INV-RIVER-IMMUTABLE VIOLATION: {len(bad)} bar(s) have mismatched hashes. "
                f"First: {bad.iloc[0]['timestamp']}. Possible disk corruption."
            )

    # ------------------------------------------------------------------
    # Ghost bar injection (INV-RIVER-CONTINUOUS)
    # ------------------------------------------------------------------

    def _inject_ghosts(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return self._empty_materialized()

        expected = self._expected_timestamps(
            df["timestamp"].min(),
            df["timestamp"].max(),
        )
        actual = set(df["timestamp"])
        missing = expected - actual

        df = df.copy()
        df["is_ghost"] = False

        if not missing:
            return df

        ghost_rows = []
        last_close = df.iloc[0]["close"]

        ts_to_close = dict(zip(df["timestamp"], df["close"], strict=False))

        for ts in sorted(missing):
            # Carry forward: find the most recent real bar's close
            prev_ts = ts - pd.Timedelta(minutes=1)
            while prev_ts not in ts_to_close and prev_ts >= df["timestamp"].min():
                prev_ts -= pd.Timedelta(minutes=1)
            carry_close = ts_to_close.get(prev_ts, last_close)

            ghost_rows.append(
                {
                    "timestamp": ts,
                    "open": carry_close,
                    "high": carry_close,
                    "low": carry_close,
                    "close": carry_close,
                    "volume": 0.0,
                    "source": "ghost",
                    "knowledge_time": pd.Timestamp.now(tz="UTC"),
                    "bar_hash": "",
                    "is_ghost": True,
                }
            )
            ts_to_close[ts] = carry_close

        ghosts = pd.DataFrame(ghost_rows)
        result = pd.concat([df, ghosts], ignore_index=True)
        result = result.sort_values("timestamp").reset_index(drop=True)

        logger.debug("ghosts_injected", count=len(ghost_rows))
        return result

    # ------------------------------------------------------------------
    # Timeframe aggregation
    # ------------------------------------------------------------------

    def _aggregate(
        self,
        df: pd.DataFrame,
        timeframe: str,
        inject_ghosts: bool,
    ) -> pd.DataFrame:
        if inject_ghosts:
            df = self._inject_ghosts(df)
        else:
            df = df.copy()
            df["is_ghost"] = False

        minutes = TF_MINUTES[timeframe]

        # Floor timestamps to the target timeframe bucket
        df["bucket"] = df["timestamp"].dt.floor(f"{minutes}min")

        agg = (
            df.groupby("bucket")
            .agg(
                open=("open", "first"),
                high=("high", "max"),
                low=("low", "min"),
                close=("close", "last"),
                volume=("volume", "sum"),
                source=("source", "first"),
                knowledge_time=("knowledge_time", "max"),
                bar_hash=("bar_hash", "first"),
                is_ghost=("is_ghost", "all"),
            )
            .reset_index()
        )

        agg = agg.rename(columns={"bucket": "timestamp"})

        # A higher-TF bar is ghost only if ALL constituent 1m bars are ghosts
        # volume sum: ghost bars contribute 0, IBKR bars contribute -1 per bar
        return agg.sort_values("timestamp").reset_index(drop=True)

    # ------------------------------------------------------------------
    # Trading hour utilities
    # ------------------------------------------------------------------

    def _expected_timestamps(
        self,
        start: pd.Timestamp,
        end: pd.Timestamp,
    ) -> set[pd.Timestamp]:
        """Generate expected 1m timestamps for forex trading hours.

        Forex: Sunday ~22:00 UTC to Friday ~22:00 UTC (DST-dependent).
        This generates every minute in that window, excluding weekends.
        """
        s = start.tz_convert("UTC") if start.tz is not None else start.tz_localize("UTC")
        e = end.tz_convert("UTC") if end.tz is not None else end.tz_localize("UTC")
        all_minutes = pd.date_range(start=s, end=e, freq="1min", tz="UTC")

        # Convert to NY time for weekend detection
        ny_times = all_minutes.tz_convert(NY)
        mask = _is_trading_hour(ny_times)

        return set(all_minutes[mask])

    @staticmethod
    def _empty_materialized() -> pd.DataFrame:
        return pd.DataFrame(
            columns=[
                "timestamp",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "source",
                "knowledge_time",
                "bar_hash",
                "is_ghost",
            ]
        )


def _is_trading_hour(ny_times: pd.DatetimeIndex) -> pd.Series:
    """True if the timestamp falls within forex trading hours (NY perspective).

    Trading: Sunday 17:00 NY → Friday 17:00 NY.
    Closed: Friday 17:00 NY → Sunday 17:00 NY.
    """
    dow = ny_times.dayofweek  # Mon=0 ... Sun=6
    hour = ny_times.hour

    # Closed: Saturday (all day), Sunday before 17:00, Friday at/after 17:00
    is_saturday = dow == 5
    is_sunday_early = (dow == 6) & (hour < 17)
    is_friday_late = (dow == 4) & (hour >= 17)

    return ~(is_saturday | is_sunday_early | is_friday_late)
