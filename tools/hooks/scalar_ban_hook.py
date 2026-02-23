"""
Scalar Ban Hook — S40 Track C
=============================

Constitutional patterns for detecting heretical code.
The machine does not decide. The human interprets.

PATTERNS:
  - SCALAR: scalar_score, viability_index, confidence_score
  - AVG: avg_sharpe, mean_return (hidden aggregation)
  - CAUSAL: contributed to, caused by, drove Y%
  - GRADE: Grade A/B/C, quality_grade

INVARIANTS:
  INV-SCALAR-BAN: No scalar scores
  INV-NO-AGGREGATE-SCALAR: No hidden averages
"""

from __future__ import annotations

import re
from pathlib import Path

from .pre_commit_linter import (
    PreCommitLinter,
    LintRule,
    Violation,
    ViolationSeverity,
)


# =============================================================================
# PATTERN DEFINITIONS
# =============================================================================


# Scalar score patterns - these are HERESY
SCALAR_PATTERNS = [
    re.compile(r"\bscalar_score\b", re.IGNORECASE),
    re.compile(r"\boverall_quality\b", re.IGNORECASE),
    re.compile(r"\bviability_index\b", re.IGNORECASE),
    re.compile(r"\bquality_metric\b", re.IGNORECASE),
    re.compile(r"\bconfidence_score\b", re.IGNORECASE),
    re.compile(r"\boverall_score\b", re.IGNORECASE),
    re.compile(r"\bfinal_score\b", re.IGNORECASE),
    re.compile(r"\baggregate_score\b", re.IGNORECASE),
    re.compile(r"\bcomposite_score\b", re.IGNORECASE),
    re.compile(r"\bweighted_score\b", re.IGNORECASE),
    re.compile(r"\bnormalized_score\b", re.IGNORECASE),
    re.compile(r"\b(?:rank|ranking)_(?:score|position|index)\b", re.IGNORECASE),
]

# Ranking patterns - implicit ordering is HERESY
RANKING_PATTERNS = [
    re.compile(r"\brank_\d+\b", re.IGNORECASE),
    re.compile(r"\bbest_strategy\b", re.IGNORECASE),
    re.compile(r"\bworst_strategy\b", re.IGNORECASE),
    re.compile(r"\btop_performer\b", re.IGNORECASE),
    re.compile(r"\bbottom_performer\b", re.IGNORECASE),
    re.compile(r"\branked_(?:first|second|third|last)\b", re.IGNORECASE),
    re.compile(r"\b(?:winner|loser)_strategy\b", re.IGNORECASE),
]

# Average/aggregation patterns - hidden scalars
AVG_PATTERNS = [
    re.compile(r"\bavg_sharpe\b", re.IGNORECASE),
    re.compile(r"\bavg_return\b", re.IGNORECASE),
    re.compile(r"\bmean_return\b", re.IGNORECASE),
    re.compile(r"\bavg_drawdown\b", re.IGNORECASE),
    re.compile(r"\baverage_performance\b", re.IGNORECASE),
    re.compile(r"\bmean_score\b", re.IGNORECASE),
    re.compile(r"\baggregated_(?:result|metric|score)\b", re.IGNORECASE),
]

# Causal language patterns - attribution is HERESY
CAUSAL_PATTERNS = [
    re.compile(r"\bcontributed\s+to\b", re.IGNORECASE),
    re.compile(r"\bcaused\s+by\b", re.IGNORECASE),
    re.compile(r"\bdue\s+to\s+(?:factor|parameter|variable)\b", re.IGNORECASE),
    re.compile(r"\bdrove\s+\d+(?:\.\d+)?%", re.IGNORECASE),
    re.compile(r"\bresponsible\s+for\s+\d+(?:\.\d+)?%\b", re.IGNORECASE),
    re.compile(r"\battributed\s+to\b", re.IGNORECASE),
    re.compile(r"\bexplained\s+by\b", re.IGNORECASE),
]

# Grade patterns - discrete ratings are HERESY
GRADE_PATTERNS = [
    re.compile(r"\bGrade\s+[A-F]\b", re.IGNORECASE),
    re.compile(r"\bquality_grade\b", re.IGNORECASE),
    re.compile(r"\bsetup_rating\b", re.IGNORECASE),
    re.compile(r"\bperformance_tier\b", re.IGNORECASE),
    re.compile(r"\brating_[A-F]\b", re.IGNORECASE),
    re.compile(r"\b(?:excellent|good|average|poor|bad)_(?:quality|rating)\b", re.IGNORECASE),
    re.compile(r"\bpass(?:ed)?_(?:grade|rating)\b", re.IGNORECASE),
    re.compile(r"\bfail(?:ed)?_(?:grade|rating)\b", re.IGNORECASE),
]

