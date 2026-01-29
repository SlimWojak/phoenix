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

__version__ = "0.1.0"
__status__ = "S35_DAY1"

# Public interface (populated as tracks complete)
__all__ = [
    # Track A
    "LensQuery",
    "LensQueryValidator",
    # Track B
    # "CFPExecutor",
    # Track C
    # "CFPResult",
    # Track D
    # "CausalBanLinter",
    # Track E
    # "ConflictDisplay",
]

# Track A imports (Day 1-2)
from cfp.validation import LensQuery, LensQueryValidator
