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
project: Phoenix / WarBoar
purpose: Constitutional trading system
status: S40_COMPLETE | S33_P2_BLOCKED (Olya)
block_complete: S35-S40 (CONSTITUTIONAL_CEILING + SLEEP_SAFE)
s40_completion_date: 2026-01-30
certification: SLEEP_SAFE_CERTIFIED
relationship: Sibling to God_Mode (forge builds tools, Phoenix protects capital)
canonical_fate: docs/DEFINITIVE_FATE.yaml
total_tests: 1279
total_invariants: 89+
total_chaos_vectors: 204
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

# S35-S39 (COMPLETE)
cfp/:
  purpose: Conditional Fact Projector
  authority: COMPUTED (conditional facts only, no causal claims)
  status: S35_COMPLETE ✓
  tests: 62

cso/:
  purpose: Gate status (facts, not grades)
  authority: READ_ONLY (consumes, never generates grades)
  status: S36_COMPLETE ✓
  tests: 45

athena/:
  purpose: Memory discipline (CLAIM/FACT/CONFLICT beads)
  authority: STORAGE_ONLY (no doctrine mutation)
  status: S37_COMPLETE ✓
  tests: 51

hunt/:
  purpose: Exhaustive variant computation
  authority: COMPUTE_ONLY (human-declared grids, no selection)
  status: S38_COMPLETE ✓
  tests: 69

validation/:
  purpose: Research validation suite (decomposed outputs)
  authority: COMPUTE_ONLY (no viability scores, no verdicts)
  status: S39_COMPLETE ✓
  tests: 109
  codename: CONSTITUTIONAL_CEILING

# S40 (COMPLETE)
governance/circuit_breaker.py:
  purpose: Circuit breaker FSM (CLOSED→OPEN→HALF_OPEN)
  authority: SELF_HEALING
  status: S40_COMPLETE ✓
  
governance/backoff.py:
  purpose: Exponential backoff with jitter
  authority: RETRY_CONTROL
  status: S40_COMPLETE ✓
  
governance/health_fsm.py:
  purpose: Health state machine (HEALTHY→DEGRADED→CRITICAL→HALTED)
  authority: HEALTH_MONITORING
  status: S40_COMPLETE ✓
  
governance/runtime_assertions.py:
  purpose: Constitutional assertions at runtime boundaries
  authority: RUNTIME_ENFORCEMENT
  status: S40_COMPLETE ✓
  
brokers/ibkr/supervisor.py:
  purpose: Shadow supervisor OUTSIDE trading loop
  authority: WATCHDOG
  status: S40_COMPLETE ✓
  
brokers/ibkr/heartbeat.py:
  purpose: Connector liveness monitoring
  authority: HEARTBEAT
  status: S40_COMPLETE ✓
  
brokers/ibkr/degradation.py:
  purpose: Graceful degradation cascade (T2→T1→T0)
  authority: DEGRADATION
  status: S40_COMPLETE ✓
  
narrator/:
  purpose: Template-based state projection (boar dialect)
  authority: PROJECTION_ONLY (facts, no synthesis)
  status: S40_COMPLETE ✓
  
tools/hooks/:
  purpose: Pre-commit constitutional enforcement
  authority: BUILD_TIME_ENFORCEMENT
  status: S40_COMPLETE ✓
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
  cfp/: S35_COMPLETE ✓
  cso_harness/: S36_COMPLETE ✓
  athena/: S37_COMPLETE ✓
  hunt/: S38_COMPLETE ✓
  validation/: S39_COMPLETE ✓

validation_flow:
  River → CFP (conditional facts) → Athena (memory) → Hunt (grid) → Validation (decomposed)
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

### ATTRIBUTION (S35 CFP) ✓

```yaml
INV-ATTR-CAUSAL-BAN: "No causal claims; only conditional facts" ✓
INV-ATTR-PROVENANCE: "All outputs include query_string + dataset_hash + bead_id" ✓
INV-ATTR-NO-RANKING: "No ranking, no best/worst, no implied priority" ✓
INV-ATTR-SILENCE: "System does not resolve conflicts; surfaces and waits" ✓
INV-ATTR-NO-WRITEBACK: "Stored facts cannot mutate doctrine" ✓
INV-ATTR-CONFLICT-DISPLAY: "When showing best, must show worst alongside" ✓
```

### HARNESS (S36) ✓

```yaml
INV-HARNESS-1: "CSO outputs gate status only, never grades" ✓
INV-HARNESS-2: "No confidence scores unless explicit formula" ✓
INV-HARNESS-3: "Alerts fire on gate combinations, not quality" ✓
INV-HARNESS-4: "Multi-pair sorted alphabetically by default" ✓
INV-NO-GRADE-RECONSTRUCTION: "No A/B/C/D/F grades anywhere" ✓
```

### MEMORY (S37) ✓

```yaml
INV-CLAIM-FACT-SEPARATION: "Claims and facts are distinct bead types" ✓
INV-CONFLICT-NO-RESOLUTION: "System flags conflicts, never resolves" ✓
INV-MEMORY-PROVENANCE: "All memories have full provenance chain" ✓
```

### HUNT (S38) ✓

```yaml
INV-HUNT-EXHAUSTIVE: "Hunt computes ALL declared variants, never selects" ✓
INV-HUNT-BUDGET: "Compute/token cap enforced per run" ✓
INV-HUNT-NO-SURVIVOR-RANKING: "No 'best performer' rankings" ✓
INV-HUNT-NO-SELECTION: "Grid returns full table, never filters" ✓
```

### VALIDATION (S39) ✓ — CONSTITUTIONAL CEILING

