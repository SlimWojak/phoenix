# NEX AUDIT REPORT

**SPRINT**: S28.E
**MISSION**: NEX_SUBSUMPTION_ASSESSMENT
**DATE**: 2026-01-23
**VERDICT**: READY_TO_INTEGRATE

---

## SECTION 1: REPO MAP

### Directory Structure

```
~/echopeso/nex/
├── nex_os/                 # Operating System layer (639 files)
│   ├── mcp_tools/          # 48 MCP tool files (141 tools total)
│   ├── athena/             # Learning loop (Hunt experiments)
│   ├── memory/             # Fact store + semantic search
│   ├── intelligence/       # Gemma client, market context
│   ├── hunt/               # Hunt Engine (hypothesis testing)
│   ├── flywheel/           # Learning loop state machine
│   ├── cockpit/            # Dashboard components
│   ├── secretary/          # Logging, progress tracking
│   ├── agents/             # Agent configurations
│   ├── session/            # Session YAML files (~88)
│   └── skills/             # Operator skill definitions
│
├── nex_lab/                # Research Lab (801 files)
│   ├── backtest/           # Backtest runner infrastructure
│   ├── replay/             # Signal replay engine
│   ├── strategies/         # Strategy implementations
│   ├── athena/             # Lab experiment framework
│   ├── analyst/            # DeepSeek analyst integration
│   ├── regime_forecast/    # Gemma regime prediction
│   ├── methodology/        # ICT methodology logic
│   ├── tools/              # 40 tool files
│   └── reports/            # 453 report files
│
├── nex_arena/              # Live Execution (60 files)
│   ├── core/               # Executor, observation builder
│   ├── execution/          # Order executor, bracket manager
│   ├── positions/          # Position tracker, P&L calculator
│   ├── risk/               # Kill switch, drawdown monitor, news gate
│   ├── ibkr/               # IBKR connector, mock client
│   ├── strategies/         # Evaluator adapter, strategy manager
│   ├── monitoring/         # Health checker
│   └── safety/             # Error handler, position reconciler
│
└── meridian_gold/          # Enrichment specs (45 files)
    └── enrichment_specs/   # Layer 0-11 specifications
```

### Key Module Inventory

| Module | Location | Purpose |
|--------|----------|---------|
| **MCP Server** | `nex_os/mcp_server.py` | Tool server (141 tools) |
| **Athena OS** | `nex_os/athena/` | Hunt learning loop |
| **Athena Lab** | `nex_lab/athena/` | Lab experiment framework |
| **Memory Bus** | `nex_os/memory/` | Fact store + FAISS semantic |
| **Gemma Client** | `nex_os/intelligence/` | ICT analysis via Ollama/Google |
| **Hunt Engine** | `nex_os/hunt/` | Hypothesis → backtest → learn |
| **Flywheel** | `nex_os/flywheel/` | Learning phase state machine |
| **Backtest Runner** | `nex_lab/backtest/` | Quick backtest for Hunt |
| **Kill Switch** | `nex_arena/risk/kill_switch.py` | Emergency halt |
| **Strategy Evaluator** | `nex_lab/strategies/` | Signal grading |

---

## SECTION 2: SUPERPOWER INVENTORY

### Operator-Facing Capabilities

| Capability | Implementation | How It Served Olya | Phoenix Equivalent |
|------------|----------------|--------------------|--------------------|
| **Morning Briefing** | `aggregators_nex.py:nex_os_morning_briefing()` | Daily status summary: equity, P&L, positions, strategies, session, health | NONE — need to build |
| **"What's Setting Up?"** | `gemma_tools.py:nex_gemma_analyze()` | Real-time ICT analysis: setup quality, direction bias, key levels | CSO skeleton exists, needs Gemma |
| **Test My Idea** | `hunt_tools.py:nex_run_hunt_engine()` | Hypothesis → variations → backtest → survivors | NONE — need to build |
| **Backtest Engine** | `nex_lab/backtest/runner.py` | ICT strategy evaluation on historical data | NONE — need to subsume |
| **Multi-Pair Scan** | `gemma_tools.py:nex_gemma_scan_pairs()` | Scan 6 pairs for setup quality | NONE — need to build |
| **Memory/Learning** | `memory/athena_memory.py` | Remember facts, detect contradictions, recall | NONE — need to build |
| **Quick Status** | `mcp_tools/quick_status.py` | Fast system health check | `monitoring/dashboard.py` (partial) |
| **Kill Switch** | `nex_arena/risk/kill_switch.py` | Emergency halt all trading | `governance/halt.py` (proved <50ms) |
| **Regime Forecast** | `regime_forecast/forecast_gemma.py` | 4h regime probability prediction | NONE — need to build |
| **Session Tracking** | `session/*.yaml` | Conversation state persistence | Boardroom beads (partial) |

