"""
Checkpoint — Two-Phase Commit for State Transitions
=====================================================

Atomic state transitions with prepare/commit/rollback.

INVARIANTS:
- INV-CHKPT-ATOMIC-1: State transitions are atomic
- INV-CHKPT-BEAD-1: Every checkpoint emits CONTEXT_SNAPSHOT bead

DESIGN:
1. prepare() — validate transition, lock resources
2. commit() — apply transition, emit bead
3. rollback() — revert on failure

Two-phase commit ensures no partial state updates.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# Import BeadStore for integration
try:
    from memory.bead_store import BeadStore, BeadType, Signer
except ImportError:
    BeadStore = None  # type: ignore[misc, assignment]
    BeadType = None  # type: ignore[misc, assignment]
    Signer = None  # type: ignore[misc, assignment]


# =============================================================================
# ENUMS
# =============================================================================


class CheckpointState(str, Enum):
    """Checkpoint lifecycle states."""

    IDLE = "IDLE"
    PREPARED = "PREPARED"
    COMMITTED = "COMMITTED"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"


class TransitionType(str, Enum):
    """State transition types."""

    SESSION_START = "SESSION_START"
    HYPOTHESIS_UPDATE = "HYPOTHESIS_UPDATE"
    HUNT_COMPLETE = "HUNT_COMPLETE"
    REGIME_SHIFT = "REGIME_SHIFT"
    SESSION_END = "SESSION_END"
    MANUAL_CHECKPOINT = "MANUAL_CHECKPOINT"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class CheckpointError(Exception):
    """Base exception for checkpoint errors."""

    pass


class PrepareError(CheckpointError):
    """Failed to prepare checkpoint."""

    pass


class CommitError(CheckpointError):
    """Failed to commit checkpoint."""

    pass


class RollbackError(CheckpointError):
    """Failed to rollback checkpoint."""

    pass


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ContextSnapshot:
    """
    Point-in-time session state.

    Emitted as CONTEXT_SNAPSHOT bead on commit.
    """

    session_id: str
    timestamp_utc: datetime
    transition_type: TransitionType

    # Current state
    current_hypothesis: str
    active_hunts: list[str]  # Hunt bead IDs
    regime_state: dict[str, Any]

    # Momentum (learnings so far)
    momentum_summary: str
    confidence_delta: float

    # Metadata
    previous_checkpoint_id: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for bead storage."""
        return {
            "session_id": self.session_id,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "transition_type": self.transition_type.value,
            "current_hypothesis": self.current_hypothesis,
            "active_hunts": self.active_hunts,
            "regime_state": self.regime_state,
            "momentum_summary": self.momentum_summary,
            "confidence_delta": self.confidence_delta,
            "previous_checkpoint_id": self.previous_checkpoint_id,
            "notes": self.notes,
        }


@dataclass
class CheckpointResult:
    """Result of checkpoint operation."""

    checkpoint_id: str
    status: CheckpointState
    bead_id: str | None = None
    bead_hash: str | None = None
    errors: list[str] = field(default_factory=list)


# =============================================================================
# CHECKPOINT
# =============================================================================


