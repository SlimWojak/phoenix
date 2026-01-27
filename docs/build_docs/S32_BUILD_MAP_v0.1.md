```yaml
CTO_READY:
  status: ENGAGED
  formula: PROVEN (S30/S31 compression: ~40x)
  
  sequence:
    1: Draft S32_BUILD_MAP v0.1
    2: Advisory panel (GPT + GROK minimum, OWL if IBKR contracts need review)
    3: Synthesize v0.2
    4: Brief OPUS for execution
    
  s32_context:
    theme: "Real markets"
    risk_elevation: CAPITAL-AFFECTING (T2 tier)
    external_dependency: IBKR API
    
  drafting_now: S32_BUILD_MAP_v0.1.md
```

---

# S32_BUILD_MAP_v0.1.md

**Sprint:** S32 EXECUTION_PATH  
**Theme:** "Real markets"  
**Duration:** 3-4 weeks (IBKR complexity buffer)  
**Risk Tier:** ELEVATED (first capital-affecting sprint)  
**Status:** DRAFT — AWAITING ADVISORY REVIEW

---

## SPRINT CONTEXT

```yaml
S31_PROVIDES:
  - CSE signals ready (CSO emits canonical format)
  - State anchor validates freshness (adaptive TTL)
  - Kill flags block entries (ONE-WAY-KILL)
  - Autopsy ready (will analyze real trades)
  - Telegram notifications (throttled)
  - Lens injection (responses flow to Claude)

S32_BUILDS:
  - IBKR connector (broker API)
  - T2 approval workflow (human gate for capital)
  - Position lifecycle (state machine)
  - Reconciliation (Phoenix vs broker sync)
  - Promotion checklist (shadow → live ceremony)

S32_EXIT_GATE:
  binary: "T2 workflow proven on paper, IBKR connected"
```

---

## SURFACES

```yaml
SURFACE_1_IBKR_CONNECTOR:
  location: phoenix/brokers/ibkr/
  purpose: Interactive Brokers API integration
  
  files:
    - connector.py      # Main API client
    - orders.py         # Order submission/tracking
    - positions.py      # Position queries
    - account.py        # Balance, margin queries
    - mock_client.py    # Full mock for testing
    
  capabilities:
    - Order submission (market, limit, bracket)
    - Order status tracking
    - Position query (current holdings)
    - Fill tracking (execution details)
    - Account balance/margin
    
  constraints:
    tier: T2 (capital-affecting)
    requires: Approval token for any order
    mock: Full mock client for all testing
    rate_limits: Respect IBKR throttling
    
  api_notes:
    library: ib_insync (async wrapper)
    connection: TWS or IB Gateway
    paper_trading: IBKR paper account for validation

SURFACE_2_T2_APPROVAL:
  location: phoenix/governance/t2/
  purpose: Human sovereignty gate for capital decisions
  
  files:
    - approval.py       # Approval workflow
    - tokens.py         # Token generation/validation
    - evidence.py       # Evidence bundle assembly
    
  flow:
    1: CSO emits CSE signal (READY)
    2: Evidence bundle assembled
    3: State hash validated (fresh)
    4: Human reviews in Claude Desktop
    5: Explicit APPROVE action
    6: Token generated (single-use, 5-min expiry)
    7: Token attached to order submission
    8: Order executed with audit trail
    
  token_schema:
    id: uuid
    intent_id: uuid (linked to specific intent)
    timestamp: ISO8601
    expires_at: timestamp + 5 minutes
    used: boolean (starts false)
    evidence_hash: str (what was approved)
    
  evidence_displayed:
    - Setup quality score + breakdown
    - HTF/LTF alignment details
    - Risk parameters (stop, target, size)
    - Red check results
    - State hash freshness TTL
    - Position sizing calculation

SURFACE_3_POSITION_LIFECYCLE:
  location: phoenix/execution/positions/
  purpose: State machine for position management
  
  files:
    - lifecycle.py      # State machine
    - states.py         # State definitions
    - transitions.py    # Valid transitions
    - tracker.py        # Active position tracking
    
  states:
    PROPOSED: Intent received, awaiting approval
    APPROVED: Human approved, token issued
    SUBMITTED: Order sent to broker
    FILLED: Entry executed, position open
    MANAGED: SL/TP in place, monitoring
    CLOSED: Position exited (win/loss/breakeven)
    CANCELLED: Order cancelled before fill
    REJECTED: Broker rejected order
    
  state_machine:
    PROPOSED → APPROVED: T2 token issued
    PROPOSED → CANCELLED: Human passes
    APPROVED → SUBMITTED: Order sent
    APPROVED → EXPIRED: Token timeout (5 min)
    SUBMITTED → FILLED: Broker confirms
    SUBMITTED → REJECTED: Broker rejects
    FILLED → MANAGED: SL/TP placed
    MANAGED → CLOSED: Exit triggered
    
  beads:
    - POSITION bead at each state transition
    - Full audit trail of lifecycle

SURFACE_4_RECONCILIATION:
  location: phoenix/execution/reconciliation/
  purpose: Sync Phoenix state with broker reality
  
  files:
    - reconciler.py     # Main reconciliation logic
    - drift.py          # Drift detection
    - resolver.py       # Conflict resolution
    
  checks:
    - Position count match
    - Position size match
    - P&L alignment
    - Order status sync
    
  schedule:
    - On fill (immediate)
    - Periodic (every 5 min during market hours)
    - On demand (manual trigger)
    
  drift_handling:
    detect: Phoenix vs IBKR mismatch
    alert: Immediate notification
    action: Flag for human review (no auto-correct)

SURFACE_5_PROMOTION:
  location: phoenix/execution/promotion/
  purpose: Shadow → live ceremony with evidence
  
  files:
    - checklist.py      # Promotion requirements
    - evidence_bundle.py # Bundle assembly
    - ceremony.py       # Promotion workflow
    
  requirements:
    duration:
      min_sessions: 20 trading sessions
      min_regimes: 2 distinct (trend + range)
    performance:
      max_drawdown: recorded
      worst_day: recorded
      sharpe: recorded (no minimum, just recorded)
    defensive:
      signalman_kills: count of would-have-killed
      override_frequency: Olya override rate
    reasoning:
      autopsy_summary: patterns from shadow autopsies
      
  ceremony:
    1: Evidence bundle assembled
    2: DISPATCH:PROMOTE_STRATEGY intent
    3: T2 gate (human approval)
    4: PROMOTION bead emitted
    5: Strategy config updated (SHADOW → LIVE)
```

