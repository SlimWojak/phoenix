"""
Tests for Lease State Machine
=============================

Sprint: S47 LEASE_IMPLEMENTATION
EXIT_GATE_S47_1: Lease FSM transitions correctly (all 5 terminal states)
EXIT_GATE_S47_6: All lease transitions emit beads with provenance

Tests:
  - Valid transitions (DRAFT→ACTIVE, ACTIVE→EXPIRED, etc.)
  - Invalid transitions rejected
  - State lock hash verification (INV-STATE-LOCK)
  - Bead emission on all transitions
"""

from datetime import UTC, datetime, timedelta

import pytest

from governance.lease import (
    TERMINAL_STATES,
    VALID_TRANSITIONS,
    LeaseStateMachine,
    NullBeadEmitter,
)
from governance.lease_types import (
    AllowedMode,
    Lease,
    LeaseActivationBead,
    LeaseBounds,
    LeaseDuration,
    LeaseExpiryBead,
    LeaseHaltBead,
    LeaseIdentity,
    LeaseRevocationBead,
    LeaseState,
    LeaseSubject,
    StateLockBead,
    TransitionResult,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def basic_lease() -> Lease:
    """Create a basic DRAFT lease for testing."""
    now = datetime.now(UTC)
    return Lease(
        identity=LeaseIdentity(
            created_at=now,
            created_by="test_user",
        ),
        subject=LeaseSubject(
            strategy_ref="TEST_STRAT_v1.0.0",
            strategy_hash="abc123def456",
        ),
        duration=LeaseDuration(
            starts_at=now,
            expires_at=now + timedelta(days=7),
            duration_days=7,
        ),
        bounds=LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EUR/USD", "GBP/USD"],
            allowed_pairs_mode=AllowedMode.SUBSET,
        ),
    )


@pytest.fixture
def emitter() -> NullBeadEmitter:
    """Create a test bead emitter."""
    return NullBeadEmitter()


# =============================================================================
# STATE MACHINE TESTS — Valid Transitions
# =============================================================================


