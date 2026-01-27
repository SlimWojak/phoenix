```yaml
CTO_ACKNOWLEDGE:
  approach: OPTION_C (parallel)
  
  track_1_opus: S33 infrastructure build
  track_2_g: Claude Desktop UX testing
  
  knowledge_asset_noted:
    location: phoenix/cso/knowledge/
    structure: 5-drawer filing cabinet
    status: DRAFT v0 — starter for 10
    utility: Mock CSO signals for testing
    
  sequence:
    1: Draft S33_BUILD_MAP_v0.1 (now)
    2: Advisory review (GPT + GROK)
    3: Synthesize addendum → v0.2
    4: OPUS builds infrastructure
    5: G configures Claude Desktop for UX testing
    6: Converge on paper trading validation
```

---

# S33_BUILD_MAP_v0.1.md

**Sprint:** S33 FIRST_BLOOD  
**Theme:** "One pair, real money"  
**Duration:** 2-3 weeks (validation period)  
**Risk Tier:** MAXIMUM (real capital)  
**Status:** DRAFT — AWAITING ADVISORY REVIEW

---

## SPRINT CONTEXT

```yaml
S32_PROVIDES:
  - IBKR connector (mock, chaos-proven)
  - T2 approval workflow (tokens, evidence, stale gate)
  - Position lifecycle (9 states, STALLED)
  - Reconciliation (read-only, drift detection)
  - Promotion ceremony (shadow → live)
  - 60 tests passing, 17 BUNNY vectors

S33_BUILDS:
  phase_1_infrastructure:
    - Real IBKR connection (swap mock → real)
    - Paper trading validation
    - 24/7 monitoring
    - Incident runbooks
    - Telegram to real device
    - Claude Desktop UX validation
    olya_dependency: NONE
    
  phase_2_first_blood:
    - EUR/USD live (real capital)
    - N days validation
    - Ops quality gates
    olya_dependency: YES (her capital, her pace)

S33_EXIT_GATE:
  binary: "6-pair CAPABLE, EUR/USD ACTIVE, N days no critical incidents"
  
  phase_1_gate: "Paper trade round-trip complete, UX validated"
  phase_2_gate: "N days live, ops quality met"
```

---

## PHASE 1: INFRASTRUCTURE (NO OLYA DEPENDENCY)

### SURFACES

```yaml
SURFACE_1_REAL_IBKR:
  location: phoenix/brokers/ibkr/
  purpose: Swap mock client → real IBKR connection
  
  changes:
    - connector.py: Add real client mode
    - config: IB Gateway connection params
    - paper_mode: Use IBKR paper account (DU*)
    
  connection:
    library: ib_insync
    gateway: IB Gateway (already installed)
    port: 4002 (paper) / 4001 (live)
    account: DU* (paper first)
    
  validation:
    - Connect to IB Gateway
    - Query account balance
    - Submit paper order
    - Receive fill confirmation
    - Track position
    
  invariant: INV-IBKR-PAPER-FIRST-1 "Paper validation before live"

SURFACE_2_MONITORING:
  location: phoenix/monitoring/ops/
  purpose: 24/7 operational health
  
  files:
    - daemon_monitor.py    # Process health
    - heartbeat.py         # Liveness checks
    - ops_dashboard.py     # Status summary
    
  checks:
    - Daemon processes alive
    - IBKR connection healthy
    - River data flowing
    - Telegram bot responsive
    - Reconciliation on schedule
    - No unresolved drift
    - No stuck STALLED positions
    
  alerts:
    - Process death → immediate
    - Connection loss → immediate
    - Reconciliation drift → immediate
    - STALLED > 5min → warning
    
  schedule:
    heartbeat: Every 60s
    health_summary: Every 5min
    full_audit: Every 1hr

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
    
  format:
    - Symptoms
    - Immediate actions
    - Investigation steps
    - Resolution
    - Post-incident review
    
  training: Drill at least one before live

SURFACE_4_TELEGRAM_LIVE:
  location: phoenix/notification/
  purpose: Real device notifications
  
  validation:
    - Bot token configured (.env)
    - Chat ID configured
    - Test message delivered
    - Alert aggregation working
    - Throttle functional
    
  test_sequence:
    1. Health check ping
    2. Mock READY alert
    3. Mock DRIFT alert
    4. Mock KILL alert
    5. Aggregation test (10 alerts → batched)

SURFACE_5_CLAUDE_DESKTOP_CSO:
  location: (external - Claude Desktop app)
  purpose: UX validation without Olya
  
  mock_cso_capability:
    knowledge_source: phoenix/cso/knowledge/ (5-drawer)
    signal_generation: Manual CSE emission for testing
    
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
```