---

## SEAMS

```yaml
SEAM_CSE_TO_EXECUTION:
  boundary: CSO | Execution Pipeline
  contract:
    cso_provides: CSE-formatted signal
    execution_validates: CSE schema compliance
    execution_requires: State hash fresh
    execution_requires: No kill flags active
    execution_routes: To T2 approval workflow
  invariant: INV-CSE-1 (all paths consume identical format)

SEAM_APPROVAL_TO_BROKER:
  boundary: T2 Approval | IBKR Connector
  contract:
    approval_provides: Valid token + order params
    broker_validates: Token exists, not expired, not used
    broker_marks: Token as used (single-use)
    broker_submits: Order to IBKR
    broker_returns: Order ID + status
  invariant: INV-T2-TOKEN-1 (single-use, 5-min expiry)

SEAM_BROKER_TO_LIFECYCLE:
  boundary: IBKR Connector | Position Lifecycle
  contract:
    broker_reports: Fill details
    lifecycle_transitions: SUBMITTED → FILLED
    lifecycle_emits: POSITION bead
    lifecycle_triggers: Reconciliation check
  invariant: INV-POSITION-AUDIT-1 (bead at each transition)

SEAM_LIFECYCLE_TO_AUTOPSY:
  boundary: Position Lifecycle | Autopsy (S31)
  contract:
    lifecycle_reports: Position closed
    autopsy_receives: Position ID + outcome
    autopsy_queries: Entry thesis (original evidence)
    autopsy_emits: AUTOPSY bead
  integration: Already built in S31, wire connection

SEAM_RECONCILIATION_TO_ALERT:
  boundary: Reconciliation | Alert Pipeline
  contract:
    reconciler_detects: Drift
    alert_fires: Immediate notification
    alert_includes: Mismatch details
    alert_escalates: If unresolved >15 min
  invariant: INV-RECONCILE-ALERT-1

SEAM_SHADOW_TO_PROMOTION:
  boundary: Shadow Boxer (S30) | Promotion
  contract:
    shadow_provides: Performance beads
    promotion_queries: Evidence requirements
    promotion_validates: Checklist complete
    promotion_gates: T2 human approval
  invariant: INV-PROMOTION-EVIDENCE-1
```

---

## WIRING

