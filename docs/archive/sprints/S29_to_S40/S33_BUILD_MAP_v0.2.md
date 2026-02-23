# S33_BUILD_MAP_v0.2.md

**Sprint:** S33 FIRST_BLOOD  
**Theme:** "One pair, real money"  
**Duration:** 2-3 weeks (validation period)  
**Risk Tier:** MAXIMUM (real capital)  
**Status:** CANONICAL — READY FOR EXECUTION

---

## BUILD MAP STATUS

```yaml
BUILD_MAP_STATUS: FINAL_v0.2
BLOCKERS: 0
INVARIANTS: 12 (6 from S32 context + 6 new)
CHAOS_VECTORS: 15
RUNBOOKS: 8
TRACKS: 6

READY_FOR: OPUS EXECUTION
```

---

## SPRINT CONTEXT

```yaml
S32_PROVIDES:
  - IBKR connector (mock, chaos-proven) ✓
  - T2 approval workflow (tokens, evidence, stale gate) ✓
  - Position lifecycle (9 states, STALLED) ✓
  - Reconciliation (read-only, drift detection) ✓
  - Promotion ceremony (shadow → live) ✓
  - 60 tests passing, 17 BUNNY vectors ✓

S33_BUILDS:
  phase_1_infrastructure:
    - Real IBKR connection (swap mock → real)
    - Paper trading validation
    - 24/7 monitoring with semantic health
    - Incident runbooks (8 total)
    - Telegram to real device
    - Claude Desktop UX validation
    - Mock CSE generator script
    olya_dependency: NONE

  phase_2_first_blood:
    - EUR/USD live (real capital)
    - N days validation
    - Ops quality gates
    - Revalidation on param change
    olya_dependency: YES (her capital, her pace)

S33_EXIT_GATE:
  binary: "6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents"

  phase_1_gate: |
    - Paper trade round-trip complete
    - Minimum 3 paper trades across 2 sessions
    - At least 1 forced disconnect + recovery drill
    - Runbook drill completed (RB-004 minimum)
    - UX validated

  phase_2_gate: "N days live, ops quality met, no param changes without revalidation"

S33_SCOPE_DISCIPLINE:
  FORBIDDEN:
    - NO optimization
    - NO multi-pair live (capability yes, active no)
    - NO automation of approval
    - NO hot-flip paper → live
  MANTRA: "Boring is safe. Safe is fast."
```

---

## SCHEMA ADDITIONS (S33)

```yaml
# Add to phoenix/schemas/beads.yaml

IBKR_SESSION_BEAD:
  extends: base_bead_fields
  bead_type_value: "IBKR_SESSION"

  fields:
    event:
      type: enum
      values: [CONNECT, DISCONNECT, RECONNECT]
      description: Session event type
      required: true

    mode:
      type: enum
      values: [MOCK, PAPER, LIVE]
      description: Connection mode
      required: true

    account:
      type: string
      description: Account ID (DU* for paper, U* for live)
      required: true

    port:
      type: int
      description: Gateway port (4002 paper, 4001 live)
      required: true

    gateway_version:
      type: string
      description: IB Gateway version (if available)
      required: false

    reconnect_attempt:
      type: int
      description: Attempt number (if RECONNECT event)
      required: false
      default: 0

HEARTBEAT_BEAD:
  extends: base_bead_fields
  bead_type_value: "HEARTBEAT"

  fields:
    status:
      type: enum
      values: [HEALTHY, DEGRADED, MISSED]
      description: Health status
      required: true

    checks:
      type: object
      description: Individual health check results
      required: true
      fields:
        process_alive:
          type: bool
        ibkr_connected:
          type: bool
        semantic_healthy:
          type: bool

    details:
      type: object
      description: Details if DEGRADED or MISSED
      required: false

    miss_count:
      type: int
      description: Consecutive miss count
      required: false
      default: 0
```

---

## PHASE 1: INFRASTRUCTURE (NO OLYA DEPENDENCY)

### SURFACE 1: REAL IBKR CONNECTION

