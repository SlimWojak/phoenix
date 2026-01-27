#!/usr/bin/env python3
"""
TEST: CHECK_HALT YIELD POINTS
SPRINT: 26.TRACK_B
EXIT_GATE: Cooperative halt at yield points

PURPOSE:
  Prove check_halt() raises HaltException when called during halt.
  Validates cooperative yielding mechanism.
"""

import sys
from pathlib import Path

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    HaltException,
    HaltManager,
    HaltSignal,
)

# =============================================================================
# TESTS
# =============================================================================


def test_check_halt_raises_when_set():
    """check_halt() raises HaltException when signal set."""
    signal = HaltSignal()

    # Should not raise when clear
    signal.check()  # No exception
    print("\ncheck_halt() when clear: OK")

    # Set signal
    result = signal.set()

    # Should raise now
    try:
        signal.check()
        assert False, "Should have raised HaltException"
    except HaltException as e:
        print("check_halt() when set: HaltException raised")
        print(f"  halt_id: {e.halt_id}")
        assert e.halt_id == result.halt_id


def test_halt_manager_check_halt():
    """HaltManager.check_halt() works correctly."""
    manager = HaltManager(module_id="test")

    # Should not raise when clear
    manager.check_halt()  # No exception

    # Request halt
    result = manager.request_halt()

    # Should raise now
    try:
        manager.check_halt()
        assert False, "Should have raised HaltException"
    except HaltException as e:
        print("\nHaltManager.check_halt(): HaltException raised")
        assert e.halt_id == result.halt_id


def test_yield_points_in_loop():
    """Simulate yield points in a processing loop."""
    manager = HaltManager(module_id="processor")

    # Simulate long computation with yield points
    iterations_completed = 0
    total_iterations = 100
    halt_at = 50

    for i in range(total_iterations):
        # Yield point
        try:
            manager.check_halt()
        except HaltException:
            iterations_completed = i
            break

        # Simulate work
        _ = i**2

        # Trigger halt partway through
        if i == halt_at:
            manager.request_halt()

        iterations_completed = i + 1

    print("\nLoop with yield points:")
    print(f"  halt_at: {halt_at}")
    print(f"  iterations_completed: {iterations_completed}")

    # Should have stopped at halt point
    assert (
        iterations_completed == halt_at + 1
    ), f"Expected {halt_at + 1} iterations, got {iterations_completed}"


def test_halt_exception_contains_halt_id():
    """HaltException contains correct halt_id."""
    signal = HaltSignal()
    result = signal.set()

    try:
        signal.check()
    except HaltException as e:
        assert e.halt_id == result.halt_id
        assert "halt_id" in str(e)
        print(f"\nHaltException message: {e}")


def test_clear_allows_check_to_pass():
    """Clearing halt allows check_halt() to pass."""
    signal = HaltSignal()

    # Set and check
    signal.set()
    try:
        signal.check()
        assert False
    except HaltException:
        pass

    # Clear and check
    signal.clear()
    signal.check()  # Should not raise

    print("\nClear → check passes: VERIFIED")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CHECK_HALT YIELD POINTS TEST")
    print("=" * 60)

    try:
        test_check_halt_raises_when_set()
        test_halt_manager_check_halt()
        test_yield_points_in_loop()
        test_halt_exception_contains_halt_id()
        test_clear_allows_check_to_pass()

        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - check_halt() raises HaltException when set")
        print("  - Yield points interrupt long computation")
        print("  - HaltException contains halt_id")
        print("=" * 60)

        sys.exit(0)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
