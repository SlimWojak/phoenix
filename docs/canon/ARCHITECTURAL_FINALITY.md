# ARCHITECTURAL_FINALITY.md — Path to WARBOAR v0.1

**Sprint**: S42 COMPLETE → S43-S52 ROADMAP LOCKED
**Date**: 2026-01-31
**Status**: UNFREEZE FOR v0.1 PATH | S43 ACTIVE

---

## Purpose

This document marks the architectural state after S42 and the canonical path to WARBOAR v0.1.

**S42 Delivered**:
- **Observable** (phoenix_status, health FSM, alerts)
- **Testable** (1465+ passing tests, 28 documented xfails)
- **Recoverable** (failure playbook, chaos vectors proven)
- **Documented** (operator instructions, CSO production-ready)

**S43-S52 Path**: 10 sprints to production-standard software.

**Key Invariant**: `INV-NO-CORE-REWRITES-POST-S44` — After live validation, only tightening/surfacing/governance. No architectural rewrites.

---

## Frozen Architecture

### Core Modules (Immutable)

```
phoenix/
├── governance/          # INV-*, halt, health FSM
├── cso/                 # Strategy detection (INV-CSO-CORE-1)
├── execution/           # Intent flow, halt gates
├── narrator/            # Guard dog, templates, surface
├── notification/        # Alert taxonomy, Telegram
├── river/               # Data (+ synthetic fallback)
├── enrichment/          # L1-L5 layers
└── cli/                 # phoenix_status
```

### Invariants Locked

| ID | Description | Enforcement |
|----|-------------|-------------|
| INV-HALT-1 | Halt response < 50ms | governance/halt.py |
| INV-CSO-CORE-1 | Strategy logic immutable | cso/strategy_core.py |
| INV-NARRATOR-1 | No recommendation, suggest, should | narrator/renderer.py |
| INV-NARRATOR-2 | FACTS_ONLY banner always present | narrator/renderer.py |
| INV-SLM-NARRATOR-GATE | All output validated | narrator/renderer.py |
| INV-OBSERVE-NO-INTERPRETATION | Facts only in status | cli/phoenix_status.py |
| INV-SYNTH-DETERMINISM | Same inputs → same outputs | river/synthetic_river.py |

### Test Suite Locked

```yaml
tests:
  total: 1502
  passed: 1465
  xfailed: 28 (documented, strict)
  errors: 7 (setup fixtures)

xfail_cap: 75 (5%)
actual_xfail: 28 (1.9%)
```

### Chaos Vectors Proven

| ID | Vector | Status |
|----|--------|--------|
| CV-S42-01 | river_ingestion_killed | PASS |
| CV-S42-02 | ibkr_rapid_reconnect_loop | PASS |
| CV-S42-03 | narrator_heresy_injection | PASS |
| CV-S42-04 | multi_degrade_cascade | PASS |
| CV-S42-05 | state_hash_stale_approval | PASS |
| CV-S42-06 | semantic_data_poison | PASS |

---

## What's Allowed Post-S42

### Allowed (Without Unfreeze)

1. **Bug fixes** - Fix existing behavior, don't add new
2. **Calibration** - Tune thresholds, params, timeouts
3. **Documentation** - Add/update docs
4. **Test additions** - New tests for existing behavior
5. **XFAIL cleanup** - Fix xfailed tests, reduce count

### Requires Unfreeze

1. **New invariants** - Must update this document
2. **New modules** - Must have exit gates
3. **Schema changes** - Must update schema hash
4. **API changes** - Must update affected tests
5. **New features** - Must have sprint brief

---

## Tech Debt Summary

See `docs/TECH_DEBT.md` for full register.

### Critical (Fix in S43)

| Item | Impact | Notes |
|------|--------|-------|
| River 2.8d stale | High | Data source reliability |
| auto_fix patterns | Medium | Audit enrichment layers |
| Schema drift | Medium | Update or fix enrichment |

### Low Priority (Parked)

| Item | Notes |
|------|-------|
| Telegram API tests | Need complete rewrite |
| Mirror test fixtures | Parquet file issues |
| MCP token budget | 57 vs 50 limit |

---

## S42 Deliverables

### Track B: Failure Rehearsal ✅

```
drills/s42_failure_playbook.py
- 6 chaos vectors implemented
- Exit gates B1-B3 PASS
- No alert storms
- No silent failures
```

### Track C: Tech Debt Burn ✅

```
Tests fixed: 79
Tests XFAILed: 28
Final state: 0 failures
```

### Track D: River Completion ✅

```
river/synthetic_river.py
- Deterministic mock data
- All 6 pairs supported
- Works offline
```

### Track E: Observability ✅

```
cli/phoenix_status.py
- One command shows state
- 70ms runtime (< 2s gate)
- INV-OBSERVE-NO-INTERPRETATION enforced
```

### Track F: Documentation ✅

```
This file (ARCHITECTURAL_FINALITY.md)
docs/TECH_DEBT.md
docs/S42_FAILURE_TRIAGE.md
```

---

## Unfreeze Protocol

To unfreeze for new development:

1. Create sprint brief with explicit scope
2. Update this document with new invariants
3. Get CTO approval
4. Run full test suite before/after
5. Update tech debt register

---

## S43-S52 Roadmap Summary

```yaml
total_sprints: 10
estimated_timeline: 5-7 weeks

S43: QUICK_WINS — Developer velocity (pytest parallel, config, narrator)
S44: LIVE_VALIDATION — IBKR paper, 48h soak, chaos replay
S45: RESEARCH_UX — IDEA → HUNT → CFP → DECIDE journey
S46: LEASE_DESIGN — Schema, bounds, expiry (design only)
S47: LEASE_IMPLEMENTATION — Interpreter, revoke, halt integration
S48: HUD_SURFACE — Widget evolution, daily briefing
S49: DMG_PACKAGING — One-click install, first-run wizard
S50: RUNBOOKS_CALIBRATION — All degraded states, CSO prep
S51: PRO_FLOURISHES — Sound/haptics, OINK easter eggs
S52: WARBOAR_SEAL — Final freeze, handover ceremony
```

### New Invariants (S43-S52)

| ID | Sprint | Rule |
|----|--------|------|
| INV-NO-CORE-REWRITES-POST-S44 | Global | No architectural rewrites after live validation |
| INV-RESEARCH-RAW-DEFAULT | S45 | Raw table default, human summary opt-in |
| INV-HALT-OVERRIDES-LEASE | S47 | Halt signal overrides lease bounds (<50ms) |

### S52 Exit Gate (WARBOAR v0.1)

```yaml
final_bunny_nuke:
  rule: "ALL xfails must pass or be explicitly waived by G before freeze"
  rationale: "No hidden xfails ship rotten"
```

---

## Certification

```
S42 COMPLETE
S43-S52 ROADMAP LOCKED
Date: 2026-01-31
Tests: 1465 passing, 28 xfailed
Path to v0.1: 10 sprints, 5-7 weeks
```

---

*Prove it works. Make it visible. Make it installable. Make it delightful. Ship it.* 🐗🔥
