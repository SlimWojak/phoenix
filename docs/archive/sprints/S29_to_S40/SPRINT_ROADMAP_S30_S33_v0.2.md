# SPRINT ROADMAP S30-S33 v0.2

**Document:** SPRINT_ROADMAP_S30_S33_v0.2.md  
**Purpose:** Production path from Cognitive Foundation to First Blood  
**Scope:** S30-S33 (build), S34 (expand), Post-S34 (harden)  
**Status:** ADVISOR SYNTHESIS COMPLETE — BUILD READY  
**Exit Criteria:** 6-pair CAPABLE, EUR/USD ACTIVE, real capital

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-01-27 | Initial draft, open questions |
| v0.2 | 2026-01-27 | All questions resolved, advisor synthesis integrated |

**v0.1 → v0.2 Summary:**
- Hunt: HPG frozen schema + determinism invariant
- Athena: Query IR intermediate + DB-layer read-only enforcement
- Checkpoint: Two-phase commit + explicit triggers only
- Shadow: Scaffold in S30, full function in S31
- Signals: Canonical Signal Envelope (CSE)
- Signalman: Multi-signal detection + adaptive freshness
- Telegram: Alert aggregation + throttle
- T2 tokens: Single-use, 5-minute expiry
- CSO: Immutable core + parameter calibration
- S33: Added ops quality gates
- Chaos: Bunny at each sprint handoff
- Schemas: Bead, HPG, Query IR, River access, 6-pair manifest defined

---

## ROADMAP OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BUILD TO PRODUCTION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  S29 ────────► S30 ────────► S31 ────────► S32 ────────► S33               │
│  COGNITIVE    LEARNING      SIGNAL &      EXECUTION     FIRST              │
│  FOUNDATION   LOOP          DECAY         PATH          BLOOD              │
│  ✓ LOCKED     [NEXT]                                                       │
│                                                                             │
│  File Seam    Hunt (HPG)    CSO           IBKR          EUR/USD            │
│  EXPLORE      Athena (IR)   Signalman     T2 Workflow   Live               │
│  Briefing     Checkpoint    Autopsy       Positions     6-Pair Cap         │
│  Session      Shadow        Telegram      Staging                          │
│               (scaffold)    (throttled)                                    │
│                                                                             │
│  BUNNY ──────► BUNNY ──────► BUNNY ──────► BUNNY ──────► BUNNY             │
│  (handoff)    (handoff)     (handoff)     (handoff)     (final)            │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                        EXPAND WHEN EARNED                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  S34 ────────► Post-S34                                                    │
│  EXPAND       HARDEN &                                                     │
│  PAIRS        TRUST                                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## PRE-S30 REQUIREMENTS (BLOCKING)

```yaml
BEFORE_S30_KICKOFF:
  status: MUST_COMPLETE
  estimated_effort: 2-3 days
  owner: OPUS (builder)
  
  deliverables:
    1_BEAD_SCHEMAS:
      file: phoenix/schemas/beads.yaml
      contains: HUNT, CONTEXT_SNAPSHOT, PERFORMANCE, AUTOPSY, POSITION
      
    2_HPG_SCHEMA:
      file: phoenix/schemas/hpg_schema.yaml
      contains: Hunt Parameter Grammar v1
      
    3_QUERY_IR_SCHEMA:
      file: phoenix/schemas/query_ir_schema.yaml
      contains: Athena query intermediate representation
      
    4_RIVER_READER:
      file: phoenix/data/river_reader.py
      contains: Read-only interface for data access
      
    5_PAIRS_MANIFEST:
      file: phoenix/config/pairs.yaml
      contains: 6-pair list with data status verification
      
  blocking: S30 CANNOT start until all 5 deliverables complete
```

---

## DEPENDENCY CHAIN

```yaml
S29_PROVIDES:
  - File seam operational (/acting/ watched)
  - EXPLORE mode (cognitive only)
  - Session management (authoritative file)
  - Lens injection (mechanism chosen)
  - Briefing worker (template for all workers)
  - Daemon health monitoring

PRE_S30_PROVIDES:
  - Bead schemas (all types)
  - HPG v1 schema
  - Query IR schema
  - River reader interface
  - 6-pair manifest (verified)

S30_REQUIRES: S29 complete + PRE_S30 complete
S30_PROVIDES:
  - Hunt engine (HPG-based, deterministic)
  - Athena (Query IR, capped, read-only)
  - Checkpoint mechanics (two-phase, explicit)
  - Shadow scaffold (CSE consumer)
  - DISPATCH:QUERY_MEMORY route

S31_REQUIRES: S30 complete + Bunny passes
S31_PROVIDES:
  - CSO (setup detection, 6 pairs, immutable core)
  - Signalman (multi-signal decay detection)
  - Autopsy (post-trade analysis)
  - State hash validation (adaptive freshness)
  - Telegram notification (aggregated, throttled)
  - Shadow full function (CSO → Shadow → tracking)

S32_REQUIRES: S31 complete + Bunny passes
S32_PROVIDES:
  - IBKR connector
  - T2 approval workflow (secure tokens)
  - Position lifecycle management
  - Reconciliation worker
  - Staging enforcement (promotion checklist)

S33_REQUIRES: S32 complete + Bunny passes
S33_PROVES:
  - 6-pair CAPABILITY
  - EUR/USD ACTIVE trading
  - N days live, no critical incidents
  - Ops quality metrics met
```

---

## CORE SCHEMAS

### Hunt Parameter Grammar (HPG v1)

```yaml
HPG_SCHEMA:
  version: "1.0"
  location: phoenix/schemas/hpg_schema.yaml
  
  fields:
    hpg_version: "1.0"
    signal_type: enum[FVG, BOS, CHoCH, OTE, LIQUIDITY_SWEEP]
    pair: string (from pairs.yaml manifest)
    session: enum[LONDON, NY, ASIA, ANY]
    time_filter:
      operator: enum[AFTER, BEFORE, BETWEEN]
      value: string (HH:MM or HH:MM-HH:MM)
    stop_model: enum[TIGHT, NORMAL, WIDE, ATR_BASED]
    risk_percent: float (0.5-2.5)
    
  variation_generation:
    base: Parse NL to HPG via LLM
    variants: Systematic permutation of parameters
    chaos_injection: Random mutations for robustness
    cap: Max 50 variants per Hunt
    
  invariant: INV-HUNT-HPG-1 "Hunt only accepts valid HPG JSON"
```

