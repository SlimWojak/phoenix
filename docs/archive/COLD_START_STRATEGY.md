# COLD START STRATEGY

**SPRINT:** 26.TRACK_C  
**DATE:** 2026-01-25  
**PURPOSE:** Define Phoenix/CSO bootstrap from zero state

---

## OVERVIEW

Cold start = Phoenix boots with no prior state.
CSO cannot emit valid signals until warmup complete.

---

## WARMUP REQUIREMENTS

### Minimum Data Before Signals Valid

| Indicator | Warmup Bars (1m) | Warmup Time | Rationale |
|-----------|------------------|-------------|-----------|
| ATR(14) | 14 | 14 min | Need 14 periods minimum |
| Swing Detection | 60 | 1 hour | N-bar lookback for HH/HL |
| Asia Range | 540 | 9 hours | Full Asia session |
| PDH/PDL | 1440 | 24 hours | Previous full day |
| PWH/PWL | 10080 | 7 days | Previous full week |
| Structure (HTF) | 2880 | 48 hours | 2 days for context |
| OTE Zones | 2880 | 48 hours | Needs swing + PDH/PDL |

### Total Warmup

```yaml
warmup_bars: 10080
warmup_duration: 7 days
critical_warmup: 2880 bars (48 hours)
minimum_warmup: 1440 bars (24 hours)
```

**Tiered Signals:**
- `0-1440 bars`: NO SIGNALS (missing PDH/PDL)
- `1440-2880 bars`: DEGRADED (missing structure context)
- `2880-10080 bars`: LIMITED (missing PWH/PWL)
- `>10080 bars`: FULL (all indicators valid)

---

## REQUIRED HISTORY

| Level | Duration | Bars (1m) | Purpose |
|-------|----------|-----------|---------|
| Minimum | 24 hours | 1,440 | PDH/PDL, basic signals |
| Standard | 7 days | 10,080 | PWH/PWL, full context |
| Optimal | 30 days | 43,200 | IPDA(20), dealing range |
| Deep | 60 days | 86,400 | IPDA(40), quarterly levels |

**Recommendation:** Standard (7 days) for production.
Deep (60 days) for initial calibration.

---

## BOOTSTRAP SEQUENCE

### Step 1: Data Acquisition

```yaml
order: 1
action: fetch_historical_data
inputs:
  symbols: [EURUSD, GBPUSD, USDJPY, USDCHF, USDCAD, AUDUSD]
  timeframe: 1m
  lookback: 7 days (minimum) or 60 days (calibration)
output: raw OHLCV in River
duration: ~30 seconds per symbol
```

### Step 2: Initial Enrichment

```yaml
order: 2
action: run_enrichment_pipeline
inputs:
  raw_bars: from Step 1
  layers: [L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L11, L12]
output: enriched bars with all 472 columns
duration: ~60 seconds per symbol
```

### Step 3: Reference Level Initialization

```yaml
order: 3
action: initialize_reference_levels
inputs:
  enriched_bars: from Step 2
compute:
  - asia_range: current session
  - pdh_pdl: previous day
  - pwh_pwl: previous week
  - swing_points: last 48 hours
  - dealing_range: last 60 days
output: reference_state dict
duration: ~5 seconds
```

### Step 4: HTF Context Build

```yaml
order: 4
action: build_htf_context
inputs:
  enriched_bars: from Step 2
  reference_state: from Step 3
compute:
  - daily_bias: bullish/bearish/neutral
  - weekly_bias: bullish/bearish/neutral
  - ipda_zone: premium/discount/equilibrium
  - order_flow: bullish/bearish
output: htf_context dict
duration: ~10 seconds
```

### Step 5: CSO Initialization

```yaml
order: 5
action: initialize_cso
inputs:
  htf_context: from Step 4
  reference_state: from Step 3
actions:
  - register with GovernanceMesh
  - run self_check()
  - emit initial_state_hash
output: CSO ready for process_state()
duration: ~2 seconds
```

### Step 6: Signal Validation

```yaml
order: 6
action: validate_warmup_complete
checks:
  - pdh_pdl_available: TRUE
  - asia_range_calculated: TRUE
  - swing_points_detected: TRUE
  - htf_bias_set: TRUE
output: warmup_complete flag
action_if_fail: mark CSO DEGRADED, continue with limited signals
```

---

## TOTAL BOOTSTRAP TIME

| Phase | Duration |
|-------|----------|
| Data fetch (6 symbols) | ~3 minutes |
| Enrichment (6 symbols) | ~6 minutes |
| Reference init | ~30 seconds |
| HTF context | ~1 minute |
| CSO init | ~5 seconds |
| **Total** | **~10-12 minutes** |

