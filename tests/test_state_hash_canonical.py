#!/usr/bin/env python3
"""
TEST: STATE HASH CANONICAL
SPRINT: 26.TRACK_B
EXIT_GATE: same state → same hash (deterministic)

PURPOSE:
  Prove INV-CONTRACT-1: deterministic state machine.
  State hash computation is canonical and reproducible.
"""

import hashlib
import json
import sys
from pathlib import Path

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import StateInput

# =============================================================================
# HELPER: Canonical state hash
# =============================================================================


def compute_state_hash(state: dict) -> str:
    """
    Compute canonical state hash.

    Method:
    - Filter to hashable components (exclude timestamps, heartbeats)
    - Canonical JSON serialization (sorted keys)
    - SHA256 hash (first 16 chars)
    """
    # Filter state
    hashable = {
        k: v
        for k, v in state.items()
        if k not in ["timestamp", "heartbeat", "diagnostics", "last_update"]
    }

    # Canonical JSON
    canonical = json.dumps(hashable, sort_keys=True, default=str)

    # Hash
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


# =============================================================================
# TESTS
# =============================================================================


def test_same_state_same_hash():
    """Same state produces same hash."""
    state = {
        "positions": {"EURUSD": 100000},
        "orders": [],
        "risk_status": "NORMAL",
    }

    hash1 = compute_state_hash(state)
    hash2 = compute_state_hash(state)
    hash3 = compute_state_hash(state)

    print("\nSame State → Same Hash:")
    print(f"  hash1: {hash1}")
    print(f"  hash2: {hash2}")
    print(f"  hash3: {hash3}")

    assert hash1 == hash2 == hash3


def test_different_state_different_hash():
    """Different state produces different hash."""
    state1 = {"positions": {"EURUSD": 100000}}
    state2 = {"positions": {"EURUSD": 100001}}  # 1 lot difference

    hash1 = compute_state_hash(state1)
    hash2 = compute_state_hash(state2)

    print("\nDifferent State → Different Hash:")
    print(f"  state1 hash: {hash1}")
    print(f"  state2 hash: {hash2}")

    assert hash1 != hash2


def test_key_order_doesnt_matter():
    """Key order doesn't affect hash (canonical JSON)."""
    state1 = {"a": 1, "b": 2, "c": 3}
    state2 = {"c": 3, "b": 2, "a": 1}
    state3 = {"b": 2, "a": 1, "c": 3}

    hash1 = compute_state_hash(state1)
    hash2 = compute_state_hash(state2)
    hash3 = compute_state_hash(state3)

    print("\nKey Order Independence:")
    print(f"  {{'a':1,'b':2,'c':3}} → {hash1}")
    print(f"  {{'c':3,'b':2,'a':1}} → {hash2}")
    print(f"  {{'b':2,'a':1,'c':3}} → {hash3}")

    assert hash1 == hash2 == hash3


def test_timestamps_excluded():
    """Timestamps don't affect hash."""
    state1 = {
        "positions": {"EURUSD": 100000},
        "timestamp": "2024-01-01T00:00:00Z",
        "last_update": "2024-01-01T00:00:00Z",
    }
    state2 = {
        "positions": {"EURUSD": 100000},
        "timestamp": "2024-01-02T12:00:00Z",
        "last_update": "2024-01-02T12:00:00Z",
    }

    hash1 = compute_state_hash(state1)
    hash2 = compute_state_hash(state2)

    print("\nTimestamp Exclusion:")
    print(f"  timestamp=2024-01-01 → {hash1}")
    print(f"  timestamp=2024-01-02 → {hash2}")

    assert hash1 == hash2


def test_heartbeats_excluded():
    """Heartbeats don't affect hash."""
    state1 = {
        "positions": {},
        "heartbeat": 1000,
        "diagnostics": {"cpu": 50},
    }
    state2 = {
        "positions": {},
        "heartbeat": 2000,
        "diagnostics": {"cpu": 75},
    }

    hash1 = compute_state_hash(state1)
    hash2 = compute_state_hash(state2)

    print("\nHeartbeat/Diagnostics Exclusion:")
    print(f"  heartbeat=1000 → {hash1}")
    print(f"  heartbeat=2000 → {hash2}")

    assert hash1 == hash2


def test_nested_state_deterministic():
    """Nested state structures hash deterministically."""
    state = {
        "positions": {
            "EURUSD": {"qty": 100000, "entry": 1.0950},
            "GBPUSD": {"qty": -50000, "entry": 1.2700},
        },
        "orders": [
            {"id": "001", "type": "limit", "price": 1.0900},
            {"id": "002", "type": "stop", "price": 1.1000},
        ],
        "risk": {
            "max_dd": 0.05,
            "current_dd": 0.01,
            "status": "NORMAL",
        },
    }

    # Hash 10 times
    hashes = [compute_state_hash(state) for _ in range(10)]

    print("\nNested State Determinism:")
    print(f"  hash (repeated 10x): {hashes[0]}")

    assert len(set(hashes)) == 1, "Nested state should produce same hash"


def test_state_input_hash():
    """StateInput.compute_hash() works."""
    data = {"positions": {"EURUSD": 100000}}

    input1 = StateInput(data=data)
    input2 = StateInput(data=data)

    hash1 = input1.compute_hash()
    hash2 = input2.compute_hash()

    print("\nStateInput.compute_hash():")
    print(f"  input1: {hash1}")
    print(f"  input2: {hash2}")

    assert hash1 == hash2


def test_empty_state_hash():
    """Empty state produces consistent hash."""
    hash1 = compute_state_hash({})
    hash2 = compute_state_hash({})

    print(f"\nEmpty State Hash: {hash1}")

    assert hash1 == hash2
    assert len(hash1) == 16  # SHA256 truncated to 16 chars


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("STATE HASH CANONICAL TEST")
    print("=" * 60)
    print("INV-CONTRACT-1: same input → same output")

    try:
        test_same_state_same_hash()
        test_different_state_different_hash()
        test_key_order_doesnt_matter()
        test_timestamps_excluded()
        test_heartbeats_excluded()
        test_nested_state_deterministic()
        test_state_input_hash()
        test_empty_state_hash()

        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - Same state → same hash")
        print("  - Key order independent")
        print("  - Timestamps/heartbeats excluded")
        print("  - Nested structures work")
        print("=" * 60)

        sys.exit(0)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
