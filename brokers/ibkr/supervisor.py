"""
IBKR Supervisor — S40 Track B
=============================

Shadow process OUTSIDE main trading loop.
Watches connector heartbeat, triggers degradation.

Principle: Supervisor cannot be killed by connector crash.

INVARIANTS:
  INV-IBKR-FLAKEY-2: Supervisor survives connector crash
  INV-SUPERVISOR-1: Supervisor death → immediate alert
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol

from governance.circuit_breaker import CircuitBreaker
from governance.health_fsm import HealthStateMachine, HealthState

from .heartbeat import HeartbeatMonitor, HeartbeatState
from .degradation import DegradationManager, DegradationLevel


# =============================================================================
# PROTOCOLS
# =============================================================================


class IBKRConnectorProtocol(Protocol):
    """Protocol for IBKR connector (for testing)."""

    def is_connected(self) -> bool:
        """Check if connector is connected."""
        ...


# =============================================================================
# ENUMS
# =============================================================================


class SupervisorState(str, Enum):
    """Supervisor states."""

    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    ALERTING = "ALERTING"  # Degradation active


# =============================================================================
# SUPERVISOR
# =============================================================================


@dataclass
class IBKRSupervisor:
    """
    Shadow supervisor running OUTSIDE main trading loop.

    Monitors connector heartbeat and triggers degradation cascade
    when connector becomes unresponsive.

    Key property: Supervisor runs in separate thread and survives
    connector crashes.

    Usage:
        supervisor = IBKRSupervisor(
            connector=ibkr_connector,
            on_alert=send_telegram,
        )
        supervisor.start()

        # In connector main loop:
        supervisor.heartbeat.beat()

    INVARIANTS:
      INV-IBKR-FLAKEY-2: Survives connector crash
      INV-SUPERVISOR-1: Death → alert
    """

    # Connector to monitor (can be None for testing)
    connector: IBKRConnectorProtocol | None = None

    # Configuration
    heartbeat_interval: float = 5.0
    miss_threshold: int = 3
    check_interval: float = 1.0  # How often supervisor checks

    # Callbacks
    on_alert: Callable[[str, str], None] | None = None
    on_degradation: Callable[[DegradationLevel, str], None] | None = None
    on_recovery: Callable[[], None] | None = None

    # Components (auto-created if not provided)
    heartbeat: HeartbeatMonitor | None = None
    degradation: DegradationManager | None = None
    health_fsm: HealthStateMachine | None = None
    circuit_breaker: CircuitBreaker | None = None

    # Internal state
    _state: SupervisorState = field(default=SupervisorState.STOPPED, repr=False)
    _running: bool = field(default=False, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # Metrics
    _degradation_triggers: int = field(default=0, repr=False)
    _recovery_count: int = field(default=0, repr=False)
    _check_count: int = field(default=0, repr=False)

    def __post_init__(self):
        """Initialize components if not provided."""
        if self.heartbeat is None:
            self.heartbeat = HeartbeatMonitor(
                interval=self.heartbeat_interval,
                miss_threshold=self.miss_threshold,
            )

        if self.health_fsm is None:
            self.health_fsm = HealthStateMachine(
                name="ibkr_supervisor",
                alert_callback=self._health_alert_callback,
            )

        if self.degradation is None:
            self.degradation = DegradationManager(
                health_fsm=self.health_fsm,
                on_degrade=self._on_degrade_callback,
                on_restore=self._on_restore_callback,
            )

        if self.circuit_breaker is None:
            self.circuit_breaker = CircuitBreaker(
                name="ibkr_connector",
                failure_threshold=3,
                recovery_timeout=30.0,
            )

    @property
    def state(self) -> SupervisorState:
        """Current supervisor state."""
        with self._lock:
            return self._state

    @property
    def is_running(self) -> bool:
        """Check if supervisor is running."""
        with self._lock:
            return self._running

    @property
    def connector_alive(self) -> bool:
        """Check if connector is alive (via heartbeat)."""
        return self.heartbeat.is_alive

    def start(self) -> None:
        """
        Start supervisor monitoring.

        Runs in separate thread (OUTSIDE main trading loop).
        """
        with self._lock:
            if self._running:
                return

            self._running = True
            self._state = SupervisorState.RUNNING
            self._thread = threading.Thread(
                target=self._supervisor_loop,
                name="IBKRSupervisor",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop supervisor monitoring."""
        with self._lock:
            self._running = False

        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

        with self._lock:
            self._state = SupervisorState.STOPPED

    def force_degradation(self, reason: str = "manual") -> None:
        """
        Force immediate degradation.

        Admin override to trigger T2→T1→T0 cascade.
        """
        with self._lock:
            self._degradation_triggers += 1

        self.degradation.trigger_degradation(f"Manual: {reason}")

        if self.on_alert:
            self.on_alert("IBKR_FORCED_DEGRADATION", reason)

    def _supervisor_loop(self) -> None:
        """
        Main supervisor loop.

        Runs in separate thread, survives connector crashes.
        INV-IBKR-FLAKEY-2: This loop keeps running even if connector dies.
        """
        while True:
            with self._lock:
                if not self._running:
                    break
                self._check_count += 1

            try:
                self._check_heartbeat()
            except Exception as e:
                # Supervisor must not crash
                if self.on_alert:
                    self.on_alert("SUPERVISOR_ERROR", str(e))

            time.sleep(self.check_interval)

    def _check_heartbeat(self) -> None:
        """Check heartbeat and trigger degradation if needed."""
        hb_state = self.heartbeat.check()

        with self._lock:
            current_state = self._state

        if hb_state == HeartbeatState.DEAD:
            if current_state != SupervisorState.ALERTING:
                self._trigger_degradation("Heartbeat DEAD")
        elif hb_state == HeartbeatState.DEGRADED:
            # Log but don't escalate yet
            pass
        elif hb_state == HeartbeatState.ALIVE:
            if current_state == SupervisorState.ALERTING:
                self._attempt_recovery()

    def _trigger_degradation(self, reason: str) -> None:
        """Trigger degradation cascade."""
        with self._lock:
            self._state = SupervisorState.ALERTING
            self._degradation_triggers += 1

        self.degradation.trigger_degradation(reason)
        self.circuit_breaker._record_failure()

        if self.on_alert:
            self.on_alert("IBKR_DEGRADATION", reason)

    def _attempt_recovery(self) -> None:
        """Attempt recovery after heartbeat resumes."""
        # INV-IBKR-FLAKEY-3: Validation before restore
        restored = self.degradation.restore(validate_first=True)

        if restored:
            with self._lock:
                self._state = SupervisorState.RUNNING
                self._recovery_count += 1

            if self.on_recovery:
                self.on_recovery()

    def _health_alert_callback(self, title: str, state: HealthState, message: str) -> None:
        """Callback from health FSM."""
        if self.on_alert:
            self.on_alert(f"HEALTH_{title}", message)

    def _on_degrade_callback(self, level: DegradationLevel, reason: str) -> None:
        """Callback when degradation triggered."""
        if self.on_degradation:
            self.on_degradation(level, reason)

    def _on_restore_callback(self) -> None:
        """Callback when degradation restored."""
        if self.on_recovery:
            self.on_recovery()

    def get_status(self) -> dict:
        """Get comprehensive supervisor status."""
        with self._lock:
            return {
                "state": self._state.value,
                "running": self._running,
                "heartbeat": self.heartbeat.get_status(),
                "degradation": self.degradation.get_status(),
                "circuit_breaker": self.circuit_breaker.get_metrics(),
                "metrics": {
                    "degradation_triggers": self._degradation_triggers,
                    "recovery_count": self._recovery_count,
                    "check_count": self._check_count,
                },
            }


