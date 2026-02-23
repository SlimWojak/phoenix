# S32_BUILD_MAP v0.2

**Sprint:** S32 EXECUTION_PATH
**Theme:** "Real markets"
**Duration:** 3-4 weeks (IBKR complexity buffer)
**Risk Tier:** ELEVATED (first capital-affecting sprint)
**Status:** FINAL — READY FOR EXECUTION

---

## VERSION HISTORY

```yaml
v0.1: CTO draft
v0.2: Advisory synthesis + OPUS review
  integrations:
    - GPT (Architect Lint): 4 hard flags incorporated
    - GROK (Chaos Boar): 7 flags, 2 blockers resolved
  opus_additions:
    - Rate limiting awareness for IBKR
    - Market-only orders for S32 (limit deferred to S33)
    - Emergency close bypass clarification
    - API throttle guardrails
```

---

## SPRINT CONTEXT

```yaml
S31_PROVIDES:
  cse_signals: CSO emits canonical format ✓
  state_anchor: Validates freshness (adaptive TTL) ✓
  kill_flags: ONE-WAY-KILL blocks entries ✓
  autopsy: Ready to analyze real trades ✓
  telegram: Throttled notifications ✓
  lens: Responses flow to Claude ✓

S32_BUILDS:
  ibkr_connector: Broker API integration
  t2_workflow: Human gate for capital decisions
  position_lifecycle: State machine (9 states)
  reconciliation: Phoenix vs broker sync
  promotion: Shadow → live ceremony

S32_EXIT_GATE:
  binary: "T2 workflow proven on paper, IBKR connected"
```

---

## PRE-SPRINT SCHEMA UPDATES

```yaml
SCHEMA_UPDATES:
  # Must be created BEFORE track implementation

  1_update_beads_yaml:
    file: phoenix/schemas/beads.yaml
    add_types:
      - T2_TOKEN        # Token lifecycle audit
      - RECONCILIATION_DRIFT     # Drift detection
      - RECONCILIATION_RESOLUTION # Drift resolution

  2_create_position_lifecycle_yaml:
    file: phoenix/schemas/position_lifecycle.yaml
    purpose: Position state machine + bead schema

  3_create_t2_token_yaml:
    file: phoenix/schemas/t2_token.yaml
    purpose: Token generation, validation, expiry
```

---

## SURFACE 1: IBKR CONNECTOR

```yaml
IBKR_CONNECTOR:
  location: phoenix/brokers/ibkr/
  purpose: Interactive Brokers API integration

  files:
    - __init__.py       # Module exports
    - connector.py      # Main API client (ib_insync wrapper)
    - orders.py         # Order submission/tracking
    - positions.py      # Position queries
    - account.py        # Balance, margin queries
    - mock_client.py    # Full mock with chaos modes

  library:
    choice: ib_insync
    rationale: Better async ergonomics than ibapi
    guardrail: Wrapped behind Phoenix interface
    imports: ONLY in phoenix/brokers/ibkr/

  capabilities:
    - Order submission (MARKET ONLY in S32)
    - Order status tracking
    - Position query (current holdings)
    - Fill tracking (execution details)
    - Account balance/margin

  constraints:
    tier: T2 (capital-affecting)
    requires: Approval token for any order
    rate_limits: Max 50 orders/second, 12 reconciliations/minute

  api_notes:
    connection: TWS or IB Gateway (port 4002 paper, 4001 live)
    paper_trading: DU account for validation
    market_hours: Respect FX session windows

  # OPUS ADDITION: Order type scope
  order_types_s32:
    enabled: [MARKET]
    deferred_to_s33: [LIMIT, BRACKET, OCO]
    rationale: Start simple, prove flow, add complexity
```

---

## SURFACE 2: MOCK CLIENT (ENHANCED)

