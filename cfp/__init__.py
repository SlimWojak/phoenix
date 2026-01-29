"""
CFP — Conditional Fact Projector
================================

S35 DELIVERABLE
Theme: "Where/when does performance concentrate?"

The microscope that shows WHERE performance lives
without claiming WHY it lives there.

GOVERNING PRINCIPLE:
  "Human frames the question, machine computes the answer."
  Facts are projections. Meaning is human territory.

INVARIANTS ENFORCED:
  - INV-ATTR-CAUSAL-BAN: No causal claims
  - INV-ATTR-PROVENANCE: query + hash + bead_id + governance_hash
  - INV-ATTR-CONFLICT-DISPLAY: Best always paired with worst
  - INV-CFP-BUDGET-ENFORCE: Pre-execution budget check
  - INV-CFP-LOW-N-GATE: N < 30 cannot persist as FACT

PUBLIC INTERFACE:
  - LensQuery: The question schema
  - CFPResult: The answer schema (with provenance)
  - CFPExecutor: Execute queries against River/Beads
  - CausalBanLinter: Enforce no causal language
  - ConflictDisplay: Best/worst pairing

USAGE:
  from cfp import LensQuery, CFPExecutor

  query = LensQuery(
      source="river",
      group_by=["session"],
      filter={"conditions": [{"field": "pair", "op": "==", "value": "EURUSD"}]},
      aggregate={"metrics": ["sharpe", "win_rate"]},
      strategy_config_hash="abc123",
  )

  executor = CFPExecutor()
  result = executor.execute(query)
  # result.provenance.governance_hash proves INV-ATTR-CAUSAL-BAN was active
"""

__version__ = "1.0.0"
__status__ = "S35_COMPLETE"

# Public interface — S35 CFP Complete
__all__ = [
    # Track A: LENS_SCHEMA
    "LensQuery",
    "LensQueryValidator",
    "ValidationResult",
    # Track B: QUERY_EXECUTOR
    "CFPExecutor",
    "CFPResult",
    "Provenance",
    "ResultType",
    "BudgetEstimator",
    "BudgetExceededError",
    # Track C: OUTPUT_SCHEMA (in executor)
    # Track D: CAUSAL_BAN_LINTER
    "CausalBanLinter",
    "LintResult",
    # Track E: CONFLICT_DISPLAY
    "ConflictDisplay",
    "ConflictPair",
    "validate_conflict_request",
    # Track F: INTEGRATION
    "CFPAPI",
    "handle_cfp_query",
]

# Track A imports (Day 1-2)
# Track F imports (Day 6-7)
from cfp.api import CFPAPI, handle_cfp_query
from cfp.budget import BudgetEstimator, BudgetExceededError

# Track E imports (Day 5-6)
from cfp.conflict_display import ConflictDisplay, ConflictPair, validate_conflict_request

# Track B imports (Day 2-4)
from cfp.executor import CFPExecutor, CFPResult, Provenance, ResultType

# Track D imports (Day 4-5)
from cfp.linter import CausalBanLinter, LintResult
from cfp.validation import LensQuery, LensQueryValidator, ValidationResult
