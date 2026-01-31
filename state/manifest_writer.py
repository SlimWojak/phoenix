#!/usr/bin/env python3
"""
Manifest Writer — HUD Integration Bridge
=========================================

Sprint: S48 INTEGRATION
Purpose: Transform Phoenix state files into HUD-readable manifest.json

Reads:
  - state/health.yaml     (system health from health_writer.py)
  - state/orientation.yaml (execution context)

Writes:
  - state/manifest.json   (HUD v1.1 schema)

Usage:
  python -m state.manifest_writer          # One-shot write
  python -m state.manifest_writer --watch  # Continuous mode (future)

Invariants:
  INV-HUD-ATOMIC-READ: Write .tmp → os.rename (atomic)
  INV-HUD-READ-ONLY: HUD only reads, never writes
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import UTC
from datetime import datetime as dt
from pathlib import Path
from typing import Any

# Constants
STATE_DIR = Path(__file__).parent
MANIFEST_FILE = STATE_DIR / "manifest.json"
HEALTH_FILE = STATE_DIR / "health.yaml"
ORIENTATION_FILE = STATE_DIR / "orientation.yaml"
SEQ_FILE = STATE_DIR / ".manifest_seq"

SCHEMA_VERSION = "1.1"

# ═══════════════════════════════════════════════════════════════════════════
# KILLZONE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════

# Killzone schedule (UTC)
KILLZONES = [
    ("ASIA", 0, 3),  # 00:00-03:00 UTC
    ("LONDON", 7, 10),  # 07:00-10:00 UTC
    ("NEW_YORK", 12, 15),  # 12:00-15:00 UTC
]


def get_current_killzone(now: dt | None = None) -> dict[str, Any]:
    """
    Calculate current killzone session based on UTC time.

    Returns:
        dict with kz, active, time_remaining, next_session, next_start
    """
    if now is None:
        now = dt.now(UTC)

    hour = now.hour
    minute = now.minute

    # Check if in any killzone
    for kz_name, start_hour, end_hour in KILLZONES:
        if start_hour <= hour < end_hour:
            # Calculate time remaining
            remaining_mins = (end_hour - hour - 1) * 60 + (60 - minute)
            remaining_str = _format_duration(remaining_mins)

            # Find next session
            next_kz, next_start = _get_next_killzone(kz_name)

            return {
                "kz": kz_name,
                "active": True,
                "time_remaining": remaining_str,
                "next_session": next_kz,
                "next_start": f"{next_start:02d}:00",
            }

    # Not in any killzone
    next_kz, next_start = _get_next_killzone_from_hour(hour)

    return {
        "kz": "OFF_SESSION",
        "active": False,
        "time_remaining": "--",  # HUD expects non-null string
        "next_session": next_kz,
        "next_start": f"{next_start:02d}:00",
    }


def _get_next_killzone(current_kz: str) -> tuple[str, int]:
    """Get the killzone after the current one."""
    kz_order = ["ASIA", "LONDON", "NEW_YORK"]
    idx = kz_order.index(current_kz)
    next_idx = (idx + 1) % len(kz_order)
    next_kz = kz_order[next_idx]

    for name, start, _ in KILLZONES:
        if name == next_kz:
            return name, start

    return "ASIA", 0


def _get_next_killzone_from_hour(hour: int) -> tuple[str, int]:
    """Get the next killzone from current hour when off-session."""
    for kz_name, start_hour, _ in KILLZONES:
        if hour < start_hour:
            return kz_name, start_hour

    # After all sessions, next is ASIA (tomorrow)
    return "ASIA", 0


def _format_duration(minutes: int) -> str:
    """Format minutes as 'Xh Ym' or 'Ym'."""
    if minutes >= 60:
        h = minutes // 60
        m = minutes % 60
        if m > 0:
            return f"{h}h {m}m"
        return f"{h}h"
    return f"{minutes}m"


# ═══════════════════════════════════════════════════════════════════════════
# YAML READER (minimal, no dependency)
# ═══════════════════════════════════════════════════════════════════════════


def read_yaml_simple(path: Path) -> dict[str, Any]:
    """
    Simple YAML reader for flat/nested key-value structures.
    Handles our health.yaml and orientation.yaml formats.

    Not a full YAML parser - just enough for our state files.
    """
    if not path.exists():
        return {}

    result: dict[str, Any] = {}
    current_section: str | None = None
    current_dict: dict[str, Any] = result

    with open(path) as f:
        for line in f:
            # Skip comments and empty lines
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # Handle multi-line values (skip for now)
            if stripped.startswith("|"):
                continue

            # Check indentation level
            indent = len(line) - len(line.lstrip())

            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip()

                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                if indent == 0:
                    # Top-level key
                    if not value:
                        # Section header
                        result[key] = {}
                        current_section = key
                        current_dict = result[key]
                    else:
                        result[key] = _parse_value(value)
                        current_section = None
                        current_dict = result
                elif indent == 2 and current_section:
                    # Second level (component)
                    if not value:
                        current_dict[key] = {}
                    else:
                        current_dict[key] = _parse_value(value)
                elif indent == 4 and current_section:
                    # Third level (component property)
                    parent_key = list(current_dict.keys())[-1] if current_dict else None
                    if parent_key and isinstance(current_dict.get(parent_key), dict):
                        current_dict[parent_key][key] = _parse_value(value)

    return result


def _parse_value(value: str) -> Any:
    """Parse a YAML value to appropriate Python type."""
    if not value:
        return None

    # Boolean
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() in ("null", "~"):
        return None

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    return value


# ═══════════════════════════════════════════════════════════════════════════
# HEALTH MAPPING
# ═══════════════════════════════════════════════════════════════════════════


def map_health_to_hud(health_data: dict[str, Any]) -> dict[str, Any]:
    """
    Map health.yaml data to HUD v1.1 health schema.

    Health status mapping:
      HEALTHY → GREEN
      DEGRADED/STALE → YELLOW
      CRITICAL/ERROR/HALTED → RED
    """
    overall_status = health_data.get("overall", "UNKNOWN")

    # Map to HUD traffic light
    status_map = {
        "HEALTHY": "GREEN",
        "READY": "GREEN",
        "RUNNING": "GREEN",
        "CONNECTED": "GREEN",
        "DEGRADED": "YELLOW",
        "STALE": "YELLOW",
        "DISCONNECTED": "YELLOW",
        "STOPPED": "YELLOW",
        "CRITICAL": "RED",
        "ERROR": "RED",
        "HALTED": "RED",
        "TRIGGERED": "RED",  # Halt triggered
        "UNKNOWN": "YELLOW",
    }
    overall_color = status_map.get(overall_status, "YELLOW")

    # Extract component statuses
    components_raw = health_data.get("components", {})
    degraded_reasons = []

    def get_comp_color(comp_name: str) -> str:
        comp_data = components_raw.get(comp_name, {})
        if isinstance(comp_data, dict):
            comp_status = comp_data.get("status", "UNKNOWN")
        else:
            comp_status = str(comp_data) if comp_data else "UNKNOWN"
        return status_map.get(comp_status, "YELLOW")

    # Build HUD-compatible components dict
    # HUD expects exactly: ibkr, river, halt_state, lease, decay
    components = {
        "ibkr": get_comp_color("ibkr"),
        "river": get_comp_color("river"),
        "halt_state": get_comp_color("halt"),
        "lease": "GREEN",  # Stub - no lease system yet
        "decay": "GREEN",  # Stub - no decay tracking yet
    }

    # Build degraded reasons from all components
    for comp_name, comp_data in components_raw.items():
        if isinstance(comp_data, dict):
            comp_status = comp_data.get("status", "UNKNOWN")
            detail = comp_data.get("detail", "")
        else:
            comp_status = str(comp_data) if comp_data else "UNKNOWN"
            detail = ""

        if comp_status not in ("HEALTHY", "READY", "RUNNING", "CONNECTED"):
            degraded_reasons.append(
                f"{comp_name}: {comp_status}" + (f" ({detail})" if detail else "")
            )

    # Calculate heartbeat age
    timestamp_str = health_data.get("timestamp", "")
    heartbeat_age = _calculate_age_seconds(timestamp_str)

    return {
        "overall": overall_color,
        "status": overall_status,
        "since": timestamp_str if timestamp_str else dt.now(UTC).isoformat(),
        "degraded_reasons": degraded_reasons,
        "components": components,
        "heartbeat_age_seconds": heartbeat_age,
    }


def _calculate_age_seconds(timestamp_str: str) -> int:
    """Calculate seconds since timestamp."""
    if not timestamp_str:
        return 9999

    try:
        # Handle various ISO formats
        if "+" in timestamp_str:
            ts = dt.fromisoformat(timestamp_str)
        elif timestamp_str.endswith("Z"):
            ts = dt.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            ts = dt.fromisoformat(timestamp_str + "+00:00")

        age = dt.now(UTC) - ts
        return int(age.total_seconds())
    except Exception:
        return 9999


# ═══════════════════════════════════════════════════════════════════════════
# SEQUENCE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════


def get_next_seq() -> int:
    """Get and increment manifest sequence number."""
    try:
        if SEQ_FILE.exists():
            seq = int(SEQ_FILE.read_text().strip())
        else:
            seq = 0

        next_seq = seq + 1
        SEQ_FILE.write_text(str(next_seq))
        return next_seq
    except Exception:
        return 1


# ═══════════════════════════════════════════════════════════════════════════
# MANIFEST BUILDER
# ═══════════════════════════════════════════════════════════════════════════


def build_manifest() -> dict[str, Any]:
    """
    Build complete manifest.json from Phoenix state files.

    Reads health.yaml and orientation.yaml, produces HUD v1.1 schema.
    """
    now = dt.now(UTC)

    # Read source files
    health_data = read_yaml_simple(HEALTH_FILE)
    orientation_data = read_yaml_simple(ORIENTATION_FILE)

    # Build meta section
    meta = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest_seq": get_next_seq(),
        "phoenix_state_hash": orientation_data.get("bead_hash", "unknown"),
        "source": "phoenix",
    }

    # Build session section (calculated)
    session = get_current_killzone(now)

    # Build health section (from health.yaml)
    health = map_health_to_hud(health_data)

    # Stub sections (Phoenix doesn't have these yet)
    # Note: HUD Swift models expect non-null numbers, use 0.0 as default
    portfolio = {
        "balance": 0.0,
        "currency": "USD",
        "today_pnl": 0.0,
        "today_pct": 0.0,
        "week_pct": 0.0,
    }

    live_positions: list[dict[str, Any]] = []

    recent_trades: dict[str, Any] = {"items": [], "total_count": 0}

    gates_summary: list[dict[str, Any]] = []

    narrator: dict[str, Any] = {"lines": [], "buffer_size": 20}

    requires_action: list[dict[str, Any]] = []

    # Build lease section (stub)
    lease = {"status": "ABSENT", "strategy": None, "time_remaining": None, "expires_at": None}

    return {
        "meta": meta,
        "session": session,
        "portfolio": portfolio,
        "live_positions": live_positions,
        "recent_trades": recent_trades,
        "gates_summary": gates_summary,
        "narrator": narrator,
        "requires_action": requires_action,
        "health": health,
        "lease": lease,
    }


# ═══════════════════════════════════════════════════════════════════════════
# ATOMIC WRITE
# ═══════════════════════════════════════════════════════════════════════════


def write_manifest(manifest: dict[str, Any]) -> Path:
    """
    Write manifest.json atomically.

    INV-HUD-ATOMIC-READ: Write to .tmp, then os.rename
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Write to temp file
    fd, tmp_path = tempfile.mkstemp(suffix=".json", prefix="manifest_", dir=STATE_DIR)

    try:
        with os.fdopen(fd, "w") as f:
            json.dump(manifest, f, indent=2)

        # Atomic rename
        os.replace(tmp_path, MANIFEST_FILE)

    except Exception:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    return MANIFEST_FILE


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════


def main() -> int:
    """Build and write manifest, return exit code."""
    import time

    start = time.monotonic()

    manifest = build_manifest()
    path = write_manifest(manifest)

    elapsed_ms = (time.monotonic() - start) * 1000

    # Output to stderr for CLI (not stdout which tools parse)
    sys.stderr.write(f"Manifest written to: {path}\n")
    sys.stderr.write(f"Completed in {elapsed_ms:.0f}ms\n")
    sys.stderr.write(f"Sequence: {manifest['meta']['manifest_seq']}\n")
    sys.stderr.write(f"Session: {manifest['session']['kz']}")
    if manifest["session"]["active"]:
        sys.stderr.write(f" (active, {manifest['session']['time_remaining']} remaining)")
    sys.stderr.write("\n")
    sys.stderr.write(f"Health: {manifest['health']['overall']} ({manifest['health']['status']})\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
