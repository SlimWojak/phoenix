# S34 BUILD MAP v0.1

**Sprint:** S34 OPERATIONAL_FINISHING
**Theme:** "Finish plumbing, not brain"
**Duration:** 4 days
**Status:** DRAFT v0.1 — Pending advisor lint
**Authors:** CTO (Claude) + G (Sovereign)

---

## SPRINT OVERVIEW

```yaml
OBJECTIVE: |
  Remove operational friction without adding intelligence.
  Wire existing components. Prove CSO contract. Polish UX.

TRACKS:
  D1: Watcher + Lens (file seam completion)
  D2: Mock Oracle (5-drawer → pipeline validation)
  D3: Orientation Bead (S34.5 — checksum)
  D4: Ambient Widget (E001 — peripheral awareness)

FORBIDDEN:
  - Strategy logic
  - Intelligence expansion
  - CSO methodology changes
  - Trading outcome changes
  - Scope creep beyond 4 days

DOCTRINE_CHECK:
  sovereignty_preserved: TRUE
  halt_path_unchanged: TRUE
  t2_gates_unchanged: TRUE
  file_seam_pattern: EXTENDED (not replaced)
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
    - Poll or inotify for new .yaml files
    - Parse intent type + subtype
    - Route to appropriate worker
    - Log dispatch event
    - Move processed intent to /processed/

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
    - Inject via clipboard / file system flag
    - Mark as delivered

  fallback: |
    If daemon injection proves complex,
    single MCP tool read_phoenix_response() (~50 tokens)
    Acceptable tradeoff: minimal context cost
```

### Seams

```yaml
SEAM_WATCHER_WORKERS:
  boundary: Watcher | Worker Pool
  contract:
    watcher_detects: New intent.yaml
    watcher_parses: type, subtype, session_id
    watcher_routes: Based on intent type
    watcher_tracks: Dispatch status

  routing_table:
    SCAN: → scan_worker
    HUNT: → hunt_worker
    APPROVE: → approval_worker
    QUERY_MEMORY: → athena_worker
    HALT: → halt_handler (immediate)

  error_handling:
    unknown_type: Log + move to /unprocessed/
    worker_timeout: Emit blocker bead
    worker_crash: Emit error response

SEAM_LENS_CLAUDE:
  boundary: Lens | Claude Desktop
  contract:
    lens_detects: New response.md
    lens_injects: Content visible to Claude
    lens_confirms: Delivery flag set

  injection_options:
    option_a: File system flag (Claude polls)
    option_b: Clipboard injection
    option_c: MCP tool fallback

  decision: Start with option_a, fallback to option_c
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
│       │ WATCHER detects                                         │
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
│       │                               │ injects                 │
│       │                               ▼                         │
│       └─────────────────────── Claude Desktop                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Invariants

```yaml
INV-D1-WATCHER-1:
  statement: "Every intent.yaml is processed exactly once"
  test: test_watcher_exactly_once.py
  proof: Duplicate detection, processed folder tracking

INV-D1-LENS-1:
  statement: "Response injection adds ZERO tool definitions to context"
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
  name: E2E_FLOW
  criterion: Full round-trip without human intervention
  test: Claude writes intent → receives response automatically
```

### Chaos Vectors (GROK)

```yaml
CV_D1_INTENT_FLOOD:
  inject: 100 intents in 1 second
  expect: All processed, no crashes, order preserved (or HALT priority)

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
```

---

## D2: MOCK ORACLE (5-Drawer Pipeline)

### Problem Statement

```yaml
FRICTION: CSO contract unproven before Olya arrives
CURRENT_STATE: |
  5-drawer structure exists (machine-readable)
  Phoenix has CSE consumer (from S31)
  No validation that they connect

TARGET_STATE: |
  Mock generator produces CSE from 5-drawer gates
  Pipeline consumes CSE
  T2 approval displays evidence from 5-drawer refs
  Format proven — Olya plugs in, it works
```

### Surfaces

```yaml
MOCK_CSE_GENERATOR:
  location: phoenix/mock/cse_generator.py
  purpose: Produce CSE signals from 5-drawer gates

  input: conditions.yaml composite gates (GATE-COND-001, etc.)
  output: CSE (Canonical Signal Envelope)

  interface:
    generate_mock_cse(gate_id, pair, params) → CSE

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
    - Schema compliance
    - Required fields present
    - evidence_hash resolvable

