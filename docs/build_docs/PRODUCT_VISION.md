# PHOENIX PRODUCT VISION

**Document:** PRODUCT_VISION.md  
**Version:** 1.2 CANONICAL  
**Date:** 2026-01-27  
**Status:** CANONICAL_LOCKED  
**Evolution:** NEX magic + Phoenix skeleton + God_Mode patterns

---

## The Synthesis

We spent months learning what works and what kills.

**NEX taught us the magic:** Claude as thinking partner. Real conversation. Ideas crystallizing through dialogue. The feeling of being heard. Thinking unfolding over time. *That's what we're doing right now, in this very conversation.*

**NEX taught us the death:** 200 MCP tools flooding context. Claude holding state, memory, execution, AND conversation. Mid-session amnesia. The magic dying when context died.

**Phoenix taught us the skeleton:** Governance that holds. Halt in <50ms. Data integrity via River. Deterministic replay. Constitutional enforcement.

**God_Mode taught us the patterns:** HIVE workers. Boardroom state. Beads for continuity. Sub-agents. Cognitive arbitrage. Separate concerns or die.

**This document is the synthesis.** The magic without the death. The skeleton with a soul. The thinking partner backed by robust infrastructure.

---

## The Core Insight

```
The NEX failure wasn't "Claude as interface."
The NEX failure was "Claude as EVERYTHING."

When Claude holds conversation + state + memory + execution,
context dies and magic dies with it.

The fix isn't "dumb down the interface."
The fix is "liberate Claude from everything except thinking."
```

**The mental model Olya needs:**

> "Claude is my thinking partner. Phoenix is the system Claude talks to."

| Role | Lives Where | Never In |
|------|-------------|----------|
| Thinking / Ideation | Claude Desktop | Phoenix |
| Persistent State | Boardroom | Claude's context |
| Execution | HIVE Workers | Claude's context |
| Memory | Athena (Beads) | Claude's context |
| Governance | Phoenix Core | Claude's context |
| Alerts / Control | Telegram | - |

**Claude holds conversation only. Nothing else.**

---

## 1. The Two Planes

Phoenix operates across two distinct planes:

### Cognitive Plane (Claude Desktop)

**Purpose:** Thinking partner. Ideation. Crystallization.

**What happens here:**
- Olya thinks out loud
- Ideas form and develop
- Intuitions get structured
- Hypotheses crystallize
- Questions get explored
- Understanding deepens

**What Olya feels:**
- Heard
- Supported
- Intellectually matched
- Safe to explore
- Never rushed

**What Claude holds:**
- The conversation (and only the conversation)
- No tool definitions
- No state
- No execution traces
- No raw data

### Notification Plane (Telegram)

**Purpose:** Alerts. Approvals. Emergency control.

**What happens here:**
- Morning briefing push
- Setup alerts ("GBPUSD READY")
- Approval requests
- Emergency halt
- End-of-day summary

**What Olya does:**
- Glances
- Confirms
- Vetoes
- Halts if needed

**What Telegram is NOT:**
- A thinking partner
- A place for ideation
- The primary interface
- Where insights are born

> "Telegram is neurologically incompatible with reflective cognition."
> — Advisory validation

---

### Advisory Insight: The OODA Advantage

OWL (Gemini) identified a strategic framing worth preserving:

```
OODA Loop Mapping:
  OBSERVE → Morning Briefing, Scan
  ORIENT  → EXPLORE (thinking partner)
  DECIDE  → Hypothesis formation, T2 review
  ACT     → APPROVE, execution
```

> "By protecting EXPLORE from ACT, you have given Olya the ultimate competitive advantage: **Unpolluted Clarity.**"

**Design Principle:** EXPLORE is the Orient phase. It must remain unpolluted by action pressure. This is where battles are won.

The cognitive plane is not a "nice to have." It is the strategic center of gravity. Everything else serves it.

---

## 2. The File Seam Architecture

### Why Not MCP?

Even 5-6 macro-tools would inject tool definitions into Claude's context. Tool definitions consume tokens. Tool outputs flood context. This is how NEX died.

### The Solution: File-Based Intent