# Verdict patterns - machine should not judge
VERDICT_PATTERNS = [
    re.compile(r"\bverdict\s*[:=]\s*['\"](?:pass|fail|good|bad)", re.IGNORECASE),
    re.compile(r"\brecommendation\s*[:=]\s*['\"](?:buy|sell|hold)", re.IGNORECASE),
    re.compile(r"\bdecision\s*[:=]\s*['\"](?:accept|reject)", re.IGNORECASE),
]


# =============================================================================
# EXCLUSION FILTERS
# =============================================================================


def is_in_comment_or_docstring(line: str, matched: str) -> bool:
    """Check if match is in a comment or docstring (still counted but noted)."""
    # We still want to catch these - they're often where heresy hides!
    # This filter is for future use if we want to distinguish
    return False


def is_test_mock_data(line: str, matched: str) -> bool:
    """Check if this is test mock data (expected violation)."""
    # Allow in test files that explicitly test for violations
    lower = line.lower()
    return "test_catches" in lower or "expected_violation" in lower


# =============================================================================
# LINT RULES
# =============================================================================


def get_constitutional_rules() -> list[LintRule]:
    """Get all constitutional lint rules."""
    return [
        LintRule(
            id="INV-SCALAR-BAN",
            name="Scalar Score Ban",
            patterns=SCALAR_PATTERNS,
            message="Scalar scores violate the constitution. Use decomposed metrics.",
            severity=ViolationSeverity.ERROR,
            exclude_files=["tests/test_hooks/*"],
        ),
        LintRule(
            id="INV-RANKING-BAN",
            name="Ranking Ban",
            patterns=RANKING_PATTERNS,
            message="Rankings violate the constitution. Present all options equally.",
            severity=ViolationSeverity.ERROR,
            exclude_files=["tests/test_hooks/*"],
        ),
        LintRule(
            id="INV-NO-AGGREGATE-SCALAR",
            name="Hidden Average Ban",
            patterns=AVG_PATTERNS,
            message="Aggregated metrics hide decomposed data. Show full arrays.",
            severity=ViolationSeverity.ERROR,
            exclude_files=["tests/test_hooks/*"],
        ),
        LintRule(
            id="INV-NEUTRAL-ADJECTIVES",
            name="Causal Language Ban",
            patterns=CAUSAL_PATTERNS,
            message="Causal attribution violates the constitution. Show correlations only.",
            severity=ViolationSeverity.ERROR,
            exclude_files=["tests/test_hooks/*"],
        ),
        LintRule(
            id="INV-NO-GRADE-RECONSTRUCTION",
            name="Grade Ban",
            patterns=GRADE_PATTERNS,
            message="Discrete grades violate the constitution. Show continuous data.",
            severity=ViolationSeverity.ERROR,
            exclude_files=["tests/test_hooks/*"],
        ),
        LintRule(
            id="INV-NO-IMPLICIT-VERDICT",
            name="Verdict Ban",
            patterns=VERDICT_PATTERNS,
            message="Machine verdicts violate the constitution. Human interprets.",
            severity=ViolationSeverity.ERROR,
            exclude_files=["tests/test_hooks/*"],
        ),
    ]


# =============================================================================
# SCALAR BAN HOOK
# =============================================================================


class ScalarBanHook:
    """
    Pre-commit hook for scalar ban enforcement.

    Usage:
        hook = ScalarBanHook()
        violations = hook.check_file(Path("my_file.py"))
        if violations:
            hook.block_commit(violations)
    """

    def __init__(self, additional_rules: list[LintRule] | None = None):
        rules = get_constitutional_rules()
        if additional_rules:
            rules.extend(additional_rules)
        self.linter = PreCommitLinter(rules)

    def check_file(self, filepath: Path) -> list[Violation]:
        """Check single file for violations."""
        return self.linter.check_file(filepath)

    def check_staged(self) -> list[Violation]:
        """Check all staged files."""
        return self.linter.check_staged()

    def check_directory(self, directory: Path) -> list[Violation]:
        """Check entire directory."""
        return self.linter.check_directory(directory)

    def format_report(self, violations: list[Violation]) -> str:
        """Format violation report."""
        return self.linter.format_report(violations)

    def run(self) -> int:
        """
        Run hook and return exit code.

        Returns:
            0 if no violations, 1 if violations found
        """
        violations = self.check_staged()

        if not violations:
            print("✓ Constitutional check passed")
            return 0

        print(self.format_report(violations))

        errors = [v for v in violations if v.severity == ViolationSeverity.ERROR]
        if errors:
            print(f"\n❌ {len(errors)} constitutional violations block this commit")
            return 1

        return 0


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main() -> int:
    """CLI entry point for pre-commit hook."""
    hook = ScalarBanHook()
    return hook.run()


if __name__ == "__main__":
    import sys
    sys.exit(main())
