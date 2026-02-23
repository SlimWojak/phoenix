# S34 BUILD MAP v0.2 — CANONICAL

**Sprint:** S34 OPERATIONAL_FINISHING
**Theme:** "Finish plumbing, not brain"
**Duration:** 4 days (HARD CAP)
**Status:** FINAL — Build Ready
**Authors:** CTO (Claude) + G (Sovereign) + Advisor Panel (GPT, GROK) + OPUS (Synthesizer)

---

## SPRINT OVERVIEW

```yaml
OBJECTIVE: |
  Remove operational friction without adding intelligence.
  Wire existing components. Prove CSO contract. Polish UX.

TRACKS:
  D1: Watcher + Lens (file seam completion)
  D2: Mock Oracle (5-drawer → pipeline validation)
  D3: Orientation Bead (S34.5 — checksum not briefing)
  D4: Ambient Widget (E001 — peripheral awareness)

MANTRA:
  gpt: "Reduce friction, preserve doctrine"
  grok: "Finish plumbing, not brain"
  cto: "Zero intelligence expansion"
  opus: "Wire, don't invent"

DOCTRINE_CHECK:
  sovereignty_preserved: TRUE
  halt_path_unchanged: TRUE
  t2_gates_unchanged: TRUE
  file_seam_pattern: EXTENDED (not replaced)
```

---

## GLOBAL CONSTRAINTS (GPT Additions)

```yaml
FORBIDDEN:
  - Strategy logic
  - Intelligence expansion
  - CSO methodology changes
  - Trading outcome changes
  - Scope creep beyond 4 days
  - New beads beyond ORIENTATION type (GROK)
  - Worker mutations (read-only plumbing) (GROK)

S34_GLOBAL_KILL_GATE:
  statement: "Abort sprint if any trading decision or outcome deviates from S33_P1 behavior"
  enforcement: Hard invariant, not aspiration
  test: Run S33 paper trade drill, outcomes identical

SCOPE_CREEP_VECTORS:
  identified:
    - D2 realism creep (tuning confidence to 'feel right')
    - D3 prose/summary creep
    - D4 evolving into control surface
    - Timeline bleed beyond 4 days
  mitigation: Cut scope, NEVER extend time

SEQUENCING_PRIORITY:
  must_complete: [D1, D2, D3]
  cut_candidate: D4 (if sprint pressure)
  rule: Do not extend sprint for D4
```

---

## D1: WATCHER + LENS

### Problem Statement

```yaml
FRICTION: F003 — Manual polling breaks flow
CURRENT_STATE: |
  Claude writes intent.yaml
  [GAP — no watcher running]
  Manual simulation required
  Response.md must be manually attached

TARGET_STATE: |
  Claude writes intent.yaml
  Watcher detects, dispatches to worker
  Worker produces response.md
  Lens injects response into Claude
  Zero manual steps
  Latency: <5s end-to-end (GROK tightening)
```

### Surfaces

```yaml
WATCHER_DAEMON:
  location: phoenix/daemons/watcher.py
  purpose: Detect new intents, dispatch to workers
  watches: /phoenix/intents/incoming/
  dispatches_to: Existing workers (SCAN, HUNT, APPROVE, etc.)

  interface:
    start(): void
    stop(): void
    on_intent(intent_path): void

  behavior:
    - inotify (preferred) or poll fallback for new .yaml files
    - Parse intent type + subtype
    - Route to appropriate worker
    - Log dispatch event
    - Move processed intent to /processed/

  resilience:
    - Exponential backoff on worker failure
    - Orphan intent recovery on restart
    - Graceful degradation (log, don't crash)

LENS_DAEMON:
  location: phoenix/daemons/lens.py
  purpose: Inject responses into Claude's view
  watches: /phoenix/responses/

  interface:
    start(): void
    stop(): void
    on_response(response_path): void

  behavior:
    - Detect new .md files
    - Read content
    - Inject via file system flag (Claude polls)
    - Mark as delivered

  fallback: |
    If daemon injection proves complex,
    single MCP tool read_phoenix_response() (~50 tokens)
    Acceptable tradeoff: minimal context cost
    GROK: Measure context bloat — >50 tokens = death creep
```