### The Flywheel Pattern

```
EXPLORE → VALIDATE → OPTIMIZE → PROMOTE → EXECUTE → LEARN → ACT
   ↑                                                          ↓
   └──────────────────────────────────────────────────────────┘
```

**NEX Implementation:**
- `flywheel_state.py` tracks phase
- Hunt Engine handles EXPLORE/VALIDATE
- Lab handles OPTIMIZE
- Arena handles EXECUTE
- Athena handles LEARN

**What Made It Feel Alive:**
1. Natural language → backtest via MCP tools
2. Immediate feedback (Hunt survivors)
3. Memory persistence (facts accumulate)
4. Morning briefings (daily discovery layer)
5. Conversational operation (no terminal needed)

---

## SECTION 3: SUBSUMPTION MATRIX

| Component | Status | Rationale | Integration Path |
|-----------|--------|-----------|------------------|
| **Kill Switch** | ✅ PORTABLE_AS_IS | Phoenix halt mechanism superior (0.003ms) | Use `governance/halt.py` |
| **Backtest Runner** | 🔄 REWRITE | Needs River integration, governance | Adapt to use River data + halt gates |
| **Hunt Engine** | 🔄 REWRITE | Core value, needs governance + River | `phoenix/lab/hunt.py` with halt respect |
| **Athena OS** | 🔄 REWRITE | Learning loop valuable, needs bead integration | `phoenix/memory/` with boardroom beads |
| **Memory System** | 🔄 REWRITE | Fact store good, needs River alignment | `phoenix/memory/athena.py` |
| **Gemma Client** | ✅ PORTABLE_AS_IS | Clean interface, no conflicts | `phoenix/intelligence/gemma.py` |
| **Morning Briefing** | 🔄 REWRITE | Token-efficient pattern good, needs Phoenix data | `phoenix/briefings/morning.py` |
| **MCP Tools** | ⚠️ PARTIAL | 58/141 working, 76 broken (missing kill_switch import) | Port working tools, fix imports |
| **Flywheel State** | ✅ PORTABLE_AS_IS | Simple state machine, no conflicts | `phoenix/flywheel/state.py` |
| **Strategy Evaluator** | 🔄 REWRITE | Core value, needs River + CSO integration | `phoenix/cso/evaluator.py` |
| **Signal Replay** | 🔄 REWRITE | Valuable for testing, needs River | `phoenix/lab/replay.py` |
| **Regime Forecast** | ⚠️ STUBBED | Mock data only, needs real implementation | Future work after Gemma |
| **Arena Executor** | ❌ OBSOLETE | Phoenix execution skeleton better designed | Use `execution/` instead |
| **Arena Risk** | 🔄 REWRITE | Good patterns, needs Phoenix governance | Port to `phoenix/execution/risk/` |
| **Arena IBKR** | 🔄 REWRITE | Broker integration needed, needs T2 gates | `phoenix/brokers/ibkr.py` |
| **Lab Analyst** | ✅ PORTABLE_AS_IS | DeepSeek integration clean | `phoenix/intelligence/analyst.py` |

### Summary

| Category | Count |
|----------|-------|
| ✅ PORTABLE_AS_IS | 5 |
| 🔄 REWRITE | 10 |
| ⚠️ PARTIAL/STUBBED | 2 |
| ❌ OBSOLETE | 1 |

---

## SECTION 4: INTEGRATION ARCHITECTURE

### Proposed Phoenix Structure

