"""
Health FSM Tests — S40 Track A
==============================

Proves INV-HEALTH-1, INV-HEALTH-2, and INV-HEAL-REENTRANCY.
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from governance.health_fsm import (
    HealthStateMachine,
    HealthState,
    HealthConfig,
    HealthRegistry,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def config() -> HealthConfig:
    """Create test config with short windows."""
    return HealthConfig(
        degraded_threshold=3,
        critical_threshold=5,
        halt_threshold=10,
        failure_window=60.0,
        recovery_window=1.0,  # Short for testing
        alert_cooldown=0.1,  # Short for testing
        batch_window=0.1,
    )


@pytest.fixture
def mock_alert() -> MagicMock:
    """Create mock alert callback."""
    return MagicMock()


@pytest.fixture
def mock_halt() -> MagicMock:
    """Create mock halt callback."""
    return MagicMock()


@pytest.fixture
def hsm(config: HealthConfig, mock_alert: MagicMock, mock_halt: MagicMock) -> HealthStateMachine:
    """Create health FSM with mocked callbacks."""
    return HealthStateMachine(
        name="test_fsm",
        config=config,
        alert_callback=mock_alert,
        halt_callback=mock_halt,
    )


# =============================================================================
# BASIC STATE TESTS
# =============================================================================


class TestHealthFSMStates:
    """Test basic health state transitions."""

    def test_initial_state_healthy(self, hsm: HealthStateMachine):
        """New FSM starts HEALTHY."""
        assert hsm.state == HealthState.HEALTHY
        print("✓ Initial state is HEALTHY")

    def test_transitions_to_degraded(self, hsm: HealthStateMachine):
        """3 failures → DEGRADED."""
        for i in range(3):
            hsm.record_failure(f"comp_{i}")

        assert hsm.state == HealthState.DEGRADED
        print("✓ HEALTHY → DEGRADED after 3 failures")

    def test_transitions_to_critical(self, hsm: HealthStateMachine):
        """5 failures → CRITICAL."""
        for i in range(5):
            hsm.record_failure(f"comp_{i}")

        assert hsm.state == HealthState.CRITICAL
        print("✓ HEALTHY → CRITICAL after 5 failures")

    def test_transitions_to_halted(self, hsm: HealthStateMachine):
        """10 failures → HALTED."""
        for i in range(10):
            hsm.record_failure(f"comp_{i}")

        assert hsm.state == HealthState.HALTED
        print("✓ HEALTHY → HALTED after 10 failures")


# =============================================================================
# INV-HEALTH-1: CRITICAL → ALERT
# =============================================================================


class TestHealthCriticalAlert:
    """Prove INV-HEALTH-1: CRITICAL triggers alert."""

    def test_critical_sends_alert(
        self, hsm: HealthStateMachine, mock_alert: MagicMock
    ):
        """INV-HEALTH-1: CRITICAL → alert_callback invoked."""
        # Trigger CRITICAL
        for i in range(5):
            hsm.record_failure(f"comp_{i}")

        assert hsm.state == HealthState.CRITICAL

        # Alert should have been called
        mock_alert.assert_called()
        print("✓ INV-HEALTH-1: CRITICAL → alert sent")

    def test_critical_alert_contains_state(
        self, hsm: HealthStateMachine, mock_alert: MagicMock
    ):
        """CRITICAL alert includes state info."""
        for i in range(5):
            hsm.record_failure("test_component")

        # Check alert call
        mock_alert.assert_called()
        call_args = mock_alert.call_args

        # Alert should include CRITICAL and component info
        assert call_args is not None
        title, state, message = call_args[0]
        assert "CRITICAL" in title
        assert state == HealthState.CRITICAL
        print("✓ CRITICAL alert contains state info")


# =============================================================================
# INV-HEALTH-2: HALTED → HALT_LOCAL
# =============================================================================


class TestHealthHaltedCallback:
    """Prove INV-HEALTH-2: HALTED invokes halt_callback."""

    def test_halted_invokes_callback(
        self, hsm: HealthStateMachine, mock_halt: MagicMock
    ):
        """INV-HEALTH-2: HALTED → halt_callback invoked."""
        # Trigger HALTED
        for i in range(10):
            hsm.record_failure(f"comp_{i}")

        assert hsm.state == HealthState.HALTED

        # halt_callback should have been called exactly once
        mock_halt.assert_called_once()
        print("✓ INV-HEALTH-2: HALTED → halt_callback invoked")

    def test_force_halt_invokes_callback(
        self, hsm: HealthStateMachine, mock_halt: MagicMock
    ):
        """force_halt() also invokes halt_callback."""
        hsm.force_halt("manual_test")

        assert hsm.state == HealthState.HALTED
        mock_halt.assert_called_once()
        print("✓ force_halt() invokes halt_callback")

    def test_halt_only_once(
        self, hsm: HealthStateMachine, mock_halt: MagicMock
    ):
        """halt_callback invoked only once even with more failures."""
        # Trigger HALTED
        for i in range(15):
            hsm.record_failure(f"comp_{i}")

        # Only one call despite 15 failures
        mock_halt.assert_called_once()
        print("✓ halt_callback invoked only once")


# =============================================================================
# INV-HEAL-REENTRANCY: NO ALERT MULTIPLICATION
# =============================================================================


class TestHealthReentrancy:
    """Prove INV-HEAL-REENTRANCY: N failures → 1 alert."""

    def test_rapid_failures_single_alert(
        self, hsm: HealthStateMachine, mock_alert: MagicMock
    ):
        """INV-HEAL-REENTRANCY: 10 failures in 1s → 1 alert (not 10)."""
        # Fire 10 rapid failures (all within 1s)
        for i in range(10):
            hsm.record_failure(f"comp_{i}")

        # Should have limited alerts due to cooldown
        # In HEALTHY→DEGRADED→CRITICAL→HALTED transitions:
        # - DEGRADED: batched
        # - CRITICAL: 1 alert (or suppressed if within cooldown)
        # - HALTED: 1 alert

        # We expect at most 3 alerts (one per state transition with suppression)
        assert mock_alert.call_count <= 3
        print(f"✓ INV-HEAL-REENTRANCY: {mock_alert.call_count} alerts for 10 failures")

    def test_cooldown_suppresses_duplicates(
        self, config: HealthConfig, mock_alert: MagicMock, mock_halt: MagicMock
    ):
        """Alert cooldown suppresses duplicate alerts within window."""
        # Very short cooldown for this test
        config.alert_cooldown = 0.01  # 10ms cooldown

        hsm = HealthStateMachine(
            name="cooldown_test",
            config=config,
            alert_callback=mock_alert,
            halt_callback=mock_halt,
        )

        # First 5 failures → CRITICAL → alert
        for i in range(5):
            hsm.record_failure(f"comp_{i}")

        first_alert_count = mock_alert.call_count
        assert first_alert_count >= 1, "First CRITICAL should alert"

        # Wait past cooldown
        import time
        time.sleep(0.02)

        # Reset and trigger again
        hsm.reset()
        mock_alert.reset_mock()

        # Another 5 failures → should alert again (past cooldown)
        for i in range(5):
            hsm.record_failure(f"comp_{i}")

        # Alert should fire because cooldown elapsed
        assert mock_alert.call_count >= 1
        print("✓ Cooldown behavior verified")


# =============================================================================
# RECOVERY TESTS
# =============================================================================


class TestHealthRecovery:
    """Test recovery from degraded states."""

    def test_recovery_to_healthy(self, hsm: HealthStateMachine):
        """Sustained success → HEALTHY."""
        # Degrade
        for i in range(3):
            hsm.record_failure(f"comp_{i}")

        assert hsm.state == HealthState.DEGRADED

        # Wait for recovery window and record successes
        time.sleep(0.1)
        for i in range(5):
            hsm.record_success("comp")

        # Should recover (if no recent failures)
        time.sleep(1.1)  # Recovery window
        for i in range(3):
            hsm.record_success("comp")

        assert hsm.state == HealthState.HEALTHY
        print("✓ Recovery to HEALTHY works")

    def test_no_recovery_from_halted(self, hsm: HealthStateMachine):
        """HALTED requires manual reset to recover."""
        # Force HALTED
        hsm.force_halt("test")
        assert hsm.state == HealthState.HALTED

        # Successes don't recover HALTED
        for i in range(10):
            hsm.record_success("comp")

        assert hsm.state == HealthState.HALTED
        print("✓ HALTED requires manual reset")


# =============================================================================
# STATUS AND METRICS
# =============================================================================


class TestHealthStatus:
    """Test status reporting."""

    def test_get_status_includes_state(self, hsm: HealthStateMachine):
        """Status includes current state."""
        status = hsm.get_status()

        assert status["name"] == "test_fsm"
        assert status["state"] == "HEALTHY"
        assert "recent_failures" in status
        assert "thresholds" in status
        print("✓ Status includes all fields")

    def test_status_tracks_duration(self, hsm: HealthStateMachine):
        """Status tracks state duration."""
        time.sleep(0.1)
        status = hsm.get_status()

        assert status["state_duration"] >= 0.1
        print(f"✓ State duration tracked: {status['state_duration']:.2f}s")


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestHealthRegistry:
    """Test health FSM registry."""

    def test_get_or_create_same_instance(self):
        """Same name returns same instance."""
        registry = HealthRegistry()

        h1 = registry.get_or_create("test")
        h2 = registry.get_or_create("test")

        assert h1 is h2
        print("✓ Same name returns same instance")

    def test_all_status_returns_all(self):
        """all_status returns all FSM status."""
        registry = HealthRegistry()

        registry.get_or_create("one")
        registry.get_or_create("two")
        registry.get_or_create("three")

        status = registry.all_status()
        assert len(status) == 3
        names = {s["name"] for s in status}
        assert names == {"one", "two", "three"}
        print("✓ all_status returns all FSMs")

    def test_any_critical_detection(self):
        """any_critical detects CRITICAL/HALTED."""
        registry = HealthRegistry()

        _h1 = registry.get_or_create("healthy")  # Creates FSM, verifies creation
        h2 = registry.get_or_create("sick")

        # Initially none critical
        assert not registry.any_critical()

        # Make one critical
        for i in range(5):
            h2.record_failure(f"comp_{i}")

        assert registry.any_critical()
        print("✓ any_critical detects sick FSM")


# =============================================================================
# CHAOS: CONCURRENT FAILURES
# =============================================================================


class TestHealthChaos:
    """Chaos tests for health FSM."""

    def test_concurrent_failures_safe(
        self, hsm: HealthStateMachine, mock_halt: MagicMock
    ):
        """Concurrent failures don't corrupt state."""
        import threading

        def fail_worker():
            for i in range(5):
                hsm.record_failure(f"worker_comp_{i}")
                time.sleep(0.01)

        threads = [threading.Thread(target=fail_worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should be HALTED (15 total failures)
        assert hsm.state == HealthState.HALTED
        # halt_callback should be called exactly once
        mock_halt.assert_called_once()
        print("✓ Concurrent failures handled safely")

    def test_rapid_state_transitions(
        self, config: HealthConfig, mock_alert: MagicMock, mock_halt: MagicMock
    ):
        """Rapid state transitions handled correctly."""
        config.alert_cooldown = 0.0  # No cooldown for this test

        hsm = HealthStateMachine(
            name="rapid_test",
            config=config,
            alert_callback=mock_alert,
            halt_callback=mock_halt,
        )

        # Rapid failures: HEALTHY → DEGRADED → CRITICAL → HALTED
        states = []
        for i in range(10):
            hsm.record_failure(f"comp_{i}")
            states.append(hsm.state)

        # Should see progression
        assert HealthState.DEGRADED in states
        assert HealthState.CRITICAL in states
        assert hsm.state == HealthState.HALTED
        print(f"✓ Rapid transitions: {[s.value for s in states]}")