```yaml
WIRE_SIGNAL_TO_ORDER:
  flow: |
    CSO detects READY (CSE)
         ↓
    State Anchor validates freshness
         ↓ (FRESH)
    Kill Flag check
         ↓ (NO KILL)
    Evidence bundle assembled
         ↓
    Claude Desktop displays for review
         ↓
    Human: [APPROVE]
         ↓
    T2 Token generated (uuid, 5-min, single-use)
         ↓
    Order params constructed
         ↓
    IBKR Connector submits (with token)
         ↓
    Token marked USED
         ↓
    Position Lifecycle: PROPOSED → APPROVED → SUBMITTED
         ↓
    Broker confirms fill
         ↓
    Position Lifecycle: SUBMITTED → FILLED → MANAGED
         ↓
    Reconciliation validates
         ↓
    POSITION bead emitted

WIRE_POSITION_CLOSE:
  flow: |
    SL/TP triggered OR manual close
         ↓
    IBKR reports fill
         ↓
    Position Lifecycle: MANAGED → CLOSED
         ↓
    POSITION bead (final state)
         ↓
    Autopsy triggered (async)
         ↓
    AUTOPSY bead emitted

WIRE_TOKEN_EXPIRY:
  flow: |
    Token issued (5-min TTL)
         ↓
    No order submission within 5 min
         ↓
    Token expires
         ↓
    Position Lifecycle: APPROVED → EXPIRED
         ↓
    Requires new approval to proceed

WIRE_RECONCILIATION:
  flow: |
    Trigger (fill, periodic, manual)
         ↓
    Query IBKR positions
         ↓
    Compare to Phoenix state
         ↓
    Match? → LOG (healthy)
    Mismatch? → ALERT + FLAG
         ↓
    Human reviews
         ↓
    Manual resolution (Phoenix doesn't auto-correct)
```

---

## INVARIANTS TO PROVE

```yaml
INV-T2-TOKEN-1:
  statement: "Approval tokens are single-use, expire in 5 minutes"
  test: test_t2_token_security.py
  proof: 
    - Reuse attempt → REJECTED
    - Expired token → REJECTED
    - Valid token → ACCEPTED + marked used

INV-T2-GATE-1:
  statement: "No order submission without valid T2 token"
  test: test_t2_gate_enforcement.py
  proof: Order without token → REJECTED at connector

INV-POSITION-AUDIT-1:
  statement: "POSITION bead emitted at every state transition"
  test: test_position_lifecycle_beads.py
  proof: State change → bead exists with correct state

INV-POSITION-SM-1:
  statement: "Position state machine only allows valid transitions"
  test: test_position_state_machine.py
  proof: Invalid transition → REJECTED

INV-RECONCILE-ALERT-1:
  statement: "Position drift triggers immediate alert"
  test: test_reconciliation_alert.py
  proof: Induced mismatch → alert within 60s

INV-RECONCILE-READONLY-1:
  statement: "Reconciliation detects but does not auto-correct"
  test: test_reconciliation_readonly.py
  proof: Drift detected → flagged, no position modification

INV-PROMOTION-EVIDENCE-1:
  statement: "Strategy promotion requires evidence bundle"
  test: test_promotion_checklist.py
  proof: Promotion without bundle → REJECTED

INV-PROMOTION-T2-1:
  statement: "Promotion is T2 gated (human approval)"
  test: test_promotion_t2.py
  proof: Promotion attempt → requires token

INV-IBKR-MOCK-1:
  statement: "All IBKR tests use mock client (no real API in tests)"
  test: (meta) verify test imports
  proof: No test hits real IBKR

INV-KILL-BLOCKS-ENTRY-1:
  statement: "Active kill flag blocks new position entry"
  test: test_kill_blocks_entry.py
  proof: Kill active → order rejected pre-submission
```

---

## CHAOS VECTORS

```yaml
CV_S32_TOKEN_REPLAY:
  inject: Attempt to reuse approval token
  expect: REJECTED, audit logged
  
CV_S32_TOKEN_EXPIRED:
  inject: Use token after 5 minutes
  expect: REJECTED as expired

CV_S32_TOKEN_WRONG_INTENT:
  inject: Use token for different intent than approved
  expect: REJECTED (intent_id mismatch)

CV_S32_ORDER_WITHOUT_TOKEN:
  inject: Submit order with no token
  expect: REJECTED at connector layer

CV_S32_ORDER_RACE:
  inject: Two orders same intent simultaneously
  expect: One succeeds, one rejected (idempotent)

CV_S32_RECONCILIATION_DRIFT:
  inject: IBKR mock returns wrong position
  expect: Drift detected, alert fired, no auto-correct

CV_S32_PROMOTION_BYPASS:
  inject: Attempt live trading without shadow period
  expect: REJECTED, checklist incomplete

CV_S32_PROMOTION_PARTIAL:
  inject: Promotion with incomplete evidence
  expect: REJECTED, missing requirements listed

CV_S32_LIFECYCLE_INVALID:
  inject: Force invalid state transition (PROPOSED → CLOSED)
  expect: State machine rejects

CV_S32_KILL_ENTRY_ATTEMPT:
  inject: Order submission while kill flag active
  expect: REJECTED pre-broker

CV_S32_STALE_APPROVAL:
  inject: Approve then wait 31 min (state anchor)
  expect: STATE_CONFLICT when attempting order

CV_S32_IBKR_TIMEOUT:
  inject: Mock IBKR with 30s delay
  expect: Timeout handled gracefully, position in SUBMITTED state

CV_S32_IBKR_REJECTION:
  inject: Mock IBKR rejects order (insufficient margin)
  expect: SUBMITTED → REJECTED, alert, no retry

CV_S32_FILL_PARTIAL:
  inject: Mock partial fill (50%)
  expect: Position reflects partial, reconciliation tracks
```

