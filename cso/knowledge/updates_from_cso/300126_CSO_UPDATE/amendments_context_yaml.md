# AMENDMENTS: context.yaml
## Missing Components to Add
## Date: January 30, 2026
## Purpose: Add 3Q framework, P/D calculation, PDA detection per BLUR-001/002/003

---

## 🤖 INSTRUCTIONS FOR CTO MACHINE

**File to modify:** `context.yaml`

**Action:** INSERT new sections (do NOT replace existing content)

**Total amendments:** 5
- Amendment 1: Add 3Q Framework section (LARGE - ~150 lines)
- Amendment 2: Add P/D State Calculation section (~40 lines)
- Amendment 3: Add PDA Detection Registry section (~120 lines)
- Amendment 4: Update output format section (REPLACE one section)
- Amendment 5: Update file header label (REPLACE one line)

**Verification after applying:**
- File should parse as valid YAML
- Signal count should increase from 21 to 24
- References in conditions.yaml should now resolve

**Estimated time:** 30-45 minutes

---

## AMENDMENT 1: Add 3Q Framework (BLUR-001)

**🤖 MACHINE INSTRUCTION:**
- **Action:** INSERT new section
- **Location:** After line 220 (after `daily_objective` section ends)
- **Before what:** The next major section (likely a comment line starting with `#`)
- **Size:** ~150 lines
- **Verification:** Search file for "SIG-CTX-Q1" - should find it

**Location:** Insert after `daily_objective` section (around line 220)

**Reason:** Per BLUR-001, Context OWNS the 3Q framework. Currently conditions.yaml references `context.Q1_location`, `context.Q2_objective`, `context.Q3_respect` but these don't exist in context.yaml.

**Source:** Extract from LAYER_0_HTF_CONTEXT_CLEAN.md lines 1684-1800

**Add this section:**

