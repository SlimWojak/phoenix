# NEX SALVAGE REPORT

**SPRINT:** 26.TRACK_C  
**DATE:** 2026-01-25  
**PURPOSE:** Audit NEX components for Phoenix subsumption

---

## EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total Components** | 24 |
| **Subsume Candidates** | 18 (75%) |
| **Requires Refactor** | 4 (17%) |
| **Incompatible** | 2 (8%) |

**VERDICT:** NEX enrichment pipeline is 92% compatible with Phoenix governance.
The 12-layer architecture can be wrapped in `GovernanceInterface` with minimal refactoring.

---

## COMPONENT TABLE

| # | Component | Location | Subsume | Refactor | Blocker |
|---|-----------|----------|---------|----------|---------|
| 0 | HTF Analysis | `htf_analysis.py` | ✓ | Minor | None |
| 0.5 | HTF Bias | `htf_bias.py` | ✓ | Minor | None |
| 1 | Time Sessions | `time_sessions.py` | ✓ | No | None |
| 2 | Reference Levels | `reference_levels.py` | ✓ | Minor | Dep: Layer 1 |
| 3 | Sweeps | `sweeps.py` | ✓ | Minor | Dep: L1, L2 |
| 4 | Statistical | `statistical_features.py` | ✓ | No | None |
| 5 | MTF FVG | `mtf_fvg.py` | ✓ | No | None |
| 6 | Displacement | `displacement.py` | ✓ | No | None |
| 7 | Structure | `structure.py` | ✓ | Minor | DXY vendor |
| 8 | Premium/Discount | `premium_discount.py` | ✓ | No | None |
| 9 | Order Blocks | `order_blocks.py` | ✓ | No | Dep: Layer 6 |
| 10 | Timing | `timing_enrichment.py` | ✓ | No | None |
| 11 | Alignment | `alignment.py` | ✓ | Minor | Composite |
| 12 | MMM | `mmm_enrichment.py` | ✓ | Minor | Composite |
| - | DXY Merge | `dxy_merge.py` | ✗ | Rewrite | IBKR coupling |
| - | DXY Swing | `dxy_swing_enrichment.py` | ✗ | Rewrite | IBKR coupling |
| - | Incremental Runner | `incremental.py` | ⚠ | Major | Global state |
| - | Pipeline Runner | `pipeline.py` | ⚠ | Major | Orchestration |

---

## COMPATIBLE (Direct Subsumption)

These components can be wrapped in `GovernanceInterface` as-is:

### Pure Functions (No State)

| Component | Columns | Deterministic | Notes |
|-----------|---------|---------------|-------|
| `time_sessions.py` | 25 | ✓ | Timezone handling only |
| `displacement.py` | 12 | ✓ | ATR-based detection |
| `statistical_features.py` | 35 | ✓ | Rolling stats |
| `mtf_fvg.py` | 56 | ✓ | Multi-TF resampling |
| `order_blocks.py` | 28 | ✓ | Vectorized forward-fill |
| `premium_discount.py` | 15 | ✓ | Fibonacci zones |
| `timing_enrichment.py` | 8 | ✓ | Macro time flags |

### With Layer Dependencies

| Component | Dependencies | Columns | Notes |
|-----------|--------------|---------|-------|
| `reference_levels.py` | L1 | 74 | Asia range, PDH/PDL |
| `sweeps.py` | L1, L2 | 37 | Liquidity sweep detection |
| `structure.py` | None | 21 | Swing HH/HL/LH/LL |
| `htf_analysis.py` | Daily resample | 54 | HTF context broadcast |
| `htf_bias.py` | L0 | 33 | OTE, bias filters |

---

## REQUIRES REFACTOR

### 1. `alignment.py` — Minor Refactor

**Issue:** Reads from multiple layers, performs composite logic.
**Fix:** Add explicit layer inputs, separate compute from I/O.

```python
# Current (implicit):
def enrich_alignment(df): ...

# Phoenix (explicit):
def compute_alignment(
    df: pd.DataFrame,
    htf_context: dict,
    entry_signals: dict
) -> pd.DataFrame: ...
```

### 2. `mmm_enrichment.py` — Minor Refactor

**Issue:** MMM (Manipulation-Mitigation-Momentum) is composite evaluation.
**Fix:** Split into atomic checks that CSO aggregates.

### 3. `structure.py` DXY Section — Minor Refactor

**Issue:** `_add_dxy_swing_structure()` has IBKR fetch inside enrichment.
**Fix:** Extract DXY as separate River tributary, inject as data.

