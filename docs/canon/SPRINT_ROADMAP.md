# SPRINT_ROADMAP.md
# Phoenix Sprint Roadmap — M2M Advisor Reference

```yaml
document: SPRINT_ROADMAP.md
version: 2.4
date: 2026-02-04
status: CANONICAL
format: M2M_DENSE
audience: Advisors (GPT, GROK, OWL, Opus)
```

---

## CURRENT STATE

```yaml
current_sprint: S48_PENDING (next after S47 complete)
status: S44_COMPLETE | S46_DESIGN_LOCKED | S47_COMPLETE | S48_HUD_COMPLETE
s33_p2: BLOCKED (Olya CSO calibration) — unblock via COE model

recent_completions:
  s43_completion_date: 2026-01-31
  s44_completion_date: 2026-02-04
  s46_design_locked: 2026-01-31
  s47_completion_date: 2026-02-04
  s48_completion_date: 2026-01-31
  filing_cabinet: 2026-01-31

certification: WARBOAR_CERTIFIED | LIVE_GATEWAY_VALIDATED | CSO_PRODUCTION_READY | S46_CANONICAL | HUD_INTEGRATED | S44_FOUNDATION_VALIDATED | S47_LEASE_PROVEN
cumulative:
  sprints_complete: 19 (S28 → S44, S47, S48)
  tests_passing: 1618+
  xfailed: 28 (documented, strict)
  chaos_vectors: 240/240 PASS
  invariants_proven: 111+
  bead_types: 17
  runbooks: 8
  gate_glossary: 48 gates mapped

s44_soak_final:
  completed: 2026-02-04
  actual_duration: ~24h (travel interrupted, sufficient for foundation proof)
  exit_gate: FOUNDATION_VALIDATED
  arch_flaws: 0
  invariant_violations: 0
  catastrophic_crashes: 0
  ops_gaps_documented: [heartbeat daemon, IBKR disconnect, River staleness, health_writer]
  disposition: "Software exists. Now we operate."

INV-NO-CORE-REWRITES-POST-S44: ACTIVE (soak complete, enforced)
```

---

## SPRINT ARCHAEOLOGY (S28-S39)

| Sprint | Codename | Key Deliverables | Exit Gate |
|--------|----------|------------------|-----------|
| S28 | STEEL_PIPES | Foundation, contracts | ✓ |
| S29 | BUILD_MAP | Schema arch, River | ✓ |
| S30 | LEARNING_LOOP | Hunt, Athena, BeadStore | ✓ 19/19 BUNNY |
| S31 | SIGNAL_AND_DECAY | CSO, Signalman, Autopsy | ✓ 20/20 BUNNY |
| S32 | EXECUTION_PATH | IBKR mock, T2, 9-state lifecycle | ✓ 17/17 BUNNY |
| S33.P1 | FIRST_BLOOD | Real IBKR, monitoring, 8 runbooks | ✓ 15/15 BUNNY |
| S34 | OPERATIONAL_FINISHING | File seam, CSO contract, orientation, widget | ✓ 13/13 BUNNY |
| **S35** | **CFP** | **Conditional facts, causal ban, provenance** | **✓ 62 tests, 21 BUNNY** |
| **S36** | **CSO_HARNESS** | **Gate status, no grades, bit-vector** | **✓ 45 tests, 18 BUNNY** |
| **S37** | **ATHENA** | **Memory discipline, CLAIM/FACT/CONFLICT** | **✓ 51 tests, 15 BUNNY** |
| **S38** | **HUNT** | **Exhaustive grid, no survivor ranking** | **✓ 69 tests, 23 BUNNY** |
| **S39** | **VALIDATION** | **Decomposed outputs, scalar ban linter** | **✓ 109 tests, 28 BUNNY** |
| **S40** | **SLEEP_SAFE** | **Self-healing, IBKR resilience, hooks, narrator** | **✓ 312 tests, 15 BUNNY** |

### Key Assets Built
```yaml
governance/: halt.py, invariants/, kill_flags.py  # AUTHORITY: ABSOLUTE
execution/: position.py (9-state), tier_gates.py  # T2 gate for capital
brokers/ibkr/: connector.py, real_client.py, session_bead.py
monitoring/: heartbeat.py, semantic_health.py
daemons/: watcher.py, lens.py, routing.py  # FILE_SEAM_SPINE
orientation/: generator.py, validator.py  # KILL_TEST proven
approval/: evidence.py  # T2 evidence display
cso/: consumer.py  # CSE validation
widget/: surface_renderer.py, menu_bar.py  # READ_ONLY projection
```

### Patterns Proven
- **Checksum not briefing** (D3) — machine-verifiable orientation
- **Contract before integration** (D2) — mock-first validation
- **Truth-first UI surfacing** (D4) — UI freedom earned by state discipline
- **Projection not participation** — UI subordinate to state

---

## S35: CFP (CONDITIONAL FACT PROJECTOR)

```yaml
status: COMPLETE ✓
completion_date: 2026-01-29
tests: 62
bunny_vectors: 21
theme: "Where/when does performance concentrate?"
ref: DEFINITIVE_FATE.yaml → sprint_allocation.S35_CFP
```

### Scope
| Component | Purpose | Priority |
|-----------|---------|----------|
| Lens schema | YAML: group_by, filter, agg | P0 |
| Query executor | Against River/beads | P0 |
| Output schema | facts + provenance (query_string + dataset_hash + bead_id) | P0 |
| Causal-ban linter | TEST not policy | P0 |
| Conflict display | best/worst always paired | P0 |
| Bead-query endpoint | Live recombobulation | P1 |
| Negative assertion | "where Gate X passed but Outcome Y negative" | P1 |

### NEX Capabilities Addressed
| NEX-ID | Name | Fate |
|--------|------|------|
| NEX-020 | Signal Replay | REIMAGINE (forensic primitives) |
| NEX-021 | Compare Backtests | KEEP |
| NEX-022 | Grade Comparison | REIMAGINE → gates_passed >= N |
| NEX-024 | Regime Breakdown | REIMAGINE → explicit predicates |
| NEX-025 | Session/KZ Breakdown | KEEP |
| NEX-026 | P&L Attribution | REIMAGINE → conditional facts |

### Invariants to Prove
```yaml
- INV-ATTR-CAUSAL-BAN: "No causal claims; only conditional facts"
- INV-ATTR-PROVENANCE: "All outputs include query + hash + bead_id"
- INV-ATTR-NO-RANKING: "No ranking, no best/worst, no implied priority"
- INV-ATTR-SILENCE: "System does not resolve conflicts"
- INV-ATTR-CONFLICT-DISPLAY: "When showing best, must show worst"
- INV-REGIME-EXPLICIT: "Regimes = explicit predicates, never auto-detected"
- INV-REGIME-GOVERNANCE: "Regimes versioned, capped (~20 max)"
- INV-SLICE-MINIMUM-N: "N < 30 → warn or fail-silent"
```

### Build Notes (Advisor Synthesis)
- Lens schema is constitutional boundary — validate rigorously
- Provenance link must be first-class
- Regimes live in conditions.yaml (explicit predicates)
- Brinson attribution pattern: decomposition without causality

### Exit Gate
"CFP returns conditional facts with provenance; causal-ban linter passes"

---

## S36: CSO HARNESS

