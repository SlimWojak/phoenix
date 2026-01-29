# Phoenix

**Status:** S35 READY | S33 Phase 2 BLOCKED (Olya-dependent)
**Founded:** 2026-01-24

---

## What Is Phoenix

Phoenix is the constitutional trading system built on God_Mode governance.

```
God_Mode (Forge) = The OS — governance patterns, constitutional enforcement
Phoenix (App)    = The Trading System — River, CSO, Execution
```

**Constitutional Anchor:** Human sovereignty over capital is absolute.

**Core Doctrine:**
> "Human frames, machine computes. The system never proposes."

> "Truth before UI. UI freedom is earned by state discipline."

---

## Current Status

| Sprint | Name | Status |
|--------|------|--------|
| S28-S31 | Foundation | ✓ Complete |
| S32 | EXECUTION_PATH | ✓ Complete |
| S33 P1 | FIRST_BLOOD Infrastructure | ✓ Complete |
| S33 P2 | FIRST_BLOOD UX Validation | Blocked (Olya) |
| S34 | OPERATIONAL_FINISHING | ✓ Complete |
| **S35** | **CFP (Conditional Fact Projector)** | **READY** |
| S36 | CSO Harness | LOCKED |
| S37 | Memory Discipline | PLANNED |
| S38 | Hunt Infrastructure | PLANNED |
| S39 | Research Validation | PLANNED |

### S35 Target: CFP (Conditional Fact Projector)

**Theme:** "Where/when does performance concentrate?"

**Scope:**
- Lens schema (YAML: group_by, filter, agg)
- Query executor against River/beads
- Output schema (facts + provenance)
- Causal-ban enforcement
- Conflict display pattern

**Key Invariants:**
- INV-ATTR-CAUSAL-BAN: No causal claims; only conditional facts
- INV-ATTR-PROVENANCE: All outputs include query + hash + bead_id
- INV-ATTR-NO-RANKING: No ranking, no implied priority

See: `docs/SPRINT_ROADMAP.md` for full S35-S39 detail.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/SlimWojak/phoenix.git
cd phoenix

# 2. Setup venv
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Run tests
python -m pytest tests/ -v

# 4. Run S34 verification drills
python drills/d3_negative_test.py  # THE KILL TEST
python drills/d4_verification.py

# 5. Run menu bar widget (macOS)
python widget/menu_bar.py
```

---

## Key Docs

| Doc | Purpose |
|-----|---------|
| [DEFINITIVE_FATE](docs/DEFINITIVE_FATE.yaml) | NEX→Phoenix fate table (61 capabilities) |
| [SPRINT_ROADMAP](docs/SPRINT_ROADMAP.md) | S35-S39 detailed scope + invariants |
| [PHOENIX_MANIFEST](docs/PHOENIX_MANIFEST.md) | System topology (M2M bootstrap) |
| [PHOENIX_MANIFESTO](docs/PHOENIX_MANIFESTO.md) | Vision, characters, narrative culture |
| [CONSTITUTION](CONSTITUTION/invariants/) | Proven invariants |

---

## Proven Invariants (Cumulative: 52+ proven, 17 new defined)

### Foundation (S28-S34)
| ID | Description | Status |
|----|-------------|--------|
| INV-HALT-1 | Local halt <50ms | ✓ 0.15ms |
| INV-T2-TOKEN-1 | Single-use, 5min expiry | ✓ |
| INV-D1-WATCHER-1 | Exactly-once processing | ✓ |
| INV-D3-CORRUPTION-1 | Corruption → STATE_CONFLICT | ✓ 5/5 |
| INV-D4-NO-DERIVATION-1 | Verbatim fields only | ✓ |
| INV-IBKR-PAPER-GUARD-1 | Live requires explicit enable | ✓ |

### S35-S39 Target Invariants
| ID | Description | Sprint |
|----|-------------|--------|
| INV-ATTR-CAUSAL-BAN | No causal claims | S35 |
| INV-ATTR-PROVENANCE | query + hash + bead_id | S35 |
| INV-NO-UNSOLICITED | System never proposes | S36 |
| INV-HARNESS-1 | Gate status only, no grades | S36 |
| INV-HUNT-EXHAUSTIVE | Compute ALL variants, no selection | S38 |
| INV-SCALAR-BAN | No composite scores (0-100) | S39 |

Full list: `docs/DEFINITIVE_FATE.yaml` → invariants section

---

## BUNNY Chaos Validation

| Sprint | Vectors | Status |
|--------|---------|--------|
| S30 | 19 | ✓ PASS |
| S31 | 20 | ✓ PASS |
| S32 | 17 | ✓ PASS |
| S33 P1 | 15 | ✓ PASS |
| S34 | 13 | ✓ PASS |
| **Total** | **84** | |

---

## Architecture

```
phoenix/
├── CONSTITUTION/       # The Law (invariants, roles, wiring)
├── governance/         # Halt, T2 tokens, telemetry
├── brokers/ibkr/       # IBKR connector with paper guards
├── cso/                # CSO scanner + consumer
├── orientation/        # Orientation bead system (S34 D3)
├── widget/             # Surface renderer (S34 D4)
├── daemons/            # File seam spine (S34 D1)
├── schemas/            # YAML schemas (beads, CSE, orientation)
├── state/              # Runtime state (orientation.yaml)
├── drills/             # Verification scripts
├── reports/            # Sprint completion reports
└── docs/
    ├── DEFINITIVE_FATE.yaml  # NEX→Phoenix fate table
    ├── SPRINT_ROADMAP.md     # S35-S39 roadmap
    ├── PHOENIX_MANIFEST.md   # System topology
    ├── PHOENIX_MANIFESTO.md  # Vision document
    ├── build_docs/           # Sprint build maps
    └── runbooks/             # Operational runbooks (RB-001 to RB-008)
```

---

## Sprint Roadmap Summary

| Sprint | Theme | Key Deliverable |
|--------|-------|-----------------|
| S35 | CFP | Conditional facts with provenance |
| S36 | CSO Harness | Gate status per pair (facts, not grades) |
| S37 | Memory Discipline | CLAIM/FACT/CONFLICT beads |
| S38 | Hunt Infrastructure | Exhaustive variant computation |
| S39 | Research Validation | Decomposed outputs, no viability scores |
| S40+ | Carpark | Multi-agent, self-healing (dormant) |

---

## Related

| Repo | Purpose |
|------|---------|
| God_Mode | Forge — governance patterns |
| nex | Legacy data pipeline (reference) |

---

*S35 READY. Human frames, machine computes. Phoenix rises.*
