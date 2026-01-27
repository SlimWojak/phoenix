# Phoenix

**Status:** S31 COMPLETE | S32 EXECUTION_PATH next
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
| S29 | BUILD_MAP | ✓ Complete |
| S30 | LEARNING_LOOP | ✓ Complete |
| S31 | SIGNAL_AND_DECAY | ✓ Complete |
| S32 | EXECUTION_PATH | Next |

### S31 Delivered: SIGNAL_AND_DECAY
- CSO: Multi-pair setup detection with ICT structures
- Signalman: Multi-signal decay detection + ONE-WAY-KILL
- Autopsy: Post-trade analysis with LLM fallback
- Telegram: Throttled notification plane
- Lens: File-based Claude response injection
- State Anchor: T2 intent freshness validation

### S32 Focus: EXECUTION_PATH
- IBKR connector (CSE → real execution)
- Position sizing (Kelly, fractional)
- Shadow → Live promotion gate
- Vibe monitoring (market regime)

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
| [SPRINT_STATUS](docs/SPRINT_STATUS.md) | Current sprint status |
| [CONSTITUTION](CONSTITUTION/invariants/) | Proven invariants |

---

## Proven Invariants (S30 + S31)

| ID | Description | Status |
|----|-------------|--------|
| **Halt** | | |
| INV-HALT-1 | Local halt <50ms | ✓ 0.003ms |
| INV-HALT-2 | Cascade <500ms | ✓ 22.59ms |
| **Data** | | |
| INV-CONTRACT-1 | Deterministic state | ✓ Hash match |
| INV-DATA-CANON | Single truth (River) | ✓ Enforced |
| **Hunt** | | |
| INV-HUNT-HPG-1 | Valid HPG schema | ✓ BUNNY |
| INV-HUNT-DET-1 | Deterministic variations | ✓ BUNNY |
| INV-HUNT-CAP-1 | Max 50 variations | ✓ BUNNY |
| **Athena** | | |
| INV-ATHENA-RO-1 | Read-only queries | ✓ BUNNY |
| INV-ATHENA-CAP-1 | Max 100 rows | ✓ BUNNY |
| **CSO** | | |
| INV-CSO-CORE-1 | Immutable core logic | ✓ BUNNY |
| INV-CSO-CAL-1 | Shadow on param change | ✓ BUNNY |
| INV-CSO-6PAIR-1 | All 6 pairs scanned | ✓ BUNNY |
| **Signalman** | | |
| INV-SIGNALMAN-MULTI-1 | Multi-signal decay | ✓ BUNNY |
| INV-SIGNALMAN-COLD-1 | No false alerts cold start | ✓ BUNNY |
| INV-STATE-ANCHOR-1 | Valid state hash | ✓ BUNNY |
| **Autopsy** | | |
| INV-AUTOPSY-ASYNC-1 | Non-blocking | ✓ BUNNY |
| INV-AUTOPSY-FALLBACK-1 | Rule-based fallback | ✓ BUNNY |
| **Notification** | | |
| INV-ALERT-THROTTLE-1 | Max 10/hour except HALT | ✓ BUNNY |
| INV-LENS-1 | Kill-switchable | ✓ BUNNY |

**BUNNY S30:** 19/19 PASS
**BUNNY S31:** 20/20 PASS

---

## Architecture

```
phoenix/
├── CONSTITUTION/       # The Law (invariants, roles, wiring)
├── contracts/          # Data & governance contracts
├── governance/         # GovernanceInterface, halt, telemetry
├── monitoring/         # Signalman, KillManager, StateAnchor
├── execution/          # Position, broker, replay
├── cso/                # Chief Strategy Officer (structure detection)
├── analysis/           # Autopsy, LearningExtractor
├── notification/       # Telegram, AlertAggregator
├── lens/               # ResponseWriter (Claude injection)
├── shadow/             # Paper trading engine
├── memory/             # BeadStore, Athena
├── lab/                # Hunt, HPGParser, Backtester
├── enrichment/         # Data enrichment layers (L1-L6)
├── dispatcher/         # Worker coordination
├── schemas/            # YAML schemas (beads, HPG, CSE, etc)
├── config/             # CSO params, Telegram params
├── responses/          # Lens output files
├── reports/            # BUNNY reports
├── scripts/            # Utilities
├── tests/              # Test suite (unit, integration, chaos)
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

# Run integration tests
pytest tests/integration/ -v

# Run BUNNY chaos tests
pytest tests/chaos/ -v
```

---

## Test Suites

| Suite | Location | Purpose |
|-------|----------|---------|
| Unit | `tests/unit/` | Component tests |
| Integration | `tests/integration/` | E2E pipeline tests |
| Chaos | `tests/chaos/` | BUNNY attack vectors |

---

## Related

| Repo | Purpose |
|------|---------|
| God_Mode | Forge — governance patterns |
| nex | Legacy data pipeline |

---

*S31 SIGNAL_AND_DECAY complete. S32 EXECUTION_PATH next.*
