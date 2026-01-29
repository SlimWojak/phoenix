"""
Hunt — Exhaustive Computation Engine
=====================================

S38 Deliverable: Compute engine, not idea engine.
Human frames. Machine computes ALL. Human interprets.

INVARIANTS:
  - INV-HUNT-EXHAUSTIVE: Compute ALL variants, never select
  - INV-NO-UNSOLICITED: System never proposes
  - INV-HUNT-BUDGET: Compute ceiling enforced
  - INV-HUNT-METRICS-DECLARED: Metrics mandatory, no defaults
  - INV-HUNT-GRID-ORDER-DECLARED: Grid order explicit
  - INV-GRID-DIMENSION-CAP: Max 3 dimensions
  - INV-HUNT-PARTIAL-WATERMARK: Completeness on abort
  - INV-OUTPUT-SHUFFLE: Shuffle opt-in
  - INV-QUEUE-SHUFFLE: Random dequeue opt-in
  - INV-HUNT-REGIME-ANCHOR: Regime change → abort
  - INV-HUNT-DIM-CARDINALITY-CAP: Per-dim caps
"""

__version__ = "1.0.0"
__status__ = "S38_COMPLETE"

from hunt.budget import (
    BudgetCheck,
    BudgetEnforcer,
    BudgetEstimate,
    BudgetStatus,
)
from hunt.executor import (
    AbortMetadata,
    HuntExecutor,
    HuntProvenance,
    HuntResult,
    HuntStatus,
    VariantResult,
)
from hunt.grid import GridExpander, GridExpansion, Variant
from hunt.hypothesis import (
    DIMENSION_HARD_CAP,
    DIMENSION_SOFT_CAP,
    FORBIDDEN_FIELDS,
    FORBIDDEN_SOURCES,
    MAX_DIMENSIONS,
    CardinalityWarning,
    GridDimension,
    Hypothesis,
    HypothesisApproval,
    HypothesisBudget,
    HypothesisConstraints,
    HypothesisFraming,
    HypothesisGrid,
    HypothesisStatus,
    HypothesisValidator,
)
from hunt.output import (
    FORBIDDEN_OUTPUT_FIELDS,
    FORBIDDEN_SECTIONS,
    HuntOutputFormatter,
    OutputValidator,
)
from hunt.queue import (
    ApprovalRequiredError,
    DequeueMode,
    HuntQueue,
    PriorityForbiddenError,
    QueueEntry,
    QueueEntryStatus,
    QueueError,
)

__all__ = [
    # Version
    "__version__",
    "__status__",
    # Hypothesis
    "Hypothesis",
    "HypothesisGrid",
    "GridDimension",
    "HypothesisFraming",
    "HypothesisConstraints",
    "HypothesisBudget",
    "HypothesisApproval",
    "HypothesisStatus",
    "HypothesisValidator",
    "CardinalityWarning",
    # Queue
    "HuntQueue",
    "QueueEntry",
    "QueueEntryStatus",
    "DequeueMode",
    "QueueError",
    "ApprovalRequiredError",
    "PriorityForbiddenError",
    # Grid
    "GridExpander",
    "GridExpansion",
    "Variant",
    # Executor
    "HuntExecutor",
    "HuntResult",
    "HuntStatus",
    "VariantResult",
    "AbortMetadata",
    "HuntProvenance",
    # Budget
    "BudgetEnforcer",
    "BudgetEstimate",
    "BudgetCheck",
    "BudgetStatus",
    # Output
    "HuntOutputFormatter",
    "OutputValidator",
    "FORBIDDEN_OUTPUT_FIELDS",
    "FORBIDDEN_SECTIONS",
    # Constants
    "MAX_DIMENSIONS",
    "DIMENSION_SOFT_CAP",
    "DIMENSION_HARD_CAP",
    "FORBIDDEN_SOURCES",
    "FORBIDDEN_FIELDS",
]
