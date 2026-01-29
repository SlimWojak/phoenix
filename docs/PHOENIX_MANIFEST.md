# PHOENIX_MANIFEST.md

> "Anthropic is discovering the same law from the opposite direction.
> They started with UI → struggling toward truth.
> You started with truth → earned UI.
> That asymmetry is everything."
> — GPT synthesis, 2026

> "Beads are the town's records – inhabitants forget, town remembers."
> — Yegge (via GROK)

> "UI is a projection of state, not a participant in reasoning."

---

## 1. IDENTITY

```yaml
project: Phoenix
purpose: Constitutional trading system
status: S35_ACTIVE | S33_P2_BLOCKED (Olya)
relationship: Sibling to God_Mode (forge builds tools, Phoenix protects capital)
canonical_fate: docs/DEFINITIVE_FATE.yaml
```

## 1b. NON-GOALS

```yaml
- NOT an AI trader (logic lives in CSO + operator)
- NOT a dashboard (no control surfaces)
- NOT a strategy generator
- NOT self-improving without human oversight
- NOT a recommendation engine (system never says "I noticed")
- NOT an authority on meaning (human frames, machine computes)
```

---

## 2. ARCHITECTURE_TOPOLOGY

### MODULES

```yaml
governance/:
  purpose: Halt, invariants, kill flags
  authority: ABSOLUTE

brokers/ibkr/:
  purpose: IBKR connection, guards, session beads
  authority: GATED (T2 required)

cso/:
  purpose: CSE validation, signal routing (gate status, not grades)
  authority: READ_ONLY (consumes, never generates)

orientation/:
  purpose: Machine-verifiable system state checksum
  authority: COMPUTED (aggregation only)

widget/:
  purpose: Verbatim state projection
  authority: NONE (read-only surface)

approval/:
  purpose: T2 evidence display
  authority: PRESENTATION_ONLY

daemons/:
  purpose: File seam spine
  authority: ROUTING_ONLY

# S35+
cfp/:
  purpose: Conditional Fact Projector
  authority: COMPUTED (conditional facts only, no causal claims)
  status: S35_TARGET

athena/:
  purpose: Memory discipline (CLAIM/FACT/CONFLICT beads)
  authority: STORAGE_ONLY (no doctrine mutation)
  status: S37_TARGET

hunt/:
  purpose: Exhaustive variant computation
  authority: COMPUTE_ONLY (human-declared grids, no selection)
  status: S38_TARGET
```

### DAEMONS

```yaml
watcher.py: Intent routing | FILE_SEAM_SPINE
lens.py: Response injection | FILE_SEAM_SPINE
menu_bar.py: Surface renderer | READ_ONLY
```

### FILE_SEAM

```yaml
intents:
  path: /intents/incoming/ → watcher → workers
responses:
  path: /responses/ → lens → Claude
state:
  path: /state/orientation.yaml → surface renderer
```

### DATA_FLOW

```yaml
River → Enrichment → CSO → CSE → Approval → Execution

nodes:
  river/: BUILT
  cso/scanner.py: BUILT
  cso/consumer.py: BUILT
  approval/evidence.py: BUILT
  execution/: STUB
  brokers/ibkr/: BUILT (paper mode)
  cfp/: S35_TARGET
  athena/: S37_TARGET
  hunt/: S38_TARGET
```

---

## 3. CONTRACTS_AND_SEAMS

```yaml
cse_schema.yaml:
  status: PROVEN (mock ↔ production validated)
  path: schemas/cse_schema.yaml

orientation_bead.yaml:
  status: PROVEN (machine-verifiable)
  path: schemas/orientation_bead.yaml

5_drawer_interface:
  status: PROVEN (whitelist only)
  path: cso/knowledge/conditions.yaml

t2_token_contract:
  status: PROVEN (single-use, 5min expiry)
  path: schemas/t2_token.yaml

ibkr_connector:
  status: PROVEN (paper mode)
  path: brokers/ibkr/connector.py

bead_schema:
  status: BUILT (14 types)
  path: schemas/beads.yaml
  s37_additions: [CLAIM_BEAD, FACT_BEAD, CONFLICT_BEAD]

INV-D4-NO-DERIVATION-1:
  status: PROVEN (verbatim projection contract)
  test: drills/d4_verification.py
```

---

## 4. INVARIANTS_PROVEN

### FOUNDATION (S28-S34)