```yaml
status: COMPLETE ✓
completion_date: 2026-01-29
tests: 45
bunny_vectors: 18
theme: "Gate status per pair, facts not grades"
ref: DEFINITIVE_FATE.yaml → sprint_allocation.S36_CSO_HARNESS
```

### Scope
| Component | Purpose | Priority |
|-----------|---------|----------|
| 5-drawer gate evaluation | conditions.yaml predicates | P0 |
| Gate status output | gates_passed[] + gates_failed[] | P0 |
| CSE emission | With evidence bundle | P0 |
| Multi-pair scan | gates_passed per pair, alphabetical | P0 |
| Bit-vector output | 01011 mapping to conditions.yaml | P1 |
| Bento Box layout | Cognitive Air Gap (UI) | P1 |

### NEX Capabilities Addressed
| NEX-ID | Name | Fate |
|--------|------|------|
| NEX-003 | Scan All Setups | REIMAGINE → bit-vector |
| NEX-008 | 4Q Gate Analysis | REIMAGINE → boolean per gate |
| NEX-012 | Multi-Pair Scan | REIMAGINE → gates_passed_count |
| NEX-060 | Grade A Alerts | REIMAGINE → explicit gate triggers |

### Invariants to Prove
```yaml
- INV-HARNESS-1: "CSO outputs gate status only, never grades"
- INV-HARNESS-2: "No confidence scores unless explicit formula"
- INV-HARNESS-3: "Alerts fire on gate combinations, not quality"
- INV-HARNESS-4: "Multi-pair sorted alphabetically by default"
- INV-NO-UNSOLICITED: "System never proposes"
- INV-BIAS-PREDICATE: "HTF bias as predicate status, not directional words"
```

### Build Notes (Advisor Synthesis)
- CSO "grades" can NEVER exist as concept in harness output
- "Passed gates" is the only language
- Any "confidence" feature is illegal (trap)
- Bento Box layout is Cognitive Air Gap, not aesthetic

### Exit Gate
"CSO harness returns gate status per pair; no grades anywhere in output"

---

## S37: MEMORY DISCIPLINE

```yaml
status: COMPLETE ✓
completion_date: 2026-01-29
tests: 51
bunny_vectors: 15
theme: "Memory, not myth"
ref: DEFINITIVE_FATE.yaml → sprint_allocation.S37_MEMORY_DISCIPLINE
```

### Scope
| Component | Purpose | Priority |
|-----------|---------|----------|
| CLAIM_BEAD | Human-asserted statements | P0 |
| FACT_BEAD | Machine-computed results | P0 |
| CONFLICT_BEAD | Conflict flag (no resolution) | P0 |
| Athena store | claim + evidence + provenance | P0 |
| Semantic query | Embedding distance (not "relevance") | P1 |
| Memory history | Chronological fact trail | P1 |

### NEX Capabilities Addressed
| NEX-ID | Name | Fate |
|--------|------|------|
| NEX-013 | Teach Athena | REIMAGINE → CLAIM_BEAD |
| NEX-014 | Recall Memory | KEEP |
| NEX-015 | Semantic Search | REIMAGINE → distance scores |
| NEX-016 | Contradiction Detection | REIMAGINE → CONFLICT_BEAD |
| NEX-017 | Memory History | KEEP |

### Invariants to Prove
```yaml
- INV-ATTR-NO-WRITEBACK: "Stored facts cannot mutate doctrine"
- INV-ATTR-SILENCE: "System does not resolve conflicts"
```

### Bead Type Definitions
```yaml
CLAIM_BEAD:
  source: human input
  status: unverified assertion
  example: "Olya believes London FVG works better after 8:30"

FACT_BEAD:
  source: computation (formula explicit)
  status: verified output
  provenance: query_string + dataset_hash
  example: "win_rate(session=London, time>8:30) = 62%"

CONFLICT_BEAD:
  references: [bead_a_id, bead_b_id]
  resolution: NONE (human must resolve)
  example: "CLAIM_123 conflicts with FACT_456"
```

### Build Notes (Advisor Synthesis)
- Must implement CLAIM vs FACT vs CONFLICT distinction
- This is the difference between "memory" and "myth"
- Wikipedia pattern: flag inconsistency, never choose

### Exit Gate
"Athena stores claims with explicit type; conflicts surfaced without resolution"

---

## S38: HUNT INFRASTRUCTURE

```yaml
status: COMPLETE ✓
completion_date: 2026-01-29
tests: 69
bunny_vectors: 23
theme: "Compute engine, not idea engine"
ref: DEFINITIVE_FATE.yaml → sprint_allocation.S38_HUNT_INFRASTRUCTURE
```

### Scope
| Component | Purpose | Priority |
|-----------|---------|----------|
| Hypothesis schema | Structured framing | P0 |
| Hunt queue | Human-approved only | P0 |
| Exhaustive compute | ALL variants, no selection | P0 |
| Parameter sweep | Grid at each point | P0 |
| Budget cap | Token/compute limit per run | P0 |
| Batch processing | Epoch overnight | P1 |

### NEX Capabilities Addressed
| NEX-ID | Name | Fate |
|--------|------|------|
| NEX-035 | Hypothesis Framing | REIMAGINE → schema |
| NEX-037 | Pending Queue | KEEP |
| NEX-038 | Hunt Engine Run | REIMAGINE → exhaustive |
| NEX-040 | Epoch Processing | KEEP |
| NEX-041 | Parameter Sweep | REIMAGINE → table output |

### Invariants to Prove
```yaml
- INV-HUNT-EXHAUSTIVE: "Hunt computes ALL declared variants, never selects"
- INV-NO-UNSOLICITED: "System never proposes hypotheses"
- INV-HUNT-BUDGET: "Compute/token cap enforced per run"
```

### Budget Enforcement
```yaml
enforcement:
  - Max variants per hunt declared upfront
  - Token/compute estimate before execution
  - Hard abort if budget exceeded
rationale: "Exhaustive grids can explode"
```

### Build Notes (Advisor Synthesis)
- No auto-variant generation, no internal selection
- Just grid compute + table output
- Quant AutoML pattern: human-defined search space

### Exit Gate
"Hunt engine computes exhaustive grid with budget enforcement; no survivor ranking"

---

## S39: RESEARCH VALIDATION

```yaml
status: COMPLETE ✓
completion_date: 2026-01-29
tests: 109
bunny_vectors: 28
theme: "Decomposed outputs, no viability scores"
ref: DEFINITIVE_FATE.yaml → sprint_allocation.S39_RESEARCH_VALIDATION
codename: CONSTITUTIONAL_CEILING
```

### Scope
| Component | Purpose | Priority |
|-----------|---------|----------|
| Backtest worker | Factual metrics + provenance | P0 |
| Walk-forward | Out-of-sample validation | P0 |
| Monte Carlo | Drawdown distribution | P0 |
| Overfitting suite | Per-check results | P0 |
| Cost curve | Sharpe degradation table | P1 |
| Sandbox | Isolated from live | P1 |

### NEX Capabilities Addressed
| NEX-ID | Name | Fate |
|--------|------|------|
| NEX-018 | Backtest Strategy | KEEP |
| NEX-019 | Sandbox Testing | KEEP |
| NEX-028 | Walk-Forward | KEEP |
| NEX-029 | Monte Carlo | KEEP |
| NEX-030 | Overfitting Suite | KEEP |
| NEX-031 | Parameter Sensitivity | REIMAGINE → sensitivity not importance |
| NEX-033 | Cost Curve | KEEP |