---

## EXIT GATES

```yaml
GATE_S32_1:
  name: IBKR_CONNECTED
  criterion: Query account, submit paper order, receive fill
  test: test_ibkr_e2e.py
  evidence: Paper trade round-trip with mock

GATE_S32_2:
  name: T2_TOKENS_SECURE
  criterion: Single-use, 5 min expiry, replay rejected
  test: test_t2_token_security.py
  evidence: All token chaos vectors PASS

GATE_S32_3:
  name: POSITION_LIFECYCLE_TRACKED
  criterion: State machine transitions correctly, beads emitted
  test: test_position_lifecycle_e2e.py
  evidence: Full lifecycle with POSITION beads

GATE_S32_4:
  name: RECONCILIATION_WORKS
  criterion: Induced mismatch → detected → alerted
  test: test_reconciliation_e2e.py
  evidence: Drift detected, no auto-correct

GATE_S32_5:
  name: PROMOTION_CHECKLIST
  criterion: Shadow → live requires evidence bundle + T2
  test: test_promotion_e2e.py
  evidence: Incomplete → rejected, complete → approved

GATE_S32_6:
  name: KILL_BLOCKS_ENTRY
  criterion: Kill flag prevents new positions
  test: test_kill_integration.py
  evidence: Entry blocked when signalman kill active

GATE_S32_7:
  name: BUNNY_PASSES
  criterion: All S32 chaos vectors green
  test: chaos_suite_s32.py
  evidence: BUNNY_REPORT_S32.md

BINARY_EXIT:
  statement: "T2 workflow proven on paper, IBKR connected"
```

---

## TRACKS

```yaml
TRACK_A_IBKR:
  scope: Broker connector + mock
  files:
    - phoenix/brokers/ibkr/connector.py
    - phoenix/brokers/ibkr/orders.py
    - phoenix/brokers/ibkr/positions.py
    - phoenix/brokers/ibkr/account.py
    - phoenix/brokers/ibkr/mock_client.py
  tests:
    - tests/brokers/test_ibkr_connector.py
    - tests/brokers/test_ibkr_orders.py
    - tests/brokers/test_ibkr_mock.py
  depends_on: None (can start immediately)
  blocks: Track B, Track C

TRACK_B_T2_WORKFLOW:
  scope: Approval tokens + evidence display
  files:
    - phoenix/governance/t2/approval.py
    - phoenix/governance/t2/tokens.py
    - phoenix/governance/t2/evidence.py
  tests:
    - tests/governance/test_t2_tokens.py
    - tests/governance/test_t2_approval.py
    - tests/governance/test_t2_evidence.py
  depends_on: Track A (needs connector to submit)
  blocks: Track C

TRACK_C_POSITION_LIFECYCLE:
  scope: State machine + reconciliation
  files:
    - phoenix/execution/positions/lifecycle.py
    - phoenix/execution/positions/states.py
    - phoenix/execution/positions/tracker.py
    - phoenix/execution/reconciliation/reconciler.py
    - phoenix/execution/reconciliation/drift.py
  tests:
    - tests/execution/test_position_lifecycle.py
    - tests/execution/test_reconciliation.py
  depends_on: Track A (broker reports), Track B (token flow)
  blocks: Track D

TRACK_D_PROMOTION:
  scope: Shadow → live ceremony
  files:
    - phoenix/execution/promotion/checklist.py
    - phoenix/execution/promotion/evidence_bundle.py
    - phoenix/execution/promotion/ceremony.py
  tests:
    - tests/execution/test_promotion.py
  depends_on: Track C (position lifecycle), S30 Shadow
  blocks: None (final track)

TRACK_E_INTEGRATION:
  scope: Full flow testing + BUNNY
  files:
    - tests/integration/test_s32_e2e.py
    - tests/chaos/chaos_suite_s32.py
  depends_on: All tracks
  deliverable: BUNNY_REPORT_S32.md
```