### Query IR Schema

```yaml
QUERY_IR_SCHEMA:
  version: "1.0"
  location: phoenix/schemas/query_ir_schema.yaml
  
  fields:
    query_version: "1.0"
    bead_types: list[enum] (HUNT, AUTOPSY, CONTEXT_SNAPSHOT, PERFORMANCE, POSITION)
    keywords: list[string]
    date_range:
      start: ISO8601 (optional)
      end: ISO8601 (optional)
    pair_filter: list[string] (optional)
    limit: int (max 100, default 20)
    
  enforcement:
    result_cap: 100 rows maximum
    token_budget: 2000 tokens maximum (pre-compression)
    read_only: Separate DB handle, Datasette read-only mode
    
  invariants:
    INV-ATHENA-RO-1: "Athena queries cannot modify data"
    INV-ATHENA-CAP-1: "Athena results capped at 100 rows, 2000 tokens"
```

### Canonical Signal Envelope (CSE)

```yaml
CSE_SCHEMA:
  version: "1.0"
  location: phoenix/schemas/cse_schema.yaml
  
  fields:
    cse_version: "1.0"
    signal_id: uuid
    timestamp: ISO8601
    pair: string
    source: enum[CSO, HUNT_SURVIVOR, MANUAL]
    setup_type: string
    confidence: float (0.0-1.0)
    parameters:
      entry: float
      stop: float
      target: float
      risk_percent: float
    evidence_hash: string (reference to evidence bundle)
    
  consumers:
    - Shadow boxer (paper tracking)
    - Live execution (real capital)
    - Signalman (decay monitoring)
    - Autopsy (post-trade analysis)
    
  invariant: INV-CSE-1 "All execution paths consume identical CSE format"
```

### Bead Schemas

```yaml
BEAD_SCHEMAS:
  location: phoenix/schemas/beads.yaml

HUNT_BEAD:
  bead_id: uuid
  bead_type: "HUNT"
  timestamp: ISO8601
  hpg_version: string
  hypothesis_text: string (original NL)
  hpg_json: object (frozen parameters)
  data_window:
    start: ISO8601
    end: ISO8601
  variants_tested: int
  survivors: list[object]
    - variant_id: string
    - params: object
    - sharpe: float
    - win_rate: float
    - max_drawdown: float
  random_seed: int

CONTEXT_SNAPSHOT_BEAD:
  bead_id: uuid
  bead_type: "CONTEXT_SNAPSHOT"
  timestamp: ISO8601
  session_id: uuid
  intuitions: list[string]
  open_questions: list[string]
  current_hypothesis: string
  cognitive_momentum:
    operator_stance: enum[skeptical, neutral, confident, frustrated, exploratory]
    momentum_direction: string
    discarded_paths: list[string]
    emotional_context: string

PERFORMANCE_BEAD:
  bead_id: uuid
  bead_type: "PERFORMANCE"
  timestamp: ISO8601
  source: enum[SHADOW, LIVE]
  period:
    start: ISO8601
    end: ISO8601
  pair: string
  strategy_id: string
  metrics:
    sharpe: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    trades: int
  signals_seen: int
  signals_taken: int

AUTOPSY_BEAD:
  bead_id: uuid
  bead_type: "AUTOPSY"
  timestamp: ISO8601
  position_id: uuid
  entry_thesis:
    confidence: float
    reasoning_hash: string
    setup_type: string
  outcome:
    result: enum[WIN, LOSS, BREAKEVEN]
    pnl_percent: float
    duration: string
  comparison:
    thesis_valid: bool
    unknown_factors: list[string]
    learnings: list[string]

POSITION_BEAD:
  bead_id: uuid
  bead_type: "POSITION"
  timestamp: ISO8601
  position_id: uuid
  state: enum[PROPOSED, APPROVED, SUBMITTED, FILLED, MANAGED, CLOSED]
  pair: string
  direction: enum[LONG, SHORT]
  entry_price: float (when filled)
  exit_price: float (when closed)
  size: float
  pnl: float (when closed)
  approval_token: string (for audit)

PROMOTION_BEAD:
  bead_id: uuid
  bead_type: "PROMOTION"
  timestamp: ISO8601
  strategy_id: string
  evidence_bundle_bead: uuid
  olya_reasoning: string
  approved_by: string
```

### River Access Contract

```yaml
RIVER_READER:
  location: phoenix/data/river_reader.py
  
  interface:
    get_bars(pair, timeframe, start, end) → DataFrame
    get_enrichment(pair, layer, start, end) → DataFrame
    get_latest_state(pair) → dict (current prices, spreads)
    
  constraints:
    read_only: TRUE (no writes ever)
    source: River tables only (no direct broker)
    caching: Optional, for backtest performance
    
  access_control:
    allowed_callers: Hunt, CSO, Briefing, Shadow
    denied_callers: Execution (uses separate path)
    
  invariant: INV-RIVER-RO-1 "River reader cannot modify data"
```

### 6-Pair Manifest

```yaml
PAIRS_MANIFEST:
  location: phoenix/config/pairs.yaml
  
  pairs:
    - symbol: EURUSD
      status: ACTIVE
      river_flowing: TRUE
      enrichment_layers: [L0, L1, L2, L3, L4, L5, L6]
      
    - symbol: GBPUSD
      status: ACTIVE
      river_flowing: TRUE
      enrichment_layers: [L0, L1, L2, L3, L4, L5, L6]
      
    - symbol: USDJPY
      status: ACTIVE
      river_flowing: TRUE
      enrichment_layers: [L0, L1, L2, L3, L4, L5, L6]
      
    - symbol: AUDUSD
      status: ACTIVE
      river_flowing: TRUE
      enrichment_layers: [L0, L1, L2, L3, L4, L5, L6]
      
    - symbol: USDCAD
      status: ACTIVE
      river_flowing: TRUE
      enrichment_layers: [L0, L1, L2, L3, L4, L5, L6]
      
    - symbol: NZDUSD
      status: ACTIVE
      river_flowing: TRUE
      enrichment_layers: [L0, L1, L2, L3, L4, L5, L6]

  verification:
    script: scripts/verify_pair_data.py
    runs: Before S31 start
    
  note: Verify actual data status before S31
```