```yaml
SURFACE_1_REAL_IBKR:
  location: phoenix/brokers/ibkr/
  purpose: Swap mock client → real IBKR connection with ironclad guards

  files:
    - connector.py (update with mode guards)
    - config.py (new - connection config)
    - real_client.py (new - ib_insync wrapper)
    - session_bead.py (new - session bead emission)

  connection:
    library: ib_insync
    gateway: IB Gateway (already installed)
    port_separation:
      paper: 4002
      live: 4001
    account_prefix:
      paper: DU*
      live: U*

  # BLOCKING: Paper-first invariant hardening
  env_guards:
    IBKR_MODE: enum[mock, paper, live] (default: mock)
    IBKR_ALLOW_LIVE: bool (default: false)

  startup_validation:
    - Assert IBKR_MODE != live unless IBKR_ALLOW_LIVE=true
    - Assert account prefix matches mode (DU* for paper, U* for live)
    - Assert port matches mode (4002 for paper, 4001 for live)
    - Emit IBKR_SESSION bead on connect

  order_submit_guard:
    - Re-check account + port before EVERY order submit
    - Reject if mismatch detected
    - Log violation as CRITICAL

  live_enable_ceremony:
    - Requires: IBKR_ALLOW_LIVE=true in .env
    - Requires: Manual restart (no hot-flip)
    - Future: Olya veto bead for live mode

  reconnect_strategy:
    attempts: 3
    backoff: exponential (5s, 15s, 45s)
    max_time: 65s total
    after_max_attempts:
      - Alert via Telegram: "Connection rotting — run RB-001"
      - Require manual restart
      - Do NOT auto-retry indefinitely
    on_reconnect:
      - Emit IBKR_SESSION bead (RECONNECT)
      - Re-validate subscriptions
      - Immediate reconciliation

  validation:
    - Connect to IB Gateway
    - Query account balance
    - Submit paper order
    - Receive fill confirmation
    - Track position

  invariants:
    - INV-IBKR-PAPER-FIRST-1: "Paper validation before live"
    - INV-IBKR-PAPER-GUARD-1: "Live mode requires IBKR_ALLOW_LIVE=true + restart"
    - INV-IBKR-ACCOUNT-CHECK-1: "Every order submit validates account matches mode"
    - INV-IBKR-RECONNECT-1: "Max 3 reconnect attempts, then human escalation"
```

### SURFACE 2: MONITORING WITH SEMANTIC HEALTH

```yaml
SURFACE_2_MONITORING:
  location: phoenix/monitoring/ops/
  purpose: 24/7 operational health with semantic checks

  files:
    - daemon_monitor.py    # Process health
    - heartbeat.py         # Liveness + semantic checks
    - semantic_health.py   # Deep health validation
    - ops_dashboard.py     # Status summary

  # BLOCKING: Heartbeat hardening
  heartbeat_config:
    frequency: 30s (compromise between detection speed and overhead)
    jitter: ±5s (banteg fuzz tolerance)
    miss_threshold: 3 consecutive (90s max blind)
    bead_emission: HEARTBEAT bead on every check

  process_checks:
    - Daemon processes alive
    - IBKR connection healthy
    - River data flowing
    - Telegram bot responsive

  semantic_checks:
    orders_flowing:
      - If orders pending, check status updating
      - Stale order status > 5min → DEGRADED

    fills_updating:
      - If positions open, check last_fill_timestamp
      - Stale fills > 10min → WARNING

    subscriptions_alive:
      - Verify market data subscriptions active
      - Dead subscription → ALERT

    reconciliation_fresh:
      - reconciliation_last_run < 10 min
      - No unresolved drift
      - No stuck STALLED positions

  health_state_enum:
    HEALTHY: All checks pass
    DEGRADED: Semantic issues, process alive
    CRITICAL: Process or connection down

  alerts:
    - Process death → immediate CRITICAL
    - Connection loss → immediate CRITICAL
    - Semantic degradation → WARNING (escalate after 5min)
    - Reconciliation drift → immediate CRITICAL
    - STALLED > 5min → WARNING

  athena_query: "Show heartbeat gaps last N hours"

  invariants:
    - INV-OPS-HEARTBEAT-SEMANTIC-1: "Heartbeat includes semantic health checks"
    - INV-OPS-HEARTBEAT-30S-1: "Heartbeat every 30s ±5s jitter"
```

### SURFACE 3: INCIDENT RUNBOOKS

