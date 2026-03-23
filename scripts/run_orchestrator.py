#!/usr/bin/env python3
"""
Strategy Orchestrator Runner — DEPLOY.P3
==========================================

Wires the full 10-step constitutional chain:
  River bars → L1-L7 enrichment → MarketState → 5-drawer CSO → governance

Watches staging JSONL for new bars. Processes each bar through the
StrategyOrchestrator with scoped data reads (last 3 days, not full corpus).

Usage:
    cd ~/phoenix
    .venv/bin/python scripts/run_orchestrator.py --pair EURUSD --poll-interval 30

INV-GOV-HALT-BEFORE-ACTION: halt checked before every cycle.
INV-SHADOW-MODE-RESPECTED: shadow=True → observe only.
INV-PRE-FLIGHT-HEARTBEAT: pre-flight before first cycle.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import structlog

PHOENIX_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

import pandas as pd  # noqa: E402

from daemons.strategy_orchestrator import (  # noqa: E402
    BarOutcome,
    OrchestratorConfig,
    StrategyOrchestrator,
)
from enrichment.layers import (  # noqa: E402
    l1_time_sessions,
    l2_reference_levels,
    l3_sweeps,
    l4_structure_breaks,
    l5_order_blocks,
    l6_fvg_imbalances,
    l7_asia_scalp,
)
from river.reader import RiverReader  # noqa: E402

log = structlog.get_logger("orchestrator.runner")

RIVER_ROOT = Path(os.environ.get("RIVER_ROOT", str(Path.home() / "phoenix-river")))
LOOKBACK_DAYS = 3
ENRICHMENT_TF = "5m"


def enrich_pipeline(df: pd.DataFrame, pair: str) -> pd.DataFrame:
    """Run L1-L7 enrichment chain on raw bars."""
    df = l1_time_sessions.enrich(df)
    df = l2_reference_levels.enrich(df, symbol=pair)
    df = l3_sweeps.enrich(df, symbol=pair)
    df = l4_structure_breaks.enrich(df, symbol=pair)
    df = l5_order_blocks.enrich(df, symbol=pair)
    df = l6_fvg_imbalances.enrich(df)
    df = l7_asia_scalp.enrich(df, symbol=pair)
    return df


def read_scoped_bars(reader: RiverReader, pair: str, tf: str) -> pd.DataFrame:
    """Read recent bars only — scoped to LOOKBACK_DAYS, not full corpus."""
    end = pd.Timestamp.now(tz="UTC")
    start = end - pd.Timedelta(days=LOOKBACK_DAYS)
    return reader.get_bars(pair, tf, start=start, end=end)


def get_latest_bar_time(heartbeat_path: Path) -> str | None:
    """Read last_bar_time from River heartbeat JSON."""
    if not heartbeat_path.exists():
        return None
    try:
        data = json.loads(heartbeat_path.read_text())
        val = data.get("last_bar_time")
        return str(val) if val is not None else None
    except (json.JSONDecodeError, OSError):
        return None


def run_cycle(
    orchestrator: StrategyOrchestrator,
    reader: RiverReader,
    pair: str,
) -> None:
    """Single processing cycle: read → enrich → evaluate."""
    cycle_start = time.monotonic()

    raw_bars = read_scoped_bars(reader, pair, ENRICHMENT_TF)
    if raw_bars.empty:
        log.warning("no_bars", pair=pair, lookback_days=LOOKBACK_DAYS)
        return

    bar_count = len(raw_bars)
    latest_ts = raw_bars["timestamp"].max()

    try:
        enriched = enrich_pipeline(raw_bars, pair)
    except Exception as e:
        log.error("enrichment_failed", error=str(e), pair=pair)
        return

    col_count = len(enriched.columns)
    now = pd.Timestamp.now(tz="UTC").floor("min").to_pydatetime()

    result = orchestrator.process_bar(enriched, pair, now)

    cycle_ms = (time.monotonic() - cycle_start) * 1000

    gate_summary = ""
    if result.five_drawer is not None:
        passed = list(result.five_drawer.drawer_status.values())
        gate_summary = f"{sum(passed)}/{len(passed)} drawers"

    log.info(
        "cycle_complete",
        pair=pair,
        outcome=result.outcome.value,
        bar_count=bar_count,
        columns=col_count,
        latest_bar=str(latest_ts),
        gates=gate_summary,
        cycle_ms=round(cycle_ms, 1),
        rejection=result.rejection_reason,
        shadow_obs=result.shadow_observation is not None,
    )

    if result.outcome == BarOutcome.SHADOW_OBSERVATION and result.proposal:
        p = result.proposal
        log.info(
            "shadow_observation",
            direction=p.direction.value,
            entry=f"{p.entry_price:.5f}",
            sl=f"{p.stop_loss:.5f}",
            tp=f"{p.take_profit:.5f}",
            rr=f"{p.rr_ratio:.2f}",
            size=p.position_size_lots,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="a8ra Strategy Orchestrator")
    parser.add_argument("--pair", default="EURUSD", help="Trading pair")
    parser.add_argument("--poll-interval", type=int, default=30, help="Seconds between cycles")
    parser.add_argument("--lease", default=None, help="Lease YAML path (unused — shadow default)")
    parser.add_argument("--once", action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
    )

    config = OrchestratorConfig(
        pair=args.pair,
        shadow_mode=True,
        cartridge_hash="ARS_v2.0.0",
    )
    orchestrator = StrategyOrchestrator(config)
    reader = RiverReader(river_root=RIVER_ROOT)
    heartbeat_path = RIVER_ROOT / ".heartbeat.json"

    pf = orchestrator.pre_flight()
    if not pf.healthy:
        log.error("pre_flight_failed", errors=pf.errors)
        sys.exit(1)

    log.info(
        "orchestrator_started",
        pair=args.pair,
        shadow_mode=True,
        river_root=str(RIVER_ROOT),
        poll_interval=args.poll_interval,
        lookback_days=LOOKBACK_DAYS,
        timeframe=ENRICHMENT_TF,
    )

    if args.once:
        run_cycle(orchestrator, reader, args.pair)
        return

    last_bar_time: str | None = None

    while True:
        try:
            current_bar_time = get_latest_bar_time(heartbeat_path)

            if current_bar_time and current_bar_time != last_bar_time:
                log.info("new_bar_detected", bar_time=current_bar_time)
                run_cycle(orchestrator, reader, args.pair)
                last_bar_time = current_bar_time

        except KeyboardInterrupt:
            log.info("orchestrator_stopped", reason="keyboard_interrupt")
            break
        except Exception as e:
            log.error("cycle_error", error=str(e), exc_info=True)

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()