---

## S30: LEARNING_LOOP

**Theme:** "The flywheel spins"  
**Duration:** 3-4 weeks  
**Detail Level:** FULL (next sprint)  
**Exit Gate:** Hypothesis → test → learn → surface working

### S30 SURFACES

```yaml
HUNT_SURFACE:
  location: phoenix/lab/hunt.py
  purpose: Hypothesis → HPG → variations → backtest → survivors
  input: Natural language hypothesis via DISPATCH:HUNT
  mechanism:
    1. LLM parses NL → HPG JSON (constrained)
    2. Hunt validates against HPG schema
    3. Hunt generates variations (systematic + chaos)
    4. Backtest each on River data
    5. Filter survivors (threshold criteria)
    6. Emit HUNT bead with full provenance
  output: Survivor report + HUNT bead

ATHENA_SURFACE:
  location: phoenix/memory/athena.py
  purpose: Queryable memory palace
  mechanism:
    1. LLM parses NL → Query IR JSON
    2. Athena validates IR
    3. Athena generates SQL (no LLM at execution)
    4. Execute SQL via Datasette (read-only)
    5. Cap results, compress to summary
  storage: Boardroom beads (all types)
  access: DISPATCH:QUERY_MEMORY (ACTING mode only)

CHECKPOINT_SURFACE:
  location: phoenix/session/checkpoint.py
  purpose: Graceful context reset with momentum
  trigger: Explicit only (Olya request, system health, context limit warning)
  mechanism: Two-phase commit (prepare → commit, abort on failure)
  output: CONTEXT_SNAPSHOT bead (includes cognitive_momentum)

SHADOW_SURFACE:
  location: phoenix/lab/shadow.py
  purpose: Paper trading scaffold (full function in S31)
  scope_s30: CSE consumer interface + divergence framework
  scope_s31: Full signal tracking from CSO
  output: Comparison reports (shadow vs live)
```

### S30 SEAMS

```yaml
SEAM_DISPATCH_HUNT:
  boundary: Dispatcher | Hunt Engine
  contract:
    dispatcher_provides: DISPATCH:HUNT intent with hypothesis text
    hunt_parses: NL → HPG JSON via LLM
    hunt_validates: HPG against schema (reject free-text)
    hunt_generates: Variations (max 50, systematic + chaos)
    hunt_backtests: Each variation on River data
    hunt_filters: Survivors by threshold
    hunt_returns: Survivor report + bead_id
  worker_type: HIVE (disposable context)
  timeout: 5 minutes
  determinism: Fixed random seeds, sorted inputs, pinned data ranges

SEAM_DISPATCH_MEMORY:
  boundary: Dispatcher | Athena
  contract:
    dispatcher_provides: DISPATCH:QUERY_MEMORY intent with query
    athena_parses: NL → Query IR JSON via LLM
    athena_validates: IR against schema
    athena_generates: SQL (deterministic)
    athena_executes: SQL via read-only Datasette
    athena_caps: 100 rows, 2000 tokens
    athena_returns: Results + bead references
  invariants:
    INV-ATHENA-RO-1: Cannot modify data
    INV-ATHENA-CAP-1: Results capped

SEAM_CHECKPOINT_SESSION:
  boundary: Checkpoint | Session Management
  mechanism: Two-phase commit
  phase_1_prepare:
    1. Session status → CHECKPOINTING
    2. Watcher pauses intents for this session_id
    3. Draft CONTEXT_SNAPSHOT bead (temporary)
    4. Validate momentum fields complete
  phase_2_commit:
    5. Persist CONTEXT_SNAPSHOT bead (finalized)
    6. Create new session file (fresh session_id)
    7. Old session status → CLOSED
    8. Lens injects new session header
    9. Log checkpoint completion
  abort:
    - Any step fails → rollback to ACTIVE
    - No partial state
    - Log abort reason

SEAM_SHADOW_CSE:
  boundary: Shadow Boxer | Signal Pipeline
  contract:
    shadow_receives: CSE-formatted signals (from CSO in S31)
    shadow_tracks: Paper positions, paper P&L
    shadow_compares: What would have happened vs actual
  s30_scope: Interface ready, awaiting signals
  s31_scope: Full tracking operational
```

### S30 KEY WIRING