```yaml
SURFACE_3_INCIDENT_RUNBOOKS:
  location: phoenix/docs/runbooks/
  purpose: Documented procedures for incidents

  runbooks:
    - RB-001_CONNECTION_LOSS.md
    - RB-002_RECONCILIATION_DRIFT.md
    - RB-003_STALLED_POSITION.md
    - RB-004_EMERGENCY_HALT.md
    - RB-005_KILL_FLAG_ACTIVE.md
    - RB-006_TELEGRAM_DOWN.md
    - RB-007_GATEWAY_AUTO_UPDATE.md (NEW)
    - RB-008_PACING_VIOLATION.md (NEW)

  total: 8 runbooks

  format:
    - Symptoms
    - Immediate actions
    - Investigation steps
    - Resolution
    - Post-incident review

  gateway_gotchas_documented:
    - Auto-updates can restart process (pin version if possible)
    - Timezone mismatches affect session state
    - Pacing violations may not throw hard errors
    - Silent disconnects possible

  training: Drill at least one before live (RB-004 minimum)

  invariant:
    - INV-OPS-RUNBOOK-1: "Every CRITICAL alert type has documented runbook"
```

### SURFACE 4: TELEGRAM LIVE

```yaml
SURFACE_4_TELEGRAM_LIVE:
  location: phoenix/notification/
  purpose: Real device notifications

  validation:
    - Bot token configured (.env)
    - Chat ID configured
    - Test message delivered
    - Alert aggregation working
    - Throttle functional
    - CRITICAL bypasses throttle

  test_sequence:
    1. Health check ping
    2. Mock READY alert
    3. Mock DRIFT alert
    4. Mock KILL alert
    5. Aggregation test (10 alerts → batched)
    6. Flood test (50 alerts → throttled)

  invariant:
    - INV-TELEGRAM-LIVE-1: "Telegram alerts reach real device"
```

### SURFACE 5: MOCK CSE GENERATOR

```yaml
SURFACE_5_MOCK_CSE_GENERATOR:
  location: phoenix/mocks/mock_cse_generator.py
  purpose: Scripted mock signal generation for UX testing

  usage:
    1. Claude Desktop generates CSE structure
    2. G runs: python mock_cse_generator.py --signal READY --pair EURUSD
    3. Script writes to /phoenix/intents/incoming/mock_intent.yaml
    4. Phoenix processes as normal

  cli_schema:
    python mock_cse_generator.py \
      --signal READY|FORMING|NONE \
      --pair EURUSD|GBPUSD|USDJPY|AUDUSD|USDCAD|NZDUSD \
      --confidence 0.85 \
      --entry 1.0850 \
      --stop 1.0820 \
      --target 1.0910 \
      --setup-type FVG_ENTRY|OTE_ENTRY|BOS_ENTRY

  benefits:
    - No copy-paste errors
    - Human-in-loop preserved
    - Testable, repeatable
    - Schema-validated output
```

### SURFACE 6: CLAUDE DESKTOP UX

```yaml
SURFACE_6_CLAUDE_DESKTOP_CSO:
  location: (external - Claude Desktop app)
  purpose: UX validation without Olya

  mock_cso_capability:
    knowledge_source: phoenix/cso/knowledge/ (5-drawer)
    signal_generation: Via mock_cse_generator.py

  test_scenarios:
    - EXPLORE session (pure thinking)
    - Hunt hypothesis test
    - Athena memory query
    - CSO mock signal → T2 approval
    - Paper order execution
    - Checkpoint mechanics
    - Stale gate trigger

  validation_criteria:
    - "Superpower feeling" present
    - Friction points identified
    - UX smooth for approval flow
    - Evidence display clear
    - Token mechanics invisible to user

  invariant:
    - INV-UX-APPROVAL-1: "T2 approval flow completable in <30 seconds"
```

---

## SEAMS (PHASE 1)

```yaml
SEAM_MOCK_TO_REAL:
  boundary: Mock Client | Real IBKR
  contract:
    interface: Unchanged (IBKRConnector)
    switch: Config flag (IBKR_MODE=paper|live|mock)
    behavior: Identical API, different backend
    guards: Account + port validation on every operation
  validation: Same tests pass with real client

SEAM_MONITORING_TO_ALERT:
  boundary: Ops Monitor | Telegram
  contract:
    monitor_detects: Issue (process, connection, semantic, drift)
    alert_fires: Via existing Telegram surface
    priority: CRITICAL bypasses throttle
    bead_emission: HEARTBEAT bead on every check
  existing: Telegram already built (S31)

SEAM_DESKTOP_TO_PHOENIX:
  boundary: Claude Desktop | Phoenix File Seam
  contract:
    desktop_writes: /phoenix/intents/incoming/intent.yaml
    phoenix_responds: /phoenix/responses/response.md
    lens_injects: Response into Desktop view
    mock_cse: Via mock_cse_generator.py script
  existing: File seam architecture (S29)
```

