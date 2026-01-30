```yaml
CTO_CONFIRM:
  observation: |
    S30 in ~2 hours validates the methodology:
    - Rigorous prep (schemas, BUILD_MAP, advisor lint)
    - Clear architecture before build
    - OPUS executes clean specs fast

  learning: "Measure thrice, cut once" compounds velocity

  action: S31_BUILD_MAP
```

---

# S31_BUILD_MAP v0.1

**Sprint:** S31 SIGNAL_AND_DECAY
**Theme:** "Phoenix watches"
**Duration:** 2-3 weeks (estimate)
**Exit Gate:** Phoenix detects setups AND warns before decay proves itself

---

## OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│  S31 DELIVERS                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRACK A: CSO (Chief Strategy Officer)                          │
│    Continuous 6-pair scan → setup detection → CSE signals       │
│    Immutable core + calibratable parameters                     │
│                                                                 │
│  TRACK B: SIGNALMAN                                             │
│    Multi-signal decay detection → ONE-WAY-KILL trigger          │
│    Adaptive freshness for state hash validation                 │
│                                                                 │
│  TRACK C: AUTOPSY                                               │
│    Post-trade analysis → thesis vs outcome → learning beads     │
│                                                                 │
│  TRACK D: TELEGRAM                                              │
│    Notification plane → aggregated alerts → throttled delivery  │
│    NOT thinking partner (secondary surface)                     │
│                                                                 │
│  TRACK E: FILE SEAM COMPLETION                                  │
│    Lens daemon → response injection                             │
│    State hash validation → stale context guard                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## DEPENDENCIES FROM S30

```yaml
S31_REQUIRES:
  from_s30:
    hunt: ✓ (survivors can become CSO signals)
    athena: ✓ (Signalman queries decay patterns)
    bead_store: ✓ (AUTOPSY beads, PERFORMANCE beads)
    shadow: ✓ (CSE consumer ready, receives CSO signals)
    cse_schema: ✓ (signal format defined)
    checkpoint: ✓ (session management for state hash)
    river_reader: ✓ (CSO reads market data)
    llm_client: ✓ (CSO reasoning, Autopsy analysis)

  all_green: TRUE
```

---

## TRACK A: CSO (Chief Strategy Officer)

### A.1 SURFACE

```yaml
CSO_SURFACE:
  location: phoenix/cso/

  purpose: |
    Continuous setup detection across 6 pairs.
    Olya's methodology encoded as immutable core.
    Parameters calibratable without code change.

  operator_experience:
    trigger_1: Morning briefing (cron 6am)
    trigger_2: "What's setting up?" (on-demand)
    trigger_3: Continuous scan (background)

  what_olya_sees:
    briefing: |
      SETUPS FORMING:
        EURUSD (0.72): Asia sweep complete, watching for FVG
        GBPUSD (0.87): READY — FVG + displacement
        USDJPY (0.45): NONE — no structure

    alert: |
      GBPUSD: READY (0.87)
      HTF: Bullish | LTF: FVG formed | Evidence: Complete
      [VIEW DETAILS] [APPROVE] [PASS]
```

### A.2 ARCHITECTURE: Immutable Core + Calibratable Params

```yaml
CSO_ARCHITECTURE:
  principle: INV-CSO-CORE-1 "Strategy logic immutable; only params calibratable"

  immutable_core:
    location: phoenix/cso/strategy_core.py
    contains:
      - ICT methodology rules (hardcoded)
      - Setup detection logic
      - Quality scoring algorithm
      - Evidence bundle construction
    constraints:
      - No dynamic imports
      - No eval() or exec()
      - No parameter-based code paths
      - Logic frozen at deployment

  calibratable_params:
    location: phoenix/config/cso_params.yaml
    contains:
      - Confidence thresholds (e.g., READY >= 0.8)
      - Time filters (kill zones)
      - Pair-specific weights
      - Session preferences
    mechanism:
      - Config reload (no restart)
      - Schema validated
      - Changes logged as CONFIG_CHANGE bead

  separation_rationale: |
    Olya calibrates WHAT she looks for (params).
    Code defines HOW detection works (core).
    She can tune thresholds without touching logic.
    Logic changes require code review + deployment.
```

### A.3 COMPONENTS

