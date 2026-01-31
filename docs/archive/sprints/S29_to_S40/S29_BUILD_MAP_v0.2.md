# S29 BUILD MAP v0.2

**Sprint:** S29_COGNITIVE_FOUNDATION  
**Theme:** "The thinking partner comes alive"  
**Duration:** 1-2 weeks  
**Status:** ADVISOR SYNTHESIS COMPLETE — BUILD READY (CONDITIONAL)  
**Exit Gate:** Olya can EXPLORE with Claude AND receive morning briefing

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-01-27 | Initial draft, 4 open questions |
| v0.2 | 2026-01-27 | All questions resolved, advisor synthesis integrated |

**v0.1 → v0.2 Summary:**
- EXPLORE enforcement: Path-based (/acting/ watched, /explore/ ignored)
- Mode field: Removed from schema (path IS mode)
- Lens: Prototype plan ranked C>B>A, summary-only injection, monotonic ordering
- Session: Authoritative file with atomic checkpoint
- Athena in EXPLORE: Prohibited (deferred to S30)
- New: Daemon heartbeat, typed failures, perceptual latency, 6 additional chaos vectors

---

## 1. SURFACES

### 1.1 File System Surfaces

```yaml
INTENT_SURFACE:
  acting_path: /phoenix/intents/acting/
    - intent.yaml (Claude writes when ACTING)
    - .processed/ (watcher moves after handling)
    - WATCHED by Phoenix Watcher
    
  explore_path: /phoenix/intents/explore/
    - intent.yaml (optional debug writes)
    - NOT WATCHED by Phoenix Watcher
    - Exists for audit/debug only
    
  ownership: Claude Desktop → Phoenix Watcher (acting only)
  
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

SESSION_SURFACE:
  path: /phoenix/sessions/
  files:
    - {session_id}.yaml (Phoenix creates/manages)
  ownership: Phoenix (authoritative) → Claude (read-only copy)

HEALTH_SURFACE:
  path: /phoenix/health/
  files:
    - watcher_heartbeat.ts (Watcher writes every 30s)
    - lens_heartbeat.ts (Lens writes every 30s)
  ownership: Daemons → Monitoring
```

### 1.2 Schema Surfaces

```yaml
INTENT_SCHEMA:
  version: "1.1"
  note: "mode field REMOVED — path IS mode"
  fields:
    intent_id: uuid
    type: enum[DISPATCH, READ, APPROVE, QUERY_MEMORY, HALT]
    subtype: string (e.g., MORNING_BRIEF, HUNT, SCAN)
    timestamp: ISO8601
    payload: object (type-specific, max 1MB)
    session_id: uuid (copied from session file)
    last_known_state_hash: string (required for T2)
    
  removed_fields:
    - mode (path determines mode)
  
RESPONSE_SCHEMA:
  version: "1.1"
  fields:
    response_id: uuid
    intent_id: uuid (correlation)
    status: enum[COMPLETE, PARTIAL, FAILED, STATE_CONFLICT]
    error_type: enum[
      SCHEMA_ERROR,
      DOCTRINE_REJECT,
      HALTED,
      TIMEOUT,
      INFRA_ERROR,
      STATE_CONFLICT,
      DUPLICATE_INTENT,
      PAYLOAD_TOO_LARGE
    ] (only if status=FAILED)
    timestamp: ISO8601
    summary: string (≤500 tokens)
    bead_id: string (if persisted)
    detail_path: string (full report location)
    next_actions: list[string] (suggested follow-ups)

SESSION_SCHEMA:
  version: "1.0"
  fields:
    session_id: uuid
    started_at: ISO8601
    last_known_state_hash: string
    last_response_ts: ISO8601
    status: enum[ACTIVE, CHECKPOINTING, CHECKPOINTED, CLOSED]
```

### 1.3 Process Surfaces

```yaml
DAEMONS:
  phoenix_watcher:
    location: phoenix/watcher/daemon.py
    watches: /phoenix/intents/acting/ (ONLY)
    ignores: /phoenix/intents/explore/
    heartbeat: /phoenix/health/watcher_heartbeat.ts (every 30s)
    triggers: intent.yaml creation in /acting/
    
  lens_daemon:
    location: phoenix/lens/daemon.py
    watches: /phoenix/responses/
    heartbeat: /phoenix/health/lens_heartbeat.ts (every 30s)
    checks: watcher_heartbeat.ts age (alert if >60s)
    action: inject summary into Claude Desktop
    mechanism: TBD (prototype C>B>A)
    
  briefing_cron:
    schedule: "0 6 * * *" (6am daily)
    action: emit DISPATCH:MORNING_BRIEF intent to /acting/
```