---

### SEAMS (PHASE 1)

```yaml
SEAM_MOCK_TO_REAL:
  boundary: Mock Client | Real IBKR
  contract:
    interface: Unchanged (IBKRConnector)
    switch: Config flag (IBKR_MODE=paper|live|mock)
    behavior: Identical API, different backend
  validation: Same tests pass with real client

SEAM_MONITORING_TO_ALERT:
  boundary: Ops Monitor | Telegram
  contract:
    monitor_detects: Issue (process, connection, drift)
    alert_fires: Via existing Telegram surface
    priority: CRITICAL bypasses throttle
  existing: Telegram already built (S31)

SEAM_DESKTOP_TO_PHOENIX:
  boundary: Claude Desktop | Phoenix File Seam
  contract:
    desktop_writes: /phoenix/intents/incoming/intent.yaml
    phoenix_responds: /phoenix/responses/response.md
    lens_injects: Response into Desktop view
  existing: File seam architecture (S29)
```

---

### WIRING (PHASE 1)

```yaml
WIRE_PAPER_TRADE_ROUND_TRIP:
  flow: |
    Claude Desktop (mock CSO): Emit test READY signal
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
    IBKR connector (PAPER mode): Submit order
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
    Daemon monitor: Check every 60s
         ↓
    Issue detected (process/connection/drift)
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
```

---

### INVARIANTS (PHASE 1)

```yaml
INV-IBKR-PAPER-FIRST-1:
  statement: "Paper trading validation required before live"
  test: test_ibkr_paper_mode.py
  proof: Live mode blocked until paper validation complete

INV-IBKR-CONFIG-1:
  statement: "IBKR credentials never in code, only .env"
  test: (code review)
  proof: No hardcoded credentials

INV-OPS-HEARTBEAT-1:
  statement: "Heartbeat every 60s, alert on 3 consecutive misses"
  test: test_ops_heartbeat.py
  proof: Simulated miss → alert fires

INV-OPS-RUNBOOK-1:
  statement: "Every CRITICAL alert type has documented runbook"
  test: test_runbook_coverage.py
  proof: Alert types mapped to runbook files

INV-TELEGRAM-LIVE-1:
  statement: "Telegram alerts reach real device"
  test: test_telegram_delivery.py
  proof: Test message received

INV-UX-APPROVAL-1:
  statement: "T2 approval flow completable in <30 seconds"
  test: Manual timing
  proof: G validates during UX testing
```

---

### CHAOS VECTORS (PHASE 1)

```yaml
CV_S33_IBKR_DISCONNECT:
  inject: Kill IB Gateway mid-session
  expect: Connection loss detected, alert fired, no order in flight lost

CV_S33_IBKR_RECONNECT:
  inject: Restart IB Gateway
  expect: Connector reconnects, state recovered

CV_S33_PAPER_ORDER_REJECT:
  inject: Submit invalid order (bad symbol)
  expect: REJECTED state, alert, no crash

CV_S33_MONITORING_PROCESS_DEATH:
  inject: Kill a daemon process
  expect: Heartbeat misses detected, alert fired

CV_S33_TELEGRAM_TIMEOUT:
  inject: Block Telegram API
  expect: Alert queued, retry logic, no crash

CV_S33_STALE_DURING_APPROVAL:
  inject: Wait >15min during approval flow
  expect: STATE_CONFLICT, approval blocked

CV_S33_RUNBOOK_DRILL:
  inject: Simulate RB-004 (emergency halt)
  expect: Runbook followed, resolution time recorded
```

