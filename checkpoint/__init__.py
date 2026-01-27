"""
Phoenix Checkpoint Module
=========================

Session state management with two-phase commit.

Components:
- Checkpoint: Two-phase commit for atomic state transitions
- SessionManager: Session lifecycle management
- MomentumExtractor: Extract learnings from session

INVARIANTS:
- INV-CHKPT-ATOMIC-1: State transitions are atomic (commit or rollback)
- INV-CHKPT-BEAD-1: Every checkpoint emits CONTEXT_SNAPSHOT bead
- INV-CHKPT-AUDIT-1: All checkpoints have audit trail
"""

from .checkpoint import Checkpoint, CheckpointError, CheckpointState
from .momentum_extractor import Momentum, MomentumExtractor
from .session_manager import Session, SessionManager

__all__ = [
    "Checkpoint",
    "CheckpointError",
    "CheckpointState",
    "SessionManager",
    "Session",
    "MomentumExtractor",
    "Momentum",
]
