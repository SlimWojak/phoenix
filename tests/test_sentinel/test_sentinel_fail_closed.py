"""
S53 T1: Sentinel fail-closed chaos vector.

EXIT_GATE: GATE_S53_1
Proves:
  - sentinel_crash_no_alert: RuntimeError in intercept → HALT (not continue)
  - unexpected exception halts (not swallowed)

INVARIANTS:
  INV-SENTINEL-FAIL-CLOSED-1: sentinel exception → HALT, never continue
"""

from __future__ import annotations

from typing import Any

import pytest

from execution.halt_gate import HaltGate, SentinelHaltError
from governance.sentinel import BoundsSentinel, SentinelResult


class TestSentinelCrashNoAlert:
    """Chaos vector: sentinel crashes → system HALTS."""

    def test_runtime_error_in_intercept_halts(self):
        """Inject RuntimeError → assert HALT, not continue."""
        sentinel = BoundsSentinel()
        gate = HaltGate(
            halt_signal_fn=lambda: False,
            sentinel=sentinel,
            state_fn=lambda: {},
        )

        def _crash(state: dict[str, Any]) -> SentinelResult:
            raise RuntimeError("simulated sentinel crash")

        sentinel.intercept = _crash  # type: ignore[assignment]

        with pytest.raises(SentinelHaltError, match="SENTINEL_CRASH"):
            gate.check_before("submit_order")

    def test_type_error_in_intercept_halts(self):
        """Any exception type → HALT."""
        sentinel = BoundsSentinel()
        gate = HaltGate(
            halt_signal_fn=lambda: False,
            sentinel=sentinel,
            state_fn=lambda: {},
        )

        def _type_crash(state: dict[str, Any]) -> SentinelResult:
            raise TypeError("bad argument")

        sentinel.intercept = _type_crash  # type: ignore[assignment]

        with pytest.raises(SentinelHaltError):
            gate.check_before("submit_order")

    def test_crash_emits_breach_bead(self):
        """Even on crash, a BreachBead is emitted for audit trail."""
        sentinel = BoundsSentinel()
        gate = HaltGate(
            halt_signal_fn=lambda: False,
            sentinel=sentinel,
            state_fn=lambda: {},
        )

        sentinel.intercept = lambda s: (_ for _ in ()).throw(  # type: ignore[assignment]
            RuntimeError("boom")
        )

        with pytest.raises(SentinelHaltError):
            gate.check_before("submit_order")

        assert len(gate.breach_beads) == 1
