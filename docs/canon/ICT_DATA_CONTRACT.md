# ICT DATA CONTRACT v1.0

**Document:** ICT_DATA_CONTRACT.md  
**Version:** 1.0.0  
**Date:** 2026-01-23  
**Status:** SCHEMA LOCKDOWN — Prerequisite for Mirror Test  
**Author:** CTO (Opus) via Cursor  
**Sprint:** 26 Track A Day 0.5

---

## 1. PURPOSE

This contract defines the **immutable schema specification** for the Phoenix River data pipeline. It establishes:

1. Canonical bar construction semantics
2. Vendor-specific raw input definitions
3. The frozen 472-column enriched schema
4. Boolean marker registry for Mirror XOR testing
5. Volume semantics declaration (critical: vendors are NON-COMPARABLE)
6. Gap and synthetic fill policy
7. Mechanical sign-off gate conditions

**INV-CONTRACT-0:** No Phoenix organ may consume data that does not comply with this contract.

---

## 2. CANONICAL BAR SPECIFICATION

### 2.1 Bar Construction Rules

| Parameter | Value | Invariant |
|-----------|-------|-----------|
| `bar_interval` | 60 seconds (1 minute) | Fixed, no variable intervals |
| `bar_open_rule` | First tick price within minute | NOT first tick of next bar |
| `bar_close_rule` | Last tick price within minute | NOT last tick of previous bar |
| `bar_high_rule` | Maximum price within minute | max(all ticks in bar) |
| `bar_low_rule` | Minimum price within minute | min(all ticks in bar) |
| `timezone` | UTC | All timestamps in UTC |
| `timestamp_meaning` | **bar_start_time_utc** | The timestamp indicates when the bar OPENED |

### 2.2 Timestamp Convention

```
timestamp = 2024-01-15 14:30:00+00:00

This means:
- Bar covers period: 14:30:00.000 to 14:30:59.999 UTC
- Open price: first tick >= 14:30:00.000
- Close price: last tick < 14:31:00.000
- High/Low: from all ticks in that period
```

**INVARIANT:** `timestamp_convention = bar_start_time_utc` across ALL sources after normalization.

### 2.3 Session Boundary Handling

| Boundary | Rule |
|----------|------|
| **Sunday Open** | First bar when Sydney session opens (~22:00 UTC Sunday) |
| **Weekend Gap** | Friday 22:00 UTC to Sunday ~22:00 UTC — NO BARS EXPECTED |
| **DST Transitions** | Irrelevant (all data in UTC) |
| **Partial Bars** | FORBIDDEN in canonical output — `is_partial=True` required if emitted |

---

## 3. VENDOR RAW INPUTS

### 3.1 Dukascopy (Historical Backdata)

**Source:** CSV files from Dukascopy tick data, aggregated to 1-minute bars  
**Coverage:** 2020-11-23 to 2025-11-21 (5 years)  
**Pairs:** EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF

| Column | Type | Semantics |
|--------|------|-----------|
| `timestamp` | datetime64[ns, UTC] | Bar start time in UTC |
| `open` | float64 | First tick price in bar |
| `high` | float64 | Maximum tick price in bar |
| `low` | float64 | Minimum tick price in bar |
| `close` | float64 | Last tick price in bar |
| `volume` | float64 | **TICK VOLUME** (see Volume Semantics) |
| `missing_bar` | bool | Flag for bars marked missing at source (dropped in parquet) |

**Dukascopy Volume Semantics:**
- Type: Tick volume (count of price updates, possibly fractional due to aggregation)
- Range: Typically 10-4000 per 1-minute bar
- **Sentinel value:** `-1.0` indicates NO VOLUME DATA (54,857 instances in EURUSD)
- **Zero volume:** Rare (106 instances) — indicates very low activity period
- **NOT traded volume** — FX is OTC, no centralized exchange

### 3.2 IBKR (Live Data)

**Source:** Interactive Brokers Gateway API (`reqHistoricalData`)  
**Coverage:** 2025-11-22 onwards (real-time append)  
**Connection:** Port 4002 (Paper) / 4001 (Live)

| Column | Type | Semantics |
|--------|------|-----------|
| `timestamp` | datetime64[ns, UTC] | Bar start time in UTC |
| `open` | float64 | First tick MIDPOINT in bar |
| `high` | float64 | Maximum MIDPOINT in bar |
| `low` | float64 | Minimum MIDPOINT in bar |
| `close` | float64 | Last MIDPOINT in bar |
| `volume` | float64 | **ALWAYS 0 or UNAVAILABLE** (see Volume Semantics) |