```yaml
# =============================================================================
# 3Q FRAMEWORK (BIAS SYNTHESIS) - OWNER per BLUR-001
# =============================================================================
# Context CALCULATES bias, Conditions CONSUMES it

bias_framework:
  id: "SIG-CTX-3Q"
  name: "Three Questions Framework"
  purpose: "Synthesize daily trade bias from HTF context"
  execution: "00:00 NY daily, frozen until next day"
  note: "OWNER role per BLUR-001 - conditions.yaml reads from this"
  ref: "L0:1350-1500, CSO:filing_blurs_fixes_v1.yaml:BLUR-001"
  
  Q1_location:
    id: "SIG-CTX-Q1"
    question: "Where is price RIGHT NOW?"
    purpose: "Determine current price position in context"
    
    outputs:
      - {col: position_pct, type: float, desc: "% position in dealing range"}
      - {col: zone, type: str, values: [premium, discount, equilibrium]}
      - {col: nearest_pda, type: dict, desc: "Closest PDA and distance"}
      - {col: in_pda, type: bool, desc: "Currently inside PDA zone"}
    
    zones:
      deep_discount: "<25%"
      discount: "25-50%"
      equilibrium: "~50%"
      premium: "50-75%"
      deep_premium: ">75%"
    
    calculation:
      position_pct: "(current_price - dealing_range_low) / (dealing_range_high - dealing_range_low) * 100"
      zone: "compare(current_price, dealing_range_equilibrium)"
      nearest_pda: "find_nearest(current_price, all_pdas)"
      in_pda: "check_inside_any_pda(current_price, all_pdas)"
    
    ref: "L0:1352-1388"
  
  Q2_objective:
    id: "SIG-CTX-Q2"
    question: "Where is price LIKELY TO GO?"
    purpose: "Identify clear external draw on liquidity"
    requires: "daily_mss.exists == True"
    
    outputs:
      - {col: dol_primary, type: dict, desc: "Primary target"}
      - {col: dol_secondary, type: dict, desc: "Secondary target"}
      - {col: expected_path, type: str, desc: "Narrative description"}
    
    target_priority:
      1: "MMXM High/Low (original consolidation)"
      2: "PDH/PDL"
      3: "PWH/PWL"
      4: "Daily/Weekly FVG"
    
    filters:
      - "Target must be external (unreached)"
      - "Target must align with daily_mss.direction"
      - "Target status must be LIQUIDITY_UNDELIVERED"
    
    logic:
      - {step: 1, action: "Get all liquidity levels in direction"}
      - {step: 2, action: "Filter by status == LIQUIDITY_UNDELIVERED"}
      - {step: 3, action: "Sort by priority then distance"}
      - {step: 4, action: "Select nearest high-priority target"}
      - {step: 5, action: "If no target found → return None"}
    
    no_objective_result: "trade_bias = none"
    
    ref: "L0:1390-1429"
  
  Q3_respect:
    id: "SIG-CTX-Q3"
    question: "Where is price COMING FROM?"
    purpose: "Determine HTF directional intent from behavior"
    
    outputs:
      - {col: htf_direction, values: [bullish, bearish, neutral]}
      - {col: confidence, values: [high, medium, low]}
      - {col: structure_bias, type: str, desc: "From order flow"}
      - {col: pda_bias, type: str, desc: "From PDA respect"}
    
    components:
      structure_component:
        source: "daily_order_flow"
        bullish: "HH + HL pattern"
        bearish: "LH + LL pattern"
        ranging: "Mixed or insufficient data"
      
      pda_component:
        method: "Count respected PDAs by direction"
        bullish: "More bullish PDAs held than bearish"
        bearish: "More bearish PDAs held than bullish"
        neutral: "Equal or unclear"
    
    combination_logic:
      - {condition: "structure_bias == pda_bias", result: "htf_direction = bias", confidence: high}
      - {condition: "structure_bias == ranging", result: "htf_direction = pda_bias", confidence: medium}
      - {condition: "structure_bias != pda_bias", result: "htf_direction = neutral", confidence: low}
    
    ref: "L0:1431-1475"
  
  bias_synthesis:
    id: "SIG-CTX-BIAS-SYNTHESIS"
    name: "Trade Bias Synthesis"
    purpose: "Combine 3 questions into final trade bias"
    inputs: [q1_location, q2_objective, q3_respect]
    
    outputs:
      - {col: trade_bias, values: [long_only, short_only, both, none]}
      - {col: bias_note, type: str, desc: "Explanation"}
    
    decision_tree:
      - {check: "htf_direction == neutral", result: "trade_bias = none", reason: "No clear HTF direction"}
      - {check: "zone == equilibrium", result: "trade_bias = none", reason: "At equilibrium - no directional edge"}
      - {check: "dol_primary == None", result: "trade_bias = none", reason: "No clear objective"}
      - {check: "htf_direction == bullish", result: "trade_bias = long_only", reason: "Bullish HTF context"}
      - {check: "htf_direction == bearish", result: "trade_bias = short_only", reason: "Bearish HTF context"}
    
    frozen_until: "next 00:00 NY"
    
    ref: "L0:1477-1505"
```

---

## AMENDMENT 2: Add P/D State Calculation (BLUR-002)

**🤖 MACHINE INSTRUCTION:**
- **Action:** INSERT new section
- **Location:** Immediately after Amendment 1 (after the 3Q framework section ends)
- **Size:** ~40 lines
- **Verification:** Search file for "SIG-CTX-PD-STATE" - should find it

**Location:** Insert after 3Q framework section

**Reason:** Per BLUR-002, Foundation DEFINES formula, Context CALCULATES state, Conditions READS it. Currently conditions.yaml references `context.structural_pd_state` which doesn't exist.

**Add this section:**

