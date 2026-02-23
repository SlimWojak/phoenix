"""
S52 T2: Dead-man's switch — sentinel silence → HALT.

EXIT_GATE: T2_PASSIVE_BOUNDS
Proof: Sentinel silent > threshold → system halts.

CTO ADDENDUM 1_T2_EXTERNAL_HEARTBEAT:
  Heartbeat detection lives in the EXECUTION LOOP.
  A crashed sentinel cannot self-report.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from governance.sentinel import (
    BoundsSentinel,
    SentinelHeartbeatMonitor,
)


class TestDeadMansSwitch:
    """INV-BOUNDS-HEARTBEAT-1: Silent sentinel triggers HALT."""

    def test_fresh_sentinel_is_alive(self):
        """Sentinel that just executed is alive."""
        sentinel = BoundsSentinel()
        sentinel._record_execution(100_000)

        halts = []
        monitor = SentinelHeartbeatMonitor(
            sentinel=sentinel,
            halt_callback=lambda msg: halts.append(msg),
            threshold_sec=30.0,
        )

        assert monitor.check_liveness() is True
        assert len(halts) == 0

    def test_stale_sentinel_triggers_halt(self):
        """Sentinel that hasn't executed recently triggers HALT."""
        sentinel = BoundsSentinel()
        stale_time = datetime.now(UTC) - timedelta(seconds=60)
        sentinel._last_execution_timestamp = stale_time

        halts = []
        monitor = SentinelHeartbeatMonitor(
            sentinel=sentinel,
            halt_callback=lambda msg: halts.append(msg),
            threshold_sec=30.0,
        )

        assert monitor.check_liveness() is False
        assert len(halts) == 1
        assert "SENTINEL_DEAD" in halts[0]

    def test_never_executed_is_alive(self):
        """Sentinel that never executed yet is treated as alive (startup grace)."""
        sentinel = BoundsSentinel()
        assert sentinel.get_last_execution_timestamp() is None

        halts = []
        monitor = SentinelHeartbeatMonitor(
            sentinel=sentinel,
            halt_callback=lambda msg: halts.append(msg),
            threshold_sec=30.0,
        )

        assert monitor.check_liveness() is True
        assert len(halts) == 0

    def test_halt_only_fires_once(self):
        """Dead sentinel only triggers halt once, not repeatedly."""
        sentinel = BoundsSentinel()
        sentinel._last_execution_timestamp = datetime.now(UTC) - timedelta(seconds=60)

        halts = []
        monitor = SentinelHeartbeatMonitor(
            sentinel=sentinel,
            halt_callback=lambda msg: halts.append(msg),
            threshold_sec=30.0,
        )

        monitor.check_liveness()
        monitor.check_liveness()
        monitor.check_liveness()

        assert len(halts) == 1

    def test_configurable_threshold(self):
        """Threshold is configurable."""
        sentinel = BoundsSentinel()
        sentinel._last_execution_timestamp = datetime.now(UTC) - timedelta(seconds=5)

        halts = []
        tight_monitor = SentinelHeartbeatMonitor(
            sentinel=sentinel,
            halt_callback=lambda msg: halts.append(msg),
            threshold_sec=3.0,
        )

        assert tight_monitor.check_liveness() is False
        assert len(halts) == 1

    def test_reset_allows_re_trigger(self):
        """After reset, monitor can trigger again."""
        sentinel = BoundsSentinel()
        sentinel._last_execution_timestamp = datetime.now(UTC) - timedelta(seconds=60)

        halts = []
        monitor = SentinelHeartbeatMonitor(
            sentinel=sentinel,
            halt_callback=lambda msg: halts.append(msg),
            threshold_sec=30.0,
        )

        monitor.check_liveness()
        assert monitor.is_halted is True

        monitor.reset()
        assert monitor.is_halted is False
