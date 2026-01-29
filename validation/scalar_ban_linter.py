"""
Scalar Ban Linter — S39 Track F
===============================

THE CONSTITUTIONAL CEILING.
Scans ALL validation outputs for forbidden scalar patterns.
The "Linter of Linters."

INVARIANTS:
  - INV-SCALAR-BAN: No composite scores
  - INV-NEUTRAL-ADJECTIVES: No evaluative words
  - INV-NO-AGGREGATE-SCALAR: No avg_* fields
  - INV-VISUAL-PARITY: No color metadata
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# =============================================================================
# CONSTANTS
# =============================================================================


class ViolationType(str, Enum):
    """Types of scalar ban violations."""

    FORBIDDEN_FIELD = "FORBIDDEN_FIELD"
    FORBIDDEN_VALUE = "FORBIDDEN_VALUE"
    EVALUATIVE_ADJECTIVE = "EVALUATIVE_ADJECTIVE"
    THRESHOLD_IMPLICATION = "THRESHOLD_IMPLICATION"
    COMPARISON_SUPERLATIVE = "COMPARISON_SUPERLATIVE"
    SUMMARY_SYNTHESIS = "SUMMARY_SYNTHESIS"
    AVG_FIELD = "AVG_FIELD"
    COLOR_METADATA = "COLOR_METADATA"
    VERDICT_LANGUAGE = "VERDICT_LANGUAGE"


# =============================================================================
# FORBIDDEN PATTERNS
# =============================================================================

FORBIDDEN_FIELD_PATTERNS = [
    r".*_score$",
    r".*_index$",
    r".*_rating$",
    r".*_rank$",
    r"^viability.*",
    r"^robustness.*",
    r"^quality.*",
    r"^overall.*",
    r"^composite.*",
    r"^verdict$",
    r"^recommendation$",
    r"^avg_.*",  # INV-NO-AGGREGATE-SCALAR
    r"^risk_level$",
    r"^danger_zone$",
    r"^acceptable.*",
    r"^importance.*",
    r"^impact.*",
]

FORBIDDEN_VALUE_PATTERNS = [
    r"\bPASS\b.*\bFAIL\b",
    r"\bGOOD\b.*\bBAD\b",
    r"\bHIGH\b.*\bMEDIUM\b.*\bLOW\b",
    r"\b[A-F]\b.*grade",  # Letter grades
    r"\d+\s*/\s*100",  # X/100 scores
]

EVALUATIVE_ADJECTIVES = [
    "strong",
    "weak",
    "solid",
    "fragile",
    "consistent",
    "inconsistent",
    "healthy",
    "unhealthy",
    "safe",
    "unsafe",
    "concerning",
    "promising",
    "robust",
    "brittle",
    "stable",  # when used as judgment
    "unstable",
    "reliable",
    "unreliable",
]

THRESHOLD_IMPLICATIONS = [
    r"if\s+\w+\s*[><=]+\s*[\d.]+\s+then",
    r"above\s+threshold",
    r"below\s+acceptable",
    r"within\s+tolerance",
    r"exceeds\s+limit",
]

COMPARISON_SUPERLATIVES = [
    "most sensitive",
    "least robust",
    "best performing",
    "worst case",  # as verdict, not percentile
    "most important",
    "highest priority",
]

SUMMARY_SYNTHESIS = [
    r"\boverall\b",
    r"in summary",
    r"taken together",
    r"\bcombined\b",
    r"net assessment",
]

VERDICT_LANGUAGE = [
    "appears overfit",
    "likely fragile",
    r"\brecommend\b",
    r"\bacceptable\b",
    r"\bsuggests\b",
    "indicates that",
    "danger zone",
]

COLOR_METADATA_FIELDS = [
    "color_scale",
    "highlight_threshold",
    "emphasis_rules",
    "color_coding",
]


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class ScalarBanViolation:
    """A scalar ban violation."""

    violation_type: ViolationType
    field_or_text: str
    pattern_matched: str
    message: str


@dataclass
class ScalarBanResult:
    """Result of scalar ban linting."""

    valid: bool
    violations: list[ScalarBanViolation] = field(default_factory=list)

    @property
    def error_messages(self) -> list[str]:
        return [f"{v.violation_type.value}: {v.message}" for v in self.violations]


# =============================================================================
# SCALAR BAN LINTER
# =============================================================================


class ScalarBanLinter:
    """
    THE CONSTITUTIONAL CEILING.

    Scans validation outputs for forbidden scalar patterns.
    The "Linter of Linters."

    INVARIANTS:
      - INV-SCALAR-BAN: No composite scores
      - INV-NEUTRAL-ADJECTIVES: No evaluative words
      - INV-NO-AGGREGATE-SCALAR: No avg_* fields
      - INV-VISUAL-PARITY: No color metadata
    """

    def lint(self, data: dict[str, Any]) -> ScalarBanResult:
        """
        Lint validation output for forbidden patterns.

        Args:
            data: Validation output dictionary

        Returns:
            ScalarBanResult with violations
        """
        violations: list[ScalarBanViolation] = []

        # Check field names
        violations.extend(self._check_field_names(data))

        # Check values for patterns
        violations.extend(self._check_values(data))

        # Check for color metadata
        violations.extend(self._check_color_metadata(data))

        return ScalarBanResult(valid=len(violations) == 0, violations=violations)

    def lint_text(self, text: str) -> ScalarBanResult:
        """
        Lint text content for forbidden patterns.

        Args:
            text: Text to lint

        Returns:
            ScalarBanResult with violations
        """
        violations: list[ScalarBanViolation] = []
        text_lower = text.lower()

        # Check evaluative adjectives
        for adj in EVALUATIVE_ADJECTIVES:
            if adj in text_lower:
                violations.append(
                    ScalarBanViolation(
                        violation_type=ViolationType.EVALUATIVE_ADJECTIVE,
                        field_or_text=text[:50],
                        pattern_matched=adj,
                        message=f"Evaluative adjective '{adj}' forbidden. "
                        "Use mathematical descriptors only.",
                    )
                )

        # Check threshold implications
        for pattern in THRESHOLD_IMPLICATIONS:
            if re.search(pattern, text_lower):
                violations.append(
                    ScalarBanViolation(
                        violation_type=ViolationType.THRESHOLD_IMPLICATION,
                        field_or_text=text[:50],
                        pattern_matched=pattern,
                        message="Threshold implication language forbidden.",
                    )
                )

        # Check comparison superlatives
        for phrase in COMPARISON_SUPERLATIVES:
            if phrase in text_lower:
                violations.append(
                    ScalarBanViolation(
                        violation_type=ViolationType.COMPARISON_SUPERLATIVE,
                        field_or_text=text[:50],
                        pattern_matched=phrase,
                        message=f"Comparison superlative '{phrase}' forbidden.",
                    )
                )

        # Check summary synthesis
        for pattern in SUMMARY_SYNTHESIS:
            if re.search(pattern, text_lower):
                violations.append(
                    ScalarBanViolation(
                        violation_type=ViolationType.SUMMARY_SYNTHESIS,
                        field_or_text=text[:50],
                        pattern_matched=pattern,
                        message="Summary synthesis language forbidden.",
                    )
                )

        # Check verdict language
        for pattern in VERDICT_LANGUAGE:
            if re.search(pattern, text_lower):
                violations.append(
                    ScalarBanViolation(
                        violation_type=ViolationType.VERDICT_LANGUAGE,
                        field_or_text=text[:50],
                        pattern_matched=pattern,
                        message="Verdict language forbidden.",
                    )
                )

        return ScalarBanResult(valid=len(violations) == 0, violations=violations)

    def _check_field_names(
        self,
        data: dict[str, Any],
        prefix: str = "",
    ) -> list[ScalarBanViolation]:
        """Check field names for forbidden patterns."""
        violations: list[ScalarBanViolation] = []

        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            key_lower = key.lower()

            # Check against forbidden patterns
            for pattern in FORBIDDEN_FIELD_PATTERNS:
                if re.match(pattern, key_lower):
                    # Special handling for avg_*
                    if pattern == r"^avg_.*":
                        violations.append(
                            ScalarBanViolation(
                                violation_type=ViolationType.AVG_FIELD,
                                field_or_text=full_key,
                                pattern_matched=pattern,
                                message=f"avg_* field '{key}' forbidden. "
                                "Return full arrays instead. "
                                "INV-NO-AGGREGATE-SCALAR violation.",
                            )
                        )
                    else:
                        violations.append(
                            ScalarBanViolation(
                                violation_type=ViolationType.FORBIDDEN_FIELD,
                                field_or_text=full_key,
                                pattern_matched=pattern,
                                message=f"Forbidden field pattern '{key}'.",
                            )
                        )
                    break

            # Recurse into nested dicts
            if isinstance(value, dict):
                violations.extend(self._check_field_names(value, full_key))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        violations.extend(self._check_field_names(item, f"{full_key}[{i}]"))

        return violations

    def _check_values(self, data: dict[str, Any]) -> list[ScalarBanViolation]:
        """Check values for forbidden patterns."""
        violations: list[ScalarBanViolation] = []

        def check_value(v: Any, path: str) -> None:
            if isinstance(v, str):
                result = self.lint_text(v)
                violations.extend(result.violations)
            elif isinstance(v, dict):
                for k, val in v.items():
                    check_value(val, f"{path}.{k}")
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    check_value(item, f"{path}[{i}]")

        for key, value in data.items():
            check_value(value, key)

        return violations

    def _check_color_metadata(
        self,
        data: dict[str, Any],
    ) -> list[ScalarBanViolation]:
        """Check for color metadata (INV-VISUAL-PARITY)."""
        violations: list[ScalarBanViolation] = []

        def check_dict(d: dict[str, Any], path: str = "") -> None:
            for key, value in d.items():
                full_path = f"{path}.{key}" if path else key

                if key.lower() in COLOR_METADATA_FIELDS:
                    if value is not None:
                        violations.append(
                            ScalarBanViolation(
                                violation_type=ViolationType.COLOR_METADATA,
                                field_or_text=full_path,
                                pattern_matched=key,
                                message=f"Color metadata '{key}' must be null. "
                                "INV-VISUAL-PARITY violation.",
                            )
                        )

                if isinstance(value, dict):
                    check_dict(value, full_path)

        check_dict(data)
        return violations


# =============================================================================
# EXCEPTIONS
# =============================================================================


class ScalarBanError(Exception):
    """Raised when scalar ban violation detected."""

    def __init__(self, violations: list[ScalarBanViolation]):
        self.violations = violations
        messages = [v.message for v in violations]
        super().__init__(f"ScalarBanError: {'; '.join(messages)}")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "ScalarBanLinter",
    "ScalarBanResult",
    "ScalarBanViolation",
    "ScalarBanError",
    "ViolationType",
    "FORBIDDEN_FIELD_PATTERNS",
    "EVALUATIVE_ADJECTIVES",
    "THRESHOLD_IMPLICATIONS",
    "COMPARISON_SUPERLATIVES",
    "SUMMARY_SYNTHESIS",
    "VERDICT_LANGUAGE",
    "COLOR_METADATA_FIELDS",
]
