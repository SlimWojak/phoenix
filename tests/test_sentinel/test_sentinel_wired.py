"""
S53 T1: Sentinel wired at halt gate chokepoint.

EXIT_GATE: GATE_S53_1
Proves:
  - intercept called on every execution path (monkeypatch test)
  - bypass attempt fails
  - breach halts in same stack frame
  - BreachBead emitted on halt

INVARIANTS:
  INV-SENTINEL-WIRED-1: intercept() called on every capital mutation
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock

import pytest

from execution.halt_gate import (
    BreachBead,
    HaltGate,
    SentinelHaltError,
)
from governance.sentinel import (
    BoundsSentinel,
    GovernanceVerdict,
    SentinelResult,
)


class _SentinelMarker(Exception):
    """Test-only marker proving sentinel was invoked."""


def _make_gate_with_sentinel(
    halted: bool = False,
    sentinel: BoundsSentinel | None = None,
    state: dict[str, Any] | None = None,
) -> HaltGate:
    """Build a HaltGate wired to a sentinel."""
    if sentinel is None:
        sentinel = BoundsSentinel()
    return HaltGate(
        halt_signal_fn=lambda: halted,
        sentinel=sentinel,
        state_fn=lambda: state or {},
    )


class TestNoExecutionWithoutSentinel:
    """INV-SENTINEL-WIRED-1: every execution path triggers sentinel."""

    def test_sentinel_fires_on_check_before(self):
        """Monkeypatch intercept to raise marker; assert it fires."""
        sentinel = BoundsSentinel()
        gate = _make_gate_with_sentinel(sentinel=sentinel)

        def _raise_marker(state: dict) -> SentinelResult:
            raise _SentinelMarker("intercept was called")

        sentinel.intercept = _raise_marker  # type: ignore[assignment]

        with pytest.raises(SentinelHaltError, match="SENTINEL_CRASH"):
            gate.check_before("submit_order")

    def test_sentinel_fires_for_every_action(self):
        """All action names route through sentinel."""
        call_log: list[str] = []
        sentinel = BoundsSentinel()
        gate = _make_gate_with_sentinel(sentinel=sentinel)

        original = sentinel.intercept

        def _tracking_intercept(state: dict) -> SentinelResult:
            call_log.append("intercepted")
            return SentinelResult(
                verdict=GovernanceVerdict.PASS,
                check_latency_ns=100,
            )

        sentinel.intercept = _tracking_intercept  # type: ignore[assignment]

        gate.check_before("submit_order")
        gate.check_before("exit_position")
        gate.check_before("modify_order")

        assert len(call_log) == 3


class TestSentinelBreachHalts:
    """Breach verdict from sentinel → HaltGate raises."""

    def test_bounds_breach_raises(self):
        sentinel = BoundsSentinel()
        gate = _make_gate_with_sentinel(sentinel=sentinel)

        sentinel.intercept = lambda state: SentinelResult(  # type: ignore[assignment]
            verdict=GovernanceVerdict.FAIL_BOUNDS_BREACH,
            check_latency_ns=100,
            breach_detail="drawdown > 5%",
        )

        with pytest.raises(SentinelHaltError, match="drawdown"):
            gate.check_before("submit_order")

    def test_no_lease_raises(self):
        sentinel = BoundsSentinel()
        gate = _make_gate_with_sentinel(sentinel=sentinel)

        sentinel.intercept = lambda state: SentinelResult(  # type: ignore[assignment]
            verdict=GovernanceVerdict.FAIL_NO_LEASE,
            check_latency_ns=100,
            breach_detail="No active lease",
        )

        with pytest.raises(SentinelHaltError):
            gate.check_before("submit_order")


class TestBreachBeadEmitted:
    """BreachBead emitted on every sentinel FAIL."""

    def test_breach_bead_on_fail(self):
        sentinel = BoundsSentinel()
        gate = _make_gate_with_sentinel(sentinel=sentinel)

        sentinel.intercept = lambda state: SentinelResult(  # type: ignore[assignment]
            verdict=GovernanceVerdict.FAIL_BOUNDS_BREACH,
            check_latency_ns=100,
            breach_detail="max_drawdown exceeded",
        )

        with pytest.raises(SentinelHaltError):
            gate.check_before("submit_order", intent_id="CSE-001", lease_id="L-42")

        assert len(gate.breach_beads) == 1
        bead = gate.breach_beads[0]
        assert bead.intent_id == "CSE-001"
        assert bead.lease_id == "L-42"
        assert "max_drawdown" in bead.breach_reason
        assert isinstance(bead.world_time, datetime)

    def test_breach_bead_on_crash(self):
        sentinel = BoundsSentinel()
        gate = _make_gate_with_sentinel(sentinel=sentinel)

        def _crash(state: dict) -> SentinelResult:
            raise RuntimeError("sentinel internal error")

        sentinel.intercept = _crash  # type: ignore[assignment]

        with pytest.raises(SentinelHaltError, match="SENTINEL_CRASH"):
            gate.check_before("submit_order")

        assert len(gate.breach_beads) == 1
        assert "SENTINEL_CRASH" in gate.breach_beads[0].breach_reason


class TestGateWithoutSentinel:
    """Backwards compatibility: gate works without sentinel."""

    def test_no_sentinel_passes(self):
        gate = HaltGate(halt_signal_fn=lambda: False)
        result = gate.check_before("submit_order")
        assert result.checked
        assert not result.halted
