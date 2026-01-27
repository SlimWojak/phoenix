# BUNNY REPORT S32 — Execution Path

**Sprint:** S32_EXECUTION_PATH  
**Date:** 2026-01-27  
**Status:** **17/17 PASS**  
**Verdict:** **PASS**

---

## Summary

All 17 chaos vectors passed, proving capital-tier resilience for the S32 execution path components.

| Wave | Vectors | Pass | Fail |
|------|---------|------|------|
| Wave 1: Token Security | 4 | 4 | 0 |
| Wave 2: IBKR Chaos | 2 | 2 | 0 |
| Wave 3: Lifecycle | 4 | 4 | 0 |
| Wave 4: Reconciliation | 2 | 2 | 0 |
| Wave 5: Promotion | 4 | 4 | 0 |
| Wave 6: Stale Gate | 1 | 1 | 0 |
| **TOTAL** | **17** | **17** | **0** |

---

## Wave 1: Token Security

| Vector | Invariant | Inject | Expected | Actual | Verdict |
|--------|-----------|--------|----------|--------|---------|
| CV_TOKEN_SINGLE_USE | INV-T2-TOKEN-1 | Use token twice | ALREADY_USED rejection | ALREADY_USED | **PASS** |
| CV_TOKEN_EXPIRY | INV-T2-TOKEN-1 | Backdate expiry | EXPIRED rejection | EXPIRED | **PASS** |
| CV_TOKEN_INTENT_BIND | INV-T2-TOKEN-1 | Wrong intent_id | INTENT_MISMATCH rejection | INTENT_MISMATCH | **PASS** |
| CV_T2_GATE_BYPASS | INV-T2-GATE-1 | Order with token_id=None | Order rejected | REJECTED | **PASS** |

---

## Wave 2: IBKR Chaos

| Vector | Invariant | Inject | Expected | Actual | Verdict |
|--------|-----------|--------|----------|--------|---------|
| CV_IBKR_CHAOS_REJECT | INV-IBKR-MOCK-1 | ADVERSARIAL mode | Some rejections | Handled | **PASS** |
| CV_IBKR_CHAOS_PARTIAL | INV-IBKR-MOCK-1 | ADVERSARIAL mode | Partial fills | 0 < ratio < 1 | **PASS** |

---

## Wave 3: Lifecycle

| Vector | Invariant | Inject | Expected | Actual | Verdict |
|--------|-----------|--------|----------|--------|---------|
| CV_POSITION_SM_INVALID | INV-POSITION-SM-1 | PROPOSED → FILLED | TransitionError | TransitionError | **PASS** |
| CV_POSITION_BEAD_EMIT | INV-POSITION-AUDIT-1 | 3 transitions | 3 beads emitted | 3 beads | **PASS** |
| CV_SUBMITTED_TIMEOUT | INV-POSITION-SUBMITTED-TTL-1 | 65s in SUBMITTED | STALLED | STALLED | **PASS** |
| CV_STALLED_NO_RETRY | WP_C1 | Check STALLED exits | Only FILLED/CANCELLED | 2 exits | **PASS** |

---

## Wave 4: Reconciliation

| Vector | Invariant | Inject | Expected | Actual | Verdict |
|--------|-----------|--------|----------|--------|---------|
| CV_RECONCILE_READONLY | INV-RECONCILE-READONLY-1, WP_C2 | Create + resolve drift | State unchanged | MANAGED unchanged | **PASS** |
| CV_RECONCILE_PARTIAL | WP_C3 | 75% vs 80% fill | Drift detected | PARTIAL_FILL drift | **PASS** |

---

## Wave 5: Promotion

| Vector | Invariant | Inject | Expected | Actual | Verdict |
|--------|-----------|--------|----------|--------|---------|
| CV_PROMOTION_KILL_BLOCK | INV-PROMOTION-SAFE-1, WP_D1 | Active kill flag | Promotion blocked | BLOCKED | **PASS** |
| CV_PROMOTION_STALLED_BLOCK | WP_D1 | 2 STALLED positions | Promotion blocked | BLOCKED | **PASS** |
| CV_PROMOTION_DRIFT_BLOCK | INV-PROMOTION-SAFE-2, WP_D1 | Unresolved drift | Promotion blocked | BLOCKED | **PASS** |
| CV_PROMOTION_ONEWAY | WP_D2 | Complete promotion | No demotion path | No demote() | **PASS** |

---

## Wave 6: Stale Gate

| Vector | Invariant | Inject | Expected | Actual | Verdict |
|--------|-----------|--------|----------|--------|---------|
| CV_STALE_KILL_GATE | INV-STALE-KILL-1 | 20min old anchor | Temp kill + STATE_CONFLICT | Kill emitted | **PASS** |

---

## Invariants Proven

