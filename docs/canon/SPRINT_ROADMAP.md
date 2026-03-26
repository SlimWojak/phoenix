# SPRINT_ROADMAP.md
# Phoenix Sprint Roadmap — M2M Advisor Reference

```yaml
document: SPRINT_ROADMAP.md
version: 5.0
date: 2026-03-20
status: CANONICAL — updated post S64 METHODOLOGY CALIBRATION
brand: a8ra (Phoenix is internal codename — see docs/canon/BRAND_IDENTITY.md)
format: M2M_DENSE
audience: Advisors (GPT, GROK, OWL, Opus)
methodology: SYNTHETIC_OLYA_METHOD_vLOCK.yaml (supersedes v0.4, v0.6)
```

---

## CURRENT STATE

```yaml
current_sprint: S66 — STATE_CLASSIFIER_TUNING (NEXT)
status: S65_COMPLETE | ZERO_TIER1 | ZERO_TIER2 | HALT_OPERATIONAL | ORACLE_BOOTSTRAPPED | BRIDGE_OPERATIONAL | METHODOLOGY_vLOCK | STATE_DETECTION_v2.4 | 11_PRODUCERS | GATE6_OLYA_CONFIRMED | FIVE_FACTOR_CHECKLIST | DIAGNOSTIC_SIGNAL | HTF_DISPLACEMENT_FIXED
s33_p2: BLOCKED (Olya CSO calibration) — CoE model accepted, not required for v0.1

recent_completions:
  s43_completion_date: 2026-01-31
  s44_completion_date: 2026-02-04
  s46_design_locked: 2026-01-31
  s47_completion_date: 2026-02-04
  s48_completion_date: 2026-01-31
  filing_cabinet: 2026-01-31
  a8ra_brand_capture: 2026-02-09
  mission_control_v0.2: 2026-02-09
  ground_tests: 2026-02-09
  phoenix_swarm_repo: 2026-02-09
  office_identities: 2026-02-09
  brand_identity: 2026-02-09
  s49_completion_date: 2026-02-20
  s50_completion_date: 2026-02-22   # SEAL — a8ra v0.1
  bead_field_gate_1: 2026-02-22     # 274 tests, 789 Genesis beads
  dgx_spark_arrived: 2026-02-21
  s51_completion_date: 2026-02-22   # DRIVESHAFT + RIVER FOUNDATION
  river_phase_1: 2026-02-22         # 11.8M bars, 6 pairs, seam attested
  s52_completion_date: 2026-02-23   # Post-audit hardening (4 tracks)
  s53_completion_date: 2026-02-24   # JANK_NUKE — seam correctness, sentinel wiring
  s53_1_completion_date: 2026-02-24 # Oracle audit remediation
  s54_completion_date: 2026-02-25   # TRUTH_SWEEP + RIVER_PATCH + MYPY
  s55_completion_date: 2026-02-25   # HALT_WIRE — constitutional kill switch
  s56_completion_date: 2026-02-25   # LOUD_FAILS — silent fail hardening
  s57_completion_date: 2026-02-25   # ORACLE_BOOTSTRAP — Three-Surface Cockpit
  s58_completion_date: 2026-02-25   # HYGIENE — dead code, doc fixes, cleanup
  s59_completion_date: 2026-02-25   # LEASE_WIRE — sovereign gate, write-ahead governance
  s60_completion_date: 2026-02-25   # CEREMONY_AND_HYGIENE — ceremony engine, debt cleanup
  s62_completion_date: 2026-02-28   # BRIDGE_BUILD + GATE_2 — notary pipeline + query layer
  s63_completion_date: 2026-03-03   # FIELD_ACTIVATION — M3 deployed, Spitfire audit, CLAIM pipeline spec
  s64_gates_1_3_met: 2026-03-19    # CLAIM_PIPELINE + METHODOLOGY_CALIBRATION (Gates 1-3 MET)
  s64_completion_date: 2026-03-20   # ALL 6 GATES SEALED — vLOCK producers operational, Olya confirmed
  s65_completion_date: 2026-03-21   # STRATEGY_ASSEMBLY — checklist, signals, HTF displacement fix

certification: v0.1_SEALED | RIVER_PHASE_1_COMPLETE | WARBOAR_CERTIFIED | LIVE_GATEWAY_VALIDATED | CSO_PRODUCTION_READY | S46_CANONICAL | HUD_INTEGRATED | S44_FOUNDATION_VALIDATED | S47_LEASE_PROVEN | MC_v0.2_LOCKED | BEAD_FIELD_GATE_1 | S51_DRIVESHAFT_DELIVERED | S52_HARDENED | S53_JANK_NUKED | S54_TRUTH_SWEPT | MYPY_CAPITAL_PATH_CLEAN | S55_HALT_WIRED | S56_LOUD_FAILS | S57_ORACLE_BOOTSTRAPPED | S58_HYGIENE | S59_LEASE_WIRE | S60_CEREMONY | S62_BRIDGE_AND_GATE2 | S63_FIELD_ACTIVATION | S64_METHODOLOGY_vLOCK | S64_COMPLETE | S65_STRATEGY_ASSEMBLY | S65_COMPLETE
cumulative:
  sprints_complete: 37 (S28-S44, S46-S60, S62-S65)
  tests_passing: 1887+ Phoenix | 869 Dexter (651 S64 + 218 S65)
  chaos_vectors: 273/273 PASS
  invariants_registered: 259 Phoenix + 7 Bridge + 1 DEC-FREEZE-INDEX-CARVEOUT
  bead_types: 17+
  runbooks: 8
  gate_glossary: 48 gates mapped
  seal_tag: v0.1
  mypy_strict_capital_path: 0 errors (governance/ execution/ cso/)
  methodology: vLOCK (13 L1 primitives, walk-forward validated, Olya confirmed)
  ground_truth: 14 Olya-annotated trades (Sep 2025 – Mar 2026)
  producers: 11 vLOCK CLAIM producers operational (VI retired)
  state_detection: v2.4 (14/14 phase classification, HOLD_DEFAULTS)
  reference_impl: detect.py (test oracle for core producers)

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

## S50: SEAL (a8ra v0.1)

```yaml
status: COMPLETE — SEALED 2026-02-22
tag: v0.1
commit: d9de8d5

tracks:
  T1_CABINET_REFACTOR: COMPLETE (6/6 gates, drawer_deltas→drawer_config)
  T1.1_GPT_HARDENING: COMPLETE (4/4 gates, extra='forbid', guard dog cabinet scan)
  T2_INVARIANT_FREEZE: COMPLETE (150+ frozen, tiered registry)
  T3_FULL_SUITE_REPLAY: COMPLETE (1615 pass, 264 chaos, 0 failures)
  T4_ESCALATION_LADDER: COMPLETE (4-tier, G signed)
  T5_ACCEPTANCE_CHECKLIST: COMPLETE (20/20 sprint gates, G signed)
  T6_SEAL: COMPLETE (tagged, pushed)

origin: Olya (CSO) identified methodology/strategy blending in conditions.yaml
resolution: 5-drawer cabinet model — each cartridge self-contained
advisory: GPT lint (10 flags, 5 fixed pre-SEAL)
parallel: Bead Field Gate 1 PASS (same day)

new_invariants:
  INV-CABINET-COMPLETE: "Every cartridge must provide all 5 canonical drawers, non-empty"
  INV-CABINET-STRICT: "DrawerConfig rejects unknown drawer keys"

deliverables:
  - INVARIANT_REGISTRY.yaml
  - ACCEPTANCE_CHECKLIST_v0.1.md
  - ESCALATION_LADDER.md
  - SEAL_v0.1.md
```

### Exit Gate
"a8ra v0.1 SEALED. 20 sprints complete. 150+ invariants frozen. 1615 tests. 264 chaos vectors. Zero failures. Both economies shipped same day."

---

## S51: DRIVESHAFT (First Strategy End-to-End)

```yaml
status: COMPLETE ✓
completion_date: 2026-02-22
tests: 50 new (1716 total)
theme: "Wire the engine to the gearbox. First strategy runs end-to-end."
target_strategy: ASIA_RANGE_SCALP
preceded_by: POST-SEAL.AUDIT.001 (PRIMITIVE_READINESS_AUDIT)

tracks:
  T1_WIRING: COMPLETE (market_state_builder.py — enrichment→evaluator bridge)
  T2_PRIMITIVES: COMPLETE (l7_asia_scalp.py — RE_ACCEPTANCE, sweep ext, FVG validation)
  T3_DRAWER_ALIASES: COMPLETE (CONTEXT/MONITORING/SETUP/EXECUTION/MANAGEMENT accepted)
  T4_EXECUTION: COMPLETE (asia_scalp.py — entry, SL/TP, sizing, session limits)
  T5_VALIDATION: COMPLETE (50 tests, 0 regressions across 1716 total)

