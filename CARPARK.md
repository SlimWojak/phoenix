CTO_ASSESSMENT: CLAUDE_CODE_HOOKS

VALUE: HIGH (but S27+ implementation)

ALIGNMENT_WITH_PHOENIX:
  constitution_enforcement:
    trigger: file_save, git_commit
    hook: verify_constitution.py (async)
    effect: Inquisitor runs without blocking Opus
    
  ripple_analysis:
    trigger: contract_change
    hook: blast_radius.py (async)
    effect: affected contracts flagged automatically
    
  truth_teller:
    trigger: data_ingest
    hook: quality_check.py (async)
    effect: corruption detection parallel to enrichment
    
  owl_integration:
    trigger: git_push
    hook: notify_antigravity.py (async)
    effect: Owl sees changes, audits without sprint stall

SPECIFIC_USE_CASES:
  1_INQUISITOR_HOOK:
    event: file_save (phoenix/**)
    command: "python verify_invariants.py --changed-files $FILES"
    async: true
    effect: heresy caught at save, not at PR
    
  2_SCHEMA_DRIFT_HOOK:
    event: file_save (contracts/*)
    command: "python check_schema_hash.py"
    async: true
    effect: ICT_DATA_CONTRACT hash mismatch flagged instantly
    
  3_HALT_REGRESSION_HOOK:
    event: pre_commit
    command: "pytest tests/test_halt_latency.py -x"
    async: false (blocking — sovereignty invariant)
    effect: <50ms regression cannot merge
    
  4_OWL_NOTIFY_HOOK:
    event: git_push
    command: "python notify_owl.py --diff HEAD~1"
    async: true
    effect: Owl in AntiGravity gets structured diff

IMPLEMENTATION_TIMING:
  now: NO (foundation just proven)
  s27: CONSIDER (if CSO build reveals friction)
  s28+: YES (as HIVE matures)
  
RATIONALE:
  - hooks are optimization, not foundation
  - current workflow: manual triggers working
  - risk: premature automation hides learning
  - benefit unlocks: after patterns stabilize

RECOMMENDATION:
  action: LOG_FOR_S27_PLANNING
  priority: P2 (nice-to-have, not blocking)
  revisit: when Opus/HIVE friction emerges
  
PARKING:
  add_to: S27_PLANNING.md (tooling section)
  note: "async hooks for Inquisitor + Owl integration"