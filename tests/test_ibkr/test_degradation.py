"""
Degradation Manager Tests — S40 Track B
=======================================

Proves INV-IBKR-DEGRADE-1 and INV-IBKR-DEGRADE-2.
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from governance.health_fsm import HealthStateMachine

from brokers.ibkr.degradation import (
    DegradationManager,
    DegradationLevel,
    TierBlockedError,
    require_tier,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def health_fsm() -> HealthStateMachine:
    """Create health FSM."""
    return HealthStateMachine(name="test_fsm")


@pytest.fixture
def degradation(health_fsm: HealthStateMachine) -> DegradationManager:
    """Create degradation manager."""
    return DegradationManager(health_fsm=health_fsm)


@pytest.fixture
def mock_callbacks() -> tuple[MagicMock, MagicMock]:
    """Create mock callbacks."""
    return MagicMock(), MagicMock()


# =============================================================================
# BASIC TESTS
# =============================================================================


class TestDegradationBasic:
    """Test basic degradation functionality."""

    def test_initial_level_none(self, degradation: DegradationManager):
        """Initial level is NONE (no degradation)."""
        assert degradation.level == DegradationLevel.NONE
        assert not degradation.is_degraded
        print("✓ Initial level is NONE")

    def test_all_tiers_allowed_initially(self, degradation: DegradationManager):
        """All tiers allowed when not degraded."""
        assert degradation.can_execute_tier(0)
        assert degradation.can_execute_tier(1)
        assert degradation.can_execute_tier(2)
        print("✓ All tiers allowed initially")


# =============================================================================
# INV-IBKR-DEGRADE-1: T2 BLOCKED WITHIN 1S
# =============================================================================


class TestDegradeTiming:
    """Prove INV-IBKR-DEGRADE-1: T2 blocked within 1s."""

    def test_t2_blocked_immediately(self, degradation: DegradationManager):
        """INV-IBKR-DEGRADE-1: T2 blocked within 1s."""
        start = time.monotonic()

        degradation.trigger_degradation("test_disconnect")

        # Check T2 is blocked
        elapsed = time.monotonic() - start
        assert not degradation.can_execute_tier(2)
        assert elapsed < 1.0

        print(f"✓ INV-IBKR-DEGRADE-1: T2 blocked in {elapsed:.4f}s (<1s)")

    def test_degradation_returns_level(self, degradation: DegradationManager):
        """trigger_degradation returns the new level."""
        level = degradation.trigger_degradation("test")
        assert level == DegradationLevel.SOFT
        print("✓ Degradation returns SOFT level")


# =============================================================================
# INV-IBKR-DEGRADE-2: NO T2 IN DEGRADED STATE
# =============================================================================


class TestNoT2InDegraded:
    """Prove INV-IBKR-DEGRADE-2: No T2 in DEGRADED state."""

    def test_t2_raises_when_degraded(self, degradation: DegradationManager):
        """INV-IBKR-DEGRADE-2: T2 raises TierBlockedError."""
        degradation.trigger_degradation("test")

        with pytest.raises(TierBlockedError) as exc_info:
            degradation.check_tier(2)

        assert exc_info.value.tier == 2
        assert exc_info.value.level == DegradationLevel.SOFT
        print("✓ INV-IBKR-DEGRADE-2: T2 raises TierBlockedError")

    def test_t1_allowed_in_soft_degradation(self, degradation: DegradationManager):
        """T1 still allowed in SOFT degradation."""
        degradation.trigger_degradation("test")

        # T1 should not raise
        degradation.check_tier(1)
        assert degradation.can_execute_tier(1)
        print("✓ T1 allowed in SOFT degradation")

    def test_t0_always_allowed(self, degradation: DegradationManager):
        """T0 allowed in all degradation levels."""
        # SOFT
        degradation.trigger_degradation("test")
        assert degradation.can_execute_tier(0)

        # HARD
        degradation.escalate()
        assert degradation.can_execute_tier(0)

        # TOTAL
        degradation.escalate()
        assert not degradation.can_execute_tier(0)  # TOTAL blocks all

        print("✓ T0 allowed except in TOTAL")


# =============================================================================
# ESCALATION
# =============================================================================


class TestDegradationEscalation:
    """Test degradation escalation."""

    def test_escalation_soft_to_hard(self, degradation: DegradationManager):
        """SOFT → HARD escalation."""
        degradation.trigger_degradation("test")
        assert degradation.level == DegradationLevel.SOFT

        degradation.escalate()
        assert degradation.level == DegradationLevel.HARD
        print("✓ SOFT → HARD")

    def test_escalation_hard_to_total(self, degradation: DegradationManager):
        """HARD → TOTAL escalation."""
        degradation.trigger_degradation("test")
        degradation.escalate()  # HARD
        degradation.escalate()  # TOTAL

        assert degradation.level == DegradationLevel.TOTAL
        print("✓ HARD → TOTAL")

    def test_hard_blocks_t1(self, degradation: DegradationManager):
        """HARD level blocks T1."""
        degradation.trigger_degradation("test")
        degradation.escalate()  # HARD

        assert not degradation.can_execute_tier(1)
        assert not degradation.can_execute_tier(2)
        assert degradation.can_execute_tier(0)
        print("✓ HARD blocks T1 and T2")

    def test_total_blocks_all(self, degradation: DegradationManager):
        """TOTAL level blocks all tiers."""
        degradation.trigger_degradation("test")
        degradation.escalate()  # HARD
        degradation.escalate()  # TOTAL

        assert not degradation.can_execute_tier(0)
        assert not degradation.can_execute_tier(1)
        assert not degradation.can_execute_tier(2)
        print("✓ TOTAL blocks all tiers")


# =============================================================================
# RESTORATION
# =============================================================================


class TestDegradationRestore:
    """Test restoration from degradation."""

    def test_restore_clears_degradation(self, degradation: DegradationManager):
        """restore() clears degradation."""
        degradation.trigger_degradation("test")
        assert degradation.is_degraded

        degradation.restore(validate_first=False)
        assert not degradation.is_degraded
        assert degradation.level == DegradationLevel.NONE
        print("✓ Restore clears degradation")

    def test_restore_with_validation(self, degradation: DegradationManager):
        """INV-IBKR-FLAKEY-3: Restore requires validation."""
        degradation.trigger_degradation("test")

        # Default validation passes
        result = degradation.restore(validate_first=True)
        assert result is True
        assert not degradation.is_degraded
        print("✓ INV-IBKR-FLAKEY-3: Restore with validation")

    def test_all_tiers_allowed_after_restore(self, degradation: DegradationManager):
        """All tiers allowed after restore."""
        degradation.trigger_degradation("test")
        degradation.restore()

        assert degradation.can_execute_tier(0)
        assert degradation.can_execute_tier(1)
        assert degradation.can_execute_tier(2)
        print("✓ All tiers allowed after restore")


# =============================================================================
# CALLBACKS
# =============================================================================


class TestDegradationCallbacks:
    """Test degradation callbacks."""

    def test_on_degrade_callback(self, health_fsm: HealthStateMachine, mock_callbacks: tuple):
        """on_degrade called when degradation triggered."""
        on_degrade, on_restore = mock_callbacks

        dm = DegradationManager(
            health_fsm=health_fsm,
            on_degrade=on_degrade,
        )

        dm.trigger_degradation("test_reason")

        on_degrade.assert_called_once()
        args = on_degrade.call_args[0]
        assert args[0] == DegradationLevel.SOFT
        assert "test_reason" in args[1]
        print("✓ on_degrade callback fired")

    def test_on_restore_callback(self, health_fsm: HealthStateMachine, mock_callbacks: tuple):
        """on_restore called when restored."""
        on_degrade, on_restore = mock_callbacks

        dm = DegradationManager(
            health_fsm=health_fsm,
            on_restore=on_restore,
        )

        dm.trigger_degradation("test")
        dm.restore()

        on_restore.assert_called_once()
        print("✓ on_restore callback fired")


# =============================================================================
# STATUS
# =============================================================================


class TestDegradationStatus:
    """Test status reporting."""

    def test_status_includes_all_fields(self, degradation: DegradationManager):
        """Status includes all required fields."""
        degradation.trigger_degradation("test")
        status = degradation.get_status()

        assert "level" in status
        assert "is_degraded" in status
        assert "reason" in status
        assert "tiers_allowed" in status
        assert "degradation_count" in status
        print("✓ Status includes all fields")

    def test_status_tiers_allowed_accurate(self, degradation: DegradationManager):
        """tiers_allowed reflects current state."""
        status = degradation.get_status()
        assert status["tiers_allowed"] == [0, 1, 2]

        degradation.trigger_degradation("test")
        status = degradation.get_status()
        assert status["tiers_allowed"] == [0, 1]

        degradation.escalate()
        status = degradation.get_status()
        assert status["tiers_allowed"] == [0]
        print("✓ tiers_allowed accurate")


# =============================================================================
# DECORATOR
# =============================================================================


class TestRequireTierDecorator:
    """Test require_tier decorator."""

    def test_decorator_allows_when_not_degraded(self, degradation: DegradationManager):
        """Decorator allows when not degraded."""
        @require_tier(2, degradation)
        def place_order():
            return "order_placed"

        result = place_order()
        assert result == "order_placed"
        print("✓ Decorator allows when not degraded")

    def test_decorator_blocks_when_degraded(self, degradation: DegradationManager):
        """Decorator blocks when degraded."""
        @require_tier(2, degradation)
        def place_order():
            return "order_placed"

        degradation.trigger_degradation("test")

        with pytest.raises(TierBlockedError):
            place_order()
        print("✓ Decorator blocks when degraded")


# =============================================================================
# CHAOS
# =============================================================================


class TestDegradationChaos:
    """Chaos tests for degradation."""

    def test_rapid_triggers_counted(self, degradation: DegradationManager):
        """Rapid triggers counted correctly."""
        for i in range(10):
            degradation.trigger_degradation(f"trigger_{i}")
            degradation.restore(validate_first=False)

        status = degradation.get_status()
        assert status["degradation_count"] == 10
        print(f"✓ {status['degradation_count']} degradation triggers counted")

    def test_blocked_operations_counted(self, degradation: DegradationManager):
        """Blocked operations counted."""
        degradation.trigger_degradation("test")

        for _ in range(5):
            try:
                degradation.check_tier(2)
            except TierBlockedError:
                pass

        status = degradation.get_status()
        assert status["blocked_operations"] == 5
        print(f"✓ {status['blocked_operations']} blocked operations counted")

    def test_no_just_one_more_order(self, degradation: DegradationManager):
        """No 'just one more order' loophole."""
        # Even if we check tier first, degradation should block
        assert degradation.can_execute_tier(2)

        degradation.trigger_degradation("market_close")

        # No matter how we try, T2 should be blocked
        assert not degradation.can_execute_tier(2)
        with pytest.raises(TierBlockedError):
            degradation.check_tier(2)
        print("✓ No 'just one more order' loophole")