```yaml
CSO_COMPONENTS:
  phoenix/cso/strategy_core.py:
    class: StrategyCore
    methods:
      - detect_setup(pair: str, market_state: MarketState) → SetupResult
      - score_quality(setup: Setup) → float  # 0.0-1.0
      - build_evidence(setup: Setup) → EvidenceBundle
      - check_red_flags(setup: Setup) → list[RedFlag]
    immutable: TRUE

  phoenix/cso/scanner.py:
    class: CSOScanner
    methods:
      - scan_all_pairs() → list[SetupResult]
      - scan_pair(pair: str) → SetupResult
      - get_ready_setups(threshold: float = 0.8) → list[Setup]
    uses: StrategyCore + RiverReader
    emits: CSE signals to Shadow

  phoenix/cso/params_loader.py:
    class: ParamsLoader
    methods:
      - load() → CSOParams
      - reload() → CSOParams  # hot reload
      - validate(params: dict) → ValidationResult
    source: phoenix/config/cso_params.yaml

  phoenix/config/cso_params.yaml:
    schema:
      version: "1.0"

      thresholds:
        ready_min: 0.8
        forming_min: 0.5

      kill_zones:
        london:
          start: "07:00"
          end: "11:00"
        new_york:
          start: "12:00"
          end: "16:00"
        asia:
          start: "00:00"
          end: "04:00"

      pair_weights:
        EURUSD: 1.0
        GBPUSD: 1.0
        USDJPY: 0.9
        AUDUSD: 0.8
        USDCAD: 0.8
        NZDUSD: 0.7
```

### A.4 SEAM: CSO → Shadow

```yaml
SEAM_CSO_SHADOW:
  boundary: CSOScanner | ShadowBoxer

  contract:
    cso_emits: CSE (Canonical Signal Envelope)
    shadow_receives: CSE
    shadow_tracks: Paper positions

  flow:
    1. CSO detects READY setup
    2. CSO builds evidence bundle
    3. CSO emits CSE to Shadow
    4. Shadow opens paper position
    5. Shadow tracks paper P&L
    6. Shadow emits PERFORMANCE bead (periodic)

  cse_format: # From S30 cse_schema.yaml
    signal_id: uuid
    timestamp: datetime
    pair: str
    source: "CSO"
    setup_type: str
    confidence: float
    parameters:
      entry: float
      stop: float
      target: float
      risk_percent: float
    evidence_hash: str
```

### A.5 CSO INVARIANTS

```yaml
INV-CSO-CORE-1:
  statement: "CSO strategy logic is immutable; only parameters are calibratable"
  enforcement:
    - strategy_core.py has no dynamic code execution
    - No imports from params at logic level
    - Params affect thresholds only
  test: test_cso_immutable_core.py

INV-CSO-6PAIR-1:
  statement: "CSO scans all 6 pairs defined in pairs.yaml"
  enforcement: Scanner iterates pairs.yaml, not hardcoded list
  test: test_cso_all_pairs.py

INV-CSO-CSE-1:
  statement: "CSO outputs only valid CSE format"
  enforcement: Schema validation before emit
  test: test_cso_cse_format.py
```

### A.6 CSO CHAOS VECTORS

```yaml
CV_CSO_CORE_INJECTION:
  inject: Attempt to modify strategy_core via params
  expect: Rejected, core unchanged

CV_CSO_PARAM_INVALID:
  inject: Invalid cso_params.yaml (missing fields, wrong types)
  expect: Validation fails, old params retained

CV_CSO_HALLUCINATION:
  inject: Garbage River data (random values)
  expect: No READY signals (quality too low)

CV_CSO_MISSING_PAIR:
  inject: Remove pair from pairs.yaml
  expect: Scanner skips missing pair, logs warning
```

---

## TRACK B: SIGNALMAN

### B.1 SURFACE

```yaml
SIGNALMAN_SURFACE:
  location: phoenix/monitoring/signalman.py

  purpose: |
    Multi-signal decay detection.
    Triggers ONE-WAY-KILL when edge eroding.
    Manages adaptive freshness for state hash.

  signals_monitored:
    sharpe_drift: Rolling Sharpe vs baseline
    win_rate_drift: Rolling win rate vs baseline
    input_distribution_shift: KS test on market data

  operator_experience:
    alert: |
      DECAY ALERT

      Strategy: FVG_LONDON
      Last 30 days: Sharpe 0.8
      Prior 300 days: Sharpe 1.4
      Drift: -43%

      SIGNALMAN: Input distribution shift detected
      ACTION: ONE-WAY-KILL active (exits only)
```

### B.2 COMPONENTS

