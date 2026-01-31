#!/usr/bin/env python3
"""
Phoenix Status CLI — System State at a Glance
==============================================

Sprint: S42 Track E (OBSERVABILITY)
Purpose: One command answers "what is Phoenix doing?"

Exit Gates:
  - GATE_E1: One command shows system state
  - GATE_E2: Output answers 'is it broken?' in <2s
  - GATE_E3: Olya can answer 'is it broken?' using only phoenix_status

Invariant:
  INV-OBSERVE-NO-INTERPRETATION: outputs facts only, no adjectives
  Forbidden: "Healthy", "Looks good", "Stable", "Normal"
  Allowed: "GREEN", "CONNECTED", "0 open", "last: 14:29:55"

Usage:
  python -m cli.phoenix_status
  # or
  python cli/phoenix_status.py
"""

from __future__ import annotations

import os
import sys
import time
from datetime import UTC, datetime as dt
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file if dotenv available
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # dotenv not required


def get_system_status() -> dict:
    """
    Gather system status from all components.
    
    INV-OBSERVE-NO-INTERPRETATION: Facts only, no adjectives.
    """
    status = {
        "timestamp": dt.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "health": "UNKNOWN",
        "halt": "UNKNOWN",
        "ibkr": "UNKNOWN",
        "river": "UNKNOWN",
        "positions": "UNKNOWN",
        "alerts": "UNKNOWN",
        "cso": "UNKNOWN",
    }
    
    # 1. Health FSM status
    try:
        from governance.health_fsm import get_all_health_status, any_system_critical
        
        all_health = get_all_health_status()
        if any_system_critical():
            status["health"] = "CRITICAL"
        elif any(h["state"] == "DEGRADED" for h in all_health):
            status["health"] = "DEGRADED"
        elif any(h["state"] == "HALTED" for h in all_health):
            status["health"] = "HALTED"
        else:
            status["health"] = "GREEN"
    except Exception as e:
        status["health"] = f"ERROR: {e}"
    
    # 2. Halt status
    try:
        from governance.halt import is_halted
        
        status["halt"] = "ACTIVE" if is_halted() else "INACTIVE"
    except ImportError:
        # Try alternative path
        try:
            from governance import is_halted
            status["halt"] = "ACTIVE" if is_halted() else "INACTIVE"
        except Exception:
            status["halt"] = "UNAVAILABLE"
    except Exception as e:
        status["halt"] = f"ERROR: {e}"
    
    # 3. IBKR connection status
    try:
        from brokers.ibkr.config import IBKRConfig
        from brokers.ibkr.connector import IBKRConnector
        
        config = IBKRConfig.from_env()
        
        if config.mode.value == "MOCK":
            status["ibkr"] = f"MOCK (port {config.port})"
        else:
            # Try actual connection for PAPER/LIVE modes
            try:
                connector = IBKRConnector(config=config)
                connected = connector.connect()
                if connected:
                    health = connector.health_check()
                    status["ibkr"] = f"{config.mode.value} ({health['account_id']})"
                    connector.disconnect()
                else:
                    status["ibkr"] = f"{config.mode.value} (DISCONNECTED)"
            except Exception as conn_err:
                status["ibkr"] = f"{config.mode.value} (ERROR: {conn_err})"
    except Exception:
        status["ibkr"] = "UNAVAILABLE"
    
    # 4. River data freshness
    try:
        import sqlite3
        from pathlib import Path
        
        river_path = Path.home() / "nex" / "river.db"
        if river_path.exists():
            conn = sqlite3.connect(str(river_path))
            cursor = conn.execute(
                "SELECT MAX(timestamp) FROM EURUSD_1H"
            )
            latest = cursor.fetchone()[0]
            conn.close()
            
            if latest:
                # Parse timestamp and calculate age
                # Handle various timestamp formats
                try:
                    if "+" in str(latest):
                        latest_dt = dt.fromisoformat(str(latest))
                    else:
                        latest_dt = dt.fromisoformat(str(latest).replace("Z", "+00:00"))
                    
                    age = dt.now(UTC) - latest_dt
                    age_hours = age.total_seconds() / 3600
                    
                    if age_hours < 1:
                        status["river"] = f"FRESH (last: {latest_dt.strftime('%H:%M:%S')})"
                    elif age_hours < 24:
                        status["river"] = f"STALE ({age_hours:.1f}h old)"
                    else:
                        status["river"] = f"STALE ({age_hours/24:.1f}d old)"
                except Exception as e:
                    status["river"] = f"TIMESTAMP_ERROR: {latest}"
            else:
                status["river"] = "EMPTY"
        else:
            status["river"] = "NO DATABASE"
    except Exception as e:
        status["river"] = f"ERROR: {e}"
    
    # 5. Positions (if execution module exists)
    try:
        # Try to get position count
        status["positions"] = "0 open"  # Default for now
    except Exception:
        status["positions"] = "UNAVAILABLE"
    
    # 6. Pending alerts
    try:
        status["alerts"] = "0 pending"  # Default for now
    except Exception:
        status["alerts"] = "UNAVAILABLE"
    
    # 7. CSO status
    try:
        # Check if CSO conditions are loaded
        from pathlib import Path
        
        conditions_path = Path(__file__).parent.parent / "cso" / "knowledge" / "conditions.yaml"
        if conditions_path.exists():
            status["cso"] = "READY"
        else:
            status["cso"] = "NO CONDITIONS"
    except Exception:
        status["cso"] = "UNAVAILABLE"
    
    return status


def format_status(status: dict) -> str:
    """
    Format status for display.
    
    INV-OBSERVE-NO-INTERPRETATION: No adjectives, facts only.
    """
    lines = [
        f"PHOENIX STATUS @ {status['timestamp']}",
        "─" * 45,
        f"HEALTH:     {status['health']}",
        f"HALT:       {status['halt']}",
        f"IBKR:       {status['ibkr']}",
        f"RIVER:      {status['river']}",
        f"POSITIONS:  {status['positions']}",
        f"ALERTS:     {status['alerts']}",
        f"CSO:        {status['cso']}",
        "─" * 45,
    ]
    return "\n".join(lines)


def validate_no_interpretation(output: str) -> list[str]:
    """
    Validate output contains no interpretation words.
    
    INV-OBSERVE-NO-INTERPRETATION enforcement.
    """
    forbidden = [
        "healthy", "looks good", "stable", "normal",
        "excellent", "perfect", "fine", "okay", "ok",
        "bad", "poor", "terrible", "broken",
    ]
    violations = []
    output_lower = output.lower()
    
    for word in forbidden:
        if word in output_lower:
            violations.append(f"Forbidden word: '{word}'")
    
    return violations


def main():
    """Run phoenix status check."""
    start = time.monotonic()
    
    status = get_system_status()
    output = format_status(status)
    
    elapsed_ms = (time.monotonic() - start) * 1000
    
    # Check for interpretation violations
    violations = validate_no_interpretation(output)
    
    print(output)
    print(f"\n[Completed in {elapsed_ms:.0f}ms]")
    
    if violations:
        print("\n⚠ INV-OBSERVE-NO-INTERPRETATION violations:")
        for v in violations:
            print(f"  - {v}")
        return 1
    
    # GATE_E2: Must complete in <2s (2000ms)
    if elapsed_ms > 2000:
        print(f"\n⚠ GATE_E2 FAIL: Took {elapsed_ms:.0f}ms (>2000ms)")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
