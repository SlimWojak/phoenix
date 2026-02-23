"""
Heartbeat Monitor Tests — S40 Track B
=====================================

Proves INV-IBKR-FLAKEY-1.
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import MagicMock

from brokers.ibkr.heartbeat import (
    HeartbeatMonitor,
    HeartbeatState,
    HeartbeatEmitter,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def monitor() -> HeartbeatMonitor:
    """Create heartbeat monitor with short interval."""
    return HeartbeatMonitor(
        interval=0.1,  # 100ms for fast testing
        miss_threshold=3,
    )


@pytest.fixture
def mock_callbacks() -> tuple[MagicMock, MagicMock, MagicMock]:
    """Create mock callbacks."""
    return MagicMock(), MagicMock(), MagicMock()


# =============================================================================
# BASIC TESTS
# =============================================================================


class TestHeartbeatBasic:
    """Test basic heartbeat functionality."""

    def test_initial_state_dead(self, monitor: HeartbeatMonitor):
        """New monitor starts DEAD (no beats received)."""
        assert monitor.state == HeartbeatState.DEAD
        print("✓ Initial state is DEAD")

    def test_beat_makes_alive(self, monitor: HeartbeatMonitor):
        """Single beat transitions to ALIVE."""
        monitor.beat()
        assert monitor.state == HeartbeatState.ALIVE
        assert monitor.is_alive
        print("✓ Beat makes ALIVE")

    def test_beat_count_increments(self, monitor: HeartbeatMonitor):
        """Beat count increments with each beat."""
        for i in range(5):
            monitor.beat()

        status = monitor.get_status()
        assert status["beat_count"] == 5
        print("✓ Beat count increments")


# =============================================================================
# INV-IBKR-FLAKEY-1: 3 MISSED BEATS → DEAD
# =============================================================================


class TestHeartbeatDead:
    """Prove INV-IBKR-FLAKEY-1: 3 missed beats → DEAD."""

    def test_one_missed_beat_degraded(self, monitor: HeartbeatMonitor):
        """1 missed beat → DEGRADED."""
        monitor.beat()
        time.sleep(0.15)  # 1.5 intervals

        assert monitor.state == HeartbeatState.DEGRADED
        assert monitor.missed_beats == 1
        print("✓ 1 missed beat → DEGRADED")

    def test_two_missed_beats_still_degraded(self, monitor: HeartbeatMonitor):
        """2 missed beats → still DEGRADED."""
        monitor.beat()
        time.sleep(0.25)  # 2.5 intervals

        assert monitor.state == HeartbeatState.DEGRADED
        assert monitor.missed_beats == 2
        print("✓ 2 missed beats → DEGRADED")

    def test_three_missed_beats_dead(self, monitor: HeartbeatMonitor):
        """INV-IBKR-FLAKEY-1: 3 missed beats → DEAD."""
        monitor.beat()
        time.sleep(0.35)  # 3.5 intervals

        assert monitor.state == HeartbeatState.DEAD
        assert monitor.missed_beats >= 3
        assert not monitor.is_alive
        print("✓ INV-IBKR-FLAKEY-1: 3 missed beats → DEAD")

    def test_recovery_after_dead(self, monitor: HeartbeatMonitor):
        """Beat after DEAD → ALIVE."""
        monitor.beat()
        time.sleep(0.35)  # Go DEAD
        assert monitor.state == HeartbeatState.DEAD

        monitor.beat()  # Recover
        assert monitor.state == HeartbeatState.ALIVE
        print("✓ Recovery from DEAD")


# =============================================================================
# CALLBACKS
# =============================================================================


class TestHeartbeatCallbacks:
    """Test heartbeat callbacks."""

    def test_on_dead_callback(self, mock_callbacks: tuple):
        """on_dead called when DEAD."""
        on_degraded, on_dead, on_recovery = mock_callbacks

        monitor = HeartbeatMonitor(
            interval=0.1,
            miss_threshold=3,
            on_dead=on_dead,
        )

        monitor.beat()
        time.sleep(0.35)  # Go DEAD
        monitor.check()

        on_dead.assert_called_once()
        print("✓ on_dead callback fired")

    def test_on_degraded_callback(self, mock_callbacks: tuple):
        """on_degraded called when DEGRADED."""
        on_degraded, on_dead, on_recovery = mock_callbacks

        monitor = HeartbeatMonitor(
            interval=0.1,
            miss_threshold=3,
            on_degraded=on_degraded,
        )

        monitor.beat()
        time.sleep(0.15)  # Go DEGRADED
        monitor.check()

        on_degraded.assert_called_once()
        print("✓ on_degraded callback fired")

    def test_on_recovery_callback(self, mock_callbacks: tuple):
        """on_recovery called when recovering."""
        on_degraded, on_dead, on_recovery = mock_callbacks

        monitor = HeartbeatMonitor(
            interval=0.1,
            miss_threshold=3,
            on_recovery=on_recovery,
        )

        monitor.beat()
        time.sleep(0.35)  # Go DEAD
        monitor.check()

        monitor.beat()  # Recover
        on_recovery.assert_called()
        print("✓ on_recovery callback fired")


# =============================================================================
# STATUS
# =============================================================================


class TestHeartbeatStatus:
    """Test status reporting."""

    def test_status_includes_all_fields(self, monitor: HeartbeatMonitor):
        """Status includes all required fields."""
        monitor.beat()
        status = monitor.get_status()

        assert "state" in status
        assert "beat_count" in status
        assert "missed_beats" in status
        assert "interval" in status
        assert "miss_threshold" in status
        print("✓ Status includes all fields")

    def test_last_beat_age(self, monitor: HeartbeatMonitor):
        """last_beat_age tracks time since beat."""
        monitor.beat()
        time.sleep(0.05)

        age = monitor.last_beat_age
        assert age is not None
        assert age >= 0.05
        print(f"✓ Last beat age: {age:.3f}s")


# =============================================================================
# EMITTER
# =============================================================================


class TestHeartbeatEmitter:
    """Test heartbeat emitter."""

    def test_emitter_starts_and_stops(self, monitor: HeartbeatMonitor):
        """Emitter can start and stop."""
        emitter = HeartbeatEmitter(monitor, interval=0.05)

        emitter.start()
        assert emitter.is_running
        time.sleep(0.1)

        emitter.stop()
        assert not emitter.is_running
        print("✓ Emitter starts and stops")

    def test_emitter_sends_beats(self, monitor: HeartbeatMonitor):
        """Emitter sends beats automatically."""
        emitter = HeartbeatEmitter(monitor, interval=0.05)
        emitter.start()

        time.sleep(0.2)
        emitter.stop()

        status = monitor.get_status()
        assert status["beat_count"] >= 3
        print(f"✓ Emitter sent {status['beat_count']} beats")


# =============================================================================
# CHAOS
# =============================================================================


class TestHeartbeatChaos:
    """Chaos tests for heartbeat."""

    def test_rapid_beats_stable(self, monitor: HeartbeatMonitor):
        """Rapid beats keep state ALIVE."""
        for _ in range(100):
            monitor.beat()
            assert monitor.state == HeartbeatState.ALIVE

        print("✓ 100 rapid beats stable")

    def test_flapping_state(self, monitor: HeartbeatMonitor):
        """State handles flapping correctly."""
        states = []

        for i in range(5):
            monitor.beat()
            states.append(monitor.state)
            time.sleep(0.35)  # Go DEAD
            states.append(monitor.state)

        # Should see alternating ALIVE/DEAD
        alive_count = sum(1 for s in states if s == HeartbeatState.ALIVE)
        dead_count = sum(1 for s in states if s == HeartbeatState.DEAD)

        assert alive_count >= 4
        assert dead_count >= 4
        print(f"✓ Flapping handled: {alive_count} ALIVE, {dead_count} DEAD")

    def test_reset_clears_state(self, monitor: HeartbeatMonitor):
        """Reset clears all state."""
        monitor.beat()
        monitor.beat()
        monitor.beat()

        monitor.reset()

        assert monitor.state == HeartbeatState.DEAD
        status = monitor.get_status()
        assert status["beat_count"] == 0
        print("✓ Reset clears state")
