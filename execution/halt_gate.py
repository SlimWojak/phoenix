"""
Execution Halt Gate — Halt-first wiring + Sentinel enforcement.

The halt gate enforces INV-GOV-HALT-BEFORE-ACTION:
- EVERY action must check halt_signal FIRST
- If halted, action is BLOCKED
- No bypasses allowed

S53 JANK_NUKE: BoundsSentinel.intercept() wired here (single chokepoint).
- INV-SENTINEL-WIRED-1: intercept() called on every capital mutation
- INV-SENTINEL-FAIL-CLOSED-1: sentinel exception → HALT, never continue

INVARIANTS:
- INV-GOV-HALT-BEFORE-ACTION: halt check precedes any action
- INV-HALT-1: halt_local_latency < 50ms
- INV-SENTINEL-WIRED-1: sentinel intercept on every capital mutation
- INV-SENTINEL-FAIL-CLOSED-1: sentinel crash → HALT
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar

if TYPE_CHECKING:
    from .intent import ExecutionIntent
    from governance.sentinel import GovernanceSentinel, SentinelResult

logger = logging.getLogger(__name__)

# =============================================================================
# EXCEPTIONS
# =============================================================================


class HaltGateViolation(Exception):
    """Raised when action attempted without halt check."""

    def __init__(self, action: str):
        self.action = action
        super().__init__(
            f"INV-GOV-HALT-BEFORE-ACTION violated: "
            f"Action '{action}' attempted without halt check"
        )


class HaltBlockedError(Exception):
    """Raised when action blocked by active halt."""

    def __init__(self, action: str, halt_id: str):
        self.action = action
        self.halt_id = halt_id
        super().__init__(f"Action '{action}' blocked by halt signal {halt_id}")


class SentinelHaltError(HaltBlockedError):
    """Raised when sentinel intercept fails (bounds breach or crash)."""

    def __init__(self, action: str, breach_detail: str):
        super().__init__(action, f"SENTINEL:{breach_detail}")
        self.breach_detail = breach_detail


# =============================================================================
# BREACH BEAD
# =============================================================================


@dataclass(frozen=True)
class BreachBead:
    """Immutable record of a sentinel breach. Emitted on every halt."""

    intent_id: str
    lease_id: str
    breach_reason: str
    world_time: datetime
    knowledge_time: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# HALT GATE
# =============================================================================


@dataclass
class HaltCheckResult:
    """Result of halt check."""

    checked: bool
    halted: bool
    halt_id: str | None
    check_time_ms: float
    timestamp: datetime


class HaltGate:
    """
    Halt gate enforcing halt-first pattern.

    Usage:
        gate = HaltGate(halt_signal_fn)
        gate.check_before('submit_order')  # Must call before action
        # ... do action ...
    """

    def __init__(
        self,
        halt_signal_fn: Callable[[], bool],
        sentinel: GovernanceSentinel | None = None,
        state_fn: Callable[[], dict[str, Any]] | None = None,
    ):
        """
        Initialize halt gate.

        Args:
            halt_signal_fn: Function returning True if halted
            sentinel: Optional BoundsSentinel for intercept on every check
            state_fn: Provides current execution state for sentinel
        """
        self._halt_signal_fn = halt_signal_fn
        self._sentinel = sentinel
        self._state_fn = state_fn
        self._last_check: HaltCheckResult | None = None
        self._action_attempted: str | None = None
        self._breach_log: list[BreachBead] = []

    def check_before(
        self, action: str, *, intent_id: str = "", lease_id: str = ""
    ) -> HaltCheckResult:
        """
        Check halt signal + sentinel before action.

        INV-GOV-HALT-BEFORE-ACTION: MUST call before any capital action.
        INV-SENTINEL-WIRED-1: sentinel intercept fires on every call (if wired).

        Raises:
            HaltBlockedError: If halt signal is active
            SentinelHaltError: If sentinel intercept fails or crashes
        """
        start = time.perf_counter()

        halted = self._halt_signal_fn()
        halt_id = None

        end = time.perf_counter()
        check_time_ms = (end - start) * 1000

        result = HaltCheckResult(
            checked=True,
            halted=halted,
            halt_id=halt_id if halted else None,
            check_time_ms=check_time_ms,
            timestamp=datetime.now(UTC),
        )

        self._last_check = result
        self._action_attempted = action

        if halted:
            raise HaltBlockedError(action, halt_id or "UNKNOWN")

        # INV-SENTINEL-WIRED-1: intercept on every capital mutation
        if self._sentinel is not None:
            self._run_sentinel(action, intent_id=intent_id, lease_id=lease_id)

        return result

    def _run_sentinel(
        self, action: str, *, intent_id: str = "", lease_id: str = ""
    ) -> None:
        """Run sentinel intercept. Fail-closed: any exception → HALT."""
        from governance.sentinel import GovernanceVerdict

        state = self._state_fn() if self._state_fn else {}

        try:
            sentinel_result: SentinelResult = self._sentinel.intercept(state)  # type: ignore[union-attr]  # None guard at line 167
        except Exception as exc:
            # INV-SENTINEL-FAIL-CLOSED-1: crash → HALT
            breach = BreachBead(
                intent_id=intent_id or action,
                lease_id=lease_id,
                breach_reason=f"SENTINEL_CRASH: {exc}",
                world_time=datetime.now(UTC),
            )
            self._breach_log.append(breach)
            logger.error(
                "sentinel_intercept intent_id=%s lease_id=%s decision=CRASH latency_ms=N/A",
                intent_id or action,
                lease_id,
            )
            raise SentinelHaltError(action, f"SENTINEL_CRASH: {exc}") from exc

        # Structured log on every intercept
        logger.info(
            "sentinel_intercept intent_id=%s lease_id=%s decision=%s latency_ms=%.3f",
            intent_id or action,
            lease_id,
            sentinel_result.verdict.value,
            sentinel_result.check_latency_ms,
        )

        if sentinel_result.verdict != GovernanceVerdict.PASS:
            breach = BreachBead(
                intent_id=intent_id or action,
                lease_id=lease_id,
                breach_reason=sentinel_result.breach_detail or sentinel_result.verdict.value,
                world_time=datetime.now(UTC),
            )
            self._breach_log.append(breach)
            raise SentinelHaltError(
                action, sentinel_result.breach_detail or sentinel_result.verdict.value
            )

    @property
    def breach_beads(self) -> list[BreachBead]:
        """Emitted BreachBeads (observable)."""
        return list(self._breach_log)

    def verify_checked(self, action: str) -> None:
        """
        Verify that halt was checked before action.

        Call this to enforce the halt-first pattern.

        Raises:
            HaltGateViolation: If no check was performed
        """
        if self._last_check is None:
            raise HaltGateViolation(action)

        if self._action_attempted != action:
            raise HaltGateViolation(action)

    def get_last_check(self) -> HaltCheckResult | None:
        """Get result of last halt check."""
        return self._last_check

    def clear(self) -> None:
        """Clear last check (for testing)."""
        self._last_check = None
        self._action_attempted = None


# =============================================================================
# HALT-GATED DECORATOR
# =============================================================================


_P = ParamSpec("_P")
_R = TypeVar("_R")


def halt_gated(gate: HaltGate) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """
    Decorator to enforce halt-first pattern.

    Usage:
        @halt_gated(gate)
        def submit_order(...):
            ...
    """

    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            name: str = getattr(fn, "__name__", "unknown")
            gate.check_before(name)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# EXECUTION GATE COORDINATOR
# =============================================================================


class ExecutionGateCoordinator:
    """
    Coordinates halt gate checks for execution skeleton.

    S27: SKELETON ONLY — no actual execution.
    """

    def __init__(self, halt_signal_fn: Callable[[], bool]):
        self._gate = HaltGate(halt_signal_fn)
        self._blocked_actions: list[dict[str, Any]] = []
        self._passed_actions: list[dict[str, Any]] = []

    def gate_intent(self, intent: "ExecutionIntent") -> bool:
        """
        Gate an execution intent.

        Returns:
            True if intent passes halt gate
            False if blocked
        """
        try:
            self._gate.check_before(f"intent:{intent.intent_id}")
            self._passed_actions.append(
                {
                    "intent_id": intent.intent_id,
                    "timestamp": datetime.now(UTC),
                }
            )
            return True
        except HaltBlockedError:
            self._blocked_actions.append(
                {
                    "intent_id": intent.intent_id,
                    "timestamp": datetime.now(UTC),
                    "reason": "halt_active",
                }
            )
            return False

    def get_blocked_count(self) -> int:
        """Get count of blocked actions."""
        return len(self._blocked_actions)

    def get_passed_count(self) -> int:
        """Get count of passed actions."""
        return len(self._passed_actions)

    def reset_stats(self) -> None:
        """Reset statistics."""
        self._blocked_actions.clear()
        self._passed_actions.clear()