# =============================================================================
# WATCHDOG
# =============================================================================


class SupervisorWatchdog:
    """
    Watches the supervisor itself.

    If supervisor dies unexpectedly, sends alert.
    INV-SUPERVISOR-1: Supervisor death → immediate alert
    """

    def __init__(
        self,
        supervisor: IBKRSupervisor,
        check_interval: float = 10.0,
        on_supervisor_dead: Callable[[], None] | None = None,
    ):
        self.supervisor = supervisor
        self.check_interval = check_interval
        self.on_supervisor_dead = on_supervisor_dead
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start watching the supervisor."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._watch_loop,
            name="SupervisorWatchdog",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Stop watching."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _watch_loop(self) -> None:
        """Watch loop."""
        while self._running:
            if not self.supervisor.is_running:
                # Supervisor died!
                if self.on_supervisor_dead:
                    self.on_supervisor_dead()
                break

            time.sleep(self.check_interval)


# =============================================================================
# FACTORY
# =============================================================================


def create_ibkr_supervisor(
    connector: IBKRConnectorProtocol | None = None,
    on_alert: Callable[[str, str], None] | None = None,
) -> tuple[IBKRSupervisor, SupervisorWatchdog]:
    """
    Factory to create supervisor with watchdog.

    Returns:
        Tuple of (supervisor, watchdog)
    """
    supervisor = IBKRSupervisor(
        connector=connector,
        on_alert=on_alert,
    )

    def on_supervisor_dead():
        if on_alert:
            on_alert("SUPERVISOR_DEAD", "IBKRSupervisor has stopped unexpectedly!")

    watchdog = SupervisorWatchdog(
        supervisor=supervisor,
        on_supervisor_dead=on_supervisor_dead,
    )

    return supervisor, watchdog
