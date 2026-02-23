# SPRINT DEPENDENCY MAP

**Document:** SPRINT_DEPENDENCY_MAP.md  
**Purpose:** Critical path visualization and sprint dependencies  
**Target:** S29-S33 (Cognitive Foundation → First Blood)

---

## Critical Path Diagram

```
                              ┌─────────────────────────────────────────┐
                              │  S29: COGNITIVE_FOUNDATION              │
                              │  "The thinking partner comes alive"     │
                              │                                         │
                              │  MUST COMPLETE:                         │
                              │  • File seam (intent.yaml ↔ response)   │
                              │  • EXPLORE mode                         │
                              │  • Phoenix watcher + Inquisitor         │
                              │  • Morning Briefing worker              │
                              │  • Lens daemon                          │
                              └───────────────────┬─────────────────────┘
                                                  │
                                                  ▼
                              ┌─────────────────────────────────────────┐
                              │  S30: LEARNING_LOOP                     │
                              │  "The flywheel spins"                   │
                              │                                         │
                              │  MUST COMPLETE:                         │
                              │  • Hunt Engine (test my idea)           │
                              │  • Athena + Datasette (memory palace)   │
                              │  • Context checkpoint mechanics         │
                              │  • Cognitive momentum preservation      │
                              │  • Shadow boxing                        │
                              └───────────────────┬─────────────────────┘
                                                  │
                                                  ▼
                              ┌─────────────────────────────────────────┐
                              │  S31: SIGNAL_AND_DECAY                  │
                              │  "Phoenix watches"                      │
                              │                                         │
                              │  MUST COMPLETE:                         │
                              │  • Setup detection (what's setting up)  │
                              │  • Signalman + ONE-WAY-KILL             │
                              │  • Autopsy worker                       │
                              │  • State Hash validation                │
                              │  • Telegram notification plane          │
                              └───────────────────┬─────────────────────┘
                                                  │
                                                  ▼
                              ┌─────────────────────────────────────────┐
                              │  S32: EXECUTION_PATH                    │
                              │  "Real markets"                         │
                              │                                         │
                              │  MUST COMPLETE:                         │
                              │  • IBKR connector                       │
                              │  • T2 approval workflow                 │
                              │  • Position reconciliation              │
                              │  • Staging enforcement                  │
                              └───────────────────┬─────────────────────┘
                                                  │
                                                  ▼
                              ┌─────────────────────────────────────────┐
                              │  S33: FIRST_BLOOD                       │
                              │  "One pair, real money"                 │
                              │                                         │
                              │  MUST COMPLETE:                         │
                              │  • EUR/USD live trading                 │
                              │  • Incident procedures                  │
                              │  • 24/7 monitoring                      │
                              │  • N days live with real P&L            │
                              └─────────────────────────────────────────┘
```

---

## Parallel Tracks Within Sprints

### S29: COGNITIVE_FOUNDATION

```
TRACK A: File Seam ──────────────────────────────────────────────────►
         (intent.yaml schema, response.md schema, folder structure)
         
TRACK B: EXPLORE Mode ───────────────────────────────────────────────►
         (Claude Desktop configuration, mode classification)
         
TRACK C: Phoenix Watcher + Inquisitor ───────────────────────────────►
         (daemon, intent validation, doctrine gates)
         DEPENDS ON: Track A (file schema)
         
TRACK D: Morning Briefing Worker ────────────────────────────────────►
         (HIVE worker, cron trigger, briefing template)
         DEPENDS ON: Track C (watcher routing)
         
TRACK E: Lens Daemon ────────────────────────────────────────────────►
         (response injection mechanism)
         DEPENDS ON: Track A (response.md location)
```

**Parallelization:** A+B can run simultaneously. C needs A. D+E need C.

---

### S30: LEARNING_LOOP

```
TRACK A: Hunt Engine ────────────────────────────────────────────────►
         (hypothesis parsing, variant generation, local LLM eval)
         DEPENDS ON: S29 complete (file seam working)
         
TRACK B: Athena + Datasette ─────────────────────────────────────────►
         (bead storage, query interface, memory palace)
         CAN START: Immediately (independent infrastructure)
         
TRACK C: Context Checkpoint ─────────────────────────────────────────►
         (pressure detection, CONTEXT_SNAPSHOT bead, hot-load)
         DEPENDS ON: Track B (bead storage)
         
TRACK D: Cognitive Momentum ─────────────────────────────────────────►
         (snapshot schema extension, stance preservation)
         DEPENDS ON: Track C (checkpoint mechanics)
         
TRACK E: Shadow Boxing ──────────────────────────────────────────────►
         (paper trading harness, signal comparison)
         DEPENDS ON: Track A (Hunt for signals)
```

**Parallelization:** A+B can run simultaneously. C needs B. D needs C. E needs A.

---

### S31: SIGNAL_AND_DECAY

```
TRACK A: Setup Detection ────────────────────────────────────────────►
         (CSO continuous scan, quality scoring, push alerts)
         DEPENDS ON: S30 complete
         
TRACK B: Signalman + ONE-WAY-KILL ───────────────────────────────────►
         (drift detection, defensive mode trigger)
         CAN START: With Track A
         
TRACK C: Autopsy Worker ─────────────────────────────────────────────►
         (post-trade analysis, reasoning comparison)
         DEPENDS ON: S30 Athena (bead storage)
         
TRACK D: State Hash Validation ──────────────────────────────────────►
         (staleness detection, STATE_CONFLICT intercept)
         DEPENDS ON: Track A (active sessions to validate)
         
TRACK E: Telegram Notification ──────────────────────────────────────►
         (Takopi integration, alert routing)
         CAN START: Immediately (independent surface)
```

