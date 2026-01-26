# EXTRACTION_LOG — HTF Full Extraction

**Sprint:** S27.HTF_FULL_EXTRACTION
**Date:** 2026-01-23
**Owner:** OPUS
**Status:** COMPLETE

---

## Summary

| Metric | Value |
|--------|-------|
| Source Lines | 2,072 (LAYER_0_HTF_CONTEXT_CLEAN.md) |
| Output Lines | 555 (4 YAML files) |
| Compression | 73% |
| Signals Extracted | 31 |
| Invariants Extracted | 19 |
| Prohibitions | 6 |
| Conflicts Flagged | 1 |
| GAPS Covered | 8/8 (100%) |

---

## Files Created

| File | Purpose | Signals | INVs | Lines |
|------|---------|---------|------|-------|
| htf_structure.yaml | MSS, swings, ranges, bootstrap | 8 | 6 | 133 |
| htf_signals.yaml | Displacement, FVG, liquidity | 9 | 4 | 135 |
| htf_bias.yaml | 3Q framework, bias synthesis | 7 | 4 | 141 |
| htf_state_machine.yaml | MMXM, warmup, post-expansion | 7 | 5 | 146 |
| **4 CORE FILES** | | **31** | **19** | **555** |

---

## Signals by File

### htf_structure.yaml (8 signals)
| ID | Name | Covers |
|----|------|--------|
| SIG-HTF-001 | Weekly MSS Bullish | GAP-2 |
| SIG-HTF-002 | Weekly MSS Bearish | GAP-2 |
| SIG-HTF-003 | Daily MSS Bullish | GAP-2 |
| SIG-HTF-004 | Daily MSS Bearish | GAP-2 |
| SIG-HTF-005 | Bootstrap MSS | GAP-1 |
| SIG-HTF-006 | Daily Dealing Range | GAP-5 |
| SIG-HTF-007 | Validated Swing | GAP-5 |
| SIG-HTF-008 | Daily Order Flow | - |

### htf_signals.yaml (9 signals)
| ID | Name | Covers |
|----|------|--------|
| SIG-HTF-010 | Displacement Confirmed | GAP-3 |
| SIG-HTF-011 | FVG Bullish | GAP-4 |
| SIG-HTF-012 | FVG Bearish | GAP-4 |
| SIG-HTF-013 | FVG Respected | GAP-4 |
| SIG-HTF-014 | Liquidity NOT_DELIVERED | GAP-7 |
| SIG-HTF-015 | Liquidity LIQUIDITY_RUN | GAP-7 |
| SIG-HTF-016 | Liquidity DELIVERED_WITH_CONSEQUENCE | GAP-7 |
| SIG-HTF-017 | Daily Objective | GAP-7 |
| SIG-HTF-018 | PDA Types | - |

### htf_bias.yaml (7 signals)
| ID | Name | Cross-ref |
|----|------|-----------|
| SIG-HTF-020 | Q1 Location | - |
| SIG-HTF-021 | Q2 Objective | - |
| SIG-HTF-022 | Q3 Respect | - |
| SIG-HTF-023 | Daily Bias Synthesis | - |
| SIG-HTF-024 | DOL Framework | NEX L0.5 |
| SIG-HTF-025 | Premium/Discount State | - |
| SIG-HTF-026 | Weekly/Daily Alignment | NEX L0.5 |

### htf_state_machine.yaml (7 signals)
| ID | Name | Covers |
|----|------|--------|
| SIG-HTF-030 | MMXM Detection | GAP-6 |
| SIG-HTF-031 | MMXM as Manipulation | GAP-6 |
| SIG-HTF-032 | MMXM as Target | GAP-6 |
| SIG-HTF-033 | MMXM Consolidation | GAP-6 |
| SIG-HTF-034 | Post-Expansion Status | GAP-8 |
| SIG-HTF-035 | Structure State | GAP-8 |
| SIG-HTF-036 | Grind vs Impulsive | GAP-8 |

---

## Invariants (19 total, deduped)

### htf_structure.yaml (6)
| ID | Rule |
|----|------|
| INV-HTF-001 | Structure exists ONLY after MSS |
| INV-HTF-002 | BOS = MSS (use MSS only) |
| INV-HTF-003 | Bootstrap uses PDH/PDL/PWH/PWL ONLY |
| INV-HTF-004 | MSS requires displacement + FVG |
| INV-HTF-005 | Range priority: Liquidity > External > MSS > Validated |
| INV-HTF-006 | Validated swing needs immediate reaction (1-3 bars) |

### htf_signals.yaml (4)
| ID | Rule |
|----|------|
| INV-HTF-007 | Displacement is QUALITATIVE (no pip thresholds) |
| INV-HTF-008 | FVG detection universal (all TFs same) |
| INV-HTF-009 | Only NOT_DELIVERED or LIQUIDITY_RUN are valid targets |
| INV-HTF-010 | FVG respect uses 5 conditions (all required) |

