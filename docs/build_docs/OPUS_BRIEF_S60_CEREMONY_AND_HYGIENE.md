# OPUS BRIEF: S60 CEREMONY_AND_HYGIENE
# For: Opus MAX Session (Cursor) — execute AFTER S59 complete
# From: CTO (Claude) — synthesized from 3 investigations + 3 advisor audits
# Date: 2026-02-25
# Prerequisite: S59 LEASE_WIRE all gates PASS

```yaml
BRIEF: S60.ALL.D1
MISSION: CEREMONY_AND_HYGIENE — Full ceremony engine + architectural debt cleanup
OWNER: OPUS (Cursor)
FORMAT: DENSE
SPRINT: S60
CODENAME: CEREMONY_AND_HYGIENE
PREREQUISITE: S59 COMPLETE (all exit gates PASS)
```

---

## P0: ORIENTATION (Read Before Coding)

```yaml
orientation_sequence:
  # Carry forward from S59 — re-read if fresh session
  1: docs/canon/SPRINT_ROADMAP.md
  2: docs/canon/a8ra_SYSTEM_MANIFEST_v1_0.md
  3: INVARIANT_REGISTRY.yaml                 # Now 251 after S59

  # S60-specific orientation
  4: governance/sovereign_gate.py             # S59 deliverable — the guard decorator
  5: governance/bead_emitter.py               # S59 deliverable — durable emitter
  6: governance/lease_types.py:406-417        # Ceremony schema fields
  7: governance/lease.py                      # State machine (check S59 modifications)
  8: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md:552-588   # Ceremony design spec
  9: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md:1045-1110 # Weekly ceremony flow
  10: cso/consumer.py:395-439                 # CSO rejection records (transient)
  11: cfp/bead_adapter.py                     # Legacy adapter (mark deprecated)
  12: dexter/core/bundler.py                  # Legacy export (mark deprecated)
```

---

## CONTEXT

```yaml
status: a8ra v0.1 post-S59 | S59 gates PASS | sovereign_gate operational
prior_work:
  S59: CapitalGuard wired, write-ahead governance, projection honesty, scalar decapitation, ceremony stub, CI isolation

problem: |
  S59 delivered the STUB ceremony check (overdue → HALTED).
  S60 completes the ceremony lifecycle:
    - Attestation bead emission on review completion
    - Review workflow with evidence display
    - next_review_due auto-calculation
    - Ceremony scheduling integration

  Additionally, 3 investigations surfaced architectural debt that doesn't warrant
  its own sprint but should be cleaned in a hygiene pass:
    - Legacy export paths need DEPRECATED markers with CI tripwires
    - Synthetic output isolation flags for Hunt/Validation
    - INV-DEXTER-ALWAYS-CLAIM needs root registry sync
    - CSO rejection records need durability (pre-bridge prep)
    - Documentation drift (leases/README state diagram)
    - Calibration design contract (schema, not implementation)
```

---

## TRACK 1: CEREMONY_ENGINE (Full Attestation Lifecycle)