```yaml
MOCK_CLIENT:
  location: phoenix/brokers/ibkr/mock_client.py
  purpose: Realistic IBKR simulation for testing

  # GROK INTEGRATION: Banteg-style chaos
  chaos_modes:
    INSTANT:
      fill_probability: 1.0
      partial_fill_prob: 0.0
      reject_prob: 0.0
      delay_prob: 0.0
      delay_range_sec: [0, 0]
      use_case: Unit tests (fast)

    REALISTIC:
      fill_probability: 0.90
      partial_fill_prob: 0.05
      reject_prob: 0.03
      delay_prob: 0.02
      delay_range_sec: [10, 30]
      use_case: BUNNY tests

    ADVERSARIAL:
      fill_probability: 0.70
      partial_fill_prob: 0.15
      reject_prob: 0.10
      delay_prob: 0.05
      delay_range_sec: [30, 60]
      use_case: Stress tests

  interface:
    connect() → bool
    disconnect() → None
    submit_order(order: Order) → OrderResult
    get_positions() → list[Position]
    get_account() → AccountState
    set_mode(mode: ChaosMode) → None

  determinism:
    seed: Configurable for reproducible chaos
    default_seed: None (random in BUNNY)
```

---

## SURFACE 3: T2 APPROVAL WORKFLOW

```yaml
T2_APPROVAL:
  location: phoenix/governance/t2/
  purpose: Human sovereignty gate for capital decisions

  files:
    - __init__.py       # Module exports
    - approval.py       # Approval workflow orchestration
    - tokens.py         # Token generation/validation
    - evidence.py       # Evidence bundle assembly
    - cache.py          # In-memory token cache

  flow:
    1: CSO emits CSE signal (READY)
    2: State anchor validated (fresh)
    3: Kill flag check (none active)
    4: Evidence bundle assembled
    5: Human reviews in Claude Desktop
    6: Explicit APPROVE action
    7: Token generated (single-use, 5-min expiry)
    8: T2_TOKEN bead emitted (ISSUED)
    9: Token attached to order submission
    10: Order executed, token marked USED
    11: T2_TOKEN bead emitted (USED)

  # GPT INTEGRATION: Token lifecycle beads
  token_schema:
    id: uuid
    intent_id: uuid (linked to specific intent)
    timestamp: ISO8601
    expires_at: timestamp + 5 minutes
    used: boolean (starts false)
    evidence_hash: str (what was approved)

  bead_emission:
    events:
      ISSUED: On token generation
      USED: On successful order submission
      EXPIRED: On 5-min timeout
      REJECTED: On validation failure
    invariant: INV-T2-TOKEN-AUDIT-1

  token_storage:
    # HYBRID APPROACH (GPT + GROK synthesis)
    authoritative: BeadStore (T2_TOKEN beads)
    fast_lookup: In-memory cache (5-min TTL)
    cross_check: Validate cache against bead on suspicious patterns

  evidence_displayed:
    - Setup quality score + breakdown
    - HTF/LTF alignment details
    - Risk parameters (stop, target, size)
    - Red check results
    - State hash freshness TTL
    - Position sizing calculation
    - Active kill flags (should be NONE)
```

---

## SURFACE 4: POSITION LIFECYCLE

```yaml
POSITION_LIFECYCLE:
  location: phoenix/execution/positions/
  purpose: State machine for position management

  files:
    - __init__.py       # Module exports
    - lifecycle.py      # State machine
    - states.py         # State definitions (9 states)
    - transitions.py    # Valid transitions
    - tracker.py        # Active position tracking

  # GPT INTEGRATION: Added STALLED state
  states:
    PROPOSED: Intent received, awaiting approval
    APPROVED: Human approved, token issued
    SUBMITTED: Order sent to broker
    STALLED: Broker timeout (60s without ACK)  # NEW
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
    SUBMITTED → STALLED: 60s timeout (no ACK)  # NEW
    SUBMITTED → REJECTED: Broker rejects
    STALLED → CANCELLED: Human cancels  # NEW
    STALLED → FILLED: Late broker ACK  # NEW
    FILLED → MANAGED: SL/TP placed
    MANAGED → CLOSED: Exit triggered

  # GROK INTEGRATION: Partial fill tracking
  position_bead_fields:
    standard:
      - position_id
      - state
      - timestamp
      - signal_id
      - pair
      - side
      - entry_price
      - stop_price
      - target_price
    partial_fill:  # NEW
      - partial_fill_ratio: float (0.0 to 1.0)
      - filled_quantity: float
      - requested_quantity: float

  beads:
    - POSITION bead at each state transition
    - Full audit trail of lifecycle
    - partial_fill_ratio included
```

---

## SURFACE 5: RECONCILIATION

