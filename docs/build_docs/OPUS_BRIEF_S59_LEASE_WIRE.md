# OPUS BRIEF: S59 LEASE_WIRE
# For: Fresh Opus MAX Session (Cursor)
# From: CTO (Claude) — synthesized from 3 investigations + 3 advisor audits
# Date: 2026-02-25

```yaml
BRIEF: S59.ALL.D1
MISSION: LEASE_WIRE — Push S55 halt hardening from ceremonial gate to execution spine
OWNER: OPUS (Cursor)
FORMAT: DENSE
SPRINT: S59
CODENAME: LEASE_WIRE
```

---

## P0: ORIENTATION (Read Before Coding)

**Read these files in order before any code changes:**

```yaml
orientation_sequence:
  1: docs/canon/SPRINT_ROADMAP.md           # Current state (post-S58)
  2: docs/canon/a8ra_SYSTEM_MANIFEST_v1_0.md # System topology
  3: governance/halt.py                      # S55 halt mechanism (proven)
  4: governance/lease.py                     # State machine + interpreter + manager
  5: governance/insertion.py                 # 8-step insertion protocol
  6: governance/cartridge.py                 # Loader + linter + registry
  7: governance/lease_types.py              # Pydantic models (all bead types)
  8: execution/halt_gate.py                 # Abstract halt gate (built, not wired)
  9: execution/asia_scalp.py                # Execution entry (halt mentioned, not enforced)
  10: state/manifest_writer.py              # HUD projection (silent fail targets)
  11: cso/scanner.py                        # CSO scanner (scalar contradiction)
  12: cso/strategy_core.py                  # CSO core (scalar contradiction)
  13: tests/test_lease/                     # Existing lease test suite (112 tests)
  14: tests/test_halt_signal.py             # S55 halt tests (30 tests)
  15: tests/test_halt_before_exec.py        # Halt gate stub tests
  16: INVARIANT_REGISTRY.yaml               # 245 invariants (add 6 more this sprint)
```

---

## CONTEXT

```yaml
status: a8ra v0.1 post-S58 | ZERO_T1 | ZERO_T2 | 1815+ tests | 245 invariants
prior_work:
  S47: Lease FSM built (5-state, 118 tests, 16 chaos vectors). FSM is SOUND.
  S55: HALT_WIRE — kill switch wired into insertion.py Step 7. Proven with 5 chaos vectors.
  S56: LOUD_FAILS — silent exception hardening on governance paths.

problem: |
  S55 proved halt works through the INSERTION path (front door).
  Investigation 2 (forensic audit) revealed halt is NOT wired into:
    - LeaseStateMachine.activate() — can be called directly, bypasses halt
    - execution/asia_scalp.py — declares halt invariant in docstring only, no actual check
    - position management lifecycle — mid-position scaling/modification unguarded

  Additionally:
    - Governance beads (CartridgeInsertionBead, LeaseActivationBead) emit to in-memory lists only
    - state/manifest_writer.py swallows exceptions and returns GREEN/ABSENT — lies to operator
    - CSO scanner computes quality_score/confidence — violates INV-HARNESS-1 (no grades doctrine)
    - Ceremony governance (weekly attestation) is schema fields only — no runtime enforcement

  Summary: "Constitutional at the Gate, Anarchic at the Trade."
  Fix: Push halt hardening into the execution spine. One disciplined sprint.
```

---

## TRACK 1: CAPITAL_GUARD (@sovereign_gate decorator)