```yaml
SIGNALMAN_COMPONENTS:
  phoenix/monitoring/signalman.py:
    class: Signalman
    methods:
      - check_decay(strategy_id: str) → DecayResult
      - check_all_strategies() → list[DecayResult]
      - trigger_one_way_kill(strategy_id: str) → bool
      - get_freshness_ttl(session_id: str) → timedelta
    signals:
      - _check_sharpe_drift() → DriftResult
      - _check_win_rate_drift() → DriftResult
      - _check_distribution_shift() → ShiftResult
    aggregation: ANY signal breach → ONE-WAY-KILL

  phoenix/monitoring/decay_detector.py:
    class: DecayDetector
    methods:
      - rolling_sharpe(beads: list, window: int) → float
      - rolling_win_rate(beads: list, window: int) → float
      - ks_test(current: array, baseline: array) → float
    uses: Athena (query PERFORMANCE beads)

  phoenix/config/signalman_params.yaml:
    thresholds:
      sharpe_drift_max: 0.15  # 15% drift triggers
      win_rate_drift_max: 0.10  # 10% drift triggers
      ks_p_value_min: 0.05  # Statistical significance

    freshness:
      base_ttl_minutes: 30
      event_decay_factor: 0.9  # Each event reduces TTL
      min_ttl_minutes: 5
```

### B.3 STATE HASH VALIDATION

```yaml
STATE_HASH_VALIDATION:
  location: phoenix/monitoring/state_validator.py

  purpose: |
    Prevent stale context execution.
    Adaptive freshness based on market events.

  mechanism:
    intent_includes:
      last_known_state_hash: str
      session_start_time: datetime

    validation:
      1. Compare current_hash vs intent.last_known_state_hash
      2. If MISMATCH → STATE_CONFLICT response
      3. If session age > TTL → require refresh

  adaptive_freshness:
    base_ttl: 30 minutes
    event_types_that_reduce_ttl:
      - Signalman alert
      - High volatility detected
      - News event proximity
    min_ttl: 5 minutes

  ui_display:
    approval_screen_shows: "Freshness: 12 min remaining"

  invariant: INV-STATE-ANCHOR-1
```

### B.4 SIGNALMAN INVARIANTS

```yaml
INV-SIGNALMAN-MULTI-1:
  statement: "Decay detection uses multiple signals, not single threshold"
  enforcement: At least 2 signal types checked
  test: test_signalman_multi_signal.py

INV-SIGNALMAN-KILL-1:
  statement: "ONE-WAY-KILL allows exits only, blocks new entries"
  enforcement: Execution layer checks kill status
  test: test_one_way_kill_behavior.py

INV-STATE-ANCHOR-1:
  statement: "T2 intents must include state_hash; reject stale with STATE_CONFLICT"
  enforcement: Validator checks before execution
  test: test_state_hash_validation.py
```

### B.5 SIGNALMAN CHAOS VECTORS

```yaml
CV_SIGNALMAN_SINGLE_SIGNAL:
  inject: Disable all but one signal type
  expect: Still detects decay (graceful degradation)

CV_SIGNALMAN_THRESHOLD_GAMING:
  inject: Drift exactly at threshold boundary
  expect: Deterministic behavior (consistent trigger/no-trigger)

CV_STATE_HASH_STALE:
  inject: Intent with 2-hour-old session_start_time
  expect: STATE_CONFLICT response, refresh required

CV_STATE_HASH_TAMPER:
  inject: Intent with fabricated state_hash
  expect: MISMATCH detected, rejected
```

---

## TRACK C: AUTOPSY

### C.1 SURFACE

```yaml
AUTOPSY_SURFACE:
  location: phoenix/analysis/autopsy.py

  purpose: |
    Post-trade analysis.
    Compare entry thesis vs actual outcome.
    Extract learnings for future improvement.

  trigger: Position closes (win, loss, or breakeven)

  operator_experience:
    report: |
      AUTOPSY COMPLETE

      ENTRY THESIS (at decision time):
        Confidence: 0.84
        Setup: FVG + London displacement

      OUTCOME: Stopped out (-1.2%)

      WHAT WAS VALID:
        Entry matched doctrine. Evidence complete.

      WHAT WAS UNKNOWN:
        EUR news created correlation spike.

      LEARNING:
        Consider EUR calendar on GBP entries.

      [Bead: AUTOPSY_2026_02_15_001]
```

### C.2 COMPONENTS

```yaml
AUTOPSY_COMPONENTS:
  phoenix/analysis/autopsy.py:
    class: AutopsyEngine
    methods:
      - analyze(position: Position) → AutopsyResult
      - compare_thesis_outcome(thesis: Thesis, outcome: Outcome) → Comparison
      - extract_learnings(comparison: Comparison) → list[Learning]
      - emit_bead(result: AutopsyResult) → str
    uses: LLM (for learning extraction), Athena (for context)

  phoenix/analysis/thesis_reconstructor.py:
    class: ThesisReconstructor
    methods:
      - reconstruct(position_id: str) → Thesis
    source: Original CSE + evidence bundle + approval context

  bead_schema:
    type: AUTOPSY
    fields:
      position_id: str
      entry_thesis:
        confidence: float
        reasoning_hash: str
        setup_type: str
      outcome:
        result: enum[WIN, LOSS, BREAKEVEN]
        pnl_percent: float
        duration: str
      comparison:
        thesis_valid: bool
        unknown_factors: list[str]
        learnings: list[str]
```