---

## WIRING (PHASE 1)

```yaml
WIRE_PAPER_TRADE_ROUND_TRIP:
  flow: |
    Claude Desktop (mock CSO): Emit test READY signal
         ↓
    G runs: mock_cse_generator.py --signal READY --pair EURUSD
         ↓
    Intent written: DISPATCH:APPROVE (CSE format)
         ↓
    State anchor validates: FRESH
         ↓
    Evidence bundle displayed
         ↓
    Human (G): [APPROVE]
         ↓
    T2 token generated
         ↓
    IBKR connector (PAPER mode): Validate account + port
         ↓
    Submit order (with account guard check)
         ↓
    IB Gateway: Receives order
         ↓
    Paper fill returned
         ↓
    Position lifecycle: SUBMITTED → FILLED → MANAGED
         ↓
    Reconciliation: Validates match
         ↓
    POSITION bead emitted
         ↓
    Paper P&L tracked
         ↓
    Close position (manual or SL/TP)
         ↓
    Autopsy triggered
         ↓
    AUTOPSY bead emitted

  validation: Full lifecycle on paper, all beads present

WIRE_MONITORING_ALERT:
  flow: |
    Daemon monitor: Check every 30s ±5s
         ↓
    Process checks + semantic health checks
         ↓
    HEARTBEAT bead emitted (HEALTHY|DEGRADED|MISSED)
         ↓
    Issue detected (process/connection/semantic/drift)
         ↓
    Alert classified (WARNING/CRITICAL)
         ↓
    Telegram notifies (CRITICAL bypasses throttle)
         ↓
    Human reviews
         ↓
    Runbook followed
         ↓
    Resolution logged

WIRE_RECONNECTION:
  flow: |
    Connection loss detected
         ↓
    IBKR_SESSION bead (DISCONNECT)
         ↓
    Backoff: 5s wait
         ↓
    Attempt 1: Connect
         ↓ (fail)
    IBKR_SESSION bead (RECONNECT, attempt=1)
         ↓
    Backoff: 15s wait
         ↓
    Attempt 2: Connect
         ↓ (fail)
    IBKR_SESSION bead (RECONNECT, attempt=2)
         ↓
    Backoff: 45s wait
         ↓
    Attempt 3: Connect
         ↓ (fail)
    IBKR_SESSION bead (RECONNECT, attempt=3, escalated=true)
         ↓
    Alert: "Connection rotting — run RB-001"
         ↓
    Require manual restart
```

---

## INVARIANTS (ALL S33)

```yaml
# IBKR Connection
INV-IBKR-PAPER-FIRST-1:
  statement: "Paper trading validation required before live"
  test: test_ibkr_paper_mode.py
  proof: Live mode blocked until paper validation complete

INV-IBKR-PAPER-GUARD-1:
  statement: "Live mode requires IBKR_ALLOW_LIVE=true + restart"
  test: test_ibkr_paper_guard.py
  proof: Startup rejects live without explicit flag

INV-IBKR-ACCOUNT-CHECK-1:
  statement: "Every order submit validates account matches mode"
  test: test_ibkr_account_guard.py
  proof: Mismatch → rejection before order sent

INV-IBKR-RECONNECT-1:
  statement: "Max 3 reconnect attempts, then human escalation"
  test: test_ibkr_reconnect.py
  proof: After 3 attempts → alert + manual required

INV-IBKR-CONFIG-1:
  statement: "IBKR credentials never in code, only .env"
  test: (code review)
  proof: No hardcoded credentials

# Monitoring
INV-OPS-HEARTBEAT-SEMANTIC-1:
  statement: "Heartbeat includes semantic health, not just process"
  test: test_ops_heartbeat_semantic.py
  proof: DEGRADED state on semantic issues

INV-OPS-HEARTBEAT-30S-1:
  statement: "Heartbeat every 30s ±5s jitter"
  test: test_ops_heartbeat_timing.py
  proof: Timing within spec

INV-OPS-RUNBOOK-1:
  statement: "Every CRITICAL alert type has documented runbook"
  test: test_runbook_coverage.py
  proof: Alert types mapped to runbook files

# Telegram
INV-TELEGRAM-LIVE-1:
  statement: "Telegram alerts reach real device"
  test: test_telegram_delivery.py
  proof: Test message received

# UX
INV-UX-APPROVAL-1:
  statement: "T2 approval flow completable in <30 seconds"
  test: Manual timing
  proof: G validates during UX testing

# Phase 2
INV-PHASE2-REVALIDATE-1:
  statement: "Any param change triggers shadow restart + Bunny sweep"
  test: test_param_change_revalidation.py
  proof: CONFIG_CHANGE bead → shadow restart
```