```yaml
T1_CAPITAL_GUARD:
  purpose: "Single chokepoint for ALL capital mutations — no side doors"

  design:
    pattern: "Python decorator @sovereign_gate that wraps any capital-affecting method"
    checks:
      1: check_halt_signal() — fail-closed (HALT.signal present → REJECT)
      2: lease state == ACTIVE (not EXPIRED, REVOKED, HALTED, DRAFT)
      3: ceremony not overdue (next_review_due >= now) — see T5
    on_fail: "Raise SovereignGateError (subclass of appropriate base). Never continue."
    on_exception: "Fail closed. Gate check exception → treat as HALT."

  target_file: governance/sovereign_gate.py (NEW)

  wire_points:
    - governance/lease.py: LeaseStateMachine.activate() — add @sovereign_gate or internal guard
    - execution/asia_scalp.py: entry method — @sovereign_gate
    - execution/halt_gate.py: bind real check_halt_signal (replace lambda stubs)
    - "Any method that can: open position, scale position, modify SL/TP, re-enter after TP"

  invariants_to_enforce:
    - INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS: "HALT blocks entry, scaling, modification, re-entry"
    - INV-ACTIVATION-ONLY-VIA-GUARD: "All activation paths pass through CapitalGuard"
    - INV-GOV-HALT-BEFORE-ACTION: "gate checks halt before capital action" (EXISTING — extend scope)

  tests_required:
    file: tests/test_sovereign_gate.py (NEW)
    cases:
      - halt.signal present → activate() REJECTS
      - halt.signal present → execution entry REJECTS
      - halt.signal present → position scaling REJECTS
      - halt.signal present → position modification REJECTS
      - halt.signal clear + lease ACTIVE → all paths PROCEED
      - halt.signal clear + lease EXPIRED → REJECTS
      - halt.signal clear + lease DRAFT → REJECTS
      - direct LeaseStateMachine.activate() without guard → structurally impossible or fails
      - gate check itself throws exception → treated as HALT (fail-closed)
      - concurrent halt mid-operation → operation aborts

  chaos_vectors:
    file: tests/chaos/test_bunny_s59.py (NEW — append to existing chaos suite)
    vectors:
      - CV1: Halt fires mid-activate() call (race condition)
      - CV2: Halt fires mid-execution-entry (race condition)
      - CV3: Halt fires mid-position-scaling
      - CV4: 10 threads: 5 trying to activate, 5 firing halt simultaneously

  implementation_notes:
    - Do NOT make activate() private — just ensure it checks halt internally
    - The decorator should be usable on any method, not just lease methods
    - check_halt_signal is in governance/halt.py — import and use the real function
    - halt_gate.py already exists with HaltGate class — evaluate whether to compose or replace
    - Keep it simple: decorator reads HALT.signal file, checks lease state, returns or raises
```

---

## TRACK 2: WRITE_AHEAD_GOVERNANCE (Durable Bead Emission)

```yaml
T2_WRITE_AHEAD_GOVERNANCE:
  purpose: "Governance beads persist to disk BEFORE state mutation returns"

  problem:
    current: |
      governance/lease.py lines 58-73: beads emitted to NullBeadEmitter.beads (in-memory list)
      governance/cartridge.py lines 236-246: CartridgeInsertionBead to _beads list
      If process dies → beads vanish → no forensic reconstruction → constitutional violation

  design:
    pattern: "Write-ahead governance — emit bead → persist → then mutate state"
    minimum: "Append-only JSONL file per governance action type"
    preferred: "Wire to existing memory/bead_store.py SQLite if clean integration"

    boot_recovery:
      on_boot: "Check for orphaned active lease file without corresponding live process"
      if_orphan_found: "Trigger immediate HALT until human reconciles via clear_halt.sh"
      rationale: "Stale active lease after crash = unknown state = HALT"

  target_files:
    - governance/bead_emitter.py (NEW) — durable emitter replacing NullBeadEmitter
    - governance/lease.py — swap emitter from NullBeadEmitter → DurableBeadEmitter
    - governance/cartridge.py — swap emitter
    - governance/insertion.py — ensure bead persist happens BEFORE success return

  invariant:
    INV-GOVERNANCE-MUTATION-ATOMIC: "State mutation must only occur after durable bead write succeeds"

  existing_code_refs:
    - governance/lease_types.py:533-548 — CalibrationBead type exists (use as pattern)
    - governance/lease.py:202-211 — current LeaseActivationBead emission point
    - governance/lease.py:58-73 — NullBeadEmitter class (REPLACE)
    - memory/bead_store.py:46-54 — existing SQLite bead store (evaluate as target)

  tests_required:
    file: tests/test_durable_beads.py (NEW)
    cases:
      - insertion complete → CartridgeInsertionBead exists on disk
      - lease activation → LeaseActivationBead exists on disk
      - state transition → corresponding bead on disk BEFORE state change
      - process kill mid-insertion → orphan detected on boot
      - orphan detection → auto-HALT triggered
      - bead file corrupt/unreadable → fail-closed (don't ignore)

  chaos_vectors:
    - CV5: os.kill(pid) mid-insertion → boot recovery finds orphan → HALT
    - CV6: disk full during bead write → insertion FAILS (not silent success)
```

