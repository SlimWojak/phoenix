"""
Phoenix CSO — Chief Strategy Officer

Olya's methodology encoded as machine-readable invariants.
Inherits GovernanceInterface, drinks from River.

VERSION: 0.2 (S27 scaffold)
STATUS: PASSIVE_ONLY

S27 CONSTRAINTS:
- OBSERVE only (no execution writes)
- DRAFT beads only
- READ from River + intake

BLOCKED_UNTIL: Olya calibration session
"""

from .beads import (
    Bead,
    BeadFactory,
    BeadStatus,
    BeadStatusViolation,
    BeadType,
    ImmutabilityViolation,
)
from .contract import CSOContract
from .knowledge import KnowledgeEntry, KnowledgeStore
from .observer import CSOObserver, CSOWriteViolation

__all__ = [
    "CSOContract",
    "CSOObserver",
    "CSOWriteViolation",
    "Bead",
    "BeadFactory",
    "BeadStatus",
    "BeadType",
    "ImmutabilityViolation",
    "BeadStatusViolation",
    "KnowledgeStore",
    "KnowledgeEntry",
]

__version__ = "0.2.0"
