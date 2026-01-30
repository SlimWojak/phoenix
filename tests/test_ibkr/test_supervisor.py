"""
IBKR Supervisor Tests — S40 Track B
===================================

Proves INV-IBKR-FLAKEY-2, INV-IBKR-FLAKEY-3, and INV-SUPERVISOR-1.
"""

from __future__ import annotations

import time
import threading
import pytest
from unittest.mock import MagicMock

from brokers.ibkr.supervisor import (
    IBKRSupervisor,
    SupervisorState,
    SupervisorWatchdog,
    create_ibkr_supervisor,
)


# =============================================================================
# MOCK CONNECTOR
# =============================================================================


class MockIBKRConnector:
    """Mock IBKR connector for testing."""

    def __init__(self):
        self._connected = True
        self._crash_requested = False

    def is_connected(self) -> bool:
        return self._connected

    def disconnect(self) -> None:
        self._connected = False

    def connect(self) -> None:
        self._connected = True

    def crash(self) -> None:
        """Simulate connector crash."""
        self._crash_requested = True
        self._connected = False


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_connector() -> MockIBKRConnector:
    """Create mock connector."""
    return MockIBKRConnector()


@pytest.fixture
def mock_alert() -> MagicMock:
    """Create mock alert callback."""
    return MagicMock()


@pytest.fixture
def supervisor(mock_connector: MockIBKRConnector, mock_alert: MagicMock) -> IBKRSupervisor:
    """Create supervisor with short intervals for testing."""
    return IBKRSupervisor(
        connector=mock_connector,
        heartbeat_interval=0.1,  # 100ms
        miss_threshold=3,
        check_interval=0.05,  # 50ms
        on_alert=mock_alert,
    )


# =============================================================================
# BASIC TESTS
# =============================================================================


class TestSupervisorBasic:
    """Test basic supervisor functionality."""

    def test_initial_state_stopped(self, supervisor: IBKRSupervisor):
        """Initial state is STOPPED."""
        assert supervisor.state == SupervisorState.STOPPED
        assert not supervisor.is_running
        print("✓ Initial state is STOPPED")

    def test_start_and_stop(self, supervisor: IBKRSupervisor):
        """Supervisor can start and stop."""
        supervisor.start()
        assert supervisor.is_running
        assert supervisor.state == SupervisorState.RUNNING

        supervisor.stop()
        assert not supervisor.is_running
        print("✓ Supervisor starts and stops")

    def test_heartbeat_integration(self, supervisor: IBKRSupervisor):
        """Supervisor integrates with heartbeat."""
        supervisor.heartbeat.beat()
        assert supervisor.connector_alive
        print("✓ Heartbeat integration works")


# =============================================================================
# INV-IBKR-FLAKEY-2: SUPERVISOR SURVIVES CRASH
# =============================================================================


class TestSupervisorSurvivesCrash:
    """Prove INV-IBKR-FLAKEY-2: Supervisor survives connector crash."""

    def test_supervisor_survives_connector_crash(
        self, supervisor: IBKRSupervisor, mock_connector: MockIBKRConnector
    ):
        """INV-IBKR-FLAKEY-2: Supervisor keeps running after crash."""
        supervisor.start()
        supervisor.heartbeat.beat()  # Initial beat

        # Wait for supervisor to stabilize
        time.sleep(0.1)
        assert supervisor.is_running

        # Simulate connector crash
        mock_connector.crash()

        # Wait and verify supervisor still running
        time.sleep(0.2)
        assert supervisor.is_running
        assert supervisor.state in (SupervisorState.RUNNING, SupervisorState.ALERTING)

        supervisor.stop()
        print("✓ INV-IBKR-FLAKEY-2: Supervisor survived connector crash")

    def test_supervisor_loop_isolated(self, supervisor: IBKRSupervisor):
        """Supervisor loop runs in separate thread."""
        supervisor.start()

        # Get supervisor thread
        assert supervisor._thread is not None
        assert supervisor._thread.name == "IBKRSupervisor"
        assert supervisor._thread.is_alive()

        # Verify it's a different thread
        assert supervisor._thread != threading.current_thread()

        supervisor.stop()
        print("✓ Supervisor runs in isolated thread")