```yaml
RECONCILIATION:
  location: phoenix/execution/reconciliation/
  purpose: Sync Phoenix state with broker reality

  files:
    - __init__.py       # Module exports
    - reconciler.py     # Main reconciliation logic
    - drift.py          # Drift detection
    - resolver.py       # Manual resolution support

  checks:
    - Position count match
    - Position size match (including partial fill ratio)
    - P&L alignment
    - Order status sync

  schedule:
    on_fill: Immediate
    periodic: Every 5 min (configurable)
    on_demand: Manual trigger
    rate_limit: Max 12/minute  # OPUS ADDITION

  drift_handling:
    detect: Phoenix vs IBKR mismatch
    alert: Immediate notification (Telegram)
    action: Flag for human review (NO auto-correct)

  # GPT INTEGRATION: Reconciliation beads
  bead_types:
    RECONCILIATION_DRIFT:
      bead_id: uuid
      bead_type: "RECONCILIATION_DRIFT"
      timestamp: ISO8601
      drift_type: enum[POSITION_COUNT, POSITION_SIZE, PNL, ORDER_STATUS]
      phoenix_state: dict
      broker_state: dict
      severity: enum[WARNING, CRITICAL]

    RECONCILIATION_RESOLUTION:
      bead_id: uuid
      bead_type: "RECONCILIATION_RESOLUTION"
      timestamp: ISO8601
      drift_bead_id: uuid (reference)
      resolution: enum[PHOENIX_CORRECTED, BROKER_CORRECTED, ACKNOWLEDGED]
      resolved_by: str (human identifier)
      notes: str
```

---

## SURFACE 6: PROMOTION

```yaml
PROMOTION:
  location: phoenix/execution/promotion/
  purpose: Shadow → live ceremony with evidence

  files:
    - __init__.py       # Module exports
    - checklist.py      # Promotion requirements
    - evidence_bundle.py # Bundle assembly
    - ceremony.py       # Promotion workflow

  # GPT INTEGRATION: Safety checks added
  requirements:
    pre_checks:  # NEW - before evidence review
      - NO active kill flags (Signalman)
      - NO unresolved reconciliation drift

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
    0: Assert kill_flag == False  # NEW
    1: Assert unresolved_drift_count == 0  # NEW
    2: Evidence bundle assembled
    3: DISPATCH:PROMOTE_STRATEGY intent
    4: T2 gate (human approval)
    5: PROMOTION bead emitted
    6: Strategy config updated (SHADOW → LIVE)
```

---

## SURFACE 7: STALE APPROVAL KILL GATE

```yaml
# GROK INTEGRATION: Critical safety addition
STALE_APPROVAL_GATE:
  location: phoenix/governance/stale_gate.py
  purpose: Prevent execution with outdated context

  adaptive_ttl:
    default: 30 min
    high_vol_regime: 15 min
    news_proximity: 10 min

  stale_threshold: 15 min (configurable)

  behavior:
    on_stale_intent:
      1: Intent received with stale state_hash
      2: STATE_CONFLICT returned
      3: Temporary kill flag AUTO-SET (5 min)
      4: Requires explicit state refresh
      5: Alert via Telegram

  invariant: INV-STALE-KILL-1

  # OPUS CLARIFICATION: Emergency closes bypass
  bypass_for_exits: TRUE
  rationale: "Exits should always be possible, even on stale context"
```

---

## SEAMS