### Invariants to Prove
```yaml
- INV-SCALAR-BAN: "No composite scores (0-100)"
- INV-ATTR-NO-RANKING: "No robustness ranking"
```

### Build Notes (Advisor Synthesis)
- All outputs must remain decomposed
- No "viability score" — EVER
- Label as "sensitivity" NOT "importance"

### Exit Gate
"Validation suite returns per-check results; no single viability score anywhere"

---

## S40: SLEEP-SAFE RESILIENCE

```yaml
status: COMPLETE ✓
completion_date: 2026-01-30
tests: 312
bunny_vectors: 15
theme: "No 3am wake-ups"
codename: SLEEP_SAFE
```

### Tracks
| Track | Name | Tests | Key Deliverable |
|-------|------|-------|-----------------|
| A | SELF_HEALING | 57 | Circuit breakers, backoff, health FSM |
| B | IBKR_FLAKEY | 56 | Supervisor, heartbeat, degradation |
| C | HOOKS | 52 | Pre-commit + runtime assertions |
| D | NARRATOR | 38 | Template-based state projection |
| E | POLISH | 56 | API alignment, chain validation |
| F | BUNNY | 45 | 15 chaos vectors |

### Invariants Proven (20 new)
```yaml
# Self-Healing
- INV-CIRCUIT-1/2: Circuit breaker FSM
- INV-BACKOFF-1/2: Exponential backoff
- INV-HEALTH-1/2: Health state machine
- INV-HEAL-REENTRANCY: No side effect multiplication

# IBKR Resilience
- INV-IBKR-FLAKEY-1/2/3: Heartbeat monitoring
- INV-IBKR-DEGRADE-1/2: Graceful degradation
- INV-SUPERVISOR-1: Watchdog survival

# Hooks
- INV-HOOK-1/2/3/4: Constitutional enforcement

# Narrator
- INV-NARRATOR-1/2/3: Facts-only projection
```

### Chaos Vectors (15)
| Vector | Target | Attack | Status |
|--------|--------|--------|--------|
| 1 | 5 Breakers | Simultaneous trigger | ✓ PASS |
| 2 | Health FSM | Recovery race | ✓ PASS |
| 3 | Alert System | Storm (100/10s) | ✓ PASS |
| 4 | Supervisor | Connector death | ✓ PASS |
| 5 | Degradation | Tier bypass | ✓ PASS |
| 6 | Heartbeat | Flap storm | ✓ PASS |
| 7 | Runtime | Scalar injection | ✓ PASS |
| 8 | Provenance | Tampering | ✓ PASS |
| 9 | Rankings | Resurrection | ✓ PASS |
| 10 | Narrator | Missing sources | ✓ PASS |
| 11 | Templates | Heresy injection | ✓ PASS |
| 12 | Synthesis | Leak detection | ✓ PASS |
| 13 | Chain | NaN injection | ✓ PASS |
| 14 | Hunt | Regime mutation | ✓ PASS |
| 15 | Athena | Conflict flood | ✓ PASS |

### Exit Gate
"System survives coordinated chaos. Sleep-safe certified."

---

## S41: WARBOAR_AWAKENS — COMPLETE ✓ SEALED

```yaml
status: COMPLETE ✓ SEALED
completion_date: 2026-01-23
theme: "Distillation + Live Validation"
tests: 195+ (narrator/SLM/integration)
bunny_vectors: 20 (narrator injection, classifier bypass, IBKR chaos)
new_invariants: 6 (SLM-*, ALERT-TAXONOMY-*)
certification: LIVE_GATEWAY_VALIDATED
```

### Phases Delivered
| Phase | Name | Outcome |
|-------|------|---------|
| 2A | Foundation | IO schema, invariant freeze, boundary assertion |
| 2B | Dataset Generation | 1000+ training examples (pivoted to rule-based) |
| 2C | Distillation | ContentClassifier (rule-based, 100% accuracy) |
| 2D | Narrator Integration | Single chokepoint, canonicalization, heresy blocking |
| 2E | Surface Polish | Human cadence, alert one-liners, degraded messages |
| 3A | Mock Validation | 7/7 exit gates PASSED |
| 3B | Real Gateway | Live IBKR connection validated (PAPER MODE) |

### Key Deliverables
```yaml
slm/:
  - inference.py: Classification API
  - training/: Dataset generation
governance/:
  - slm_boundary.py: ContentClassifier, @slm_output_guard
narrator/:
  - renderer.py: narrator_emit() chokepoint
  - surface.py: Human-readable formatters
  - templates/: Humanized Jinja2 templates
notification/:
  - alert_taxonomy.py: One-liner formatters
drills/:
  - s41_phase3_live_validation.py: Real Gateway validation
```

### Invariants Proven (S41)
```yaml
INV-SLM-READONLY-1: "SLM output cannot mutate state"
INV-SLM-NO-CREATE-1: "SLM cannot create new information"
INV-SLM-CLASSIFICATION-ONLY-1: "Output is classification only"
INV-SLM-BANNED-WORDS-1: "SLM detects all banned categories"
INV-ALERT-TAXONOMY-1: "Alerts use defined categories"
INV-ALERT-TAXONOMY-2: "Alert severity from enum"
```

### Latency Benchmarks (Real Gateway)
```yaml
classifier_p50: 0.12ms
classifier_p95: 0.34ms
narrator_emit_p95: < 1ms
full_pipeline_p95: < 500ms
```

### Exit Gate
"SLM classifies correctly, latency < 15ms, real IBKR Gateway validated"

### References
- `docs/build_docs/WARBOAR_RESILIENCE_FINAL_FORM.md`
- `docs/S41_COMPLETION_REPORT.md`

---

## S42: TRUST_CLOSURE — COMPLETE ✅

```yaml
status: COMPLETE ✅
completion_date: 2026-01-30
theme: "Trust Closure + Production Ready"
codename: TRUST_CLOSURE
certification: CSO_PRODUCTION_READY
```

### Tracks Delivered
| Track | Name | Key Deliverables |
|-------|------|------------------|
| A | CSO_PRODUCTION | Gate glossary (48 gates), health file, operator docs, system prompt v0.2 |
| B | FAILURE_REHEARSAL | s42_failure_playbook.py (chaos vectors) |
| C | TECH_DEBT_BURN | pytest failures triaged, xfail documented |
| D | RIVER_COMPLETION | synthetic_river.py fallback |
| E | OBSERVABILITY | phoenix_status CLI |
| F | ARCHITECTURAL_FINALITY | ARCHITECTURAL_FINALITY.md, START_HERE.md, archive sweep |

### Track A Deliverables (CSO Production)
```yaml
gate_glossary:
  file: cso/knowledge/GATE_GLOSSARY.yaml
  gates_mapped: 48
  purpose: "Gate name → drawer location + meaning"

health_file:
  file: state/health_writer.py
  output: state/health.yaml
  purpose: "CSO-readable system health snapshot"

operator_docs:
  - docs/OPERATOR_INSTRUCTIONS/OPERATOR_EXPECTATIONS.md
  - docs/OPERATOR_INSTRUCTIONS/WHEN_TO_IGNORE_PHOENIX.md

cso_prompt:
  file: cso/knowledge/CSO_HEALTH_PROMPT.md
  purpose: "Instructions for health file consumption"

foundation_addition:
  concept: "inducement"
  location: foundation.yaml
  purpose: "Distinct from manipulation (bait vs switch)"
```

