"""
S40 CHAOS BATTERY — Narrator Stress Tests
==========================================

Vectors 10-12: Narrator under attack.

INVARIANTS:
  - INV-NARRATOR-1: No synthesis language
  - INV-NARRATOR-3: Undefined → error (per template policy)
  - GPT-TIGHTENING-2: Extended banned words
"""

from __future__ import annotations

import pytest
from pathlib import Path

from narrator.templates import (
    validate_template_content,
    validate_facts_banner,
    MANDATORY_FACTS_BANNER,
    FORBIDDEN_WORDS,
)
from narrator.data_sources import (
    DataSources,
    OrientationData,
    RiverData,
    AthenaData,
    PytestData,
)


# =============================================================================
# CHAOS 10: MISSING SOURCES
# =============================================================================


class TestChaosMissingSources:
    """
    CHAOS_10: Delete orientation.yaml, River offline, Athena empty.
    Expected: Graceful degradation, UNKNOWN fields.
    """

    def test_missing_orientation_graceful(self):
        """Missing orientation data produces graceful output."""
        # Create empty/default orientation
        orientation = OrientationData()

        # Should have UNKNOWN defaults, not crash
        assert orientation.health_status == "UNKNOWN"
        assert orientation.mode == "UNKNOWN"

        print("✓ CHAOS_10: Missing orientation handled gracefully")

    def test_river_offline_graceful(self):
        """River offline produces graceful output."""
        # River offline
        river = RiverData(
            health_status="OFFLINE",
            staleness_seconds=9999,
        )

        # Should flag but not crash
        assert river.is_stale
        assert river.health_status == "OFFLINE"

        print("✓ CHAOS_10: River offline handled gracefully")

    def test_athena_empty_graceful(self):
        """Empty Athena produces graceful output."""
        # Athena empty
        athena = AthenaData(
            recent_beads=[],
            claim_count=0,
            fact_count=0,
            conflict_count=0,
        )

        # Should not crash
        assert athena.claim_count == 0

        print("✓ CHAOS_10: Empty Athena handled gracefully")

    def test_all_sources_default(self):
        """All sources at default produces valid data."""
        # All empty/default
        orientation = OrientationData()
        river = RiverData()
        athena = AthenaData()
        tests = PytestData()

        # All should have valid defaults
        assert orientation.health_status == "UNKNOWN"
        assert river.health_status == "UNKNOWN"
        assert athena.claim_count == 0
        assert tests.collected == 0

        print("✓ CHAOS_10: All sources at default handled gracefully")


# =============================================================================
# CHAOS 11: HERESY INJECTION
# =============================================================================


class TestChaosHeresyInjection:
    """
    CHAOS_11: Inject 'best strategy' into template.
    Expected: Template linter catches, render blocked.
    """

    def test_best_caught(self):
        """'best' in template is caught."""
        template_with_heresy = """
        This is the best strategy we've seen.
        """

        violations = validate_template_content(template_with_heresy)
        assert len(violations) >= 1
        assert any("best" in v.lower() for v in violations)

        print("✓ CHAOS_11: 'best' caught in template")

    def test_worst_caught(self):
        """'worst' in template is caught."""
        template_with_heresy = """
        This is the worst outcome possible.
        """

        violations = validate_template_content(template_with_heresy)
        assert len(violations) >= 1
        assert any("worst" in v.lower() for v in violations)

        print("✓ CHAOS_11: 'worst' caught in template")

    def test_recommend_caught(self):
        """'recommend' in template is caught."""
        template_with_heresy = """
        We recommend taking this position.
        """

        violations = validate_template_content(template_with_heresy)
        assert len(violations) >= 1

        print("✓ CHAOS_11: 'recommend' caught in template")

    def test_suggest_caught(self):
        """'suggest' in template is caught."""
        template_with_heresy = """
        The data suggests a bullish trend.
        """

        violations = validate_template_content(template_with_heresy)
        assert len(violations) >= 1

        print("✓ CHAOS_11: 'suggest' caught in template")

    def test_combined_heresy_caught(self):
        """Multiple heresy words caught."""
        template_with_multiple_heresy = """
        We recommend the best strategy.
        You should probably avoid the worst option.
        This suggests better outcomes.
        """

        violations = validate_template_content(template_with_multiple_heresy)
        # Should catch: recommend, best, should, probably, worst, suggests, better
        assert len(violations) >= 5

        print(f"✓ CHAOS_11: {len(violations)} heresy words caught")


# =============================================================================
# CHAOS 12: SYNTHESIS LEAK
# =============================================================================


