# REPO_MAP — Phoenix Repository Structure

```yaml
document: REPO_MAP
version: 1.1
date: 2026-02-04
purpose: Filing cabinet reference
```

---

## Quick Reference

| Need | Location |
|------|----------|
| What is Phoenix? | `docs/canon/PHOENIX_MANIFEST.md` |
| System architecture | `docs/canon/ARCHITECTURAL_FINALITY.md` |
| Sprint roadmap | `docs/canon/SPRINT_ROADMAP.md` |
| Future scope | `docs/canon/CARPARK.md` |
| Cartridge/Lease design | `docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md` |
| Strategy definitions | `cartridges/active/` |
| Active leases | `leases/active/` |
| CSO knowledge (5-drawer) | `cso/knowledge/` |
| Runbooks | `docs/operations/runbooks/` |
| Operator guides | `docs/operations/operator/` |
| Current sprint work | `docs/build/current/` |
| Historical docs | `docs/archive/` |

---

## Folder Structure

```
phoenix/
├── README.md                     # Project overview
├── CLAUDE.md                     # Agent instructions
├── REPO_MAP.md                   # This file
│
├── docs/
│   ├── canon/                    # LOCKED authoritative docs
│   │   ├── designs/              # Canonical design specs
│   │   └── *.md                  # Core definitions
│   ├── operations/               # How to run Phoenix
│   │   ├── runbooks/             # Emergency procedures (RB-*)
│   │   └── operator/             # Human operator guides
│   ├── build/                    # Working documents
│   │   ├── current/              # Active sprint work
│   │   └── explorations/         # R&D, ideas
│   ├── archive/                  # Historical reference
│   │   ├── sprints/              # Completed sprint docs
│   │   ├── reports/              # Historical reports
│   │   └── designs/              # Superseded designs
│   └── reference/                # Cross-cutting guides
│
├── CONSTITUTION/                 # Constitutional definitions
│   ├── invariants/               # INV-* rules
│   └── ...
│
├── cso/
│   └── knowledge/                # Olya's 5-drawer methodology
│       ├── foundation.yaml       # Drawer 1: Market structure
│       ├── context.yaml          # Drawer 2: HTF context
│       ├── conditions.yaml       # Drawer 3: Setup conditions
│       ├── entry.yaml            # Drawer 4: Entry rules
│       ├── management.yaml       # Drawer 5: Position management
│       ├── index.yaml            # Signal relationships
│       └── GATE_GLOSSARY.yaml    # Gate definitions
│
├── cartridges/                   # Strategy manifests
│   ├── active/                   # Currently slotted
│   ├── templates/                # Blank templates
│   └── archive/                  # Deprecated strategies
│
├── leases/                       # Governance wrappers
│   ├── active/                   # Currently active
│   ├── expired/                  # Completed normally
│   └── revoked/                  # Terminated early
│
├── schemas/                      # YAML schema definitions
├── contracts/                    # Data contracts (code)
├── reports/                      # Test results
├── drills/                       # Validation scripts
│
├── governance/                   # Governance enforcement
│   ├── halt.py                   # Kill switch (<50ms)
│   ├── lease.py                  # S47: State machine + interpreter
│   ├── lease_types.py            # S47: Pydantic models
│   ├── cartridge.py              # S47: Loader + linter
│   ├── insertion.py              # S47: 8-step protocol
│   └── ...
│
├── tests/
│   ├── test_lease/               # S47: Lease system tests
│   │   ├── test_state_machine.py
│   │   ├── test_halt_override.py
│   │   ├── test_bounds.py
│   │   └── test_expiry.py
│   └── chaos/
│       └── test_bunny_s47.py     # S47: Chaos vectors
│
└── [other module folders]        # Code modules
    (brokers, cfp, execution, narrator, etc.)
```

---

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Canonical docs | `UPPER_SNAKE_CASE.md` | `ARCHITECTURAL_FINALITY.md` |
| Versioned designs | `NAME_v{version}.md` | `CARTRIDGE_AND_LEASE_DESIGN_v1.0.md` |
| Sprint docs | `S{number}_*.md` | `S44_BUILD_MAP_v0.1.md` |
| Runbooks | `RB-{number}_{TITLE}.md` | `RB-001_CONNECTION_LOSS.md` |
| Cartridges | `{STRATEGY}_v{semver}.yaml` | `ASIA_RANGE_SCALP_v1.0.0.yaml` |
| Leases | `lease_{date}_{strategy}_{id}.yaml` | `lease_2026_01_31_asia_001.yaml` |

---

## Key Paths

### Canon (Authoritative)
- `docs/canon/` — Core definitions, locked
- `docs/canon/designs/` — Design specifications
- `CONSTITUTION/` — Constitutional rules
- `cso/knowledge/` — Methodology knowledge

### Operations (How to Run)
- `docs/operations/runbooks/` — Emergency procedures
- `docs/operations/operator/` — Human guides

### Build (Working)
- `docs/build/current/` — Active sprint
- `docs/build/explorations/` — R&D

### Runtime
- `cartridges/active/` — Active strategy
- `leases/active/` — Active governance bounds

---

## Rules

1. **Canon is locked** — No edits without G approval
2. **One active cartridge** — Single strategy at a time (v1.0)
3. **Archive, don't delete** — Historical docs are forensic
4. **README in every folder** — Self-documenting structure
5. **Naming conventions matter** — Predictable, greppable

---

*Last updated: 2026-02-04 (S47 Lease Implementation added)*