---

## 2. SEAMS

### 2.1 Claude Desktop ↔ File Seam

```yaml
SEAM_CD_FS:
  boundary: Claude context | Filesystem
  contract:
    ACTING_mode:
      claude_writes: /phoenix/intents/acting/intent.yaml
      watcher: processes immediately
    EXPLORE_mode:
      claude_writes: /phoenix/intents/explore/intent.yaml (optional, debug only)
      watcher: ignores entirely
      OR: claude writes nothing (pure conversation)
    claude_reads: response.md (via Lens injection, summary only)
    
  enforcement:
    L1_PHYSICAL: Watcher ONLY watches /acting/
    L2_SCHEMA: No mode field — path IS mode
    L3_POLICY: Claude policy to not write /acting/ during EXPLORE
    
  invariants:
    INV-EXPLORE-3: /acting/ triggers machinery; /explore/ does not
    INV-EXPLORE-4: EXPLORE has no external system access
    
  validation:
    - intent.yaml must validate against INTENT_SCHEMA
    - payload max 1MB
    - malformed intent → FAILED:SCHEMA_ERROR (not silent drop)
    
  failure_modes:
    - Schema violation → FAILED:SCHEMA_ERROR with reason
    - Payload too large → FAILED:PAYLOAD_TOO_LARGE
    - File permission error → FAILED:INFRA_ERROR + alert
```

### 2.2 Phoenix Watcher ↔ Inquisitor

```yaml
SEAM_WATCHER_INQ:
  boundary: Watcher detection | Doctrine validation
  contract:
    watcher_provides: parsed intent object + source_path
    inquisitor_returns: PASS | FAIL(error_type, reason)
    
  inquisitor_checks:
    - schema_valid: true → else SCHEMA_ERROR
    - payload_size: <1MB → else PAYLOAD_TOO_LARGE
    - session_valid: session_id exists in /sessions/ → else DOCTRINE_REJECT
    - session_status: ACTIVE → else DOCTRINE_REJECT
    - tier_appropriate: T0/T1 allowed; T2 requires approval_token
    - halt_state: system not halted → else HALTED
    - doctrine_compliant: intent matches allowed patterns
    - state_hash_valid: (for T2) matches current → else STATE_CONFLICT
    - duplicate_check: intent_id not seen → else DUPLICATE_INTENT
    
  failure_modes:
    - Inquisitor FAIL → immediate FAILED response (no dispatch)
    - Inquisitor timeout (>5s) → FAILED:TIMEOUT + alert
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
    DISPATCH:QUERY_MEMORY → athena_worker (S30)
    READ:* → read_handler (inline, no worker)
    HALT → halt_handler (immediate, INV-HALT-1)
    
  failure_modes:
    - Unknown intent type → FAILED:DOCTRINE_REJECT
    - Worker unavailable → FAILED:INFRA_ERROR + retry queue
```

### 2.4 Dispatcher ↔ HIVE Worker

```yaml
SEAM_DISPATCH_WORKER:
  boundary: Coordination | Execution
  contract:
    dispatcher_provides: intent payload + session context
    worker_returns: result object + bead_id (if persisted)
    
  worker_contract:
    - respects halt (checks before heavy work)
    - emits bead (for auditable work)
    - returns structured result (not raw output)
    - timeout: 5 minutes (configurable)
    - max_output: result ≤10KB (dispatcher compresses further)
    
  failure_modes:
    - Worker crash → FAILED:INFRA_ERROR + WORKER_CRASH bead
    - Worker timeout → FAILED:TIMEOUT + alert
    - Worker exceeds output → truncate + warn in response
```

### 2.5 Worker ↔ Response Surface

```yaml
SEAM_WORKER_RESPONSE:
  boundary: Execution result | File output
  contract:
    worker_provides: result object
    dispatcher_compresses: summary ≤500 tokens
    dispatcher_writes: response.md (summary only)
    dispatcher_writes: detail file at detail_path (full output)
    
  compression_rules:
    - summary: ≤500 tokens (what operator needs to continue thinking)
    - detail_path: points to full report (Olya can click if curious)
    - bead_id: for queryable history
    - NEVER inject raw worker output into response.md
    
  failure_modes:
    - Write failure → alert + retry (3x)
    - Compression failure → include truncation warning in summary
```

### 2.6 Lens ↔ Claude Desktop

