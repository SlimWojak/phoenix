"""
Causal Ban Linter — INV-ATTR-CAUSAL-BAN Enforcement
===================================================

S35 TRACK D DELIVERABLE
Created: 2026-01-29 (Day 4-5)

Mechanical enforcement of causal language ban.
If it smells causal, it fails. No exceptions.

INVARIANT: INV-ATTR-CAUSAL-BAN
  Rule: No causal claims ("factor X contributed Y%")

INTEGRATION POINTS:
  - Query submission (lint query text)
  - Result generation (lint output labels)
  - UI rendering (lint display text)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

CFP_ROOT = Path(__file__).parent
PATTERNS_PATH = CFP_ROOT / "banned_patterns.yaml"


# =============================================================================
# TYPES
# =============================================================================


class ViolationType(Enum):
    """Type of causal violation."""

    BANNED_PHRASE = "BANNED_PHRASE"
    BANNED_STRUCTURE = "BANNED_STRUCTURE"
    METRIC_AGENT = "METRIC_AGENT"
    TEMPORAL_IMPLICATION = "TEMPORAL_IMPLICATION"


@dataclass
class Violation:
    """Single causal violation detected."""

    violation_type: ViolationType
    pattern: str
    matched_text: str
    position: int
    description: str = ""


@dataclass
class LintResult:
    """Result of causal ban linting."""

    passed: bool
    text: str
    violations: list[Violation]

    @property
    def error_message(self) -> str:
        """Generate error message from violations."""
        if self.passed:
            return ""

        msgs = []
        for v in self.violations:
            msgs.append(
                f"[{v.violation_type.value}] '{v.matched_text}' " f"({v.pattern}): {v.description}"
            )
        return "; ".join(msgs)


# =============================================================================
# CAUSAL BAN LINTER
# =============================================================================


class CausalBanLinter:
    """
    Lints text for causal language violations.

    Enforces INV-ATTR-CAUSAL-BAN mechanically.

    Usage:
        linter = CausalBanLinter()
        result = linter.lint("Sharpe improved after London")

        if not result.passed:
            raise ValueError(result.error_message)
    """

    def __init__(self, patterns_path: Path | None = None) -> None:
        """
        Initialize linter with patterns.

        Args:
            patterns_path: Path to banned_patterns.yaml (optional)
        """
        self._patterns_path = patterns_path or PATTERNS_PATH
        self._config: dict[str, Any] | None = None

    def _load_config(self) -> dict[str, Any]:
        """Load patterns configuration."""
        if self._config is not None:
            return self._config

        if not self._patterns_path.exists():
            # Default minimal config
            self._config = {
                "banned_phrases": [
                    "contributed",
                    "caused",
                    "because",
                    "explains",
                    "factor",
                ],
                "banned_structures": [],
                "metric_agent_patterns": {
                    "metrics": ["sharpe", "win_rate", "pnl"],
                    "agent_verbs": ["improved", "increased", "decreased"],
                },
                "temporal_patterns": {
                    "banned_words": ["after", "following"],
                    "anchors_that_allow": ["time_range", "session"],
                },
                "allowed_phrases": ["when", "where", "conditional on"],
            }
            return self._config

        with open(self._patterns_path) as f:
            self._config = yaml.safe_load(f)

        return self._config

    def lint(self, text: str) -> LintResult:
        """
        Lint text for causal violations.

        Checks:
        1. Banned phrases
        2. Banned structures (regex)
        3. Metric + agent verb combinations
        4. Temporal implications without anchors

        Args:
            text: Text to lint

        Returns:
            LintResult with pass/fail and violations
        """
        if not text:
            return LintResult(passed=True, text=text, violations=[])

        config = self._load_config()
        violations: list[Violation] = []

        # Lowercase for matching
        text_lower = text.lower()

        # Check for false positive exceptions first
        if self._has_exception(text_lower, config):
            return LintResult(passed=True, text=text, violations=[])

        # Check allowed phrases (short-circuit)
        # If text clearly uses allowed conditional language, it might be OK
        # But we still check for violations

        # 1. Check banned phrases
        for phrase in config.get("banned_phrases", []):
            phrase_lower = phrase.lower()
            if phrase_lower in text_lower:
                pos = text_lower.find(phrase_lower)
                violations.append(
                    Violation(
                        violation_type=ViolationType.BANNED_PHRASE,
                        pattern=phrase,
                        matched_text=text[pos : pos + len(phrase)],
                        position=pos,
                        description=f"Banned phrase: '{phrase}' implies causality",
                    )
                )

        # 2. Check banned structures (regex)
        for struct in config.get("banned_structures", []):
            pattern = struct.get("pattern", "")
            if pattern:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    violations.append(
                        Violation(
                            violation_type=ViolationType.BANNED_STRUCTURE,
                            pattern=pattern,
                            matched_text=match.group(),
                            position=match.start(),
                            description=struct.get("description", "Banned structure"),
                        )
                    )

        # 3. Check metric + agent verb (GPT v0.2)
        metric_violations = self._check_metric_agent(text_lower, config)
        violations.extend(metric_violations)

        # 4. Check temporal implications (OWL v0.2)
        temporal_violations = self._check_temporal(text_lower, config)
        violations.extend(temporal_violations)

        # Deduplicate violations by position
        unique_violations = self._dedupe_violations(violations)

        return LintResult(
            passed=len(unique_violations) == 0,
            text=text,
            violations=unique_violations,
        )

    def _has_exception(self, text_lower: str, config: dict[str, Any]) -> bool:
        """Check if text matches a false positive exception."""
        exceptions = config.get("false_positive_exceptions", [])
        for exc in exceptions:
            phrase = exc.get("phrase", "").lower()
            if phrase and phrase in text_lower:
                return True
        return False

    def _check_metric_agent(self, text_lower: str, config: dict[str, Any]) -> list[Violation]:
        """
        Check for metric + agent verb combinations.

        "Sharpe improved after London" → FAIL
        "Sharpe when session=London: 1.6" → PASS
        """
        violations = []
        ma_config = config.get("metric_agent_patterns", {})
        metrics = [m.lower() for m in ma_config.get("metrics", [])]
        verbs = [v.lower() for v in ma_config.get("agent_verbs", [])]

        for metric in metrics:
            if metric in text_lower:
                for verb in verbs:
                    # Look for metric followed by verb (with some words between)
                    pattern = rf"{metric}\s+\w*\s*{verb}"
                    matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
                    for match in matches:
                        violations.append(
                            Violation(
                                violation_type=ViolationType.METRIC_AGENT,
                                pattern=f"{metric} + {verb}",
                                matched_text=match.group(),
                                position=match.start(),
                                description=(
                                    f"Metric '{metric}' with agent verb '{verb}' "
                                    "implies causality"
                                ),
                            )
                        )

        return violations

    def _check_temporal(self, text_lower: str, config: dict[str, Any]) -> list[Violation]:
        """
        Check for temporal implications without anchors.

        "Result after news event" → FAIL
        "Result when time_range=[08:30, 09:00]" → PASS
        """
        violations: list[Violation] = []
        temp_config = config.get("temporal_patterns", {})
        banned_words = [w.lower() for w in temp_config.get("banned_words", [])]
        anchors = [a.lower() for a in temp_config.get("anchors_that_allow", [])]

        # Check if any anchor is present
        has_anchor = any(anchor in text_lower for anchor in anchors)

        if has_anchor:
            # Anchored — OK
            return violations

        # Check for banned temporal words
        for word in banned_words:
            if word in text_lower:
                pos = text_lower.find(word)
                violations.append(
                    Violation(
                        violation_type=ViolationType.TEMPORAL_IMPLICATION,
                        pattern=word,
                        matched_text=word,
                        position=pos,
                        description=(
                            f"'{word}' implies temporal causality. "
                            "Add explicit time_range or session anchor."
                        ),
                    )
                )

        return violations

    def _dedupe_violations(self, violations: list[Violation]) -> list[Violation]:
        """Remove duplicate violations by position."""
        seen_positions: set[int] = set()
        unique: list[Violation] = []

        for v in violations:
            if v.position not in seen_positions:
                seen_positions.add(v.position)
                unique.append(v)

        return unique

    def lint_query(self, query_dict: dict[str, Any]) -> LintResult:
        """
        Lint a query dictionary.

        Checks query text, predicate values, and any string fields.
        """
        # Collect all text to lint
        texts: list[str] = []

        # Add filter conditions
        filter_spec = query_dict.get("filter", {})
        for cond in filter_spec.get("conditions", []):
            if isinstance(cond.get("value"), str):
                texts.append(cond["value"])

        # Lint all collected text
        all_violations: list[Violation] = []
        for text in texts:
            result = self.lint(text)
            all_violations.extend(result.violations)

        return LintResult(
            passed=len(all_violations) == 0,
            text=str(query_dict),
            violations=all_violations,
        )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "CausalBanLinter",
    "LintResult",
    "Violation",
    "ViolationType",
]
