"""
Self-Healing Tests — S40 Track A
================================

Tests for circuit breaker, backoff, and health FSM.

INVARIANTS:
  - INV-CIRCUIT-1: OPEN circuit blocks requests
  - INV-CIRCUIT-2: HALF_OPEN allows exactly 1 probe
  - INV-BACKOFF-1: Interval doubles each attempt
  - INV-BACKOFF-2: Interval capped at max
  - INV-HEALTH-1: CRITICAL → alert within 30s
  - INV-HEALTH-2: HALTED → halt_local() invoked
  - INV-HEAL-REENTRANCY: N failures → 1 alert
"""