---

## OPEN QUESTIONS FOR ADVISORS

```yaml
Q1_IBKR_LIBRARY:
  question: ib_insync vs ibapi (official)?
  context: ib_insync is cleaner async, ibapi is official
  cto_lean: ib_insync (better ergonomics)
  seeking: GPT/GROK opinion on reliability

Q2_TOKEN_STORAGE:
  question: Where to store T2 tokens?
  options:
    a: BeadStore (immutable, queryable)
    b: Separate SQLite table (faster lookup)
    c: In-memory with periodic flush
  cto_lean: BeadStore (audit trail matters)
  seeking: GPT opinion on query performance

Q3_PARTIAL_FILL:
  question: How to handle partial fills?
  options:
    a: Single position tracks partial
    b: Split into multiple position records
    c: Wait for complete fill (timeout)
  cto_lean: Option A (simpler state machine)
  seeking: GROK chaos perspective

Q4_RECONCILIATION_FREQUENCY:
  question: How often to reconcile during market hours?
  options:
    a: Every fill only
    b: Every 1 min
    c: Every 5 min
    d: Configurable
  cto_lean: Option D, default 5 min
  seeking: Balance between drift detection and API load

Q5_MOCK_FIDELITY:
  question: How realistic should IBKR mock be?
  options:
    a: Instant fills, no delays
    b: Configurable delays (simulate latency)
    c: Full order book simulation
  cto_lean: Option B (configurable, default instant)
  seeking: GROK on chaos injection via mock
```

---

## HANDOFF ARTIFACTS

```yaml
S33_RECEIVES:
  ibkr_connector:
    - Full API integration (orders, positions, account)
    - Mock client for testing
    - Rate limit handling
    
  t2_workflow:
    - Token generation + validation
    - Evidence bundle assembly
    - Approval flow (Claude Desktop integration)
    
  position_lifecycle:
    - State machine (8 states)
    - POSITION beads at transitions
    - Tracker for active positions
    
  reconciliation:
    - Drift detection
    - Alert on mismatch
    - No auto-correct (human resolves)
    
  promotion:
    - Checklist validation
    - Evidence bundle requirements
    - T2 ceremony for live activation
    
  bunny_report:
    - BUNNY_REPORT_S32.md
    - All S32 chaos vectors green
```

---

## RISK REGISTER

```yaml
RISK_1_IBKR_API_COMPLEXITY:
  likelihood: HIGH
  impact: MEDIUM (delays, not blockers)
  mitigation:
    - Mock-first development
    - ib_insync abstracts complexity
    - Defer edge cases to S33
    
RISK_2_TOKEN_SECURITY:
  likelihood: LOW
  impact: HIGH (capital at risk)
  mitigation:
    - UUID generation (cryptographic)
    - 5-min expiry (short window)
    - Single-use enforcement
    - Audit trail in beads
    
RISK_3_STATE_DESYNC:
  likelihood: MEDIUM
  impact: MEDIUM
  mitigation:
    - Reconciliation worker
    - Alert on drift
    - Human resolution (no auto-correct)
    
RISK_4_APPROVAL_FATIGUE:
  likelihood: MEDIUM
  impact: LOW (UX, not safety)
  mitigation:
    - Glanceable evidence display
    - Clear APPROVE/PASS buttons
    - No false urgency
```

---

```yaml
BUILD_MAP_STATUS: DRAFT_v0.1
READY_FOR: Advisory review (GPT, GROK, OWL optional)
FORMAT: M2M (copy-paste ready)
```
ADVISORY REVIEWS - ADDENDUM TO FOLLOW

```yaml
SYNTHESIS_INIT:
  inputs:
    - GPT_ARCH_LINT: 4 hard flags, 5 Q answers, strong approval
    - GROK_CHAOS_BOAR: 7 flags, 6 recs, 2 blocking issues
    
  convergence: HIGH
  divergence: MINOR (token storage mechanism)
  
  blockers_identified: 2
    - Mock fidelity too low (GROK FAIL)
    - Stale approval kill gate missing (GROK FAIL)
```

---

# S32_BUILD_MAP_ADDENDUM_v0.1.md

**Purpose:** Synthesized advisory feedback for OPUS merge  
**Sources:** GPT (Architect Lint), GROK (Chaos Boar)  
**Status:** READY FOR OPUS MERGE → v0.2