---

## TRACK 3: PROJECTION_HONESTY (manifest_writer fails closed)

```yaml
T3_PROJECTION_HONESTY:
  purpose: "Projection layer never lies — stale data over hallucinated state"

  problem:
    targets:
      - state/manifest_writer.py:466 — get_lease_state() catches ImportError/Exception → returns "ABSENT"
        risk: HIGH — lease subsystem crash looks like "no active lease" → operator sees GREEN
      - state/manifest_writer.py:333 — _lease_color() catches Exception → returns "GREEN"
        risk: MEDIUM — error in lease subsystem → HUD shows green → false confidence
      - state/manifest_writer.py:358 — _calculate_age_seconds() catches Exception → returns 9999
        risk: LOW — parse error masked
      - state/manifest_writer.py:381 — get_next_seq() catches Exception → returns 1
        risk: MEDIUM — sequence corruption hidden

  design:
    rule: "On exception, projection must degrade to UNKNOWN/ERROR/frozen, never GREEN/ABSENT"
    pattern: |
      Option A (preferred): On verification failure, REFUSE to update the manifest file.
      A stale timestamp IS the alarm signal. Operator sees frozen data = knows something broke.

      Option B: Write explicit ERROR/UNKNOWN state to manifest.

      Both are acceptable. GREEN/ABSENT on exception is NEVER acceptable.

  target_file: state/manifest_writer.py

  invariant:
    INV-PROJECTION-NEVER-OPTIMISTIC: "Projection degrades to stale/unknown on exception, never GREEN/ABSENT"

  tests_required:
    file: tests/test_manifest_projection.py (NEW or extend existing)
    cases:
      - ImportError in lease subsystem → get_lease_state returns "UNKNOWN" or "ERROR" (not "ABSENT")
      - Exception in _lease_color → returns "RED" or "UNKNOWN" (not "GREEN")
      - Exception in _calculate_age_seconds → raises or returns sentinel (not 9999)
      - Exception in get_next_seq → raises or returns sentinel (not 1)

  also_check:
    - governance/halt.py:279 — _call_with_retry swallows callback exceptions
      action: "Add mandatory warning log event. Low severity but shouldn't be fully silent."
```

---

## TRACK 4: CSO_SCALAR_DECAPITATION

```yaml
T4_CSO_SCALAR_DECAPITATION:
  purpose: "Remove forbidden scalar fields from CSO emission boundary"

  problem: |
    INV-HARNESS-1 says "gate status only, never grades."
    cso/scanner.py and cso/strategy_core.py still compute quality_score and confidence.
    This is a constitutional violation — doctrine says no grades, code has grades.
    If projected through future bridge → contaminates analytical economy with forbidden patterns.

  classification: T1_CONDITIONAL (constitutional violation exists in production code TODAY)

  target_files:
    - cso/scanner.py — remove quality_score computation and emission
    - cso/strategy_core.py — remove confidence/quality scalar paths
    - cso/harness/__init__.py — verify no scalar re-export
    - Any CSESignal emission point — must emit boolean/enum readiness only

  design:
    replace: "quality_score: float" and "confidence: float"
    with: "readiness_reasons: list[ReadinessReason]" (enum of boolean conditions)
    example_enum: |
      class ReadinessReason(str, Enum):
        TREND_ALIGNED = "trend_aligned"
        VOLUME_CONFIRMED = "volume_confirmed"
        VOLATILITY_WITHIN_BOUNDS = "volatility_within_bounds"
        SESSION_ACTIVE = "session_active"
        GATE_THRESHOLD_MET = "gate_threshold_met"
    rule: "No float/int score fields in any emitted CSESignal. Boolean/enum ONLY."

  invariant:
    INV-CSO-NO-SCALAR-DECISIONS: "No scalar fields consumed by routing/gating/position sizing"

  tests_required:
    file: tests/test_cso_scalar_ban.py (NEW)
    cases:
      - lint: scan all CSESignal emission points → zero float/score fields
      - CSO evaluation run → output contains readiness_reasons enum, no quality_score
      - existing CSO tests still pass with enum readiness (no regression)

  implementation_notes:
    - This is a refactor, not a rewrite. Remove the scalar computation, replace with enum.
    - Existing cso/knowledge/conditions.yaml gates are boolean — they should stay boolean at emission.
    - Check if quality_score is consumed anywhere downstream (narrator, HUD, etc.) and remove those too.
    - grep -r "quality_score\|confidence" cso/ to find all references
```