```
┌─────────────────────────────────────────────────────────────────┐
│  CLAUDE DESKTOP (Cognitive Plane)                               │
│  ├── Holds: Conversation only                                   │
│  ├── Writes: intent.yaml to /phoenix/intents/incoming/          │
│  ├── Reads: response.md from /phoenix/responses/                │
│  └── Context: ZERO tool definitions, ZERO execution traces      │
├─────────────────────────────────────────────────────────────────┤
│  FILE SEAM (The Boundary)                                       │
│  ├── /phoenix/intents/incoming/     ← Claude writes             │
│  ├── /phoenix/responses/            → Claude reads              │
│  └── Observable: Just files. Easy to debug.                     │
├─────────────────────────────────────────────────────────────────┤
│  PHOENIX (System Plane)                                         │
│  ├── Watcher: Detects new intents                               │
│  ├── Inquisitor: Validates against doctrine                     │
│  ├── Dispatcher: Routes to HIVE workers                         │
│  ├── Workers: Execute (separate contexts, disposable)           │
│  ├── Boardroom: Persistent state (Beads, Athena)                │
│  └── Writes: response.md with summary + bead_id                 │
└─────────────────────────────────────────────────────────────────┘
```

### How It Flows

**EXPLORE Mode (No file seam needed):**
```
Olya: "I'm noticing something about London entries..."
Claude: [Responds directly — pure conversation]
        [May query Athena read-only for context]
        [No intent emitted, no workers, no files]
```

**INTENT Mode (File seam activates):**
```
Olya: "Test tighter stops on FVG entries"

Claude: [Classifies as INTENT: HUNT]
        [Writes intent.yaml]:
          type: HUNT
          payload: "tighter stops on FVG entries"
          timestamp: 2026-01-27T08:30:00Z
        
Phoenix: [Watcher detects intent.yaml]
         [Inquisitor validates — PASS]
         [Dispatcher routes to Hunt_Worker]
         [Hunt_Worker runs (separate context)]
         [Hunt_Worker writes results to Boardroom]
         [Dispatcher compresses to summary]
         [Writes response.md]:
           status: COMPLETE
           summary: "3 survivors. Best: V2 (Sharpe 1.6)"
           bead_id: HUNT_2026_01_27_001
           detail_path: /phoenix/reports/HUNT_2026_01_27_001.md

Claude: [Reads response.md via Lens]
        [Presents to Olya naturally]
        "Hunt complete. 3 survivors..."
```

### The Lens Worker (Read Seam)

**Problem:** If Olya must manually attach response.md every turn, the "superpower" feeling dies in death by a thousand clicks.

**Solution:** The Lens daemon watches `/phoenix/responses/` and injects new response content into the conversation automatically.

```
┌──────────────────────────────────────────────────────────────┐
│  LENS DAEMON                                                  │
│  ├── Watches: /phoenix/responses/                             │
│  ├── Detects: New response.md files                           │
│  ├── Injects: Content into Claude conversation                │
│  └── Context cost: ZERO (no tool definitions)                 │
└──────────────────────────────────────────────────────────────┘
```

**Fallback Option:** If the daemon proves complex, a single ultra-lean MCP tool (`read_phoenix_response`) can serve as fallback. This costs ~50 tokens for the tool definition but maintains the principle of minimal context intrusion.

**Invariant:** `INV-LENS-1` — Exactly ONE mechanism returns Phoenix responses to Claude. This mechanism adds ZERO tool definitions to Claude's context.

### Why This Works

| Problem | How File Seam Solves It |
|---------|------------------------|
| Tool definition bloat | Zero tools in Claude's context |
| Tool output flooding | Only compressed summary returns |
| Context death | Claude stays lean |
| Debugging difficulty | Just files — observable, greppable |
| Complexity | YOLO simple |

---

## 2.4 State Hash Validation (Stale Market Guard)

### The Problem

Olya enters a 2-hour EXPLORE session at 7am. Market moves. Signalman fires. Regime shifts. At 9am, she says "Approve the GBPUSD entry."

But that setup was based on 7am reality. She's "trading a ghost."

### The Solution

All intents include a `last_known_state_hash` anchor. Phoenix validates before execution.

**Intent Schema Addition:**
```yaml
type: APPROVE  # or any DISPATCH
payload: {...}
timestamp: 2026-01-27T09:00:00Z

# State Anchor (required for T2)
last_known_state_hash: abc123
session_start_time: 2026-01-27T07:00:00Z
```

