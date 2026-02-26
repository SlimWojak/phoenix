CTO REPORT

INTEGRITY_SWEEP: PHOENIX_CORE (non-capital-path)
date: 2026-02-25
assessor: CTO
method: RepoPrompt oracle export (codemap + discovery notes)

# ═══════════════════════════════════════════════════════════════
# DIRECTORY INVENTORY
# ═══════════════════════════════════════════════════════════════

directory_inventory:

  # --- INFRASTRUCTURE (S34/S40 vintage) ---
  
  - path: daemons/
    status: REAL
    sprint_origin: S34 (routing, watcher), S40 (self-healing)
    verdict: |
      Functional file-seam spine. IntentRouter with priority queue,
      exactly-once hash guard, quarantine flow. HALT priority routing
      PROVEN by test_halt_priority.py. create_halt_handler() wires
      to governance.halt.HaltManager — this is the INTERNAL halt path
      (distinct from swarm HALT.signal gap).
    notes: "StubHandler exists (create_stub_handler) — returns markdown stubs for unimplemented intents. Honest about what's missing."

  - path: monitoring/
    status: REAL (with silent-fail concern)
    sprint_origin: S40
    verdict: |
      AlertManager with debounce, threshold checks, auto-halt escalation.
      kill_manager.py maintains kill-bead state. Operational but
      callback failures are logged-not-blocking and kill_manager has
      silent except-pass paths.
    notes: "kill_manager.py silent fails flagged below"

  - path: notification/
    status: REAL (with silent-fail concern)
    sprint_origin: S41
    verdict: |
      alert_taxonomy.py — routing and bundling logic operational.
      Handler exceptions swallowed with pass. Wired to narrator output.
    notes: "Exception swallowing is deliberate (alert delivery = best-effort) but worth documenting as design choice vs bug"

  - path: orientation/
    status: REAL
    sprint_origin: S34 (D3 verification)
    verdict: |
      generator.py + validator.py. KILL_TEST proven by drills/d3_verification.py.
      Many fallback defaults (env vars, provider counts) — orientation
      degrades to defaults rather than failing. Writes state/orientation.yaml.
    notes: "Fallback-heavy but tested. D3 harness validates end-to-end."

  - path: narrator/
    status: STALE
    sprint_origin: S41
    verdict: |
      data_sources.py has PLACEHOLDER fetchers (Athena, River, Tests).
      renderer.py has narrator_emit() chokepoint (S41 proven).
      But data_sources appear to be stubs returning fallback data —
      never wired to live Phoenix modules post-S41.
    notes: "narrator_emit() is real. Data feeding it is not."

  - path: state/
    status: REAL (partial)
    sprint_origin: S42 (health_writer), S48 (manifest_writer)
    verdict: |
      manifest_writer.py projects to HUD. Has EXPLICIT stub sections
      and graceful fallbacks (decay: GREEN default). health_writer.py
      wired for CSO health consumption. Honest about what's real vs stubbed.
    notes: "Stub sections in manifest_writer are LABELED — not silent. Good pattern."

  - path: widget/
    status: STALE
    sprint_origin: S34
    verdict: |
      surface_renderer.py — strict projection, blank-on-missing.
      Predecessor to HUD (surfaces/hud/). Likely superseded by S48 HUD.
    notes: "Not dead (no import errors) but functionally replaced by HUD surface."

  - path: surfaces/hud/
    status: REAL
    sprint_origin: S48
    verdict: |
      WarBoarHUD SwiftUI app. ManifestWatcher.swift watches Phoenix
      manifest with DispatchSource + fallback polling + stale detection.
      Falls back to MockManifest.json — honest about mock vs live.
    notes: "Functional app. Mock fallback is explicit, not silent."

  # --- ANALYTICS (S35-S39 constitutional ceiling) ---

  - path: cfp/
    status: REAL (with conservative fallbacks)
    sprint_origin: S35
    verdict: |
      river_adapter.py has multiple fallback empty/conservative returns.
      Partial metric placeholders (win_rate, pnl). Query executor works
      but returns safe defaults when data missing.
    notes: "62 tests from S35. Conservative fallback = correct for conditional facts."

  - path: athena/
    status: REAL
    sprint_origin: S37
    verdict: |
      store.py — typed store with strict CLAIM/FACT/CONFLICT separation.
      Invariant framing intact.
    notes: "51 tests from S37. Clean."

  - path: hunt/
    status: REAL
    sprint_origin: S38
    verdict: |
      queue.py — PriorityForbiddenError enforces FIFO (no ranking).
      Exhaustive grid pattern intact.
    notes: "69 tests from S38. Constitutional pattern holding."

  - path: validation/
    status: REAL (with synthetic concern)
    sprint_origin: S39
    verdict: |
      backtest.py uses SYNTHETIC/RANDOMIZED metric generation.
      This is the validation harness, not production — but it means
      backtest results are illustrative, not real.
    notes: "109 tests. Synthetic output generation is LABELED as such in context. Not a silent fail but worth noting for anyone expecting real backtest results."

  - path: enrichment/
    status: REAL (with explicit stubs)
    sprint_origin: S51
    verdict: |
      L1-L6 production (155 columns). L7 Asia Scalp wired.
      l2_reference_levels.py has _add_stubbed_columns() explicitly
      inserting Phase-3 stub columns. LABELED, not silent.
    notes: "Stubbed columns are honest markers for future work. Pipeline end-to-end validated in S51."

  # --- ENFORCEMENT ---

  - path: tools/hooks/
    status: REAL
    sprint_origin: S41
    verdict: |
      scalar_ban_hook.py — constitutional lint, commit blocking.
      Pre-commit enforcement of language/metric constraints.
    notes: "Active enforcement. Firing on commits."

  - path: slm/
    status: REAL (with TODO)
    sprint_origin: S41
    verdict: |
      Classification API (rule-based, 100% accuracy per S41).
      train_slm.py has explicit TODO for LoRA adapter loading.
      Core classification operational, training pipeline incomplete.
    notes: "The TODO is in the training path, not the inference path. Classification works."

  - path: drills/
    status: REAL
    sprint_origin: S33-S41
    verdict: |
      d3_verification.py — D3 harness for orientation invariants.
      s41_phase3_live_validation.py — real Gateway validation.
    notes: "Validation infrastructure. Functional."

  - path: scripts/
    status: REAL
    sprint_origin: S53-S54
    verdict: |
      validate_manifest.py, validate_registry.py — auto-sync and
      enforcement. validate_registry.py explicitly treats dexter/ refs
      as cross-repo skips (HONEST about boundary).
    notes: "deployment_audit.py also present — INV-DEPLOYMENT-AUDIT."

  # --- THE SKELETON ---

  - path: CONSTITUTION/
    status: SKELETON
    sprint_origin: S28 (original), never completed
    verdict: |
      README.md self-declares SKELETON (<5% populated).
      CONSTITUTION_MANIFEST.yaml declares broad taxonomy — aspirational.
      modules/README.md = "to be created"
      wiring/README.md = "to be created"
      invariants/INV-GOV-HALT-BEFORE-ACTION.yaml = one real entry.
      Referenced scripts don't exist.
    notes: |
      MITIGATED by DELTA-7: INVARIANT_REGISTRY.yaml (240 entries)
      is now the canonical tracking. CONSTITUTION/ is an organizational
      artifact from S28 that was never populated because the invariants
      live IN CODE with test enforcement instead. Not a gap — a superseded
      pattern. But should be either completed or archived to avoid confusion.

  - path: config/
    status: REAL (with placeholder)
    sprint_origin: S43
    verdict: |
      schema.py — Pydantic centralized config (S43 proven).
      profiles/live.yaml — EXPLICITLY LABELED PLACEHOLDER.
      conditions.yaml — current and canonical.
    notes: "live.yaml placeholder is honest. Will need real values pre-live."

  - path: approval/
    status: NOT_IN_EXPORT
    verdict: "evidence.py not visible in this export. Cannot assess."

  - path: cartridges/ + leases/
    status: DEFERRED
    verdict: "Separate surgical pass as agreed."