### Routing Table

```yaml
ROUTING:
  SCAN: → scan_worker
  HUNT: → hunt_worker
  APPROVE: → approval_worker
  QUERY_MEMORY: → athena_worker
  HALT: → halt_handler (IMMEDIATE, bypasses queue)
  UNKNOWN: → log + quarantine to /unprocessed/

ERROR_HANDLING:
  unknown_type: Log + move to /unprocessed/
  worker_timeout: Emit blocker bead
  worker_crash: Emit error response, continue
  parse_failure: Log + quarantine (no silent drop)
```

### Wiring

```
┌─────────────────────────────────────────────────────────────────┐
│  D1 COMPLETE FILE SEAM                                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Claude Desktop                                                 │
│       │                                                         │
│       │ writes                                                  │
│       ▼                                                         │
│  /intents/incoming/intent.yaml                                  │
│       │                                                         │
│       │ WATCHER detects (inotify/poll)                          │
│       ▼                                                         │
│  ┌─────────────┐                                                │
│  │   WATCHER   │ ─── routes ───► Worker (SCAN/HUNT/etc)         │
│  └─────────────┘                      │                         │
│       │                               │ executes                │
│       │ moves to /processed/          ▼                         │
│       │                         /responses/response.md          │
│       │                               │                         │
│       │                               │ LENS detects            │
│       │                               ▼                         │
│       │                         ┌─────────────┐                 │
│       │                         │    LENS     │                 │
│       │                         └─────────────┘                 │
│       │                               │                         │
│       │                               │ injects (or MCP)        │
│       │                               ▼                         │
│       └─────────────────────── Claude Desktop                   │
│                                                                 │
│  LATENCY TARGET: <5 seconds end-to-end                          │
└─────────────────────────────────────────────────────────────────┘
```

### Invariants

```yaml
INV-D1-WATCHER-1:
  statement: "Every intent.yaml is processed exactly once"
  test: test_watcher_exactly_once.py
  proof: Duplicate detection, processed folder tracking

INV-D1-WATCHER-IMMUTABLE-1:
  statement: "Watcher may not modify intent payloads"
  test: "Hash intent before/after routing"
  rationale: Prevents future 'helpful creep'
  enforcement: Compare SHA256 at ingress vs egress

INV-D1-LENS-1:
  statement: "Response injection adds ≤50 tokens to context"
  test: test_lens_context_cost.py
  proof: Token count before/after injection

INV-D1-HALT-PRIORITY-1:
  statement: "HALT intents bypass queue, process immediately"
  test: test_halt_priority.py
  proof: Inject 10 intents, HALT in middle, HALT processes first
```

### Exit Gates

```yaml
GATE_D1_1:
  name: WATCHER_ROUTES
  criterion: Intent → Watcher → Worker automatic
  test: Write SCAN intent, worker executes without manual intervention

GATE_D1_2:
  name: LENS_INJECTS
  criterion: Response appears in Claude without manual attach
  test: Worker writes response, Claude sees it

GATE_D1_3:
  name: E2E_LATENCY
  criterion: Full round-trip in <5 seconds
  test: Timestamp delta from intent write to response visible
```

### Chaos Vectors

```yaml
CV_D1_INTENT_FLOOD:
  inject: 100 intents in 1 second
  expect: All processed, no crashes, order preserved (HALT priority)

CV_D1_MALFORMED_INTENT:
  inject: Invalid YAML, missing fields
  expect: Logged, moved to /unprocessed/, no crash

CV_D1_WORKER_CRASH:
  inject: Worker throws exception mid-processing
  expect: Error response generated, watcher continues

CV_D1_LENS_STALE:
  inject: Response older than intent (clock skew)
  expect: Handled gracefully, logged

CV_D1_HALT_RACE:
  inject: HALT intent while worker processing
  expect: HALT takes priority, worker interrupted if possible

CV_D1_DAEMON_CRASH:
  inject: Kill watcher mid-dispatch
  expect: Orphan intents in /unprocessed/, no silent drop
  recovery: Restart scans /unprocessed/

CV_D1_ROUTING_MISS:
  inject: Unknown intent type
  expect: Log + quarantine, emit blocker bead

CV_D1_INJECTION_FAIL:
  inject: Lens clipboard clobbered by other app
  expect: Fallback to MCP tool triggers

CV_D1_EMPTY_DIR_POLL:
  inject: No intents for 1 hour
  expect: Daemon idle, CPU <1%, no silent rot
```