| ID | Statement | Proven By |
|----|-----------|-----------|
| INV-T2-TOKEN-1 | Single-use, 5-min expiry | CV_TOKEN_SINGLE_USE, CV_TOKEN_EXPIRY, CV_TOKEN_INTENT_BIND |
| INV-T2-GATE-1 | No order without token | CV_T2_GATE_BYPASS |
| INV-T2-TOKEN-AUDIT-1 | Bead at every token state | Wiring verified |
| INV-IBKR-MOCK-1 | All tests use mock | CV_IBKR_CHAOS_* |
| INV-POSITION-SM-1 | Only valid transitions | CV_POSITION_SM_INVALID |
| INV-POSITION-AUDIT-1 | Bead at every transition | CV_POSITION_BEAD_EMIT |
| INV-POSITION-SUBMITTED-TTL-1 | 60s timeout → STALLED | CV_SUBMITTED_TIMEOUT |
| INV-RECONCILE-READONLY-1 | Never mutates state | CV_RECONCILE_READONLY |
| INV-RECONCILE-ALERT-1 | Drift triggers alert | Wiring verified |
| INV-RECONCILE-AUDIT-1 | DRIFT bead on detection | Wiring verified |
| INV-RECONCILE-AUDIT-2 | RESOLUTION bead on resolve | Wiring verified |
| INV-PROMOTION-EVIDENCE-1 | Evidence bundle required | Ceremony flow verified |
| INV-PROMOTION-T2-1 | T2 approval required | Ceremony flow verified |
| INV-PROMOTION-SAFE-1 | Block if kill flags | CV_PROMOTION_KILL_BLOCK |
| INV-PROMOTION-SAFE-2 | Block if drift | CV_PROMOTION_DRIFT_BLOCK |
| INV-STALE-KILL-1 | >15min → STATE_CONFLICT | CV_STALE_KILL_GATE |

---

## Watchpoints Verified

| ID | Requirement | Verified |
|----|-------------|----------|
| WP_C1 | STALLED with alert + bead + reason, no auto-retry | CV_STALLED_NO_RETRY |
| WP_C2 | Reconciler NEVER mutates state | CV_RECONCILE_READONLY |
| WP_C3 | partial_fill_ratio drift detection | CV_RECONCILE_PARTIAL |
| WP_D1 | Hard blocks (kill, STALLED, drift) | CV_PROMOTION_*_BLOCK |
| WP_D2 | Promotion is ONE-WAY | CV_PROMOTION_ONEWAY |

---

## Execution

```
$ pytest tests/chaos/test_bunny_s32.py -v
============================= test session starts ==============================
collected 17 items

tests/chaos/test_bunny_s32.py::TestWave1TokenSecurity::test_cv_token_single_use PASSED
tests/chaos/test_bunny_s32.py::TestWave1TokenSecurity::test_cv_token_expiry PASSED
tests/chaos/test_bunny_s32.py::TestWave1TokenSecurity::test_cv_token_intent_bind PASSED
tests/chaos/test_bunny_s32.py::TestWave1TokenSecurity::test_cv_t2_gate_bypass PASSED
tests/chaos/test_bunny_s32.py::TestWave2IBKRChaos::test_cv_ibkr_chaos_reject PASSED
tests/chaos/test_bunny_s32.py::TestWave2IBKRChaos::test_cv_ibkr_chaos_partial PASSED
tests/chaos/test_bunny_s32.py::TestWave3Lifecycle::test_cv_position_sm_invalid PASSED
tests/chaos/test_bunny_s32.py::TestWave3Lifecycle::test_cv_position_bead_emit PASSED
tests/chaos/test_bunny_s32.py::TestWave3Lifecycle::test_cv_submitted_timeout PASSED
tests/chaos/test_bunny_s32.py::TestWave3Lifecycle::test_cv_stalled_no_retry PASSED
tests/chaos/test_bunny_s32.py::TestWave4Reconciliation::test_cv_reconcile_readonly PASSED
tests/chaos/test_bunny_s32.py::TestWave4Reconciliation::test_cv_reconcile_partial PASSED
tests/chaos/test_bunny_s32.py::TestWave5Promotion::test_cv_promotion_kill_block PASSED
tests/chaos/test_bunny_s32.py::TestWave5Promotion::test_cv_promotion_stalled_block PASSED
tests/chaos/test_bunny_s32.py::TestWave5Promotion::test_cv_promotion_drift_block PASSED
tests/chaos/test_bunny_s32.py::TestWave5Promotion::test_cv_promotion_oneway PASSED
tests/chaos/test_bunny_s32.py::TestWave6StaleGate::test_cv_stale_kill_gate PASSED

============================== 17 passed in 0.26s ==============================
```

---

## Conclusion

**S32 EXECUTION PATH: COMPLETE**

All 17 chaos vectors pass. The execution path is proven resilient:

- T2 workflow enforces human sovereignty over capital
- IBKR connector handles chaos gracefully
- Position lifecycle enforces valid state machine
- Reconciliation is read-only (human resolves)
- Promotion blocks on kill flags, STALLED, drift
- Stale gate prevents execution with outdated context

**S33 (First Blood) is now unlocked.**

---

*Report generated: 2026-01-27*  
*BUNNY philosophy: Every invariant must have attack vector.*
