# SPRINT ROADMAP S30-S33 v0.1

**Document:** SPRINT_ROADMAP_S30_S33_v0.1.md  
**Purpose:** Production path from Cognitive Foundation to First Blood  
**Scope:** S30-S33 (build), S34 (expand), Post-S34 (harden)  
**Status:** DRAFT — Awaiting advisor review  
**Exit Criteria:** 6-pair CAPABLE, EUR/USD ACTIVE, real capital

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
│  File Seam    Hunt          CSO           IBKR          EUR/USD            │
│  EXPLORE      Athena        Signalman     T2 Workflow   Live               │
│  Briefing     Checkpoint    Autopsy       Positions     6-Pair Cap         │
│  Session      Shadow        Telegram      Staging                          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                        EXPAND WHEN EARNED                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  S34 ────────► Post-S34                                                    │
│  EXPAND       HARDEN &                                                     │
│  PAIRS        TRUST                                                        │
│                                                                             │
│  GBP/USD      Real-world                                                   │
│  Pairs 3-6    Edge cases                                                   │
│  (trust-      Tuning                                                       │
│   gated)      Calibration                                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
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

S30_REQUIRES: S29 complete
S30_PROVIDES:
  - Hunt engine (hypothesis testing)
  - Athena (memory palace)
  - Checkpoint mechanics (cognitive momentum)
  - Shadow boxing (paper validation)
  - DISPATCH:QUERY_MEMORY route

S31_REQUIRES: S30 complete (Hunt for signals, Athena for patterns)
S31_PROVIDES:
  - CSO (setup detection across 6 pairs)
  - Signalman (decay detection)
  - Autopsy (post-trade analysis)
  - State hash validation
  - Telegram notification plane

S32_REQUIRES: S31 complete (signals to execute)
S32_PROVIDES:
  - IBKR connector
  - T2 approval workflow (with state hash)
  - Position lifecycle management
  - Staging enforcement

S33_REQUIRES: S32 complete (execution capability)
S33_PROVES:
  - 6-pair CAPABILITY
  - EUR/USD ACTIVE trading
  - N days live, no critical incidents
```

---

## S30: LEARNING_LOOP

**Theme:** "The flywheel spins"  
**Duration:** 2-3 weeks  
**Detail Level:** MEDIUM (next sprint)  
**Exit Gate:** Hypothesis → test → learn → surface working

### S30 SURFACES

```yaml
HUNT_SURFACE:
  location: phoenix/lab/hunt.py
  purpose: Hypothesis → variations → backtest → survivors
  input: Natural language hypothesis via DISPATCH:HUNT
  output: Survivor report + HUNT bead

ATHENA_SURFACE:
  location: phoenix/memory/athena.py
  purpose: Queryable memory palace
  storage: Boardroom beads (all types)
  query: Datasette interface
  access: DISPATCH:QUERY_MEMORY (ACTING mode only)

CHECKPOINT_SURFACE:
  location: phoenix/session/checkpoint.py
  purpose: Graceful context reset with momentum
  trigger: Claude detects pressure OR Olya requests
  output: CONTEXT_SNAPSHOT bead (includes cognitive_momentum)

SHADOW_SURFACE:
  location: phoenix/lab/shadow.py
  purpose: Paper trading with real signals
  mode: Parallel to live (no capital risk)
  output: Comparison reports (shadow vs live)
```

### S30 SEAMS

```yaml
SEAM_DISPATCH_HUNT:
  boundary: Dispatcher | Hunt Engine
  contract:
    dispatcher_provides: DISPATCH:HUNT intent with hypothesis text
    hunt_returns: survivor report + bead_id
  hunt_internals:
    1. Parse hypothesis → testable parameters
    2. Generate N variations (configurable, default 10)
    3. Run backtest on each (local LLM for eval)
    4. Filter survivors (threshold: Sharpe, win rate, etc.)
    5. Compress results → summary
    6. Emit HUNT bead
  worker_type: HIVE (disposable context, can use full window)
  timeout: 5 minutes