```yaml
# =============================================================================
# PREMIUM/DISCOUNT STATE CALCULATION - OWNER per BLUR-002
# =============================================================================
# Foundation defines formula, Context calculates, Conditions reads

structural_pd_state:
  id: "SIG-CTX-PD-STATE"
  name: "Structural Premium/Discount State"
  source_formula: "foundation.premium_discount"
  note: "OWNER role per BLUR-002 - conditions.yaml reads from this"
  ref: "L0:694-720, CSO:filing_blurs_fixes_v1.yaml:BLUR-002"
  
  inputs:
    - current_price
    - dealing_range_equilibrium
    - dealing_range_high
    - dealing_range_low
  
  calculation:
    pd_state:
      formula: "compare(current_price, dealing_range_equilibrium)"
      values:
        premium: "current_price > equilibrium"
        discount: "current_price < equilibrium"
        equilibrium: "current_price == equilibrium"
    
    position_pct:
      formula: "(current_price - dealing_range_low) / (dealing_range_high - dealing_range_low) * 100"
      range: [0, 100]
    
    distance_from_eq:
      formula: "abs(current_price - dealing_range_equilibrium) * 10000"
      unit: "pips"
  
  outputs:
    - {col: pd_state, values: [premium, discount, equilibrium]}
    - {col: position_pct, type: float, range: [0, 100]}
    - {col: distance_from_eq_pips, type: float}
  
  validation:
    - {check: "dealing_range exists", else: "pd_state = unknown"}
    - {check: "equilibrium defined", else: "pd_state = unknown"}
```

---

## AMENDMENT 3: Add PDA Detection Registry (BLUR-003)

**🤖 MACHINE INSTRUCTION:**
- **Action:** INSERT new section
- **Location:** Immediately after Amendment 2 (after P/D state section ends)
- **Size:** ~120 lines
- **Verification:** Search file for "SIG-CTX-PDA-DETECT" - should find it

**Location:** Insert after structural_pd_state section

**Reason:** Per BLUR-003, Context DETECTS and REGISTERS PDAs (immutable metadata), Conditions TRACKS STATUS (mutable evaluation). Currently context.yaml only lists PDA types without detection logic.

**Add this section:**