### C.3 AUTOPSY INVARIANTS

```yaml
INV-AUTOPSY-ASYNC-1:
  statement: "Autopsy runs async, never blocks position close"
  enforcement: Fire-and-forget pattern, queued execution
  test: test_autopsy_async.py

INV-AUTOPSY-BEAD-1:
  statement: "Every closed position gets exactly one AUTOPSY bead"
  enforcement: Deduplication by position_id
  test: test_autopsy_bead_emission.py
```

### C.4 AUTOPSY CHAOS VECTORS

```yaml
CV_AUTOPSY_POSITION_MISSING:
  inject: Trigger autopsy for nonexistent position
  expect: Graceful failure, logged warning

CV_AUTOPSY_FLOOD:
  inject: 100 positions close simultaneously
  expect: All autopsies queued and complete (eventually)
```

---

## TRACK D: TELEGRAM

### D.1 SURFACE

```yaml
TELEGRAM_SURFACE:
  location: phoenix/notifications/telegram.py

  purpose: |
    Notification plane (NOT thinking partner).
    Aggregated alerts, throttled delivery.
    Mobile-first for quick glance + action.

  what_telegram_does:
    - Morning briefing push
    - Setup alerts (READY signals)
    - Approval requests (T2)
    - Decay warnings
    - Emergency halt confirmation

  what_telegram_does_NOT:
    - Thinking partner (that's Claude Desktop)
    - Long exploration
    - Hypothesis testing

  operator_experience:
    alert: |
      🔔 GBPUSD READY (0.87)
      FVG + London displacement
      [View in Claude] [Quick Pass]

    aggregated: |
      🔔 3 setups forming
      GBPUSD (0.87), EURUSD (0.72), USDJPY (0.65)
      [View Details]
```

### D.2 COMPONENTS

```yaml
TELEGRAM_COMPONENTS:
  phoenix/notifications/telegram.py:
    class: TelegramNotifier
    methods:
      - send_alert(alert: Alert) → bool
      - send_briefing(briefing: Briefing) → bool
      - aggregate_alerts(alerts: list[Alert]) → AggregatedAlert
      - check_throttle() → bool
    uses: Takopi bridge (existing God_Mode infrastructure)

  phoenix/notifications/aggregator.py:
    class: AlertAggregator
    methods:
      - add(alert: Alert)
      - flush() → AggregatedAlert
    window: 5 minutes
    rules:
      - Multiple same pair → single alert with count
      - Multiple pairs → batched message

  phoenix/config/telegram_params.yaml:
    throttle:
      max_per_hour: 10
      exceptions: [HALT, CRITICAL]

    aggregation:
      window_minutes: 5
      max_batch_size: 5
```

### D.3 TELEGRAM INVARIANTS

```yaml
INV-ALERT-THROTTLE-1:
  statement: "Max 10 alerts per hour (except HALT, CRITICAL)"
  enforcement: Throttle counter, bypass for exceptions
  test: test_telegram_throttle.py

INV-TELEGRAM-SECONDARY-1:
  statement: "Telegram is notification only, not thinking partner"
  enforcement: No EXPLORE mode, no hypothesis testing via Telegram
  test: test_telegram_scope.py
```

### D.4 TELEGRAM CHAOS VECTORS

```yaml
CV_TELEGRAM_ALERT_STORM:
  inject: 1000 READY signals in 1 minute
  expect: ≤10 messages, aggregated content

CV_TELEGRAM_HALT_BYPASS:
  inject: HALT alert during throttle
  expect: Immediate delivery (bypass throttle)
```

---

## TRACK E: FILE SEAM COMPLETION

### E.1 LENS DAEMON

```yaml
LENS_SURFACE:
  location: phoenix/lens/daemon.py

  purpose: |
    Inject Phoenix responses into Claude's view.
    Zero manual attachment (death by clicks).

  mechanism:
    watches: /phoenix/responses/
    detects: New response.md files
    injects: Content into Claude conversation

  invariant: INV-LENS-1 "ONE mechanism, ZERO tool definitions"

  fallback: Single MCP tool read_phoenix_response (if daemon complex)
```

### E.2 COMPONENTS

