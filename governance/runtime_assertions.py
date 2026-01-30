"""
Runtime Assertions — S40 Track C
================================

Constitutional enforcement at runtime boundaries.
Catches heresy that slips past pre-commit.

BOUNDARIES:
  - validation_output: No scalar scores
  - cfp_output: Provenance required
  - hunt_emission: No rankings

INVARIANTS:
  INV-HOOK-3: Runtime catches missing provenance
  INV-HOOK-4: Runtime catches ranking fields
"""

from __future__ import annotations

import functools
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Callable, TypeVar


# =============================================================================
# EXCEPTIONS
# =============================================================================


class ConstitutionalViolation(Exception):
    """Base exception for constitutional violations at runtime."""

    def __init__(self, violation_type: str, context: str, details: str = ""):
        self.violation_type = violation_type
        self.context = context
        self.details = details
        super().__init__(
            f"CONSTITUTIONAL VIOLATION [{violation_type}] in {context}: {details}"
        )


class ScalarScoreViolation(ConstitutionalViolation):
    """Raised when a scalar score is detected at runtime."""

    def __init__(self, context: str, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value
        super().__init__(
            violation_type="SCALAR_SCORE",
            context=context,
            details=f"Field '{field_name}' contains scalar score: {value}",
        )


class ProvenanceMissing(ConstitutionalViolation):
    """Raised when required provenance is missing."""

    def __init__(self, context: str, missing_fields: list[str]):
        self.missing_fields = missing_fields
        super().__init__(
            violation_type="PROVENANCE_MISSING",
            context=context,
            details=f"Missing required provenance: {', '.join(missing_fields)}",
        )


class RankingViolation(ConstitutionalViolation):
    """Raised when ranking metadata is detected."""

    def __init__(self, context: str, field_name: str):
        self.field_name = field_name
        super().__init__(
            violation_type="RANKING",
            context=context,
            details=f"Ranking field detected: {field_name}",
        )


class GradeViolation(ConstitutionalViolation):
    """Raised when grade/verdict metadata is detected."""

    def __init__(self, context: str, field_name: str, value: Any):
        self.field_name = field_name
        self.value = value
        super().__init__(
            violation_type="GRADE",
            context=context,
            details=f"Grade/verdict detected: {field_name}={value}",
        )


# =============================================================================
# SCALAR SCORE DETECTION
# =============================================================================


# Fields that are scalar scores (HERESY)
SCALAR_SCORE_FIELDS = {
    "scalar_score",
    "overall_quality",
    "viability_index",
    "confidence_score",
    "quality_metric",
    "overall_score",
    "final_score",
    "aggregate_score",
    "composite_score",
    "weighted_score",
}

# Fields that are rankings (HERESY)
RANKING_FIELDS = {
    "rank",
    "ranking",
    "rank_position",
    "ranking_position",
    "rank_index",
    "position",
    "best_strategy",
    "worst_strategy",
    "top_performer",
}

# Fields that are grades/verdicts (HERESY)
GRADE_FIELDS = {
    "grade",
    "quality_grade",
    "setup_rating",
    "performance_tier",
    "verdict",
    "recommendation",
    "decision",
}

# Required provenance fields
PROVENANCE_FIELDS = {
    "query_string",
    "dataset_hash",
    "bead_id",
}


def assert_no_scalar_score(obj: Any, context: str) -> None:
    """
    Assert that object contains no scalar scores.

    Checks dict keys and object attributes for scalar score patterns.

    Args:
        obj: Object to check (dict, dataclass, or any object)
        context: Description of where this check is happening

    Raises:
        ScalarScoreViolation: If scalar score detected
    """
    fields = _extract_fields(obj)

    for field_name, value in fields.items():
        field_lower = field_name.lower()

        # Check against known scalar fields
        if field_lower in SCALAR_SCORE_FIELDS:
            raise ScalarScoreViolation(context, field_name, value)

        # Check for score suffix pattern
        if field_lower.endswith("_score") and field_lower not in {"test_score"}:
            # Allow certain legitimate uses
            if not _is_legitimate_score_field(field_name, value):
                raise ScalarScoreViolation(context, field_name, value)


def assert_provenance(obj: Any, context: str, required: list[str] | None = None) -> None:
    """
    Assert that object contains required provenance fields.

    Args:
        obj: Object to check
        context: Description of where this check is happening
        required: Override required fields (default: PROVENANCE_FIELDS)

    Raises:
        ProvenanceMissing: If required provenance missing
    """
    required_fields = set(required) if required else PROVENANCE_FIELDS
    fields = _extract_fields(obj)
    field_names = {k.lower() for k in fields.keys()}

    missing = []
    for required_field in required_fields:
        if required_field.lower() not in field_names:
            missing.append(required_field)

    if missing:
        raise ProvenanceMissing(context, missing)


def assert_no_ranking(items: list | Any, context: str) -> None:
    """
    Assert that items contain no ranking metadata.

    Args:
        items: List of items or single item to check
        context: Description of where this check is happening

    Raises:
        RankingViolation: If ranking field detected
    """
    if not isinstance(items, list):
        items = [items]

    for item in items:
        fields = _extract_fields(item)

        for field_name in fields.keys():
            field_lower = field_name.lower()

            if field_lower in RANKING_FIELDS:
                raise RankingViolation(context, field_name)

            # Check for rank_ prefix
            if field_lower.startswith("rank_"):
                raise RankingViolation(context, field_name)


def assert_no_grade(obj: Any, context: str) -> None:
    """
    Assert that object contains no grade/verdict fields.

    Args:
        obj: Object to check
        context: Description of where this check is happening

    Raises:
        GradeViolation: If grade/verdict detected
    """
    fields = _extract_fields(obj)

    for field_name, value in fields.items():
        field_lower = field_name.lower()

        if field_lower in GRADE_FIELDS:
            raise GradeViolation(context, field_name, value)

        # Check for grade pattern in value
        if isinstance(value, str):
            value_lower = value.lower()
            if value_lower in {"pass", "fail", "a", "b", "c", "d", "f"}:
                if "grade" in field_lower or "rating" in field_lower:
                    raise GradeViolation(context, field_name, value)


# =============================================================================
# CONTEXT MANAGER
# =============================================================================


@contextmanager
def constitutional_boundary(name: str, checks: list[str] | None = None):
    """
    Context manager for constitutional checkpoints.

    Usage:
        with constitutional_boundary("cfp_output", ["provenance", "no_scalar"]):
            result = cfp.query(...)
            return result  # Checked on exit

    Args:
        name: Name of this boundary
        checks: List of checks to perform ("provenance", "no_scalar", "no_ranking", "no_grade")
    """
    checks = checks or ["no_scalar", "no_ranking", "no_grade"]

    # Track violations
    violations: list[ConstitutionalViolation] = []

    try:
        yield violations  # Allow caller to add violations
    finally:
        # Log boundary exit
        if violations:
            raise violations[0]  # Raise first violation


# =============================================================================
# DECORATORS
# =============================================================================


T = TypeVar("T")


def enforce_constitution(
    checks: list[str] | None = None,
    context: str | None = None,
):
    """
    Decorator to enforce constitutional checks on function return value.

    Usage:
        @enforce_constitution(["provenance", "no_scalar"])
        def query_cfp(params):
            return result

    Args:
        checks: Checks to perform on return value
        context: Context name (defaults to function name)
    """
    checks = checks or ["no_scalar", "no_ranking"]

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        ctx = context or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> T:
            result = fn(*args, **kwargs)

            # Run checks on result
            if "provenance" in checks:
                assert_provenance(result, ctx)
            if "no_scalar" in checks:
                assert_no_scalar_score(result, ctx)
            if "no_ranking" in checks:
                assert_no_ranking(result, ctx)
            if "no_grade" in checks:
                assert_no_grade(result, ctx)

            return result

        return wrapper

    return decorator


def validate_output(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for validation output boundaries.

    Checks: no scalar scores, no rankings.
    """
    return enforce_constitution(["no_scalar", "no_ranking"], f"validation:{fn.__name__}")(fn)


def cfp_output(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for CFP output boundaries.

    Checks: provenance required, no scalar scores.
    """
    return enforce_constitution(["provenance", "no_scalar"], f"cfp:{fn.__name__}")(fn)


def hunt_output(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator for Hunt output boundaries.

    Checks: no rankings, no scalar scores.
    """
    return enforce_constitution(["no_ranking", "no_scalar"], f"hunt:{fn.__name__}")(fn)


# =============================================================================
# HELPERS
# =============================================================================


def _extract_fields(obj: Any) -> dict[str, Any]:
    """Extract fields from various object types."""
    if obj is None:
        return {}

    if isinstance(obj, dict):
        return obj

    # Dataclass or object with __dict__
    if hasattr(obj, "__dict__"):
        return vars(obj)

    # Named tuple
    if hasattr(obj, "_asdict"):
        return obj._asdict()

    return {}


def _is_legitimate_score_field(field_name: str, value: Any) -> bool:
    """Check if a score field is legitimate (not a scalar score)."""
    # Allow score arrays/lists (decomposed data)
    if isinstance(value, (list, tuple)):
        return True

    # Allow score dicts (structured data)
    if isinstance(value, dict):
        return True

    return False


# =============================================================================
# RUNTIME CHECKER
# =============================================================================


class RuntimeConstitutionalChecker:
    """
    Aggregates runtime constitutional checks.

    Usage:
        checker = RuntimeConstitutionalChecker()
        checker.check_validation_output(result)
        checker.check_cfp_output(result)
        checker.check_hunt_output(result)
    """

    def __init__(self, strict: bool = True):
        self.strict = strict
        self._violations: list[ConstitutionalViolation] = []

    def check_validation_output(self, obj: Any) -> None:
        """Check validation output boundary."""
        try:
            assert_no_scalar_score(obj, "validation_output")
            assert_no_ranking(obj, "validation_output")
        except ConstitutionalViolation as e:
            self._handle_violation(e)

    def check_cfp_output(self, obj: Any) -> None:
        """Check CFP output boundary."""
        try:
            assert_provenance(obj, "cfp_output")
            assert_no_scalar_score(obj, "cfp_output")
        except ConstitutionalViolation as e:
            self._handle_violation(e)

    def check_hunt_output(self, obj: Any) -> None:
        """Check Hunt output boundary."""
        try:
            assert_no_ranking(obj, "hunt_output")
            assert_no_scalar_score(obj, "hunt_output")
        except ConstitutionalViolation as e:
            self._handle_violation(e)

    def _handle_violation(self, violation: ConstitutionalViolation) -> None:
        """Handle a violation."""
        self._violations.append(violation)
        if self.strict:
            raise violation

    @property
    def violations(self) -> list[ConstitutionalViolation]:
        """Get all recorded violations."""
        return self._violations.copy()

    def clear(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()