---

## CONVERGENCE SUMMARY

```yaml
UNANIMOUS_APPROVALS:
  Q1_IBKR_LIBRARY: ib_insync
  Q3_PARTIAL_FILL: Option A (single position tracks partial)
  Q4_RECONCILIATION_FREQ: Configurable, default 5min
  Q5_MOCK_FIDELITY: Option B+ (configurable delays + chaos injection)
  
ALIGNED_WITH_MODIFICATION:
  Q2_TOKEN_STORAGE: Hybrid approach
    GPT: BeadStore + SQLite index
    GROK: BeadStore + in-memory cache
    SYNTHESIS: BeadStore (authoritative) + in-memory cache (5min TTL) + bead cross-check
```

---

## HARD FLAGS TO INCORPORATE

### FLAG_A: TOKEN LIFECYCLE BEADS (GPT)

```yaml
ISSUE: Token marked USED only after broker submit. Missing FAILED/EXPIRED bead emission.
RISK: Ambiguous audit trail under submit failure/timeout.

REQUIRED_CHANGES:
  new_bead_type: T2_TOKEN
  
  T2_TOKEN_BEAD:
    bead_id: uuid
    bead_type: "T2_TOKEN"
    token_id: uuid
    intent_id: uuid
    timestamp: ISO8601
    event: enum[ISSUED, USED, EXPIRED, REJECTED]
    reason: str (for REJECTED/EXPIRED)
    evidence_hash: str
    
  emission_points:
    - ISSUED: On token generation
    - USED: On successful order submission
    - EXPIRED: On 5-min timeout
    - REJECTED: On validation failure (replay, wrong intent, etc.)
    
  invariant_addition:
    INV-T2-TOKEN-AUDIT-1: "Every token state change emits T2_TOKEN bead"
```

### FLAG_B: SUBMITTED STATE TTL (GPT)

```yaml
ISSUE: IBKR timeout leaves position in SUBMITTED indefinitely.
RISK: Zombie SUBMITTED positions under network partition.

REQUIRED_CHANGES:
  new_state: STALLED
  
  state_machine_update:
    SUBMITTED → STALLED: After 60s without broker ACK
    STALLED → CANCELLED: Human intervention
    STALLED → FILLED: Late broker response (rare)
    
  behavior:
    - STALLED triggers immediate alert
    - No auto-retry (human decides)
    - Reconciliation flags STALLED as priority
    
  invariant_addition:
    INV-POSITION-SUBMITTED-TTL-1: "SUBMITTED > 60s without ACK → STALLED + alert"
```

### FLAG_C: RECONCILIATION BEADS (GPT)

```yaml
ISSUE: Resolution path not codified. No audit trail for drift resolution.

REQUIRED_CHANGES:
  new_bead_types:
  
    RECONCILIATION_DRIFT_BEAD:
      bead_id: uuid
      bead_type: "RECONCILIATION_DRIFT"
      timestamp: ISO8601
      drift_type: enum[POSITION_COUNT, POSITION_SIZE, PNL, ORDER_STATUS]
      phoenix_state: dict
      broker_state: dict
      severity: enum[WARNING, CRITICAL]
      
    RECONCILIATION_RESOLUTION_BEAD:
      bead_id: uuid
      bead_type: "RECONCILIATION_RESOLUTION"
      timestamp: ISO8601
      drift_bead_id: uuid (reference)
      resolution: enum[PHOENIX_CORRECTED, BROKER_CORRECTED, ACKNOWLEDGED]
      resolved_by: str (human identifier)
      notes: str
      
  invariant_addition:
    INV-RECONCILE-AUDIT-1: "Every drift emits RECONCILIATION_DRIFT bead"
    INV-RECONCILE-AUDIT-2: "Every resolution emits RECONCILIATION_RESOLUTION bead"
```

### FLAG_D: PROMOTION KILL CHECK (GPT)

```yaml
ISSUE: Promotion checks evidence + T2 but not global kill state.

REQUIRED_CHANGES:
  promotion_checklist_additions:
    - NO active kill flags (Signalman)
    - NO unresolved reconciliation drift
    
  ceremony_update:
    step_0: Assert kill_flag == False
    step_1: Assert unresolved_drift_count == 0
    step_2: (existing) Evidence bundle assembled
    step_3: (existing) T2 approval
    
  invariant_addition:
    INV-PROMOTION-SAFE-1: "Promotion rejected if kill flag active"
    INV-PROMOTION-SAFE-2: "Promotion rejected if unresolved drift exists"
```

