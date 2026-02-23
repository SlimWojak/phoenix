# S52 HARDENING SPRINT — OPUS BUILD BRIEF

```yaml
BRIEF: S52.HARDENING.D1
MISSION: POST_AUDIT_HARDENING
OWNER: OPUS (Primary Builder)
FORMAT: DENSE
DATE: 2026-02-23
FROM: CTO (Claude, a8ra)
```

---

## 0. WHY YOU'RE READING THIS

You (Opus) just completed a forensic audit of the entire a8ra codebase.
That audit lives at `~/phoenix/docs/forensic_audit/FORENSIC_AUDIT.md`.
You found 12 risks. CTO triaged them with input from three advisors
(OWL/GPT/BOAR). Three are TIER_1 — capital path risks that need fixing
before any further feature work.

This brief scopes the hardening sprint. Four tracks. Tight scope.
No feature creep. Ship and prove.

---

## 1. SYSTEM STATE (Post-S51)

```yaml
PROVEN:
  phoenix_v0.1: SEALED
  tests: 1690+ passing (1665 confirmed + 25 xfailed)
  chaos_vectors: 264
  frozen_invariants: 150+
  halt_latency: 0.003ms local, 22.59ms cascade
  river: S51 complete — schema, writer, reader, streamer, seam, enrichment L1-L7
  bead_field: Gate 1 PASS — 789 genesis beads, signed ML-DSA-65, bi-temporal store
  execution: Paper broker proven, IBKR connector operational
  governance: Cartridge→Lease→T2→Halt chain built and tested

WHAT_JUST_HAPPENED:
  - S51 Driveshaft/River shipped (market data foundation)
  - Full forensic audit completed via RepoPrompt oracle + Opus
  - 12 risks found, 3 TIER_1 (capital path), advisor-validated
  - All three advisors (OWL, GPT, BOAR) independently confirmed same priorities
```

---

## 2. THE THREE TIER_1 RISKS (Your Audit Findings)

### RISK-1: Dual Position State Machine (LIVE_RISK — HIGH)

```yaml
finding: |
  Two coexisting position FSMs in execution path:
    OLD: execution/position.py — 5 states (PENDING/OPEN/PARTIAL/CLOSED/HALTED)
    NEW: execution/positions/states.py — 9 states (includes SUBMITTED/FILLED/STALLED)

  Mixed imports:
    broker_stub.py:194 → imports from execution.position (OLD)
    execution/__init__.py:3254 → exports from execution.positions (NEW)

why_critical: |
  Callers can get different FSMs from different import paths.
  Race condition: one path says OPEN, other says HALTED.
  Fill happens on stale state. Silent capital loss.
  Advisor (BOAR): "Two kings ruling the same realm."
  Advisor (OWL): "Two truths is zero truths."

your_audit_ref: "FORENSIC_AUDIT.md Section 8 DELTA-6, Section 10 RISK-1"
```

### RISK-3: Bounds Enforcement Not Auto-Fed (LIVE_RISK — HIGH)

```yaml
finding: |
  governance/lease.py:396 LeaseInterpreter.check_all_bounds() requires
  caller to provide current_drawdown_pct, consecutive_losses, daily_loss_pct.
  No automatic sourcing from broker/position state.
  If monitoring loop crashes or caller forgets, bounds are never checked.

why_critical: |
  A governance invariant that requires manual invocation is not an invariant.
  Advisor (OWL): "Must be passive and atmospheric, not active and episodic."
  Advisor (GPT): "Governance theater — bounds without auto-feed = suggestion."
  Advisor (BOAR): "Daemon crashes, watcher crashes, nobody notices. Silent drawdown."

your_audit_ref: "FORENSIC_AUDIT.md Section 6.4 FINDING-5, Section 10 RISK-3"
```

### RISK-7: River Freshness Untested (LIVE_RISK — MEDIUM-HIGH)