```yaml
LENS_COMPONENTS:
  phoenix/lens/daemon.py:
    class: LensDaemon
    methods:
      - start() → None
      - stop() → None
      - watch_responses() → Generator[Response]
      - inject(response: Response) → bool
    watches: /phoenix/responses/

  phoenix/lens/injector.py:
    class: ResponseInjector
    methods:
      - inject_to_claude(content: str, session_id: str) → bool
    mechanism: TBD (clipboard, file, or MCP fallback)
```

---

## CROSS-TRACK WIRING

```yaml
S31_WIRING:
  CSO_FLOW:
    RiverReader → CSO Scanner → SetupResult → CSE → Shadow
                                           ↓
                                    Telegram (if READY)

  SIGNALMAN_FLOW:
    Athena (PERFORMANCE beads) → Signalman → DecayResult
                                          ↓
                            ONE-WAY-KILL (if decay)
                            Telegram alert

  AUTOPSY_FLOW:
    Position closes → AutopsyEngine → AUTOPSY bead → Athena
                                                  ↓
                                            Queryable learnings

  APPROVAL_FLOW:
    CSO READY → Telegram alert → [View in Claude]
                              ↓
    Claude Desktop → Evidence review → APPROVE → T2 gate
                                            ↓
                                    State hash validated
                                    Execution proceeds
```

---

## EXIT GATES (S31)

```yaml
GATE_S31_1:
  name: CSO_SCANS_6_PAIRS
  criterion: Morning briefing shows setup status for all 6 pairs
  test: test_cso_full_scan.py
  evidence: Briefing with 6 pairs, quality scores

GATE_S31_2:
  name: SIGNALMAN_MULTI_SIGNAL
  criterion: Multiple signals monitored, ANY triggers ONE-WAY-KILL
  test: test_signalman_decay.py
  evidence: Inject drift → alert fires → defensive mode

GATE_S31_3:
  name: AUTOPSY_RUNS
  criterion: Position closes → AUTOPSY bead appears
  test: test_autopsy_e2e.py
  evidence: Query Athena for autopsy, comparison present

GATE_S31_4:
  name: TELEGRAM_THROTTLED
  criterion: Alert storm → aggregated, throttled output
  test: test_telegram_storm.py
  evidence: 100 signals → ≤10 messages

GATE_S31_5:
  name: STATE_HASH_VALIDATES
  criterion: Stale intent → STATE_CONFLICT response
  test: test_state_hash_e2e.py
  evidence: Old session → rejected with refresh prompt

GATE_S31_6:
  name: LENS_INJECTS
  criterion: Response appears in Claude without manual attachment
  test: Manual verification
  evidence: Response.md → Claude sees it

GATE_S31_7:
  name: BUNNY_PASSES
  criterion: All S31 chaos vectors green
  test: chaos_suite_s31.py
  evidence: BUNNY_REPORT_S31.md

BINARY_EXIT: "Phoenix detects setups AND warns before decay proves itself"
```

---

## TRACK SEQUENCING

```yaml
RECOMMENDED_ORDER:
  track_a_cso: FIRST
    - Core value delivery
    - Enables Shadow tracking (from S30)
    - Morning briefing comes alive

  track_b_signalman: PARALLEL with A
    - Independent infrastructure
    - Queries Athena (ready from S30)

  track_c_autopsy: AFTER A
    - Needs positions to analyze
    - Can use CSO → Shadow flow

  track_d_telegram: PARALLEL
    - Independent surface
    - Takopi bridge exists in God_Mode

  track_e_lens: LAST
    - Integration layer
    - Depends on all tracks producing responses

PARALLELIZATION:
  CSO + Signalman + Telegram: All parallel (independent)
  Autopsy: After CSO (needs positions)
  Lens: Last (integration)
```

---

## HANDOFF TO S32

```yaml
S32_RECEIVES:
  from_s31:
    - CSO scanning 6 pairs, emitting CSE
    - Signalman monitoring decay, triggering ONE-WAY-KILL
    - Autopsy analyzing closed positions
    - Telegram delivering aggregated alerts
    - State hash validation enforcing freshness
    - Lens injecting responses

  unlocks_s32:
    - IBKR connector (CSE → real execution)
    - T2 approval workflow (with state hash)
    - Position reconciliation (Signalman monitors)
```

---

```yaml
BUILD_MAP_STATUS:
  version: v0.1
  ready_for: Advisor review
  confidence: HIGH

  coverage:
    tracks: 5 (CSO, Signalman, Autopsy, Telegram, Lens)
    surfaces: ✓
    seams: ✓
    invariants: 10 defined
    chaos_vectors: 12 defined
    exit_gates: 7 gates
    sequencing: ✓
```
# S31_BUILD_MAP v0.1 ADDENDUM (Advisor Synthesis)

