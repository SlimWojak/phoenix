# Phoenix / WarBoar

**Status:** S42 COMPLETE | S43-S52 PATH LOCKED → WARBOAR v0.1
**Founded:** 2026-01-24
**S35-S42 Block:** COMPLETE (Constitutional Ceiling + Sleep-Safe + WarBoar + Trust Closure)
**Current:** S43 QUICK_WINS (active)
**Target:** WARBOAR v0.1 (10 sprints, 5-7 weeks)
**Tests:** 1465 passing (28 xfailed) | **Invariants:** 95+ proven | **Chaos Vectors:** 224 handled

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

> "No scalar scores. No rankings. No verdicts. Ever."

---

## S35-S41 Complete — WarBoar Certified

| Sprint | Codename | Tests | Key Invariant |
|--------|----------|-------|---------------|
| S35 | CFP | 62 | INV-ATTR-NO-CAUSAL |
| S36 | CSO | 45 | INV-NO-GRADE-RECONSTRUCTION |
| S37 | ATHENA | 51 | INV-ATTR-PROVENANCE |
| S38 | HUNT | 69 | INV-HUNT-NO-SURVIVOR-RANKING |
| S39 | VALIDATION | 109 | INV-SCALAR-BAN |
| S40 | SLEEP_SAFE | 312 | 20 invariants, 15 chaos vectors |
| **S41** | **WARBOAR** | **195** | **6 invariants, 20 chaos vectors, Live Gateway** |
| **S42** | **TRUST_CLOSURE** | **CSO** | **Gate glossary, health file, operator docs** |
| **TOTAL** | | **1465+** | **95+ proven, 224 chaos vectors** |

**What This Means:**
- **NEX died saying:** "Strategy Stability Index: 78/100"
- **Phoenix says:** "Walk-forward delta: +0.3 Sharpe. Monte Carlo 95th DD: -12%. You interpret."

See: `docs/DEFINITIVE_FATE.yaml` for complete capability mapping.

---

## Current Status

| Sprint | Name | Status |
|--------|------|--------|
| S28-S31 | Foundation | ✓ Complete |
| S32 | EXECUTION_PATH | ✓ Complete |
| S33 P1 | FIRST_BLOOD Infrastructure | ✓ Complete |
| S33 P2 | FIRST_BLOOD UX Validation | Blocked (Olya) |
| S34 | OPERATIONAL_FINISHING | ✓ Complete |
| S35 | CFP (Conditional Fact Projector) | ✓ **Complete** (62 tests) |
| S36 | CSO Harness | ✓ **Complete** (45 tests) |
| S37 | Memory Discipline | ✓ **Complete** (51 tests) |
| S38 | Hunt Infrastructure | ✓ **Complete** (69 tests) |
| S39 | Research Validation | ✓ **Complete** (109 tests) |
| S40 | Sleep-Safe Resilience | ✓ **Complete** (312 tests) |
| **S41** | **WARBOAR_AWAKENS** | ✓ **Complete** (195 tests) **SEALED** |
| S42 | TBD | PLANNING |

### Key Invariants Proven (S35-S40)

**S35-S39 (Constitutional Ceiling):**
- **INV-ATTR-NO-CAUSAL:** No "causes", no "leads to" — conditional facts only
- **INV-NO-GRADE-RECONSTRUCTION:** No A/B/C/D/F grades — gate status only
- **INV-ATTR-PROVENANCE:** Full provenance on all outputs
- **INV-HUNT-NO-SURVIVOR-RANKING:** No "best performer" rankings
- **INV-SCALAR-BAN:** No composite scores (0-100) — decomposed factors only
- **INV-NO-AGGREGATE-SCALAR:** No avg_* fields — return full arrays

**S40 (Sleep-Safe):**
- **INV-CIRCUIT-1/2:** Circuit breaker FSM (CLOSED→OPEN→HALF_OPEN)
- **INV-HEALTH-1/2:** Health state machine (HEALTHY→DEGRADED→CRITICAL→HALTED)
- **INV-IBKR-FLAKEY-1/2/3:** Heartbeat monitoring, supervisor survival
- **INV-IBKR-DEGRADE-1/2:** Graceful degradation cascade (T2→T1→T0)
- **INV-HOOK-1/2/3/4:** Constitutional enforcement at commit + runtime
- **INV-NARRATOR-1/2/3:** Facts-only projection (no synthesis)

**S41 (WarBoar):**
- **INV-SLM-READONLY-1:** SLM output cannot mutate state
- **INV-SLM-NO-CREATE-1:** SLM cannot create new information
- **INV-SLM-CLASSIFICATION-ONLY-1:** Output is classification, not decision
- **INV-SLM-BANNED-WORDS-1:** SLM detects all banned categories
- **INV-ALERT-TAXONOMY-1/2:** Alerts use defined categories and severity enum
- **Live Gateway Validated:** Real IBKR connection (paper mode)

