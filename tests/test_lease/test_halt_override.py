"""
Tests for Halt Override
=======================

Sprint: S47 LEASE_IMPLEMENTATION
EXIT_GATE_S47_3: Halt overrides lease — <50ms, no race

Tests:
  - INV-HALT-OVERRIDES-LEASE: Halt always wins
  - Halt latency < 50ms (INV-HALT-1)
  - Halt bypasses state lock hash check
  - Global halt propagation to lease
"""

import threading
import time
from datetime import UTC, datetime, timedelta

import pytest

from governance.lease import (
    LeaseInterpreter,
    LeaseManager,
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
    """Create an active lease."""
    now = datetime.now(UTC)
    lease = Lease(
        identity=LeaseIdentity(
            created_at=now,
            created_by="test_user",
        ),
        subject=LeaseSubject(
            strategy_ref="HALT_TEST_v1.0.0",
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
    return lease


@pytest.fixture
def lease_manager() -> LeaseManager:
    """Fresh lease manager for each test."""
    # Reset singleton state
    LeaseManager._instance = None
    manager = LeaseManager()
    manager.configure()
    yield manager
    # Cleanup
    manager.reset()
    LeaseManager._instance = None


# =============================================================================
# INV-HALT-OVERRIDES-LEASE TESTS
# =============================================================================


class TestHaltOverridesLease:
    """Test INV-HALT-OVERRIDES-LEASE: Halt always wins."""

    def test_halt_succeeds_on_active_lease(self, active_lease: Lease):
        """Halt transitions active lease to HALTED."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()

        assert fsm.state == LeaseState.ACTIVE

        result = fsm.halt(
            trigger="GLOBAL_HALT",
            bound_exceeded="system",
            value=0,
        )

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED

    def test_halt_bypasses_state_lock(self, active_lease: Lease):
        """
        Halt ignores state_lock_hash check.

        INV-HALT-OVERRIDES-LEASE: Halt must succeed regardless of race.
        """
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()

        # Try halt with completely wrong hash
        result = fsm.halt(
            trigger="EMERGENCY",
            bound_exceeded="global",
            value=0,
            expected_hash="totally_wrong_hash_1234567890",
        )

        # Should still succeed
        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED

    def test_halt_from_any_active_state(self, active_lease: Lease):
        """Halt only works from ACTIVE state."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)

        # DRAFT state — halt should fail
        result = fsm.halt(trigger="TEST", bound_exceeded="test", value=0)
        assert result == TransitionResult.REJECTED_INVALID_TRANSITION

        # Activate then halt
        fsm.activate()
        result = fsm.halt(trigger="TEST", bound_exceeded="test", value=0)
        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED


# =============================================================================
# HALT LATENCY TESTS — INV-HALT-1
# =============================================================================


class TestHaltLatency:
    """Test halt latency < 50ms (INV-HALT-1)."""

    @pytest.mark.parametrize("iteration", range(10))
    def test_halt_under_50ms(self, active_lease: Lease, iteration: int):
        """Halt completes in under 50ms."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()

        start = time.perf_counter_ns()
        result = fsm.halt(trigger="BENCHMARK", bound_exceeded="test", value=0)
        elapsed_ns = time.perf_counter_ns() - start
        elapsed_ms = elapsed_ns / 1_000_000

        assert result == TransitionResult.SUCCESS
        assert elapsed_ms < 50, f"Halt took {elapsed_ms:.2f}ms, exceeds 50ms"

    def test_global_halt_under_50ms(self, lease_manager: LeaseManager, active_lease: Lease):
        """Global halt completes in under 50ms."""
        # Activate lease via manager
        lease_manager.activate_lease(active_lease)
        assert lease_manager.has_active_lease

        start = time.perf_counter_ns()
        lease_manager.on_global_halt("EMERGENCY_001")
        elapsed_ns = time.perf_counter_ns() - start
        elapsed_ms = elapsed_ns / 1_000_000

        assert elapsed_ms < 50, f"Global halt took {elapsed_ms:.2f}ms"
        assert not lease_manager.has_active_lease  # Lease no longer active


# =============================================================================
# GLOBAL HALT PROPAGATION TESTS
# =============================================================================


class TestGlobalHaltPropagation:
    """Test global halt propagation to lease manager."""

    def test_global_halt_halts_active_lease(self, lease_manager: LeaseManager, active_lease: Lease):
        """Global halt signal halts the active lease."""
        state_machine, result = lease_manager.activate_lease(active_lease)
        assert result == TransitionResult.SUCCESS
        assert lease_manager.has_active_lease

        lease_manager.on_global_halt("EMERGENCY_TEST")

        assert not lease_manager.has_active_lease
        assert state_machine.state == LeaseState.HALTED
        assert active_lease.status.halt_trigger == "GLOBAL_HALT:EMERGENCY_TEST"

    def test_global_halt_no_active_lease(self, lease_manager: LeaseManager):
        """Global halt is safe when no lease is active."""
        assert not lease_manager.has_active_lease

        # Should not raise
        lease_manager.on_global_halt("NO_LEASE_TEST")

        assert not lease_manager.has_active_lease

    def test_global_halt_after_expiry(self, lease_manager: LeaseManager, active_lease: Lease):
        """Global halt on expired lease is safe (no-op)."""
        state_machine, result = lease_manager.activate_lease(active_lease)
        assert result == TransitionResult.SUCCESS

        # Expire the lease
        state_machine.expire()
        assert not lease_manager.has_active_lease

        # Global halt should be safe
        lease_manager.on_global_halt("POST_EXPIRY_TEST")

        # State should still be EXPIRED (not HALTED)
        assert state_machine.state == LeaseState.EXPIRED


# =============================================================================
# RACE CONDITION TESTS
# =============================================================================


class TestHaltRaceConditions:
    """Test halt behavior under concurrent conditions."""

    def test_concurrent_halt_calls(self, active_lease: Lease):
        """Multiple concurrent halt calls should all succeed or be no-ops."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()

        results = []
        errors = []

        def try_halt(thread_id: int):
            try:
                result = fsm.halt(
                    trigger=f"CONCURRENT_{thread_id}",
                    bound_exceeded="race_test",
                    value=thread_id,
                )
                results.append((thread_id, result))
            except Exception as e:
                errors.append((thread_id, e))

        # Launch multiple threads trying to halt simultaneously
        threads = [threading.Thread(target=try_halt, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # No exceptions
        assert errors == []

        # Exactly one SUCCESS, rest should be REJECTED_INVALID_TRANSITION
        successes = [r for r in results if r[1] == TransitionResult.SUCCESS]
        rejections = [r for r in results if r[1] == TransitionResult.REJECTED_INVALID_TRANSITION]

        assert len(successes) == 1
        assert len(rejections) == 9

        # Final state should be HALTED
        assert fsm.state == LeaseState.HALTED

    def test_halt_during_revoke(self, active_lease: Lease):
        """
        Halt and revoke racing — valid outcomes depend on timing.

        Possible outcomes:
        1. Halt wins first (ACTIVE→HALTED), then revoke wins (HALTED→REVOKED) = both succeed
        2. Revoke wins first (ACTIVE→REVOKED), then halt fails = one succeed
        3. Halt wins first, revoke fails (trying invalid transition) = one succeed

        All outcomes are valid — the key is no corruption.
        """
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()

        results = {"halt": None, "revoke": None}

        def try_halt():
            results["halt"] = fsm.halt(
                trigger="RACE",
                bound_exceeded="concurrent",
                value=0,
            )

        def try_revoke():
            results["revoke"] = fsm.revoke(
                revoked_by="admin",
                reason="concurrent_revoke",
            )

        # Launch both operations
        t1 = threading.Thread(target=try_halt)
        t2 = threading.Thread(target=try_revoke)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # At least one should succeed
        success_count = sum(1 for r in results.values() if r == TransitionResult.SUCCESS)
        assert success_count >= 1

        # If both succeed, it means halt happened first (ACTIVE→HALTED),
        # then revoke happened (HALTED→REVOKED) — this is valid
        # Final state must be either HALTED or REVOKED
        assert fsm.state in (LeaseState.HALTED, LeaseState.REVOKED)


# =============================================================================
# HALT DURING BOUNDS CHECK
# =============================================================================


class TestHaltDuringBoundsCheck:
    """Test halt during bounds enforcement."""

    def test_bounds_breach_triggers_halt(self, active_lease: Lease):
        """Bounds breach via interpreter triggers halt."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()
        interpreter = LeaseInterpreter(fsm)

        # Trigger bounds breach
        result = interpreter.enforce_bounds(
            current_drawdown_pct=10.0,  # > 5.0
            consecutive_losses=0,
        )

        assert result == TransitionResult.SUCCESS
        assert fsm.state == LeaseState.HALTED

    def test_bounds_halt_includes_breach_info(self, active_lease: Lease):
        """Bounds halt includes which bound was breached."""
        emitter = NullBeadEmitter()
        fsm = LeaseStateMachine(active_lease, emitter)
        fsm.activate()
        interpreter = LeaseInterpreter(fsm)

        interpreter.enforce_bounds(
            current_drawdown_pct=7.5,
            consecutive_losses=0,
        )

        # Check halt info
        assert active_lease.status.halt_trigger == "BOUNDS_BREACH"

        # Check bead
        halt_bead = emitter.beads[-1]
        assert halt_bead.bound_exceeded == "max_drawdown_pct"
        assert halt_bead.value == 7.5
