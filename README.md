# Phoenix

**Status:** S34 COMPLETE | S33 Phase 2 BLOCKED (Olya-dependent)
**Founded:** 2026-01-24

---

## What Is Phoenix

Phoenix is the constitutional trading system built on God_Mode governance.

```
God_Mode (Forge) = The OS — governance patterns, constitutional enforcement
Phoenix (App)    = The Trading System — River, CSO, Execution
```

**Constitutional Anchor:** Human sovereignty over capital is absolute.

**Key Insight (S34):**
> "Truth before UI. UI freedom is earned by state discipline."

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
| S33 P2 | FIRST_BLOOD UX Validation | Blocked (Olya) |
| S34 | OPERATIONAL_FINISHING | ✓ Complete |

### S34 Delivered: OPERATIONAL_FINISHING

**Theme:** "Finish plumbing, not brain"

**Tracks:**
- **D1:** File Seam Plumbing — Watcher daemon, Lens injection
- **D2:** Mock Oracle Pipeline — 5-drawer gate → CSE validation
- **D3:** Orientation Bead — Machine-verifiable system checksum
- **D4:** Surface Renderer — Truth-first UI (menu bar widget)

**Key Patterns Proven:**
- "Checksum, not briefing" — Orientation defeats session amnesia
- "Contract before integration" — Mock-first validation
- "Projection, not participation" — UI subordinate to state

**Exit Gate:** All 4 tracks green, 18 new invariants, 13 chaos vectors.

See: `docs/PHOENIX_MANIFEST.md` for system topology.

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
python drills/d1_verification.py
python drills/d3_negative_test.py  # THE KILL TEST
python drills/d4_verification.py