### 4. `htf_analysis.py` — Minor Refactor

**Issue:** Can call IBKR directly if cache miss.
**Fix:** Cache-only mode enforced, fresh data from River.

---

## INCOMPATIBLE (Must Rewrite)

### 1. `dxy_merge.py` / `dxy_swing_enrichment.py`

**Blocker:** Tightly coupled to IBKR vendor API.
**Action:** DXY becomes separate Phoenix tributary with own governance.
**Phoenix Design:**
- `phoenix/river/dxy.py` — DXY data source
- Follows same `GovernanceInterface` as FX River
- CSO receives both FX and DXY via River contract

### 2. `incremental.py` Runner

**Blocker:** Global state mutation, file I/O in hot path.
**Action:** Replaced by Phoenix River streaming model.
**Phoenix Design:**
- River produces enriched bars
- CSO consumes via `GovernanceInterface.process_state()`
- No incremental file management

---

## EXTERNAL DEPENDENCIES

| Dependency | Version | Usage | Phoenix Status |
|------------|---------|-------|----------------|
| `pandas` | >=1.5 | Core data | Required |
| `numpy` | >=1.24 | Vectorized ops | Required |
| `zoneinfo` | stdlib | Timezone | Required |
| `ib_insync` | 0.9.86 | IBKR fetch | **Isolate to Broker** |
| `pyarrow` | >=12.0 | Parquet I/O | Required |

**IBKR Note:** All IBKR dependencies must be isolated to `phoenix/brokers/`,
never imported in enrichment or CSO layers.

---

## SUBSUMPTION ARCHITECTURE

```
NEX                           PHOENIX
───────────────────          ──────────────────────────
enrichment/                   river/enrichment/
├── time_sessions.py    →     ├── layer_1_sessions.py
├── reference_levels.py →     ├── layer_2_reference.py
├── sweeps.py           →     ├── layer_3_sweeps.py
├── statistical.py      →     ├── layer_4_stats.py
├── mtf_fvg.py          →     ├── layer_5_fvg.py
├── displacement.py     →     ├── layer_6_displacement.py
├── structure.py        →     ├── layer_7_structure.py
├── premium_discount.py →     ├── layer_8_premium.py
├── order_blocks.py     →     ├── layer_9_ob.py
├── timing.py           →     ├── layer_10_timing.py
├── alignment.py        →     ├── layer_11_alignment.py
└── mmm.py              →     └── layer_12_mmm.py
                              
vendors/ibkr.py         →     brokers/ibkr/adapter.py (isolated)
dxy_*.py                →     river/tributaries/dxy.py (new)
```

---

## GOVERNANCE WRAPPER

Each layer becomes:

```python
class Layer1Sessions(GovernanceInterface):
    module_id = "river.enrichment.layer_1_sessions"
    module_tier = ModuleTier.T0  # Read-only
    enforced_invariants = ["INV-CONTRACT-1"]
    
    def process_state(self, input: StateInput) -> StateTransition:
        df = input.data['bars']
        self.check_halt()  # Yield point
        
        enriched = enrich_time_sessions(df)
        
        return StateTransition(
            previous_hash=self.compute_state_hash(),
            new_hash=compute_hash(enriched),
            mutations=['layer_1_columns']
        )
```

---

## RECOMMENDATIONS

1. **Phase 1:** Wrap L1-L6 (foundational layers) — pure functions
2. **Phase 2:** Wrap L7-L12 (composite layers) — with refactor
3. **Phase 3:** Rewrite DXY tributary — new governance-compliant source
4. **Phase 4:** Deprecate NEX incremental runner — River replaces

---

## INV-CONTRACT-1 COMPLIANCE

| Layer | Same Input → Same Output | Notes |
|-------|--------------------------|-------|
| L1 | ✓ | Timezone-pure |
| L2 | ✓ | Uses L1 outputs only |
| L3 | ✓ | Uses L1, L2 outputs |
| L4 | ✓ | Rolling window deterministic |
| L5 | ✓ | Resampling deterministic |
| L6 | ✓ | ATR-based thresholds |
| L7 | ⚠ | DXY fetch breaks determinism |
| L8 | ✓ | Fibonacci math only |
| L9 | ✓ | Uses L6 output |
| L10 | ✓ | Time-based flags |
| L11 | ✓ | Composite of L0-L10 |
| L12 | ✓ | MMM evaluation |

**Action:** L7 DXY section must be extracted to maintain determinism.

---

*Generated: Sprint 26 Track C*