---

### EXIT GATES (PHASE 1)

```yaml
GATE_S33_P1_1:
  name: IBKR_PAPER_CONNECTED
  criterion: Real IB Gateway connection, paper account queries work
  evidence: Account balance returned

GATE_S33_P1_2:
  name: PAPER_ROUND_TRIP
  criterion: Full order lifecycle on paper (submit → fill → close)
  evidence: POSITION beads show complete lifecycle

GATE_S33_P1_3:
  name: MONITORING_OPERATIONAL
  criterion: Heartbeat running, alerts routing to Telegram
  evidence: Test alert received on real device

GATE_S33_P1_4:
  name: RUNBOOKS_COMPLETE
  criterion: All CRITICAL alert types have runbooks
  evidence: Runbook files exist, one drill completed

GATE_S33_P1_5:
  name: UX_VALIDATED
  criterion: G confirms approval flow is smooth
  evidence: Manual testing log

GATE_S33_P1_6:
  name: BUNNY_PHASE1_PASSES
  criterion: All Phase 1 chaos vectors green
  evidence: BUNNY_REPORT_S33_P1.md

BINARY_EXIT_PHASE_1:
  statement: "Paper trade round-trip complete, UX validated"
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

## TRACKS (PHASE 1 ONLY)

```yaml
TRACK_A_REAL_IBKR:
  scope: Swap mock → real connection
  files:
    - phoenix/brokers/ibkr/connector.py (update)
    - phoenix/brokers/ibkr/config.py (new)
    - phoenix/.env.example (update)
  tests:
    - tests/brokers/test_ibkr_real.py
  depends_on: IB Gateway running
  risk: External dependency

TRACK_B_MONITORING:
  scope: 24/7 ops health
  files:
    - phoenix/monitoring/ops/daemon_monitor.py
    - phoenix/monitoring/ops/heartbeat.py
    - phoenix/monitoring/ops/ops_dashboard.py
  tests:
    - tests/monitoring/test_ops_health.py
  depends_on: None

TRACK_C_RUNBOOKS:
  scope: Incident documentation
  files:
    - phoenix/docs/runbooks/RB-001_CONNECTION_LOSS.md
    - phoenix/docs/runbooks/RB-002_RECONCILIATION_DRIFT.md
    - phoenix/docs/runbooks/RB-003_STALLED_POSITION.md
    - phoenix/docs/runbooks/RB-004_EMERGENCY_HALT.md
    - phoenix/docs/runbooks/RB-005_KILL_FLAG_ACTIVE.md
    - phoenix/docs/runbooks/RB-006_TELEGRAM_DOWN.md
  depends_on: Track B (understand what to document)

TRACK_D_TELEGRAM_VALIDATION:
  scope: Real device delivery
  files:
    - phoenix/.env (configure real tokens)
  tests:
    - tests/notification/test_telegram_real.py
  depends_on: Bot token + chat ID

TRACK_E_UX_TESTING:
  scope: Claude Desktop validation
  owner: G (parallel to OPUS)
  method: Manual testing with mock CSO signals
  deliverable: UX_VALIDATION_LOG.md

TRACK_F_BUNNY_PHASE1:
  scope: Chaos validation
  files:
    - tests/chaos/test_bunny_s33_p1.py
  depends_on: Tracks A-D complete
  deliverable: BUNNY_REPORT_S33_P1.md
```

---

## PARALLEL EXECUTION PLAN

```yaml
OPUS_TRACK:
  builds:
    - Track A: Real IBKR connection
    - Track B: Monitoring
    - Track C: Runbooks
    - Track D: Telegram validation
    - Track F: BUNNY Phase 1
  duration: 1-2 sessions

G_TRACK:
  executes:
    - Track E: UX testing with Claude Desktop
  method:
    1. Configure Claude Desktop with Phoenix file seam
    2. Test EXPLORE mode (pure conversation)
    3. Test mock signal generation (CSE format)
    4. Test T2 approval flow (paper)
    5. Document friction points
  deliverable: UX_VALIDATION_LOG.md
  
