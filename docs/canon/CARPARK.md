# CARPARK.md
# Phoenix Future Fuel — Items Not Yet Scheduled

```yaml
document: CARPARK.md
version: 5.0
date: 2026-01-31
status: CANONICAL
source: S43+ advisory convergence + DEFINITIVE_FATE.yaml
```

---

## COMPLETED (S41) ✓ — WARBOAR_AWAKENS

### SLM_DISTILLATION — DONE (PIVOTED TO RULE-BASED)
```yaml
description: |
  Originally: Distill Claude reasoning to local SLM using Unsloth.
  Actual: Rule-based ContentClassifier (100% accuracy, 0.34ms p95).
  Pivot reason: LoRA fine-tuning exhibited mode collapse.
path: governance/slm_boundary.py, slm/inference.py
status: S41_COMPLETE ✓
tests: 195
invariants: INV-SLM-READONLY-1, INV-SLM-NO-CREATE-1, INV-SLM-CLASSIFICATION-ONLY-1, INV-SLM-BANNED-WORDS-1
```

### NARRATOR_INTEGRATION — DONE
```yaml
description: |
  Wire ContentClassifier into narrator pipeline.
  Single chokepoint (narrator_emit), canonicalization, heresy blocking.
path: narrator/renderer.py, narrator/surface.py
status: S41_COMPLETE ✓
tests: 171
```

### SURFACE_POLISH — DONE
```yaml
description: |
  Human cadence in narrator output.
  Alert one-liners, degraded messages, receipts hidden.
path: narrator/surface.py, notification/alert_taxonomy.py
status: S41_COMPLETE ✓
tests: 24
```

### LIVE_VALIDATION — DONE
```yaml
description: |
  Paper → Live progression with explicit gates.
  Real IBKR Gateway connection validated.
path: drills/s41_phase3_live_validation.py
status: S41_COMPLETE ✓
certification: LIVE_GATEWAY_VALIDATED (PAPER MODE)
```

### DMG_PACKAGING — DONE
```yaml
description: |
  macOS app distribution via .dmg
  Self-contained Python runtime
status: S41_COMPLETE ✓
artifact: Phoenix-0.41.0.dmg
```

---

## COMPLETED (S40) ✓

### IBKR_FLAKEY — DONE
```yaml
path: brokers/ibkr/supervisor.py, heartbeat.py, degradation.py
pattern: Heartbeat + supervisor (@banteg zero deps)
status: S40_COMPLETE ✓
tests: 56
invariants: INV-IBKR-FLAKEY-1/2/3, INV-IBKR-DEGRADE-1/2, INV-SUPERVISOR-1
```

### CLAUDE_CODE_HOOKS — DONE
```yaml
description: |
  Pre-commit + runtime constitutional enforcement:
  - ScalarBanLinter on commit
  - Runtime assertions at boundaries
path: tools/hooks/, governance/runtime_assertions.py
status: S40_COMPLETE ✓
tests: 52
invariants: INV-HOOK-1/2/3/4
```

### SELF_HEALING_MECHANISMS — DONE
```yaml
description: |
  - Exponential backoff retries
  - Circuit breakers on repeated failures
  - Health state machine
path: governance/circuit_breaker.py, backoff.py, health_fsm.py
status: S40_COMPLETE ✓
tests: 57
invariants: INV-CIRCUIT-1/2, INV-BACKOFF-1/2, INV-HEALTH-1/2, INV-HEAL-REENTRANCY
```

---

## COMPLETED (S42) ✓ — TRUST_CLOSURE

### TECH_DEBT_CLEANUP — DONE
```yaml
description: |
  Cleaned up 104 pre-existing test failures + 7 errors.
  28 xfailed (documented), 0 failures.
status: S42_COMPLETE ✓
path: tests/conftest.py, docs/S42_FAILURE_TRIAGE.md
```

### RIVER_DATA_PIPELINE — DONE (SYNTHETIC FALLBACK)
```yaml
description: |
  Created synthetic river fallback for testing.
  Real River connectivity remains IBKR-dependent.
status: S42_COMPLETE ✓
path: river/synthetic_river.py
```

### CSO_PRODUCTION_READINESS — DONE
```yaml
description: |
  Gate glossary (48 gates), health file, operator docs.
  CSO validated for production.
status: S42_COMPLETE ✓
paths:
  - cso/knowledge/GATE_GLOSSARY.yaml
  - state/health_writer.py
  - docs/OPERATOR_INSTRUCTIONS/
```

---