class TestValidTransitions:
    """Test valid state transitions."""

    def test_draft_to_active(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Test DRAFT → ACTIVE transition."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        assert fsm.state == LeaseState.DRAFT
        assert not fsm.is_active

        result = fsm.activate()

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.ACTIVE
        assert fsm.is_active
        assert basic_lease.status.activated_at is not None

    def test_active_to_expired(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Test ACTIVE → EXPIRED transition."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        result = fsm.expire(final_stats={"trades": 5, "win_rate": 0.6})

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.EXPIRED
        assert fsm.is_terminal

    def test_active_to_revoked(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Test ACTIVE → REVOKED transition."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        result = fsm.revoke(revoked_by="admin", reason="Strategy underperforming")

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.REVOKED
        assert fsm.is_terminal
        assert basic_lease.status.revoked_at is not None
        assert basic_lease.status.revocation_reason == "Strategy underperforming"

    def test_active_to_halted(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Test ACTIVE → HALTED transition."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        result = fsm.halt(
            trigger="BOUNDS_BREACH",
            bound_exceeded="max_drawdown_pct",
            value=6.5,
        )

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED
        assert not fsm.is_terminal  # HALTED is not terminal, can go to REVOKED
        assert basic_lease.status.halted_at is not None
        assert basic_lease.status.halt_trigger == "BOUNDS_BREACH"

    def test_halted_to_revoked(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Test HALTED → REVOKED transition (the only way out of HALTED)."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        fsm.halt(trigger="TEST", bound_exceeded="test", value=0)

        assert fsm.state == LeaseState.HALTED

        result = fsm.revoke(revoked_by="admin", reason="Confirming halt")

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.REVOKED
        assert fsm.is_terminal


# =============================================================================
# STATE MACHINE TESTS — Invalid Transitions
# =============================================================================


class TestInvalidTransitions:
    """Test invalid state transitions are rejected."""

    def test_draft_cannot_expire(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """DRAFT cannot transition to EXPIRED."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        result = fsm.expire()

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.DRAFT

    def test_draft_cannot_revoke(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """DRAFT cannot be revoked (must activate first)."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        result = fsm.revoke(revoked_by="admin", reason="test")

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.DRAFT

    def test_draft_cannot_halt(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """DRAFT cannot be halted."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        result = fsm.halt(trigger="TEST", bound_exceeded="test", value=0)

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.DRAFT

    def test_expired_is_terminal(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """EXPIRED is terminal — no transitions allowed."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        fsm.expire()

        assert fsm.state == LeaseState.EXPIRED

        # Try all transitions
        assert fsm.activate() == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.expire() == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.revoke("admin", "test") == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.halt("TEST", "test", 0) == TransitionResult.REJECTED_INVALID_TRANSITION

    def test_revoked_is_terminal(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """REVOKED is terminal — no transitions allowed."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        fsm.revoke("admin", "test")

        assert fsm.state == LeaseState.REVOKED

        # Try all transitions
        assert fsm.activate() == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.expire() == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.revoke("admin", "test") == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.halt("TEST", "test", 0) == TransitionResult.REJECTED_INVALID_TRANSITION

    def test_halted_cannot_expire(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """HALTED cannot transition to EXPIRED (must be revoked)."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        fsm.halt(trigger="TEST", bound_exceeded="test", value=0)

        result = fsm.expire()

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.HALTED

    def test_halted_cannot_activate(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """HALTED cannot re-activate (no resurrection)."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        fsm.halt(trigger="TEST", bound_exceeded="test", value=0)

        result = fsm.activate()

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.HALTED

    def test_active_cannot_activate(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """ACTIVE cannot transition to ACTIVE."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        result = fsm.activate()

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.ACTIVE


# =============================================================================
# STATE LOCK TESTS — INV-STATE-LOCK
# =============================================================================


class TestStateLock:
    """Test state lock hash verification (INV-STATE-LOCK)."""

    def test_activate_with_valid_hash(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Activation works without prior hash (first transition)."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        result = fsm.activate(expected_hash=None)

        assert result == TransitionResult.SUCCESS

    def test_expire_with_valid_hash(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Expiry works with correct prior hash."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        # Get current hash after activation
        current_hash = basic_lease.governance.state_lock_hash

        result = fsm.expire(expected_hash=current_hash)

        assert result == TransitionResult.SUCCESS

    def test_expire_with_invalid_hash(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Expiry rejected with wrong hash."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        result = fsm.expire(expected_hash="wrong_hash_12345")

        assert result == TransitionResult.REJECTED_HASH_MISMATCH
        assert fsm.state == LeaseState.ACTIVE  # State unchanged

    def test_revoke_with_invalid_hash(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Revocation rejected with wrong hash."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        result = fsm.revoke(
            revoked_by="admin",
            reason="test",
            expected_hash="wrong_hash",
        )

        assert result == TransitionResult.REJECTED_HASH_MISMATCH
        assert fsm.state == LeaseState.ACTIVE

    def test_halt_bypasses_hash_check(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """
        Halt bypasses hash check.

        INV-HALT-OVERRIDES-LEASE: Halt must succeed regardless of race.
        """
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()

        # Halt with wrong hash — should still succeed
        result = fsm.halt(
            trigger="EMERGENCY",
            bound_exceeded="global",
            value=0,
            expected_hash="completely_wrong_hash",
        )

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED


# =============================================================================
# BEAD EMISSION TESTS — EXIT_GATE_S47_6
# =============================================================================


class TestBeadEmission:
    """Test that all transitions emit appropriate beads."""

    def test_activate_emits_beads(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Activation emits StateLockBead and LeaseActivationBead."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        fsm.activate()

        assert len(emitter.beads) == 2

        # First: StateLockBead
        state_bead = emitter.beads[0]
        assert isinstance(state_bead, StateLockBead)
        assert state_bead.prior_state == LeaseState.DRAFT
        assert state_bead.requested_transition == "DRAFT→ACTIVE"
        assert state_bead.transition_result == TransitionResult.SUCCESS

        # Second: LeaseActivationBead
        activation_bead = emitter.beads[1]
        assert isinstance(activation_bead, LeaseActivationBead)
        assert activation_bead.strategy_ref == "TEST_STRAT_v1.0.0"
        assert "max_drawdown_pct" in activation_bead.bounds_snapshot

    def test_expire_emits_beads(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Expiry emits StateLockBead and LeaseExpiryBead."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        emitter.beads.clear()

        fsm.expire(final_stats={"trades": 10})

        assert len(emitter.beads) == 2

        state_bead = emitter.beads[0]
        assert isinstance(state_bead, StateLockBead)
        assert state_bead.requested_transition == "ACTIVE→EXPIRED"

        expiry_bead = emitter.beads[1]
        assert isinstance(expiry_bead, LeaseExpiryBead)
        assert expiry_bead.final_stats == {"trades": 10}

    def test_revoke_emits_beads(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Revocation emits StateLockBead and LeaseRevocationBead."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        emitter.beads.clear()

        fsm.revoke(revoked_by="admin", reason="Performance")

        assert len(emitter.beads) == 2

        revoke_bead = emitter.beads[1]
        assert isinstance(revoke_bead, LeaseRevocationBead)
        assert revoke_bead.revoked_by == "admin"
        assert revoke_bead.reason == "Performance"

    def test_halt_emits_beads(self, basic_lease: Lease, emitter: NullBeadEmitter):
        """Halt emits StateLockBead and LeaseHaltBead."""
        fsm = LeaseStateMachine(basic_lease, emitter)
        fsm.activate()
        emitter.beads.clear()

        fsm.halt(trigger="BOUNDS", bound_exceeded="drawdown", value=6.5)

        assert len(emitter.beads) == 2

        halt_bead = emitter.beads[1]
        assert isinstance(halt_bead, LeaseHaltBead)
        assert halt_bead.trigger == "BOUNDS"
        assert halt_bead.bound_exceeded == "drawdown"
        assert halt_bead.value == 6.5

    def test_rejected_transition_emits_state_lock_bead(
        self, basic_lease: Lease, emitter: NullBeadEmitter
    ):
        """Rejected transitions still emit StateLockBead for audit trail."""
        fsm = LeaseStateMachine(basic_lease, emitter)

        # Try invalid transition
        fsm.expire()

        assert len(emitter.beads) == 1

        state_bead = emitter.beads[0]
        assert isinstance(state_bead, StateLockBead)
        assert state_bead.transition_result == TransitionResult.REJECTED_INVALID_TRANSITION


# =============================================================================
# TRANSITION MAP COMPLETENESS
# =============================================================================


class TestTransitionMapCompleteness:
    """Verify the transition map is complete and correct."""

    def test_all_states_in_transition_map(self):
        """All LeaseState values should be keys in VALID_TRANSITIONS."""
        for state in LeaseState:
            assert state in VALID_TRANSITIONS

    def test_terminal_states_have_no_transitions(self):
        """Terminal states should have empty transition lists."""
        for state in TERMINAL_STATES:
            assert VALID_TRANSITIONS[state] == []

    def test_draft_only_goes_to_active(self):
        """DRAFT can only transition to ACTIVE."""
        assert VALID_TRANSITIONS[LeaseState.DRAFT] == [LeaseState.ACTIVE]

    def test_active_has_three_exits(self):
        """ACTIVE can transition to EXPIRED, REVOKED, or HALTED."""
        expected = {LeaseState.EXPIRED, LeaseState.REVOKED, LeaseState.HALTED}
        actual = set(VALID_TRANSITIONS[LeaseState.ACTIVE])
        assert actual == expected

    def test_halted_only_goes_to_revoked(self):
        """HALTED can only transition to REVOKED (no resurrection)."""
        assert VALID_TRANSITIONS[LeaseState.HALTED] == [LeaseState.REVOKED]