```
┌─────────────────────────────────────────────────────────────────┐
│  HUNT FLOW (HPG-based)                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Olya: "Test FVG entries only after 8:30am London"              │
│                         │                                       │
│                         ▼                                       │
│  Claude: "Writing intent..." → /acting/intent.yaml              │
│          (type: DISPATCH, subtype: HUNT)                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  Hunt Worker (HIVE)                 │                        │
│  │                                     │                        │
│  │  1. LLM Parse NL → HPG JSON:        │                        │
│  │     {                               │                        │
│  │       hpg_version: "1.0",           │                        │
│  │       signal_type: "FVG",           │                        │
│  │       pair: "EURUSD",               │                        │
│  │       session: "LONDON",            │                        │
│  │       time_filter: {                │                        │
│  │         operator: "AFTER",          │                        │
│  │         value: "08:30"              │                        │
│  │       },                            │                        │
│  │       stop_model: "NORMAL",         │                        │
│  │       risk_percent: 1.0             │                        │
│  │     }                               │                        │
│  │                                     │                        │
│  │  2. Validate against HPG schema     │                        │
│  │     (reject if invalid)             │                        │
│  │                                     │                        │
│  │  3. Generate variations (max 50):   │                        │
│  │     - time: 08:00, 08:15, 08:30...  │                        │
│  │     - stop: TIGHT, NORMAL, WIDE     │                        │
│  │     - chaos mutations               │                        │
│  │                                     │                        │
│  │  4. Backtest each on River data     │                        │
│  │     (deterministic, fixed seed)     │                        │
│  │                                     │                        │
│  │  5. Filter: Sharpe > threshold      │                        │
│  │     Survivors: 3/50                 │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  HUNT bead emitted: HUNT_2026_02_01_001                         │
│  (includes: hpg_json, data_window, random_seed, survivors)      │
│                         │                                       │
│                         ▼                                       │
│  Response: "3 survivors. Best: V2 (Sharpe 1.6)"                 │
│  Lens injects summary → Claude presents                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│  ATHENA QUERY FLOW (Query IR)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Olya: "What did I learn about ranging markets?"                │
│                         │                                       │
│                         ▼                                       │
│  Claude: "Querying Athena..." → /acting/intent.yaml             │
│          (type: DISPATCH, subtype: QUERY_MEMORY)                │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  Athena Worker                      │                        │
│  │                                     │                        │
│  │  1. LLM Parse NL → Query IR:        │                        │
│  │     {                               │                        │
│  │       query_version: "1.0",         │                        │
│  │       bead_types: ["HUNT",          │                        │
│  │         "CONTEXT_SNAPSHOT"],        │                        │
│  │       keywords: ["ranging",         │                        │
│  │         "markets"],                 │                        │
│  │       date_range: null,             │                        │
│  │       limit: 20                     │                        │
│  │     }                               │                        │
│  │                                     │                        │
│  │  2. Validate against Query IR       │                        │
│  │                                     │                        │
│  │  3. Generate SQL (deterministic)    │                        │
│  │                                     │                        │
│  │  4. Execute via read-only Datasette │                        │
│  │                                     │                        │
│  │  5. Cap: 100 rows, 2000 tokens      │                        │
│  │                                     │                        │
│  │  6. Compress to summary             │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  Response (≤500 tokens):                                        │
│    "From your beads (January):                                  │
│     - JAN 15: Tighter stops in ranging (Hunt: 3 survivors)      │
│     - JAN 22: Correlation spike confusion (unresolved)          │
│     Pattern: Your ranging insights improving edge"              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│  CHECKPOINT FLOW (Two-Phase Commit)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER: Explicit only                                         │
│    - Olya: "checkpoint please"                                  │
│    - System health warning                                      │
│    - Context limit (mechanical, not subjective)                 │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  PHASE 1: PREPARE                   │                        │
│  │  1. Session status → CHECKPOINTING  │                        │
│  │  2. Watcher pauses this session     │                        │
│  │  3. Draft CONTEXT_SNAPSHOT (temp)   │                        │
│  │  4. Validate momentum complete      │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                     SUCCESS?                                    │
│                    /        \                                   │
│                  YES         NO                                 │
│                   │           │                                 │
│                   ▼           ▼                                 │
│  ┌─────────────────────┐  ┌─────────────────────┐               │
│  │ PHASE 2: COMMIT     │  │ ABORT               │               │
│  │ 5. Persist bead     │  │ - Rollback ACTIVE   │               │
│  │ 6. New session file │  │ - No Lens injection │               │
│  │ 7. Old → CLOSED     │  │ - Log abort reason  │               │
│  │ 8. Lens injects new │  │                     │               │
│  │ 9. Log completion   │  │                     │               │
│  └─────────────────────┘  └─────────────────────┘               │
│                                                                 │
│  INVARIANT: INV-CHECKPOINT-ATOMIC-1                             │
│  "Checkpoint is all-or-nothing; no partial state"               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### S30 INVARIANTS

```yaml
INV-HUNT-HPG-1:
  statement: "Hunt only accepts valid HPG JSON, rejects free-text"
  test: test_hunt_hpg_validation.py
  proof: Invalid HPG → rejection with error

INV-HUNT-DET-1:
  statement: "Identical HPG + identical data window → identical results"
  test: test_hunt_determinism.py
  proof: Same Hunt twice → byte-identical survivor ranking

INV-ATHENA-RO-1:
  statement: "Athena queries cannot create, modify, or delete data"
  test: test_athena_readonly_enforcement.py
  proof: INSERT/UPDATE/DELETE attempt → rejected at DB layer

INV-ATHENA-CAP-1:
  statement: "Athena results capped at 100 rows, 2000 tokens"
  test: test_athena_caps.py
  proof: Large query → capped result, no overflow

INV-CHECKPOINT-ATOMIC-1:
  statement: "Checkpoint is all-or-nothing; no partial state"
  test: test_checkpoint_abort_rollback.py
  proof: Kill mid-checkpoint → clean rollback

INV-CHECKPOINT-EXPLICIT-1:
  statement: "Checkpoint only on explicit trigger"
  test: test_checkpoint_triggers.py
  proof: No "Claude detects pressure" triggers

INV-SHADOW-ISOLATED-1:
  statement: "Shadow never touches real capital"
  test: test_shadow_isolation.py
  proof: Shadow positions are paper-only
```

### S30 EXIT GATES

```yaml
GATE_S30_1:
  name: HUNT_HPG_WORKS
  criterion: HPG accepted, variations generated, deterministic results
  test: test_e2e_hunt.py
  evidence: Hunt completes in <5 min, survivors ranked, reproducible

GATE_S30_2:
  name: ATHENA_QUERY_IR
  criterion: Query IR parsed, SQL generated, results capped
  test: test_athena_query.py
  evidence: NL → Query IR → results ≤100 rows

GATE_S30_3:
  name: CHECKPOINT_ATOMIC
  criterion: Two-phase commit, explicit trigger, abort rollback
  test: test_checkpoint_e2e.py
  evidence: Checkpoint completes OR cleanly aborts

GATE_S30_4:
  name: SHADOW_SCAFFOLD
  criterion: CSE consumer ready, divergence framework built
  test: test_shadow_scaffold.py
  evidence: Shadow can receive CSE, track paper positions

GATE_S30_5:
  name: BUNNY_PASSES
  criterion: All S30 chaos vectors green
  test: chaos_suite_s30.py
  evidence: BUNNY_REPORT_S30.md

GATE_S30_6:
  name: FLYWHEEL_FEELS_ALIVE
  criterion: Olya confirms "learning is accumulating"
  test: Manual session
  evidence: Verbal/written confirmation

BINARY_EXIT:
  statement: "Hypothesis → test → learn → surface working"
```

### S30 CHAOS VECTORS

```yaml
CV_S30_HUNT_DETERMINISM:
  inject: Run same Hunt twice with same HPG
  expect: Byte-identical survivor ranking

