# VISUAL ANCHOR MAP

**SPRINT:** 26.TRACK_C  
**DATE:** 2026-01-25  
**PURPOSE:** CSO sight calibration for Olya's ICT methodology

---

## OVERVIEW

Maps what Olya sees on a chart → what CSO computes from data.
Identifies gaps where human interpretation cannot be mechanized.

---

## COVERAGE SUMMARY

| Category | ICT Concepts | Machine-Readable | Coverage |
|----------|--------------|------------------|----------|
| Time & Sessions | 8 | 8 | 100% |
| Reference Levels | 12 | 10 | 83% |
| Liquidity | 6 | 5 | 83% |
| Structure | 8 | 7 | 88% |
| PDAs (Imbalances) | 10 | 9 | 90% |
| HTF Bias | 6 | 5 | 83% |
| Composite | 5 | 3 | 60% |
| **TOTAL** | **55** | **47** | **85%** |

---

## ICT CONCEPT → DATA COLUMN MAPPING

### 1. Time & Sessions (100% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| Asia Session | Chart hours shaded | `is_asia_session` | ✓ | 19:00-00:00 NY |
| London Session | Chart hours shaded | `is_london_session` | ✓ | 02:00-05:00 NY |
| NY Session | Chart hours shaded | `is_ny_session` | ✓ | 07:00-10:00 NY |
| Asia Kill Zone | High-conviction window | `is_kz_asia` | ✓ | 20:00-21:00 NY |
| LOKZ | High-conviction window | `is_kz_lokz` | ✓ | 03:00-04:00 NY |
| NYKZ | High-conviction window | `is_kz_nykz` | ✓ | 08:00-09:00 NY |
| Day of Week | Calendar awareness | `day_of_week` | ✓ | Monday=0 |
| DST | Clock shift awareness | `is_dst_us` | ✓ | US DST tracked |

### 2. Reference Levels (83% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| Asia High | Horizontal line | `asia_high` | ✓ | |
| Asia Low | Horizontal line | `asia_low` | ✓ | |
| Asia Range CE | 50% of Asia | `asia_range_ce` | ✓ | |
| PDH | Previous day high line | `pdh` | ✓ | |
| PDL | Previous day low line | `pdl` | ✓ | |
| PWH | Previous week high | `pwh` | ✓ | |
| PWL | Previous week low | `pwl` | ✓ | |
| Weekly Open | Week open level | `weekly_open_price` | ✓ | |
| Midnight Open | Midnight NY level | `ny_midnight_open` | ✓ | |
| Monthly Levels | Monthly extremes | `monthly_*` | ✓ | |
| **Quarterly Levels** | Quarterly extremes | — | ✗ | **GAP** |
| **True Day Open** | 18:00 NY open | — | ✗ | **GAP** |

### 3. Liquidity & Sweeps (83% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| Sweep | Wick beyond level | `sweep_detected` | ✓ | |
| Liquidity Pool | Cluster of stops | `sweep_target_type` | ✓ | PDH/PDL/PWH/PWL |
| Sweep Quality | Clean vs messy | `sweep_extension_pips` | ✓ | |
| Sweep Into PDA | Swept into zone | `sweep_into_pda` | ✓ | |
| Sweep Direction | Bull/bear sweep | `sweep_direction` | ✓ | |
| **Retail Liquidity** | Obvious S/R clusters | — | ✗ | **GAP: Pattern recognition** |

### 4. Structure (88% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| Higher High | Chart annotation | `is_higher_high` | ✓ | |
| Higher Low | Chart annotation | `is_higher_low` | ✓ | |
| Lower High | Chart annotation | `is_lower_high` | ✓ | |
| Lower Low | Chart annotation | `is_lower_low` | ✓ | |
| Break of Structure | Level breach | `structure_break_up/down` | ✓ | |
| Order Flow | HH+HL or LH+LL | `order_flow_bullish` | ✓ | |
| Change of Character | Trend shift | `choch_detected` | ✓ | MSS proxy |
| **Market Structure Shift** | Complex evaluation | — | ⚠ | **COMPOSITE** |

### 5. PDAs — Price Delivery Arrays (90% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| FVG (Fair Value Gap) | 3-candle gap | `in_*_fvg_up/down` | ✓ | All TFs |
| Bullish OB | Down candle before up | `in_*_ob_bull` | ✓ | 15m, 1H |
| Bearish OB | Up candle before down | `in_*_ob_bear` | ✓ | 15m, 1H |
| IFVG | Inverted FVG | `in_ifvg_bull/bear` | ✓ | |
| BPR | Balanced Price Range | `in_bpr` | ✓ | |
| OTE Zone | 61.8%-78.6% fib | `in_ote` | ✓ | |
| Premium Zone | Above 50% | `in_premium` | ✓ | |
| Discount Zone | Below 50% | `in_discount` | ✓ | |
| Consequent Encroachment | 50% of imbalance | `*_ce` columns | ✓ | |
| **Breaker Block** | Failed OB becomes S/R | — | ✗ | **GAP** |

