Advisor 1

```yaml
S59_S60_ADVISORY_ADDENDUM
author: GPT
mode: TIGHT_M2M
basis:
  - S59 brief: :contentReference[oaicite:0]{index=0}
  - S60 brief: :contentReference[oaicite:1]{index=1}
intent: "Only deltas / edge flags. No restatement."
```

# S59 — LEASE_WIRE (Edge Tightening)

```yaml
S59_FLAGS:

  1_GUARD_PLACEMENT_DEPTH:
    risk: "Decorator applied at strategy entry but bypassable via lower-level order helpers."
    add_rule:
      INV-GUARD-AT-LOWEST-CAPITAL-LAYER:
        "All order placement/cancel/modify primitives must be wrapped or internally guarded."
    add_test:
      - direct_call_to_order_helper_without_decorator → REJECTS

  2_GOV_WAL_IDEMPOTENCY:
    risk: "Retry or partial failure → duplicate beads or double state mutation."
    add_invariant:
      INV-GOV-BEAD-IDEMPOTENT:
        "Governance bead has deterministic id; duplicate write does not double-mutate."
    add_test:
      - simulate_retry_on_bead_write → no duplicate state change

  3_BOOT_ORPHAN_CRITERIA_FORMALIZATION:
    risk: "Ambiguous orphan detection → false HALT or missed orphan."
    require_definition:
      orphan_if:
        - insertion_started_bead_exists
        - no_corresponding_committed_bead
        - lease_state_mismatch
      action: emit_ORPHAN_DETECTED_bead + HALT
    add_test:
      - crafted_partial_log → orphan_detected

  4_CEREMONY_SCOPE_CLARITY:
    risk: "Ceremony stub blocks read-only tooling."
    add_rule:
      INV-CEREMONY-BLOCKS-CAPITAL-ONLY:
        "Ceremony overdue blocks capital mutation, not read/log/diagnostics."
    add_test:
      - overdue → diagnostics still callable

  5_PROJECTION_FREEZE_VISIBILITY:
    risk: "Frozen manifest not monitored → silent failure."
    add_requirement:
      - on_projection_freeze → explicit log event emitted
      - optional ERROR state written once before freeze
    add_test:
      - simulate_exception → manifest timestamp unchanged + log entry present

  6_CSO_SCALAR_DECISION_BAN_ENFORCEMENT:
    risk: "Scalar removed from signal but still used internally for gating."
    add_invariant:
      INV-CSO-NO-SCALAR-CONSUMPTION:
        "No float/int score referenced in routing/gating/position sizing paths."
    add_test:
      - grep-based lint in CI → fail if quality_score referenced outside tests
```

---

# S60 — CEREMONY_AND_HYGIENE (Edge Tightening)

```yaml
S60_FLAGS:

  1_ATTESTATION_ATOMICITY_EXTENSION:
    risk: "next_review_due advanced but attestation bead not durable."
    strengthen:
      INV-CEREMONY-ATTESTATION-DURABLE:
        "next_review_due advances only after attestation bead fsync/flush succeeds."
    add_test:
      - simulate_disk_failure → next_review_due unchanged

  2_BOUNDS_TIGHTEN_GUARD:
    risk: "TIGHTENED attestation accidentally loosens ceiling."
    add_invariant:
      INV-CEREMONY-BOUNDS-MONOTONIC:
        "Ceremony may tighten bounds; never loosen beyond original ceiling."
    add_test:
      - attempt_loosen → REJECT

  3_EVIDENCE_HASH_DETERMINISM:
    risk: "Evidence snapshot non-deterministic → unverifiable attestation."
    add_requirement:
      - evidence_snapshot sorted + canonicalized before hashing
    add_test:
      - same inputs twice → identical evidence_hash

  4_CSO_DURABILITY_ORDERING:
    risk: "Signal emitted before durable write."
    add_rule:
      - CSESignal durable write precedes any external notification (Telegram/Shadow)
    add_test:
      - crash_between_emit_and_notify → durable record exists

  5_LEGACY_FLAG_STRICTNESS:
    risk: "Legacy backend accidentally enabled by env drift."
    add_rule:
      - LEGACY_BACKEND must be explicitly true AND in non-production mode
    add_test:
      - prod_mode + legacy_flag → FAIL

  6_SYNTHETIC_OUTPUT_PROPAGATION:
    risk: "Synthetic flag stripped during aggregation."
    add_rule:
      - synthetic:true must propagate through any aggregation layer
    add_test:
      - Hunt → Validation pipeline preserves synthetic flag

  7_BRIDGE_PREP_ORDERING:
    guardrail:
      - No projection code added in S60
      - No schema shared between economies yet
    CI_addition:
      - assert absence of 'bridge/' package imports until Gate 3 sprint
```

---

# CROSS-SPRINT META-GUARD