```yaml
T1_CEREMONY_ENGINE:
  purpose: "Complete the weekly attestation ceremony from stub to operational"

  design:
    lifecycle:
      1_schedule: "On lease activation or renewal → set next_review_due (default: +7 days)"
      2_check: "sovereign_gate checks ceremony_due (S59 stub — already wired)"
      3_review: "Human initiates review → system presents evidence"
      4_attest: "Human signs off → CeremonyAttestationBead emitted (durable)"
      5_advance: "next_review_due advances by ceremony_interval_days"
      6_miss: "If missed → lease stays HALTED until human reviews + attests"

    evidence_surface:
      on_ceremony: "Display to reviewer:"
        - total_trades_in_period
        - win_loss_record
        - pnl_summary
        - max_drawdown_reached
        - gates_passed_failed_distribution
        - calibration_drift_pct (if CALIBRATION_BEAD exists)
      source: "Query from governance beads (durable after S59)"
      note: "Display FACTS only. No grades, no recommendations. INV-HARNESS-1."

    bead_types:
      CeremonyAttestationBead:
        fields:
          lease_id: str
          reviewer: str
          reviewed_at: datetime
          attestation: enum[RENEWED, TIGHTENED, REVOKED]
          bounds_changes: Optional[dict]  # if tightened
          evidence_hash: str  # hash of evidence snapshot
          next_review_due: datetime
        persist: "Via S59 DurableBeadEmitter — MUST be on disk before state advances"

  target_files:
    - governance/ceremony.py (NEW) — ceremony engine
    - governance/lease_types.py — add CeremonyAttestationBead if not already in schema
    - governance/lease.py — integrate ceremony advance into state machine
    - governance/sovereign_gate.py — verify ceremony_due check works with new engine

  invariants:
    INV-CEREMONY-BLOCKS-ACTIVE: "Already enforced (S59). Ceremony engine extends, not replaces."
    INV-CEREMONY-ATTESTATION-DURABLE: "Attestation bead must persist before next_review_due advances" (NEW)

  tests_required:
    file: tests/test_ceremony.py (NEW)
    cases:
      - lease activated → next_review_due set correctly (now + interval)
      - ceremony completed → CeremonyAttestationBead on disk
      - ceremony completed → next_review_due advances
      - ceremony RENEWED → lease stays ACTIVE
      - ceremony TIGHTENED → lease bounds updated (tighter only)
      - ceremony REVOKED → lease transitions to REVOKED
      - ceremony missed → lease stays HALTED (S59 stub behavior preserved)
      - attestation bead fails to persist → ceremony NOT recorded (atomic)
      - evidence surface contains no scalar grades (lint check)

  implementation_notes:
    - The ceremony is HUMAN-INITIATED. No auto-trigger.
    - The engine PRESENTS evidence and RECORDS attestation. It does NOT decide.
    - Bounds changes must respect INV-LEASE-CEILING (can only tighten, never loosen)
    - Use existing DurableBeadEmitter from S59 for bead persistence
```

---

## TRACK 2: CSO_REJECTION_DURABILITY

```yaml
T2_CSO_REJECTION_DURABILITY:
  purpose: "Make CSO rejection records durable — pre-bridge preparation"

  problem: |
    cso/consumer.py lines 395-439: CSERejectionRecord stored in in-memory list.
    When bridge (Gate 3) projects rejections as PROPOSAL_REJECTED beads,
    the source data must be durable. If transient, bridge projects nothing.

  design:
    pattern: "Same as S59 write-ahead — append-only JSONL or wire to bead_store"
    scope: "CSERejectionRecord and CSESignal emission points"
    target: "cso/scanner.py lines 297, 356, 363 — emission points"

  target_files:
    - cso/consumer.py — replace in-memory list with durable store
    - cso/scanner.py — verify emission points write to durable path

  tests_required:
    file: tests/test_cso_durability.py (NEW)
    cases:
      - CSO evaluation → rejection record exists on disk
      - CSO evaluation → signal record exists on disk
      - process crash mid-evaluation → records persisted up to crash point

  implementation_notes:
    - Use same DurableBeadEmitter pattern from S59 if possible
    - These are GOVERNANCE artifacts (Economy 1) — they go to Phoenix storage, not Dexter
    - Bridge will read FROM these durable records when Gate 3 ships
```

---

## TRACK 3: LEGACY_DEPRECATION_GUARDS

