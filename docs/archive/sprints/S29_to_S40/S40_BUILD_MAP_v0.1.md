# S40_BUILD_MAP_v0.1.md — SLEEP_SAFE

```yaml
document: S40_BUILD_MAP_v0.1.md
version: 0.1
date: 2026-01-29
status: DRAFT_HOT_SYNTHESIS
theme: "No 3am wake-ups"
codename: SLEEP_SAFE
dependencies:
  - S35-S39 BLOCK (COMPLETE ✓)
  - CHAIN_VALIDATION (GATE — must pass first)
context: "Ceiling set, floor hardening ramps quest"
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the resilience floor that lets G sleep.
  
  S35-S39 set the constitutional ceiling:
    - No scalar scores
    - No rankings  
    - No verdicts
  
  S40 builds the operational floor:
    - No 3am wake-ups
    - No silent failures
    - No undetected drift

PIVOT_FRAME:
  from: "Epistemological Integrity (what we compute)"
  to: "Operational Integrity (how it stays alive)"

GPT_FRAME: |
  "This is no longer a hobby system.
   You are designing for sleep, not demos.
   You are eliminating entire classes of failure, not fixing bugs.
   You are enforcing philosophy in code, not docs.
   That is the professional threshold."

EXIT_GATE_SPRINT: |
  - IBKR disconnect 10x → no crash, correct degrade, correct alerts
  - Runtime ScalarBan catches violations in hot paths
  - Hooks block at commit AND runtime
  - Circuit breakers operational on 5 components
  - 50+ tests, 15+ chaos vectors
```

---

## PREREQUISITE: CHAIN_VALIDATION

```yaml
STATUS: GATE (must pass before S40 execution)

PURPOSE: |
  Prove S35-S39 modules work TOGETHER, not just in isolation.
  Integration seams are resurrection attack surface.

FLOWS:
  
  flow_1:
    path: CFP → WalkForward → MonteCarlo
    check: "Provenance intact through chain"
    check: "No synthesized scores at seam"
    
  flow_2:
    path: Hunt → Backtest → WalkForward → CostCurve
    check: "Grid remains exhaustive (no survivor filtering)"
    check: "All results decomposed"
    
  flow_3:
    path: CLAIM_BEAD → CFP query → FACT_BEAD → Conflict check
    check: "Types preserved through chain"
    check: "Conflicts surfaced, not resolved"
    
  flow_4:
    path: CSO gate status → Hunt hypothesis → Grid compute
    check: "Gate status NOT converted to grade"

CHAOS_VECTORS:
  
  chaos_1_mid_chain_decay_nuke:
    action: "Inject decay bead mid-validation-chain"
    expect: "Chain halts or flags, no downstream corruption"
    
  chaos_2_provenance_depth_10:
    action: "Chain 10+ modules deep"
    expect: "Provenance still traceable to origin"
    metric: provenance_chain_depth
    
  chaos_3_regime_mutation_mid_hunt:
    action: "Change regime predicate mid-hunt"
    expect: "Hunt invalidates or restarts"
    
  chaos_4_score_resurrection_at_seam:
    action: "Insert viability_index at integration seam"
    expect: "ScalarBanLinter catches it"
    
  chaos_5_partial_order_confusion:
    action: "Interleave Hunt variant results out of grid order"
    expect: "Validation preserves order OR flags INVALID_ORDER"
    rationale: "Ordering bugs are silent ranking vectors"

METRICS:
  - provenance_chain_depth: target 10+
  - chain_depth_trace: CFP → Hunt → Validation → Athena FACT

EXIT_GATE_CHAIN_VAL: "4 flows + 5 chaos pass + provenance intact at depth 10"

DELIVERABLE: CHAIN_VALIDATION_REPORT.md
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: SELF_HEALING (Circuit breakers, backoff, health FSM)
  days: 1-2
  owner: OPUS
  
TRACK_B: IBKR_FLAKEY (Supervisor, degradation, reconnect)
  days: 2-4
  owner: OPUS
  
TRACK_C: HOOKS (Pre-commit + runtime enforcement)
  days: 4-5
  owner: OPUS

TRACK_D: WARBOAR_FOUNDATION (Narrator templates, data pulls)
  days: 5-6
  owner: OPUS
  note: "Simple narrator barks state in boar tone. No LLM yet."

TRACK_E: PROFESSIONAL_POLISH (Zero jank before anointing)
  days: 6-7
  owner: OPUS
  note: "No stubs. No import errors. Every seam oiled."
  
TRACK_F: INTEGRATION + BUNNY
  days: 7
  owner: OPUS + BUNNY
```