```yaml
SEAM_CSE_TO_EXECUTION:
  boundary: CSO | Execution Pipeline
  contract:
    cso_provides: CSE-formatted signal
    execution_validates: CSE schema compliance
    execution_requires: State hash fresh (<15 min)
    execution_requires: No kill flags active
    execution_routes: To T2 approval workflow
  invariant: INV-CSE-1

SEAM_APPROVAL_TO_BROKER:
  boundary: T2 Approval | IBKR Connector
  contract:
    approval_provides: Valid token + order params
    broker_validates: Token exists, not expired, not used
    broker_marks: Token as used (single-use)
    broker_emits: T2_TOKEN bead (USED)
    broker_submits: Order to IBKR
    broker_returns: Order ID + status
  invariant: INV-T2-TOKEN-1, INV-T2-GATE-1

SEAM_BROKER_TO_LIFECYCLE:
  boundary: IBKR Connector | Position Lifecycle
  contract:
    broker_reports: Fill details (including partial)
    lifecycle_transitions: SUBMITTED → FILLED (or STALLED)
    lifecycle_emits: POSITION bead
    lifecycle_triggers: Reconciliation check
  invariant: INV-POSITION-AUDIT-1

SEAM_LIFECYCLE_TO_AUTOPSY:
  boundary: Position Lifecycle | Autopsy (S31)
  contract:
    lifecycle_reports: Position closed
    autopsy_receives: Position ID + outcome
    autopsy_queries: Entry thesis (original evidence)
    autopsy_emits: AUTOPSY bead
  integration: Wire S31 Autopsy._trigger_autopsy

SEAM_RECONCILIATION_TO_ALERT:
  boundary: Reconciliation | Alert Pipeline
  contract:
    reconciler_detects: Drift
    reconciler_emits: RECONCILIATION_DRIFT bead
    alert_fires: Immediate notification
    alert_includes: Mismatch details
    alert_escalates: If unresolved >15 min
  invariant: INV-RECONCILE-ALERT-1, INV-RECONCILE-AUDIT-1

SEAM_SHADOW_TO_PROMOTION:
  boundary: Shadow Boxer (S30) | Promotion
  contract:
    shadow_provides: Performance beads
    promotion_validates: Kill flags clear
    promotion_validates: No unresolved drift
    promotion_queries: Evidence requirements
    promotion_validates: Checklist complete
    promotion_gates: T2 human approval
  invariant: INV-PROMOTION-EVIDENCE-1, INV-PROMOTION-SAFE-1
```

---

## INVARIANTS (17 TOTAL)

```yaml
# Original (10)
INV-T2-TOKEN-1:
  statement: "Approval tokens are single-use, expire in 5 minutes"
  test: test_t2_token_security.py

INV-T2-GATE-1:
  statement: "No order submission without valid T2 token"
  test: test_t2_gate_enforcement.py

INV-POSITION-AUDIT-1:
  statement: "POSITION bead emitted at every state transition"
  test: test_position_lifecycle_beads.py

INV-POSITION-SM-1:
  statement: "Position state machine only allows valid transitions"
  test: test_position_state_machine.py

INV-RECONCILE-ALERT-1:
  statement: "Position drift triggers immediate alert"
  test: test_reconciliation_alert.py

INV-RECONCILE-READONLY-1:
  statement: "Reconciliation detects but does not auto-correct"
  test: test_reconciliation_readonly.py

INV-PROMOTION-EVIDENCE-1:
  statement: "Strategy promotion requires evidence bundle"
  test: test_promotion_checklist.py

INV-PROMOTION-T2-1:
  statement: "Promotion is T2 gated (human approval)"
  test: test_promotion_t2.py

INV-IBKR-MOCK-1:
  statement: "All IBKR tests use mock client (no real API in tests)"
  test: (meta) verify test imports

INV-KILL-BLOCKS-ENTRY-1:
  statement: "Active kill flag blocks new position entry"
  test: test_kill_blocks_entry.py

# NEW (7) — Advisor additions
INV-T2-TOKEN-AUDIT-1:
  statement: "Every token state change emits T2_TOKEN bead"
  test: test_t2_token_audit.py

INV-POSITION-SUBMITTED-TTL-1:
  statement: "SUBMITTED > 60s without ACK → STALLED + alert"
  test: test_position_stalled.py

INV-RECONCILE-AUDIT-1:
  statement: "Every drift emits RECONCILIATION_DRIFT bead"
  test: test_reconciliation_drift_bead.py

INV-RECONCILE-AUDIT-2:
  statement: "Every resolution emits RECONCILIATION_RESOLUTION bead"
  test: test_reconciliation_resolution_bead.py

INV-PROMOTION-SAFE-1:
  statement: "Promotion rejected if kill flag active"
  test: test_promotion_kill_check.py

INV-PROMOTION-SAFE-2:
  statement: "Promotion rejected if unresolved drift exists"
  test: test_promotion_drift_check.py

INV-STALE-KILL-1:
  statement: "State anchor >15min stale → STATE_CONFLICT + temporary kill"
  test: test_stale_kill_gate.py
```

---

## CHAOS VECTORS (17 TOTAL)