---

## TRACK 5: CEREMONY_STUB (Minimum Viable Attestation Check)

```yaml
T5_CEREMONY_STUB:
  purpose: "If next_review_due < now → lease execution blocked"

  problem: |
    governance/lease_types.py lines 406-417: next_review_due field EXISTS in schema.
    Zero runtime enforcement. No code checks it.
    Lease can run indefinitely without human attestation.
    Even paper trading, this compounds edge decay invisibly.

  design:
    scope: MINIMUM VIABLE — tick check only, no ceremony workflow
    rule: "If next_review_due is set and world_time > next_review_due → HALTED"
    transition: "Lease → HALTED state (not EXPIRED, not REVOKED — force conscious review)"

    integration_point: |
      Best: Integrate into @sovereign_gate decorator (T1).
      Gate checks: halt_signal → lease_state → ceremony_due.
      If ceremony overdue → treat as halt condition.

    what_this_does_NOT_include:
      - Attestation bead emission
      - Review workflow UI
      - Ceremony scheduling engine
      - next_review_due auto-calculation on renewal
      These are S60 scope.

  target_files:
    - governance/sovereign_gate.py — add ceremony_due check to gate
    - governance/lease.py — add method to check ceremony status

  invariant:
    INV-CEREMONY-BLOCKS-ACTIVE: "Overdue review halts lease execution"

  tests_required:
    file: tests/test_ceremony_stub.py (NEW)
    cases:
      - lease with next_review_due in future → execution PROCEEDS
      - lease with next_review_due in past → execution BLOCKED (HALTED)
      - lease with next_review_due = None → execution PROCEEDS (no ceremony required)
      - lease transitions to HALTED when ceremony overdue (not EXPIRED)
```

---

## TRACK 6: ISOLATION_GUARDS (CI Enforcement)

```yaml
T6_ISOLATION_GUARDS:
  purpose: "CI enforcement of Two-Economy boundary — no accidental coupling"

  design:
    script: scripts/check_economy_isolation.py (NEW)
    hook: .pre-commit-config.yaml or Makefile target

    guards:
      G1: "No phoenix/ imports from dexter/* (grep -r 'from dexter\|import dexter' phoenix/)"
      G2: "No dexter/ imports from phoenix/* (grep -r 'from phoenix\|import phoenix' dexter/ — if in same repo context)"
      G3: "No cross-economy filesystem writes (no phoenix code writing to dexter paths)"
      G4: "Future bridge package = only allowed cross-economy dependency (allowlist)"

    exception_allowlist:
      - "bridge/ directory (when it exists) may import from both — this is its purpose"
      - "Test files may reference both for integration testing (explicit marker required)"

  invariant:
    INV-ECONOMY-ISOLATION-ENFORCED: "CI rejects cross-economy coupling outside bridge package"

  tests_required:
    - Script itself acts as test — run in CI, fail on violation
    - Add to Makefile: make check-isolation

  implementation_notes:
    - This is a shell script or simple Python scanner. Half-day work.
    - Run as part of existing make truth_sync or similar validation target.
    - Currently repos are physically separate (phoenix/ vs dexter/) — guard prevents future drift.
```

---

## EXIT GATES

```yaml
EXIT_GATES:
  G1_CAPITAL_GUARD:
    criterion: "No capital path reachable while HALT.signal present"
    test: "tests/test_sovereign_gate.py — all decorated paths reject when halted"
    proof: "pytest tests/test_sovereign_gate.py — 0 failures"

  G2_WRITE_AHEAD:
    criterion: "Governance beads durable before state mutation"
    test: "tests/test_durable_beads.py — bead on disk before state change"
    proof: "pytest tests/test_durable_beads.py — 0 failures"

  G3_PROJECTION:
    criterion: "Projection layer never returns optimistic fallback"
    test: "tests/test_manifest_projection.py — no GREEN/ABSENT on exception"
    proof: "pytest tests/test_manifest_projection.py — 0 failures"

  G4_SCALAR_BAN:
    criterion: "CSO emits zero scalar fields in signals"
    test: "tests/test_cso_scalar_ban.py — lint passes, no quality_score in emissions"
    proof: "pytest tests/test_cso_scalar_ban.py — 0 failures"

  G5_CEREMONY:
    criterion: "Overdue ceremony blocks execution"
    test: "tests/test_ceremony_stub.py — past due → blocked"
    proof: "pytest tests/test_ceremony_stub.py — 0 failures"

  G6_ISOLATION:
    criterion: "CI rejects cross-economy coupling"
    test: "scripts/check_economy_isolation.py — zero violations"
    proof: "python scripts/check_economy_isolation.py — exit 0"

  G7_REGRESSION:
    criterion: "Zero regressions on existing test suite"
    test: "pytest — full suite"
    proof: "pytest — 1815+ pass, 0 new failures"

PASS_CONDITION: "All G1-G7 binary PASS"
FAIL_CONDITION: "Any gate FAIL → halt sprint, report to G"
```