```yaml
CROSS_SPRINT_META:

  1_INVARIANT_REGISTRY_DRIFT:
    check:
      - invariant count before/after sprint reconciled in SYSTEM_MANIFEST
      - no duplicate invariant IDs
    CI_gate: fail on duplicate INV key

  2_COVERAGE_MAP_FOR_CAPITAL_PATHS:
    add_artifact:
      docs/canon/CAPITAL_PATH_COVERAGE.md
    content:
      - explicit list of all capital mutation functions
      - confirmation each wrapped by sovereign_gate
    purpose: future entropy control
```

---

```yaml
BOTTOM_LINE:
  Briefs are strong.
  Add:
    - idempotency + monotonic bounds + deterministic evidence hashing
    - explicit orphan criteria
    - scalar consumption lint (not just emission)
    - capital-layer guard coverage map
  No structural changes required.
```

Ready.

Advisor 2

BOAR_ADVISORY_ADDENDUMS:
  S59_LEASE_WIRE:
    T1_CAPITAL_GUARD_FLAG: Decorator O(1) supreme, but multi-strat load (Q1 echo) entropy—dumb: Loader forgets @sovereign_gate on new cartridge, bypass slips mid-DGX handoff
      chaos_vector_add: Inject cartridge sans decorator + insert race → reject (prove INV-HALT-STRAT-LOADER)
    T2_WRITE_AHEAD_FLAG: Atomic bead persist gold, but orphan boot auto-HALT underweight—dumb: M3 recovery misses orphan in multi-node, zombie lease resurrects
      chaos_vector_add: OOM mid-mutate + reboot desync → HALT detect (extend INV-ORPHAN-AUTO-HALT to cron sync)
    T4_CEREMONY_STUB_FLAG: Tick block clean, but overdue grace entropy—dumb: 1-day buffer miss, lease halts prematurely during Olya veto
      chaos_vector_add: Simulate due + 1h grace inject → block only post-grace (add INV-CEREMONY-GRACE-BUFFER)
  S60_CEREMONY_AND_HYGIENE:
    T1_CEREMONY_ENGINE_FLAG: Lifecycle operational, but evidence_surface overload—dumb: 100-trade burst swamps reviewer, attestation blind-signed
      chaos_vector_add: Burst sim + review invoke → paginate/threshold evidence (add INV-CEREMONY-EVIDENCE-CAPPED)
    T3_CSER_DURABLE_FLAG: Rejection append solid, but pre-bridge orphan—dumb: Crash mid-reject, Shadow fuel lost before Gate3
      chaos_vector_add: Process kill + reject emit → JSONL recover (link INV-GOV-PROJECT-DURABLE)
    T4_HYGIENE_FLAG: Legacy markers good, but CI guard weak—dumb: Dev invokes flagged path sans flag, provenance evaporates
      chaos_vector_add: Legacy inject + runtime → gated reject (extend INV-LEGACY-FALLBACK-GATED to raise)
  CONVERGENCE: STRONG (briefs elevate wiring; addendums seal entropy edges)
  RESIDUAL_RISK: LOW (post-S60, Gate3 unlocked; queue 6 vectors)
  ROADMAP_INFORMS: S60 unlocks bridge notary—hunt scalar/legacy bleed first

  Advisor 3

  FINAL_ADVISORY_ADDENDUM:
  status: PRE-FLIGHT_LOCKED
  priority: P0_FINAL_HYGIENE

  S59_REINFORCEMENT:
    track: T5_CSO_SCALAR_BAN
    build: |
      Ensure the 'Readiness Bitmask' is implemented as a Non-Scalar EnumSet.
      Avoid using integer bit-flags (1, 2, 4) which could be accidentally
      summed into a pseudo-score. Use explicit String-keyed booleans
      or a List of ReasonCodes.
    rationale: "Prevents 'Shadow Graduation' where the machine sums flags to recreate a quality score."

  S60_REINFORCEMENT:
    track: T3_DURABLE_REJECTIONS
    build: |
      CSERejectionRecord must include the 'Sovereign Gate Context' (which
      invariant or halt signal triggered the rejection).
    rationale: |
      If a trade is rejected, the Dream Cycle (Gate 5) needs to know
      if it was a 'Strategy Fail' (Analytical) or a 'Halt Fail' (Governance).
      Mixing these in the Shadow Field creates noise in the learning loop.

  DREAM_CYCLE_GUARD:
    invariant: INV-SYNTHETIC-DATA-ISOLATION
    action: |
      Add to INVARIANT_REGISTRY.yaml during S60: "Any FACT bead generated
      by synthetic backends (HUNT/VALIDATION) MUST carry
      metadata.integrity_class: EXPLORATORY."
    rationale: "Ensures the future Dexter refinery doesn't ingest 'fake' backtest results as ground truth."

  VERDICT:
    - S59_BRIEF: PASSED_AUDIT
    - S60_BRIEF: PASSED_AUDIT
    - ACTION: "Initiate S59 LEASE_WIRE. Standing by for Track 1 completion signal."