# ═══════════════════════════════════════════════════════════════
# SILENT FAILS
# ═══════════════════════════════════════════════════════════════

silent_fails:

  - file: monitoring/kill_manager.py
    risk: T2
    description: |
      Multiple `except Exception: pass` paths around kill-bead writes.
      If bead storage fails, kill state is lost silently. Capital-adjacent.

  - file: notification/alert_taxonomy.py
    risk: T3
    description: |
      Handler exceptions swallowed with pass. Deliberate (best-effort
      delivery) but alert loss is invisible.

  - file: daemons/watcher.py
    risk: T3
    description: |
      Silent duplicate cleanup (pass). Exactly-once guard is solid
      but hash cleanup failure is invisible.

  - file: narrator/data_sources.py
    risk: T3
    description: |
      Placeholder fetchers return fallback data. Narrator renders
      as if data is real. Consumer can't distinguish real vs fallback.

  - file: cfp/river_adapter.py
    risk: T3
    description: |
      Empty/conservative returns on missing data. Correct behavior
      for conditional facts but caller may not realize data was absent.

# ═══════════════════════════════════════════════════════════════
# CROSS-REFS
# ═══════════════════════════════════════════════════════════════

cross_refs:
  - source: scripts/validate_registry.py
    target: dexter/
    status: "SKIP (explicit cross-repo exclusion — honest)"

  - source: CONSTITUTION/CONSTITUTION_MANIFEST.yaml
    target: "multiple phoenix/ modules"
    status: "ASPIRATIONAL — references modules that exist but mapping is stale"

  - source: narrator/data_sources.py
    target: "athena/, river/"
    status: "STUB fetchers — interfaces declared, implementations placeholder"

  - source: daemons/routing.py
    target: governance/halt.py
    status: "REAL — create_halt_handler() → HaltManager. Tested."

  - source: state/manifest_writer.py
    target: "HUD surfaces/hud/"
    status: "REAL — manifest.json consumed by ManifestWatcher.swift"

