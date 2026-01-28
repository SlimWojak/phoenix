"""
Halt Mechanism — Fast halt signal and cascade propagation

VERSION: 0.2
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md

INVARIANTS:
  INV-HALT-1: halt_local_latency < 50ms (HARD)
  INV-HALT-2: halt_cascade_latency < 500ms (SLO)

DESIGN:
  - request_halt(): NO IO, NO logging, NO propagation
  - propagate_halt(): async cascade to dependents
  - check_halt(): cooperative yield point
"""

import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Optional

from .errors import HaltError
from .types import (
    AckReceipt,
    HaltCascadeReport,
    HaltSignalSetResult,
    LifecycleState,
)

# =============================================================================
# HALT SIGNAL (Thread-safe, minimal latency)
# =============================================================================


class HaltSignal:
    """
    Thread-safe halt signal with minimal latency.

    Design: Uses simple boolean flag with lock.
    NO IO, NO logging in the hot path.
    """

    def __init__(self):
        self._signal = False
        self._halt_id: str | None = None
        self._lock = threading.Lock()
        self._timestamp: datetime | None = None

    def set(self) -> HaltSignalSetResult:
        """
        Set halt signal.

        LATENCY REQUIREMENT: < 50ms (INV-HALT-1)

        Returns:
            HaltSignalSetResult with timing proof
        """
        start = time.perf_counter_ns()

        with self._lock:
            halt_id = str(uuid.uuid4())[:8]
            self._signal = True
            self._halt_id = halt_id
            self._timestamp = datetime.now(UTC)

        end = time.perf_counter_ns()
        latency_ms = (end - start) / 1_000_000

        return HaltSignalSetResult(
            success=True, latency_ms=latency_ms, halt_id=halt_id, timestamp=self._timestamp
        )

    def clear(self) -> None:
        """Clear halt signal (for recovery)."""
        with self._lock:
            self._signal = False
            self._halt_id = None
            self._timestamp = None

    def is_set(self) -> bool:
        """Check if halt signal is set (lock-free read)."""
        return self._signal

    @property
    def halt_id(self) -> str | None:
        """Get current halt ID if set."""
        return self._halt_id

    def check(self) -> None:
        """
        Check halt signal and raise if set.

        Called at yield points.
        """
        if self._signal:
            raise HaltError(self._halt_id or "unknown")


# =============================================================================
# HALT MANAGER (Cascade coordination)
# =============================================================================


@dataclass
class HaltManager:
    """
    Manages halt signal and cascade propagation.

    Coordinates between modules for clean shutdown.
    """

    module_id: str
    signal: HaltSignal = field(default_factory=HaltSignal)
    _dependents: list[str] = field(default_factory=list)
    _dependent_halt_callbacks: dict[str, Callable] = field(default_factory=dict)
    _lifecycle_state: LifecycleState = LifecycleState.RUNNING

    # Timing config
    ACK_TIMEOUT_MS: float = 50.0
    MAX_RETRIES: int = 2
    BACKOFF_MS: float = 10.0

    def register_dependent(
        self, module_id: str, halt_callback: Callable[[str], AckReceipt]
    ) -> None:
        """Register a dependent module for halt propagation."""
        self._dependents.append(module_id)
        self._dependent_halt_callbacks[module_id] = halt_callback

    def get_dependents(self) -> list[str]:
        """Return list of dependent module IDs."""
        return self._dependents.copy()

    def request_halt(self) -> HaltSignalSetResult:
        """
        Request halt (local only, no propagation).

        LATENCY: < 50ms (INV-HALT-1)

        This is the hot path - NO IO, NO logging.
        """
        result = self.signal.set()
        self._lifecycle_state = LifecycleState.STOPPING
        return result

    def propagate_halt(self, halt_id: str) -> HaltCascadeReport:
        """
        Propagate halt to all dependents.

        LATENCY: < 500ms SLO (INV-HALT-2)

        Args:
            halt_id: The halt ID to propagate

        Returns:
            HaltCascadeReport with acknowledgments
        """
        start = time.perf_counter_ns()

        acks_received = []
        acks_failed = []

        for dep_id in self._dependents:
            callback = self._dependent_halt_callbacks.get(dep_id)
            if callback is None:
                acks_failed.append(dep_id)
                continue

            # Try with retries
            ack = self._call_with_retry(callback, halt_id, dep_id)
            if ack:
                acks_received.append(ack)
            else:
                acks_failed.append(dep_id)

        end = time.perf_counter_ns()
        total_latency_ms = (end - start) / 1_000_000

        return HaltCascadeReport(
            halt_id=halt_id,
            propagated_to=self._dependents.copy(),
            acks_received=acks_received,
            acks_failed=acks_failed,
            total_latency_ms=total_latency_ms,
        )

    def _call_with_retry(
        self, callback: Callable[[str], AckReceipt], halt_id: str, dep_id: str
    ) -> AckReceipt | None:
        """Call dependent with retry logic."""
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                start = time.perf_counter_ns()
                ack = callback(halt_id)
                elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000

                if elapsed_ms > self.ACK_TIMEOUT_MS:
                    # Timeout but got response - still accept
                    pass

                return ack

            except Exception:
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_MS / 1000)
                continue

        return None

    def acknowledge_halt(self, halt_id: str) -> AckReceipt:
        """
        Acknowledge halt from upstream.

        Called when a dependent receives halt signal.
        """
        # Set local halt signal
        if not self.signal.is_set():
            self.signal.set()

        self._lifecycle_state = LifecycleState.STOPPING

        return AckReceipt(
            module_id=self.module_id,
            ack=True,
            module_state=self._lifecycle_state,
            timestamp=datetime.now(UTC),
        )

    def check_halt(self) -> None:
        """
        Cooperative yield point.

        MUST be called at declared yield_points.
        Raises HaltError if signal set.
        """
        self.signal.check()

    def clear_halt(self) -> None:
        """
        Clear halt signal and restore RUNNING state.

        IMPORTANT: Only call after root cause resolved.
        This is the programmatic equivalent of RB-004 Step 4.

        Requires human decision - this is NOT called automatically.
        """
        self.signal.clear()
        self._lifecycle_state = LifecycleState.RUNNING

    @property
    def lifecycle_state(self) -> LifecycleState:
        return self._lifecycle_state

    @lifecycle_state.setter
    def lifecycle_state(self, state: LifecycleState) -> None:
        self._lifecycle_state = state


# =============================================================================
# HALT MESH (Global coordination)
# =============================================================================


class HaltMesh:
    """
    Global halt mesh for coordinating across modules.

    Singleton pattern for process-wide halt coordination.
    """

    _instance: Optional["HaltMesh"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "HaltMesh":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._modules: dict[str, HaltManager] = {}
        return cls._instance

    def register(self, manager: HaltManager) -> None:
        """Register a halt manager with the mesh."""
        self._modules[manager.module_id] = manager

    def deregister(self, module_id: str) -> None:
        """Deregister a module from the mesh."""
        self._modules.pop(module_id, None)

    def get_manager(self, module_id: str) -> HaltManager | None:
        """Get halt manager for a module."""
        return self._modules.get(module_id)

    def global_halt(self) -> dict[str, HaltSignalSetResult]:
        """
        Trigger global halt across all modules.

        Returns:
            Dict of module_id -> HaltSignalSetResult
        """
        results = {}
        for module_id, manager in self._modules.items():
            results[module_id] = manager.request_halt()
        return results

    def clear_all(self) -> None:
        """Clear all halt signals (for testing/recovery)."""
        for manager in self._modules.values():
            manager.signal.clear()
            manager.lifecycle_state = LifecycleState.RUNNING