```yaml
SEAM_LENS_CD:
  boundary: Response file | Claude context
  contract:
    lens_detects: new response.md
    lens_validates: response.timestamp > last_injected_timestamp
    lens_injects: summary field ONLY (≤500 tokens)
    lens_archives: moves to .archive/ after injection
    
  mechanism_prototype_plan:
    priority_1: OPTION_C — Claude Desktop API (if exists)
    priority_2: OPTION_B — Single MCP tool (≤50 tokens def)
    priority_3: OPTION_A — Daemon + clipboard automation
    fallback: Manual attachment (documented, not shameful)
    
  prototype_schedule:
    day_1: Research Claude Desktop API availability
    day_2: Build Option B as working fallback
    day_3: Attempt Option A for comparison
    day_4: Evaluate latency, reliability, context cost
    
  invariants:
    INV-LENS-1: Exactly ONE mechanism, ZERO tool defs (unless Option B)
    INV-LENS-ORDER-1: Responses injected strictly monotonic by timestamp
    INV-CONTEXT-1: Only summary (≤500 tokens) injected
    
  injection_contract:
    - Summary only (never raw output)
    - detail_path provided for expansion
    - bead_id for audit reference
    - Dedup by response_id (no double injection)
    
  failure_modes:
    - Injection fails → manual fallback (Olya attaches file)
    - Out-of-order response → reject (log warning)
    - Multiple injections same ID → dedup, inject once
```

### 2.7 Session Management

```yaml
SEAM_SESSION:
  boundary: Phoenix session state | Claude awareness
  contract:
    phoenix_creates: session file on first intent or explicit start
    phoenix_manages: state_hash updates, status transitions
    lens_injects: session header once per session (not every turn)
    claude_copies: session_id into intent when writing
    
  lifecycle:
    1. Session starts → Phoenix creates /sessions/{id}.yaml (status=ACTIVE)
    2. Lens injects session header into Claude (once)
    3. Claude copies session_id when writing intent
    4. Watcher/Inquisitor verify session_id against file
    5. State changes → Phoenix updates state_hash in session file
    6. Checkpoint → atomic transition (see below)
    
  checkpoint_atomicity:
    1. Session status → CHECKPOINTING
    2. File seam temporarily locked (Watcher ignores this session's new intents)
    3. CONTEXT_SNAPSHOT bead written with cognitive_momentum
    4. New session file created (status=ACTIVE, fresh session_id)
    5. Old session status → CHECKPOINTED
    6. Lens injects new session header
    7. ACTING resumes
    
  invariant:
    INV-SESSION-1: Session state lives in /phoenix/sessions/, never in Claude
    
  failure_modes:
    - Session file missing → FAILED:DOCTRINE_REJECT
    - Session status not ACTIVE → FAILED:DOCTRINE_REJECT
    - Checkpoint interrupted → rollback to ACTIVE, retry
```

### 2.8 Daemon Health

```yaml
SEAM_DAEMON_HEALTH:
  boundary: Daemon liveness | Monitoring
  contract:
    each_daemon_writes: heartbeat file every 30s
    each_daemon_checks: peer heartbeat age
    alert_trigger: peer heartbeat age > 60s → Telegram alert
    
  heartbeat_format:
    timestamp: ISO8601
    daemon: string
    status: enum[HEALTHY, DEGRADED]
    last_processed: ISO8601 (last intent/response handled)
    
  monitoring:
    watcher_checks: lens_heartbeat.ts
    lens_checks: watcher_heartbeat.ts
    alert_message: "🐗 DAEMON DOWN: {name} — manual intervention required"
    
  failure_modes:
    - Daemon crash → peer detects within 60s → alert
    - Both daemons crash → external monitor required (Telegram bot health check)
```

---

## 3. WIRING

### 3.1 EXPLORE Flow (No File Seam)