# ═══════════════════════════════════════════════════════════════
# DEAD CODE CANDIDATES
# ═══════════════════════════════════════════════════════════════

dead_code:
  - path: widget/surface_renderer.py
    reason: "Superseded by surfaces/hud/. No import errors but functionally replaced."

  - path: CONSTITUTION/modules/ + CONSTITUTION/wiring/
    reason: "Empty template directories. Superseded by INVARIANT_REGISTRY.yaml."

  - path: narrator/data_sources.py (fetcher implementations)
    reason: "Placeholder fetchers never wired to live data. Renderer works but is fed stubs."

# ═══════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════

summary:
  directories_assessed: 17
  real: 12 (daemons, monitoring, orientation, state, surfaces/hud,
            cfp, athena, hunt, validation, enrichment, tools/hooks,
            scripts, drills, slm, config)
  stale: 2 (narrator data_sources, widget)
  skeleton: 1 (CONSTITUTION/ — mitigated by registry)
  not_assessed: 2 (approval, cartridges/leases deferred)

  t1_risks: 0
    # Capital path was S54-swept. Non-capital has no T1.

  t2_risks: 1
    - "kill_manager.py silent except-pass on bead writes — kill state loss invisible"

  t3_risks: 4
    - "notification handler exception swallowing"
    - "watcher hash cleanup silent pass"
    - "narrator placeholder fetchers indistinguishable from real data"
    - "cfp conservative fallbacks silent to caller"

  overall_verdict: |
    Phoenix non-capital-path is SUBSTANTIALLY REAL. 12 of 17 directories
    are functional, tested code from proven sprints. The S35-S39
    constitutional ceiling modules (cfp, athena, hunt, validation) are
    intact and holding their invariants.

    No T1 risks found. The single T2 (kill_manager silent fails) is
    capital-adjacent and should be hardened. CONSTITUTION/ is a known
    skeleton but mitigated by the registry — recommend archiving or
    completing to avoid future confusion.

    The narrator and widget are the weakest modules — both functionally
    superseded but not cleaned up. Dead code candidates, not risks.

    Compared to phoenix-swarm: Phoenix is in dramatically better shape.
    The capital path (S54-swept) plus this non-capital audit gives us
    high confidence the engine is sound. Remaining work is hygiene
    (dead code cleanup, silent-fail hardening) not structural.

    GPT REVIEW

    directory_inventory:

  daemons:
    classification: REAL
    evidence:
      - routing.py implements Intent, hashing, immutability verification, HALT handler wiring.
      - watcher.py enforces exactly-once via hash guard + quarantine flow.
      - tests/daemons/test_halt_priority.py proves HALT priority ordering.
    risk:
      - parse_intent() returns None on failure (silent drop path).
      - create_stub_handler() writes stub markdown responses (non-production path exists).
    integration_status: production-like, seam-proven via tests.

  monitoring:
    classification: REAL
    evidence:
      - alerts.py debounce + auto-halt escalation logic.
      - kill_manager.py persistent kill flag model + bead hash.
    risk:
      - callback failures swallowed (non-blocking).
      - kill flag bead writes wrapped in silent except.
    integration_status: functional, but failure-tolerant to a fault.

  notification:
    classification: REAL
    evidence:
      - alert_taxonomy.py routing + bundling + dedup.
    risk:
      - handler exceptions swallowed with pass.
    integration_status: operational but not fail-loud.

  orientation:
    classification: REAL_WITH_DEFAULTS
    evidence:
      - generator.py emits OrientationBead with hash verification.
      - drills/d3_verification.py validates checksum + no-derived invariants.
    risk:
      - multiple fallback providers + DEFAULT_INVARIANT_COUNT.
      - missing providers degrade silently to defaults.
    integration_status: structurally real, semantically permissive.

  state:
    classification: REAL_WITH_STUBS
    evidence:
      - manifest_writer.py builds HUD manifest from health/orientation.
      - explicit HUD stub sections + graceful defaults (decay: GREEN).
    risk:
      - default health coloring if upstream missing.
      - lease/state color derivation tolerant to missing data.
    integration_status: projection real; upstream dependency assumptions soft.

  widget:
    classification: REAL
    evidence:
      - surface_renderer.py strict projection; verify_no_derivation().
      - blank-on-missing enforcement.
    risk:
      - dependent on orientation file existence.
    integration_status: projection-only, constitutionally aligned.

  surfaces/hud:
    classification: REAL_WITH_MOCK_FALLBACK
    evidence:
      - ManifestWatcher.swift falls back to MockManifest.json.
    risk:
      - silent drop to mock surface masks upstream failure.
    integration_status: consumer real; fallback path weakens signal integrity.

  enrichment:
    classification: STUBBED_PARTIAL
    evidence:
      - l2_reference_levels.py _add_stubbed_columns() inserts Phase-3 stub columns.
    risk:
      - analytics columns may appear present but synthetic.
    integration_status: partially real, explicitly forward-declared.

  cfp:
    classification: REAL_WITH_CONSERVATIVE_FALLBACKS
    evidence:
      - river_adapter.py real aggregation path + dataset hashing.
    risk:
      - conservative empty returns on missing data.
      - partial metric placeholders.
    integration_status: data-real; metrics layer incomplete.

  validation:
    classification: SYNTHETIC
    evidence:
      - backtest.py worker uses synthetic/randomized metric generation.
    risk:
      - presents structured BacktestResult without real capital computation.
    integration_status: scaffolding; not capital-path valid.

  athena:
    classification: REAL
    evidence:
      - store.py strict typed Claim/Fact/Conflict separation.
      - validate_no_claim_execution(), validate_no_auto_surface().
    risk:
      - relies on SQLite file integrity.
    integration_status: structurally mature; execution-isolated.

  hunt:
    classification: REAL_MINIMAL
    evidence:
      - queue.py FIFO enforcement + PriorityForbiddenError.
    risk:
      - limited surface; unclear runtime wiring.
    integration_status: constrained but real.

  slm:
    classification: STUBBED_EXPERIMENTAL
    evidence:
      - train_slm.py TODO for LoRA adapter loading in inference test.
    risk:
      - inference path incomplete.
    integration_status: R&D only.

  tools/hooks:
    classification: REAL
    evidence:
      - scalar_ban_hook.py constitutional lint rules + commit blocking.
    risk:
      - bypassable outside git hook enforcement.
    integration_status: strong preventive layer if enforced in CI.

  drills:
    classification: REAL_TEST_HARNESS
    evidence:
      - d3_verification.py verifies orientation invariants.
    integration_status: integrity proving layer.

  CONSTITUTION:
    classification: STALE_SKELETON
    evidence:
      - README marks <5% populated.
      - modules/ and wiring/ placeholders.
      - invariants reference execution paths not fully verified.
    risk:
      - declarative authority exceeds implemented enforcement.
    integration_status: aspirational taxonomy > wired enforcement.

  config/profiles:
    classification: STALE
    evidence:
      - live.yaml labeled PLACEHOLDER.
    risk:
      - accidental promotion to live path.
    integration_status: non-production.

