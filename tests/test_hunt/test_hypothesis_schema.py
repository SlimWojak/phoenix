"""
Hypothesis Schema Tests — S38 Track A
=====================================

INVARIANTS PROVEN:
  - INV-NO-UNSOLICITED: Human frames only
  - INV-HUNT-METRICS-DECLARED: Metrics mandatory
  - INV-GRID-DIMENSION-CAP: Max 3 dimensions
  - INV-HUNT-DIM-CARDINALITY-CAP: Per-dim caps

EXIT GATE A:
  Criterion: "Hypothesis validates; metrics mandatory; dimension caps enforced"
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from hunt.hypothesis import (
    DIMENSION_HARD_CAP,
    DIMENSION_SOFT_CAP,
    FORBIDDEN_FIELDS,
    FORBIDDEN_SOURCES,
    MAX_DIMENSIONS,
    CardinalityWarning,
    FixedParameter,
    GridDimension,
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisConstraints,
    HypothesisFraming,
    HypothesisGrid,
    HypothesisValidator,
    ValidationResult,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def validator() -> HypothesisValidator:
    """Create validator instance."""
    return HypothesisValidator()


@pytest.fixture
def valid_hypothesis() -> Hypothesis:
    """Valid hypothesis for testing."""
    return Hypothesis(
        framing=HypothesisFraming(
            question="Does waiting until 8:30 improve London FVG entries?",
            source="Olya",
            domain="ICT",
        ),
        grid=HypothesisGrid(
            dimensions=[
                GridDimension(dimension="entry_delay", values=[0, 15, 30, 45, 60]),
                GridDimension(dimension="stop_mult", values=[1.0, 1.5, 2.0]),
            ]
        ),
        metrics=["sharpe", "win_rate", "max_drawdown"],
        budget=HypothesisBudget(max_variants=15),
        approval=HypothesisApproval(
            approved=True,
            approved_by="Olya",
            approved_at=datetime.now(UTC),
        ),
    )


# =============================================================================
# SOURCE VALIDATION TESTS (INV-NO-UNSOLICITED)
# =============================================================================


class TestSourceValidation:
    """Tests for human-only source validation."""

    def test_human_source_allowed(
        self,
        validator: HypothesisValidator,
        valid_hypothesis: Hypothesis,
    ) -> None:
        """Human source is allowed."""
        result = validator.validate(valid_hypothesis)
        assert result.valid

    def test_system_source_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """System source is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="system",  # FORBIDDEN
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid
        assert any(e.code == "FORBIDDEN_SOURCE" for e in result.errors)

    def test_athena_source_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Athena source is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="athena",  # FORBIDDEN
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid

    def test_hunt_engine_source_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Hunt engine source is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="hunt_engine",  # FORBIDDEN
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid

    def test_auto_source_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Auto source is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="auto",  # FORBIDDEN
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid

    def test_missing_source_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Missing source is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="",  # MISSING
                domain="test",
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid
        assert any(e.code == "MISSING_SOURCE" for e in result.errors)


# =============================================================================
# METRICS VALIDATION TESTS (INV-HUNT-METRICS-DECLARED)
# =============================================================================


class TestMetricsValidation:
    """Tests for mandatory metrics."""

    def test_metrics_required(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Empty metrics list is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="Olya",
                domain="test",
            ),
            metrics=[],  # EMPTY — INVALID
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert not result.valid
        assert any(e.code == "EMPTY_METRICS" for e in result.errors)

    def test_metrics_present_passes(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Hypothesis with metrics passes."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="Olya",
                domain="test",
            ),
            metrics=["sharpe"],  # Present
            budget=HypothesisBudget(max_variants=10),
        )
        result = validator.validate(hypothesis)

        assert result.valid


# =============================================================================
# DIMENSION CAP TESTS (INV-GRID-DIMENSION-CAP)
# =============================================================================