```yaml
# Wave 1: Token Security (5)
CV_S32_TOKEN_REPLAY:
  inject: Attempt to reuse approval token
  expect: REJECTED, T2_TOKEN bead (REJECTED), audit logged

CV_S32_TOKEN_EXPIRED:
  inject: Use token after 5 minutes
  expect: REJECTED as expired, T2_TOKEN bead (EXPIRED)

CV_S32_TOKEN_WRONG_INTENT:
  inject: Use token for different intent than approved
  expect: REJECTED (intent_id mismatch)

CV_S32_ORDER_WITHOUT_TOKEN:
  inject: Submit order with no token
  expect: REJECTED at connector layer

CV_S32_TOKEN_RACE:  # NEW
  inject: Two validation requests for same token simultaneously
  expect: One succeeds (marks used), second fails

# Wave 2: IBKR Chaos (4)
CV_S32_IBKR_TIMEOUT:
  inject: Mock IBKR with 30s delay
  expect: Timeout → STALLED state, alert fired

CV_S32_IBKR_REJECTION:
  inject: Mock IBKR rejects order (insufficient margin)
  expect: SUBMITTED → REJECTED, alert, no retry

CV_S32_FILL_PARTIAL:
  inject: Mock partial fill (50%)
  expect: Position reflects partial, partial_fill_ratio correct

CV_S32_PARTIAL_DRIFT:  # NEW
  inject: Mock 50% fill, spoof broker reporting 60%
  expect: RECONCILIATION_DRIFT bead, alert

# Wave 3: Reconciliation (2)
CV_S32_RECONCILIATION_DRIFT:
  inject: IBKR mock returns wrong position
  expect: Drift detected, RECONCILIATION_DRIFT bead, no auto-correct

CV_S32_ORDER_RACE:
  inject: Two orders same intent simultaneously
  expect: One succeeds, one rejected (idempotent)

# Wave 4: Lifecycle + Promotion (6)
CV_S32_LIFECYCLE_INVALID:
  inject: Force invalid state transition (PROPOSED → CLOSED)
  expect: State machine rejects

CV_S32_PROMOTION_BYPASS:
  inject: Attempt live trading without shadow period
  expect: REJECTED, checklist incomplete

CV_S32_PROMOTION_PARTIAL:
  inject: Promotion with incomplete evidence
  expect: REJECTED, missing requirements listed

CV_S32_PROMOTION_VETO:  # NEW
  inject: Attempt promotion with active kill flag
  expect: REJECTED, kill flag cited

CV_S32_KILL_ENTRY_ATTEMPT:
  inject: Order submission while kill flag active
  expect: REJECTED pre-broker

CV_S32_STALE_APPROVAL:
  inject: Approve then wait 16 min (exceeds 15-min threshold)
  expect: STATE_CONFLICT, temporary kill set
```

---

## BUNNY WAVE ORDER

```yaml
WAVE_1_TOKEN_SECURITY:
  vectors: 5
  tests:
    - CV_S32_TOKEN_REPLAY
    - CV_S32_TOKEN_EXPIRED
    - CV_S32_TOKEN_WRONG_INTENT
    - CV_S32_ORDER_WITHOUT_TOKEN
    - CV_S32_TOKEN_RACE

WAVE_2_IBKR_CHAOS:
  vectors: 4
  mode: REALISTIC
  tests:
    - CV_S32_IBKR_TIMEOUT
    - CV_S32_IBKR_REJECTION
    - CV_S32_FILL_PARTIAL
    - CV_S32_PARTIAL_DRIFT

WAVE_3_RECONCILIATION:
  vectors: 2
  tests:
    - CV_S32_RECONCILIATION_DRIFT
    - CV_S32_ORDER_RACE

WAVE_4_LIFECYCLE_PROMOTION:
  vectors: 6
  tests:
    - CV_S32_LIFECYCLE_INVALID
    - CV_S32_PROMOTION_BYPASS
    - CV_S32_PROMOTION_PARTIAL
    - CV_S32_PROMOTION_VETO
    - CV_S32_KILL_ENTRY_ATTEMPT
    - CV_S32_STALE_APPROVAL

TOTAL: 17 vectors
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
  criterion: Single-use, 5 min expiry, replay rejected, beads emitted
  test: test_t2_token_security.py
  evidence: All token chaos vectors PASS

GATE_S32_3:
  name: POSITION_LIFECYCLE_TRACKED
  criterion: State machine transitions (including STALLED), beads emitted
  test: test_position_lifecycle_e2e.py
  evidence: Full lifecycle with POSITION beads

GATE_S32_4:
  name: RECONCILIATION_WORKS
  criterion: Induced mismatch → detected → drift bead → alerted
  test: test_reconciliation_e2e.py
  evidence: Drift detected, resolution tracked

GATE_S32_5:
  name: PROMOTION_CHECKLIST
  criterion: Shadow → live requires evidence + kill check + T2
  test: test_promotion_e2e.py
  evidence: Incomplete → rejected, kill active → rejected

GATE_S32_6:
  name: KILL_BLOCKS_ENTRY
  criterion: Kill flag prevents new positions
  test: test_kill_integration.py
  evidence: Entry blocked when signalman kill active

GATE_S32_7:
  name: STALE_GATE_WORKS
  criterion: Stale approval → STATE_CONFLICT + temp kill
  test: test_stale_gate_e2e.py
  evidence: 16-min-old intent rejected

GATE_S32_8:
  name: BUNNY_PASSES
  criterion: All 17 S32 chaos vectors green
  test: chaos_suite_s32.py
  evidence: BUNNY_REPORT_S32.md

BINARY_EXIT:
  statement: "T2 workflow proven on paper, IBKR connected"
```

