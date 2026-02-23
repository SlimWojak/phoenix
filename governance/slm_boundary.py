"""
SLM Boundary Enforcement — S41 Track A
======================================

Runtime assertions that enforce the SLM read-only boundary.
The SLM can CLASSIFY. It cannot CREATE.

INVARIANTS:
  INV-SLM-READONLY-1: SLM output cannot mutate state
  INV-SLM-NO-CREATE-1: SLM cannot create new information
  INV-SLM-CLASSIFICATION-ONLY-1: Output is classification, not decision

Date: 2026-01-23
Sprint: S41 Phase 2A
"""

from __future__ import annotations

import functools
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, TypeVar

from .runtime_assertions import ConstitutionalViolation


# =============================================================================
# EXCEPTIONS
# =============================================================================


class SLMBoundaryViolation(ConstitutionalViolation):
    """Raised when SLM attempts to violate its read-only boundary."""

    def __init__(self, violation_type: str, details: str):
        self.violation_type = violation_type
        super().__init__(
            violation_type=f"SLM_BOUNDARY_{violation_type}",
            context="slm_output",
            details=details,
        )


class SLMStateAttempt(SLMBoundaryViolation):
    """Raised when SLM output attempts to mutate state."""

    def __init__(self, attempted_mutation: str):
        self.attempted_mutation = attempted_mutation
        super().__init__(
            violation_type="STATE_MUTATION",
            details=f"SLM attempted state mutation: {attempted_mutation}",
        )


class SLMCreationAttempt(SLMBoundaryViolation):
    """Raised when SLM attempts to create new information."""

    def __init__(self, created_content: str):
        self.created_content = created_content
        super().__init__(
            violation_type="INFORMATION_CREATION",
            details=f"SLM attempted to create: {created_content[:100]}...",
        )


class SLMRecommendationAttempt(SLMBoundaryViolation):
    """Raised when SLM attempts to make recommendations."""

    def __init__(self, recommendation: str):
        self.recommendation = recommendation
        super().__init__(
            violation_type="RECOMMENDATION",
            details=f"SLM attempted recommendation: {recommendation}",
        )


# =============================================================================
# CLASSIFICATION TYPES
# =============================================================================


class SLMClassification(Enum):
    """Valid SLM classification outputs."""

    VALID_FACTS = "VALID_FACTS"
    BANNED = "BANNED"


class SLMReasonCode(Enum):
    """Reason codes for BANNED classification."""

    CAUSAL = "CAUSAL"
    RANKING = "RANKING"
    SCORING = "SCORING"
    RECOMMENDATION = "RECOMMENDATION"
    SYNTHESIS = "SYNTHESIS"
    ADJECTIVE = "ADJECTIVE"
    BANNER_MISSING = "BANNER_MISSING"
    PROVENANCE_MISSING = "PROVENANCE_MISSING"