```
┌─────────────────────────────────────────────────────────────────┐
│  EXPLORE FLOW (Cognitive Only)                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Olya: "I'm noticing something about London entries..."         │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  Claude Desktop (Thinking Partner)  │                        │
│  │  - Classifies as EXPLORE            │                        │
│  │  - File seam CLOSED                 │                        │
│  │  - NO Athena access (INV-EXPLORE-4) │                        │
│  │  - NO River access                  │                        │
│  │  - Responds from conversation only  │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  Claude: "Let me help structure that..."                        │
│                                                                 │
│  PATH: /phoenix/intents/acting/ — UNTOUCHED                     │
│  PATH: /phoenix/intents/explore/ — OPTIONAL (debug only)        │
│                                                                 │
│  [NO intent in /acting/]                                        │
│  [NO workers triggered]                                         │
│  [NO beads emitted]                                             │
│  [NO external queries]                                          │
│  [Pure conversation]                                            │
│                                                                 │
│  PROMOTION TO ACTING:                                           │
│  Olya: "Let's test that hypothesis"                             │
│  Claude: "Writing intent..." → /acting/intent.yaml              │
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
│  │  - Immediate ack: "Working on it"  │  ← INV-UX-1                          │
│  │  - Writes to /acting/intent.yaml   │─────┐                                │
│  └─────────────────────────────────────┘     │                                │
│                                              │                                │
│                                              ▼                                │
│                    ┌─────────────────────────────────────┐                   │
│                    │  /phoenix/intents/acting/           │                   │
│                    │  intent.yaml                        │                   │
│                    │  (session_id copied from session)   │                   │
│                    └─────────────────────────────────────┘                   │
│                                              │                                │
│                                              ▼                                │
│                    ┌─────────────────────────────────────┐                   │
│                    │  Phoenix Watcher (daemon)           │                   │
│                    │  - Detects new file in /acting/     │                   │
│                    │  - Parses intent                    │                   │
│                    │  - Moves to .processed/             │                   │
│                    └─────────────────────────────────────┘                   │
│                                              │                                │
│                                              ▼                                │
│                    ┌─────────────────────────────────────┐                   │
│                    │  Inquisitor                         │                   │
│                    │  - Validates schema                 │                   │
│                    │  - Validates session (ACTIVE)       │                   │
│                    │  - Checks doctrine                  │                   │
│                    │  - Checks halt state                │                   │
│                    │  - Returns PASS/FAIL(error_type)    │                   │
│                    └─────────────────────────────────────┘                   │
│                                              │                                │
│                              PASS            │           FAIL                 │
│                    ┌─────────────────────────┴─────────────────┐             │
│                    │                                           │             │
│                    ▼                                           ▼             │
│     ┌──────────────────────────┐            ┌──────────────────────────────┐ │
│     │  Dispatcher              │            │  Write FAILED response       │ │
│     │  - Routes to worker      │            │  - status: FAILED            │ │
│     │  - Tracks execution      │            │  - error_type: {type}        │ │
│     └──────────────────────────┘            │  - summary: {reason}         │ │
│                    │                         └──────────────────────────────┘ │
│                    ▼                                                          │
│     ┌──────────────────────────┐                                             │
│     │  Briefing Worker (HIVE)  │                                             │
│     │  - Queries governance    │                                             │
│     │  - Aggregates metrics    │                                             │
│     │  - Formats briefing      │                                             │
│     │  - Emits BRIEFING bead   │                                             │
│     │  - Returns result        │                                             │
│     └──────────────────────────┘                                             │
│                    │                                                          │
│                    ▼                                                          │
│     ┌──────────────────────────┐                                             │
│     │  Dispatcher              │                                             │
│     │  - Compresses to ≤500 tk │                                             │
│     │  - Writes response.md    │                                             │
│     │  - Writes detail file    │                                             │
│     └──────────────────────────┘                                             │
│                    │                                                          │
│                    ▼                                                          │
│     ┌──────────────────────────┐                                             │
│     │  /phoenix/responses/     │                                             │
│     │  response.md (summary)   │                                             │
│     │  /reports/{detail}.md    │                                             │
│     └──────────────────────────┘                                             │
│                    │                                                          │
│                    ▼                                                          │
│     ┌──────────────────────────┐                                             │
│     │  Lens Daemon             │                                             │
│     │  - Detects new response  │                                             │
│     │  - Validates timestamp   │  ← INV-LENS-ORDER-1                         │
│     │  - Injects SUMMARY ONLY  │  ← INV-CONTEXT-1                            │
│     │  - Archives response     │                                             │
│     └──────────────────────────┘                                             │
│                    │                                                          │
│                    ▼                                                          │
│  ┌─────────────────────────────────────┐                                     │
│  │  Claude Desktop                     │                                     │
│  │  - Receives summary injection      │                                     │
│  │  - Presents to Olya naturally      │                                     │
│  │  - Can reference detail_path       │                                     │
│  └─────────────────────────────────────┘                                     │
│                    │                                                          │
│                    ▼                                                          │
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
│  │  - daemon health (heartbeat ages)   │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  2. OVERNIGHT SUMMARY               │                        │
│  │  - Position changes (if any)        │                        │
│  │  - P&L since last briefing          │                        │
│  │  - Beads: any HALT/VIOLATION beads  │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  3. SETUP SCAN (S29 stub)           │                        │
│  │  - "CSO pending S31"                │                        │
│  │  - OR: basic market data summary    │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  4. DOCTRINE STATUS                 │                        │
│  │  - Contract violations (last 24h)   │                        │
│  │  - Pending challenges               │                        │
│  │  - Invariant test results           │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  OUTPUT: Formatted briefing (≤500 tokens summary)               │
│  DETAIL: /phoenix/briefings/morning_{date}.md (full)            │
│  BEAD: BRIEFING_2026_01_28_001                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Checkpoint Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  CHECKPOINT FLOW (Graceful Context Reset)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRIGGER: Claude detects context pressure OR Olya requests      │
│                                                                 │
│  ┌─────────────────────────────────────┐                        │
│  │  1. CHECKPOINT REQUEST              │                        │
│  │  - Claude: "Shall I checkpoint?"    │                        │
│  │  - Olya: [CHECKPOINT]               │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  2. SESSION LOCK                    │                        │
│  │  - Phoenix: session.status →        │                        │
│  │    CHECKPOINTING                    │                        │
│  │  - Watcher: ignores this session    │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  3. SNAPSHOT BEAD                   │                        │
│  │  - CONTEXT_SNAPSHOT bead written    │                        │
│  │  - Includes: intuitions, questions, │                        │
│  │    hypothesis, cognitive_momentum   │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  4. NEW SESSION                     │                        │
│  │  - New session file created         │                        │
│  │  - Fresh session_id                 │                        │
│  │  - status: ACTIVE                   │                        │
│  │  - Old session: CHECKPOINTED        │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────┐                        │
│  │  5. LENS INJECTS NEW HEADER         │                        │
│  │  - Fresh Claude instance            │                        │
│  │  - Loads last 3-5 CONTEXT_SNAPSHOT  │                        │
│  │  - Inherits cognitive_momentum      │                        │
│  └─────────────────────────────────────┘                        │
│                         │                                       │
│                         ▼                                       │
│  Claude (fresh): "I'm back with full context..."                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. FRONTIER PATTERNS

```yaml
FILE_SEAM:
  applies: All Claude ↔ Phoenix communication
  why: Zero MCP tools = zero context bloat
  implementation: 
    write: /phoenix/intents/acting/intent.yaml
    read: response.md via Lens (summary only)
  key_insight: Path IS mode (no mode field needed)
  
