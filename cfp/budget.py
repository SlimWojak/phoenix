"""
Budget Enforcement — Pre-execution Compute Ceiling
==================================================

S35 TRACK B DELIVERABLE
Created: 2026-01-29 (Day 2)

Prevents compute explosions before they happen.
"Estimate cardinality, reject if threshold exceeded."

INVARIANT: INV-CFP-BUDGET-ENFORCE
  Rule: Pre-execution estimate > threshold → REJECT with suggestions

PATTERN: Willison datasette — sample query first
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cfp.validation import LensQuery


# =============================================================================
# CONSTANTS
# =============================================================================

# Default cell limit (rows × metrics)
MAX_CELLS_DEFAULT = 10_000

# Hard limit (even with T2 override)
MAX_CELLS_HARD = 100_000

# Sample size for cardinality estimation
SAMPLE_SIZE = 1000


# =============================================================================
# TYPES
# =============================================================================


class BudgetStatus(Enum):
    """Budget check result status."""

    OK = "OK"
    WARNING = "WARNING"
    EXCEEDED = "EXCEEDED"


@dataclass
class BudgetResult:
    """Result of budget estimation."""

    status: BudgetStatus
    estimated_cells: int
    max_cells: int
    estimated_rows: int
    num_metrics: int
    suggestion: str | None = None

    @property
    def ok(self) -> bool:
        """Check if budget is within limits."""
        return self.status == BudgetStatus.OK

    @property
    def exceeded(self) -> bool:
        """Check if budget is exceeded."""
        return self.status == BudgetStatus.EXCEEDED


# =============================================================================
# BUDGET ESTIMATOR
# =============================================================================


class BudgetEstimator:
    """
    Estimates query compute cost before execution.

    Uses cardinality estimation to predict result size,
    then checks against configured limits.

    PATTERN: Willison datasette — COUNT(*) on filtered subset first

    Usage:
        estimator = BudgetEstimator()
        result = estimator.check(query, data_source)

        if result.exceeded:
            raise BudgetExceededError(result.suggestion)
    """

    def __init__(
        self,
        max_cells: int = MAX_CELLS_DEFAULT,
        hard_limit: int = MAX_CELLS_HARD,
    ) -> None:
        """
        Initialize budget estimator.

        Args:
            max_cells: Soft limit for cells (rows × metrics)
            hard_limit: Hard limit (cannot be overridden)
        """
        self._max_cells = max_cells
        self._hard_limit = hard_limit

    def estimate_cardinality(
        self,
        query: LensQuery,
        total_rows: int,
    ) -> int:
        """
        Estimate number of output rows.

        Uses group_by dimensions to estimate unique combinations.

        Args:
            query: The lens query
            total_rows: Total rows in source data

        Returns:
            Estimated number of output rows
        """
        if not query.group_by:
            # No grouping — single row output
            return 1

        # Estimate cardinality for each dimension
        # These are rough estimates based on domain knowledge
        cardinality_estimates = {
            "session": 4,  # London, NY, Asia, Sydney
            "kill_zone": 6,  # London Open, NY Open, etc.
            "pair": 8,  # Major pairs
            "regime": 3,  # trending, ranging, volatile
            "direction": 2,  # LONG, SHORT
            "day_of_week": 5,  # Mon-Fri
            "hour": 24,  # 0-23
        }

        # Product of dimension cardinalities
        estimated_groups = 1
        for dim in query.group_by:
            card = cardinality_estimates.get(dim, 10)
            estimated_groups *= card

        # Cap at total rows (can't have more groups than rows)
        estimated_groups = min(estimated_groups, total_rows)

        # Cap at max_groups if specified
        if query.max_groups:
            estimated_groups = min(estimated_groups, query.max_groups)

        return estimated_groups

    def estimate_cells(
        self,
        query: LensQuery,
        total_rows: int,
    ) -> int:
        """
        Estimate total cells (rows × metrics).

        Args:
            query: The lens query
            total_rows: Total rows in source data

        Returns:
            Estimated total cells
        """
        estimated_rows = self.estimate_cardinality(query, total_rows)
        num_metrics = len(query.aggregate.metrics)

        return estimated_rows * num_metrics

    def check(
        self,
        query: LensQuery,
        total_rows: int,
        allow_override: bool = False,
    ) -> BudgetResult:
        """
        Check if query is within budget.

        Args:
            query: The lens query to check
            total_rows: Total rows in source data
            allow_override: If True, use hard_limit instead of max_cells

        Returns:
            BudgetResult with status and suggestions
        """
        estimated_rows = self.estimate_cardinality(query, total_rows)
        num_metrics = len(query.aggregate.metrics)
        estimated_cells = estimated_rows * num_metrics

        limit = self._hard_limit if allow_override else self._max_cells

        if estimated_cells <= limit:
            return BudgetResult(
                status=BudgetStatus.OK,
                estimated_cells=estimated_cells,
                max_cells=limit,
                estimated_rows=estimated_rows,
                num_metrics=num_metrics,
            )

        if estimated_cells <= self._hard_limit:
            # Over soft limit but under hard — warning
            return BudgetResult(
                status=BudgetStatus.WARNING,
                estimated_cells=estimated_cells,
                max_cells=limit,
                estimated_rows=estimated_rows,
                num_metrics=num_metrics,
                suggestion=self._generate_suggestion(query, estimated_cells, limit),
            )

        # Over hard limit — reject
        return BudgetResult(
            status=BudgetStatus.EXCEEDED,
            estimated_cells=estimated_cells,
            max_cells=self._hard_limit,
            estimated_rows=estimated_rows,
            num_metrics=num_metrics,
            suggestion=self._generate_suggestion(query, estimated_cells, self._hard_limit),
        )

    def _generate_suggestion(
        self,
        query: LensQuery,
        estimated: int,
        limit: int,
    ) -> str:
        """Generate suggestion for reducing query scope."""
        suggestions = []

        # Suggest reducing dimensions
        if len(query.group_by) > 2:
            suggestions.append(f"Reduce group_by dimensions (currently {len(query.group_by)})")

        # Suggest adding filters
        if not query.filter or not query.filter.conditions:
            suggestions.append("Add filter conditions to narrow scope")

        # Suggest reducing metrics
        if len(query.aggregate.metrics) > 2:
            suggestions.append(f"Reduce metrics (currently {len(query.aggregate.metrics)})")

        # Suggest time range
        if not query.filter or not query.filter.time_range:
            suggestions.append("Add time_range filter to limit data window")

        # Suggest max_groups
        if query.max_groups > 100:
            suggestions.append(f"Reduce max_groups (currently {query.max_groups})")

        if suggestions:
            return (
                f"Estimated {estimated:,} cells exceeds limit of {limit:,}. "
                f"Suggestions: {'; '.join(suggestions)}"
            )

        return f"Estimated {estimated:,} cells exceeds limit of {limit:,}."


# =============================================================================
# EXCEPTIONS
# =============================================================================


class BudgetExceededError(Exception):
    """Raised when query exceeds compute budget."""

    def __init__(self, result: BudgetResult) -> None:
        self.result = result
        super().__init__(result.suggestion or "Budget exceeded")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "BudgetEstimator",
    "BudgetResult",
    "BudgetStatus",
    "BudgetExceededError",
    "MAX_CELLS_DEFAULT",
    "MAX_CELLS_HARD",
]