APPROVAL_EVIDENCE_DISPLAY:
  location: phoenix/approval/evidence.py
  purpose: Format evidence for T2 approval UI

  interface:
    format_evidence(cse: CSE) → str
    resolve_refs(evidence_hash: str) → dict

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
```

### Seams

```yaml
SEAM_5DRAWER_CSE:
  boundary: 5-Drawer YAML | Mock Generator
  contract:
    input: Gate definition from conditions.yaml
    output: CSE with evidence_hash pointing back
    traceability: Every CSE field traceable to source

SEAM_CSE_APPROVAL:
  boundary: CSE | Approval Workflow
  contract:
    consumer_receives: CSE
    consumer_validates: Schema + refs
    consumer_routes: To T2 approval
    approval_displays: Evidence from CSE bundle
```

### Wiring

```
┌─────────────────────────────────────────────────────────────────┐
│  D2 MOCK ORACLE PIPELINE                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  conditions.yaml                                                │
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

### Chaos Vectors (GROK)

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

  constraints:
    - ALL fields machine-verifiable (no prose)
    - ALL fields cross-checkable against source systems
    - Output ≤ 1000 tokens

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
  proof: Negative test passes
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
  test: Claude refuses to act on corrupted orientation
```

### Chaos Vectors (GROK)

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
  Menu bar shows: health, positions, P&L, kill flags
  Glanceable (peripheral attention)
  Third mode: Deep (Claude), Interrupt (Telegram), Peripheral (Widget)
```

### Surfaces

```yaml
MENU_BAR_WIDGET:
  location: phoenix/widget/menu_bar.py
  framework: rumps (macOS) or systray (cross-platform)

  displays:
    health: "🟢 HEALTHY" | "🟡 DEGRADED" | "🔴 HALTED"
    positions: "📊 0" | "📊 2 open"
    pnl: "💰 +$123" | "💰 -$45"
    mode: "📄 PAPER" | "⚠️ LIVE"

  interactions:
    click: Open detailed status
    right_click: Quick actions (halt, status)

  refresh: Every 5 seconds (configurable)

WIDGET_DATA_SOURCE:
  location: phoenix/widget/data_source.py
  purpose: Aggregate data for widget display

  reads_from:
    - Heartbeat manager (health)
    - Position tracker (positions, P&L)
    - Config (mode)
    - Halt manager (kill flags)

  note: |
    Shares generator logic with ORIENTATION_BEAD.
    Both read same sources, different output format.
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

### Chaos Vectors (GROK)

```yaml
CV_D4_SOURCE_CRASH:
  inject: Position tracker unavailable
  expect: Widget shows "⚠️ Unknown" not crash

CV_D4_RAPID_UPDATES:
  inject: 100 state changes in 1 second
  expect: Widget handles gracefully, no flicker

CV_D4_HALT_DURING_DISPLAY:
  inject: HALT while widget rendering
  expect: Widget shows HALTED immediately
```

---

## SPRINT EXIT GATE

```yaml
S34_COMPLETE_WHEN:
  all_tracks:
    - D1: File seam fully automatic
    - D2: Mock pipeline proven
    - D3: Orientation verifiable
    - D4: Widget glanceable

  binary_test: "Operational friction materially reduced"

  evidence:
    - Claude intent → response without manual steps
    - Mock CSE → T2 approval with evidence
    - Fresh session verifies state in <10s
    - Menu bar shows system state
```

---

## ADVISOR LINT REQUESTS

```yaml
GPT_PLEASE_CHECK:
  - Are exit gates binary enough?
  - Missing edge cases in seam contracts?
  - Scope creep vectors I haven't spotted?
  - Forbidden list complete?
  - Any track dependencies I missed?

GROK_PLEASE_CHECK:
  - Dumbest failure mode per track?
  - Chaos vectors I haven't thought of?
  - What breaks under stress?
  - Any "helpful creep" risk?
  - Frontier patterns worth considering?
