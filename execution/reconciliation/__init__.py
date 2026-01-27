"""
Reconciliation — Phoenix/Broker state sync
==========================================

S32: EXECUTION_PATH

Read-only reconciliation between Phoenix state and broker reality.

INVARIANTS:
- INV-RECONCILE-READONLY-1: NEVER mutates lifecycle state
- INV-RECONCILE-ALERT-1: Drift triggers immediate alert
- INV-RECONCILE-AUDIT-1: RECONCILIATION_DRIFT bead on detection

WATCHPOINTS:
- WP_C2: Reconciler NEVER mutates state
- WP_C3: partial_fill_ratio drift detection
"""

from .drift import DriftRecord, DriftSeverity, DriftType
from .reconciler import Reconciler

__all__ = [
    "Reconciler",
    "DriftType",
    "DriftSeverity",
    "DriftRecord",
]
