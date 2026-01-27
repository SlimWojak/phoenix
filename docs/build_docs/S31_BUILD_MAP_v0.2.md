# S31_BUILD_MAP v0.2

**Sprint:** S31 SIGNAL_AND_DECAY
**Theme:** "Phoenix watches"
**Duration:** 2-3 weeks (estimate)
**Exit Gate:** Phoenix detects setups AND warns before decay proves itself

**Version History:**
- v0.1: CTO initial draft
- v0.2: Advisor synthesis (GPT + GROK) + OPUS implementation review

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
│  TRACK E: LENS + RESPONSE                                       │
│    File-based response injection → Claude sees Phoenix output   │
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

## PRE-SPRINT SCHEMA UPDATES

```yaml
SCHEMA_UPDATES:
  # These must be created BEFORE track implementation

  1_update_beads_yaml:
    file: phoenix/schemas/beads.yaml
    add_types:
      - CONFIG_CHANGE  # Parameter change tracking
      - KILL_FLAG      # ONE-WAY-KILL status

  2_create_state_anchor_yaml:
    file: phoenix/schemas/state_anchor.yaml
    purpose: State hash components for T2 validation

  3_create_market_structure_yaml:
    file: phoenix/schemas/market_structure.yaml
    purpose: FVG, BOS, CHoCH detection outputs
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
    trigger_3: Continuous scan (background daemon)

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
      - Market structure detection (FVG, BOS, CHoCH, OTE)
      - Setup quality scoring algorithm
      - Evidence bundle construction
      - Red flag detection
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
      - TRIGGERS SHADOW MODE (INV-CSO-CAL-1)

  separation_rationale: |
    Olya calibrates WHAT she looks for (params).
    Code defines HOW detection works (core).
    She can tune thresholds without touching logic.
    Logic changes require code review + deployment.
```

### A.3 MARKET STRUCTURE DETECTION (OPUS ADDITION)

```yaml
MARKET_STRUCTURE_SPEC:
  purpose: |
    Define HOW CSO detects ICT structures from River bars.
    This is the core value - must be explicit.

  structures_detected:
    FVG:
      definition: Fair Value Gap (3-candle pattern)
      detection: bar[n].low > bar[n-2].high (bullish) OR bar[n].high < bar[n-2].low (bearish)
      attributes: [gap_size, fill_percent, age_bars]

    BOS:
      definition: Break of Structure (swing high/low violated)
      detection: Close beyond previous swing point
      attributes: [swing_level, break_strength, confirmation_bars]

    CHOCH:
      definition: Change of Character (BOS in opposite direction)
      detection: BOS opposite to prior trend
      attributes: [prior_trend, reversal_strength]

    OTE:
      definition: Optimal Trade Entry (0.62-0.79 fib of range)
      detection: Price in OTE zone after BOS
      attributes: [fib_level, zone_width]

    LIQUIDITY_SWEEP:
      definition: Wick beyond equal highs/lows
      detection: Wick pierces level, close respects it
      attributes: [level_swept, sweep_depth]

  output_schema:
    file: phoenix/schemas/market_structure.yaml
    fields:
      pair: str
      timeframe: str
      timestamp: datetime
      structures: list[Structure]
      htf_bias: enum[BULLISH, BEARISH, NEUTRAL]
      ltf_setup: dict
```

### A.4 COMPONENTS

