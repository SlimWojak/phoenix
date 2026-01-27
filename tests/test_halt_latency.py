#!/usr/bin/env python3
"""
TEST: HALT LATENCY
SPRINT: 26.TRACK_B
EXIT_GATE: request_halt() < 50ms (p99)

PURPOSE:
  Prove halt_local_latency < 50ms mechanically.
  This is INV-HALT-1 — a HARD invariant.

METHOD:
  - Measure ONLY request_halt() path
  - NO IO, NO logging, NO propagation in measurement
  - Statistical proof: p99 < 50ms over 1000 iterations
"""

import statistics
import sys
import time
from pathlib import Path

# Add phoenix to path
PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import HaltManager, HaltSignal

# =============================================================================
# TEST CONFIGURATION
# =============================================================================

ITERATIONS = 1000
LATENCY_THRESHOLD_MS = 50.0  # INV-HALT-1


# =============================================================================
# TESTS
# =============================================================================


def test_halt_signal_latency():
    """Test raw HaltSignal.set() latency."""
    latencies = []

    for _ in range(ITERATIONS):
        signal = HaltSignal()

        start = time.perf_counter_ns()
        result = signal.set()
        end = time.perf_counter_ns()

        latency_ms = (end - start) / 1_000_000
        latencies.append(latency_ms)

        # Also verify the result reports correct latency
        assert result.success is True
        assert result.halt_id is not None

    # Statistical analysis
    p50 = statistics.median(latencies)
    p99 = statistics.quantiles(latencies, n=100)[98]  # 99th percentile
    p_max = max(latencies)

    print(f"\nHaltSignal.set() latency (n={ITERATIONS}):")
    print(f"  p50: {p50:.3f} ms")
    print(f"  p99: {p99:.3f} ms")
    print(f"  max: {p_max:.3f} ms")

    # Assert p99 < 50ms
    assert (
        p99 < LATENCY_THRESHOLD_MS
    ), f"FAIL: p99 latency {p99:.3f}ms >= {LATENCY_THRESHOLD_MS}ms threshold"

    return {
        "p50": p50,
        "p99": p99,
        "max": p_max,
        "iterations": ITERATIONS,
        "threshold": LATENCY_THRESHOLD_MS,
        "passed": True,
    }


def test_halt_manager_request_halt_latency():
    """Test HaltManager.request_halt() latency."""
    latencies = []

    for i in range(ITERATIONS):
        manager = HaltManager(module_id=f"test_module_{i}")

        start = time.perf_counter_ns()
        result = manager.request_halt()
        end = time.perf_counter_ns()

        latency_ms = (end - start) / 1_000_000
        latencies.append(latency_ms)

        # Verify result
        assert result.success is True
        assert result.halt_id is not None
        assert result.latency_ms < LATENCY_THRESHOLD_MS

    # Statistical analysis
    p50 = statistics.median(latencies)
    p99 = statistics.quantiles(latencies, n=100)[98]
    p_max = max(latencies)

    print(f"\nHaltManager.request_halt() latency (n={ITERATIONS}):")
    print(f"  p50: {p50:.3f} ms")
    print(f"  p99: {p99:.3f} ms")
    print(f"  max: {p_max:.3f} ms")

    # Assert p99 < 50ms
    assert (
        p99 < LATENCY_THRESHOLD_MS
    ), f"FAIL: p99 latency {p99:.3f}ms >= {LATENCY_THRESHOLD_MS}ms threshold"

    return {
        "p50": p50,
        "p99": p99,
        "max": p_max,
        "iterations": ITERATIONS,
        "threshold": LATENCY_THRESHOLD_MS,
        "passed": True,
    }


def test_halt_signal_reported_latency_accurate():
    """Verify HaltSignalSetResult.latency_ms is accurate."""
    for _ in range(100):
        signal = HaltSignal()

        start = time.perf_counter_ns()
        result = signal.set()
        end = time.perf_counter_ns()

        external_latency = (end - start) / 1_000_000

        # Reported latency should be close to measured
        # Allow 0.5ms tolerance for measurement overhead
        assert (
            abs(result.latency_ms - external_latency) < 0.5
        ), f"Reported {result.latency_ms:.3f}ms != measured {external_latency:.3f}ms"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HALT LATENCY TEST")
    print("=" * 60)
    print(f"INV-HALT-1: request_halt() < {LATENCY_THRESHOLD_MS}ms (p99)")
    print(f"ITERATIONS: {ITERATIONS}")

    try:
        result1 = test_halt_signal_latency()
        result2 = test_halt_manager_request_halt_latency()
        test_halt_signal_reported_latency_accurate()

        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print(f"  HaltSignal p99: {result1['p99']:.3f} ms < {LATENCY_THRESHOLD_MS} ms")
        print(f"  HaltManager p99: {result2['p99']:.3f} ms < {LATENCY_THRESHOLD_MS} ms")
        print("=" * 60)

        sys.exit(0)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