---

## NEW INVARIANTS TO REGISTER

```yaml
register_in_INVARIANT_REGISTRY.yaml:
  INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS:
    domain: GOVERNANCE
    tier: TIER_1
    rule: "HALT blocks entry, scaling, modification, re-entry — not just initial activation"
    proven_by: tests/test_sovereign_gate.py

  INV-ACTIVATION-ONLY-VIA-GUARD:
    domain: GOVERNANCE
    tier: TIER_1
    rule: "All activation/execution paths pass through sovereign gate"
    proven_by: tests/test_sovereign_gate.py

  INV-GOVERNANCE-MUTATION-ATOMIC:
    domain: GOVERNANCE
    tier: TIER_1
    rule: "State mutates only after durable bead write succeeds"
    proven_by: tests/test_durable_beads.py

  INV-PROJECTION-NEVER-OPTIMISTIC:
    domain: MONITORING
    tier: TIER_2
    rule: "Projection degrades to stale/unknown on exception, never GREEN/ABSENT"
    proven_by: tests/test_manifest_projection.py

  INV-CSO-NO-SCALAR-DECISIONS:
    domain: CSO
    tier: TIER_1
    rule: "No scalar fields in emitted CSESignal; boolean/enum readiness only"
    proven_by: tests/test_cso_scalar_ban.py

  INV-CEREMONY-BLOCKS-ACTIVE:
    domain: GOVERNANCE
    tier: TIER_1
    rule: "Overdue ceremony review halts lease execution"
    proven_by: tests/test_ceremony_stub.py
```

---

## REPORT FORMAT

```yaml
REPORT_FORMAT: DENSE

on_track_completion:
  format: |
    T{N}_{NAME}: COMPLETE
    files_modified: [list]
    files_created: [list]
    tests_added: N
    invariants_proven: [INV-*]
    regressions: 0|N
    notes: {any deviation from brief}

on_sprint_completion:
  format: |
    S59_LEASE_WIRE: COMPLETE
    tracks: {N}/{N}
    tests_added: N (total now N)
    invariants_added: N (total now N)
    chaos_vectors: N
    regressions: 0
    exit_gates: G1-G7 all PASS
```

---

## CONSTRAINTS

```yaml
DO:
  - Read orientation files FIRST (P0 above)
  - Run existing tests before ANY changes (baseline)
  - One track at a time, in order T1→T6
  - Register invariants in INVARIANT_REGISTRY.yaml
  - Update SYSTEM_MANIFEST version (1.7→1.8)
  - Commit after each track with clear message

DO_NOT:
  - Rewrite existing lease FSM (it's proven — S47, 118 tests)
  - Modify halt.py core mechanism (it's proven — S55)
  - Add features not in this brief
  - Use assert for invariant enforcement (use raise — survives python -O)
  - Skip the orientation read
  - Combine tracks into single commits
```

---

## REFERENCE DOCUMENTS

```yaml
REF:
  - docs/canon/SPRINT_ROADMAP.md
  - docs/canon/a8ra_SYSTEM_MANIFEST_v1_0.md
  - docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md
  - INVARIANT_REGISTRY.yaml
  - governance/halt.py (S55 proven halt mechanism)
  - governance/lease.py (S47 state machine)
  - governance/insertion.py (S47+S55 insertion protocol)
  - execution/halt_gate.py (abstract gate — wire it)
  - state/manifest_writer.py (silent fail targets)
```

---

*S59 LEASE_WIRE: "Push hardening from the ceremonial gate to the execution spine."*
*Quality > Speed. No jank. Pro standard.*