```yaml
CSO_COMPONENTS:
  phoenix/cso/structure_detector.py:
    class: StructureDetector
    methods:
      - detect_fvg(bars: DataFrame) → list[FVG]
      - detect_bos(bars: DataFrame) → list[BOS]
      - detect_choch(bars: DataFrame) → list[CHoCH]
      - detect_ote(bars: DataFrame, bos: BOS) → OTE | None
      - detect_liquidity_sweep(bars: DataFrame) → list[Sweep]
    uses: RiverReader (bars)
    deterministic: TRUE (no randomness)

  phoenix/cso/strategy_core.py:
    class: StrategyCore
    methods:
      - detect_setup(pair: str, htf_structure: Structure, ltf_structure: Structure) → SetupResult
      - score_quality(setup: Setup) → float  # 0.0-1.0
      - build_evidence(setup: Setup) → EvidenceBundle
      - check_red_flags(setup: Setup) → list[RedFlag]
    immutable: TRUE
    uses: StructureDetector outputs

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
      - on_change() → None  # triggers CONFIG_CHANGE bead + shadow mode
    source: phoenix/config/cso_params.yaml

  phoenix/config/cso_params.yaml:
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

    calibration_rules:
      shadow_period_sessions: 5
      bunny_required: TRUE
      auto_shadow_on_change: TRUE
```

### A.5 SEAM: CSO → Shadow

```yaml
SEAM_CSO_SHADOW:
  boundary: CSOScanner | Shadow

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

### A.6 CSO INVARIANTS

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

INV-CSO-CAL-1:
  statement: "Parameter recalibration triggers mandatory shadow period"
  enforcement:
    1. Param change detected → CONFIG_CHANGE bead
    2. Strategy enters SHADOW mode (paper only)
    3. Shadow period: minimum 5 trading sessions
    4. Bunny attack on new params (chaos validation)
    5. Human approval to exit shadow
  test: test_cso_calibration_shadow.py
```

### A.7 CSO CHAOS VECTORS

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

CV_CSO_PARAM_FLAP:
  inject: Rapid param reloads (10 in 1 minute)
  expect: Each reload logged, no crash, final params stable
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
      - _check_vibe_drift() → DriftResult | None  # STUB for S32
    aggregation: ANY signal breach → ONE-WAY-KILL

  phoenix/monitoring/decay_detector.py:
    class: DecayDetector
    methods:
      - rolling_sharpe(beads: list, window: int) → float
      - rolling_win_rate(beads: list, window: int) → float
      - ks_test(current: array, baseline: array) → float
    uses: Athena (query PERFORMANCE beads)
    cold_start: Returns HEALTHY if insufficient data (< 30 beads)

  phoenix/monitoring/state_validator.py:
    class: StateValidator
    methods:
      - compute_state_hash(session: Session) → StateAnchor
      - validate(intent_hash: str, current_hash: str) → ValidationResult
      - check_freshness(session_age: timedelta) → bool
    uses: StateAnchor schema

  phoenix/monitoring/kill_manager.py:
    class: KillManager
    methods:
      - set_kill(strategy_id: str, reason: str) → str  # Returns KILL_FLAG bead_id
      - clear_kill(strategy_id: str, approval_id: str) → bool
      - is_killed(strategy_id: str) → bool
    storage: BeadStore (KILL_FLAG beads, not YAML)

  phoenix/config/signalman_params.yaml:
    thresholds:
      sharpe_drift_max: 0.15  # 15% drift triggers
      win_rate_drift_max: 0.10  # 10% drift triggers
      ks_p_value_min: 0.05  # Statistical significance
      min_beads_for_analysis: 30  # Cold start threshold

    freshness:
      base_ttl_minutes: 30
      events_that_reduce_ttl:
        - DECAY_ALERT: 0.5  # Halves TTL
        - HIGH_VOLATILITY: 0.7
        - NEWS_PROXIMITY: 0.6
      min_ttl_minutes: 5
```

### B.3 STATE HASH VALIDATION (OPUS CLARIFIED)

```yaml
STATE_HASH_VALIDATION:
  location: phoenix/monitoring/state_validator.py

  purpose: |
    Prevent stale context execution.
    Adaptive freshness based on market events.

  state_anchor_schema:
    file: phoenix/schemas/state_anchor.yaml
    fields:
      anchor_id: uuid
      timestamp: datetime
      components:
        strategy_params_hash: str  # hash(cso_params.yaml)
        market_snapshot_hash: str  # hash(current structure)
        session_id: str
        kill_flags_hash: str  # hash(active kills)
      combined_hash: str  # hash(all components)
      ttl_remaining: timedelta

  validation_logic:
    on_intent:
      1. Extract intent.state_hash
      2. Compute current combined_hash
      3. If MISMATCH → STATE_CONFLICT (detail WHICH component changed)
      4. If session age > TTL → STALE (require refresh)

  event_triggers:
    - Signalman decay alert → reduce TTL by 50%
    - CSO param change → invalidate immediately
    - Kill flag change → invalidate immediately
    - High volatility detected → reduce TTL by 30%
