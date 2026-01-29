# SPRINT_ROADMAP.md
# Phoenix Sprint Roadmap — M2M Advisor Reference

```yaml
document: SPRINT_ROADMAP.md
version: 1.0
date: 2026-01-29
status: CANONICAL
format: M2M_DENSE
audience: Advisors (GPT, GROK, OWL, Opus)
```

---

## CURRENT STATE

```yaml
current_sprint: S35_CFP
status: READY_TO_EXECUTE
s33_p2: BLOCKED (Olya CSO calibration)
cumulative:
  sprints_complete: 7 (S28 → S34)
  chaos_vectors: 84/84 PASS
  invariants_proven: 52+
  bead_types: 14
  runbooks: 8
```

---

## SPRINT ARCHAEOLOGY (S28-S34)

| Sprint | Codename | Key Deliverables | Exit Gate |
|--------|----------|------------------|-----------|
| S28 | STEEL_PIPES | Foundation, contracts | ✓ |
| S29 | BUILD_MAP | Schema arch, River | ✓ |
| S30 | LEARNING_LOOP | Hunt, Athena, BeadStore | ✓ 19/19 BUNNY |
| S31 | SIGNAL_AND_DECAY | CSO, Signalman, Autopsy | ✓ 20/20 BUNNY |
| S32 | EXECUTION_PATH | IBKR mock, T2, 9-state lifecycle | ✓ 17/17 BUNNY |
| S33.P1 | FIRST_BLOOD | Real IBKR, monitoring, 8 runbooks | ✓ 15/15 BUNNY |
| S34 | OPERATIONAL_FINISHING | File seam, CSO contract, orientation, widget | ✓ 13/13 BUNNY |

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
status: LOCKED
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
status: LOCKED
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
status: PLANNED
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
status: PLANNED
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
status: PLANNED
theme: "Decomposed outputs, no viability scores"
ref: DEFINITIVE_FATE.yaml → sprint_allocation.S39_RESEARCH_VALIDATION
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

## S40+: CARPARK (FUTURE FUEL)

```yaml
status: DORMANT
activation: Post-S39 foundation
source: GROK frontier synthesis
```

| Item | Description | Dependencies |
|------|-------------|--------------|
| Multi-agent orchestration | Orchestrator → sub-agents w/ dependency graphs | S35-S39 proven |
| Self-healing mechanisms | Backoff, circuit breakers, auto-escalation | S35-S39 proven |
| Workflow learning | Store successful patterns → propose refinements (human veto) | INV-NO-UNSOLICITED salvage |
| RBAC sub-agents | T2 gating extended to sub-agent spawning | Multi-agent operational |
| Token/cost infrastructure | Per-workflow budget, prompt optimization | INV-HUNT-BUDGET extended |

---

## INVARIANT REFERENCE (CUMULATIVE)

### Attribution (CFP)
- INV-ATTR-CAUSAL-BAN, INV-ATTR-PROVENANCE, INV-ATTR-NO-RANKING
- INV-ATTR-SILENCE, INV-ATTR-NO-WRITEBACK, INV-ATTR-CONFLICT-DISPLAY

### Safety
- INV-NO-UNSOLICITED, INV-LLM-REMOVAL-TEST, INV-SCALAR-BAN, INV-NO-ROLLUP
- INV-NO-DEFAULT-SALIENCE, INV-SLICE-MINIMUM-N, INV-BIAS-PREDICATE

### Governance
- INV-REGIME-EXPLICIT, INV-REGIME-GOVERNANCE, INV-HUNT-EXHAUSTIVE, INV-HUNT-BUDGET

### Harness
- INV-HARNESS-1 through INV-HARNESS-4

**Total: 17 new (DEFINITIVE_FATE) + 52 proven (S28-S34) = 69+ invariants**

---

## CRITICAL REFERENCES

| Document | Purpose |
|----------|---------|
| `DEFINITIVE_FATE.yaml` | NEX→Phoenix fate table, invariants, patterns |
| `PHOENIX_MANIFEST.md` | System topology (M2M bootstrap) |
| `conditions.yaml` | 5-drawer gate predicates |
| `schemas/beads.yaml` | Bead type definitions |

---

```yaml
# Advisor Bootstrap Checklist
orientation_sequence:
  1: cat DEFINITIVE_FATE.yaml | head -100  # Fate framework
  2: cat SPRINT_ROADMAP.md | grep -A20 "S35:"  # Current sprint
  3: cat conditions.yaml  # CSO gates
  4: cat state/orientation.yaml  # Current state (if exists)

first_questions:
  - "Which sprint is active?"
  - "What invariants must this sprint prove?"
  - "What NEX capabilities does this sprint address?"
```

---

*"Quality > Speed. Explicit > Implicit. Facts > Stories."*
*Phoenix builds with discipline. Phoenix builds with purpose.*