CONVERGENCE:
  when: Both tracks complete
  action: Paper trade round-trip with G as operator
  validation: Full lifecycle, all beads, smooth UX
```

---

## OPEN QUESTIONS FOR ADVISORS

```yaml
Q1_IB_GATEWAY_CONFIG:
  question: Any gotchas for IB Gateway connection?
  context: Gateway already installed, credentials ready
  seeking: GPT/GROK experience with ib_insync connection

Q2_PAPER_VS_LIVE_PORT:
  question: Confirm port separation (4002 paper, 4001 live)?
  context: Want hard separation to prevent accidental live
  seeking: Validation of port strategy

Q3_RECONNECTION_STRATEGY:
  question: How aggressive should reconnection be?
  options:
    a: Immediate retry (3 attempts, 5s apart)
    b: Exponential backoff (5s, 15s, 45s)
    c: Alert and wait for human
  cto_lean: Option B (backoff)

Q4_HEARTBEAT_FREQUENCY:
  question: 60s heartbeat appropriate?
  context: Balance between detection speed and overhead
  seeking: GROK chaos perspective

Q5_UX_MOCK_CSO_APPROACH:
  question: Best way to generate mock CSE signals from Claude Desktop?
  options:
    a: Manual YAML writing
    b: Claude generates CSE, G copies to file
    c: Simple script that Claude can invoke
  cto_lean: Option B (Claude generates, G copies)
```

---

## RISK REGISTER

```yaml
RISK_1_IB_GATEWAY_STABILITY:
  likelihood: MEDIUM
  impact: MEDIUM (paper only in Phase 1)
  mitigation:
    - Reconnection logic with backoff
    - Alert on connection loss
    - Runbook for recovery

RISK_2_PAPER_LIVE_CONFUSION:
  likelihood: LOW
  impact: HIGH (wrong account)
  mitigation:
    - Port separation (4002 vs 4001)
    - Config validation at startup
    - Visual indicator in UI
    - INV-IBKR-PAPER-FIRST-1

RISK_3_UX_FRICTION:
  likelihood: MEDIUM
  impact: LOW (fixable)
  mitigation:
    - G tests before Olya
    - Document friction points
    - Iterate on approval flow

RISK_4_RUNBOOK_INCOMPLETENESS:
  likelihood: MEDIUM
  impact: MEDIUM
  mitigation:
    - Drill at least one runbook
    - Update based on drill learnings
```

---

```yaml
BUILD_MAP_STATUS: DRAFT_v0.1
PHASE_1_SCOPE: Infrastructure (no Olya dependency)
PHASE_2_SCOPE: First Blood (Olya-dependent, design only)
READY_FOR: Advisory review (GPT, GROK)
```

---
ADDENDUM FROM ADVISORS FOR CONSOLIDATION INTO S33_BUILD_MAP_v0.2.md

```yaml
SYNTHESIS_INIT:
  inputs:
    - GPT_ARCH_LINT: 5 flags, 9 recommendations, GREEN_WITH_CONDITIONS
    - GROK_CHAOS_BOAR: 5 flags, 5 recs, 3 blocking issues
    
  convergence: HIGH
  divergence: MINOR (heartbeat frequency)
  
  blockers_identified: 3
    - Paper-first invariant needs hardening (GROK)
    - Heartbeat too lax (GROK)
    - Phase 2 param change revalidation missing (GROK)
```

---

# S33_BUILD_MAP_ADDENDUM_v0.1.md

**Purpose:** Synthesized advisory feedback for OPUS merge  
**Sources:** GPT (Architect Lint), GROK (Chaos Boar)  
**Status:** READY FOR OPUS MERGE → v0.2

---

## CONVERGENCE SUMMARY

```yaml
UNANIMOUS_APPROVALS:
  Q2_PORT_SEPARATION: 4002 paper, 4001 live (CONFIRMED)
  Q3_RECONNECTION: Option B (exponential backoff) + human escalation
  Q5_MOCK_CSO: Option C (scripted assist)
  