SEAM_DISPATCH_MEMORY:
  boundary: Dispatcher | Athena
  contract:
    dispatcher_provides: DISPATCH:QUERY_MEMORY intent with query
    athena_returns: results + bead references
  query_types:
    - Natural language → Datasette SQL
    - "Show me losing patterns" → filtered bead query
    - "What did I learn about X" → semantic search
  invariant: Read-only (Athena never writes during query)

SEAM_CHECKPOINT_SESSION:
  boundary: Checkpoint | Session Management
  contract:
    checkpoint_signals: Session status → CHECKPOINTING
    checkpoint_writes: CONTEXT_SNAPSHOT bead
    session_creates: New session file (fresh ID)
    lens_injects: New session header
  atomicity: Per S29 session seam contract
  cognitive_momentum:
    - operator_stance
    - momentum_direction
    - discarded_paths
    - emotional_context

SEAM_SHADOW_EXECUTION:
  boundary: Shadow Boxer | Signal Pipeline
  contract:
    shadow_receives: Same signals as live pipeline
    shadow_tracks: Paper positions, paper P&L
    shadow_compares: What would have happened vs actual
  purpose: Validate before risking capital
  output: Divergence report (shadow vs Olya's actual decisions)
```

### S30 KEY WIRING

```
┌─────────────────────────────────────────────────────────────────┐
│  HUNT FLOW                                                      │
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
│  │  1. Parse: "FVG + 8:30am filter"    │                        │
│  │  2. Generate: 10 variations         │                        │
│  │     - Timing: 8:00, 8:15, 8:30, 8:45│                        │
│  │     - Stop: tight, normal, wide     │                        │
│  │  3. Backtest each on River data     │                        │
│  │  4. Filter: Sharpe > 1.0            │                        │
│  │  5. Survivors: 3/10                 │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  HUNT bead emitted: HUNT_2026_02_01_001                         │
│  Response: "3 survivors. Best: V2 (Sharpe 1.6)"                 │
│                         │                                       │
│                         ▼                                       │
│  Lens injects summary → Claude presents                         │
│                                                                 │
│  Olya: "Queue V2 for shadow"                                    │
│                         │                                       │
│                         ▼                                       │
│  Shadow boxer tracks V2 signals (paper only)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

```
┌─────────────────────────────────────────────────────────────────┐
│  MEMORY QUERY FLOW                                              │
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
│  │  1. Parse query intent              │                        │
│  │  2. Search beads: HUNT, EXPLORE,    │                        │
│  │     CONTEXT_SNAPSHOT, AUTOPSY       │                        │
│  │  3. Filter: "ranging" + "markets"   │                        │
│  │  4. Rank by relevance               │                        │
│  │  5. Compress to summary             │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  Response:                                                      │
│    "From your beads (January):                                  │
│     - JAN 15: Tighter stops in ranging (Hunt: 3 survivors)      │
│     - JAN 22: Correlation spike confusion (unresolved)          │
│     Pattern: Your ranging insights improving edge"              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### S30 INVARIANTS

```yaml
INV-HUNT-1:
  statement: "Hunt respects halt (checks before backtest)"
  test: test_hunt_halted.py

INV-HUNT-2:
  statement: "Hunt uses River data only (no forward-fill)"
  test: test_hunt_data_integrity.py

INV-ATHENA-1:
  statement: "Athena queries are read-only (never writes during query)"
  test: test_athena_readonly.py

INV-CHECKPOINT-1:
  statement: "Checkpoint is atomic (no partial state)"
  test: test_checkpoint_atomicity.py

INV-CHECKPOINT-2:
  statement: "Checkpoint preserves cognitive_momentum"
  test: test_checkpoint_momentum.py

INV-SHADOW-1:
  statement: "Shadow never touches real capital"
  test: test_shadow_isolation.py
```

### S30 EXIT GATES

```yaml
GATE_S30_1:
  name: HUNT_WORKS
  criterion: Hypothesis → variations → survivors → bead
  test: test_e2e_hunt.py
  evidence: Hunt completes in <5 min, survivors ranked

GATE_S30_2:
  name: ATHENA_QUERYABLE
  criterion: Natural language → relevant bead results
  test: test_athena_query.py
  evidence: "What did I learn about X" returns relevant beads

GATE_S30_3:
  name: CHECKPOINT_SEAMLESS
  criterion: Checkpoint + fresh instance + momentum preserved
  test: test_checkpoint_e2e.py
  evidence: Fresh Claude continues with correct stance

GATE_S30_4:
  name: SHADOW_TRACKING
  criterion: Shadow boxer tracks signals without capital risk
  test: test_shadow_tracking.py
  evidence: Paper P&L calculated, divergence detectable

GATE_S30_5:
  name: FLYWHEEL_FEELS_ALIVE
  criterion: Olya confirms "learning is accumulating"
  test: Manual session
  evidence: Verbal/written confirmation

BINARY_EXIT:
  statement: "Hypothesis → test → learn → surface working"
```

### S30 OPEN QUESTIONS

```yaml
Q_S30_1:
  topic: Hunt variation generation
  question: How does Hunt generate variations from natural language?
  options:
    A: Rule-based parsing (explicit patterns)
    B: Local LLM interprets hypothesis → parameters
    C: Template library (common variation types)
  recommendation: B with C fallback (LLM + templates)

Q_S30_2:
  topic: Athena semantic search
  question: How does "What did I learn about X" find relevant beads?
  options:
    A: Keyword matching only
    B: Embedding similarity (FAISS)
    C: LLM summarizes bead content, matches query
  recommendation: A for v1, B for v2 (complexity gated)

Q_S30_3:
  topic: Shadow divergence threshold
  question: When does shadow divergence become alertable?
  options:
    A: Any divergence logged, no alerts
    B: Threshold-based (e.g., >20% P&L difference)
    C: Pattern-based (consistent divergence direction)
  recommendation: A for S30 (observability), B for S31 (actionable)
```

### S30 HANDOFF TO S31

```yaml
S31_RECEIVES:
  hunt_engine:
    - Hypothesis parsing
    - Variation generation
    - Backtest integration with River
    - Survivor filtering

  athena:
    - Bead storage + indexing
    - Query interface
    - Natural language → results

  checkpoint:
    - Atomic transition
    - Cognitive momentum schema
    - Hot-load from snapshots

  shadow:
    - Paper position tracking
    - Signal comparison framework
    - Divergence calculation
```

---

## S31: SIGNAL_AND_DECAY

**Theme:** "Phoenix watches"  
**Duration:** 1-2 weeks  
**Detail Level:** LIGHT  
**Exit Gate:** Phoenix detects setups AND warns before decay proves itself

### S31 DELIVERS

```yaml
CSO_CAPABILITY:
  what: Chief Strategy Officer — continuous setup detection
  scans: 6 pairs (multi-pair ARCHITECTURE)
  outputs:
    - Setup quality scores (NONE/FORMING/READY)
    - Reasoning breakdown (decomposable)
    - Evidence bundles for T2
  integration:
    - Morning briefing shows all 6 pairs
    - Telegram push when >0.8 confidence
    - DISPATCH:SCAN for on-demand check

SIGNALMAN_CAPABILITY:
  what: Drift and decay detection
  monitors:
    - Strategy Sharpe drift
    - Input distribution shift
    - Win rate degradation
  actions:
    - ONE-WAY-KILL on threshold breach
    - Alert before P&L proves decay
  integration:
    - Morning briefing includes decay status
    - Telegram alert on detection

AUTOPSY_CAPABILITY:
  what: Post-trade analysis
  runs: Async after position close
  compares:
    - Entry thesis vs outcome
    - Reasoning at decision time vs what happened
  outputs:
    - AUTOPSY bead
    - Learning extraction
  integration:
    - Queryable via Athena
    - Patterns surfaced in briefing

STATE_HASH_VALIDATION:
  what: Stale context execution guard
  mechanism: Per S29 design (state_hash in intent)
  enforcement: Inquisitor rejects STATE_CONFLICT
  staleness: >30 min sessions require refresh for T2

TELEGRAM_PLANE:
  what: Notification surface (not thinking partner)
  alerts:
    - Setup ready (>0.8)
    - Decay detected
    - Position filled/closed
    - Daemon health
  actions:
    - Approval buttons (T2)
    - HALT button
    - Link to Claude Desktop
```

### S31 KEY COMPONENTS

```yaml
COMPONENTS:
  phoenix/cso/scanner.py:
    - Continuous pair scanning
    - ICT methodology rules (from Olya calibration)
    - Quality scoring

  phoenix/cso/evaluator.py:
    - Evidence bundle assembly
    - Reasoning decomposition
    - Red check validation

  phoenix/monitoring/signalman.py:
    - Drift detection algorithms
    - Threshold management
    - ONE-WAY-KILL trigger

  phoenix/lab/autopsy.py:
    - Trade reconstruction
    - Thesis vs outcome comparison
    - Learning extraction

  phoenix/notifications/telegram.py:
    - Takopi integration (existing)
    - Alert formatting
    - Button handlers
```

### S31 DEPENDENCIES

```yaml
REQUIRES_FROM_S30:
  - Hunt engine (CSO uses similar pattern for scanning)
  - Athena (Autopsy writes beads, patterns queryable)
  - River data flowing (6 pairs)

REQUIRES_FROM_S29:
  - File seam (CSO alerts via DISPATCH)
  - Session management (state hash)
  - Telegram bridge (Takopi exists in God_Mode)
```

### S31 EXIT GATES

```yaml
GATE_S31_1:
  name: CSO_SCANS_6_PAIRS
  criterion: Morning briefing shows setup status for all 6 pairs
  evidence: Briefing includes EUR/USD, GBP/USD, etc. with scores

GATE_S31_2:
  name: SIGNALMAN_DETECTS
  criterion: Induced decay → alert before P&L proves it
  evidence: Inject drift → alert fires → ONE-WAY-KILL activates

GATE_S31_3:
  name: AUTOPSY_RUNS
  criterion: Position closes → autopsy bead appears
  evidence: Query Athena for autopsy, reasoning comparison present

GATE_S31_4:
  name: TELEGRAM_ALERTS
  criterion: Setup ready → phone buzzes with correct content
  evidence: Manual test with Olya's device

GATE_S31_5:
  name: STATE_HASH_GUARDS
  criterion: Stale intent → STATE_CONFLICT rejection
  evidence: 2-hour-old session → T2 attempt → rejected with refresh prompt

BINARY_EXIT:
  statement: "Phoenix detects setups AND warns before decay proves itself"
```

### S31 OPEN QUESTIONS

```yaml
Q_S31_1:
  topic: CSO calibration source
  question: Where do ICT methodology rules come from?
  options:
    A: Hardcoded from documentation
    B: Extracted from Olya's trading journal
    C: Parallel calibration track with Olya's Claude
  recommendation: A for launch, C as parallel workstream
  note: "Olya's pace, not ours" — don't block S31 on calibration

Q_S31_2:
  topic: Signalman thresholds
  question: What drift % triggers ONE-WAY-KILL?
  options:
    A: Fixed (e.g., 15% Sharpe decline)
    B: Adaptive (based on historical volatility)
    C: Configurable per strategy
  recommendation: A for launch, C for tuning

Q_S31_3:
  topic: Telegram approval security
  question: How do we prevent unauthorized T2 approval via Telegram?
  options:
    A: Telegram is notification only, approval in Claude Desktop
    B: Confirmation code required (shown in Claude, entered in Telegram)
    C: Biometric on Telegram app
  recommendation: A (simplest, most secure)
```

---

## S32: EXECUTION_PATH

**Theme:** "Real markets"  
**Duration:** 2-3 weeks  
**Detail Level:** SKETCH  
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

T2_APPROVAL_WORKFLOW:
  what: Human sovereignty gate for capital decisions
  flow:
    1. CSO presents evidence bundle
    2. State hash validated (fresh context)
    3. Human reviews reasoning
    4. Explicit approval (APPROVE button)
    5. Approval token generated
    6. Order submitted with token
  evidence_displayed:
    - Setup quality score + breakdown
    - HTF/LTF alignment
    - Risk parameters (stop, target, size)
    - Red check results
    - State hash confirmation

POSITION_LIFECYCLE:
  what: State machine for position management
  states:
    PROPOSED → APPROVED → SUBMITTED → FILLED → MANAGED → CLOSED
  tracking:
    - Entry thesis (frozen at approval)
    - Fill details
    - P&L (real-time)
    - Exit reason
  beads: POSITION bead at each state transition

STAGING_ENFORCEMENT:
  what: Shadow period before live
  rule: INV-STAGE-BEFORE-LIVE
  mechanism:
    - New strategy must shadow for N days
    - Shadow P&L tracked
    - Promotion requires human ceremony
```

### S32 KEY RISKS

```yaml
RISK_1_IBKR_API:
  description: IBKR API is complex, rate-limited, sometimes unreliable
  mitigation:
    - Mock client for all testing
    - Retry logic with backoff
    - Position reconciliation (detect drift)
    - Manual override always available

RISK_2_ORDER_STATE:
  description: Order state can desync (Phoenix thinks filled, IBKR doesn't)
  mitigation:
    - Reconciliation worker (periodic)
    - Heartbeat to IBKR
    - Alert on mismatch

RISK_3_APPROVAL_FATIGUE:
  description: Too many T2 gates → Olya bypasses mentally
  mitigation:
    - Evidence bundle must be glanceable
    - Clear APPROVE / PASS options
    - No false urgency
```

### S32 EXIT GATES

```yaml
GATE_S32_1:
  name: IBKR_CONNECTED
  criterion: Can query account, submit paper order, receive fill
  evidence: Paper trade completes round-trip

GATE_S32_2:
  name: T2_WORKFLOW_COMPLETE
  criterion: Evidence → Review → Approve → Order → Fill
  evidence: Full workflow on paper account

GATE_S32_3:
  name: POSITION_LIFECYCLE_TRACKED
  criterion: Position state machine transitions correctly
  evidence: POSITION beads at each state

GATE_S32_4:
  name: RECONCILIATION_WORKS
  criterion: Induced mismatch → detected → alerted
  evidence: Fake IBKR state → reconciler catches

BINARY_EXIT:
  statement: "T2 workflow proven on paper, IBKR connected"
```

---

## S33: FIRST_BLOOD

**Theme:** "One pair, real money"  
**Duration:** 2+ weeks (validation period)  
**Detail Level:** SKETCH  
**Exit Gate:** 6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents

### S33 PROVES

```yaml
CAPABILITY_COMPLETE:
  architecture: Multi-pair (6 pairs scan, detect, execute)
  active_trading: EUR/USD with real capital
  superpowers: ALL operational
    - Thinking partner (EXPLORE) ✓
    - Morning briefing ✓
    - Hunt (test my idea) ✓
    - Athena (memory palace) ✓
    - CSO (what's setting up) ✓
    - Signalman (decay detection) ✓
    - Autopsy (post-trade analysis) ✓
    - T2 approval workflow ✓
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
  evidence: Incident log empty (or all resolved)
  value_of_N: TBD (suggest 5-10 trading days)

GATE_S33_4:
  name: OLYA_TRUSTS_IT
  criterion: Olya comfortable with system managing her trades
  evidence: Verbal confirmation, continued use

GATE_S33_5:
  name: RUNBOOKS_TESTED
  criterion: At least one incident drill completed
  evidence: Drill log with resolution time

BINARY_EXIT:
  statement: "6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents"
```

### S33 SUCCESS CRITERIA

```yaml
A_DAY_IN_OLYAS_LIFE_WORKS:
  6am: Morning briefing (6 pairs shown) ✓
  6:30am: EXPLORE thinking session ✓
  7:30am: Hunt tests hypothesis ✓
  8:30am: Setup alert (Telegram) ✓
  9am: T2 approval (real capital) ✓
  3pm: Position managed/closed ✓
  5pm: Athena query ("what did I learn") ✓
  overnight: Phoenix watches ✓

SYSTEM_HEALTH:
  halt_latency: <50ms (proven)
  daemon_uptime: >99%
  alert_latency: <60s
  reconciliation: No drift detected
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
    4. Olya approves live
    5. Config update (pair → ACTIVE)
    6. Monitoring period

EXPANSION_ORDER:
  suggested:
    - Pair 2: GBP/USD (similar to EUR/USD)
    - Pair 3-4: Other majors
    - Pair 5-6: As trust builds
  actual: Olya decides based on her methodology

NOT_S34:
  - Code changes (architecture is done)
  - New capabilities (superpowers complete)
  - Rush (trust-gated, not time-gated)
```

---

## POST-S34: HARDEN_AND_TRUST

**Theme:** "Earn it through use"  
**Detail Level:** DIRECTIONAL

### POST-S34 ACTIVITIES

```yaml
REAL_WORLD_HARDENING:
  - Edge cases surface from live trading
  - Signalman thresholds tuned from real data
  - CSO calibration refined (Olya's feedback)
  - Regime-specific learnings accumulated

TRUST_BUILDING:
  - Consistent performance
  - No surprises
  - Graceful handling of market stress
  - Olya's confidence grows

CALIBRATION_TRACK:
  - Olya's Claude (CSO) captures her methodology
  - Intertwine Protocol verifies comprehension
  - Tacit knowledge → machine-readable invariants
  - Runs PARALLEL (her pace, not ours)

FUTURE_HORIZONS:
  when_earned:
    - Echo domain (crypto via Hyperliquid)
    - Foundry-as-a-Service (external clients)
  trigger: "S34 stable, Olya confident, system battle-tested"
```

---

## CROSS-SPRINT INVARIANTS

```yaml
SOVEREIGNTY:
  INV-SOVEREIGN-1: "Human sovereignty over capital is absolute"
  INV-SOVEREIGN-2: "T2 requires human gate"
  applies: All sprints, especially S32-S33

HALT:
  INV-HALT-1: "halt_local < 50ms"
  INV-HALT-2: "halt_cascade < 500ms"
  applies: All sprints

DATA:
  INV-DATA-CANON: "Single truth from River"
  applies: S30 Hunt, S31 CSO, S32 execution

COGNITIVE:
  INV-EXPLORE-3: "/acting/ triggers machinery; /explore/ does not"
  INV-EXPLORE-4: "EXPLORE has no external system access"
  INV-CONTEXT-1: "Claude holds conversation only"
  applies: All sprints

RISK:
  INV-EVIDENCE-1: "No entry without evidence bundle"
  INV-RISK-DEFENSIVE: "ONE-WAY-KILL on decay/drawdown"
  INV-STAGE-BEFORE-LIVE: "Shadow period before live"
  INV-EXPOSURE-LIMIT: "2.5% max per currency"
  applies: S31-S33
```

---

## ADVISOR POLLING REQUEST

```yaml
TO_GPT:
  role: Architect Lint
  focus:
    - S30 seam contracts (Hunt, Athena)
    - Q_S30_1/2/3 analysis
    - Edge cases in checkpoint atomicity
    - Shadow → live promotion gaps

TO_GROK:
  role: Frontier Patterns
  focus:
    - Hunt variation generation (YOLO opportunities)
    - Signalman decay detection patterns
    - Chaos vectors for S30-S31
    - What's the dumbest failure in this roadmap?

TO_OWL:
  role: Wise Owl
  focus:
    - Structural coherence across S30-S33
    - Dependency chain integrity
    - CSO calibration as parallel track
    - T2 approval workflow security

TO_OPUS:
  role: Builder
  focus:
    - Implementation readiness of S30
    - What's underspecified for building?
    - Effort estimates per sprint
    - Risk assessment (what's hardest?)
```

---

## SUMMARY

| Sprint | Theme | Exit Gate | Detail |
|--------|-------|-----------|--------|
| S29 | Cognitive Foundation | EXPLORE + Briefing | ✓ LOCKED |
| S30 | Learning Loop | Hunt + Athena + Checkpoint | MEDIUM |
| S31 | Signal & Decay | CSO + Signalman + Telegram | LIGHT |
| S32 | Execution Path | IBKR + T2 + Positions | SKETCH |
| S33 | First Blood | 6-pair capable, EUR/USD live | SKETCH |
| S34 | Expand Pairs | Add pairs (config, not code) | DIRECTIONAL |
| Post | Harden & Trust | Real-world proving | DIRECTIONAL |

**PRODUCTION GATE (S33):**
- ALL superpowers operational
- 6-pair CAPABLE (architecture)
- EUR/USD ACTIVE (governance)
- N days no critical incidents