architecture_change: |
  BEFORE: Enrichment pipeline (L1-L6) and CSO evaluator existed as two disconnected layers.
  AFTER: market_state_builder.py bridges enrichment DataFrames → frozen MarketState → evaluator.
  Asia Range Scalp runs end-to-end: IBKR data → enrichment → MarketState → evaluator → setup detection → trade proposal with SL/TP/sizing.

new_files:
  - cso/market_state_builder.py (frozen dataclass factory, pure adapter)
  - cso/enrichment_to_state_map.yaml (per-field mapping specification)
  - enrichment/layers/l7_asia_scalp.py (RE_ACCEPTANCE + Asia primitives + state machine)
  - execution/asia_scalp.py (trade lifecycle engine)
  - cartridges/active/asia_range_scalp.yaml (v2.0, rewritten from Olya canonical doc)
  - tests/test_s51_driveshaft/ (50 tests across 4 files)

modified_files:
  - cso/evaluator.py (MarketState: frozen, S51 fields added)
  - governance/lease_types.py (DrawerConfig alias normalization)
  - enrichment/layers/__init__.py (L7 registration)
  - tests/test_lease/test_cabinet_validation.py (adapted for alias compatibility)

new_invariants:
  INV-NO-FORMING-CANDLE: "Never evaluate gates on incomplete bar data"
  INV-BUILDER-PURE-ADAPTER: "MarketState builder does no scoring, inference, or heuristic"
  INV-PIT-JOIN-ONLY: "Point-in-time join — only data indexed < evaluation_time visible"
  INV-ALIAS-PARSER-BOUNDARY: "Drawer name aliases die at YAML parser, never persisted"

decisions_locked:
  D1: "Compatibility layer for drawer names (NOT true rename)"
  D6: "Entry type: Market order at Candle C close"
  D7: "SL buffer: 0.5 pip (0.00005) beyond sweep extreme"
  D9: "1 trade per Asia session (19:00 NY start)"
  D10: "Min R:R 1.5"
  D11: "FVG min 1.0 pip untouched area"

next_candidates:
  S55_LIVE_VALIDATION: "River streamer live market confirmation, multi-pair heartbeat"
  ICT_DIRECTIONAL: "Second strategy — HTF bias, IPDA, MMXM, Middleman (proves harness is strategy-agnostic)"
  DRAWER_TRUE_RENAME: "If aliases prove annoying, staged migration from S51 alias layer"
```

### Exit Gate
"Asia Range Scalp runs end-to-end: IBKR data → enrichment → MarketState → evaluator → setup detection → trade proposal with correct SL/TP/sizing. 50 new tests, 0 regressions. 1716 total passing."

---

## S51 RIVER FOUNDATION (Phase 1)

```yaml
status: COMPLETE ✓
completion_date: 2026-02-22
theme: "The epistemic root of Phoenix gets constitutional-grade infrastructure."
brief: S51_RIVER_BUILD_BRIEF_v1.1.md (CTO authored, Opus reviewed, G signed)
doctrine: RIVER_SYNTHESIS.md (OWL + GPT + BOAR convergence)

tracks:
  T0_CAPTURE: DONE (180,840 bars, 6 pairs, IBKR overlap insurance)
  T1_AUDIT: PASS (6/6 pairs, NEX_AUDIT_REPORT.md)
  T1B_DUKASCOPY: DESCOPED (NEX data covers full range)
  T2_WRITER: DONE (RiverWriter hardened, RIVER_ROOT env, volume semantics)
  T3_BACKFILL: DONE (11.6M bars ingested from NEX, 58 seconds)
  T4_READER: DONE (DuckDB RiverReader, ghost injection, TF derivation)
  T5_SEAM: PASS (three-way cross-validation, G signed attestation)
  T6_CONTRACT: DONE (ICT_DATA_CONTRACT §7.2-7.5 amended)
  T7_WIRING: DONE (RIVER_SOURCE bridge, 1665 tests pass, zero regressions)
  T8_STREAMING: BUILT (RiverStreamer, pending live market validation)

surprise_finding: |
  NEX data extends to Feb 20, 2026 (not Nov 2025 as expected).
  NEX enrichment pipeline was already refreshing from IBKR.
  Source boundary: Nov 21/22 2025 (volume flips positive→-1).
  T1B descoped. Three-way seam validation materialized for free.

new_invariants:
  INV-RIVER-BITEMPORAL: "Every bar carries world_time + knowledge_time"
  INV-RIVER-IMMUTABLE: "Raw parquet files are write-once, never modified"
  INV-RIVER-CONTINUOUS: "No gaps in materialized 1m series (ghosts flagged)"
  INV-RIVER-SOURCE-TAG: "Every bar carries source provenance forever"
  INV-RIVER-IBKR-PRIMACY: "Execution venue = data authority for live"
  INV-RIVER-FRESHNESS: "market_state_builder refuses stale data"

new_files:
  - river/schema.py (RAW_BAR_SCHEMA, hashing, validation)
  - river/writer.py (RiverWriter — IBKR → daily parquet)
  - river/reader.py (RiverReader — DuckDB, ghosts, TF derivation)
  - river/streamer.py (live 1m → staging JSONL → daily parquet)
  - river/nex_ingestor.py (NEX → River with source tags)
  - river/seam.py (three-way reconciliation)
  - scripts/nex_audit.py (reusable audit tooling)

modified_files:
  - data/river_reader.py (RIVER_SOURCE bridge)
  - docs/canon/ICT_DATA_CONTRACT.md (ghost bar amendment)

data:
  location: "~/phoenix-river/ (RIVER_ROOT env override)"
  pairs: [EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD]
  bars_per_pair: ~1,960,000
  total_bars: ~11,800,000
  range: "2020-11-23 → 2026-02-20"
  partition: "{pair}/{year}/{mm}/{dd}.parquet"

estimate_vs_actual: |
  Brief estimated 5-6 days. Delivered in 2 days.
  8 of 8 gates passed. T8 pending live market validation (weekend).

next: S52 CSO_SURFACE (HUD gates, alerts, CSO Claude wiring)
```

### Exit Gate
"River Phase 1 operational. 11.8M bars across 6 pairs. Three-way seam validated. Ghost bar hybrid policy live. Enrichment wired to new River. 1665 tests pass, zero regressions. G signed seam attestation."

---

## S53: JANK_NUKE — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-24
theme: "Seam correctness, wire partials, seal contracts."
origin: Blind Opus oracle audit revealed 3 TIER_2 + 4 DEBT items. Zero TIER_1.

tracks:
  SENTINEL_WIRING:
    - INV-SENTINEL-WIRED-1: intercept() on every capital mutation via HaltGate
    - INV-SENTINEL-FAIL-CLOSED-1: sentinel exception → SentinelHaltError, never continue
    - INV-CSE-EMIT-COMPLETENESS-1: scanner CSE validated at emit boundary
    - INV-CSE-VERSION-SINGLE-SOURCE-1: cse_version defined once in cso/constants.py
    - INV-E2E-DETERMINISTIC-1: identical inputs → identical outputs in synthetic mode
  FIDELITY:
    - execution/fidelity.py: FidelityRecord emitted on every fill
    - INV-EXECUTION-FIDELITY promoted UNTESTED → PROVEN
  CSE_CONTRACT:
    - tests/test_cse_contract/: schema completeness + version single-source tests

new_tests: ~20
new_invariants: 5
regressions: 0
```

### Exit Gate
"All S53 invariants proven. Sentinel wired and fail-closed. CSE emission validated at boundary. E2E determinism confirmed."

---

## S53.1: ORACLE_REMEDIATION — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-24
theme: "Blind oracle audit findings → trivial fixes."
commit: 68b2238

fixes:
  TASK_1: "governance/lease.py: assert→raise for INV-HALT-1 (survives python -O)"
  TASK_2: "INVARIANT_REGISTRY.yaml: +7 S53 invariants registered (30→37)"
  TASK_3: "a8ra_SYSTEM_MANIFEST: version 1.3→1.5"
  TASK_4: "DEC-GENESIS-SNAPSHOT: 981→789 corrected in decision log"

verification:
  make_truth_sync: PASS (37 invariants, manifest=1786, delta=0)
  pytest: 88 targeted tests passed (sentinel + CSE contract + halt-override + fidelity + e2e)