```yaml
# HALT
INV-HALT-1: halt_local < 50ms | tests/test_halt.py
INV-HALT-2: cascade halt < 500ms

# FILE_SEAM
INV-D1-WATCHER-1: exactly-once processing
INV-D1-LENS-1: ≤50 tokens context

# ORIENTATION
INV-D3-CHECKSUM-1: machine-verifiable, no prose
INV-D3-CORRUPTION-1: corruption → STATE_CONFLICT

# SURFACE
INV-D4-GLANCEABLE-1: update <100ms
INV-D4-NO-DERIVATION-1: verbatim fields only
INV-D4-EPHEMERAL-1: no local persistence

# IBKR
INV-IBKR-PAPER-GUARD-1: live blocked without flag
INV-IBKR-ACCOUNT-CHECK-1: account validation

# T2
INV-T2-TOKEN-1: single-use, 5min expiry
INV-T2-GATE-1: no order without token
```

### ATTRIBUTION (S35 CFP)

```yaml
INV-ATTR-CAUSAL-BAN: "No causal claims; only conditional facts"
INV-ATTR-PROVENANCE: "All outputs include query_string + dataset_hash + bead_id"
INV-ATTR-NO-RANKING: "No ranking, no best/worst, no implied priority"
INV-ATTR-SILENCE: "System does not resolve conflicts; surfaces and waits"
INV-ATTR-NO-WRITEBACK: "Stored facts cannot mutate doctrine"
INV-ATTR-CONFLICT-DISPLAY: "When showing best, must show worst alongside"
```

### SAFETY (S35-S39)

```yaml
INV-NO-UNSOLICITED: "System never says 'I noticed' or proposes hypotheses"
INV-LLM-REMOVAL-TEST: "If removing LLM prevents reconstruction from raw output → invalid"
INV-SCALAR-BAN: "No composite scores (0-100); decompose to factor traffic lights"
INV-NO-ROLLUP: "No aggregation across traffic lights; no 'overall' label"
INV-NO-DEFAULT-SALIENCE: "UI must not imply importance without explicit user selection"
INV-SLICE-MINIMUM-N: "N < 30 → warn or fail-silent"
INV-BIAS-PREDICATE: "HTF bias as predicate status, not directional words"
```

### GOVERNANCE (S35-S38)

```yaml
INV-REGIME-EXPLICIT: "Regimes = explicit predicates, never auto-detected"
INV-REGIME-GOVERNANCE: "Regimes versioned, capped (~20 max)"
INV-HUNT-EXHAUSTIVE: "Hunt computes ALL declared variants, never selects"
INV-HUNT-BUDGET: "Compute/token cap enforced per run"
```

### HARNESS (S36)

```yaml
INV-HARNESS-1: "CSO outputs gate status only, never grades"
INV-HARNESS-2: "No confidence scores unless explicit formula"
INV-HARNESS-3: "Alerts fire on gate combinations, not quality"
INV-HARNESS-4: "Multi-pair sorted alphabetically by default"
```

---

## 5. PATTERNS

### PROVEN

```yaml
checksum_not_briefing:
  source: D3
  insight: Machine-verifiable orientation defeats session amnesia

contract_before_integration:
  source: D2
  insight: Mock-first validation proves interface before real data

truth_first_ui:
  source: D4
  insight: UI freedom earned by state discipline

projection_not_participation:
  source: D4
  insight: UI subordinate to state, never participant in reasoning

file_seam_spine:
  source: D1
  insight: Universal injection point for Claude interaction

human_frames_machine_computes:
  source: DEFINITIVE_FATE
  insight: System never proposes; human declares what to compute
```

### REIMAGINE_PATTERNS (S35-S39)

```yaml
gate_facts_not_grades:
  applies_to: [NEX-003, NEX-008, NEX-012]
  phoenix_output: gates_passed[] + gates_failed[]
  forbidden: [letter grades, quality scores, aggregated metrics]

conditional_facts_not_causality:
  applies_to: [NEX-024, NEX-026]
  phoenix_output: "P&L when [condition]"
  forbidden: ["factor X contributed Y%"]
  precedent: Brinson attribution

conflict_surface_not_resolution:
  applies_to: [NEX-016]
  phoenix_output: "Fact A conflicts Fact B" (CONFLICT_BEAD)
  forbidden: [resolution authority]
  precedent: Wikipedia corpus detection
```

### LOGGED_FOR_FUTURE