See: `docs/SPRINT_ROADMAP.md` for full detail.

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

## Proven Invariants (Cumulative: 69+ proven)

### Foundation (S28-S34)
| ID | Description | Status |
|----|-------------|--------|
| INV-HALT-1 | Local halt <50ms | ✓ 0.15ms |
| INV-T2-TOKEN-1 | Single-use, 5min expiry | ✓ |
| INV-D1-WATCHER-1 | Exactly-once processing | ✓ |
| INV-D3-CORRUPTION-1 | Corruption → STATE_CONFLICT | ✓ 5/5 |
| INV-D4-NO-DERIVATION-1 | Verbatim fields only | ✓ |
| INV-IBKR-PAPER-GUARD-1 | Live requires explicit enable | ✓ |

### S35-S39 Invariants (ALL PROVEN)
| ID | Description | Sprint | Status |
|----|-------------|--------|--------|
| INV-ATTR-NO-CAUSAL | No causal claims | S35 | ✓ |
| INV-ATTR-PROVENANCE | query + hash + bead_id | S35 | ✓ |
| INV-NO-UNSOLICITED | System never proposes | S36 | ✓ |
| INV-HARNESS-1 | Gate status only, no grades | S36 | ✓ |
| INV-HUNT-EXHAUSTIVE | Compute ALL variants, no selection | S38 | ✓ |
| INV-SCALAR-BAN | No composite scores (0-100) | S39 | ✓ |
| INV-NO-AGGREGATE-SCALAR | No avg_* fields | S39 | ✓ |
| INV-NEUTRAL-ADJECTIVES | No evaluative words | S39 | ✓ |
| INV-VISUAL-PARITY | No color metadata | S39 | ✓ |
| INV-NO-IMPLICIT-VERDICT | Mandatory disclaimers | S39 | ✓ |

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
| S35 | 21 | ✓ PASS |
| S36 | 18 | ✓ PASS |
| S37 | 15 | ✓ PASS |
| S38 | 23 | ✓ PASS |
| S39 | 28 | ✓ PASS |
| S40 | 15 | ✓ PASS |
| **S41** | **20** | **✓ PASS** |
| **Total** | **224** | |

---

## Architecture

```
phoenix/
├── CONSTITUTION/       # The Law (invariants, roles, wiring)
├── governance/         # Halt, T2 tokens, telemetry
├── brokers/ibkr/       # IBKR connector with paper guards
├── cso/                # CSO scanner + consumer (S36)
├── cfp/                # Conditional Fact Projector (S35)
├── athena/             # Memory discipline (S37)
├── hunt/               # Exhaustive grid compute (S38)
├── validation/         # Research validation suite (S39)
├── orientation/        # Orientation bead system (S34 D3)
├── widget/             # Surface renderer (S34 D4)
├── daemons/            # File seam spine (S34 D1)
├── schemas/            # YAML schemas (beads, CSE, orientation)
├── state/              # Runtime state (orientation.yaml)
├── drills/             # Verification scripts
├── reports/            # Sprint completion reports
├── tests/
│   ├── test_validation/    # 81 validation tests
│   └── chaos/              # 28 BUNNY vectors
└── docs/
    ├── DEFINITIVE_FATE.yaml  # NEX→Phoenix fate table (61 capabilities)
    ├── SPRINT_ROADMAP.md     # S35-S39 roadmap (COMPLETE)
    ├── PHOENIX_MANIFEST.md   # System topology
    ├── PHOENIX_MANIFESTO.md  # Vision document
    ├── build_docs/           # Sprint build maps (S29-S39)
    └── runbooks/             # Operational runbooks (RB-001 to RB-008)
```

---

## Sprint Roadmap Summary

| Sprint | Theme | Key Deliverable | Status |
|--------|-------|-----------------|--------|
| S35 | CFP | Conditional facts with provenance | ✓ COMPLETE |
| S36 | CSO Harness | Gate status per pair (facts, not grades) | ✓ COMPLETE |
| S37 | Memory Discipline | CLAIM/FACT/CONFLICT beads | ✓ COMPLETE |
| S38 | Hunt Infrastructure | Exhaustive variant computation | ✓ COMPLETE |
| S39 | Research Validation | Decomposed outputs, no viability scores | ✓ COMPLETE |
| S40+ | Carpark | Multi-agent, self-healing | DORMANT |

---

## Related

| Repo | Purpose |
|------|---------|
| God_Mode | Forge — governance patterns |
| nex | Legacy data pipeline (reference) |

---

*S35-S41 COMPLETE. Human frames, machine computes. Human sleeps.*
*No scalar scores. No rankings. No verdicts. Ever.*
*Ceiling set. Floor holds. Guard dog armed. Live gateway validated. 🐗🔥*