---

## CHAOS VECTORS (15 TOTAL)

```yaml
# Wave 1: IBKR Connection (3 vectors)
CV_S33_1_IBKR_DISCONNECT:
  inject: Kill IB Gateway mid-session
  expect: Connection loss detected, alert fired, IBKR_SESSION bead (DISCONNECT)

CV_S33_2_IBKR_RECONNECT:
  inject: Restart IB Gateway
  expect: Connector reconnects within 3 attempts, state recovered

CV_S33_3_GATEWAY_AUTO_UPDATE:
  inject: Simulate gateway restart (like auto-update)
  expect: Reconnect + IBKR_SESSION bead + reconciliation

# Wave 2: Monitoring (3 vectors)
CV_S33_4_MONITORING_PROCESS_DEATH:
  inject: Kill a daemon process
  expect: Heartbeat detects, HEARTBEAT bead (MISSED), alert fired

CV_S33_5_SEMANTIC_HEALTH_DEGRADE:
  inject: Stale order status (no updates 10min)
  expect: DEGRADED state detected, HEARTBEAT bead shows semantic issue

CV_S33_6_HEARTBEAT_JITTER:
  inject: Network latency variance ±10s
  expect: Jitter absorbs, no false alerts within spec

# Wave 3: Telegram (2 vectors)
CV_S33_7_TELEGRAM_TIMEOUT:
  inject: Block Telegram API
  expect: Alert queued, retry logic, no crash

CV_S33_8_TELEGRAM_REAL_FLOOD:
  inject: 50 alerts in 1 minute
  expect: Aggregate + throttle, no device death

# Wave 4: UX Approval (2 vectors)
CV_S33_9_STALE_DURING_APPROVAL:
  inject: Wait >15min during approval flow
  expect: STATE_CONFLICT, approval blocked

CV_S33_10_PAPER_ORDER_REJECT:
  inject: Submit invalid order (bad symbol)
  expect: REJECTED state, alert, no crash

# Wave 5: Runbook Drill (2 vectors)
CV_S33_11_RUNBOOK_DRILL:
  inject: Simulate RB-004 (emergency halt)
  expect: Runbook followed, resolution time recorded

CV_S33_12_RECON_DRIFT_LIVE:
  inject: Spoof live position mismatch
  expect: Kill flag + runbook trigger

# Wave 6: Guards (3 vectors)
CV_S33_13_ACCOUNT_MISMATCH:
  inject: Attempt order on wrong account type
  expect: Rejected at submit guard, no order sent

CV_S33_14_PACING_VIOLATION:
  inject: Rapid order spam
  expect: Rate limit, no ban, warning logged

CV_S33_15_PARAM_CHANGE_REVALIDATE:
  inject: CSO param change mid-Phase 2
  expect: Shadow restart + Bunny sweep triggered

# BUNNY Wave Order
BUNNY_WAVE_ORDER:
  wave_1_ibkr_connection: [CV_S33_1, CV_S33_2, CV_S33_3]
  wave_2_monitoring: [CV_S33_4, CV_S33_5, CV_S33_6]
  wave_3_telegram: [CV_S33_7, CV_S33_8]
  wave_4_ux_approval: [CV_S33_9, CV_S33_10]
  wave_5_runbook_drill: [CV_S33_11, CV_S33_12]
  wave_6_guards: [CV_S33_13, CV_S33_14, CV_S33_15]
```

---

## EXIT GATES (PHASE 1)