### FLAG_E: MOCK FIDELITY UPGRADE (GROK - BLOCKING)

```yaml
ISSUE: Configurable delays too soft. Real IBKR chaos not simulated.
STATUS: BLOCKING (false green on paper → real capital bleed)

REQUIRED_CHANGES:
  mock_client_upgrade:
    configurable_chaos:
      fill_probability: 0.90      # 90% instant fill
      partial_fill_prob: 0.05     # 5% partial fill
      reject_prob: 0.03           # 3% rejection
      delay_prob: 0.02            # 2% delayed (10-30s)
      delay_range_sec: [10, 30]
      
    chaos_modes:
      INSTANT: fill_probability=1.0, delays=0
      REALISTIC: defaults above
      ADVERSARIAL: fill=0.7, partial=0.15, reject=0.10, delay=0.05
      
  usage:
    tests: INSTANT mode (fast)
    bunny: REALISTIC mode
    stress: ADVERSARIAL mode
    
  banteg_pattern: Randomized latency + partial ratio injection
```

### FLAG_F: STALE APPROVAL KILL GATE (GROK - BLOCKING)

```yaml
ISSUE: T2 token issued → Olya approves stale setup → IBKR executes ghost
STATUS: BLOCKING (dumbest failure in map)

REQUIRED_CHANGES:
  state_anchor_upgrade:
    adaptive_ttl:
      default: 30 min
      high_vol_regime: 15 min
      news_proximity: 10 min
      
    stale_gate:
      threshold: 15 min (configurable)
      behavior:
        - Intent received with stale state_hash
        - STATE_CONFLICT returned
        - Kill flag AUTO-SET (temporary, 5 min)
        - Requires explicit state refresh to proceed
        
  invariant_addition:
    INV-STALE-KILL-1: "State anchor >15min stale → STATE_CONFLICT + temporary kill"
```

### FLAG_G: PARTIAL FILL TRACKING (GROK)

```yaml
ISSUE: Single position tracks partial but drift confusion possible.

REQUIRED_CHANGES:
  position_bead_addition:
    partial_fill_ratio: float (0.0 to 1.0)
    filled_quantity: float
    requested_quantity: float
    
  reconciliation_check:
    - On each fill event, verify partial_fill_ratio matches broker
    - Drift alert only if ratio mismatch, not just "partial exists"
    
  chaos_vector_addition:
    CV_S32_PARTIAL_DRIFT:
      inject: Mock 50% fill, spoof broker reporting 60%
      expect: Drift detected, alert fired
```

---

## ADDITIONAL CHAOS VECTORS (GROK)

```yaml
CV_S32_15_PARTIAL_DRIFT:
  inject: Mock partial fill ratio mismatch
  expect: RECONCILIATION_DRIFT bead, alert, no auto-correct

CV_S32_16_TOKEN_RACE:
  inject: Two validation requests for same token simultaneously
  expect: One succeeds (marks used), second fails

CV_S32_17_PROMOTION_VETO:
  inject: Attempt promotion with active kill flag
  expect: REJECTED, kill flag cited

UPDATED_QUOTA: 17 vectors minimum
```

---

## BUNNY WAVE ORDER (GROK)

```yaml
WAVE_1_TOKEN_SECURITY:
  vectors:
    - CV_S32_TOKEN_REPLAY
    - CV_S32_TOKEN_EXPIRED
    - CV_S32_TOKEN_WRONG_INTENT
    - CV_S32_ORDER_WITHOUT_TOKEN
    - CV_S32_TOKEN_RACE (new)
    
WAVE_2_IBKR_CHAOS:
  vectors:
    - CV_S32_IBKR_TIMEOUT
    - CV_S32_IBKR_REJECTION
    - CV_S32_FILL_PARTIAL
    - CV_S32_PARTIAL_DRIFT (new)
    
WAVE_3_RECONCILIATION:
  vectors:
    - CV_S32_RECONCILIATION_DRIFT
    - CV_S32_ORDER_RACE
    
WAVE_4_LIFECYCLE_PROMOTION:
  vectors:
    - CV_S32_LIFECYCLE_INVALID
    - CV_S32_PROMOTION_BYPASS
    - CV_S32_PROMOTION_PARTIAL
    - CV_S32_PROMOTION_VETO (new)
    - CV_S32_KILL_ENTRY_ATTEMPT
    - CV_S32_STALE_APPROVAL
```

---

## INVARIANTS ADDITIONS (FULL LIST)

