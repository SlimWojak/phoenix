"""
Phoenix Shadow Module
======================

Paper trading scaffold — CSE consumer + position tracking.

Components:
- Shadow: Main shadow trading engine
- PaperPosition: Paper position management
- Divergence: Track paper vs live divergence

INVARIANTS:
- INV-SHADOW-ISO-1: Shadow positions NEVER affect live capital
- INV-SHADOW-CSE-1: Only consumes validated CSE signals
- INV-SHADOW-BEAD-1: Emits PERFORMANCE beads for tracking
"""

from .paper_position import PaperPosition, PositionResult, PositionState
from .shadow import Shadow, ShadowConfig, ShadowResult

__all__ = [
    "Shadow",
    "ShadowConfig",
    "ShadowResult",
    "PaperPosition",
    "PositionState",
    "PositionResult",
]
