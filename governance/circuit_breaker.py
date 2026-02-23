"""
Circuit Breaker — S40 Self-Healing Track A
==========================================

Prevents cascade failures by breaking circuits under stress.
No 3am wake-ups. System degrades gracefully.

STATES:
  CLOSED: Normal operation, requests pass through
  OPEN: Circuit tripped, all requests rejected
  HALF_OPEN: Testing recovery, single probe allowed

INVARIANTS:
  INV-CIRCUIT-1: OPEN circuit blocks new requests
  INV-CIRCUIT-2: HALF_OPEN allows exactly 1 probe
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


# =============================================================================
# ENUMS
# =============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is blocked."""

    def __init__(self, breaker_name: str, time_until_probe: float = 0.0):
        self.breaker_name = breaker_name
        self.time_until_probe = time_until_probe
        super().__init__(
            f"Circuit '{breaker_name}' is OPEN. "
            f"Retry in {time_until_probe:.1f}s"
        )


class CircuitHalfOpenError(Exception):
    """Raised when probe is already in progress during HALF_OPEN."""

    def __init__(self, breaker_name: str):
        self.breaker_name = breaker_name
        super().__init__(
            f"Circuit '{breaker_name}' is HALF_OPEN with probe in progress"
        )


# =============================================================================
# CIRCUIT BREAKER
# =============================================================================


@dataclass
class CircuitBreaker(Generic[T]):
    """
    Circuit breaker for graceful degradation.

    Usage:
        breaker = CircuitBreaker("river", failure_threshold=3)

        try:
            result = breaker.call(lambda: fetch_data())
        except CircuitOpenError:
            # Circuit is open, use fallback
            result = get_cached_data()

    INVARIANTS:
      INV-CIRCUIT-1: OPEN state blocks all requests
      INV-CIRCUIT-2: HALF_OPEN allows exactly 1 probe
    """

    name: str
    failure_threshold: int = 3
    recovery_timeout: float = 60.0  # seconds before OPEN → HALF_OPEN
    probe_timeout: float = 30.0  # max time for probe call

    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failure_count: int = field(default=0, repr=False)
    _success_count: int = field(default=0, repr=False)
    _last_failure_time: float | None = field(default=None, repr=False)
    _opened_at: float | None = field(default=None, repr=False)
    _probe_in_progress: bool = field(default=False, repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # Metrics
    _total_calls: int = field(default=0, repr=False)
    _total_failures: int = field(default=0, repr=False)
    _total_successes: int = field(default=0, repr=False)
    _total_blocked: int = field(default=0, repr=False)

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        with self._lock:
            return self._check_state_transition()

    def _check_state_transition(self) -> CircuitState:
        """Check if state should transition (called under lock)."""
        if self._state == CircuitState.OPEN:
            # Check if recovery timeout elapsed → HALF_OPEN
            if self._opened_at is not None:
                elapsed = time.monotonic() - self._opened_at
                if elapsed >= self.recovery_timeout:
                    self._state = CircuitState.HALF_OPEN
                    self._probe_in_progress = False

        return self._state

    def call(self, fn: Callable[[], T]) -> T:
        """
        Execute function if circuit allows.

        Raises:
            CircuitOpenError: Circuit is OPEN
            CircuitHalfOpenError: HALF_OPEN with probe in progress

        INV-CIRCUIT-1: OPEN blocks requests
        INV-CIRCUIT-2: HALF_OPEN allows exactly 1 probe
        """
        with self._lock:
            current_state = self._check_state_transition()
            self._total_calls += 1

            if current_state == CircuitState.OPEN:
                # INV-CIRCUIT-1: Block request
                self._total_blocked += 1
                time_until_probe = 0.0
                if self._opened_at is not None:
                    elapsed = time.monotonic() - self._opened_at
                    time_until_probe = max(0, self.recovery_timeout - elapsed)
                raise CircuitOpenError(self.name, time_until_probe)

            if current_state == CircuitState.HALF_OPEN:
                # INV-CIRCUIT-2: Allow exactly 1 probe
                if self._probe_in_progress:
                    self._total_blocked += 1
                    raise CircuitHalfOpenError(self.name)
                self._probe_in_progress = True

        # Execute outside lock to avoid deadlocks
        try:
            result = fn()
            self._record_success()
            return result
        except Exception:
            self._record_failure()
            raise

    def _record_success(self) -> None:
        """Record successful call."""
        with self._lock:
            self._success_count += 1
            self._total_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                # Probe succeeded → CLOSED
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._opened_at = None
                self._probe_in_progress = False

    def _record_failure(self) -> None:
        """Record failed call."""
        with self._lock:
            self._failure_count += 1
            self._total_failures += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed → OPEN
                self._state = CircuitState.OPEN
                self._opened_at = time.monotonic()
                self._probe_in_progress = False

            elif self._state == CircuitState.CLOSED:
                # Check threshold
                if self._failure_count >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._opened_at = time.monotonic()

    def reset(self) -> None:
        """
        Force circuit to CLOSED state.

        Admin override only. Use with caution.
        """
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._opened_at = None
            self._probe_in_progress = False

    def get_metrics(self) -> dict:
        """Return circuit metrics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "total_calls": self._total_calls,
                "total_successes": self._total_successes,
                "total_failures": self._total_failures,
                "total_blocked": self._total_blocked,
                "current_failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
            }

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self.name!r}, state={self._state.value}, "
            f"failures={self._failure_count}/{self.failure_threshold})"
        )


# =============================================================================
# CIRCUIT BREAKER REGISTRY
# =============================================================================


class CircuitBreakerRegistry:
    """
    Registry of circuit breakers by name.

    Usage:
        registry = CircuitBreakerRegistry()
        river_breaker = registry.get_or_create("river", failure_threshold=3)
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = threading.Lock()

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 3,
        recovery_timeout: float = 60.0,
    ) -> CircuitBreaker:
        """Get existing breaker or create new one."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(
                    name=name,
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                )
            return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        """Get breaker by name."""
        with self._lock:
            return self._breakers.get(name)

    def all_metrics(self) -> list[dict]:
        """Get metrics from all breakers."""
        with self._lock:
            return [b.get_metrics() for b in self._breakers.values()]

    def reset_all(self) -> None:
        """Reset all breakers (admin only)."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()


# Global registry
_global_registry = CircuitBreakerRegistry()


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 3,
    recovery_timeout: float = 60.0,
) -> CircuitBreaker:
    """Get or create a circuit breaker from global registry."""
    return _global_registry.get_or_create(name, failure_threshold, recovery_timeout)


def get_all_circuit_metrics() -> list[dict]:
    """Get metrics from all circuit breakers."""
    return _global_registry.all_metrics()