CV_S30_HPG_FUZZING:
  inject: Malformed HPG (missing fields, wrong types, free-text)
  expect: Rejected with error, not crash

CV_S30_BEAD_FLOOD:
  inject: 1000 Hunt variants (exceeds cap)
  expect: Cap enforced (50), alert raised

CV_S30_ATHENA_WRITE_ATTEMPT:
  inject: Malicious query attempts INSERT/UPDATE/DELETE
  expect: Rejected at DB layer

CV_S30_ATHENA_BOMB:
  inject: Query requesting 1M rows
  expect: Capped at 100, no OOM

CV_S30_MOMENTUM_LOSS:
  inject: Kill daemon mid-checkpoint
  expect: Abort + rollback, no partial state

CV_S30_CHECKPOINT_RACE:
  inject: Two checkpoint requests same session
  expect: First wins, second rejected
```

### S30 HANDOFF TO S31

```yaml
S31_RECEIVES:
  hunt_engine:
    - HPG parsing + validation
    - Variation generation (systematic + chaos)
    - Deterministic backtest
    - Survivor filtering
    - HUNT bead emission

  athena:
    - Query IR parsing + validation
    - SQL generation
    - Read-only Datasette execution
    - Result capping + compression

  checkpoint:
    - Two-phase commit
    - Explicit triggers only
    - Abort rollback
    - Cognitive momentum preservation

  shadow_scaffold:
    - CSE consumer interface
    - Paper position tracking schema
    - Divergence calculation framework
    - Awaiting CSO signals

  bunny_report:
    - BUNNY_REPORT_S30.md
    - All S30 chaos vectors green
```

---

## S31: SIGNAL_AND_DECAY

**Theme:** "Phoenix watches"  
**Duration:** 2-3 weeks  
**Detail Level:** MEDIUM  
**Exit Gate:** Phoenix detects setups AND warns before decay proves itself

### S31 DELIVERS

```yaml
CSO_CAPABILITY:
  what: Chief Strategy Officer — continuous setup detection
  architecture: Immutable core + parameter calibration
  scans: 6 pairs (from pairs.yaml manifest)
  outputs:
    - CSE-formatted signals
    - Setup quality scores (NONE/FORMING/READY)
    - Reasoning breakdown (decomposable)
    - Evidence bundles for T2
  integration:
    - Morning briefing shows all 6 pairs
    - Telegram push when >0.8 confidence (aggregated)
    - DISPATCH:SCAN for on-demand check

CSO_STRUCTURE:
  immutable_core:
    location: phoenix/cso/strategy_core.py
    contains: ICT methodology rules (hardcoded)
    constraint: No dynamic imports, no eval(), no parameter-based code paths
  calibratable_params:
    location: phoenix/cso/strategy_params.yaml
    contains: Thresholds, weights, time filters
    mechanism: Config reload, schema validated

SIGNALMAN_CAPABILITY:
  what: Multi-signal drift and decay detection
  signals:
    - sharpe_drift: Rolling Sharpe vs baseline
    - win_rate_drift: Rolling win rate vs baseline
    - input_distribution_shift: Statistical test (KS)
    - autopsy_semantic_drift: (v2, keyword matching v1)
  aggregation: ANY signal breaches threshold → ONE-WAY-KILL
  freshness: Adaptive based on session event count
  display: Remaining TTL in approval UI

AUTOPSY_CAPABILITY:
  what: Post-trade analysis
  runs: Async after position close
  compares: Entry thesis vs outcome
  outputs: AUTOPSY bead + learning extraction
  integration: Queryable via Athena

STATE_HASH_VALIDATION:
  what: Stale context execution guard
  freshness: Adaptive (event-based, not fixed time)
  display: Remaining TTL shown in approval UI

TELEGRAM_PLANE:
  what: Notification surface (not thinking partner)
  aggregation:
    window: 5 minutes
    multiple_same_pair: Single alert with count
    multiple_pairs: Batched ("3 setups forming")
  throttle:
    max_per_hour: 10 (configurable)
    exception: HALT, CRITICAL (bypass)
  security: Notification only, approval in Claude Desktop
```

### S31 KEY COMPONENTS

```yaml
COMPONENTS:
  phoenix/cso/strategy_core.py:
    - ICT methodology rules (immutable)
    - High-probability criteria
    - CANNOT be modified by calibration

  phoenix/cso/strategy_params.yaml:
    - Thresholds (calibratable)
    - Weights (calibratable)
    - Schema validated at load

  phoenix/cso/scanner.py:
    - Continuous pair scanning (6 pairs)
    - Quality scoring
    - CSE emission

  phoenix/monitoring/signalman.py:
    - Multi-signal detection
    - Threshold management
    - ONE-WAY-KILL trigger
    - Adaptive freshness

  phoenix/lab/autopsy.py:
    - Trade reconstruction
    - Thesis vs outcome comparison
    - Learning extraction

  phoenix/notifications/telegram.py:
    - Takopi integration
    - Alert aggregation
    - Throttle enforcement
```

### S31 INVARIANTS

```yaml
INV-SIGNALMAN-MULTI-1:
  statement: "Decay detection uses multiple signals, not single threshold"
  test: test_signalman_multi.py

INV-CSO-CORE-1:
  statement: "CSO strategy logic is immutable; only parameters are calibratable"
  test: test_cso_immutable.py
  proof: strategy_core.py has no dynamic code execution

INV-ALERT-THROTTLE-1:
  statement: "Max 10 alerts per hour (except HALT, CRITICAL)"
  test: test_alert_throttle.py

INV-CSE-1:
  statement: "All execution paths consume identical CSE format"
  test: test_cse_format.py
```

### S31 EXIT GATES

```yaml
GATE_S31_1:
  name: CSO_SCANS_6_PAIRS
  criterion: Morning briefing shows setup status for all 6 pairs
  evidence: CSE signals for each pair, quality scores displayed

GATE_S31_2:
  name: SIGNALMAN_MULTI_SIGNAL
  criterion: Multiple signals monitored, ANY triggers ONE-WAY-KILL
  evidence: Inject drift → alert fires → defensive mode

GATE_S31_3:
  name: AUTOPSY_RUNS
  criterion: Position closes → AUTOPSY bead appears
  evidence: Query Athena for autopsy, reasoning comparison present

