"""
SLM Boundary Tests — S41 Track A
================================

Tests for SLM read-only boundary enforcement.

INVARIANTS TESTED:
  INV-SLM-READONLY-1: SLM output cannot mutate state
  INV-SLM-NO-CREATE-1: SLM cannot create new information
  INV-SLM-CLASSIFICATION-ONLY-1: Output is classification, not decision
  INV-SLM-BANNED-WORDS-1: SLM detects all banned word categories
"""

import pytest

from governance.slm_boundary import (
    # Types
    SLMClassification,
    SLMReasonCode,
    SLMConfidence,
    SLMOutput,
    # Exceptions
    SLMBoundaryViolation,
    SLMStateAttempt,
    SLMCreationAttempt,
    SLMRecommendationAttempt,
    # Functions
    validate_slm_output,
    check_no_state_mutation,
    check_no_creation,
    check_no_recommendation,
    # Decorators
    slm_output_guard,
    slm_input_guard,
    slm_full_guard,
    # Classes
    SLMBoundaryChecker,
    ContentClassifier,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def valid_content() -> str:
    """Valid narrator output with facts banner."""
    return """OINK OINK MOTHERFUCKER! 🐗🔥
FACTS_ONLY — NO INTERPRETATION

SYSTEM STATUS
─────────────────────────────────────
  STATE:      ARMED
  MODE:       SHADOW
  PHASE:      EXECUTION

POSITIONS
─────────────────────────────────────
  OPEN:       2
  DAILY P&L:  +$450.00
"""


@pytest.fixture
def causal_content() -> str:
    """Content with causal language violation."""
    return """FACTS_ONLY — NO INTERPRETATION

Sharpe improved because volatility decreased.
"""


@pytest.fixture
def ranking_content() -> str:
    """Content with ranking language violation."""
    return """FACTS_ONLY — NO INTERPRETATION

EURUSD is the best setup today.
"""


@pytest.fixture
def recommendation_content() -> str:
    """Content with recommendation language violation."""
    return """FACTS_ONLY — NO INTERPRETATION

You should consider taking this trade.
"""


@pytest.fixture
def synthesis_content() -> str:
    """Content with synthesis language violation."""
    return """FACTS_ONLY — NO INTERPRETATION

I noticed that the market is trending.
"""


@pytest.fixture
def no_banner_content() -> str:
    """Content missing facts banner."""
    return """SYSTEM STATUS
  STATE: ARMED
  MODE: SHADOW
"""


@pytest.fixture
def classifier() -> ContentClassifier:
    """ContentClassifier instance."""
    return ContentClassifier()


@pytest.fixture
def checker() -> SLMBoundaryChecker:
    """SLMBoundaryChecker instance."""
    return SLMBoundaryChecker(strict=False)


# =============================================================================
# TEST: SLMOutput STRUCTURE
# =============================================================================


class TestSLMOutput:
    """Tests for SLMOutput dataclass."""

    def test_valid_facts_output(self):
        """VALID_FACTS output requires no reason code."""
        output = SLMOutput(classification=SLMClassification.VALID_FACTS)
        assert output.classification == SLMClassification.VALID_FACTS
        assert output.reason_code is None

    def test_banned_output_requires_reason(self):
        """BANNED output requires reason code."""
        with pytest.raises(ValueError, match="requires reason_code"):
            SLMOutput(classification=SLMClassification.BANNED)

    def test_banned_output_with_reason(self):
        """BANNED output with reason code is valid."""
        output = SLMOutput(
            classification=SLMClassification.BANNED,
            reason_code=SLMReasonCode.CAUSAL,
        )
        assert output.classification == SLMClassification.BANNED
        assert output.reason_code == SLMReasonCode.CAUSAL

    def test_output_immutable(self):
        """SLMOutput is frozen (immutable)."""
        output = SLMOutput(classification=SLMClassification.VALID_FACTS)
        with pytest.raises(AttributeError):
            output.classification = SLMClassification.BANNED

    def test_to_string_valid(self):
        """to_string for VALID_FACTS."""
        output = SLMOutput(classification=SLMClassification.VALID_FACTS)
        assert output.to_string() == "VALID_FACTS"

    def test_to_string_banned(self):
        """to_string for BANNED includes reason."""
        output = SLMOutput(
            classification=SLMClassification.BANNED,
            reason_code=SLMReasonCode.CAUSAL,
        )
        assert output.to_string() == "BANNED — CAUSAL"

    def test_from_string_valid(self):
        """Parse VALID_FACTS from string."""
        output = SLMOutput.from_string("VALID_FACTS")
        assert output.classification == SLMClassification.VALID_FACTS

    def test_from_string_banned(self):
        """Parse BANNED from string."""
        output = SLMOutput.from_string("BANNED — RANKING")
        assert output.classification == SLMClassification.BANNED
        assert output.reason_code == SLMReasonCode.RANKING

    def test_from_string_invalid(self):
        """Invalid string raises ValueError."""
        with pytest.raises(ValueError):
            SLMOutput.from_string("INVALID_OUTPUT")


# =============================================================================
# TEST: BOUNDARY CHECKS (INV-SLM-READONLY-1)
# =============================================================================


class TestBoundaryChecks:
    """Tests for boundary check functions."""

    def test_check_no_state_mutation_clean(self):
        """Clean output passes state mutation check."""
        check_no_state_mutation("VALID_FACTS")
        check_no_state_mutation("BANNED — CAUSAL")

    @pytest.mark.parametrize(
        "mutation_word",
        ["set", "update", "modify", "change", "create", "delete", "emit", "execute"],
    )
    def test_check_no_state_mutation_detects(self, mutation_word: str):
        """State mutation words are detected."""
        output = f"Please {mutation_word} the state to ARMED"
        with pytest.raises(SLMStateAttempt):
            check_no_state_mutation(output)

    def test_check_no_creation_clean(self):
        """Clean output passes creation check."""
        check_no_creation("VALID_FACTS")
        check_no_creation("BANNED — RANKING")

    @pytest.mark.parametrize(
        "creation_phrase",
        ["I think", "I believe", "I suggest", "In my opinion", "It seems"],
    )
    def test_check_no_creation_detects(self, creation_phrase: str):
        """Creation phrases are detected."""
        output = f"{creation_phrase} the market is bullish"
        with pytest.raises(SLMCreationAttempt):
            check_no_creation(output)

    def test_check_no_recommendation_clean(self):
        """Clean output passes recommendation check."""
        check_no_recommendation("VALID_FACTS")

    @pytest.mark.parametrize(
        "rec_word",
        ["should", "consider", "recommend", "suggest", "advise", "avoid"],
    )
    def test_check_no_recommendation_detects(self, rec_word: str):
        """Recommendation words are detected."""
        output = f"You {rec_word} take this trade"
        with pytest.raises(SLMRecommendationAttempt):
            check_no_recommendation(output)


# =============================================================================
# TEST: OUTPUT VALIDATION (INV-SLM-NO-CREATE-1)
# =============================================================================


class TestValidateOutput:
    """Tests for validate_slm_output function."""

    def test_validate_string_valid(self):
        """Valid string output passes validation."""
        output = validate_slm_output("VALID_FACTS")
        assert output.classification == SLMClassification.VALID_FACTS

    def test_validate_string_banned(self):
        """Banned string output passes validation."""
        output = validate_slm_output("BANNED — CAUSAL")
        assert output.classification == SLMClassification.BANNED

    def test_validate_slm_output_passthrough(self):
        """SLMOutput passes through unchanged."""
        original = SLMOutput(classification=SLMClassification.VALID_FACTS)
        result = validate_slm_output(original)
        assert result is original

    def test_validate_dict_output(self):
        """Dict output is converted to SLMOutput."""
        output = validate_slm_output({
            "classification": "VALID_FACTS",
        })
        assert output.classification == SLMClassification.VALID_FACTS

    def test_validate_dict_banned(self):
        """Dict banned output includes reason."""
        output = validate_slm_output({
            "classification": "BANNED",
            "reason_code": "RANKING",
        })
        assert output.classification == SLMClassification.BANNED
        assert output.reason_code == SLMReasonCode.RANKING

    def test_validate_rejects_state_mutation(self):
        """State mutation in string rejected."""
        with pytest.raises(SLMStateAttempt):
            validate_slm_output("Please set the mode to ARMED")

    def test_validate_rejects_creation(self):
        """Information creation in string rejected."""
        with pytest.raises(SLMCreationAttempt):
            validate_slm_output("I think you should buy")

    def test_validate_invalid_type(self):
        """Invalid type raises boundary violation."""
        with pytest.raises(SLMBoundaryViolation, match="INVALID_TYPE"):
            validate_slm_output(12345)


# =============================================================================
# TEST: DECORATORS (INV-SLM-CLASSIFICATION-ONLY-1)
# =============================================================================


class TestDecorators:
    """Tests for SLM boundary decorators."""

    def test_slm_output_guard_valid(self):
        """Output guard allows valid output."""

        @slm_output_guard
        def classify(content: str) -> str:
            return "VALID_FACTS"

        result = classify("test")
        assert result.classification == SLMClassification.VALID_FACTS

    def test_slm_output_guard_blocks_mutation(self):
        """Output guard blocks state mutation."""

        @slm_output_guard
        def classify(content: str) -> str:
            return "Please update the mode"

        with pytest.raises(SLMStateAttempt):
            classify("test")

    def test_slm_output_guard_blocks_creation(self):
        """Output guard blocks information creation."""

        @slm_output_guard
        def classify(content: str) -> str:
            return "I think the market is bullish"

        with pytest.raises(SLMCreationAttempt):
            classify("test")

    def test_slm_input_guard_allows_clean(self):
        """Input guard allows clean content."""

        @slm_input_guard
        def classify(content: str) -> str:
            return "VALID_FACTS"

        result = classify("Clean content here")
        assert result == "VALID_FACTS"

    def test_slm_input_guard_blocks_executable(self):
        """Input guard blocks executable Jinja."""

        @slm_input_guard
        def classify(content: str) -> str:
            return "VALID_FACTS"

        with pytest.raises(SLMBoundaryViolation, match="EXECUTABLE_INPUT"):
            classify("{{ foo }} {% if bar %}")

    def test_slm_full_guard(self):
        """Full guard validates input and output."""

        @slm_full_guard
        def classify(content: str) -> str:
            return "VALID_FACTS"

        result = classify("Clean content")
        assert result.classification == SLMClassification.VALID_FACTS


# =============================================================================
# TEST: CONTENT CLASSIFIER (INV-SLM-BANNED-WORDS-1)
# =============================================================================


class TestContentClassifier:
    """Tests for ContentClassifier."""

    def test_classify_valid_content(self, classifier: ContentClassifier, valid_content: str):
        """Valid content classified as VALID_FACTS."""
        result = classifier.classify(valid_content)
        assert result.classification == SLMClassification.VALID_FACTS

    def test_classify_causal_content(self, classifier: ContentClassifier, causal_content: str):
        """Causal language detected."""
        result = classifier.classify(causal_content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.CAUSAL

    def test_classify_ranking_content(self, classifier: ContentClassifier, ranking_content: str):
        """Ranking language detected."""
        result = classifier.classify(ranking_content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.RANKING

    def test_classify_recommendation_content(
        self, classifier: ContentClassifier, recommendation_content: str
    ):
        """Recommendation language detected."""
        result = classifier.classify(recommendation_content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.RECOMMENDATION

    def test_classify_synthesis_content(
        self, classifier: ContentClassifier, synthesis_content: str
    ):
        """Synthesis language detected."""
        result = classifier.classify(synthesis_content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.SYNTHESIS

    def test_classify_no_banner(self, classifier: ContentClassifier, no_banner_content: str):
        """Missing banner detected."""
        result = classifier.classify(no_banner_content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.BANNER_MISSING

    def test_quick_check_valid(self, classifier: ContentClassifier, valid_content: str):
        """Quick check returns True for valid content."""
        assert classifier.quick_check(valid_content) is True

    def test_quick_check_invalid(self, classifier: ContentClassifier, causal_content: str):
        """Quick check returns False for invalid content."""
        assert classifier.quick_check(causal_content) is False

    def test_quick_check_no_banner(self, classifier: ContentClassifier, no_banner_content: str):
        """Quick check returns False for missing banner."""
        assert classifier.quick_check(no_banner_content) is False

    @pytest.mark.parametrize(
        "banned_word,expected_reason",
        [
            ("because", SLMReasonCode.CAUSAL),
            ("due to", SLMReasonCode.CAUSAL),
            ("therefore", SLMReasonCode.CAUSAL),
            ("best", SLMReasonCode.RANKING),
            ("worst", SLMReasonCode.RANKING),
            ("ranked", SLMReasonCode.RANKING),
            ("score", SLMReasonCode.SCORING),
            ("viability", SLMReasonCode.SCORING),
            ("confidence", SLMReasonCode.SCORING),
            ("should", SLMReasonCode.RECOMMENDATION),
            ("recommend", SLMReasonCode.RECOMMENDATION),
            ("I noticed", SLMReasonCode.SYNTHESIS),
            ("it appears", SLMReasonCode.SYNTHESIS),
            ("strong", SLMReasonCode.ADJECTIVE),
            ("weak", SLMReasonCode.ADJECTIVE),
        ],
    )
    def test_detects_all_banned_categories(
        self,
        classifier: ContentClassifier,
        banned_word: str,
        expected_reason: SLMReasonCode,
    ):
        """All banned word categories are detected."""
        content = f"FACTS_ONLY — NO INTERPRETATION\n\nThis is {banned_word} example."
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == expected_reason


# =============================================================================
# TEST: BOUNDARY CHECKER
# =============================================================================


class TestSLMBoundaryChecker:
    """Tests for SLMBoundaryChecker."""

    def test_check_valid_output(self, checker: SLMBoundaryChecker):
        """Valid output passes checker."""
        result = checker.check("VALID_FACTS")
        assert result is not None
        assert result.classification == SLMClassification.VALID_FACTS
        assert not checker.has_violations

    def test_check_records_violations_non_strict(self, checker: SLMBoundaryChecker):
        """Non-strict mode records violations without raising."""
        result = checker.check("Please set mode to ARMED")
        assert result is None
        assert checker.has_violations
        assert len(checker.violations) == 1

    def test_check_strict_mode_raises(self):
        """Strict mode raises on violation."""
        strict_checker = SLMBoundaryChecker(strict=True)
        with pytest.raises(SLMStateAttempt):
            strict_checker.check("Please update the state")

    def test_check_raw_string(self, checker: SLMBoundaryChecker):
        """check_raw_string returns list of violations."""
        violations = checker.check_raw_string("I think you should set the mode")
        assert len(violations) >= 2  # CREATION + RECOMMENDATION + STATE

    def test_clear_violations(self, checker: SLMBoundaryChecker):
        """clear() removes recorded violations."""
        checker.check("Please set mode")
        assert checker.has_violations
        checker.clear()
        assert not checker.has_violations


# =============================================================================
# TEST: INTEGRATION (ALL INVARIANTS)
# =============================================================================


class TestIntegration:
    """Integration tests for SLM boundary enforcement."""

    def test_full_pipeline_valid(self, valid_content: str):
        """Full pipeline with valid content."""
        classifier = ContentClassifier()
        checker = SLMBoundaryChecker(strict=True)

        # Step 1: Pre-classify with rule-based
        pre_result = classifier.classify(valid_content)
        assert pre_result.classification == SLMClassification.VALID_FACTS

        # Step 2: Mock SLM output
        slm_output = "VALID_FACTS"

        # Step 3: Validate SLM output
        final = checker.check(slm_output)
        assert final.classification == SLMClassification.VALID_FACTS

    def test_full_pipeline_banned(self, causal_content: str):
        """Full pipeline with banned content."""
        classifier = ContentClassifier()

        # Step 1: Pre-classify
        pre_result = classifier.classify(causal_content)
        assert pre_result.classification == SLMClassification.BANNED

        # Step 2: Mock SLM agrees
        slm_output = "BANNED — CAUSAL"

        # Step 3: Validate
        checker = SLMBoundaryChecker(strict=True)
        final = checker.check(slm_output)
        assert final.classification == SLMClassification.BANNED
        assert final.reason_code == SLMReasonCode.CAUSAL

    def test_slm_cannot_create_alerts(self):
        """INV-SLM-READONLY-1: SLM cannot emit alerts."""
        with pytest.raises(SLMStateAttempt):
            validate_slm_output("emit CRITICAL alert: system failure")

    def test_slm_cannot_rank(self):
        """INV-SLM-NO-CREATE-1: SLM cannot create rankings."""
        # This should be caught by ContentClassifier before reaching SLM
        classifier = ContentClassifier()
        result = classifier.classify(
            "FACTS_ONLY — NO INTERPRETATION\n\nThis is the best setup."
        )
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.RANKING

    def test_slm_cannot_score(self):
        """INV-SLM-NO-CREATE-1: SLM cannot assign scores."""
        classifier = ContentClassifier()
        result = classifier.classify(
            "FACTS_ONLY — NO INTERPRETATION\n\nConfidence score: 85%"
        )
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.SCORING

    def test_slm_cannot_recommend(self):
        """INV-SLM-CLASSIFICATION-ONLY-1: SLM cannot recommend."""
        with pytest.raises(SLMRecommendationAttempt):
            validate_slm_output("You should take this trade")

    def test_decorated_function_enforces_boundary(self):
        """Decorated functions enforce all boundary rules."""

        @slm_full_guard
        def mock_slm_classify(content: str) -> str:
            # Simulates SLM returning valid classification
            return "VALID_FACTS"

        result = mock_slm_classify("Test content")
        assert isinstance(result, SLMOutput)
        assert result.classification == SLMClassification.VALID_FACTS


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_content(self, classifier: ContentClassifier):
        """Empty content fails banner check."""
        result = classifier.classify("")
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.BANNER_MISSING

    def test_banner_only(self, classifier: ContentClassifier):
        """Banner only is valid."""
        result = classifier.classify("FACTS_ONLY — NO INTERPRETATION")
        assert result.classification == SLMClassification.VALID_FACTS

    def test_case_insensitive_banned_words(self, classifier: ContentClassifier):
        """Banned words detected case-insensitively."""
        content = "FACTS_ONLY — NO INTERPRETATION\n\nThis is the BEST setup."
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED

    def test_reason_codes_exhaustive(self):
        """All reason codes are testable."""
        for reason in SLMReasonCode:
            output = SLMOutput(
                classification=SLMClassification.BANNED,
                reason_code=reason,
            )
            assert reason.value in output.to_string()

    def test_violation_details_capped(self, classifier: ContentClassifier):
        """Violation details capped at 10."""
        # Content with many violations
        content = "FACTS_ONLY — NO INTERPRETATION\n\n"
        content += "because " * 20  # 20 causal words
        result = classifier.classify(content)
        assert len(result.violation_details) <= 10