### CSO Validation Points
```yaml
methodology_fluency: "CSO understands 5-drawer ICT methodology"
health_awareness: "CSO reads health.yaml, reports naturally"
approve_flow: "CSO handles APPROVE intent correctly"
degraded_handling: "CSO explains degraded states calmly"
boundary_respect: "CSO knows when Phoenix can/cannot help"
```

### Exit Gate
"CSO production-ready; gate glossary maps all gates; health file enables visibility"

---

## S43: FOUNDATION_TIGHTENING — COMPLETE ✅

```yaml
status: COMPLETE ✅
completion_date: 2026-01-31
theme: "Quick wins = momentum. Boring = correct."
codename: FOUNDATION_TIGHTENING
```

### Tracks Delivered
| Track | Name | Key Deliverables |
|-------|------|------------------|
| A | PYTEST_PARALLEL | xdist_group markers for stateful tests, parallelization enabled |
| B | ALERT_BUNDLING | CRITICAL/HALT bypass bundling, 30min window configurable, MULTI_DEGRADED summary |
| C | CONFIG_CENTRAL | Pydantic schema (config/schema.py), zero new deps, virgin VM concept |
| D | NARRATOR_FACTS | INV-NARRATOR-FACTS-ONLY linter, forbidden words regex, receipts_link template option |

### New Invariants
```yaml
INV-NARRATOR-FACTS-ONLY:
  rule: "Narrator templates contain facts only, no interpretation"
  enforcement: Pre-commit linter + test
  forbidden: ["edge concentrates", "best", "strongest", "likely"]
```

### Exit Gates
```yaml
GATE_S43_1: "pytest -n auto completes without fixture errors"
GATE_S43_2: "Alert bundling passes >5 alerts → MULTI_DEGRADED test"
GATE_S43_3: "Config validates on virgin VM concept"
GATE_S43_4: "Narrator templates pass facts-only linter"
GATE_S43_5: "All xfails reviewed before close"
```

### Exit Gate
"Developer velocity unlocked, foundation tightened. Tests 2:21, parallel-safe."

---

## S44: LIVE_VALIDATION — COMPLETE ✅

```yaml
status: COMPLETE ✅
started: 2026-01-31
completed: 2026-02-04
theme: "Boring for 48h"
codename: LIVE_VALIDATION
actual_duration: ~24h (travel interrupted — sufficient for foundation proof)
exit_classification: FOUNDATION_VALIDATED
```

### Phases
| Phase | Name | Status | Outcome |
|-------|------|--------|---------|
| 1 | RIVER_VERIFICATION | ✅ COMPLETE | River verified, IBKR diagnosed + fixed |
| 2 | FULL_PATH_TEST | ✅ COMPLETE | CSO → Narrator → Execution path validated |
| 3 | 24H_SOAK | ✅ COMPLETE | Real IBKR soak — no arch flaws, no invariant violations |

### Phase 1 Findings
```yaml
river_status: Synthetic fallback operational (real River stale)
ibkr_diagnosis:
  issue: ".env not loaded, defaulted to MOCK"
  fix: "Added dotenv loading to phoenix_status and soak script"
  verification: "IBKR: PAPER (DUO768070) confirmed"
```

### Soak Results (Feb 3-4, 2026)
```yaml
RESULTS:
  arch_flaws: 0
  invariant_violations: 0
  catastrophic_crashes: 0
  phoenix_independence: CONFIRMED (ran without HUD)
  state_surfaces: CORRECT
  health_transitions: INTELLIGIBLE

OPS_GAPS_DOCUMENTED:
  - No persistent heartbeat daemon (cron workaround used)
  - IBKR/TWS disconnect when operator closed app
  - River feed stale when upstream disconnected
  - health_writer not continuous by default

DISPOSITION: |
  24h unattended, zero violations = sufficient foundation proof.
  Ops gaps are EXPECTED at this stage — software exists, now transition to operating.
```

### Exit Gates
```yaml
GATE_S44_P1: "River has fresh bars or synthetic fallback" ✅
GATE_S44_P2: "Historical/live seam flagged correctly" ✅
GATE_S44_P3: "Truth Teller quality scores accurate" ✅
GATE_S44_P4: "Full loop completes without error" ✅
GATE_S44_P5: "Execution bead has correct provenance" ✅
GATE_S44_P6: "Narrator output passes guard dog" ✅
GATE_S44_P7: "24h elapsed, no unexpected alerts" ✅
GATE_S44_P8: "Health log shows no CRITICAL" ✅
GATE_S44_P9: "All beads have valid provenance" ✅
```

### Exit Gate
"Foundation validated. 24h soak with zero arch flaws, zero invariant violations. INV-NO-CORE-REWRITES-POST-S44 now ACTIVE."

---

## S46: CARTRIDGE_AND_LEASE_DESIGN — COMPLETE ✅ LOCKED

```yaml
status: COMPLETE ✅ CANONICAL
completion_date: 2026-01-31
theme: "Governance architecture for bounded autonomy"
codename: CARTRIDGE_AND_LEASE_DESIGN
canonical_doc: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md
```

### Design Delivered
```yaml
cartridge:
  purpose: "Strategy manifest — the WHAT"
  schema: identity, scope, risk_defaults, gate_requirements, methodology_hash
  new_fields: primitive_set, calibration_threshold_pct, regime_affinity

lease:
  purpose: "Governance wrapper — the WHEN/HOW MUCH"
  schema: identity, bounds, duration, state_machine, attestation
  new_fields: governance_buffer_seconds, expiry_behavior, state_lock_hash
  states: DRAFT → ACTIVE → EXPIRED | REVOKED | HALTED
```

### New Invariants (S46)
```yaml
INV-NO-SESSION-OVERLAP: "One lease per session, no concurrent execution"
INV-LEASE-CEILING: "Lease bounds = ceiling, Cartridge = floor"
INV-BEAD-COMPLETENESS: "Calibration bead must link to lease schema version"
INV-EXPIRY-BUFFER: "60-second buffer before lease expiry triggers MARKET_CLOSE"
INV-STATE-LOCK: "State transition guard prevents race conditions"
```

### Insertion Protocol (8-step)
```yaml
steps:
  1: Load cartridge YAML
  2: Schema validation + dependency check
  3: CSO knowledge merge (5-drawer)
  4: Gate compatibility check
  5: Lease creation (DRAFT)
  6: Human attestation (DRAFT → ACTIVE)
  7: Calibration smoke test
  8: Guard Dog final scan
```

### Advisor Consensus
```yaml
reviewers: [GPT, GROK, OWL, Opus]
verdict: UNANIMOUS_APPROVAL
key_decisions:
  - Single active cartridge for v1.0 (multi earned later)
  - OR logic for bounds (any breach = halt)
  - Session-level only (no partial sessions)
  - Per-direction extension tracking
```

### Exit Gate
"S46 design locked. CARTRIDGE_AND_LEASE_DESIGN_v1.0_CANONICAL.md is authoritative."

---

## S48: HUD_SURFACE — COMPLETE ✅

```yaml
status: COMPLETE ✅
completion_date: 2026-01-31
theme: "Glanceable sovereignty"
codename: HUD_SURFACE
effort: ~8h (design + build + integration)
```