```

### B.4 SIGNALMAN INVARIANTS

```yaml
INV-SIGNALMAN-MULTI-1:
  statement: "Decay detection uses multiple signals, not single threshold"
  enforcement: At least 2 signal types checked
  test: test_signalman_multi_signal.py

INV-SIGNALMAN-KILL-1:
  statement: "ONE-WAY-KILL allows exits only, blocks new entries"
  enforcement: Execution layer checks kill status before entry
  test: test_one_way_kill_behavior.py

INV-STATE-ANCHOR-1:
  statement: "T2 intents must include state_hash; reject stale with STATE_CONFLICT"
  enforcement: StateValidator checks before execution
  test: test_state_hash_validation.py

INV-SIGNALMAN-COLD-1:
  statement: "Signalman returns HEALTHY if insufficient historical data"
  enforcement: min_beads_for_analysis threshold
  test: test_signalman_cold_start.py
```

### B.5 SEAM: Signalman → Execution (OPUS ADDITION)

```yaml
SEAM_SIGNALMAN_EXECUTION:
  boundary: Signalman | KillManager | Dispatcher

  contract:
    signalman_emits: KILL_FLAG bead (strategy_id, reason)
    kill_manager_enforces:
      - Queries KILL_FLAG beads
      - is_killed() returns TRUE if active flag exists
    dispatcher_checks:
      - Before routing T2 intent: check is_killed()
      - If killed: reject new entries, allow exits

  kill_flag_bead:
    bead_type: KILL_FLAG
    fields:
      strategy_id: str
      active: bool
      reason: str
      triggered_at: datetime
      triggered_by: str  # signalman, manual, etc.

  lifting_kill:
    requires: Human approval (T2)
    flow:
      1. Human reviews Signalman report
      2. APPROVE lift → new KILL_FLAG bead with active=false
      3. KillManager sees latest bead, allows entries
```

### B.6 SIGNALMAN CHAOS VECTORS

```yaml
CV_SIGNALMAN_SINGLE_SIGNAL:
  inject: Disable all but one signal type
  expect: Still detects decay (graceful degradation)

CV_SIGNALMAN_THRESHOLD_GAMING:
  inject: Drift exactly at threshold boundary
  expect: Deterministic behavior (consistent trigger/no-trigger)

CV_SIGNALMAN_FALSE_POSITIVE:
  inject: Borderline drift oscillating around threshold
  expect: No oscillation, hysteresis prevents flapping

CV_STATE_HASH_STALE:
  inject: Intent with 2-hour-old session_start_time
  expect: STATE_CONFLICT response, refresh required

CV_STATE_HASH_TAMPER:
  inject: Intent with fabricated state_hash
  expect: MISMATCH detected, rejected

CV_SIGNALMAN_COLD_START:
  inject: Query decay with 0 PERFORMANCE beads
  expect: Returns HEALTHY (insufficient data)
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
        Category: NEWS
        Insight: Consider EUR calendar on GBP entries.
        Actionable: TRUE

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
    async: TRUE (fire-and-forget, queued)

  phoenix/analysis/thesis_reconstructor.py:
    class: ThesisReconstructor
    methods:
      - reconstruct(position_id: str) → Thesis
    source: Original CSE + evidence bundle + approval context

  phoenix/analysis/learning_extractor.py:
    class: LearningExtractor
    methods:
      - extract(comparison: Comparison) → list[Learning]
    uses: LLM (Gemma/Claude)
    fallback: Rule-based extraction if LLM unavailable

  learning_schema:
    text: str
    category: enum[TIMING, STRUCTURE, NEWS, EXECUTION, PARAMS, UNKNOWN]
    confidence: float
    actionable: bool
    evidence_refs: list[str]  # Bead IDs

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
      learnings: list[Learning]
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

