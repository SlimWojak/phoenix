# ============================================================
# S44 BUILD MAP — LIVE_VALIDATION
# ============================================================

document: S44_BUILD_MAP
version: 0.1
date: 2026-01-31
status: EXECUTING
author: OPUS
approved_by: CTO
theme: "Boring for 48h"

# ============================================================
# PREAMBLE
# ============================================================

context: |
  S43 unlocked fast tests, stable alerts, config reproducibility.
  S44 proves the full path works under real market conditions.
  
  If it's boring, it's correct.
  If it survives 48h unattended, we ship.

governing_principle: |
  "Verify. Validate. Soak. Done."
  "No clever fixes. No architectural changes."
  "Phase 1 blocks everything — don't proceed on bad foundation."

non_goals:
  - River architecture changes
  - IBKR connector rewrites
  - New execution paths
  - Any cleverness

# ============================================================
# PHASE STRUCTURE
# ============================================================

phases:
  P1: RIVER_VERIFICATION    # BLOCKING — data flows correctly
  P2: FULL_PATH_TEST        # signal → CSO → narrator → T2 → bead
  P3: 48H_SOAK              # boring = correct

estimated_duration: |
  P1: 1-2 hours
  P2: 2-4 hours
  P3: 48 hours
  Total: ~52 hours

# ============================================================
# PHASE 1: RIVER_VERIFICATION (BLOCKING)
# ============================================================

phase_1:
  name: RIVER_VERIFICATION
  priority: P0_BLOCKING
  duration: 1-2 hours
  
  questions_to_answer:
    - Does IBKR → River data flow work?
    - Are live bars ingesting?
    - Does Dukascopy/IBKR seam stitch cleanly?
    - Does Truth Teller quality_score correctly?
    - Any gaps flagged?
  
  tasks:
    task_1:
      action: "Check river.db current state"
      command: "SELECT MAX(timestamp), COUNT(*) FROM river_eurusd"
      expect: "Timestamp within 24h, reasonable row count"
      
    task_2:
      action: "Check IBKR connection status"
      command: "python -c 'from brokers.ibkr.connector import get_connection_status; print(get_connection_status())'"
      expect: "CONNECTED or PAPER mode active"
      
    task_3:
      action: "Request fresh bars via IBKR"
      method: "If available, trigger bar request; else verify synthetic"
      expect: "New bars or synthetic fallback documented"
      
    task_4:
      action: "Check historical/live seam"
      query: "SELECT timestamp, source FROM river_eurusd ORDER BY timestamp DESC LIMIT 100"
      expect: "Consistent source attribution, no gaps"
      
    task_5:
      action: "Verify quality_score at boundaries"
      method: "Check enrichment quality scores near seam"
      expect: "No forward-fill hidden as quality=1.0"
  
  # CTO ADDENDUM: Restart sanity between P1 → P2
  restart_sanity:
    timing: "After P1 PASS, before P2 start"
    action: "Cold restart Phoenix, run phoenix_status"
    expect: "Status coherent, no config init edge cases"
    catches: "Config state pollution, River cache issues"
  
  exit_gates:
    GATE_P1_1:
      criterion: "River has data (real or synthetic documented)"
      test: "SELECT COUNT(*) FROM river_eurusd > 0"
      
    GATE_P1_2:
      criterion: "IBKR connection status known"
      test: "Connection status is explicit (CONNECTED/PAPER/DISCONNECTED)"
      
    GATE_P1_3:
      criterion: "Data freshness documented"
      test: "MAX(timestamp) known, staleness hours calculated"
  
  if_fail:
    - Document gaps and root cause
    - Check if synthetic_river fallback sufficient
    - Escalate to CTO before Phase 2

# ============================================================
# PHASE 2: FULL_PATH_TEST
# ============================================================

phase_2:
  name: FULL_PATH_TEST
  priority: P0 (after Phase 1 PASS)
  duration: 2-4 hours
  blocked_by: Phase 1 PASS + restart_sanity
  
  scope: |
    Prove complete loop:
    Signal → CSO gate evaluation → Narrator bark → T2 approval → Execution bead
  
  tasks:
    task_1:
      action: "Trigger setup detection"
      method: "Use test signal or wait for real market condition"
      expect: "CSO receives signal, begins evaluation"
      
    task_2:
      action: "CSO gate evaluation"
      verify: "gates_passed output is list of gate names"
      expect: "Correct gates evaluated per conditions.yaml"
      
    task_3:
      action: "Narrator formats output"
      verify: "Output passes guard dog (ContentClassifier)"
      expect: "Facts only, no forbidden words"
      
    task_4:
      action: "T2 approval flow"
      mode: "PAPER (no real capital)"
      verify: "T2 token generated, approval simulated"
      
    task_5:
      action: "Execution bead written"
      verify: "Bead exists in BeadStore with provenance"
      expect: "bead_id, timestamp, hash, source_ref"
      
    task_6:
      action: "Forensic trail verification"
      verify: "Can trace bead back to signal"
      expect: "Full chain: signal → CSO → narrator → T2 → bead"
  
  chaos_injection:
    cv_s44_01:
      name: "ibkr_heartbeat_drop"
      method: "Simulate heartbeat timeout mid-flow"
      expect: "Graceful degradation, no crash"
      
    cv_s44_02:
      name: "river_degraded_during_cso"
      method: "Mark River stale during CSO evaluation"
      expect: "CSO handles gracefully, alerts fire"
  
  exit_gates:
    GATE_P2_1:
      criterion: "Full loop completes without error"
      test: "Signal → bead with no exceptions"
      
    GATE_P2_2:
      criterion: "Execution bead has correct provenance"
      test: "bead.source_ref traces to signal"
      
    GATE_P2_3:
      criterion: "Narrator output passes guard dog"
      test: "ContentClassifier.validate() returns True"

