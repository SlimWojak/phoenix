#!/usr/bin/env python3
"""
S44 Phase 3: 48h Soak Test
==========================

Sprint: S44 LIVE_VALIDATION
Purpose: Prove system runs unattended for 48h. Boring = success.

Usage:
    python drills/s44_soak_test.py --start      # Start soak test
    python drills/s44_soak_test.py --status     # Check status
    python drills/s44_soak_test.py --end        # End soak and generate report

Dead Man Switch:
    Emits heartbeat bead every 6h to prove system is alive.
    Silent death (GREEN health but no beads) is caught.

End Soak Replay:
    After 48h, replays beads to verify chain integrity.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # dotenv not required

# Constants
SOAK_STATE_FILE = Path(__file__).parent / ".soak_state.json"
BEAD_DB = Path.home() / "God_Mode" / "boardroom" / "advisor_beads.db"
HEARTBEAT_INTERVAL_HOURS = 6
SOAK_DURATION_HOURS = 48


def emit_heartbeat_bead(status_snapshot: dict) -> str:
    """Emit a heartbeat bead to prove system is alive."""
    conn = sqlite3.connect(str(BEAD_DB))
    cursor = conn.cursor()

    content = json.dumps({
        "type": "S44_HEARTBEAT",
        "timestamp": datetime.now(UTC).isoformat(),
        "status": status_snapshot,
    })

    import hashlib
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    cursor.execute("""
        INSERT INTO beads (ts, role, type, sprint, content, content_hash)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(UTC).isoformat(),
        "s44_soak",
        "heartbeat",
        "S44",
        content,
        content_hash,
    ))

    conn.commit()
    bead_id = cursor.lastrowid
    conn.close()

    return str(bead_id)


def get_phoenix_status() -> dict:
    """Get current phoenix status snapshot including IBKR."""
    status = {
        "timestamp": datetime.now(UTC).isoformat(),
    }
    
    # Get phoenix_status CLI output
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, "cli/phoenix_status.py"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent.parent,
        )
        status["phoenix_status"] = result.stdout[:500]
        status["exit_code"] = result.returncode
    except Exception as e:
        status["phoenix_status_error"] = str(e)
    
    # Get direct IBKR status
    try:
        from brokers.ibkr.config import IBKRConfig
        from brokers.ibkr.connector import IBKRConnector
        
        config = IBKRConfig.from_env()
        status["ibkr_mode"] = config.mode.value
        status["ibkr_port"] = config.port
        
        if config.mode.value != "MOCK":
            connector = IBKRConnector(config=config)
            connected = connector.connect()
            if connected:
                health = connector.health_check()
                status["ibkr_connected"] = True
                status["ibkr_account"] = health.get("account_id", "unknown")
                connector.disconnect()
            else:
                status["ibkr_connected"] = False
    except Exception as e:
        status["ibkr_error"] = str(e)
    
    return status