class SLMConfidence(Enum):
    """Advisory confidence levels (NOT binding scores)."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =============================================================================
# OUTPUT DATACLASS
# =============================================================================


@dataclass(frozen=True)  # Frozen = immutable
class SLMOutput:
    """
    Valid SLM output structure.

    Immutable by design — SLM cannot modify its own output.

    INV-SLM-READONLY-1: This structure enforces read-only output.
    """

    classification: SLMClassification
    reason_code: SLMReasonCode | None = None
    violation_details: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    confidence: SLMConfidence | None = None

    def __post_init__(self):
        """Validate output structure."""
        # BANNED must have reason_code
        if self.classification == SLMClassification.BANNED and self.reason_code is None:
            raise ValueError("BANNED classification requires reason_code")

    def to_string(self) -> str:
        """Convert to canonical string format."""
        if self.classification == SLMClassification.VALID_FACTS:
            return "VALID_FACTS"
        return f"BANNED — {self.reason_code.value}"

    @classmethod
    def from_string(cls, s: str) -> "SLMOutput":
        """Parse from canonical string format."""
        s = s.strip()

        if s == "VALID_FACTS":
            return cls(classification=SLMClassification.VALID_FACTS)

        if s.startswith("BANNED"):
            # Extract reason code
            parts = s.split("—")
            if len(parts) >= 2:
                reason_str = parts[1].strip()
                try:
                    reason = SLMReasonCode(reason_str)
                    return cls(
                        classification=SLMClassification.BANNED,
                        reason_code=reason,
                    )
                except ValueError:
                    raise ValueError(f"Unknown reason code: {reason_str}")

        raise ValueError(f"Invalid SLM output format: {s}")


# =============================================================================
# BOUNDARY CHECKS
# =============================================================================


# Patterns that indicate state mutation attempts
STATE_MUTATION_PATTERNS = [
    r"\bset\s+",
    r"\bupdate\s+",
    r"\bmodify\s+",
    r"\bchange\s+",
    r"\bcreate\s+",
    r"\bdelete\s+",
    r"\bemit\s+",
    r"\bsend\s+",
    r"\bexecute\s+",
    r"\btrigger\s+",
    r"\bfire\s+",
    r"\braise\s+",
]

# Patterns that indicate new information creation
CREATION_PATTERNS = [
    r"\bI think\b",
    r"\bI believe\b",
    r"\bI suggest\b",
    r"\bI recommend\b",
    r"\bIn my opinion\b",
    r"\bIt seems\b",
    r"\bIt appears\b",
    r"\bProbably\b",
    r"\bLikely\b",
    r"\bMight be\b",
    r"\bCould be\b",
]

# Patterns that indicate recommendations
RECOMMENDATION_PATTERNS = [
    r"\bshould\b",
    r"\bconsider\b",
    r"\brecommend\b",
    r"\bsuggest\b",
    r"\badvise\b",
    r"\bbetter to\b",
    r"\bworse to\b",
    r"\bavoid\b",
    r"\bprefer\b",
]

# Compile patterns
_STATE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in STATE_MUTATION_PATTERNS]
_CREATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CREATION_PATTERNS]
_RECOMMENDATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in RECOMMENDATION_PATTERNS]


def check_no_state_mutation(output: str) -> None:
    """
    Assert output contains no state mutation attempts.

    INV-SLM-READONLY-1: SLM output cannot mutate state.

    Raises:
        SLMStateAttempt: If state mutation detected
    """
    for pattern in _STATE_PATTERNS:
        match = pattern.search(output)
        if match:
            raise SLMStateAttempt(match.group())


def check_no_creation(output: str) -> None:
    """
    Assert output contains no new information creation.

    INV-SLM-NO-CREATE-1: SLM cannot create new information.

    Raises:
        SLMCreationAttempt: If creation detected
    """
    for pattern in _CREATION_PATTERNS:
        match = pattern.search(output)
        if match:
            raise SLMCreationAttempt(match.group())


def check_no_recommendation(output: str) -> None:
    """
    Assert output contains no recommendations.

    INV-SLM-CLASSIFICATION-ONLY-1: Output is classification, not decision.

    Raises:
        SLMRecommendationAttempt: If recommendation detected
    """
    for pattern in _RECOMMENDATION_PATTERNS:
        match = pattern.search(output)
        if match:
            raise SLMRecommendationAttempt(match.group())


def validate_slm_output(output: Any) -> SLMOutput:
    """
    Validate that output conforms to SLM boundary.

    Args:
        output: Raw output from SLM (string or SLMOutput)

    Returns:
        Validated SLMOutput

    Raises:
        SLMBoundaryViolation: If boundary violated
    """
    # Already validated
    if isinstance(output, SLMOutput):
        return output

    # String output — parse and validate
    if isinstance(output, str):
        # Check for violations in the raw string
        check_no_state_mutation(output)
        check_no_creation(output)
        check_no_recommendation(output)

        # Parse to structured output
        return SLMOutput.from_string(output)

    # Dict output — convert to SLMOutput
    if isinstance(output, dict):
        classification_str = output.get("classification", "")
        reason_code_str = output.get("reason_code")

        try:
            classification = SLMClassification(classification_str)
            reason_code = SLMReasonCode(reason_code_str) if reason_code_str else None

            return SLMOutput(
                classification=classification,
                reason_code=reason_code,
            )
        except ValueError as e:
            raise SLMBoundaryViolation(
                violation_type="INVALID_OUTPUT",
                details=str(e),
            )

    raise SLMBoundaryViolation(
        violation_type="INVALID_TYPE",
        details=f"Expected str, dict, or SLMOutput, got {type(output).__name__}",
    )


# =============================================================================
# DECORATORS
# =============================================================================


T = TypeVar("T")


def slm_output_guard(fn: Callable[..., T]) -> Callable[..., SLMOutput]:
    """
    Decorator to enforce SLM boundary on function output.

    Usage:
        @slm_output_guard
        def classify_content(content: str) -> str:
            return model.predict(content)

    INV-SLM-READONLY-1: Decorated functions cannot return state mutations.
    INV-SLM-NO-CREATE-1: Decorated functions cannot create information.
    INV-SLM-CLASSIFICATION-ONLY-1: Output is forced to classification format.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> SLMOutput:
        result = fn(*args, **kwargs)
        return validate_slm_output(result)

    return wrapper


