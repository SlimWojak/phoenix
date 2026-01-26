# Phoenix

**Status:** Sprint 28 — STEEL_PIPES (Complete)
**Jurisdiction:** Sibling to God_Mode (Forge)
**Founded:** 2026-01-24

---

## What Is Phoenix

Phoenix is the first application built on the God_Mode governance framework.

```
God_Mode (Forge) = The OS — governance patterns, constitutional enforcement
Phoenix (App)    = The Trading System — River, CSO, Execution
```

**Founding Invariant:** The Forge remains the lawgiver, not the body.

---

## Current Sprint: S28 STEEL_PIPES

| Track | Name | Status |
|-------|------|--------|
| A | Chaos V3 (Regime Stress) | ✓ COMPLETE |
| B | Monitoring (Dashboard/Alerts) | ✓ COMPLETE |
| C | Execution Path (T0/T1/T2 Wiring) | ✓ COMPLETE |
| D | Consolidation (Docs/Constitution) | ✓ COMPLETE |

### Exit Gate Summary

| Gate | Criterion | Status |
|------|-----------|--------|
| Chaos V3 | 100% vectors pass | ✓ PASS |
| Dashboard | Renders with live data | ✓ PASS |
| Auto-Halt | >3 CRITICAL → halt | ✓ PASS |
| Determinism | Same replay = same hash | ✓ PASS |
| Constitution | Invariants populated | ✓ PASS |

---

## Architecture

```
phoenix/
├── CONSTITUTION/           # The Law
│   ├── invariants/         # 6 proven invariants
│   ├── roles/              # sovereign, cto, cso
│   └── wiring/             # halt propagation
│
├── contracts/              # Data & governance contracts
│   ├── ICT_DATA_CONTRACT.md
│   └── GOVERNANCE_INTERFACE_CONTRACT.md
│
├── governance/             # GovernanceInterface (Track B)
│   ├── interface.py        # ABC for all organs
│   ├── halt.py             # <50ms halt mechanism
│   ├── telemetry.py        # Quality reporting
│   └── types.py            # Tier enums
│
├── monitoring/             # Observability (S28.B)
│   ├── alerts.py           # Threshold + debounce + auto-halt
│   └── dashboard.py        # Web health view
│
├── execution/              # Execution path (S28.C)
│   ├── position.py         # Lifecycle state machine
│   ├── broker_stub.py      # Paper broker (P&L v0)
│   ├── replay.py           # Deterministic harness
│   └── intent.py           # Order intents
│
├── cso/                    # Chief Strategy Officer
│   ├── knowledge/          # 5-drawer methodology (59 signals)
│   ├── observer.py         # Passive observer
│   └── beads.py            # Decision artifacts
│
├── enrichment/             # Data enrichment (L1-L6)
│   └── layers/             # ICT marker calculation
│
├── dispatcher/             # Worker coordination
│   └── tmux_control.py     # TMUX C2
│
├── tests/                  # 60+ tests
│   ├── test_halt_*.py
│   ├── test_execution_path.py
│   ├── test_monitoring.py
│   └── chaos/
│
└── docs/                   # Sprint reports & docs
```

---

## Proven Invariants

| Invariant | Description | Proven Value |
|-----------|-------------|--------------|
| INV-HALT-1 | Local halt < 50ms | 0.003ms |
| INV-HALT-2 | Cascade < 500ms | 22.59ms |
| INV-CONTRACT-1 | Deterministic state | Hash match |
| INV-DATA-CANON | Single truth (River) | XOR == 0 |
| INV-GOV-HALT-BEFORE-ACTION | Halt-first pattern | Tests pass |
| INV-EXEC-LIFECYCLE-1 | Valid transitions | Enforced |

---

## Quick Start

```bash
# Clone
git clone https://github.com/SlimWojak/phoenix.git
cd phoenix

# Run tests (requires nex venv)
cd ~/nex && source .venv/bin/activate
python -m pytest ~/phoenix/tests/ -v

# Check halt latency
python -c "
from governance.halt import HaltSignal
import time
h = HaltSignal()
t = time.perf_counter()
h.set()
print(f'Halt latency: {(time.perf_counter()-t)*1000:.3f}ms')
"

# Run execution path tests
python tests/test_execution_path.py
```

---

## Fresh Session Bootstrap

**Load these files in order:**

1. `SKILL.md` — Communication standard
2. `CONSTITUTION/invariants/` — Proven laws
3. `contracts/ICT_DATA_CONTRACT.md` — Data schema
4. `docs/SPRINT_26.md` — Current sprint
5. `docs/ADVISOR_ORIENTATION.md` — Full bootstrap guide

---

## Constitutional Anchors

1. **Human sovereignty over capital is absolute**
2. **Tier 2 (capital-affecting) always requires human gate**
3. **Forge amplifies judgment, never replaces it**
4. **No agent assumes operator reads code**

---

## Related Repositories

| Repo | Purpose |
|------|---------|
| `God_Mode` | Forge — governance patterns |
| `nex` | Legacy data pipeline (being subsumed) |

---

*Sprint 28 — Steel Pipes Complete*
*OINK OINK.* 🐗🔥
