"""
Health State Machine — S40 Self-Healing Track A
================================================

Tracks system health and triggers appropriate responses.
No 3am wake-ups. System knows when to escalate.

STATES:
  HEALTHY: Normal operation
  DEGRADED: Minor issues, logging/batching alerts
  CRITICAL: Major issues, immediate alert
  HALTED: System stopped, human intervention required

INVARIANTS:
  INV-HEALTH-1: CRITICAL → Telegram alert within 30s
  INV-HEALTH-2: HALTED → halt_local() invoked
  INV-HEAL-REENTRANCY: Repeated failures → 1 alert (not N)
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


# =============================================================================
# ENUMS
# =============================================================================


class HealthState(str, Enum):
    """System health states."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    HALTED = "HALTED"


# =============================================================================
# CONFIGURATION
# =============================================================================


@dataclass
class HealthConfig:
    """Configuration for health state machine."""

    # Failure thresholds
    degraded_threshold: int = 3  # failures in window → DEGRADED
    critical_threshold: int = 5  # failures in window → CRITICAL
    halt_threshold: int = 10  # failures in window → HALTED

    # Time windows
    failure_window: float = 60.0  # seconds to count failures
    recovery_window: float = 30.0  # seconds of success → recovery

    # Alert suppression (INV-HEAL-REENTRANCY)
    alert_cooldown: float = 60.0  # min seconds between alerts
    batch_window: float = 30.0  # batch DEGRADED alerts


# =============================================================================
# HEALTH STATE MACHINE
# =============================================================================


@dataclass
class HealthStateMachine:
    """
    Finite state machine for system health tracking.

    Usage:
        hsm = HealthStateMachine(
            name="river",
            alert_callback=send_telegram,
            halt_callback=halt_local,
        )

        # Record events
        hsm.record_failure("data_fetch")
        hsm.record_success("data_fetch")

        # Check state
        if hsm.state == HealthState.CRITICAL:
            # Take action

    INVARIANTS:
      INV-HEALTH-1: CRITICAL → alert_callback within 30s
      INV-HEALTH-2: HALTED → halt_callback invoked
      INV-HEAL-REENTRANCY: N failures in 1s → 1 alert
    """

    name: str
    config: HealthConfig = field(default_factory=HealthConfig)

    # Callbacks
    alert_callback: Callable[[str, HealthState, str], None] | None = None
    halt_callback: Callable[[], None] | None = None

    # Internal state
    _state: HealthState = field(default=HealthState.HEALTHY, repr=False)
    _failures: deque = field(default_factory=lambda: deque(maxlen=1000), repr=False)
    _successes: deque = field(default_factory=lambda: deque(maxlen=1000), repr=False)
    _last_alert_time: dict = field(default_factory=dict, repr=False)
    _pending_degraded_alerts: list = field(default_factory=list, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # State entry timestamps
    _state_entered_at: float = field(default_factory=time.monotonic, repr=False)
    _halt_invoked: bool = field(default=False, repr=False)

    @property
    def state(self) -> HealthState:
        """Current health state."""
        with self._lock:
            return self._state

    def record_failure(self, component: str, error: str = "") -> HealthState:
        """
        Record a failure event.

        Args:
            component: Name of failing component
            error: Optional error message

        Returns:
            New health state after processing
        """
        now = time.monotonic()

        with self._lock:
            # Record failure timestamp
            self._failures.append((now, component, error))

            # Count recent failures
            failure_count = self._count_recent_failures(now)

            # Determine new state
            old_state = self._state
            new_state = self._compute_new_state(failure_count)

            if new_state != old_state:
                self._transition_to(new_state, component, error)

            return self._state

    def record_success(self, component: str) -> HealthState:
        """
        Record a success event.

        Args:
            component: Name of successful component

        Returns:
            New health state after processing
        """
        now = time.monotonic()

        with self._lock:
            self._successes.append((now, component))

            # Check recovery conditions
            if self._state in (HealthState.DEGRADED, HealthState.CRITICAL):
                if self._should_recover(now):
                    self._transition_to(HealthState.HEALTHY, component, "recovery")

            return self._state

    def force_halt(self, reason: str = "manual") -> None:
        """
        Force immediate halt state.

        Human override to HALTED.
        """
        with self._lock:
            self._transition_to(HealthState.HALTED, "manual", reason)

    def reset(self) -> None:
        """
        Reset to HEALTHY state.

        Admin override only.
        """
        with self._lock:
            self._state = HealthState.HEALTHY
            self._failures.clear()
            self._successes.clear()
            self._halt_invoked = False
            self._state_entered_at = time.monotonic()

    def _count_recent_failures(self, now: float) -> int:
        """Count failures within the failure window."""
        cutoff = now - self.config.failure_window
        return sum(1 for ts, _, _ in self._failures if ts > cutoff)

    def _should_recover(self, now: float) -> bool:
        """Check if we should recover to HEALTHY."""
        # Need sustained success period
        cutoff = now - self.config.recovery_window
        recent_successes = sum(1 for ts, _ in self._successes if ts > cutoff)
        recent_failures = sum(1 for ts, _, _ in self._failures if ts > cutoff)

        # Recovery: more successes than failures, minimum success count
        return recent_successes >= 3 and recent_failures == 0

    def _compute_new_state(self, failure_count: int) -> HealthState:
        """Compute new state based on failure count."""
        if failure_count >= self.config.halt_threshold:
            return HealthState.HALTED
        elif failure_count >= self.config.critical_threshold:
            return HealthState.CRITICAL
        elif failure_count >= self.config.degraded_threshold:
            return HealthState.DEGRADED
        else:
            return HealthState.HEALTHY

    def _transition_to(
        self, new_state: HealthState, component: str, reason: str
    ) -> None:
        """Execute state transition with side effects."""
        _old_state = self._state  # Reserved for future transition logging
        self._state = new_state
        self._state_entered_at = time.monotonic()

        # Handle state-specific actions
        if new_state == HealthState.HALTED:
            # INV-HEALTH-2: Invoke halt callback
            if not self._halt_invoked and self.halt_callback:
                self._halt_invoked = True
                # Release lock before callback to prevent deadlock
                self._lock.release()
                try:
                    self.halt_callback()
                finally:
                    self._lock.acquire()

            self._send_alert(
                f"HALTED: {self.name}",
                new_state,
                f"Component: {component}. Reason: {reason}",
            )

        elif new_state == HealthState.CRITICAL:
            # INV-HEALTH-1: Immediate alert
            self._send_alert(
                f"CRITICAL: {self.name}",
                new_state,
                f"Component: {component}. Reason: {reason}",
            )

        elif new_state == HealthState.DEGRADED:
            # Batch degraded alerts (INV-HEAL-REENTRANCY)
            self._pending_degraded_alerts.append({
                "component": component,
                "reason": reason,
                "time": time.monotonic(),
            })
            self._maybe_send_batched_degraded_alert()

    def _send_alert(self, title: str, state: HealthState, message: str) -> None:
        """
        Send alert with reentrancy protection.

        INV-HEAL-REENTRANCY: Suppress duplicate alerts within cooldown.
        """
        now = time.monotonic()
        alert_key = f"{state.value}:{title}"

        # Check cooldown
        last_alert = self._last_alert_time.get(alert_key, 0)
        if now - last_alert < self.config.alert_cooldown:
            return  # Suppress (INV-HEAL-REENTRANCY)

        self._last_alert_time[alert_key] = now

        if self.alert_callback:
            # Release lock before callback
            self._lock.release()
            try:
                self.alert_callback(title, state, message)
            finally:
                self._lock.acquire()

    def _maybe_send_batched_degraded_alert(self) -> None:
        """Send batched DEGRADED alerts if window elapsed."""
        if not self._pending_degraded_alerts:
            return

        now = time.monotonic()
        oldest = self._pending_degraded_alerts[0]["time"]

        if now - oldest >= self.config.batch_window:
            count = len(self._pending_degraded_alerts)
            components = set(a["component"] for a in self._pending_degraded_alerts)
            
            self._send_alert(
                f"DEGRADED: {self.name}",
                HealthState.DEGRADED,
                f"{count} issues in {', '.join(components)}",
            )
            self._pending_degraded_alerts.clear()

    def get_status(self) -> dict:
        """Get current health status."""
        now = time.monotonic()
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "state_duration": now - self._state_entered_at,
                "recent_failures": self._count_recent_failures(now),
                "halt_invoked": self._halt_invoked,
                "thresholds": {
                    "degraded": self.config.degraded_threshold,
                    "critical": self.config.critical_threshold,
                    "halt": self.config.halt_threshold,
                },
            }


