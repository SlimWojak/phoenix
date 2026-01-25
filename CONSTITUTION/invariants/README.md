# invariants/

Constitutional invariants in YAML format.

## Files (to be created)

- `halt.yaml` — INV-HALT-* invariants
- `governance.yaml` — INV-GOV-* invariants
- `contract.yaml` — INV-CONTRACT-* invariants
- `data.yaml` — INV-DATA-* invariants
- `cso.yaml` — INV-CSO-* invariants
- `dynasty.yaml` — INV-DYNASTY-* invariants

## Format

```yaml
invariants:
  - id: INV-HALT-1
    description: "halt_local_latency < 50ms"
    enforcement: "hard"
    test: "test_halt_latency.py"
    proven: true
    proof_date: "2026-01-25"
```
