"""
Degradation Manager — S40 Track B
=================================

Graceful degradation cascade: T2 → T1 → T0.
DEGRADED = no trading, even for existing strategies.

INVARIANTS:
  INV-IBKR-DEGRADE-1: T2 blocked within 1s of disconnect
  INV-IBKR-DEGRADE-2: No T2 allowed in DEGRADED state
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable

from governance.health_fsm import HealthStateMachine


# =============================================================================
# ENUMS
# =============================================================================


class DegradationLevel(str, Enum):
    """Degradation levels corresponding to blocked tiers."""

    NONE = "NONE"  # All tiers allowed
    SOFT = "SOFT"  # T2 blocked, T1/T0 allowed
    HARD = "HARD"  # T2/T1 blocked, T0 allowed
    TOTAL = "TOTAL"  # All tiers blocked (system halted)


# =============================================================================
# EXCEPTIONS
# =============================================================================


class TierBlockedError(Exception):
    """Raised when operation blocked due to degradation."""

    def __init__(self, tier: int, level: DegradationLevel, reason: str):
        self.tier = tier
        self.level = level
        self.reason = reason
        super().__init__(
            f"Tier {tier} operation blocked. "
            f"Degradation: {level.value}. Reason: {reason}"
        )


# =============================================================================
# DEGRADATION MANAGER
# =============================================================================


@dataclass
class DegradationManager:
    """
    Manages graceful degradation cascade.

    Tiers:
      T0: Read-only (positions, prices, status)
      T1: Position changes (close only, no new)
      T2: Full trading (new orders, modifications)

    Cascade: T2 → T1 → T0
      - On disconnect: Block T2 immediately
      - On prolonged disconnect: Block T1
      - On critical failure: Block all (halt)

    Usage:
        dm = DegradationManager(health_fsm)

        # Before any T2 operation:
        dm.check_tier(2)  # Raises if blocked

        # On disconnect:
        dm.trigger_degradation("IBKR disconnect")

    INVARIANTS:
      INV-IBKR-DEGRADE-1: T2 blocked within 1s of disconnect
      INV-IBKR-DEGRADE-2: No T2 in DEGRADED state
    """

    health_fsm: HealthStateMachine | None = None

    # Callbacks
    on_degrade: Callable[[DegradationLevel, str], None] | None = None
    on_restore: Callable[[], None] | None = None

    # Configuration
    soft_degradation_delay: float = 0.0  # Immediate T2 block
    hard_degradation_delay: float = 30.0  # T1 block after 30s

    # Internal state
    _level: DegradationLevel = field(default=DegradationLevel.NONE, repr=False)
    _degraded_at: float | None = field(default=None, repr=False)
    _reason: str = field(default="", repr=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    # Metrics
    _degradation_count: int = field(default=0, repr=False)
    _blocked_operations: int = field(default=0, repr=False)

    @property
    def level(self) -> DegradationLevel:
        """Current degradation level."""
        with self._lock:
            return self._level

    @property
    def is_degraded(self) -> bool:
        """Check if any degradation active."""
        with self._lock:
            return self._level != DegradationLevel.NONE

    def trigger_degradation(self, reason: str) -> DegradationLevel:
        """
        Trigger degradation cascade.

        INV-IBKR-DEGRADE-1: T2 blocked within 1s
        """
        now = time.monotonic()

        with self._lock:
            if self._level == DegradationLevel.NONE:
                self._degraded_at = now
                self._degradation_count += 1

            self._level = DegradationLevel.SOFT  # T2 blocked immediately
            self._reason = reason

            # Update health FSM if connected
            if self.health_fsm:
                self.health_fsm.record_failure("degradation", reason)

            level = self._level

        # Callback outside lock
        if self.on_degrade:
            self.on_degrade(level, reason)

        return level

    def escalate(self) -> DegradationLevel:
        """
        Escalate degradation level.

        SOFT → HARD → TOTAL
        """
        with self._lock:
            if self._level == DegradationLevel.SOFT:
                self._level = DegradationLevel.HARD
            elif self._level == DegradationLevel.HARD:
                self._level = DegradationLevel.TOTAL

            level = self._level
            reason = self._reason

        if self.on_degrade:
            self.on_degrade(level, f"Escalated: {reason}")

        return level

    def check_tier(self, tier: int) -> None:
        """
        Check if tier operation is allowed.

        Raises TierBlockedError if blocked.

        INV-IBKR-DEGRADE-2: No T2 in DEGRADED state
        """
        with self._lock:
            level = self._level
            reason = self._reason

            blocked = False
            if level == DegradationLevel.TOTAL:
                blocked = True  # All blocked
            elif level == DegradationLevel.HARD and tier >= 1:
                blocked = True  # T1, T2 blocked
            elif level == DegradationLevel.SOFT and tier >= 2:
                blocked = True  # T2 blocked

            if blocked:
                self._blocked_operations += 1
                raise TierBlockedError(tier, level, reason)

    def can_execute_tier(self, tier: int) -> bool:
        """
        Check if tier allowed (non-raising version).

        Returns True if operation can proceed.
        """
        try:
            self.check_tier(tier)
            return True
        except TierBlockedError:
            return False

    def restore(self, validate_first: bool = True) -> bool:
        """
        Restore from degradation after reconnection.

        INV-IBKR-FLAKEY-3: Restoration requires validation

        Args:
            validate_first: If True, performs health check before restore

        Returns:
            True if restored, False if validation failed
        """
        if validate_first:
            # Run validation (in real impl, this would check IBKR state)
            validation_passed = self._run_validation()
            if not validation_passed:
                return False

        with self._lock:
            self._level = DegradationLevel.NONE
            self._degraded_at = None
            self._reason = ""

            # Update health FSM
            if self.health_fsm:
                self.health_fsm.record_success("degradation")

        if self.on_restore:
            self.on_restore()

        return True

    def _run_validation(self) -> bool:
        """
        Run pre-restoration validation.

        In real implementation:
          - Check IBKR connection state
          - Verify account access
          - Confirm position sync
        """
        # Placeholder: always passes in base implementation
        # Override in subclass for real validation
        return True

    def get_status(self) -> dict:
        """Get degradation status."""
        with self._lock:
            degraded_duration = None
            if self._degraded_at is not None:
                degraded_duration = time.monotonic() - self._degraded_at

            return {
                "level": self._level.value,
                "is_degraded": self._level != DegradationLevel.NONE,
                "reason": self._reason,
                "degraded_duration": degraded_duration,
                "degradation_count": self._degradation_count,
                "blocked_operations": self._blocked_operations,
                "tiers_allowed": self._get_allowed_tiers(),
            }

    def _get_allowed_tiers(self) -> list[int]:
        """Get list of currently allowed tiers."""
        if self._level == DegradationLevel.NONE:
            return [0, 1, 2]
        elif self._level == DegradationLevel.SOFT:
            return [0, 1]
        elif self._level == DegradationLevel.HARD:
            return [0]
        else:
            return []


# =============================================================================
# TIER GUARD DECORATOR
# =============================================================================


def require_tier(tier: int, manager: DegradationManager):
    """
    Decorator to guard functions by tier.

    Usage:
        @require_tier(2, degradation_manager)
        def place_order(order):
            ...
    """
    def decorator(fn):
        def wrapper(*args, **kwargs):
            manager.check_tier(tier)
            return fn(*args, **kwargs)
        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper
    return decorator
