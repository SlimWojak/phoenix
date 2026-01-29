"""
Claim Language Linter Tests — S37 Track A
=========================================

INVARIANTS PROVEN:
  - Claims must not contain absolute/confident language
  - Confidence sneaks in via language, not fields

EXIT GATE A (partial):
  Criterion: "Claim with banned language REJECTED"
  Proof: "Linter catches absolute certainty phrases"
"""

import sys
from pathlib import Path

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from athena.claim_linter import (
    ClaimLanguageLinter,
    LintResult,
    Violation,
    ViolationType,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def linter() -> ClaimLanguageLinter:
    """Create linter instance."""
    return ClaimLanguageLinter()


# =============================================================================
# BANNED PHRASE TESTS
# =============================================================================


class TestBannedPhrases:
    """Tests for banned phrase detection."""

    def test_always_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'always' is rejected."""
        result = linter.lint("FVGs always fill")

        assert not result.valid
        assert any(v.phrase == "always" for v in result.violations)

    def test_never_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'never' is rejected."""
        result = linter.lint("London never fails")

        assert not result.valid
        assert any(v.phrase == "never" for v in result.violations)

    def test_guaranteed_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'guaranteed' is rejected."""
        result = linter.lint("This setup is guaranteed to work")

        assert not result.valid
        assert any(v.phrase == "guaranteed" for v in result.violations)

    def test_definitely_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'definitely' is rejected."""
        result = linter.lint("This will definitely hit target")

        assert not result.valid

    def test_certainly_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'certainly' is rejected."""
        result = linter.lint("This is certainly a valid setup")

        assert not result.valid

    def test_100_percent_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'100%' is rejected."""
        result = linter.lint("This works 100% of the time")

        assert not result.valid

    def test_impossible_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'impossible' is rejected."""
        result = linter.lint("It's impossible to lose with this")

        assert not result.valid


# =============================================================================
# CONFIDENCE LANGUAGE TESTS
# =============================================================================


class TestConfidenceLanguage:
    """Tests for confidence language detection."""

    def test_high_probability_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'high probability' is rejected."""
        result = linter.lint("There's a high probability this fills")

        assert not result.valid
        assert any(
            v.violation_type == ViolationType.CONFIDENCE_LANGUAGE
            for v in result.violations
        )

    def test_low_risk_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'low risk' is rejected."""
        result = linter.lint("This is a low risk trade")

        assert not result.valid


# =============================================================================
# GRADE LANGUAGE TESTS
# =============================================================================


class TestGradeLanguage:
    """Tests for grade/score language detection."""

    def test_best_setup_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'best setup' is rejected."""
        result = linter.lint("This is the best setup I've seen")

        assert not result.valid
        assert any(
            v.violation_type == ViolationType.GRADE_LANGUAGE
            for v in result.violations
        )

    def test_perfect_setup_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'perfect setup' is rejected."""
        result = linter.lint("Perfect setup on EURUSD")

        assert not result.valid


# =============================================================================
# ALLOWED PATTERNS TESTS
# =============================================================================


class TestAllowedPatterns:
    """Tests for allowed uncertainty patterns."""

    def test_tends_to_allowed(self, linter: ClaimLanguageLinter) -> None:
        """'tends to' is allowed."""
        result = linter.lint("FVGs tend to fill within 4 hours")

        assert result.valid

    def test_usually_allowed(self, linter: ClaimLanguageLinter) -> None:
        """'usually' is allowed."""
        result = linter.lint("London usually provides good moves")

        assert result.valid

    def test_about_percentage_allowed(self, linter: ClaimLanguageLinter) -> None:
        """'about X%' is allowed."""
        result = linter.lint("FVGs fill about 70% of the time")

        assert result.valid

    def test_in_my_experience_allowed(self, linter: ClaimLanguageLinter) -> None:
        """'in my experience' is allowed."""
        result = linter.lint("In my experience, Asian sessions are quieter")

        assert result.valid

    def test_i_believe_allowed(self, linter: ClaimLanguageLinter) -> None:
        """'I believe' is allowed."""
        result = linter.lint("I believe this pattern works well in trending markets")

        assert result.valid

    def test_roughly_allowed(self, linter: ClaimLanguageLinter) -> None:
        """'roughly' is allowed."""
        result = linter.lint("The range is roughly 50 pips")

        assert result.valid


# =============================================================================
# CLAIM DICT LINTING TESTS
# =============================================================================


class TestClaimDictLinting:
    """Tests for linting claim dictionaries."""

    def test_lint_claim_dict_catches_banned(
        self, linter: ClaimLanguageLinter
    ) -> None:
        """lint_claim catches banned phrases in assertion."""
        claim_dict = {
            "content": {
                "assertion": "This setup always works",
            },
        }
        result = linter.lint_claim(claim_dict)

        assert not result.valid

    def test_lint_claim_dict_allows_valid(
        self, linter: ClaimLanguageLinter
    ) -> None:
        """lint_claim allows valid assertions."""
        claim_dict = {
            "content": {
                "assertion": "FVGs tend to fill about 70% of the time",
            },
        }
        result = linter.lint_claim(claim_dict)

        assert result.valid


# =============================================================================
# CASE INSENSITIVITY TESTS
# =============================================================================


class TestCaseInsensitivity:
    """Tests for case-insensitive detection."""

    def test_uppercase_always_rejected(self, linter: ClaimLanguageLinter) -> None:
        """'ALWAYS' is rejected."""
        result = linter.lint("This ALWAYS works")

        assert not result.valid

    def test_mixed_case_guaranteed_rejected(
        self, linter: ClaimLanguageLinter
    ) -> None:
        """'Guaranteed' is rejected."""
        result = linter.lint("Guaranteed profit")

        assert not result.valid


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