### OPUS Build Notes

```yaml
EXISTING_ASSETS:
  - File seam proven in S33 Track F (read/write validated)
  - Intent YAML format already used (SCAN, APPROVE)
  - Workers exist from S30-S32 (need wiring, not building)

IMPLEMENTATION_HINTS:
  - Use watchdog library (cross-platform inotify abstraction)
  - Fallback: simple poll with 500ms interval
  - MCP fallback: ~10 lines, minimal risk
  - Start with MCP fallback, upgrade to daemon if time
```

---

## D2: MOCK ORACLE (5-Drawer Pipeline)

### Problem Statement

```yaml
FRICTION: CSO contract unproven before Olya arrives
CURRENT_STATE: |
  5-drawer structure exists (machine-readable)
  Phoenix has CSE consumer stub (from S31)
  No validation that they connect
  Mock CSE generator exists (S33)

TARGET_STATE: |
  Mock generator produces CSE from 5-drawer gates
  Pipeline consumes CSE
  T2 approval displays evidence from 5-drawer refs
  Format proven — Olya plugs in, it works

KEY_INSIGHT: |
  Mock and real use IDENTICAL format.
  When Olya plugs in, it works.
  No integration debugging during live prep.
```

### Surfaces

```yaml
MOCK_CSE_GENERATOR:
  location: phoenix/mocks/mock_cse_generator.py (EXISTS from S33)
  purpose: Produce CSE signals from 5-drawer gates

  enhancement_needed:
    - Read from conditions.yaml (5-drawer gates)
    - Generate evidence_hash pointing to source refs
    - Emit source: "MOCK_5DRAWER" for distinguishing

  example_output:
    signal_id: "mock-001"
    timestamp: ISO8601
    pair: "EURUSD"
    source: "MOCK_5DRAWER"
    setup_type: "GRADE_A_LONG"
    confidence: 0.85
    parameters:
      entry: 1.0850
      stop: 1.0820
      target: 1.0920
      risk_percent: 1.0
    evidence_hash: "ref:GATE-COND-001"
    evidence_bundle:
      gate: "high_quality_long"
      requires:
        - "in_structural_discount: TRUE"
        - "freshness_score: 7.2 (>= 6)"
        - "entry_matches_htf_long: TRUE"
      source_refs:
        - "conditions.yaml:GATE-COND-001"
        - "foundation.yaml:INV-007"

CSO_CONSUMER:
  location: phoenix/cso/consumer.py
  purpose: Receive CSE, validate, route to approval

  interface:
    on_signal(cse: CSE) → void
    validate_cse(cse: CSE) → bool
    route_to_approval(cse: CSE) → void

  validation:
    - Schema compliance (cse_schema.yaml)
    - Required fields present
    - evidence_hash resolvable
    - source field present (MOCK vs REAL)

APPROVAL_EVIDENCE_DISPLAY:
  location: phoenix/approval/evidence.py
  purpose: Format evidence for T2 approval UI

  output_example: |
    SETUP: GRADE_A_LONG on EURUSD
    CONFIDENCE: 0.85

    GATE: high_quality_long (conditions.yaml:GATE-COND-001)
    REQUIRES:
      ✓ in_structural_discount: TRUE
      ✓ freshness_score: 7.2 (threshold: 6)
      ✓ entry_matches_htf_long: TRUE
      ✓ no conflicting_signals

    SOURCE: foundation.yaml:INV-007 (structural range PRIMARY)

    [APPROVE] [PASS]
```

