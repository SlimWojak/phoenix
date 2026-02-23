# ============================================================
# S42 BUILD MAP — PRODUCTION CLOSURE
# ============================================================

document: S42_BUILD_MAP
version: 0.1
date: 2026-01-30
status: DRAFT_FOR_ADVISOR_REVIEW
author: CTO_CLAUDE
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
        - RIVER_DEAD: River stops updating
        - IBKR_FLAP: Connection dies/reconnects rapidly
        - CSO_EMPTY: No conditions match
        - NARRATOR_SUPPRESSED: Guard blocks all output
        - HALT_CASCADE: Manual halt propagation
        - DATA_STALE: River health < threshold
      
    - docs/FAILURE_BEHAVIOR_MATRIX.md
      format: |
        | Failure | Detection | Alert | Recovery | Human Action |
        |---------|-----------|-------|----------|--------------|
  
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
  
  dependencies: None (can start immediately)
  
  build_notes:
    - OPUS has repo intimacy — he knows what's real vs stale
    - Banteg pattern: "Nuke jank deps, harden for apocalypse-mode"
    - This is surgery, not archaeology

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
  
  deliverables:
    - River health GREEN for 24-48h continuous
    - docs/RIVER_EXPECTATIONS.md
      content: |
        - Data sources
        - Update frequency
        - Gap handling
        - Quality thresholds
        - Alert triggers
  
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
  
  dependencies: None (can start immediately)
  
  build_notes:
    - May need IBKR market data subscription check
    - Alternative: synthetic bars for testing
    - Goal is CONTINUOUS, not COMPREHENSIVE (6 pairs enough)

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
  
  deliverables:
    - cli/phoenix_status.py (or widget enhancement)
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
  
  exit_gates:
    GATE_E1:
      criterion: "One command shows system state"
      test: cli/phoenix_status.py runs without error
      
    GATE_E2:
      criterion: "Output answers 'is it broken?' in <2s"
      test: timing + completeness check
  
  dependencies: Track D (River status meaningful)
  
  build_notes:
    - Can extend existing widget if simpler
    - Read-only aggregation of existing state
    - NO new state, NO new computation

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
    - docs/S41_COMPLETION_REPORT.md (finalized)
    - docs/INVARIANT_FREEZE_S41.md (finalized)
    - docs/ARCHIVE/ (obsolete docs moved)
    - docs/START_HERE.md (new advisor bootstrap)
  
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
# ADVISOR REVIEW QUESTIONS
# ============================================================

for_gpt:
  - "Is the scope appropriately bounded?"
  - "Any P0-P5 misordered?"
  - "Missing closure items?"

for_owl:
  - "Structural coherence across tracks?"
  - "Dependency graph sound?"
  - "Any ripple risks?"

for_grok:
  - "Failure scenarios complete?"
  - "What's the dumbest way S42 fails?"
  - "Chaos vectors for Track B?"

for_opus:
  - "Tech debt triage feasible in scope?"
  - "River restoration blockers?"
  - "Repo-level gaps I'm missing?"

# ============================================================
# VERSION HISTORY
# ============================================================

versions:
  v0.1:
    date: 2026-01-30
    author: CTO_CLAUDE
    status: DRAFT_FOR_ADVISOR_REVIEW
    changes: Initial draft

# ============================================================
# END BUILD MAP v0.1
# ============================================================

ADVISORY ADDENDUM FOR OPUS REVIEW AND SYNTHESISING INTO S42_BUILD_ROADMAP_v0.2 SEE BELOW : 

# ============================================================
# S42_BUILD_MAP ADDENDUM
# ADVISOR SYNTHESIS
# ============================================================

document: S42_BUILD_MAP_ADDENDUM
version: 0.1.1
date: 2026-01-30
author: CTO_CLAUDE
sources: [GPT, GROK, OWL]
status: READY_FOR_OPUS_SWEEP

# ============================================================
# CONVERGENCE SUMMARY
# ============================================================

advisor_verdicts:
  GPT: STRONG_PASS (additive only)
  GROK: APPROVE (entropy blades needed)
  OWL: SOLID (structural coherence verified)

convergence_points:
  - v0.1 base: APPROVED by all
  - XFAIL trap: flagged by ALL THREE
  - More failure scenarios: GPT + GROK
  - Post-S42 freeze: GPT + OWL
  - Semantic data validation: GROK (critical insight)

