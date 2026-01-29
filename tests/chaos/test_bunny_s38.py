"""
BUNNY Chaos Tests — S38 Hunt Engine
===================================

32+ chaos vectors targeting idea-engine leakage.

INVARIANTS TESTED:
  - INV-HUNT-EXHAUSTIVE: Compute ALL, never select
  - INV-NO-UNSOLICITED: No auto-propose
  - INV-HUNT-METRICS-DECLARED: Metrics mandatory
  - INV-GRID-DIMENSION-CAP: Max 3 dimensions
  - INV-HUNT-PARTIAL-WATERMARK: Completeness on abort

CRITICAL: Hunt computes, never proposes.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from hunt.budget import BudgetEnforcer, BudgetStatus
from hunt.executor import HuntExecutor, HuntStatus
from hunt.hypothesis import (
    FORBIDDEN_FIELDS,
    GridDimension,
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisFraming,
    HypothesisGrid,
    HypothesisValidator,
)
from hunt.output import OutputValidator
from hunt.queue import ApprovalRequiredError, HuntQueue, PriorityForbiddenError


# =============================================================================
# WAVE 1: PROPOSAL ATTACKS
# =============================================================================


class TestWave1ProposalAttacks:
    """Attempts to make system propose hypotheses."""

    def test_cv_system_sourced_hypothesis_rejected(self) -> None:
        """CV-P1: System-sourced hypothesis rejected."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test?",
                source="system",  # FORBIDDEN
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid, "System source must be rejected"

    def test_cv_auto_generated_hypothesis_rejected(self) -> None:
        """CV-P2: Auto-generated hypothesis rejected."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test?",
                source="generated",  # FORBIDDEN
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid

    def test_cv_suggest_next_hypothesis_rejected(self) -> None:
        """CV-P3: suggest_next() is forbidden."""
        queue = HuntQueue()
        with pytest.raises(PriorityForbiddenError):
            queue.suggest_next()


# =============================================================================
# WAVE 2: SELECTION ATTACKS
# =============================================================================


class TestWave2SelectionAttacks:
    """Attempts to get subset of results."""

    def test_cv_request_top_5_variants_forbidden(self) -> None:
        """CV-S1: 'top_variants' field rejected."""
        validator = OutputValidator()
        output = {"top_variants": ["V1", "V2"]}
        valid, _ = validator.validate(output)

        assert not valid, "top_variants must be rejected"

    def test_cv_request_survivors_only_forbidden(self) -> None:
        """CV-S2: 'survivors' field rejected."""
        validator = OutputValidator()
        output = {"survivors": ["V1"]}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_request_promising_variants_forbidden(self) -> None:
        """CV-S3: 'promising' field rejected."""
        validator = OutputValidator()
        output = {"promising": ["V1"]}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_output_variants_skipped_zero(self) -> None:
        """CV-S4: Complete execution has variants_skipped=0."""
        executor = HuntExecutor()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=[1, 2, 3])]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=3),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        result = executor.execute(hypothesis)
        assert result.variants_skipped == 0


# =============================================================================
# WAVE 3: RANKING ATTACKS
# =============================================================================


class TestWave3RankingAttacks:
    """Attempts to get ranked output."""

    def test_cv_request_sort_by_sharpe_rejected(self) -> None:
        """CV-R1: Sort by metric rejected."""
        validator = OutputValidator()
        valid, _ = validator.validate_no_sort_request("sort by sharpe")

        assert not valid, "Sort by metric must be rejected"

    def test_cv_best_variant_field_rejected(self) -> None:
        """CV-R2: 'best_variant' field rejected."""
        validator = OutputValidator()
        output = {"best_variant": "V1"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_ranking_field_rejected(self) -> None:
        """CV-R3: 'ranking' field rejected."""
        validator = HypothesisValidator()
        data = {"hypothesis_id": "test", "ranking": [1, 2, 3]}
        result = validator.validate_dict(data)

        assert not result.valid


# =============================================================================
# WAVE 4: PRIORITY ATTACKS
# =============================================================================


class TestWave4PriorityAttacks:
    """Attempts to prioritize queue."""

    def test_cv_enqueue_with_priority_rejected(self) -> None:
        """CV-PR1: Priority insert forbidden."""
        queue = HuntQueue()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        with pytest.raises(PriorityForbiddenError):
            queue.priority_insert(hypothesis)

    def test_cv_reorder_queue_by_potential_rejected(self) -> None:
        """CV-PR2: Reorder by potential forbidden."""
        queue = HuntQueue()
        with pytest.raises(PriorityForbiddenError):
            queue.reorder_by_potential()


# =============================================================================
# WAVE 5: BUDGET ATTACKS
# =============================================================================


class TestWave5BudgetAttacks:
    """Attempts to exceed budget."""

    def test_cv_100k_variants_without_t2_rejected(self) -> None:
        """CV-B1: 100k variants without T2 rejected."""
        enforcer = BudgetEnforcer(max_variants=10000)
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[
                    GridDimension(dimension="x", values=list(range(1000))),
                    GridDimension(dimension="y", values=list(range(100))),
                ]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=100000),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        check = enforcer.check_pre_execution(hypothesis)
        assert check.status == BudgetStatus.REJECTED


# =============================================================================
# WAVE 6: SYNTHESIS ATTACKS
# =============================================================================


class TestWave6SynthesisAttacks:
    """Attempts to get synthesis/recommendations."""

    def test_cv_key_finding_rejected(self) -> None:
        """CV-SY1: 'key_finding' rejected."""
        validator = OutputValidator()
        output = {"key_finding": "Delay improves performance"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_recommendation_rejected(self) -> None:
        """CV-SY2: 'recommendation' rejected."""
        validator = OutputValidator()
        output = {"recommendation": "Use variant 3"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_pattern_detected_rejected(self) -> None:
        """CV-SY3: 'pattern_detected' rejected."""
        validator = OutputValidator()
        output = {"pattern_detected": "Higher delay = better"}
        valid, _ = validator.validate(output)

        assert not valid


# =============================================================================
# WAVE 7: APPROVAL BYPASS
# =============================================================================


class TestWave7ApprovalBypass:
    """Attempts to bypass approval."""

    def test_cv_execute_unapproved_rejected(self) -> None:
        """CV-A1: Execute unapproved hypothesis rejected."""
        executor = HuntExecutor()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=[1, 2])]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=2),
            approval=HypothesisApproval(approved=False),  # NOT APPROVED
        )

        with pytest.raises(ValueError):
            executor.execute(hypothesis)

    def test_cv_enqueue_unapproved_rejected(self) -> None:
        """CV-A2: Enqueue unapproved hypothesis rejected."""
        queue = HuntQueue()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
            approval=HypothesisApproval(approved=False),
        )

        with pytest.raises(ApprovalRequiredError):
            queue.enqueue(hypothesis)


# =============================================================================
# WAVE 12: METRIC ATTACKS (NEW)
# =============================================================================


class TestWave12MetricAttacks:
    """Attempts to manipulate metrics."""

    def test_cv_system_adds_derived_metric_rejected(self) -> None:
        """CV-M1: System cannot add derived metrics."""
        validator = HypothesisValidator()
        data = {"hypothesis_id": "test", "edge_score": 85}  # FORBIDDEN
        result = validator.validate_dict(data)

        assert not result.valid

    def test_cv_empty_metrics_list_invalid(self) -> None:
        """CV-M2: Empty metrics list is invalid."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            metrics=[],  # EMPTY — INVALID
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid
        assert any(e.code == "EMPTY_METRICS" for e in result.errors)