## S48-S51 CANDIDATES (PRE-SCHEDULED)

### VOICE_WHISPERER
```yaml
description: |
  Natural language voice interface.
status: SCHEDULED → S48 (HUD_SURFACE)
priority: P3
```

### OINK_EASTER_EGGS
```yaml
description: |
  Fun messages on success ("Recombobulation complete").
status: SCHEDULED → S51 (PRO_FLOURISHES)
priority: P4
```

---

## S43 SCOPE (SCHEDULED)

### PYTEST_PARALLELIZATION
```yaml
status: SCHEDULED → S43_BUILD_MAP (Track A)
source: NEX pattern subsumption + banteg zero-jank hardening
priority: P0
sprint_target: S43

description: |
  Leverage pytest-xdist (-n auto / -n logical) to parallelize
  chaos bunny + validation suite.
  Goal: 1502+ tests from ~7 min → <3 min wall time.
  Preserve strict ordering for stateful fixtures via xdist groups / worker gating.

dependencies:
  - S42 tech debt burn complete (pytest must tell truth first)

invariants_to_preserve:
  - INV-HEALTH-1 (no parallel health races)
  - INV-CIRCUIT-1 (circuit breaker isolation)

implementation_notes:
  - pip install pytest-xdist
  - pytest -n auto (or -n logical for core-aware)
  - Group stateful tests: @pytest.mark.xdist_group("health")
  - Verify no shared state pollution across workers

hardware_context:
  - Mac Studio: 12+ cores available
  - Mac Mini Pro M4: 10+ cores available
  - Either sufficient for parallel gains

effort_estimate: 2-4 hours (config + grouping + smoke)

chaos_upside: |
  Run bunny vectors in parallel → discover race conditions
  we never saw sequentially. If it breaks, we learn.
  If it flies, supremacy speed unlocked.
```

### STRATEGY_CARTRIDGE_PRIMITIVE
```yaml
status: PARKED
source: CSO knowledge integration (S42)
priority: P3 (future sprint)
sprint_target: TBD

description: |
  Target: Olya strategy = one YAML manifest + drawer deltas + optional template override
  → slots in, CSO auto-indexes, narrator picks up, hunt/CFP just runs
  → guard dog unchanged, calibration drift measurable

trigger: "Can strategies slot in like Nintendo cartridges?"
assessment: "Highly likely needs tuning"

dependencies:
  - 5-drawer filing cabinet stable (S42 BLUR fixes complete)
  - CSO validation complete
  - Guard dog proven in production

invariants_to_preserve:
  - INV-SLM-CLASSIFICATION-ONLY-1 (guard dog unchanged)
  - INV-NO-UNSOLICITED (no strategy self-modification)

implementation_notes:
  - Strategy manifest schema (YAML)
  - Drawer delta format (additions/overrides only)
  - Auto-index hook in CSO
  - Narrator template discovery
  - Drift measurement baseline

effort_estimate: Unknown (needs scoping)
```

---

## POST v0.1 PARKED (S43+ Advisory Convergence)

### MULTI_AGENT_ORCHESTRATION_LIGHT
```yaml
status: PARKED (post v0.1)
source: GROK synthesis, advisory convergence 2026-01-31
priority: P4 (complexity after foundation stable)

description: |
  Orchestrator spawns sub-agents for Hunt/CFP parallel execution.
  Full business orchestration beyond trading scope.

dependencies:
  - S35-S42 foundation proven ✓
  - WARBOAR v0.1 complete
  - Production stability observed

governance: Requires T2 extension to sub-agent spawning
verdict: KEEP PARKED — complexity after foundation stable
```

### TOKEN_COST_INFRASTRUCTURE
```yaml
status: NEW_PARK (post v0.1)
source: GROK synthesis, advisory convergence 2026-01-31
priority: P3 (nice-to-have)

description: |
  - Per-lease budget enforcement
  - Spike alerts
  - No runaway bills

relation: INV-HUNT-BUDGET is immediate (S38)
verdict: PARK — nice-to-have, not blocking v0.1
```

### REGIME_NUKE_AUTOPSY
```yaml
status: NEW_PARK (post v0.1)
source: GROK synthesis, advisory convergence 2026-01-31
priority: P3 (forensic enhancement)

description: |
  Post-crash bead palace queries ("why did lease fail?")
  Enhanced forensic analysis on regime changes.

dependencies:
  - Bead palace operational ✓
  - Lease framework complete (S47)

verdict: PARK — forensic palace exists, enhance post-ship
```