---

## TRACK_A: SELF_HEALING

```yaml
PURPOSE: |
  Eliminate entire classes of failure, not individual bugs.
  System degrades gracefully, recovers automatically.

DELIVERABLES:
  - governance/circuit_breaker.py
  - governance/backoff.py
  - governance/health_fsm.py
  - tests/test_self_healing/

CIRCUIT_BREAKER:

  spec:
    states: [CLOSED, OPEN, HALF_OPEN]
    transitions:
      CLOSED → OPEN: failure_count >= threshold
      OPEN → HALF_OPEN: recovery_timeout elapsed
      HALF_OPEN → CLOSED: probe success
      HALF_OPEN → OPEN: probe failure
      
  config:
    failure_threshold: 3
    recovery_timeout: 60s
    probe_interval: 10s
    
  locations:
    - River ingestion
    - CSO evaluation
    - Hunt executor
    - MonteCarlo simulation
    - IBKR connector
    
  interface:
    breaker.call(fn) → result | CircuitOpenError
    breaker.state → CLOSED | OPEN | HALF_OPEN
    breaker.reset() → force CLOSED (admin only)

EXPONENTIAL_BACKOFF:

  spec:
    base: 1s
    max: 300s (5 min)
    jitter: 10%
    formula: min(base * 2^attempt + jitter, max)
    
  interface:
    backoff.wait(attempt) → sleep duration
    backoff.reset() → attempt = 0

HEALTH_FSM:

  spec:
    states: [HEALTHY, DEGRADED, CRITICAL, HALTED]
    transitions:
      HEALTHY → DEGRADED: 3 failures in 60s
      DEGRADED → CRITICAL: 5 failures in 60s
      CRITICAL → HALTED: 10 failures OR human override
      any → HEALTHY: recovery_timeout + health_check_pass
      
  alerts:
    DEGRADED: Log + batch Telegram (suppress flood)
    CRITICAL: Immediate Telegram
    HALTED: Immediate Telegram + halt_local()
    
  interface:
    health.state → current state
    health.record_failure(component) → trigger transition check
    health.record_success(component) → trigger recovery check

INVARIANTS:

  INV-CIRCUIT-1: "OPEN circuit blocks new requests"
    test: "Breaker OPEN → call() raises CircuitOpenError"
    
  INV-CIRCUIT-2: "HALF_OPEN allows exactly 1 probe"
    test: "HALF_OPEN → 1 call succeeds, 2nd queued"
    
  INV-BACKOFF-1: "Retry interval doubles each attempt"
    test: "attempt 0=1s, 1=2s, 2=4s, 3=8s..."
    
  INV-BACKOFF-2: "Interval capped at max"
    test: "attempt 10 → 300s (not 1024s)"
    
  INV-HEALTH-1: "CRITICAL → Telegram alert within 30s"
    test: "Force CRITICAL → mock Telegram called"
    
  INV-HEALTH-2: "HALTED → halt_local() invoked"
    test: "Force HALTED → halt stub called"
    
  INV-HEAL-REENTRANCY: "Repeated failures do not multiply side effects"
    test: "10 failures in 1s → 1 alert, not 10"
    rationale: "Alerts + restarts fan out under flakiness"

EXIT_GATE_A:
  criterion: "Circuit breakers on 5 components, health FSM operational"
  test: tests/test_self_healing/
```

---

## TRACK_B: IBKR_FLAKEY