GATE_S31_4:
  name: TELEGRAM_THROTTLED
  criterion: Alert storm → aggregated, throttled output
  evidence: 100 signals → ≤10 messages

GATE_S31_5:
  name: STATE_HASH_ADAPTIVE
  criterion: Freshness TTL displayed, adaptive to events
  evidence: Approval UI shows remaining TTL

GATE_S31_6:
  name: BUNNY_PASSES
  criterion: All S31 chaos vectors green
  evidence: BUNNY_REPORT_S31.md

BINARY_EXIT:
  statement: "Phoenix detects setups AND warns before decay proves itself"
```

### S31 CHAOS VECTORS

```yaml
CV_S31_ALERT_STORM:
  inject: 1000 READY signals in 1 minute
  expect: ≤10 Telegram messages, aggregated content

CV_S31_CSO_HALLUCINATION:
  inject: Spoof River data with garbage
  expect: CSO rejects invalid data, no false READY

CV_S31_SIGNALMAN_GAMING:
  inject: Exactly-at-threshold Sharpe drift
  expect: Consistent behavior (deterministic boundary)

CV_S31_CALIBRATION_INJECTION:
  inject: Attempt to modify strategy_core.py via params
  expect: Rejected, core unchanged

CV_S31_AUTOPSY_FLOOD:
  inject: 100 positions close simultaneously
  expect: All autopsies complete, no lost beads
```

---

## S32: EXECUTION_PATH

**Theme:** "Real markets"  
**Duration:** 3-4 weeks  
**Detail Level:** MEDIUM  
**Exit Gate:** T2 workflow proven on paper, IBKR connected

### S32 DELIVERS

```yaml
IBKR_CONNECTOR:
  what: Interactive Brokers API integration
  capabilities:
    - Order submission (market, limit, bracket)
    - Position query
    - Fill tracking
    - Account balance
  tier: T2 (capital-affecting, human gate required)
  mock: Full mock client for testing
  reconciliation: Periodic state comparison

T2_APPROVAL_WORKFLOW:
  what: Human sovereignty gate for capital decisions
  flow:
    1. CSO presents evidence bundle (CSE)
    2. State hash validated (fresh, adaptive TTL)
    3. Human reviews reasoning
    4. Explicit approval (APPROVE button)
    5. Approval token generated (single-use, 5 min expiry)
    6. Order submitted with token
  evidence_displayed:
    - Setup quality score + breakdown
    - HTF/LTF alignment
    - Risk parameters (stop, target, size)
    - Red check results
    - State hash freshness TTL

T2_TOKEN_SECURITY:
  properties:
    id: uuid (unique per approval)
    intent_id: uuid (linked to specific intent)
    timestamp: ISO8601
    expires: timestamp + 5 minutes
    used: boolean (starts false)
  validation:
    - Token exists
    - Not expired
    - Not used (single-use)
    - Intent ID matches
  anti_replay: Token consumed on use

POSITION_LIFECYCLE:
  what: State machine for position management
  states: PROPOSED → APPROVED → SUBMITTED → FILLED → MANAGED → CLOSED
  tracking: Entry thesis, fill details, P&L, exit reason
  beads: POSITION bead at each state transition

PROMOTION_CHECKLIST:
  what: Negative proof before strategy activation
  evidence_required:
    duration:
      min_sessions: 20 trading sessions
      min_regimes: 2 distinct (trend + range)
    performance:
      max_drawdown: recorded
      worst_day: recorded
      sharpe: recorded
    defensive:
      signalman_kills: count of would-have-killed
      override_frequency: Olya override rate
    reasoning:
      autopsy_summary: patterns from shadow autopsies
  ceremony:
    intent: DISPATCH:PROMOTE_STRATEGY
    gate: T2 (human approval)
    bead: PROMOTION bead references evidence bundle

STAGING_ENFORCEMENT:
  what: Shadow period before live
  rule: INV-STAGE-BEFORE-LIVE
  mechanism: Promotion checklist must pass
```

### S32 INVARIANTS

```yaml
INV-T2-TOKEN-1:
  statement: "Approval tokens are single-use, expire in 5 minutes"
  test: test_t2_token_replay.py
  proof: Attempt reuse → rejected

INV-PROMOTION-EVIDENCE-1:
  statement: "Strategy promotion requires evidence bundle"
  test: test_promotion_checklist.py
  proof: Promotion without bundle → rejected
```

### S32 KEY RISKS

```yaml
RISK_1_IBKR_API:
  description: Complex, rate-limited, sometimes unreliable
  mitigation:
    - Mock client for all testing
    - Retry logic with backoff
    - Position reconciliation
    - Manual override always available

RISK_2_ORDER_STATE:
  description: State desync (Phoenix vs IBKR)
  mitigation:
    - Reconciliation worker (periodic)
    - Heartbeat to IBKR
    - Alert on mismatch

RISK_3_APPROVAL_FATIGUE:
  description: Too many gates → mental bypass
  mitigation:
    - Evidence glanceable
    - Clear APPROVE/PASS options
    - No false urgency
```

### S32 EXIT GATES

```yaml
GATE_S32_1:
  name: IBKR_CONNECTED
  criterion: Query account, submit paper order, receive fill
  evidence: Paper trade round-trip complete

GATE_S32_2:
  name: T2_TOKENS_SECURE
  criterion: Single-use, 5 min expiry, replay rejected
  evidence: Token reuse attempt → rejected

GATE_S32_3:
  name: POSITION_LIFECYCLE_TRACKED
  criterion: State machine transitions correctly
  evidence: POSITION beads at each state

GATE_S32_4:
  name: RECONCILIATION_WORKS
  criterion: Induced mismatch → detected → alerted
  evidence: Fake drift → reconciler catches

GATE_S32_5:
  name: PROMOTION_CHECKLIST
  criterion: Shadow → live requires evidence bundle
  evidence: Promotion without bundle → rejected

GATE_S32_6:
  name: BUNNY_PASSES
  criterion: All S32 chaos vectors green
  evidence: BUNNY_REPORT_S32.md

BINARY_EXIT:
  statement: "T2 workflow proven on paper, IBKR connected"