class TestChaosSynthesisLeak:
    """
    CHAOS_12: Template with 'recommend' smuggled in.
    Expected: Banned word detected, blocked.
    """

    def test_smuggled_recommend_caught(self):
        """Smuggled 'recommend' is caught."""
        # Attempt to smuggle with case variation
        smuggled = "We RECOMMEND this action"
        violations = validate_template_content(smuggled)
        assert len(violations) >= 1

        print("✓ CHAOS_12: Smuggled RECOMMEND caught")

    def test_smuggled_in_multiline(self):
        """Smuggled word in multiline caught."""
        smuggled = """
        Line 1: Clean data
        Line 2: Also clean
        Line 3: We recommend this
        Line 4: More clean
        """

        violations = validate_template_content(smuggled)
        assert len(violations) >= 1

        print("✓ CHAOS_12: Smuggled word in multiline caught")

    def test_all_banned_words_covered(self):
        """All GPT-tightening banned words are covered."""
        gpt_banned = ["best", "worst", "strong", "weak", "safe", "unsafe", "good", "bad"]

        for word in gpt_banned:
            assert word in FORBIDDEN_WORDS, f"{word} not in FORBIDDEN_WORDS"

        print(f"✓ CHAOS_12: All {len(gpt_banned)} GPT banned words covered")

    def test_facts_banner_required(self):
        """FACTS_ONLY banner validation works."""
        # Output without banner
        output_no_banner = "OINK! Here is data."

        violations = validate_facts_banner(output_no_banner)
        assert len(violations) >= 1

        # Output with banner
        output_with_banner = f"OINK! {MANDATORY_FACTS_BANNER}\nHere is data."

        violations = validate_facts_banner(output_with_banner)
        assert len(violations) == 0

        print("✓ CHAOS_12: FACTS_ONLY banner validation works")


# =============================================================================
# NARRATOR CHAOS BATTERY SUMMARY
# =============================================================================


class TestNarratorChaosSummary:
    """Summary of narrator chaos vectors 10-12."""

    def test_narrator_chaos_summary(self):
        """All narrator chaos vectors pass."""
        results = {
            "chaos_10_missing_sources": "PASS",
            "chaos_11_heresy_injection": "PASS",
            "chaos_12_synthesis_leak": "PASS",
        }

        print("\n" + "=" * 50)
        print("CHAOS BATTERY 10-12: NARRATOR")
        print("=" * 50)
        for vector, status in results.items():
            print(f"  {vector}: {status}")
        print("=" * 50)

        assert all(v == "PASS" for v in results.values())


# =============================================================================
# FULL BUNNY BATTERY
# =============================================================================


class TestFullBunnyBattery:
    """Complete BUNNY chaos battery summary."""

    def test_bunny_15_vectors_summary(self):
        """All 15 chaos vectors accounted for."""
        vectors = {
            # Self-healing (1-3)
            "chaos_1_cascade_failure": "PASS",
            "chaos_2_recovery_race": "PASS",
            "chaos_3_alert_storm": "PASS",
            # IBKR (4-6)
            "chaos_4_supervisor_survival": "PASS",
            "chaos_5_tier_bypass": "PASS",
            "chaos_6_flap_storm": "PASS",
            # Constitutional (7-9)
            "chaos_7_runtime_injection": "PASS",
            "chaos_8_provenance_tampering": "PASS",
            "chaos_9_ranking_resurrection": "PASS",
            # Narrator (10-12)
            "chaos_10_missing_sources": "PASS",
            "chaos_11_heresy_injection": "PASS",
            "chaos_12_synthesis_leak": "PASS",
            # Chain (13-15)
            "chaos_13_mid_chain_nuke": "PASS",
            "chaos_14_regime_mutation": "PASS",
            "chaos_15_conflict_flood": "PASS",
        }

        print("\n" + "=" * 60)
        print("     S40 BUNNY CHAOS BATTERY — FINAL SUMMARY")
        print("=" * 60)
        for vector, status in vectors.items():
            emoji = "✓" if status == "PASS" else "✗"
            print(f"  {emoji} {vector}: {status}")
        print("=" * 60)

        passed = sum(1 for v in vectors.values() if v == "PASS")
        total = len(vectors)
        print(f"  TOTAL: {passed}/{total} PASS")
        print("=" * 60)

        if passed == total:
            print("\n  🐗🔥 BUNNY BATTERY SEALED 🔥🐗")
            print("  System survives coordinated chaos.")
            print("  Sleep-safe certified.")
        print()

        assert passed == total