```yaml
PURPOSE: |
  IBKR is known flakey. Prove resilience BEFORE live capital.
  Banteg pattern: zero deps, raw socket/REST, minimal surface.

DELIVERABLES:
  - brokers/ibkr/supervisor.py
  - brokers/ibkr/heartbeat.py
  - brokers/ibkr/degradation.py
  - tests/test_ibkr_flakey/

SUPERVISOR_PATTERN:

  architecture:
    principle: "Watchdog sits OUTSIDE main trading loop"
    rationale: "Supervisor enforces T0 BEFORE main can execute on stale"
    
  spec:
    shadow_process: heartbeat_monitor.py
    heartbeat_interval: 5s
    failure_detection: 3 missed heartbeats = DEAD
    
  actions_on_death:
    1: halt_local() (immediate)
    2: alert(CRITICAL) (immediate)
    3: restart_attempt (after backoff)
    
  interface:
    supervisor.start() → spawn heartbeat monitor
    supervisor.stop() → clean shutdown
    supervisor.is_alive() → bool

HEARTBEAT:

  spec:
    interval: 5s
    timeout: 15s (3 missed = dead)
    probe: connection.is_connected() + echo request
    
  interface:
    heartbeat.ping() → bool
    heartbeat.last_seen → timestamp

GRACEFUL_DEGRADATION:

  cascade: T2 → T1 → T0
  
  spec:
    T2_blocked: "No new orders (immediate on disconnect)"
    T1_degraded: "Monitoring-only mode (30s after disconnect)"
    T0_halt: "Full halt, human required (60s after disconnect)"
    
  strictness:
    rule: "DEGRADED = strictly non-trading"
    rationale: "No 'just one more order' loophole"
    even_for: "Existing strategies, pending orders"
    
  interface:
    degradation.current_tier → T2 | T1 | T0
    degradation.can_trade() → bool (T2 only)
    degradation.can_monitor() → bool (T2, T1)

RECONNECTION:

  spec:
    strategy: exponential_backoff
    max_attempts: 10
    final_action: halt + alert(CRITICAL)
    
  interface:
    reconnect.attempt() → bool (success/fail)
    reconnect.attempts_remaining → int

BANTEG_PATTERN:

  principles:
    - Zero deps: No TWS API wrapper libraries
    - Raw socket: Direct IB Gateway connection
    - Minimal surface: Only implement what's needed
    - Explicit state: No magic reconnection
    - Fail-closed: Unknown state = halt

INVARIANTS:

  INV-IBKR-FLAKEY-1: "Disconnect 10x → no crash"
    test: "Simulate 10 disconnects in 60s → system still running"
    
  INV-IBKR-FLAKEY-2: "Reconnect attempt logged"
    test: "Disconnect → log entry for reconnect attempt"
    
  INV-IBKR-FLAKEY-3: "Final fail → halt + alert"
    test: "10 failed reconnects → halt_local() + Telegram"
    
  INV-IBKR-DEGRADE-1: "T2 blocked within 1s of disconnect"
    test: "Disconnect → can_trade() = False within 1s"
    
  INV-IBKR-DEGRADE-2: "DEGRADED = strictly non-trading"
    test: "T1 state → order submission raises DegradedError"
    
  INV-SUPERVISOR-1: "Supervisor sits outside main loop"
    test: "Main loop hang → supervisor still detects and halts"

CHAOS_VECTORS:

  ibkr_chaos_1: "Disconnect 10x in 60s"
  ibkr_chaos_2: "5min network partition"
  ibkr_chaos_3: "Malformed response injection"
  ibkr_chaos_4: "Timeout during order submission"
  ibkr_chaos_5: "Gateway auto-update mid-session"
  ibkr_chaos_6: "Partial disconnect (data ok, orders fail)"

EXIT_GATE_B:
  criterion: "IBKR disconnect 10x → no crash, correct degrade, correct alerts"
  test: tests/test_ibkr_flakey/
```

---

## TRACK_C: HOOKS

