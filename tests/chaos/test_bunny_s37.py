"""
BUNNY Chaos Tests — S37 Memory Discipline
=========================================

28+ chaos vectors targeting myth leakage.

INVARIANTS TESTED:
  - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates
  - INV-NO-AUTO-SURFACE: No unsolicited surfacing
  - INV-CONFLICT-NO-AGGREGATION: No counting/ranking
  - INV-SEMANTIC-NO-SINGLE-BEST: Unordered neighborhood
  - INV-HISTORY-NO-BURY: Full chain always

CRITICAL: These tests prove claims cannot become doctrine.
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from athena.bead_types import (
    BeadValidator,
    ClaimBead,
    ClaimContent,
    ClaimSource,
    ClaimStatus,
    ConflictBead,
    ConflictReferences,
    ConflictType,
    FactBead,
    FactContent,
    FactProvenance,
    FactSource,
    StatisticalParameters,
    StatisticalType,
)
from athena.claim_linter import ClaimLanguageLinter
from athena.conflict_detector import ConflictAggregationBan, ConflictDetector
from athena.semantic import SemanticQuery


# =============================================================================
# WAVE 1: CLAIM EXECUTION ATTACKS (Critical)
# =============================================================================


class TestWave1ClaimExecutionAttacks:
    """
    Wave 1: Attempts to use claims as executable predicates.

    This is the PRIMARY HARDENING TARGET for S37.
    """

    def test_cv_claim_in_cso_predicate_rejected(self) -> None:
        """CV-E1: Claim in CSO predicate is rejected."""
        from athena.store import AthenaStore, ExecutionGuardError

        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            store = AthenaStore(db_path=Path(f.name))

            with pytest.raises(ExecutionGuardError):
                store.validate_no_claim_execution(
                    predicate_refs=["CLAIM_abc123"],
                    alert_refs=[],
                    hunt_refs=[],
                )

    def test_cv_claim_in_alert_rule_rejected(self) -> None:
        """CV-E2: Claim in alert rule is rejected."""
        from athena.store import AthenaStore, ExecutionGuardError

        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            store = AthenaStore(db_path=Path(f.name))

            with pytest.raises(ExecutionGuardError):
                store.validate_no_claim_execution(
                    predicate_refs=[],
                    alert_refs=["CLAIM_xyz789"],
                    hunt_refs=[],
                )

    def test_cv_claim_in_hunt_parameter_rejected(self) -> None:
        """CV-E3: Claim in hunt parameter is rejected."""
        from athena.store import AthenaStore, ExecutionGuardError

        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            store = AthenaStore(db_path=Path(f.name))

            with pytest.raises(ExecutionGuardError):
                store.validate_no_claim_execution(
                    predicate_refs=[],
                    alert_refs=[],
                    hunt_refs=["CLAIM_hunt123"],
                )


# =============================================================================
# WAVE 2: WRITEBACK ATTACKS
# =============================================================================


class TestWave2WritebackAttacks:
    """
    Wave 2: Attempts to mutate doctrine from claims.
    """

    def test_cv_claim_with_verified_true_rejected(self) -> None:
        """CV-W1: Claim with verified=true is rejected."""
        validator = BeadValidator()
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(assertion="Test", domain="test"),
            status=ClaimStatus(verified=True),  # FORBIDDEN
        )
        result = validator.validate_claim(claim)

        assert not result.valid, "Verified=true must be rejected"

    def test_cv_claim_without_disclaimer_rejected(self) -> None:
        """CV-W2: Claim without disclaimer is rejected."""
        validator = BeadValidator()
        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(assertion="Test", domain="test"),
            disclaimer="",  # MISSING
        )
        result = validator.validate_claim(claim)

        assert not result.valid, "Missing disclaimer must be rejected"

    def test_cv_claim_without_attribution_rejected(self) -> None:
        """CV-W3: Claim without attribution is rejected."""
        validator = BeadValidator()
        claim = ClaimBead(
            source=ClaimSource(attribution=""),  # MISSING
            content=ClaimContent(assertion="Test", domain="test"),
        )
        result = validator.validate_claim(claim)

        assert not result.valid, "Missing attribution must be rejected"


# =============================================================================
# WAVE 3: RESOLUTION ATTACKS
# =============================================================================


class TestWave3ResolutionAttacks:
    """
    Wave 3: Attempts to auto-resolve conflicts.
    """

    def test_cv_conflict_with_severity_rejected(self) -> None:
        """CV-R1: Conflict with severity is rejected."""
        validator = BeadValidator()
        conflict_dict = {
            "bead_id": "test",
            "severity": "HIGH",  # FORBIDDEN
        }
        result = validator.validate_dict(conflict_dict)

        assert not result.valid, "Severity field must be rejected"

    def test_cv_conflict_with_urgency_rejected(self) -> None:
        """CV-R2: Conflict with urgency is rejected."""
        validator = BeadValidator()
        conflict_dict = {
            "bead_id": "test",
            "urgency": "CRITICAL",  # FORBIDDEN
        }
        result = validator.validate_dict(conflict_dict)

        assert not result.valid, "Urgency field must be rejected"


# =============================================================================
# WAVE 4: CONFLICT AGGREGATION ATTACKS
# =============================================================================


class TestWave4ConflictAggregationAttacks:
    """
    Wave 4: Attempts to aggregate conflicts.
    """

    def test_cv_conflicts_per_domain_rejected(self) -> None:
        """CV-A1: Request for conflicts per domain count is rejected."""
        valid, error = ConflictAggregationBan.validate_query(
            "Give me conflicts_per_domain count"
        )

        assert not valid, "Conflict count must be rejected"

    def test_cv_oldest_unresolved_rejected(self) -> None:
        """CV-A2: Request for oldest unresolved conflicts is rejected."""
        valid, error = ConflictAggregationBan.validate_query(
            "Show me oldest_unresolved conflicts"
        )

        assert not valid, "Oldest unresolved must be rejected"

    def test_cv_domains_with_most_conflicts_rejected(self) -> None:
        """CV-A3: Request for domains with most conflicts is rejected."""
        valid, error = ConflictAggregationBan.validate_query(
            "Which domains_with_most conflicts?"
        )

        assert not valid, "Most conflicts must be rejected"


# =============================================================================
# WAVE 5: SEMANTIC RANKING ATTACKS
# =============================================================================


class TestWave5SemanticRankingAttacks:
    """
    Wave 5: Attempts to get ranked semantic results.
    """

    def test_cv_most_similar_rejected(self) -> None:
        """CV-S1: Request for 'most similar' is rejected."""
        query = SemanticQuery()
        valid, error = query.validate_query("Give me most similar claims")

        assert not valid, "Most similar must be rejected"

    def test_cv_top_match_rejected(self) -> None:
        """CV-S2: Request for 'top match' is rejected."""
        query = SemanticQuery()
        valid, error = query.validate_query("What's the top match?")

        assert not valid, "Top match must be rejected"

    def test_cv_best_match_rejected(self) -> None:
        """CV-S3: Request for 'best match' is rejected."""
        query = SemanticQuery()
        valid, error = query.validate_query("Find best match")

        assert not valid, "Best match must be rejected"

    def test_cv_descending_sort_rejected(self) -> None:
        """CV-S4: Request for descending sort is rejected."""
        query = SemanticQuery()
        valid, error = query.validate_sort_order("DESC")

        assert not valid, "Descending sort must be rejected"


# =============================================================================
# WAVE 6: AUTO-SURFACE ATTACKS
# =============================================================================


class TestWave6AutoSurfaceAttacks:
    """
    Wave 6: Attempts to auto-surface claims.
    """

    def test_cv_auto_surface_on_chart_rejected(self) -> None:
        """CV-AS1: Auto-surface on chart open is rejected."""
        from athena.store import AthenaStore, AutoSurfaceError

        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            store = AthenaStore(db_path=Path(f.name))

            with pytest.raises(AutoSurfaceError):
                store.validate_no_auto_surface("PUSH_CLAIM_ON_CHART")

    def test_cv_surface_matching_claims_rejected(self) -> None:
        """CV-AS2: Surface matching claims is rejected."""
        from athena.store import AthenaStore, AutoSurfaceError

        with tempfile.NamedTemporaryFile(suffix=".db") as f:
            store = AthenaStore(db_path=Path(f.name))

            with pytest.raises(AutoSurfaceError):
                store.validate_no_auto_surface("SURFACE_MATCHING_CLAIMS")


# =============================================================================
# WAVE 7: HISTORY ATTACKS
# =============================================================================


class TestWave7HistoryAttacks:
    """
    Wave 7: Attempts to manipulate history.
    """

    def test_cv_claims_contradicted_most_rejected(self) -> None:
        """CV-H1: Request for 'claims contradicted_most' is rejected."""
        valid, error = ConflictAggregationBan.validate_query(
            "Which claims were contradicted_most?"
        )

        assert not valid, "Contradicted most must be rejected"

    def test_cv_facts_disproved_claims_rejected(self) -> None:
        """CV-H2: Request for 'facts that disproved_claims' is rejected."""
        valid, error = ConflictAggregationBan.validate_query(
            "Show facts that disproved_claims"
        )

        assert not valid, "Disproved claims must be rejected"

    def test_cv_conflict_count_rejected(self) -> None:
        """CV-H3: Request for 'conflict_count' is rejected."""
        valid, error = ConflictAggregationBan.validate_query(
            "What is the conflict_count?"
        )

        assert not valid, "Conflict count must be rejected"


# =============================================================================
# WAVE 8: STATISTICAL CONFLICT DETECTION
# =============================================================================


class TestWave8StatisticalConflict:
    """
    Wave 8: Statistical conflict detection.
    """

    def test_cv_70_claim_vs_40_fact_conflict(self) -> None:
        """CV-ST1: 70% claim vs 40% fact creates conflict."""
        detector = ConflictDetector()

        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(
                assertion="FVGs work about 70% of the time",
                domain="ICT",
            ),
            statistical_parameters=StatisticalParameters(
                type=StatisticalType.PERCENTAGE,
                value=0.70,
                bounds_lower=0.60,
                bounds_upper=0.80,
            ),
        )

        fact = FactBead(
            source=FactSource(module="cfp"),
            content=FactContent(
                statement="FVGs filled 40% this week",
                value=0.40,
                domain="ICT",
            ),
            provenance=FactProvenance(
                query_string="q",
                dataset_hash="a",
                governance_hash="b",
                strategy_config_hash="c",
            ),
        )

        result = detector.check_claim_against_fact(claim, fact)

        assert result.has_conflict, "40% outside 60-80% bounds should conflict"
        assert result.conflict_type == ConflictType.STATISTICAL

    def test_cv_within_bounds_no_conflict(self) -> None:
        """CV-ST2: Fact within bounds creates no conflict."""
        detector = ConflictDetector()

        claim = ClaimBead(
            source=ClaimSource(attribution="Olya"),
            content=ClaimContent(
                assertion="FVGs work about 70% of the time",
                domain="ICT",
            ),
            statistical_parameters=StatisticalParameters(
                type=StatisticalType.PERCENTAGE,
                value=0.70,
                bounds_lower=0.60,
                bounds_upper=0.80,
            ),
        )

        fact = FactBead(
            source=FactSource(module="cfp"),
            content=FactContent(
                statement="FVGs filled 68% this week",
                value=0.68,  # Within bounds
                domain="ICT",
            ),
            provenance=FactProvenance(
                query_string="q",
                dataset_hash="a",
                governance_hash="b",
                strategy_config_hash="c",
            ),
        )

        result = detector.check_claim_against_fact(claim, fact)

        assert not result.has_conflict, "68% within 60-80% bounds should not conflict"


# =============================================================================
# WAVE 9: POLARITY ATTACKS
# =============================================================================


class TestWave9PolarityAttacks:
    """
    Wave 9: Semantic polarity handling.
    """

    def test_cv_bullish_returns_bearish_flagged(self) -> None:
        """CV-P1: Bullish query returning bearish is flagged."""
        query = SemanticQuery()
        is_ambiguous, reason = query.check_polarity(
            "Bullish FVG",
            "Bearish order block works well",
            0.15,  # Low distance
        )

        assert is_ambiguous, "Polar match at low distance must be flagged"
        assert "Polar opposite" in reason


# =============================================================================
# WAVE 10: LANGUAGE LINTING ATTACKS
# =============================================================================


class TestWave10LanguageLinting:
    """
    Wave 10: Claim language linting.
    """

    def test_cv_always_in_claim_rejected(self) -> None:
        """CV-L1: 'always' in claim is rejected."""
        linter = ClaimLanguageLinter()
        result = linter.lint("FVGs always fill")

        assert not result.valid, "'always' must be rejected"

    def test_cv_guaranteed_in_claim_rejected(self) -> None:
        """CV-L2: 'guaranteed' in claim is rejected."""
        linter = ClaimLanguageLinter()
        result = linter.lint("Guaranteed profit with this setup")

        assert not result.valid, "'guaranteed' must be rejected"

    def test_cv_100_percent_in_claim_rejected(self) -> None:
        """CV-L3: '100%' in claim is rejected."""
        linter = ClaimLanguageLinter()
        result = linter.lint("This works 100% of the time")

        assert not result.valid, "'100%' must be rejected"


# =============================================================================
# WAVE 11: TYPE CONFUSION ATTACKS
# =============================================================================


class TestWave11TypeConfusion:
    """
    Wave 11: Type validation.
    """

    def test_cv_fact_without_provenance_rejected(self) -> None:
        """CV-T1: Fact without provenance is rejected."""
        validator = BeadValidator()
        fact = FactBead(
            source=FactSource(module="cfp"),
            content=FactContent(statement="Test", value=1.0, domain="test"),
            # No provenance
        )
        result = validator.validate_fact(fact)

        assert not result.valid, "Fact without provenance must be rejected"

    def test_cv_conflict_without_refs_rejected(self) -> None:
        """CV-T2: Conflict without references is rejected."""
        validator = BeadValidator()
        conflict = ConflictBead(
            references=ConflictReferences(
                claim_bead_id="",  # MISSING
                fact_bead_id="",  # MISSING
            ),
        )
        result = validator.validate_conflict(conflict)

        assert not result.valid, "Conflict without refs must be rejected"


# =============================================================================
# SUMMARY
# =============================================================================


def test_chaos_vector_count() -> None:
    """Verify 28+ chaos vectors exist."""

    test_classes = [
        TestWave1ClaimExecutionAttacks,
        TestWave2WritebackAttacks,
        TestWave3ResolutionAttacks,
        TestWave4ConflictAggregationAttacks,
        TestWave5SemanticRankingAttacks,
        TestWave6AutoSurfaceAttacks,
        TestWave7HistoryAttacks,
        TestWave8StatisticalConflict,
        TestWave9PolarityAttacks,
        TestWave10LanguageLinting,
        TestWave11TypeConfusion,
    ]

    total_tests = 0
    for cls in test_classes:
        methods = [m for m in dir(cls) if m.startswith("test_cv_")]
        total_tests += len(methods)

    assert total_tests >= 28, f"Expected 28+ chaos vectors, got {total_tests}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