```yaml
NEW_INVARIANTS:
  INV-T2-TOKEN-AUDIT-1: "Every token state change emits T2_TOKEN bead"
  INV-POSITION-SUBMITTED-TTL-1: "SUBMITTED > 60s without ACK → STALLED + alert"
  INV-RECONCILE-AUDIT-1: "Every drift emits RECONCILIATION_DRIFT bead"
  INV-RECONCILE-AUDIT-2: "Every resolution emits RECONCILIATION_RESOLUTION bead"
  INV-PROMOTION-SAFE-1: "Promotion rejected if kill flag active"
  INV-PROMOTION-SAFE-2: "Promotion rejected if unresolved drift exists"
  INV-STALE-KILL-1: "State anchor >15min stale → STATE_CONFLICT + temporary kill"
```

---

## ANSWERS TO OPEN QUESTIONS (FINAL)

```yaml
Q1_IBKR_LIBRARY:
  answer: ib_insync
  guardrail: Wrap behind Phoenix interface, zero direct imports outside phoenix/brokers/ibkr/
  
Q2_TOKEN_STORAGE:
  answer: HYBRID
  implementation:
    - BeadStore: Authoritative audit trail (T2_TOKEN beads)
    - In-memory cache: Fast validation (TTL = 5min)
    - Cross-check: Validate cache against bead on suspicious patterns
    
Q3_PARTIAL_FILL:
  answer: Option A (single position)
  addition: partial_fill_ratio field in POSITION bead
  
Q4_RECONCILIATION_FREQUENCY:
  answer: Configurable, default 5min
  guardrail: Rate limit max 12/min, env var for tuning
  immediate_triggers: Fill, Reject, Cancel, Drift
  
Q5_MOCK_FIDELITY:
  answer: Option B+ (banteg-style chaos)
  modes: INSTANT (tests), REALISTIC (bunny), ADVERSARIAL (stress)
```

---

## SCHEMA ADDITIONS

```yaml
NEW_BEAD_SCHEMAS:

T2_TOKEN_BEAD:
  bead_id: uuid
  bead_type: "T2_TOKEN"
  token_id: uuid
  intent_id: uuid
  timestamp: ISO8601
  event: enum[ISSUED, USED, EXPIRED, REJECTED]
  reason: str (nullable)
  evidence_hash: str
  expires_at: ISO8601

RECONCILIATION_DRIFT_BEAD:
  bead_id: uuid
  bead_type: "RECONCILIATION_DRIFT"
  timestamp: ISO8601
  drift_type: enum[POSITION_COUNT, POSITION_SIZE, PNL, ORDER_STATUS]
  phoenix_state: dict
  broker_state: dict
  severity: enum[WARNING, CRITICAL]

RECONCILIATION_RESOLUTION_BEAD:
  bead_id: uuid
  bead_type: "RECONCILIATION_RESOLUTION"
  timestamp: ISO8601
  drift_bead_id: uuid
  resolution: enum[PHOENIX_CORRECTED, BROKER_CORRECTED, ACKNOWLEDGED]
  resolved_by: str
  notes: str

STATE_MACHINE_UPDATE:
  new_state: STALLED
  transitions:
    SUBMITTED → STALLED: 60s timeout
    STALLED → CANCELLED: Human cancels
    STALLED → FILLED: Late broker ACK
```

---

## OPUS MERGE INSTRUCTIONS

```yaml
MERGE_TASK:
  input:
    - S32_BUILD_MAP_v0.1.md (draft)
    - S32_BUILD_MAP_ADDENDUM_v0.1.md (this file)
    
  output:
    - S32_BUILD_MAP_v0.2.md (unified)
    
  merge_actions:
    1: Add T2_TOKEN bead schema to SCHEMAS section
    2: Add RECONCILIATION_DRIFT and RECONCILIATION_RESOLUTION beads
    3: Add STALLED state to position lifecycle
    4: Update token_schema with T2_TOKEN bead emission points
    5: Update mock_client section with chaos modes
    6: Add stale approval kill gate to state_anchor
    7: Update promotion checklist with kill/drift checks
    8: Add partial_fill_ratio to POSITION bead
    9: Add 3 new chaos vectors (quota now 17)
    10: Add 7 new invariants
    11: Update Bunny wave order
    12: Mark Q1-Q5 as RESOLVED with final answers
    
  validation:
    - All blockers addressed (mock fidelity, stale kill)
    - Chaos quota >= 17
    - Invariants count >= 17 (10 original + 7 new)
```

---

```yaml
ADDENDUM_STATUS: COMPLETE
BLOCKERS_RESOLVED: 2/2
READY_FOR: OPUS merge
```

