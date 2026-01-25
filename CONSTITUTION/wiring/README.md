# wiring/

Module interconnection topology.

## Files (to be created)

- `halt_propagation.yaml` — Halt cascade graph
- `data_flow.yaml` — Data pipeline topology
- `telemetry_aggregation.yaml` — Quality reporting paths

## Format

```yaml
topology:
  name: "halt_propagation"
  type: "directed_acyclic_graph"
  
  nodes:
    - river
    - cso
    - execution
    
  edges:
    - from: river
      to: cso
      latency_slo_ms: 50
      
    - from: cso
      to: execution
      latency_slo_ms: 50
      
  invariants:
    - "total_cascade_latency < 500ms"
    - "no_orphan_halts"
```