```yaml
dynamic_workflow_entry:
  source: Spenser Skates 2026
  status: S40+ DORMANT

pilot_as_whisperer:
  source: S34.5 exploration
  status: S40+ DORMANT

bead_query_endpoint:
  source: Willison datasette
  status: S35 CFP scope
```

---

## 6. BEAD_TYPES (S37 Scope)

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

rationale: "Separates memory from myth"
```

---

## 7. CARPARK

```yaml
# IMMEDIATE (S35-S39 scope)
IBKR_FLAKEY.md:
  path: docs/explorations/IBKR_FLAKEY.md
  pattern: Heartbeat + supervisor (@banteg zero deps)

# S40+ DORMANT (GROK frontier)
MULTI_AGENT_ORCHESTRATION:
  description: Orchestrator → sub-agents w/ dependency graphs
  dependencies: S35-S39 proven

SELF_HEALING:
  description: Backoff, circuit breakers, auto-escalation
  dependencies: S35-S39 proven

WORKFLOW_LEARNING:
  description: Store patterns → propose refinements (human veto)
  governance: NEX-027 salvage path

RBAC_SUB_AGENTS:
  description: T2 gating extended to sub-agent spawning
  dependencies: Multi-agent operational

TOKEN_COST_INFRASTRUCTURE:
  description: Per-workflow budget, prompt optimization
  relation: INV-HUNT-BUDGET extended
```

---

## 8. SPRINT_ARCHAEOLOGY

```yaml
# COMPLETE
S28-S31: Foundation (River, Governance, Halt, CSO, Signalman)
S32: Execution path (IBKR mock, T2, lifecycle) | 17/17 BUNNY
S33_P1: Infrastructure (Real IBKR, monitoring, runbooks) | 15/15 BUNNY
S34: Operational finishing (D1-D4) | 13/13 BUNNY

# BLOCKED
S33_P2: BLOCKED (Olya CSO calibration)

# ACTIVE
S35: CFP (Conditional Fact Projector) | LOCKED

# PLANNED
S36: CSO Harness (gate status, not grades) | LOCKED
S37: Memory Discipline (CLAIM/FACT/CONFLICT) | PLANNED
S38: Hunt Infrastructure (exhaustive compute) | PLANNED
S39: Research Validation (decomposed outputs) | PLANNED

# DORMANT
S40+: Multi-agent, self-healing, workflow learning
```

---

## 9. BOOTSTRAP

### SEQUENCE

```bash
git pull
cat docs/DEFINITIVE_FATE.yaml | head -100  # Fate framework
cat docs/SPRINT_ROADMAP.md | grep -A20 "current_sprint"  # Active work
cat docs/PHOENIX_MANIFEST.md  # System map
cat state/orientation.yaml  # if exists
```

### FIRST_QUESTIONS

```yaml
- "What is current execution_phase?"
- "Any kill_flags_active?"
- "What's the last human action bead?"
- "Which sprint is active?"
- "What invariants must this sprint prove?"
```

### WHAT_NOT_TO_ASSUME

```yaml
- State hash mismatch = heresy, halt first
- Orientation.yaml exists (might be deleted)
- CSO is calibrated (operator-paced)
- System can propose (it cannot — human frames only)
- Grades exist (gates_passed only)
```

### FIRST_FAILURE_TEST

```yaml
test_1:
  action: Delete orientation.yaml
  expect: Widget goes blank (⚠️ NO STATE)

test_2:
  action: Inject corrupted bead (wrong hash)
  expect: STATE_CONFLICT detected

test_3:
  action: Request "Grade A" output
  expect: System returns gates_passed[], refuses grades
```

---

## 10. CRITICAL_REFERENCES

```yaml
DEFINITIVE_FATE.yaml:
  purpose: NEX→Phoenix fate table (61 capabilities)
  location: docs/DEFINITIVE_FATE.yaml

SPRINT_ROADMAP.md:
  purpose: S35-S39 detailed scope + invariants
  location: docs/SPRINT_ROADMAP.md

PHOENIX_MANIFESTO.md:
  purpose: Vision, characters, narrative culture
  location: docs/PHOENIX_MANIFESTO.md

conditions.yaml:
  purpose: 5-drawer gate predicates
  location: cso/knowledge/conditions.yaml

beads.yaml:
  purpose: Bead type definitions
  location: schemas/beads.yaml
```

---

*S35 active. Human frames, machine computes. Phoenix rises.*