---

## STATE PERSISTENCE

### What Survives Restart

| State | Persistence | Recovery |
|-------|-------------|----------|
| Raw bars | Parquet (River) | Load from file |
| Enriched bars | Parquet (River) | Load from file |
| Reference levels | JSON (Boardroom) | Recompute from bars |
| HTF context | JSON (Boardroom) | Recompute from bars |
| CSO decisions | Beads (Boardroom) | Load from DB |
| Open positions | DB (Execution) | Load from broker |

### What Is Ephemeral

| State | Lifetime | On Restart |
|-------|----------|------------|
| In-flight calculations | Process | Recompute |
| Streaming bar buffer | Session | Refetch last N bars |
| Websocket connections | Session | Reconnect |
| Local halt signals | Session | Clear |

---

## RECOVERY PROCEDURE

### After Clean Shutdown

```yaml
steps:
  1. Load persisted state:
     - enriched_bars from parquet
     - reference_state from JSON
     - beads from Boardroom
  2. Compute delta:
     - last_enriched_ts vs current_time
     - fetch missing bars if gap
  3. Update enrichment:
     - incremental enrichment on new bars only
  4. Initialize CSO:
     - load bead state
     - verify state_hash matches
  5. Resume:
     - CSO.lifecycle_state = RUNNING

recovery_time: ~2-3 minutes
```

### After Crash (No Clean Shutdown)

```yaml
steps:
  1. Check data integrity:
     - verify parquet not corrupted
     - verify Boardroom beads intact
  2. Identify recovery point:
     - last_known_good_state_hash
     - last_bead_timestamp
  3. Full recompute from recovery point:
     - re-enrich bars from recovery_point
     - recalculate reference levels
     - rebuild HTF context
  4. Verify state:
     - compute_state_hash() matches expected
  5. Resume with DEGRADED flag:
     - CSO.quality_score = 0.80
     - emit CRASH_RECOVERY bead

recovery_time: ~5-10 minutes
```

### After Data Gap (Network Outage)

```yaml
detection:
  - timestamp gap > 5 minutes
  - missing_bars_count > threshold

steps:
  1. Fetch missing bars from broker
  2. If gap > 24 hours:
     - flag MAJOR_GAP
     - require human approval to proceed
  3. If gap < 24 hours:
     - fill with synthetic flag
     - quality_score penalty
  4. Re-enrich affected range
  5. Recalculate affected reference levels

gap_policy: FLAG_ONLY (no silent fill)
```

---

## CSO WARMUP STATES

```python
class WarmupState(Enum):
    COLD = "COLD"           # No data, no signals
    WARMING = "WARMING"     # <1440 bars, no signals
    LIMITED = "LIMITED"     # 1440-2880 bars, degraded signals
    PARTIAL = "PARTIAL"     # 2880-10080 bars, missing PWH/PWL
    READY = "READY"         # >10080 bars, full signals
```

### State Machine

```
COLD → fetch_data → WARMING → enrich → LIMITED → htf_build → PARTIAL → pwh_pwl → READY
  ↓                    ↓                  ↓                     ↓
[error]            [error]            [error]               [error]
  ↓                    ↓                  ↓                     ↓
HALT               HALT               DEGRADED              DEGRADED
```

---

## SIGNAL VALIDITY BY WARMUP

| State | PDH/PDL | Asia | Structure | PWH/PWL | Signal Quality |
|-------|---------|------|-----------|---------|----------------|
| COLD | ✗ | ✗ | ✗ | ✗ | NO SIGNAL |
| WARMING | ✗ | ✗ | ✗ | ✗ | NO SIGNAL |
| LIMITED | ✓ | ✓ | ✗ | ✗ | 50% (intraday only) |
| PARTIAL | ✓ | ✓ | ✓ | ✗ | 80% (missing weekly) |
| READY | ✓ | ✓ | ✓ | ✓ | 100% |

---

## CONFIGURATION

```yaml
# Cold Start Config
cold_start:
  minimum_warmup_bars: 1440
  standard_warmup_bars: 10080
  optimal_warmup_bars: 43200
  
  warmup_timeout_minutes: 30
  
  signal_policy:
    cold: NO_SIGNAL
    warming: NO_SIGNAL
    limited: ADVISORY_ONLY
    partial: TRADE_REDUCED_SIZE
    ready: FULL_TRADE
    
  recovery:
    max_gap_hours: 24
    gap_policy: FLAG_ONLY
    crash_quality_penalty: 0.20
```

---

*Generated: Sprint 26 Track C*