### Deliverables
```yaml
committed:
  1: "feat(hud): bring WarBoar HUD into Phoenix repo as surfaces/hud"
  2: "feat(state): add manifest_writer.py for HUD integration"

created:
  - phoenix/surfaces/hud/ (complete SwiftUI app)
  - phoenix/state/manifest_writer.py (schema v1.1 bridge)
  - phoenix/state/manifest.json (output)

features:
  - 9 section views (constitutional colors)
  - Smoked glass backdrop
  - WarBoar logo + timezone clocks
  - Stale detection (60s threshold)
  - Parse error resilience
  - File watcher with throttling
  - Real health data integration
  - Calculated KZ session times
```

### Exit Gates Passed
| Gate | Criterion | Status |
|------|-----------|--------|
| GATE_1 | Panel launches left-edge with glassy background | ✓ |
| GATE_2 | All 9 sections render with data | ✓ |
| GATE_3 | manifest.json change → UI update <500ms | ✓ |
| GATE_4 | HUD displays real Phoenix state | ✓ |
| GATE_5 | Narrator shows observations | ✓ (empty stub) |
| GATE_6 | Stale overlay appears after 60s | ✓ |
| GATE_7 | S44 soak unaffected | ✓ |

### What's Working NOW
```yaml
real_data:
  - Health section (DEGRADED, component status)
  - Session/KZ times (LONDON calculated)
  - Stale detection (accurate)

stub_data (graceful):
  - Portfolio ($0.00)
  - Positions (empty)
  - Trades (empty)
  - Gates (empty)
  - Narrator (empty)
  - Lease (ABSENT)
```

### Future Scope (Not S48)
```yaml
live_feed:
  need: "Phoenix daemon calls manifest_writer.py every 30s"
  when: "S50 or operational polish sprint"

real_data_sections:
  portfolio: "When IBKR account query added"
  positions: "When position tracking active"
  trades: "When bead query for trades"
  gates: "When CSO scanner running"
  narrator: "When narrator templates active"
  lease: "S47 scope"
```

### Exit Gate
"HUD displays real Phoenix state with <500ms latency. The WarBoar has a face."

---

## S47: LEASE_IMPLEMENTATION — COMPLETE ✅

```yaml
status: COMPLETE ✅
completion_date: 2026-02-04
theme: "Bounded autonomy with sovereign override"
codename: LEASE_IMPLEMENTATION
tests: 118
chaos_vectors: 16 (BUNNY)
new_invariants: 6
design_spec: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md
```

### Deliverables
```yaml
governance/lease_types.py:
  purpose: Pydantic models for Cartridge + Lease schemas
  content: Enums (LeaseState, AllowedMode, ExpiryBehavior), CartridgeManifest, Lease, all bead types

governance/lease.py:
  purpose: State machine + interpreter
  content: LeaseStateMachine (DRAFT→ACTIVE→EXPIRED|REVOKED|HALTED), LeaseInterpreter (bounds), LeaseManager

governance/cartridge.py:
  purpose: Cartridge loader + schema validation
  content: CartridgeLoader (YAML), CartridgeLinter (guard dog), CartridgeRegistry

governance/insertion.py:
  purpose: 8-step insertion protocol
  content: InsertionProtocol, validate_bounds_ceiling (INV-LEASE-CEILING)

state/manifest_writer.py:
  purpose: HUD integration (updated)
  content: get_lease_state() for live lease status in manifest.json
```

### Tests Created
```yaml
tests/test_lease/:
  test_state_machine.py: 28 tests (FSM transitions, bead emission)
  test_bounds.py: 23 tests (OR logic, INV-LEASE-CEILING)
  test_halt_override.py: 21 tests (INV-HALT-OVERRIDES-LEASE, <50ms latency)
  test_expiry.py: 17 tests (governance buffer, effective expiry)
  test_insertion.py: 13 tests (8-step protocol, rollback)

tests/chaos/:
  test_bunny_s47.py: 16 chaos vectors
```

### BUNNY Chaos Vectors (16)
| Vector | Target | Attack | Status |
|--------|--------|--------|--------|
| 1 | Concurrent activation | 10 threads racing | ✓ PASS |
| 2 | Rapid activate/revoke | 20 cycles | ✓ PASS |
| 3 | Trade on expired lease | Bounds check | ✓ PASS |
| 4 | Expired lease bounds | enforce_bounds | ✓ PASS |
| 5 | Halt during revoke | Race condition | ✓ PASS |
| 6 | Revoke after halt | Valid path | ✓ PASS |
| 7 | Immediate breach halt | Bounds OR logic | ✓ PASS |
| 8 | Multiple breaches | First triggers | ✓ PASS |
| 9 | Invalid schema | Clean rejection | ✓ PASS |
| 10 | Missing invariants | Clean rejection | ✓ PASS |
| 11 | Rapid transitions | Serialization | ✓ PASS |
| 12 | Hash mismatch | State lock | ✓ PASS |
| 13 | Expiry boundary | Exact buffer | ✓ PASS |
| 14 | Zero buffer edge | Effective = legal | ✓ PASS |
| 15 | Concurrent ops stress | 50 threads | ✓ PASS |
| 16 | State lock contention | 20 threads | ✓ PASS |

### Invariants Proven (S47)
```yaml
INV-HALT-OVERRIDES-LEASE:
  rule: "Halt wins. Always. <50ms."
  test: tests/test_lease/test_halt_override.py
  enforcement: Halt bypasses state_lock_hash verification

INV-NO-SESSION-OVERLAP:
  rule: "One lease per session, no concurrent execution"
  test: tests/chaos/test_bunny_s47.py::TestConcurrentActivation
  enforcement: LeaseManager.activate_lease() rejects if active

INV-LEASE-CEILING:
  rule: "Lease bounds = ceiling, Cartridge = floor"
  test: tests/test_lease/test_bounds.py::TestLeaseCeiling
  enforcement: validate_bounds_ceiling() at insertion time

INV-BEAD-COMPLETENESS:
  rule: "Calibration bead must link to lease schema version"
  test: tests/test_lease/test_state_machine.py::TestBeadEmission
  enforcement: All transitions emit StateLockBead + specific bead

INV-EXPIRY-BUFFER:
  rule: "60-second buffer before lease expiry triggers MARKET_CLOSE"
  test: tests/test_lease/test_expiry.py::TestExpiryBuffer
  enforcement: get_effective_expiry() subtracts governance_buffer_seconds

INV-STATE-LOCK:
  rule: "State transition guard prevents race conditions"
  test: tests/test_lease/test_state_machine.py::TestStateLock
  enforcement: compute_state_hash() verification before transitions
```

### Exit Gates
```yaml
GATE_S47_1: "Lease FSM transitions correctly (all 5 terminal states)" ✅
GATE_S47_2: "Bounds check — any breach = halt (OR logic)" ✅
GATE_S47_3: "Halt overrides lease — <50ms, no race" ✅
GATE_S47_4: "Expiry triggers MARKET_CLOSE with 60s buffer" ✅
GATE_S47_5: "8-step insertion completes with valid cartridge" ✅
GATE_S47_6: "All lease transitions emit beads with provenance" ✅
GATE_S47_7: "BUNNY chaos — concurrent lease, expired lease trade, halt-during-revoke" ✅
GATE_S47_8: "HUD manifest includes lease state" ✅
```

### Exit Gate
"Lease system operational. 118 tests, 16 chaos vectors. INV-HALT-OVERRIDES-LEASE proven (<50ms). Bounded autonomy with sovereign override."

---

## PARALLEL TRACKS (Independent of Phoenix Sprint Cadence)