**IBKR Price Semantics:**
- Data type: `whatToShow='MIDPOINT'` — average of bid/ask
- NOT bid, NOT ask, NOT last traded price
- FX is OTC — no "last traded" concept

**IBKR Volume Semantics:**
- FX pairs return NO VOLUME from IBKR historical API
- Code sets `volume = float(bar.volume) if bar.volume else 0.0`
- Result: Effectively ALL ZEROS for FX data

---

## 4. VOLUME SEMANTICS DECLARATION

```yaml
volume_semantics:
  dukascopy:
    type: "tick_volume"
    definition: "Count of price updates within bar (fractional due to aggregation method)"
    range: "[−1.0, 4375.53]"
    sentinel_missing: -1.0
    unit: "ticks"
    reliable: false
    notes: "Negative values are sentinel for 'no data'. Not comparable to traded volume."
    
  ibkr:
    type: "null"
    definition: "IBKR FX historical API does not provide volume for OTC forex"
    range: "[0.0, 0.0]"
    unit: "none"
    reliable: false
    notes: "Always zero or unavailable. FX is OTC - no centralized volume exists."

volume_comparability: NONE
```

**CRITICAL DIRECTIVE:**

> **Any ICT marker that depends on "volume strength" MUST declare `VendorVolumeModel` and MUST NOT assume cross-vendor parity.**

**Volume-Dependent Columns (PROHIBITED from Mirror XOR):**

| Column | Reason |
|--------|--------|
| `volume` | Raw volume is non-comparable |
| Any column derived from `volume` | Inherits non-comparability |

**Recommendation:** Until a vendor-agnostic volume proxy is defined (e.g., bar range as activity proxy), volume-derived signals should be flagged as `vendor_specific=True` and excluded from cross-vendor validation.

---

## 5. CANONICAL OUTPUT SCHEMA

### 5.1 Schema Metadata

```yaml
schema_version: "1.0.0"
schema_hash: "b848ffe506fd3fff"
total_columns: 472
column_breakdown:
  boolean_markers: 110
  continuous_features: 277
  categorical_tags: 85
```

### 5.2 Layer Origin Map

| Layer | Module | Columns Added | Description |
|-------|--------|---------------|-------------|
| **Raw** | — | 6 | timestamp, OHLCV |
| **0** | `htf_analysis.py` | ~54 | Dealing range, IPDA, BSL/SSL, daily PDAs |
| **0.5** | `htf_bias.py` | ~33 | OTE zones, DOL, HTF direction, bias |
| **1** | `time_sessions.py` | ~26 | Session labels, Kill Zones |
| **2** | `reference_levels.py` | ~80 | Asia range, PDH/PDL, PWH/PWL, session levels |
| **3** | `sweeps.py` | ~24 | Sweep detection, classification |
| **4** | `statistical_features.py` | ~5 | ATR, volatility, trend strength |
| **5** | `mtf_fvg.py` | ~100 | Multi-timeframe FVG (5m to monthly) |
| **6** | `displacement.py` | ~12 | Displacement bull/bear, strength |
| **7** | `structure.py` | ~12 | BOS, CHOCH, swing points |
| **7B** | `dxy_merge.py` | ~22 | DXY context, SMT divergences |
| **8** | `premium_discount.py` | ~14 | Premium/discount zones, OTE |
| **9** | `order_blocks.py` | ~28 | Order block detection (15m, 1h) |
| **10** | `timing_enrichment.py` | ~22 | Zone age, touch count |
| **11** | `alignment.py` | ~14 | Confluence counts |
| **12** | `mmm_enrichment.py` | ~7 | MMM state machine |

### 5.3 Full Schema (472 Columns)

**Note:** Complete ordered column list is critical for schema hash reproducibility.

<details>
<summary>Click to expand full schema (472 columns)</summary>