```yaml
finding: |
  cso/market_state_builder.py:107 has STALENESS_THRESHOLD_MINUTES constant.
  No test proves stale data is actually refused.
  If threshold check has a bug, stale market data reaches gate evaluation.

why_critical: |
  IBKR goes down → River serves yesterday's data → enrichment runs on stale bars →
  gate evaluator passes a setup based on prices that no longer exist →
  CSE fires → T2 approves → order on expired price.
  Advisor (BOAR): Traced full kill chain from stale bar to capital loss.

additional_risk: |
  BOAR found a hidden risk Opus missed (compressed modules):
  CSE emitted from stale MarketState carries no River provenance.
  routing.py routes to T2 without freshness check.
  Defense-in-depth gap: even if builder catches staleness, downstream has no guard.

your_audit_ref: "FORENSIC_AUDIT.md Section 7.3, Section 10 RISK-7"
```

---

## 3. FOUR TRACKS

### T1: KILL OLD FSM

```yaml
TASK:
  1. Identify ALL importers of execution/position.py (grep the full codebase)
  2. Migrate broker_stub.py to import from execution/positions/
  3. Migrate replay.py to import from execution/positions/
  4. Migrate any other importers found in step 1
  5. Map state equivalences (5-state → 9-state) and update transition logic
  6. Add deprecation guard: importing execution/position.py must raise ImportError
     with message directing to execution/positions/
  7. Verify execution/__init__.py exports are clean and canonical
  8. Run full test suite — zero regressions

DELIVERABLES:
  code:
    - execution/position.py (gutted to ImportError raiser)
    - execution/broker_stub.py (migrated imports)
    - execution/replay.py (migrated imports)
    - execution/__init__.py (verified canonical exports)
  tests:
    - tests/test_deprecated_position_import.py (assert old import raises)

EXIT_GATE:
  T1_SINGLE_FSM:
    criterion: "One canonical position FSM. Old import hard-fails."
    test: "pytest tests/ — zero regressions + new deprecation test passes"
    proof: "grep -r 'from execution.position import' returns only the deprecation guard"
```

### T2: PASSIVE BOUNDS (Sentinel Pattern)

```yaml
DESIGN_CONTRACT (from OWL advisor — implement this pattern):

  The GovernanceSentinel wraps the PositionTracker. State cannot update
  without passing through bounds enforcement. This is NOT a cron job
  that checks periodically — it fires ON EVERY STATE UPDATE.

  interface:
    GovernanceSentinel(ABC):
      intercept(state: SystemState) -> GovernanceVerdict:
        "Passive check. FAIL → ExecutionEngine MUST transition to HALTED."
      heartbeat() -> bool:
        "Self-check. If sentinel stale/crashed → system fail-safes to HALT."

  implementation_strategy:
    step_a: "Pre-commit hook on PositionTracker — before any PnL/position update
             is finalized, pass state to LeaseInterpreter.check_all_bounds()"
    step_b: "MonitoringLoop becomes verdict engine:
             Update State → Sentinel.intercept(state) → Commit or Kill"
    step_c: "Dead-man's switch — if check_all_bounds() hasn't executed within
             N seconds, trigger HALT. Governance must be the most alive part."

  wiring:
    - PositionTracker.get_stats() provides: current_drawdown_pct,
      consecutive_losses, daily_loss_pct
    - These feed AUTOMATICALLY into LeaseInterpreter.check_all_bounds()
    - No manual caller needed. Bounds fire on tracker update.
    - Observable heartbeat proves liveness

  latency_note: |
    Running LeaseInterpreter on every tick adds micro-latency ("Sovereign Tax").
    Acceptable for discretionary/semi-freq trading. Not HFT.

  state_locking_note: |
    While Sentinel checks state, execution engine cannot change it.
    Prevents race condition where position closes during bounds calculation.

TASK:
  1. Create GovernanceSentinel ABC in governance/ (or extend GovernanceInterface)
  2. Implement BoundsSentinel wrapping LeaseInterpreter.check_all_bounds()
  3. Wire into PositionTracker update cycle as pre-commit interceptor
  4. Implement heartbeat with configurable staleness threshold
  5. Implement dead-man's switch: sentinel silent > N seconds → HALT
  6. Add INV-BOUNDS-HEARTBEAT invariant + test
  7. Test: daemon crash simulation → system halts (not silently continues)
  8. Test: bounds breach during position update → immediate halt
  9. Test: heartbeat proves liveness under normal operation

DELIVERABLES:
  code:
    - governance/sentinel.py (GovernanceSentinel ABC + BoundsSentinel)
    - governance/lease.py (updated — auto-feed wiring)
    - execution/positions/tracker.py or equivalent (sentinel integration)
    - monitoring/ updates (heartbeat observable)
  tests:
    - tests/test_sentinel/test_bounds_autofeed.py
    - tests/test_sentinel/test_deadmans_switch.py
    - tests/test_sentinel/test_heartbeat_liveness.py
    - tests/test_sentinel/test_crash_halts_system.py

EXIT_GATE:
  T2_PASSIVE_BOUNDS:
    criterion: "Bounds enforcement is automatic. Heartbeat proves liveness. Crash → HALT."
    test: "All sentinel tests pass. No manual bounds invocation required."
    proof: |
      1. Position update without sentinel attached → fails/raises
      2. Bounds breach during update → halt fires automatically
      3. Sentinel silent > threshold → system halts
      4. Normal operation → heartbeat observable
```

