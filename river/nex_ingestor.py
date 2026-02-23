"""
NEX Ingestor — Migrate audited NEX parquet data into River daily partitions.

T1 audit finding: NEX data contains two sources joined at 2025-11-22.
  - Before 2025-11-22: Dukascopy (positive tick volume, Sunday open at 00:00 UTC)
  - From 2025-11-22: IBKR MIDPOINT (volume=-1, Sunday open at ~22:15 UTC)

This ingestor reads the monolithic NEX parquet files and writes them
into the River daily partition scheme with proper source tags.

Invariants:
    INV-RIVER-SOURCE-TAG: source = 'dukascopy' or 'ibkr' based on boundary
    INV-RIVER-BITEMPORAL: knowledge_time = ingestion_timestamp
    INV-RIVER-IMMUTABLE: Daily files written once, never modified
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from .schema import (
    CANONICAL_PAIRS,
    NEX_SOURCE_BOUNDARY,
    RAW_BAR_SCHEMA,
    compute_bar_hashes,
    get_river_root,
    validate_raw_bars,
)

logger = structlog.get_logger(__name__)

NEX_FX_DIR: Path = Path.home() / "nex" / "nex_lab" / "data" / "fx"


def ingest_pair(
    pair: str,
    *,
    river_root: Path | None = None,
    nex_dir: Path | None = None,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> int:
    """Ingest one pair from NEX into River daily partitions.

    Returns total bars written (skips existing daily files).
    """
    if pair not in CANONICAL_PAIRS:
        raise ValueError(f"Non-canonical pair: {pair}")

    root = river_root or get_river_root()
    src = nex_dir or NEX_FX_DIR
    parquet_file = src / f"{pair}_1m.parquet"

    if not parquet_file.exists():
        raise FileNotFoundError(f"NEX file not found: {parquet_file}")

    logger.info("ingest_start", pair=pair, source=str(parquet_file))
    df = pd.read_parquet(parquet_file)
    df = df.sort_values("timestamp").reset_index(drop=True)

    if start is not None:
        df = df[df["timestamp"] >= start]
    if end is not None:
        df = df[df["timestamp"] < end]

    if df.empty:
        logger.warning("no_bars_in_range", pair=pair)
        return 0

    # Tag source based on T1 audit boundary
    df["source"] = "dukascopy"
    df.loc[df["timestamp"] >= NEX_SOURCE_BOUNDARY, "source"] = "ibkr"

    kt = pd.Timestamp.now(tz="UTC")
    df["knowledge_time"] = kt
    df["bar_hash"] = compute_bar_hashes(df)

    errors = validate_raw_bars(df)
    if errors:
        logger.error("validation_failed", pair=pair, errors=errors)
        raise ValueError(f"NEX validation failed for {pair}: {errors}")

    duka_count = (df["source"] == "dukascopy").sum()
    ibkr_count = (df["source"] == "ibkr").sum()
    logger.info(
        "source_split",
        pair=pair,
        dukascopy=int(duka_count),
        ibkr=int(ibkr_count),
        boundary=str(NEX_SOURCE_BOUNDARY),
    )

    written = _write_daily_partitions(root, pair, df)
    logger.info(
        "ingest_complete",
        pair=pair,
        total=len(df),
        written=written,
        first=str(df["timestamp"].min()),
        last=str(df["timestamp"].max()),
    )
    return written


def ingest_all(
    *,
    river_root: Path | None = None,
    start: pd.Timestamp | None = None,
    end: pd.Timestamp | None = None,
) -> dict[str, int]:
    """Ingest all 6 canonical pairs from NEX into River."""
    results: dict[str, int] = {}
    for pair in sorted(CANONICAL_PAIRS):
        try:
            results[pair] = ingest_pair(
                pair,
                river_root=river_root,
                start=start,
                end=end,
            )
        except Exception:
            logger.exception("ingest_pair_failed", pair=pair)
            results[pair] = 0

    total = sum(results.values())
    logger.info("ingest_all_complete", results=results, total=total)
    return results


def _write_daily_partitions(root: Path, pair: str, df: pd.DataFrame) -> int:
    df = df.copy()
    df["_date"] = df["timestamp"].dt.date
    written = 0

    for date_val, group in df.groupby("_date"):
        path = (
            root
            / pair
            / str(date_val.year)
            / f"{date_val.month:02d}"
            / f"{date_val.day:02d}.parquet"
        )
        if path.exists():
            continue

        path.parent.mkdir(parents=True, exist_ok=True)
        out = group.drop(columns=["_date"]).sort_values("timestamp").reset_index(drop=True)
        table = pa.Table.from_pandas(out, schema=RAW_BAR_SCHEMA, preserve_index=False)
        pq.write_table(table, path)
        written += len(out)

    return written


def run_nex_ingest() -> None:
    """Entry point: ingest all 6 canonical pairs from NEX.

    Ingests full range. T0 files (Jan 18+) are preserved — ingestor
    skips existing daily files. NEX IBKR data (Nov 22 → Jan 17) fills
    the gap between Dukascopy and T0 capture.
    """
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
    )
    log = structlog.get_logger("nex_ingest")

    log.info("nex_ingest_start", pairs=sorted(CANONICAL_PAIRS))
    log.info("note", msg="Full range. T0 files preserved where they exist.")

    results = ingest_all()

    log.info("nex_ingest_summary")
    for pair, count in sorted(results.items()):
        log.info("pair_result", pair=pair, bars=count)

    total = sum(results.values())
    log.info("nex_ingest_done", total=total, river_root=str(get_river_root()))


if __name__ == "__main__":
    run_nex_ingest()