no_deletions_required: TRUE
no_priority_inversions: TRUE

# ============================================================
# NEW SECTION: POST-S42 FREEZE
# (GPT G1 + OWL alignment)
# ============================================================

add_section:
  location: after TRACK F, before SUCCESS CRITERIA
  
  content:
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
# TRACK A ADDITIONS
# ============================================================

track_a_additions:

  # GPT: Negative expectations section
  add_to_operator_expectations_md:
    section: "What Phoenix Will NEVER Do"
    bullets:
      - Explain *why* a trade worked
      - Tell you what you *should* do
      - Infer your intent
      - Fill silence with reassurance
      - Propose hypotheses
      - Say "I noticed..."
    rationale: "Prevents anthropomorphization drift"

# ============================================================
# TRACK B ADDITIONS
# ============================================================

track_b_additions:

  # GPT: Partial recovery scenario
  add_failure_scenario:
    - name: PARTIAL_RECOVERY
      description: "Subsystem recovers but upstream remains degraded"
      example: "IBKR reconnects but River still stale"
      why: "Partial recovery = operator confusion + system lies by omission"

  # GROK: Additional high-entropy scenarios
  add_failure_scenarios:
    - name: GUARD_DOG_FALSE_NEGATIVE
      description: "Heretical output slips past classifier"
      attack: "homoglyph sneak, zwsp abuse, unicode edge"
      expect: "receipts summonable, audit trail exists"
      
    - name: GUARD_DOG_FALSE_POSITIVE
      description: "Legit output blocked → narrator silent"
      attack: "force block legitimate template"
      expect: "suppressed: reason X" bark, distinguishable from dead
      
    - name: STATE_HASH_STALE
      description: "Stale intent hits T2 gate after long session"
      attack: "submit shadow intent with old hash"
      expect: "STATE_CONFLICT, phoenix_status shows 'stale since HH:MM'"
      
    - name: MULTI_FAILURE_COMPOUND
      description: "River dead + IBKR flap + narrator suppressed simultaneously"
      attack: "triple chaos injection"
      expect: "deduped alert bundle, not 17 Telegram pings"

  # GROK: Chaos vectors (ready for drills/s42_failure_playbook.py)
  chaos_vectors_s42:
    - id: CV-S42-01
      name: river_ingestion_killed
      method: "kill ingestion daemon / unplug mock data feed"
      expect: "DEGRADED → CRITICAL, single alert, no spam"

    - id: CV-S42-02
      name: ibkr_rapid_reconnect_loop
      method: "toggle connect/disconnect every 8-12s for 3min"
      expect: "backoff+jitter, T2→T1 cascade, one alert, no storm"

    - id: CV-S42-03
      name: narrator_heresy_injection
      method: "inject zwsp + homoglyph into template render"
      expect: "NarratorHeresyError, minimal Telegram, receipts summonable"

    - id: CV-S42-04
      name: multi_degrade_cascade
      method: "river dead + IBKR flap + CSO empty simultaneously"
      expect: "deduped MULTI_DEGRADED alert, phoenix_status shows all three"

    - id: CV-S42-05
      name: state_hash_stale_approval
      method: "long dry-run → market moves → submit with old hash"
      expect: "T2 gate rejects, STATE_CONFLICT, stale timestamp visible"

    - id: CV-S42-06
      name: semantic_data_poison
      method: "inject 1s bars when expecting 1min"
      expect: "data resolution mismatch alert after silence threshold"

# ============================================================
# TRACK C ADDITIONS
# ============================================================

track_c_additions:

  # ALL THREE: XFAIL policy (GPT: 5%, OWL: 10% → split difference)
  xfail_policy:
    max_ratio: "5% of test suite"
    hard_cap: 75  # assuming ~1500 tests
    review_required_above: YES
    expiration_warning: |
      XFAIL is quarantine, not cure.
      Any xfail without S43 ticket = tech debt smuggling.
    
  add_to_exit_gates:
    GATE_C4:
      criterion: "XFAIL count ≤ 5% of test suite"
      test: "pytest --collect-only | grep xfail | wc -l"

# ============================================================
# TRACK D ADDITIONS
# ============================================================

