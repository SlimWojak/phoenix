# modules/

Phoenix organ definitions.

## Files (to be created)

- `river.yaml` — Data pipeline (T0)
- `cso.yaml` — Chief Strategy Officer (T1)
- `execution.yaml` — Order execution (T2)
- `governance.yaml` — Governance mesh (T0)

## Format

```yaml
module:
  id: "phoenix.cso"
  name: "Chief Strategy Officer"
  tier: "T1"
  inherits: "GovernanceInterface"
  
  enforced_invariants:
    - INV-CSO-1
    - INV-CSO-2
    
  yield_points:
    - evaluate_4q_gate
    - compute_confidence
    
  dependencies:
    - river
    - governance
```
