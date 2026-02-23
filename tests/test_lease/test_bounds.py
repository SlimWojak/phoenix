"""
Tests for Lease Bounds Checking
===============================

Sprint: S47 LEASE_IMPLEMENTATION
EXIT_GATE_S47_2: Bounds check — any breach = halt (OR logic)

Tests:
  - Drawdown breach detection
  - Consecutive loss breach detection
  - Daily loss limit breach detection
  - OR logic: any single breach triggers halt
  - Pair/session filtering
  - Position size cap validation
  - INV-LEASE-CEILING: bounds can only tighten
"""

from datetime import UTC, datetime, timedelta

import pytest

from governance.cartridge import create_minimal_cartridge
from governance.insertion import validate_bounds_ceiling
from governance.lease import (
    LeaseInterpreter,
    LeaseStateMachine,
    NullBeadEmitter,
)
from governance.lease_types import (
    AllowedMode,
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
def active_lease() -> Lease:
    """Create an already-active lease for bounds testing."""
    now = datetime.now(UTC)
    lease = Lease(
        identity=LeaseIdentity(
            created_at=now,
            created_by="test_user",
        ),
        subject=LeaseSubject(
            strategy_ref="BOUNDS_TEST_v1.0.0",
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
            allowed_pairs=["EUR/USD", "GBP/USD"],
            allowed_pairs_mode=AllowedMode.SUBSET,
            allowed_sessions=["london", "new_york"],
            allowed_sessions_mode=AllowedMode.SUBSET,
            position_size_cap=1.0,
            daily_loss_limit_pct=2.0,
        ),
    )

    # Manually set to ACTIVE for bounds testing
    lease.status.current = LeaseState.ACTIVE
    lease.status.activated_at = now

    return lease


@pytest.fixture
def interpreter(active_lease: Lease) -> LeaseInterpreter:
    """Create interpreter with active lease."""
    emitter = NullBeadEmitter()
    fsm = LeaseStateMachine(active_lease, emitter)
    return LeaseInterpreter(fsm)


# =============================================================================
# BREACH DETECTION TESTS
# =============================================================================


class TestBreachDetection:
    """Test bounds breach detection."""

    def test_no_breach_when_within_bounds(self, interpreter: LeaseInterpreter):
        """No breach when all values within bounds."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=2.0,  # < 5.0
            consecutive_losses=1,  # < 3
            daily_loss_pct=0.5,  # < 2.0
        )

        assert breaches == []

    def test_drawdown_breach(self, interpreter: LeaseInterpreter):
        """Detect drawdown breach."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=6.5,  # > 5.0
            consecutive_losses=0,
        )

        assert len(breaches) == 1
        assert breaches[0].bound_name == "max_drawdown_pct"
        assert breaches[0].current_value == 6.5
        assert breaches[0].limit == 5.0

    def test_consecutive_losses_breach(self, interpreter: LeaseInterpreter):
        """Detect consecutive losses breach."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=1.0,
            consecutive_losses=5,  # > 3
        )

        assert len(breaches) == 1
        assert breaches[0].bound_name == "max_consecutive_losses"
        assert breaches[0].current_value == 5
        assert breaches[0].limit == 3

    def test_daily_loss_breach(self, interpreter: LeaseInterpreter):
        """Detect daily loss limit breach."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=1.0,
            consecutive_losses=0,
            daily_loss_pct=3.5,  # > 2.0
        )

        assert len(breaches) == 1
        assert breaches[0].bound_name == "daily_loss_limit_pct"
        assert breaches[0].current_value == 3.5
        assert breaches[0].limit == 2.0

    def test_multiple_breaches(self, interpreter: LeaseInterpreter):
        """Detect multiple simultaneous breaches."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=10.0,  # > 5.0
            consecutive_losses=5,  # > 3
            daily_loss_pct=3.0,  # > 2.0
        )

        assert len(breaches) == 3


# =============================================================================
# OR LOGIC TESTS — EXIT_GATE_S47_2
# =============================================================================


class TestOrLogic:
    """Test OR logic: any single breach triggers halt."""

    def test_single_breach_triggers_halt(self, active_lease: Lease):
        """A single breach should trigger halt."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm._lease.status.current = LeaseState.ACTIVE  # Bypass activation
        interpreter = LeaseInterpreter(fsm)

        result = interpreter.enforce_bounds(
            current_drawdown_pct=7.0,  # BREACH
            consecutive_losses=0,  # OK
            daily_loss_pct=0.1,  # OK
        )

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED

    def test_no_breach_no_halt(self, active_lease: Lease):
        """No breach = no halt triggered."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm._lease.status.current = LeaseState.ACTIVE
        interpreter = LeaseInterpreter(fsm)

        result = interpreter.enforce_bounds(
            current_drawdown_pct=1.0,  # OK
            consecutive_losses=1,  # OK
            daily_loss_pct=0.5,  # OK
        )

        assert result is None
        assert fsm.state == LeaseState.ACTIVE

    def test_first_breach_triggers_halt(self, active_lease: Lease):
        """When multiple breaches, first one triggers halt."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm._lease.status.current = LeaseState.ACTIVE
        interpreter = LeaseInterpreter(fsm)

        result = interpreter.enforce_bounds(
            current_drawdown_pct=10.0,  # BREACH
            consecutive_losses=5,  # BREACH
            daily_loss_pct=5.0,  # BREACH
        )

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED

        # Halt bead shows first breach
        halt_bead = emitter.beads[-1]
        assert halt_bead.bound_exceeded == "max_drawdown_pct"


# =============================================================================
# FILTERING TESTS
# =============================================================================


