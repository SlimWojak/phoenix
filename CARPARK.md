# CARPARK.md
# Phoenix Future Fuel — Items Not Yet Scheduled

```yaml
document: CARPARK.md
version: 2.0
date: 2026-01-29
status: CANONICAL
source: DEFINITIVE_FATE.yaml carpark section + advisor synthesis
```

---

## IMMEDIATE BACKLOG (S35-S39 Adjacent)

### IBKR_FLAKEY
```yaml
path: docs/explorations/IBKR_FLAKEY.md
pattern: Heartbeat + supervisor (@banteg zero deps)
status: DOCUMENTED
priority: P2 (revisit if IBKR instability emerges)
```

### CLAUDE_CODE_HOOKS
```yaml
description: |
  Async hooks for constitution enforcement:
  - verify_invariants.py on file_save
  - check_schema_hash.py on contract change
  - halt_regression test on pre_commit
  - notify_owl.py on git_push
status: LOGGED
priority: P3 (optimization, not foundation)
revisit: When Opus/HIVE friction emerges
```

---

## S40+ DORMANT (GROK Frontier Synthesis)

### MULTI_AGENT_ORCHESTRATION
```yaml
description: |
  Orchestrator agent spawns role-specific sub-agents with dependency graphs.
  Enables "runs a business" endgame beyond trading.
dependencies: S35-S39 foundation proven
governance: Requires T2 extension to sub-agent spawning
status: DORMANT
```

### SELF_HEALING_MECHANISMS
```yaml
description: |
  - Exponential backoff retries
  - Circuit breakers on repeated failures
  - Auto-escalation logic beyond basic halt
rationale: Long-running workflows need resilience
dependencies: S35-S39 foundation proven
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
relation: INV-HUNT-BUDGET is immediate (S38); full infrastructure is S40+
status: DORMANT
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
