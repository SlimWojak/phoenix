#!/bin/bash
# Strategy Orchestrator Runner — watches River staging for new bars
# Shadow mode: observes and records, does NOT execute trades.
# Launched by launchd (com.a8ra.strategy-orchestrator)

cd ~/phoenix || exit 1

export RIVER_ROOT="${RIVER_ROOT:-$HOME/phoenix-river}"
export PYTHONUNBUFFERED=1

# Use venv python if available
if [ -f .venv/bin/python3 ]; then
    PYTHON=.venv/bin/python3
else
    PYTHON=python3
fi

exec $PYTHON -c "
import time
import json
import logging
from pathlib import Path
from datetime import datetime, UTC

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(name)s | %(message)s',
)
log = logging.getLogger('orchestrator.runner')

from daemons.strategy_orchestrator import StrategyOrchestrator, OrchestratorConfig
from river.reader import RiverReader

RIVER_ROOT = Path('${RIVER_ROOT:-$HOME/phoenix-river}')
STAGING = RIVER_ROOT / 'EURUSD' / '.staging'
POLL_INTERVAL = 30  # seconds

config = OrchestratorConfig(
    pair='EURUSD',
    shadow_mode=True,
    cartridge_hash='ARS_v2.0.0',
)
orchestrator = StrategyOrchestrator(config)

log.info('Strategy orchestrator started (SHADOW MODE)')
log.info(f'Watching: {STAGING}')

last_bar_time = None

while True:
    try:
        # Check heartbeat for new bars
        hb_path = RIVER_ROOT / '.heartbeat.json'
        if hb_path.exists():
            hb = json.loads(hb_path.read_text())
            current_bar_time = hb.get('last_bar_time')

            if current_bar_time and current_bar_time != last_bar_time:
                log.info(f'New bar detected: {current_bar_time}')

                # Pre-flight
                pf = orchestrator.pre_flight()
                if not pf.healthy:
                    log.warning(f'Pre-flight failed: {pf.errors}')
                else:
                    # Read latest bars and process
                    reader = RiverReader(river_root=RIVER_ROOT)
                    bars = reader.get_bars('EURUSD')
                    if bars is not None and len(bars) > 0:
                        latest = bars.iloc[-1]
                        result = orchestrator.process_bar(latest)
                        log.info(f'Bar result: outcome={result.outcome}, gates_passed={result.gates_passed}/{result.gates_total}')
                        if result.shadow_observation:
                            log.info(f'Shadow observation: {result.shadow_observation.verdict}')

                last_bar_time = current_bar_time

    except Exception as e:
        log.error(f'Orchestrator error: {e}', exc_info=True)

    time.sleep(POLL_INTERVAL)
"