```yaml
GATE_S33_P1_1:
  name: IBKR_PAPER_CONNECTED
  criterion: Real IB Gateway connection, paper account queries work
  evidence: Account balance returned, IBKR_SESSION bead emitted

GATE_S33_P1_2:
  name: PAPER_ROUND_TRIP
  criterion: Full order lifecycle on paper (submit → fill → close)
  evidence: POSITION beads show complete lifecycle

GATE_S33_P1_3:
  name: PAPER_VOLUME
  criterion: Minimum 3 paper trades across 2 sessions
  evidence: BeadStore shows 3+ POSITION beads with CLOSED state

GATE_S33_P1_4:
  name: MONITORING_OPERATIONAL
  criterion: Heartbeat running with semantic checks, alerts routing
  evidence: HEARTBEAT beads at 30s intervals, test alert received

GATE_S33_P1_5:
  name: RUNBOOKS_COMPLETE
  criterion: All 8 runbooks exist, one drill completed
  evidence: Runbook files exist, RB-004 drill documented

GATE_S33_P1_6:
  name: DISCONNECT_DRILL
  criterion: At least 1 forced disconnect + recovery drill
  evidence: IBKR_SESSION beads show DISCONNECT → RECONNECT sequence

GATE_S33_P1_7:
  name: UX_VALIDATED
  criterion: G confirms approval flow is smooth
  evidence: UX_VALIDATION_LOG.md

GATE_S33_P1_8:
  name: BUNNY_PHASE1_PASSES
  criterion: All 15 chaos vectors green
  evidence: BUNNY_REPORT_S33_P1.md

BINARY_EXIT_PHASE_1:
  statement: |
    "Paper trade round-trip complete (3+ trades),
     UX validated, disconnect drill passed,
     runbook drill completed"
```

---

## PHASE 2: FIRST BLOOD (OLYA-DEPENDENT)

```yaml
PHASE_2_SCOPE:
  status: DESIGN_ONLY (build when Olya ready)

  prerequisites:
    - Phase 1 complete ✓
    - Olya's CSO calibrated to her methodology
    - Shadow period complete (promotion checklist)
    - Olya comfortable with system

  deliverables:
    - EUR/USD live trading (real capital)
    - 6-pair capability proven (architecture)
    - N days validation (5-10 trading days)
    - Ops quality metrics met

  # BLOCKING: Param change revalidation
  revalidation_trigger:
    on_param_change:
      - Any CSO param update
      - Any config flip
      - Any strategy tune

    action:
      - Auto-trigger shadow period restart
      - 5-vector Bunny sweep on changed components
      - Athena query "Show bunny scars last N days"

  promotion_gate:
    - bunny_vectors_fail == 0 in validation period
    - If fail > 0 → extend validation, do not promote

  ops_quality_gates:
    reconciliation: Zero drift events
    alert_accuracy: Precision >80%, recall >90%
    latency: Median e2e <30s
    daemon_uptime: >99%

  exit_gate:
    binary: "6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents"

  note: |
    Phase 2 is Olya's phase.
    She joins when her CSO is calibrated.
    She decides when to go live.
    Her capital, her pace, her decision.
```

---

## TRACKS (PHASE 1)

```yaml
TRACK_A_REAL_IBKR:
  scope: Swap mock → real connection with guards
  files:
    - phoenix/brokers/ibkr/connector.py (update)
    - phoenix/brokers/ibkr/config.py (new)
    - phoenix/brokers/ibkr/real_client.py (new)
    - phoenix/brokers/ibkr/session_bead.py (new)
    - phoenix/.env.example (update)
  tests:
    - tests/brokers/test_ibkr_real.py
    - tests/brokers/test_ibkr_guards.py
  depends_on: IB Gateway running
  risk: External dependency

TRACK_B_MONITORING:
  scope: 24/7 ops health with semantic checks
  files:
    - phoenix/monitoring/ops/daemon_monitor.py
    - phoenix/monitoring/ops/heartbeat.py
    - phoenix/monitoring/ops/semantic_health.py
    - phoenix/monitoring/ops/ops_dashboard.py
  tests:
    - tests/monitoring/test_ops_health.py
    - tests/monitoring/test_heartbeat_semantic.py
  depends_on: None

TRACK_C_RUNBOOKS:
  scope: Incident documentation (8 total)
  files:
    - phoenix/docs/runbooks/RB-001_CONNECTION_LOSS.md
    - phoenix/docs/runbooks/RB-002_RECONCILIATION_DRIFT.md
    - phoenix/docs/runbooks/RB-003_STALLED_POSITION.md
    - phoenix/docs/runbooks/RB-004_EMERGENCY_HALT.md
    - phoenix/docs/runbooks/RB-005_KILL_FLAG_ACTIVE.md
    - phoenix/docs/runbooks/RB-006_TELEGRAM_DOWN.md
    - phoenix/docs/runbooks/RB-007_GATEWAY_AUTO_UPDATE.md (NEW)
    - phoenix/docs/runbooks/RB-008_PACING_VIOLATION.md (NEW)
  depends_on: Track B (understand what to document)

TRACK_D_TELEGRAM_VALIDATION:
  scope: Real device delivery
  files:
    - phoenix/.env (configure real tokens)
  tests:
    - tests/notification/test_telegram_real.py
  depends_on: Bot token + chat ID

TRACK_E_MOCK_CSE_GENERATOR:
  scope: Scripted mock signal generation
  files:
    - phoenix/mocks/mock_cse_generator.py (NEW)
  tests:
    - tests/mocks/test_mock_cse_generator.py
  depends_on: None

TRACK_F_UX_TESTING:
  scope: Claude Desktop validation
  owner: G (parallel to OPUS)
  method: Manual testing with mock CSO signals via mock_cse_generator.py
  deliverable: UX_VALIDATION_LOG.md

TRACK_G_BUNNY_PHASE1:
  scope: Chaos validation (15 vectors)
  files:
    - tests/chaos/test_bunny_s33_p1.py
  depends_on: Tracks A-E complete
  deliverable: BUNNY_REPORT_S33_P1.md
```

