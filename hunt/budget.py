"""
Budget Enforcement — S38 Track D
================================

Prevent compute explosion. Hard ceiling on variants.
Pre-execution estimate. Abort if exceeded.

INVARIANTS:
  - INV-HUNT-BUDGET: Compute ceiling enforced
  - INV-HUNT-PARTIAL-WATERMARK: Completeness on abort
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from hunt.hypothesis import Hypothesis


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_VARIANTS_DEFAULT = 10000
MAX_VARIANTS_T2_OVERRIDE = 100000
MAX_COMPUTE_SECONDS = 1800  # 30 minutes
MAX_MEMORY_MB = 4096


# =============================================================================
# ENUMS
# =============================================================================


class BudgetStatus(str, Enum):
    """Budget check status."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WARNING = "WARNING"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class BudgetEstimate:
    """Budget estimate for a hypothesis."""

    total_variants: int
    estimated_compute_seconds: float
    estimated_memory_mb: float
    within_budget: bool


@dataclass
class BudgetCheck:
    """Result of budget check."""

    status: BudgetStatus
    reason: str = ""
    suggestion: str = ""


# =============================================================================
# BUDGET ENFORCER
# =============================================================================


class BudgetEnforcer:
    """
    Enforces compute budget.

    Pre-execution check. Abort if exceeded.

    INVARIANT: INV-HUNT-BUDGET
    """

    def __init__(
        self,
        max_variants: int = MAX_VARIANTS_DEFAULT,
        max_variants_t2: int = MAX_VARIANTS_T2_OVERRIDE,
    ) -> None:
        """Initialize enforcer."""
        self._max_variants = max_variants
        self._max_variants_t2 = max_variants_t2

    def estimate(self, hypothesis: Hypothesis) -> BudgetEstimate:
        """
        Estimate compute budget for hypothesis.

        Args:
            hypothesis: Hypothesis to estimate

        Returns:
            BudgetEstimate
        """
        total_variants = hypothesis.grid.total_variants

        # Simplified estimates
        compute_seconds = total_variants * 0.01  # 10ms per variant
        memory_mb = total_variants * 0.1  # 0.1MB per variant

        within_budget = total_variants <= self._max_variants

        return BudgetEstimate(
            total_variants=total_variants,
            estimated_compute_seconds=compute_seconds,
            estimated_memory_mb=memory_mb,
            within_budget=within_budget,
        )

    def check_pre_execution(
        self,
        hypothesis: Hypothesis,
        t2_override: bool = False,
    ) -> BudgetCheck:
        """
        Check budget before execution.

        Args:
            hypothesis: Hypothesis to check
            t2_override: T2 approval for higher limits

        Returns:
            BudgetCheck
        """
        total_variants = hypothesis.grid.total_variants
        max_allowed = self._max_variants_t2 if t2_override else self._max_variants

        # Check against human-declared max
        if hypothesis.budget.max_variants > 0:
            if total_variants > hypothesis.budget.max_variants:
                return BudgetCheck(
                    status=BudgetStatus.REJECTED,
                    reason=f"Grid size ({total_variants}) exceeds declared max_variants ({hypothesis.budget.max_variants})",
                    suggestion="Narrow grid dimensions or increase max_variants",
                )

        # Check against system ceiling
        if total_variants > max_allowed:
            if t2_override:
                return BudgetCheck(
                    status=BudgetStatus.REJECTED,
                    reason=f"Grid size ({total_variants}) exceeds T2 max ({max_allowed})",
                    suggestion="Break into multiple hunts",
                )
            else:
                return BudgetCheck(
                    status=BudgetStatus.REJECTED,
                    reason=f"Grid size ({total_variants}) exceeds max ({max_allowed}). T2 required for larger hunts.",
                    suggestion=f"Request T2 override or narrow to <{max_allowed} variants",
                )

        # Warning if approaching limit
        if total_variants > max_allowed * 0.8:
            return BudgetCheck(
                status=BudgetStatus.WARNING,
                reason=f"Grid size ({total_variants}) approaching limit ({max_allowed})",
            )

        return BudgetCheck(status=BudgetStatus.APPROVED)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "BudgetEnforcer",
    "BudgetEstimate",
    "BudgetCheck",
    "BudgetStatus",
    "MAX_VARIANTS_DEFAULT",
    "MAX_VARIANTS_T2_OVERRIDE",
    "MAX_COMPUTE_SECONDS",
    "MAX_MEMORY_MB",
]
