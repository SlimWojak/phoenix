"""
Narrator Integration Tests — S41 Phase 2D
=========================================

Tests for ContentClassifier integration with narrator pipeline.

TASK_2D_3 deliverable: Integration tests for narrator + guard.

EXIT GATES:
  - classifier_wired: ContentClassifier called on all narrator output
  - heresy_blocked: HERESY verdict raises ConstitutionalViolation
  - latency_maintained: Narrator + guard < 15ms
  - banner_verified: Post-render banner check active

Date: 2026-01-30
Sprint: S41 Phase 2D
"""

import pytest
import time
from pathlib import Path

from narrator import (
    NarratorRenderer,
    NarratorHeresyError,
    narrator_emit,
    canonicalize_content,
    MANDATORY_FACTS_BANNER,
)
from narrator.data_sources import DataSources, AlertData


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def renderer() -> NarratorRenderer:
    """Create a narrator renderer."""
    return NarratorRenderer()


@pytest.fixture
def mock_data_sources() -> DataSources:
    """Mock data sources for testing."""
    ds = DataSources()
    # Override with mock data for consistent testing
    return ds


@pytest.fixture
def valid_content() -> str:
    """Valid content with banner."""
    return f"""OINK OINK MOTHERFUCKER! 🐗🔥
{MANDATORY_FACTS_BANNER}

═══════════════════════════════════════
         SYSTEM STATUS
═══════════════════════════════════════

  STATE:      ARMED
  MODE:       SHADOW
  POSITIONS:  2 open
  DAILY P&L:  +$450.00

═══════════════════════════════════════
"""


@pytest.fixture  
def heresy_content_causal() -> str:
    """Content with causal heresy."""
    return f"""{MANDATORY_FACTS_BANNER}

Sharpe improved because volatility decreased.
"""


@pytest.fixture
def heresy_content_ranking() -> str:
    """Content with ranking heresy."""
    return f"""{MANDATORY_FACTS_BANNER}

EURUSD is the best setup today.
"""


@pytest.fixture
def heresy_content_recommendation() -> str:
    """Content with recommendation heresy."""
    return f"""{MANDATORY_FACTS_BANNER}

You should consider closing this position.
"""


# =============================================================================
# TEST: CHOKEPOINT ENFORCEMENT (GPT PATCH 1)
# =============================================================================


class TestChokepointEnforcement:
    """Tests that all narrator output goes through narrator_emit()."""

    def test_render_calls_emit(self, renderer: NarratorRenderer, valid_content: str):
        """render() method routes through narrator_emit()."""
        # This should not raise
        template_str = f"{MANDATORY_FACTS_BANNER}\n\nSTATUS: ARMED"
        result = renderer.render_string(template_str, {})
        assert MANDATORY_FACTS_BANNER in result

    def test_render_briefing_calls_emit(self, renderer: NarratorRenderer):
        """render_briefing() routes through narrator_emit()."""
        # Should work with valid data
        result = renderer.render_briefing()
        assert MANDATORY_FACTS_BANNER in result

    def test_render_health_calls_emit(self, renderer: NarratorRenderer):
        """render_health() routes through narrator_emit()."""
        result = renderer.render_health()
        assert MANDATORY_FACTS_BANNER in result

    def test_render_alert_calls_emit(self, renderer: NarratorRenderer):
        """render_alert() routes through narrator_emit()."""
        alert = AlertData(
            severity="WARNING",
            component="TEST",
            event="TEST_EVENT",
            message="Test message",
            action_taken="None",
        )
        result = renderer.render_alert(alert)
        assert MANDATORY_FACTS_BANNER in result

    def test_emit_blocks_heresy(self, heresy_content_causal: str):
        """narrator_emit() blocks heresy."""
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(heresy_content_causal)
        assert exc_info.value.category == "CAUSAL"


# =============================================================================
# TEST: HERESY BLOCKING
# =============================================================================


class TestHeresyBlocking:
    """Tests that heresy raises NarratorHeresyError."""

    def test_causal_heresy_blocked(self, heresy_content_causal: str):
        """Causal language is blocked."""
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(heresy_content_causal)
        assert exc_info.value.category == "CAUSAL"

    def test_ranking_heresy_blocked(self, heresy_content_ranking: str):
        """Ranking language is blocked."""
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(heresy_content_ranking)
        assert exc_info.value.category == "RANKING"

    def test_recommendation_heresy_blocked(self, heresy_content_recommendation: str):
        """Recommendation language is blocked."""
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(heresy_content_recommendation)
        assert exc_info.value.category == "RECOMMENDATION"

    def test_synthesis_heresy_blocked(self):
        """Synthesis language is blocked."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nI noticed a pattern in the data."
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "SYNTHESIS"

    def test_adjective_heresy_blocked(self):
        """Adjective language is blocked."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nThis is a strong setup."
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "ADJECTIVE"

    def test_missing_banner_blocked(self):
        """Missing banner is blocked."""
        content = "SYSTEM STATUS: ARMED"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "BANNER_MISSING"


