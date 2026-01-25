# Phoenix

**Status:** Sprint 26 in progress  
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

## Project Structure

```
phoenix/
├── contracts/           # Data & governance contracts
│   ├── ICT_DATA_CONTRACT.md
│   ├── GOVERNANCE_INTERFACE_CONTRACT.md
│   ├── truth_teller.py
│   └── mirror_markers.py
│
├── governance/          # GovernanceInterface implementation
│   ├── interface.py     # Abstract base class (all organs inherit)
│   ├── halt.py          # <50ms halt mechanism
│   ├── telemetry.py     # Quality reporting
│   ├── tokens.py        # T2 approval tokens
│   ├── types.py         # Enums, dataclasses
│   └── errors.py        # Error classification
│
├── cso/                 # Chief Strategy Officer (skeleton)
│   ├── contract.py      # CSOContract ABC
│   └── __init__.py
│
├── docs/                # Canonical documentation
│   ├── VISION_v4.md
│   ├── PHOENIX_MANIFESTO.md
│   ├── CONSTITUTION_AS_CODE.md
│   ├── COLD_START_STRATEGY.md
│   └── ...
│
├── CONSTITUTION/        # Constitutional architecture graph
│   ├── modules/
│   ├── seams/
│   ├── invariants/
│   └── ...
│
├── reports/             # Sprint reports & test results
│   ├── TRACK_B_REPORT.md
│   ├── TRACK_C_REPORT.md
│   └── ...
│
├── tests/               # Test suite
│   ├── test_halt_latency.py
│   ├── test_mirror.py
│   └── ...
│
├── CLAUDE.md            # Agent orientation
└── GEMINI.md            # Advisor context
```

---

## Sprint 26 Progress

| Track | Name | Status |
|-------|------|--------|
| A | River (Data Integrity) | COMPLETE |
| B | Governance Skeleton | COMPLETE |
| C | Oracle Foundation | COMPLETE |
| D | Hands (Execution) | PENDING |

### Proven Invariants

- **INV-HALT-1:** `request_halt() < 50ms` — Proven at 0.003ms p99
- **INV-CONTRACT-1:** Deterministic state machine — XOR test passed
- **INV-DATA-1:** Schema locked — 472 columns, hash `b848ffe506fd3fff`

---

## Founding Commit

```
Phoenix founded — Schema Lockdown complete (Sprint 26 Track A Day 0.5)
```

---

## Related Repositories

| Repo | Purpose |
|------|---------|
| `God_Mode` | Forge — governance patterns, constitutional enforcement |
| `nex` | Legacy data pipeline (being subsumed) |

---

## Constitutional Anchors

1. **Human sovereignty over capital is absolute**
2. **Tier 2 (capital-affecting) always requires human gate**
3. **Forge amplifies judgment, never replaces it**
4. **No agent assumes operator reads code**

---

## Quick Start

```bash
# Clone
git clone https://github.com/SlimWojak/phoenix.git
cd phoenix

# Run tests (requires nex venv for data tests)
cd ~/nex && source .venv/bin/activate
pytest ~/phoenix/tests/ -v

# Verify governance halt latency
python -c "from phoenix.governance import HaltSignal; import time; h=HaltSignal(); t=time.perf_counter(); h.set(); print(f'{(time.perf_counter()-t)*1000:.3f}ms')"
```

---

*Sprint 26 — Foundation Proof*