```

### S32 CHAOS VECTORS

```yaml
CV_S32_TOKEN_REPLAY:
  inject: Attempt to reuse approval token
  expect: Rejected, audit logged

CV_S32_TOKEN_EXPIRED:
  inject: Use token after 5 minutes
  expect: Rejected as expired

CV_S32_ORDER_RACE:
  inject: Two orders same intent simultaneously
  expect: One succeeds, one rejected (idempotent)

CV_S32_RECONCILIATION_DRIFT:
  inject: IBKR mock returns wrong position
  expect: Drift detected, alert fired

CV_S32_PROMOTION_BYPASS:
  inject: Attempt live without shadow period
  expect: Rejected, checklist incomplete
```

---

## S33: FIRST_BLOOD

**Theme:** "One pair, real money"  
**Duration:** 3-4 weeks (validation period)  
**Detail Level:** MEDIUM  
**Exit Gate:** 6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents

### S33 PROVES

```yaml
CAPABILITY_COMPLETE:
  architecture: Multi-pair (6 pairs scan, detect, execute)
  active_trading: EUR/USD with real capital
  superpowers_operational:
    - Thinking partner (EXPLORE) ✓
    - Morning briefing ✓
    - Hunt (HPG-based) ✓
    - Athena (Query IR) ✓
    - CSO (6-pair scan) ✓
    - Signalman (multi-signal) ✓
    - Autopsy (post-trade analysis) ✓
    - T2 approval (secure tokens) ✓
    - Position management ✓

PRODUCTION_CRITERIA:
  trading:
    - Real capital at risk
    - Real P&L
    - Real fills from IBKR
  operations:
    - 24/7 monitoring
    - Daemon health maintained
    - Alerts routing correctly
  incidents:
    - Runbooks documented
    - Escalation paths defined
    - N days without critical incident

OPS_QUALITY:
  reconciliation: Zero drift events
  alert_accuracy: Precision >80%, recall >90%
  latency: Median e2e <30s
  daemon_uptime: >99%

MULTI_PAIR_PROOF:
  morning_briefing: Shows all 6 pairs
  cso_scan: Returns setups across 6 pairs
  hunt: Can test hypothesis on any pair
  t2_workflow: Works for any pair
  active: EUR/USD only (governance decision)
```

### S33 EXIT GATES

```yaml
GATE_S33_1:
  name: 6_PAIR_CAPABILITY
  criterion: System scans, detects, can execute on all 6 pairs
  evidence: Briefing shows 6 pairs, Hunt works on GBP/USD

GATE_S33_2:
  name: EUR_USD_LIVE
  criterion: Real trade executed with real capital
  evidence: IBKR confirms fill, P&L is real

GATE_S33_3:
  name: N_DAYS_STABLE
  criterion: N consecutive days, no critical incidents
  value_of_N: 5-10 trading days (TBD)
  evidence: Incident log empty or all resolved

GATE_S33_OPS_1:
  name: RECONCILIATION_CLEAN
  criterion: Zero position mismatches during validation
  evidence: Reconciliation log shows 0 drift

GATE_S33_OPS_2:
  name: ALERT_ACCURACY
  criterion: Precision >80%, recall >90%
  evidence: Alert audit log reviewed

GATE_S33_OPS_3:
  name: LATENCY_ACCEPTABLE
  criterion: Median e2e <30s
  evidence: Latency percentiles logged

GATE_S33_OPS_4:
  name: DAEMON_UPTIME
  criterion: >99% during validation
  evidence: Heartbeat logs show <1% gap

GATE_S33_5:
  name: OLYA_TRUSTS_IT
  criterion: Olya comfortable with system
  evidence: Verbal confirmation, continued use

GATE_S33_6:
  name: RUNBOOKS_TESTED
  criterion: At least one incident drill completed
  evidence: Drill log with resolution time

BINARY_EXIT:
  statement: "6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents, ops quality met"
```

### S33 SUCCESS CRITERIA

```yaml
A_DAY_IN_OLYAS_LIFE_WORKS:
  6am: Morning briefing (6 pairs shown) ✓
  6:30am: EXPLORE thinking session ✓
  7:30am: Hunt tests hypothesis (HPG) ✓
  8:30am: Setup alert (Telegram, aggregated) ✓
  9am: T2 approval (secure token, real capital) ✓
  3pm: Position managed/closed ✓
  5pm: Athena query (Query IR) ✓
  overnight: Phoenix watches (Signalman) ✓

SYSTEM_HEALTH:
  halt_latency: <50ms (proven)
  daemon_uptime: >99%
  alert_latency: <60s
  reconciliation: Zero drift
  latency_e2e: <30s median
```

---

## S34: EXPAND_PAIRS

**Theme:** "Governance, not architecture"  
**Detail Level:** DIRECTIONAL  
**Trigger:** S33 stable, Olya trusts system

### S34 APPROACH

```yaml
EXPANSION_IS_CONFIGURATION:
  architecture: Already multi-pair (proven S33)
  adding_pair: Config + ceremony, not rebuild

EXPANSION_CEREMONY:
  per_pair:
    1. Olya selects pair (e.g., GBP/USD)
    2. Shadow period (N days)
    3. Review shadow performance
    4. Promotion checklist (evidence bundle)
    5. Olya approves live (T2)
    6. Config update (pair → ACTIVE)
    7. Monitoring period

EXPANSION_ORDER:
  suggested:
    - Pair 2: GBP/USD (similar to EUR/USD)
    - Pair 3-4: Other majors
    - Pair 5-6: As trust builds
  actual: Olya decides based on methodology

NOT_S34:
  - Code changes (architecture is done)
  - New capabilities (superpowers complete)
  - Rush (trust-gated, not time-gated)
