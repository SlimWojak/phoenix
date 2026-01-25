# CONSTITUTION/

**Phoenix Constitutional Architecture Graph (CAG)**

This directory contains the machine-verifiable structure of Phoenix governance.

---

## Structure

```
CONSTITUTION/
├── CONSTITUTION_MANIFEST.yaml    # Master registry
│
├── modules/          # Organ definitions
│   └── (river.yaml, cso.yaml, execution.yaml)
│
├── seams/            # Inter-module contracts
│   └── (river_to_cso.yaml, cso_to_execution.yaml)
│
├── scenarios/        # Behavioral test scenarios
│   └── (halt_cascade.yaml, warmup_sequence.yaml)
│
├── environment/      # Runtime contexts
│   └── (dev.yaml, test.yaml, prod.yaml)
│
├── roles/            # Agent/human definitions
│   └── (cto.yaml, sovereign.yaml, worker.yaml)
│
├── dependencies/     # External contracts
│   └── (ibkr.yaml, dukascopy.yaml)
│
├── wiring/           # Module topology
│   └── (halt_propagation.yaml, data_flow.yaml)
│
├── invariants/       # Constitutional invariants
│   └── (halt.yaml, governance.yaml, contract.yaml)
│
├── state/            # State machine definitions
│   └── (cso_warmup.yaml, execution_lifecycle.yaml)
│
└── tests/            # Test → invariant mappings
    └── (invariant_test_map.yaml)
```

---

## Purpose

> "A Constitution is invalid unless an automated test can fail it."

This directory transforms `docs/CONSTITUTION_AS_CODE.md` from human-readable
law into machine-verifiable structure.

---

## Usage

```bash
# Validate constitution integrity
python scripts/validate_constitution.py

# Check blast radius of contract change
python scripts/blast_radius.py --contract ICT_DATA_CONTRACT.md

# Run invariant tests
pytest tests/ -k "INV-"
```

---

## Status

| Component | Status |
|-----------|--------|
| Manifest | Skeleton |
| Modules | Pending |
| Invariants | Registered |
| Tests | Mapped |

---

*Sprint 26 — Foundation Proof*
