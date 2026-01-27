"""
Promotion Checklist — Safety validation
=======================================

S32: EXECUTION_PATH

Comprehensive checklist for promotion from Shadow to Live.

INVARIANTS:
- INV-PROMOTION-SAFE-1: Block if kill flags active
- INV-PROMOTION-SAFE-2: Block if unresolved drift

WATCHPOINT WP_D1: Hard blocks on:
- Active kill flags
- Unresolved STALLED positions
- Unresolved reconciliation drift
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class CheckStatus(Enum):
    """Status of a checklist item."""

    PASS = "PASS"  # noqa: S105
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    """Result of a single checklist item."""

    name: str
    status: CheckStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    is_blocker: bool = False

    @property
    def passed(self) -> bool:
        """Check if this item passed."""
        return self.status == CheckStatus.PASS

    @property
    def blocked(self) -> bool:
        """Check if this item blocks promotion."""
        return self.is_blocker and self.status == CheckStatus.FAIL


@dataclass
class ChecklistResult:
    """Result of full checklist evaluation."""

    checks: list[CheckResult] = field(default_factory=list)
    evaluated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def all_passed(self) -> bool:
        """Check if all items passed."""
        return all(c.passed for c in self.checks)

    @property
    def has_blockers(self) -> bool:
        """Check if any blockers failed."""
        return any(c.blocked for c in self.checks)

    @property
    def blockers(self) -> list[CheckResult]:
        """Get list of failed blockers."""
        return [c for c in self.checks if c.blocked]

    @property
    def warnings(self) -> list[CheckResult]:
        """Get list of warnings."""
        return [c for c in self.checks if c.status == CheckStatus.WARN]

    @property
    def can_promote(self) -> bool:
        """Check if promotion can proceed."""
        return not self.has_blockers

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "all_passed": self.all_passed,
            "has_blockers": self.has_blockers,
            "can_promote": self.can_promote,
            "evaluated_at": self.evaluated_at.isoformat(),
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "is_blocker": c.is_blocker,
                }
                for c in self.checks
            ],
            "blockers": [c.name for c in self.blockers],
            "warnings": [c.name for c in self.warnings],
        }


class PromotionChecklist:
    """
    Promotion checklist validator.

    Validates all requirements before Shadow → Live promotion.

    WATCHPOINT WP_D1 HARD BLOCKS:
    - Assert NO active kill flags
    - Assert NO unresolved STALLED positions
    - Assert NO unresolved reconciliation drift
    """

    def __init__(
        self,
        check_kill_flags: Callable[[], bool] | None = None,
        check_stalled_positions: Callable[[], int] | None = None,
        check_unresolved_drift: Callable[[], int] | None = None,
        check_shadow_sessions: Callable[[], int] | None = None,
        check_shadow_performance: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize checklist.

        Args:
            check_kill_flags: Returns True if any kill flag active
            check_stalled_positions: Returns count of STALLED positions
            check_unresolved_drift: Returns count of unresolved drifts
            check_shadow_sessions: Returns count of shadow sessions
            check_shadow_performance: Returns performance metrics
        """
        self._check_kill_flags = check_kill_flags
        self._check_stalled_positions = check_stalled_positions
        self._check_unresolved_drift = check_unresolved_drift
        self._check_shadow_sessions = check_shadow_sessions
        self._check_shadow_performance = check_shadow_performance

    def evaluate(self) -> ChecklistResult:
        """
        Evaluate all checklist items.

        Returns:
            ChecklistResult with all check results
        """
        results = ChecklistResult()

        # WP_D1: Hard blockers
        results.checks.append(self._check_kill_flag_blocker())
        results.checks.append(self._check_stalled_blocker())
        results.checks.append(self._check_drift_blocker())

        # Duration requirements
        results.checks.append(self._check_session_count())

        # Performance recording (not blocking, just recording)
        results.checks.append(self._check_performance_recorded())

        return results

    def _check_kill_flag_blocker(self) -> CheckResult:
        """
        WP_D1: Check for active kill flags.

        INV-PROMOTION-SAFE-1: Block if kill flags active.
        """
        if self._check_kill_flags is None:
            return CheckResult(
                name="kill_flags",
                status=CheckStatus.SKIP,
                message="No kill flag checker configured",
                is_blocker=True,
            )

        try:
            has_kill = self._check_kill_flags()
            if has_kill:
                return CheckResult(
                    name="kill_flags",
                    status=CheckStatus.FAIL,
                    message="Active kill flag(s) detected",
                    is_blocker=True,
                )
            return CheckResult(
                name="kill_flags",
                status=CheckStatus.PASS,
                message="No active kill flags",
                is_blocker=True,
            )
        except Exception as e:
            return CheckResult(
                name="kill_flags",
                status=CheckStatus.FAIL,
                message=f"Error checking kill flags: {e}",
                is_blocker=True,
            )

    def _check_stalled_blocker(self) -> CheckResult:
        """
        WP_D1: Check for unresolved STALLED positions.

        Positions in STALLED state indicate broker issues that must
        be resolved before promotion.
        """
        if self._check_stalled_positions is None:
            return CheckResult(
                name="stalled_positions",
                status=CheckStatus.SKIP,
                message="No stalled checker configured",
                is_blocker=True,
            )

        try:
            stalled_count = self._check_stalled_positions()
            if stalled_count > 0:
                return CheckResult(
                    name="stalled_positions",
                    status=CheckStatus.FAIL,
                    message=f"{stalled_count} STALLED position(s) exist",
                    details={"count": stalled_count},
                    is_blocker=True,
                )
            return CheckResult(
                name="stalled_positions",
                status=CheckStatus.PASS,
                message="No STALLED positions",
                is_blocker=True,
            )
        except Exception as e:
            return CheckResult(
                name="stalled_positions",
                status=CheckStatus.FAIL,
                message=f"Error checking stalled: {e}",
                is_blocker=True,
            )

    def _check_drift_blocker(self) -> CheckResult:
        """
        WP_D1: Check for unresolved reconciliation drift.

        INV-PROMOTION-SAFE-2: Block if unresolved drift.
        """
        if self._check_unresolved_drift is None:
            return CheckResult(
                name="reconciliation_drift",
                status=CheckStatus.SKIP,
                message="No drift checker configured",
                is_blocker=True,
            )

        try:
            drift_count = self._check_unresolved_drift()
            if drift_count > 0:
                return CheckResult(
                    name="reconciliation_drift",
                    status=CheckStatus.FAIL,
                    message=f"{drift_count} unresolved drift(s) exist",
                    details={"count": drift_count},
                    is_blocker=True,
                )
            return CheckResult(
                name="reconciliation_drift",
                status=CheckStatus.PASS,
                message="No unresolved drift",
                is_blocker=True,
            )
        except Exception as e:
            return CheckResult(
                name="reconciliation_drift",
                status=CheckStatus.FAIL,
                message=f"Error checking drift: {e}",
                is_blocker=True,
            )

    def _check_session_count(self) -> CheckResult:
        """Check minimum shadow sessions (not a blocker, just warning)."""
        if self._check_shadow_sessions is None:
            return CheckResult(
                name="shadow_sessions",
                status=CheckStatus.SKIP,
                message="No session counter configured",
                is_blocker=False,
            )

        try:
            session_count = self._check_shadow_sessions()
            min_sessions = 20  # Configurable
            if session_count < min_sessions:
                return CheckResult(
                    name="shadow_sessions",
                    status=CheckStatus.WARN,
                    message=f"Only {session_count}/{min_sessions} sessions",
                    details={"count": session_count, "minimum": min_sessions},
                    is_blocker=False,
                )
            return CheckResult(
                name="shadow_sessions",
                status=CheckStatus.PASS,
                message=f"{session_count} sessions (>= {min_sessions})",
                details={"count": session_count, "minimum": min_sessions},
                is_blocker=False,
            )
        except Exception as e:
            return CheckResult(
                name="shadow_sessions",
                status=CheckStatus.WARN,
                message=f"Error counting sessions: {e}",
                is_blocker=False,
            )

    def _check_performance_recorded(self) -> CheckResult:
        """Check that performance metrics are recorded."""
        if self._check_shadow_performance is None:
            return CheckResult(
                name="performance_recorded",
                status=CheckStatus.SKIP,
                message="No performance checker configured",
                is_blocker=False,
            )

        try:
            perf = self._check_shadow_performance()
            if not perf:
                return CheckResult(
                    name="performance_recorded",
                    status=CheckStatus.WARN,
                    message="No performance data",
                    is_blocker=False,
                )
            return CheckResult(
                name="performance_recorded",
                status=CheckStatus.PASS,
                message="Performance recorded",
                details=perf,
                is_blocker=False,
            )
        except Exception as e:
            return CheckResult(
                name="performance_recorded",
                status=CheckStatus.WARN,
                message=f"Error getting performance: {e}",
                is_blocker=False,
            )
