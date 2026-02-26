# Capital Path Coverage Map

```yaml
document: CAPITAL_PATH_COVERAGE
version: 1.0
date: 2026-02-25
status: CANONICAL
purpose: Explicit list of all capital mutation functions and their sovereign_gate status
invariant: INV-GUARD-AT-LOWEST-CAPITAL-LAYER
update_discipline: Add entry for every new capital mutation path
```

## Capital Mutation Functions

| Function | Location | Guard | Status |
|----------|----------|-------|--------|
| `LeaseStateMachine.activate()` | `governance/lease.py` | `check_sovereign_gate(require_active_lease=False)` | WIRED (S59) |
| `InsertionProtocol._complete_insertion()` | `governance/insertion.py` | `check_halt_signal()` at Step 7 | WIRED (S55) |
| `evaluate_asia_scalp_setup()` | `execution/asia_scalp.py` | Pure eval — guard at caller | DESIGNED |
| `HaltGate.check_before()` | `execution/halt_gate.py` | In-process halt + sentinel | WIRED (S53) |
| Order submission primitives | `brokers/ibkr/` | Not yet built | FUTURE |
| Position scaling | Not yet built | — | FUTURE |
| SL/TP modification | Not yet built | — | FUTURE |

## Guard Layers

```yaml
LAYER_1_FILESYSTEM:
  guard: governance/sovereign_gate.py (@sovereign_gate decorator)
  checks: [HALT.signal, lease_state, ceremony_due]
  scope: All capital-affecting methods

LAYER_2_IN_PROCESS:
  guard: execution/halt_gate.py (HaltGate + sentinel)
  checks: [in-process halt signal, BoundsSentinel intercept]
  scope: Per-action execution checks

LAYER_3_BOUNDS:
  guard: governance/sentinel.py (BoundsSentinel)
  checks: [drawdown, consecutive losses, daily loss]
  scope: Passive bounds enforcement on every capital mutation
```

## Expansion Protocol

When adding new capital mutation paths:
1. Add entry to this table
2. Apply `@sovereign_gate` decorator (or `check_sovereign_gate()` imperative)
3. Add test proving halt blocks the new path
4. Update this document
