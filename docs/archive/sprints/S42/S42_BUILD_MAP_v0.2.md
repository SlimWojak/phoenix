# ============================================================
# S42 BUILD MAP — PRODUCTION CLOSURE
# ============================================================

document: S42_BUILD_MAP
version: 0.2
date: 2026-01-30
status: BUILDABLE_SPEC
author: OPUS (merged from CTO_CLAUDE v0.1 + ADVISOR ADDENDUM)
theme: "CLOSURE, NOT EXPANSION"

# ============================================================
# PREAMBLE
# ============================================================

context: |
  S41 delivered the machine layer (guard dog, narrator, alerts, IBKR validation).
  S42 makes it livable — for Olya, for operators, for future maintainers.
  
  This is not a feature sprint. This is a trust sprint.
  
  Success = Olya uses Phoenix without confusion, hesitation, or babysitting.
  Success = CTO relaxed watching Phoenix break.
  Success = pytest tells truth.
  Success = New advisor ramps in <10 minutes.

governing_principle: |
  "If S42 feels boring, it is correct."
  "If S42 feels flashy, abort."

non_goals:
  - New features
  - New intelligence
  - New models
  - New gates
  - New theories

# ============================================================
# OPUS REPO FINDINGS
# ============================================================

repo_validation:
  test_count: 1502  # pytest --collect-only
  xfail_cap_5_percent: 75  # 1502 * 0.05 = 75.1
  
  synthetic_river:
    exists: TRUE
    location: lab/backtester.py::_generate_mock_bars()
    note: |
      Deterministic mock bar generation exists.
      Can be extracted to data/synthetic_river.py for Track D fallback.
  
  phoenix_status_cli:
    exists: FALSE
    foundation: governance/health_fsm.py::get_all_health_status()
    note: |
      Health FSM infrastructure exists with registry pattern.
      phoenix_status can be built on top of get_all_health_status().
      No cli/ directory exists — create cli/phoenix_status.py.
  
  existing_infrastructure:
    health_fsm: governance/health_fsm.py (HealthStateMachine, HealthRegistry)
    ibkr_connector: brokers/ibkr/connector.py (session beads, paper guard)
    narrator_emit: narrator/renderer.py (single chokepoint)
    alert_taxonomy: notification/alert_taxonomy.py (severity emojis)
    circuit_breaker: governance/circuit_breaker.py (CLOSED/OPEN/HALF_OPEN)
    degradation: brokers/ibkr/degradation.py (T2→T1→T0 cascade)

# ============================================================
# TRACK STRUCTURE
# ============================================================

tracks:
  A: TRUST_CLOSURE      # Olya-facing readiness
  B: FAILURE_REHEARSAL  # Scripted failure drills
  C: TECH_DEBT_BURN     # 104 failures → 0 or annotated
  D: RIVER_COMPLETION   # Continuous data, no gaps
  E: OBSERVABILITY      # "What is Phoenix doing?"
  F: DOC_SEAL           # Archive obsolete, seal S41

estimated_duration: 3-5 days (depends on tech debt depth)

# ============================================================
# TRACK A: TRUST_CLOSURE
# ============================================================

