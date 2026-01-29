"""
Conflict Detector — S37 Track C
===============================

Detects when claims contradict facts. Surfaces, NEVER resolves.
System has NO authority to decide which is correct.

INVARIANTS:
  - INV-ATTR-SILENCE: System does not resolve conflicts
  - INV-CONFLICT-SHUFFLE: Conflicts returned shuffled
  - INV-CONFLICT-NO-AGGREGATION: No counting/ranking
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from athena.bead_types import (
    ClaimBead,
    ConflictBead,
    ConflictDetails,
    ConflictReferences,
    ConflictType,
    FactBead,
    StatisticalParameters,
)


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class ConflictCheckResult:
    """Result of conflict check."""

    has_conflict: bool
    conflict_type: ConflictType | None = None
    description: str = ""


# =============================================================================
# CONFLICT DETECTOR
# =============================================================================


class ConflictDetector:
    """
    Detects conflicts between claims and facts.

    Detection rules:
    - Boolean: Direct contradiction (X vs NOT X)
    - Numeric: Numeric contradiction (A > B vs A <= B)
    - Statistical: Fact outside claim bounds

    System has NO resolution authority.

    INVARIANTS:
      - INV-ATTR-SILENCE: Surface and wait
      - INV-CONFLICT-SHUFFLE: Results shuffled
      - INV-CONFLICT-NO-AGGREGATION: No counts
    """

    def check_claim_against_fact(
        self,
        claim: ClaimBead,
        fact: FactBead,
    ) -> ConflictCheckResult:
        """
        Check if a claim conflicts with a fact.

        Args:
            claim: The claim to check
            fact: The fact to check against

        Returns:
            ConflictCheckResult
        """
        # Must be same domain
        if claim.content.domain != fact.content.domain:
            return ConflictCheckResult(has_conflict=False)

        # Check statistical conflict first
        if claim.statistical_parameters:
            stat_result = self._check_statistical_conflict(
                claim.statistical_parameters,
                fact.content.value,
            )
            if stat_result.has_conflict:
                return stat_result

        # Check for boolean/numeric contradiction
        # This is a simplified check - in production would use NLP
        contradiction = self._check_contradiction(
            claim.content.assertion,
            fact.content.statement,
            fact.content.value,
        )

        return contradiction

    def _check_statistical_conflict(
        self,
        params: StatisticalParameters,
        fact_value: Any,
    ) -> ConflictCheckResult:
        """
        Check for statistical conflict.

        Conflict if fact value is outside claim bounds.

        Args:
            params: Claim's statistical parameters
            fact_value: The fact value to check

        Returns:
            ConflictCheckResult
        """
        # Need numeric fact value
        if not isinstance(fact_value, (int, float)):
            return ConflictCheckResult(has_conflict=False)

        # Need bounds
        if params.bounds_lower is None or params.bounds_upper is None:
            return ConflictCheckResult(has_conflict=False)

        # Check bounds
        if fact_value < params.bounds_lower:
            return ConflictCheckResult(
                has_conflict=True,
                conflict_type=ConflictType.STATISTICAL,
                description=(
                    f"Fact value {fact_value} below claim lower bound "
                    f"{params.bounds_lower}"
                ),
            )

        if fact_value > params.bounds_upper:
            return ConflictCheckResult(
                has_conflict=True,
                conflict_type=ConflictType.STATISTICAL,
                description=(
                    f"Fact value {fact_value} above claim upper bound "
                    f"{params.bounds_upper}"
                ),
            )

        return ConflictCheckResult(has_conflict=False)

    def _check_contradiction(
        self,
        assertion: str,
        statement: str,
        value: Any,
    ) -> ConflictCheckResult:
        """
        Check for boolean/numeric contradiction.

        This is a simplified implementation.
        Production would use more sophisticated NLP.

        Args:
            assertion: Claim assertion text
            statement: Fact statement text
            value: Fact value

        Returns:
            ConflictCheckResult
        """
        assertion_lower = assertion.lower()
        statement_lower = statement.lower()

        # Simple numeric check
        if isinstance(value, (int, float)):
            # Look for percentage claims vs percentage facts
            # E.g., "70%" in assertion vs 0.40 in fact
            if "%" in assertion:
                # Extract percentage from assertion
                try:
                    # Find number before %
                    import re
                    match = re.search(r"(\d+(?:\.\d+)?)\s*%", assertion)
                    if match:
                        claim_pct = float(match.group(1)) / 100
                        # Check if significantly different (> 20% difference)
                        if abs(claim_pct - value) > 0.20:
                            return ConflictCheckResult(
                                has_conflict=True,
                                conflict_type=ConflictType.NUMERIC,
                                description=(
                                    f"Claim asserts ~{claim_pct*100:.0f}%, "
                                    f"Fact shows {value*100:.0f}%"
                                ),
                            )
                except (ValueError, AttributeError):
                    pass

        # Simple boolean contradiction patterns
        contradiction_pairs = [
            ("works", "failed"),
            ("always", "sometimes"),
            ("high", "low"),
            ("profitable", "loss"),
            ("bullish", "bearish"),
        ]

        for pos, neg in contradiction_pairs:
            if pos in assertion_lower and neg in statement_lower:
                return ConflictCheckResult(
                    has_conflict=True,
                    conflict_type=ConflictType.BOOLEAN,
                    description=f"Claim asserts '{pos}', Fact shows '{neg}'",
                )
            if neg in assertion_lower and pos in statement_lower:
                return ConflictCheckResult(
                    has_conflict=True,
                    conflict_type=ConflictType.BOOLEAN,
                    description=f"Claim asserts '{neg}', Fact shows '{pos}'",
                )

        return ConflictCheckResult(has_conflict=False)

    def create_conflict_bead(
        self,
        claim: ClaimBead,
        fact: FactBead,
        conflict_type: ConflictType,
        description: str,
    ) -> ConflictBead:
        """
        Create a conflict bead from claim and fact.

        Args:
            claim: The conflicting claim
            fact: The contradicting fact
            conflict_type: Type of conflict
            description: Conflict description

        Returns:
            ConflictBead (status=OPEN, no resolution)
        """
        return ConflictBead(
            references=ConflictReferences(
                claim_bead_id=claim.bead_id,
                fact_bead_id=fact.bead_id,
                supersession_chain=[],
            ),
            conflict=ConflictDetails(
                description=f"CLAIM asserts: {claim.content.assertion}. "
                           f"FACT shows: {fact.content.statement}. "
                           f"Conflict: {description}",
                domain=claim.content.domain,
                conflict_type=conflict_type,
            ),
        )


# =============================================================================
# FORBIDDEN OPERATIONS VALIDATOR
# =============================================================================


class ConflictAggregationBan:
    """
    Validates that no conflict aggregation is attempted.

    INV-CONFLICT-NO-AGGREGATION
    """

    FORBIDDEN_PATTERNS = frozenset([
        "count_by_domain",
        "conflicts_per_domain",
        "sort_by_time_open",
        "oldest_unresolved",
        "domains_with_most",
        "conflict_frequency",
        "most_conflicts",
        "conflict_count",
        "contradicted_most",
        "disproved_claims",
    ])

    @classmethod
    def validate_query(cls, query: str) -> tuple[bool, str]:
        """
        Validate a query doesn't request conflict aggregation.

        Args:
            query: Query string

        Returns:
            (valid, error_message)
        """
        query_lower = query.lower().replace(" ", "_").replace("-", "_")

        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in query_lower:
                return (
                    False,
                    f"Conflict aggregation forbidden: '{pattern}' pattern detected. "
                    "INV-CONFLICT-NO-AGGREGATION",
                )

        return (True, "")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "ConflictDetector",
    "ConflictCheckResult",
    "ConflictAggregationBan",
]