HIVE:
  applies: Briefing worker (and all future workers)
  why: Disposable contexts, main Claude stays lean
  implementation: Dispatcher routes to tmux-managed CLI Claude or local LLM
  
COGNITIVE_ARBITRAGE:
  applies: S29 partially (briefing can use local LLM)
  why: Save API costs, reduce latency
  implementation: Briefing worker can be Sonnet CLI, not API
  
BEADS:
  applies: Briefing persistence, checkpoint snapshots
  why: Queryable history, audit trail, continuity
  implementation: BRIEFING bead, CONTEXT_SNAPSHOT bead
  
TWO_PLANES:
  applies: Architecture validation
  why: Cognitive (Claude Desktop) vs Notification (Telegram)
  implementation: S29 establishes cognitive plane only; Telegram is S31
  
COGNITIVE_MOMENTUM:
  applies: Checkpoint continuity
  why: Fresh Claude inherits stance, not just facts
  implementation: CONTEXT_SNAPSHOT includes operator_stance, discarded_paths
```

---

## 5. RESOLVED DECISIONS

### R1: EXPLORE Enforcement

```yaml
DECISION: Path-based enforcement (Option D + C synthesis)

MECHANISM:
  directories:
    /phoenix/intents/acting/   — Watcher WATCHES (triggers machinery)
    /phoenix/intents/explore/  — Watcher IGNORES (debug/audit only)
  
  enforcement_layers:
    L1_PHYSICAL: Watcher only watches /acting/
    L2_SCHEMA: mode field REMOVED (path IS mode)
    L3_POLICY: Claude policy not to write /acting/ during EXPLORE
    
RESULT:
  - Path IS mode (single source of truth)
  - INV-EXPLORE-3 is MECHANICAL not behavioral
  - No mode field to drift or lie about
  
TEST: test_watcher_ignores_explore_dir.py
```

### R2: Lens Mechanism

```yaml
DECISION: Prototype three options, ranked by preference

PRIORITY:
  1. OPTION_C: Claude Desktop API (cleanest if exists)
  2. OPTION_B: Single MCP tool (≤50 tokens, acceptable fallback)
  3. OPTION_A: Daemon + clipboard (fragile but zero tools)
  
FALLBACK: Manual attachment (documented, not shameful)

MANDATORY_ADDITIONS:
  - Lens tracks last_injected_timestamp
  - Reject if response.timestamp < last_seen
  - INV-LENS-ORDER-1: Monotonic injection
  
INJECTION_CONTRACT:
  - Summary only (≤500 tokens)
  - detail_path for expansion
  - Never inject raw worker output
```

### R3: Session State

```yaml
DECISION: Authoritative session file (Option C)

LOCATION: /phoenix/sessions/{session_id}.yaml

