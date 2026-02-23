# PHOENIX PATTERN GLOSSARY

**Document:** PATTERN_GLOSSARY.md  
**Purpose:** Portable pattern definitions for sprint execution  
**Context:** Distilled from God_Mode learnings, NEX failures, advisor synthesis

---

## Core Architecture Patterns

### FILE_SEAM

**What:** Intent-based communication between Claude and Phoenix via filesystem.

**Mechanics:**
```
Claude writes: /phoenix/intents/incoming/intent.yaml
Phoenix writes: /phoenix/responses/response.md
```

**Why this pattern:**
- MCP tools (even 5-6) inject definitions into Claude's context → bloat
- File seam = ZERO tool definitions in Claude's context
- Observable (just files), debuggable (grep), simple (YOLO)

**Origin:** BOAR advisory — "even 5-6 macro-tools = context pressure creep"

**Anti-pattern:** Any MCP tool calls from Claude Desktop (except Lens fallback)

---

### LENS_WORKER

**What:** Daemon that injects Phoenix responses into Claude's conversation.

**Mechanics:**
```
Phoenix writes response.md
Lens daemon detects new file
Lens injects content into Claude's view
```

**Why this pattern:**
- Without Lens, Olya must manually attach response.md every turn
- "Death by a thousand clicks" kills superpower feeling
- Zero context bloat (no tool definition needed)

**Origin:** OWL final sweep — "The Read Seam"

**Fallback:** Single MCP tool `read_phoenix_response` if daemon proves complex

---

### HIVE

**What:** Disposable worker instances that execute tasks outside main Claude context.

**Mechanics:**
```
Main Claude (thinking partner) → emits intent
Dispatcher → routes to HIVE worker
Worker (CLI Claude, local LLM) → executes in isolation
Worker → writes results to Boardroom
Dispatcher → compresses summary for main Claude
```

**Why this pattern:**
- Workers can use full context for heavy tasks
- Workers are disposable (no continuity needed)
- Main Claude stays lean (conversation only)
- Execution traces never enter thinking context

**Origin:** God_Mode Sprint 1-25 learnings

**Key insight:** "Agents are cattle, not pets"

---

### BOARDROOM

**What:** External state store that survives all Claude instances.

**Components:**
- Beads (immutable ledger)
- Athena (queryable index)
- Coordination state (worker handoffs)

**Why this pattern:**
- Claude's memory dies with context
- Boardroom persists across sessions, checkpoints, instance death
- State ownership is SYSTEM, not agent

**Origin:** God_Mode — "separate concerns or die"

**Key insight:** "Claude is the thinking partner, not the system"

---

### BEADS

**What:** Immutable event records that form continuity chain.

**Types:**
```yaml
CONTEXT_SNAPSHOT: Checkpoint state (intuitions, questions, momentum)
TRADE: Execution record
HUNT: Hypothesis test results
AUTOPSY: Post-trade analysis
LEARNING: Extracted pattern
SIGNAL: Setup detection
APPROVAL: T2 gate passage
HALT: Emergency stop record
```

**Why this pattern:**
- Immutable = auditable, replayable
- Queryable via Datasette (memory palace)
- Survives instance death
- Continuity without context

**Origin:** Yegge's "beads-style immutable event streams"

**Key insight:** "Beads are atoms. Continuity survives instance death."

---

### COGNITIVE_ARBITRAGE

**What:** Right model for right task.

**Routing:**
| Task | Model | Why |
|------|-------|-----|
| Thinking partner | Claude API | Nuance, empathy |
| Volume scanning | Local LLM (Gemma) | Cheap, fast |
| Setup detection | Local LLM | Real-time |
| Hypothesis filtering | Local LLM | Evaluate 50 variants |
| Judgment calls | Claude API | Complex reasoning |
| Adversarial audit | GPT API | Cold, contrarian |
| Autopsy | Claude API | Deep analysis |

**Why this pattern:**
- API calls are expensive, have latency
- Local LLMs are always-on, cheap
- Match capability to requirement

**Origin:** God_Mode exploration of Ollama/Gemma

---

### CONTEXT_CHECKPOINT

**What:** Graceful save-and-reset when context pressure detected.

**Mechanics:**
```
Monitor: bead_density + token_projection
Threshold: projected_next_turn > 80% window
Trigger: "I'm sensing we're going deep. Shall I reset fresh?"
Save: CONTEXT_SNAPSHOT bead (intuitions, questions, momentum)
Reset: Fresh Claude loads last 3-5 snapshots
```

**Why this pattern:**
- Long thinking sessions WILL approach context limit
- Surprise collapse = lost continuity, lost trust
- Graceful checkpoint = sovereignty preserved

**Origin:** OWL probe + BOAR mechanics

**Key insight:** "Never surprise reset. Always sovereign choice."

---

### COGNITIVE_MOMENTUM

**What:** Preserving operator stance across checkpoints, not just facts.

**Schema addition to CONTEXT_SNAPSHOT:**
```yaml
cognitive_momentum:
  operator_stance: skeptical|neutral|confident|frustrated|exploratory
  momentum_direction: "toward X" | "away from Y"
  discarded_paths: ["Already rejected Z because..."]
  emotional_context: "Olya expressed frustration with..."
```

**Why this pattern:**
- Fresh Claude is blank slate emotionally
- Without momentum, new instance might repeat discarded paths
- Soul must transfer, not just state