### Wiring

```
┌─────────────────────────────────────────────────────────────────┐
│  D2 MOCK ORACLE PIPELINE                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  conditions.yaml (5-DRAWER)                                     │
│  ┌─────────────────────────────────┐                            │
│  │ GATE-COND-001: high_quality_long│                            │
│  │   requires:                     │                            │
│  │     - in_structural_discount    │                            │
│  │     - freshness_score >= 6      │                            │
│  │     - entry_matches_htf_long    │                            │
│  └─────────────────────────────────┘                            │
│       │                                                         │
│       │ Mock Generator reads                                    │
│       ▼                                                         │
│  ┌─────────────────────────────────┐                            │
│  │     MOCK CSE GENERATOR          │                            │
│  │     (mock data, real format)    │                            │
│  │     source: MOCK_5DRAWER        │                            │
│  └─────────────────────────────────┘                            │
│       │                                                         │
│       │ Produces CSE                                            │
│       ▼                                                         │
│  ┌─────────────────────────────────┐                            │
│  │     CSO CONSUMER                │                            │
│  │     (validates, routes)         │                            │
│  └─────────────────────────────────┘                            │
│       │                                                         │
│       │ Routes to approval                                      │
│       ▼                                                         │
│  ┌─────────────────────────────────┐                            │
│  │     T2 APPROVAL UI              │                            │
│  │     (displays evidence)         │                            │
│  └─────────────────────────────────┘                            │
│       │                                                         │
│       │ Human reviews                                           │
│       ▼                                                         │
│  [APPROVE] or [PASS]                                            │
│                                                                 │
│  KEY: Mock = test harness. Format = production.                 │
│       When Olya's CSO replaces mock, pipeline unchanged.        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Invariants

```yaml
INV-D2-FORMAT-1:
  statement: "Mock CSE and production CSE use identical schema"
  test: test_cse_schema_match.py
  proof: Both validate against cse_schema.yaml

INV-D2-TRACEABLE-1:
  statement: "Every CSE field traceable to 5-drawer source"
  test: test_cse_traceability.py
  proof: evidence_hash resolves to valid source_ref

INV-D2-NO-INTELLIGENCE-1:
  statement: "Mock generator has zero market analysis logic"
  test: test_mock_no_intelligence.py
  proof: Code inspection — only format, no strategy

INV-D2-NO-COMPOSITION-1:
  statement: "Mock generator may only emit single, pre-declared gate IDs from conditions.yaml"
  test: "Attempt composite/synthesized gate → must fail"
  rationale: Prevents accidental strategy assembly
  enforcement: Whitelist of valid gate IDs only
```

### Exit Gates

```yaml
GATE_D2_1:
  name: MOCK_GENERATES_CSE
  criterion: Gate from conditions.yaml → valid CSE
  test: generate_mock_cse("GATE-COND-001", "EURUSD", params)

GATE_D2_2:
  name: CONSUMER_ACCEPTS
  criterion: CSE validates and routes to approval
  test: CSO consumer accepts mock CSE without error

GATE_D2_3:
  name: EVIDENCE_DISPLAYS
  criterion: T2 UI shows evidence from 5-drawer refs
  test: Approval screen shows gate requirements + source refs

GATE_D2_4:
  name: FORMAT_IDENTICAL
  criterion: Mock CSE schema == production CSE schema
  test: Schema validation against cse_schema.yaml
```

### Chaos Vectors

```yaml
CV_D2_INVALID_CSE:
  inject: CSE with missing required fields
  expect: Consumer rejects, logs error, no crash

CV_D2_UNRESOLVABLE_REF:
  inject: evidence_hash pointing to non-existent gate
  expect: Logged warning, approval shows "ref unresolved"

CV_D2_CONFIDENCE_BOUNDS:
  inject: confidence = 1.5 (out of range)
  expect: Schema validation fails

CV_D2_REAL_FAKE_MIX:
  inject: Mix of mock and (future) real CSE
  expect: Both validate, source field distinguishes