```yaml
T3_LEGACY_DEPRECATION:
  purpose: "Mark stale code paths with enforced deprecation — prevent shadow bridge"

  targets:
    1_DEXTER_CORE_EXPORT:
      file: dexter/core/bundler.py — export_claim_beads function
      action: |
        Add DEPRECATED_BY_BRIDGE marker.
        Add Python warning: "WARNING: Legacy JSON export. Not canonical bridge path."
        Add CI test: if called in default test suite without explicit LEGACY flag → FAIL
      evidence: "Zero Phoenix consumers (grep 'claims.jsonl' phoenix/ = 0 matches)"
      note: "If dexter repo is separate, coordinate with G on where to apply"

    2_CFP_BEAD_ADAPTER:
      file: cfp/bead_adapter.py
      action: |
        Add DEPRECATED_BY_BRIDGE marker.
        Add warning on import: "Legacy JSON backend. Will be replaced by bridge query at Gate 2."
        Gate behind explicit LEGACY_BACKEND=true flag.
      evidence: "Uses legacy state/beads.json backend, not River or Bead Field"

    3_HUNT_SYNTHETIC_OUTPUTS:
      file: hunt/executor.py
      action: |
        All generated metrics must include metadata:
          synthetic: true
          generator: "RNG_STUB"
          mode: "EXPLORATORY"
          do_not_use_for_decisions: true
        CI test: fail if any Hunt output lacks synthetic flag

    4_VALIDATION_SYNTHETIC_OUTPUTS:
      file: validation/backtest.py
      action: "Same as Hunt — all synthetic outputs self-identify"
      also: validation/walkforward.py, validation/monte_carlo.py (if they exist)

  invariants:
    INV-LEGACY-FALLBACK-GATED: "Legacy paths require explicit flag; default refuses legacy"
    INV-SYNTHETIC-DATA-ISOLATION: "Pre-Gate-5 Hunt/Validation outputs marked EXPLORATORY"

  tests_required:
    file: tests/test_legacy_guards.py (NEW)
    cases:
      - cfp/bead_adapter import without LEGACY flag → warning emitted
      - Hunt output → synthetic: true present in metadata
      - Validation output → synthetic: true present in metadata
      - Hunt output missing synthetic flag → CI test FAILS
```

---

## TRACK 4: REGISTRY_AND_DOC_HYGIENE

```yaml
T4_REGISTRY_DOC_HYGIENE:
  purpose: "Close documentation drift and registry gaps found across all 3 investigations"

  tasks:
    1_INV_REGISTRY_SYNC:
      action: "Ensure INV-DEXTER-ALWAYS-CLAIM is in root INVARIANT_REGISTRY.yaml"
      status: "Currently doc-only — must be in active registry"
      note: "245 → 246+ (plus S59 additions and S60 ceremony invariant)"

    2_LEASES_README_FIX:
      file: leases/README.md
      action: "Fix state diagram — currently shows 'REVOKED -> HALTED (terminal)' which conflicts with runtime FSM"
      correct: "HALTED is non-terminal, transitions to REVOKED only. Terminal states: EXPIRED, REVOKED."

    3_ATHENA_DISAMBIGUATION:
      action: |
        Add note in appropriate doc (SYSTEM_MANIFEST or REPO_MAP):
        "phoenix/athena/ = Memory discipline (CLAIM/FACT/CONFLICT store)"
        "phoenix/memory/athena/ = Query engine over bead types (different module)"
        Purpose: prevent bridge implementation mistakes from naming confusion.

    4_CALIBRATION_DESIGN_CONTRACT:
      action: |
        Create docs/canon/designs/CALIBRATION_SPEC_v0.1.md (DESIGN ONLY — no implementation)
        Content: Schema for CALIBRATION_BEAD + ceremony integration + drift threshold logic.
        Link calibration_bead existence to ceremony evidence surface.
      note: "CalibrationBead type exists in lease_types.py:533-548 but has no runtime path or tests"
      scope: "Design document only. Implementation is Gate 3+ scope."

    5_SYSTEM_MANIFEST_UPDATE:
      action: "Update a8ra_SYSTEM_MANIFEST to v1.9 (or appropriate) reflecting S59+S60"

    6_SPRINT_ROADMAP_UPDATE:
      action: "Add S59 and S60 entries to SPRINT_ROADMAP.md"

    7_DRIFT_LOG:
      action: "Close any DELTA entries resolved by S59/S60. Add new DELTAs if discovered."

  tests_required:
    - make truth_sync (or equivalent validation) — zero drift between manifest and pytest count
```

---

## EXIT GATES