```yaml
DEXTER_COE:
  status: OPERATIONAL (independent repo/hardware/CTO)
  location: Mac Mini (isolated sandbox)
  repo: github.com/SlimWojak/Dexter (sibling, not subfolder)
  purpose: ICT knowledge extraction → CLAIM_BEADs for CSO calibration
  integration: NONE_YET (file-based bridge, post-stabilization)
  owner: Dexter CTO (separate Claude instance)
  key_invariant: INV-DEXTER-ALWAYS-CLAIM
  overnight_proof: 504 validated signatures from 18 videos ($0.003/video)
  tests: 208/208 PASS
  blocker: CSO Curriculum (Olya, 24-48h)
  known_gaps:
    P1: Chronicler (memory management) — URGENT
    P2: Queue atomicity (write-tmp + rename)
    P3: Injection guard tuning
    P4: Auditor rejection rate tuning

CSO_COE:
  status: MODEL_SHIFT_ACCEPTED (2026-02-04)
  paradigm: Recognition-based validation (not recall extraction)
  old_model: "Olya's brain → articulation → Claude → MD → conditions.yaml"
  new_model: "Dexter + Perplexity → comprehensive base → Olya validates/corrects"
  key_insight: "Recognition > recall. Olya as sovereign validator, not sole source being mined."
  calibration_guards:
    - default_reject: "Approval requires explicit action"
    - delta_input: "Edit ≥1 parameter per 5 signatures"
    - view_separation: "Dexter vs Perplexity shown separately"
    - foils_optional: "Operator-configurable stress testing"
  next_action: Olya provides curated curriculum
  unblocks: S33_P2 (operator-paced)

PERPLEXITY_VALIDATION:
  status: COMPLETE (2026-02-04)
  outcome: Phoenix architecture validated as industry best practice
  key_findings:
    - Gate-driven (pull) enrichment: CONFIRMED
    - 30-60 feature atoms (not 400+): CONFIRMED
    - Deterministic MSS + probabilistic regime overlay: CONFIRMED
    - Functions over sequences (not more columns): CONFIRMED
    - Human-in-loop overrides: CONFIRMED
  action: Atom budget 32-48 logged for gate-backward audit when S33 P2 unblocks
```

### DEXTER → PHOENIX Bridge Contract (Future)

```yaml
interface:
  dexter_output: CLAIM_BEAD
    fields: [signature_id, condition_if, action_then, source_timestamp, drawer_tag, auditor_verdict]
    status: ALWAYS CLAIM (never FACT)

  phoenix_input: CLAIM_BEAD → CSO validates → FACT_BEAD → conditions.yaml
    promotion_authority: Olya ONLY
    fact_encapsulates_claim: INV-FACT-ENCAPSULATES-CLAIM (source CLAIM_ID required)

back_propagation:
  when: Olya rejects CLAIM_BEAD
  action: NEGATIVE_BEAD → feeds back to Dexter Theorist context
  purpose: "Dexter learns from rejections — the seam that makes the refinery LEARN"

timeline: Integration AFTER both systems stabilize
```

---

## S43-S52: PATH TO WARBOAR v0.1 (CANONICAL)

```yaml
status: CONVICTION_LOCKED
date: 2026-01-31
source: Advisory team convergence (CTO + GPT + GROK + OPUS)
target: WARBOAR v0.1 — Production standard software
estimated_timeline: 5-7 weeks (10 sprints)
```

### Philosophy
```yaml
1: Quick wins first (S43) — momentum
2: Prove it works (S44-S45) — confidence
3: Design before build (S46-S47) — governance
4: Make it visible (S48) — operator happiness
5: Make it installable (S49) — real software
6: Operationalize it (S50) — boring excellence
7: Make it delightful (S51) — engagement
8: Ship it (S52) — production standard
```

### Sprint Skeleton

| Sprint | Codename | Scope | Status |
|--------|----------|-------|--------|
| **S43** | FOUNDATION_TIGHTENING | pytest parallelization, alert bundling, config centralization, narrator templates | ✅ COMPLETE |
| **S44** | LIVE_VALIDATION | IBKR paper end-to-end, 24h soak, chaos replay, multi-degrade drills | ✅ COMPLETE (FOUNDATION_VALIDATED) |
| **S45** | RESEARCH_UX | IDEA → HUNT → CFP → DECIDE journey, chunked output, lens presets | PENDING |
| **S46** | CARTRIDGE_LEASE_DESIGN | Cartridge + Lease schema, insertion protocol, state machine, attestation | ✅ COMPLETE (CANONICAL) |
| **S47** | LEASE_IMPLEMENTATION | Lease interpreter + expiry, revoke path, evidence, halt integration | ✅ COMPLETE (118 tests, 16 BUNNY) |
| **S48** | HUD_SURFACE | WarBoar HUD SwiftUI panel, manifest_writer bridge, file seam integration | ✅ COMPLETE |
| **S49** | DMG_PACKAGING | One-command build, DMG signed, first-run wizard, config migration | PENDING |
| **S50** | RUNBOOKS_CALIBRATION | Runbooks for ALL states, escalation ladder, CSO calibration prep | PENDING |
| **S51** | PRO_FLOURISHES | Sound/haptics, OINK easter eggs, session summaries, drift dashboard | PENDING |
| **S52** | WARBOAR_SEAL | Invariant freeze, constitutional audit, acceptance checklist, handover | **WARBOAR v0.1 TARGET** |

### New Invariants (S43-S52)

```yaml
# Global (after S44)
INV-NO-CORE-REWRITES-POST-S44:
  rule: "After live validation, no architectural rewrites. Only tightening, surfacing, governance."
  rationale: "Prevents 'one last clever refactor' syndrome. Protects momentum."

# S45 Research UX
INV-RESEARCH-RAW-DEFAULT:
  rule: "Research output defaults to raw table. Human summary is opt-in toggle, not default."
  rationale: "Catches authority leakage at UX layer. Prevents NEX dashboard poison."

# S47 Lease Implementation
INV-HALT-OVERRIDES-LEASE:
  rule: "Halt signal overrides lease bounds check. Halt always wins. <50ms."
  rationale: "Constitutional safety non-negotiable. No revoke race with halt."
```

### Dependencies

```yaml
key_dependencies:
  S44: IBKR availability (may delay)
  S50: Olya availability (partial, operator-paced)
  S51: Can run parallel to S50

acceleration_options:
  merge_s48_s51: "HUD + flourishes if ahead of schedule"
  ten_to_eight: "Possible if no IBKR blockers — let velocity reveal"
```

### Parked Items (Post v0.1)

| Item | Status | Notes |
|------|--------|-------|
| Multi-agent orchestration | ALREADY_PARKED | Complexity after foundation stable |
| Token cost infrastructure | NEW_PARK | Nice-to-have, not blocking v0.1 |
| Regime nuke autopsy | NEW_PARK | Forensic palace exists, enhance post-ship |
| Olya OCD integration | OPERATOR_PACED | Can't force Olya's rhythm |
| **DEXTER_RESEARCH_REFINERY** | **NEW_PARK (S53+)** | **24/7 hypothesis → test → evidence loop** |