---

## TRACKS

```yaml
TRACK_A_IBKR:
  scope: Broker connector + mock with chaos modes
  week: 1
  files:
    - phoenix/brokers/ibkr/__init__.py
    - phoenix/brokers/ibkr/connector.py
    - phoenix/brokers/ibkr/orders.py
    - phoenix/brokers/ibkr/positions.py
    - phoenix/brokers/ibkr/account.py
    - phoenix/brokers/ibkr/mock_client.py
  tests:
    - tests/brokers/test_ibkr_connector.py
    - tests/brokers/test_ibkr_orders.py
    - tests/brokers/test_ibkr_mock.py
  depends_on: None
  blocks: Track B, Track C

TRACK_B_T2_WORKFLOW:
  scope: Approval tokens + evidence display + beads
  week: 2
  files:
    - phoenix/governance/t2/__init__.py
    - phoenix/governance/t2/approval.py
    - phoenix/governance/t2/tokens.py
    - phoenix/governance/t2/evidence.py
    - phoenix/governance/t2/cache.py
    - phoenix/governance/stale_gate.py
  tests:
    - tests/governance/test_t2_tokens.py
    - tests/governance/test_t2_approval.py
    - tests/governance/test_t2_evidence.py
    - tests/governance/test_stale_gate.py
  depends_on: Track A
  blocks: Track C

TRACK_C_POSITION_LIFECYCLE:
  scope: State machine (9 states) + reconciliation + beads
  week: 2-3
  files:
    - phoenix/execution/positions/__init__.py
    - phoenix/execution/positions/lifecycle.py
    - phoenix/execution/positions/states.py
    - phoenix/execution/positions/transitions.py
    - phoenix/execution/positions/tracker.py
    - phoenix/execution/reconciliation/__init__.py
    - phoenix/execution/reconciliation/reconciler.py
    - phoenix/execution/reconciliation/drift.py
    - phoenix/execution/reconciliation/resolver.py
  tests:
    - tests/execution/test_position_lifecycle.py
    - tests/execution/test_reconciliation.py
  depends_on: Track A, Track B
  blocks: Track D

TRACK_D_PROMOTION:
  scope: Shadow → live ceremony with safety checks
  week: 3
  files:
    - phoenix/execution/promotion/__init__.py
    - phoenix/execution/promotion/checklist.py
    - phoenix/execution/promotion/evidence_bundle.py
    - phoenix/execution/promotion/ceremony.py
  tests:
    - tests/execution/test_promotion.py
  depends_on: Track C
  blocks: Track E

TRACK_E_INTEGRATION:
  scope: Full flow testing + BUNNY (17 vectors)
  week: 3-4
  files:
    - tests/integration/test_s32_e2e.py
    - tests/chaos/test_bunny_s32.py
  depends_on: All tracks
  deliverable: BUNNY_REPORT_S32.md
```

---