**Phoenix Validation Flow:**
```
on_intent_receive:
  1. Check: current_state_hash == intent.last_known_state_hash
  
  2. If MISMATCH:
       action: INTERCEPT
       response:
         status: STATE_CONFLICT
         message: |
           "The market has shifted since your session started.
           
            CHANGES DETECTED:
            - Signalman: EURUSD regime flag (8:15am)
            - GBPUSD: Setup confidence dropped 0.87 → 0.62
            
            Please review the updated briefing before executing."
         updated_briefing_path: /phoenix/briefings/latest.md
         
  3. If MATCH:
       action: PROCEED
```

**Staleness Threshold:**
- If `session_start_time` is >30 minutes old AND intent is T2:
- Phoenix requires explicit "I've reviewed current state" confirmation

This prevents stale-context execution without blocking legitimate long thinking sessions.

---

## 3. The Context Checkpoint

### The Problem

Even with a lean context (conversation only), long thinking sessions will eventually approach Claude's window limit. In NEX, this meant sudden collapse and lost continuity.

### The Solution: Graceful Checkpoint

**Detection:**
- Monitor conversation density (turns, token projection)
- Threshold: projected_next_turn > 80% window capacity

**The UX:**
```
Claude: "I'm sensing we're going deep on this exploration.
         Would you like me to summarize and reset fresh?
         
         Preview of what I'll preserve:
         - Your intuition about London timing
         - The 3 questions we're exploring
         - Current hypothesis about volatility settling
         - Your skepticism about the news angle (cognitive momentum)
         
         [CHECKPOINT & RESET] [CONTINUE A BIT LONGER]"

Olya: [CHECKPOINT & RESET]

Claude: [Writes CONTEXT_SNAPSHOT bead]
        [Fresh Claude instance spins up]
        [Loads last 3-5 CONTEXT_SNAPSHOT beads]
        [Continues seamlessly]

Claude (fresh): "Okay, I'm back with full context. 
                 We were exploring your intuition about London timing.
                 I notice you were skeptical of the news-timing angle
                 and leaning toward the volatility-settling hypothesis.
                 Shall we continue from there?"
```

### Cognitive Momentum Field

A fresh Claude instance is a blank slate emotionally. If Olya was skeptical, frustrated, or had momentum in a direction, the new Claude shouldn't start neutral — it should inherit her stance.

**Enhanced CONTEXT_SNAPSHOT Schema:**
```yaml
type: CONTEXT_SNAPSHOT
state_hash: abc123

# Facts & Questions
intuitions:
  - "London entries better when I wait"
  - "First 30 minutes feels chaotic"
open_questions:
  - "Is it volatility or liquidity?"
  - "Does news timing matter?"
current_hypothesis: "FVG entries only after 8:30am London"

# Cognitive Momentum (NEW)
cognitive_momentum:
  operator_stance: "skeptical"  # skeptical|neutral|confident|frustrated|exploratory
  momentum_direction: "toward volatility-settling hypothesis"
  discarded_paths:
    - "Already explored and rejected: news-timing angle"
    - "Olya dismissed: correlation spike theory"
  emotional_context: "Olya expressed mild frustration with ranging markets"
```

**Hot-Load Behavior:**
Fresh Claude reads the `cognitive_momentum` field FIRST, calibrates tone and approach, then continues. The conversation picks up where it left off — not just factually, but emotionally.

### The Principles

1. **Never surprise reset.** Always Olya's choice.
2. **Preview before commit.** She sees what will be preserved.
3. **Seamless continuation.** Fresh Claude feels like same conversation.
4. **Beads as atoms.** CONTEXT_SNAPSHOT survives instance death.
5. **Inherit stance, not just facts.** Cognitive momentum preserves the soul.

---

## 4. The Six Intents

Claude doesn't call tools. Claude writes intents. Phoenix executes.