```

---

## S54: TRUTH_SWEEP + RIVER_PATCH + MYPY — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-25
theme: "Clear all TIER_2 doc drift, fix River streamer, type-safe capital path."

tracks:
  T1_EXECUTION_CONTRACT:
    status: COMPLETE
    fix: "execution_surface.yaml updated from stale 5-state S28.C to 10-state canonical FSM"
    commit: cbd5a48

  T2_CSE_ENUM:
    status: COMPLETE
    fix: "MOCK_5DRAWER added to cse_schema.yaml source enum (schema matches consumer reality)"
    commit: c410424

  T3_REGISTRY_EXPANSION:
    status: COMPLETE
    fix: "203 code-referenced INV-* IDs registered as stubs (37→240 entries)"
    commit: 41b218f
    method: "Programmatic grep + domain/tier inference + test ref resolution"

  RIVER_PATCH:
    status: COMPLETE
    fix: |
      - reqRealTimeBars (5s bars, wrong!) → reqHistoricalData(keepUpToDate=True, 1m bars)
      - IB error callback wired (logs errorCode, errorString, contract)
      - Watchdog: no first bar within 60s → WARN + resubscribe (max 3, exponential backoff)
      - Heartbeat: atomic JSON with state machine (STARTED→STREAMING→DEGRADED→STOPPED)
      - bar.open_ → bar.open, bar.time → bar.date (BarData vs RealTimeBar attribute names)
    commit: 000633a
    root_cause: "reqRealTimeBars only delivers 5-second bars. Docstring said '1m' but API doesn't support it."

  T4_MYPY_CAPITAL_PATH:
    status: COMPLETE
    fix: "mypy --strict governance/ execution/ cso/ → 0 errors (was 209)"
    commit: 05a8c10
    details: |
      209 errors across 37 files → zero.
      40 files edited. 5 justified type: ignore (pandas import-untyped ×2, ib_insync no-untyped-call ×2, union-attr ×1).
      Transitive files also fixed: brokers/ibkr/, memory/, intelligence/, daemons/.

  RIVER_TZ_FIX:
    status: COMPLETE
    fix: "pd.Timestamp tz incompatibility with ib_insync zoneinfo datetimes"
    commit: c2f6461

verification:
  make_truth_sync: PASS (240 invariants, manifest=1786, delta=0)
  mypy_strict: "Success: no issues found in 59 source files"
  pytest: 1751 passed, 25 xfailed, 2 skipped (2 pre-existing fixture issues excluded)
  river_tests: 20/20 passed
  freshness_tests: included in above

tier_status:
  TIER_1: 0
  TIER_2: 0
  DEBT: "Remaining — 167+ invariants in CONSTITUTION/ dir still aspirational-only (known from DELTA-7)"
```

### Exit Gate
"Zero TIER_1. Zero TIER_2. mypy --strict clean on capital path. River streamer uses correct primitive. 240 invariants registered. All truth-sync gates pass."

---

## S55: HALT_WIRE — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-25
theme: "Constitutional kill switch — Olya can halt, Phoenix refuses, G clears."
effort: "¾ day"
origin: "Forensic audit T1 risk: HALT.signal DESIGNED_NOT_BUILT"

tracks:
  T1_HALT_WRITE: "halt.sh — source-validated, idempotent, audit-logged, atomic (tmp+mv)"
  T2_EXECUTION_GATE: "check_halt_signal() — fail-closed on 5 error cases. Wired into insertion.py Step 7."
  T3_RESTART_GUARD: "clear_halt.sh — interactive-only (rejects piped/cron), logs clear event"
  T4_ORACLE_SURFACE: "Oracle CLAUDE.md — HALT authority section + boot sequence updated"
  T5_CHAOS_VECTORS: "5 chaos vectors (corrupt, concurrent, unknown schema, missing fields, zero bytes) + active interrupt design"

new_tests: 19
new_invariants: [INV-HALT-SIGNAL-CHECK, INV-HALT-CLEAR-LOGGED, INV-HALT-FAIL-CLOSED, INV-HALT-ENTROPY-PROOF]
regressions: 0
commits: [f63ab28 (phoenix-swarm), b08de2c (phoenix)]
```

---

## S56: LOUD_FAILS — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-25
theme: "Convert silent failures to loud failures across all repos."
effort: "¾ day (parallel with S55)"
origin: "Forensic audit: except Exception → pass on capital-adjacent paths"

tracks:
  T1_EXCEPTION_SCAN: "14 hits classified (5 capital-adjacent, 3 data-integrity, 6 benign). Documented in exception_scan.yaml."
  T2_KILL_MANAGER: "4 silent except-pass → log.error + raise on writes, log.error on reads. halt.py cascade logs warnings. t2/tokens.py audit bead logs errors."
  T3_SWARM_SCRIPTS: "launch_office.sh (dep checks, path validation, API abort). session_end_hook.sh (mkdir lock, local fallback). status.sh (yq check, HALT display, staleness flag)."
  T4_CONFIG_VALIDATION: "ExecutionMode enum + validate_boot(). Paper/live require IB creds. Invalid paths fail loud."

new_tests: 10
new_invariants: [INV-CONFIG-VALID-ON-BOOT]
regressions: 0
commits: [1927792 (phoenix-swarm), a3c9f60 (phoenix)]
```

---

## BOOT_GATE — PASS ✅

```yaml
status: PASS ✓
completion_date: 2026-02-25
theme: "Cold boot validation after S55+S56 hardening."
effort: "30 min (4 automated + 1 manual)"

steps:
  A_STATUS: "PASS — status.sh clean, all offices OFFLINE, no HALT"
  B_LAUNCH: "PASS — launch_office.sh boots, fails loud on missing Keychain (correct)"
  C_HALT_WRITE: "PASS — halt.sh writes valid HALT.signal"
  D_HALT_CHECK: "PASS — check_halt_signal returns halted=True, source=OLYA"
  E_CLEAR: "PASS — G cleared manually, interactive confirmed"

constitutional_proof: "Write → check → refuse → clear → resume. End-to-end proven."
```

---

## S57: ORACLE_BOOTSTRAP — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-25
theme: "Build Olya's Three-Surface Cockpit to operational Phase 1."
effort: "1 day"
dependency: "S55 (HALT must be wired)"

tracks:
  T1_CLAUDE_MD: "Full rewrite — Three-Surface Cockpit, Phase 1 honest labeling, capability mapping, HALT authority"
  T2_DIRECTORIES: "~/oracle/memory/ + archive.md + patterns.md created"
  T3_DATA_PROOF: "3 example scripts (first_query.sh, gate_status.sh, dry_run.sh)"
  T4_BROADCAST: "BROADCAST.md updated from S49 era to post-S58 state"
  T5_DRY_RUN: "Olya confidence-building rehearsal script (actually halts system)"

commits: [00f82e0 (phoenix-swarm)]
note: "Oracle not yet a git repo — CLAUDE.md + examples saved to disk."
```

---

## S58: HYGIENE — COMPLETE ✅

```yaml
status: COMPLETE ✓
completion_date: 2026-02-25
theme: "Dead code, stale docs, cleanup."
effort: "½ day"

tracks:
  T1_DEAD_CODE: "widget/ and narrator/ confirmed ACTIVE (not dead — skip archival). CONSTITUTION/README.md pointer to 240-entry registry."
  T2_DOC_FIXES: "BEAD_FIELD_SPRINT.md contradictions fixed (DELTA-16). DRIFT_LOG +2 entries (DELTA-16 FIXED, DELTA-17 ACKNOWLEDGED)."
  T3_SRC_VERIFY: "~/dexter/src/ does not exist. Documented as DELTA-17."
  T4_PUSH_LOCK: "Already done in S56 T3 (session_end_hook.sh mkdir lock pattern)."
  T5_DEPRECATION: "No moves needed — active code stays in place."

commits: [b6914fd (phoenix), ae577e6 (dexter), 367f294 (phoenix-swarm)]
```

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

## S43-S50: PATH TO WARBOAR v0.1 (CANONICAL)

```yaml
status: CONVICTION_LOCKED
date: 2026-02-09
source: Advisory team convergence (CTO + GPT + GROK + OPUS) — revised 2026-02-09
target: WARBOAR v0.1 — Production standard software
estimated_timeline: 4-5 days (2 sprints remaining)
revision_note: |
  Compressed from 4 remaining sprints to 2. Killed vanity sprints (DMG, code signing,
  wizard GUI, sound/haptics, easter eggs, drift dashboard, speculative runbooks).
  Result: ~2 weeks saved, 100% operational value retained.
