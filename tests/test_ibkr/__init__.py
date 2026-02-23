"""
IBKR Tests — S40 Track B
========================

Tests for supervisor, heartbeat, and degradation.

INVARIANTS:
  - INV-IBKR-FLAKEY-1: 3 missed beats → DEAD
  - INV-IBKR-FLAKEY-2: Supervisor survives connector crash
  - INV-IBKR-FLAKEY-3: Reconnection requires validation
  - INV-IBKR-DEGRADE-1: T2 blocked within 1s
  - INV-IBKR-DEGRADE-2: No T2 in DEGRADED state
  - INV-SUPERVISOR-1: Supervisor death → alert
"""
