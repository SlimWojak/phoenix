"""
Budget Tests — S38 Track D
==========================

INVARIANTS PROVEN:
  - INV-HUNT-BUDGET: Compute ceiling enforced

EXIT GATE D:
  Criterion: "Budget enforced; exceeding ceiling → REJECT or ABORT"
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from hunt.budget import BudgetEnforcer, BudgetStatus
from hunt.hypothesis import (
    GridDimension,
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisFraming,
    HypothesisGrid,
)


@pytest.fixture
def enforcer() -> BudgetEnforcer:
    return BudgetEnforcer(max_variants=1000, max_variants_t2=10000)


class TestBudgetEnforcement:
    def test_under_budget_approved(self, enforcer: BudgetEnforcer) -> None:
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=list(range(10)))]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=100),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        check = enforcer.check_pre_execution(hypothesis)
        assert check.status == BudgetStatus.APPROVED

    def test_over_system_max_rejected(self, enforcer: BudgetEnforcer) -> None:
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=list(range(2000)))]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=2000),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        check = enforcer.check_pre_execution(hypothesis)
        assert check.status == BudgetStatus.REJECTED

    def test_over_declared_max_rejected(self, enforcer: BudgetEnforcer) -> None:
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=list(range(100)))]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=50),  # Declared less than grid
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        check = enforcer.check_pre_execution(hypothesis)
        assert check.status == BudgetStatus.REJECTED

    def test_t2_override_allows_higher(self, enforcer: BudgetEnforcer) -> None:
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            grid=HypothesisGrid(
                dimensions=[GridDimension(dimension="x", values=list(range(2000)))]
            ),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=2000),
            approval=HypothesisApproval(
                approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
            ),
        )

        check = enforcer.check_pre_execution(hypothesis, t2_override=True)
        assert check.status == BudgetStatus.APPROVED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