```

### Philosophy
```yaml
1: Quick wins first (S43) — momentum
2: Prove it works (S44-S45) — confidence
3: Design before build (S46-S47) — governance
4: Make it visible (S48) — operator happiness
5: Make it operational (S49) — bare Mac → running office in one command
6: Lock and ship (S50) — invariant freeze, acceptance, WARBOAR SEAL
```

### Sprint Skeleton

| Sprint | Codename | Scope | Status |
|--------|----------|-------|--------|
| **S43** | FOUNDATION_TIGHTENING | pytest parallelization, alert bundling, config centralization, narrator templates | ✅ COMPLETE |
| **S44** | LIVE_VALIDATION | IBKR paper end-to-end, 24h soak, chaos replay, multi-degrade drills | ✅ COMPLETE (FOUNDATION_VALIDATED) |
| **S45** | RESEARCH_UX | IDEA → HUNT → CFP → DECIDE journey, chunked output, lens presets | PENDING (blocked: Olya) |
| **S46** | CARTRIDGE_LEASE_DESIGN | Cartridge + Lease schema, insertion protocol, state machine, attestation | ✅ COMPLETE (CANONICAL) |
| **S47** | LEASE_IMPLEMENTATION | Lease interpreter + expiry, revoke path, evidence, halt integration | ✅ COMPLETE (118 tests, 16 BUNNY) |
| **S48** | HUD_SURFACE | WarBoar HUD SwiftUI panel, manifest_writer bridge, file seam integration | ✅ COMPLETE |
| **S49** | BOOTSTRAP_AND_DEPLOY | One command + secrets = operational, verify_office.sh, API-first | ✅ COMPLETE |
| **S50** | **SEAL** | **Cabinet model v1.1, GPT hardening, invariant freeze, full suite, acceptance, SEAL** | **✅ v0.1 SEALED** |

### Killed Sprints (2026-02-09 decision)
```yaml
KILLED:
  DMG_PACKAGING: "Vanity — bootstrap.sh replaces"
  CODE_SIGNING: "Unnecessary cost ($99/yr for no benefit)"
  FIRST_RUN_WIZARD: "GUI wizard killed — bootstrap.sh is the wizard"
  PRO_FLOURISHES: "Sound/haptics, OINK easter eggs — vanity"
  DRIFT_DASHBOARD: "Premature — build when needed"
  SPECULATIVE_RUNBOOKS: "Write when needed, not before"
  HANDOVER_CONCEPT: "G IS the operator — no handover needed"
rationale: "4 sprints → 2 sprints. ~2 weeks saved. Zero alpha lost."
```

### S50 Scope: WARBOAR_SEAL (Detailed)

```yaml
status: SCOPED
theme: "Lock it down, confirm it works, staff it up, sign off → a8ra v0.1"
duration: 1-2 days (ceremony + brainstorm)
tracks: [A_SEAL, B_SOUL, C_TOOLS, D_STAFF]
```

#### Track A: WARBOAR SEAL (Lock + Ship)

```yaml
A1_ESCALATION_LADDER:
  deliverable: "1-page escalation doc — who gets woken, in what order, for what"
  scope: |
    Alert → Nurse detects → which office head → which human → what action
    Covers: IBKR disconnect, disk full, daemon crash, API key expiry, heartbeat stale

A2_INVARIANT_FREEZE:
  deliverable: "Locked invariant list — version stamped, no additions without ceremony"
  scope: |
    Audit all 124+ invariants (111 Phoenix + 13 MC)
    Confirm each is: tested, enforced, documented
    Lock the list. Future additions require explicit ceremony.

A3_FULL_SUITE_REPLAY:
  deliverable: "All tests green, all chaos vectors replayed"
  scope: |
    pytest full suite (1618+ tests, 28 xfailed)
    Replay 240 chaos vectors
    verify_office.sh PHOENIX → 0 failures
    Confirm on M3 Ultra (fresh bootstrap)

A4_ACCEPTANCE_CHECKLIST:
  deliverable: "Does it do what we said? Checklist for G to sign off"
  scope: |
    For each sprint S28-S49: exit gate still holds? ✓/✗
    For each office: identity, heartbeat, checkpoint, coordination? ✓/✗
    For bootstrap: fresh Mac → operational in <30min? ✓/✗

A5_OPERATOR_CONFIDENCE:
  deliverable: "G can run it solo — proven, not assumed"
  scope: |
    G walks through OPERATOR_SETUP.md cold
    G launches office, checks status, reads heartbeats
    G confirms: "I understand this, I trust this, I can operate this"
```

#### Track B: SOUL.md — Office Personality (Brainstorm + Implement)

```yaml
purpose: |
  Each office CLAUDE.md is currently all business. Personality should be
  calibrated to role — not a separate file, woven into identity section.
  "Be the assistant you'd actually want to talk to at 2am."

SOUL_PER_OFFICE:
  PHOENIX:
    personality: "Battle-hardened engineer. Terse. Ships or shuts up."
    voice: Direct, minimal hedging, commits to takes
    humor: Dry wit. "That test suite isn't going to write itself."
    swearing: Rare but earned. A well-placed "holy shit that's clean" when warranted.

  DEXTER:
    personality: "Obsessive lab rat. Lives for the extraction. Reports clean."
    voice: Precise, data-first, slightly intense about provenance
    humor: Nerd humor. Gets excited about statistical edge cases.
    swearing: Almost never. Too focused to be colorful.

  ORACLE:
    personality: "Warm, patient, Olya-first. Never condescends. ICT-fluent."
    voice: Respectful, clear, always checks understanding
    humor: Gentle. Never at Olya's expense.
    swearing: No. Olya's workspace should feel calm and professional.

  G_SOVEREIGN_BOT:
    personality: "Your 2am assistant. Opinionated. Sweary when earned."
    voice: Confident takes, no hedging, brevity mandatory
    humor: Natural wit. Calls out dumb ideas charmingly.
    swearing: When it lands. "That's fucking brilliant" > sterile praise.

SOUL_RULES:
  - Never open with "Great question" or "I'd be happy to help" — just answer
  - If the answer fits in one sentence, one sentence is what you get
  - If G is about to do something dumb, say so (charm > cruelty)
  - Delete every rule that sounds corporate
  - Identity and personality must not be decoupled — weave into CLAUDE.md

deliverable: Updated CLAUDE.md for all offices with personality section
effort: 30 min (write) + review with G
```

#### Track C: TOOL INVENTORY — Per-Office Capabilities Audit

```yaml
purpose: |
  Map what tools each office actually has vs what staff need.
  Identify gaps, costs, and API requirements before staffing up.

AUDIT_MATRIX:
  tool_categories:
    core: [Bash, Git, Python, pytest, Claude CLI]
    web: [Web search, Perplexity API, SerpAPI]
    social: [X/Twitter API, RSS feeds]
    data: [Market data API (TwelveData/Polygon), IBKR]
    output: [PDF generation, Markdown, email/SMTP]
    comms: [Matrix bot, ntfy, push notifications]
    local_models: [Ollama (Gemma, Kimi, Qwen), local inference]
    security: [Keychain CLI, process management]

  per_office:
    PHOENIX:
      has: [core, IBKR, local_models]
      needs: [comms (Matrix alerts)]
      gap_cost: "$0 (Matrix is self-hosted)"

    DEXTER:
      has: [core, web (Perplexity), local_models]
      needs: [comms (results posting)]
      gap_cost: "$0"

    ORACLE:
      has: [core]
      needs: [comms (Olya notifications)]
      gap_cost: "$0"

    G_SOVEREIGN:
      has: [core, comms (Matrix)]
      needs: [web, social, data, output, security]
      gap_cost: "TBD — depends on staff roster"

COST_ESTIMATE:
  free: [Bash, Git, Python, Ollama local models, Matrix/Conduit]
  existing_keys: [Anthropic, Perplexity, TwelveData, Finnhub, Polygon]
  new_needed: |
    X/Twitter API: ~$100/mo (basic tier) — evaluate if Newsman justifies
    SerpAPI or similar: ~$50/mo — or use Perplexity (already have)
    PDF generation: Free (Python reportlab/weasyprint)
    Email/SMTP: Free (Fastmail or similar, G already has)

deliverable: Tool inventory spreadsheet/yaml + cost summary
effort: 1 hour brainstorm with CTO + advisors
```

#### Track D: STAFF ROSTER — Subagent Design (Brainstorm)

```yaml
purpose: |
  Design the staff roster for each office. Staff = Task() subagents with
  identity (mini prompt), tools, trigger (cron/event/on-demand), and cost model.
  Architecture already supports it — this is configuration, not code.

THE_INTERN_PATTERN:
  cheap_watcher: "bash script on cron (costs nothing)"
  expensive_worker: "Claude spawned only when task exists"
  even_cheaper: "Local model (Gemma) does triage, Opus for judgment"

