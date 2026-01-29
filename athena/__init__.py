"""
Athena — Memory Discipline Module
=================================

S37 Deliverable: Memory, not myth.
Claims are queryable, not executable.
Facts have provenance. Conflicts have no resolution authority.

INVARIANTS:
  - INV-CLAIM-NO-EXECUTION: Claims cannot be predicates
  - INV-ATTR-NO-WRITEBACK: Claims cannot mutate doctrine
  - INV-NO-AUTO-SURFACE: Claims retrieved ONLY via explicit query
  - INV-ATTR-SILENCE: System does not resolve conflicts
  - INV-CONFLICT-SHUFFLE: Conflicts returned shuffled
  - INV-CONFLICT-NO-AGGREGATION: No counting/ranking
  - INV-SEMANTIC-NO-SINGLE-BEST: Unordered neighborhood
  - INV-SEMANTIC-POLARITY: Polar handling
  - INV-HISTORY-NO-BURY: Full chain always
"""

__version__ = "1.0.0"
__status__ = "S37_COMPLETE"

from athena.bead_types import (
    AthenaBeadType,
    BeadValidator,
    ClaimBead,
    ConflictBead,
    FactBead,
    FORBIDDEN_FIELDS,
)
from athena.claim_linter import ClaimLanguageLinter
from athena.conflict_detector import ConflictAggregationBan, ConflictDetector
from athena.history import ClaimEvolution, CycleDetectedError, MemoryHistory
from athena.rate_limiter import AthenaRateLimiter
from athena.semantic import SemanticQuery, SemanticSearchResponse
from athena.store import (
    AthenaStore,
    AutoSurfaceError,
    ExecutionGuardError,
    RateLimitError,
    ValidationError,
)

__all__ = [
    # Version
    "__version__",
    "__status__",
    # Bead types
    "AthenaBeadType",
    "ClaimBead",
    "FactBead",
    "ConflictBead",
    "BeadValidator",
    "FORBIDDEN_FIELDS",
    # Store
    "AthenaStore",
    "ValidationError",
    "RateLimitError",
    "ExecutionGuardError",
    "AutoSurfaceError",
    # Linter
    "ClaimLanguageLinter",
    # Conflict
    "ConflictDetector",
    "ConflictAggregationBan",
    # Semantic
    "SemanticQuery",
    "SemanticSearchResponse",
    # History
    "MemoryHistory",
    "ClaimEvolution",
    "CycleDetectedError",
    # Rate limiter
    "AthenaRateLimiter",
]
