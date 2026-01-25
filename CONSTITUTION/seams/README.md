# seams/

Inter-module contract definitions.

## Files (to be created)

- `river_to_cso.yaml` — How CSO receives from River
- `cso_to_execution.yaml` — How Execution receives from CSO
- `governance_mesh.yaml` — Halt propagation topology

## Format

```yaml
seam:
  id: "river_to_cso"
  producer: "river"
  consumer: "cso"
  
  contract:
    data_format: "enriched_bar"
    schema_hash: "b848ffe506fd3fff"
    
  invariants:
    - "producer.quality_score > 0.70"
    - "consumer.warmup_state == READY"
    
  failure_mode:
    stale_data: "block_consumer"
    schema_mismatch: "halt_both"
```