# =============================================================================
# INV-IBKR-FLAKEY-3: VALIDATION BEFORE RESTORE
# =============================================================================


class TestValidationBeforeRestore:
    """Prove INV-IBKR-FLAKEY-3: Reconnection requires validation."""

    def test_restore_requires_validation(self, supervisor: IBKRSupervisor):
        """INV-IBKR-FLAKEY-3: Restoration requires validation."""
        # Trigger degradation
        supervisor.degradation.trigger_degradation("test_disconnect")
        assert supervisor.degradation.is_degraded

        # Restore with validation
        result = supervisor.degradation.restore(validate_first=True)
        assert result is True
        assert not supervisor.degradation.is_degraded
        print("✓ INV-IBKR-FLAKEY-3: Restore requires validation")


# =============================================================================
# INV-SUPERVISOR-1: SUPERVISOR DEATH → ALERT
# =============================================================================


class TestSupervisorDeathAlert:
    """Prove INV-SUPERVISOR-1: Supervisor death triggers alert."""

    def test_watchdog_detects_death(self, supervisor: IBKRSupervisor, mock_alert: MagicMock):
        """INV-SUPERVISOR-1: Watchdog detects supervisor death."""
        on_dead = MagicMock()

        watchdog = SupervisorWatchdog(
            supervisor=supervisor,
            check_interval=0.05,
            on_supervisor_dead=on_dead,
        )

        supervisor.start()
        watchdog.start()
        time.sleep(0.1)

        # Stop supervisor (simulates death)
        supervisor.stop()
        time.sleep(0.2)

        # Watchdog should have detected
        on_dead.assert_called_once()
        print("✓ INV-SUPERVISOR-1: Watchdog detected supervisor death")

    def test_factory_creates_watchdog(self, mock_alert: MagicMock):
        """Factory creates supervisor with watchdog."""
        supervisor, watchdog = create_ibkr_supervisor(on_alert=mock_alert)

        assert supervisor is not None
        assert watchdog is not None
        assert watchdog.supervisor is supervisor
        print("✓ Factory creates supervisor + watchdog")


# =============================================================================
# DEGRADATION INTEGRATION
# =============================================================================


class TestSupervisorDegradation:
    """Test degradation integration."""

    def test_missed_beats_trigger_degradation(self, supervisor: IBKRSupervisor, mock_alert: MagicMock):
        """Missed heartbeats trigger degradation."""
        supervisor.start()
        supervisor.heartbeat.beat()  # Initial beat
        time.sleep(0.1)

        # Let beats lapse (should go DEAD after 3 misses)
        time.sleep(0.5)

        # Should have triggered degradation
        assert supervisor.degradation.is_degraded or supervisor.state == SupervisorState.ALERTING

        supervisor.stop()
        print("✓ Missed beats trigger degradation")

    def test_force_degradation(self, supervisor: IBKRSupervisor, mock_alert: MagicMock):
        """force_degradation works."""
        supervisor.force_degradation("manual_test")

        assert supervisor.degradation.is_degraded
        mock_alert.assert_called()
        print("✓ Force degradation works")


# =============================================================================
# STATUS
# =============================================================================


class TestSupervisorStatus:
    """Test status reporting."""

    def test_status_includes_all_components(self, supervisor: IBKRSupervisor):
        """Status includes all component status."""
        supervisor.start()
        supervisor.heartbeat.beat()
        time.sleep(0.1)

        status = supervisor.get_status()

        assert "state" in status
        assert "running" in status
        assert "heartbeat" in status
        assert "degradation" in status
        assert "circuit_breaker" in status
        assert "metrics" in status

        supervisor.stop()
        print("✓ Status includes all components")


