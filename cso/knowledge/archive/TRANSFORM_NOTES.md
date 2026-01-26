# Transform Notes — HTF Context to OLYA_SIGNAL_CONTRACT

## Source Document
- **File**: `docs/olya_skills/LAYER_0_HTF_CONTEXT_CLEAN.md`
- **Lines**: 2072
- **Version**: 4.0 FINAL (With 8 Gaps Resolved)

## Transform Decisions

### 1. Signal Selection Rationale

Selected 5 patterns that cover the breadth of HTF methodology:

| Signal | Why Selected | Source Lines |
|--------|--------------|--------------|
| Weekly MSS | Foundation of structure | L42-95 |
| Displacement | Universal, qualitative | L159-210 |
| FVG Detection | Universal, critical for PDAs | L217-275 |
| Liquidity Status | GAP 7 resolution, target filtering | L830-930 |
| Daily Bias | Composite decision, 3Q framework | L1386-1490 |

### 2. Schema Design Decisions

**Timeframe Enum (HTF/ITF/LTF)**
- Collapsed Weekly+Daily into HTF (both macro context)
- H4+H1 as ITF (intermediate/rebalance)
- 15m/5m/1m as LTF (execution)

**Condition Types**
- `qualitative` operator for displacement (NO pip thresholds)
- `exists` / `forms` for pattern detection
- Preserved Olya's emphasis on "no numeric thresholds"

**Liquidity Status**
- Three-state enum from GAP 7:
  - `NOT_DELIVERED` (highest priority)
  - `LIQUIDITY_RUN` (valid target)
  - `DELIVERED_WITH_CONSEQUENCE` (invalid)

### 3. Invariant Extraction

Extracted 11 invariants from absolute prohibitions and gap resolutions:

| ID | Rule Summary | Source |
|----|--------------|--------|
| INV-OLYA-001 | Structure only after MSS | Global Rule |
| INV-OLYA-002 | Swings from MSS | Global Rule |
| INV-OLYA-003 | Ranges from MSS | GAP 2 |
| INV-OLYA-004 | Bootstrap: PDH/PDL/PWH/PWL only | GAP 1 |
| INV-OLYA-005 | Displacement: no pip thresholds | GAP 3 |
| INV-OLYA-006 | FVG: universal detection | GAP 4 |
| INV-OLYA-007 | BOS = MSS (terminology) | GAP 2 |
| INV-OLYA-008 | Daily bias frozen at 00:00 NY | Prohibitions |
| INV-OLYA-009 | No trade from equilibrium | Prohibitions |
| INV-OLYA-010 | MMXM lookback from last MSS | GAP 6 |
| INV-OLYA-011 | Post-expansion: displacement required | GAP 8 |

### 4. What Was NOT Transformed (Out of Scope)

- **MMXM Detection**: Complex pattern, deferred to full transform
- **Validated Swings**: Algorithm detailed, needs separate signal
- **Order Blocks**: Mentioned but not fully specified in source
- **H4/H1 Rebalance**: Layer 2 scope, not Layer 0

### 5. Traceability

Every signal includes `source_ref` in format:
```
L{start}-{end}:{function_name}
```

Example: `L159-210:check_displacement_qualitative`

### 6. Weight Assignment

| Signal | Weight | Rationale |
|--------|--------|-----------|
| Weekly MSS | 1.0 | Foundation, blocks everything |
| Displacement | 0.9 | Required for MSS, high impact |
| FVG | 0.7 | Common, but needs confluence |
| Liquidity Status | 0.8 | Target filtering, critical |
| Daily Bias | 1.0 | Final gate, blocks trades |

### 7. Validation Checks Added

From source document's validation checklist (Section H):
- Weekly MSS detected
- Daily MSS confirmed
- Daily range defined (structure-based)
- Objective identified and aligned
- Premium/Discount determined (NOT equilibrium)
- State machine in FULL_CONTEXT

## Transform Quality

| Metric | Value |
|--------|-------|
| Patterns Extracted | 5 |
| Invariants Extracted | 11 |
| GAPs Covered | 6/8 |
| Source Lines Referenced | ~600 |
| Schema Compliance | Yes |

## Next Steps

1. **Olya Review**: Share sample with her Claude for validation
2. **Full Transform**: If approved, transform remaining signals
3. **Test Generation**: Auto-generate tests from invariants
4. **CSO Integration**: Wire signals to observer pattern detection

---

*Transform completed: 2026-01-23*
*Schema: OLYA_SIGNAL_CONTRACT v1.0*
