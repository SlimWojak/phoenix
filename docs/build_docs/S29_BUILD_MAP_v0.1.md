# S29 BUILD MAP v0.1

**Sprint:** S29_COGNITIVE_FOUNDATION  
**Theme:** "The thinking partner comes alive"  
**Duration:** 1-2 weeks  
**Status:** DRAFT FOR ADVISOR REVIEW  
**Exit Gate:** Olya can EXPLORE with Claude AND receive morning briefing

---

## ADVISOR POLLING CONTEXT

```yaml
approach: S29 deep → advisor poll → synthesize → harden → S30-33

advisors_ready:
  GPT: Architect Lint (edge cases, spec gaps)
  GROK: Frontier Patterns (magic, YOLO opportunities)
  OWL: Wise Owl (structural audit, full repo context)
  OPUS: Builder (implementation readiness check)

process:
  1. CTO produces S29_BUILD_MAP_v0.1 (this document)
  2. Fan out to advisors (parallel, independent)
  3. G curates DENSE returns
  4. CTO synthesizes → v0.2
  5. Exit gates locked → OPUS can build
```

---

## 1. SURFACES

### 1.1 File System Surfaces

```yaml
INTENT_SURFACE:
  path: /phoenix/intents/incoming/
  files:
    - intent.yaml (Claude writes)
    - .processed/ (watcher moves after handling)
  ownership: Claude Desktop → Phoenix Watcher
  
RESPONSE_SURFACE:
  path: /phoenix/responses/
  files:
    - response.md (Phoenix writes)
    - .archive/ (Lens moves after injection)
  ownership: Phoenix Dispatcher → Lens Daemon

BRIEFING_SURFACE:
  path: /phoenix/briefings/
  files:
    - morning_{date}.md (Briefing Worker writes)
    - latest.md (symlink to most recent)
  ownership: Briefing Worker → Lens Daemon
```

### 1.2 Schema Surfaces

```yaml
INTENT_SCHEMA:
  version: "1.0"
  fields:
    intent_id: uuid
    type: enum[EXPLORE, DISPATCH, READ, APPROVE, QUERY_MEMORY, HALT]
    subtype: string (e.g., MORNING_BRIEF, HUNT, SCAN)
    timestamp: ISO8601
    payload: object (type-specific)
    session_context:
      session_id: uuid
      session_start: ISO8601
      last_known_state_hash: string (required for T2)
    mode: enum[THINKING, ACTING]
  
RESPONSE_SCHEMA:
  version: "1.0"
  fields:
    response_id: uuid
    intent_id: uuid (correlation)
    status: enum[COMPLETE, PARTIAL, FAILED, STATE_CONFLICT]
    timestamp: ISO8601
    summary: string (token-efficient, <500 tokens)
    bead_id: string (if persisted)
    detail_path: string (full report location)
    next_actions: list[string] (suggested follow-ups)
```

### 1.3 Process Surfaces

```yaml
DAEMONS:
  phoenix_watcher:
    location: phoenix/watcher/daemon.py
    watches: /phoenix/intents/incoming/
    triggers: intent.yaml creation
    
  lens_daemon:
    location: phoenix/lens/daemon.py
    watches: /phoenix/responses/
    triggers: response.md creation
    action: inject into Claude Desktop (mechanism TBD)
    
  briefing_cron:
    schedule: "0 6 * * *" (6am daily)
    action: emit DISPATCH:MORNING_BRIEF intent
```

---

## 2. SEAMS

### 2.1 Claude Desktop ↔ File Seam

```yaml
SEAM_CD_FS:
  boundary: Claude context | Filesystem
  contract:
    claude_writes: intent.yaml (ONLY when mode=ACTING)
    claude_reads: response.md (via Lens injection)
    invariant: INV-EXPLORE-3 (EXPLORE cannot emit intent.yaml)
  
  validation:
    - intent.yaml must validate against INTENT_SCHEMA
    - malformed intent → FAILED response (not silent drop)
    
  failure_modes:
    - Claude writes during EXPLORE → REJECT (how enforced?)
    - Schema violation → FAILED response with reason
    - File permission error → FAILED response + alert
```

### 2.2 Phoenix Watcher ↔ Inquisitor