silent_fails:

  - parse_intent() returning None without raising.
  - watcher duplicate cleanup with pass.
  - multiple broad except Exception in watcher quarantine paths.
  - kill_manager bead writes wrapped in silent except.
  - alert_taxonomy handler exceptions swallowed.
  - monitoring callback fanout failures non-blocking.
  - orientation default providers masking missing upstream state.
  - manifest_writer default decay/health values on missing data.
  - HUD ManifestWatcher.swift fallback to MockManifest.json.
  - cfp adapter conservative empty returns instead of hard failure.
  - synthetic BacktestWorker presenting valid-shaped but non-real metrics.

cross_refs:

  phoenix-swarm:
    status: REAL_INTERFACE
    evidence:
      - watcher/routing seam aligns with swarm intent model.
      - registry validation scripts exist.
    risk:
      - validate_registry.py skips dexter references.

  dexter:
    status: ASPIRATIONAL_LINK
    evidence:
      - registry validator treats dexter refs as cross-repo skip.
    risk:
      - no enforced existence check.

  oracle:
    status: UNKNOWN_EXTERNAL
    evidence:
      - no directory present in loaded phoenix tree.
    risk:
      - references cannot be verified; assume aspirational.

dead_code:

  - CONSTITUTION/modules and wiring placeholders.
  - config/profiles/live.yaml placeholder.
  - slm inference TODO path.
  - validation/backtest synthetic metrics path (non-capital usable).
  - enrichment Phase-3 stub columns not yet replaced.