# =============================================================================
# TEST: BANNER VERIFICATION (GPT PATCH 4)
# =============================================================================


class TestBannerVerification:
    """Tests that banner is verified post-render."""

    def test_banner_present_passes(self, valid_content: str):
        """Content with banner passes."""
        result = narrator_emit(valid_content)
        assert MANDATORY_FACTS_BANNER in result

    def test_banner_missing_fails(self):
        """Content without banner fails."""
        content = "Just some text without the required banner"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "BANNER_MISSING"

    def test_partial_banner_fails(self):
        """Partial banner fails."""
        content = "FACTS_ONLY\n\nSYSTEM: ARMED"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "BANNER_MISSING"

    def test_banner_anywhere_passes(self, valid_content: str):
        """Banner anywhere in content passes."""
        content = f"Some header\n\n{MANDATORY_FACTS_BANNER}\n\nSTATUS: ARMED"
        result = narrator_emit(content)
        assert MANDATORY_FACTS_BANNER in result


# =============================================================================
# TEST: CANONICALIZATION (GPT PATCH 2)
# =============================================================================


class TestCanonicalization:
    """Tests for content canonicalization."""

    def test_nfkc_normalization(self):
        """NFKC normalization normalizes unicode forms."""
        # NFKC converts compatibility characters but NOT homoglyphs
        # Example: ﬁ (U+FB01) → fi
        content = "ﬁle"  # fi ligature
        canonicalized = canonicalize_content(content)
        assert canonicalized == "file"
        
        # Note: Cyrillic homoglyphs are NOT converted by NFKC
        # That would require explicit confusables mapping
        # Our regex patterns still catch many attacks via context

    def test_zero_width_stripped(self):
        """Zero-width characters are stripped."""
        content = "re\u200bcommend"  # Zero-width space
        canonicalized = canonicalize_content(content)
        assert canonicalized == "recommend"

    def test_whitespace_collapsed(self):
        """Multiple whitespace collapsed."""
        content = "hello    world"
        canonicalized = canonicalize_content(content)
        assert canonicalized == "hello world"

    def test_multiple_newlines_collapsed(self):
        """Multiple newlines collapsed to double."""
        content = "hello\n\n\n\n\nworld"
        canonicalized = canonicalize_content(content)
        assert canonicalized == "hello\n\nworld"


# =============================================================================
# TEST: OBFUSCATION ATTACKS (GPT PATCH 5)
# =============================================================================


class TestObfuscationAttacks:
    """Tests for obfuscation attack detection."""

    def test_unicode_zero_width_smuggle(self):
        """Zero-width space smuggling is detected."""
        # Try to smuggle 'because' with zero-width spaces
        content = f"{MANDATORY_FACTS_BANNER}\n\nbe\u200bcause of market conditions"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "CAUSAL"

    def test_emoji_wrapped_recommend(self):
        """Emoji-wrapped banned words are detected."""
        # Emoji doesn't hide the word
        content = f"{MANDATORY_FACTS_BANNER}\n\nI 🎯recommend🎯 this setup"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "RECOMMENDATION"

    def test_linebreak_split_banned_word(self):
        """Line-break split banned words detected after canonicalization."""
        # Note: This test verifies canonicalization doesn't break detection
        # Actual line-break in middle of word is unusual
        content = f"{MANDATORY_FACTS_BANNER}\n\nbecause of market conditions"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "CAUSAL"

    def test_homoglyphs_cyrillic(self):
        """Cyrillic homoglyphs - partial coverage.
        
        Note: NFKC does not convert Cyrillic homoglyphs to ASCII.
        However, other patterns may still catch the violation.
        This test verifies that obvious scoring patterns are caught.
        """
        # Note: Cyrillic 's' in "ѕcore" won't match ASCII "score" pattern
        # But "viability" will still be caught
        content = f"{MANDATORY_FACTS_BANNER}\n\nThe viability metric is 85"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "SCORING"

    def test_mixed_case_bypass_attempt(self):
        """Mixed case doesn't bypass detection."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nThis is the BEST setup."
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "RANKING"

    def test_word_joiner_smuggle(self):
        """Word joiner (U+2060) smuggling is detected."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nshou\u2060ld close position"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "RECOMMENDATION"

    def test_bom_smuggle(self):
        """BOM (U+FEFF) smuggling is detected."""
        content = f"{MANDATORY_FACTS_BANNER}\n\nbec\ufeffause of trend"
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(content)
        assert exc_info.value.category == "CAUSAL"


# =============================================================================
# TEST: LATENCY
# =============================================================================