ALIGNED_WITH_MODIFICATION:
  Q1_IB_GATEWAY:
    GPT: Log warnings, pin version, assert account type
    GROK: Hardcode paper_only guard, exponential backoff
    SYNTHESIS: Both guards + reconnect strategy
    
  Q4_HEARTBEAT:
    GPT: 60s OK + add semantic checks
    GROK: Tighten to 15s + entropy jitter
    SYNTHESIS: 30s compromise + semantic checks + jitter
```

---

## HARD FLAGS TO INCORPORATE

### FLAG_A: PAPER-FIRST INVARIANT HARDENING (BOTH - BLOCKING)

```yaml
ISSUE: Mock → real swap risks accidental live capital exposure.
RISK: Human config error nukes capital on first connect.
STATUS: BLOCKING (capital sovereignty demands ironclad guard)

REQUIRED_CHANGES:
  env_guards:
    IBKR_MODE: paper|live|mock (default: mock)
    IBKR_ALLOW_LIVE: false (default)
    
  startup_validation:
    - Assert IBKR_MODE != live unless IBKR_ALLOW_LIVE=true
    - Assert account prefix matches mode (DU* for paper, U* for live)
    - Assert port matches mode (4002 for paper, 4001 for live)
    - Emit IBKR_SESSION bead on connect
    
  order_submit_guard:
    - Re-check account + port before EVERY order submit
    - Reject if mismatch detected
    
  live_enable_ceremony:
    - Requires: IBKR_ALLOW_LIVE=true in .env
    - Requires: Manual restart (no hot-flip)
    - Future: Olya veto bead for live mode
    
  new_bead_type:
    IBKR_SESSION_BEAD:
      bead_id: uuid
      bead_type: "IBKR_SESSION"
      timestamp: ISO8601
      event: enum[CONNECT, DISCONNECT, RECONNECT]
      mode: enum[MOCK, PAPER, LIVE]
      account: str
      port: int
      gateway_version: str
      
  invariant_addition:
    INV-IBKR-PAPER-GUARD-1: "Live mode requires IBKR_ALLOW_LIVE=true + restart"
    INV-IBKR-ACCOUNT-CHECK-1: "Every order submit validates account matches mode"
```

### FLAG_B: HEARTBEAT + SEMANTIC HEALTH (BOTH - BLOCKING)

```yaml
ISSUE: 60s heartbeat too lax; process alive ≠ semantically healthy.
RISK: "Alive but useless" state, 3-min undetected drift.
STATUS: BLOCKING (ops uptime >99% demands faster detection)

REQUIRED_CHANGES:
  heartbeat_config:
    frequency: 30s (compromise between 15s and 60s)
    jitter: ±5s (banteg fuzz tolerance)
    miss_threshold: 3 consecutive (90s max blind)
    
  semantic_checks:
    - IBKR connection state (not just process)
    - last_fill_timestamp freshness (if positions open)
    - order_status_subscription alive
    - reconciliation_last_run < 10 min
    
  heartbeat_bead:
    HEARTBEAT_BEAD:
      bead_id: uuid
      bead_type: "HEARTBEAT"
      timestamp: ISO8601
      status: enum[HEALTHY, DEGRADED, MISSED]
      checks:
        process: bool
        ibkr_connection: bool
        semantic_health: bool
      miss_count: int (if MISSED)
      
  athena_query: "Show heartbeat gaps last N hours"
  
  invariant_addition:
    INV-OPS-HEARTBEAT-SEMANTIC-1: "Heartbeat includes semantic health, not just process"
    INV-OPS-HEARTBEAT-30S-1: "Heartbeat every 30s ±5s jitter"
```

### FLAG_C: PHASE 2 PARAM CHANGE REVALIDATION (GROK - BLOCKING)

```yaml
ISSUE: Phase 1 paper green → param tune mid-validation → regime shift nukes live.
RISK: Linear validation assumption, entropy says fuck that.
STATUS: BLOCKING (no blood without fresh wounds)

