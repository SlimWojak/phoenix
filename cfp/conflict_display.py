"""
Conflict Display — Best/Worst Pairing Enforcement
=================================================

S35 TRACK E DELIVERABLE
Created: 2026-01-29 (Day 5-6)

When showing "best", must show "worst".
Prevents selective presentation that becomes implicit recommendation.

INVARIANTS ENFORCED:
  - INV-ATTR-CONFLICT-DISPLAY: Best always paired with worst
  - INV-ATTR-NO-RANKING: No ordered lists beyond top/bottom
  - INV-NO-DEFAULT-SALIENCE: Equal visual weight + random position
  - INV-CFP-LOW-N-GATE: N < 30 cannot persist as FACT without T2

FEATURES (v0.2):
  - Randomized best/worst positioning
  - Spread.delta disabled by default
  - Low-N persistence gate
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from cfp.executor import Provenance, ResultType

# =============================================================================
# CONSTANTS
# =============================================================================

# Minimum sample size for FACT persistence
LOW_N_THRESHOLD = 30


# =============================================================================
# TYPES
# =============================================================================


class SpreadStatus(Enum):
    """Status of spread display."""

    DISABLED = "DISABLED"  # Default — spread.delta not shown
    ENABLED = "ENABLED"  # Explicit user request


@dataclass
class MetricValue:
    """Single metric value with metadata."""

    dimension_value: str  # e.g., "London"
    metrics: dict[str, float | None]
    sample_size: int
    provenance: Provenance


@dataclass
class Spread:
    """Spread between best and worst."""

    metric: str
    delta: float
    status: SpreadStatus = SpreadStatus.DISABLED


@dataclass
class Scope:
    """Scope of comparison."""

    comparison_domain: str  # explicit slice only, never "global"
    dimension: str
    filter_applied: str = ""


@dataclass
class ConflictPair:
    """
    Paired best/worst for a dimension.

    INV-ATTR-CONFLICT-DISPLAY: Best always comes with worst.
    INV-ATTR-NO-RANKING: No ordered list — just top and bottom.
    """

    dimension: str  # e.g., "session"
    best: MetricValue
    worst: MetricValue
    spread: Spread
    scope: Scope

    @property
    def can_persist(self) -> bool:
        """Check if both sides have sufficient sample size."""
        return (
            self.best.sample_size >= LOW_N_THRESHOLD and self.worst.sample_size >= LOW_N_THRESHOLD
        )


@dataclass
class RenderedPair:
    """
    Rendered conflict pair with randomized positioning.

    INV-NO-DEFAULT-SALIENCE: Position randomized per render.
    """

    left: MetricValue
    left_label: str  # "BEST" or "WORST"
    right: MetricValue
    right_label: str  # "BEST" or "WORST"
    dimension: str
    spread: Spread
    scope: Scope
    rendered_at: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# CONFLICT DISPLAY ENGINE
# =============================================================================


class ConflictDisplay:
    """
    Generates conflict pairs from CFP results.

    Enforces:
    - Best always paired with worst
    - Randomized positioning
    - No ranking beyond top/bottom
    - Low-N persistence gate

    Usage:
        display = ConflictDisplay()
        pair = display.create_pair(
            dimension="session",
            values={"London": {...}, "Tokyo": {...}},
            comparison_metric="sharpe",
        )
        rendered = display.render(pair)
    """

    def __init__(self, spread_enabled: bool = False) -> None:
        """
        Initialize conflict display.

        Args:
            spread_enabled: If True, show spread.delta (default: disabled)
        """
        self._spread_status = SpreadStatus.ENABLED if spread_enabled else SpreadStatus.DISABLED

    def create_pair(
        self,
        dimension: str,
        values: dict[str, dict[str, Any]],
        comparison_metric: str,
        scope_description: str = "",
    ) -> ConflictPair | None:
        """
        Create a conflict pair from dimension values.

        Finds best and worst for the comparison metric.

        Args:
            dimension: Dimension name (e.g., "session")
            values: Dict of dimension_value -> {metrics, sample_size, provenance}
            comparison_metric: Metric to compare (e.g., "sharpe")
            scope_description: Description of filter scope

        Returns:
            ConflictPair or None if insufficient data
        """
        if len(values) < 2:
            # Need at least 2 values to compare
            return None

        # Extract metric values and find best/worst
        metric_values: list[tuple[str, float | None, dict[str, Any]]] = []

        for dim_value, data in values.items():
            metric_val = data.get("metrics", {}).get(comparison_metric)
            metric_values.append((dim_value, metric_val, data))

        # Filter out None values for comparison
        valid_values = [(dv, mv, data) for dv, mv, data in metric_values if mv is not None]

        if len(valid_values) < 2:
            return None

        # Sort by metric value (x[1] is always float here due to filter above)
        sorted_values = sorted(valid_values, key=lambda x: float(x[1]), reverse=True)

        best_dim, best_val, best_data = sorted_values[0]
        worst_dim, worst_val, worst_data = sorted_values[-1]

        # Create MetricValue objects
        best = MetricValue(
            dimension_value=best_dim,
            metrics=best_data.get("metrics", {}),
            sample_size=best_data.get("sample_size", 0),
            provenance=self._make_provenance(best_data),
        )

        worst = MetricValue(
            dimension_value=worst_dim,
            metrics=worst_data.get("metrics", {}),
            sample_size=worst_data.get("sample_size", 0),
            provenance=self._make_provenance(worst_data),
        )

        # Create spread
        spread = Spread(
            metric=comparison_metric,
            delta=round(float(best_val) - float(worst_val), 2),
            status=self._spread_status,
        )

        # Create scope
        scope = Scope(
            comparison_domain="explicit",  # Never "global"
            dimension=dimension,
            filter_applied=scope_description,
        )

        return ConflictPair(
            dimension=dimension,
            best=best,
            worst=worst,
            spread=spread,
            scope=scope,
        )

    def _make_provenance(self, data: dict[str, Any]) -> Provenance:
        """Create provenance from data dict."""
        prov_data = data.get("provenance", {})
        if isinstance(prov_data, Provenance):
            return prov_data

        return Provenance(
            query_string=prov_data.get("query_string", ""),
            dataset_hash=prov_data.get("dataset_hash", ""),
            governance_hash=prov_data.get("governance_hash", ""),
            computed_at=datetime.now(UTC),
            strategy_config_hash=prov_data.get("strategy_config_hash", ""),
        )

    def render(self, pair: ConflictPair) -> RenderedPair:
        """
        Render conflict pair with randomized positioning.

        INV-NO-DEFAULT-SALIENCE: Position is randomized per render.
        User must read labels, not rely on position.

        Args:
            pair: ConflictPair to render

        Returns:
            RenderedPair with randomized left/right
        """
        # Randomize which side gets left vs right
        # secrets.randbelow(2) returns 0 or 1
        best_on_left = secrets.randbelow(2) == 0

        if best_on_left:
            return RenderedPair(
                left=pair.best,
                left_label="BEST",
                right=pair.worst,
                right_label="WORST",
                dimension=pair.dimension,
                spread=pair.spread,
                scope=pair.scope,
            )
        else:
            return RenderedPair(
                left=pair.worst,
                left_label="WORST",
                right=pair.best,
                right_label="BEST",
                dimension=pair.dimension,
                spread=pair.spread,
                scope=pair.scope,
            )

    def check_persistence_gate(self, pair: ConflictPair) -> tuple[bool, str]:
        """
        Check if pair can be persisted as FACT.

        INV-CFP-LOW-N-GATE: N < 30 cannot persist without T2.

        Args:
            pair: ConflictPair to check

        Returns:
            (can_persist, reason)
        """
        if pair.best.sample_size < LOW_N_THRESHOLD:
            return (
                False,
                f"Best sample size ({pair.best.sample_size}) < {LOW_N_THRESHOLD}",
            )

        if pair.worst.sample_size < LOW_N_THRESHOLD:
            return (
                False,
                f"Worst sample size ({pair.worst.sample_size}) < {LOW_N_THRESHOLD}",
            )

        return (True, "")

    def get_result_type(self, pair: ConflictPair) -> ResultType:
        """
        Determine result type based on sample sizes.

        Returns FACT if both sides have N >= 30, else VIEW.
        """
        can_persist, _ = self.check_persistence_gate(pair)
        return ResultType.FACT if can_persist else ResultType.VIEW

    def to_dict(self, pair: ConflictPair) -> dict[str, Any]:
        """Convert conflict pair to dictionary."""
        return {
            "dimension": pair.dimension,
            "best": {
                "value": pair.best.dimension_value,
                "metrics": pair.best.metrics,
                "sample_size": pair.best.sample_size,
            },
            "worst": {
                "value": pair.worst.dimension_value,
                "metrics": pair.worst.metrics,
                "sample_size": pair.worst.sample_size,
            },
            "spread": {
                "metric": pair.spread.metric,
                "delta": pair.spread.delta if pair.spread.status == SpreadStatus.ENABLED else None,
                "status": pair.spread.status.value,
            },
            "scope": {
                "comparison_domain": pair.scope.comparison_domain,
                "dimension": pair.scope.dimension,
                "filter_applied": pair.scope.filter_applied,
            },
            "can_persist": pair.can_persist,
        }


# =============================================================================
# VALIDATION
# =============================================================================


def validate_conflict_request(
    request_type: str,
    include_worst: bool = True,
) -> tuple[bool, str]:
    """
    Validate a conflict display request.

    INV-ATTR-CONFLICT-DISPLAY: Cannot request "best" without "worst".

    Args:
        request_type: "best", "worst", or "both"
        include_worst: Whether worst is included

    Returns:
        (valid, error_message)
    """
    if request_type == "best" and not include_worst:
        return (
            False,
            "Cannot request 'best' without 'worst'. "
            "INV-ATTR-CONFLICT-DISPLAY requires paired display.",
        )

    return (True, "")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "ConflictDisplay",
    "ConflictPair",
    "RenderedPair",
    "MetricValue",
    "Spread",
    "SpreadStatus",
    "Scope",
    "validate_conflict_request",
    "LOW_N_THRESHOLD",
]
