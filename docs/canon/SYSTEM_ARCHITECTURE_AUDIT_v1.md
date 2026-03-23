# SYSTEM_ARCHITECTURE_AUDIT_v1.md
# a8ra — Cross-Repo Structural Audit for Deployment Readiness

```yaml
document: SYSTEM_ARCHITECTURE_AUDIT_v1
version: 1.0
date: 2026-03-22
status: CANONICAL — produced by RepoPrompt structural scan (3 passes, 216 files examined)
purpose: Single ground-truth map of what EXISTS, what's WIRED, what's DEAD, and what's MISSING
author: G + RepoPrompt (Opus) + Oracle consultation
audience: Any CTO instance, any advisor, G
repos_audited: phoenix, dexter, research_accelerator
methodology: Context Builder discovery (102+50+64 files), Oracle-assisted analysis
supersedes: Partial understanding from sprint docs and canon orientation
```

---

## TABLE OF CONTENTS

1. [Data Flow Map](#1-data-flow-map)
2. [Detection Inventory (13 vLOCK Primitives)](#2-detection-inventory)
3. [Strategy Path Trace](#3-strategy-path-trace)
4. [Phoenix CSO Anatomy](#4-phoenix-cso-anatomy)
5. [Signal Ingress Gap](#5-signal-ingress-gap)
6. [Stale and Dead Code](#6-stale-and-dead-code)
7. [Live Readiness Checklist](#7-live-readiness-checklist)

---

## 1. DATA FLOW MAP

### 1.1 IBKR → River Ingestion

```
IBKR Gateway (127.0.0.1:4002)
  │
  ├─► phoenix/river/streamer.py::RiverStreamer.start()
  │     reqHistoricalData(keepUpToDate=True, barSize="1 min", whatToShow="MIDPOINT")
  │     │
  │     ├─► _on_bar_update() callback
  │     │     INV-NO-FORMING-CANDLE: only when has_new_bar=True
  │     │     Writes JSONL line to:
  │     │       ~/phoenix-river/{pair}/.staging/{YYYY-MM-DD}.jsonl
  │     │     Updates heartbeat:
  │     │       ~/phoenix-river/.heartbeat.json
  │     │
  │     └─► consolidate_day() / consolidate_all_pending()
  │           Staging JSONL → daily parquet (write-once immutable)
  │           Path: ~/phoenix-river/{pair}/{year}/{mm}/{dd}.parquet
  │           Schema: RAW_BAR_SCHEMA (9 cols) from phoenix/river/schema.py
  │           Adds: bar_hash via compute_bar_hashes(), validates via validate_raw_bars()
  │
  ├─► phoenix/river/writer.py::RiverWriter.capture_all()
  │     Historical backfill: reqHistoricalData (non-streaming, 2-day chunks)
  │     Same parquet path, same schema, write-once guard (skip if exists)
  │     source="ibkr", knowledge_time=now, volume=-1 (MIDPOINT convention)
  │
  └─► phoenix/river/schema.py
        RAW_BAR_SCHEMA: timestamp, open, high, low, close, volume, source, knowledge_time, bar_hash
        CANONICAL_PAIRS: {EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD}
        VALID_SOURCES: {dukascopy, ibkr}
```

### 1.2 River Parquet Substrate

```
~/phoenix-river/
  ├── {pair}/{year}/{mm}/{dd}.parquet     ← immutable daily files (write-once)
  ├── {pair}/.staging/{YYYY-MM-DD}.jsonl  ← intraday live accumulation
  └── .heartbeat.json                     ← streamer liveness
```

### 1.3 River Consumers (All Read-Only)

| Consumer | File Path | Read Mechanism | Notes |
|----------|-----------|----------------|-------|
| **Phoenix RiverReader** | `phoenix/river/reader.py` | DuckDB glob over `**/*.parquet` | Ghost injection, TF aggregation. Hash verification on sample. |
| **Dexter RiverBarAdapter** | `dexter/dexter/bead_field/river/river_adapter.py` | `pd.read_parquet()` per day + staging JSONL fallback | Converts to `OHLCVBar` NamedTuples. 30-day warmup. |
| **RA RiverAdapter** | `research_accelerator/src/ra/data/river_adapter.py` | DuckDB `read_parquet([file_list])` | Asia/Bangkok→UTC normalization, session tagging. |
| **Phoenix CFP adapter** | `phoenix/cfp/river_adapter.py` | Read-only consumer | CFP lens queries. |
| **Phoenix data reader** | `phoenix/data/river_reader.py` | Thin wrapper | Additional read path. |
| **MIRROR backend** | `research_accelerator/mirror/backend/server.py` | Imports Dexter's `RiverBarAdapter` | Serves bars + detection JSON to web frontend. |

### 1.4 Key Data Flow Observations

1. **Two ingestion paths**: `streamer.py` (live, JSONL→parquet) and `writer.py` (historical backfill). Both produce identical schema.
2. **Three independent River readers** with different read mechanisms: Phoenix uses DuckDB glob, Dexter uses per-file `pd.read_parquet` + JSONL fallback, RA uses DuckDB with explicit file list.
3. **Ghost bar semantics differ**: Phoenix Reader injects synthetic ghosts (`is_ghost=True, volume=0`); Dexter adapter does not inject ghosts; RA flags `volume==0` as ghost but doesn't inject.
4. **Staging JSONL** consumed by both `streamer.py::consolidate_day()` and Dexter adapter — Dexter can read live intraday data before consolidation.
5. **No River write from Dexter or RA** — read-only invariant respected.

---

## 2. DETECTION INVENTORY

### 2.1 Summary Matrix (13 vLOCK Primitives)

| # | Primitive | Phoenix | Dexter | RA | Similarity | Canonical |
|---|-----------|---------|--------|----|------------|-----------|
| 1 | **FVG** | L6 `_detect_fvg()` (basic 3-candle) | `fvg.py` FVGProducer + HTF `detect_htf_fvg()` (state machine: ACTIVE→CE_TOUCHED→FILLED, multi-TF, floor pips) | `fvg.py` FVGDetector | Similar | **Dexter** |
| 2 | **MSS** | L4 `enrich()` (swing breaks, no displacement confirmation) | `mss.py` MSSProducer + HTF `detect_htf_mss()` (displacement-confirmed, body ratio) | `mss.py` MSSDetector | **Divergent** | **Dexter** |
| 3 | **Displacement** | L6 `enrich()` (body>1.5×ATR, body_ratio>0.6) | `displacement.py` + HTF `detect_htf_displacement()` (per-TF body_ratio, close_gate, decisive override) | `displacement.py` DisplacementDetector | Similar | **Dexter HTF** |
| 4 | **SwingPoints** | L4 `_detect_swings()` (fixed N=3) | `swing_point.py` + HTF `detect_htf_swings()` (per-TF N, height floor) | `swing_points.py` SwingPointDetector | Similar | **Dexter HTF** |
| 5 | **OrderBlock** | L5 `_detect_order_blocks()` (displacement-anchored) | `order_block.py` OrderBlockProducer (MSS-anchored) | `order_block.py` OrderBlockDetector | **Divergent** | **Dexter** |
| 6 | **IFVG** | L2 **stubbed** (all `MISSING_LEVEL`/`False`) | `ifvg.py` (implemented) | — | N/A | **Dexter** |
| 7 | **BPR** | L2 **stubbed** (all `MISSING_LEVEL`/`None`) | `bpr.py` (implemented) | — | N/A | **Dexter** |
| 8 | **SessionBoundary** | L1 `enrich()` (DataFrame columns) | `session_boundary.py` (CLAIMs) | session_tagger | Similar | Both valid |
| 9 | **AsiaRange** | L2 `_calculate_asia_range()` + L7 state machine | `asia_range.py` (3-tier TIGHT/MID/WIDE) | `asia_range.py` (parametric binary) | Similar | **Dexter** |
| 10 | **PDH_PDL** | L2 `_calculate_pdh_pdl()` | `pdh_pdl.py` PDHPDLProducer | `reference_levels.py` | Identical concept | Equivalent |
| 11 | **LiquiditySweep** | L3 `enrich()` (wick breach, extension class) | `liquidity_sweep.py` (CLAIM-based input) | `liquidity_sweep.py` LiquiditySweepDetector | Similar | **Dexter** |
| 12 | **EQH_EQL** | — | — | `equal_hl.py` **DEFERRED stub** | N/A | **None** |
| 13 | **OTE** | — | `ote.py` OTEProducer (mss+disp inputs) | `ote.py` OTEDetector | Unknown | **Dexter** |

### 2.2 Key Detection Observations

- **Dexter is canonical for 11 of 13 primitives.** Phoenix enrichment layers are simplified column-enrichment versions adequate for the Asia Range Scalp strategy but not vLOCK-aligned for HTF analysis.
- **Phoenix has stubs for IFVG and BPR** — these only exist in Dexter.
- **EQH_EQL is not implemented anywhere** — RA has a registered stub only.
- **OTE exists only in Dexter** (no Phoenix enrichment layer).
- **MSS and OrderBlock are semantically divergent** — Phoenix uses simplified swing-break detection while Dexter uses displacement-confirmed MSS (vLOCK definition).
- **Output formats are incompatible**: Phoenix produces DataFrame columns, Dexter produces `ClaimSpec` beads with `reasoning_trace`, RA produces `Detection` objects with `properties` dicts.

---

## 3. STRATEGY PATH TRACE

### 3.1 Asia Range Scalp — Phoenix Wired Path

```
IBKR 1m bar
  │
  ├─► phoenix/river/streamer.py::_on_bar_update()
  │     Writes to ~/phoenix-river/EURUSD/.staging/{date}.jsonl
  │
  ├─► phoenix/river/reader.py::RiverReader.get_bars("EURUSD", "5m")
  │     Reads parquet, aggregates to 5m, injects ghosts
  │
  ├─► phoenix/enrichment/layers/l1_time_sessions.py::enrich()   → 25 cols
  ├─► phoenix/enrichment/layers/l2_reference_levels.py::enrich() → 74 cols
  ├─► phoenix/enrichment/layers/l3_sweeps.py::enrich()           → 37 cols
  ├─► phoenix/enrichment/layers/l4_structure_breaks.py::enrich() → 13 cols
  ├─► phoenix/enrichment/layers/l5_order_blocks.py::enrich()     → 14 cols
  ├─► phoenix/enrichment/layers/l6_fvg_imbalances.py::enrich()   → 20 cols
  ├─► phoenix/enrichment/layers/l7_asia_scalp.py::enrich()       → 16 cols
  │
  ├─► phoenix/cso/market_state_builder.py::build_market_state(df, "EURUSD", now)
  │     INV-PIT-JOIN-ONLY: filters df to timestamp < now
  │     INV-RIVER-FRESHNESS: rejects stale data
  │     Maps enrichment columns → immutable MarketState dataclass
  │
  ├─► phoenix/cso/evaluator.py::GateEvaluator.evaluate(pair, market_state, config_hash)
  │     5-drawer gate evaluation → FiveDrawerResult
  │     ⚠️ ISSUE: Cartridge gate IDs (GATE_ASIA_RANGE_VALID, etc.) do NOT exist
  │     in evaluator — they fall through to "UNKNOWN_GATE". See Section 4.
  │
  ├─► phoenix/execution/asia_scalp.py::evaluate_asia_scalp_setup(...)
  │     Pure function: validates range ≤30, sweep 1-20 pips, re_acceptance,
  │     FVG valid, candle C inside, R:R ≥ 1.5, session/daily limits
  │     Returns SetupResult(verdict=VALID, proposal=TradeProposal) or REJECTED
  │
  ├─► ⚠️ GAP: No production orchestrator that chains L1→L7 → build_market_state()
  │     → evaluate_asia_scalp_setup() → broker submission
  │
  ├─► ⚠️ GAP: No adapter from TradeProposal → ExecutionIntent
  │
  ├─► phoenix/execution/halt_gate.py::check_before() → sentinel intercept
  ├─► phoenix/execution/intent.py → ExecutionIntent (immutable, hashed)
  ├─► phoenix/execution/broker_stub.py::submit_order(intent) → PaperPosition
  └─► phoenix/execution/positions/paper.py → PENDING → OPEN → CLOSED
```

**Status:** Components exist individually. **Three gaps** prevent end-to-end operation:
1. No production orchestrator for enrichment chain
2. No TradeProposal → ExecutionIntent adapter
3. Cartridge gate IDs don't match evaluator gate IDs

### 3.2 HTF Directional — Dexter Detection Path

```
IBKR 1m bars (via River parquet)
  │
  ├─► dexter/dexter/bead_field/river/river_adapter.py::load_date_range()
  │     Parquet + staging JSONL fallback, 30-day warmup
  │
  ├─► dexter/scripts/daily_detection_export.py::run_pipeline()
  │     │
  │     ├─► LTF Producers (5m/15m):
  │     │     FVG, SwingPoint, Displacement, MSS, OrderBlock,
  │     │     SessionBoundary, PDH_PDL, LiquiditySweep, OTE
  │     │
  │     ├─► HTF Producers (1H/4H/1D via tf_aggregator):
  │     │     detect_htf_swings(), detect_htf_fvg(),
  │     │     detect_htf_displacement(), detect_htf_mss()
  │     │     INV-WARMUP-MANDATORY: skips TF if bars < minimums
  │     │
  │     ├─► Composite: detect_setup_chains(), dedup_mss()
  │     │
  │     ├─► dexter/dexter/state/classifier.py::classify_day_snapshots()
  │     │     3-mechanism hierarchy → WorldState per bar close:
  │     │       M1: Daily swing structure (HH/HL, LL/LH)
  │     │       M2: Relaxed 4H MSS (10-day window)
  │     │       M3: 4H sustained (3+ swings trending)
  │     │     → htf_phase: EXPANSION|RETRACE|RANGE|UNCLEAR
  │     │     → direction_permission: WITH_EXPANSION|COUNTER_ALLOWED|NEUTRAL|BOTH
  │     │
  │     ├─► dexter/dexter/state/level_lifecycle.py::track_level_lifecycle()
  │     │     SESSION_BOUNDARY + PDH_PDL → LEVEL_SWEPT CLAIMs
  │     │
  │     ├─► dexter/dexter/checklist/evaluator.py::evaluate_checklist()
  │     │     F1: HTF bias, F2: Liquidity, F3: Structure,
  │     │     F4: PDA, F5: Target → ChecklistResult per chain
  │     │
  │     ├─► dexter/dexter/checklist/signal_builder.py::build_diagnostic_signal()
  │     │     shadow_mode=True ALWAYS (hardcoded, "no exceptions")
  │     │     Rate limit: max 3 per 4H window
  │     │
  │     └─► Export: ~/dexter/output/detections/{forex_day}.json
  │
  ├─► CONSUMED BY: MIRROR backend (visual dashboard)
  │
  └─► ❌ NOT CONSUMED BY: Phoenix execution pipeline
        No file in phoenix/ reads dexter output
        No import of dexter modules in phoenix/
        No shared message bus or IPC
```

**Status:** Detection pipeline is complete and producing signals. **Fully disconnected** from Phoenix execution. The gap is architectural — see Section 5.

### 3.3 Architecture Summary: Two Disconnected Pipelines

```
PIPELINE A (Phoenix — enrichment-based):
  River → RiverReader → DataFrame → L1→L7 → build_market_state() → MarketState
  → GateEvaluator → FiveDrawerResult → evaluate_asia_scalp_setup() → TradeProposal
  → [UNWIRED TO BROKER]

PIPELINE B (Dexter — CLAIM-based):
  River → RiverBarAdapter → OHLCVBar → LTF+HTF Producers → ClaimSpecs
  → classify_day_snapshots() → WorldState → evaluate_checklist() → ChecklistResult
  → build_diagnostic_signal() → DIAGNOSTIC_SIGNAL → JSON file → [MIRROR dashboard]

BRIDGE: None for market signals.
  - Governance bridge exists (governance_log.py → bridge/ → FACT beads)
  - No market signal bridge between the two pipelines
  - Only shared substrate is ~/phoenix-river/ parquet files (read-only by both)
```

---

## 4. PHOENIX CSO ANATOMY

### 4.1 MarketState Field Map

**Construction:** Enrichment DataFrame → `cso/market_state_builder.py::build_market_state()` → frozen `MarketState`

#### Fields Populated from Enrichment

| MarketState Field | Source Column | Layer | Extraction | Notes |
|---|---|---|---|---|
| `pair` | runtime arg | — | direct | |
| `timestamp` | runtime arg (`now`) | — | direct | Wall-clock time |
| `evaluation_time` | `pit_df["timestamp"].iloc[-1]` | L0 | last closed bar | |
| `htf_bias` | `order_flow` | L4 | `_safe_str()` | |
| `current_session` | `session_name` | L1 | `_safe_str()` | |
| `session_bias` | `order_flow` | L4 | `_safe_str()` | **Same source as htf_bias** |
| `asia_high` | `asia_high` | L2 | `_safe_float()` | REQUIRED |
| `asia_low` | `asia_low` | L2 | `_safe_float()` | REQUIRED |
| `asia_range_pips` | `asia_range_pips` | L2 | `_safe_float()` | |
| `asia_range_valid` | computed | L2 | `pips <= 30.0` | |
| `fvg_count` | `fvg_bull`, `fvg_bear` | L6 | 12-bar window | |
| `fvg_direction` | `fvg_bull`, `fvg_bear` | L6 | latest in window | |
| `fvg_bull_present` | `fvg_bull` | L6 | any True in window | |
| `fvg_bear_present` | `fvg_bear` | L6 | any True in window | |
| `fvg_untouched_pips` | `fvg_*_high/low` | L6 | gap size / PIP_SIZE | |
| `displacement_pips` | `displacement_pips` | L6 | `_safe_float()` | |
| `recent_sweep` | `sweep_detected` | L3 | 48-bar window | |
| `sweep_age_bars` | `sweep_detected` | L3 | bars since last True | |
| `sweep_direction` | `sweep_direction` | L3 | at last sweep row | |
| `sweep_extension_pips` | `sweep_extension_pips` | L3 | at last sweep row | |
| `sweep_target_type` | `sweep_target_type` | L3 | at last sweep row | |
| `re_acceptance` | `sweep_detected` + `close` vs `asia_*` | L3+L0+L2 | post-sweep close inside range | |
| `candle_c_inside_range` | `close` vs `asia_high/low` | L0+L2 | strict inequality | |
| `ltf_confirmation` | `structure_confirmed` | L4 | any() over 6 bars | |
| `ltf_direction` | `structure_trend` | L4 | `_safe_str()` | |

#### Fields NEVER Populated (remain at defaults)

| Field | Default | Note |
|---|---|---|
| `poi_distance_pips` | `None` | Declared as "Set by strategy engine" |
| `entry_model` | `None` | Declared as "Set by strategy engine" |
| `stop_distance_pips` | `None` | Declared as "Set by strategy engine" |
| `target_defined` | `False` | Declared as "Set by strategy engine" |
| `rr_ratio` | `None` | Declared as "Set by strategy engine" |
| `partials_defined` | `False` | Declared as "Set by strategy engine" |

### 4.2 Three Layers of Gate Definition (Misaligned)

#### Layer A: Schema Declarations (`cso/schemas/`)

| Drawer | Gates | Rule |
|--------|-------|------|
| 1: HTF Bias | `htf_structure_bullish`, `htf_structure_bearish`, `htf_poi_identified` | `at_least_one_directional` |
| 2: Session Context | `kill_zone_active`, `asia_range_defined`, `session_bias_aligned` | `all_gates_independent` (always passes) |
| 3: Entry Conditions | `fvg_present`, `displacement_sufficient`, `liquidity_swept` | `minimum_2_of_3` |
| 4: Entry Trigger | `ltf_confirmation`, `entry_model_valid`, `stop_defined` | `all_required` |
| 5: Trade Management | `target_defined`, `rr_acceptable`, `partials_planned` | `all_required` |

#### Layer B: Runtime Implementation (`evaluator.py`)

12 gates hardcoded in `_evaluate_gate()`. Any unrecognized gate → `(False, "UNKNOWN_GATE")`.

#### Layer C: Cartridge Gate Requirements (`asia_range_scalp.yaml`)

```
GATE_ASIA_RANGE_VALID, GATE_LIQUIDITY_SWEEP_DETECTED, GATE_SWEEP_EXTENSION_VALID,
GATE_LTF_PDA_ENGAGED, GATE_FVG_ACTIVE, GATE_CANDLE_C_INSIDE, GATE_RR_VALID,
GATE_SESSION_LIMIT
```

**⚠️ CRITICAL: NONE of these cartridge gate IDs are implemented in `_evaluate_gate()`.** The evaluator only knows the 12 generic gates from Layer A. Cartridge gates exist as declarations only — no runtime code evaluates them.

### 4.3 Drawer Evaluation Reality

| Drawer | Can Pass? | Why |
|--------|-----------|-----|
| 1: HTF Bias | Only if `htf_bias == "bullish"` or `"bearish"` | `poi_distance_pips` always None → SKIP, but one directional may suffice |
| 2: Session | **Always passes** | Rule is `all_gates_independent` → True unconditionally |
| 3: Entry Conditions | Possible | 2-of-3 from enrichment (fvg_present, displacement, liquidity_swept) |
| 4: Entry Trigger | **Always fails** | `entry_model` always None → `entry_model_valid` always FAIL |
| 5: Trade Management | **Always fails** | `target_defined` always False, `rr_ratio` always None |

### 4.4 Asia Scalp Evaluator (Parallel Path)

`execution/asia_scalp.py::evaluate_asia_scalp_setup()` is a **completely separate evaluation** from the 5-drawer system. It takes raw floats, not MarketState:

```python
evaluate_asia_scalp_setup(
    asia_high, asia_low, asia_range_pips, sweep_direction, sweep_extension_pips,
    sweep_extreme_price, re_acceptance, fvg_valid, fvg_untouched_pips,
    candle_c_inside, candle_c_close, session_id, account_equity, tracker, pip_value
) → SetupResult(verdict, proposal=TradeProposal)
```

**No caller bridges MarketState → these arguments.**

### 4.5 TradeProposal → ExecutionIntent Gap

| TradeProposal Field | ExecutionIntent Field | Translation |
|---|---|---|
| `direction` (TradeDirection) | `direction` (Direction) | LONG→LONG, SHORT→SHORT |
| `entry_price` | `entry_price` | direct |
| `stop_loss` | `stop_loss` | direct |
| `take_profit` | `take_profit` | direct |
| `position_size_lots` | `size` | direct |
| — | `intent_id` | generated |
| — | `intent_type` | `ENTRY` |
| — | `status` | `PENDING` |
| — | `symbol` | from context |
| — | `source_state_hash` | from MarketState hash |

**No adapter exists.**

---

## 5. SIGNAL INGRESS GAP

### 5.1 DIAGNOSTIC_SIGNAL Schema (Dexter Output)

From `checklist/signal_builder.py::build_diagnostic_signal()`:

```yaml
ClaimSpec:
  claim_subtype: "DIAGNOSTIC_SIGNAL"
  drawer: Drawer.ENTRY_MODEL
  world_time_valid_from: bar_time
  world_time_valid_to: bar_time + 5min
  reasoning_trace:
    shadow_mode: true              # ALWAYS — hardcoded, "no exceptions"
    direction: "bullish"|"bearish"
    model_type: "REVERSAL"|"CONTINUATION"
    chain_type: "REVERSAL_CHAIN"|"CONTINUATION_CHAIN"
    f1_bias_pass: bool
    f2_liquidity_pass: bool
    f3_structure_pass: bool
    f4_pda_pass: bool
    f5_target_pass: bool
    all_factors_pass: bool
    eligible_for_signal: bool
    pda_type: "BPR"|"IFVG"|"FVG"|"ORDER_BLOCK"
    pda_confluence: int
    interaction_depth: "ACTIVE"|"CE_TOUCHED"
    pd_position: "PREMIUM"|"DISCOUNT"|"EQUILIBRIUM"
    primary_target: {level: float, type: str, distance_pips: float}
    target_hierarchy: int (1-4)
    worldstate_snapshot: {htf_phase, direction_permission, authority_tf, daily_direction, mechanism_used}
    mss_time: str, displacement_time: str, pda_time: str, sweep_time: str
    bar_time: str (ISO), source_timeframe: str
```

### 5.2 ExecutionIntent Schema (Phoenix Input)

```yaml
ExecutionIntent:
  intent_id: str                   # "INT-{source}-{timestamp}-{counter}"
  intent_type: ENTRY|EXIT|SCALE|HEDGE|CANCEL
  status: PENDING|BLOCKED|APPROVED|REJECTED|EXPIRED
  created_at: datetime
  expires_at: datetime|None
  symbol: str
  direction: LONG|SHORT
  size: float
  entry_price: float|None
  stop_loss: float|None
  take_profit: float|None
  source_bead_id: str|None
  source_state_hash: str
  intent_hash: str                 # SHA256[:16] of deterministic fields
```

### 5.3 Structural Gap Analysis

| Dimension | DIAGNOSTIC_SIGNAL | ExecutionIntent | Gap |
|---|---|---|---|
| **Entry price** | ❌ Not present | Required for fill | **Critical** — no price discovery |
| **Stop loss** | ❌ Not present | Optional but needed | **Critical** |
| **Position size** | ❌ Not present | Required | **Critical** — no sizing |
| **Take profit** | `primary_target.level` (target, not TP) | Optional | Partial |
| **Direction** | `"bullish"`/`"bearish"` (lowercase) | `Direction.LONG`/`SHORT` (enum) | Vocabulary translation needed |
| **Shadow mode** | `True` always | No equivalent | Semantic firewall |
| **Symbol** | Implicit from pipeline | Required explicit | Must be carried |
| **State hash** | worldstate_snapshot dict | source_state_hash (SHA256) | Must compute hash |
| **Timing** | bar_time + 5min validity | created_at + expires_at | Temporal model differs |

### 5.4 Candidate Ingress Points

| Candidate | Mechanism | Verdict |
|-----------|-----------|---------|
| **A: File-Intent** (`daemons/watcher.py`) | Drop YAML → watcher polls → route by IntentType | **Viable as transport** — needs new IntentType + handler |
| **B: CSE Consumer** (`cso/consumer.py`) | Validate against cse_schema.yaml → ApprovalHandler | **Not viable** — DIAGNOSTIC_SIGNAL lacks 8+ required CSE fields |
| **C: New Dedicated Adapter** | Read signal → bridge to `evaluate_asia_scalp_setup()` for price discovery | **Required** — only path that handles price discovery gap |

### 5.5 Recommended Ingress Architecture

```
Dexter daily_detection_export.py → output/detections/{date}.json

Bridge script (new, minimal)
  → reads detection JSON, extracts diagnostic_signals[]
  → wraps each in YAML intent envelope {type: DIAGNOSTIC_SIGNAL, payload: {...}}
  → writes to phoenix/intents/incoming/

Phoenix daemons/watcher.py → picks up → routes to DexterSignalHandler (new)

DexterSignalHandler (new: cso/dexter_adapter.py)
  → validates schema
  → IF shadow_mode=True: record ShadowObservation only, STOP
  → IF shadow_mode lifted (governance ceremony):
      → obtain Phoenix enrichment for same bar window
      → feed to evaluate_asia_scalp_setup()
      → IF VALID: TradeProposal → IntentFactory → ExecutionIntent
      → ExecutionIntent → HaltGate → T2 approval → broker_stub
```

**Critical insight:** The adapter cannot work from DIAGNOSTIC_SIGNAL alone. It needs **concurrent access to Phoenix enrichment data** for the same bar window (asia_high, asia_low, sweep_extreme_price, candle_c_close, etc.). The signal provides *what structure exists*; enrichment provides *what prices to trade at*.

### 5.6 Constitutional Invariants for Ingress

| Invariant | Enforcement |
|-----------|-------------|
| INV-SHADOW-MODE-RESPECTED (new) | shadow_mode=True → ShadowObservation only, no ExecutionIntent |
| INV-GOV-HALT-BEFORE-ACTION | HaltGate.check_before() before any intent creation |
| INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS | sovereign_gate wraps live-mode path |
| INV-T2-GATE-1 | No broker submission without valid T2 token |
| INV-ATTR-CAUSAL-BAN | CausalBanLinter on human-visible text from signal |
| INV-CONTRACT-1 | Same signal + same MarketState → same intent_hash |
| INV-CSE-PROVENANCE-1 | CSE must carry River provenance (from Phoenix, not Dexter) |
| INV-BUILDER-PURE-ADAPTER | Adapter maps fields only — no scoring/inference |
| INV-NO-FORMING-CANDLE | Signal bar_time must reference closed bar |

### 5.7 Open Wiring Questions

1. **`sweep_extreme_price` is not in MarketState** — needed for SL computation, exists in enrichment DF but not extracted by builder
2. **Enrichment synchronization** — adapter needs Phoenix enrichment for same bar window as signal; PIT-filter to signal.bar_time
3. **Rate limiting** — Dexter limits 3/4H; Phoenix has no equivalent; adapter should carry forward
4. **Shadow→Live governance ceremony** — no mechanism exists to flip shadow_mode; needs lease-level decision

---

## 6. STALE AND DEAD CODE

### BLOCKING

| ID | Location | Issue |
|----|----------|-------|
| B1 | `phoenix/enrichment/__init__.py` | Imports L2–L6 modules that don't exist in file tree → **crashes on import** |
| B2 | `phoenix/execution/intent.py` | Docstring declares `CAPITAL: DISABLED` / `S27: SKELETON` — but broker_stub actively consumes ExecutionIntent. Documentation-reality mismatch. |
| B3 | `dexter/bead_field/producers/runner.py` | Docstring lists VI as step 4 in execution order — no VI producer exists |
| B4 | `dexter/bead_field/ingestion/lineage.py` | Contiguity check references "FVG/VI requirement" — VI is retired |

### MISLEADING

| ID | Location | Issue |
|----|----------|-------|
| M1 | `phoenix/execution/contracts/execution_surface.yaml` | Declares `mode: MOCK_SIGNALS` and `tier: T0/T1/T2_MOCKED` — actual capability is beyond this |
| M2 | `phoenix/execution/replay.py` | Repeated "NOT Olya methodology" disclaimers (4×) — correct for signals but surrounding machinery is real |
| M3 | `phoenix/cso/scanner.py` | Emits `confidence=len(readiness_reasons)/5.0` to Shadow — violates INV-CSO-NO-SCALAR-DECISIONS |
| M4 | `phoenix/enrichment/layers/l1_time_sessions.py` | Header says `STATUS: SUBSUMED` from NEX — confusing if NEX is retired |
| M5 | `phoenix/execution/contracts/execution_surface.yaml` | Position lifecycle says 9 states in header, 10 in body |
| M6 | `phoenix/execution/asia_scalp.py` | Parallel setup evaluator disconnected from ExecutionIntent path — two execution vocabularies |
| M7 | `phoenix/daemons/routing.py` | `create_halt_handler()` creates isolated HaltManager — halt effect is local-only, not connected to global HaltMesh |
| M8 | `dexter/checklist/signal_builder.py` | `shadow_mode=True` hardcoded with "no exceptions" — no toggle or graduation path documented |

### HARMLESS

| ID | Location | Issue |
|----|----------|-------|
| H1 | `research_accelerator/src/ra/detectors/equal_hl.py` | DEFERRED stub with clear documentation |
| H2 | `phoenix/brokers/ibkr/config.py` | Deprecated `ConnectionConfig` with clear docstring |
| H3 | `phoenix/execution/broker_stub.py` | P&L v0 SIMPLIFIED disclaimers — accurate and well-labeled |
| H4 | `phoenix/enrichment/layers/l1_time_sessions.py` | `__main__` self-test block — development convenience |
| H5 | `dexter/dream_cycle/analyzer.py` | Hardcoded DEFAULT_SL_PIPS=15.0 — analysis params, not execution |

---

## 7. LIVE READINESS CHECKLIST

| Component | Status | Evidence |
|-----------|--------|----------|
| **River Streamer** | ✅ LIVE_READY | IBKR keepUpToDate subscription, staging JSONL, heartbeat, watchdog with resubscribe. Only gap: consolidation not auto-triggered at 17:00 NY (requires external call). |
| **Phoenix Enrichment** | ❌ NOT_WIRED | `__init__.py` imports L2–L6 that don't exist in file tree → crashes on import. No visible production orchestrator chains L1→L7. |
| **Dexter Detection** | 🔄 BATCH_ONLY | `daily_detection_export.py` is CLI-driven with date args. Complete pipeline but purely batch — no daemon, no file-watcher trigger. |
| **MIRROR Backend** | ✅ LIVE_READY | FastAPI + WebSocket, watchdog on staging files, periodic detection refresh (5min), REST endpoints, proper lifespan. Depends on detection JSONs from batch pipeline. |
| **CSO Evaluator** | 🔄 BATCH_ONLY | GateEvaluator is a pure function (works if given MarketState). CSOScanner has own data loading. Neither has production loop/daemon. Drawers 4+5 always fail. |
| **Execution Engine** | ⚠️ UNTESTED | Components exist (ExecutionIntent, PaperBrokerStub, halt gate, position lifecycle). TradeProposal→ExecutionIntent adapter missing. No end-to-end integration test from signal→paper trade. |
| **Dream Cycle** | 🔄 BATCH_ONLY | `dream_cycle_nightly.py` CLI runner + `analyzer.py` (MFE/MAE/outcome sim). Complete but script-driven, no daemon. |
| **Halt Mechanism** | ✅ LIVE_READY | Multi-layer: HALT.signal file (6 fail-closed cases), HaltSignal thread-safe, HaltManager cascade, HaltGate execution chokepoint, BoundsSentinel (<2ms). All tested. |
| **Bridge** | 🔄 BATCH_ONLY | `orchestrator.cycle()` is complete (poll→verify→seal→project). Heavily tested (7 invariants, kill chain). Pull-based — needs external loop to call cycle() on cadence. |

---

## 8. CRITICAL FINDINGS SUMMARY

### The Three Gaps Blocking Paper Trading

1. **No production orchestrator** — Nothing chains River → L1-L7 enrichment → build_market_state() → evaluate setup → create intent → submit order. Each component works individually; the glue doesn't exist.

2. **No TradeProposal → ExecutionIntent adapter** — The Asia Scalp evaluator produces TradeProposals; the broker consumes ExecutionIntents. These are parallel vocabularies with no bridge.

3. **No Dexter signal → Phoenix execution path** — DIAGNOSTIC_SIGNAL is a dead end for execution. The governance bridge carries events, not market signals. A dedicated adapter is needed that combines Dexter's detection context with Phoenix's enrichment data for price discovery.

### The Gate Alignment Problem

The cartridge declares gates (`GATE_ASIA_RANGE_VALID`, etc.) that the evaluator doesn't implement. The evaluator implements generic gates (`htf_structure_bullish`, etc.) that no cartridge references. The 5-drawer system's Drawers 4 and 5 always fail because the fields they check are never populated. The Asia Scalp evaluator bypasses the 5-drawer system entirely with its own guard chain. **The gate architecture is structurally sound but the wiring between layers is incomplete.**

### What Works

- River streaming (live data flowing)
- Halt mechanism (constitutional, multi-layer, tested)
- Dexter detection pipeline (produces correct signals on historical + live data)
- MIRROR dashboard (live-capable web frontend)
- Bridge protocol (governance events, heavily tested)
- Position lifecycle (10-state FSM, tested)
- Paper broker (immediate fills, P&L tracking)

### What Doesn't Connect

- Enrichment layers exist but can't be imported as a package
- MarketState is built but 6 fields are never populated
- Two independent detection pipelines (Phoenix enrichment vs Dexter producers) both read River data but produce incompatible outputs
- Shadow mode has no graduation mechanism

---

## APPENDIX A: GATE WIRING TABLE (Deep Dive 1)

### A.1 Cartridge Gate → Evaluator → Execution Cross-Reference

| Cartridge Gate ID | Plain English | MarketState Field(s) | Builder Populates? | Evaluator Predicate? | Asia Scalp Guard? | Enrichment Source | **Status** |
|---|---|---|---|---|---|---|---|
| `GATE_ASIA_RANGE_VALID` | Asia range defined AND ≤ 30 pips | `asia_high`, `asia_low`, `asia_range_pips`, `asia_range_valid` | ✅ | ❌ (only weaker `asia_range_defined`) | ✅ `REJECTED_RANGE_TOO_WIDE` | L2 `_calculate_asia_range()` | **PARTIAL** |
| `GATE_LIQUIDITY_SWEEP_DETECTED` | Sweep of Asia boundary detected in window | `recent_sweep`, `sweep_direction`, `sweep_age_bars` | ✅ | ❌ (only `liquidity_swept`, different semantics) | ✅ `REJECTED_NO_SWEEP` | L3 `enrich()` | **PARTIAL** |
| `GATE_SWEEP_EXTENSION_VALID` | Extension 1–20 pips inclusive | `sweep_extension_pips` | ✅ | ❌ | ✅ `REJECTED_EXTENSION_INVALID` | L3 `enrich()` | **MISSING** |
| `GATE_LTF_PDA_ENGAGED` | Re-acceptance: 5m close strictly inside range after sweep | `re_acceptance` | ✅ | ❌ | ✅ `REJECTED_NO_REACCEPTANCE` | L7 `_detect_re_acceptance()` | **MISSING** |
| `GATE_FVG_ACTIVE` | FVG exists with untouched ≥ 1.0 pip | `fvg_bull_present`, `fvg_bear_present`, `fvg_untouched_pips` | ✅ | ❌ (only weaker `fvg_present`) | ✅ `REJECTED_NO_FVG` + `REJECTED_FVG_TOO_SMALL` | L6 `_detect_fvg()` + L7 `_validate_fvg_asia()` | **MISSING** |
| `GATE_CANDLE_C_INSIDE` | Candle C close strictly inside Asia range | `candle_c_inside_range` | ✅ | ❌ | ✅ `REJECTED_CANDLE_NOT_INSIDE` | L7 + L0 `close` vs L2 `asia_high/low` | **MISSING** |
| `GATE_RR_VALID` | R:R ≥ 1.5 (cartridge `min_rr`) | `rr_ratio` | ❌ (strategy-computed) | ❌ (only `rr_acceptable` at 2.0, and `rr_ratio` always None) | ✅ `REJECTED_RR_INSUFFICIENT` | None — runtime computation | **MISSING** |
| `GATE_SESSION_LIMIT` | Max 1 trade/session, max 1 daily loss | N/A (stateful) | ❌ (not market-state) | ❌ | ✅ `SessionTracker.can_trade()` | None — runtime state | **MISSING** |

**Totals: 0 WIRED · 2 PARTIAL · 6 MISSING**

### A.2 Evaluator Gates NOT in Cartridge (All 15 Are Orphans)

| Evaluator Gate ID | Drawer | What It Checks | Why Not in Asia Cartridge |
|---|---|---|---|
| `htf_structure_bullish` | 1 | `htf_bias == "bullish"` | Asia scalp is mean-reversion; `htf_bias_required: false` |
| `htf_structure_bearish` | 1 | `htf_bias == "bearish"` | Same |
| `htf_poi_identified` | 1 | `poi_distance_pips <= 50` | No HTF POI concept in Asia scalp |
| `kill_zone_active` | 2 | Session in `[london, new_york, london_close]` | Asia uses own sweep window (00:00–04:00 NY) |
| `asia_range_defined` | 2 | `asia_high is not None and asia_low is not None` | Subsumed by `GATE_ASIA_RANGE_VALID` |
| `session_bias_aligned` | 2 | `session_bias == htf_bias` | No bias alignment for mean-reversion |
| `fvg_present` | 3 | `fvg_count > 0` | Subsumed by `GATE_FVG_ACTIVE` |
| `displacement_sufficient` | 3 | `displacement_pips >= 15` | Not an Asia scalp gate |
| `liquidity_swept` | 3 | `recent_sweep and age <= 10` | Subsumed by `GATE_LIQUIDITY_SWEEP_DETECTED` |
| `ltf_confirmation` | 4 | `ltf_confirmation and direction == htf_bias` | Replaced by `GATE_LTF_PDA_ENGAGED` |
| `entry_model_valid` | 4 | `entry_model in [fvg_entry, ob_entry, breaker_entry]` | Asia scalp: market order at Candle C close |
| `stop_defined` | 4 | `stop_distance_pips <= 30` | Stop computed by execution engine |
| `target_defined` | 5 | `target_defined == True` | Always opposite Asia boundary |
| `rr_acceptable` | 5 | `rr_ratio >= 2.0` | Replaced by `GATE_RR_VALID` at 1.5 |
| `partials_planned` | 5 | `partials_defined == True` | Asia scalp is set-and-forget |

### A.3 Key Structural Observation

**No adapter exists between cartridge gate IDs and evaluator gate IDs.** The `CartridgeLoader` validates schema; the `CartridgeLinter` checks content; neither resolves gate IDs to evaluator predicates. `GateEvaluator` loads gates exclusively from `gate_schema.yaml`.

The cartridge's 8 gates, the evaluator's 15 gates, and conditions.yaml's vLOCK gate names are **three disjoint namespaces** with no runtime bridge.

MarketState is well-populated for all enrichment-derived fields the cartridge gates need (6 of 8). The gap is purely in the evaluator predicate layer and the strategy-computed fields (R:R, session limits).

---

## APPENDIX B: SIGNAL ADAPTER DATA REQUIREMENTS (Deep Dive 2)

### B.1 ExecutionIntent Fields Not Provided by DIAGNOSTIC_SIGNAL

| ExecutionIntent Field | Required? | In Signal? | Source | Enrichment Column | Layer | In MarketState? | Available at signal.bar_time? |
|---|---|---|---|---|---|---|---|
| `intent_id` | REQUIRED | ❌ | Generated by `IntentFactory` | — | Runtime | — | N/A |
| `intent_type` | REQUIRED | ❌ | Hardcoded `ENTRY` | — | Runtime | — | N/A |
| `status` | REQUIRED | ❌ | Always `PENDING` | — | Runtime | — | N/A |
| `created_at` | REQUIRED | ✅ `bar_time` | Direct map | — | Signal | — | YES |
| `symbol` | REQUIRED | ❌ (implicit) | Pipeline context | — | Runtime | — | Inferrable |
| `direction` | REQUIRED | ✅ `"bullish"`/`"bearish"` | `bullish→LONG`, `bearish→SHORT` | — | Signal | — | YES |
| **`entry_price`** | Needed | ❌ | Raw bar `close` at Candle C | `df["close"]` | L0 | ❌ | **NO** |
| **`stop_loss`** | Needed | ❌ | `sweep_extreme ± 0.00005` | Reconstructed from L2+L3 | L2+L3 | **Reconstructible** | **NO** |
| **`take_profit`** | Needed | Partial (`primary_target.level`) | `asia_high` (long) / `asia_low` (short) | `asia_high`, `asia_low` | L2 | ✅ | YES |
| **`size`** | REQUIRED | ❌ | `(equity × 1%) / (|entry-SL| × pip_value × 10000)` | — | Runtime | ❌ | **NO** |
| `source_state_hash` | REQUIRED | ❌ | `MarketState.compute_hash()` | — | Runtime | — | After build |

### B.2 Critical Field Derivation

#### entry_price
- **Formula:** `candle_c_close` = raw bar `close` at latest PIT bar
- **NOT in MarketState** — only `candle_c_inside_range: bool` exists
- **Adapter must:** Read enrichment DataFrame `df[df["timestamp"] < now]["close"].iloc[-1]`

#### stop_loss
- **Formula:** `sweep_extreme_price ± SL_BUFFER (0.00005)`
- **`sweep_extreme_price` has no enrichment column** — must be reconstructed
- **Reconstruction from MarketState fields only:**
  ```
  if direction == "bullish":
      sweep_extreme = state.asia_low - state.sweep_extension_pips * 0.0001
      stop_loss = sweep_extreme - 0.00005
  elif direction == "bearish":
      sweep_extreme = state.asia_high + state.sweep_extension_pips * 0.0001
      stop_loss = sweep_extreme + 0.00005
  ```
- **Caveat:** Assumes sweep target is Asia boundary. Adapter must validate `state.sweep_target_type in ("asia_high", "asia_low")`

#### take_profit
- **Formula:** Opposite Asia boundary — `asia_high` (long) / `asia_low` (short)
- **In MarketState:** ✅ `state.asia_high`, `state.asia_low` (REQUIRED fields)
- **Do NOT use** `primary_target.level` from signal (different target hierarchy)

#### size (position_size_lots)
- **Formula:** `(account_equity × 0.01) / (|entry - SL| × pip_value × 10000)`
- **Requires:** `entry_price` (derived), `stop_loss` (derived), `account_equity` (runtime), `pip_value` (config)
- **Entirely runtime computation** — no enrichment input

### B.3 PIT Boundary Alignment

| System | Anchor | Filter | Rule |
|---|---|---|---|
| Dexter signal | `bar_time_utc` | CLAIMs `<= cutoff` | Inclusive of signal bar |
| Phoenix builder | `now` argument | `timestamp < now` | **Strict less-than** — excludes `now` bar |

**Adapter must set:** `phoenix_now = signal.bar_time + timedelta(minutes=5)` so the signal bar is the latest *closed* bar visible to Phoenix.

### B.4 Minimum Viable Adapter Call Sequence

```python
# 1. Receive signal
signal = receive_diagnostic_signal()

# 2. Set PIT boundary (bar close time, not bar open time)
now = signal.bar_time + timedelta(minutes=5)

# 3. Build Phoenix enrichment + MarketState
df = load_enriched_dataframe(pair, covering=signal.bar_time)
state, report = build_market_state(df, pair, now)     # PIT + freshness enforced

# 4. Extract entry price (NOT in MarketState)
candle_c_close = df[df["timestamp"] < now]["close"].iloc[-1]

# 5. Reconstruct stop loss (from MarketState fields)
sweep_extreme = reconstruct_sweep_extreme(state)
stop_loss = sweep_extreme ± SL_BUFFER

# 6. Take profit (from MarketState)
take_profit = state.asia_high if direction == LONG else state.asia_low

# 7. Position sizing (runtime inputs)
risk_pips = abs(candle_c_close - stop_loss) / 0.0001
size = (account_equity * 0.01) / (risk_pips * pip_value)

# 8. Run full Asia Scalp guard chain
result = evaluate_asia_scalp_setup(
    asia_high=state.asia_high, asia_low=state.asia_low, ...
)

# 9. Create ExecutionIntent (if VALID)
intent = IntentFactory.create_entry_intent(
    symbol=pair, direction=Direction.LONG/SHORT,
    size=result.proposal.position_size_lots,
    entry_price=result.proposal.entry_price, ...
)
```

### B.5 What `worldstate_snapshot` CAN and CANNOT Do

**Can cross-check:** direction consistency, phase assessment, authority TF
**Cannot provide:** any execution price geometry (entry, SL, TP, size inputs)

---

*One document. Three repos. Complete wiring map. Two deep dives. Build from here.*