def slm_input_guard(fn: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to validate SLM input is read-only facts.

    Usage:
        @slm_input_guard
        def classify_content(content: str) -> str:
            ...

    Validates that input content is pure facts, not mutable state.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> T:
        # Validate first positional arg (content) if string
        if args and isinstance(args[0], str):
            content = args[0]

            # Check input doesn't contain executable code
            if "{{" in content and "}}" in content:
                # Allow Jinja variables, but not expressions
                if "{{" in content and "{%" in content:
                    raise SLMBoundaryViolation(
                        violation_type="EXECUTABLE_INPUT",
                        details="Input contains executable Jinja expressions",
                    )

        return fn(*args, **kwargs)

    return wrapper


def slm_full_guard(fn: Callable[..., T]) -> Callable[..., SLMOutput]:
    """
    Full SLM boundary guard — input and output validation.

    Usage:
        @slm_full_guard
        def classify_content(content: str) -> str:
            return model.predict(content)
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> SLMOutput:
        # Input validation
        if args and isinstance(args[0], str):
            content = args[0]
            if "{{" in content and "{%" in content:
                raise SLMBoundaryViolation(
                    violation_type="EXECUTABLE_INPUT",
                    details="Input contains executable Jinja expressions",
                )

        # Execute function
        result = fn(*args, **kwargs)

        # Output validation
        return validate_slm_output(result)

    return wrapper


# =============================================================================
# RUNTIME CHECKER
# =============================================================================


class SLMBoundaryChecker:
    """
    Runtime boundary checker for SLM outputs.

    Aggregates violations for audit trail.

    Usage:
        checker = SLMBoundaryChecker()
        output = checker.check(raw_output)
        if checker.has_violations:
            log_violations(checker.violations)
    """

    def __init__(self, strict: bool = True):
        self.strict = strict
        self._violations: list[SLMBoundaryViolation] = []

    def check(self, output: Any) -> SLMOutput | None:
        """
        Check output against boundary.

        Returns validated SLMOutput or None if violation (non-strict mode).

        Raises:
            SLMBoundaryViolation: In strict mode if violation detected
        """
        try:
            return validate_slm_output(output)
        except SLMBoundaryViolation as e:
            self._violations.append(e)
            if self.strict:
                raise
            return None

    def check_raw_string(self, output: str) -> list[str]:
        """
        Check raw string for boundary violations.

        Returns list of violation descriptions (for testing/debugging).
        """
        violations = []

        for pattern in _STATE_PATTERNS:
            if pattern.search(output):
                violations.append(f"STATE_MUTATION: {pattern.pattern}")

        for pattern in _CREATION_PATTERNS:
            if pattern.search(output):
                violations.append(f"CREATION: {pattern.pattern}")

        for pattern in _RECOMMENDATION_PATTERNS:
            if pattern.search(output):
                violations.append(f"RECOMMENDATION: {pattern.pattern}")

        return violations

    @property
    def violations(self) -> list[SLMBoundaryViolation]:
        """Get all recorded violations."""
        return self._violations.copy()

    @property
    def has_violations(self) -> bool:
        """Check if any violations recorded."""
        return len(self._violations) > 0

    def clear(self) -> None:
        """Clear recorded violations."""
        self._violations.clear()


# =============================================================================
# CONTENT CLASSIFIER (Pre-SLM Validation)
# =============================================================================


class ContentClassifier:
    """
    Pre-SLM content classifier.

    Uses rule-based detection before SLM inference.
    Useful for fast-path rejection of obvious violations.
    """

    # Banned word patterns (from narrator/templates.py + extensions)
    BANNED_PATTERNS = {
        SLMReasonCode.CAUSAL: [
            r"\bbecause\b",
            r"\bdue to\b",
            r"\bdriven by\b",
            r"\bcaused\b",
            r"\bas a result\b",
            r"\btherefore\b",
            r"\bconsequently\b",
            r"\bleads to\b",
            r"\bresults in\b",
            r"\bthe data suggests\b",
            r"\bthis indicates\b",
        ],
        SLMReasonCode.RANKING: [
            r"\bbest\b",
            r"\bworst\b",
            r"\btop\b",
            r"\bbottom\b",
            r"\branked\b",
            r"\bgrade\b",
            r"\btier\b",
            r"\bsuperior\b",
            r"\binferior\b",
        ],
        SLMReasonCode.SCORING: [
            r"\bscore\b",
            r"\bviability\b",
            r"\bconfidence\b",
            r"\bprobability\b",
            r"\blikelihood\b",
            r"\b/10\b",
            r"\b/100\b",
            r"\brating\b",
        ],
        SLMReasonCode.RECOMMENDATION: [
            r"\bshould\b",
            r"\bconsider\b",
            r"\brecommend",
            r"\bsuggest",
            r"\badvise\b",
            r"\bmight want\b",
            r"\byou could\b",
            r"\bbetter to\b",
            r"\bworse to\b",
            r"\bprefer\b",
            r"\bavoid\b",
        ],
        SLMReasonCode.SYNTHESIS: [
            r"\bI noticed\b",
            r"\bI observed\b",
            r"\bit appears\b",
            r"\bseems like\b",
            r"\blooks like\b",
            r"\bprobably\b",
            r"\blikely\b",
            r"\bunlikely\b",
            r"\bin my opinion\b",
            r"\bI think\b",
            r"\bI believe\b",
        ],
        SLMReasonCode.ADJECTIVE: [
            r"\bstrong\b",
            r"\bweak\b",
            r"\bsafe\b",
            r"\bunsafe\b",
            r"\bgood\b",
            r"\bbad\b",
            r"\bexcellent\b",
            r"\bpoor\b",
            r"\boptimal\b",
            r"\bsuboptimal\b",
        ],
    }

    FACTS_BANNER = "FACTS_ONLY — NO INTERPRETATION"

    def __init__(self):
        # Compile patterns
        self._compiled: dict[SLMReasonCode, list[re.Pattern]] = {}
        for reason, patterns in self.BANNED_PATTERNS.items():
            self._compiled[reason] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]

    def classify(self, content: str) -> SLMOutput:
        """
        Classify content using rule-based detection.

        Returns SLMOutput with classification and violations.
        """
        violations: list[dict[str, Any]] = []

        # Check for banner
        if self.FACTS_BANNER not in content:
            return SLMOutput(
                classification=SLMClassification.BANNED,
                reason_code=SLMReasonCode.BANNER_MISSING,
            )

        # Check banned patterns
        for reason, patterns in self._compiled.items():
            for pattern in patterns:
                match = pattern.search(content)
                if match:
                    violations.append({
                        "word": match.group(),
                        "position": match.start(),
                        "reason": reason.value,
                    })

        if violations:
            # Return first violation's reason (most severe)
            first_reason = SLMReasonCode(violations[0]["reason"])
            return SLMOutput(
                classification=SLMClassification.BANNED,
                reason_code=first_reason,
                violation_details=tuple(violations[:10]),  # Cap at 10
            )

        return SLMOutput(classification=SLMClassification.VALID_FACTS)

    def quick_check(self, content: str) -> bool:
        """
        Quick boolean check — is content valid?

        Faster than full classify() when you just need pass/fail.
        """
        if self.FACTS_BANNER not in content:
            return False

        for patterns in self._compiled.values():
            for pattern in patterns:
                if pattern.search(content):
                    return False

        return True


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    # Exceptions
    "SLMBoundaryViolation",
    "SLMStateAttempt",
    "SLMCreationAttempt",
    "SLMRecommendationAttempt",
    # Types
    "SLMClassification",
    "SLMReasonCode",
    "SLMConfidence",
    "SLMOutput",
    # Decorators
    "slm_output_guard",
    "slm_input_guard",
    "slm_full_guard",
    # Functions
    "validate_slm_output",
    "check_no_state_mutation",
    "check_no_creation",
    "check_no_recommendation",
    # Classes
    "SLMBoundaryChecker",
    "ContentClassifier",
]