```
phoenix/
├── EXISTING (S28)
│   ├── governance/         # GovernanceInterface ✓
│   ├── execution/          # Position lifecycle ✓
│   ├── monitoring/         # Alerts + dashboard ✓
│   ├── cso/                # Knowledge + observer ✓
│   ├── enrichment/         # L1-L6 layers ✓
│   └── dispatcher/         # Worker coordination ✓
│
├── NEW (From NEX)
│   ├── lab/                # Research engine
│   │   ├── hunt.py         # Hunt Engine (from nex_os/hunt)
│   │   ├── backtest.py     # Backtest runner (from nex_lab/backtest)
│   │   └── replay.py       # Signal replay (from nex_lab/replay)
│   │
│   ├── memory/             # Athena memory
│   │   ├── athena.py       # Fact store (from nex_os/memory)
│   │   ├── semantic.py     # FAISS search
│   │   └── journal.py      # Hunt journal
│   │
│   ├── intelligence/       # Analysis engines
│   │   ├── gemma.py        # Gemma client (from nex_os/intelligence)
│   │   ├── analyst.py      # DeepSeek (from nex_lab/analyst)
│   │   └── market_context.py
│   │
│   ├── briefings/          # Operator summaries
│   │   ├── morning.py      # Morning brief (from aggregators)
│   │   └── status.py       # Quick status
│   │
│   ├── flywheel/           # Learning loop
│   │   └── state.py        # Phase tracking (from nex_os/flywheel)
│   │
│   └── brokers/            # Broker integrations (T2)
│       └── ibkr/           # IBKR connector
```

### Integration Points

| NEX Component | Phoenix Location | River Integration | Governance |
|---------------|------------------|-------------------|------------|
| Hunt Engine | `phoenix/lab/hunt.py` | Reads enriched data from River | T1, respects halt |
| Backtest | `phoenix/lab/backtest.py` | Uses River historical data | T1, deterministic |
| Athena Memory | `phoenix/memory/athena.py` | Stores facts as beads | T0/T1 |
| Gemma Analysis | `phoenix/intelligence/gemma.py` | Reads River context | T1 |
| Morning Brief | `phoenix/briefings/morning.py` | Aggregates River metrics | T0 |
| Broker (IBKR) | `phoenix/brokers/ibkr.py` | N/A | T2, human gate |

### Governance Additions Required

| Component | Tier | Additions |
|-----------|------|-----------|
| Hunt Engine | T1 | `check_halt()` before backtest, emit beads |
| Backtest | T1 | Deterministic, no ffill, use River |
| Memory | T0/T1 | Bead emission for facts |
| Gemma | T1 | Context from River only |
| Broker | T2 | Human approval token required |

---

## SECTION 5: GAP ANALYSIS

### What NEX Had That Phoenix Needs

| Capability | NEX Status | Phoenix Gap |
|------------|------------|-------------|
| Morning Briefing | ✅ Working | MISSING |
| Hunt Engine | ✅ Working | MISSING |
| Backtest Engine | ✅ Working | MISSING |
| Memory System | ✅ Working | MISSING |
| Gemma Analysis | ⚠️ Stubbed | MISSING |
| Multi-Pair Scan | ✅ Working | MISSING |
| Session Persistence | ✅ Working | Partial (beads) |
| MCP Tools | ⚠️ 58/141 | MISSING |
| Regime Forecast | ⚠️ Mock | MISSING |

### What Phoenix Has That NEX Lacked

| Capability | Phoenix Status | NEX Gap |
|------------|----------------|---------|
| Constitutional Governance | ✅ Proven | Missing |
| Halt < 50ms | ✅ 0.003ms | Kill switch async (slow) |
| Tier Gates (T0/T1/T2) | ✅ Enforced | Missing |
| Deterministic State Machine | ✅ Hash proven | Missing |
| Data Integrity (River) | ✅ XOR == 0 | Forward-fill bugs |
| Chaos Testing | ✅ 100% pass | Missing |
| Auto-Halt Escalation | ✅ >3 CRITICAL | Missing |
| Bead Emission | ✅ Audit trail | Missing |
| Position Lifecycle | ✅ State machine | Weak tracking |

### Synthesis Opportunity

Phoenix + NEX = Complete Trading Intelligence:
- Phoenix provides: governance, integrity, halt, determinism
- NEX provides: superpowers, operator experience, learning loop

---

## SECTION 6: PRODUCT VISION SKELETON

### Unified Capability Set