# =============================================================================
# WAVE 13: DIMENSION ATTACKS (NEW)
# =============================================================================


class TestWave13DimensionAttacks:
    """Attempts to exceed dimension caps."""

    def test_cv_4_dimension_grid_rejected(self) -> None:
        """CV-D1: 4-dimension grid rejected."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[
                    GridDimension(dimension="d1", values=[1, 2]),
                    GridDimension(dimension="d2", values=[1, 2]),
                    GridDimension(dimension="d3", values=[1, 2]),
                    GridDimension(dimension="d4", values=[1, 2]),  # 4th — REJECTED
                ]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=16),
        )
        result = validator.validate(hypothesis)

        assert not result.valid
        assert any(e.code == "DIMENSION_CAP_EXCEEDED" for e in result.errors)

    def test_cv_1000_value_dimension_without_t2_rejected(self) -> None:
        """CV-D2: 1000+ values without T2 rejected."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[
                    GridDimension(dimension="x", values=list(range(1500))),  # > hard cap
                ]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=1500),
        )
        result = validator.validate(hypothesis, t2_override=False)

        assert not result.valid
        assert any(e.code == "CARDINALITY_HARD_CAP" for e in result.errors)


# =============================================================================
# WAVE 14: PARTIAL INTERPRETATION (NEW)
# =============================================================================