```yaml
SEAM_WATCHER_INQ:
  boundary: Watcher detection | Doctrine validation
  contract:
    watcher_provides: parsed intent object
    inquisitor_returns: PASS | FAIL(reason)
    
  inquisitor_checks:
    - schema_valid: true
    - tier_appropriate: T0/T1 allowed, T2 requires approval_token
    - halt_state: system not halted
    - doctrine_compliant: intent matches allowed patterns
    - state_hash_valid: (for T2) matches current system state
    
  failure_modes:
    - Inquisitor FAIL → immediate FAILED response (no dispatch)
    - Inquisitor timeout → FAILED response + alert
```

### 2.3 Inquisitor ↔ Dispatcher

```yaml
SEAM_INQ_DISPATCH:
  boundary: Validation | Routing
  contract:
    inquisitor_provides: validated intent + PASS
    dispatcher_routes_to: appropriate HIVE worker
    
  routing_table:
    DISPATCH:MORNING_BRIEF → briefing_worker
    DISPATCH:HUNT → hunt_worker (S30)
    DISPATCH:SCAN → scan_worker (S31)
    READ:* → read_handler (inline, no worker)
    HALT → halt_handler (immediate, INV-HALT-1)
    
  failure_modes:
    - Unknown intent type → FAILED response
    - Worker unavailable → FAILED response + retry queue
```

### 2.4 Dispatcher ↔ HIVE Worker

```yaml
SEAM_DISPATCH_WORKER:
  boundary: Coordination | Execution
  contract:
    dispatcher_provides: intent payload + context
    worker_returns: result object + bead_id (if persisted)
    
  worker_contract:
    - respects halt (checks before heavy work)
    - emits bead (for auditable work)
    - returns structured result (not raw output)
    - timeout: 5 minutes (configurable)
    
  failure_modes:
    - Worker crash → FAILED response + bead (WORKER_CRASH)
    - Worker timeout → FAILED response + alert
    - Worker exceeds token budget → truncate + warn
```

### 2.5 Worker ↔ Response Surface

```yaml
SEAM_WORKER_RESPONSE:
  boundary: Execution result | File output
  contract:
    worker_provides: result object
    dispatcher_writes: response.md (compressed summary)
    dispatcher_writes: detail file (full output, if large)
    
  compression_rules:
    - summary: ≤500 tokens (what operator needs)
    - detail_path: points to full report
    - bead_id: for queryable history
    
  failure_modes:
    - Write failure → alert + retry
    - Compression failure → include truncation warning
```

### 2.6 Lens ↔ Claude Desktop

```yaml
SEAM_LENS_CD:
  boundary: Response file | Claude context
  contract:
    lens_detects: new response.md
    lens_injects: content into Claude conversation
    
  mechanism_options:
    OPTION_A: Daemon with clipboard/paste automation
    OPTION_B: Single MCP tool (read_phoenix_response)
    OPTION_C: Claude Desktop API (if available)
    
  decision: TBD (prototype all three, pick simplest working)
  
  invariant: INV-LENS-1 (exactly ONE mechanism, ZERO tool definitions for Option A/C)
  
  failure_modes:
    - Injection fails → manual fallback (Olya attaches file)
    - Multiple injections → dedup by response_id
```

---

## 3. WIRING

### 3.1 EXPLORE Flow (No File Seam)

