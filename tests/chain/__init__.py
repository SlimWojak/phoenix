"""
Chain Validation Tests — S40 Prerequisites
==========================================

Proves S35-S39 modules work TOGETHER, not just in isolation.
Watches for warm ranking leakage at integration seams.

FLOWS TESTED:
  1. CFP → WalkForward → MonteCarlo
  2. Hunt → Backtest → WalkForward → CostCurve
  3. CLAIM → CFP → FACT → Conflict
  4. CSO → Hunt → Grid

CHAOS VECTORS:
  1. Mid-chain decay nuke
  2. Provenance depth 10
  3. Regime mutation mid-hunt
  4. Score resurrection at seam
  5. Order confusion injection

INVARIANTS:
  - INV-CROSS-MODULE-NO-SYNTH: No synthesized scores at seams
  - INV-ATTR-PROVENANCE: Provenance intact through chain
  - INV-SCALAR-BAN: Scalar ban enforced at every seam
"""

__version__ = "1.0.0"
__status__ = "S40_CHAIN_VALIDATION"