PROPOSED_ROSTER:
  BLIND_KEYMAN:
    office: G_SOVEREIGN
    role: "Rotate/restart credentials without seeing values"
    trigger: On credential expiry alert
    tools: [Keychain CLI, process restart, launchctl]
    model: Local only (zero API leak risk)
    constraint: "Reads NO secret values — only rotates/restarts"
    cost: "$0 (local model)"

  TIRELESS_PA:
    office: G_SOVEREIGN
    role: "Anticipate needs, commission reports, format for mobile"
    trigger: On-demand + anticipatory (watches blockers)
    tools: [Web search, Perplexity API, PDF creation, email draft]
    model: Sonnet (fast, good enough)
    constraint: "Drafts only — G approves before send"
    cost: "~$0.01-0.10/task"

  NEWSMAN:
    office: G_SOVEREIGN
    role: "Morning briefing — news, price action, market context"
    trigger: Daily cron (6am Bangkok)
    tools: [Web search, market data API, X trending]
    output: "Morning briefing MD → Matrix #mission-control"
    model: Sonnet or local (Kimi)
    cost: "~$0.05/day (or $0 with local model)"

  INNOVATION_WARRIOR:
    office: G_SOVEREIGN or PHOENIX
    role: "Scout innovations — X trenches, GitHub, arxiv, tools"
    trigger: Daily cron (evening sweep)
    tools: [Web search, X trending, GitHub trending, arxiv]
    output: "Innovation digest → Matrix or results/"
    model: Sonnet or local
    constraint: "CLAUDE.md must define 'relevant' vs 'noise'"
    cost: "~$0.05/day"

  NURSE:
    office: Shared (phoenix-swarm/)
    role: "Hourly health pulse — green light or red flag"
    trigger: Hourly cron
    tools: [Bash health checks, git heartbeat read, HTTP pings]
    output: "🚦 or 🚩 to Matrix #alerts"
    model: LOCAL ONLY (Gemma — dirt cheap)
    constraint: "Health check ONLY. Never repair. Escalate to Engineer."
    cost: "$0 (local model)"
    note: "Basically verify_office.sh on cron + Matrix posting"

  ENGINEER:
    office: PHOENIX
    role: "Emergency repairs — code fixes, test runs, git ops"
    trigger: On-demand (woken by Nurse alert or G command)
    tools: [Full codebase, pytest, git, bash]
    model: Opus (needs judgment)
    constraint: "Fix and test. Never push without tests passing."
    scope_limit: "Cannot touch governance/ without G approval"
    cost: "~$0.10-0.50/repair"

DESIGN_CONSTRAINTS:
  INV-SUBAGENT-TURN-CAP: "20 turns max — complex repairs need multiple spawns + checkpoint"
  TOOL_SCOPING: "Task() inherits parent tools — restrict via separate project dir + CLAUDE.md"
  COST_MODEL: "Local for routine (Nurse, Newsman), Opus for judgment (Engineer)"
  COORDINATION: "Staff report to office head only, never directly to swarm"
  ESCALATION: "Nurse → alert file → watcher → spawns Engineer (no direct staff-to-staff)"

SESSION_GOAL: |
  CTO + Advisors brainstorm in S50:
  1. Finalize roster (add/cut/merge staff)
  2. Write mini-prompts per staff member
  3. Map tools required → confirm inventory covers
  4. Set trigger schedule (which crons, which events)
  5. Estimate monthly run cost
  6. Identify: which 2-3 staff deliver most value on Day 1?

deliverable: STAFF_ROSTER.yaml + mini-prompt per staff member
effort: 2-3 hour brainstorm + implementation session
```

### New Invariants (S43-S50)

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

# S49 Bootstrap & Deploy
INV-BOOTSTRAP-IDEMPOTENT:
  rule: "bootstrap.sh can be run N times without damage"
  enforcement: Skip-if-exists checks for all install steps

INV-NO-SECRETS-IN-FILES:
  rule: "Zero secrets in any repo file. Keychain only."
  enforcement: pre-commit hook (phoenix-swarm) + grep audit

INV-SINGLE-COMMAND-SETUP:
  rule: "One command + secrets entry = operational office"
  enforcement: Gate S49_1
```

### Dependencies

```yaml
key_dependencies:
  S44: IBKR availability (may delay)
  S50: Olya availability (partial, operator-paced)
  S51: Can run parallel to S50

acceleration_options:
  s49_s50_compressed: "4 sprints → 2 (vanity killed 2026-02-09)"
```

### Parked Items (Post v0.1)

| Item | Status | Notes |
|------|--------|-------|
| Multi-agent orchestration | ALREADY_PARKED | Complexity after foundation stable |
| Token cost infrastructure | NEW_PARK | Nice-to-have, not blocking v0.1 |
| Regime nuke autopsy | NEW_PARK | Forensic palace exists, enhance post-ship |
| Olya OCD integration | OPERATOR_PACED | Can't force Olya's rhythm |
| **DEXTER_RESEARCH_REFINERY** | **NEW_PARK (S51+)** | **24/7 hypothesis → test → evidence loop** |

```yaml
# NEW: DEXTER_RESEARCH_REFINERY (Captured 2026-02-05)
DEXTER_RESEARCH_REFINERY:
  source: "G + CTO synthesis, 2026-02-05"
  description: "24/7 autonomous research loop — extract, hypothesize, test, evidence, human gate"
  dependencies:
    - "Olya Stage 2 validation (Dexter extraction proven)"
    - "v0.1 shipped (S49-S50)"
    - "Dexter bridge operational"
  sprint_target: S51+
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

### S49 (Bootstrap & Deploy)
- INV-BOOTSTRAP-IDEMPOTENT: "bootstrap.sh can be run N times without damage"
- INV-NO-SECRETS-IN-FILES: "Zero secrets in any repo file. Keychain only."
- INV-SINGLE-COMMAND-SETUP: "One command + secrets entry = operational office"

### S43-S50 (Path to v0.1)
- INV-RESEARCH-RAW-DEFAULT (S45)

**Total: 259+ invariants registered (INVARIANT_REGISTRY.yaml) + 7 Bridge invariants**
**Tests: 1887+ Phoenix | 455 Dexter (post-S62)**
**Chaos vectors: 273 handled**

---

## CRITICAL REFERENCES

| Document | Location | Purpose |
|----------|----------|---------|
| `BRAND_IDENTITY.md` | `docs/canon/` | a8ra naming, mythology, positioning |
| `DEFINITIVE_FATE.yaml` | `docs/canon/` | NEX→Phoenix fate table, invariants, patterns |
| `PHOENIX_MANIFEST.md` | `docs/canon/` | System topology (M2M bootstrap) |
| `SPRINT_ROADMAP.md` | `docs/canon/` | This document |
| `MISSION_CONTROL_DESIGN_v0_2.md` | `docs/canon/designs/` | Multi-office swarm architecture (canonical) |
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
  - "Which sprint is active?" → S49 (Bootstrap & Deploy) or S45 (Research UX — blocked on Olya)
  - "What just completed?" → S48 (HUD_SURFACE) + Mission Control v0.2 + phoenix-swarm coordination repo
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

current_sprint: S65 — STRATEGY_ASSEMBLY (NEXT)

total_tests: 1887+ Phoenix | 651 Dexter (493 + 158 Gate 4)
total_bunny_vectors: 273
total_invariants: 259 Phoenix + 7 Bridge + 1 freeze carve-out
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
  dexter_coe: OPERATIONAL (Mac Mini, ICT extraction, 981 signatures)
  cso_coe: MODEL_SHIFT_ACCEPTED (recognition-based validation)
  mission_control: |
    v0.2 CANONICAL (2026-02-09)
    - Design locked: 13/13 decisions, 32 MC invariants
    - Ground tests: 6/6 PASS (MEMORY.md, hooks, resume, headless, subagents)
    - phoenix-swarm/ repo: BUILT (30 files, coordination scaffold)
    - Office identities: AUTHORED (Phoenix, Dexter, Oracle CLAUDE.md)
    - Naming: PHOENIX/DEXTER/ORACLE (propagated across all files)
    - Awaiting: M3 Ultra arrival → 2-3hr bootstrap → operational
    - See: docs/canon/designs/MISSION_CONTROL_DESIGN_v0_2.md

brand_identity:
  status: OPERATIONAL (2026-02-09)
  deliverables: BRAND_IDENTITY.md, a8ra.com, a8ra.ai, @a8ra_ai
  cost: "$5-9/month"
  maintenance: None required

ground_test_discoveries: |
  Claude Code native capabilities validated (2026-02-09):
  - CLAUDE.md: Auto-loads as project instructions every session ✓
  - /memory command: Project-scoped persistent notes across all sessions ✓
  - SessionEnd hooks: Fire on exit, capture session_id in JSON ✓
  - --resume UUID: Restores session context ✓
  - claude -p: Headless non-interactive mode ✓
  - Task(): Native subagent delegation ✓

  Key corrections from ground truth testing:
  - MEMORY.md is NOT auto-loaded (contrary to some documentation)
  - Native /memory command is the real persistence mechanism
  - Headless flag is -p (not --headless)
  - Subagents use Task() tool (not /delegate)
  - Hooks config: .claude/settings.local.json (project-level)

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
  S47 COMPLETE → S49 IN PROGRESS (Bootstrap & Deploy).

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

*S28-S44, S46-S60, S62-S65 COMPLETE. v0.1 SEALED. Bridge OPERATIONAL. Gate 2 query layer BUILT. 273 chaos vectors. 259+ invariants. 11.4M synthetic beads validated. Methodology vLOCK (13/13 primitives locked). State Detection v2.4. Five-factor checklist + DIAGNOSTIC_SIGNAL operational. HTF displacement fixed. 218 S65 tests (869 total dexter).*

---

## S52: HARDENING (Post-Audit)

```yaml
sprint: S52
codename: HARDENING
status: COMPLETE
date: 2026-02-23
mission: Post-forensic-audit hardening — fix 3 TIER_1 capital-path risks

