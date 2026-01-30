# CARPARK.md
# Phoenix Future Fuel — Items Not Yet Scheduled

```yaml
document: CARPARK.md
version: 3.0
date: 2026-01-30
status: CANONICAL
source: DEFINITIVE_FATE.yaml carpark section + advisor synthesis
```

---

## S41 PROMOTED (WARBOAR_AWAKENS)

### UNSLOTH_DISTILLATION
```yaml
description: |
  Distill Claude reasoning to local SLM using Unsloth.
  WarBoar LLM as "state projector" — barks facts in boar dialect.
  Zero hallucination (locked templates + verifiable data pulls).
status: PROMOTED_TO_S41
priority: P0
reference: docs/build_docs/WARBOAR_RESILIENCE_FINAL_FORM.md
```

### LIVE_VALIDATION
```yaml
description: |
  Paper → Live progression with explicit gates.
  Requires sovereignty membrane operational.
status: PROMOTED_TO_S41
priority: P1
dependencies: S40 IBKR resilience proven
```

### DMG_PACKAGING
```yaml
description: |
  macOS app distribution via .dmg
  Self-contained Python runtime
status: PROMOTED_TO_S41
priority: P2
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