**Origin:** OWL final sweep — "Context Snapshot Fidelity"

---

### STATE_HASH_ANCHOR

**What:** Preventing action on stale market context.

**Mechanics:**
```yaml
intent.yaml includes:
  last_known_state_hash: abc123
  session_start_time: ISO8601

Phoenix validates:
  if current_hash != intent_hash:
    return STATE_CONFLICT
    "Market has shifted. Review before executing."
```

**Why this pattern:**
- 2-hour EXPLORE session = market has moved
- Acting on stale setup = "trading a ghost"
- Intercept prevents dangerous execution

**Origin:** OWL final sweep — "State Hash as Truth Anchor"

**Staleness threshold:** Sessions >30 min old require state refresh for T2

---

## Operational Patterns

### TWO_PLANES

**Cognitive Plane (Claude Desktop):**
- Thinking partner
- Ideation, crystallization
- EXPLORE mode
- Long-form continuity

**Notification Plane (Telegram):**
- Alerts, approvals
- Emergency halt
- NOT thinking partner

**Why this separation:**
- "Telegram is neurologically incompatible with reflective cognition"
- Messaging ≠ thinking
- Different tools for different purposes

**Origin:** Old GPT validation + advisor convergence

---

### EXPLORE_VS_INTENT

**EXPLORE (Thinking Mode):**
- No workers triggered
- No persistence (unless promoted)
- No intent.yaml written
- File seam CLOSED
- Pure conversation

**INTENT (Acting Mode):**
- Workers may trigger
- Beads persist
- intent.yaml written
- File seam OPEN

**Why this separation:**
- Thinking must be SAFE (no accidental execution)
- Action must be EXPLICIT (clear intent)
- Mode confusion = dangerous

**Key invariant:** INV-EXPLORE-3 — "EXPLORE cannot emit intent.yaml"

---

### INQUISITOR_GATE

**What:** Doctrine validation before worker dispatch.

**Mechanics:**
```
Intent received → Inquisitor validates:
  - Complies with doctrine?
  - Respects exposure limits?
  - Has required evidence?
  - System state allows this?
  
PASS → Dispatcher routes to worker
FAIL → Rejection with reason (no silent modification)
```

**Why this pattern:**
- Fail-closed prevents heresy
- Early rejection = no wasted work
- Explicit rejection = learning opportunity

**Origin:** Advisor convergence (GPT + OWL)

---

### ONE_WAY_KILL

**What:** Defensive posture allowing only risk reduction.

**Trigger:** Decay detected (Sharpe drift >15%) OR drawdown threshold

**Behavior:**
- Exits allowed
- New entries BLOCKED
- Requires human review to lift

**Why this pattern:**
- When edge decays, stop adding risk
- Professional risk management
- System protects itself

**Origin:** Pro hardening addendum

---

### SHADOW_BOXING

**What:** Paper trading with real signals for validation.

**Mechanics:**
- Load historical or live data
- Run strategy signals
- Track paper P&L
- Compare CSO signals to Olya's actual decisions

**Why this pattern:**
- Validate before risking capital
- Calibrate CSO to Olya's actual behavior
- Zero-capital firebreak

**Origin:** INV-STAGE-BEFORE-LIVE

---

## Anti-Patterns (What Killed NEX)

### MCP_TOOL_EXPLOSION
- **What happened:** 200+ tools, each injecting definitions
- **Result:** Context death, mid-session amnesia
- **Fix:** File seam (zero tools in context)

### CLAUDE_AS_SYSTEM
- **What happened:** Claude held state + memory + execution + conversation
- **Result:** Context collapse = everything lost
- **Fix:** Claude holds conversation ONLY

### RAW_OUTPUT_FLOODING
- **What happened:** Tool outputs dumped into context
- **Result:** Token death
- **Fix:** Workers write files, only summaries return

### SILENT_DEGRADATION
- **What happened:** System rotted without signaling
- **Result:** Trust erosion
- **Fix:** Health always first-class, Signalman detects decay

### FORWARD_FILL
- **What happened:** Gaps hidden by filling forward
- **Result:** Data lies, false confidence
- **Fix:** River pattern (gaps visible, never masked)

---

## Frontier Sources

| Source | Key Pattern | Application |
|--------|-------------|-------------|
| **Yegge** | Beads (immutable events) | Continuity, audit trail |
| **Willison** | "Chat is not state" / Datasette | Memory palace queries |
| **Banteg** | Execution separation, fuzz | Cognitive arbitrage, chaos testing |
| **OODA** | Orient phase protection | EXPLORE as unpolluted clarity |

---

## Quick Reference

```
THINKING: Claude Desktop → EXPLORE → no file seam → pure conversation
ACTING:   Claude Desktop → INTENT → intent.yaml → Phoenix → response.md → Lens → Claude

STATE: Lives in Boardroom (Beads + Athena), never in Claude's context
CONTINUITY: Beads survive instance death, checkpoint preserves momentum
EXECUTION: HIVE workers (disposable), main Claude never executes
VALIDATION: Inquisitor gate, State Hash anchor, Evidence bundle required
RECOVERY: Graceful checkpoint, hot-load from snapshots, never surprise
```

---

**The mantra:** "Claude is the mind. Phoenix is the body. Beads are the memory."