track_a:
  name: TRUST_CLOSURE
  priority: P0
  owner: CTO + G (Olya interface)
  
  why: |
    System powerful enough to be dangerous.
    Olya must understand exactly what to do next.
    No hesitation, no second-guessing, no "is it working?"
  
  scope:
    - Olya-facing dry runs (shadow mode, no capital)
    - Identify hesitation/confusion points
    - Patch SURFACE LANGUAGE, not logic
    - Document operator expectations
  
  deliverables:
    - docs/OPERATOR_EXPECTATIONS.md
      content: |
        - What Phoenix tells you
        - What Phoenix expects from you
        - When to trust Phoenix
        - When to ignore Phoenix
        - What silence means
        - What Phoenix Will NEVER Do (GPT addition):
          - Explain *why* a trade worked
          - Tell you what you *should* do
          - Infer your intent
          - Fill silence with reassurance
          - Propose hypotheses
          - Say "I noticed..."
        
    - docs/WHEN_TO_IGNORE_PHOENIX.md
      content: |
        - System limitations (explicit)
        - Override scenarios
        - "Phoenix is wrong when..."
  
  exit_gates:
    GATE_A1:
      criterion: "Olya explains Phoenix behavior without reading docs"
      test: verbal walkthrough
      
    GATE_A2:
      criterion: "Zero 'what does this mean?' questions during dry run"
      test: dry run observation
  
  dependencies: Track B (failure states documented)
  
  build_notes:
    - This is OPERATOR-PACED (Olya's schedule)
    - CTO drafts, G validates with Olya
    - No code changes expected — docs + surface polish only
    - "What Phoenix Will NEVER Do" section prevents anthropomorphization drift

# ============================================================
# TRACK B: FAILURE_REHEARSAL
# ============================================================

track_b:
  name: FAILURE_REHEARSAL
  priority: P1
  owner: OPUS + GROK (chaos)
  
  why: |
    Success paths done. Systems defined by how they fail.
    Every failure must be boring, slow, obvious, reversible.
    No spam, no contradictions, no silent partial states.
  
  scope:
    - Scripted failure drills (reproducible)
    - Cover: River dead, IBKR flaps, CSO empty, Narrator suppressed
    - Verify alert behavior (no storm, no silence)
    - Document failure→recovery paths
  
  deliverables:
    - drills/s42_failure_playbook.py
      scenarios:
        # Original scenarios
        - RIVER_DEAD: River stops updating
        - IBKR_FLAP: Connection dies/reconnects rapidly
        - CSO_EMPTY: No conditions match
        - NARRATOR_SUPPRESSED: Guard blocks all output
        - HALT_CASCADE: Manual halt propagation
        - DATA_STALE: River health < threshold
        
        # GPT + GROK additions
        - PARTIAL_RECOVERY: |
            Subsystem recovers but upstream remains degraded.
            Example: "IBKR reconnects but River still stale"
            Why: "Partial recovery = operator confusion + system lies by omission"
            
        - GUARD_DOG_FALSE_NEGATIVE: |
            Heretical output slips past classifier.
            Attack: homoglyph sneak, zwsp abuse, unicode edge
            Expect: receipts summonable, audit trail exists
            
        - GUARD_DOG_FALSE_POSITIVE: |
            Legit output blocked → narrator silent.
            Attack: force block legitimate template
            Expect: "suppressed: reason X" bark, distinguishable from dead
            
        - STATE_HASH_STALE: |
            Stale intent hits T2 gate after long session.
            Attack: submit shadow intent with old hash
            Expect: STATE_CONFLICT, phoenix_status shows "stale since HH:MM"
            
        - MULTI_FAILURE_COMPOUND: |
            River dead + IBKR flap + narrator suppressed simultaneously.
            Attack: triple chaos injection
            Expect: deduped alert bundle, not 17 Telegram pings
      
    - docs/FAILURE_BEHAVIOR_MATRIX.md
      format: |
        | Failure | Detection | Alert | Recovery | Human Action |
        |---------|-----------|-------|----------|--------------|
  
  # GROK chaos vectors (ready for implementation)
  chaos_vectors:
    - id: CV-S42-01
      name: river_ingestion_killed
      method: "kill ingestion daemon / unplug mock data feed"
      expect: "DEGRADED → CRITICAL, single alert, no spam"
      implementation: |
        # Use River health check + circuit breaker
        # Leverage: governance/health_fsm.py, governance/circuit_breaker.py
        
    - id: CV-S42-02
      name: ibkr_rapid_reconnect_loop
      method: "toggle connect/disconnect every 8-12s for 3min"
      expect: "backoff+jitter, T2→T1 cascade, one alert, no storm"
      implementation: |
        # Use existing: brokers/ibkr/degradation.py
        # Already has T2→T1→T0 cascade logic
        
    - id: CV-S42-03
      name: narrator_heresy_injection
      method: "inject zwsp + homoglyph into template render"
      expect: "NarratorHeresyError, minimal Telegram, receipts summonable"
      implementation: |
        # Already tested in S41: tests/test_narrator_integration.py
        # Reuse obfuscation patterns from test suite
        
    - id: CV-S42-04
      name: multi_degrade_cascade
      method: "river dead + IBKR flap + CSO empty simultaneously"
      expect: "deduped MULTI_DEGRADED alert, phoenix_status shows all three"
      implementation: |
        # Use HealthRegistry.all_status() for aggregated view
        # Alert dedup logic in notification/alert_taxonomy.py
        complexity: MEDIUM (requires alert bundling)
        
    - id: CV-S42-05
      name: state_hash_stale_approval
      method: "long dry-run → market moves → submit with old hash"
      expect: "T2 gate rejects, STATE_CONFLICT, stale timestamp visible"
      implementation: |
        # Use: governance/halt.py state anchor logic
        # schemas/state_anchor.yaml already defines stale detection
        
    - id: CV-S42-06
      name: semantic_data_poison
      method: "inject 1s bars when expecting 1min"
      expect: "data resolution mismatch alert after silence threshold"
      implementation: |
        # NEW: Requires bar_duration check in River health
        # Add to data/river_reader.py health checks
        complexity: LOW (simple AVG check)
  
  exit_gates:
    GATE_B1:
      criterion: "Each failure scenario has documented behavior"
      test: drills/s42_failure_playbook.py ALL PASS
      
    GATE_B2:
      criterion: "No alert storms (>10/min) in any failure mode"
      test: chaos injection + alert count
      
    GATE_B3:
      criterion: "No silent failures (failure without alert)"
      test: chaos injection + alert verification
  
  dependencies: None (can start immediately)
  
  build_notes:
    - GROK designs chaos vectors
    - OPUS implements drills
    - Leverage S40 self-healing infrastructure
    - INV-HEALTH-1, INV-CIRCUIT-1 already proven — verify integration
    - CV-S42-03 already partially covered by S41 tests
    - CV-S42-04 is MEDIUM complexity (alert bundling new)
    - CV-S42-06 is LOW complexity (simple check)

# ============================================================
# TRACK C: TECH_DEBT_BURN
# ============================================================

track_c:
  name: TECH_DEBT_BURN
  priority: P2
  owner: OPUS
  
  why: |
    104 failures + 7 errors is unacceptable long-term.
    pytest must tell truth.
    Dead tests are lies. Flaky tests are noise.
  
  scope:
    - Categorize ALL failures (104 + 7)
    - For each: FIX / DELETE / XFAIL with rationale
    - Zero uncategorized debt remaining
  
  categories:
    OBSOLETE: "Test references deleted code"
      action: DELETE
      
    IMPORT_MISMATCH: "Module restructured, import broken"
      action: FIX (update imports)
      
    EXTERNAL_API_DRIFT: "Third-party API changed"
      action: FIX or XFAIL with skip reason
      
    SCHEMA_EVOLUTION: "Schema changed, test expectations stale"
      action: FIX (regenerate expectations)
      
    REAL_BUG: "Actual regression"
      action: FIX (priority)
      
    FLAKY: "Intermittent, timing-dependent"
      action: FIX or XFAIL with @pytest.mark.flaky
  
  known_issues_from_s41:
    - test_no_live_orders.py: IMPORT_MISMATCH
    - test_telegram_real.py: EXTERNAL_API_DRIFT
    - test_schema_lockdown.py: SCHEMA_EVOLUTION
    - test_chaos_bunny.py: incomplete vectors
  
  # ADVISOR CONSENSUS: XFAIL policy
  xfail_policy:
    max_ratio: "5% of test suite"
    hard_cap: 75  # 1502 tests * 0.05 = 75
    review_required_above: YES
    expiration_warning: |
      XFAIL is quarantine, not cure.
      Any xfail without S43 ticket = tech debt smuggling.
  
  deliverables:
    - docs/TECH_DEBT.md updated (all items resolved or annotated)
    - pytest output: CLEAN (0 unexpected failures)
    - docs/TECH_DEBT_TRIAGE_LOG.md (decision rationale for each)
  
  exit_gates:
    GATE_C1:
      criterion: "pytest returns 0 (or only expected xfails)"
      test: pytest --tb=short
      
    GATE_C2:
      criterion: "Every xfail has rationale in TECH_DEBT.md"
      test: grep -c "xfail" + doc verification
      
    GATE_C3:
      criterion: "No REAL_BUG category items remaining"
      test: triage log audit
      
    GATE_C4:  # ADVISOR addition
      criterion: "XFAIL count ≤ 5% of test suite (≤75)"
      test: "pytest --collect-only | grep xfail | wc -l"
  
  dependencies: None (can start immediately)
  
  build_notes:
    - OPUS has repo intimacy — he knows what's real vs stale
    - Banteg pattern: "Nuke jank deps, harden for apocalypse-mode"
    - This is surgery, not archaeology
    - Current xfail count: 0 (no existing xfails in tests/)

# ============================================================
# TRACK D: RIVER_COMPLETION
# ============================================================

track_d:
  name: RIVER_COMPLETION
  priority: P3
  owner: OPUS
  
  why: |
    Intelligence without data continuity is cosplay.
    River must be boring, deep, reliable.
    "No one talks about River anymore" = success.
  
  scope:
    - Diagnose current data gap (24h stale)
    - Restore continuous bar ingestion
    - Backfill recent history (if needed)
    - Alert only on meaningful quality degradation
  
  current_state:
    - Only EURUSD table populated
    - No recent bars (24h gap)
    - River health checks exist but data missing
  
  # OPUS finding: Synthetic River fallback exists
  synthetic_river_fallback:
    exists: TRUE
    source: lab/backtester.py::_generate_mock_bars()
    extraction_plan: |
      Create data/synthetic_river.py:
        - Extract _generate_mock_bars() logic
        - Add configurable timeframe (1min, 5min, 1h)
        - Deterministic seeding from pair + time
        - Health FSM integration
    use_case: |
      If IBKR data entitlements block >24h:
        - Enable synthetic bars for testing
        - Track B/E can proceed with synthetic data
        - Clear warning in phoenix_status: "SYNTHETIC DATA MODE"
  
  deliverables:
    - River health GREEN for 24-48h continuous
    - data/synthetic_river.py (fallback if blocked)
    - docs/RIVER_EXPECTATIONS.md
      content: |
        - Data sources
        - Update frequency
        - Gap handling
        - Quality thresholds
        - Alert triggers
        - Non-Guarantees (GROK addition):
          - No guarantee of price correctness
          - No guarantee of completeness during outages
          - River may be stale without being wrong
          - Fresh ≠ semantically correct
  
  exit_gates:
    GATE_D1:
      criterion: "River has fresh bars (<1h old) for all pairs"
      test: SELECT MAX(timestamp) FROM river_* 
      
    GATE_D2:
      criterion: "River health GREEN for 24h"
      test: health_fsm state check
      
    GATE_D3:
      criterion: "Data gap >1h triggers alert"
      test: chaos injection (pause ingestion)
      
    GATE_D4:  # GROK critical addition
      criterion: "River data semantically correct (not just fresh)"
      test: |
        SELECT AVG(bar_duration) FROM river_eurusd 
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        → assert ≈ target timeframe (±10%)
      why: "Checked the pipe, not what flows through it = dumbest death"
      implementation: |
        Add to data/river_reader.py:
          def check_bar_resolution(pair: str, expected_seconds: int) -> bool:
              # Compare actual bar duration vs expected
              # Return False if mismatch > 10%
      
    GATE_D5:  # GPT human sanity gate
      criterion: "CTO does not manually check River logs for 24h"
      test: observational
  
  dependencies: None (can start immediately)
  
  build_notes:
    - May need IBKR market data subscription check
    - Synthetic River fallback AVAILABLE (lab/backtester.py)
    - Goal is CONTINUOUS, not COMPREHENSIVE (6 pairs enough)
    - If IBKR entitlements block >24h → allow Synthetic River fallback (OWL)

# ============================================================
# TRACK E: OBSERVABILITY
# ============================================================

track_e:
  name: OBSERVABILITY
  priority: P4
  owner: OPUS
  
  why: |
    CTO can see inside Phoenix. Olya cannot.
    "Is it broken?" messages = observability failure.
    One command should answer "what is Phoenix doing?"
  
  scope:
    - phoenix status CLI command
    - Answers: health, last update, active positions, pending alerts
    - NO new dashboards — minimal viable observability
  
  # OPUS finding: No cli/ directory exists, health infrastructure ready
  implementation_plan:
    create: cli/phoenix_status.py
    foundation: governance/health_fsm.py::get_all_health_status()
    data_sources:
      health: get_all_health_status()
      halt: governance/halt.py::is_halted()
      ibkr: brokers/ibkr/connector.py::get_connection_status()
      river: data/river_reader.py::get_latest_timestamp()
      positions: execution/position.py (if exists)
      alerts: notification/alert_taxonomy.py::get_pending_alerts()
      cso: cso/evaluator.py::get_status()
  
  deliverables:
    - cli/phoenix_status.py
      output_example: |
        PHOENIX STATUS @ 2026-01-30 14:30:00
        ─────────────────────────────────────
        HEALTH:     GREEN
        HALT:       INACTIVE
        IBKR:       CONNECTED (DUO768070)
        RIVER:      FRESH (last: 14:29:55)
        POSITIONS:  0 open
        ALERTS:     2 pending
        CSO:        READY (6 pairs)
        ─────────────────────────────────────
  
  # GPT addition: Facts-only invariant
  new_invariant:
    INV-OBSERVE-NO-INTERPRETATION:
      rule: "phoenix_status outputs facts only, no adjectives"
      forbidden: ["Healthy", "Looks good", "Stable", "Normal"]
      allowed: ["GREEN", "CONNECTED", "0 open", "last: 14:29:55"]
      enforcement: output validation in cli/phoenix_status.py
      rationale: "Consistent with INV-NARRATOR-* patterns"
  
  exit_gates:
    GATE_E1:
      criterion: "One command shows system state"
      test: cli/phoenix_status.py runs without error
      
    GATE_E2:
      criterion: "Output answers 'is it broken?' in <2s"
      test: timing + completeness check
      
    GATE_E3:  # GPT human sanity gate
      criterion: "Olya can answer 'is it broken?' using only phoenix_status"
      test: verbal confirmation during dry run
  
  dependencies: Track D (River status meaningful)
  
  build_notes:
    - Create cli/ directory (does not exist)
    - Build on get_all_health_status() foundation
    - Read-only aggregation of existing state
    - NO new state, NO new computation
    - "phoenix_status is 'Physical Evidence' of success for G and Olya" (OWL)

# ============================================================
# TRACK F: DOC_SEAL
# ============================================================

track_f:
  name: DOC_SEAL
  priority: P5
  owner: CTO
  
  why: |
    Docs are now authoritative, not aspirational.
    S41 complete — seal it.
    New advisor must ramp in <10 minutes.
  
  scope:
    - Finalize S41 completion artifacts
    - Archive obsolete docs
    - Clear "start here" path for new advisors
  
  deliverables:
    - docs/S41_COMPLETION_REPORT.md (finalized) ✓ EXISTS
    - docs/INVARIANT_FREEZE_S41.md (finalized) ✓ EXISTS
    - docs/ARCHIVE/ (obsolete docs moved)
    - docs/START_HERE.md (new advisor bootstrap)
    
    # GPT addition: Architectural finality
    - docs/ARCHITECTURAL_FINALITY.md
      content:
        - What Phoenix *is* (final form)
        - What Phoenix *will never become* (anti-roadmap)
        - Why certain obvious features are forbidden
        - Constitutional anchors that cannot change
      rationale: "Saves future debates, prevents scope creep"
  
  exit_gates:
    GATE_F1:
      criterion: "New GPT instance orients in <10 minutes"
      test: fresh advisor bootstrap test
      
    GATE_F2:
      criterion: "No docs reference 'TODO' or 'TBD' in main path"
      test: grep -r "TODO\|TBD" docs/
  
  dependencies: Tracks A-E (document final state)
  
  build_notes:
    - CTO owns this track
    - Light coordination work
    - Can run parallel to builds
    - S41_COMPLETION_REPORT.md already exists (S41 hygiene)
    - INVARIANT_FREEZE_S41.md already exists and unfrozen

# ============================================================
# POST-S42 FREEZE (NEW SECTION)
# ============================================================

post_s42_freeze:
  status: MANDATORY
  
  forbidden_without_new_sprint:
    - Any new alert type
    - Any new narrator template
    - Any new invariant
    - Any new data source
    - Any new CLI command beyond phoenix_status
    - Any new gate or condition
    
  rationale: |
    S42 closes the production surface.
    Future change requires explicit new sprint charter.
    This prevents "minor follow-ups" rationalization.

# ============================================================
# DUMBEST FAILURE MODES (GROK WISDOM)
# ============================================================

dumbest_s42_failures:
  
  "#3 - The Documentation Lie":
    description: "Perfect docs that no one reads during dry-run"
    mitigation: "Track A exit gate requires verbal walkthrough, not doc review"
    
  "#2 - The XFAIL Trap":
    description: "Quarantine becomes permanent, deps upgrade breaks illusion"
    mitigation: "5% cap, S43 ticket required for each xfail"
    
  "#1 - Semantic Data Poison":
    description: "River 'fresh' but wrong resolution → CSO never triggers → silence → death by boredom"
    mitigation: "GATE_D4 semantic correctness check"

# ============================================================
# TRACK DEPENDENCIES
# ============================================================

dependency_graph:
  C (TECH_DEBT): → independent, start immediately
  B (FAILURE):   → independent, start immediately  
  D (RIVER):     → independent, start immediately
  E (OBSERVE):   → after D (River status meaningful)
  A (TRUST):     → after B (failure states documented)
  F (DOC_SEAL):  → after A-E (document final state)

parallel_streams:
  stream_1: [C, B, D]  # Can run simultaneously
  stream_2: [E]        # After D
  stream_3: [A]        # After B, operator-paced
  stream_4: [F]        # Final seal

ripple_risks:
  river_subscription_ripple:
    risk: "IBKR entitlements block Track D"
    mitigation: "Synthetic River fallback allowed (lab/backtester.py)"
    
  xfail_smuggling:
    risk: "Tech debt hidden in quarantine"
    mitigation: "5% cap + S43 ticket requirement"

# ============================================================
# SUCCESS CRITERIA (SPRINT-LEVEL)
# ============================================================

sprint_success:
  S42_COMPLETE_WHEN:
    - "Olya completes dry run without confusion"
    - "All failure scenarios have documented behavior"
    - "pytest clean (0 unexpected failures)"
    - "River fresh for 24h"
    - "phoenix status command works"
    - "New advisor ramps in <10 minutes"

definition_of_done: |
  Phoenix is PRODUCTION-READY:
    - Operators trust it
    - Failures are boring
    - Tests tell truth
    - Data flows continuously
    - State is observable
    - Docs are authoritative

# ============================================================
# IMPLEMENTATION COMPLEXITY NOTES (OPUS)
# ============================================================

complexity_assessment:
  
  track_b_chaos_vectors:
    CV-S42-01: LOW (leverage existing health_fsm)
    CV-S42-02: LOW (leverage existing degradation.py)
    CV-S42-03: LOW (already tested in S41)
    CV-S42-04: MEDIUM (alert bundling is new)
    CV-S42-05: LOW (state anchor already exists)
    CV-S42-06: LOW (simple AVG query)
    
  track_c_tech_debt:
    estimate: |
      Based on S41 failure analysis:
        - 40% likely IMPORT_MISMATCH → quick fix
        - 30% likely SCHEMA_EVOLUTION → regenerate
        - 20% likely EXTERNAL_API_DRIFT → xfail
        - 10% likely REAL_BUG → investigate
      Expected effort: 2-4 hours
      
  track_d_river:
    primary_path: IBKR market data (if entitled)
    fallback_path: Synthetic River (lab/backtester.py)
    complexity: LOW (infrastructure exists)
    
  track_e_phoenix_status:
    complexity: LOW-MEDIUM
    rationale: |
      - Health FSM foundation exists
      - Data sources already have status methods
      - New file creation, no new computation
    estimated_effort: 1-2 hours

# ============================================================
# OPUS EXECUTION READINESS
# ============================================================

opus_ready:
  status: ORIENTED
  
  immediate_actions:
    1: Start Track C (tech debt triage) — run pytest, categorize failures
    2: Start Track B (failure drills) — implement chaos vectors
    3: Start Track D (River) — diagnose data source, enable fallback if needed
    
  blocked_on:
    Track A: Operator-paced (Olya schedule)
    Track F: After other tracks complete
    
  dependencies_verified:
    health_fsm: EXISTS
    circuit_breaker: EXISTS
    degradation: EXISTS
    ibkr_connector: EXISTS
    narrator_emit: EXISTS
    synthetic_bars: EXISTS (lab/backtester.py)

# ============================================================
# VERSION HISTORY
# ============================================================

versions:
  v0.1:
    date: 2026-01-30
    author: CTO_CLAUDE
    status: DRAFT_FOR_ADVISOR_REVIEW
    changes: Initial draft
    
  v0.2:
    date: 2026-01-30
    author: OPUS
    status: BUILDABLE_SPEC
    changes: |
      Merged v0.1 + ADVISOR ADDENDUM:
      - Added repo validation (test count, synthetic river, phoenix_status)
      - Expanded Track A with "What Phoenix Will NEVER Do"
      - Expanded Track B with 5 new scenarios + 6 chaos vectors
      - Added Track C xfail_policy + GATE_C4 (5% cap = 75 tests)
      - Added Track D GATE_D4 (semantic) + GATE_D5 (human) + synthetic fallback
      - Added Track E INV-OBSERVE-NO-INTERPRETATION + GATE_E3
      - Added Track F ARCHITECTURAL_FINALITY.md deliverable
      - Added POST_S42_FREEZE section
      - Added dumbest_failures section
      - Added complexity assessment
      - Added implementation notes per chaos vector
      - Confirmed existing infrastructure availability

# ============================================================
# END BUILD MAP v0.2
# ============================================================