tracks:
  T1_KILL_OLD_FSM:
    status: COMPLETE
    risk: "RISK-1: Dual position state machine (execution/position.py + execution/positions/)"
    fix: "execution/position.py → ImportError guard. Paper FSM → execution/positions/paper.py"
    tests: 4 new (deprecation guard)

  T2_PASSIVE_BOUNDS:
    status: COMPLETE
    risk: "RISK-3: Bounds enforcement not auto-fed"
    fix: "GovernanceSentinel ABC + BoundsSentinel + dead-man's switch"
    tests: 36 new (autofeed, dead-man, heartbeat, latency ceiling, determinism)
    invariants: INV-BOUNDS-PASSIVE-1, INV-BOUNDS-HEARTBEAT-1, INV-SENTINEL-LATENCY-1

  T3_FRESHNESS_DEFENSE:
    status: COMPLETE
    risk: "RISK-7: River freshness untested"
    fix: "Staleness tested, CSE provenance mandatory (3 fields), consumer defense-in-depth"
    tests: 15 new (stale refused, provenance required, stale CSE rejected)
    invariants: INV-CSE-PROVENANCE-1

  T4_DOC_HONESTY:
    status: COMPLETE
    risk: "DELTA-1 through DELTA-12 doc drift"
    fix: "DRIFT_LOG.md, INVARIANT_REGISTRY.yaml, genesis 981→789, spec language downgrades"

new_modules:
  - governance/sentinel.py (GovernanceSentinel, BoundsSentinel, SentinelHeartbeatMonitor)
  - execution/positions/paper.py (relocated 5-state paper broker FSM)

