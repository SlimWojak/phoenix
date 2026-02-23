"""
Queue Tests — S38 Track B
=========================

INVARIANTS PROVEN:
  - INV-NO-UNSOLICITED: No auto-queue
  - INV-QUEUE-SHUFFLE: Random dequeue opt-in

EXIT GATE B:
  Criterion: "Queue accepts approved only; FIFO default; shuffle opt-in"
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

from hunt.hypothesis import (
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisFraming,
)
from hunt.queue import (
    ApprovalRequiredError,
    DequeueMode,
    HuntQueue,
    PriorityForbiddenError,
)


@pytest.fixture
def queue() -> HuntQueue:
    return HuntQueue()


@pytest.fixture
def approved_hypothesis() -> Hypothesis:
    return Hypothesis(
        framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
        metrics=["sharpe"],
        budget=HypothesisBudget(max_variants=10),
        approval=HypothesisApproval(
            approved=True,
            approved_by="Olya",
            approved_at=datetime.now(UTC),
        ),
    )


class TestQueueBasics:
    def test_enqueue_approved(
        self, queue: HuntQueue, approved_hypothesis: Hypothesis
    ) -> None:
        queue_id = queue.enqueue(approved_hypothesis)
        assert queue_id.startswith("Q_")

    def test_enqueue_unapproved_rejected(self, queue: HuntQueue) -> None:
        hypothesis = Hypothesis(
            framing=HypothesisFraming(question="Test?", source="Olya", domain="test"),
            metrics=["sharpe"],
            budget=HypothesisBudget(max_variants=10),
            approval=HypothesisApproval(approved=False),
        )
        with pytest.raises(ApprovalRequiredError):
            queue.enqueue(hypothesis)

    def test_dequeue_fifo(self, queue: HuntQueue) -> None:
        for i in range(3):
            h = Hypothesis(
                hypothesis_id=f"H_{i}",
                framing=HypothesisFraming(question=f"Q{i}?", source="Olya", domain="test"),
                metrics=["sharpe"],
                budget=HypothesisBudget(max_variants=10),
                approval=HypothesisApproval(
                    approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
                ),
            )
            queue.enqueue(h)

        first = queue.dequeue(DequeueMode.FIFO)
        assert first is not None
        assert first.hypothesis_id == "H_0"

    def test_dequeue_random(self, queue: HuntQueue) -> None:
        for i in range(10):
            h = Hypothesis(
                hypothesis_id=f"H_{i}",
                framing=HypothesisFraming(question=f"Q{i}?", source="Olya", domain="test"),
                metrics=["sharpe"],
                budget=HypothesisBudget(max_variants=10),
                approval=HypothesisApproval(
                    approved=True, approved_by="Olya", approved_at=datetime.now(UTC)
                ),
            )
            queue.enqueue(h)

        # Random mode should return something (not testing order)
        result = queue.dequeue(DequeueMode.RANDOM)
        assert result is not None


class TestForbiddenOperations:
    def test_sort_by_priority_forbidden(self, queue: HuntQueue) -> None:
        with pytest.raises(PriorityForbiddenError):
            queue.sort_by_priority()

    def test_auto_enqueue_forbidden(
        self, queue: HuntQueue, approved_hypothesis: Hypothesis
    ) -> None:
        with pytest.raises(PriorityForbiddenError):
            queue.auto_enqueue(approved_hypothesis)

    def test_suggest_next_forbidden(self, queue: HuntQueue) -> None:
        with pytest.raises(PriorityForbiddenError):
            queue.suggest_next()

    def test_priority_insert_forbidden(
        self, queue: HuntQueue, approved_hypothesis: Hypothesis
    ) -> None:
        with pytest.raises(PriorityForbiddenError):
            queue.priority_insert(approved_hypothesis)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