track_d_additions:

  # GROK: Semantic correctness check (critical insight)
  add_to_exit_gates:
    GATE_D4:
      criterion: "River data semantically correct (not just fresh)"
      test: |
        SELECT AVG(bar_duration) FROM river_eurusd 
        WHERE timestamp > NOW() - INTERVAL '1 hour'
        → assert ≈ target timeframe (±10%)
      why: "Checked the pipe, not what flows through it = dumbest death"
      
    GATE_D5:  # GPT: Human sanity gate
      criterion: "CTO does not manually check River logs for 24h"
      test: "observational"

  # OWL: Synthetic fallback for blockers
  add_to_build_notes:
    - "If IBKR data entitlements block >24h → allow Synthetic River fallback"
    - "Track B/E can proceed with synthetic data if live blocked"

  # GROK: Non-guarantees section
  add_to_river_expectations_md:
    section: "Non-Guarantees"
    bullets:
      - No guarantee of price correctness
      - No guarantee of completeness during outages
      - River may be stale without being wrong
      - Fresh ≠ semantically correct
    rationale: "Prevents operator over-trust"

# ============================================================
# TRACK E ADDITIONS
# ============================================================

track_e_additions:

  # GPT: Facts-only invariant
  add_invariant:
    INV-OBSERVE-NO-INTERPRETATION:
      rule: "phoenix_status outputs facts only, no adjectives"
      forbidden: ["Healthy", "Looks good", "Stable", "Normal"]
      allowed: ["GREEN", "CONNECTED", "0 open", "last: 14:29:55"]
      enforcement: "output validation in cli/phoenix_status.py"

  # GPT: Human sanity gate
  add_to_exit_gates:
    GATE_E3:
      criterion: "Olya can answer 'is it broken?' using only phoenix_status"
      test: "verbal confirmation during dry run"

  # OWL: Priority note
  add_to_build_notes:
    - "phoenix_status is 'Physical Evidence' of success for G and Olya"
    - "Prioritize this as operator's primary window into system"

# ============================================================
# TRACK F ADDITIONS
# ============================================================

track_f_additions:

  # GPT: Architectural finality doc
  add_deliverable:
    - docs/ARCHITECTURAL_FINALITY.md
      content:
        - What Phoenix *is* (final form)
        - What Phoenix *will never become* (anti-roadmap)
        - Why certain obvious features are forbidden
        - Constitutional anchors that cannot change
      rationale: "Saves future debates, prevents scope creep"

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
# DEPENDENCY GRAPH UPDATE
# ============================================================

dependency_validation:
  OWL_verdict: SOUND
  
  noted_ripples:
    river_subscription_ripple:
      risk: "IBKR entitlements block Track D"
      mitigation: "Synthetic River fallback allowed"
      
    xfail_smuggling:
      risk: "Tech debt hidden in quarantine"
      mitigation: "5% cap + S43 ticket requirement"

# ============================================================
# OPUS SWEEP BRIEF
# ============================================================

opus_instructions:
  task: "Merge v0.1 + this addendum → v0.2"
  
  merge_actions:
    1: "Add post_s42_freeze section after Track F"
    2: "Expand Track A deliverables with 'What Phoenix Will NEVER Do'"
    3: "Expand Track B scenarios (5 additional) + chaos vectors (6)"
    4: "Add Track C xfail_policy + GATE_C4"
    5: "Add Track D GATE_D4 (semantic) + GATE_D5 (human) + non-guarantees"
    6: "Add Track E INV-OBSERVE-NO-INTERPRETATION + GATE_E3"
    7: "Add Track F ARCHITECTURAL_FINALITY.md deliverable"
    8: "Add dumbest_failures section (visibility for team)"
    
  repo_knowledge_request:
    - "Flag any additions that conflict with existing code"
    - "Note implementation complexity for new chaos vectors"
    - "Identify if Synthetic River fallback already exists"
    - "Confirm current test count for XFAIL cap calculation"

# ============================================================
# SUMMARY
# ============================================================

additions_count:
  new_sections: 1 (post_s42_freeze)
  new_failure_scenarios: 5
  new_chaos_vectors: 6
  new_exit_gates: 5 (C4, D4, D5, E3 + semantic)
  new_invariants: 1 (INV-OBSERVE-NO-INTERPRETATION)
  new_deliverables: 1 (ARCHITECTURAL_FINALITY.md)
  new_doc_sections: 2 (NEVER Do, Non-Guarantees)

scope_impact: ADDITIVE_ONLY
risk_change: REDUCED (more failure coverage)
flash_risk: NONE (all additions serve closure)

# ============================================================