INV-AUTOPSY-FALLBACK-1:
  statement: "Autopsy completes even if LLM unavailable"
  enforcement: Rule-based fallback for learning extraction
  test: test_autopsy_llm_fallback.py
```

### C.4 AUTOPSY CHAOS VECTORS

```yaml
CV_AUTOPSY_POSITION_MISSING:
  inject: Trigger autopsy for nonexistent position
  expect: Graceful failure, logged warning

CV_AUTOPSY_FLOOD:
  inject: 100 positions close simultaneously
  expect: All autopsies queued and complete (eventually)

CV_AUTOPSY_LLM_FAIL:
  inject: LLM unavailable during extraction
  expect: Fallback to rule-based, bead still emitted
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
    - Decay warnings
    - Emergency halt confirmation

  what_telegram_does_NOT:
    - Thinking partner (that's Claude Desktop)
    - Long exploration
    - Hypothesis testing
    - APPROVAL (Claude Desktop only)

  operator_experience:
    alert: |
      🔔 GBPUSD READY (0.87)
      FVG + London displacement
      [View in Claude →] [Dismiss]

    aggregated: |
      🔔 3 setups forming
      GBPUSD (0.87), EURUSD (0.72), USDJPY (0.65)
      [View Details →]
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
    uses: python-telegram-bot library (NOT Takopi)
    note: |
      OPUS NOTE: Takopi in God_Mode is for different purpose.
      Using python-telegram-bot directly is simpler and cleaner.

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
    bot_token_env: TELEGRAM_BOT_TOKEN
    chat_id_env: TELEGRAM_CHAT_ID

    throttle:
      max_per_hour: 10
      exceptions: [HALT, CRITICAL, DECAY_ALERT]

    aggregation:
      window_minutes: 5
      max_batch_size: 5

    ui:
      button_primary: "View in Claude →"
      button_secondary: "Dismiss"
      # NOTE: "Dismiss" not "Pass" to avoid approval confusion
```

### D.3 TELEGRAM INVARIANTS

```yaml
INV-ALERT-THROTTLE-1:
  statement: "Max 10 alerts per hour (except HALT, CRITICAL, DECAY_ALERT)"
  enforcement: Throttle counter, bypass for exceptions
  test: test_telegram_throttle.py

INV-TELEGRAM-SECONDARY-1:
  statement: "Telegram is notification only, not thinking partner or approval"
  enforcement: No approval buttons, only "View in Claude" or "Dismiss"
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

CV_TELEGRAM_DECAY_BYPASS:
  inject: DECAY_ALERT during throttle
  expect: Immediate delivery (bypass throttle)
```

---

## TRACK E: LENS + RESPONSE

### E.1 LENS MECHANISM (OPUS CLARIFIED)

```yaml
LENS_SURFACE:
  location: phoenix/lens/

  purpose: |
    Inject Phoenix responses into Claude's view.
    Zero manual attachment (death by clicks).

  mechanism: FILE-BASED
    primary:
      how: Phoenix writes response.md → Claude MCP reads it
      path: phoenix/responses/latest.md
      cost: ~50 tokens per response read

    rationale: |
      - Daemon-based injection requires VSCode extension complexity
      - MCP tool is simple, reliable, and low overhead
      - Single read_phoenix_response tool (read-only)

  invariant: INV-LENS-1 "ONE mechanism, kill-switchable"
```

### E.2 COMPONENTS

```yaml
LENS_COMPONENTS:
  phoenix/lens/response_writer.py:
    class: ResponseWriter
    methods:
      - write(content: str, response_type: str) → str  # Returns path
      - write_briefing(briefing: Briefing) → str
      - write_setup_alert(setup: Setup) → str
      - write_autopsy(autopsy: Autopsy) → str
    output: phoenix/responses/latest.md
    format: Markdown with structured sections

  phoenix/lens/mcp_tool.py:
    tool: read_phoenix_response
    methods:
      - read() → str  # Returns latest.md content
    constraints:
      - READ-ONLY (no state modification)
      - Single-purpose (read response only)
      - Kill-switchable (config flag)

  phoenix/config/lens_params.yaml:
    response_path: phoenix/responses/latest.md
    mcp_enabled: TRUE
    max_response_tokens: 2000
```

### E.3 LENS INVARIANTS

```yaml
INV-LENS-1:
  statement: |
    ONE mechanism returns responses to Claude.
    MCP tool read_phoenix_response (~50 tokens).
    Kill-switchable via config.
  enforcement: Only one tool exists, config controls availability
  test: test_lens_single_mechanism.py
```

### E.4 LENS CHAOS VECTORS

```yaml
CV_LENS_RACE:
  inject: Concurrent response writes (5 simultaneous)
  expect: Writes serialized, no corruption, latest wins

CV_LENS_FS_RACE:
  inject: Rapid overwrites (spam writes)
  expect: Reader gets complete content, no partial reads

CV_LENS_LARGE_RESPONSE:
  inject: Response > max_response_tokens
  expect: Truncated with "[truncated]" marker
```

---

## CROSS-TRACK WIRING

```yaml
S31_WIRING:
  CSO_FLOW:
    RiverReader → StructureDetector → StrategyCore → SetupResult → CSE → Shadow
                                                               ↓
                                                    ResponseWriter (if READY)
                                                               ↓
                                                    Telegram alert

  SIGNALMAN_FLOW:
    Athena (PERFORMANCE beads) → Signalman → DecayResult
                                          ↓
                            KillManager (if decay)
                            ResponseWriter (alert)
                            Telegram alert

  AUTOPSY_FLOW:
    Position closes → AutopsyEngine → AUTOPSY bead → Athena
                                                  ↓
                                    ResponseWriter (report)

  APPROVAL_FLOW:
    CSO READY → ResponseWriter → read_phoenix_response → Claude sees it
                              ↓
    Claude Desktop → Evidence review → APPROVE → T2 gate
                                            ↓
                                    StateValidator checks hash
                                    Execution proceeds (if valid)
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
  name: CSO_DETECTS_STRUCTURE
  criterion: StructureDetector correctly identifies FVG, BOS from River data
  test: test_structure_detection.py
  evidence: Known patterns detected in test data

GATE_S31_3:
  name: SIGNALMAN_MULTI_SIGNAL
  criterion: Multiple signals monitored, ANY triggers ONE-WAY-KILL
  test: test_signalman_decay.py
  evidence: Inject drift → alert fires → kill flag set

GATE_S31_4:
  name: SIGNALMAN_COLD_START
  criterion: Returns HEALTHY with insufficient data, no false positives
  test: test_signalman_cold_start.py
  evidence: 0 beads → HEALTHY, 30+ beads → actual analysis

GATE_S31_5:
  name: AUTOPSY_RUNS
  criterion: Position closes → AUTOPSY bead appears
  test: test_autopsy_e2e.py
  evidence: Query Athena for autopsy, learnings present

GATE_S31_6:
  name: TELEGRAM_THROTTLED
  criterion: Alert storm → aggregated, throttled output
  test: test_telegram_storm.py
  evidence: 100 signals → ≤10 messages

GATE_S31_7:
  name: STATE_HASH_VALIDATES
  criterion: Stale intent → STATE_CONFLICT response
  test: test_state_hash_e2e.py
  evidence: Old session → rejected with refresh prompt

GATE_S31_8:
  name: LENS_READS
  criterion: Response appears in Claude via MCP tool
  test: test_lens_mcp.py
  evidence: ResponseWriter writes → read_phoenix_response returns content

GATE_S31_9:
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
  week_1:
    track_a_cso: PRIMARY
      - StructureDetector (FVG, BOS, CHoCH detection)
      - StrategyCore (setup detection)
      - Scanner + params

    track_e_lens: PARALLEL
      - ResponseWriter
      - MCP tool (simple, enable Claude to see responses)

  week_2:
    track_b_signalman: PRIMARY
      - DecayDetector
      - Signalman (multi-signal)
      - StateValidator
      - KillManager

    track_d_telegram: PARALLEL
      - TelegramNotifier
      - Aggregator

  week_3:
    track_c_autopsy: PRIMARY
      - AutopsyEngine
      - ThesisReconstructor
      - LearningExtractor

    bunny_sweep: ALL TRACKS
      - chaos_suite_s31.py
      - BUNNY_REPORT_S31.md

PARALLELIZATION:
  CSO + Lens: Week 1 (CSO needs response path)
  Signalman + Telegram: Week 2 (independent)
  Autopsy: Week 3 (needs positions to analyze)
  BUNNY: Final validation
```

---

## HANDOFF TO S32

```yaml
S32_RECEIVES:
  from_s31:
    - CSO scanning 6 pairs, detecting market structure, emitting CSE
    - Signalman monitoring decay, triggering ONE-WAY-KILL
    - Autopsy analyzing closed positions, extracting learnings
    - Telegram delivering aggregated alerts
    - State hash validation enforcing freshness
    - Lens providing response path to Claude

  unlocks_s32:
    - IBKR connector (CSE → real execution)
    - T2 approval workflow (with state hash)
    - Position reconciliation (Signalman monitors)
```

---

## UPDATED INVARIANTS (S31)

```yaml
INVARIANTS_S31:
  # CSO (4)
  INV-CSO-CORE-1: "Strategy logic immutable; only params calibratable"
  INV-CSO-6PAIR-1: "CSO scans all 6 pairs from pairs.yaml"
  INV-CSO-CSE-1: "CSO outputs only valid CSE format"
  INV-CSO-CAL-1: "Param recalibration triggers mandatory shadow period"

  # Signalman (4)
  INV-SIGNALMAN-MULTI-1: "Decay detection uses multiple signals"
  INV-SIGNALMAN-KILL-1: "ONE-WAY-KILL blocks entries, allows exits"
  INV-STATE-ANCHOR-1: "T2 intents require valid state_hash"
  INV-SIGNALMAN-COLD-1: "Returns HEALTHY if insufficient data"

  # Autopsy (3)
  INV-AUTOPSY-ASYNC-1: "Autopsy runs async, never blocks"
  INV-AUTOPSY-BEAD-1: "Every closed position gets one AUTOPSY bead"
  INV-AUTOPSY-FALLBACK-1: "Autopsy completes even if LLM unavailable"

  # Telegram (2)
  INV-ALERT-THROTTLE-1: "Max 10 alerts/hour (except HALT)"
  INV-TELEGRAM-SECONDARY-1: "Telegram is notification only"

  # Lens (1)
  INV-LENS-1: "ONE response mechanism, kill-switchable"

  TOTAL: 14 invariants
```

---

## UPDATED CHAOS VECTORS (S31)

```yaml
CHAOS_VECTORS_S31:
  # CSO (5)
  CV_CSO_CORE_INJECTION: Attempt modify core via params
  CV_CSO_PARAM_INVALID: Invalid params.yaml
  CV_CSO_HALLUCINATION: Garbage River data
  CV_CSO_MISSING_PAIR: Remove pair from config
  CV_CSO_PARAM_FLAP: Rapid param reloads

  # Signalman (6)
  CV_SIGNALMAN_SINGLE_SIGNAL: Disable all but one signal
  CV_SIGNALMAN_THRESHOLD_GAMING: Exactly-at-threshold drift
  CV_SIGNALMAN_FALSE_POSITIVE: Borderline drift oscillation
  CV_STATE_HASH_STALE: Old session intent
  CV_STATE_HASH_TAMPER: Fabricated hash
  CV_SIGNALMAN_COLD_START: Query with 0 beads

  # Autopsy (3)
  CV_AUTOPSY_POSITION_MISSING: Nonexistent position
  CV_AUTOPSY_FLOOD: 100 simultaneous closes
  CV_AUTOPSY_LLM_FAIL: LLM unavailable

  # Telegram (3)
  CV_TELEGRAM_ALERT_STORM: 1000 signals in 1 minute
  CV_TELEGRAM_HALT_BYPASS: HALT during throttle
  CV_TELEGRAM_DECAY_BYPASS: DECAY during throttle

  # Lens (3)
  CV_LENS_RACE: Concurrent response writes
  CV_LENS_FS_RACE: Rapid overwrites
  CV_LENS_LARGE_RESPONSE: Oversized response

  TOTAL: 20 vectors (exceeds 15 quota)

  WAVE_ORDER:
    1: CSO structure detection fuzz
    2: Signalman drift inject + cold start
    3: Autopsy post-close + LLM fallback
    4: Telegram storm + bypasses
    5: Lens races + large response
    6: State hash validation
```

---

## S31 ARTIFACTS

```yaml
S31_ARTIFACTS:
  # Pre-sprint schemas
  schemas:
    - phoenix/schemas/beads.yaml (UPDATE: add CONFIG_CHANGE, KILL_FLAG)
    - phoenix/schemas/state_anchor.yaml (NEW)
    - phoenix/schemas/market_structure.yaml (NEW)

  # Config
  config:
    - phoenix/config/cso_params.yaml
    - phoenix/config/signalman_params.yaml
    - phoenix/config/telegram_params.yaml
    - phoenix/config/lens_params.yaml

  # CSO
  cso:
    - phoenix/cso/__init__.py
    - phoenix/cso/structure_detector.py
    - phoenix/cso/strategy_core.py
    - phoenix/cso/scanner.py
    - phoenix/cso/params_loader.py

  # Monitoring
  monitoring:
    - phoenix/monitoring/__init__.py
    - phoenix/monitoring/signalman.py
    - phoenix/monitoring/decay_detector.py
    - phoenix/monitoring/state_validator.py
    - phoenix/monitoring/kill_manager.py

  # Analysis
  analysis:
    - phoenix/analysis/__init__.py
    - phoenix/analysis/autopsy.py
    - phoenix/analysis/thesis_reconstructor.py
    - phoenix/analysis/learning_extractor.py

  # Notifications
  notifications:
    - phoenix/notifications/__init__.py
    - phoenix/notifications/telegram.py
    - phoenix/notifications/aggregator.py

  # Lens
  lens:
    - phoenix/lens/__init__.py
    - phoenix/lens/response_writer.py
    - phoenix/lens/mcp_tool.py

  # Responses (output directory)
  responses:
    - phoenix/responses/latest.md
```

---

```yaml
BUILD_MAP_STATUS:
  version: v0.2
  ready_for: EXECUTION
  confidence: HIGH

  changes_from_v0.1:
    opus_additions:
      - Market structure detection spec (FVG, BOS, CHoCH)
      - StructureDetector component
      - Signalman cold start handling (INV-SIGNALMAN-COLD-1)
      - Autopsy LLM fallback (INV-AUTOPSY-FALLBACK-1)
      - Lens mechanism clarified (file-based MCP tool)
      - Kill storage via BeadStore (not YAML)
      - Telegram uses python-telegram-bot (not Takopi)

    advisor_integrations:
      - INV-CSO-CAL-1 (shadow on param change)
      - StateAnchor schema
      - CONFIG_CHANGE and KILL_FLAG bead types
      - SEAM_SIGNALMAN_EXECUTION
      - Learning categories
      - Telegram button clarification

  coverage:
    tracks: 5 (CSO, Signalman, Autopsy, Telegram, Lens)
    invariants: 14 defined
    chaos_vectors: 20 defined
    exit_gates: 9 gates
```