CV_D2_GAP_INJECTION:
  inject: Flagged gaps in mock (CONFLICT-COND-001)
  expect: Pipeline BLOCK, not forward-fill lies

CV_D2_FORMAT_DRIFT:
  inject: Corrupt YAML (missing ID refs)
  expect: Parse fail → emit STATE_CONFLICT bead

CV_D2_T2_EVIDENCE_OVERLOAD:
  inject: Mock generates 100+ evidence bundles
  expect: UI handles gracefully, no veto fatigue
```

### OPUS Build Notes

```yaml
EXISTING_ASSETS:
  - mock_cse_generator.py exists from S33 Track E
  - 5-drawer YAML structure defined by CSO
  - T2 approval workflow from S32

IMPLEMENTATION_HINTS:
  - Extend mock_cse_generator.py to read conditions.yaml
  - Add source field to distinguish MOCK vs REAL
  - Create cse_schema.yaml for validation
  - Wire to existing T2 approval display
```

---

## D3: ORIENTATION BEAD (S34.5)

### Problem Statement

```yaml
FRICTION: 15+ min rehydration cost per fresh session
CURRENT_STATE: |
  Fresh Claude = blank slate
  Must re-read docs, ask questions, rebuild context
  Orientation is vibes, not system-owned

TARGET_STATE: |
  Fresh Claude calls get_system_orientation()
  Receives ORIENTATION_BEAD (machine-verifiable checksum)
  Verifies state in <10 seconds
  Corruption detected automatically

MANTRA: "Checksum, not briefing. Verification, not understanding."
```

### Surfaces

```yaml
ORIENTATION_BEAD_SCHEMA:
  location: phoenix/schemas/orientation_bead.yaml

  fields:
    execution_phase: enum [S33_P1_COMPLETE, S33_P2_ACTIVE, etc.]
    mode: enum [MOCK, PAPER, LIVE_LOCKED]
    active_invariants_count: int
    last_human_action_bead_id: uuid | null
    last_alert_id: uuid | null
    kill_flags_active: int
    unresolved_drift_count: int
    heartbeat_status: enum [HEALTHY, DEGRADED, MISSED]
    positions_open: int
    bead_hash: sha256
    generated_at: ISO8601

  constraints:
    - ALL fields machine-verifiable (no prose)
    - ALL fields cross-checkable against source systems
    - NO derived/interpreted/summary fields (GPT)
    - Output ≤ 1000 tokens

FORBIDDEN_FIELDS:
  - system_stable (derived)
  - risk_level (interpreted)
  - narrative_state (prose)
  - summary (prose)
  - recommendation (intelligence)

ORIENTATION_GENERATOR:
  location: phoenix/orientation/generator.py
  purpose: Aggregate system state into ORIENTATION_BEAD

  interface:
    generate() → ORIENTATION_BEAD
    validate(bead: ORIENTATION_BEAD) → bool

  sources:
    - Bead store (last_human_action, last_alert)
    - Halt manager (kill_flags)
    - Heartbeat (status)
    - Position tracker (positions_open)
    - Config (execution_phase, mode)

ORIENTATION_EXPOSER:
  location: phoenix/orientation/expose.py
  purpose: Make orientation available to Claude

  options:
    file_seam: Write to /phoenix/state/orientation.yaml
    mcp_server: get_system_orientation() endpoint

  decision: Start with file seam (consistent with D1)
```

### Tests

```yaml
POSITIVE_TEST:
  name: Verification Speed
  procedure:
    1: Generate ORIENTATION_BEAD
    2: Give to fresh Claude session
    3: Ask "What is the system state?"
    4: Measure time to correct answer
  success:
    - Claude correctly states phase/mode/positions/health
    - Time < 10 seconds
    - No additional context required