```yaml
# =============================================================================
# PDA DETECTION & REGISTRY - OWNER per BLUR-003
# =============================================================================
# Context DETECTS and REGISTERS (immutable), Conditions TRACKS STATUS (mutable)

pda_detection:
  id: "SIG-CTX-PDA-DETECT"
  name: "PDA Detection & Registration"
  purpose: "Detect PDAs from price action, store immutable metadata"
  note: "OWNER role per BLUR-003 - conditions.yaml evaluates status"
  ref: "L0:757-820, CSO:filing_blurs_fixes_v1.yaml:BLUR-003"
  
  fvg_detection:
    id: "SIG-CTX-PDA-FVG"
    name: "FVG Detection"
    source_definition: "foundation.FVG"
    logic: "uses foundation.FVG.detection (universal across all TFs)"
    
    detection_rule:
      bullish: "candle_A.high < candle_C.low"
      bearish: "candle_A.low > candle_C.high"
    
    outputs:
      - {col: fvg_id, type: str, desc: "Unique identifier (timestamp-based)"}
      - {col: fvg_high, type: float, desc: "Top boundary (wick)"}
      - {col: fvg_low, type: float, desc: "Bottom boundary (wick)"}
      - {col: fvg_ce, type: float, desc: "Consequent Encroachment (50%)"}
      - {col: fvg_mid, type: float, desc: "Midpoint"}
      - {col: fvg_direction, values: [bullish, bearish]}
      - {col: fvg_timeframe, values: [5m, 15m, 1h, 4h, daily, weekly]}
      - {col: fvg_timestamp, type: datetime, desc: "When formed"}
      - {col: fvg_size_pips, type: float, desc: "Gap size"}
    
    note: "Immutable - stored at detection, never changed"
    ref: "foundation.FVG, L0:222-298"
  
  ob_detection:
    id: "SIG-CTX-PDA-OB"
    name: "Order Block Detection"
    source_definition: "foundation.OB"
    logic: "Last opposing candle before displacement"
    
    detection_rule:
      bullish_ob: "Last DOWN candle before bullish displacement"
      bearish_ob: "Last UP candle before bearish displacement"
    
    outputs:
      - {col: ob_id, type: str, desc: "Unique identifier"}
      - {col: ob_body_high, type: float, desc: "Body top (NOT wick)"}
      - {col: ob_body_low, type: float, desc: "Body bottom (NOT wick)"}
      - {col: ob_mt, type: float, desc: "Mean Threshold (50% of body)"}
      - {col: ob_direction, values: [bullish, bearish]}
      - {col: ob_timeframe, values: [5m, 15m, 1h, 4h, daily]}
      - {col: ob_timestamp, type: datetime}
      - {col: ob_body_pct, type: float, desc: "Body % of total range"}
      - {col: ob_quality, values: [beefy, acceptable, weak], desc: "Based on body_pct"}
    
    quality_grading:
      beefy: "body_pct > 70%"
      acceptable: "body_pct > 50%"
      weak: "body_pct <= 50%"
    
    note: "Immutable - stored at detection, BODY ONLY (not wicks)"
    ref: "foundation.OB, NEX:L9"
  
  ifvg_detection:
    id: "SIG-CTX-PDA-IFVG"
    name: "Inverse FVG Detection"
    definition: "FVG broken with displacement - polarity flips"
    
    outputs:
      - {col: ifvg_id, type: str}
      - {col: ifvg_original_fvg_id, type: str, desc: "Reference to original FVG"}
      - {col: ifvg_high, type: float}
      - {col: ifvg_low, type: float}
      - {col: ifvg_direction, values: [bullish, bearish], desc: "Flipped from original"}
      - {col: ifvg_timestamp, type: datetime}
    
    note: "Created when FVG broken with displacement"
    ref: "foundation.IFVG, NEX:L5"
  
  bpr_detection:
    id: "SIG-CTX-PDA-BPR"
    name: "Balanced Price Range Detection"
    definition: "Overlapping bullish and bearish FVGs"
    
    outputs:
      - {col: bpr_id, type: str}
      - {col: bpr_high, type: float, desc: "Top of overlap"}
      - {col: bpr_low, type: float, desc: "Bottom of overlap"}
      - {col: bpr_fvg_bull_id, type: str, desc: "Bullish FVG component"}
      - {col: bpr_fvg_bear_id, type: str, desc: "Bearish FVG component"}
      - {col: bpr_timestamp, type: datetime}
    
    note: "Strong reaction zones - balance of opposing flows"
    ref: "foundation.BPR, NEX:L5"
  
  pda_registry:
    description: "Central registry of all detected PDAs (immutable)"
    structure: |
      {
        pda_id: str,           # Unique identifier
        pda_type: str,         # fvg | ob | ifvg | bpr
        price_levels: {...},   # Type-specific boundaries
        timeframe: str,        # Detection timeframe
        timestamp: datetime,   # When formed
        direction: str,        # bullish | bearish
        metadata: {...}        # Type-specific immutable data
      }
    
    persistence: "Stored until no longer relevant (MSS reset, age limit, etc.)"
    
    note: |
      Context creates and maintains this registry.
      Conditions READS from registry to evaluate STATUS.
      Status (respected/broken/untested) is MUTABLE (tracked in Conditions).
      Registry itself is IMMUTABLE (set at detection).
```

---

## AMENDMENT 4: Update Output Format Section

**🤖 MACHINE INSTRUCTION:**
- **Action:** REPLACE existing content
- **Location:** Find section around line 390+ in the `layer_0_context` output format
- **Search for:** `bias: [q1_location, q2_objective, q3_respect, trade_bias, bias_note]`
- **Replace with:** The expanded YAML structure below
- **Size:** Replace 1 line with ~20 lines
- **Verification:** Old format was single line, new format is nested structure

**Location:** Find the `layer_0_context` output format section (around line 390+)

**Action:** Update the `bias` subsection to include the new 3Q outputs

**Replace this:**
```yaml
bias: [q1_location, q2_objective, q3_respect, trade_bias, bias_note]
```

**With this:**
```yaml
bias:
  q1_location:
    position_pct: float
    zone: str
    nearest_pda: dict
    in_pda: bool
  
  q2_objective:
    dol_primary: dict
    dol_secondary: dict
    expected_path: str
  
  q3_respect:
    htf_direction: str
    confidence: str
    structure_bias: str
    pda_bias: str
  
  synthesis:
    trade_bias: str
    bias_note: str
```

---

## AMENDMENT 5: Update Signal Counts in File Header

**🤖 MACHINE INSTRUCTION:**
- **Action:** REPLACE one line
- **Location:** Top of file (around line 9)
- **Search for exact line:** `label: "v1.0 — Updated with GAP 7-9 resolutions + blur fixes (3Q owner, P/D owner, PDA detection)"`
- **Replace with:** New label below
- **Verification:** Line should end with "...PDA detection added)"