### htf_bias.yaml (4)
| ID | Rule |
|----|------|
| INV-HTF-011 | Bias set at 00:00 NY, frozen until next day |
| INV-HTF-012 | Trade requires: MSS + range + objective + not equilibrium |
| INV-HTF-013 | Weekly = limits only, Daily = execution direction |
| INV-HTF-014 | Counter-trend only toward HTF PDA |

### htf_state_machine.yaml (5)
| ID | Rule |
|----|------|
| INV-HTF-015 | Higher TF MMXM overrides lower TF |
| INV-HTF-016 | MMXM valid only after last Daily MSS |
| INV-HTF-017 | Post-expansion = impulsive delivery only |
| INV-HTF-018 | Post-expansion state permanent until new MSS |
| INV-HTF-019 | REBALANCE mode = H4/H1 operating range |

---

## NEX Gap-Fills Used

| Source | Used For | Note |
|--------|----------|------|
| LAYER_0_5_HTF_BIAS_SPEC.md | DOL path types, counter-trend rules | 2 signals |
| LAYER_0_HTF_ANALYSIS_SPEC.md | Column reference validation | Alignment confirmed |

---

## Conflicts Flagged (1)

| ID | Description | Recommendation |
|----|-------------|----------------|
| CONFLICT-HTF-001 | NEX L7 uses 'BOS', L0 doc uses 'MSS' only | Align NEX to MSS terminology |

---

## GAPS Coverage (8/8)

| GAP | Topic | File | Status |
|-----|-------|------|--------|
| 1 | Bootstrap (first MSS) | htf_structure.yaml | ✓ |
| 2 | BOS = MSS terminology | htf_structure.yaml | ✓ |
| 3 | Displacement (qualitative) | htf_signals.yaml | ✓ |
| 4 | FVG (universal) | htf_signals.yaml | ✓ |
| 5 | Validated swings | htf_structure.yaml | ✓ |
| 6 | MMXM identification | htf_state_machine.yaml | ✓ |
| 7 | Liquidity status (3-state) | htf_signals.yaml | ✓ |
| 8 | Post-expansion threshold | htf_state_machine.yaml | ✓ |

---

## Coverage Assessment

### Section-by-Section Audit

| Section | Topic | Extracted |
|---------|-------|-----------|
| A | Weekly Context | ✓ htf_structure + htf_signals |
| A1 | Weekly MSS Detection | ✓ SIG-HTF-001/002 |
| A1.1 | Bootstrap Logic | ✓ SIG-HTF-005 |
| A1.2 | Displacement Definition | ✓ SIG-HTF-010 |
| A1.3 | FVG Detection | ✓ SIG-HTF-011/012/013 |
| A2 | Weekly Range | ✓ SIG-HTF-006 |
| A3 | Weekly Role | ✓ INV-HTF-013 |
| B | Daily Context | ✓ htf_structure + htf_bias |
| B1 | Daily MSS | ✓ SIG-HTF-003/004 |
| B2 | Daily Structure | ✓ SIG-HTF-008 |
| B3 | Daily Dealing Range | ✓ SIG-HTF-006 |
| B3.1 | Validated Swings | ✓ SIG-HTF-007 |
| B4 | Premium/Discount | ✓ SIG-HTF-025 |
| B4.5 | MMXM | ✓ SIG-HTF-030/031/032/033 |
| B5 | Daily Objective | ✓ SIG-HTF-017 |
| B5.1 | Liquidity Status | ✓ SIG-HTF-014/015/016 |
| B6 | Daily PDAs | ✓ SIG-HTF-018 |
| B7 | Structure State | ✓ SIG-HTF-034/035/036 |
| C | Daily Bias | ✓ htf_bias |
| D | Prohibitions | ✓ htf_bias.prohibitions |
| E | Output Format | ✓ htf_state_machine.output_schema |
| F | State Machine | ✓ htf_state_machine.warmup_states |
| G-K | Integration, Validation, Principles, Gaps | ✓ Distributed |

**Coverage: 100%**

---

## Validation Checklist

- [x] All YAML parses (`yaml.safe_load()`)
- [x] All signals have `ref` (source reference)
- [x] All 8 GAPS covered
- [x] Invariants deduped (19 unique)
- [x] Conflicts flagged (1)
- [x] Total < 600 lines (~540)
- [x] Cross-ref NEX used only for gaps

---

## Final State

### Before
- htf_context_sample.yaml (5 signals, ~40% coverage)
- 14+ NEX docs (sprawl)

### After
- cso/knowledge/htf/ (4 files, 31 signals, 100% coverage)
- cso/knowledge/nex_baseline/entry_quality.yaml (21 signals)
- **Total: 5 contracts covering HTF + Entry methodology**
- **Compression: ~85%**

---

**Document Version:** 1.0
**Ready for:** CSO validation with Olya