```yaml
1_EXPLORE:
  mode: THINKING
  file_seam: NO (pure conversation)
  purpose: Unbounded ideation, crystallization
  persists: Nothing (unless promoted)
  executes: Nothing
  emits_intent: NEVER (file seam closed)
  examples:
    - "I'm wondering about liquidity sweeps..."
    - "Something feels off about my entries"
    - "Help me think through this"

2_DISPATCH:
  mode: ACTING  
  file_seam: YES (intent.yaml)
  purpose: Request work from HIVE
  persists: Beads
  executes: Workers
  types:
    - MORNING_BRIEF: Overnight summary
    - HUNT: Test hypothesis variations
    - SCAN: What's setting up?
    - BACKTEST: Validate strategy
    - AUTOPSY: Analyze trade

3_READ:
  mode: ACTING
  file_seam: YES (lightweight)
  purpose: Fetch current state
  persists: Nothing
  executes: File read only
  examples:
    - "How's the Euro?"
    - "System health?"

4_APPROVE:
  mode: ACTING
  file_seam: YES (T2 gate)
  purpose: Human sovereignty gate
  persists: APPROVAL bead
  executes: Position action
  requires: 
    - Evidence bundle visible
    - State hash validation (INV-STATE-ANCHOR-1)

5_QUERY_MEMORY:
  mode: ACTING
  file_seam: YES (Athena)
  purpose: Ask the memory palace
  persists: Nothing
  executes: Datasette query
  examples:
    - "What did I learn about ranging markets?"
    - "Show me losing patterns this month"

6_HALT:
  mode: ACTING
  file_seam: YES (direct)
  purpose: Emergency stop
  persists: HALT bead
  executes: Immediate system halt
  tier: Always available
```

---

## 5. The Superpowers

### Thinking Partner (EXPLORE)

The foundational superpower. What made NEX magical. What we almost lost.

**What Olya Experiences:**
```
Olya: "I've been noticing that my FVG entries in London have 
       been getting stopped out more often. Not sure why."

Claude:
  I notice you're sensing a pattern. Let me help structure this.
  
  WHAT YOU'RE OBSERVING:
    - FVG entries in London
    - Higher stop-out rate recently
    
  FROM ATHENA (read-only):
    - Last 30 days: 12 London FVG entries, 5 stopped (42%)
    - Prior 90 days: 34 entries, 11 stopped (32%)
    - Notable: 4 of 5 recent stops were first 30 min
    
  POSSIBLE DIMENSIONS:
    - Time within session (early vs late)?
    - News proximity?
    - HTF alignment quality?
    
  QUESTION:
    Is it possible you're entering too early?
    
  If this resonates, I can help form a testable hypothesis.
  Or we can keep exploring.

Olya: "Early London... that feels right. Let me sit with it."

[No workers. No beads. No files. Just thinking together.]
```

**The Magic:**
- Claude thinks WITH her, not FOR her
- Structures without rushing
- Queries memory without flooding
- Waits for her to be ready
- Promotes to hypothesis only when she says

### Morning Briefing

**Trigger:** 6am cron OR "Good morning"

**What Olya Sees:**
```
Good morning, Olya.

HEALTH: GREEN (halt ready: 0.003ms)
OVERNIGHT: EURUSD +15 pips (T0 managed), GBPUSD flat
ACCOUNT: $10,234 (+0.8%)

SETUPS FORMING:
  • EURUSD (0.72): Asia sweep complete, watching for FVG
  • GBPUSD (0.68): London approaching, bias bullish

DECAY CHECK: All strategies nominal
DOCTRINE: No contradictions flagged

MODE: NORMAL (declare DEFENSIVE if needed)
```

### Test My Idea (Hunt)

**Trigger:** Formed hypothesis ready to test

**What Olya Sees:**
```
Olya: "Test FVG entries only after 8:30am London"

Claude: Writing intent to Phoenix...

[File seam: intent.yaml written]
[Phoenix: Hunt_Worker runs]
[2 minutes pass]

Claude: [Reads response.md via Lens]

  Hunt complete.
  
  SURVIVORS: 3/10
  BEST: LATE_LONDON_V2 (Sharpe 1.6)
  
  REASONING BREAKDOWN:
    - Timing filter: 0.9 (30-min delay effective)
    - Combined with tighter stop: 0.95
    
  WHY OTHERS FAILED:
    - Win rate below threshold (7 variants)
    
  [View Full Report] [Queue for Shadow]
```