summary:

  posture: phoenix/ non-capital-path is structurally real but permissive.
  strength:
    - daemons + HALT priority proven by tests.
    - orientation + D3 checksum harness.
    - athena strict type separation.
    - scalar ban constitutional lint.
  weakness:
    - silent-fail bias (broad except + quiet defaults).
    - HUD/mock fallback masks upstream degradation.
    - synthetic analytics/backtest surfaces risk misinterpretation.
    - CONSTITUTION taxonomy exceeds enforced reality.
  risk_classification:
    HALT_layer: strong.
    health_projection: tolerant-to-fault.
    analytics/refinery: partially stubbed.
    constitutional_enforcement: partially symbolic.
  recommendation_signal:
    prioritize fail-loud refactor in watcher/kill_manager/alerts.
    remove or hard-flag mock HUD fallback.
    clearly mark synthetic backtest outputs as NON-CAPITAL.
    either wire CONSTITUTION invariants to tests or downgrade claims.

    Wise Owl Review

    ### **BLOCK_1_INTEGRITY_SWEEP: `phoenix` (Core)**

**Status:** High-Density | **Calibration:** STEEL-REINFORCED (Post-S54)

#### **1. The Governance Seams (`governance/`)**

* **Integrity:** **STEEL**
* **Findings:** `governance.halt.HaltManager` is deeply integrated into `daemons/routing.py`. The "Intent Routing" logic explicitly checks for HALT priority before processing intents.
* **The Hole:** While the *check* exists, the **Propagation Latency** is undefined. If a worker is mid-execution in a sub-process, the `HaltManager` can prevent *new* intents, but does it actively `SIGKILL` running workers?
* **Risk:** **LOW.** Standard "Zombie Worker" risk common in async systems.

