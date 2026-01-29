"""
Athena Bead Types — S37 Track A
===============================

Three memory bead types with strict semantic boundaries.
CLAIM = human wisdom. FACT = machine truth. CONFLICT = tension.

INVARIANTS:
  - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates
  - INV-ATTR-SILENCE: Conflicts have no resolution authority
  - INV-ATTR-PROVENANCE: Facts require full provenance
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class AthenaBeadType(str, Enum):
    """Athena bead types."""

    CLAIM = "CLAIM"
    FACT = "FACT"
    CONFLICT = "CONFLICT"


class SourceType(str, Enum):
    """Source types for beads."""

    HUMAN = "HUMAN"
    COMPUTATION = "COMPUTATION"


class ConflictType(str, Enum):
    """Types of conflicts."""

    BOOLEAN = "BOOLEAN"
    NUMERIC = "NUMERIC"
    STATISTICAL = "STATISTICAL"


class ConflictStatus(str, Enum):
    """Conflict resolution status."""

    OPEN = "OPEN"
    RESOLVED = "RESOLVED"


class ResolutionAction(str, Enum):
    """Human resolution actions."""

    CLAIM_UPDATED = "CLAIM_UPDATED"
    CLAIM_RETAINED = "CLAIM_RETAINED"
    FACT_DISPUTED = "FACT_DISPUTED"
    RESOLVED_BY_SUPERSESSION = "RESOLVED_BY_SUPERSESSION"


class StatisticalType(str, Enum):
    """Statistical parameter types."""

    POINT_ESTIMATE = "point_estimate"
    RANGE = "range"
    PERCENTAGE = "percentage"


# =============================================================================
# FORBIDDEN FIELDS
# =============================================================================

FORBIDDEN_FIELDS = frozenset([
    "importance",
    "priority",
    "weight",
    "score",
    "quality",
    "confidence",
    "confidence_interval",
    "severity",
    "urgency",
    "auto_resolution",
])


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ClaimSource:
    """Source information for a claim."""

    type: SourceType = SourceType.HUMAN
    attribution: str = ""  # Who made the claim
    context: str = ""  # Session/conversation reference


@dataclass
class StatisticalParameters:
    """
    Statistical parameters for range-based conflict detection.

    FORBIDDEN: confidence_interval (system cannot assign)
    """

    type: StatisticalType = StatisticalType.POINT_ESTIMATE
    value: Any = None
    bounds_lower: float | None = None
    bounds_upper: float | None = None


@dataclass
class ClaimContent:
    """Content of a claim."""

    assertion: str = ""
    domain: str = ""
    # confidence_declared: FORBIDDEN


@dataclass
class ClaimStatus:
    """Status of a claim."""

    verified: bool = False  # ALWAYS False — claims never verified
    superseded_by: str | None = None


@dataclass
class ClaimProvenance:
    """Provenance of a claim."""

    session_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ClaimBead:
    """
    CLAIM BEAD — Human Assertion.

    Claims are QUERYABLE, never EXECUTABLE.
    No claim can mutate doctrine.

    INVARIANTS:
      - INV-CLAIM-NO-EXECUTION: Cannot be used as predicate
      - INV-ATTR-NO-WRITEBACK: Cannot mutate doctrine
    """

    bead_id: str = ""
    bead_type: AthenaBeadType = AthenaBeadType.CLAIM
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    source: ClaimSource = field(default_factory=ClaimSource)
    content: ClaimContent = field(default_factory=ClaimContent)

    # MANDATORY disclaimer
    disclaimer: str = "HUMAN_ASSERTION_ONLY — no doctrine impact"

    # Optional statistical parameters for range-based conflicts
    statistical_parameters: StatisticalParameters | None = None

    status: ClaimStatus = field(default_factory=ClaimStatus)
    provenance: ClaimProvenance = field(default_factory=ClaimProvenance)

    def __post_init__(self) -> None:
        """Generate bead_id if not provided."""
        if not self.bead_id:
            self.bead_id = f"CLAIM_{uuid.uuid4().hex[:12]}"

    # FORBIDDEN: These fields must never exist
    # - importance
    # - priority
    # - weight
    # - score
    # - quality
    # - confidence (system-assigned)


@dataclass
class FactSource:
    """Source information for a fact."""

    type: SourceType = SourceType.COMPUTATION
    module: str = ""  # e.g., "cfp", "river", "cso"
    formula: str = ""  # Explicit computation description


@dataclass
class FactContent:
    """Content of a fact."""

    statement: str = ""
    value: Any = None
    domain: str = ""


@dataclass
class FactProvenance:
    """
    Provenance of a fact.

    MANDATORY — from CFP pattern (quadruplet).
    """

    query_string: str = ""
    dataset_hash: str = ""
    governance_hash: str = ""
    strategy_config_hash: str = ""
    computed_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def is_complete(self) -> bool:
        """Check if provenance is complete."""
        return all([
            self.query_string,
            self.dataset_hash,
            self.governance_hash,
            self.strategy_config_hash,
        ])


@dataclass
class FactStatus:
    """Status of a fact."""

    valid_until: datetime | None = None
    recomputed_from: str | None = None


@dataclass
class FactBead:
    """
    FACT BEAD — Machine Computation.

    Facts have full provenance. Computed by verified modules.

    INVARIANTS:
      - INV-ATTR-PROVENANCE: Full provenance required
    """

    bead_id: str = ""
    bead_type: AthenaBeadType = AthenaBeadType.FACT
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    source: FactSource = field(default_factory=FactSource)
    content: FactContent = field(default_factory=FactContent)
    provenance: FactProvenance = field(default_factory=FactProvenance)
    status: FactStatus = field(default_factory=FactStatus)

    def __post_init__(self) -> None:
        """Generate bead_id if not provided."""
        if not self.bead_id:
            self.bead_id = f"FACT_{uuid.uuid4().hex[:12]}"


@dataclass
class ConflictReferences:
    """References to conflicting beads."""

    claim_bead_id: str = ""
    fact_bead_id: str = ""
    supersession_chain: list[str] = field(default_factory=list)


@dataclass
class ConflictDetails:
    """Details of the conflict."""

    description: str = ""  # Auto-generated
    domain: str = ""
    conflict_type: ConflictType = ConflictType.BOOLEAN
    # severity: FORBIDDEN


@dataclass
class ConflictResolution:
    """
    Resolution information.

    System has NO authority. Human decides.
    """

    status: ConflictStatus = ConflictStatus.OPEN
    resolved_by: str | None = None
    resolution_action: ResolutionAction | None = None
    resolved_at: datetime | None = None


@dataclass
class ConflictBead:
    """
    CONFLICT BEAD — Tension Between Claim and Fact.

    System surfaces, NEVER resolves.
    No severity. No auto-resolution. Human decides.

    INVARIANTS:
      - INV-ATTR-SILENCE: System does not resolve
      - INV-CONFLICT-SHUFFLE: Returned shuffled
      - INV-CONFLICT-NO-AGGREGATION: No counting/ranking
    """

    bead_id: str = ""
    bead_type: AthenaBeadType = AthenaBeadType.CONFLICT
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    references: ConflictReferences = field(default_factory=ConflictReferences)
    conflict: ConflictDetails = field(default_factory=ConflictDetails)
    resolution: ConflictResolution = field(default_factory=ConflictResolution)

    def __post_init__(self) -> None:
        """Generate bead_id if not provided."""
        if not self.bead_id:
            self.bead_id = f"CONFLICT_{uuid.uuid4().hex[:12]}"

    # FORBIDDEN: These fields must never exist
    # - severity
    # - urgency
    # - importance
    # - auto_resolution


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


class BeadValidator:
    """
    Validates bead types.

    Rejects forbidden fields. Enforces required fields.
    """

    def validate_claim(self, claim: ClaimBead) -> ValidationResult:
        """
        Validate a claim bead.

        Checks:
        1. Disclaimer is present
        2. Attribution is present
        3. Verified is False
        4. No forbidden fields
        """
        errors: list[ValidationError] = []

        # Disclaimer required
        if not claim.disclaimer:
            errors.append(ValidationError(
                field="disclaimer",
                message="Disclaimer is required for claims",
                code="MISSING_DISCLAIMER",
            ))

        # Attribution required
        if not claim.source.attribution:
            errors.append(ValidationError(
                field="source.attribution",
                message="Attribution is required for claims",
                code="MISSING_ATTRIBUTION",
            ))

        # Verified must be False
        if claim.status.verified:
            errors.append(ValidationError(
                field="status.verified",
                message="Claims cannot be verified by system",
                code="VERIFIED_FORBIDDEN",
            ))

        # Assertion required
        if not claim.content.assertion:
            errors.append(ValidationError(
                field="content.assertion",
                message="Assertion is required",
                code="MISSING_ASSERTION",
            ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_fact(self, fact: FactBead) -> ValidationResult:
        """
        Validate a fact bead.

        Checks:
        1. Full provenance present
        2. Module is specified
        """
        errors: list[ValidationError] = []

        # Provenance required
        if not fact.provenance.is_complete():
            errors.append(ValidationError(
                field="provenance",
                message="Complete provenance quadruplet required for facts",
                code="INCOMPLETE_PROVENANCE",
            ))

        # Module required
        if not fact.source.module:
            errors.append(ValidationError(
                field="source.module",
                message="Source module is required for facts",
                code="MISSING_MODULE",
            ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_conflict(self, conflict: ConflictBead) -> ValidationResult:
        """
        Validate a conflict bead.

        Checks:
        1. References are present
        2. No severity field
        """
        errors: list[ValidationError] = []

        # References required
        if not conflict.references.claim_bead_id:
            errors.append(ValidationError(
                field="references.claim_bead_id",
                message="Claim reference is required",
                code="MISSING_CLAIM_REF",
            ))

        if not conflict.references.fact_bead_id:
            errors.append(ValidationError(
                field="references.fact_bead_id",
                message="Fact reference is required",
                code="MISSING_FACT_REF",
            ))

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_dict(self, bead_dict: dict[str, Any]) -> ValidationResult:
        """
        Validate a bead dictionary for forbidden fields.

        Used for raw dict validation before dataclass conversion.
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

        check_dict(bead_dict)
        return ValidationResult(valid=len(errors) == 0, errors=errors)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Enums
    "AthenaBeadType",
    "SourceType",
    "ConflictType",
    "ConflictStatus",
    "ResolutionAction",
    "StatisticalType",
    # Dataclasses
    "ClaimBead",
    "ClaimSource",
    "ClaimContent",
    "ClaimStatus",
    "ClaimProvenance",
    "StatisticalParameters",
    "FactBead",
    "FactSource",
    "FactContent",
    "FactProvenance",
    "FactStatus",
    "ConflictBead",
    "ConflictReferences",
    "ConflictDetails",
    "ConflictResolution",
    # Validation
    "BeadValidator",
    "ValidationResult",
    "ValidationError",
    "FORBIDDEN_FIELDS",
]