### What's Setting Up (Scan)

**Trigger:** "What's setting up?" OR push when >0.8

**What Olya Sees:**
```
GBPUSD: READY (0.87)

  REASONING:
    HTF bias: 0.9 (bullish structure confirmed)
    LTF trigger: 0.85 (FVG + displacement)
    Evidence: COMPLETE
    Red check: PASSED
    
  WHY 0.87:
    News in 2 hours (medium impact) caps confidence
    
  [Expand Full Reasoning]
```

### Memory Palace (Athena + Datasette)

**Trigger:** "What did I learn about X?" OR direct query

**What Olya Experiences:**
```
Olya: "Show me when I felt uncertain last month"

Claude: [Queries Datasette on Beads]

  From your CONTEXT_SNAPSHOT and EXPLORE beads (January):
  
  JAN 8: "Something feels off about London"
    → Led to: Hunt on timing (3 survivors)
    
  JAN 15: "Not sure about ranging markets"
    → Led to: Tighter stop discovery
    → Led to: Doctrine addition (ranging regime)
    
  JAN 22: "Correlation spike confusion"
    → Still open (no resolution yet)
    
  PATTERN: Your uncertainty often precedes discoveries.
```

**The Power:**
- Beads are queryable history
- Datasette makes patterns visible
- "Show me rejected intents" — learn from what didn't work
- "Show me when I was right" — build confidence
- Recombobulation supremacy

### Autopsy & Decay

**Autopsy:** Post-trade analysis (async, never blocks)

```
AUTOPSY COMPLETE:

  ENTRY THESIS (at decision time):
    Confidence: 0.84
    Reasoning hash: abc123
    
  OUTCOME: Stopped out (-1.2%)
  
  WHAT WAS VALID:
    Entry matched doctrine. Evidence complete.
    
  WHAT WAS UNKNOWN:
    EUR news created correlation spike.
    
  LEARNING:
    Consider EUR calendar on GBP entries.
    
  [Bead: AUTOPSY_2026_01_27_001]
```

**Decay Detection (Signalman):**

```
DECAY ALERT

Strategy: FVG_LONDON
  Last 30 days: Sharpe 0.8
  Prior 300 days: Sharpe 1.4
  Drift: -43%

SIGNALMAN: Input distribution shift detected
  - FVG frequency down 30%
  - Displacement size down 25%
  
INTERPRETATION: Regime may have shifted

ACTION: ONE-WAY-KILL active (exits only)
```

---

## 6. The Invariants

### Operational

| Invariant | Rule |
|-----------|------|
| **INV-HALT-1** | Halt < 50ms (proven: 0.003ms) |
| **INV-DATA-CANON** | Single truth from River |
| **INV-CONTRACT-1** | Deterministic state machine |
| **INV-SOVEREIGN-1** | Human sovereignty over capital |

### Cognitive

| Invariant | Rule |
|-----------|------|
| **INV-EXPLORE-1** | EXPLORE never triggers workers |
| **INV-EXPLORE-2** | EXPLORE never persists (unless promoted) |
| **INV-EXPLORE-3** | EXPLORE cannot emit intent.yaml (file seam closed) |
| **INV-CONTEXT-1** | Claude holds conversation only |
| **INV-CONTEXT-2** | Checkpoint before collapse, never surprise |
| **INV-SNAPSHOT-1** | CONTEXT_SNAPSHOT must include cognitive_momentum |
| **INV-REASONING-1** | All proposals decomposable |

### Architectural

| Invariant | Rule |
|-----------|------|
| **INV-LENS-1** | Exactly ONE mechanism returns Phoenix responses to Claude; adds ZERO tool definitions |
| **INV-STATE-ANCHOR-1** | All T2 intents must include last_known_state_hash; Phoenix rejects stale-state execution with STATE_CONFLICT |
| **INV-STATE-ANCHOR-2** | Sessions >30 minutes old require state refresh before T2 action |

### Risk

| Invariant | Rule |
|-----------|------|
| **INV-EVIDENCE-1** | No entry without evidence bundle |
| **INV-RISK-DEFENSIVE** | ONE-WAY-KILL on decay/drawdown |
| **INV-STAGE-BEFORE-LIVE** | Shadow period before live |
| **INV-EXPOSURE-LIMIT** | 2.5% max per currency |