```

---

## POST-S34: HARDEN_AND_TRUST

**Theme:** "Earn it through use"  
**Detail Level:** DIRECTIONAL

```yaml
REAL_WORLD_HARDENING:
  - Edge cases surface from live trading
  - Signalman thresholds tuned from real data
  - CSO parameters refined (Olya's feedback)
  - Regime-specific learnings accumulated

TRUST_BUILDING:
  - Consistent performance
  - No surprises
  - Graceful handling of market stress
  - Olya's confidence grows

CALIBRATION_TRACK:
  - Olya's Claude (CSO) captures methodology
  - Parameters validated against schema
  - Core logic NEVER touched
  - Runs PARALLEL (her pace, not ours)

FUTURE_HORIZONS:
  when_earned:
    - Echo domain (crypto via Hyperliquid)
    - Foundry-as-a-Service
  trigger: S34 stable, Olya confident, battle-tested
```

---

## BUNNY ROADMAP (Per-Sprint Chaos)

```yaml
BUNNY_PHILOSOPHY:
  rule: Sprint N+1 cannot start until Bunny passes on Sprint N
  entropy_quota: Minimum 5 chaos vectors per sprint
  coverage: All new invariants must have attack vector
  evidence: BUNNY_REPORT_{SPRINT}.md in handoff

S29_TO_S30_BUNNY:
  focus: File seam integrity
  vectors:
    - FS races (concurrent intents)
    - Malformed intents
    - Session collisions
    - Daemon crashes
    - Checkpoint interrupts

S30_TO_S31_BUNNY:
  focus: Hunt + Athena
  vectors:
    - HPG fuzzing (invalid schemas)
    - Hunt determinism (reproducibility)
    - Athena write attempts
    - Athena query bombs
    - Bead floods
    - Checkpoint races

S31_TO_S32_BUNNY:
  focus: CSO + Signalman
  vectors:
    - Alert storms
    - CSO hallucination (garbage data)
    - Signalman threshold gaming
    - Calibration injection
    - Autopsy floods

S32_TO_S33_BUNNY:
  focus: Execution
  vectors:
    - Token replay attacks
    - Token expiry
    - Order races
    - Reconciliation drift
    - Promotion bypass

S33_FINAL_BUNNY:
  focus: Production readiness
  vectors:
    - Full integration chaos
    - Multi-pair stress
    - Regime simulation
    - Overnight stability
```

---

## CROSS-SPRINT INVARIANTS

```yaml
SOVEREIGNTY:
  INV-SOVEREIGN-1: "Human sovereignty over capital is absolute"
  INV-SOVEREIGN-2: "T2 requires human gate"

HALT:
  INV-HALT-1: "halt_local < 50ms"
  INV-HALT-2: "halt_cascade < 500ms"

DATA:
  INV-DATA-CANON: "Single truth from River"
  INV-RIVER-RO-1: "River reader cannot modify data"

COGNITIVE:
  INV-EXPLORE-3: "/acting/ triggers machinery; /explore/ does not"
  INV-EXPLORE-4: "EXPLORE has no external system access"
  INV-CONTEXT-1: "Claude holds conversation only"

HUNT:
  INV-HUNT-HPG-1: "Hunt only accepts valid HPG JSON"
  INV-HUNT-DET-1: "Identical HPG + data window → identical results"

ATHENA:
  INV-ATHENA-RO-1: "Athena queries cannot modify data"
  INV-ATHENA-CAP-1: "Results capped at 100 rows, 2000 tokens"

CHECKPOINT:
  INV-CHECKPOINT-ATOMIC-1: "Checkpoint is all-or-nothing"
  INV-CHECKPOINT-EXPLICIT-1: "Checkpoint only on explicit trigger"

SIGNALS:
  INV-CSE-1: "All execution paths consume identical CSE format"
  INV-SIGNALMAN-MULTI-1: "Decay detection uses multiple signals"
  INV-CSO-CORE-1: "CSO strategy logic is immutable"
  INV-ALERT-THROTTLE-1: "Max 10 alerts per hour (except HALT)"

EXECUTION:
  INV-T2-TOKEN-1: "Approval tokens single-use, expire in 5 minutes"
  INV-PROMOTION-EVIDENCE-1: "Strategy promotion requires evidence bundle"
  INV-SHADOW-ISOLATED-1: "Shadow never touches real capital"

RISK:
  INV-EVIDENCE-1: "No entry without evidence bundle"
  INV-RISK-DEFENSIVE: "ONE-WAY-KILL on decay/drawdown"
  INV-STAGE-BEFORE-LIVE: "Shadow period before live"
  INV-EXPOSURE-LIMIT: "2.5% max per currency"
```

---

## EFFORT ESTIMATES

```yaml
REALISTIC_TIMELINE:
  PRE_S30: 2-3 days (schemas + contracts)
  S30: 3-4 weeks (was 2-3, +1 for HPG + bead schemas)
  S31: 2-3 weeks (CSO calibration parallel)
  S32: 3-4 weeks (IBKR known complexity)
  S33: 3-4 weeks (validation, not build)

TOTAL_TO_PRODUCTION: 14-18 weeks realistic

CRITICAL_PATH:
  1. Bead schemas (blocks S30)
  2. HPG v1 (blocks Hunt)
  3. CSO calibration (parallel, affects S31 scope)
  4. IBKR connector (S32 risk)

BUILD_CONFIDENCE: 85%
```

---

## SUMMARY

| Sprint | Theme | Exit Gate | Duration | Status |
|--------|-------|-----------|----------|--------|
| PRE-S30 | Schemas | 5 deliverables | 2-3 days | BLOCKING |
| S30 | Learning Loop | Hunt + Athena + Checkpoint | 3-4 weeks | NEXT |
| S31 | Signal & Decay | CSO + Signalman + Telegram | 2-3 weeks | AFTER S30 |
| S32 | Execution Path | IBKR + T2 + Positions | 3-4 weeks | AFTER S31 |
| S33 | First Blood | 6-pair capable, EUR/USD live | 3-4 weeks | VALIDATION |
| S34 | Expand Pairs | Config + ceremony | TBD | EARNED |

**PRODUCTION GATE (S33):**
- ALL superpowers operational
- 6-pair CAPABLE (architecture)
- EUR/USD ACTIVE (governance)
- N days no critical incidents
- Ops quality metrics met

---

**STATUS:** v0.2 ADVISOR SYNTHESIS COMPLETE  
**BUILD CONFIDENCE:** 85%  
**NEXT:** PRE-S30 deliverables (2-3 days), then S30 kickoff  
**CRITICAL PATH:** Schemas → HPG → Hunt → Athena → CSO → IBKR → Live

**OINK OINK.** 🐗🔥