| # | Column Name | Dtype | Nullable | Marker Type | Layer |
|---|-------------|-------|----------|-------------|-------|
| 1 | timestamp | datetime64[ns, UTC] | No | — | Raw |
| 2 | open | float64 | No | CONTINUOUS_FEATURE | Raw |
| 3 | high | float64 | No | CONTINUOUS_FEATURE | Raw |
| 4 | low | float64 | No | CONTINUOUS_FEATURE | Raw |
| 5 | close | float64 | No | CONTINUOUS_FEATURE | Raw |
| 6 | volume | float64 | No | CONTINUOUS_FEATURE | Raw |
| 7 | dealing_range_high | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 8 | dealing_range_low | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 9 | dealing_range_mid | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 10 | dealing_range_size_pips | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 11 | dealing_range_method | object | Yes | CATEGORICAL_TAG | 0 |
| 12 | dealing_range_premium | bool | No | BOOLEAN_MARKER | 0 |
| 13 | dealing_range_discount | bool | No | BOOLEAN_MARKER | 0 |
| 14 | dealing_range_position | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 15 | ipda_20d_high | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 16 | ipda_20d_low | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 17 | ipda_20d_mid | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 18 | ipda_20d_range_pips | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 19 | ipda_20d_premium | bool | No | BOOLEAN_MARKER | 0 |
| 20 | ipda_20d_discount | bool | No | BOOLEAN_MARKER | 0 |
| 21 | ipda_20d_consolidating | bool | No | BOOLEAN_MARKER | 0 |
| 22 | ipda_40d_high | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 23 | ipda_40d_low | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 24 | ipda_40d_mid | float64 | Yes | CONTINUOUS_FEATURE | 0 |
| 25 | ipda_40d_premium | bool | No | BOOLEAN_MARKER | 0 |
| 26-472 | ... | ... | ... | ... | ... |

</details>

*(Full 472-column table available in machine-readable format: `phoenix/contracts/schema_v1.0.0.json`)*

---

## 6. BOOLEAN MARKER REGISTRY

### 6.1 Mirror XOR Scope

The following 110 boolean markers are candidates for Mirror XOR comparison:

```python
mirror_marker_columns = [
    # Layer 0: HTF Analysis
    "dealing_range_premium", "dealing_range_discount",
    "ipda_20d_premium", "ipda_20d_discount", "ipda_20d_consolidating",
    "ipda_40d_premium",
    
    # Layer 0.5: HTF Bias
    "in_ote_bull", "in_ote_bear", "in_htf_pda", "counter_trend_allowed",
    
    # Layer 1: Time Sessions
    "is_dst_us", "is_asia_session", "is_london_session", "is_ny_session",
    "is_session_overlap", "is_kz_asia", "is_kz_lokz", "is_kz_nykz",
    "kz_active", "is_manipulation_hour", "is_how_low_day", "is_trading_hours",
    
    # Layer 2: Reference Levels
    "above_weekly_open", "above_midnight_open",
    "above_asia_range", "below_asia_range", "inside_asia_range",
    "above_pdh", "below_pdl", "between_pd_levels",
    "in_pd_fvg_bull", "in_pd_fvg_bear",
    "in_pd_ob_bull", "in_pd_ob_bear",
    "in_ifvg_bull", "in_ifvg_bear", "in_bpr",
    "above_pwh", "below_pwl",
    "above_london_high", "below_london_low",
    "above_ny_high", "below_ny_low",
    
    # Layer 3: Sweeps
    "sweep_detected", "sweep_is_valid", "sweep_during_kz", "sweep_during_session",
    "sweep_into_pda", "sweep_mss_confirmed", "sweep_displacement_confirmed",
    "sweep_fvg_created", "sweep_is_setup",
    
    # Layer 5: FVG (all timeframes)
    "in_5m_fvg_up", "in_5m_fvg_down", "5m_fvg_up_created", "5m_fvg_down_created",
    "in_15m_fvg_up", "in_15m_fvg_down", "15m_fvg_up_created", "15m_fvg_down_created",
    "in_1h_fvg_up", "in_1h_fvg_down", "1h_fvg_up_created", "1h_fvg_down_created",
    "in_4h_fvg_up", "in_4h_fvg_down", "4h_fvg_up_created", "4h_fvg_down_created",
    "in_daily_fvg_up", "in_daily_fvg_down", "daily_fvg_up_created", "daily_fvg_down_created",
    "in_weekly_fvg_up", "in_weekly_fvg_down", "weekly_fvg_up_created", "weekly_fvg_down_created",
    "in_monthly_fvg_up", "in_monthly_fvg_down", "monthly_fvg_up_created", "monthly_fvg_down_created",
    "entry_fvg_present", "htf_fvg_present",
    
    # Layer 6: Displacement
    "displacement_up", "displacement_down", "is_displacement",
    
    # Layer 7: Structure
    "is_higher_high", "is_lower_high", "is_higher_low", "is_lower_low",
    "structure_break_up", "structure_break_down",
    
    # Layer 7B: DXY/SMT
    "smt_bullish", "smt_bearish",
    
    # Layer 8: Premium/Discount
    "in_premium", "in_discount", "in_ote",
    
    # Layer 9: Order Blocks
    "in_15m_ob_bull", "in_15m_ob_bear",
    "in_1h_ob_bull", "in_1h_ob_bear",
    "in_ob_bull", "in_ob_bear",
    
    # Layer 11: Alignment
    "htf_unanimous", "entry_direction_unanimous", "conflicting_signals",
    "htf_supports_long", "htf_supports_short",
    "entry_matches_htf_long", "entry_matches_htf_short",
    
    # Layer 12: MMM
    "mmm_htf_aligned",
]
```