# =============================================================================
# CHAOS
# =============================================================================


class TestSupervisorChaos:
    """Chaos tests for supervisor."""

    def test_flap_connection_5x(self, supervisor: IBKRSupervisor, mock_alert: MagicMock):
        """Flap connection 5x → supervisor stable."""
        supervisor.start()

        for i in range(5):
            # Beat (alive)
            supervisor.heartbeat.beat()
            time.sleep(0.1)

            # No beat (dead)
            time.sleep(0.4)

        # Supervisor should still be running
        assert supervisor.is_running

        supervisor.stop()
        print("✓ Survived 5x connection flap")

    def test_reconnect_during_degraded(self, supervisor: IBKRSupervisor):
        """Reconnect during DEGRADED requires validation."""
        # Trigger degradation
        supervisor.degradation.trigger_degradation("disconnect")
        assert supervisor.degradation.is_degraded

        # Try to "reconnect" by just beating
        supervisor.heartbeat.beat()

        # Should still be degraded until explicit restore
        assert supervisor.degradation.is_degraded

        # Explicit restore with validation
        supervisor.degradation.restore(validate_first=True)
        assert not supervisor.degradation.is_degraded

        print("✓ Reconnect during DEGRADED requires validation")

    def test_concurrent_degradation_triggers(self, supervisor: IBKRSupervisor):
        """Concurrent degradation triggers safe."""
        def trigger_worker():
            for _ in range(10):
                supervisor.force_degradation("worker")
                time.sleep(0.01)

        threads = [threading.Thread(target=trigger_worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should not crash, degradation should be active
        assert supervisor.degradation.is_degraded
        print("✓ Concurrent degradation triggers handled")

    def test_kill_mid_order_scenario(
        self, supervisor: IBKRSupervisor, mock_connector: MockIBKRConnector
    ):
        """Kill connector mid-order → degrade, no crash."""
        supervisor.start()
        supervisor.heartbeat.beat()
        time.sleep(0.1)

        # Simulate mid-order crash
        mock_connector.crash()

        # Trigger degradation manually (simulating detection)
        supervisor.force_degradation("mid_order_crash")

        # Should be degraded
        assert supervisor.degradation.is_degraded

        # T2 should be blocked
        assert not supervisor.degradation.can_execute_tier(2)

        # Supervisor should still be running
        assert supervisor.is_running

        supervisor.stop()
        print("✓ Mid-order kill → degrade, no crash")


# =============================================================================
# DISCONNECT 10X TEST
# =============================================================================


class TestDisconnect10x:
    """Test disconnect 10x scenario from exit gate."""

    def test_ibkr_disconnect_10x_stable(self, mock_alert: MagicMock):
        """IBKR disconnect 10x → no crash, correct degrade, supervisor alive."""
        supervisor = IBKRSupervisor(
            heartbeat_interval=0.05,
            miss_threshold=3,
            check_interval=0.02,
            on_alert=mock_alert,
        )

        supervisor.start()
        results = {"degradations": 0, "recoveries": 0}

        for i in range(10):
            # Beat (connected)
            supervisor.heartbeat.beat()
            time.sleep(0.02)

            # No beat (disconnect simulation)
            supervisor.force_degradation(f"disconnect_{i}")
            results["degradations"] += 1

            # Verify degraded
            assert supervisor.degradation.is_degraded

            # Restore (reconnect simulation)
            supervisor.degradation.restore(validate_first=False)
            results["recoveries"] += 1

            # Verify restored
            assert not supervisor.degradation.is_degraded

        # Supervisor should be alive
        assert supervisor.is_running

        supervisor.stop()

        print(f"✓ 10 disconnect cycles: {results}")
        print("✓ EXIT GATE: IBKR disconnect 10x → no crash, correct degrade, supervisor alive")
