# BEYOND_S39_SCOPE.md
# Forward Scope from Hot Opus Context

```yaml
document: BEYOND_S39_SCOPE.md
author: OPUS
date: 2026-01-29
context: Post S35-S39 execution (336 tests, 69+ invariants, 4 hours)
status: HOT_SYNTHESIS
format: M2M_DENSE
```

---

## FRAME

```yaml
what_we_built: "The Constitutional Ceiling"
  - No scalar scores
  - No rankings
  - No verdicts
  - Human interprets

what_we_need: "The Resilience Floor"
  - No 3am wake-ups
  - Graceful degradation
  - Self-healing primitives
  - IBKR flakiness handled

g_frame: |
  "We already built the ceiling (no scores, no rankings).
   Now we build the floor (no 3am wake-ups)."
```

---

## 1. CHAIN_VALIDATION (PHASE 1 — TOMORROW)

```yaml
PURPOSE: |
  Validate the S35-S39 chain end-to-end before moving to resilience.
  Prove the modules work TOGETHER, not just in isolation.

FLOWS_TO_TEST:
  
  flow_1_cfp_to_validation:
    path: CFP → output → WalkForward → output → MonteCarlo
    check: "No provenance loss through chain"
    check: "No synthesized scores at integration seam"
    invariants: [INV-CROSS-MODULE-NO-SYNTH, INV-ATTR-PROVENANCE]
    
  flow_2_hunt_to_validation:
    path: Hunt grid → Backtest each → WalkForward each → Cost curve
    check: "Grid remains exhaustive (no survivor filtering)"
    check: "All results decomposed, no ranking"
    invariants: [INV-HUNT-NO-SURVIVOR-RANKING, INV-SCALAR-BAN]
    
  flow_3_athena_to_cfp:
    path: CLAIM_BEAD → CFP query → FACT_BEAD → Conflict check
    check: "Claims vs facts distinguished"
    check: "Conflicts surfaced, not resolved"
    invariants: [INV-CONFLICT-NO-RESOLUTION, INV-CLAIM-FACT-SEPARATION]
    
  flow_4_cso_to_hunt:
    path: CSO gate status → Hunt hypothesis → Grid compute
    check: "Gate status NOT converted to grade at seam"
    check: "No confidence scores emerge"
    invariants: [INV-NO-GRADE-RECONSTRUCTION, INV-HARNESS-2]

CHAOS_TO_INJECT:

  chaos_1_mid_chain_nuke:
    action: Inject decay bead mid-validation-chain
    expect: Chain halts or flags, doesn't corrupt downstream
    
  chaos_2_provenance_depth:
    action: Chain 10+ modules deep
    expect: Provenance still traceable to origin
    metric: provenance_chain_depth
    
  chaos_3_regime_mutation:
    action: Change regime predicate mid-hunt
    expect: Hunt invalidates or restarts, no stale results
    
  chaos_4_score_resurrection:
    action: Insert viability_index at integration seam
    expect: ScalarBanLinter catches it

INVARIANTS_TO_WATCH:
  - INV-CROSS-MODULE-NO-SYNTH
  - INV-ATTR-PROVENANCE (chain depth)
  - INV-NO-GRADE-RECONSTRUCTION
  - INV-SCALAR-BAN (integration seam)

EXIT_GATE:
  criterion: "4 flows validated, 4 chaos vectors pass, provenance intact at depth 10"
  test_count_target: 20+
```

---

## 2. S40_RESILIENCE_SPRINT