**Location:** Top of file, update label

**Change from:**
```yaml
label: "v1.0 — Updated with GAP 7-9 resolutions + blur fixes (3Q owner, P/D owner, PDA detection)"
```

**To:**
```yaml
label: "v1.1 — Updated with GAP 7-9 + BLUR 1-3 fixes COMPLETE (3Q framework added, P/D calc added, PDA detection added)"
```

---

## SUMMARY OF CHANGES

**What these amendments add:**

1. **3Q Framework** (BLUR-001):
   - Q1_location: Full definition with outputs and logic
   - Q2_objective: Target identification with priority
   - Q3_respect: HTF behavior evaluation
   - bias_synthesis: Combines 3Qs into trade_bias

2. **P/D Calculation** (BLUR-002):
   - structural_pd_state: Actual calculation (not just reference)
   - Outputs: pd_state, position_pct, distance_from_eq

3. **PDA Detection** (BLUR-003):
   - fvg_detection: Immutable FVG metadata
   - ob_detection: Immutable OB metadata
   - ifvg_detection: Inverse FVG tracking
   - bpr_detection: Balanced Price Range
   - pda_registry: Central registry structure

**References now resolve:**
- ✅ conditions.yaml → context.Q1_location (now exists)
- ✅ conditions.yaml → context.Q2_objective (now exists)
- ✅ conditions.yaml → context.Q3_respect (now exists)
- ✅ conditions.yaml → context.structural_pd_state (now exists)
- ✅ conditions.yaml → context.pda_detection (now exists)

**Signal count update:**
- Previous: 21 signals
- New: 21 + 1 (3Q) + 1 (P/D) + 1 (PDA) = 24 signals

---

**Status:** Ready for Craig to implement
**Priority:** CRITICAL (blocks system functionality)
**Estimated implementation time:** 30-45 minutes (copy-paste + verify)

---

## ✅ POST-APPLICATION VERIFICATION CHECKLIST

**For CTO Machine to verify after applying all amendments:**

### File Integrity
- [ ] `context.yaml` parses as valid YAML (no syntax errors)
- [ ] File size increased by ~300-350 lines
- [ ] All 5 amendments successfully applied

### Section Checks
- [ ] Search for "SIG-CTX-Q1" → Found ✓
- [ ] Search for "SIG-CTX-Q2" → Found ✓
- [ ] Search for "SIG-CTX-Q3" → Found ✓
- [ ] Search for "SIG-CTX-BIAS-SYNTHESIS" → Found ✓
- [ ] Search for "SIG-CTX-PD-STATE" → Found ✓
- [ ] Search for "SIG-CTX-PDA-DETECT" → Found ✓

### Signal Count
- [ ] Previous count: 21 signals
- [ ] New count: 24 signals (21 + 3 new sections)
- [ ] Update `index.yaml` to reflect new count

### Reference Resolution Test
After applying amendments, these references in `conditions.yaml` should now resolve:
- [ ] `context.Q1_location` → Exists in context.yaml ✓
- [ ] `context.Q2_objective` → Exists in context.yaml ✓
- [ ] `context.Q3_respect` → Exists in context.yaml ✓
- [ ] `context.bias_synthesis.trade_bias` → Exists in context.yaml ✓
- [ ] `context.structural_pd_state` → Exists in context.yaml ✓
- [ ] `context.pda_detection` → Exists in context.yaml ✓

### Completeness Check
- [ ] All BLUR-001 requirements met (3Q framework owned by Context)
- [ ] All BLUR-002 requirements met (P/D calculation owned by Context)
- [ ] All BLUR-003 requirements met (PDA detection owned by Context)

### Final Validation
- [ ] No duplicate IDs (all SIG-CTX-* IDs unique)
- [ ] All sections have proper YAML indentation
- [ ] All references to foundation.yaml are correct
- [ ] File header updated with new version

**If all checkboxes pass → Amendment application SUCCESSFUL ✅**

**If any checkbox fails → Review that amendment and reapply**

---