**Parallelization:** A+B+E can run simultaneously. C needs Athena. D needs A.

---

### S32: EXECUTION_PATH

```
TRACK A: IBKR Connector ─────────────────────────────────────────────►
         (API integration, order routing, fill tracking)
         DEPENDS ON: S31 complete (signals to execute)
         
TRACK B: T2 Approval Workflow ───────────────────────────────────────►
         (evidence display, approval token, state hash)
         DEPENDS ON: Track A (something to approve)
         
TRACK C: Position Reconciliation ────────────────────────────────────►
         (broker state vs Phoenix state, drift detection)
         DEPENDS ON: Track A (live positions)
         
TRACK D: Staging Enforcement ────────────────────────────────────────►
         (shadow → live pipeline, promotion gates)
         DEPENDS ON: S30 Shadow Boxing
```

**Parallelization:** A first, then B+C+D can run in parallel.

---

### S33: FIRST_BLOOD

```
TRACK A: EUR/USD Live ───────────────────────────────────────────────►
         (single pair, real capital, full workflow)
         DEPENDS ON: S32 complete
         
TRACK B: Incident Procedures ────────────────────────────────────────►
         (runbooks, escalation paths, recovery)
         CAN START: Parallel with Track A
         
TRACK C: 24/7 Monitoring ────────────────────────────────────────────►
         (overnight operation, alert routing, health checks)
         DEPENDS ON: Track A (something to monitor)
```

**Parallelization:** A+B can start together. C needs A running.

---

## Dependencies Summary

| Sprint | Hard Dependencies | Can Start Early |
|--------|-------------------|-----------------|
| S29 | None (foundation) | - |
| S30 | S29 file seam | Athena infrastructure |
| S31 | S30 Hunt + Athena | Telegram integration |
| S32 | S31 signals | Staging docs |
| S33 | S32 execution | Incident procedures |

---

## Critical Path Items

These items are on the critical path — delays here delay everything:

1. **S29: File Seam** — everything depends on intent.yaml ↔ response.md working
2. **S29: Phoenix Watcher** — no routing = no workers = no superpowers
3. **S30: Athena** — no memory = no learning loop = no flywheel
4. **S31: State Hash** — without this, stale execution risk exists
5. **S32: IBKR Connector** — no broker = no live trading

---

## Risk Mitigation

| Risk | Sprint | Mitigation |
|------|--------|------------|
| File seam latency too high | S29 | Benchmark early, have MCP fallback |
| Lens daemon complexity | S29 | Option A (single MCP tool) as fallback |
| Checkpoint feels disruptive | S30 | UX testing with Olya, iterate |
| Hunt generates too many variants | S30 | Hard caps enforced, test at limits |
| IBKR API issues | S32 | Paper trading mode as fallback |
| Signalman false positives | S31 | Tunable thresholds, manual override |

---

## Milestone Gates

| Milestone | Sprint | Gate Criteria |
|-----------|--------|---------------|
| **Thinking Partner Works** | S29 | Olya can EXPLORE + get briefing |
| **Flywheel Spins** | S30 | Hypothesis → test → learn → surface |
| **Phoenix Watches** | S31 | Decay detected, alerts sent |
| **Ready for Capital** | S32 | T2 workflow proven on paper |
| **Live Trading** | S33 | N days real P&L, no incidents |

---

## Time Estimates (Rough)

| Sprint | Estimated Duration | Notes |
|--------|-------------------|-------|
| S29 | 1-2 weeks | Foundation, can't rush |
| S30 | 2-3 weeks | Hunt + Athena are meaty |
| S31 | 1-2 weeks | Mostly integration |
| S32 | 2-3 weeks | Broker integration is fiddly |
| S33 | 2+ weeks | Live validation takes time |

**Total to First Blood:** ~8-12 weeks (conservative)

---

## Handoff Artifacts

Each sprint produces artifacts the next sprint consumes:

| Sprint | Produces | Consumed By |
|--------|----------|-------------|
| S29 | Working file seam, EXPLORE mode, briefing | S30 (Hunt uses file seam) |
| S30 | Hunt engine, Athena, checkpoint | S31 (signals need Hunt) |
| S31 | Setup detection, Signalman, Telegram | S32 (execution needs signals) |
| S32 | IBKR connector, T2 workflow | S33 (live needs execution) |
| S33 | Proven live system | S34+ (expansion) |

---

## Olya Integration Points

| Sprint | Olya Involvement |
|--------|------------------|
| S29 | Test EXPLORE feel, validate briefing format |
| S30 | Test Hunt UX, validate shadow boxing |
| S31 | Tune Signalman thresholds, validate alerts |
| S32 | Approve T2 workflow, test approval UX |
| S33 | Active trading, incident response |

**Key insight:** Olya's methodology wire (CSO calibration) runs PARALLEL to technical sprints. Her pace, not ours.

---

## Quick Reference: What Blocks What

```
S29 File Seam ────────► S30 Hunt
S29 Watcher ──────────► S30 All workers
S30 Athena ───────────► S30 Checkpoint
S30 Checkpoint ───────► S30 Momentum
S30 Hunt ─────────────► S30 Shadow Boxing
S30 Athena ───────────► S31 Autopsy
S31 Signals ──────────► S32 Execution
S32 IBKR ─────────────► S32 T2 Workflow
S32 Complete ─────────► S33 Live
```

---

**The critical path is clear. The parallel tracks are mapped. Execute.**