### Constitutional Anchors

1. **Human sovereignty over capital is absolute.**
2. **The River is sacred.** Data integrity is lifeblood.
3. **Thinking precedes acting.** EXPLORE is always safe.
4. **Claude is the thinking partner, not the system.**
5. **Context is finite.** Protect it. Checkpoint gracefully.
6. **Beads are atoms.** Continuity survives instance death.
7. **Reasoning must be visible.** No opaque proposals.
8. **<50ms halt always works.**
9. **File seam is the boundary.** No tools in Claude's context.
10. **Stale context cannot execute.** State hash guards T2 actions.

---

## 7. The Anti-Patterns

### What Must Never Happen

| Anti-Pattern | Why It Kills Us |
|--------------|-----------------|
| **Tools in Claude's context** | Definitions bloat, outputs flood |
| **Claude holding state** | Context death = state death |
| **Telegram as thinking partner** | Neurologically incompatible |
| **Surprise checkpoint** | Violates sovereignty |
| **EXPLORE → Execute** | Violates safe thinking space |
| **Opaque scores** | Trust erosion |
| **Silent degradation** | Decay undetected |
| **Stale context execution** | Trading a ghost |

### Forbidden Patterns

- Sharpe hunting (curve fitting)
- Auto-parameter adjustment
- ML mutation without ceremony
- "System improved itself" narratives
- Tool calls from Claude (file seam only)
- Intent emission during EXPLORE
- T2 action without state hash validation

---

## 8. The Roadmap

### S29: COGNITIVE_FOUNDATION

**Theme:** "The thinking partner comes alive"

| Track | Deliverable |
|-------|-------------|
| A | File seam architecture (intent.yaml ↔ response.md) |
| B | EXPLORE mode in Claude Desktop |
| C | Phoenix watcher + Inquisitor |
| D | Morning Briefing worker |
| E | Lens daemon for response injection |

**Exit:** Olya can think with Claude AND get a briefing.

### S30: LEARNING_LOOP

**Theme:** "The flywheel spins"

| Track | Deliverable |
|-------|-------------|
| A | Hunt Engine (test my idea) |
| B | Athena + Datasette (memory palace) |
| C | Context checkpoint mechanics + cognitive momentum |
| D | Shadow boxing |

**Exit:** Hypothesis → test → learn → surface.

### S31: SIGNAL_AND_DECAY

**Theme:** "Phoenix watches"