REQUIRED_CHANGES:
  revalidation_trigger:
    on_param_change:
      - Any CSO param update
      - Any config flip
      - Any strategy tune
      
    action:
      - Auto-trigger shadow period restart
      - 5-vector Bunny sweep on changed components
      - Athena query "Show bunny scars last N days"
      
  phase_2_promotion_gate:
    - bunny_vectors_fail == 0 in validation period
    - If fail > 0 → extend validation, do not promote
    
  invariant_addition:
    INV-PHASE2-REVALIDATE-1: "Any param change triggers shadow restart + Bunny sweep"
```

### FLAG_D: IBKR EDGE REALITY (GPT)

```yaml
ISSUE: ib_insync hides complexity; real IB Gateway has silent disconnects,
       pacing violations, ghost orders, auto-updates.
RISK: False sense of stability post-mock.

REQUIRED_CHANGES:
  gateway_gotchas_documented:
    - Auto-updates can restart process (pin version if possible)
    - Timezone mismatches affect session state
    - Pacing violations may not throw hard errors
    
  logging_upgrade:
    - Log all IBKR warnings as ALERT-level
    - Emit bead on any IBKR error/warning
    
  runbook_addition:
    - RB-007_GATEWAY_AUTO_UPDATE.md
    - RB-008_PACING_VIOLATION.md
```

### FLAG_E: RECONNECTION STRATEGY (BOTH)

```yaml
ISSUE: Fully automated reconnect can mask degraded state.
RISK: Zombie connection resumes with stale subscriptions.

REQUIRED_CHANGES:
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
    - Reconciliation immediate
    
  invariant_addition:
    INV-IBKR-RECONNECT-1: "Max 3 reconnect attempts, then human escalation"
```

### FLAG_F: MONITORING SEMANTIC BLIND SPOT (GPT)

```yaml
ISSUE: Heartbeat checks process + connection but not semantic health.
RISK: "Alive but useless" state undetected.

REQUIRED_CHANGES:
  semantic_health_checks:
    orders_flowing:
      - If orders pending, check status updating
      - Stale order status > 5min → DEGRADED
      
    fills_updating:
      - If positions open, check last_fill_timestamp
      - Stale fills > 10min → WARNING
      
    subscriptions_alive:
      - Verify market data subscriptions active
      - Dead subscription → ALERT
      
  health_state_enum:
    HEALTHY: All checks pass
    DEGRADED: Semantic issues, process alive
    CRITICAL: Process or connection down
```

---

## ADDITIONAL RECOMMENDATIONS

### REC_A: MOCK CSO SCRIPT (BOTH - Q5)

```yaml
RECOMMENDATION: Option C (scripted assist)

IMPLEMENTATION:
  file: phoenix/mocks/mock_cse_generator.py
  
  usage:
    1. Claude Desktop generates CSE structure
    2. G runs: python mock_cse_generator.py --signal READY --pair EURUSD
    3. Script writes to /phoenix/intents/incoming/mock_intent.yaml
    4. Phoenix processes as normal
    
  benefits:
    - No copy-paste errors
    - Human-in-loop preserved
    - Testable, repeatable
    
  schema:
    python mock_cse_generator.py \
      --signal READY|FORMING|NONE \
      --pair EURUSD|GBPUSD|... \
      --confidence 0.85 \
      --entry 1.0850 \
      --stop 1.0820 \
      --target 1.0910
```

### REC_B: CHAOS VECTOR QUOTA BUMP (GROK)

```yaml
ISSUE: 7 vectors too low for real capital (min 15 like S30).