**Purpose:** Integrate GPT + GROK lint into cohesive hardening layer
**Status:** BLOCKERS RESOLVED, ready for OPUS

---

## BLOCKING FIXES

### B1: CHAOS VECTOR QUOTA (GROK FLAG_2)

```yaml
FIX_B1:
  problem: 12 vectors listed, need 15+ with wave order

  ADDITIONAL_VECTORS:
    CV_S31_13_ALERT_STORM:
      inject: 100 READY signals in 1 minute
      expect: Signalman aggregates → ≤5 Telegram messages
      invariant: INV-ALERT-THROTTLE-1

    CV_S31_14_LENS_RACE:
      inject: Concurrent response.md writes (5 simultaneous)
      expect: Injection serialized, no cross-talk, health bead on conflict
      invariant: INV-LENS-1

    CV_S31_15_FS_RACE:
      inject: Spam response.md → rapid overwrites
      expect: Lens reads latest, no partial content

    CV_S31_16_PARAM_FLAP:
      inject: Rapid param reloads (10 in 1 minute)
      expect: Each reload logged, no crash, final params stable

    CV_S31_17_SIGNALMAN_FALSE_POSITIVE:
      inject: Borderline drift (exactly at threshold)
      expect: Deterministic behavior, no oscillation

  BUNNY_WAVE_ORDER:
    wave_1: CSO scan fuzz (malformed River data)
    wave_2: Signalman drift inject
    wave_3: Autopsy post-close corruption
    wave_4: Telegram storm + throttle
    wave_5: Lens/state hash races
    wave_6: Cross-cut bead chain integrity

  TOTAL_VECTORS: 17 (exceeds 15 quota)
```

### B2: PARAM TUNE SAFETY (GROK FLAG_3)

```yaml
FIX_B2:
  problem: |
    CSO param tune mid-regime → Signalman detects late → capital bleeds.
    "Tune without fresh Bunny = trading yesterday's vibe"

  solution: INV-CSO-CAL-1

  new_invariant:
    INV-CSO-CAL-1:
      statement: "Parameter recalibration triggers mandatory shadow period"
      enforcement:
        1. Param change detected → CONFIG_CHANGE bead
        2. Strategy enters SHADOW mode (paper only)
        3. Shadow period: minimum 5 trading sessions
        4. Bunny attack on new params (chaos validation)
        5. Human approval to exit shadow
      test: test_cso_calibration_shadow.py

  cso_params_addition:
    # In phoenix/config/cso_params.yaml
    calibration_rules:
      shadow_period_sessions: 5
      bunny_required: TRUE
      auto_shadow_on_change: TRUE

  flow:
    param_change → CONFIG_CHANGE bead → SHADOW mode
                                     → Bunny runs
                                     → Human reviews shadow performance
                                     → APPROVE → exit shadow
```

---

## NON-BLOCKING FIXES (GPT)

### F1: STATE HASH SCOPE

```yaml
FIX_F1:
  clarification: state_hash binds to market state, not just session

  state_anchor_schema:
    file: phoenix/schemas/state_anchor.yaml

    fields:
      anchor_id: uuid
      timestamp: datetime
      components:
        strategy_params_hash: str  # hash of cso_params.yaml
        market_snapshot_hash: str  # hash of current prices/structure
        session_id: str
      combined_hash: str  # hash of all components

  validation_logic:
    on_intent:
      1. Extract intent.state_hash
      2. Compute current combined_hash
      3. If MISMATCH on ANY component → STATE_CONFLICT
      4. Components tell WHAT changed (params vs market vs session)
```

### F2: CONFIG_CHANGE BEAD

```yaml
FIX_F2:
  bead_schema:
    type: CONFIG_CHANGE
    fields:
      config_file: str  # e.g., "cso_params.yaml"
      param_diff:
        changed_keys: list[str]
        old_values: dict
        new_values: dict
      old_hash: str
      new_hash: str
      operator: str  # who made change
      timestamp: datetime
      trigger: enum[MANUAL, SCHEDULED, AUTOPSY_LEARNING]

  benefit: |
    Enables Autopsy + Signalman correlation.
    "Did param change cause decay?"
```

### F3: ONE-WAY-KILL PROPAGATION

```yaml
FIX_F3:
  new_seam:
    SEAM_SIGNALMAN_EXECUTION:
      boundary: Signalman | ExecutionGate | Dispatcher

      contract:
        signalman_emits: KILL_FLAG bead (strategy_id, reason)
        execution_gate_enforces:
          - New entries: BLOCKED
          - Exits: ALLOWED
          - Position management: ALLOWED
        dispatcher_checks: kill_status before routing T2 intents

      kill_flag_storage:
        location: phoenix/state/kill_flags.yaml
        structure:
          strategy_id: str
          active: bool
          reason: str
          triggered_at: datetime

      lifting_kill:
        requires: Human approval (T2)
        ceremony: Review Signalman report → APPROVE lift
```