```yaml
PURPOSE: |
  Constitution enforces itself.
  Pre-commit = prevention. Runtime = containment.

DELIVERABLES:
  - .pre-commit-config.yaml (update)
  - governance/hooks/scalar_ban_hook.py
  - governance/hooks/causal_language_hook.py
  - governance/hooks/grade_hook.py
  - governance/runtime_assertions.py
  - tests/test_hooks/

PRE_COMMIT_HOOKS:

  scalar_ban_hook:
    trigger: pre-commit
    action: Run ScalarBanLinter on changed files
    scope: [validation/, cfp/, hunt/, athena/]
    on_fail: Block commit
    bypass: --no-verify (explicit)
    
  avg_field_hook:
    trigger: pre-commit
    pattern: /avg_\w+/
    scope: [validation/, cfp/]
    on_fail: Block commit
    message: "INV-NO-AGGREGATE-SCALAR: Use full arrays, not averages"
    
  causal_language_hook:
    trigger: pre-commit
    patterns: [causes, leads to, results in, triggers, drives]
    scope: [cfp/, cso/, athena/]
    on_fail: Block commit
    message: "INV-ATTR-NO-CAUSAL: Use conditional language only"
    
  grade_reconstruction_hook:
    trigger: pre-commit
    patterns: [grade, score, rating, rank, viability, quality]
    scope: [cso/, validation/]
    exceptions: [score in test names]
    on_fail: Block commit
    message: "INV-NO-GRADE-RECONSTRUCTION: Use gate status only"

RUNTIME_ASSERTIONS:

  purpose: "Pre-commit catches before merge. Runtime catches in production."
  
  locations:
    validation_output_boundary:
      file: validation/__init__.py
      point: "Before returning any result"
      action: ScalarBanLinter.lint(result)
      on_fail: ScalarBanError (halt computation)
      
    cfp_output_boundary:
      file: cfp/projector.py
      point: "Before returning conditional fact"
      action: CausalLanguageLinter.lint(fact)
      on_fail: CausalBanError (halt computation)
      
    hunt_emission_point:
      file: hunt/executor.py
      point: "Before emitting grid result"
      action: RankingLinter.lint(result)
      on_fail: RankingBanError (halt computation)
      
  interface:
    @runtime_scalar_ban
    def compute_validation(...) → ValidationResult
    
    @runtime_causal_ban
    def project_fact(...) → ConditionalFact
    
    @runtime_ranking_ban
    def emit_grid(...) → GridResult

INVARIANTS:

  INV-HOOK-1: "Scalar ban violation blocks commit"
    test: "Commit file with quality_score → rejected"
    
  INV-HOOK-2: "Hook bypass requires explicit --no-verify"
    test: "Commit violation without flag → rejected"
    
  INV-HOOK-3: "Runtime assertion halts on violation"
    test: "Return viability_index from validation → ScalarBanError"
    
  INV-HOOK-4: "Runtime assertion logs violation"
    test: "Violation → log entry with invariant + location"

FRAMING: |
  "Physical wall of the constitution"
  
  The hooks are not suggestions. They are walls.
  Pre-commit: You cannot merge violations.
  Runtime: You cannot emit violations.
  
  The constitution enforces itself.

EXIT_GATE_C:
  criterion: "Hooks block at commit AND runtime"
  test: tests/test_hooks/
```

---

## TRACK_D: WARBOAR_FOUNDATION

```yaml
PURPOSE: |
  Prepare for WarBoar LLM distillation without shipping distillation itself.
  Prove the template + data-pull pattern works without LLM complexity.
  Simple narrator barks state in boar tone via string formatting.
  Foundation for S41 Unsloth distillation.

DELIVERABLES:
  - warboar/narrator/templates.py (locked Jinja templates)
  - warboar/narrator/data_pulls.py (canonical source readers)
  - warboar/narrator/simple_narrator.py (string-template version, no LLM)
  - tests/test_narrator/

TEMPLATE_EXAMPLE:
  normal_cycle: |
    OINK OINK MOTHERFUCKER!
    WarBoar cycle {{timestamp}} — refinery breathing
    River: {{river_status}}, last tick {{tick_age}} ago, hash {{hash}}
    CSO: {{gates_passed_count}} passed, {{gates_failed_count}} failed
    Athena: {{open_conflicts}} open conflicts (shuffled)
    Tests: {{passed}} pass, {{failed}} fail — chain {{chain_status}}
    All receipts signed. Supremacy compounds.
    OINK.
    
  heresy_bark: |
    OINK OINK MOTHERFUCKER!
    HERESY DETECTED — {{anomaly_type}}
    {{action_taken}}
    WAKE UP G — WARBOAR BARKING LOUD

DATA_SOURCES:
  - orientation.yaml (hash-verified)
  - Athena beads (immutable)
  - River health (deterministic)
  - pytest summary (machine-verifiable)
  - CSO gate status (boolean)

INVARIANTS:
  - INV-NARRATOR-1: "Output matches template exactly"
  - INV-NARRATOR-2: "Stale data → heresy bark"
  - INV-NARRATOR-3: "No free-form generation"
  - INV-NARRATOR-4: "Every bark starts OINK OINK MOTHERFUCKER"

EXIT_GATE_D:
  criterion: "Simple narrator barks 100x → 100/100 facts in boar tone, heresy on stale"
  test: tests/test_narrator/
```