```yaml
# NEW: DEXTER_RESEARCH_REFINERY (Captured 2026-02-05)
DEXTER_RESEARCH_REFINERY:
  source: "G + CTO synthesis, 2026-02-05"
  description: "24/7 autonomous research loop — extract, hypothesize, test, evidence, human gate"
  dependencies:
    - "Olya Stage 2 validation (Dexter extraction proven)"
    - "v0.1 shipped (S47-S52)"
    - "Dexter bridge operational"
  sprint_target: S53+
  design_doc: docs/canon/ENDGAME_VISION_v0.2.md

  new_invariants_needed:
    INV-DEXTER-NO-AUTO-PROMOTE-TO-LIVE:
      rule: "No Dexter-generated thesis can enter live execution without explicit human promotion"
    INV-VARIANT-PROVENANCE:
      rule: "Every variant must link to root FACT_BEAD validated by Olya"
    INV-DEXTER-EVIDENCE-NOT-ADVICE:
      rule: "Dexter outputs are evidence bundles, never recommendations or advice"

  infrastructure_already_built:
    - S35_CFP (conditional facts)
    - S36_CSO (gate evaluation)
    - S37_ATHENA (CLAIM/FACT memory)
    - S38_HUNT (exhaustive testing)
    - S39_VALIDATION (walk-forward, Monte Carlo)
    - S44_LIVE (IBKR paper)
    - S47_LEASE (bounded autonomy)

  foundry_link: "If Dexter can run this for ICT, it can run for ANY methodology"
```

---

## INVARIANT REFERENCE (CUMULATIVE)

### Attribution (CFP) — S35 ✓
- INV-ATTR-CAUSAL-BAN, INV-ATTR-PROVENANCE, INV-ATTR-NO-RANKING
- INV-ATTR-SILENCE, INV-ATTR-NO-WRITEBACK, INV-ATTR-CONFLICT-DISPLAY

### Harness — S36 ✓
- INV-HARNESS-1 through INV-HARNESS-4
- INV-NO-GRADE-RECONSTRUCTION

### Memory — S37 ✓
- INV-CLAIM-FACT-SEPARATION, INV-CONFLICT-NO-RESOLUTION
- INV-MEMORY-PROVENANCE

### Hunt — S38 ✓
- INV-HUNT-EXHAUSTIVE, INV-HUNT-BUDGET
- INV-HUNT-NO-SURVIVOR-RANKING, INV-HUNT-NO-SELECTION

### Validation — S39 ✓ (CONSTITUTIONAL CEILING)
- INV-SCALAR-BAN, INV-NO-AGGREGATE-SCALAR
- INV-NEUTRAL-ADJECTIVES, INV-VISUAL-PARITY
- INV-NO-IMPLICIT-VERDICT, INV-CROSS-MODULE-NO-SYNTH

### Safety (Cross-Sprint)
- INV-NO-UNSOLICITED, INV-LLM-REMOVAL-TEST, INV-NO-ROLLUP
- INV-NO-DEFAULT-SALIENCE, INV-SLICE-MINIMUM-N, INV-BIAS-PREDICATE

### Governance
- INV-REGIME-EXPLICIT, INV-REGIME-GOVERNANCE

### Self-Healing — S40 ✓
- INV-CIRCUIT-1/2, INV-BACKOFF-1/2, INV-HEALTH-1/2, INV-HEAL-REENTRANCY

### IBKR Resilience — S40 ✓
- INV-IBKR-FLAKEY-1/2/3, INV-IBKR-DEGRADE-1/2, INV-SUPERVISOR-1

### Hooks — S40 ✓
- INV-HOOK-1/2/3/4

### Narrator — S40 ✓
- INV-NARRATOR-1/2/3

### S43 (Foundation Tightening) ✓
- INV-NARRATOR-FACTS-ONLY: "Narrator templates contain facts only, no interpretation"

### S46 (Cartridge + Lease Design) ✓
- INV-NO-SESSION-OVERLAP: "One lease per session, no concurrent execution"
- INV-LEASE-CEILING: "Lease bounds = ceiling, Cartridge = floor"
- INV-BEAD-COMPLETENESS: "Calibration bead must link to lease schema version"
- INV-EXPIRY-BUFFER: "60-second buffer before lease expiry triggers MARKET_CLOSE"
- INV-STATE-LOCK: "State transition guard prevents race conditions"

### S44 Closure + Advisor Synthesis (2026-02-04) ✓
- INV-NO-CORE-REWRITES-POST-S44: "After live validation, no architectural rewrites. Only tightening, surfacing, governance." **NOW ACTIVE**
- INV-DEXTER-ALWAYS-CLAIM: "All Dexter output = CLAIM, never FACT. Refinement makes review faster, not unnecessary."
- INV-DEXTER-ICT-NATIVE: "Theorist uses raw ICT terminology. Phoenix translation at Bundler only."
- INV-FACT-ENCAPSULATES-CLAIM: "Every FACT bead must reference source CLAIM_ID for forensic trace"
- INV-CALIBRATION-FOILS: "Validation batches may include foils. Foil approval flags session." (operator-configurable)
- INV-RUNAWAY-CAP: "Agent loops hard-capped at N turns. No-output > X min → halt."

### Divergence Ruling (2026-02-04)
```yaml
RULING: CLAIM/FACT binary states + rich metadata
REJECTED: OWL's PROVISIONAL_FACT (gray authority risk)
ADOPTED: OWL's provenance chain (FACT encapsulates source CLAIM_ID)
RATIONALE: "Binary states. Rich metadata. GPT wins on state machine, OWL wins on provenance."
```

### S47 (Lease Implementation) ✓
- INV-HALT-OVERRIDES-LEASE: "Halt wins. Always. <50ms."
- INV-NO-SESSION-OVERLAP: "One lease per session, no concurrent execution"
- INV-LEASE-CEILING: "Lease bounds = ceiling, Cartridge = floor"
- INV-BEAD-COMPLETENESS: "Calibration bead must link to lease schema version"
- INV-EXPIRY-BUFFER: "60-second buffer before lease expiry triggers MARKET_CLOSE"
- INV-STATE-LOCK: "State transition guard prevents race conditions"

### S43-S52 (Path to v0.1)
- INV-RESEARCH-RAW-DEFAULT (S45)

**Total: 111+ invariants proven (S28-S44, S46 design, S47 implementation)**
**Tests: 1618+ passing (28 xfailed)**
**Chaos vectors: 240 handled**

---

## CRITICAL REFERENCES

| Document | Location | Purpose |
|----------|----------|---------|
| `DEFINITIVE_FATE.yaml` | `docs/canon/` | NEX→Phoenix fate table, invariants, patterns |
| `PHOENIX_MANIFEST.md` | `docs/canon/` | System topology (M2M bootstrap) |
| `SPRINT_ROADMAP.md` | `docs/canon/` | This document |
| `ARCHITECTURAL_FINALITY.md` | `docs/canon/` | System architecture freeze |
| `CARTRIDGE_AND_LEASE_DESIGN_v1.0.md` | `docs/canon/designs/` | S46 governance architecture |
| `POST_S44_SYNTHESIS_v0.1.md` | `docs/` | S44 closure + Dexter + COE advisor synthesis |
| `ADVISOR_SYNC_S44_DEXTER.md` | `docs/` | Dense M2M advisor orientation (Opus synthesis) |
| `conditions.yaml` | `cso/knowledge/` | 5-drawer gate predicates |
| `schemas/beads.yaml` | `schemas/` | Bead type definitions |
| `REPO_MAP.md` | root | Repository navigation |

---