```yaml
INV-SCALAR-BAN: "No composite scores (0-100); decompose to factors" ✓
INV-NO-AGGREGATE-SCALAR: "No avg_* fields; return full arrays" ✓
INV-NEUTRAL-ADJECTIVES: "No evaluative words (strong, weak, robust)" ✓
INV-VISUAL-PARITY: "No color metadata (red=bad, green=good)" ✓
INV-NO-IMPLICIT-VERDICT: "Mandatory disclaimer on all outputs" ✓
INV-CROSS-MODULE-NO-SYNTH: "Chain outputs remain decomposed" ✓
```

### SELF-HEALING (S40) ✓

```yaml
INV-CIRCUIT-1: "OPEN circuit blocks all requests" ✓
INV-CIRCUIT-2: "HALF_OPEN allows exactly 1 probe" ✓
INV-BACKOFF-1: "Retry interval doubles each attempt" ✓
INV-BACKOFF-2: "Interval capped at max (300s)" ✓
INV-HEALTH-1: "CRITICAL → alert callback within 30s" ✓
INV-HEALTH-2: "HALTED → halt_callback invoked" ✓
INV-HEAL-REENTRANCY: "N failures in 1s → 1 alert, not N" ✓
```

### IBKR RESILIENCE (S40) ✓

```yaml
INV-IBKR-FLAKEY-1: "3 missed heartbeats → DEAD declaration" ✓
INV-IBKR-FLAKEY-2: "Supervisor survives connector crash" ✓
INV-IBKR-FLAKEY-3: "Reconnection restores only after validation" ✓
INV-IBKR-DEGRADE-1: "T2 blocked within 1s of disconnect" ✓
INV-IBKR-DEGRADE-2: "No T2 allowed in DEGRADED state" ✓
INV-SUPERVISOR-1: "Supervisor death → immediate alert" ✓
```

### HOOKS (S40) ✓

```yaml
INV-HOOK-1: "Pre-commit blocks scalar_score in new code" ✓
INV-HOOK-2: "Pre-commit blocks causal language" ✓
INV-HOOK-3: "Runtime catches missing provenance" ✓
INV-HOOK-4: "Runtime catches ranking fields" ✓
```

### NARRATOR (S40) ✓

```yaml
INV-NARRATOR-1: "Narrator outputs facts only, no synthesis" ✓
INV-NARRATOR-2: "All data fields have explicit source" ✓
INV-NARRATOR-3: "Undefined variable → error, not silent" ✓
```

### SAFETY (Cross-Sprint)

```yaml
INV-NO-UNSOLICITED: "System never says 'I noticed' or proposes hypotheses" ✓
INV-LLM-REMOVAL-TEST: "If removing LLM prevents reconstruction → invalid" ✓
INV-NO-ROLLUP: "No aggregation across traffic lights; no 'overall' label" ✓
INV-NO-DEFAULT-SALIENCE: "UI must not imply importance" ✓
INV-SLICE-MINIMUM-N: "N < 30 → warn or fail-silent" ✓
INV-BIAS-PREDICATE: "HTF bias as predicate status, not directional words" ✓
```

### GOVERNANCE

```yaml
INV-REGIME-EXPLICIT: "Regimes = explicit predicates, never auto-detected" ✓
INV-REGIME-GOVERNANCE: "Regimes versioned, capped (~20 max)" ✓
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
# FOUNDATION (S28-S34)
S28-S31: Foundation (River, Governance, Halt, CSO, Signalman)
S32: Execution path (IBKR mock, T2, lifecycle) | 17/17 BUNNY
S33_P1: Infrastructure (Real IBKR, monitoring, runbooks) | 15/15 BUNNY
S34: Operational finishing (D1-D4) | 13/13 BUNNY

# BLOCKED
S33_P2: BLOCKED (Olya CSO calibration)

# CONSTITUTIONAL BLOCK (S35-S39) — COMPLETE ✓
S35: CFP (Conditional Fact Projector) | ✓ 62 tests, 21 BUNNY
S36: CSO Harness (gate status, not grades) | ✓ 45 tests, 18 BUNNY
S37: Memory Discipline (CLAIM/FACT/CONFLICT) | ✓ 51 tests, 15 BUNNY
S38: Hunt Infrastructure (exhaustive compute) | ✓ 69 tests, 23 BUNNY
S39: Research Validation (decomposed outputs) | ✓ 109 tests, 28 BUNNY

# SLEEP_SAFE BLOCK (S40) — COMPLETE ✓
S40: Sleep-Safe Resilience | ✓ 312 tests, 15 BUNNY
  Track_A: Self-Healing (circuit breakers, backoff, health FSM) | 57 tests
  Track_B: IBKR Flakey (supervisor, heartbeat, degradation) | 56 tests
  Track_C: Hooks (pre-commit + runtime assertions) | 52 tests
  Track_D: Narrator (template-based state projection) | 38 tests
  Track_E: Professional Polish (API alignment) | 56 tests
  Track_F: BUNNY Chaos Battery (15 vectors) | 45 tests

cumulative_summary:
  s35_s39_completion_date: 2026-01-29
  s40_completion_date: 2026-01-30
  total_tests: 1279
  total_bunny_vectors: 204
  total_invariants: 89+
  s35_s39_theme: "CONSTITUTIONAL CEILING"
  s40_theme: "SLEEP_SAFE"

# NEXT
S41: WARBOAR_AWAKENS (Unsloth distillation, live validation)
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

*S35-S40 COMPLETE. Human frames, machine computes. Human sleeps.*
*No scalar scores. No rankings. No verdicts. Ever.*
*The constitutional ceiling is set. The floor holds. Sleep-safe certified. 🐗🔥*