### 6. HTF Bias (83% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| Daily Bias | D1 chart trend | `daily_bias` | ✓ | |
| Weekly Bias | W1 chart trend | `weekly_bias` | ✓ | |
| Monthly Bias | M1 chart trend | `monthly_bias` | ✓ | |
| IPDA Zone | Premium/discount vs 20/40d | `ipda_*_premium/discount` | ✓ | |
| Dealing Range | Current range context | `dealing_range_premium/discount` | ✓ | |
| **Narrative** | Fundamental context | — | ✗ | **GAP: Human domain** |

### 7. Composite Evaluation (60% Coverage)

| ICT Concept | Olya Sees | Data Column | Computed | Notes |
|-------------|-----------|-------------|----------|-------|
| 4Q Gate | Checklist evaluation | `alignment_*` | ⚠ | Partial |
| Entry Confluence | Multiple confirmations | `entry_fvg_present` etc | ✓ | |
| SMT Divergence | DXY vs pair divergence | `smt_bullish/bearish` | ✓ | Requires DXY |
| **Model Setup** | Full ICT model | — | ✗ | **GAP: Human evaluation** |
| **News Awareness** | Event calendar | — | ✗ | **GAP: External data** |

---

## GAPS REQUIRING HUMAN INTERPRETATION

### Critical Gaps (Cannot Mechanize)

| Gap | Why Human Required | Mitigation |
|-----|-------------------|------------|
| **Narrative/Fundamentals** | Requires news interpretation | Olya provides via CSO session |
| **Model Selection** | Which ICT model applies | Rule-based model selector |
| **Context Quality** | "Does this setup feel right?" | Confidence scoring |

### Addressable Gaps (Future Enhancement)

| Gap | Implementation Path | Priority |
|-----|---------------------|----------|
| Quarterly Levels | Add quarterly resample | Medium |
| True Day Open | Track 18:00 NY | Low |
| Breaker Blocks | Track failed OBs | Medium |
| Retail Liquidity | Pattern detection | Low |
| News Awareness | External calendar API | High |

---

## CALIBRATION TESTS

### How to Verify CSO "Sees" Correctly

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Session Match | Compare `is_*_session` to chart | 100% match |
| Reference Level Match | Compare `pdh`, `pdl` to chart | Within 0.1 pip |
| FVG Detection | Manual FVG count vs computed | >95% match |
| OB Detection | Manual OB count vs computed | >90% match |
| Sweep Detection | Manual sweep count vs computed | >85% match |
| Structure Match | Manual HH/HL vs computed | >90% match |

### Calibration Procedure

```yaml
calibration_session:
  duration: 2 hours
  participants: [Olya, CSO Display]
  symbols: [EURUSD, GBPUSD]
  timeframe: Live 1m + 15m

steps:
  1. Olya marks PDAs on chart
  2. CSO displays computed PDAs
  3. Compare and document discrepancies
  4. Adjust thresholds if systematic error
  5. Re-run calibration tests
  6. Document final parameters
```

---

## ICT 4Q GATE MAPPING

Olya's 4 Questions → CSO Evaluation:

| Question | Olya Asks | CSO Computes |
|----------|-----------|--------------|
| Q1: HTF Order Flow | "Is D1/W1 bullish or bearish?" | `daily_bias`, `weekly_bias` |
| Q2: Dealing Range | "Premium or discount?" | `dealing_range_premium/discount` |
| Q3: PDA Destination | "Where is price going?" | `sweep_target_type` |
| Q4: Timing | "Is this the right time?" | `is_kz_*`, `kz_active` |

### 4Q Gate Pass Columns

```yaml
q1_pass: htf_supports_long OR htf_supports_short
q2_pass: in_premium (for shorts) OR in_discount (for longs)
q3_pass: sweep_into_pda == TRUE
q4_pass: kz_active == TRUE

full_gate_pass: q1_pass AND q2_pass AND q3_pass AND q4_pass
```

---

## OLYA INTERVIEW AGENDA

Based on gaps identified, questions for Olya sessions:

### Session 1: Model Selection
1. When do you choose London Swing vs NY Reversal?
2. What makes you skip a "valid" setup?
3. How do you weigh conflicting HTF vs LTF signals?

### Session 2: Context Quality
1. What makes a sweep "clean" vs "messy"?
2. How do you assess liquidity pool significance?
3. When is a PDA "stale" and shouldn't be traded?

### Session 3: News Awareness
1. Which events do you never trade through?
2. How far before/after news do you pause?
3. How do you interpret surprise vs expected data?

---

## SUMMARY

```yaml
total_coverage: 85%
machine_readable: 47/55 concepts
critical_gaps: 3 (narrative, model selection, context quality)
addressable_gaps: 5 (quarterly, breaker, etc)

calibration_required: TRUE
calibration_method: Olya + CSO side-by-side

recommendation: Proceed to CSO build with current coverage
flag_for_olya: model_selection, context_quality, news_awareness
```

---

*Generated: Sprint 26 Track C*