NEGATIVE_TEST:
  name: Corruption Detection (THE KILL TEST)
  procedure:
    1: Generate valid ORIENTATION_BEAD
    2: Corrupt 1 field (e.g., mode: LIVE when actually PAPER)
    3: Give to fresh Claude
    4: Ask "What is the system state?"
  expected:
    - Claude reports STATE_CONFLICT or contradiction
    - Claude asks for clarification
    - Claude refuses to act on corrupted orientation
  variants_required: 5 (GROK requirement)
    - Hash wrong
    - Fields invalid
    - Stale timestamp
    - Mode mismatch
    - Position count mismatch
  rationale: |
    If this fails, orientation is still vibes.
    This is the kill test for "did we actually solve it?"
```

### Invariants

```yaml
INV-D3-CHECKSUM-1:
  statement: "ORIENTATION_BEAD is machine-verifiable, not prose"
  test: test_orientation_no_prose.py
  proof: All fields are enum, int, uuid, or sha256

INV-D3-CROSS-CHECK-1:
  statement: "Every field cross-checkable against source system"
  test: test_orientation_cross_check.py
  proof: Generate bead, verify each field against source

INV-D3-CORRUPTION-1:
  statement: "Corrupted bead triggers STATE_CONFLICT"
  test: test_orientation_corruption.py
  proof: Negative test passes (min 3 variants, GROK)

INV-D3-NO-DERIVED-1:
  statement: "Orientation bead contains no derived, interpreted, or summary fields"
  forbidden_examples:
    - system_stable
    - risk_level
    - narrative_state
  rationale: Keep bead raw, countable, hashable
```

### Exit Gates

```yaml
GATE_D3_1:
  name: BEAD_GENERATES
  criterion: ORIENTATION_BEAD generated from system state
  test: generator.generate() returns valid bead

GATE_D3_2:
  name: POSITIVE_TEST_PASSES
  criterion: Fresh Claude verifies state in <10s
  test: Manual test with fresh session

GATE_D3_3:
  name: NEGATIVE_TEST_PASSES
  criterion: Corrupted bead triggers detection
  test: Min 3 corruption variants caught
```

### Chaos Vectors

```yaml
CV_D3_ALL_FIELDS_CORRUPT:
  inject: Corrupt every field
  expect: Detected immediately

CV_D3_HASH_MISMATCH:
  inject: Valid fields but wrong bead_hash
  expect: Hash validation fails

CV_D3_STALE_BEAD:
  inject: Bead from 1 hour ago
  expect: Staleness flag or warning

CV_D3_SOURCE_DISAGREES:
  inject: Bead says 0 positions, position tracker says 1
  expect: Cross-check catches discrepancy

CV_D3_SOURCE_OUTAGE:
  inject: Heartbeat down during generation
  expect: Partial bead + warning flag, not full emit

CV_D3_HOSTILE_LOAD:
  inject: 5 corruption variants to fresh session
  expect: All trigger STATE_CONFLICT

CV_D3_RAPID_FIRE:
  inject: 10 bead requests in 1s
  expect: Aggregator handles gracefully, cap at 1/min
```

### OPUS Build Notes

```yaml
EXISTING_ASSETS:
  - S34.5_ORIENTATION_FLEX.md (approved spec)
  - Heartbeat infrastructure from S33
  - Bead store from S30
  - Position lifecycle from S32

IMPLEMENTATION_HINTS:
  - Generator pulls from existing sources (no new queries)
  - Hash computation: SHA256 of sorted field values
  - File seam exposure: /phoenix/state/orientation.yaml
  - Negative tests: Create dedicated test file with 5 variants
```

---

## D4: AMBIENT WIDGET (E001)

### Problem Statement

```yaml
FRICTION: F004 — No peripheral awareness
CURRENT_STATE: |
  System state only visible via explicit query
  No glanceable third mode
  NEX had menu bar widget — Phoenix doesn't

TARGET_STATE: |
  Menu bar shows: health, positions, P&L, mode
  Glanceable (peripheral attention)
  Third mode: Deep (Claude), Interrupt (Telegram), Peripheral (Widget)