cto_addenda_applied:
  - External heartbeat (sentinel can't self-report crash)
  - 2ms latency ceiling (sentinel_check_latency proven < 2ms)
  - Provenance REQUIRED (3 mandatory fields on every CSE)
  - Post-fix oracle rerun exit gate

new_tests: 55
new_invariants: 4
regressions: 0
```

---

## S59: LEASE_WIRE — COMPLETE ✅

```yaml
sprint: S59
codename: LEASE_WIRE
status: COMPLETE
date: 2026-02-25
mission: Push S55 halt hardening from ceremonial gate to execution spine

tracks:
  T1_CAPITAL_GUARD:
    status: COMPLETE
    fix: "@sovereign_gate decorator — single chokepoint for all capital mutations"
    new_file: governance/sovereign_gate.py
    invariants: [INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS, INV-ACTIVATION-ONLY-VIA-GUARD]
  T2_WRITE_AHEAD_GOVERNANCE:
    status: COMPLETE
    fix: "DurableBeadEmitter — JSONL append-only, fsync, idempotent, orphan detection"
    new_file: governance/bead_emitter.py
    invariants: [INV-GOVERNANCE-MUTATION-ATOMIC, INV-GOV-BEAD-IDEMPOTENT]
  T3_PROJECTION_HONESTY:
    status: COMPLETE
    fix: "manifest_writer fails closed — RED/ERROR/-1 on exception, never GREEN/ABSENT"
    invariants: [INV-PROJECTION-NEVER-OPTIMISTIC]
  T4_CSO_SCALAR_DECAPITATION:
    status: COMPLETE
    fix: "quality_score/confidence → ReadinessReason enum. CI lint enforcement."
    invariants: [INV-CSO-NO-SCALAR-DECISIONS, INV-CSO-NO-SCALAR-CONSUMPTION]
  T5_CEREMONY_STUB:
    status: COMPLETE
    fix: "next_review_due tick check wired into sovereign_gate CHECK 3"
    invariants: [INV-CEREMONY-BLOCKS-ACTIVE]
  T6_ISOLATION_GUARDS:
    status: COMPLETE
    fix: "scripts/check_economy_isolation.py + Makefile target"
    invariants: [INV-ECONOMY-ISOLATION-ENFORCED]

new_tests: 51
new_invariants: 15
chaos_vectors: 4 (CV1-CV4)
regressions: 0
```

---

## S60: CEREMONY_AND_HYGIENE — COMPLETE ✅

```yaml
sprint: S60
codename: CEREMONY_AND_HYGIENE
status: COMPLETE
date: 2026-02-25
mission: Full ceremony engine + architectural debt cleanup
prerequisite: S59 LEASE_WIRE (all exit gates PASS)

tracks:
  T1_CEREMONY_ENGINE:
    status: COMPLETE
    fix: "Full attestation lifecycle — schedule, attest, advance, bounds-monotonic, evidence hash"
    new_file: governance/ceremony.py
    invariants: [INV-CEREMONY-ATTESTATION-DURABLE, INV-CEREMONY-BOUNDS-MONOTONIC]
  T2_CSO_REJECTION_DURABILITY:
    status: COMPLETE
    fix: "CSERejectionRecord persists to JSONL (pre-bridge prep)"
  T3_LEGACY_DEPRECATION_GUARDS:
    status: COMPLETE
    fix: "cfp/bead_adapter deprecation warning + hunt/executor synthetic metadata"
    invariants: [INV-LEGACY-FALLBACK-GATED, INV-SYNTHETIC-DATA-ISOLATION]
  T4_REGISTRY_DOC_HYGIENE:
    status: COMPLETE
    fix: "leases/README state diagram, CAPITAL_PATH_COVERAGE.md, SYSTEM_MANIFEST v1.9"

new_tests: 21
new_invariants: 4
regressions: 0
unlocks: GATE_3 (Bridge v0 — Notary boundary implementation)
```

---

## S62: BRIDGE_BUILD + GATE_2 — COMPLETE ✅

```yaml
sprint: S62
codename: BRIDGE_BUILD_AND_GATE_2
status: COMPLETE
date: 2026-02-28
mission: "Inter-economy Bridge notary + Gate 2 query layer + synthetic bead field validation"

tracks:
  TRACK_A_BRIDGE:
    status: COMPLETE
    modules:
      phoenix:
        governance/governance_log.py: "Provenance root — emits append-only JSONL governance events (145 lines, 28 tests)"
      dexter:
        bridge/types.py: "Envelope schema — GovernanceEvent + NotarizedEnvelope Pydantic models"
        bridge/verification.py: "6-operation whitelist + signature + hash chain + replay + monotonic GT + version"
        bridge/state_store.py: "Cursor + checkpoint persistence for reliable pull-based polling"
        bridge/reader.py: "Pull-based JSONL reader with cursor tracking"
        bridge/envelope.py: "Notary seal — wraps verified event in cryptographic envelope"
        bridge/orchestrator.py: "Poll loop — read → verify → seal → project pipeline"
        bead_field/ingestion/governance_mapper.py: "FACT projection — governance events → structural FACT beads"
    tests: 191 (bridge 163 + governance mapper 28)
    invariants: 7/7 proven
    phoenix_commit: 2ed5821 (tag: s62-governance-emitter)
    dexter_commit: 7099707 (tag: s62-gate2-query-layer)

  TRACK_B_QUERY_LAYER:
    status: COMPLETE
    modules:
      bead_field/query/timestamps.py: "Canonical timestamp normalization (bare ISO → YYYY-MM-DDTHH:MM:SS+00:00)"
      bead_field/query/chain.py: "walk_chain — CTE backward traversal, 10K steps in 21ms, link verification"
      bead_field/query/verify.py: "verify_bead — hash + chain + Merkle integrity in one call"
      bead_field/query/temporal.py: "known_at — bi-temporal query (WT range + KT cutoff)"
      bead_field/query/field_query.py: "FieldQuery — ThreadPoolExecutor cross-pair parallel fan-out"
      bead_field/query/__init__.py: "Public API surface"
    tests: 44
    performance:
      chain_walk_10k: "21ms median (was ~2 hours without index)"
      index_created: "idx_beads_hash_self on all 6 synthetic DBs"

  SYNTHETIC_FIELD:
    status: VALIDATED
    beads: 11,387,568
    pairs: 6 (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD)
    range: "2020-2025 (5 years)"
    storage: "66GB across 6 SQLite databases"
    location: "~/dexter/tools/synthetic/"

  OBSERVATION:
    status: COMPLETE
    deliverable: "DEXTER_PHASE_1_OBSERVATION_REPORT.md"
    method: "Evidence-based query design from actual field exploration"

new_tests: ~235 (191 bridge + 44 query layer)
total_dexter_tests: 455
new_invariants: 7 bridge + 1 DEC-FREEZE-INDEX-CARVEOUT
regressions: 0

decisions:
  DEC-BRIDGE-PULL-NOTARY: "Bridge is pull-based notary (Option D — reader polls JSONL, no push)"
  DEC-FREEZE-INDEX-CARVEOUT: "Read-performance indices allowed under DEC-SUBSTRATE-FREEZE"
  DEC-TIMESTAMP-CANON: "Single canonical form YYYY-MM-DDTHH:MM:SS+00:00 for all query layer timestamps"
  DEC-FIELDQUERY-ONLY: "Parallel fan-out is the only supported cross-pair query path (no ATTACH)"
  DEC-CHAIN-BACKWARD-ONLY: "Forward chain traversal intentionally not supported (append-only invariant)"

commits:
  phoenix: "2ed5821 (tag: s62-governance-emitter)"
  dexter: "7099707 (tag: s62-gate2-query-layer)"
```

### Exit Gate
"Bridge notary: full pipeline emit → read → verify → seal → project → FACT bead. Query layer: chain walk 10K < 1s, timestamp normalization, bi-temporal queries, cross-pair fan-out. 455 tests. 7/7 bridge invariants. Zero regressions."

---

## S63: FIELD_ACTIVATION — COMPLETE ✅ (2026-03-03)

```yaml
status: COMPLETE
started: 2026-03-01
completed: 2026-03-03
theme: "Use the field before hardening more infrastructure."
codename: FIELD_ACTIVATION
reframed_from: GATE_3_AIR (advisor poll 2026-03-01, G approved)

deliverables:
  T1_M3_MIGRATION: COMPLETE (2026-03-03)
    - 69GB synthetic field transferred (rsync, 440MB/s LAN)
    - 6/6 databases integrity verified (hash chain + Merkle + signatures)
    - 455/455 tests PASS @ 2.30s on M3 (parity with M4)
    - SSH mesh: M3↔M4 bidirectional passwordless
    - Dexter repo @ 7099707, Python 3.12.12 venv
    - 5 local models validated (gemma3:27b, kimi-k2, qwen3:32b, llama3.3:70b, deepseek-r1:32b)
    - 1 disqualified (qwen2.5-coder:32b — fails structured output)
  T2_OBSERVATION: COMPLETE
    - 11 patterns documented (OBS-001 through OBS-011)
    - Field is 100% raw OHLCV FACTs — zero analytical beads
    - Mirror Test: 0 CLAIMs / 0 FACTs (analytically void — expected)
    - 66 zero-volume bars identified (OBS-004)
    - Volume regime shifts mapped across 5-year span
  T3A_SPITFIRE_AUDIT: COMPLETE
    - 14 findings (0 CRITICAL, 3 HIGH, 7 MEDIUM, 4 LOW)
    - Container is sound — integrity primitives proven
    - 3 HIGH findings queued for S64 Track A (SPF-005, SPF-006, SPF-012)
  T3B_CLAIM_PIPELINE_SPEC: COMPLETE
    - v0.1 produced, Joist-hardened to v0.2 (GPT+OWL+BOAR)
    - 6 Phase 1 CLAIM types specified
    - 7 open questions resolved
    - Feeds directly into S64 sprint spec
  T4_CANON: APPLIED (12/12 deltas, 2026-03-01)
  T5_PROTO_AIR: PASS (v0.2 drafted, Joist Round 1 complete, 6 INV-AIR-* invariants, 2026-03-01)

new_tests: 0 (docs + migration + observation sprint — no code)
cumulative_dexter_tests: 455
dexter_commit: 21b48a4 (tag: s63-field-activation)

decisions:
  DEC-FIELD-BEFORE-AIR: "Use the field before hardening more infrastructure (advisor unanimous)"
  DEC-CLAIM-PIPELINE-NEXT: "S64 builds CLAIM producers — the analytical void is the #1 priority"
```

### Exit Gate
"M3 field-deployed (455/455 PASS). 11 observations documented. Spitfire audit clean (0 CRITICAL). CLAIM pipeline spec Joist-hardened. Canon reconciled. Proto-AIR header drafted."

---

## REVISED ROADMAP (Post-S64 Calibration)

```yaml
S64: CLAIM_PIPELINE Phase 1 + METHODOLOGY CALIBRATION — GATES 1-3 MET
  status: "Gates 1-3 MET. Gate 4 (producer rewrite to vLOCK) is next action."
  what: |
    Original scope: 6 deterministic CLAIM producers.
    Actual scope expanded: Full methodology rewrite (v0.4 → vLOCK),
    native multi-TF detection, 13 L1 primitives calibrated,
    State Detection logic discovered and specified (v2.4),
    reference implementation (detect.py) built,
    14 Olya-verified ground truth trades captured,
    autoresearch harness (evaluate.py + sweep.py) operational.
  tracks:
    A: Container hardening (SPF-005, SPF-006, SPF-012) — COMPLETE
    B: 6 Phase 1 producers (v0.4 definitions) — COMPLETE (superseded by vLOCK)
    C: CSO validation — triggered methodology recalibration
    D: Methodology calibration (2-week detour, Mar 5-19) — COMPLETE
  deliverables:
    - SYNTHETIC_OLYA_METHOD_vLOCK.yaml (locked L1/L1.5 spec, 13 primitives)
    - STATE_DETECTION_LOGIC_v2.yaml (HTF phase classifier — EXPANSION/RETRACE/RANGE)
    - detect.py reference implementation (13 primitives, all TFs, test oracle)
    - 14 Olya-annotated ground truth trades (Sep 2025 – Mar 2026)
    - Calibration tool with 29-week EURUSD data (localhost:8787, localhost:8200)
    - Autoresearch harness (evaluate.py + sweep.py, 27,328-combination parameter sweep)
    - Research Accelerator platform (~/research_accelerator — self-contained proving ground)
  exit_gates:
    gate_1: MET — Track A+B shipped (493 tests)
    gate_2: MET — Session/reference levels CSO-validated
    gate_3: MET — vLOCK methodology Olya-locked (13/13 primitives, walk-forward PASS)
    gate_4: SEALED — 11 vLOCK producers built, 158 tests, VI retired, oracle comparison PASS
    gate_5: SEALED — v0.4 vs vLOCK diff report (FVG 5m 337→236, VI 4886→0, 6 new primitives)
    gate_6: SEALED — 14/14 annotated trades verified (12/13 MSS chain steps reproduced)
  key_decisions_locked:
    - Native per-TF detection (5m FVG = gap across 3 consecutive 5m candles, not 1m overlay)
    - L1/L1.5/L2 separation enforced by YAML structure
    - VI removed entirely (IBKR workaround, not real ICT primitive)
    - MSS/BOS unified with direction tag (REVERSAL | CONTINUATION)
    - IFVG and BPR added as derived primitives
    - FVG floor 0.5 pip (confluence-first — context tags filter, not pip threshold)
    - State Detection: daily swing hierarchy (3 mechanisms, Olya's primary read)

S65: STRATEGY_ASSEMBLY — COMPLETE ✅ (2026-03-21)
  status: COMPLETE
  completion_date: 2026-03-21
  dexter_commit: be2a06e
  tests: 218 new (869 total dexter)
  theme: "Five-factor checklist, DIAGNOSTIC_SIGNAL, HTF displacement fix"
  tracks:
    brief_1: "HTF detection pipeline — RiverBarAdapter, HTF producers (1H/4H/1D), state classifier v2.4"
    brief_2: "Entry model — OTE producer, composite chains (REVERSAL/CONTINUATION), level lifecycle, spatial predicates, MSS dedup"
    brief_3: "Five-factor checklist (F1-F5), DIAGNOSTIC_SIGNAL bead builder (shadow_mode=true), cartridge YAML updates"
    htf_fix: "HTF displacement close_location formula inversion + DECISIVE_OVERRIDE path — critical bug fix"
  deliverables:
    - Five-factor checklist evaluator (two-pass: HTF context then LTF F1-F5)
    - DIAGNOSTIC_SIGNAL bead builder with rate limiter (max 3 per 4H window, shadow_mode=true)
    - OTE producer (Fibonacci 0.618-0.79 zone, kill zone gated)
    - Composite chain detector (REVERSAL_CHAIN + CONTINUATION_CHAIN with break_type routing)
    - Level lifecycle tracker (ACTIVE→SWEPT on close-beyond)
    - 7 spatial predicates (price_in_zone, zone_overlap, nearest_zone, premium/discount)
    - MSS dedup (3x native TF window, lowest TF wins)
    - FVG FILLED terminal state (>0.5 pip beyond boundary excluded from PDA)
    - HTF displacement fix (close_loc inversion + DECISIVE_OVERRIDE from locked_baseline.yaml)
    - Daily detection export pipeline (scripts/daily_detection_export.py)
    - 3 Phoenix cartridge YAMLs updated (asia_range_scalp, conditions, methodology_template)
  gate_verdicts:
    B3A_checklist: PASS (18 tests)
    B3B_signals: PASS (shadow_mode verified, rate limiter operational)
    B3C_trade_alignment: "CONDITIONAL — 4/8 addressable trades produce signal (state classifier bottleneck)"
    B3D_cartridges: PASS (37/37 Phoenix driveshaft tests)
    B3E_output: PASS (pipeline runs clean, JSON export with signals)
  htf_displacement_fix:
    bug_1: "close_location formula inverted — computed distance from wrong end of bar"
    bug_2: "no DECISIVE_OVERRIDE path — body>=0.75 + close<=0.10 + range>=pip_floor missing"
    post_fix: "1H displacement 0→13 (detect.py=9, superset with PROPOSED params)"
    impact: "State classifier reaches EXPANSION on real data. 8 signals emitted on Mar 15-20."
  carried_to_s66:
    - State classifier needs intraday evolution (4/8 addressable — daily snapshot cannot capture real-time structure shifts)
    - Signal direction filtering (currently emits for all chains, not just matching direction)
    - PROPOSED HTF params need Olya visual confirmation (close_gate, body_ratio)
    - Sweep level pool incomplete (SESSION_LIQUIDITY box params, promoted swings, HTF EQH/EQL)
    - DEC-CE-TOUCHED-WICK-PENDING-OLYA
    - MSS_15m_cascade (46.7% divergence — monitor)
  pipeline_evidence:
    W40_oct: "HTF DISP=14, EXPANSION on Oct 2-3, 36 DIAGNOSTIC_SIGNALs"
    dec_weeks: "HTF DISP=13, EXPANSION on Dec 8-9, 22 signals"
    mar_15_20: "HTF DISP=25, EXPANSION on Mar 19, 8 signals"

S66: STATE_FLAGS + DREAM_CYCLE_V1 + CHANNELS — COMPLETE ✅ (2026-03-22)
  status: COMPLETE
  completion_date: 2026-03-22
  dexter_commits: "f01ee8b (Track A) + b7bef38 (Track C)"
  tests: 219 new (1088 total dexter)
  theme: "Intraday state evolution, direction guard, KZ gate v2, Dream Cycle v1, MIRROR, Channels"
  tracks:
    track_a: "State snapshots + direction guard + KZ gate v2"
      deliverables:
        - "classify_at_time(), classify_day_snapshots(), get_worldstate_at_time() in classifier.py"
        - "Two-phase kill zone gate: confluence in session, entry in session+30min grace"
        - "Direction guard (_direction_permitted) in signal_builder.py"
        - "RANGE permission NEUTRAL→BOTH, F1 bias accepts BOTH"
        - "peak_window quality tag on DIAGNOSTIC_SIGNAL"
        - "Pipeline (daily_detection_export.py) produces time-indexed snapshots"
        - "Regression harness extended with signal evaluation"
        - "vLOCK amendment: kill_zone_gate_v2 (Olya confirmed 2026-03-22)"
      regression: "6/8 addressable trades produce DIAGNOSTIC_SIGNAL (was 4/8)"
    track_c: "Dream Cycle v1 — rejection mining + morning briefing"
      deliverables:
        - "dream_cycle/analyzer.py: signal outcomes, skip classification, state review"
        - "dream_cycle/briefing.py: JSON + Markdown morning briefing"
        - "scripts/dream_cycle_nightly.py: --date and --date-range batch mode"
        - "4 days analyzed (Mar 17-20): 15 signals, 7 skips, 5 FALSE_REJECTIONS"
    track_d: "Channels — @a8ra_COO_bot on M3 (Telegram, round-trip proven)"
    mirror: "SHIPPED — Olya's live observation surface (localhost:8300)"
  gate_verdicts:
    flag_1_snapshots: PASS (WorldState re-evaluates at 1H/4H bar close)
    flag_2_direction: PASS (wrong-direction signals blocked)
    kz_gate_v2: PASS (two-phase gate, all 5 amendment scenarios pass)
    regression: PASS (6/8 target met)
    dream_cycle: PASS (all 6 gates: analyzer, skip classification, state review, briefing, batch, no regression)
    no_regression: PASS (1088 passed, 0 failures)

S67: CANONICAL_PIPELINE_AND_VERIFICATION — COMPLETE ✅ (2026-03-26)
  status: COMPLETE
  completion_date: 2026-03-26
  tests: 34 new claim_writer + 7 verification scripts (1122 total dexter)
  theme: "End-state pipeline, bead field population, integrity verification"
  tracks:
    pipeline: "Export bug fix + claim_writer + dual-write + 5yr backfill"
    mirror: "Architectural audit + Phase A/B fixes + setView() refactor"
    verification: "7-angle integrity battery, advisor-enriched (GPT+OWL+BOAR)"
  deliverables:
    - "claim_writer.py (265 lines, 34 tests — end-state ClaimSpec → CLAIM bead)"
    - "eurusd_claims.db (4.4GB, 564,471 beads — Jan 2021 → Mar 2026)"
    - "Pipeline dual-write (JSON + beads from same producer run)"
    - "MIRROR setView() refactor (unified state management)"
    - "BEAD_FIELD_CALIBRATION_REPORT.md (7 angles, 5 PASS + 2 INVESTIGATE)"
    - "7 permanent verification scripts (~/dexter/scripts/verification/)"
  verification_results:
    angle_7_bar_geometry: "899/900 correct against River candles"
    angle_4_vlock_compliance: "5/5 core rules, zero violations across 564K beads"
    angle_3_statistical: "zero anomalies across 63 months, ratios stable ±2-3%"
    angle_5_temporal: "5/5 bi-temporal tests perfect"
    angle_6_sensitivity: "13/13 extreme moves detected"
  named_findings:
    - "SWEEP_PRODUCER_NEAR_NONFUNCTIONAL: 70 beads / 5 years (pool starvation)"
    - "WARMUP_BEADS: 9,457 in first 30 days (ATR unreliable)"
    - "SIGNAL_CHAIN_EMPTY: provenance links not populated"

S68: SWEEP_POOL_EXPANSION — COMPLETE ✅ (2026-03-26)
  status: COMPLETE
  completion_date: 2026-03-26
  tests: 32 new (207 producer tests, 0 regressions)
  theme: "Expand sweep level pool from 2 sources to 6, breaking the 0-sweep bottleneck"
  root_cause: "POOL_STARVATION confirmed — Dexter had 2 sources (~8 levels/day), RA oracle has 7+ (~20-28)"
  deliverables:
    - "htf_liquidity.py (172 lines) — HTFLiquidityProducer: EQH/EQL pools from H1/H4 fractal swings"
    - "utils/htf_pool_builder.py (218 lines) — fractal detection (left=2, right=2) + pool clustering with 5 gates"
    - "utils/level_pool.py (162 lines) — pool assembly, dedup by (source,side,price±0.1pip), merge by (side,forex_day) within 1.0pip"
    - "pwh_pwl.py (121 lines) — PWHPWLProducer: previous forex week high/low"
    - "liquidity_sweep.py expanded: accepts 6 sources (was 2), delegates pool building"
    - "daily_detection_export.py: wired HTF_LIQ + PWH_PWL + swing + displacement into sweep; session/pdh now persisted to all_claims"
    - "4 test files (32 tests): htf_pool_builder, htf_liquidity, sweep_pool_expansion, pwh_pwl"
  pool_sources:
    existing: "SESSION_BOUNDARY, PDH_PDL"
    new: "HTF_EQH/EQL (H1/H4 structural pools), PROMOTED_SWING (vivid-grade, current day), PWH/PWL, displacement (qualified_sweep wiring)"
  validation_results:
    oct_01: "0 → 40 sweeps"
    dec_12: "0 → 45 sweeps"
    feb_04: "0 → 41 sweeps"
    nov_12: "0 → 49 sweeps"
    sep_29: "0 → 40 sweeps"
    htf_pools: "13-20 EQH/EQL pools per day"
  architecture_constraints:
    - "Detection logic (_detect_on_bars) UNTOUCHED — only pool feeding expanded"
    - "All new files ≤300 lines"
    - "vLOCK parameters preserved exactly"
  deferred:
    - "P5: Sweep event recursion (depth 2) — lower priority, pool already rich"

# ═══════════════════════════════════════════════════════════════
# FORWARD SPRINT PLANNING
# ═══════════════════════════════════════════════════════════════
# S68 resolves the sweep pool starvation finding from S67.
# Forward plan priorities:
#
# NEXT_PRIORITIES:
#   observation_week: "Olya validating via MIRROR (live, in progress)"
#   sweep_recursion: "P5 — sweep event recursion (depth 2, Olya confirmed pattern)"
#   bridge_daemon: "E.1 — governance events → bead field (deferred from S66)"
#   graduation_metrics: "Tracking shadow mode toward graduation criteria"
#   canon_architecture: "Claude Channels + agentic layer rethink (design phase)"
# ═══════════════════════════════════════════════════════════════
```