#### **2. The 10-State FSM (`execution/positions/`)**

* **Integrity:** **STEEL**
* **Findings:** S54-T1 successfully migrated the 5-state S28.C artifact to the 10-state canonical FSM. `execution/positions/states.py` is the source of truth.
* **The Hole:** The `execution_surface.yaml` contract has been updated, but the **Transition Logic** in `daemons/routing.py` still shows some "handler" patterns that seem to assume a simpler flow.
* **Observation:** The code is honest, but the logic is complex. This is the primary area where "Logic Drift" will occur if not guarded by strict state-transition tests.

#### **3. The River Primitive (`infrastructure/river/` via `cfp/river_adapter.py`)**

* **Integrity:** **SCAFFOLD**
* **Findings:** The `river_adapter.py` exists and feeds the `cfp` (Common Feature Provider). It handles the 1m bar flow.
* **The Hole:** **Fallback Conservatism.** The adapter uses "conservative fallback defaults" when data is missing or late.
* **Risk:** **MEDIUM.** In a "Go Fast" scenario, a "Conservative Fallback" might look like a valid trading signal (e.g., zero volume or flat price) when it's actually just a network timeout. We need a "Data-Invalid" state rather than a "Default" state.

#### **4. The Bridge Interface (Analytical ↔ Governance)**

* **Integrity:** **VAPOR / STUB**
* **Findings:** While the Manifest claims a "One-way valve," the actual bridge logic (`BRIDGE_SPEC.md` mentioned in MASTER_PLAN) is not visible in the core. `validate_registry.py` explicitly skips `dexter/` references.
* **The Hole:** The system is "Aware" of Dexter but cannot "Verify" Dexter. The bridge is currently a human-in-the-loop operation.

---

### **Strategic Gap Inventory: `phoenix**`