```yaml
EXIT_GATES:
  G1_CEREMONY:
    criterion: "Full ceremony lifecycle operational — schedule, check, attest, advance"
    test: "tests/test_ceremony.py — all cases pass"
    proof: "pytest tests/test_ceremony.py — 0 failures"

  G2_CSO_DURABLE:
    criterion: "CSO rejection and signal records persist to disk"
    test: "tests/test_cso_durability.py — records on disk after evaluation"
    proof: "pytest tests/test_cso_durability.py — 0 failures"

  G3_LEGACY_GUARDS:
    criterion: "Legacy paths gated + synthetic outputs self-identify"
    test: "tests/test_legacy_guards.py — all guards enforced"
    proof: "pytest tests/test_legacy_guards.py — 0 failures"

  G4_REGISTRY:
    criterion: "INVARIANT_REGISTRY.yaml complete — all new invariants registered"
    test: "make truth_sync — zero drift"
    proof: "validate_registry.py — count matches"

  G5_DOCS:
    criterion: "leases/README fixed, SYSTEM_MANIFEST updated, SPRINT_ROADMAP current"
    test: "Manual review — state diagram matches runtime FSM"
    proof: "CTO or G confirms"

  G6_REGRESSION:
    criterion: "Zero regressions on full test suite"
    test: "pytest — full suite"
    proof: "All S59 tests + S60 tests + existing suite pass"

PASS_CONDITION: "All G1-G6 binary PASS"
FAIL_CONDITION: "Any gate FAIL → halt sprint, report to G"
```

---

## NEW INVARIANTS TO REGISTER

```yaml
register_in_INVARIANT_REGISTRY.yaml:
  INV-CEREMONY-ATTESTATION-DURABLE:
    domain: GOVERNANCE
    tier: TIER_1
    rule: "Attestation bead persists before next_review_due advances"
    proven_by: tests/test_ceremony.py

  INV-LEGACY-FALLBACK-GATED:
    domain: ARCHITECTURE
    tier: TIER_2
    rule: "Legacy code paths require explicit flag; default runtime refuses legacy"
    proven_by: tests/test_legacy_guards.py

  INV-SYNTHETIC-DATA-ISOLATION:
    domain: DATA
    tier: TIER_2
    rule: "Pre-Gate-5 Hunt/Validation outputs carry synthetic:true + MODE:EXPLORATORY"
    proven_by: tests/test_legacy_guards.py

  INV-ECONOMY-ISOLATION-ENFORCED:
    domain: ARCHITECTURE
    tier: TIER_1
    rule: "CI rejects cross-economy coupling outside bridge package"
    proven_by: scripts/check_economy_isolation.py
    note: "May already be registered from S59 — verify, don't duplicate"
```

---

## CONSTRAINTS

```yaml
DO:
  - Verify S59 exit gates still pass before starting
  - Read orientation files (especially S59 deliverables)
  - One track at a time, in order T1→T4
  - Use S59 DurableBeadEmitter for all new bead persistence
  - Register invariants in INVARIANT_REGISTRY.yaml
  - Update SYSTEM_MANIFEST version
  - Commit after each track

DO_NOT:
  - Modify sovereign_gate.py core (S59 — proven)
  - Modify halt.py core (S55 — proven)
  - Implement calibration runtime (design doc only this sprint)
  - Build bridge code (Gate 3 scope)
  - Add features not in this brief
```

---

## WHAT THIS SPRINT UNLOCKS

```yaml
after_S60:
  ceremony: OPERATIONAL (full lifecycle)
  debt: CLEARED (legacy guards, synthetic isolation, doc hygiene)
  registry: COMPLETE (all investigation invariants registered)
  ready_for: GATE_3 (Bridge v0 — Notary boundary implementation)

gate_3_prerequisites_met:
  - CapitalGuard operational (S59)
  - Write-ahead governance (S59)
  - Scalar ban enforced (S59)
  - Ceremony lifecycle (S60)
  - CSO rejection durability (S60)
  - Legacy paths marked (S60)
  - Economy isolation enforced (S59)
  - "All governance surfaces hardened and durable — ready for bridge projection"
```

---

## REFERENCE DOCUMENTS

```yaml
REF:
  - docs/canon/SPRINT_ROADMAP.md
  - docs/canon/a8ra_SYSTEM_MANIFEST_v1_0.md
  - docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md (ceremony sections)
  - INVARIANT_REGISTRY.yaml
  - governance/sovereign_gate.py (S59)
  - governance/bead_emitter.py (S59)
  - governance/ceremony.py (S60 T1 — you'll create this)
  - cso/consumer.py (rejection records)
  - cso/scanner.py (emission points)
```

---

*S60 CEREMONY_AND_HYGIENE: "Complete the governance lifecycle. Clear the debt. Unlock the bridge."*
*Quality > Speed. No jank. Pro standard.*
