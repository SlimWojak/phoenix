"""
Tests for Lease Expiry
======================

Sprint: S47 LEASE_IMPLEMENTATION
EXIT_GATE_S47_4: Expiry triggers MARKET_CLOSE with 60s buffer

Tests:
  - INV-EXPIRY-BUFFER: Software halt N seconds BEFORE legal expiry
  - Effective expiry calculation
  - Expiry behavior (MARKET_CLOSE vs FREEZE_AND_WAIT)
  - Expiry check logic
"""

from datetime import UTC, datetime, timedelta

import pytest

from governance.lease import (
    LeaseInterpreter,
    LeaseStateMachine,
    NullBeadEmitter,
)
from governance.lease_types import (
    AllowedMode,
    ExpiryBehavior,
    Lease,
    LeaseBounds,
    LeaseDuration,
    LeaseIdentity,
    LeaseState,
    LeaseSubject,
    TransitionResult,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def lease_with_expiry(request) -> Lease:
    """Create a lease with customizable expiry settings."""
    now = datetime.now(UTC)

    # Get parameters or use defaults
    buffer_seconds = getattr(request, "param", {}).get("buffer_seconds", 60)
    duration_days = getattr(request, "param", {}).get("duration_days", 7)
    expiry_behavior = getattr(request, "param", {}).get(
        "expiry_behavior", ExpiryBehavior.MARKET_CLOSE
    )

    expires_at = now + timedelta(days=duration_days)

    lease = Lease(
        identity=LeaseIdentity(
            created_at=now,
            created_by="test_user",
        ),
        subject=LeaseSubject(
            strategy_ref="EXPIRY_TEST_v1.0.0",
            strategy_hash="abc123",
        ),
        duration=LeaseDuration(
            starts_at=now,
            expires_at=expires_at,
            duration_days=duration_days,
        ),
        bounds=LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EUR/USD"],
            allowed_pairs_mode=AllowedMode.SUBSET,
        ),
    )

    # Configure halt integration
    lease.halt_integration.governance_buffer_seconds = buffer_seconds
    lease.halt_integration.expiry_behavior = expiry_behavior

    return lease


@pytest.fixture
def active_lease() -> Lease:
    """Create an already-active lease for expiry testing."""
    now = datetime.now(UTC)
    lease = Lease(
        identity=LeaseIdentity(
            created_at=now,
            created_by="test_user",
        ),
        subject=LeaseSubject(
            strategy_ref="EXPIRY_TEST_v1.0.0",
            strategy_hash="abc123",
        ),
        duration=LeaseDuration(
            starts_at=now,
            expires_at=now + timedelta(days=7),
            duration_days=7,
        ),
        bounds=LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EUR/USD"],
            allowed_pairs_mode=AllowedMode.SUBSET,
        ),
    )

    # Activate
    lease.status.current = LeaseState.ACTIVE
    lease.status.activated_at = now

    return lease


# =============================================================================
# INV-EXPIRY-BUFFER TESTS — 60s buffer
# =============================================================================


