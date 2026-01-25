# GOVERNANCE INTERFACE CONTRACT

**VERSION:** 0.2 (lint-hardened)  
**STATUS:** ACTIVE  
**DATE:** 2026-01-25  
**AMENDED:** GPT L1-L15, OWL F1-F2 integrated

---

## PURPOSE

Define the abstract base class that ALL Phoenix organs must inherit.
Provides governance skeleton for halt mechanism, tier enforcement,
quality telemetry, and state machine determinism.

---

## INVARIANTS

| ID | Invariant | Type | Test |
|----|-----------|------|------|
| INV-HALT-1 | `halt_local_latency < 50ms` | HARD | test_halt_latency.py |
| INV-HALT-2 | `halt_cascade_latency < 500ms` | SLO | test_halt_propagation.py |
| INV-GOV-1 | All Phoenix organs inherit GovernanceInterface | HARD | build reject |
| INV-GOV-2 | Tier violations trigger automatic escalation | HARD | test_tier_gates.py |
| INV-GOV-NO-T1-WRITE-EXEC | T1 may not write execution_state, orders, positions | HARD | test_tier_gates.py |
| INV-GOV-HALT-BEFORE-ACTION | Gate checks halt_signal before T2 submit | HARD | test_halt_blocks_t2_action.py |
| INV-CONTRACT-1 | Deterministic state machine | HARD | test_state_hash_canonical.py |

---

## MODULE IDENTITY

```yaml
module_id:
  type: str
  required: TRUE
  semantics: unique identifier for dependency graph

module_tier:
  type: enum[T0, T1, T2]
  required: TRUE
  semantics:
    T0: read-only, no capital impact
    T1: capital-adjacent, automated gates
    T2: capital-affecting, human gate required

enforced_invariants:
  type: List[str]
  required: TRUE
  enforcement: missing invariant → build rejection

yield_points:
  type: List[str]
  required: TRUE (if module has loops/long compute)
  enforcement: missing → build reject for long-compute modules

dependency_graph_hash:
  type: str
  semantics: hash of [module_id, get_dependents()]
```

---

## TIER PERMISSIONS

### T0 (Read-Only)
- **writes:** none
- **reads:** market_data, indicators
- **forbidden:** advisory_state, execution_state, orders, positions

### T1 (Capital-Adjacent)
- **writes:** advisory_state
- **reads:** market_data, indicators, advisory_state
- **forbidden:** execution_state, orders, positions
- **gate:** automated (quality_score > 0.70, no CRITICAL 24h)

### T2 (Capital-Affecting)
- **writes:** execution_state, orders, positions
- **reads:** all
- **gate:** human (Sovereign or delegate)
- **requires:** ApprovalToken
- **pre_check:** halt_signal == FALSE

---

## HALT MECHANISM

### request_halt()
```yaml
signature: () -> HaltSignalSetResult
latency: < 50ms (HARD)
semantics: |
  - sets local halt flag
  - NO IO, NO logging, NO propagation
  - returns immediately
test: test_halt_latency.py
```

### propagate_halt()
```yaml
signature: (halt_id: str) -> HaltCascadeReport
latency: < 500ms (SLO)
semantics: |
  - async propagation to dependents
  - logs halt reason
  - collects ack receipts
test: test_halt_propagation.py
```

### check_halt()
```yaml
signature: () -> None
semantics: |
  - cooperative yield point
  - raises HaltException if halt_signal TRUE
  - MUST be called at declared yield_points
test: test_check_halt_yield_points.py
```

### acknowledge_halt()
```yaml
signature: (halt_id: str) -> AckReceipt
timeout: 50ms per hop
retry_policy:
  max_retries: 2
  backoff_ms: 10
```

---

## STATE MACHINE

### process_state()
```yaml
signature: (input: StateInput) -> StateTransition
required: TRUE
semantics: |
  - core execution method
  - deterministic (same input → same output)
  - must call check_halt() at yield_points
```

### compute_state_hash()
```yaml
signature: () -> str
semantics: |
  includes: [positions, orders, constraints, risk_state.status]
  excludes: [timestamps, heartbeats, diagnostics]
  serialization: canonical_sorted_json
  hash_fn: sha256[:16]
test: test_state_hash_canonical.py
```

---

## QUALITY TELEMETRY

### QualityTelemetry
```yaml
data_health: enum[HEALTHY, DEGRADED, CRITICAL]
lifecycle_state: enum[RUNNING, STOPPING, STOPPED]
quality_score: float (0.0-1.0)
last_update: timestamp
anomaly_count: int
gap_count: int
staleness_seconds: float
```

### Health Thresholds
| Score | State |
|-------|-------|
| >= 0.95 | HEALTHY |
| >= 0.70 | DEGRADED |
| < 0.70 | CRITICAL |

### Test: test_telemetry_emission.py

---

## VIOLATION HANDLING

### ViolationTicket
```yaml
ticket_id: str
invariant_id: str
timestamp: datetime
severity: enum[WARNING, VIOLATION, CRITICAL]
status: enum[OPEN, ACKED, RESOLVED, WAIVED]
auto_escalate_cto_at: timestamp (+12h)
auto_escalate_sovereign_at: timestamp (+24h)
```

### Escalation Schedule (Dead-Man's Switch)
- **+12h:** Escalate to CTO
- **+24h:** Escalate to Sovereign

### Test: test_violation_escalation_schedule.py

---

## APPROVAL TOKEN (T2)

```yaml
ApprovalToken:
  issued_by: str (human_id)
  issued_at: datetime
  expires_at: datetime
  scope: List[action_types]
  state_hash: str (must match compute_state_hash())

validation:
  1. halt_signal == FALSE (INV-GOV-HALT-BEFORE-ACTION)
  2. token not expired
  3. state_hash matches current
  4. scope includes requested action

test: test_halt_blocks_t2_action.py
```

---

## WIRING CONTRACT

```
River.request_halt() → River.propagate_halt()
  → Enrichment.acknowledge_halt()
  → Enrichment.propagate_halt()
    → CSO.acknowledge_halt()
    → CSO.propagate_halt()
      → Execution.acknowledge_halt()
```

**Invariant:** No orphan halts (validated via get_dependents())

---

## FILES

| File | Purpose |
|------|---------|
| governance/__init__.py | Package exports |
| governance/interface.py | GovernanceInterface ABC |
| governance/types.py | Enums, dataclasses |
| governance/halt.py | Halt mechanism |
| governance/telemetry.py | Quality reporting |
| governance/tokens.py | ApprovalToken validation |
| governance/errors.py | Error classification |

---

## TESTS

| Test | Exit Gate |
|------|-----------|
| test_halt_latency.py | request_halt() < 50ms (p99) |
| test_halt_propagation.py | cascade completes, no orphans |
| test_halt_blocks_t2_action.py | T2 rejected when halted |
| test_check_halt_yield_points.py | cooperative halt works |
| test_tier_gates.py | T1 cannot write execution |
| test_telemetry_emission.py | telemetry emits correctly |
| test_state_hash_canonical.py | same state → same hash |
| test_violation_escalation_schedule.py | 12h/24h escalation |

---

## CONTRACT VALIDITY

> "A contract is invalid unless an automated test can fail it"

Every MUST clause → mapped test (L15)

---

*Generated: Sprint 26 Track B*