---

## RESOLVED QUESTIONS

```yaml
Q1_IB_GATEWAY_CONFIG:
  status: RESOLVED
  answer: Multiple guards + logging
  implementation:
    - Assert account type on connect
    - Log all IBKR warnings as ALERT
    - Emit IBKR_SESSION bead on connect/disconnect
    - Document gateway gotchas in runbooks (RB-007, RB-008)
    - Pin gateway version if possible

Q2_PAPER_VS_LIVE_PORT:
  status: RESOLVED
  answer: CONFIRMED + DUAL GUARD
  ports: 4002 (paper), 4001 (live)
  additional: Assert account prefix (DU* vs U*)

Q3_RECONNECTION_STRATEGY:
  status: RESOLVED
  answer: Option B + HUMAN ESCALATION
  spec:
    - Exponential backoff (5s, 15s, 45s)
    - Max 3 attempts (65s total)
    - After max → alert + require manual restart
    - On reconnect → validate subscriptions + reconcile

Q4_HEARTBEAT_FREQUENCY:
  status: RESOLVED
  answer: 30s (compromise) + SEMANTIC CHECKS + JITTER
  spec:
    - Frequency: 30s
    - Jitter: ±5s
    - Semantic checks: order flow, fill freshness, subscriptions
    - Miss threshold: 3 consecutive (90s max blind)

Q5_UX_MOCK_CSO_APPROACH:
  status: RESOLVED
  answer: Option C (scripted assist)
  implementation:
    - phoenix/mocks/mock_cse_generator.py
    - Claude generates params, G runs script
    - Script writes intent to file seam
```

---

## RISK REGISTER

```yaml
RISK_1_IB_GATEWAY_STABILITY:
  likelihood: MEDIUM
  impact: MEDIUM (paper only in Phase 1)
  mitigation:
    - Reconnection logic with backoff (max 3 attempts)
    - Alert on connection loss
    - Runbook RB-001, RB-007 for recovery
    - IBKR_SESSION beads for audit

RISK_2_PAPER_LIVE_CONFUSION:
  likelihood: LOW
  impact: HIGH (wrong account)
  mitigation:
    - Port separation (4002 vs 4001)
    - Account prefix validation (DU* vs U*)
    - Config validation at startup
    - Order submit guard on every order
    - INV-IBKR-PAPER-GUARD-1, INV-IBKR-ACCOUNT-CHECK-1

RISK_3_UX_FRICTION:
  likelihood: MEDIUM
  impact: LOW (fixable)
  mitigation:
    - G tests before Olya
    - mock_cse_generator.py reduces friction
    - Document friction points
    - Iterate on approval flow

RISK_4_RUNBOOK_INCOMPLETENESS:
  likelihood: MEDIUM
  impact: MEDIUM
  mitigation:
    - 8 runbooks covering all CRITICAL scenarios
    - Drill at least one (RB-004)
    - Update based on drill learnings

RISK_5_SEMANTIC_BLIND_SPOT:
  likelihood: MEDIUM
  impact: MEDIUM
  mitigation:
    - Semantic health checks in heartbeat
    - Order flow, fill freshness, subscription health
    - DEGRADED state detection
```

