"""
S52 CLOSURE: Sentinel Determinism Proof.

ADVISOR QUESTION:
  "If PositionTracker.update() is called and sentinel throws —
   does execution engine transition to HALTED deterministically
   in the SAME control flow? Not eventually. Not via callback. Same flow."

PROOF:
  sentinel.intercept(state) → enforce_bounds() → LeaseStateMachine.halt()
  All synchronous. Single call stack. Lease state is HALTED before intercept() returns.

  Call chain:
    governance/sentinel.py:134  intercept()
    governance/sentinel.py:159    → check_all_bounds() [sync]
    governance/sentinel.py:177    → enforce_bounds() [sync]
    governance/lease.py:466         → state_machine.halt() [sync, thread-locked]
    governance/lease.py:340           → lease.status.current = HALTED [immediate]
    governance/sentinel.py:179  return SentinelResult(FAIL_BOUNDS_BREACH)

  No async. No event loop. No deferred callback. Same stack frame.
"""

from __future__ import annotations

from datetime import UTC, datetime

from governance.lease import (
    LeaseInterpreter,
    LeaseStateMachine,
    NullBeadEmitter,
    create_lease_from_cartridge,
)
from governance.lease_types import LeaseState
from governance.sentinel import BoundsSentinel, GovernanceVerdict


def _make_system():
    """Create active lease + interpreter + sentinel."""
    lease = create_lease_from_cartridge(
        cartridge_ref="TEST_DETERMINISM_v1.0.0",
        cartridge_hash="abc",
        created_by="TEST",
        starts_at=datetime.now(UTC),
        duration_days=7,
        bounds={
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "allowed_pairs": ["EURUSD"],
            "allowed_pairs_mode": "ALL",
        },
    )
    emitter = NullBeadEmitter()
    sm = LeaseStateMachine(lease=lease, bead_emitter=emitter)
    sm.activate()
    interpreter = LeaseInterpreter(sm)
    sentinel = BoundsSentinel(lease_interpreter=interpreter)
    return lease, sm, interpreter, sentinel


class TestSentinelDeterminism:
    """Prove FAIL → HALT is synchronous in same control flow."""

    def test_halt_before_return(self):
        """
        PROOF: After intercept() returns FAIL_BOUNDS_BREACH,
        lease state is ALREADY HALTED. Not eventually — immediately.
        """
        lease, sm, interpreter, sentinel = _make_system()
        assert sm.state == LeaseState.ACTIVE

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 10.0,
                "consecutive_losses": 0,
            }
        )

        # PROOF POINT: verdict is FAIL
        assert result.verdict == GovernanceVerdict.FAIL_BOUNDS_BREACH

        # PROOF POINT: lease is ALREADY HALTED when intercept() returns
        # This proves halt happened synchronously in the same call stack
        assert sm.state == LeaseState.HALTED
        assert lease.status.current == LeaseState.HALTED
        assert lease.status.halt_trigger == "BOUNDS_BREACH"

    def test_halt_callback_fires_before_return(self):
        """
        PROOF: halt_callback fires synchronously during intercept().
        Not deferred. Not queued.
        """
        _, _, interpreter, _ = _make_system()
        callback_log = []
        sentinel = BoundsSentinel(
            lease_interpreter=interpreter,
            halt_callback=lambda msg: callback_log.append(msg),
        )

        sentinel.intercept(
            {
                "current_drawdown_pct": 10.0,
                "consecutive_losses": 0,
            }
        )

        # callback_log is populated BEFORE we inspect it (same flow)
        assert len(callback_log) == 1
        assert "SENTINEL_BOUNDS_BREACH" in callback_log[0]

    def test_no_halt_on_pass(self):
        """Control: passing state does NOT halt."""
        lease, sm, _, sentinel = _make_system()

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
            }
        )

        assert result.verdict == GovernanceVerdict.PASS
        assert sm.state == LeaseState.ACTIVE

    def test_halt_is_atomic_with_verdict(self):
        """
        If verdict says FAIL, lease is halted. If verdict says PASS, lease is active.
        No inconsistency possible between verdict and lease state.
        """
        lease, sm, interpreter, sentinel = _make_system()

        # Pass — state stays ACTIVE
        r1 = sentinel.intercept({"current_drawdown_pct": 1.0, "consecutive_losses": 0})
        assert r1.verdict == GovernanceVerdict.PASS
        assert sm.state == LeaseState.ACTIVE

        # Fail — state transitions to HALTED in same call
        r2 = sentinel.intercept({"current_drawdown_pct": 10.0, "consecutive_losses": 0})
        assert r2.verdict == GovernanceVerdict.FAIL_BOUNDS_BREACH
        assert sm.state == LeaseState.HALTED