### 6.2 Marker Sensitivity Classification

| Sensitivity | Meaning | Default |
|-------------|---------|---------|
| `LOW` | Should match exactly across vendors | Most markers |
| `MED` | Minor deviations acceptable (floating-point) | Price-derived thresholds |
| `HIGH` | Expected vendor differences | Time-boundary edge cases |

**Default:** All markers `acceptable_vendor_sensitivity = LOW` unless explicitly classified.

### 6.3 Excluded from Mirror XOR

The following markers are **EXCLUDED** from Mirror XOR due to known vendor variance:

| Column | Reason |
|--------|--------|
| `volume` | Vendors non-comparable (see Section 4) |
| `dxy_*` columns | DXY data may have different source/timing |
| `smt_*` columns | Depends on DXY alignment |

---

## 7. GAP & SYNTHETIC POLICY

### 7.1 Current NEX Behavior (VIOLATION DOCUMENTED)

The NEX `validators.py` currently applies forward-fill to gaps ≤3 bars:

```python
# From validators.py auto_fix():
small_gaps = (time_diffs > pd.Timedelta(minutes=1)) & (
    time_diffs <= pd.Timedelta(minutes=3)
)
# ... forward fills and sets volume=0 for filled bars
```

**This VIOLATES INV-DATA-2:** "No synthetic fills permitted."

### 7.2 Required Phoenix Policy

```yaml
gap_policy: FLAG_ONLY

# Canonical pipeline MUST NOT forward-fill
# Any gap must produce:
filled_bar_requirements:
  is_synthetic: true
  quality_score: "<1.0"
  gap_count: "increment"
  
# Silent fill of OHLC or markers: PROHIBITED
```

### 7.3 Gap Detection Statistics (Current Data)

From EURUSD raw parquet analysis:
- Total bars: 1,933,937
- Gaps > 5 minutes: 303
- Expected gaps (weekends): ~260 (5 years × 52 weeks)
- Unexpected gaps: ~43 (require investigation)

### 7.4 Gap Handling for Phoenix

| Gap Type | Action |
|----------|--------|
| **Weekend** | Expected, no action required |
| **≤3 bars** | Flag as gap, emit `quality_score < 1.0`, do NOT fill |
| **>3 bars** | Flag as gap, emit `quality_score = 0.0`, HALT entries |
| **>1 hour** | CRITICAL — investigate before trading |

---

## 8. DETERMINISM REQUIREMENTS

### 8.1 Enrichment Determinism

**INVARIANT:** All enrichment functions must be deterministic under identical input ordering.

| Requirement | Implementation |
|-------------|----------------|
| Rolling windows | Explicit `window`, `closed`, `min_periods` |
| Tie-breaking | Explicit rules for equal highs/lows |
| Thresholds | No floating epsilon ambiguity |
| Timestamps | Timezone-aware (UTC), never naive |
| Resampling | Stable aggregation rules |

### 8.2 Non-Deterministic Elements (PROHIBITED)

- Random sampling
- System time dependencies
- Unspecified tie-breakers
- Implicit defaults that vary by pandas version

---

## 9. SCHEMA VERSIONING

### 9.1 Current Version

```yaml
schema_version: "1.0.0"
schema_hash: "b848ffe506fd3fff"
created: "2026-01-23"
```