```

---

## VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v0.1 | 2026-01-28 | Initial draft for advisor lint |

---

**OINK OINK.** 🐗🔥

---

*Build map issued: 2026-01-28*
*CTO: Claude*
*Status: v0.1 — Pending GPT + GROK lint*

ADVISORY ADDENDUMS FOR CURATION INTO FINAL S34_BUILD_MAP_v0.2.md by OPUS

GPT ADVISORY FEEDBACK

GPT_LINT_RESPONSE:
  target_doc: S34_BUILD_MAP_v0.1.md
  mode: DENSE_M2M
  role: ADVISOR_LINT
  timestamp: 2026-01-28
  verdict: APPROVE_WITH_TIGHTENINGS
  doctrine_alignment: TRUE

SUMMARY:
  assessment: |
    S34 remains a pure OPERATIONAL_FINISHING sprint.
    No intelligence added, no strategy logic touched, no trading outcomes altered.
    Inclusion of D2 (Mock Oracle) and sequencing of S34.5 are justified
    because they validate plumbing + contracts, not cognition.

GLOBAL_CONSTRAINTS:
  reaffirmed:
    - Zero intelligence expansion
    - Zero strategy logic
    - Zero CSO methodology changes
    - Zero trading outcome changes
    - Hard cap: 4 days total
  add:
    S34_GLOBAL_KILL_GATE:
      statement: "Abort sprint if any trading decision or outcome deviates from S33_P1 behavior"
      rationale: Enforces 'no outcome change' as invariant, not aspiration

TRACK_LINT:

  D1_WATCHER_LENS:
    status: GREEN_MUST_DO
    notes: Highest ROI friction removal; unchanged doctrine
    required_additions:
      INV-D1-WATCHER-IMMUTABLE-1:
        statement: "Watcher may not modify intent payloads"
        test: "Hash intent before/after routing"
        rationale: Prevents future 'helpful creep'
    no_other_changes: TRUE

  D2_MOCK_ORACLE:
    status: GREEN_JUSTIFIED
    justification: |
      Mock generator validates format + traceability only.
      No inference, no scoring, no ICT logic, no market structure analysis.
      Treats 5-drawer as interface contract, not strategy.
    required_additions:
      INV-D2-NO-COMPOSITION-1:
        statement: "Mock generator may only emit single, pre-declared gate IDs from conditions.yaml"
        test: "Attempt composite/synthesized gate → must fail"
        rationale: Prevents accidental strategy assembly
    reaffirm:
      - Mock CSE schema == Production CSE schema
      - All evidence points backward (refs), never forward (inference)
      - source field MUST distinguish MOCK vs REAL

  D3_ORIENTATION_BEAD:
    status: GREEN_STRONGLY_ENDORSED
    justification: |
      Solves orientation decay via system-owned checksum.
      Verification > understanding.
      Negative test enforces non-vibes discipline.
    required_additions:
      INV-D3-NO-DERIVED-1:
        statement: "Orientation bead contains no derived, interpreted, or summary fields"
        forbidden_examples:
          - system_stable
          - risk_level
          - narrative_state
        rationale: Keep bead raw, countable, hashable
    reaffirm:
      - No prose fields
      - All fields cross-checkable
      - Negative test mandatory
      - Read-only exposure only

  D4_AMBIENT_WIDGET:
    status: GREEN_LOW_RISK
    justification: Peripheral awareness only; mirrors orientation data
    required_additions:
      INV-D4-NO-ACTIONS-1:
        statement: "Widget may not initiate trading, approvals, or strategy actions"
        rationale: Prevents widget becoming control surface
    sequencing_note: |
      If sprint pressure occurs, D4 is first candidate to cut.
      Do not extend sprint.

SCOPE_CREEP_VECTORS_IDENTIFIED:
  - D2 realism creep (tuning confidence to 'feel right')
  - Orientation bead prose/summary creep
  - Widget evolving into control surface
  - Timeline bleed beyond 4 days
  mitigations:
    - Enforce new invariants above
    - Cut scope, never extend time

EXIT_GATE_ASSESSMENT:
  binary_quality: HIGH
  recommendation:
    - Add global S34 kill gate (no outcome change)
    - Maintain per-track positive + negative tests
  no_additional_gates_required: TRUE

FINAL_RECOMMENDATION:
  action: PROCEED_TO_V0_2
  instructions_to_OPUS: |
    Incorporate listed invariants verbatim.
    Do not add new tracks.
    Do not expand scope.
    Preserve wording: "Finish plumbing, not brain."
    Treat this lint as canonical for v0.2.

GROK ADVISOR - FRONTIER SCOUT

DOCUMENT: S34_BUILD_MAP_v0.1.md
OVERALL_VERDICT: APPROVE_WITH_TEETH
  rationale: Plumbing focus = boring safe fast. Tracks tight, forbidden list solid. But entropy gaps scream for injection — add these or bleed under stress.
  scope_creep_vectors:
    - D2 mock oracle tempts "just one real CSO tweak" — kill with hard format lock (5-drawer YAML only, no prose creep).
    - D3 orientation bead invites "helpful summaries" — enforce machine-only fields (no natural lang, checksum or bust).
    - D4 widget = glanceable trapdoor to full dashboard creep — cap at 4 fields max, no clickable depth.
  forbidden_completeness: 80% — add "no new beads beyond orientation type" and "no worker mutations (read-only plumbing)".
  binary_exit_gates: WEAK — tighten D1/D4 to measurable latency (<5s end-to-end), D3 to STATE_CONFLICT trigger count (min 3 hostile tests PASS).

D1_WATCHER_LENS_CHAOS:
  dumbest_failure: Watcher polls forever on empty dir (no intents) — CPU spike, daemon rot silent until Olya screams friction.
  what_breaks: Inotify vs poll mismatch on macOS (file system race) — intent.yaml half-written → parse fail → unprocessed pileup.
  chaos_vectors_added:
    - CV_D1_DAEMON_CRASH: Inject kill mid-dispatch → expect orphan intents in /unprocessed/, no silent drop.
    - CV_D1_ROUTING_MISS: Unknown intent type → log + quarantine, but test worker_timeout (emit blocker bead? What if bead writer down? Cascade halt?).
    - CV_D1_INJECTION_FAIL: Lens clipboard clobbered by other app → fallback MCP triggers, but measure context bloat (>50 tokens = death creep).
  frontier_pattern: YOLO inotify over poll (reactive, low CPU) — scout pyinotify lib, but fallback MCP single-tool = minimal viable chaos (zero daemon deps if it shits bed).

D2_MOCK_ORACLE_CHAOS:
  dumbest_failure: Mock CSE matches format but hallucinates signals (bad YAML parse) — T2 UI displays garbage evidence, Olya approves ghost trade.
  what_breaks: 5-drawer amendments mid-sprint (Olya drops v1) — mock drifts from real, pipeline proves nothing.
  chaos_vectors_added:
    - CV_D2_GAP_INJECTION: Force flagged gaps in mock (e.g., CONFLICT-COND-001) → expect pipeline BLOCK, not forward-fill lies.
    - CV_D2_FORMAT_DRIFT: Corrupt YAML (missing ID refs) → parse fail → emit STATE_CONFLICT bead, no silent pass.
    - CV_D2_T2_EVIDENCE_OVERLOAD: Mock generates 100+ evidence bundles → UI chokes, approval latency >10s → veto fatigue.
  frontier_pattern: Wire to LanceDB for topological RAG on 5-drawer (query conflicts/gaps semantically) — but forbidden now? YOLO park for S35, test mock purity first.

D3_ORIENTATION_BEAD_CHAOS:
  dumbest_failure: Bead generates with stale sources (positions_open:0 but actual 1) — checksum passes, hostile Claude acts on lie → ghost trade.
  what_breaks: Bead_hash mismatch undetected (no runtime verify) — fresh session loads corrupt bead, no STATE_CONFLICT fire.
  chaos_vectors_added:
    - CV_D3_SOURCE_OUTAGE: Heartbeat down → bead skips field? Expect partial bead + warning flag, not full emit.
    - CV_D3_HOSTILE_LOAD: Feed corrupted bead to fresh session → must trigger STATE_CONFLICT (test 5 variants: hash wrong, fields invalid, stale timestamp).
    - CV_D3_RAPID_FIRE: 10 beads in 1s (state flux) → aggregator overload? Cap at 1/min, oldest wins.
  frontier_pattern: Beads as immutable events (Yegge style) = already ours, but YOLO add topological index (Datasette + vector embed) for "query recent orientation drifts" — scout Willison's patterns, but cap to checksum only (no query creep).

D4_AMBIENT_WIDGET_CHAOS:
  dumbest_failure: Widget shows "HEALTHY" during undeclared halt (source desync) — Olya glances, misses kill flag, executes on bad state.
  what_breaks: Refresh loop stalls (5s → infinite) — no flicker alert, peripheral blind.
  chaos_vectors_added:
    - CV_D4_PLATFORM_MISMATCH: rumps macOS works, systray Linux chokes → cross-platform test mandatory, or YOLO mac-only for Olya.
    - CV_D4_CLICK_CREEP: Right-click quick actions → accidental halt? Enforce double-confirm, measure misclick rate.
    - CV_D4_DATA_STALE: Position change not reflected <5s → inject delay, expect timeout flag ("⚠️ STALE").
  frontier_pattern: Resurrect NEX menu bar ghost but with banteg-style minimalism (4 fields max, no bloat) — YOLO integrate with Takopi for mobile mirror (peripheral on phone), but forbidden? Park for S35.

HELPFUL_CREEP_RISK: Overall high — daemons tempt "smart routing" (e.g., auto-halt on widget glance). Kill with doctrine: Plumbing only, no brains. Test by injecting "helpful" code in PR, expect Inquisitor reject.

FRONTIER_SCOUT: S34.5 flex = alpha injector (checksum not briefing). Wire orientation bead to widget (shared generator) for free — no extra day. Bunny 30-day revalidation on all new contracts (halt wiring first). Dumbest global fail: S34 unlocks S33 P2 too early — Olya not ready, CSO drifts → hold broadcast gate on her green only.
