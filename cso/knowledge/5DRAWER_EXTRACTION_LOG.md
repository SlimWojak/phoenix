# 5-DRAWER EXTRACTION LOG
## Date: 2026-01-23
## Sprint: S27.5DRAWER.EXTRACTION
## Status: COMPLETE

---

## SUMMARY

| Metric | Value |
|--------|-------|
| **Drawers Created** | 5 |
| **Total Lines** | ~650 |
| **Definitions** | 24 |
| **Signals** | 40 |
| **Invariants** | 21 |
| **Prohibitions** | 8 |
| **Gaps Flagged** | 8 |
| **Conflicts** | 2 |

---

## ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│  DRAWER 1: FOUNDATION — "What ARE these concepts?"              │
│  - Definitions (MSS, FVG, OB, displacement, liquidity, IPDA)    │
│  - Invariants (INV-*) — universal rules                         │
│  - Prohibitions (PRO-*) — things we NEVER do                    │
├─────────────────────────────────────────────────────────────────┤
│  DRAWER 2: CONTEXT — "Where is the market?"                     │
│  - HTF structure (weekly/daily MSS, swings, ranges)             │
│  - Daily state (type of day, phase, classification)             │
│  - Objectives (DOL, targets, liquidity status)                  │
│  - Warmup states / state machine                                │
├─────────────────────────────────────────────────────────────────┤
│  DRAWER 3: CONDITIONS — "Is this setup valid?"                  │
│  - 3Q framework (location, objective, respect)                  │
│  - Range selection / alignment                                  │
│  - Premium/discount / confluence                                │
├─────────────────────────────────────────────────────────────────┤
│  DRAWER 4: ENTRY — "When/how to act?"                           │
│  - Timing (sessions, kill zones, day of week)                   │
│  - Triggers (sweep, displacement, LTF MSS)                      │
│  - Execution (entry price, stop placement)                      │
├─────────────────────────────────────────────────────────────────┤
│  DRAWER 5: MANAGEMENT — "How to manage the trade?"              │
│  - Targets (partials, full exit, post-expansion)                │
│  - Stops (initial, trailing, invalidation)                      │
│  - Adjustments (re-entry, scale, hold vs exit)                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## SOURCES USED

### Primary
- `docs/olya_skills/LAYER_0_HTF_CONTEXT_CLEAN.md` (2073 lines)

### Secondary (NEX)
- `LAYER_1_TIME_SESSIONS_SPEC.md` — sessions, kill zones, timing
- `LAYER_3_SWEEPS_SPEC.md` — sweep formula, liquidity pools
- `LAYER_5_MTF_FVG_SPEC.md` — FVG detection, BISI/SIBI
- `LAYER_6_DISPLACEMENT_SPEC.md` — displacement definition
- `LAYER_7_STRUCTURE_SPEC.md` — order flow, structure breaks
- `LAYER_8_PREMIUM_DISCOUNT_SPEC.md` — P/D calculation
- `LAYER_9_ORDER_BLOCKS_SPEC.md` — OB body zones, MT
- `LAYER_10_TIMING_SPEC.md` — freshness scoring
- `LAYER_11_ALIGNMENT_SPEC.md` — HTF/layer alignment
- `MMM_FRAMEWORK_SPEC.md` — MMM phases, lifecycle

---

## FILE BREAKDOWN

| File | Lines | Contents |
|------|-------|----------|
| `foundation.yaml` | ~180 | 24 definitions, 21 invariants, 8 prohibitions |
| `context.yaml` | ~150 | 17 signals, 6 warmup states, 10 principles |
| `conditions.yaml` | ~150 | 15 signals, 4 gates, 2 conflicts |
| `entry.yaml` | ~120 | Sessions, KZs, triggers, liquidity pools |
| `management.yaml` | ~100 | Targets, stops, adjustments, 6 gaps |
| `index.yaml` | ~80 | Manifest, totals, validation status |

---

## DEDUPLICATION RULES

1. **Definitions live in FOUNDATION only**
   - MSS, FVG, OB, displacement → `foundation.yaml`
   - Other drawers reference, don't redefine

2. **Signals grouped by question**
   - "Where is market?" → `context.yaml`
   - "Is setup valid?" → `conditions.yaml`
   - "When to act?" → `entry.yaml`
   - "How to manage?" → `management.yaml`

3. **Invariants all in FOUNDATION**
   - Universal rules that never change
   - Prohibitions are a special invariant type

---

## GAPS IDENTIFIED

### MANAGEMENT (Thinnest Drawer)

| Gap ID | Area | Question | Status |
|--------|------|----------|--------|
| GAP-MGMT-001 | Partial exits | What % at 1R? | requires_olya |
| GAP-MGMT-002 | Trailing stops | Trail behind what? | requires_olya |
| GAP-MGMT-003 | Re-entry | When to re-enter? | requires_olya |
| GAP-MGMT-004 | Scaling | Scale in/out rules? | requires_olya |
| GAP-MGMT-005 | Time exits | Exit before session end? | requires_olya |
| GAP-MGMT-006 | Risk sizing | Fixed % or variable? | requires_olya |

### ENTRY

| Gap ID | Area | Question | Status |
|--------|------|----------|--------|
| GAP-ENTRY-001 | Entry price | FVG top/bottom vs CE? | evaluator_decides |
| GAP-ENTRY-002 | Multi-entry | Scaling rules? | deferred_to_mgmt |

---

## CONFLICTS FLAGGED

| Conflict ID | Description | Recommendation |
|-------------|-------------|----------------|
| CONFLICT-COND-001 | L8 uses structural P/D, L11 uses daily P/D | Align L11 to structural |
| CONFLICT-COND-002 | L10 hardcoded thresholds vs L11 principle | Move scoring to evaluator |

---

## ARCHIVED FILES

Moved to `cso/knowledge/archive/`:
- `htf/htf_structure.yaml`
- `htf/htf_signals.yaml`
- `htf/htf_bias.yaml`
- `htf/htf_state_machine.yaml`
- `htf/index.yaml`
- `htf/EXTRACTION_AUDIT.md`
- `htf/EXTRACTION_LOG.md`
- `nex_baseline/entry_quality.yaml`
- `nex_baseline/CONSOLIDATION_LOG.md`

---

## VALIDATION CHECKLIST

- [x] All 5 YAMLs parse successfully
- [x] No duplicate definitions across drawers
- [x] source_ref on all signals/invariants
- [x] Conflicts documented, not resolved
- [x] Gaps documented for Olya
- [x] Index manifest complete

---

## NEXT STEPS

1. **Olya Validation**
   - Review all 5 drawers
   - Resolve MANAGEMENT gaps
   - Confirm CONFLICT resolutions

2. **CSO Integration**
   - Wire drawers to CSO observer
   - Implement validation logic per drawer

3. **Test Coverage**
   - Tests for each invariant
   - Tests for each composite gate

---

*Extraction completed: 2026-01-23*
*Auditor: OPUS*
*Label: DRAFT v0 — pending Olya validation*
