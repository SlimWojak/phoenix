# tests/

Test-to-invariant mappings.

## Files (to be created)

- `invariant_test_map.yaml` — Which test proves which invariant

## Format

```yaml
test_map:
  INV-HALT-1:
    test_file: "test_halt_latency.py"
    test_function: "test_halt_signal_latency_p99"
    proven: true
    last_run: "2026-01-25"
    result: "0.003ms < 50ms"
    
  INV-CONTRACT-1:
    test_file: "test_state_hash_canonical.py"
    test_function: "test_same_state_same_hash"
    proven: true
```

## Validation Rule

> "A contract is invalid unless an automated test can fail it."

Every INV-* must have a corresponding test mapping.