### T3: FRESHNESS DEFENSE (River + CSE Provenance)

```yaml
TASK:
  1. Write test: feed data older than STALENESS_THRESHOLD_MINUTES to
     market_state_builder → assert cold_start path taken, no signal produced
  2. Verify: remove the threshold constant → test FAILS (proves it's not theater)
  3. Add River provenance to MarketStateBuildReport if not already present:
     - river_latest_bar_timestamp
     - river_knowledge_time
     - river_bar_hash (sample)
  4. Thread provenance into CSE emission: CSESignal must carry river KT provenance
     so downstream (routing, T2) can verify freshness independently
  5. Test: CSE with stale river KT → routing refuses (defense-in-depth)
  6. Test: end-to-end stale data kill chain — stale bar → builder → scanner →
     assert no CSE emitted OR CSE refused by consumer

DELIVERABLES:
  code:
    - cso/market_state_builder.py (provenance fields if needed)
    - cso/scanner.py (CSE carries river provenance)
    - cso/consumer.py (freshness check on incoming CSE)
  tests:
    - tests/test_river_freshness/test_stale_data_refused.py
    - tests/test_river_freshness/test_threshold_removal_fails.py
    - tests/test_river_freshness/test_cse_provenance.py
    - tests/test_river_freshness/test_stale_cse_refused.py

EXIT_GATE:
  T3_FRESHNESS:
    criterion: "Stale data refused at source. CSE carries provenance. Downstream guards exist."
    test: "All freshness tests pass. Threshold removal breaks tests."
    proof: "Full kill chain tested: stale bar → no signal reaches T2."
```

### T4: DOC HONESTY

