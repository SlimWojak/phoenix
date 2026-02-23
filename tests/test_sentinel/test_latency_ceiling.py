"""
S52 T2: Sentinel latency ceiling — < 2ms per check.

CTO ADDENDUM 2_T2_LATENCY_CEILING:
  sentinel_check_latency < 2ms. Prevents invisible latency creep.
  Proves Sovereign Tax is bounded.

INV-SENTINEL-LATENCY-1: sentinel_check_latency < 2ms.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest

from governance.lease import (
    LeaseInterpreter,
    LeaseStateMachine,
    NullBeadEmitter,
    create_lease_from_cartridge,
)
from governance.sentinel import BoundsSentinel, GovernanceVerdict


def _make_active_interpreter() -> LeaseInterpreter:
    lease = create_lease_from_cartridge(
        cartridge_ref="TEST_LATENCY_v1.0.0",
        cartridge_hash="abc",
        created_by="TEST",
        starts_at=datetime.now(UTC),
        duration_days=7,
        bounds={
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "daily_loss_limit_pct": 2.0,
            "allowed_pairs": ["EURUSD"],
            "allowed_pairs_mode": "ALL",
        },
    )
    emitter = NullBeadEmitter()
    sm = LeaseStateMachine(lease=lease, bead_emitter=emitter)
    sm.activate()
    return LeaseInterpreter(sm)


class TestLatencyCeiling:
    """INV-SENTINEL-LATENCY-1: sentinel_check_latency < 2ms."""

    @pytest.mark.parametrize("iteration", range(10))
    def test_sentinel_under_2ms(self, iteration: int):
        """Each sentinel check completes in < 2ms."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0 + iteration * 0.1,
                "consecutive_losses": iteration,
                "daily_loss_pct": 0.5,
            }
        )

        assert result.check_latency_ms < 2.0, (
            f"Sentinel check took {result.check_latency_ms:.3f}ms, "
            f"exceeds 2ms ceiling (iteration {iteration})"
        )

    def test_breach_check_under_2ms(self):
        """Even a breach check completes in < 2ms."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 10.0,
                "consecutive_losses": 5,
                "daily_loss_pct": 5.0,
            }
        )

        assert result.verdict == GovernanceVerdict.FAIL_BOUNDS_BREACH
        assert (
            result.check_latency_ms < 2.0
        ), f"Breach check took {result.check_latency_ms:.3f}ms, exceeds 2ms ceiling"

    def test_sustained_throughput(self):
        """100 consecutive checks average < 1ms each."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        start = time.perf_counter_ns()
        for _ in range(100):
            sentinel.intercept(
                {
                    "current_drawdown_pct": 1.0,
                    "consecutive_losses": 0,
                }
            )
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

        avg_ms = elapsed_ms / 100
        assert avg_ms < 1.0, f"Average sentinel check {avg_ms:.3f}ms, exceeds 1ms target"

    def test_max_latency_tracked(self):
        """Sentinel tracks max latency in metrics."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        for _ in range(5):
            sentinel.intercept(
                {
                    "current_drawdown_pct": 1.0,
                    "consecutive_losses": 0,
                }
            )

        metrics = sentinel.get_metrics()
        assert metrics["max_latency_ms"] > 0
        assert metrics["max_latency_ms"] < 2.0
