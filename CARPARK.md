# CARPARK.md
# Phoenix Future Fuel — Items Not Yet Scheduled

```yaml
document: CARPARK.md
version: 4.1
date: 2026-01-30
status: CANONICAL
source: DEFINITIVE_FATE.yaml carpark section + advisor synthesis
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

## S42 CANDIDATES

### TECH_DEBT_CLEANUP
```yaml
description: |
  Clean up 104 pre-existing test failures + 7 errors.
  - test_no_live_orders.py: ExecutionIntent import error
  - test_telegram_real.py: API mismatch
  - test_schema_lockdown.py: Schema drift
  - test_chaos_bunny.py: Chaos vectors incomplete
status: CANDIDATE
priority: P1
effort: 1-2 hours
reference: docs/TECH_DEBT.md
```

### RIVER_DATA_PIPELINE
```yaml
description: |
  Connect River to live data source.
  No recent bars during S41 validation.
status: CANDIDATE
priority: P2
dependencies: IBKR market data subscription OR alternative source
```

### VOICE_WHISPERER
```yaml
description: |
  Natural language voice interface.
  Parked from S40.
status: PARKED
priority: P3
dependencies: Foundation proven in production
```

### OINK_EASTER_EGGS
```yaml
description: |
  Fun messages on success ("Recombobulation complete").
  Parked from S41 Phase 2E.
status: PARKED
priority: P4
dependencies: Post-production launch
```

---

## S43 CANDIDATES

### PYTEST_PARALLELIZATION
```yaml
status: PROPOSED
source: NEX pattern subsumption + banteg zero-jank hardening
priority: P3 (post-S42)
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

## S42+ DORMANT (GROK Frontier Synthesis)

### MULTI_AGENT_ORCHESTRATION
```yaml
description: |
  Orchestrator agent spawns role-specific sub-agents with dependency graphs.
  Enables "runs a business" endgame beyond trading.
dependencies: S35-S40 foundation proven
governance: Requires T2 extension to sub-agent spawning
status: DORMANT
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