1. **HALT Propagation:** We need to move from "Passive Halt" (don't start new things) to "Active Kill" (stop current things) to meet the Tier 1 safety requirement.
2. **Mock Dependency:** `MOCK_5DRAWER` in the CSE schema is a "Soothe-the-Linter" fix. It works, but it masks the fact that the real drawer logic isn't fully feeding the execution engine yet.
3. **The "Silence" of the River:** The `river_adapter` needs a hard `DataGapsError` instead of falling back to defaults.

---

### **Next Move: `dexter/` Node (Gate 1 Audit)**

This is the most critical audit for today. We need to verify if the 789 Genesis beads are truly signed and immutable, or if we are still running on "Extraction Claims."

**Standing by for `dexter/` oracle report.** *Note: If `oracle/` directory does not exist, we will conclude Block 1 with the Dexter report and move to synthesis.*

Grok Review 

file_inventory:
  - path: daemons/routing.py
    classification: REAL
  - path: daemons/watcher.py
    classification: REAL
  - path: monitoring/alerts.py
    classification: REAL
  - path: monitoring/kill_manager.py
    classification: REAL
  - path: orientation/generator.py
    classification: REAL
  - path: state/manifest_writer.py
    classification: STUB
    breaks_if_used: Graceful fallbacks to default/green states; live data wiring incomplete—HUD stale/missing real sources (river heartbeat, lease yaml, evaluator conditions).
  - path: widget/surface_renderer.py
    classification: REAL
  - path: surfaces/hud/WarBoarHUD/Services/ManifestWatcher.swift
    classification: REAL
  - path: enrichment/layers/l2_reference_levels.py
    classification: STUB
    breaks_if_used: Explicit _add_stubbed_columns() inserts Phase-3 placeholders; missing real L2 enrichment—empty columns in output.
  - path: cfp/river_adapter.py
    classification: STUB
    breaks_if_used: Conservative empty returns/default metrics; partial/non-real computation—win_rate/pnl placeholders inaccurate for live.
  - path: athena/store.py
    classification: REAL
  - path: hunt/queue.py
    classification: REAL
  - path: validation/backtest.py
    classification: STUB
    breaks_if_used: Synthetic/randomized metrics; non-real backtest path—outputs demo data, not validated history.
  - path: tools/hooks/scalar_ban_hook.py
    classification: REAL
  - path: slm/train_slm.py
    classification: STUB
    breaks_if_used: TODO LoRA loading in inference; training path real but inference incomplete—model fails to load adapters.
  - path: drills/d3_verification.py
    classification: REAL
  - path: tests/daemons/test_halt_priority.py
    classification: REAL
  - path: CONSTITUTION/README.md
    classification: SCAFFOLD
    breaks_if_used: <5% populated; missing scripts—invariant checks fail silently if referenced.
  - path: CONSTITUTION/CONSTITUTION_MANIFEST.yaml
    classification: SCAFFOLD
    breaks_if_used: Taxonomy/validation templates only; no enforcement—migration/invariant gaps uncaught.
  - path: CONSTITUTION/modules/README.md
    classification: SCAFFOLD
    breaks_if_used: To-be-created; empty—module wiring assumes existence, silent import errors.
  - path: CONSTITUTION/wiring/README.md
    classification: SCAFFOLD
    breaks_if_used: To-be-created; empty—wiring assumptions fail, no graph validation.
  - path: CONSTITUTION/invariants/INV-GOV-HALT-BEFORE-ACTION.yaml
    classification: REAL
  - path: config/profiles/live.yaml
    classification: STUB
    breaks_if_used: Explicit PLACEHOLDER; defaults unsafe for live—config gaps cause runtime errors.
  - path: scripts/deployment_audit.py
    classification: REAL
  - path: scripts/validate_registry.py
    classification: REAL
silent_fails:
  - pattern: manifest_writer.py default/green states
    desc: Missing live sources (river/evaluator/lease) fallback to stubs; HUD renders nominal but stale—operator blind to real risks.
  - pattern: surface_renderer.py blank-on-missing
    desc: Projection skips absent data; incomplete HUD without error—silent degradation.
  - pattern: river_adapter.py empty returns/default metrics
    desc: Query failures return conservative empties; partial pnl/win_rate placeholders—analysis proceeds with inaccurate data undetected.
  - pattern: backtest.py synthetic generation
    desc: Randomized metrics without validation flag; non-real outputs treated as true—misleads strategy eval.
  - pattern: train_slm.py TODO LoRA inference
    desc: Adapter load skipped; model runs base-only without error—degraded performance silent.
  - pattern: validate_registry.py dexter/ skips
    desc: Cross-repo refs unvalidated; invariant gaps in dexter uncaught—system assumes completeness.
cross_refs:
  - ref: governance/halt.py (daemons/routing.py, watcher.py, test_halt_priority.py)
    target_real: yes (sealed v0.1, <50ms proven per invariants)
  - ref: ~/dexter (validate_registry.py skips, athena/store.py potential)
    target_real: yes (Gate 1 PASS, substrate real frozen per bead gate)
  - ref: ~/oracle (manifest_writer.py potential, cfp/river_adapter.py)
    target_real: partial (impl comprehensive but reg stale per DELTA-12; instructions pending)
  - ref: river/ (manifest_writer.py wiring, river_adapter.py)
    target_real: yes (operational post-S54 patch, heartbeat/logs real)
  - ref: cso/ (manifest_writer.py conditions, athena/store.py)
    target_real: yes (comprehensive per manifest, template.yaml real)
halt_mechanism:
  type: wired-priority
  wired: yes
  details: Explicit HaltManager in routing.py/watcher.py; priority queue for IntentType.HALT, <50ms local/<500ms cascade proven (INV-HALT-1/2); test_halt_priority.py verifies watcher handling; escalation from alerts.py/kill_manager.py to halt callback—enforced pre-action (INV-GOV-HALT-BEFORE-ACTION.yaml refs execution/tests real).
summary:
  real_count: 15
  stub_count: 6
  scaffold_count: 5
  risk_level: low (S54 sweep/mypy clean/240 invariants minimize surprises; stubs intentional post-seal/Gate3+)
  verdict: capital engine sealed real with small stubs (enrichment/backtest Phase-3); silent fails in stubs but invariants guard; cross-refs solid, halt wired robust—constitutional anchor.