## RESOLVED QUESTIONS

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
  answer: Option A (single position tracks partial)
  addition: partial_fill_ratio, filled_quantity, requested_quantity fields

Q4_RECONCILIATION_FREQUENCY:
  answer: Configurable, default 5min
  guardrail: Rate limit max 12/min, env var RECONCILE_INTERVAL_SEC
  immediate_triggers: Fill, Reject, Cancel, Drift

Q5_MOCK_FIDELITY:
  answer: Banteg-style chaos modes
  modes: INSTANT (unit tests), REALISTIC (bunny), ADVERSARIAL (stress)
```

---

## RISK REGISTER

```yaml
RISK_1_IBKR_API_COMPLEXITY:
  likelihood: HIGH
  impact: MEDIUM
  mitigation:
    - Mock-first development
    - ib_insync abstracts complexity
    - Market orders only (limit deferred)
    - Defer edge cases to S33

RISK_2_TOKEN_SECURITY:
  likelihood: LOW
  impact: HIGH
  mitigation:
    - UUID generation (secrets module)
    - 5-min expiry (short window)
    - Single-use enforcement
    - T2_TOKEN beads for audit

RISK_3_STATE_DESYNC:
  likelihood: MEDIUM
  impact: MEDIUM
  mitigation:
    - Reconciliation worker
    - RECONCILIATION_DRIFT beads
    - Alert on drift
    - Human resolution (no auto-correct)

RISK_4_STALE_EXECUTION:
  likelihood: MEDIUM
  impact: HIGH
  mitigation:
    - 15-min stale threshold
    - STATE_CONFLICT + temp kill
    - Exit bypass allowed
```

---

## HANDOFF TO S33

```yaml
S33_RECEIVES:
  ibkr_connector:
    - Full API integration (market orders)
    - Mock client with chaos modes
    - Rate limit handling

  t2_workflow:
    - Token generation + validation
    - T2_TOKEN bead audit trail
    - Stale approval kill gate
    - Evidence bundle assembly

  position_lifecycle:
    - State machine (9 states including STALLED)
    - POSITION beads at transitions
    - Partial fill tracking
    - Tracker for active positions

  reconciliation:
    - Drift detection with beads
    - Resolution tracking
    - Alert on mismatch
    - No auto-correct (human resolves)

  promotion:
    - Checklist validation (+ kill/drift checks)
    - Evidence bundle requirements
    - T2 ceremony for live activation

  bunny_report:
    - BUNNY_REPORT_S32.md
    - 17/17 chaos vectors green

S33_BUILDS:
  - Limit/bracket orders
  - Position sizing (Kelly, fractional)
  - Advanced risk management
  - Market regime detection
```

---

## OPUS REVIEW SUMMARY

```yaml
FRESH_EYES_OBSERVATIONS:

  STRENGTHS:
    - T2_TOKEN beads provide complete audit trail
    - STALLED state prevents zombie positions
    - Stale approval kill gate is critical safety
    - Mock chaos modes enable realistic testing
    - Promotion safety checks (kill + drift) are essential

  ENHANCEMENTS_MADE:
    - Added rate limiting awareness to IBKR connector
    - Scoped S32 to MARKET orders only (limit deferred)
    - Clarified emergency close bypass for exits
    - Added API throttle guardrails (12/min reconcile)

  INTEGRATION_POINTS:
    from_s31:
      - KillManager (already built)
      - StateAnchorManager (already built)
      - Autopsy (wire to position close)
      - TelegramNotifier (for alerts)
    new_wiring:
      - CSO → T2 workflow
      - T2 → IBKR connector
      - Lifecycle → Autopsy
      - Reconciliation → Telegram

  CONCERNS_ADDRESSED:
    - GROK blocker: Mock fidelity → banteg chaos modes
    - GROK blocker: Stale approval → kill gate
    - GPT flag: Token audit → T2_TOKEN beads
    - GPT flag: SUBMITTED timeout → STALLED state

  EXECUTION_READY: TRUE
```

---

```yaml
BUILD_MAP_STATUS: FINAL_v0.2
BLOCKERS: 0
INVARIANTS: 17
CHAOS_VECTORS: 17
EXIT_GATES: 8
TRACKS: 5

READY_FOR: OPUS EXECUTION
```

---

*S32 EXECUTION_PATH: "Real markets await. T2 guards the gate."*