```
┌─────────────────────────────────────────────────────────────────┐
│  EXPLORE FLOW (mode=THINKING)                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Olya: "I'm noticing something about London entries..."         │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  Claude Desktop (Thinking Partner)  │                        │
│  │  - Classifies as EXPLORE            │                        │
│  │  - File seam CLOSED                 │                        │
│  │  - May query Athena (read-only)     │                        │
│  │  - Responds directly                │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  Claude: "Let me help structure that..."                        │
│                                                                 │
│  [NO intent.yaml written]                                       │
│  [NO workers triggered]                                         │
│  [NO beads emitted]                                             │
│  [Pure conversation]                                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 DISPATCH Flow (File Seam Active)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  DISPATCH FLOW (mode=ACTING)                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Olya: "Give me the morning briefing"                                        │
│                         │                                                    │
│                         ▼                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │  Claude Desktop                     │                                     │
│  │  - Classifies as DISPATCH:BRIEF    │                                     │
│  │  - Writes intent.yaml              │─────┐                                │
│  │  - Tells Olya: "Getting briefing"  │     │                                │
│  └─────────────────────────────────────┘     │                                │
│                                              │                                │
│                                              ▼                                │
│                         ┌────────────────────────────────┐                   │
│                         │  /phoenix/intents/incoming/    │                   │
│                         │  intent.yaml                   │                   │
│                         └────────────────────────────────┘                   │
│                                              │                                │
│                                              ▼                                │
│                         ┌────────────────────────────────┐                   │
│                         │  Phoenix Watcher (daemon)      │                   │
│                         │  - Detects new file            │                   │
│                         │  - Parses intent               │                   │
│                         │  - Moves to .processed/        │                   │
│                         └────────────────────────────────┘                   │
│                                              │                                │
│                                              ▼                                │
│                         ┌────────────────────────────────┐                   │
│                         │  Inquisitor                    │                   │
│                         │  - Validates schema            │                   │
│                         │  - Checks doctrine             │                   │
│                         │  - Checks halt state           │                   │
│                         │  - Returns PASS/FAIL           │                   │
│                         └────────────────────────────────┘                   │
│                                              │                                │
│                              PASS            │           FAIL                 │
│                         ┌────────────────────┴────────────────┐              │
│                         │                                     │              │
│                         ▼                                     ▼              │
│          ┌──────────────────────────┐          ┌──────────────────────────┐  │
│          │  Dispatcher              │          │  Write FAILED response   │  │
│          │  - Routes to worker      │          │  - reason: {why}         │  │
│          │  - Tracks execution      │          │  - intent_id: {id}       │  │
│          └──────────────────────────┘          └──────────────────────────┘  │
│                         │                                                    │
│                         ▼                                                    │
│          ┌──────────────────────────┐                                        │
│          │  Briefing Worker (HIVE)  │                                        │
│          │  - Queries River data    │                                        │
│          │  - Aggregates metrics    │                                        │
│          │  - Formats briefing      │                                        │
│          │  - Emits BRIEFING bead   │                                        │
│          │  - Returns result        │                                        │
│          └──────────────────────────┘                                        │
│                         │                                                    │
│                         ▼                                                    │
│          ┌──────────────────────────┐                                        │
│          │  Dispatcher              │                                        │
│          │  - Compresses summary    │                                        │
│          │  - Writes response.md    │                                        │
│          │  - Writes detail file    │                                        │
│          └──────────────────────────┘                                        │
│                         │                                                    │
│                         ▼                                                    │
│          ┌──────────────────────────┐                                        │
│          │  /phoenix/responses/     │                                        │
│          │  response.md             │                                        │
│          └──────────────────────────┘                                        │
│                         │                                                    │
│                         ▼                                                    │
│          ┌──────────────────────────┐                                        │
│          │  Lens Daemon             │                                        │
│          │  - Detects new response  │                                        │
│          │  - Injects into Claude   │                                        │
│          │  - Archives response     │                                        │
│          └──────────────────────────┘                                        │
│                         │                                                    │
│                         ▼                                                    │
│  ┌─────────────────────────────────────┐                                     │
│  │  Claude Desktop                     │                                     │
│  │  - Receives injected response      │                                     │
│  │  - Presents to Olya naturally      │                                     │
│  └─────────────────────────────────────┘                                     │
│                         │                                                    │
│                         ▼                                                    │
│  Claude: "Good morning. Here's your briefing..."                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Morning Briefing Content Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  BRIEFING WORKER INTERNALS                                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUT: DISPATCH:MORNING_BRIEF intent                           │
│                                                                 │
│  ┌─────────────────────────────────────┐                        │
│  │  1. HEALTH CHECK                    │                        │
│  │  - governance/halt.py status        │                        │
│  │  - halt latency (last measured)     │                        │
│  │  - system tier (NORMAL/DEGRADED)    │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  2. OVERNIGHT SUMMARY               │                        │
│  │  - River: position changes          │                        │
│  │  - River: P&L since last briefing   │                        │
│  │  - Beads: any HALT/VIOLATION beads  │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  3. SETUP SCAN (stub for S29)       │                        │
│  │  - Placeholder: "CSO pending S31"   │                        │
│  │  - OR: basic River data summary     │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  4. DOCTRINE STATUS                 │                        │
│  │  - Any contract violations?         │                        │
│  │  - Any pending challenges?          │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  OUTPUT: Formatted briefing (markdown)                          │
│  BEAD: BRIEFING_2026_01_28_001                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. FRONTIER PATTERNS

```yaml
FILE_SEAM:
  applies: All Claude ↔ Phoenix communication
  why: Zero MCP tools = zero context bloat
  implementation: intent.yaml (write) + response.md (read via Lens)
  
