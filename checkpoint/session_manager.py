"""
Session Manager — Session Lifecycle Management
===============================================

Manages trading session lifecycle with checkpoints.

DESIGN:
- Session start: Initialize state, emit START checkpoint
- During session: Track hunts, update hypothesis, checkpoint on changes
- Session end: Extract momentum, emit END checkpoint

INVARIANTS:
- INV-SESS-SINGLE-1: Only one active session per manager
- INV-SESS-CHKPT-1: Session transitions emit checkpoints
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .checkpoint import (
    Checkpoint,
    CheckpointResult,
    ContextSnapshot,
    TransitionType,
)

# =============================================================================
# ENUMS
# =============================================================================


class SessionState(str, Enum):
    """Session lifecycle states."""

    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Session:
    """Active trading session."""

    session_id: str
    started_at: datetime
    state: SessionState

    # Current state
    current_hypothesis: str
    active_hunts: list[str] = field(default_factory=list)
    regime_state: dict[str, Any] = field(default_factory=dict)

    # Tracking
    checkpoints: list[str] = field(default_factory=list)  # Checkpoint IDs
    momentum_notes: list[str] = field(default_factory=list)

    # Metrics
    confidence: float = 0.5  # 0.0 to 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "state": self.state.value,
            "current_hypothesis": self.current_hypothesis,
            "active_hunts": self.active_hunts,
            "regime_state": self.regime_state,
            "checkpoints": self.checkpoints,
            "momentum_notes": self.momentum_notes,
            "confidence": self.confidence,
        }


# =============================================================================
# SESSION MANAGER
# =============================================================================


class SessionManager:
    """
    Manages trading session lifecycle.

    INVARIANT: INV-SESS-SINGLE-1 — Only one active session
    """

    def __init__(self, bead_store: Any | None = None) -> None:
        """
        Initialize session manager.

        Args:
            bead_store: BeadStore for checkpoint beads
        """
        self._bead_store = bead_store
        self._current_session: Session | None = None
        self._session_history: list[str] = []  # Past session IDs

    @property
    def current_session(self) -> Session | None:
        """Get current session."""
        return self._current_session

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return (
            self._current_session is not None
            and self._current_session.state == SessionState.ACTIVE
        )

    def start_session(
        self,
        initial_hypothesis: str,
        regime_state: dict[str, Any] | None = None,
    ) -> tuple[Session, CheckpointResult]:
        """
        Start new trading session.

        INVARIANT: INV-SESS-SINGLE-1 — Fails if session already active

        Args:
            initial_hypothesis: Starting hypothesis
            regime_state: Initial regime state

        Returns:
            (Session, CheckpointResult) tuple

        Raises:
            ValueError: If session already active
        """
        if self.is_active:
            raise ValueError(
                "Cannot start session: session already active (INV-SESS-SINGLE-1)"
            )

        # Create session
        session_id = f"SESS-{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC)

        session = Session(
            session_id=session_id,
            started_at=now,
            state=SessionState.ACTIVE,
            current_hypothesis=initial_hypothesis,
            regime_state=regime_state or {},
        )

        # Create START checkpoint
        snapshot = ContextSnapshot(
            session_id=session_id,
            timestamp_utc=now,
            transition_type=TransitionType.SESSION_START,
            current_hypothesis=initial_hypothesis,
            active_hunts=[],
            regime_state=regime_state or {},
            momentum_summary="Session started",
            confidence_delta=0.0,
            notes=f"Initial hypothesis: {initial_hypothesis}",
        )

        checkpoint = Checkpoint(self._bead_store)
        checkpoint.prepare(snapshot)
        result = checkpoint.commit()

        # Track checkpoint
        session.checkpoints.append(result.checkpoint_id)

        self._current_session = session
        return session, result

    def update_hypothesis(
        self,
        new_hypothesis: str,
        confidence_delta: float = 0.0,
        notes: str = "",
    ) -> CheckpointResult:
        """
        Update current hypothesis.

        Args:
            new_hypothesis: New hypothesis text
            confidence_delta: Change in confidence (-1.0 to 1.0)
            notes: Optional notes

        Returns:
            CheckpointResult

        Raises:
            ValueError: If no active session
        """
        if not self.is_active or self._current_session is None:
            raise ValueError("No active session")

        session = self._current_session
        old_hypothesis = session.current_hypothesis

        # Update session
        session.current_hypothesis = new_hypothesis
        session.confidence = max(0.0, min(1.0, session.confidence + confidence_delta))
        session.momentum_notes.append(f"Hypothesis: {old_hypothesis} → {new_hypothesis}")

        # Create HYPOTHESIS_UPDATE checkpoint
        snapshot = ContextSnapshot(
            session_id=session.session_id,
            timestamp_utc=datetime.now(UTC),
            transition_type=TransitionType.HYPOTHESIS_UPDATE,
            current_hypothesis=new_hypothesis,
            active_hunts=session.active_hunts,
            regime_state=session.regime_state,
            momentum_summary=f"Refined: {old_hypothesis[:30]} → {new_hypothesis[:30]}",
            confidence_delta=confidence_delta,
            previous_checkpoint_id=session.checkpoints[-1] if session.checkpoints else None,
            notes=notes,
        )

        checkpoint = Checkpoint(self._bead_store)
        checkpoint.prepare(snapshot)
        result = checkpoint.commit()

        session.checkpoints.append(result.checkpoint_id)
        return result

    def record_hunt(
        self,
        hunt_bead_id: str,
        survivors: int,
        notes: str = "",
    ) -> CheckpointResult:
        """
        Record completed hunt.

        Args:
            hunt_bead_id: HUNT bead ID
            survivors: Number of survivors
            notes: Optional notes

        Returns:
            CheckpointResult

        Raises:
            ValueError: If no active session
        """
        if not self.is_active or self._current_session is None:
            raise ValueError("No active session")

        session = self._current_session

        # Update session
        session.active_hunts.append(hunt_bead_id)
        confidence_delta = 0.1 if survivors > 0 else -0.05
        session.confidence = max(0.0, min(1.0, session.confidence + confidence_delta))
        session.momentum_notes.append(f"Hunt {hunt_bead_id}: {survivors} survivors")

        # Create HUNT_COMPLETE checkpoint
        snapshot = ContextSnapshot(
            session_id=session.session_id,
            timestamp_utc=datetime.now(UTC),
            transition_type=TransitionType.HUNT_COMPLETE,
            current_hypothesis=session.current_hypothesis,
            active_hunts=session.active_hunts,
            regime_state=session.regime_state,
            momentum_summary=f"Hunt complete: {survivors} survivors",
            confidence_delta=confidence_delta,
            previous_checkpoint_id=session.checkpoints[-1] if session.checkpoints else None,
            notes=notes or f"Hunt {hunt_bead_id}",
        )

        checkpoint = Checkpoint(self._bead_store)
        checkpoint.prepare(snapshot)
        result = checkpoint.commit()

        session.checkpoints.append(result.checkpoint_id)
        return result

    def end_session(self, final_notes: str = "") -> tuple[Session, CheckpointResult]:
        """
        End current session.

        Args:
            final_notes: Final session notes

        Returns:
            (Session, CheckpointResult) tuple

        Raises:
            ValueError: If no active session
        """
        if not self.is_active or self._current_session is None:
            raise ValueError("No active session")

        session = self._current_session

        # Build momentum summary
        momentum_summary = self._build_momentum_summary(session)

        # Create SESSION_END checkpoint
        snapshot = ContextSnapshot(
            session_id=session.session_id,
            timestamp_utc=datetime.now(UTC),
            transition_type=TransitionType.SESSION_END,
            current_hypothesis=session.current_hypothesis,
            active_hunts=session.active_hunts,
            regime_state=session.regime_state,
            momentum_summary=momentum_summary,
            confidence_delta=0.0,
            previous_checkpoint_id=session.checkpoints[-1] if session.checkpoints else None,
            notes=final_notes,
        )

        checkpoint = Checkpoint(self._bead_store)
        checkpoint.prepare(snapshot)
        result = checkpoint.commit()

        session.checkpoints.append(result.checkpoint_id)

        # Mark session as ended
        session.state = SessionState.ENDED
        self._session_history.append(session.session_id)
        self._current_session = None

        return session, result

    def _build_momentum_summary(self, session: Session) -> str:
        """Build momentum summary for session."""
        lines = [
            f"Session {session.session_id}",
            f"Duration: {session.started_at.isoformat()} to {datetime.now(UTC).isoformat()}",
            f"Hunts: {len(session.active_hunts)}",
            f"Checkpoints: {len(session.checkpoints)}",
            f"Final confidence: {session.confidence:.2f}",
            "",
            "Key learnings:",
        ]

        for note in session.momentum_notes[-5:]:  # Last 5 notes
            lines.append(f"  - {note}")

        return "\n".join(lines)