```yaml
MORNING_DISCOVERY:
  - Morning briefing with overnight summary
  - Multi-pair setup scan (6 pairs)
  - Best opportunities highlighted
  - Health status (halt, quality, positions)

HYPOTHESIS_TESTING:
  - "Test my idea" via Hunt Engine
  - Natural language → backtest variations
  - Survivors automatically queued
  - Learning accumulated in Athena

REAL_TIME_ANALYSIS:
  - "What's setting up?" via Gemma
  - ICT analysis on current conditions
  - Setup quality: NONE/FORMING/READY
  - Direction bias with reasoning

MEMORY_PERSISTENCE:
  - Facts learned across sessions
  - Contradiction detection
  - Pattern extraction from experiments
  - Flywheel phase tracking

EXECUTION_GOVERNANCE:
  - Halt in <50ms (proven)
  - Tier gates (T0/T1/T2)
  - Human approval for capital actions
  - Position lifecycle tracking
```

### A Day in Olya's Life (Combined System)

```
6:00 AM — Morning Brief
  Olya: "Good morning"
  Phoenix: [Morning Briefing]
    - Overnight: EURUSD +15 pips, GBPUSD flat
    - Account: $10,234 (+0.8% daily)
    - System: HEALTHY, halt ready (0.003ms)
    - Setups: EURUSD Asia sweep forming

7:00 AM — Research Phase
  Olya: "Test FVG with tighter stops on EURUSD"
  Phoenix: [Hunt Engine]
    - Testing 5 variations...
    - 3 survivors (60% survival rate)
    - Best: FVG_TIGHT_V2 (Sharpe 1.8)
    - Queued for review

8:30 AM — Kill Zone Check
  Olya: "What's setting up?"
  Phoenix: [Gemma Analysis]
    - EURUSD: FORMING (Asia low swept)
    - GBPUSD: READY (FVG + displacement)
    - Recommendation: PREPARE GBPUSD

9:00 AM — Entry Decision
  Olya: "Approve GBPUSD entry"
  Phoenix: [T2 Gate]
    - Approval token required
    - State hash: a3b4c5d6
    - Halt check: CLEAR
    - [APPROVED] Position opened

5:00 PM — Evening Review
  Olya: "What did I learn today?"
  Phoenix: [Athena]
    - Facts added: 3
    - Hunt experiments: 2
    - Pattern: "Tight stops improve FVG (7 experiments)"
    - Flywheel phase: VALIDATE → OPTIMIZE
```

### Key UX Principles

1. **Zero Terminal**: All via natural language
2. **Token Efficient**: Aggregators save 60-80%
3. **Immediate Feedback**: Hunt results in seconds
4. **Memory Persistence**: Facts survive sessions
5. **Governance Invisible**: Halt/tiers work silently
6. **Morning Discovery**: Start each day with briefing

---

## EXIT GATES

| Gate | Criterion | Status |
|------|-----------|--------|
| GATE_E1_REPO_MAPPED | Directory structure documented | ✓ PASS |
| GATE_E2_SUPERPOWERS_IDENTIFIED | Operator capabilities inventoried | ✓ PASS |
| GATE_E3_SUBSUMPTION_CLEAR | Every component assessed | ✓ PASS |
| GATE_E4_INTEGRATION_SKETCHED | Mapping to Phoenix proposed | ✓ PASS |
| GATE_E5_VISION_SKELETON | "Day in Olya's life" drafted | ✓ PASS |

---

## RECOMMENDATIONS

### Immediate (S29)

1. **Port Gemma Client** — Clean, portable, unlocks "what's setting up?"
2. **Build Morning Briefing** — Primary discovery layer
3. **Port Hunt Engine** — Core hypothesis testing capability

### Near-Term (S30)

4. **Subsume Backtest Runner** — With River integration
5. **Port Athena Memory** — With bead integration
6. **Build Multi-Pair Scan** — Using Gemma + River

### Later (S31+)

7. **Port IBKR Connector** — T2 with human gates
8. **Implement Regime Forecast** — Beyond mock
9. **Full MCP Tool Port** — Fix 76 broken tools

---

**VERDICT**: **READY_TO_INTEGRATE**

NEX contains significant operator value (superpowers) that Phoenix's constitutional foundation can support. The integration path is clear, and the synthesis produces a complete trading intelligence system.

---

*OINK OINK.* 🐗🔥