HIVE:
  applies: Briefing worker (and all future workers)
  why: Disposable contexts, main Claude stays lean
  implementation: Dispatcher routes to tmux-managed CLI Claude or local LLM
  
COGNITIVE_ARBITRAGE:
  applies: S29 partially (briefing can use local LLM for aggregation)
  why: Save API costs, reduce latency
  implementation: Briefing worker can be Sonnet CLI, not API
  
BEADS:
  applies: Briefing persistence
  why: Queryable history, audit trail
  implementation: BRIEFING bead emitted per briefing
  
TWO_PLANES:
  applies: Architecture validation
  why: Cognitive (Claude Desktop) vs Notification (Telegram)
  implementation: S29 establishes cognitive plane only; Telegram is S31
```

---

## 5. INVARIANTS TO PROVE

```yaml
S29_INVARIANTS:
  INV-EXPLORE-3:
    statement: "EXPLORE cannot emit intent.yaml"
    test: test_explore_no_intent.py
    proof: Attempt EXPLORE → verify no file created
    mechanism: TBD (how does Claude know it's in EXPLORE?)
    
  INV-LENS-1:
    statement: "Exactly ONE response mechanism, ZERO tool definitions"
    test: test_lens_single_mechanism.py
    proof: Count mechanisms = 1, count tool defs in Claude = 0
    
  INV-CONTEXT-1:
    statement: "Claude holds conversation only"
    test: test_claude_context_lean.py
    proof: After 10 briefing cycles, Claude context contains no raw data
    
  INV-HALT-RESPECTED:
    statement: "Watcher/Inquisitor respect halt state"
    test: test_halt_blocks_dispatch.py
    proof: Emit intent while halted → FAILED response
```

---

## 6. CHAOS VECTORS

```yaml
CHAOS_S29:
  CV1_MALFORMED_INTENT:
    inject: Invalid YAML, missing fields, wrong types
    expect: FAILED response with parse error, not crash
    
  CV2_RAPID_INTENTS:
    inject: 100 intents in 1 second
    expect: Queue handles gracefully, no lost intents
    
  CV3_WORKER_CRASH:
    inject: Briefing worker throws exception
    expect: FAILED response, bead logged, no hang
    
  CV4_LENS_UNAVAILABLE:
    inject: Lens daemon stopped
    expect: Response still written, manual fallback works
    
  CV5_FILESYSTEM_FULL:
    inject: Fill /phoenix/responses/
    expect: Alert raised, graceful failure
    
  CV6_HALTED_SYSTEM:
    inject: Set halt=True, then emit DISPATCH
    expect: FAILED response (doctrine: halted)
    
  CV7_INTENT_DURING_EXPLORE:
    inject: Force intent.yaml write during EXPLORE mode
    expect: ??? (mechanism unclear — GAP IDENTIFIED)
```

---

## 7. EXIT GATES

```yaml
GATE_S29_1:
  name: FILE_SEAM_WORKS
  criterion: Intent written → response returned → Lens injects
  test: test_e2e_file_seam.py
  evidence: Timestamped logs showing full cycle <10s
  
GATE_S29_2:
  name: BRIEFING_DELIVERED
  criterion: Morning briefing contains health + overnight + doctrine
  test: test_briefing_content.py
  evidence: Briefing markdown validates against template
  
GATE_S29_3:
  name: EXPLORE_SAFE
  criterion: EXPLORE mode produces no files, no beads, no workers
  test: test_explore_isolation.py
  evidence: 10 EXPLORE turns → 0 files in /phoenix/intents/
  
GATE_S29_4:
  name: INQUISITOR_REJECTS
  criterion: Invalid intents rejected with reason
  test: test_inquisitor_rejection.py
  evidence: 5 invalid intents → 5 FAILED responses with reasons
  
GATE_S29_5:
  name: OLYA_UX_VALIDATED
  criterion: Olya confirms "this feels like thinking partner"
  test: Manual (Olya session)
  evidence: Verbal/written confirmation

BINARY_EXIT:
  statement: "Olya can EXPLORE with Claude AND receive morning briefing"
  all_gates_pass: TRUE → S29 COMPLETE
```

---

## 8. HANDOFF ARTIFACTS

```yaml
S30_RECEIVES:
  working_file_seam:
    - intent.yaml schema (locked)
    - response.md schema (locked)
    - Watcher daemon (operational)
    - Inquisitor (operational)
    - Lens daemon (operational)
    
  dispatcher_routing:
    - DISPATCH routing table (extensible)
    - Worker contract (interface defined)
    
  briefing_worker:
    - Template for additional workers
    - Bead emission pattern
    
  proven_invariants:
    - INV-EXPLORE-3 (tested)
    - INV-LENS-1 (tested)
    - INV-CONTEXT-1 (tested)
```

---

## 9. OPEN QUESTIONS (ADVISOR INPUT NEEDED)

### Q1: EXPLORE Enforcement

```yaml
question: How does Claude "know" it's in EXPLORE mode and cannot emit intent?

options:
  A: Claude self-classifies (policy only, no enforcement)
  B: Separate Claude Desktop config for EXPLORE vs ACTING
  C: Intent schema requires mode field, Inquisitor rejects EXPLORE intents
  D: File seam directory is mode-specific (/explore/ vs /acting/)

risk: Without enforcement, INV-EXPLORE-3 is policy not invariant
```

### Q2: Lens Mechanism

```yaml
question: How does Lens inject response into Claude Desktop?

options:
  A: Clipboard automation (AppleScript/pyautogui)
  B: Single MCP tool (minimal context cost)
  C: Claude Desktop API (if exists)
  D: Olya manually attaches (fallback)

risk: Option A is fragile, Option B violates spirit of "zero tools"
```

### Q3: Session State

```yaml
question: How does Claude track session_id and session_start for state_hash?

options:
  A: Claude maintains in conversation (lost on checkpoint)
  B: Lens injects session context on each response
  C: Separate session file that Claude reads

risk: Session state is needed for STATE_CONFLICT validation
```

### Q4: Athena Read During EXPLORE

```yaml
question: Can EXPLORE query Athena (read-only)?

current_assumption: Yes (read-only is safe)
mechanism: Direct Datasette query? Or via intent?

risk: If via intent, EXPLORE emits file (violates INV-EXPLORE-3)
```

---

## 10. M2M LEARNINGS

```yaml
WHY_FILE_SEAM:
  origin: NEX death by 200 MCP tools
  insight: Even 5-6 tools inject definitions, flood outputs
  decision: Zero tools in Claude context
  tradeoff: Latency (file I/O) for context preservation
  
WHY_LENS:
  origin: "Death by a thousand clicks"
  insight: Manual attachment kills superpower feeling
  decision: Automatic injection (mechanism TBD)
  tradeoff: Complexity for UX
  
WHY_INQUISITOR:
  origin: Fail-closed design principle
  insight: Early rejection prevents wasted work
  decision: Validate before dispatch, not after
  tradeoff: Latency for safety
  
WHY_BRIEFING_FIRST:
  origin: Primary discovery layer from NEX
  insight: Morning ritual establishes trust
  decision: Simplest worker, proves pattern
  tradeoff: Limited content until CSO (S31)
```

---

## 11. ADVISOR POLLING REQUEST

```yaml
TO_GPT:
  role: Architect Lint
  focus:
    - Schema edge cases (intent/response)
    - Q1-Q4 analysis
    - What breaks the file seam?
    - Checkpoint implications for session_state

TO_GROK:
  role: Frontier Patterns
  focus:
    - Lens mechanism recommendation
    - YOLO opportunities (what can we simplify?)
    - Chaos vectors we missed
    - "Dumbest failure" in this design

TO_OWL:
  role: Wise Owl
  focus:
    - Seam contract integrity
    - Invariant enforcement mechanisms
    - Q1 (EXPLORE enforcement) deep dive
    - Structural coherence across components

TO_OPUS:
  role: Builder
  focus:
    - Implementation readiness
    - What's underspecified for building?
    - Estimated effort per component
    - Risk assessment (what's hardest?)
```

---

**STATUS:** Draft v0.1 ready for advisor polling

**INSTRUCTION:** Review and return DENSE lint/audit per role. Focus on OPEN QUESTIONS Q1-Q4 and assigned FOCUS areas. Format: FLAGS + RECOMMENDATIONS.