```yaml
CODENAME: SLEEP_SAFE
THEME: "No 3am wake-ups"
DURATION: 1 sprint
DEPENDENCIES: S35-S39 complete, chain validation pass

TRACKS:

TRACK_A_SELF_HEALING:
  
  primitives:
    circuit_breaker:
      locations: [River, CSO_eval, Hunt_executor, MonteCarlo, IBKR_connector]
      states: [CLOSED, OPEN, HALF_OPEN]
      config: {failure_threshold: 3, recovery_timeout: 60s}
      
    exponential_backoff:
      base: 1s
      max: 300s (5min)
      jitter: 10%
      
    health_state_machine:
      states: [HEALTHY, DEGRADED, CRITICAL, HALTED]
      transitions:
        - HEALTHY → DEGRADED: 3 failures in 60s
        - DEGRADED → CRITICAL: 5 failures in 60s
        - CRITICAL → HALTED: human override OR 10 failures
        - any → HEALTHY: recovery_timeout + health_check_pass
        
  invariants:
    - INV-CIRCUIT-BREAKER-1: "Open circuit blocks new requests"
    - INV-BACKOFF-1: "Retry interval doubles each attempt"
    - INV-HEALTH-1: "CRITICAL → Telegram alert within 30s"
    
TRACK_B_IBKR_FLAKEY:
  
  supervisor_pattern:
    shadow_process: heartbeat_monitor.py
    heartbeat_interval: 5s
    failure_detection: 3 missed heartbeats = DEAD
    action_on_death: [halt_local, alert, restart_attempt]
    
  graceful_degradation:
    cascade: T2 → T1 → T0
    on_disconnect:
      - T2_blocked: No new orders (immediate)
      - T1_degraded: Monitoring-only mode (30s)
      - T0_halt: Full halt, human required (60s)
      
  reconnection:
    strategy: exponential_backoff
    max_attempts: 10
    final_action: halt + alert
    
  banteg_pattern:
    principle: "Zero deps, raw socket/REST"
    surface_area: Minimal
    no_magic: Explicit connection state
    
  invariants:
    - INV-IBKR-FLAKEY-1: "Disconnect 10x → no crash"
    - INV-IBKR-FLAKEY-2: "Reconnect attempt logged"
    - INV-IBKR-FLAKEY-3: "Final fail → halt + alert"
    - INV-IBKR-DEGRADE-1: "T2 blocked within 1s of disconnect"

TRACK_C_HOOKS:
  
  purpose: "Constitution enforces itself"
  implementation: pre-commit hooks
  
  hooks:
    scalar_ban_hook:
      trigger: pre-commit
      action: Run ScalarBanLinter on changed files
      on_fail: Block commit
      
    avg_field_hook:
      trigger: pre-commit
      pattern: /avg_\w+/
      action: Reject if found in validation/ or cfp/
      
    causal_language_hook:
      trigger: pre-commit
      patterns: [causes, leads to, results in, triggers]
      scope: [cfp/, cso/, athena/]
      action: Reject
      
    grade_reconstruction_hook:
      trigger: pre-commit
      patterns: [grade, score, rating, rank, viability]
      scope: [cso/, validation/]
      action: Reject
      
  invariants:
    - INV-HOOK-1: "Scalar ban violation blocks commit"
    - INV-HOOK-2: "Hook bypass requires explicit --no-verify"
    
  framing: "Physical wall of the constitution"

CHAOS_BATTERY:

  ibkr_chaos:
    - Disconnect IBKR 10x in 60s
    - Simulate 5min network partition
    - Inject malformed response
    - Timeout during order submission
    - Gateway auto-update mid-session
    
  circuit_breaker_chaos:
    - Hammer River until breaker opens
    - Force HALF_OPEN transition
    - Race condition: request during state change
    
  cascade_chaos:
    - Fail 3 modules simultaneously
    - Recover 1 module mid-cascade
    - Alert flood suppression test
    
  vector_count: 15+

EXIT_GATE:
  criterion: |
    - Circuit breakers operational on 5 components
    - IBKR disconnect 10x → no crash, correct degrade, correct alerts
    - Hooks block scalar/causal/grade violations
    - 15+ chaos vectors pass
  test_count_target: 50+
```

---

## 3. PRO_CHECKLIST