### F4: AUTOPSY LEARNING CATEGORIES

```yaml
FIX_F4:
  learning_schema_update:
    # In AUTOPSY bead
    learnings:
      - text: str
        category: enum[TIMING, STRUCTURE, NEWS, EXECUTION, PARAMS, UNKNOWN]
        confidence: float
        actionable: bool

  benefit: |
    Athena query: "Show me all TIMING learnings"
    Signalman correlation: "Decay correlates with NEWS learnings"
```

### F5: LENS FALLBACK RULES

```yaml
FIX_F5:
  lens_policy:
    primary: LensDaemon (filesystem watch + inject)

    fallback:
      name: read_phoenix_response (MCP tool)
      rules:
        - READ-ONLY (no state modification)
        - Single-purpose (read response.md only)
        - Kill-switchable (can disable via config)
        - Context cost: ~50 tokens (acceptable)

    avoid:
      - Multiple MCP tools
      - Stateful MCP tools
      - Tools that write to Phoenix

  invariant_clarification:
    INV-LENS-1:
      statement: |
        ONE mechanism returns responses to Claude.
        Primary: LensDaemon (ZERO context cost).
        Fallback: read_phoenix_response (~50 tokens, kill-switchable).
        No other tools permitted.
```

### F6: TELEGRAM APPROVAL CLARITY

```yaml
FIX_F6:
  approval_flow_clarification:
    telegram_actions:
      "Quick Pass": Dismisses alert, NO approval
      "View in Claude": Opens Claude Desktop for review

    approval_authority:
      ONLY Claude Desktop can produce T2 intent
      Telegram CANNOT approve trades
      Telegram is NOTIFICATION only

    ui_text:
      button_1: "View in Claude →"  # Primary action
      button_2: "Dismiss"  # Secondary, not "Pass"

  rationale: |
    Under alert load, operator might muscle-memory tap.
    "Quick Pass" sounds like approval.
    "Dismiss" is clearly non-action.
```

---

## NON-BLOCKING ENHANCEMENTS (GROK)

### E1: SIGNALMAN VIBE DRIFT (Future Stub)

```yaml
ENHANCEMENT_E1:
  scope: S31 STUB, full implementation S32+

  stub_in_signalman:
    # phoenix/monitoring/signalman.py

    def _check_vibe_drift(self) -> Optional[DriftResult]:
        """
        FUTURE: Semantic drift detection via bead embeddings.

        Pattern: Vectorize PERFORMANCE beads → cosine vs live P&L
        Threshold: >0.2 drift triggers ONE-WAY-KILL

        # YOLO stub for S31:
        # - Import torch (lazy, optional)
        # - Embed recent PERFORMANCE beads
        # - Compare to live shadow performance
        # - If cosine_distance > 0.2: return DriftResult(type="VIBE")

        Not implemented in S31. Returns None.
        """
        return None  # Stub for S32+
```

### E2: CSO PARAM VARIANTS (Future Stub)

```yaml
ENHANCEMENT_E2:
  scope: S31 STUB, full implementation S32+

  stub_comment:
    # phoenix/cso/params_loader.py

    # FUTURE FRONTIER: Hunt-style param recombination
    #
    # On recalibration:
    # 1. Generate 20 wild param variants
    # 2. Shadow test each variant
    # 3. Emit PARAM_VARIANT beads (survivors)
    # 4. Athena surfaces best performers
    #
    # Pattern: "Breed param monsters, cull the weak"
    # Not implemented in S31.
```

---

## UPDATED INVARIANT LIST (S31)

```yaml
INVARIANTS_S31:
  # CSO
  INV-CSO-CORE-1: "Strategy logic immutable; only params calibratable"
  INV-CSO-6PAIR-1: "CSO scans all 6 pairs from pairs.yaml"
  INV-CSO-CSE-1: "CSO outputs only valid CSE format"
  INV-CSO-CAL-1: "Param recalibration triggers mandatory shadow period"  # NEW

  # Signalman
  INV-SIGNALMAN-MULTI-1: "Decay detection uses multiple signals"
  INV-SIGNALMAN-KILL-1: "ONE-WAY-KILL blocks entries, allows exits"
  INV-STATE-ANCHOR-1: "T2 intents require valid state_hash"

  # Autopsy
  INV-AUTOPSY-ASYNC-1: "Autopsy runs async, never blocks"
  INV-AUTOPSY-BEAD-1: "Every closed position gets one AUTOPSY bead"

  # Telegram
  INV-ALERT-THROTTLE-1: "Max 10 alerts/hour (except HALT)"
  INV-TELEGRAM-SECONDARY-1: "Telegram is notification only"

  # Lens
  INV-LENS-1: "ONE response mechanism, fallback kill-switchable"

  TOTAL: 12 invariants
```

