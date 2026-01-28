# PHOENIX_MANIFEST.md

> "Anthropic is discovering the same law from the opposite direction.
> They started with UI → struggling toward truth.
> You started with truth → earned UI.
> That asymmetry is everything."
> — GPT synthesis, 2026

> "Beads are the town's records – inhabitants forget, town remembers."
> — Yegge (via GROK)

---

## 1. IDENTITY

```yaml
project: Phoenix
purpose: Constitutional trading system
status: S34_COMPLETE
relationship: Sibling to God_Mode (forge builds tools, Phoenix protects capital)
```

## 1b. NON-GOALS

```yaml
- NOT an AI trader (logic lives in CSO + operator)
- NOT a dashboard (no control surfaces)
- NOT a strategy generator
- NOT self-improving without human oversight
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
  purpose: CSE validation, signal routing
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

INV-D4-NO-DERIVATION-1:
  status: PROVEN (verbatim projection contract)
  test: drills/d4_verification.py
```

---

## 4. INVARIANTS_PROVEN

### ZERO_DEPS (Green)

```yaml
INV-HALT-1: halt_local < 50ms | tests/test_halt.py
INV-D1-WATCHER-1: exactly-once processing | drills/d1_verification.py
INV-D1-LENS-1: ≤50 tokens context | drills/d1_verification.py
INV-D3-CHECKSUM-1: machine-verifiable, no prose | drills/d3_verification.py
INV-D3-CORRUPTION-1: corruption → STATE_CONFLICT | drills/d3_negative_test.py
INV-D4-GLANCEABLE-1: update <100ms | drills/d4_verification.py
INV-D4-NO-DERIVATION-1: verbatim fields only | drills/d4_verification.py
INV-D4-EPHEMERAL-1: no local persistence | drills/d4_verification.py
```

### API_DEPS (Yellow)

```yaml
INV-IBKR-PAPER-GUARD-1: live blocked without flag | tests/brokers/
INV-IBKR-ACCOUNT-CHECK-1: account validation | drills/ibkr_paper_validation.py
INV-T2-TOKEN-1: single-use, 5min expiry | tests/governance/
INV-T2-GATE-1: no order without token | tests/governance/
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
```

### LOGGED_FOR_FUTURE

```yaml
dynamic_workflow_entry:
  source: Spenser Skates 2026
  status: FUEL_ONLY

pilot_as_whisperer:
  source: S34.5 exploration
  status: DORMANT

bead_query_endpoint:
  source: Willison datasette
  status: FUEL_ONLY
```

---

## 6. CARPARK

```yaml
IBKR_FLAKEY.md:
  path: docs/explorations/IBKR_FLAKEY.md
  pattern: Heartbeat + supervisor (@banteg zero deps)

S35_FUEL:
  name: CSO Harness
  purpose: Evaluation engine for 5-drawer gates

S36_FUEL:
  name: Dynamic Workflow Entry Forge
  purpose: HUD overlay, Pilot whisperer
```

---

## 7. SPRINT_ARCHAEOLOGY

```yaml
S29-S33: Foundation (River, Governance, Halt, Execution)
S33_P1: Paper trade validation ✓
S34: Operational finishing (D1-D4) ✓
S33_P2: BLOCKED (Olya CSO calibration)
S35: PLANNED (CSO Harness)
S36: PLANNED (Dynamic Workflow Entry Forge)
```

---

## 8. BOOTSTRAP

### SEQUENCE

```bash
git pull
cat SKILL.md | head -n 50
ls CONSTITUTION/invariants/
cat docs/PHOENIX_MANIFEST.md
cat state/orientation.yaml  # if exists
```

### FIRST_QUESTIONS

```yaml
- "What is current execution_phase?"
- "Any kill_flags_active?"
- "What's the last human action bead?"
```

### WHAT_NOT_TO_ASSUME

```yaml
- State hash mismatch = heresy, halt first
- Orientation.yaml exists (might be deleted)
- CSO is calibrated (operator-paced)
```

### FIRST_FAILURE_TEST

```yaml
test_1:
  action: Delete orientation.yaml
  expect: Widget goes blank (⚠️ NO STATE)

test_2:
  action: Inject corrupted bead (wrong hash)
  expect: STATE_CONFLICT detected
```

---

*S34 capstone. Truth before UI. Phoenix rises.*