### OLYA_OCD_INTEGRATION
```yaml
status: OPERATOR_PACED (post v0.1)
source: CSO observation, advisory convergence 2026-01-31
priority: P4 (Olya-dependent)

description: |
  Custom runbook checklists as filing cabinet extension.
  Olya's personal workflow integration.

dependencies:
  - 5-drawer filing cabinet stable ✓
  - Olya calibration complete (S50)

verdict: PARK — can't force Olya's rhythm, revisit post-calibration
```

---

## S42+ DORMANT (Original GROK Frontier Synthesis)

### MULTI_AGENT_ORCHESTRATION
```yaml
description: |
  Orchestrator agent spawns role-specific sub-agents with dependency graphs.
  Enables "runs a business" endgame beyond trading.
dependencies: S35-S40 foundation proven
governance: Requires T2 extension to sub-agent spawning
status: DORMANT (superseded by MULTI_AGENT_ORCHESTRATION_LIGHT)
```

### WORKFLOW_LEARNING
```yaml
description: |
  Evaluate success metrics + bead trail → store successful patterns →
  propose template refinements (human veto only).
governance: |
  - Narrow salvage of NEX-027 pattern
  - Human veto required; no auto-update of doctrine
  - Requires INV-NO-UNSOLICITED to be proven safe
dependencies: S37 Memory Discipline complete
status: DORMANT
```

### RBAC_SUB_AGENTS
```yaml
description: |
  Extend T2 gating to sub-agents. Orchestration agent can't spawn
  sensitive workers without token. Role-based scope.
rationale: Multi-agent sprawl risks authority leakage
dependencies: Multi-agent orchestration operational
status: DORMANT
```

### TOKEN_COST_INFRASTRUCTURE
```yaml
description: |
  - Per-workflow token budget
  - Prompt optimization
  - Alert on cost spikes
relation: INV-HUNT-BUDGET is immediate (S38); full infrastructure is S42+
status: DORMANT
```

### ALERT_TAXONOMY
```yaml
description: |
  - Notification hierarchy (critical → warning → info)
  - Deduplication rules
  - Telegram/Discord routing
status: DORMANT (partial in S40 HealthFSM)
```

---

## FRONTIER PATTERNS (Reference Only)

### Yegge Beads
```yaml
source: Steve Yegge
insight: "Beads are the town's records – inhabitants forget, town remembers"
application: Immutable event sourcing, bead chain architecture
status: APPLIED (Phoenix beads)
```

### Willison Datasette
```yaml
source: Simon Willison
insight: Queryable state as memory palace
application: Bead query endpoint for live recombobulation
status: S35 CFP scope
```

### Banteg Minimalism
```yaml
source: @banteg
insight: Zero deps, fail-safe defaults
application: IBKR supervisor, halt-first architecture
status: APPLIED (governance patterns)
```

### Anthropic Dynamic Workflow Entry
```yaml
source: Spenser Skates 2026
insight: AI enters workflows dynamically at decision points
application: HUD overlay, Pilot whisperer concept
status: S40+ (truth-first foundation required)
```

---

## ACTIVATION CRITERIA

Items move from CARPARK to SPRINT backlog when:

1. **Dependencies met** - Previous sprint invariants proven
2. **User friction identified** - Real pain point, not speculative
3. **Safe path exists** - Frontier-validated, invariants defined
4. **Advisor consensus** - GPT + GROK + OWL alignment
5. **G approval** - Sovereign greenlight

---

## DEAD ITEMS (NEVER RESURRECT)

The following are explicitly KILLED per DEFINITIVE_FATE.yaml:

| NEX-ID | Name | Death Reason |
|--------|------|--------------|
| NEX-010 | Gemma Full Analysis | LLM authors meaning |
| NEX-011 | Gemma Quick Check | Compressed authority transfer |
| NEX-032 | Strategy Stability Index | Single scalar = hidden weighting |
| NEX-036 | Debrief Agent | LLM extracts "learnings" |
| NEX-039 | Edge Discovery Scan | System proposes hypotheses |
| NEX-042 | Athena Suggestions | System proposes research |
| NEX-047 | Actionability Engine | "What should I do" = authority transfer |
| NEX-052 | Drift Diagnosis Challenge | Challenges LLM explanation that shouldn't exist |
| NEX-059 | Strategy Health Score | Single scalar = hidden weighting |

**Resurrection requires:** Full advisor joist + G approval + new invariants.

---

*Fuel stays parked until foundation proves ready.*
*"Quality > Speed. Explicit > Implicit. Facts > Stories."*