# =============================================================================
# GLOBAL HEALTH REGISTRY
# =============================================================================


class HealthRegistry:
    """Registry of health state machines."""

    def __init__(self):
        self._machines: dict[str, HealthStateMachine] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self,
        name: str,
        alert_callback: Callable | None = None,
        halt_callback: Callable | None = None,
        config: HealthConfig | None = None,
    ) -> HealthStateMachine:
        """Get existing or create new health FSM."""
        with self._lock:
            if name not in self._machines:
                self._machines[name] = HealthStateMachine(
                    name=name,
                    config=config or HealthConfig(),
                    alert_callback=alert_callback,
                    halt_callback=halt_callback,
                )
            return self._machines[name]

    def get(self, name: str) -> HealthStateMachine | None:
        """Get health FSM by name."""
        with self._lock:
            return self._machines.get(name)

    def all_status(self) -> list[dict]:
        """Get status from all health FSMs."""
        with self._lock:
            return [m.get_status() for m in self._machines.values()]

    def any_critical(self) -> bool:
        """Check if any FSM is CRITICAL or HALTED."""
        with self._lock:
            return any(
                m.state in (HealthState.CRITICAL, HealthState.HALTED)
                for m in self._machines.values()
            )


# Global registry
_global_health_registry = HealthRegistry()


def get_health_fsm(
    name: str,
    alert_callback: Callable | None = None,
    halt_callback: Callable | None = None,
) -> HealthStateMachine:
    """Get or create health FSM from global registry."""
    return _global_health_registry.get_or_create(name, alert_callback, halt_callback)


def get_all_health_status() -> list[dict]:
    """Get health status from all FSMs."""
    return _global_health_registry.all_status()


def any_system_critical() -> bool:
    """Check if any system is CRITICAL or HALTED."""
    return _global_health_registry.any_critical()