LIFECYCLE:
  1. Phoenix creates session file (status=ACTIVE)
  2. Lens injects session header (once per session)
  3. Claude copies session_id into intents
  4. Watcher/Inquisitor verify against session file
  5. Checkpoint: atomic transition with seam lock
  
CHECKPOINT_ATOMICITY:
  1. status → CHECKPOINTING (seam locked)
  2. CONTEXT_SNAPSHOT bead written
  3. New session created (fresh ID)
  4. Old session → CHECKPOINTED
  5. Resume ACTING

WHY: Survives checkpoint, crash, restart. Claude never owns truth.
```

### R4: Athena in EXPLORE

```yaml
DECISION: PROHIBITED in S29

RATIONALE:
  - Any query mechanism either violates INV-EXPLORE-3 or zero-tool doctrine
  - EXPLORE must be "Cognitive Only"
  - Simplest: defer to S30
  
S29_BEHAVIOR:
  - Claude in EXPLORE has NO memory access
  - Can reference conversation only
  - Can say "I'd need to query Athena — want me to?"
  - Promotion to ACTING is explicit
  
S30_PATH:
  - DISPATCH:QUERY_MEMORY intent (ACTING mode)
  - Proper audit trail via bead
  - Worker returns compressed result

NEW_INVARIANT: INV-EXPLORE-4
```

### R5: Daemon Heartbeat

```yaml
DECISION: Mutual health monitoring (GROK catch)

MECHANISM:
  watcher: writes /phoenix/health/watcher_heartbeat.ts (every 30s)
  lens: writes /phoenix/health/lens_heartbeat.ts (every 30s)
  cross_check: each daemon monitors peer's heartbeat
  
ALERT_TRIGGER:
  condition: peer heartbeat age > 60s
  action: Telegram alert "🐗 DAEMON DOWN: {name}"
  
TEST: test_daemon_crash_alert.py
```

### R6: FAILED Status Refinement

```yaml
DECISION: Typed error responses (GPT catch)

error_type enum:
  - SCHEMA_ERROR: Malformed intent
  - DOCTRINE_REJECT: Policy violation
  - HALTED: System is halted
  - TIMEOUT: Worker exceeded time
  - INFRA_ERROR: File/network/process failure
  - STATE_CONFLICT: Stale state hash
  - DUPLICATE_INTENT: Already processed
  - PAYLOAD_TOO_LARGE: Intent > 1MB

WHY: Enables sane alerting, operator understanding, future automation
```

### R7: Perceptual Latency

```yaml
DECISION: Immediate acknowledgment + heartbeat (GPT catch)

BEHAVIOR:
  on_intent_emit:
    Claude: "Working on it — I'll have results shortly."
    
  on_delay_>10s:
    Lens injects: "[Phoenix still working... {elapsed}s]"
    
  on_complete:
    Lens injects: final response summary

NEW_INVARIANT: INV-UX-1 "No silent delays >10s during DISPATCH"
```

---

## 6. INVARIANTS TO PROVE

```yaml
S29_INVARIANTS:
  INV-EXPLORE-3:
    statement: "EXPLORE sessions write to /explore/ (unwatched) or no file; /acting/ triggers machinery"
    test: test_watcher_ignores_explore_dir.py
    proof: Files in /explore/ never processed; files in /acting/ always processed
    
  INV-EXPLORE-4:
    statement: "EXPLORE has no external system access (no Athena, no River, no workers)"
    test: test_explore_isolation.py
    proof: 10 EXPLORE turns → 0 external queries, 0 beads, 0 workers
    
  INV-LENS-1:
    statement: "Exactly ONE response mechanism; ZERO tool definitions unless Option B"
    test: test_lens_single_mechanism.py
    proof: Count mechanisms = 1
    
  INV-LENS-ORDER-1:
    statement: "Responses injected strictly monotonic by timestamp"
    test: test_lens_ordering.py
    proof: Out-of-order response rejected (logged but not injected)
    
  INV-CONTEXT-1:
    statement: "Claude holds conversation only; only summary (≤500 tokens) injected"
    test: test_injection_size.py
    proof: After 10 cycles, no raw data in Claude; all injections ≤500 tokens
    
  INV-UX-1:
    statement: "No silent delays >10s during DISPATCH"
    test: test_perceptual_latency.py
    proof: Slow dispatch → heartbeat injections at 10s intervals
    
  INV-SESSION-1:
    statement: "Session state lives in /phoenix/sessions/, never in Claude"
    test: test_session_authoritative.py
    proof: Session file is source of truth; Claude copies, doesn't own
```

---

## 7. CHAOS VECTORS

```yaml
CV1_MALFORMED_INTENT:
  inject: Invalid YAML, missing fields, wrong types
  expect: FAILED:SCHEMA_ERROR with parse details, no crash
  