class TestFiltering:
    """Test pair/session filtering."""

    def test_allowed_pair(self, interpreter: LeaseInterpreter):
        """Pairs in allowed list return True."""
        assert interpreter.is_pair_allowed("EUR/USD") is True
        assert interpreter.is_pair_allowed("GBP/USD") is True

    def test_disallowed_pair(self, interpreter: LeaseInterpreter):
        """Pairs not in allowed list return False."""
        assert interpreter.is_pair_allowed("USD/JPY") is False
        assert interpreter.is_pair_allowed("AUD/USD") is False

    def test_allowed_session(self, interpreter: LeaseInterpreter):
        """Sessions in allowed list return True."""
        assert interpreter.is_session_allowed("london") is True
        assert interpreter.is_session_allowed("new_york") is True

    def test_disallowed_session(self, interpreter: LeaseInterpreter):
        """Sessions not in allowed list return False."""
        assert interpreter.is_session_allowed("tokyo") is False
        assert interpreter.is_session_allowed("sydney") is False

    def test_all_mode_allows_everything(self, active_lease: Lease):
        """AllowedMode.ALL allows any pair/session."""
        active_lease.bounds.allowed_pairs_mode = AllowedMode.ALL
        active_lease.bounds.allowed_sessions_mode = AllowedMode.ALL

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        # Any pair/session should be allowed
        assert interpreter.is_pair_allowed("ANY/PAIR") is True
        assert interpreter.is_session_allowed("any_session") is True


# =============================================================================
# POSITION SIZE TESTS
# =============================================================================


class TestPositionSize:
    """Test position size cap validation."""

    def test_position_within_cap(self, interpreter: LeaseInterpreter):
        """Position within cap returns True."""
        assert interpreter.check_position_size(0.5) is True
        assert interpreter.check_position_size(1.0) is True

    def test_position_exceeds_cap(self, interpreter: LeaseInterpreter):
        """Position exceeding cap returns False."""
        assert interpreter.check_position_size(1.5) is False
        assert interpreter.check_position_size(2.0) is False

    def test_no_cap_allows_anything(self, active_lease: Lease):
        """No position size cap allows any size."""
        active_lease.bounds.position_size_cap = None

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        assert interpreter.check_position_size(100.0) is True


# =============================================================================
# INV-LEASE-CEILING TESTS
# =============================================================================


class TestLeaseCeiling:
    """Test INV-LEASE-CEILING: bounds can only tighten, never loosen."""

    def test_valid_tightening(self):
        """Lease bounds tighter than cartridge defaults = valid."""
        cartridge = create_minimal_cartridge(
            name="CEILING_TEST",
            version="1.0.0",
            author="test",
            pairs=["EUR/USD", "GBP/USD", "USD/JPY"],
            per_trade_pct=2.0,
        )

        # Lease with tighter bounds (fewer pairs, smaller position)
        lease_bounds = LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EUR/USD"],  # Subset of cartridge pairs
            allowed_pairs_mode=AllowedMode.SUBSET,
            position_size_cap=1.0,  # < cartridge's 2.0%
        )

        violations = validate_bounds_ceiling(cartridge, lease_bounds)

        assert violations == []

    def test_position_size_exceeds_cartridge(self):
        """Lease position size > cartridge default = violation."""
        cartridge = create_minimal_cartridge(
            name="CEILING_TEST",
            version="1.0.0",
            author="test",
            pairs=["EUR/USD"],
            per_trade_pct=1.0,  # Cartridge default
        )

        lease_bounds = LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EUR/USD"],
            allowed_pairs_mode=AllowedMode.SUBSET,
            position_size_cap=2.0,  # > cartridge's 1.0% — VIOLATION
        )

        violations = validate_bounds_ceiling(cartridge, lease_bounds)

        assert len(violations) == 1
        assert "position_size_cap" in violations[0]

    def test_pairs_not_in_cartridge(self):
        """Lease pairs not in cartridge = violation."""
        cartridge = create_minimal_cartridge(
            name="CEILING_TEST",
            version="1.0.0",
            author="test",
            pairs=["EUR/USD", "GBP/USD"],
        )

        lease_bounds = LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EUR/USD", "USD/JPY"],  # USD/JPY not in cartridge
            allowed_pairs_mode=AllowedMode.SUBSET,
        )

        violations = validate_bounds_ceiling(cartridge, lease_bounds)

        assert len(violations) == 1
        assert "USD/JPY" in violations[0]


# =============================================================================
# EDGE CASES
# =============================================================================


class TestBoundsEdgeCases:
    """Test edge cases in bounds checking."""

    def test_exact_boundary_no_breach(self, interpreter: LeaseInterpreter):
        """Exactly at boundary = not a breach (must exceed)."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=5.0,  # == 5.0 (at boundary)
            consecutive_losses=3,  # == 3 (at boundary)
            daily_loss_pct=2.0,  # == 2.0 (at boundary)
        )

        assert breaches == []

    def test_barely_over_boundary(self, interpreter: LeaseInterpreter):
        """Just over boundary = breach."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=5.01,  # > 5.0
            consecutive_losses=3,
        )

        assert len(breaches) == 1

    def test_inactive_lease_no_breach(self, active_lease: Lease):
        """Inactive lease returns no breaches."""
        active_lease.status.current = LeaseState.DRAFT  # Not active

        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        interpreter = LeaseInterpreter(fsm)

        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=100.0,  # Would breach if active
            consecutive_losses=100,
        )

        assert breaches == []

    def test_optional_daily_loss_none(self, interpreter: LeaseInterpreter):
        """Daily loss check skipped when not provided."""
        breaches = interpreter.check_all_bounds(
            current_drawdown_pct=1.0,
            consecutive_losses=0,
            daily_loss_pct=None,  # Not provided
        )

        assert breaches == []