class TestDimensionCap:
    """Tests for max 3 dimensions."""

    def test_3_dimensions_allowed(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """3 dimensions is allowed."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="Olya",
                domain="test",
            ),
            grid=HypothesisGrid(
                dimensions=[
                    GridDimension(dimension="dim1", values=[1, 2]),
                    GridDimension(dimension="dim2", values=[1, 2]),
                    GridDimension(dimension="dim3", values=[1, 2]),
                ]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=8),
        )
        result = validator.validate(hypothesis)

        assert result.valid

    def test_4_dimensions_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """4 dimensions is rejected."""
        hypothesis = Hypothesis(
            framing=HypothesisFraming(
                question="Test",
                source="Olya",
                domain="test",
            ),
            grid=HypothesisGrid(
                dimensions=[
                    GridDimension(dimension="dim1", values=[1, 2]),
                    GridDimension(dimension="dim2", values=[1, 2]),
                    GridDimension(dimension="dim3", values=[1, 2]),
                    GridDimension(dimension="dim4", values=[1, 2]),  # 4th — REJECTED
                ]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=16),
        )
        result = validator.validate(hypothesis)

        assert not result.valid
        assert any(e.code == "DIMENSION_CAP_EXCEEDED" for e in result.errors)


# =============================================================================
# CARDINALITY CAP TESTS (INV-HUNT-DIM-CARDINALITY-CAP)
# =============================================================================


class TestCardinalityCap:
    """Tests for per-dimension cardinality caps."""

    def test_under_soft_cap_ok(self) -> None:
        """Under soft cap is OK."""
        dim = GridDimension(dimension="test", values=list(range(50)))
        assert dim.check_cardinality() == CardinalityWarning.OK

    def test_over_soft_cap_warning(self) -> None:
        """Over soft cap is WARNING."""
        dim = GridDimension(dimension="test", values=list(range(150)))
        assert dim.check_cardinality() == CardinalityWarning.WARNING

    def test_over_hard_cap_rejected(self) -> None:
        """Over hard cap is REJECT."""
        dim = GridDimension(dimension="test", values=list(range(1500)))
        assert dim.check_cardinality() == CardinalityWarning.REJECT

    def test_over_hard_cap_with_t2_allowed(self) -> None:
        """Over hard cap with T2 is allowed."""
        dim = GridDimension(dimension="test", values=list(range(1500)))
        assert dim.check_cardinality(t2_override=True) == CardinalityWarning.WARNING


# =============================================================================
# APPROVAL VALIDATION TESTS
# =============================================================================


class TestApprovalValidation:
    """Tests for approval validation."""

    def test_approved_passes(
        self,
        validator: HypothesisValidator,
        valid_hypothesis: Hypothesis,
    ) -> None:
        """Approved hypothesis passes."""
        result = validator.validate_approval(valid_hypothesis)
        assert result.valid

    def test_unapproved_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Unapproved hypothesis is rejected."""
        hypothesis = Hypothesis(
            approval=HypothesisApproval(approved=False),
        )
        result = validator.validate_approval(hypothesis)

        assert not result.valid
        assert any(e.code == "NOT_APPROVED" for e in result.errors)

    def test_missing_approver_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """Missing approver is rejected."""
        hypothesis = Hypothesis(
            approval=HypothesisApproval(
                approved=True,
                approved_by="",  # MISSING
            ),
        )
        result = validator.validate_approval(hypothesis)

        assert not result.valid
        assert any(e.code == "MISSING_APPROVER" for e in result.errors)


# =============================================================================
# FORBIDDEN FIELDS TESTS
# =============================================================================


class TestForbiddenFields:
    """Tests for forbidden field rejection."""

    def test_proposed_by_system_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """proposed_by_system field is rejected."""
        data = {
            "hypothesis_id": "test",
            "proposed_by_system": True,  # FORBIDDEN
        }
        result = validator.validate_dict(data)

        assert not result.valid

    def test_confidence_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """confidence field is rejected."""
        data = {
            "hypothesis_id": "test",
            "confidence": 0.9,  # FORBIDDEN
        }
        result = validator.validate_dict(data)

        assert not result.valid

    def test_edge_score_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """edge_score field is rejected."""
        data = {
            "hypothesis_id": "test",
            "edge_score": 85,  # FORBIDDEN
        }
        result = validator.validate_dict(data)

        assert not result.valid

    def test_survivors_rejected(
        self,
        validator: HypothesisValidator,
    ) -> None:
        """survivors field is rejected."""
        data = {
            "hypothesis_id": "test",
            "survivors": ["variant_1"],  # FORBIDDEN
        }
        result = validator.validate_dict(data)

        assert not result.valid


# =============================================================================
# GRID CALCULATION TESTS
# =============================================================================


class TestGridCalculations:
    """Tests for grid calculations."""

    def test_total_variants_calculation(self) -> None:
        """Total variants is product of dimensions."""
        grid = HypothesisGrid(
            dimensions=[
                GridDimension(dimension="a", values=[1, 2, 3]),  # 3
                GridDimension(dimension="b", values=[1, 2]),  # 2
            ]
        )
        assert grid.total_variants == 6

    def test_empty_grid_zero_variants(self) -> None:
        """Empty grid has zero variants."""
        grid = HypothesisGrid(dimensions=[])
        assert grid.total_variants == 0


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
