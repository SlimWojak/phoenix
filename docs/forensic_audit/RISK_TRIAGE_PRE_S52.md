TIER_1_FIX_NOW: "Live risks that affect capital path correctness"
  
  RISK-1: Dual Position State Machine
    severity: HIGH
    why_now: Two FSMs in execution path = state corruption vector
    fix: Deprecate execution/position.py, migrate broker_stub + replay
    effort: ~100 LOC, low risk
    owner: Opus
  
  RISK-3: Bounds Enforcement Not Auto-Fed
    severity: HIGH  
    why_now: If nobody calls check_all_bounds() with live data, 
             drawdown limits are theater. Capital at risk.
    fix: Wire PositionTracker → LeaseInterpreter in monitoring loop
    effort: ~50-100 LOC
    owner: Opus

  RISK-7: INV-RIVER-FRESHNESS Untested
    severity: MEDIUM-HIGH
    why_now: Stale data reaching gate evaluation = false signals
    fix: One test — feed stale data, assert rejection
    effort: ~30 LOC
    owner: Opus (trivial)

TIER_2_SPRINT_SCOPE: "Debt that blocks next phase but not today"
  
  RISK-10: Scanner → T2 Integration Gap
    severity: MEDIUM
    why: Full signal→order chain untested end-to-end
    fix: Integration test ~100-150 LOC
    when: Before any live trading promotion
  
  RISK-11: INV-EXECUTION-FIDELITY (slippage tracking)
    severity: MEDIUM
    why: Need this before real capital flows
    fix: Fill-vs-intent comparison + alert ~50 LOC
    when: Pre-live
  
  RISK-6: River __init__.py exports
    severity: LOW
    fix: 10 LOC, do it as cleanup
  
  RISK-9: BEAD_FIELD_SPEC genesis count (981→789)
    severity: LOW  
    fix: 5 LOC spec update
  
  RISK-12: Deployment config audit
    severity: LOW-MEDIUM
    fix: Startup validation ~50-100 LOC
    when: Pre-live deployment

TIER_3_GATED: "Designed-not-built — correct by design, later gates"
  
  RISK-2: Two-Economy Bridge
    gate: Gate 3+
    note: |
      Opus correctly flags this as HIGH severity architecturally.
      But this is by design — we PLANNED to build it later.
      The risk is the DOCS claim it exists when it doesn't.
      FIX THE DOCS, not the code (yet).
  
  RISK-4: Sovereign Anchor / HSM
    gate: Gate 7
    note: No urgency. Hardware + ceremony needed.
  
  RISK-5: CONSTITUTION/ Skeleton
    decision_needed: |
      G — Opus raises a fair point. Two options:
      A) Populate CONSTITUTION/ with real invariant YAMLs (~1000 LOC)
      B) Downgrade claim, archive skeleton, acknowledge invariants 
         live in code not YAML (~50 LOC)
      
      My recommendation: Option B for now. The invariants ARE enforced 
      in code with tests. The YAML directory was aspirational documentation.
      Don't build documentation infrastructure when capital path needs hardening.
  
  RISK-8: AIR Not Built
    gate: Gate 3
    note: Bead signing works. Runtime verification is next-phase scope.