# ============================================================
# PHASE 3: 48H_SOAK
# ============================================================

phase_3:
  name: 48H_SOAK
  priority: P0 (after Phase 2 PASS)
  duration: 48 hours
  blocked_by: Phase 2 PASS
  
  scope: |
    System runs unattended.
    "Boring for 48h" = success.
  
  monitoring:
    health:
      check: "Health stays GREEN (or degrades gracefully)"
      interval: "Every 6h manual check OR heartbeat bead"
      
    alerts:
      check: "Alerts fire correctly (not storm)"
      threshold: "No CRITICAL, <5 WARNING per 24h"
      
    beads:
      check: "Beads written correctly"
      verify: "All beads have valid provenance"
      
    phoenix_status:
      check: "CLI returns clean state"
      interval: "Every 12h"
  
  # CTO ADDENDUM: Dead man switch
  dead_man_switch:
    purpose: "Catch silent partial death (health GREEN, beads stop)"
    implementation: |
      Every 6h, emit heartbeat bead:
        bead_type: "HEARTBEAT"
        timestamp: now()
        health_snapshot: phoenix_status output
    catches: "System alive but not processing"
  
  # CTO ADDENDUM: End soak replay
  end_soak_replay:
    timing: "After 48h elapsed"
    action: "Replay last 48h beads, verify chain integrity"
    query: |
      SELECT bead_id, hash, prev_hash 
      FROM beads 
      WHERE timestamp > NOW() - INTERVAL '48 hours'
      ORDER BY timestamp
    verify: "No hash mismatches, chain unbroken"
    catches: "Data corruption ghost, provenance rot"
  
  exit_gates:
    GATE_P3_1:
      criterion: "48h elapsed without unexpected alerts"
      test: "Alert count within threshold"
      
    GATE_P3_2:
      criterion: "No CRITICAL in health log"
      test: "grep CRITICAL health.log → empty"
      
    GATE_P3_3:
      criterion: "All beads have valid provenance"
      test: "end_soak_replay passes"
      
    GATE_P3_4:
      criterion: "Dead man switch beads present"
      test: "8 heartbeat beads (48h / 6h intervals)"
  
  abort_conditions:
    storm: ">10 CRITICAL alerts in 30min"
    silent_death: "Health GREEN but no beads for 12h"
    corruption: "Bead hash mismatch in replay"

# ============================================================
# INVARIANTS TO VERIFY
# ============================================================

invariants:
  INV-HALT-1:
    rule: "halt_local < 50ms (even under load)"
    test: "time phoenix halt → <50ms"
    
  INV-DATA-CANON:
    rule: "River is single truth"
    test: "All data queries go through River"
    
  INV-NARRATOR-1:
    rule: "Facts only, no synthesis"
    test: "All narrator output passes guard dog"
    
  INV-ALERT-TAXONOMY-1:
    rule: "Alerts use defined categories"
    test: "No unclassified alerts during soak"
    
  INV-NO-CORE-REWRITES-POST-S44:
    rule: "No architectural rewrites after S44"
    activation: "Becomes active after S44 COMPLETE"

# ============================================================
# ESCALATION TRIGGERS
# ============================================================

escalate_to_cto_if:
  - River/IBKR integration fundamentally broken
  - Phase 2 reveals architectural gap
  - Soak test shows systemic issue
  - Any uncertainty about scope

do_not_fix_without_escalation:
  - River architecture changes
  - IBKR connector rewrites
  - New execution paths
  - Anything taking >4 hours

# ============================================================
# SUCCESS CRITERIA
# ============================================================

s44_complete_when:
  - Phase 1 PASS (River verified)
  - Phase 2 PASS (full path proven)
  - Phase 3 PASS (48h soak, boring = correct)
  - All exit gates green
  - INV-NO-CORE-REWRITES-POST-S44 activates

definition_of_done: |
  "Prove it works, then leave it alone."
  Full path validated under real conditions.
  48h boring = shipping confidence.

# ============================================================
# VERSION HISTORY
# ============================================================

versions:
  v0.1:
    date: 2026-01-31
    author: OPUS
    approved_by: CTO
    status: EXECUTING
    changes: |
      Initial build map from CTO brief.
      3 addendums woven in:
      - Dead man switch (6h heartbeat beads)
      - End soak replay (bead chain verification)
      - Restart sanity (cold restart between P1→P2)

# ============================================================
# END BUILD MAP v0.1
# ============================================================
