# Phoenix

**Status:** S33 Phase 1 COMPLETE | Phase 2 (UX validation) next
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
| S32 | EXECUTION_PATH | ✓ Complete |
| S33 P1 | FIRST_BLOOD Infrastructure | ✓ Complete |
| S33 P2 | FIRST_BLOOD UX Validation | Next |

### S33 Phase 1 Delivered: FIRST_BLOOD Infrastructure

**Tracks:**
- **Track A:** IBKR connection with paper guards (INV-IBKR-PAPER-GUARD-1)
- **Track B:** Monitoring + semantic health (30s heartbeat with jitter)
- **Track C:** 8 Runbooks (RB-001 through RB-008)
- **Track D:** Telegram real device validation
- **Track E:** Mock CSE generator for UX testing
- **Track G:** BUNNY Phase 1 (15/15 vectors)

**Exit Gate:** Infrastructure ready for UX testing.

### S33 Phase 2 Focus: UX Validation (Tomorrow)
- Claude Desktop UX testing with G
- Paper trade round-trip (3 trades minimum)
- RB-004 drill completion
- UX friction documentation

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

# 4. Run BUNNY chaos tests
python -m pytest ~/phoenix/tests/chaos/ -v
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

## Proven Invariants (S30 → S33 Cumulative)

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
| **T2 Workflow (S32)** | | |
| INV-T2-TOKEN-1 | Single-use, time-limited | ✓ BUNNY |
| INV-T2-GATE-1 | No order without token | ✓ BUNNY |
| INV-STALE-KILL-1 | >15min → STATE_CONFLICT | ✓ BUNNY |
| **Position Lifecycle (S32)** | | |
| INV-POSITION-SM-1 | Valid state transitions | ✓ BUNNY |
| INV-POSITION-SUBMITTED-TTL-1 | 60s timeout to STALLED | ✓ BUNNY |
| **Reconciliation (S32)** | | |
| INV-RECONCILE-READONLY-1 | Reconciler never mutates | ✓ BUNNY |
| INV-RECONCILE-ALERT-1 | Drift triggers alert | ✓ BUNNY |
| **Promotion (S32)** | | |
| INV-PROMOTION-SAFE-1 | Hard blocks on kill/stalled | ✓ BUNNY |
| INV-PROMOTION-SAFE-2 | One-way promotion | ✓ BUNNY |
| **IBKR (S33)** | | |
| INV-IBKR-PAPER-GUARD-1 | Live requires explicit enable | ✓ BUNNY |
| INV-IBKR-ACCOUNT-CHECK-1 | Account matches mode | ✓ BUNNY |
| INV-IBKR-RECONNECT-1 | Max 3 reconnect attempts | ✓ BUNNY |
| **Monitoring (S33)** | | |
| INV-OPS-HEARTBEAT-SEMANTIC-1 | Semantic health in heartbeat | ✓ BUNNY |
| INV-OPS-HEARTBEAT-30S-1 | 30s ±5s timing | ✓ BUNNY |

---

## BUNNY Chaos Validation

| Sprint | Vectors | Status | Report |
|--------|---------|--------|--------|
| S30 | 19 | ✓ PASS | `reports/BUNNY_REPORT_S30.md` |
| S31 | 20 | ✓ PASS | `reports/BUNNY_REPORT_S31.md` |
| S32 | 17 | ✓ PASS | `reports/BUNNY_REPORT_S32.md` |
| S33 P1 | 15 | ✓ PASS | `reports/BUNNY_REPORT_S33_P1.md` |
| **Total** | **71** | | |

---

## Architecture

```
phoenix/
├── CONSTITUTION/       # The Law (invariants, roles, wiring)
├── contracts/          # Data & governance contracts
├── governance/         # GovernanceInterface, halt, telemetry
├── monitoring/         # Signalman, KillManager, StateAnchor
│   └── ops/            # Heartbeat, semantic health (S33)
├── execution/          # Position lifecycle, reconciliation, promotion
├── brokers/            # IBKR connector with paper guards (S33)
│   └── ibkr/           # Config, real_client, session_bead
├── cso/                # Chief Strategy Officer (structure detection)
├── analysis/           # Autopsy, LearningExtractor
├── notification/       # Telegram, AlertAggregator
├── lens/               # ResponseWriter (Claude injection)
├── shadow/             # Paper trading engine
├── memory/             # BeadStore, Athena
├── lab/                # Hunt, HPGParser, Backtester
├── mocks/              # Mock CSE generator (S33)
├── enrichment/         # Data enrichment layers (L1-L6)
├── dispatcher/         # Worker coordination
├── schemas/            # YAML schemas (beads, HPG, CSE, etc)
├── config/             # CSO params, Telegram params
├── responses/          # Lens output files
├── reports/            # BUNNY reports
├── scripts/            # Utilities
├── tests/              # Test suite (unit, integration, chaos)
│   ├── unit/           # Component tests
│   ├── integration/    # E2E pipeline tests
│   ├── chaos/          # BUNNY attack vectors
│   └── notification/   # Telegram validation (S33)
└── docs/
    ├── build_docs/     # Sprint build maps, roadmaps
    └── runbooks/       # Operational runbooks (RB-001 through RB-008)
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
| Notification | `tests/notification/` | Telegram validation |

---

## Related

| Repo | Purpose |
|------|---------|
| God_Mode | Forge — governance patterns |
| nex | Legacy data pipeline |

---

*S33 Phase 1 Infrastructure complete. Phase 2 (UX validation) next.*
