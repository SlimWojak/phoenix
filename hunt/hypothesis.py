"""
Hypothesis — S38 Track A
========================

Human-framed hypotheses. Questions, not answers.
System tests, never proposes.

INVARIANTS:
  - INV-NO-UNSOLICITED: Human frames only
  - INV-HUNT-METRICS-DECLARED: Metrics mandatory
  - INV-GRID-DIMENSION-CAP: Max 3 dimensions
  - INV-HUNT-DIM-CARDINALITY-CAP: Per-dim caps
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# =============================================================================
# CONSTANTS
# =============================================================================

MAX_DIMENSIONS = 3
DIMENSION_SOFT_CAP = 100
DIMENSION_HARD_CAP = 1000

FORBIDDEN_SOURCES = frozenset([
    "system",
    "athena",
    "hunt_engine",
    "auto",
    "generated",
])

FORBIDDEN_FIELDS = frozenset([
    "proposed_by_system",
    "auto_generated",
    "confidence",
    "priority",
    "expected_outcome",
    "recommended_variants",
    "edge_score",
    "derived_metrics",
    "quality_score",
    "ranking",
    "survivors",
])


# =============================================================================
# ENUMS
# =============================================================================


class HypothesisStatus(str, Enum):
    """Hypothesis approval status."""

    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


class CardinalityWarning(str, Enum):
    """Cardinality warning levels."""

    OK = "OK"
    WARNING = "WARNING"  # > soft cap
    REJECT = "REJECT"  # > hard cap without T2


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class GridDimension:
    """A single dimension in the hypothesis grid."""

    dimension: str
    values: list[Any]

    @property
    def cardinality(self) -> int:
        """Number of values in this dimension."""
        return len(self.values)

    def check_cardinality(self, t2_override: bool = False) -> CardinalityWarning:
        """Check if cardinality is within caps."""
        if self.cardinality > DIMENSION_HARD_CAP and not t2_override:
            return CardinalityWarning.REJECT
        if self.cardinality > DIMENSION_SOFT_CAP:
            return CardinalityWarning.WARNING
        return CardinalityWarning.OK


@dataclass
class HypothesisGrid:
    """Grid of parameters to test."""

    dimensions: list[GridDimension] = field(default_factory=list)

    @property
    def total_variants(self) -> int:
        """Calculate total grid size (product of cardinalities)."""
        if not self.dimensions:
            return 0
        result = 1
        for dim in self.dimensions:
            result *= dim.cardinality
        return result

    def check_dimension_count(self) -> tuple[bool, str]:
        """
        Check if dimension count is within cap.

        INV-GRID-DIMENSION-CAP: Max 3 dimensions.
        """
        if len(self.dimensions) > MAX_DIMENSIONS:
            return (
                False,
                f"Max {MAX_DIMENSIONS} dimensions allowed, got {len(self.dimensions)}. "
                "INV-GRID-DIMENSION-CAP violation. Use nested hunts for >3 variables.",
            )
        return (True, "")


@dataclass
class FixedParameter:
    """A fixed parameter (constant for this hunt)."""

    name: str
    value: Any


@dataclass
class HypothesisFraming:
    """Framing of the hypothesis."""

    question: str
    source: str  # HUMAN ONLY
    domain: str


@dataclass
class HypothesisConstraints:
    """Constraints for the hypothesis."""

    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    pairs: list[str] = field(default_factory=list)


@dataclass
class HypothesisBudget:
    """Budget constraints."""

    max_variants: int = 0
    estimated_compute: str = ""


@dataclass
class HypothesisApproval:
    """Approval status."""

    approved: bool = False
    approved_by: str = ""
    approved_at: datetime | None = None


@dataclass
class Hypothesis:
    """
    Human-framed hypothesis.

    Questions, not answers. System tests, never proposes.

    INVARIANTS:
      - INV-NO-UNSOLICITED: Human frames only
      - INV-HUNT-METRICS-DECLARED: Metrics mandatory
      - INV-GRID-DIMENSION-CAP: Max 3 dimensions
    """

    hypothesis_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    framing: HypothesisFraming = field(
        default_factory=lambda: HypothesisFraming("", "", "")
    )
    grid: HypothesisGrid = field(default_factory=HypothesisGrid)
    fixed: list[FixedParameter] = field(default_factory=list)

    # MANDATORY — no defaults, no derived
    metrics: list[str] = field(default_factory=list)

    constraints: HypothesisConstraints = field(default_factory=HypothesisConstraints)
    budget: HypothesisBudget = field(default_factory=HypothesisBudget)
    approval: HypothesisApproval = field(default_factory=HypothesisApproval)

    def __post_init__(self) -> None:
        """Generate hypothesis_id if not provided."""
        if not self.hypothesis_id:
            self.hypothesis_id = f"HUNT_{uuid.uuid4().hex[:12]}"


# =============================================================================
# VALIDATION
# =============================================================================


@dataclass
class ValidationError:
    """Validation error."""

    field: str
    message: str
    code: str


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class HypothesisValidator:
    """
    Validates hypotheses.

    Enforces:
    - Human source only (INV-NO-UNSOLICITED)
    - Metrics mandatory (INV-HUNT-METRICS-DECLARED)
    - Dimension caps (INV-GRID-DIMENSION-CAP)
    - Cardinality caps (INV-HUNT-DIM-CARDINALITY-CAP)
    """

    def validate(
        self,
        hypothesis: Hypothesis,
        t2_override: bool = False,
    ) -> ValidationResult:
        """
        Validate a hypothesis.

        Args:
            hypothesis: Hypothesis to validate
            t2_override: T2 approval for exceeding caps

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []
        warnings: list[str] = []

        # Check source (INV-NO-UNSOLICITED)
        source_lower = hypothesis.framing.source.lower()
        if source_lower in FORBIDDEN_SOURCES:
            errors.append(ValidationError(
                field="framing.source",
                message=f"Source '{hypothesis.framing.source}' is forbidden. "
                        "Only human sources allowed.",
                code="FORBIDDEN_SOURCE",
            ))

        if not hypothesis.framing.source:
            errors.append(ValidationError(
                field="framing.source",
                message="Source is required (human attribution)",
                code="MISSING_SOURCE",
            ))

        # Check metrics (INV-HUNT-METRICS-DECLARED)
        if not hypothesis.metrics:
            errors.append(ValidationError(
                field="metrics",
                message="Metrics list is MANDATORY and cannot be empty. "
                        "INV-HUNT-METRICS-DECLARED violation.",
                code="EMPTY_METRICS",
            ))

        # Check dimension count (INV-GRID-DIMENSION-CAP)
        valid, msg = hypothesis.grid.check_dimension_count()
        if not valid:
            errors.append(ValidationError(
                field="grid.dimensions",
                message=msg,
                code="DIMENSION_CAP_EXCEEDED",
            ))

        # Check cardinality per dimension (INV-HUNT-DIM-CARDINALITY-CAP)
        for dim in hypothesis.grid.dimensions:
            warning_level = dim.check_cardinality(t2_override)
            if warning_level == CardinalityWarning.REJECT:
                errors.append(ValidationError(
                    field=f"grid.dimensions.{dim.dimension}",
                    message=f"Dimension '{dim.dimension}' has {dim.cardinality} values, "
                            f"exceeding hard cap of {DIMENSION_HARD_CAP}. T2 required.",
                    code="CARDINALITY_HARD_CAP",
                ))
            elif warning_level == CardinalityWarning.WARNING:
                warnings.append(
                    f"Dimension '{dim.dimension}' has {dim.cardinality} values, "
                    f"exceeding soft cap of {DIMENSION_SOFT_CAP}."
                )

        # Check budget
        if hypothesis.budget.max_variants <= 0:
            errors.append(ValidationError(
                field="budget.max_variants",
                message="Budget max_variants is required and must be positive",
                code="MISSING_BUDGET",
            ))

        # Check question
        if not hypothesis.framing.question:
            errors.append(ValidationError(
                field="framing.question",
                message="Question is required",
                code="MISSING_QUESTION",
            ))

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_approval(self, hypothesis: Hypothesis) -> ValidationResult:
        """
        Validate that hypothesis is approved for execution.

        Args:
            hypothesis: Hypothesis to validate

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []

        if not hypothesis.approval.approved:
            errors.append(ValidationError(
                field="approval.approved",
                message="Hypothesis must be approved before execution",
                code="NOT_APPROVED",
            ))

        if not hypothesis.approval.approved_by:
            errors.append(ValidationError(
                field="approval.approved_by",
                message="Approval requires human attribution",
                code="MISSING_APPROVER",
            ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_dict(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate hypothesis dict for forbidden fields.

        Args:
            data: Hypothesis as dictionary

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []

        def check_dict(d: dict[str, Any], prefix: str = "") -> None:
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if key.lower() in FORBIDDEN_FIELDS:
                    errors.append(ValidationError(
                        field=full_key,
                        message=f"Forbidden field '{key}'",
                        code="FORBIDDEN_FIELD",
                    ))
                if isinstance(value, dict):
                    check_dict(value, full_key)

        check_dict(data)
        return ValidationResult(valid=len(errors) == 0, errors=errors)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Constants
    "MAX_DIMENSIONS",
    "DIMENSION_SOFT_CAP",
    "DIMENSION_HARD_CAP",
    "FORBIDDEN_SOURCES",
    "FORBIDDEN_FIELDS",
    # Enums
    "HypothesisStatus",
    "CardinalityWarning",
    # Data classes
    "GridDimension",
    "HypothesisGrid",
    "FixedParameter",
    "HypothesisFraming",
    "HypothesisConstraints",
    "HypothesisBudget",
    "HypothesisApproval",
    "Hypothesis",
    # Validation
    "HypothesisValidator",
    "ValidationResult",
    "ValidationError",
]