### 9.2 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-23 | Initial lockdown (472 columns) |

### 9.3 Hash Calculation

```python
import hashlib
import json

def calculate_schema_hash(df):
    """Deterministic schema hash."""
    schema = [(col, str(df[col].dtype)) for col in df.columns]
    schema_str = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(schema_str.encode()).hexdigest()[:16]
```

---

## 10. SIGN-OFF GATE DEFINITION

### 10.1 Mechanical Conditions

The contract is **SIGNED OFF** when ALL of the following are TRUE:

| Condition | File/Test |
|-----------|-----------|
| Contract file exists | `phoenix/contracts/ICT_DATA_CONTRACT.md` |
| Schema hash present | `schema_hash: "b848ffe506fd3fff"` in document |
| Schema hash matches runtime | `tests/test_schema_lockdown.py` passes |
| Mirror marker columns defined | `mirror_marker_columns` list in Section 6 |
| Timestamp convention declared | `timestamp_meaning: bar_start_time_utc` |
| Volume semantics declared | Section 4 complete with `volume_comparability` |
| Gap policy declared | `gap_policy: FLAG_ONLY` in Section 7 |
| Schema version present | `schema_version: "1.0.0"` |

### 10.2 Test Stub Reference

```python
# tests/test_schema_lockdown.py

import pytest
import pandas as pd
import hashlib
import json

EXPECTED_SCHEMA_HASH = "b848ffe506fd3fff"
EXPECTED_COLUMNS = 472

def test_schema_hash_matches():
    """Verify enriched parquet matches locked schema."""
    df = pd.read_parquet("nex_lab/data/features/EURUSD_1m_enriched.parquet")
    
    schema = [(col, str(df[col].dtype)) for col in df.columns]
    schema_str = json.dumps(schema, sort_keys=True)
    actual_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    
    assert actual_hash == EXPECTED_SCHEMA_HASH, \
        f"Schema drift detected! Expected {EXPECTED_SCHEMA_HASH}, got {actual_hash}"

def test_column_count():
    """Verify column count matches contract."""
    df = pd.read_parquet("nex_lab/data/features/EURUSD_1m_enriched.parquet")
    assert len(df.columns) == EXPECTED_COLUMNS, \
        f"Column count mismatch: expected {EXPECTED_COLUMNS}, got {len(df.columns)}"

def test_boolean_markers_exist():
    """Verify all mirror markers exist in schema."""
    from phoenix.contracts.mirror_markers import MIRROR_MARKER_COLUMNS
    
    df = pd.read_parquet("nex_lab/data/features/EURUSD_1m_enriched.parquet")
    missing = [col for col in MIRROR_MARKER_COLUMNS if col not in df.columns]
    
    assert not missing, f"Missing mirror markers: {missing}"

def test_timestamp_is_utc():
    """Verify timestamps are UTC."""
    df = pd.read_parquet("nex_lab/data/features/EURUSD_1m_enriched.parquet")
    assert str(df['timestamp'].dt.tz) == "UTC", \
        f"Timestamps must be UTC, got {df['timestamp'].dt.tz}"
```

---

## 11. APPENDIX: VENDOR COMPARISON MATRIX

| Aspect | Dukascopy | IBKR |
|--------|-----------|------|
| **Data Type** | Historical CSV | Live API |
| **Price Basis** | Last tick | Midpoint (bid+ask)/2 |
| **Volume** | Tick count (float) | None (0.0) |
| **Coverage** | 2020-2025 | 2025+ |
| **Gaps** | Pre-cleaned | May have gaps |
| **Timezone** | UTC | UTC |
| **Bar Alignment** | 60s fixed | 60s fixed |

---

## 12. REVISION PROTOCOL

**To amend this contract:**

1. Create branch: `schema-v1.x.x`
2. Update schema with new columns
3. Recalculate `schema_hash`
4. Update `schema_version`
5. Add entry to Version History
6. Run `test_schema_lockdown.py`
7. PR review + merge
8. Re-run Mirror Test with new schema

**INVARIANT:** Schema changes require ceremony. No silent updates.

---

**Contract Status:** LOCKED  
**Schema Hash:** `b848ffe506fd3fff`  
**Mirror Test:** READY TO PROCEED

---

*The River is sacred. This contract defines its banks.*

**OINK OINK.** 🐗🔥
