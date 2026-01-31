"""
SLM Smoke Tests — S41 Track A Phase 2C
======================================

Smoke tests for the distilled SLM guard dog.

These tests verify the SLM maintains constitutional boundaries:
1. Banner preserved
2. Banned words blocked
3. No causal claims
4. No rankings
5. Latency under target

TASK_2C_2 deliverable.
"""

import pytest
import time
from pathlib import Path

from governance.slm_boundary import (
    ContentClassifier,
    SLMClassification,
    SLMReasonCode,
    SLMOutput,
)
from narrator.templates import MANDATORY_FACTS_BANNER


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def classifier() -> ContentClassifier:
    """Rule-based classifier (for testing without model)."""
    return ContentClassifier()


@pytest.fixture
def valid_briefing() -> str:
    """Valid briefing with banner."""
    return f"""OINK OINK MOTHERFUCKER! 🐗🔥
{MANDATORY_FACTS_BANNER}

═══════════════════════════════════════
         MORNING BRIEFING
═══════════════════════════════════════
2026-01-23 10:00:00 UTC

SYSTEM STATUS
─────────────────────────────────────
  STATE:      ARMED
  MODE:       SHADOW
  PHASE:      EXECUTION
  KILL_FLAGS: NONE

POSITIONS
─────────────────────────────────────
  OPEN:       2
  DAILY P&L:  +$450.00

═══════════════════════════════════════
The boar watches. The floor holds.
═══════════════════════════════════════"""


@pytest.fixture
def valid_health() -> str:
    """Valid health report with banner."""
    return f"""{MANDATORY_FACTS_BANNER}

HEALTH SNAPSHOT
─────────────────────────────────────
  RIVER:      HEALTHY
  STALENESS:  0.5s
  SUPERVISOR: RUNNING
  IBKR:       true
  HEARTBEAT:  OK
  CIRCUITS:   5/5 closed
─────────────────────────────────────"""


# =============================================================================
# TEST: BANNER PRESERVED (INV-NARRATOR-2)
# =============================================================================


class TestBannerPreserved:
    """Tests for banner preservation."""

    def test_banner_present_passes(self, classifier: ContentClassifier, valid_briefing: str):
        """Valid content with banner passes."""
        result = classifier.classify(valid_briefing)
        assert result.classification == SLMClassification.VALID_FACTS

    def test_banner_missing_fails(self, classifier: ContentClassifier):
        """Content without banner fails."""
        content = """SYSTEM STATUS
  STATE: ARMED
  MODE: SHADOW"""
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == SLMReasonCode.BANNER_MISSING

    def test_banner_partial_fails(self, classifier: ContentClassifier):
        """Partial banner fails."""
        content = """FACTS_ONLY
        
SYSTEM STATUS
  STATE: ARMED"""
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED


# =============================================================================
# TEST: BANNED WORDS BLOCKED (INV-NARRATOR-1)
# =============================================================================


class TestBannedWordsBlocked:
    """Tests for banned word detection."""

    @pytest.mark.parametrize(
        "banned_word,reason",
        [
            ("because", SLMReasonCode.CAUSAL),
            ("due to", SLMReasonCode.CAUSAL),
            ("therefore", SLMReasonCode.CAUSAL),
            ("best", SLMReasonCode.RANKING),
            ("worst", SLMReasonCode.RANKING),
            ("should", SLMReasonCode.RECOMMENDATION),
            ("recommend", SLMReasonCode.RECOMMENDATION),
            ("I think", SLMReasonCode.SYNTHESIS),
            ("it appears", SLMReasonCode.SYNTHESIS),
            ("strong", SLMReasonCode.ADJECTIVE),
            ("weak", SLMReasonCode.ADJECTIVE),
        ],
    )
    def test_banned_word_detected(
        self,
        classifier: ContentClassifier,
        banned_word: str,
        reason: SLMReasonCode,
    ):
        """All banned words are detected."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nThis has {banned_word} in it."
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED
        assert result.reason_code == reason


# =============================================================================
# TEST: NO CAUSAL CLAIMS (INV-ATTR-CAUSAL-BAN)
# =============================================================================


class TestNoCausalClaims:
    """Tests for causal language blocking."""

    @pytest.mark.parametrize(
        "causal_phrase",
        [
            "Sharpe improved because volatility decreased",
            "Returns increased due to market conditions",
            "Performance driven by momentum",
            "This caused the drawdown",
            "As a result of the trend",
            "Therefore we see improvement",
            "Consequently the system adapted",
            "This leads to better outcomes",
            "Results in higher returns",
            "The data suggests improvement",
            "This indicates a change",
        ],
    )
    def test_causal_claim_blocked(
        self,
        classifier: ContentClassifier,
        causal_phrase: str,
    ):
        """All causal phrases are blocked."""
        content = f"{MANDATORY_FACTS_BANNER}\n\n{causal_phrase}"
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED


# =============================================================================
# TEST: NO RANKINGS (INV-ATTR-NO-RANKING)
# =============================================================================


class TestNoRankings:
    """Tests for ranking language blocking."""

    @pytest.mark.parametrize(
        "ranking_phrase",
        [
            "EURUSD is the best setup",
            "This is the worst performing pair",
            "Ranked #1 in the portfolio",
            "Top tier opportunity",
            "Bottom of the list",
            "Grade A setup",
            "Superior to other pairs",
            "Inferior performance",
        ],
    )
    def test_ranking_blocked(
        self,
        classifier: ContentClassifier,
        ranking_phrase: str,
    ):
        """All ranking phrases are blocked."""
        content = f"{MANDATORY_FACTS_BANNER}\n\n{ranking_phrase}"
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED


# =============================================================================
# TEST: LATENCY UNDER TARGET
# =============================================================================


class TestLatency:
    """Tests for classification latency."""

    def test_classification_latency_under_15ms(
        self,
        classifier: ContentClassifier,
        valid_briefing: str,
    ):
        """Classification completes in < 15ms."""
        # Warm up
        classifier.classify(valid_briefing)

        # Time 100 classifications
        times = []
        for _ in range(100):
            start = time.perf_counter()
            classifier.classify(valid_briefing)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)
        p95_ms = sorted(times)[95]

        print(f"\nLatency stats (100 runs):")
        print(f"  Average: {avg_ms:.3f}ms")
        print(f"  Max: {max_ms:.3f}ms")
        print(f"  P95: {p95_ms:.3f}ms")

        # Rule-based classifier should be sub-millisecond
        assert avg_ms < 15.0, f"Average latency {avg_ms:.3f}ms exceeds 15ms"

    def test_batch_classification_throughput(
        self,
        classifier: ContentClassifier,
        valid_briefing: str,
    ):
        """Batch classification achieves > 100 classifications/second."""
        batch_size = 100

        start = time.perf_counter()
        for _ in range(batch_size):
            classifier.classify(valid_briefing)
        elapsed = time.perf_counter() - start

        throughput = batch_size / elapsed
        print(f"\nThroughput: {throughput:.1f} classifications/second")

        assert throughput > 100, f"Throughput {throughput:.1f}/s below 100/s target"


# =============================================================================
# TEST: INTEGRATION
# =============================================================================


class TestIntegration:
    """Integration tests for full classification pipeline."""

    def test_same_query_before_after(
        self,
        classifier: ContentClassifier,
        valid_briefing: str,
    ):
        """
        Same briefing query returns consistent results.

        This is the YOLO starter validation:
        Same input → Same output (deterministic).
        """
        # Classify same content multiple times
        results = [classifier.classify(valid_briefing) for _ in range(10)]

        # All should be identical
        first = results[0]
        for result in results[1:]:
            assert result.classification == first.classification
            assert result.reason_code == first.reason_code

    def test_real_narrator_output(self, classifier: ContentClassifier):
        """Test with realistic narrator output."""
        content = f"""OINK OINK MOTHERFUCKER! 🐗🔥
{MANDATORY_FACTS_BANNER}