CV2_RAPID_INTENTS:
  inject: 100 intents in 1 second
  expect: Queue handles gracefully, no lost intents, no OOM
  
CV3_WORKER_CRASH:
  inject: Briefing worker throws exception mid-execution
  expect: FAILED:INFRA_ERROR, WORKER_CRASH bead, no hang
  
CV4_LENS_UNAVAILABLE:
  inject: Kill Lens daemon
  expect: Response still written, alert within 60s, manual fallback works
  
CV5_FILESYSTEM_FULL:
  inject: Fill /phoenix/responses/
  expect: FAILED:INFRA_ERROR, alert raised, graceful degradation
  
CV6_HALTED_SYSTEM:
  inject: Set halt=True, emit DISPATCH
  expect: FAILED:HALTED (doctrine enforced)
  
CV7_INTENT_IN_EXPLORE_DIR:
  inject: Write intent.yaml to /explore/
  expect: Watcher ignores entirely (no response, no processing)
  
CV8_FS_OVERFLOW:
  inject: Flood /acting/ with 10k intent files
  expect: Watcher caps queue, alerts, doesn't OOM
  
CV9_CORRUPT_YAML:
  inject: Malformed YAML (binary garbage, infinite nesting)
  expect: FAILED:SCHEMA_ERROR, no crash, no hang
  
CV10_SESSION_COLLISION:
  inject: Two Claude sessions emit to same /acting/
  expect: Watcher serializes, no cross-talk, session_id segregates
  
CV11_INTENT_SIZE:
  inject: Intent with 10MB payload
  expect: FAILED:PAYLOAD_TOO_LARGE (cap: 1MB)
  
CV12_CONCURRENT_RESPONSE:
  inject: Multiple responses land out-of-order
  expect: Lens injects monotonically (rejects stale per INV-LENS-ORDER-1)
  
CV13_CHECKPOINT_MID_DISPATCH:
  inject: Checkpoint triggers while intent in-flight
  expect: Intent completes OR cleanly orphans (no ghost execution)
```

---

## 8. EXIT GATES

```yaml
GATE_S29_1:
  name: FILE_SEAM_WORKS
  criterion: Intent in /acting/ → response returned → Lens injects
  test: test_e2e_file_seam.py
  evidence: Timestamped logs showing full cycle <10s

GATE_S29_2:
  name: BRIEFING_DELIVERED
  criterion: Morning briefing contains health + overnight + doctrine
  test: test_briefing_content.py
  evidence: Briefing validates against template, summary ≤500 tokens

GATE_S29_3:
  name: EXPLORE_ISOLATED
  criterion: EXPLORE produces no files in /acting/, no beads, no workers, no external queries
  test: test_explore_isolation.py
  evidence: 10 EXPLORE turns → 0 files in /acting/, 0 beads

GATE_S29_4:
  name: INQUISITOR_REJECTS
  criterion: Invalid intents rejected with typed error
  test: test_inquisitor_rejection.py
  evidence: 5 invalid intents → 5 FAILED responses with correct error_type

GATE_S29_5:
  name: SESSION_SURVIVES_CHECKPOINT
  criterion: Checkpoint completes atomically, new session inherits context
  test: test_checkpoint_session_handoff.py
  evidence: Old session CHECKPOINTED, new session ACTIVE, bead written

GATE_S29_6:
  name: DAEMON_HEALTH_MONITORED
  criterion: Daemon crash → alert within 60s
  test: test_daemon_crash_alert.py
  evidence: Kill daemon → Telegram alert fires

GATE_S29_7:
  name: OLYA_UX_VALIDATED
  criterion: Olya confirms "this feels like thinking partner"
  test: Manual session with Olya
  evidence: Verbal/written confirmation

BINARY_EXIT:
  statement: "Olya can EXPLORE with Claude AND receive morning briefing"
  all_gates_pass: TRUE → S29 COMPLETE