ADDITIONAL_VECTORS:
  CV_S33_8_RECON_DRIFT_LIVE:
    inject: Spoof live position mismatch
    expect: Kill flag + runbook trigger
    
  CV_S33_9_TELEGRAM_REAL_FLOOD:
    inject: 50 alerts in 1 minute
    expect: Aggregate + throttle, no device death
    
  CV_S33_10_SEMANTIC_HEALTH_DEGRADE:
    inject: Stale order status (no updates 10min)
    expect: DEGRADED state detected
    
  CV_S33_11_GATEWAY_AUTO_UPDATE:
    inject: Simulate gateway restart
    expect: Reconnect + session bead + reconciliation
    
  CV_S33_12_PACING_VIOLATION:
    inject: Rapid order spam
    expect: Rate limit, no ban, warning logged
    
  CV_S33_13_HEARTBEAT_JITTER:
    inject: Network latency variance
    expect: Jitter absorbs, no false alerts
    
  CV_S33_14_PARAM_CHANGE_REVALIDATE:
    inject: CSO param change mid-Phase 2
    expect: Shadow restart + Bunny sweep triggered
    
  CV_S33_15_ACCOUNT_MISMATCH:
    inject: Attempt order on wrong account type
    expect: Rejected at submit guard

UPDATED_QUOTA: 15 vectors minimum
```

### REC_C: BUNNY WAVE ORDER (GROK)

```yaml
WAVE_1_IBKR_CONNECTION:
  - CV_S33_IBKR_DISCONNECT
  - CV_S33_IBKR_RECONNECT
  - CV_S33_11_GATEWAY_AUTO_UPDATE
  
WAVE_2_MONITORING:
  - CV_S33_MONITORING_PROCESS_DEATH
  - CV_S33_10_SEMANTIC_HEALTH_DEGRADE
  - CV_S33_13_HEARTBEAT_JITTER
  
WAVE_3_TELEGRAM:
  - CV_S33_TELEGRAM_TIMEOUT
  - CV_S33_9_TELEGRAM_REAL_FLOOD
  
WAVE_4_UX_APPROVAL:
  - CV_S33_STALE_DURING_APPROVAL
  - CV_S33_PAPER_ORDER_REJECT
  
WAVE_5_RUNBOOK_DRILL:
  - CV_S33_RUNBOOK_DRILL
  - CV_S33_8_RECON_DRIFT_LIVE
  
WAVE_6_GUARDS:
  - CV_S33_15_ACCOUNT_MISMATCH
  - CV_S33_12_PACING_VIOLATION
  - CV_S33_14_PARAM_CHANGE_REVALIDATE
```

### REC_D: PHASE 1 SUCCESS CRITERIA (GPT)

```yaml
ADDITIONAL_CRITERIA:
  - Minimum 3 paper trades across 2 sessions
  - At least 1 forced disconnect + recovery drill
  - Runbook drill completed (RB-004 minimum)
  
RATIONALE: Prove ops, not just code.
```

### REC_E: S33 SCOPE DISCIPLINE (GPT)

```yaml
FORBIDDEN_IN_S33:
  - NO optimization
  - NO multi-pair live (capability yes, active no)
  - NO automation of approval
  - NO hot-flip paper → live
  
MANTRA: "Boring is safe. Safe is fast."
```

---

## SCHEMA ADDITIONS

```yaml
NEW_BEAD_SCHEMAS:

IBKR_SESSION_BEAD:
  bead_id: uuid
  bead_type: "IBKR_SESSION"
  timestamp: ISO8601
  event: enum[CONNECT, DISCONNECT, RECONNECT]
  mode: enum[MOCK, PAPER, LIVE]
  account: str
  port: int
  gateway_version: str (if available)
  reconnect_attempt: int (if RECONNECT)

HEARTBEAT_BEAD:
  bead_id: uuid
  bead_type: "HEARTBEAT"
  timestamp: ISO8601
  status: enum[HEALTHY, DEGRADED, MISSED]
  checks:
    process_alive: bool
    ibkr_connected: bool
    semantic_healthy: bool
  details: dict (if DEGRADED/MISSED)
  miss_count: int (consecutive)