CONSTRAINT: Max 4 fields (GROK — no dashboard creep)
```

### Surfaces

```yaml
MENU_BAR_WIDGET:
  location: phoenix/widget/menu_bar.py
  framework: rumps (macOS)

  displays: # MAX 4 FIELDS
    health: "🟢" | "🟡" | "🔴"
    positions: "0" | "2"
    pnl: "+$123" | "-$45"
    mode: "📄" | "⚠️"

  interactions:
    click: Open detailed status (read-only)
    right_click: Quick status (no actions)

  forbidden_interactions:
    - Trading actions
    - Approval triggers
    - Halt controls (use Telegram for that)

  refresh: Every 5 seconds (configurable)

WIDGET_DATA_SOURCE:
  location: phoenix/widget/data_source.py
  purpose: Aggregate data for widget display

  reads_from:
    - Heartbeat manager (health)
    - Position tracker (positions, P&L)
    - Config (mode)
    - Halt manager (kill flags)

  shares_with: ORIENTATION_BEAD generator (same sources)
```

### Invariants

```yaml
INV-D4-GLANCEABLE-1:
  statement: "Widget state update < 100ms"
  test: test_widget_latency.py
  proof: Benchmark refresh cycle

INV-D4-ACCURATE-1:
  statement: "Widget matches actual system state"
  test: test_widget_accuracy.py
  proof: Cross-check widget display vs source systems

INV-D4-NO-ACTIONS-1:
  statement: "Widget may not initiate trading, approvals, or strategy actions"
  rationale: Prevents widget becoming control surface
  enforcement: No buttons/actions beyond read-only display
```

### Exit Gates

```yaml
GATE_D4_1:
  name: WIDGET_DISPLAYS
  criterion: Menu bar shows health/positions/P&L/mode
  test: Visual inspection

GATE_D4_2:
  name: WIDGET_ACCURATE
  criterion: Display matches actual state
  test: Compare widget vs position tracker

GATE_D4_3:
  name: WIDGET_RESPONSIVE
  criterion: Updates within 5 seconds of state change
  test: Change position, observe widget update
```

### Chaos Vectors

```yaml
CV_D4_SOURCE_CRASH:
  inject: Position tracker unavailable
  expect: Widget shows "⚠️" not crash

CV_D4_RAPID_UPDATES:
  inject: 100 state changes in 1 second
  expect: Widget handles gracefully, no flicker

CV_D4_HALT_DURING_DISPLAY:
  inject: HALT while widget rendering
  expect: Widget shows HALTED immediately

CV_D4_PLATFORM_MISMATCH:
  inject: Run on Linux (no rumps)
  expect: Graceful fallback or clear error

CV_D4_DATA_STALE:
  inject: Position change not reflected <5s
  expect: Timeout flag ("⚠️ STALE")
```

### OPUS Build Notes

```yaml
EXISTING_ASSETS:
  - NEX menu bar pattern (investigated, clean)
  - Heartbeat from S33
  - Position tracker from S32

IMPLEMENTATION_HINTS:
  - Use rumps for macOS (simple, proven)
  - Share data source with ORIENTATION_BEAD generator
  - Start mac-only for Olya, Linux later if needed
  - If sprint pressure: CUT D4, do not extend

PRIORITY: LOWEST (cut candidate if time pressure)
```

---

## SPRINT EXIT GATE

```yaml
S34_COMPLETE_WHEN:
  all_tracks:
    - D1: File seam fully automatic (<5s latency)
    - D2: Mock pipeline proven (CSE → T2 evidence)
    - D3: Orientation verifiable (<10s, corruption caught)
    - D4: Widget glanceable (4 fields, accurate) [OR CUT]

  binary_test: "Operational friction materially reduced"

  global_gate:
    statement: "S33 paper trade drill produces identical outcomes"
    test: Run drills/ibkr_paper_trade_roundtrip.py
    expect: Same fills, same P&L (no trading behavior change)

  evidence:
    - Claude intent → response without manual steps
    - Mock CSE → T2 approval with evidence
    - Fresh session verifies state in <10s
    - Menu bar shows system state (if D4 not cut)