```yaml
TASK:
  1. Create docs/canon/DRIFT_LOG.md with all 12 forensic deltas:
     - Each entry: id, category (A_STALE_SPEC / B_MISSING_CODE / C_REAL_BUG),
       disposition, owner, date, commit ref when fixed
  2. Create INVARIANT_REGISTRY.yaml (flat, lintable):
     - Fields: id, tier, domain, status (PROVEN/ENFORCED/UNTESTED/DESIGNED),
       proven_by, test_refs, last_verified
     - Seed with all invariants from FORENSIC_AUDIT Section 3
     - Mark UNTESTED_INVARIANT for: INV-SOVEREIGN-ANCHOR, INV-EXECUTION-FIDELITY,
       INV-BRIDGE-PROMOTION-GATE, INV-DEPLOYMENT-AUDIT, INV-RIVER-FRESHNESS (until T3 ships)
  3. Update BEAD_FIELD_SPEC Section 6.1: 981 → 789 genesis count
  4. Update river/__init__.py: export RiverReader, RiverWriter, RiverStreamer, Seam
  5. Audit these docs for present-tense claims about unbuilt features:
     - SYSTEM_MANIFEST integration_with_bead_field → "DESIGNED_NOT_BUILT (Gate 3+)"
     - BEAD_FIELD_SPEC AIR section → "DESIGNED_NOT_BUILT (Gate 3)"
     - BEAD_FIELD_SPEC Sovereign Anchor → "DESIGNED_NOT_BUILT (Gate 7)"
     - BEAD_FIELD_SPEC Dolt → "SUPERSEDED by git-based coordination"
     - CONSTITUTION/ → Add README: "Skeleton. Invariants enforced in code, not YAML.
       See INVARIANT_REGISTRY.yaml for canonical list."
  6. Update SYSTEM_MANIFEST position lifecycle to reference canonical FSM only

DELIVERABLES:
  docs:
    - docs/canon/DRIFT_LOG.md
    - INVARIANT_REGISTRY.yaml (root or docs/canon/)
    - BEAD_FIELD_SPEC (genesis count fix)
    - SYSTEM_MANIFEST (bridge language, FSM reference, capability claims)
    - CONSTITUTION/README.md (honest status)
    - river/__init__.py (exports)

EXIT_GATE:
  T4_HONEST_DOCS:
    criterion: "Zero claims of capabilities that don't exist in code."
    test: "Manual review — every DESIGNED_NOT_BUILT labeled with gate number."
    proof: "DRIFT_LOG.md has disposition for all 12 deltas."
```

---

## 4. EXECUTION ORDER

```yaml
RECOMMENDED_SEQUENCE:
  1_FIRST: T1 (Kill Old FSM) — smallest scope, highest risk, unblocks confidence
  2_SECOND: T3 (Freshness Defense) — test-heavy, fast, proves river integrity
  3_THIRD: T2 (Passive Bounds) — largest scope, new pattern, needs T1 done first
  4_PARALLEL: T4 (Doc Honesty) — can ride alongside any track

RATIONALE: |
  T1 removes the dual-FSM ambiguity that T2 depends on (sentinel wraps positions/,
  not position.py). T3 is fast wins. T2 is the architectural lift.
```

---

## 5. CONSTRAINTS

```yaml
SCOPE_LOCK:
  IN_SCOPE: "TIER_1 risks + doc cleanup. Nothing else."
  NOT_IN_SCOPE:
    - Two-economy bridge (Gate 3+)
    - AIR runtime (Gate 3)
    - HSM / Sovereign Anchor (Gate 7)
    - CONSTITUTION/ population (deferred)
    - Scanner→T2 integration test (TIER_2, next sprint)
    - Deployment config audit (TIER_2, pre-live)

QUALITY:
  - Zero test regressions (all 1690+ must pass)
  - New tests must fail when protection is removed
  - DENSE report format on completion

REFERENCE:
  forensic_audit: "~/phoenix/docs/forensic_audit/FORENSIC_AUDIT.md"
  system_manifest: "a8ra_SYSTEM_MANIFEST.md (project knowledge)"
  master_plan: "a8ra_MASTER_PLAN.md (project knowledge)"
```

---

## 6. EXIT GATES (Sprint Level)

```yaml
S52_PASS:
  T1_SINGLE_FSM: "One canonical FSM. Old import raises. Zero regressions."
  T2_PASSIVE_BOUNDS: "Bounds automatic. Heartbeat proves liveness. Crash → HALT."
  T3_FRESHNESS: "Stale data refused. CSE carries provenance. Kill chain tested."
  T4_HONEST_DOCS: "Zero false capability claims. DRIFT_LOG complete. Registry seeded."

POST_FIX_VERIFICATION:
  criterion: "RepoPrompt oracle rerun on hardened codebase. Assert zero new TIER_1 risks."
  rationale: "BOAR catch — fixes could introduce new deltas. Verify."

S52_FAIL:
  - "Any test regression in existing 1690+ suite"
  - "Sentinel pattern introduces >10ms latency per tick"
  - "Scope creep beyond TIER_1 risks"

REPORT_FORMAT: DENSE
REPORT_TO: CTO (Claude, a8ra project in claude.ai)
```

---

```
BRIEF ENDS. Four tracks. Tight scope. Ship and prove.
```
