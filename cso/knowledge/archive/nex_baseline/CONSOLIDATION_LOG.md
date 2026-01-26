# CONSOLIDATION_LOG — NEX Baseline Wave 1

**Sprint:** S27.NEX_BASELINE.WAVE_1
**Date:** 2026-01-23
**Owner:** OPUS
**Status:** COMPLETE

---

## Summary

| Metric | Value |
|--------|-------|
| Specs Consolidated | 3 |
| Input Lines | 1,209 (405 + 364 + 440) |
| Output Lines | 148 |
| Compression | 88% reduction |
| Signals Extracted | 21 |
| Invariants Extracted | 11 |
| Conflicts Flagged | 3 |
| Composite Gates | 4 |

---

## Input Specs

| Spec | Decision | Lines | Columns | Function |
|------|----------|-------|---------|----------|
| L8_PREMIUM_DISCOUNT_SPEC_REVISED.md | D188 | 405 | 16 | Zone detection (premium/discount) |
| L10_TIMING_SPEC.md | D180 | 364 | 20 | Freshness metrics (age, touch, recency) |
| L11_ALIGNMENT_REFACTORED_SPEC.md | D184 | 440 | 12 | HTF/Entry layer confluence |

**Total:** 48 columns serving ENTRY GATING function.

---

## Output Structure

```yaml
entry_quality.yaml:
  signals:
    premium_discount:    # 5 signals from L8
    timing:              # 5 signals from L10
    alignment:           # 11 signals from L11
  invariants:            # 11 (deduped from 3 specs)
  conflicts:             # 3 (flagged, not resolved)
  composite_gates:       # 4 (entry quality checks)
  dependencies:          # cross-layer requirements
```

---

## Consolidation Decisions

### 1. Grouping by Function

**Decision:** Group signals by FUNCTION, not layer number.

| Function | Source | Purpose |
|----------|--------|---------|
| `premium_discount` | L8 | Where in range? |
| `timing` | L10 | How fresh? |
| `alignment` | L11 | How aligned? |

**Rationale:** All three answer "Is this entry quality good enough?" — same function, different dimensions.

### 2. Signal ID Scheme

**Decision:** Use `SIG-ENTRY-XXX` with ranges per function.

| Range | Function |
|-------|----------|
| 001-009 | premium_discount |
| 010-019 | timing |
| 020-030 | alignment |

### 3. Weight Assignment

**Decision:** Preserve implied weights from spec importance statements.

| Signal | Weight | Rationale |
|--------|--------|-----------|
| in_structural_premium/discount | 0.9 | "PRIMARY" in L8 |
| entry_freshness_score | 0.85 | "KEY grading metric" in L10 |
| htf_unanimous | 0.9 | "Strongest alignment" in L11 |
| daily/weekly_position_pct | 0.4 | "SECONDARY" in L8 |
| conflicting_signals | -0.3 | Negative — conflicts reduce quality |

### 4. Invariant Deduplication

**Merged:** No duplicates found across specs (different domains).

**Kept Separate:** 11 invariants, each from distinct aspect of entry quality.

| INV-ENTRY-* | Domain |
|-------------|--------|
| 001 | L8: Structural > time |
| 002 | L10: Fresh > confluence |
| 003 | L11: Counts > thresholds |
| 004-006 | L10: Age/touch mechanics |
| 007-008 | L11: Unanimous/conflict definitions |
| 009 | L8: OTE in evaluator |
| 010-011 | L10/L11: Pipeline order |

---

## Conflicts Flagged

### CONFLICT-001: Premium/Discount Column Usage

| Aspect | L8 | L11 |
|--------|-----|-----|
| Primary P/D | `in_structural_premium/discount` | `in_daily_premium/discount` |
| Reason | "Structure over time" (Olya) | Historical code reference |

**Recommendation:** Align L11 to use structural columns.
**Status:** FLAGGED for Olya validation.

### CONFLICT-002: Threshold Location