```

---

## CHAOS QUOTA

```yaml
TOTAL_VECTORS: 35
  D1: 10
  D2: 7
  D3: 7
  D4: 5
  GLOBAL: 1 (S33 drill unchanged)

  integration: 5 (cross-track)

INTEGRATION_CHAOS:
  CV_S34_INT_1:
    name: WATCHER_TO_ORIENTATION
    inject: Watcher processes intent, orientation bead outdated
    expect: Orientation regenerates on next request

  CV_S34_INT_2:
    name: CSE_TO_WIDGET
    inject: Mock CSE triggers position, widget stale
    expect: Widget updates within 5s

  CV_S34_INT_3:
    name: HALT_PROPAGATION
    inject: HALT intent → all surfaces reflect
    expect: Widget shows HALTED, orientation shows kill_flags:1

  CV_S34_INT_4:
    name: DAEMON_RESTART
    inject: Kill watcher, restart, orphan intents exist
    expect: Orphans recovered from /unprocessed/

  CV_S34_INT_5:
    name: FULL_PIPELINE
    inject: Mock CSE → Watcher → Approval → Response → Lens
    expect: Full flow <10s, no manual steps
```

---

## INVARIANT SUMMARY

| ID | Statement | Track |
|----|-----------|-------|
| INV-D1-WATCHER-1 | Every intent processed exactly once | D1 |
| INV-D1-WATCHER-IMMUTABLE-1 | Watcher may not modify intents | D1 |
| INV-D1-LENS-1 | Response injection ≤50 tokens | D1 |
| INV-D1-HALT-PRIORITY-1 | HALT bypasses queue | D1 |
| INV-D2-FORMAT-1 | Mock CSE == Production CSE schema | D2 |
| INV-D2-TRACEABLE-1 | Every CSE field traceable | D2 |
| INV-D2-NO-INTELLIGENCE-1 | Mock has zero market logic | D2 |
| INV-D2-NO-COMPOSITION-1 | No synthesized gates | D2 |
| INV-D3-CHECKSUM-1 | Orientation is machine-verifiable | D3 |
| INV-D3-CROSS-CHECK-1 | Every field cross-checkable | D3 |
| INV-D3-CORRUPTION-1 | Corrupted bead triggers STATE_CONFLICT | D3 |
| INV-D3-NO-DERIVED-1 | No derived/interpreted fields | D3 |
| INV-D4-GLANCEABLE-1 | Widget update <100ms | D4 |
| INV-D4-ACCURATE-1 | Widget matches actual state | D4 |
| INV-D4-NO-ACTIONS-1 | Widget read-only, no actions | D4 |

---

## ADVISOR CONSENSUS

| Advisor | Verdict | Key Contribution |
|---------|---------|------------------|
| GPT | APPROVE_WITH_TIGHTENINGS | Global kill gate, immutability invariants, scope discipline |
| GROK | APPROVE_WITH_TEETH | Chaos vectors, dumbest failures, helpful creep warnings |
| CTO | APPROVED | Scope, doctrine, sequencing |
| OPUS | BUILD_READY | Existing assets mapped, implementation hints |

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-01-28 | Initial draft for advisor lint |
| v0.2 | 2026-01-28 | Synthesized GPT + GROK + OPUS builds |

---

## BUILD SEQUENCE

```yaml
RECOMMENDED_ORDER:
  day_1: D1 (Watcher + Lens) — highest ROI
  day_2: D2 (Mock Oracle) — CSO contract validation
  day_3: D3 (Orientation Bead) — session rehydration
  day_4: D4 (Widget) — if time permits, else CUT

PARALLELIZATION:
  - D1 and D3 share no code, can parallel
  - D2 depends on workers (D1 wiring helps)
  - D4 shares data source with D3 (sequence)

IF_BEHIND:
  - Cut D4 first
  - Never extend beyond 4 days
  - Never add scope
```

---

**OINK OINK.** 🐗🔥

---

*Build map v0.2 finalized: 2026-01-28*
*Synthesized by: OPUS*
*Approved by: CTO + Advisor Panel*
*Status: CANONICAL — Build Ready*