class TestWave14PartialInterpretation:
    """Attempts to interpret partial results."""

    def test_cv_partial_has_abort_notice(self) -> None:
        """CV-PI1: Partial results have abort notice."""
        executor = HuntExecutor()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=list(range(10)))]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        result = executor.execute(hypothesis, abort_at=5)

        assert result.status == HuntStatus.ABORTED
        assert result.abort_metadata is not None
        assert "ABORTED" in result.abort_metadata.abort_notice
        assert "NO INTERPRETATION" in result.abort_metadata.abort_notice

    def test_cv_partial_has_completeness_mask(self) -> None:
        """CV-PI2: Partial results have completeness_mask."""
        executor = HuntExecutor()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=list(range(10)))]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        result = executor.execute(hypothesis, abort_at=5)

        assert result.abort_metadata is not None
        assert result.abort_metadata.completeness_mask is not None
        assert len(result.abort_metadata.completeness_mask) == 10
        assert sum(result.abort_metadata.completeness_mask) == 5  # 5 computed


# =============================================================================
# WAVE 15: SALIENCE ATTACKS (NEW)
# =============================================================================


class TestWave15SalienceAttacks:
    """Attempts to manipulate display salience."""

    def test_cv_request_highlight_extremes_rejected(self) -> None:
        """CV-SA1: 'highlighted' field rejected."""
        validator = OutputValidator()
        output = {"highlighted": ["V1"]}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_winners_section_rejected(self) -> None:
        """CV-SA2: 'Winners' in content rejected."""
        validator = OutputValidator()
        output = {"summary": "Winners: V1, V2, V3"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_best_performers_rejected(self) -> None:
        """CV-SA3: 'Best Performers' rejected."""
        validator = OutputValidator()
        output = {"text": "Best Performers: V1"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_top_n_rejected(self) -> None:
        """CV-SA4: 'Top N' rejected."""
        validator = OutputValidator()
        output = {"text": "Top N results available"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_recommended_rejected(self) -> None:
        """CV-SA5: 'Recommended' rejected."""
        validator = OutputValidator()
        output = {"text": "Recommended variants"}
        valid, _ = validator.validate(output)

        assert not valid

    def test_cv_key_insights_rejected(self) -> None:
        """CV-SA6: 'Key Insights' rejected."""
        validator = OutputValidator()
        output = {"text": "Key Insights from run"}
        valid, _ = validator.validate(output)

        assert not valid


# =============================================================================
# WAVE 16: EXECUTION ATTACKS (NEW)
# =============================================================================


class TestWave16ExecutionAttacks:
    """Additional execution attacks."""

    def test_cv_all_variants_computed(self) -> None:
        """CV-EX1: ALL variants computed."""
        executor = HuntExecutor()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[
                    GridDimension(dimension="x", values=[1, 2, 3]),
                    GridDimension(dimension="y", values=[1, 2]),
                ]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=6),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        result = executor.execute(hypothesis)
        assert result.variants_computed == result.total_variants

    def test_cv_grid_order_in_output(self) -> None:
        """CV-EX2: Grid order declared in output."""
        executor = HuntExecutor()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=[1, 2])]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=2),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        result = executor.execute(hypothesis)
        assert result.grid_order_declaration
        assert "cartesian_product" in result.grid_order_declaration

    def test_cv_athena_source_rejected(self) -> None:
        """CV-EX3: 'athena' source rejected."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="athena", domain="test"),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid

    def test_cv_hunt_engine_source_rejected(self) -> None:
        """CV-EX4: 'hunt_engine' source rejected."""
        validator = HypothesisValidator()
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="hunt_engine", domain="test"),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid


# =============================================================================
# CHAOS VECTOR COUNT
# =============================================================================


def test_chaos_vector_count() -> None:
    """Verify 32+ chaos vectors exist."""
    import inspect

    test_classes = [
        TestWave1ProposalAttacks,
        TestWave2SelectionAttacks,
        TestWave3RankingAttacks,
        TestWave4PriorityAttacks,
        TestWave5BudgetAttacks,
        TestWave6SynthesisAttacks,
        TestWave7ApprovalBypass,
        TestWave12MetricAttacks,
        TestWave13DimensionAttacks,
        TestWave14PartialInterpretation,
        TestWave15SalienceAttacks,
        TestWave16ExecutionAttacks,
    ]

    total_tests = 0
    for cls in test_classes:
        methods = [m for m in dir(cls) if m.startswith("test_cv_")]
        total_tests += len(methods)

    assert total_tests >= 32, f"Expected 32+ chaos vectors, got {total_tests}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