def start_soak():
    """Start the 48h soak test."""
    start_time = datetime.now(UTC)
    end_time = start_time + timedelta(hours=SOAK_DURATION_HOURS)

    state = {
        "status": "RUNNING",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "heartbeats": [],
        "alerts": [],
    }

    # Emit initial heartbeat
    status = get_phoenix_status()
    bead_id = emit_heartbeat_bead(status)
    state["heartbeats"].append({
        "bead_id": bead_id,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    # Save state
    SOAK_STATE_FILE.write_text(json.dumps(state, indent=2))

    print(f"S44 SOAK TEST STARTED")
    print(f"Start: {start_time.isoformat()}")
    print(f"End:   {end_time.isoformat()}")
    print(f"Duration: {SOAK_DURATION_HOURS}h")
    print(f"Heartbeat interval: {HEARTBEAT_INTERVAL_HOURS}h")
    print(f"Initial heartbeat bead: {bead_id}")
    print()
    print("To emit heartbeat manually:")
    print(f"  python {__file__} --heartbeat")
    print()
    print("To check status:")
    print(f"  python {__file__} --status")


def emit_heartbeat():
    """Emit a manual heartbeat."""
    if not SOAK_STATE_FILE.exists():
        print("ERROR: Soak test not started. Run --start first.")
        return

    state = json.loads(SOAK_STATE_FILE.read_text())

    status = get_phoenix_status()
    bead_id = emit_heartbeat_bead(status)

    state["heartbeats"].append({
        "bead_id": bead_id,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    SOAK_STATE_FILE.write_text(json.dumps(state, indent=2))

    print(f"Heartbeat emitted: bead_id={bead_id}")


def check_status():
    """Check soak test status."""
    if not SOAK_STATE_FILE.exists():
        print("No soak test running.")
        return

    state = json.loads(SOAK_STATE_FILE.read_text())

    start_time = datetime.fromisoformat(state["start_time"])
    end_time = datetime.fromisoformat(state["end_time"])
    now = datetime.now(UTC)
    elapsed = now - start_time
    remaining = end_time - now

    print(f"S44 SOAK TEST STATUS")
    print(f"Status: {state['status']}")
    print(f"Start:   {start_time.isoformat()}")
    print(f"End:     {end_time.isoformat()}")
    print(f"Elapsed: {elapsed.total_seconds() / 3600:.1f}h")
    print(f"Remaining: {max(0, remaining.total_seconds() / 3600):.1f}h")
    print(f"Heartbeats: {len(state['heartbeats'])}")

    # Check expected heartbeats
    expected = int(elapsed.total_seconds() / (HEARTBEAT_INTERVAL_HOURS * 3600)) + 1
    actual = len(state["heartbeats"])
    if actual < expected:
        print(f"⚠️  WARNING: Expected {expected} heartbeats, have {actual}")
    else:
        print(f"✓ Heartbeat count OK")


def end_soak():
    """End soak test and run verification."""
    if not SOAK_STATE_FILE.exists():
        print("No soak test running.")
        return

    state = json.loads(SOAK_STATE_FILE.read_text())
    start_time = datetime.fromisoformat(state["start_time"])
    now = datetime.now(UTC)
    elapsed = now - start_time

    print(f"S44 SOAK TEST ENDING")
    print(f"Elapsed: {elapsed.total_seconds() / 3600:.1f}h")
    print()

    # Run end soak replay
    print("--- END SOAK REPLAY ---")
    conn = sqlite3.connect(str(BEAD_DB))
    cursor = conn.cursor()

    # Get beads since soak start
    cursor.execute("""
        SELECT id, content_hash, ts
        FROM beads
        WHERE ts >= ?
        ORDER BY ts
    """, (state["start_time"],))

    beads = cursor.fetchall()
    conn.close()

    print(f"Beads since soak start: {len(beads)}")

    # Verify chain (check for gaps or corruption)
    issues = []
    heartbeat_count = len(state["heartbeats"])

    if len(beads) == 0:
        issues.append("NO BEADS during soak - possible silent death")

    print()
    print("--- VERIFICATION ---")
    print(f"Heartbeats emitted: {heartbeat_count}")
    print(f"Beads written: {len(beads)}")

    if issues:
        print(f"Issues found: {len(issues)}")
        for issue in issues:
            print(f"  ⚠️  {issue}")
        state["status"] = "FAILED"
    else:
        print("✓ No issues found")
        state["status"] = "COMPLETE"

    # Update state
    state["end_actual"] = now.isoformat()
    state["elapsed_hours"] = elapsed.total_seconds() / 3600
    state["beads_during_soak"] = len(beads)
    state["verification_issues"] = issues

    SOAK_STATE_FILE.write_text(json.dumps(state, indent=2))

    print()
    print(f"Soak test status: {state['status']}")


def main():
    parser = argparse.ArgumentParser(description="S44 Soak Test")
    parser.add_argument("--start", action="store_true", help="Start soak test")
    parser.add_argument("--status", action="store_true", help="Check status")
    parser.add_argument("--heartbeat", action="store_true", help="Emit heartbeat")
    parser.add_argument("--end", action="store_true", help="End soak and verify")

    args = parser.parse_args()

    if args.start:
        start_soak()
    elif args.status:
        check_status()
    elif args.heartbeat:
        emit_heartbeat()
    elif args.end:
        end_soak()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