class TestExpiryBuffer:
    """Test INV-EXPIRY-BUFFER: Software halt before legal expiry."""

    def test_default_buffer_is_60s(self, active_lease: Lease):
        """Default governance buffer is 60 seconds."""
        assert active_lease.halt_integration.governance_buffer_seconds == 60

    def test_effective_expiry_with_buffer(self, active_lease: Lease):
        """Effective expiry is legal expiry minus buffer."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        legal_expiry = active_lease.duration.expires_at
        effective_expiry = interpreter.get_effective_expiry()

        # Effective should be 60s before legal
        expected = legal_expiry - timedelta(seconds=60)
        assert effective_expiry == expected

    def test_custom_buffer(self, active_lease: Lease):
        """Custom buffer is respected."""
        active_lease.halt_integration.governance_buffer_seconds = 120  # 2 minutes

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        legal_expiry = active_lease.duration.expires_at
        effective_expiry = interpreter.get_effective_expiry()

        expected = legal_expiry - timedelta(seconds=120)
        assert effective_expiry == expected


# =============================================================================
# EXPIRY CHECK TESTS
# =============================================================================


class TestExpiryCheck:
    """Test expiry check logic."""

    def test_not_expired_before_effective(self, active_lease: Lease):
        """Lease not expired before effective expiry."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        # Check well before expiry
        early_time = datetime.now(UTC)
        assert interpreter.check_expiry(early_time) is False

    def test_expired_at_effective_expiry(self, active_lease: Lease):
        """Lease expires exactly at effective expiry."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        effective_expiry = interpreter.get_effective_expiry()
        assert interpreter.check_expiry(effective_expiry) is True

    def test_expired_after_effective_expiry(self, active_lease: Lease):
        """Lease expired after effective expiry."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        effective_expiry = interpreter.get_effective_expiry()
        after = effective_expiry + timedelta(seconds=1)

        assert interpreter.check_expiry(after) is True

    def test_not_expired_just_before_effective(self, active_lease: Lease):
        """Lease not expired 1ms before effective expiry."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        effective_expiry = interpreter.get_effective_expiry()
        just_before = effective_expiry - timedelta(milliseconds=1)

        assert interpreter.check_expiry(just_before) is False


# =============================================================================
# EXPIRY TRANSITION TESTS
# =============================================================================


class TestExpiryTransition:
    """Test expiry state transition."""

    def test_expire_from_active(self, active_lease: Lease):
        """Expiry transitions ACTIVE → EXPIRED."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)

        result = fsm.expire()

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.EXPIRED
        assert fsm.is_terminal

    def test_expire_with_final_stats(self, active_lease: Lease):
        """Expiry records final stats."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)

        stats = {
            "total_trades": 15,
            "winning_trades": 10,
            "losing_trades": 5,
            "total_pnl_pct": 3.2,
        }

        fsm.expire(final_stats=stats)

        # Check bead has stats
        expiry_bead = emitter.beads[-1]
        assert expiry_bead.final_stats == stats

    def test_cannot_expire_from_draft(self, active_lease: Lease):
        """Cannot expire from DRAFT state."""
        active_lease.status.current = LeaseState.DRAFT

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)

        result = fsm.expire()

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.DRAFT

    def test_cannot_expire_from_halted(self, active_lease: Lease):
        """Cannot expire from HALTED (must revoke)."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)

        # Halt first
        fsm.halt(trigger="TEST", bound_exceeded="test", value=0)

        # Try to expire
        result = fsm.expire()

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.state == LeaseState.HALTED


# =============================================================================
# EXPIRY BEHAVIOR TESTS
# =============================================================================


class TestExpiryBehavior:
    """Test expiry behavior configuration."""

    def test_default_behavior_is_market_close(self, active_lease: Lease):
        """Default expiry behavior is MARKET_CLOSE."""
        assert active_lease.halt_integration.expiry_behavior == ExpiryBehavior.MARKET_CLOSE

    def test_freeze_and_wait_behavior(self, active_lease: Lease):
        """FREEZE_AND_WAIT behavior is settable."""
        active_lease.halt_integration.expiry_behavior = ExpiryBehavior.FREEZE_AND_WAIT

        assert active_lease.halt_integration.expiry_behavior == ExpiryBehavior.FREEZE_AND_WAIT

    def test_behavior_recorded_on_lease(self, active_lease: Lease):
        """Expiry behavior is part of lease model."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        # Access behavior through interpreter
        behavior = interpreter.lease.halt_integration.expiry_behavior
        assert behavior in (ExpiryBehavior.MARKET_CLOSE, ExpiryBehavior.FREEZE_AND_WAIT)


# =============================================================================
# EDGE CASES
# =============================================================================


class TestExpiryEdgeCases:
    """Test expiry edge cases."""

    def test_zero_buffer(self, active_lease: Lease):
        """Zero buffer = effective expiry equals legal expiry."""
        active_lease.halt_integration.governance_buffer_seconds = 0

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        assert interpreter.get_effective_expiry() == active_lease.duration.expires_at

    def test_very_short_lease(self):
        """Very short lease (1 day) with buffer."""
        now = datetime.now(UTC)
        lease = Lease(
            identity=LeaseIdentity(
                created_at=now,
                created_by="test",
            ),
            subject=LeaseSubject(
                strategy_ref="SHORT_v1.0.0",
                strategy_hash="abc",
            ),
            duration=LeaseDuration(
                starts_at=now,
                expires_at=now + timedelta(days=1),
                duration_days=1,
            ),
            bounds=LeaseBounds(
                max_drawdown_pct=5.0,
                max_consecutive_losses=3,
                allowed_pairs=["EUR/USD"],
                allowed_pairs_mode=AllowedMode.SUBSET,
            ),
        )

        lease.status.current = LeaseState.ACTIVE

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        effective = interpreter.get_effective_expiry()
        expected = now + timedelta(days=1) - timedelta(seconds=60)

        assert effective == expected

    def test_expired_lease_stays_expired(self, active_lease: Lease):
        """Once expired, lease stays expired."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.expire()

        # Try various operations
        assert fsm.activate() == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.expire() == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.revoke("admin", "test") == TransitionResult.REJECTED_INVALID_TRANSITION
        assert fsm.halt("TEST", "test", 0) == TransitionResult.REJECTED_INVALID_TRANSITION

        # State unchanged
        assert fsm.state == LeaseState.EXPIRED
