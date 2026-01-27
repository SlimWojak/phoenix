"""
Execution Halt Gate — Halt-first wiring.

SPRINT: S27.0
STATUS: SKELETON
CAPITAL: DISABLED

The halt gate enforces INV-GOV-HALT-BEFORE-ACTION:
- EVERY action must check halt_signal FIRST
- If halted, action is BLOCKED
- No bypasses allowed

FORBIDDEN:
- Live order submission
- Halt bypass

INVARIANTS:
- INV-GOV-HALT-BEFORE-ACTION: halt check precedes any action
- INV-HALT-1: halt_local_latency < 50ms
"""

import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

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

    def __init__(self, halt_signal_fn: Callable[[], bool]):
        """
        Initialize halt gate.

        Args:
            halt_signal_fn: Function returning True if halted
        """
        self._halt_signal_fn = halt_signal_fn
        self._last_check: HaltCheckResult | None = None
        self._action_attempted: str | None = None

    def check_before(self, action: str) -> HaltCheckResult:
        """
        Check halt signal before action.

        INV-GOV-HALT-BEFORE-ACTION: MUST call before any capital action.

        Args:
            action: Name of action to be performed

        Returns:
            HaltCheckResult

        Raises:
            HaltBlockedError: If halt signal is active
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

        return result

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


def halt_gated(gate: HaltGate):
    """
    Decorator to enforce halt-first pattern.

    Usage:
        @halt_gated(gate)
        def submit_order(...):
            ...
    """

    def decorator(fn):
        def wrapper(*args, **kwargs):
            # Check halt before action
            gate.check_before(fn.__name__)
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
        self._blocked_actions: list = []
        self._passed_actions: list = []

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
