# Phoenix

**Status:** S29 BUILD_MAP locked | S30 LEARNING_LOOP next
**Founded:** 2026-01-24

---

## What Is Phoenix

Phoenix is the constitutional trading system built on God_Mode governance.

```
God_Mode (Forge) = The OS — governance patterns, constitutional enforcement
Phoenix (App)    = The Trading System — River, CSO, Execution
```

**Constitutional Anchor:** Human sovereignty over capital is absolute.

---

## Current Status

| Sprint | Name | Status |
|--------|------|--------|
| S28 | STEEL_PIPES | ✓ Complete |
| S29 | BUILD_MAP | ✓ Locked |
| S30 | LEARNING_LOOP | Next |

### S30 Focus: LEARNING_LOOP
- T0: Data schemas (HPG, Query IR)
- T1: CSO reasoning harness
- T2: Bead pipeline tests

See: `docs/build_docs/SPRINT_ROADMAP_S30_S33_v0.2.md`

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/SlimWojak/phoenix.git
cd phoenix

# 2. Setup (using nex venv)
cd ~/nex && source .venv/bin/activate

# 3. Run tests
python -m pytest ~/phoenix/tests/ -v
```

---

## Key Docs

| Doc | Purpose |
|-----|---------|
| [PRODUCT_VISION](docs/build_docs/PRODUCT_VISION.md) | Why we're building this |
| [SPRINT_ROADMAP](docs/build_docs/SPRINT_ROADMAP_S30_S33_v0.2.md) | S30-S33 plan |
| [CONSTITUTION](CONSTITUTION/invariants/) | Proven invariants |

---

## Proven Invariants

| ID | Description | Status |
|----|-------------|--------|
| INV-HALT-1 | Local halt <50ms | ✓ 0.003ms |
| INV-HALT-2 | Cascade <500ms | ✓ 22.59ms |
| INV-CONTRACT-1 | Deterministic state | ✓ Hash match |
| INV-DATA-CANON | Single truth (River) | ✓ Enforced |

---

## Architecture

```
phoenix/
├── CONSTITUTION/       # The Law (invariants, roles, wiring)
├── contracts/          # Data & governance contracts
├── governance/         # GovernanceInterface, halt, telemetry
├── monitoring/         # Alerts, dashboard
├── execution/          # Position, broker, replay
├── cso/                # Chief Strategy Officer (knowledge, observer)
├── enrichment/         # Data enrichment layers (L1-L6)
├── dispatcher/         # Worker coordination
├── schemas/            # YAML schemas (beads, HPG, etc)
├── scripts/            # Utilities
├── tests/              # Test suite
└── docs/               # Documentation
```

---

## Development

```bash
# Install pre-commit hooks
pre-commit install

# Run linter
ruff check .

# Run type checker
mypy --strict governance/ execution/

# Run specific test
pytest tests/test_halt_latency.py -v
```

---

## Related

| Repo | Purpose |
|------|---------|
| God_Mode | Forge — governance patterns |
| nex | Legacy data pipeline |

---

*S29 BUILD_MAP locked. S30 LEARNING_LOOP next.*