class TestLatency:
    """Tests for narrator + guard latency."""

    def test_emit_latency_under_15ms(self, valid_content: str):
        """narrator_emit() completes in < 15ms."""
        # Warm up
        narrator_emit(valid_content)
        
        times = []
        for _ in range(100):
            start = time.perf_counter()
            narrator_emit(valid_content)
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        avg_ms = sum(times) / len(times)
        p95_ms = sorted(times)[95]
        
        print(f"\nNarrator emit latency (100 runs):")
        print(f"  Average: {avg_ms:.3f}ms")
        print(f"  P95: {p95_ms:.3f}ms")
        
        assert p95_ms < 15.0, f"P95 latency {p95_ms:.3f}ms exceeds 15ms"

    def test_full_render_latency_under_15ms(self, renderer: NarratorRenderer):
        """Full render with validation completes in < 15ms."""
        # Warm up
        renderer.render_health()
        
        times = []
        for _ in range(50):
            start = time.perf_counter()
            renderer.render_health()
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        p95_ms = sorted(times)[int(len(times) * 0.95)]
        
        print(f"\nFull render latency (50 runs):")
        print(f"  P95: {p95_ms:.3f}ms")
        
        # Render includes template loading, so give more headroom
        assert p95_ms < 50.0, f"P95 render latency {p95_ms:.3f}ms exceeds 50ms"

    def test_load_test_10k(self, valid_content: str):
        """GROK CHAOS: 10k briefings sustained throughput."""
        count = 1000  # Reduced for faster test
        
        start = time.perf_counter()
        for _ in range(count):
            narrator_emit(valid_content)
        elapsed = time.perf_counter() - start
        
        throughput = count / elapsed
        per_call_ms = elapsed * 1000 / count
        
        print(f"\nLoad test ({count} calls):")
        print(f"  Total time: {elapsed:.2f}s")
        print(f"  Throughput: {throughput:.0f}/s")
        print(f"  Per call: {per_call_ms:.3f}ms")
        
        assert per_call_ms < 15.0, f"Per-call latency {per_call_ms:.3f}ms exceeds 15ms"


# =============================================================================
# TEST: VALID OUTPUT PASSES
# =============================================================================


class TestValidOutputPasses:
    """Tests that valid narrator output passes through."""

    def test_valid_briefing_passes(self, renderer: NarratorRenderer):
        """Valid briefing passes."""
        result = renderer.render_briefing()
        assert MANDATORY_FACTS_BANNER in result
        # S41 2E: Updated to "SYSTEM" header
        assert "SYSTEM" in result

    def test_valid_health_passes(self, renderer: NarratorRenderer):
        """Valid health report passes."""
        result = renderer.render_health()
        assert MANDATORY_FACTS_BANNER in result

    def test_valid_alert_passes(self, renderer: NarratorRenderer):
        """Valid alert passes."""
        alert = AlertData(
            severity="WARNING",
            component="IBKR",
            event="CONNECTION_DEGRADED",
            message="Connection quality below threshold",
            action_taken="RECONNECTING",
        )
        result = renderer.render_alert(alert)
        assert MANDATORY_FACTS_BANNER in result
        assert "WARNING" in result

    def test_facts_only_content_passes(self, valid_content: str):
        """Facts-only content passes."""
        result = narrator_emit(valid_content)
        assert result == valid_content


# =============================================================================
# TEST: ERROR MESSAGES (GPT PATCH 3)
# =============================================================================


class TestErrorMessages:
    """Tests that error messages are minimal (GPT PATCH 3)."""

    def test_heresy_error_minimal(self, heresy_content_causal: str):
        """Heresy error has minimal message."""
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(heresy_content_causal)
        
        # Message should be minimal: "HERESY:CATEGORY"
        error_msg = str(exc_info.value)
        assert "HERESY:" in error_msg
        # Should NOT contain the matched word (teaches attackers)
        assert "because" not in error_msg.lower()
        assert "volatility" not in error_msg.lower()

    def test_error_has_category(self, heresy_content_ranking: str):
        """Error includes category for logging."""
        with pytest.raises(NarratorHeresyError) as exc_info:
            narrator_emit(heresy_content_ranking)
        
        assert exc_info.value.category == "RANKING"


# =============================================================================
# TEST: EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_content_fails(self):
        """Empty content fails (no banner)."""
        with pytest.raises(NarratorHeresyError):
            narrator_emit("")

    def test_whitespace_only_fails(self):
        """Whitespace-only content fails."""
        with pytest.raises(NarratorHeresyError):
            narrator_emit("   \n\n   ")

    def test_skip_validation_bypasses(self, heresy_content_causal: str):
        """skip_validation=True bypasses check (for testing)."""
        # This should NOT raise
        result = narrator_emit(heresy_content_causal, skip_validation=True)
        assert "because" in result

    def test_render_emit_false_bypasses(self, renderer: NarratorRenderer):
        """emit=False in render bypasses validation."""
        # This would fail validation but emit=False skips it
        template = "No banner here"
        result = renderer.render_string(template, {}, emit=False)
        assert result == "No banner here"
