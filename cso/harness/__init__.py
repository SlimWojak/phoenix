"""
CSO Harness — S36 Deliverable
=============================

5-Drawer gate evaluation without grades.
Bit vectors for machine triage. No population counting.

INVARIANTS:
  - INV-HARNESS-1: Gate status only, never grades
  - INV-HARNESS-2: No confidence scores
  - INV-HARNESS-3: Alerts on gate combinations, not quality
  - INV-HARNESS-4: Output is boolean per gate
  - INV-HARNESS-5: No downstream scalar from bit_vector
  - INV-DRAWER-RULE-EXPLICIT: Rules in conditions.yaml
  - INV-BITVECTOR-NO-POPULATION: No bit counts
  - INV-DISPLAY-SHUFFLE: Randomized display order
  - INV-CSO-BUDGET: max_pairs=12 default
"""

__version__ = "1.0.0"
__status__ = "S36_COMPLETE"

# Re-export from parent cso modules
# Note: These require direct import to avoid pandas dependency in cso/__init__.py

__all__ = [
    "__version__",
    "__status__",
]
