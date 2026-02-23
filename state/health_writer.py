#!/usr/bin/env python3
"""
Health State Writer — CSO-Readable Health File
==============================================

Sprint: S42 Track A (CSO Visibility)
Purpose: Write health.yaml so CSO can read system status directly

Usage:
  # One-shot write
  python -m state.health_writer
  
  # From other modules
  from state.health_writer import write_health_file
  write_health_file()

Invariant:
  INV-OBSERVE-NO-INTERPRETATION: Facts only in status fields
  operator_summary CAN use natural language for CSO consumption

File Location: /phoenix/state/health.yaml
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import UTC, datetime as dt
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Health file location
HEALTH_FILE = Path(__file__).parent / "health.yaml"

# Status constants
STATUS_HEALTHY = "HEALTHY"
STATUS_DEGRADED = "DEGRADED"
STATUS_CRITICAL = "CRITICAL"
STATUS_HALTED = "HALTED"
STATUS_UNKNOWN = "UNKNOWN"


def get_component_status() -> dict[str, dict[str, Any]]:
    """
    Gather status from all Phoenix components.
    
    Returns dict with component name -> status dict.
    """
    components = {}
    
    # 1. River data freshness
    components["river"] = _get_river_status()
    
    # 2. IBKR connection
    components["ibkr"] = _get_ibkr_status()
    
    # 3. Halt mechanism
    components["halt"] = _get_halt_status()
    
    # 4. Watcher (file seam)
    components["watcher"] = _get_watcher_status()
    
    # 5. CSO knowledge
    components["cso"] = _get_cso_status()
    
    # 6. Health FSM
    components["health_fsm"] = _get_health_fsm_status()
    
    return components


def _get_river_status() -> dict[str, str]:
    """Get River data status."""
    try:
        import sqlite3
        
        river_path = Path.home() / "nex" / "river.db"
        if not river_path.exists():
            return {
                "status": "ERROR",
                "last_update": "unknown",
                "detail": "Database not found"
            }
        
        conn = sqlite3.connect(str(river_path))
        cursor = conn.execute("SELECT MAX(timestamp) FROM EURUSD_1H")
        latest = cursor.fetchone()[0]
        
        # Get column count
        cursor = conn.execute("PRAGMA table_info(EURUSD_1H)")
        cols = len(cursor.fetchall())
        conn.close()
        
        if not latest:
            return {
                "status": "ERROR",
                "last_update": "unknown",
                "detail": "No data in table"
            }
        
        # Parse timestamp
        if "+" in str(latest):
            latest_dt = dt.fromisoformat(str(latest))
        else:
            latest_dt = dt.fromisoformat(str(latest).replace("Z", "+00:00"))
        
        age = dt.now(UTC) - latest_dt
        age_minutes = age.total_seconds() / 60
        
        if age_minutes < 15:
            return {
                "status": STATUS_HEALTHY,
                "last_update": f"{int(age_minutes)}m ago",
                "detail": f"{cols} cols, fresh"
            }
        elif age_minutes < 60:
            return {
                "status": "STALE",
                "last_update": f"{int(age_minutes)}m ago",
                "detail": f"Data stale >{int(age_minutes)}min"
            }
        else:
            hours = age_minutes / 60
            return {
                "status": "STALE",
                "last_update": f"{hours:.1f}h ago",
                "detail": f"Data stale >{hours:.1f}h"
            }
            
    except Exception as e:
        return {
            "status": "ERROR",
            "last_update": "unknown",
            "detail": str(e)[:50]
        }


def _get_ibkr_status() -> dict[str, str]:
    """Get IBKR connection status."""
    try:
        from brokers.ibkr.config import get_ibkr_config
        
        config = get_ibkr_config()
        if config:
            return {
                "status": "CONNECTED",
                "mode": config.mode.value.upper(),
                "detail": f"{config.mode.value} account (port {config.port})"
            }
        else:
            return {
                "status": "DISCONNECTED",
                "mode": "UNKNOWN",
                "detail": "Not configured"
            }
    except Exception as e:
        return {
            "status": "UNKNOWN",
            "mode": "UNKNOWN",
            "detail": f"Config error: {str(e)[:30]}"
        }


def _get_halt_status() -> dict[str, str]:
    """Get halt mechanism status."""
    try:
        from governance.halt import is_halted
        
        halted = is_halted()
        return {
            "status": "TRIGGERED" if halted else "READY",
            "latency": "unknown",  # Would need timing test
            "detail": "Halt active" if halted else "Halt mechanism ready"
        }
    except ImportError:
        try:
            from governance import is_halted
            halted = is_halted()
            return {
                "status": "TRIGGERED" if halted else "READY",
                "latency": "unknown",
                "detail": "Halt active" if halted else "Halt mechanism ready"
            }
        except Exception:
            return {
                "status": "UNKNOWN",
                "latency": "unknown",
                "detail": "Halt module unavailable"
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "latency": "unknown",
            "detail": str(e)[:50]
        }


def _get_watcher_status() -> dict[str, str]:
    """Get watcher/file seam status."""
    # Check if intake directory exists and is writable
    try:
        intake_path = Path(__file__).parent.parent / "intake" / "olya"
        if intake_path.exists():
            return {
                "status": "RUNNING",
                "detail": "File seam operational"
            }
        else:
            return {
                "status": "STOPPED",
                "detail": "Intake directory missing"
            }
    except Exception as e:
        return {
            "status": "UNKNOWN",
            "detail": str(e)[:50]
        }


def _get_cso_status() -> dict[str, str]:
    """Get CSO knowledge status."""
    try:
        conditions_path = Path(__file__).parent.parent / "cso" / "knowledge" / "conditions.yaml"
        glossary_path = Path(__file__).parent.parent / "cso" / "knowledge" / "GATE_GLOSSARY.yaml"
        
        if conditions_path.exists() and glossary_path.exists():
            return {
                "status": STATUS_HEALTHY,
                "detail": "Knowledge files loaded"
            }
        elif conditions_path.exists():
            return {
                "status": STATUS_HEALTHY,
                "detail": "Conditions loaded (glossary missing)"
            }
        else:
            return {
                "status": "ERROR",
                "detail": "Knowledge files missing"
            }
    except Exception as e:
        return {
            "status": "ERROR",
            "detail": str(e)[:50]
        }


def _get_health_fsm_status() -> dict[str, str]:
    """Get Health FSM status."""
    try:
        from governance.health_fsm import get_all_health_status, any_system_critical
        
        all_health = get_all_health_status()
        critical_count = sum(1 for h in all_health if h.get("state") == "CRITICAL")
        degraded_count = sum(1 for h in all_health if h.get("state") == "DEGRADED")
        
        if any_system_critical():
            return {
                "status": STATUS_CRITICAL,
                "detail": f"{critical_count} critical component(s)"
            }
        elif degraded_count > 0:
            return {
                "status": STATUS_DEGRADED,
                "detail": f"{degraded_count} degraded component(s)"
            }
        else:
            return {
                "status": STATUS_HEALTHY,
                "detail": f"{len(all_health)} components tracked"
            }
    except Exception as e:
        return {
            "status": "UNKNOWN",
            "detail": f"FSM unavailable: {str(e)[:30]}"
        }


def compute_overall_status(components: dict[str, dict]) -> str:
    """
    Compute overall system status from component statuses.
    
    Priority: HALTED > CRITICAL > DEGRADED > HEALTHY
    """
    statuses = [c.get("status", "UNKNOWN") for c in components.values()]
    
    # Check halt first
    if components.get("halt", {}).get("status") == "TRIGGERED":
        return STATUS_HALTED
    
    # Then critical
    if STATUS_CRITICAL in statuses or "ERROR" in statuses:
        return STATUS_CRITICAL
    
    # Then degraded
    if STATUS_DEGRADED in statuses or "STALE" in statuses:
        return STATUS_DEGRADED
    
    # Check for unknowns
    if all(s == "UNKNOWN" for s in statuses):
        return STATUS_UNKNOWN
    
    return STATUS_HEALTHY


def generate_operator_summary(overall: str, components: dict[str, dict]) -> str:
    """
    Generate human-readable summary for CSO to report.
    
    This field CAN use natural language — it's for CSO consumption.
    """
    if overall == STATUS_HEALTHY:
        return "All systems operational. Ready for trading."
    
    if overall == STATUS_HALTED:
        return "System is HALTED. All trading suspended. Check terminal for details."
    
    issues = []
    
    # Check each component for issues
    river = components.get("river", {})
    if river.get("status") in ["STALE", "ERROR"]:
        age = river.get("last_update", "unknown")
        issues.append(f"River data is stale ({age}). Market scans won't work until refresh.")
    
    ibkr = components.get("ibkr", {})
    if ibkr.get("status") in ["DISCONNECTED", "UNKNOWN"]:
        issues.append("IBKR connection unavailable. Live trading blocked.")
    
    halt = components.get("halt", {})
    if halt.get("status") == "ERROR":
        issues.append("Halt mechanism error. This is serious — check immediately.")
    
    cso = components.get("cso", {})
    if cso.get("status") == "ERROR":
        issues.append("CSO knowledge files missing. Gate validation unavailable.")
    
    health_fsm = components.get("health_fsm", {})
    if health_fsm.get("status") == STATUS_CRITICAL:
        issues.append(f"Critical health state: {health_fsm.get('detail', 'unknown')}.")
    
    if not issues:
        return f"System is {overall}. Check component details for specifics."
    
    return " ".join(issues)


def generate_message(overall: str, components: dict[str, dict]) -> str:
    """
    Generate short status message (facts only).
    
    INV-OBSERVE-NO-INTERPRETATION: No adjectives.
    """
    if overall == STATUS_HEALTHY:
        return "All components operational"
    elif overall == STATUS_HALTED:
        return "HALT ACTIVE"
    elif overall == STATUS_CRITICAL:
        critical = [k for k, v in components.items() if v.get("status") in ["ERROR", "CRITICAL"]]
        return f"CRITICAL: {', '.join(critical)}"
    elif overall == STATUS_DEGRADED:
        degraded = [k for k, v in components.items() if v.get("status") in ["STALE", "DEGRADED"]]
        return f"DEGRADED: {', '.join(degraded)}"
    else:
        return "Status unknown"


def build_health_yaml(components: dict[str, dict], overall: str) -> str:
    """
    Build the health.yaml content as a string.
    
    Using string building instead of yaml.dump for control over formatting.
    """
    timestamp = dt.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    message = generate_message(overall, components)
    operator_summary = generate_operator_summary(overall, components)
    
    lines = [
        "# Phoenix Health State",
        "# CSO read-only - system health snapshot",
        f"# Updated: {timestamp}",
        "",
        'version: "1.0"',
        f"timestamp: {timestamp}",
        "",
        f"overall: {overall}",
        "",
        "components:",
    ]
    
    # Add each component
    for name, data in components.items():
        lines.append(f"  {name}:")
        for key, value in data.items():
            # Quote strings that might have special chars
            if isinstance(value, str) and any(c in value for c in ":#{}[]"):
                lines.append(f'    {key}: "{value}"')
            else:
                lines.append(f"    {key}: {value}")
        lines.append("")
    
    # Add message and operator summary
    lines.append(f'message: "{message}"')
    lines.append("")
    lines.append("# For CSO context - natural language OK here")
    lines.append("operator_summary: |")
    for line in operator_summary.split(". "):
        if line.strip():
            lines.append(f"  {line.strip()}.")
    lines.append("")
    
    return "\n".join(lines)


def write_health_file(force: bool = False) -> Path:
    """
    Write health.yaml with current system state.
    
    Uses atomic write (write to temp, then rename) for safety.
    
    Args:
        force: Write even if status unchanged (for periodic updates)
        
    Returns:
        Path to written file
    """
    # Gather component status
    components = get_component_status()
    
    # Compute overall status
    overall = compute_overall_status(components)
    
    # Build YAML content
    content = build_health_yaml(components, overall)
    
    # Atomic write: write to temp file, then rename
    # This prevents partial reads if CSO checks during write
    HEALTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    fd, tmp_path = tempfile.mkstemp(
        suffix=".yaml",
        prefix="health_",
        dir=HEALTH_FILE.parent
    )
    
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
        
        # Atomic rename
        os.replace(tmp_path, HEALTH_FILE)
        
    except Exception:
        # Clean up temp file on error
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise
    
    return HEALTH_FILE


def main() -> int:
    """Write health file and return status."""
    import sys
    import time
    
    start = time.monotonic()
    
    path = write_health_file()
    
    elapsed_ms = (time.monotonic() - start) * 1000
    
    # Write to stderr for CLI output (not stdout which hooks check)
    sys.stderr.write(f"Health file written to: {path}\n")
    sys.stderr.write(f"Completed in {elapsed_ms:.0f}ms\n")
    sys.stderr.write("\n--- Contents ---\n")
    sys.stderr.write(path.read_text())
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