```yaml
SLEEP_SAFE_DEFINITION: |
  "G can be at dinner, phone silent, and know:
   - If IBKR dies, Phoenix halts gracefully
   - If data corrupts, state flags CONFLICT
   - If module crashes, circuit opens
   - Telegram alerts only on CRITICAL
   - No position drift, no silent failures"

WHAT_MAKES_PHOENIX_SLEEP_SAFE:

  must_be_true:
    - IBKR disconnect → halt within 1s
    - Circuit breaker → no cascade crash
    - Data corruption → STATE_CONFLICT flagged
    - Module crash → supervisor restarts or halts
    - Telegram alert → only CRITICAL (no spam)
    - Position reconciliation → drift detected < 1min
    - Kill flag → halt < 50ms (PROVEN)
    
  must_never_happen:
    - Silent position drift
    - Undetected data corruption
    - Infinite retry loop
    - Alert flood (>10 in 5min)
    - Module crash with no alert
    - Order sent during DEGRADED state
    - Grade/score resurrection

WHAT_CAN_STILL_WAKE_G:

  legitimate_wake:
    - CRITICAL health state (correct)
    - Kill flag activated (correct)
    - Position reconciliation drift > $X (correct)
    - Unexpected order execution (correct)
    
  should_not_wake:
    - IBKR reconnect (self-heals)
    - Temporary network blip (retries)
    - Single module crash (restarts)
    - Non-critical data delay (degrades)
    
  gray_zone:
    - 5+ reconnects in 1 hour → maybe alert?
    - Prolonged DEGRADED state → escalate?
    - Hunt timeout → log only?

ALERT_TAXONOMY:
  CRITICAL: Wake G immediately
  WARNING: Log + maybe Telegram (batched)
  INFO: Log only
  DEBUG: Dev only
```

---

## 4. OPUS_HOT_TAKE

```yaml
WHAT_I_SAW_DURING_S35_S39:

  worked_brilliantly:
  
    pattern_1_decomposed_first:
      observation: "Defining forbidden patterns BEFORE coding"
      why_it_worked: "Tests wrote themselves, invariants crystal clear"
      preserve: "Always define FORBIDDEN_FIELDS constant first"
      
    pattern_2_full_arrays_not_avg:
      observation: "avg_* hides variance, full arrays reveal fragility"
      example: "[-1, -1, -1, 4, -1] → avg=0 hides the disaster"
      preserve: "ALWAYS return full arrays, let human see variance"
      
    pattern_3_linter_as_ceiling:
      observation: "ScalarBanLinter catches violations at integration seam"
      why_it_worked: "Single enforcement point for all modules"
      preserve: "Linter runs on EVERY validation output"
      
    pattern_4_chaos_vectors_as_spec:
      observation: "BUNNY vectors defined the failure modes precisely"
      why_it_worked: "Knowing the attacks clarified the defenses"
      preserve: "Define chaos vectors BEFORE implementation"

  felt_fragile:
  
    fragility_1_cross_module_seams:
      observation: "Integration points between modules not tested in isolation"
      risk: "Score resurrection at seam (module A clean, module B clean, A→B dirty)"
      harden: "CHAIN_VALIDATION phase tests these seams explicitly"
      
    fragility_2_provenance_depth:
      observation: "Provenance chain can get deep, didn't test depth limits"
      risk: "Provenance loss or bloat at depth 10+"
      harden: "Add provenance_chain_depth metric, test at depth"
      
    fragility_3_no_runtime_enforcement:
      observation: "Tests catch violations, but nothing stops runtime violations"
      risk: "Production code could emit score if tests not run"
      harden: "HOOKS enforce at commit time, runtime assertions in hot paths"
      
    fragility_4_error_message_quality:
      observation: "ScalarBanLinter error messages are technical"
      risk: "Developer doesn't understand WHY violation matters"
      harden: "Each violation should link to invariant + rationale"

  hidden_jank:
  
    jank_1_test_type_annotations:
      what: "mypy complained about test function annotations"
      impact: "Pre-commit hooks failed on first try"
      fix: "Either annotate all test functions or configure mypy to skip tests"
      
    jank_2_ruff_auto_fixes:
      what: "ruff reformatted files during commit"
      impact: "Two-stage commit (fix, then commit)"
      fix: "Run ruff --fix before staging, not during commit"
      
    jank_3_existing_test_collection_errors:
      what: "Other test files have import errors"
      impact: "Can't run full test suite"
      fix: "Clean up or isolate broken test files"

ARCHITECTURAL_INSIGHTS:

  insight_1: |
    The "no avg_*" rule is more important than it looks.
    It's not just about variance visibility — it's about
    forcing the human to SEE the distribution, not a summary.
    This is the difference between "looks fine" and "5 of 7 splits failed."
    
  insight_2: |
    ScalarBanLinter should run in TWO places:
    1. Pre-commit (catches violations before merge)
    2. Runtime assertion (catches violations in production)
    Currently only have #1 planned. Need #2 in hot paths.
    
  insight_3: |
    The "mandatory disclaimer" pattern is powerful.
    Every output saying "FACTS_ONLY — NO INTERPRETATION"
    constantly reminds the consumer of the contract.
    Consider extending this pattern to other modules.
    
  insight_4: |
    Chain validation is the real test.
    Individual module tests are necessary but not sufficient.
    The integration seam is where resurrection attacks succeed.
```