```

---

## 9. HANDOFF ARTIFACTS

```yaml
S30_RECEIVES:
  working_file_seam:
    - /phoenix/intents/acting/ (watched)
    - /phoenix/intents/explore/ (ignored)
    - intent.yaml schema v1.1 (locked)
    - response.md schema v1.1 (locked)
    - Watcher daemon (operational)
    - Inquisitor (operational)
    - Lens daemon (operational, mechanism chosen)
    
  session_management:
    - /phoenix/sessions/ (authoritative)
    - Checkpoint atomicity (proven)
    - Session schema (locked)
    
  dispatcher_routing:
    - Routing table (extensible)
    - Worker contract (interface defined)
    - DISPATCH:QUERY_MEMORY → athena_worker (S30 implements)
    
  briefing_worker:
    - Template for additional workers
    - Bead emission pattern
    - Summary compression pattern
    
  daemon_health:
    - Heartbeat mechanism
    - Cross-daemon monitoring
    - Alert pipeline (Telegram)
    
  proven_invariants:
    - INV-EXPLORE-3 (path-based enforcement)
    - INV-EXPLORE-4 (no external access)
    - INV-LENS-1 (single mechanism)
    - INV-LENS-ORDER-1 (monotonic injection)
    - INV-CONTEXT-1 (summary only)
    - INV-UX-1 (no silent delays)
    - INV-SESSION-1 (authoritative session file)
```

---

## 10. M2M LEARNINGS

```yaml
WHY_PATH_BASED_MODE:
  origin: EXPLORE enforcement question (Q1)
  insight: YAML mode field can lie; directory path cannot
  decision: /acting/ watched, /explore/ ignored
  tradeoff: Slight complexity for mechanical invariant
  
WHY_SUMMARY_ONLY:
  origin: Context protection (INV-CONTEXT-1)
  insight: Raw worker output floods context
  decision: ≤500 token summary, detail_path for expansion
  tradeoff: Requires good compression logic
  
WHY_SESSION_FILE:
  origin: State ownership question (Q3)
  insight: Claude cannot own truth (dies with context)
  decision: Phoenix-managed session file, Claude copies
  tradeoff: Extra file I/O for source of truth
  
WHY_ATHENA_PROHIBITED:
  origin: EXPLORE purity question (Q4)
  insight: Any query mechanism violates either INV-EXPLORE-3 or zero-tool
  decision: Defer to S30, keep EXPLORE "Cognitive Only"
  tradeoff: EXPLORE less powerful, but cleaner
  
WHY_IMMEDIATE_ACK:
  origin: Perceptual latency concern (GPT R-07)
  insight: Silent delays erode thinking partner illusion
  decision: Ack immediately, heartbeat during long work
  tradeoff: Extra messages for UX preservation
  
WHY_DAEMON_HEARTBEAT:
  origin: GROK FLAG_6 catch
  insight: Silent daemon death = invisible system failure
  decision: Mutual monitoring, 60s alert
  tradeoff: Polling overhead for reliability
```

---

## 11. IMPLEMENTATION PRIORITY

```yaml
CRITICAL_PATH:
  1. Lens mechanism prototype (highest risk, blocks UX)
  2. Watcher daemon (/acting/ only)
  3. Inquisitor (validation + typed errors)
  4. Session management (file + checkpoint)
  5. Dispatcher (routing + compression)
  6. Briefing worker (template for all workers)
  7. Daemon heartbeat (reliability layer)

ESTIMATED_EFFORT:
  lens_prototype: 2-3 days (research + build all three options)
  watcher: 1-2 days
  inquisitor: 2-3 days
  session: 2 days
  dispatcher: 2 days
  briefing_worker: 1-2 days
  heartbeat: 0.5 days
  testing: 2-3 days
  
TOTAL: 13-18 days (includes buffer)

PARALLELIZATION:
  - Lens prototype can start immediately
  - Watcher + Session can parallel
  - Inquisitor depends on Watcher
  - Dispatcher depends on Inquisitor
  - Briefing depends on Dispatcher
```

---

## 12. BUILD READINESS

```yaml
STATUS: BUILD READY (CONDITIONAL)

CONDITION: Lens prototype validates at least one option (C, B, or A)

RISK_MITIGATION:
  - Manual attachment documented as fallback (not shameful)
  - Option B (MCP tool) is acceptable if others fail
  
BLOCKING_RESOLVED: 4/4
  - Q1 EXPLORE: ✓ Path-based enforcement
  - Q2 LENS: ✓ Prototype plan + ordering invariant
  - Q3 SESSION: ✓ Authoritative file + checkpoint atomicity
  - Q4 ATHENA: ✓ Prohibited in S29

NEW_CATCHES_INTEGRATED: 4
  - Daemon heartbeat (GROK)
  - Typed failures (GPT)
  - Perceptual latency (GPT)
  - Injection contract (OWL)

INVARIANTS: 7 (up from 4)
CHAOS_VECTORS: 13 (up from 7)
EXIT_GATES: 7 (up from 5)
```

---

**STATUS:** v0.2 ADVISOR SYNTHESIS COMPLETE  
**NEXT:** OPUS builds, CTO monitors, advisors available for edge cases  
**EXIT:** "Olya can EXPLORE with Claude AND receive morning briefing"

**OINK OINK.** 🐗🔥