---

## OPUS FRESH EYES ENHANCEMENTS

```yaml
OPUS_ADDITIONS:

  1_IBKR_MODE_ENUM:
    observation: Current connector has use_mock bool, need tri-state
    enhancement: |
      Add IBKRMode enum: MOCK, PAPER, LIVE
      Replace use_mock: bool with mode: IBKRMode
      Default to MOCK for safety

  2_SESSION_BEAD_INTEGRATION:
    observation: Need to wire session bead emission to BeadStore
    enhancement: |
      connector.py gains emit_bead callback
      Session events automatically logged
      Athena can query: "Show connection gaps last N days"

  3_RECONNECT_STATE_MACHINE:
    observation: Reconnect needs formal state tracking
    enhancement: |
      ReconnectState enum: CONNECTED, RECONNECTING, ESCALATED
      Track attempts, last_attempt_time
      Clean state on successful connect

  4_HEARTBEAT_BEAD_EMISSION:
    observation: Every heartbeat should emit bead for audit
    enhancement: |
      heartbeat.py gains emit_bead callback
      HEALTHY beads at 30s intervals
      DEGRADED/MISSED beads with details
      Athena can query: "Show health gaps last N hours"

  5_GUARD_VALIDATION_ORDER:
    observation: Current order submit only checks token
    enhancement: |
      Add account guard before token validation
      Sequence: account_guard → port_guard → token_guard → submit
      Reject fast on mismatch

  6_MOCK_CSE_SCHEMA_VALIDATION:
    observation: Generator should validate output
    enhancement: |
      mock_cse_generator.py validates against CSE schema
      Rejects invalid combinations
      Outputs valid intent YAML only

INTEGRATION_POINTS:
  from_s32:
    - T2 workflow (unchanged)
    - Position lifecycle (unchanged)
    - Reconciliation (unchanged)
    - Promotion (add Phase 2 revalidation)

  new_in_s33:
    - IBKR_SESSION beads → BeadStore
    - HEARTBEAT beads → BeadStore
    - Real client → Connector
    - Semantic health → Heartbeat
    - mock_cse_generator → UX testing
```

---

## PARALLEL EXECUTION PLAN

```yaml
OPUS_TRACK:
  builds:
    - Track A: Real IBKR connection with guards
    - Track B: Monitoring with semantic health
    - Track C: 8 Runbooks
    - Track D: Telegram validation
    - Track E: Mock CSE generator
    - Track G: BUNNY Phase 1 (15 vectors)
  duration: 1-2 sessions

G_TRACK:
  executes:
    - Track F: UX testing with Claude Desktop
  method:
    1. Configure Claude Desktop with Phoenix file seam
    2. Test EXPLORE mode (pure conversation)
    3. Test mock signal generation via mock_cse_generator.py
    4. Test T2 approval flow (paper)
    5. Document friction points
  deliverable: UX_VALIDATION_LOG.md

CONVERGENCE:
  when: Both tracks complete
  action: Paper trade round-trip with G as operator
  validation: |
    - Full lifecycle, all beads
    - Minimum 3 trades, 2 sessions
    - 1 disconnect drill
    - 1 runbook drill (RB-004)
    - Smooth UX
```

---

```yaml
BUILD_MAP_STATUS: FINAL_v0.2
BLOCKERS: 0 (all 3 addressed)
INVARIANTS: 12 total
CHAOS_VECTORS: 15
RUNBOOKS: 8
TRACKS: 7

READY_FOR: OPUS EXECUTION

CTO_NOTE: |
  Both advisors aligned on "boring is safe" posture.
  Phase 1 is ops validation, not feature building.
  Real capital demands deliberate tempo.

  Key additions from v0.1:
  - Ironclad paper-first guards (INV-IBKR-PAPER-GUARD-1, INV-IBKR-ACCOUNT-CHECK-1)
  - Semantic health monitoring (INV-OPS-HEARTBEAT-SEMANTIC-1)
  - Phase 2 revalidation on any change (INV-PHASE2-REVALIDATE-1)
  - 15 chaos vectors (up from 7)
  - 8 runbooks (up from 6)
  - mock_cse_generator.py for UX testing

  S33 unlocks First Blood.
  Human sovereignty preserved.
  Boring is safe. Safe is fast.
```