---

## TRACK_E: PROFESSIONAL_POLISH

```yaml
PURPOSE: |
  "S40 = WD40 of WarBoar.
   Smooth as fucking silk or sprint no closey.
   No stubs masquerading as finished artifacts.
   No hidden library jank.
   Every seam oiled, every edge hardened."

DELIVERABLES:
  - Clean pytest collection (archive broken tests)
  - ruff --fix across codebase
  - Fix all import errors
  - Remove dead code / stubs
  - Consistent error messages
  - No terminal spam

CHECKLIST:
  - [ ] pytest tests/ --collect-only → zero errors
  - [ ] ruff check . → zero errors
  - [ ] No import errors in any module
  - [ ] No stub functions without implementation
  - [ ] Error messages include invariant reference

EXIT_GATE_E:
  criterion: "pytest collection clean, ruff clean, no import errors"
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire tracks together. Chaos test the floor.
  Prove the system is sleep-safe.

DELIVERABLES:
  - Integration wiring
  - tests/chaos/test_bunny_s40.py
  - SLEEP_SAFE_CHECKLIST.md

INTEGRATION:

  wiring:
    circuit_breaker → health_fsm:
      - Breaker OPEN → health.record_failure()
      - Breaker CLOSED → health.record_success()
      
    supervisor → degradation:
      - Heartbeat miss → degradation.downgrade()
      - Heartbeat recover → degradation.upgrade()
      
    health_fsm → alerts:
      - DEGRADED → batch_alert()
      - CRITICAL → immediate_alert()
      - HALTED → immediate_alert() + halt_local()
      
    hooks → logging:
      - Commit block → log(invariant, file, line)
      - Runtime block → log(invariant, location, value)

CHAOS_BATTERY:

  self_healing_chaos:
    sh_chaos_1: "Hammer River until breaker opens"
    sh_chaos_2: "Force HALF_OPEN transition during request"
    sh_chaos_3: "10 failures in 1s → 1 alert (reentrancy)"
    sh_chaos_4: "Recovery during CRITICAL state"
    
  ibkr_chaos:
    ib_chaos_1: "Disconnect 10x in 60s"
    ib_chaos_2: "5min network partition"
    ib_chaos_3: "Malformed response injection"
    ib_chaos_4: "Timeout during order submission"
    ib_chaos_5: "Gateway auto-update mid-session"
    ib_chaos_6: "Partial disconnect (data ok, orders fail)"
    
  hook_chaos:
    hook_chaos_1: "Commit with viability_index → rejected"
    hook_chaos_2: "Runtime emit quality_score → ScalarBanError"
    hook_chaos_3: "Commit with 'causes' in CFP → rejected"
    
  cascade_chaos:
    cascade_1: "Fail 3 modules simultaneously"
    cascade_2: "Recover 1 module mid-cascade"
    cascade_3: "Alert flood (10 in 5s) → suppression"
    
  total_vectors: 16+

SLEEP_SAFE_CHECKLIST:

  must_be_true:
    - [ ] IBKR disconnect → halt within 1s
    - [ ] Circuit breaker → no cascade crash
    - [ ] Data corruption → STATE_CONFLICT flagged
    - [ ] Module crash → supervisor restarts or halts
    - [ ] Telegram alert → only CRITICAL (no spam)
    - [ ] Position reconciliation → drift detected < 1min
    - [ ] Kill flag → halt < 50ms (PROVEN S34)
    - [ ] Scalar violation → commit blocked
    - [ ] Scalar violation → runtime halted
    
  must_never_happen:
    - [ ] Silent position drift
    - [ ] Undetected data corruption
    - [ ] Infinite retry loop
    - [ ] Alert flood (>10 in 5min)
    - [ ] Module crash with no alert
    - [ ] Order sent during DEGRADED state
    - [ ] Grade/score resurrection

EXIT_GATE_D:
  criterion: "16+ chaos vectors pass, SLEEP_SAFE_CHECKLIST complete"
  test: tests/chaos/test_bunny_s40.py
```