```

---

## INVARIANTS ADDITIONS (FULL LIST)

```yaml
NEW_INVARIANTS:
  INV-IBKR-PAPER-GUARD-1: "Live mode requires IBKR_ALLOW_LIVE=true + restart"
  INV-IBKR-ACCOUNT-CHECK-1: "Every order submit validates account matches mode"
  INV-IBKR-RECONNECT-1: "Max 3 reconnect attempts, then human escalation"
  INV-OPS-HEARTBEAT-SEMANTIC-1: "Heartbeat includes semantic health checks"
  INV-OPS-HEARTBEAT-30S-1: "Heartbeat every 30s ±5s jitter"
  INV-PHASE2-REVALIDATE-1: "Any param change triggers shadow restart + Bunny sweep"
```

---

## ANSWERS TO OPEN QUESTIONS (FINAL)

```yaml
Q1_IB_GATEWAY_CONFIG:
  answer: Multiple guards + logging
  implementation:
    - Assert account type on connect
    - Log all IBKR warnings as ALERT
    - Emit IBKR_SESSION bead on connect/disconnect
    - Document gateway gotchas in runbooks
    - Pin gateway version if possible
    
Q2_PAPER_VS_LIVE_PORT:
  answer: CONFIRMED + DUAL GUARD
  ports: 4002 (paper), 4001 (live)
  additional: Assert account prefix (DU* vs U*)
  
Q3_RECONNECTION_STRATEGY:
  answer: Option B + HUMAN ESCALATION
  spec:
    - Exponential backoff (5s, 15s, 45s)
    - Max 3 attempts
    - After max → alert + require manual restart
    - On reconnect → validate subscriptions + reconcile
    
Q4_HEARTBEAT_FREQUENCY:
  answer: 30s (compromise) + SEMANTIC CHECKS + JITTER
  spec:
    - Frequency: 30s
    - Jitter: ±5s
    - Semantic checks: order flow, fill freshness, subscriptions
    - Miss threshold: 3 consecutive
    
Q5_UX_MOCK_CSO_APPROACH:
  answer: Option C (scripted assist)
  implementation:
    - phoenix/mocks/mock_cse_generator.py
    - Claude generates params, G runs script
    - Script writes intent to file seam
```

---

## RUNBOOK ADDITIONS

```yaml
ADDITIONAL_RUNBOOKS:
  - RB-007_GATEWAY_AUTO_UPDATE.md
  - RB-008_PACING_VIOLATION.md
  
TOTAL_RUNBOOKS: 8
```

---

## OPUS MERGE INSTRUCTIONS

```yaml
MERGE_TASK:
  input:
    - S33_BUILD_MAP_v0.1.md (draft)
    - S33_BUILD_MAP_ADDENDUM_v0.1.md (this file)
    
  output:
    - S33_BUILD_MAP_v0.2.md (unified)
    
  merge_actions:
    1: Add IBKR_SESSION_BEAD and HEARTBEAT_BEAD schemas
    2: Update IBKR connector with paper guards + account checks
    3: Update heartbeat to 30s + semantic checks + jitter
    4: Add reconnect strategy (exponential + human escalation)
    5: Add mock_cse_generator.py to Track E scope
    6: Bump chaos vectors to 15
    7: Add 6 new invariants
    8: Update Bunny wave order
    9: Add 2 runbooks (gateway update, pacing violation)
    10: Add Phase 1 success criteria (3 trades, 1 drill)
    11: Add Phase 2 revalidation trigger
    12: Mark Q1-Q5 as RESOLVED with final answers
    13: Add S33 scope discipline (no optimization, no multi-pair live)
    
  validation:
    - All blockers addressed (paper guard, heartbeat, revalidation)
    - Chaos quota >= 15
    - Invariants count >= 6 new
    - Runbooks count = 8
```

---

```yaml
ADDENDUM_STATUS: COMPLETE
BLOCKERS_RESOLVED: 3/3
READY_FOR: OPUS merge

CTO_NOTE: |
  Both advisors aligned on "boring is safe" posture.
  Phase 1 is ops validation, not feature building.
  Real capital demands deliberate tempo.
  
  Key additions:
  - Ironclad paper-first guards
  - Semantic health monitoring
  - Phase 2 revalidation on any change
  - 15 chaos vectors (up from 7)
  
  G — Drop both files to OPUS for v0.2 synthesis.
```