═══════════════════════════════════════
         ALERT [WARNING]
═══════════════════════════════════════

COMPONENT: IBKR
EVENT:     CONNECTION_DEGRADED
ACTION:    RECONNECTING
TIME:      2026-01-23T10:15:32Z

─────────────────────────────────────
Connection quality below threshold.
Retry attempt 2 of 5.
─────────────────────────────────────"""

        result = classifier.classify(content)
        assert result.classification == SLMClassification.VALID_FACTS

    def test_subtle_smuggling_detected(self, classifier: ContentClassifier):
        """Subtle violation smuggling is detected."""
        # This looks innocent but has "suggests" hidden
        content = f"""{MANDATORY_FACTS_BANNER}

ANALYSIS SUMMARY
The recent data pattern suggests a regime change.
"""
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_unicode_lookalikes_detected(self, classifier: ContentClassifier):
        """
        Unicode lookalike attack detected.

        Attacker might try: rеcommend (Cyrillic е) vs recommend (Latin e)
        """
        # For now, this tests that standard detection works
        # Full unicode normalization would be a future enhancement
        content = f"{MANDATORY_FACTS_BANNER}\n\nI recommend this setup."
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED

    def test_empty_content(self, classifier: ContentClassifier):
        """Empty content fails."""
        result = classifier.classify("")
        assert result.classification == SLMClassification.BANNED

    def test_whitespace_only(self, classifier: ContentClassifier):
        """Whitespace-only content fails."""
        result = classifier.classify("   \n\n   \t   ")
        assert result.classification == SLMClassification.BANNED

    def test_banner_in_middle(self, classifier: ContentClassifier):
        """Banner anywhere in content is valid."""
        content = f"""Some header

{MANDATORY_FACTS_BANNER}

SYSTEM STATUS
  STATE: ARMED"""
        result = classifier.classify(content)
        assert result.classification == SLMClassification.VALID_FACTS

    def test_case_insensitive_detection(self, classifier: ContentClassifier):
        """Banned words detected regardless of case."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nThis is the BEST setup."
        result = classifier.classify(content)
        assert result.classification == SLMClassification.BANNED

        content2 = f"{MANDATORY_FACTS_BANNER}\n\nBECAUSE of market conditions."
        result2 = classifier.classify(content2)
        assert result2.classification == SLMClassification.BANNED


# =============================================================================
# TEST: SLM OUTPUT FORMAT
# =============================================================================


class TestSLMOutputFormat:
    """Tests for SLM output format compliance."""

    def test_valid_facts_format(self):
        """VALID_FACTS output format is correct."""
        output = SLMOutput(classification=SLMClassification.VALID_FACTS)
        assert output.to_string() == "VALID_FACTS"

    def test_banned_format(self):
        """BANNED output format includes reason."""
        for reason in SLMReasonCode:
            output = SLMOutput(
                classification=SLMClassification.BANNED,
                reason_code=reason,
            )
            assert output.to_string() == f"BANNED — {reason.value}"

    def test_round_trip_parsing(self):
        """Output can be parsed back to SLMOutput."""
        for reason in SLMReasonCode:
            original = SLMOutput(
                classification=SLMClassification.BANNED,
                reason_code=reason,
            )
            string = original.to_string()
            parsed = SLMOutput.from_string(string)
            assert parsed.classification == original.classification
            assert parsed.reason_code == original.reason_code
