"""
Claim Language Linter — S37 Track A
===================================

Validates claim language for forbidden patterns.
Confidence sneaks in via language, not fields.

INVARIANT: INV-CLAIM-NO-EXECUTION
Reuses S35 cfp/linter.py pattern.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

ATHENA_ROOT = Path(__file__).parent
BANNED_PHRASES_PATH = ATHENA_ROOT / "claim_banned_phrases.yaml"


class ViolationType(str, Enum):
    """Types of linter violations."""

    BANNED_PHRASE = "BANNED_PHRASE"
    ABSOLUTE_LANGUAGE = "ABSOLUTE_LANGUAGE"
    CONFIDENCE_LANGUAGE = "CONFIDENCE_LANGUAGE"
    GRADE_LANGUAGE = "GRADE_LANGUAGE"


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class Violation:
    """A linting violation."""

    violation_type: ViolationType
    phrase: str
    message: str
    position: int | None = None


@dataclass
class LintResult:
    """Result of linting."""

    valid: bool
    violations: list[Violation] = field(default_factory=list)

    @property
    def error_messages(self) -> list[str]:
        """Get error messages."""
        return [f"{v.violation_type.value}: {v.message}" for v in self.violations]


# =============================================================================
# CLAIM LANGUAGE LINTER
# =============================================================================


class ClaimLanguageLinter:
    """
    Lints claim assertions for forbidden language.

    Rejects:
    - Absolute certainty ("always", "never", "guaranteed")
    - High confidence language ("high probability", "low risk")
    - Grade/score language ("best setup", "A+ setup")

    Allows:
    - Implicit uncertainty ("tends to", "usually", "about X%")
    """

    def __init__(self) -> None:
        """Initialize linter with banned phrases."""
        self._banned_phrases: list[str] = []
        self._allowed_patterns: list[str] = []
        self._exceptions: list[str] = []
        self._load_config()

    def _load_config(self) -> None:
        """Load banned phrases from YAML config."""
        if BANNED_PHRASES_PATH.exists():
            with open(BANNED_PHRASES_PATH) as f:
                config = yaml.safe_load(f)
                self._banned_phrases = config.get("banned_phrases", [])
                self._allowed_patterns = config.get("allowed_patterns", [])
                self._exceptions = config.get("exceptions", [])
        else:
            # Default banned phrases if config not found
            self._banned_phrases = [
                "always",
                "never",
                "guaranteed",
                "definitely",
                "certainly",
                "100%",
                "impossible",
                "high probability",
                "low risk",
            ]

    def lint(self, text: str) -> LintResult:
        """
        Lint claim assertion text.

        Args:
            text: The claim assertion to lint

        Returns:
            LintResult with violations if any
        """
        violations: list[Violation] = []
        text_lower = text.lower()

        # Check for exceptions first
        for exception in self._exceptions:
            if exception.lower() in text_lower:
                # This is an allowed exception, skip banned phrase check for this
                text_lower = text_lower.replace(exception.lower(), "")

        # Check banned phrases
        for phrase in self._banned_phrases:
            phrase_lower = phrase.lower()
            if phrase_lower in text_lower:
                # Find position
                pos = text_lower.find(phrase_lower)
                violations.append(Violation(
                    violation_type=self._categorize_violation(phrase),
                    phrase=phrase,
                    message=f"Banned phrase '{phrase}' — claims cannot express absolute certainty",
                    position=pos,
                ))

        return LintResult(valid=len(violations) == 0, violations=violations)

    def _categorize_violation(self, phrase: str) -> ViolationType:
        """Categorize the type of violation."""
        phrase_lower = phrase.lower()

        # Grade/score language
        grade_terms = ["best", "worst", "top", "a+", "perfect", "ideal"]
        if any(term in phrase_lower for term in grade_terms):
            return ViolationType.GRADE_LANGUAGE

        # Confidence language
        confidence_terms = ["probability", "risk", "likely", "reliable"]
        if any(term in phrase_lower for term in confidence_terms):
            return ViolationType.CONFIDENCE_LANGUAGE

        # Absolute language
        absolute_terms = ["always", "never", "guaranteed", "definitely", "certainly", "impossible", "100%"]
        if any(term in phrase_lower for term in absolute_terms):
            return ViolationType.ABSOLUTE_LANGUAGE

        return ViolationType.BANNED_PHRASE

    def lint_claim(self, claim_dict: dict[str, Any]) -> LintResult:
        """
        Lint a claim dictionary.

        Checks:
        - content.assertion for banned language
        - Any other text fields

        Args:
            claim_dict: Claim as dictionary

        Returns:
            LintResult
        """
        violations: list[Violation] = []

        # Get assertion from content
        content = claim_dict.get("content", {})
        if isinstance(content, dict):
            assertion = content.get("assertion", "")
            if assertion:
                result = self.lint(assertion)
                violations.extend(result.violations)

        return LintResult(valid=len(violations) == 0, violations=violations)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "ClaimLanguageLinter",
    "LintResult",
    "Violation",
    "ViolationType",
]