| Track | Deliverable |
|-------|-------------|
| A | Setup detection (what's setting up) |
| B | Signalman + ONE-WAY-KILL |
| C | Autopsy worker |
| D | Telegram notification plane |
| E | State hash validation (stale market guard) |

**Exit:** Phoenix warns before problems prove themselves.

### S32: EXECUTION_PATH

**Theme:** "Real markets"

| Track | Deliverable |
|-------|-------------|
| A | IBKR connector |
| B | T2 approval workflow with state hash |
| C | Position reconciliation |
| D | Staging enforcement |

**Exit:** T2 workflow proven.

### S33: FIRST_BLOOD

**Theme:** "One pair, real money"

| Track | Deliverable |
|-------|-------------|
| A | EUR/USD live |
| B | Incident procedures |
| C | 24/7 monitoring |

**Exit:** N days live trading.

### S34+: EXPANSION

- Additional pairs
- Echo domain (crypto)
- Foundry-as-a-Service

---

## 9. A Day in Olya's Life

### The Vision Realized

```
6:00 AM — Morning Brief (Telegram push)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Phone buzzes]

Phoenix via Telegram:
  HEALTH: GREEN
  OVERNIGHT: +15 pips
  SETUPS: GBPUSD forming (0.72)
  
Olya glances. Notes GBPUSD. Opens Claude Desktop with coffee.

6:30 AM — Thinking Time (Claude Desktop)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Olya: "Morning. I've been thinking about my London entries.
       They seem better when I wait a bit. Not sure why."

Claude: 
  Good morning. That's an interesting observation.
  
  Let me help structure it. From Athena:
    - Your early London entries (first 30 min): 42% win
    - Your later entries (after 8:30): 61% win
    
  Possible factors:
    - Initial volatility settling?
    - Liquidity improving?
    - Clearer structure forming?
    
  Does any of these resonate?

Olya: "The volatility settling idea feels right.
       That first 30 minutes is chaotic."

Claude:
  That aligns with what the data shows.
  
  If you're ready, we could form a hypothesis:
  "FVG entries only after 8:30am London"
  
  Want me to test that? Or keep exploring?

Olya: "Let's keep exploring a bit. What about news timing?"

[No workers triggered. Just conversation. Ideas forming.]
[INV-EXPLORE-3: File seam remains closed.]

7:30 AM — Hypothesis Forms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Olya: "Okay, I want to test this: London FVG entries
       only after 8:30am, excluding first hour news days."

Claude: 
  Clear hypothesis. Writing intent to Phoenix...
  
  [intent.yaml written — file seam opens]
  
  Hunt is running. I'll have results in about 2 minutes.

[Time passes. Olya checks charts.]

Claude: [Lens daemon injects response]
  Hunt complete.
  
  3 survivors from 10 variations.
  Best: LATE_LONDON_V2 (Sharpe 1.6, up from 1.1 baseline)
  
  Your intuition about volatility settling appears valid.
  The news filter added marginal value (+0.1 Sharpe).
  
  Want to queue this for shadow boxing?

Olya: "Yes, queue it. Let's see how it does in real time."

8:30 AM — Setup Alert (Telegram)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Phone buzzes]

Phoenix via Telegram:
  GBPUSD: READY (0.87)
  HTF: Bullish | LTF: FVG formed | Evidence: Complete
  
  [VIEW IN CLAUDE] [APPROVE] [PASS]

Olya taps [VIEW IN CLAUDE]

Claude:
  GBPUSD setup details:
  
  REASONING BREAKDOWN:
    HTF bias: 0.9 — Daily bullish structure, 4H BoS at 1.2640
    LTF trigger: 0.85 — 15m FVG, displacement 25 pips
    Evidence: Complete — Stop clear, target defined
    Red check: Passed — No contrary signals
    
  Why 0.87 (not higher):
    Medium-impact news in 2 hours
    
  Current state_hash: def456
  This aligns with your methodology.
  
  [APPROVE] [MODIFY] [PASS]

Olya: [APPROVE]

Claude:
  Approval recorded with state_hash: def456
  Position opening.
  
  Entry: 1.2655
  Stop: 1.2625 (30 pips)
  Target: 1.2715 (60 pips)
  Risk: 0.5% account
  
  Reasoning hash preserved: abc123

12:00 PM — Checkpoint Moment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[After deep exploration of ranging market patterns]

Claude:
  I'm sensing we're going deep on this exploration.
  Would you like me to checkpoint and reset fresh?
  
  What I'll preserve:
    - Your ranging market insights
    - The 3 hypotheses we're forming
    - Current questions about regime detection
    - Your stance: skeptical of MA-based detection
    
  [CHECKPOINT] [CONTINUE]

Olya: [CHECKPOINT]

Claude: 
  Checkpoint saved with cognitive momentum.
  Resetting...
  
  [Fresh instance]
  
  I'm back with full context.
  We were exploring ranging markets.
  You had three forming hypotheses about tighter stops.
  I notice you were skeptical of MA-based regime detection.
  
  Ready to continue from that stance?

3:00 PM — Target Hit (Telegram)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Phone buzzes]

Phoenix via Telegram:
  GBPUSD: TARGET HIT +60 pips
  Autopsy queued.

5:00 PM — Evening Review (Claude Desktop)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Olya: "What did I learn today?"

Claude:
  Today's learnings:
  
  TRADES: 1 win (GBPUSD +60 pips)
  EXPLORATIONS: 2 (London timing, ranging markets)
  HUNTS: 1 (LATE_LONDON, 3 survivors)
  SHADOW QUEUE: 1 strategy added
  
  AUTOPSY:
    Entry thesis validated.
    Reasoning at entry matched outcome.
    No doctrine gaps identified.
    
  DISCOVERIES:
    Your intuition about early London volatility
    was mechanically validated (Sharpe +0.5).
    
  OPEN THREADS:
    Ranging market exploration continues tomorrow.
    
Olya: "Good day. Save the ranging thread for morning."

Claude: Saved. See you tomorrow.

10:00 PM — Overnight
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Olya sleeps.

Phoenix watches:
  - T0 workers scan Asia session
  - Shadow boxer runs LATE_LONDON_V2
  - Signalman checks decay (all nominal)
  - Briefing worker prepares tomorrow

The flywheel turns.
Intuitions become hypotheses.
Hypotheses become tests.
Tests become learnings.
Learnings compound.

The thinking partner rests, but the system never sleeps.
```

---

## 10. Success Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| **Thinking Session Length** | >2 hours | Deep exploration works |
| **Context Checkpoints** | Graceful | Never surprise collapse |
| **File Seam Latency** | <5s | Responsive feel |
| **EXPLORE Engagement** | Daily | Cognitive layer alive |
| **Hunt Completion** | <5 min | Ideas tested quickly |
| **Halt Response** | <50ms | Sovereignty guaranteed |
| **State Hash Validation** | 100% T2 | No stale execution |
| **Olya's Feeling** | "Superpowers" | Not "automated" |

---

## 11. The Bottom Line

### Phoenix Is

- **Claude as thinking partner** — the magic of NEX, preserved
- **File seam architecture** — zero tools in context
- **Lens daemon** — automatic response injection
- **Graceful checkpoints** — continuity survives with cognitive momentum
- **Memory palace** — queryable history via Datasette
- **Two planes** — cognitive (Claude) + notification (Telegram)
- **EXPLORE first** — thinking precedes acting (file seam closed)
- **Reasoning visible** — no opaque proposals
- **State hash validation** — no trading ghosts
- **Robust skeleton** — governance, halt, determinism
- **Flywheel** — learning compounds

### Phoenix Is Not

- Claude as system (Claude is only thinking partner)
- Tool-calling chatbot (file seam, not MCP)
- Telegram-primary interface (secondary notification only)
- Context-dependent memory (Boardroom owns state)
- Opaque oracle (reasoning always decomposable)
- Replacement for Olya's judgment (superpowers, not automation)
- Stale context executor (state hash guards T2)

### The Tests

> "Can I think with Claude for hours without collapse?"

> "Does it feel like the best of NEX without the death?"

> "Is my intuition valued, not just my commands?"

> "Can I ask 'why' and see the reasoning?"

> "Does Phoenix watch while I sleep?"

> "Am I protected from trading on stale context?"

If yes to all, we've built what we set out to build.

---

## Invariant Summary

### Quick Reference

| ID | Rule |
|----|------|
| INV-HALT-1 | Halt < 50ms |
| INV-DATA-CANON | Single truth from River |
| INV-CONTRACT-1 | Deterministic state machine |
| INV-SOVEREIGN-1 | Human sovereignty over capital |
| INV-EXPLORE-1 | EXPLORE never triggers workers |
| INV-EXPLORE-2 | EXPLORE never persists (unless promoted) |
| INV-EXPLORE-3 | EXPLORE cannot emit intent.yaml |
| INV-CONTEXT-1 | Claude holds conversation only |
| INV-CONTEXT-2 | Checkpoint before collapse |
| INV-SNAPSHOT-1 | CONTEXT_SNAPSHOT includes cognitive_momentum |
| INV-REASONING-1 | All proposals decomposable |
| INV-LENS-1 | ONE response mechanism, ZERO tool definitions |
| INV-STATE-ANCHOR-1 | T2 requires state_hash; reject stale with STATE_CONFLICT |
| INV-STATE-ANCHOR-2 | Sessions >30min require refresh before T2 |
| INV-EVIDENCE-1 | No entry without evidence bundle |
| INV-RISK-DEFENSIVE | ONE-WAY-KILL on decay/drawdown |
| INV-STAGE-BEFORE-LIVE | Shadow period before live |
| INV-EXPOSURE-LIMIT | 2.5% max per currency |

---

**Claude is the mind. Phoenix is the body. Beads are the memory. Together, they serve Olya's clarity.**

**The magic without the death. The skeleton with a soul.**

**OINK OINK.** 🐗🔥

---

*Document locked: 2026-01-27*
*Version: 1.2 CANONICAL*
*Status: CANONICAL_LOCKED*