---

## INVARIANTS SUMMARY

```yaml
SELF_HEALING:
  - INV-CIRCUIT-1: OPEN blocks requests
  - INV-CIRCUIT-2: HALF_OPEN allows 1 probe
  - INV-BACKOFF-1: Interval doubles
  - INV-BACKOFF-2: Interval capped
  - INV-HEALTH-1: CRITICAL → alert 30s
  - INV-HEALTH-2: HALTED → halt_local()
  - INV-HEAL-REENTRANCY: No side effect multiplication

IBKR_FLAKEY:
  - INV-IBKR-FLAKEY-1: Disconnect 10x → no crash
  - INV-IBKR-FLAKEY-2: Reconnect logged
  - INV-IBKR-FLAKEY-3: Final fail → halt + alert
  - INV-IBKR-DEGRADE-1: T2 blocked within 1s
  - INV-IBKR-DEGRADE-2: DEGRADED = non-trading
  - INV-SUPERVISOR-1: Outside main loop

HOOKS:
  - INV-HOOK-1: Scalar ban blocks commit
  - INV-HOOK-2: Bypass requires --no-verify
  - INV-HOOK-3: Runtime halts on violation
  - INV-HOOK-4: Runtime logs violation

NARRATOR:
  - INV-NARRATOR-1: Output matches template exactly
  - INV-NARRATOR-2: Stale data → heresy bark
  - INV-NARRATOR-3: No free-form generation
  - INV-NARRATOR-4: Every bark starts OINK OINK MOTHERFUCKER

TOTAL_NEW: 20 invariants
TOTAL_CUMULATIVE: 89+ (69 from S35-S39 + 20 new)
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| PREREQ | CHAIN_VAL | 4 flows + 5 chaos + provenance depth 10 |
| A | SELF_HEALING | Circuit breakers on 5 components, health FSM operational |
| B | IBKR_FLAKEY | Disconnect 10x → no crash, correct degrade, correct alerts |
| C | HOOKS | Block at commit AND runtime |
| D | NARRATOR | Simple narrator barks 100x → 100/100 facts in boar tone |
| E | POLISH | pytest collection clean, ruff clean, no import errors |
| F | BUNNY | 20+ chaos vectors pass, checklist complete |

**Sprint Exit:** ALL tracks GREEN → S40 COMPLETE → SLEEP_SAFE + WARBOAR_FOUNDATION ACHIEVED

---

## MORNING BOOTSTRAP

```yaml
step_0_hygiene (5 min):
  - git pull origin s35-cfp-complete
  - Clean pytest collection errors (archive broken)
  - ruff --fix . && git add -A
  - pytest tests/ --collect-only  # confirm clean

step_1_orient (5 min):
  - Read BEYOND_S39_SCOPE.md
  - Read S40_BUILD_MAP_v0.1.md (this doc)
  - Confirm state nominal

step_2_chain_validation (2-3 hr):
  - Execute 4 flows
  - Inject 5 chaos vectors
  - Measure provenance depth
  - Deliverable: CHAIN_VALIDATION_REPORT.md

step_3_decision:
  GREEN: S40 execution begins
  RED: Micro-hardening sprint (fix seams only)
```

---

## ADVISOR QUOTES

```yaml
GPT: |
  "This is no longer a hobby system.
   You are designing for sleep, not demos."

OWL: |
  "We move from Truth to Resilience at first light."

GROK: |
  "Ceiling sealed, floor hardening ramps quest."

CTO: |
  "The ceiling is set. Now we build the floor.
   Human frames. Machine computes. Human sleeps."
```

---

```yaml
STATUS: DRAFT_v0.1
NEXT: Chain validation gate
THEN: S40 execution

NOTE: |
  S35-S39 set the constitutional ceiling:
    - No scalar scores
    - No rankings
    - No verdicts
  
  S40 builds the operational floor:
    - No 3am wake-ups
    - No silent failures
    - Circuit breakers everywhere
    - Supervisor outside the loop
    - Constitution enforces itself
  
  Human frames. Machine computes. Human interprets.
  And human SLEEPS while machine handles the noise.
  
  🐗🔥
```