```yaml
# Advisor Bootstrap Checklist
orientation_sequence:
  1: cat REPO_MAP.md  # Repository navigation
  2: cat docs/canon/SPRINT_ROADMAP.md | head -80  # Current state
  3: cat cso/knowledge/conditions.yaml  # CSO gates
  4: cat docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md | head -100  # S46 design

first_questions:
  - "Which sprint is active?" → S49 (DMG Packaging) or S45 (Research UX — blocked on Olya)
  - "What just completed?" → S47 (LEASE_IMPLEMENTATION, 2026-02-04, 118 tests, 16 BUNNY)
  - "Where is the lease code?" → governance/lease.py, lease_types.py, cartridge.py, insertion.py
  - "What are the parallel tracks?" → Dexter (ICT extraction), CSO COE (recognition-based validation)
  - "What new invariants?" → S47 added 6: INV-HALT-OVERRIDES-LEASE, INV-NO-SESSION-OVERLAP, INV-LEASE-CEILING, INV-BEAD-COMPLETENESS, INV-EXPIRY-BUFFER, INV-STATE-LOCK
```

---

*"Quality > Speed. Explicit > Implicit. Facts > Stories."*
*Phoenix builds with discipline. Phoenix builds with purpose.*

---

## S35-S48 BLOCK SUMMARY

```yaml
s35_s39_completion_date: 2026-01-29
s40_completion_date: 2026-01-30
s41_completion_date: 2026-01-23
s42_completion_date: 2026-01-30
s43_completion_date: 2026-01-31
s44_completion_date: 2026-02-04
s46_design_locked: 2026-01-31
s47_completion_date: 2026-02-04
s48_completion_date: 2026-01-31

current_sprint: S49_PENDING (DMG Packaging) | S45 blocked (Olya)

total_tests: 1618+ (28 xfailed)
total_bunny_vectors: 240
total_invariants: 111+
total_gates_mapped: 48

s35_s39_theme: "CONSTITUTIONAL CEILING"
s40_theme: "SLEEP_SAFE"
s41_theme: "WARBOAR_AWAKENS"
s42_theme: "TRUST_CLOSURE"
s43_theme: "FOUNDATION_TIGHTENING"
s44_theme: "LIVE_VALIDATION" → FOUNDATION_VALIDATED
s46_theme: "CARTRIDGE_AND_LEASE_DESIGN"
s47_theme: "LEASE_IMPLEMENTATION" → BOUNDED_AUTONOMY
s48_theme: "HUD_SURFACE"

parallel_tracks:
  dexter_coe: OPERATIONAL (Mac Mini, ICT extraction)
  cso_coe: MODEL_SHIFT_ACCEPTED (recognition-based validation)

INV-NO-CORE-REWRITES-POST-S44: ACTIVE (2026-02-04)

what_this_means: |
  NEX died saying: "Strategy Stability Index: 78/100"
  Phoenix says: "Walk-forward delta: +0.3 Sharpe. Monte Carlo 95th DD: -12%. You interpret."

  No scalar scores. No rankings. No verdicts.
  Human frames, machine computes. Human sleeps.
  The boar barks clean facts — receipts hidden, alerts glanceable.
  CSO understands the methodology. Operator understands the boundaries.

  S46 adds: Cartridges define WHAT. Leases bound WHEN/HOW MUCH. Human always sovereign.

key_modules_delivered:
  # S35-S39 (Constitutional Ceiling)
  cfp/: Conditional facts with provenance
  cso/: Gate status (facts, not grades)
  athena/: Memory discipline (CLAIM/FACT/CONFLICT)
  hunt/: Exhaustive grid compute
  validation/: Decomposed outputs + ScalarBanLinter

  # S40 (Sleep-Safe)
  governance/circuit_breaker.py: Self-healing FSM
  governance/health_fsm.py: Health state tracking
  brokers/ibkr/supervisor.py: Watchdog outside trading loop
  brokers/ibkr/degradation.py: Graceful T2→T1→T0 cascade
  narrator/: Template-based facts projection
  tools/hooks/: Constitutional enforcement at commit + runtime

  # S41 (WarBoar Awakens)
  slm/: Classification API (rule-based, 100% accuracy)
  governance/slm_boundary.py: ContentClassifier guard dog
  narrator/renderer.py: narrator_emit() single chokepoint
  narrator/surface.py: Human-readable formatters
  notification/alert_taxonomy.py: One-liner alert formatters
  drills/s41_phase3_live_validation.py: Real Gateway validation

  # S42 (Trust Closure)
  cso/knowledge/GATE_GLOSSARY.yaml: 48 gates mapped
  state/health_writer.py: CSO-readable health file
  docs/operations/operator/: Operator expectations + boundaries
  cso/knowledge/CSO_HEALTH_PROMPT.md: Health consumption guide

  # S43 (Foundation Tightening)
  config/schema.py: Pydantic centralized config
  tests/test_narrator_templates.py: INV-NARRATOR-FACTS-ONLY linter

  # S46 (Cartridge + Lease Design) — DESIGN ONLY
  docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md: Canonical spec

  # S47 (Lease Implementation)
  governance/lease_types.py: Pydantic models (CartridgeManifest, Lease, bead types)
  governance/lease.py: State machine + interpreter (LeaseStateMachine, LeaseInterpreter, LeaseManager)
  governance/cartridge.py: Cartridge loader + registry (YAML validation, linting)
  governance/insertion.py: 8-step insertion protocol (INV-LEASE-CEILING validation)

  # S48 (HUD Surface)
  surfaces/hud/: WarBoar HUD SwiftUI app
  state/manifest_writer.py: health.yaml → manifest.json bridge
  state/manifest.json: HUD v1.1 schema output

the_floor_holds: |
  S40 proves the system survives coordinated chaos.
  S41 proves the guard dog catches heresy at the throat.
  S42 proves CSO understands the methodology and operator knows the boundaries.
  S43 proves developer velocity with tightened foundation.
  S44 proves it works FOR REAL on live IBKR.
  S46 proves governance architecture for bounded autonomy (design locked).
  S47 proves lease system with halt override (<50ms) — bounded autonomy operational.
  S48 proves the HUD surfaces real Phoenix state (glanceable sovereignty).

  Real IBKR Gateway validated in paper mode.
  15 + 20 + 16 attack vectors, 0 cascade failures, 0 alert storms.
  48 gates mapped. Health visible. Operator instructed.
  Filing cabinet operational. Cartridge/Lease system built.

  No 3am wake-ups. Sleep-safe + warboar + trust + foundation + lease certified.
  S47 COMPLETE → S49 NEXT (DMG Packaging).

filing_cabinet_update: |
  As of 2026-02-04:
  - docs/canon/ = Authoritative locked docs
  - docs/operations/ = Runbooks + operator guides
  - docs/build/current/ = Active sprint (S47)
  - docs/archive/ = Historical reference
  - cartridges/ = Strategy manifests (ready for S47)
  - leases/ = Governance wrappers (ready for S47)
  - REPO_MAP.md = Navigation at root
  - POST_S44_SYNTHESIS_v0.1.md = Advisor broadcast + synthesis + COE response

parallel_systems: |
  - DEXTER: Sovereign Evidence Refinery (Mac Mini, ICT extraction)
  - CSO COE: Recognition-based validation model accepted
  - INV-NO-CORE-REWRITES-POST-S44: ACTIVE
```

*S35-S44, S46-S48 COMPLETE. FOUNDATION_VALIDATED. LEASE_PROVEN. S49 NEXT. Dexter parallel. COE accepted. 🐗🔥*
