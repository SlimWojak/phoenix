"""
Hunt Queue — S38 Track B
========================

Queue of human-approved hypotheses. FIFO default, random opt-in.
Only approved hypotheses can be queued.

INVARIANTS:
  - INV-NO-UNSOLICITED: No auto-queue
  - INV-QUEUE-SHUFFLE: Random dequeue opt-in
"""

from __future__ import annotations

import secrets
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from hunt.hypothesis import (
    Hypothesis,
    HypothesisValidator,
)


# =============================================================================
# ENUMS
# =============================================================================


class DequeueMode(str, Enum):
    """Dequeue mode."""

    FIFO = "FIFO"  # Default — First In, First Out
    RANDOM = "RANDOM"  # T2 opt-in — Random selection


class QueueEntryStatus(str, Enum):
    """Status of queue entry."""

    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class QueueError(Exception):
    """Base queue exception."""

    pass


class ApprovalRequiredError(QueueError):
    """Hypothesis not approved."""

    pass


class PriorityForbiddenError(QueueError):
    """Priority operations forbidden."""

    pass


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class QueueEntry:
    """Entry in the hunt queue."""

    queue_id: str
    hypothesis: Hypothesis
    enqueued_at: datetime
    status: QueueEntryStatus = QueueEntryStatus.PENDING

    # NO priority field — forbidden


# =============================================================================
# HUNT QUEUE
# =============================================================================


class HuntQueue:
    """
    Queue of human-approved hypotheses.

    FIFO by default. Random selection opt-in (T2).
    Only approved hypotheses can be queued.

    INVARIANTS:
      - INV-NO-UNSOLICITED: No auto-queue
      - INV-QUEUE-SHUFFLE: Random dequeue opt-in

    FORBIDDEN:
      - sort_by_priority()
      - auto_enqueue()
      - suggest_next()
      - reorder_by_potential()
      - priority_insert()
    """

    def __init__(self) -> None:
        """Initialize queue."""
        self._queue: deque[QueueEntry] = deque()
        self._completed: list[QueueEntry] = []
        self._validator = HypothesisValidator()

    def enqueue(self, hypothesis: Hypothesis) -> str:
        """
        Enqueue a hypothesis.

        Only approved hypotheses can be queued.

        Args:
            hypothesis: Hypothesis to enqueue

        Returns:
            queue_id

        Raises:
            ApprovalRequiredError: If not approved
        """
        # Validate approval
        approval_result = self._validator.validate_approval(hypothesis)
        if not approval_result.valid:
            raise ApprovalRequiredError(
                "Hypothesis must be approved before enqueueing. "
                f"Errors: {approval_result.errors}"
            )

        # Create queue entry
        entry = QueueEntry(
            queue_id=f"Q_{uuid.uuid4().hex[:12]}",
            hypothesis=hypothesis,
            enqueued_at=datetime.now(UTC),
        )

        self._queue.append(entry)
        return entry.queue_id

    def dequeue(self, mode: DequeueMode = DequeueMode.FIFO) -> Hypothesis | None:
        """
        Dequeue next hypothesis.

        Args:
            mode: FIFO (default) or RANDOM (T2 opt-in)

        Returns:
            Next hypothesis or None if empty
        """
        pending = [e for e in self._queue if e.status == QueueEntryStatus.PENDING]
        if not pending:
            return None

        if mode == DequeueMode.FIFO:
            # First pending entry
            entry = pending[0]
        else:
            # Random selection (INV-QUEUE-SHUFFLE)
            rng = secrets.SystemRandom()
            entry = rng.choice(pending)

        entry.status = QueueEntryStatus.EXECUTING
        return entry.hypothesis

    def peek(self, shuffle: bool = False) -> list[Hypothesis]:
        """
        View pending hypotheses.

        Args:
            shuffle: If True, return in random order

        Returns:
            List of pending hypotheses
        """
        pending = [
            e.hypothesis for e in self._queue
            if e.status == QueueEntryStatus.PENDING
        ]

        if shuffle:
            rng = secrets.SystemRandom()
            rng.shuffle(pending)

        return pending

    def remove(self, hypothesis_id: str) -> bool:
        """
        Remove hypothesis from queue.

        Args:
            hypothesis_id: Hypothesis ID to remove

        Returns:
            True if removed
        """
        for entry in self._queue:
            if entry.hypothesis.hypothesis_id == hypothesis_id:
                if entry.status == QueueEntryStatus.PENDING:
                    self._queue.remove(entry)
                    return True
        return False

    def get_pending(self) -> list[Hypothesis]:
        """Get all pending hypotheses."""
        return [
            e.hypothesis for e in self._queue
            if e.status == QueueEntryStatus.PENDING
        ]

    def get_completed(self) -> list[Hypothesis]:
        """Get all completed hypotheses."""
        return [e.hypothesis for e in self._completed]

    def mark_completed(self, hypothesis_id: str) -> bool:
        """
        Mark hypothesis as completed.

        Args:
            hypothesis_id: Hypothesis ID

        Returns:
            True if marked
        """
        for entry in self._queue:
            if entry.hypothesis.hypothesis_id == hypothesis_id:
                entry.status = QueueEntryStatus.COMPLETED
                self._completed.append(entry)
                self._queue.remove(entry)
                return True
        return False

    def mark_aborted(self, hypothesis_id: str) -> bool:
        """
        Mark hypothesis as aborted.

        Args:
            hypothesis_id: Hypothesis ID

        Returns:
            True if marked
        """
        for entry in self._queue:
            if entry.hypothesis.hypothesis_id == hypothesis_id:
                entry.status = QueueEntryStatus.ABORTED
                self._completed.append(entry)
                self._queue.remove(entry)
                return True
        return False

    # =========================================================================
    # FORBIDDEN OPERATIONS
    # =========================================================================

    def sort_by_priority(self) -> None:
        """FORBIDDEN — No priority sorting."""
        raise PriorityForbiddenError(
            "sort_by_priority() is forbidden. Queue is FIFO."
        )

    def auto_enqueue(self, hypothesis: Hypothesis) -> None:
        """FORBIDDEN — No auto-enqueue."""
        raise PriorityForbiddenError(
            "auto_enqueue() is forbidden. INV-NO-UNSOLICITED."
        )

    def suggest_next(self) -> None:
        """FORBIDDEN — No suggestion."""
        raise PriorityForbiddenError(
            "suggest_next() is forbidden. INV-NO-UNSOLICITED."
        )

    def reorder_by_potential(self) -> None:
        """FORBIDDEN — No reordering."""
        raise PriorityForbiddenError(
            "reorder_by_potential() is forbidden. Queue is FIFO."
        )

    def priority_insert(self, hypothesis: Hypothesis) -> None:
        """FORBIDDEN — No priority insertion."""
        raise PriorityForbiddenError(
            "priority_insert() is forbidden. Queue is FIFO."
        )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "HuntQueue",
    "QueueEntry",
    "QueueEntryStatus",
    "DequeueMode",
    "QueueError",
    "ApprovalRequiredError",
    "PriorityForbiddenError",
]