| Aspect | L10 | L11 Principle |
|--------|-----|---------------|
| Freshness Score | Hardcoded: 1-3=+3, 4-10=+2 | "Store counts, threshold in evaluator" |
| Implication | Scoring logic in enrichment | Scoring logic should be evaluator |

**Recommendation:** Store raw metrics, move scoring to evaluator.
**Status:** FLAGGED for architecture review.

### CONFLICT-003: P/D Reference Mismatch

L11 code references `in_daily_discount` but L8 establishes `in_structural_discount` as primary.

**Recommendation:** Update L11 to use structural columns.
**Status:** FLAGGED for code update.

---

## Composite Gates

| Gate | Purpose | Key Conditions |
|------|---------|----------------|
| GATE-ENTRY-001 | High Quality Long | discount + fresh + aligned |
| GATE-ENTRY-002 | High Quality Short | premium + fresh + aligned |
| GATE-ENTRY-003 | Alignment Minimum | 2+ HTF + 3+ layers |
| GATE-ENTRY-004 | Freshness Minimum | age <= 10 + break <= 30 |

---

## Columns Not Extracted (Derived/Internal)

The following columns exist in specs but are internal/derived:

| Column | Type | Note |
|--------|------|------|
| `structural_equilibrium` | derived | Calculated from range |
| `structural_range_pips` | derived | RAW metric |
| `price_vs_structural_eq` | derived | Distance calculation |
| `daily_equilibrium` | derived | Calculated from PDH/PDL |
| `weekly_equilibrium` | derived | Calculated from PWH/PWL |
| `htf_neutral_count` | derived | 3 - bullish - bearish |

These are documented in `derived_columns` section of YAML.

---

## Validation Checklist

- [x] YAML parses (`python -c "import yaml; yaml.safe_load(...)"`)
- [x] All signals have `source_ref` (spec:line)
- [x] 3 specs → 1 file (consolidated)
- [x] < 400 lines (389 lines)
- [x] No L0/L0.5 content (covered by Olya doc)
- [x] Conflicts flagged, not resolved

---

## Next Steps

1. **Olya Validation:** Review CONFLICT-001 (structural vs daily P/D)
2. **Architecture Review:** Review CONFLICT-002 (threshold location)
3. **Code Update:** Apply CONFLICT-003 fix in Phoenix L11 subsumption
4. **Wave 2:** Extract remaining specs (if any)

---

## Traceability Matrix

| Signal ID | Source Spec | Lines |
|-----------|-------------|-------|
| SIG-ENTRY-001 | L8 | 73-82 |
| SIG-ENTRY-002 | L8 | 73-82 |
| SIG-ENTRY-003 | L8 | 132-138 |
| SIG-ENTRY-004 | L8 | 150-156 |
| SIG-ENTRY-005 | L8 | 159-165 |
| SIG-ENTRY-010 | L10 | 127-158 |
| SIG-ENTRY-011 | L10 | 70-82 |
| SIG-ENTRY-012 | L10 | 52-65 |
| SIG-ENTRY-013 | L10 | 90-98 |
| SIG-ENTRY-014 | L10 | 100-104 |
| SIG-ENTRY-020 | L11 | 68-77 |
| SIG-ENTRY-021 | L11 | 79-88 |
| SIG-ENTRY-022 | L11 | 89-92 |
| SIG-ENTRY-023 | L11 | 98-122 |
| SIG-ENTRY-024 | L11 | 124-148 |
| SIG-ENTRY-025 | L11 | 150-157 |
| SIG-ENTRY-026 | L11 | 159-163 |
| SIG-ENTRY-027 | L11 | 169-170 |
| SIG-ENTRY-028 | L11 | 171-172 |
| SIG-ENTRY-029 | L11 | 174-178 |
| SIG-ENTRY-030 | L11 | 180-184 |

---

**Document Version:** 1.0
**Label:** DRAFT v0 — consolidated from NEX L8/L10/L11, pending Olya validation