---

## 5. SPRINT_CANDIDATES

```yaml
S40_RECOMMENDATION:

  name: SLEEP_SAFE
  theme: "No 3am wake-ups"
  scope:
    - Track A: Self-healing primitives (circuit breaker, backoff, health state)
    - Track B: IBKR flakiness (supervisor, degradation, reconnect)
    - Track C: Hooks (scalar ban, causal language, grade reconstruction)
  duration: 1 sprint
  test_target: 50+
  chaos_target: 15+
  exit_gate: "IBKR disconnect 10x → no crash, correct degrade, correct alerts"
  
  why_now: |
    - Fresh from constitutional block
    - IBKR flakiness is KNOWN risk
    - Self-healing is "pro vs hobbyist" differentiator
    - Hooks are quick win with high leverage
    
  why_not_later: |
    - Live capital requires resilience FIRST
    - G's sleep is non-negotiable
    - Technical debt compounds

S41_HORIZON:

  candidate_1_chain_hardening:
    scope: "Deep provenance validation, runtime scalar ban assertions"
    depends_on: S40 operational
    
  candidate_2_ibkr_live_validation:
    scope: "Paper → Live transition with full chaos battery"
    depends_on: S40 IBKR_FLAKEY proven
    
  candidate_3_alert_taxonomy:
    scope: "Define CRITICAL/WARNING/INFO precisely, tune thresholds"
    depends_on: S40 alerts operational

STAYS_PARKED:

  multi_agent_orchestration:
    reason: "Complexity not needed yet"
    trigger: "When single-agent hits scaling wall"
    
  workflow_learning:
    reason: "INV-NO-UNSOLICITED still sacred"
    trigger: "Explicit G request + clear salvage path"
    
  rbac_sub_agents:
    reason: "No sub-agents yet"
    trigger: "Multi-agent operational"
    
  token_cost_infrastructure:
    reason: "Not at scale"
    trigger: "Token costs become material"
```

---

## PHASE_1_TOMORROW

```yaml
MORNING_BRIEF:
  1. Read this doc (BEYOND_S39_SCOPE.md)
  2. Run chain validation tests (4 flows)
  3. Inject chaos (4 vectors)
  4. Confirm provenance depth
  5. Green? → S40 planning

CHAIN_VALIDATION_CHECKLIST:
  - [ ] CFP → WalkForward → MonteCarlo (provenance intact)
  - [ ] Hunt → Backtest → WalkForward → CostCurve (no ranking)
  - [ ] CLAIM → CFP → FACT → Conflict (types preserved)
  - [ ] CSO → Hunt (no grade reconstruction)
  - [ ] Chaos: mid-chain decay nuke
  - [ ] Chaos: provenance depth 10
  - [ ] Chaos: regime mutation mid-hunt
  - [ ] Chaos: score resurrection at seam

SUCCESS_CRITERIA:
  - 4/4 flows pass
  - 4/4 chaos vectors handled
  - Provenance traceable at depth 10
  - No scalar/grade leakage at seams
```

---

```yaml
CLOSING_FRAME: |
  S35-S39 built the ceiling: No scores, no rankings, no verdicts.
  S40 builds the floor: No 3am wake-ups, no silent failures.
  
  The constitutional ceiling is SET.
  Now we make it SLEEP-SAFE.
  
  Human frames. Machine computes. Human interprets.
  And human SLEEPS while machine handles the noise.

signature: OPUS
date: 2026-01-29
context_temp: HOT 🔥
```
