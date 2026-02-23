"""
Heartbeat Monitor — S40 Track B
===============================

Tracks connector liveness via heartbeat pulses.
3 missed beats = DEAD declaration.

INVARIANTS:
  INV-IBKR-FLAKEY-1: 3 missed heartbeats → DEAD declaration
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


# =============================================================================
# ENUMS
# =============================================================================


class HeartbeatState(str, Enum):
    """Heartbeat monitor states."""

    ALIVE = "ALIVE"
    DEGRADED = "DEGRADED"  # 1-2 missed beats
    DEAD = "DEAD"  # 3+ missed beats


# =============================================================================
# HEARTBEAT MONITOR
# =============================================================================


@dataclass
class HeartbeatMonitor:
    """
    Monitors heartbeat pulses from a component.

    Usage:
        monitor = HeartbeatMonitor(interval=5.0, miss_threshold=3)

        # In connector loop:
        monitor.beat()  # Record heartbeat

        # In supervisor:
        if not monitor.is_alive:
            trigger_degradation()

    INVARIANTS:
      INV-IBKR-FLAKEY-1: 3 missed beats → DEAD
    """

    interval: float = 5.0  # Expected heartbeat interval (seconds)
    miss_threshold: int = 3  # Beats missed before DEAD

    # Callbacks
    on_degraded: Callable[[], None] | None = None
    on_dead: Callable[[], None] | None = None
    on_recovery: Callable[[], None] | None = None

    # Internal state
    _last_beat_time: float | None = field(default=None, repr=False)
    _state: HeartbeatState = field(default=HeartbeatState.DEAD, repr=False)
    _beat_count: int = field(default=0, repr=False)
    _miss_count: int = field(default=0, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def beat(self) -> None:
        """
        Record a heartbeat pulse.

        Called by the monitored component to signal liveness.
        """
        now = time.monotonic()

        with self._lock:
            was_dead = self._state == HeartbeatState.DEAD
            was_degraded = self._state == HeartbeatState.DEGRADED

            self._last_beat_time = now
            self._beat_count += 1
            self._miss_count = 0
            self._state = HeartbeatState.ALIVE

            # Trigger recovery callback if was dead/degraded
            if (was_dead or was_degraded) and self.on_recovery:
                self._lock.release()
                try:
                    self.on_recovery()
                finally:
                    self._lock.acquire()

    def check(self) -> HeartbeatState:
        """
        Check current heartbeat status.

        Updates state based on time since last beat.
        Returns current state.
        """
        now = time.monotonic()

        with self._lock:
            if self._last_beat_time is None:
                # Never received a beat
                return HeartbeatState.DEAD

            elapsed = now - self._last_beat_time
            missed = int(elapsed / self.interval)

            old_state = self._state

            if missed >= self.miss_threshold:
                self._state = HeartbeatState.DEAD
                self._miss_count = missed
            elif missed >= 1:
                self._state = HeartbeatState.DEGRADED
                self._miss_count = missed
            else:
                self._state = HeartbeatState.ALIVE
                self._miss_count = 0

            # Trigger callbacks on state change
            if old_state != self._state:
                self._trigger_callback(old_state, self._state)

            return self._state

    def _trigger_callback(self, old: HeartbeatState, new: HeartbeatState) -> None:
        """Trigger appropriate callback on state change."""
        callback = None

        if new == HeartbeatState.DEAD and self.on_dead:
            callback = self.on_dead
        elif new == HeartbeatState.DEGRADED and self.on_degraded:
            callback = self.on_degraded
        elif new == HeartbeatState.ALIVE and old != HeartbeatState.ALIVE and self.on_recovery:
            callback = self.on_recovery

        if callback:
            self._lock.release()
            try:
                callback()
            finally:
                self._lock.acquire()

    @property
    def is_alive(self) -> bool:
        """Check if component is alive (with implicit check)."""
        return self.check() == HeartbeatState.ALIVE

    @property
    def state(self) -> HeartbeatState:
        """Current state (with implicit check)."""
        return self.check()

    @property
    def missed_beats(self) -> int:
        """Number of missed beats since last heartbeat."""
        self.check()  # Update state
        with self._lock:
            return self._miss_count

    @property
    def last_beat_age(self) -> float | None:
        """Seconds since last beat (None if never beat)."""
        with self._lock:
            if self._last_beat_time is None:
                return None
            return time.monotonic() - self._last_beat_time

    def reset(self) -> None:
        """Reset monitor state (for testing/admin)."""
        with self._lock:
            self._last_beat_time = None
            self._state = HeartbeatState.DEAD
            self._beat_count = 0
            self._miss_count = 0

    def get_status(self) -> dict:
        """Get detailed status."""
        self.check()  # Update state first
        with self._lock:
            return {
                "state": self._state.value,
                "last_beat_age": (
                    time.monotonic() - self._last_beat_time
                    if self._last_beat_time else None
                ),
                "beat_count": self._beat_count,
                "missed_beats": self._miss_count,
                "interval": self.interval,
                "miss_threshold": self.miss_threshold,
            }


# =============================================================================
# HEARTBEAT EMITTER
# =============================================================================


class HeartbeatEmitter:
    """
    Emits heartbeats to a monitor at regular intervals.

    Use this in the connector to automatically send beats.

    Usage:
        monitor = HeartbeatMonitor()
        emitter = HeartbeatEmitter(monitor, interval=5.0)
        emitter.start()

        # Later
        emitter.stop()
    """

    def __init__(self, monitor: HeartbeatMonitor, interval: float = 5.0):
        self.monitor = monitor
        self.interval = interval
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start emitting heartbeats."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop emitting heartbeats."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _run(self) -> None:
        """Heartbeat emission loop."""
        while self._running:
            self.monitor.beat()
            time.sleep(self.interval)

    @property
    def is_running(self) -> bool:
        """Check if emitter is running."""
        return self._running