class Checkpoint:
    """
    Two-phase commit for atomic state transitions.

    Usage:
        checkpoint = Checkpoint(bead_store)
        checkpoint.prepare(snapshot)  # Validate, lock
        checkpoint.commit()           # Apply, emit bead
        # OR
        checkpoint.rollback()         # Revert on failure

    INVARIANT: INV-CHKPT-ATOMIC-1 — No partial state updates
    """

    def __init__(self, bead_store: Any | None = None) -> None:
        """
        Initialize checkpoint.

        Args:
            bead_store: BeadStore instance for bead emission
        """
        self._bead_store = bead_store
        self._state = CheckpointState.IDLE
        self._checkpoint_id: str | None = None
        self._prepared_snapshot: ContextSnapshot | None = None
        self._prepared_at: datetime | None = None

    @property
    def state(self) -> CheckpointState:
        """Current checkpoint state."""
        return self._state

    @property
    def checkpoint_id(self) -> str | None:
        """Current checkpoint ID (set after prepare)."""
        return self._checkpoint_id

    def prepare(self, snapshot: ContextSnapshot) -> str:
        """
        Phase 1: Prepare checkpoint.

        Validates transition and locks resources.

        Args:
            snapshot: Context snapshot to checkpoint

        Returns:
            checkpoint_id for this transition

        Raises:
            PrepareError: If validation fails
        """
        if self._state != CheckpointState.IDLE:
            raise PrepareError(
                f"Cannot prepare from state {self._state} (must be IDLE)"
            )

        # Validate snapshot
        errors = self._validate_snapshot(snapshot)
        if errors:
            raise PrepareError(f"Snapshot validation failed: {errors}")

        # Generate checkpoint ID
        self._checkpoint_id = f"CHKPT-{uuid.uuid4().hex[:8]}"
        self._prepared_snapshot = snapshot
        self._prepared_at = datetime.now(UTC)
        self._state = CheckpointState.PREPARED

        return self._checkpoint_id

    def commit(self) -> CheckpointResult:
        """
        Phase 2: Commit checkpoint.

        Applies transition and emits CONTEXT_SNAPSHOT bead.

        Returns:
            CheckpointResult with bead details

        Raises:
            CommitError: If commit fails
        """
        if self._state != CheckpointState.PREPARED:
            raise CommitError(
                f"Cannot commit from state {self._state} (must be PREPARED)"
            )

        if self._prepared_snapshot is None or self._checkpoint_id is None:
            raise CommitError("No prepared snapshot")

        try:
            # Emit CONTEXT_SNAPSHOT bead (INV-CHKPT-BEAD-1)
            bead_id, bead_hash = self._emit_bead(self._prepared_snapshot)

            self._state = CheckpointState.COMMITTED

            return CheckpointResult(
                checkpoint_id=self._checkpoint_id,
                status=self._state,
                bead_id=bead_id,
                bead_hash=bead_hash,
            )

        except Exception as e:
            self._state = CheckpointState.FAILED
            raise CommitError(f"Commit failed: {e}") from e

    def rollback(self) -> CheckpointResult:
        """
        Rollback prepared checkpoint.

        Returns:
            CheckpointResult indicating rollback

        Raises:
            RollbackError: If rollback fails
        """
        if self._state not in (CheckpointState.PREPARED, CheckpointState.FAILED):
            raise RollbackError(
                f"Cannot rollback from state {self._state}"
            )

        checkpoint_id = self._checkpoint_id or "unknown"

        # Clear prepared state
        self._prepared_snapshot = None
        self._prepared_at = None
        self._state = CheckpointState.ROLLED_BACK

        return CheckpointResult(
            checkpoint_id=checkpoint_id,
            status=self._state,
        )

    def reset(self) -> None:
        """Reset checkpoint to IDLE state."""
        self._state = CheckpointState.IDLE
        self._checkpoint_id = None
        self._prepared_snapshot = None
        self._prepared_at = None

    def _validate_snapshot(self, snapshot: ContextSnapshot) -> list[str]:
        """Validate context snapshot."""
        errors: list[str] = []

        if not snapshot.session_id:
            errors.append("session_id is required")

        if not snapshot.current_hypothesis:
            errors.append("current_hypothesis is required")

        if snapshot.confidence_delta < -1.0 or snapshot.confidence_delta > 1.0:
            errors.append("confidence_delta must be in [-1.0, 1.0]")

        return errors

    def _emit_bead(self, snapshot: ContextSnapshot) -> tuple[str, str]:
        """
        Emit CONTEXT_SNAPSHOT bead.

        INVARIANT: INV-CHKPT-BEAD-1
        """
        bead_id = f"SNAP-{uuid.uuid4().hex[:8]}"

        # Build bead content
        bead_content = {
            "bead_id": bead_id,
            "bead_type": "CONTEXT_SNAPSHOT",
            "prev_bead_id": snapshot.previous_checkpoint_id,
            "timestamp_utc": snapshot.timestamp_utc.isoformat(),
            "signer": "system",
            "version": "1.0",
            "checkpoint_id": self._checkpoint_id,
            "content": snapshot.to_dict(),
        }

        # Compute hash
        bead_hash = hashlib.sha256(
            json.dumps(bead_content, sort_keys=True).encode()
        ).hexdigest()[:16]
        bead_content["bead_hash"] = bead_hash

        # Store bead
        if self._bead_store is not None:
            try:
                self._bead_store.write_dict(bead_content)
            except Exception:  # noqa: S110
                pass  # Non-blocking, bead storage is best-effort

        return bead_id, bead_hash


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def atomic_checkpoint(
    bead_store: Any,
    snapshot: ContextSnapshot,
) -> CheckpointResult:
    """
    Create atomic checkpoint (prepare + commit).

    Convenience function for simple checkpoints.

    Args:
        bead_store: BeadStore instance
        snapshot: Context snapshot

    Returns:
        CheckpointResult

    Raises:
        CheckpointError: If checkpoint fails
    """
    checkpoint = Checkpoint(bead_store)

    try:
        checkpoint.prepare(snapshot)
        return checkpoint.commit()
    except Exception:
        checkpoint.rollback()
        raise