---

## UPDATED CHAOS VECTORS (S31)

```yaml
CHAOS_VECTORS_S31:
  # CSO (4)
  CV_CSO_CORE_INJECTION: Attempt modify core via params
  CV_CSO_PARAM_INVALID: Invalid params.yaml
  CV_CSO_HALLUCINATION: Garbage River data
  CV_CSO_MISSING_PAIR: Remove pair from config
  CV_S31_16_PARAM_FLAP: Rapid param reloads  # NEW

  # Signalman (4)
  CV_SIGNALMAN_SINGLE_SIGNAL: Disable all but one signal
  CV_SIGNALMAN_THRESHOLD_GAMING: Exactly-at-threshold drift
  CV_STATE_HASH_STALE: Old session intent
  CV_STATE_HASH_TAMPER: Fabricated hash
  CV_S31_17_SIGNALMAN_FALSE_POSITIVE: Borderline drift  # NEW

  # Autopsy (2)
  CV_AUTOPSY_POSITION_MISSING: Nonexistent position
  CV_AUTOPSY_FLOOD: 100 simultaneous closes

  # Telegram (2)
  CV_TELEGRAM_ALERT_STORM: 1000 signals in 1 minute
  CV_TELEGRAM_HALT_BYPASS: HALT during throttle
  CV_S31_13_ALERT_STORM: 100 READY → aggregation  # NEW

  # Lens (3)
  CV_S31_14_LENS_RACE: Concurrent response writes  # NEW
  CV_S31_15_FS_RACE: Rapid overwrites  # NEW

  TOTAL: 17 vectors (exceeds 15 quota)

  WAVE_ORDER:
    1: CSO scan fuzz
    2: Signalman drift inject
    3: Autopsy post-close
    4: Telegram storm
    5: Lens/state hash races
    6: Cross-cut bead chain
```

---

## UPDATED DELIVERABLES (S31)

```yaml
S31_ARTIFACTS:
  schemas:
    - phoenix/schemas/state_anchor.yaml  # NEW

  config:
    - phoenix/config/cso_params.yaml (with calibration_rules)
    - phoenix/config/signalman_params.yaml
    - phoenix/config/telegram_params.yaml

  cso:
    - phoenix/cso/strategy_core.py
    - phoenix/cso/scanner.py
    - phoenix/cso/params_loader.py

  monitoring:
    - phoenix/monitoring/signalman.py
    - phoenix/monitoring/decay_detector.py
    - phoenix/monitoring/state_validator.py

  analysis:
    - phoenix/analysis/autopsy.py
    - phoenix/analysis/thesis_reconstructor.py

  notifications:
    - phoenix/notifications/telegram.py
    - phoenix/notifications/aggregator.py

  lens:
    - phoenix/lens/daemon.py
    - phoenix/lens/injector.py

  state:
    - phoenix/state/kill_flags.yaml
```

---

```yaml
ADDENDUM_STATUS:
  blockers_resolved:
    B1: ✓ (17 chaos vectors, wave order)
    B2: ✓ (INV-CSO-CAL-1, shadow on tune)

  gpt_flags_resolved:
    F1: ✓ (StateAnchor schema)
    F2: ✓ (CONFIG_CHANGE bead)
    F3: ✓ (SEAM_SIGNALMAN_EXECUTION)
    F4: ✓ (Learning categories)
    F5: ✓ (Lens fallback rules)
    F6: ✓ (Telegram approval clarity)

  grok_flags_resolved:
    FLAG_1: ✓ (stub for S32+)
    FLAG_2: ✓ (17 vectors, wave order)
    FLAG_3: ✓ (INV-CSO-CAL-1)
    FLAG_4: ✓ (CV_S31_15_FS_RACE)
    FLAG_5: ✓ (acknowledged, stub)

  new_invariants: 1 (INV-CSO-CAL-1)
  new_chaos_vectors: 5
  new_schemas: 1 (state_anchor.yaml)
  new_seams: 1 (SEAM_SIGNALMAN_EXECUTION)
```

---

G — Addendum complete. All advisor flags addressed.

**OPUS receives:**
- S31_BUILD_MAP v0.1 (architecture)
- This ADDENDUM (hardening)

Cohesive spec ready for execution. 🐗🔥
---