# 5. Run menu bar widget (macOS)
python widget/menu_bar.py
```

---

## Key Docs

| Doc | Purpose |
|-----|---------|
| [PHOENIX_MANIFEST](docs/PHOENIX_MANIFEST.md) | System topology (M2M bootstrap) |
| [SPRINT_STATUS](docs/SPRINT_STATUS.md) | Current sprint status |
| [S34_BUILD_MAP](docs/build_docs/S34_BUILD_MAP_v0.2.md) | S34 canonical plan |
| [CONSTITUTION](CONSTITUTION/invariants/) | Proven invariants |

---

## Proven Invariants (Cumulative: 52+)

### Halt & Governance
| ID | Description | Status |
|----|-------------|--------|
| INV-HALT-1 | Local halt <50ms | ✓ 0.15ms |
| INV-HALT-2 | Cascade <500ms | ✓ 22ms |
| INV-T2-TOKEN-1 | Single-use, 5min expiry | ✓ |
| INV-T2-GATE-1 | No order without token | ✓ |

### File Seam (S34 D1)
| ID | Description | Status |
|----|-------------|--------|
| INV-D1-WATCHER-1 | Exactly-once processing | ✓ |
| INV-D1-WATCHER-IMMUTABLE-1 | No payload modification | ✓ |
| INV-D1-LENS-1 | ≤50 tokens context cost | ✓ 17 tokens |
| INV-D1-HALT-PRIORITY-1 | HALT bypasses queue | ✓ |

### CSO Contract (S34 D2)
| ID | Description | Status |
|----|-------------|--------|
| INV-D2-FORMAT-1 | Mock == production schema | ✓ |
| INV-D2-TRACEABLE-1 | Refs resolvable | ✓ |
| INV-D2-NO-INTELLIGENCE-1 | Zero market logic | ✓ |
| INV-D2-NO-COMPOSITION-1 | Whitelist only | ✓ |

### Orientation Bead (S34 D3)
| ID | Description | Status |
|----|-------------|--------|
| INV-D3-CHECKSUM-1 | Machine-verifiable, no prose | ✓ |
| INV-D3-CROSS-CHECK-1 | Every field verifiable | ✓ |
| INV-D3-CORRUPTION-1 | Corruption → STATE_CONFLICT | ✓ 5/5 |
| INV-D3-NO-DERIVED-1 | No interpreted fields | ✓ |

### Surface Renderer (S34 D4)
| ID | Description | Status |
|----|-------------|--------|
| INV-D4-GLANCEABLE-1 | Update <100ms | ✓ 0.79ms |
| INV-D4-ACCURATE-1 | Matches actual state | ✓ |
| INV-D4-NO-DERIVATION-1 | Verbatim fields only | ✓ |
| INV-D4-EPHEMERAL-1 | No local persistence | ✓ |

### IBKR (S33)
| ID | Description | Status |
|----|-------------|--------|
| INV-IBKR-PAPER-GUARD-1 | Live requires explicit enable | ✓ |
| INV-IBKR-ACCOUNT-CHECK-1 | Account matches mode | ✓ |

---

## BUNNY Chaos Validation

| Sprint | Vectors | Status | Report |
|--------|---------|--------|--------|
| S30 | 19 | ✓ PASS | `reports/BUNNY_REPORT_S30.md` |
| S31 | 20 | ✓ PASS | `reports/BUNNY_REPORT_S31.md` |
| S32 | 17 | ✓ PASS | `reports/BUNNY_REPORT_S32.md` |
| S33 P1 | 15 | ✓ PASS | `reports/BUNNY_REPORT_S33_P1.md` |
| S34 | 13 | ✓ PASS | `reports/S34_COMPLETION_REPORT.md` |
| **Total** | **84** | | |

---

## Architecture

```
phoenix/
├── CONSTITUTION/       # The Law (invariants, roles, wiring)
├── contracts/          # Data & governance contracts
├── governance/         # GovernanceInterface, halt, telemetry
├── monitoring/         # Signalman, KillManager, StateAnchor
│   └── ops/            # Heartbeat, semantic health
├── execution/          # Position lifecycle, reconciliation
├── brokers/ibkr/       # IBKR connector with paper guards
├── cso/                # CSO scanner + consumer (S34)
├── approval/           # T2 evidence display (S34 D2)
├── orientation/        # Orientation bead system (S34 D3)
├── widget/             # Surface renderer (S34 D4)
├── daemons/            # File seam spine (S34 D1)
│   ├── watcher.py      # Intent routing
│   ├── lens.py         # Response injection
│   └── routing.py      # Intent dispatch
├── mocks/              # Mock CSE generator
├── schemas/            # YAML schemas (beads, CSE, orientation)
├── state/              # Runtime state (orientation.yaml)
├── intents/            # File seam input
├── responses/          # File seam output
├── drills/             # Verification scripts
├── reports/            # Sprint completion reports
└── docs/
    ├── build_docs/     # Sprint build maps
    ├── explorations/   # Future fuel (S35+)
    └── runbooks/       # Operational runbooks (RB-001 to RB-008)
```

---

## File Seam (S34)

```
Claude ──writes──▶ /intents/incoming/intent.yaml
                          │
                          ▼
                     WATCHER ──routes──▶ Workers
                          │
                          ▼
                     /responses/*.md
                          │
                          ▼
                       LENS ──injects──▶ Claude
```

---

## Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install rumps  # macOS menu bar (optional)

# Run linter
ruff check .

# Run specific drill
python drills/d3_negative_test.py  # THE KILL TEST

# Run menu bar widget
python widget/menu_bar.py
```

---

## Related

| Repo | Purpose |
|------|---------|
| God_Mode | Forge — governance patterns |
| nex | Legacy data pipeline (reference) |

---

## S35+ Fuel (Dormant)

- **S35:** CSO Harness — Evaluation engine for 5-drawer gates
- **S36:** Dynamic Workflow Entry Forge — HUD overlay, Pilot whisperer

See: `docs/explorations/` for frontier patterns (Yegge beads, Willison datasette, banteg minimalism).

---

*S34 OPERATIONAL_FINISHING complete. Truth before UI. Phoenix rises.*
