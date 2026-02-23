"""
Executor Tests — S38 Track C
============================

INVARIANTS PROVEN:
  - INV-HUNT-EXHAUSTIVE: Compute ALL
  - INV-HUNT-PARTIAL-WATERMARK: Completeness on abort

EXIT GATE C:
  Criterion: "Executor computes ALL variants; no selection; grid order output"
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from hunt.executor import HuntExecutor, HuntStatus
from hunt.hypothesis import (
    GridDimension,
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisFraming,
    HypothesisGrid,
)


@pytest.fixture
def executor() -> HuntExecutor:
    return HuntExecutor()


@pytest.fixture
def simple_hypothesis() -> Hypothesis:
    return Hypothesis(
        framing=HypothesisFraming(
            question="Test delay vs stop?",
            source="Olya",
            domain="test",
        ),
        grid=HypothesisGrid(
            dimensions=[
                GridDimension(dimension="delay", values=[0, 15, 30]),
                GridDimension(dimension="stop", values=[1.0, 1.5]),
            ]
        ),
        metrics=["sharpe", "win_rate"],
        budget=HypothesisBudget(max_variants=6),
        approval=HypothesisApproval(
            approved=True,
            approved_by="Olya",
            approved_at=datetime.now(UTC),
        ),
    )


class TestExhaustiveExecution:
    def test_all_variants_computed(
        self, executor: HuntExecutor, simple_hypothesis: Hypothesis
    ) -> None:
        """All grid points computed."""
        result = executor.execute(simple_hypothesis)

        assert result.status == HuntStatus.COMPLETE
        assert result.total_variants == 6
        assert result.variants_computed == 6
        assert result.variants_skipped == 0
        assert len(result.rows) == 6

    def test_grid_order_declared(
        self, executor: HuntExecutor, simple_hypothesis: Hypothesis
    ) -> None:
        """Grid order is declared."""
        result = executor.execute(simple_hypothesis)

        assert result.grid_order_declaration
        assert "cartesian_product" in result.grid_order_declaration

    def test_no_selection(
        self, executor: HuntExecutor, simple_hypothesis: Hypothesis
    ) -> None:
        """No 'top_variants', 'survivors', etc."""
        result = executor.execute(simple_hypothesis)

        # These fields should not exist
        assert not hasattr(result, "top_variants")
        assert not hasattr(result, "survivors")
        assert not hasattr(result, "best_variant")


class TestAbortBehavior:
    def test_abort_includes_watermark(
        self, executor: HuntExecutor, simple_hypothesis: Hypothesis
    ) -> None:
        """Aborted results include completeness_mask."""
        result = executor.execute(simple_hypothesis, abort_at=3)

        assert result.status == HuntStatus.ABORTED
        assert result.abort_metadata is not None
        assert "ABORTED" in result.abort_metadata.abort_notice
        assert "NO INTERPRETATION" in result.abort_metadata.abort_notice
        assert result.abort_metadata.completeness_mask is not None

    def test_partial_results_count(
        self, executor: HuntExecutor, simple_hypothesis: Hypothesis
    ) -> None:
        """Partial results match abort point."""
        result = executor.execute(simple_hypothesis, abort_at=3)

        assert result.variants_computed == 3
        assert result.variants_skipped == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
