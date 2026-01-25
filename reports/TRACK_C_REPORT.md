# TRACK C REPORT — ORACLE FOUNDATION

**SPRINT:** 26.TRACK_C  
**DATE:** 2026-01-25  
**OWNER:** OPUS  
**STATUS:** COMPLETE

---

## VERDICT: PASS

All exit gates satisfied. CSO foundation ready for implementation.

---

## DELIVERABLES

| File | Purpose | Status |
|------|---------|--------|
| `reports/NEX_SALVAGE_REPORT.md` | NEX component audit | ✓ |
| `docs/COLD_START_STRATEGY.md` | Bootstrap procedure | ✓ |
| `docs/VISUAL_ANCHOR_MAP.md` | ICT concept mapping | ✓ |
| `docs/CSO_DYNASTY_SPEC.md` | Persistent state spec | ✓ |
| `cso/__init__.py` | CSO package | ✓ |
| `cso/contract.py` | CSO contract skeleton | ✓ |

---

## EXIT GATE CHECKLIST

| Gate | Criterion | Status |
|------|-----------|--------|
| nex_audit | Component table complete | **PASS** |
| cold_start | warmup_bars defined | **PASS** |
| visual_anchor | ICT coverage mapped | **PASS** |
| dynasty | Persistent state defined | **PASS** |

---

## TASK 1: NEX SALVAGE AUDIT

### Summary

| Metric | Value |
|--------|-------|
| Total Components | 24 |
| Subsume Candidates | 18 (75%) |
| Requires Refactor | 4 (17%) |
| Incompatible | 2 (8%) |

### Key Findings

- **Compatible:** L1-L6, L8-L10 (pure functions)
- **Refactor Required:** L7 (DXY coupling), L11-L12 (composite)
- **Incompatible:** DXY merge, incremental runner (global state)
- **INV-CONTRACT-1:** All layers except DXY section are deterministic

### Recommendation

Phase 1: Wrap L1-L6 immediately (no changes)
Phase 2: Refactor L7-L12 (extract DXY)
Phase 3: DXY becomes separate tributary

---

## TASK 2: COLD START STRATEGY

### Warmup Requirements

| Level | Bars | Duration | Signal Quality |
|-------|------|----------|----------------|
| Minimum | 1,440 | 24h | 50% (intraday) |
| Standard | 10,080 | 7d | 100% |
| Optimal | 43,200 | 30d | Full IPDA |

### Bootstrap Sequence

1. Data Acquisition (~3 min)
2. Initial Enrichment (~6 min)
3. Reference Level Init (~30s)
4. HTF Context Build (~1 min)
5. CSO Initialization (~5s)
6. Signal Validation

**Total Bootstrap Time:** ~10-12 minutes

### Recovery Procedures

- Clean shutdown: Load persisted state (~2-3 min)
- Crash: Recompute from beads (~5-10 min)
- Data gap: Fetch + flag synthetic

---

## TASK 3: VISUAL ANCHOR MAP

### Coverage

| Category | Concepts | Machine-Readable | Coverage |
|----------|----------|------------------|----------|
| Time & Sessions | 8 | 8 | 100% |
| Reference Levels | 12 | 10 | 83% |
| Liquidity | 6 | 5 | 83% |
| Structure | 8 | 7 | 88% |
| PDAs | 10 | 9 | 90% |
| HTF Bias | 6 | 5 | 83% |
| Composite | 5 | 3 | 60% |
| **TOTAL** | **55** | **47** | **85%** |

### Critical Gaps (Human Required)

1. **Narrative/Fundamentals** — Olya provides via session
2. **Model Selection** — Rule-based selector needed
3. **Context Quality** — Confidence scoring

### Olya Interview Agenda

- Session 1: Model Selection
- Session 2: Context Quality
- Session 3: News Awareness

---

## TASK 4: DYNASTY DEFINITION

### State Classification

| Type | Survives | Storage |
|------|----------|---------|
| Persistent | Restart | Boardroom |
| Session | Process | Memory |
| Ephemeral | Compute | Stack |

### Bead Schema

```yaml
bead_type: cso_decision
fields:
  - decision_id, timestamp, symbol
  - direction, confidence
  - 4Q gate results
  - state_hash
  - outcome (filled later)
```

### Invariants

- INV-DYNASTY-1: Every decision emits bead
- INV-DYNASTY-2: state_hash verified
- INV-DYNASTY-3: Outcome resolved within 24h
- INV-DYNASTY-4: Reference state persisted daily
- INV-DYNASTY-5: Beads immutable after emit

---

## CSO CONTRACT SKELETON

### Identity

```yaml
module_id: phoenix.cso
module_tier: T1 (capital-adjacent)
writes: advisory_state
forbidden: execution_state, orders, positions
```

### Enforced Invariants

- INV-CSO-1: No signal during COLD/WARMING
- INV-CSO-2: 4Q Gate must pass for non-NEUTRAL
- INV-CSO-3: Confidence calibrated to accuracy
- INV-CSO-4: Every decision emits bead
- INV-CONTRACT-1: Deterministic

### Yield Points

- `evaluate_4q_gate`
- `compute_confidence`
- `emit_decision`

---

## BLOCKERS & ESCALATIONS

| Item | Status | Action |
|------|--------|--------|
| DXY coupling in L7 | Documented | Refactor in Phase 2 |
| Breaker blocks | Gap | Future enhancement |
| News awareness | Gap | External API (future) |
| Olya calibration | Required | Schedule session |

**No critical blockers.** CSO implementation can proceed.

---

## TRACK STATUS

```
TRACK_C: COMPLETE

CSO Foundation:
  ✓ NEX salvage mapped (75% subsumable)
  ✓ Cold start defined (10-12 min bootstrap)
  ✓ Visual anchors mapped (85% coverage)
  ✓ Dynasty spec complete (bead schema ready)
  ✓ Contract skeleton built (4Q Gate, warmup)

READY FOR:
  - Olya calibration session
  - CSO implementation (post-calibration)
  - NEX enrichment subsumption
```

---

## NEXT STEPS

1. **Olya Session:** Schedule model selection + context quality calibration
2. **Track D (Hands):** Execution skeleton (parallel with Olya)
3. **NEX Subsumption:** Begin L1-L6 wrapper implementation
4. **CSO Implementation:** After Olya calibration

---

*Generated: Sprint 26 Track C*
