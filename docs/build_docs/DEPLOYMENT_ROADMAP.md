# ═══════════════════════════════════════════════════════════════════════════════
# DEPLOYMENT_ROADMAP.md
# a8ra — Road to Paper Trading (Canonical Build Plan)
# ═══════════════════════════════════════════════════════════════════════════════

```yaml
document: DEPLOYMENT_ROADMAP
version: 1.1
date: 2026-03-22
status: CANONICAL — synthesized from RP audit + 3 advisors + 2 deep dives + advisor addendum
author: CTO (synthesized), G (sovereign approval)
audience: CTO, Opus (builder), all advisors
supersedes: S66 framing in UNIFIED_ROADMAP, ROAD_TO_DEPLOYMENT.md (Sunday plan)
methodology: SYNTHETIC_OLYA_METHOD_vLOCK.yaml (unchanged)
principle: "No shortcuts. No parallel eval paths. Every strategy through constitutional governance."

inputs:
  - SYSTEM_ARCHITECTURE_AUDIT_v1.md (RepoPrompt, 729 lines, 216 files scanned)
  - GPT Architect Lint response (10 flags, gate unification strategy)
  - OWL Structural Audit response (5 verdicts, signal friction insight)
  - BOAR Chaos Audit response (5 vectors, ghost bar divergence, shadow escape)
  - GPT prior session: Signal Escalation Ladder (3 ontological layers)
  - Deep Dive 1: Gate Wiring Table (0 wired, 2 partial, 6 missing)
  - Deep Dive 2: Signal Adapter Data Requirements (10-step sequence)
  - v1.1 Addendum: BOAR (3 items), OWL (3 items), GPT (1 invariant)
```

---

## CURRENT STATE (as of 2026-03-22 evening)

```yaml
WHAT_SHIPPED_TODAY:
  S66_track_a: "state snapshots + direction guard + KZ gate v2 (6/8 regression)"
  S66_track_c: "Dream Cycle v1 — rejection mining + morning briefing"
  S66_track_d: "Channels proven on M3 (@a8ra_COO_bot operational)"
  mirror: "SHIPPED overnight — Olya's live observation surface"
  vlock: "kill_zone_gate_v2 amendment (Olya confirmed)"
  pipeline: "4 days exported, 15 DIAGNOSTIC_SIGNALs, intraday snapshots"
  commits: "f01ee8b (Track A) + b7bef38 (Track C)"
  tests: "1088 passed, 0 failures"

WHAT_EXISTS_AND_WORKS:
  river: "IBKR streaming, staging JSONL, parquet, heartbeat"
  halt: "constitutional, multi-layer, chaos-tested (<50ms local)"
  dexter_pipeline: "River → producers → state → checklist → DIAGNOSTIC_SIGNAL"
  mirror: "live-capable dashboard on localhost:8300"
  bridge: "governance notary (Phoenix→Dexter, 7 invariants)"
  position_lifecycle: "10-state FSM, tested"
  paper_broker: "immediate fills, P&L tracking"
  dream_cycle_v1: "morning briefing with false rejection mining"
  channels: "Telegram bot on M3, round-trip proven"

THREE_GAPS_BLOCKING_PAPER_TRADING:
  gap_1: "No production orchestrator chains enrichment→evaluation→execution"
  gap_2: "No TradeProposal → ExecutionIntent adapter"
  gap_3: "No Dexter signal → Phoenix execution path"

ADDITIONAL_ISSUES:
  blocking: "enrichment/__init__.py crashes on import (B1)"
  structural: "3 disjoint gate namespaces (cartridge/evaluator/conditions)"
  architectural: "ARS bypasses 5-drawer CSO via parallel evaluator"
  operational: "shadow_mode hardcoded, no graduation mechanism"
```

---

## PHASE 0: FOUNDATIONS (1-2 days)

```yaml
name: "STOP_THE_BLEEDING"
rationale: "Fix everything broken before building anything new"
owner: Opus (Cursor, step-through)
```

### P0.1 — Fix Enrichment Import Crash

```yaml
what: "enrichment/__init__.py imports L2-L6 modules that don't exist → crashes on import"
severity: BLOCKING (B1 from audit)
advisor_refs: GPT F003, BOAR V5
action: "restore module tree or refactor __init__ to lazy imports"
exit_gate: |
  import phoenix.enrichment succeeds.
  L1→L7 enrichment chain callable on test data.
  Existing Phoenix tests still pass.
```

### P0.2 — Gate Registry (Namespace Unification)

```yaml
what: |
  Replace hardcoded evaluator gate switch table with GateRegistry
  that maps cartridge gate IDs → predicate functions.

  The evaluator becomes a GENERIC EXECUTOR:
  - loads gate IDs from cartridge YAML
  - looks up predicate function in GateRegistry
  - calls predicate with MarketState → bool
  - unrecognized gate ID → FAIL (not UNKNOWN_GATE)

pattern: GPT's GateRegistry concept
design_principle: |
  GateRegistry is the CONSTITUTIONAL TRUTH LAYER, not just a checker.
  Both Evaluator AND CartridgeLoader import from gate_registry.py.
  No other module defines or resolves gate IDs. (BOAR)

invariant: INV-GATE-NAMESPACE-SINGLETON (new)
  rule: "Cartridge gate IDs are the ONLY gate namespace"
  enforcement: "evaluator rejects any gate not registered in GateRegistry"

deep_dive_evidence: |
  Appendix A shows all 15 evaluator gates are orphans for ARS.
  All 8 cartridge gates have clear predicate logic already
  implemented in evaluate_asia_scalp_setup()'s guard chain.
  The registry extracts that logic into callable predicates.

action: |
  1. Create cso/gate_registry.py — maps gate_id → Callable[[MarketState], bool]
  2. Refactor evaluator.py to consume GateRegistry instead of switch table
  3. Deprecate generic gates from gate_schema.yaml (kept as reference only)
  4. conditions.yaml reduced to defaults/documentation, not runtime namespace

exit_gate: |
  GateRegistry loads ARS cartridge gates.
  Evaluator resolves all 8 ARS gate IDs to predicates.
  No UNKNOWN_GATE results.
  Existing evaluator tests adapted.
```

### P0.3 — MarketState Completion

```yaml
what: "Populate remaining MarketState fields needed by Drawers 4+5"
deep_dive_evidence: |
  Appendix A.1 shows 6/8 cartridge gates already have MarketState fields populated.
  Only 2 require addition:
  - rr_ratio: runtime computation (entry - SL) / (TP - entry)
  - session trade state: runtime SessionTracker (already exists in asia_scalp.py)

action: |
  1. Add rr_ratio computation to MarketState builder (post-strategy evaluation)
  2. Wire SessionTracker state into MarketState or gate predicate context
  Note: these are strategy-computed, not enrichment-derived.
  The predicate function receives both MarketState AND runtime context.

exit_gate: |
  Drawers 4+5 evaluate on real data (not None defaults).
  GATE_RR_VALID and GATE_SESSION_LIMIT resolve to pass/fail.
```

### P0.4 — Ghost Bar Canonical Policy

```yaml
what: "Document and enforce single ghost bar behavior across readers"
audit_finding: |
  Phoenix Reader injects ghosts (is_ghost=True, volume=0).
  Dexter adapter does not inject ghosts.
  RA flags volume==0 but doesn't inject.
  → bar count divergence for same time window.

invariant: INV-GHOST-CANON (new, from BOAR)
  rule: "For any time window, all River consumers agree on bar count and bar identity"
  enforcement: "adapter PIT-filter validates bar_hash parity"

action: |
  Document canonical policy: ghost injection ON or OFF?
  If ON: Dexter adapter must inject same ghosts.
  If OFF: Phoenix Reader ghost injection made optional/configurable.
  Minimum: adapter validates bar count alignment before price discovery.

exit_gate: |
  Policy documented. Both readers produce same bar count for test window.
  Or: adapter includes bar count validation with clear error on mismatch.
```

### P0.5 — Stale Code Cleanup

```yaml
what: "Remove misleading labels and dead references"
items:
  - B3: remove VI from runner.py execution order docstring
  - B4: remove VI from lineage.py contiguity check reference
  - M1: update execution_surface.yaml (MOCK_SIGNALS → current capability)
  - M3: remove confidence scalar from scanner.py (INV-CSO-NO-SCALAR-DECISIONS)
  - M5: fix position lifecycle state count (9 vs 10)
  - M8: add shadow_mode graduation TODO with ceremony reference

exit_gate: "no misleading labels remain in codebase"
```

---

## PHASE 1: ARS THROUGH CONSTITUTIONAL PATH (2-3 days)

```yaml
name: "FIRST_STRATEGY_CANONICAL"
rationale: |
  Asia Range Scalp flows through 5-drawer CSO with no parallel eval path.
  All strategy-specific logic lives in predicate functions registered in GateRegistry.
  Constitutional governance end-to-end: cartridge → lease → CSO → halt → execution.
owner: Opus (Cursor for P1.1-P1.2, Factory for P1.3)
prerequisite: Phase 0 complete
invariant: INV-NO-PARALLEL-EVAL-PATHS (new, from GPT)
  rule: "No strategy evaluator may bypass the 5-drawer CSO system"
  enforcement: "evaluate_asia_scalp_setup() refactored into GateRegistry predicates"
```

### P1.1 — ARS Strategy Predicate Pack

```yaml
what: |
  Refactor evaluate_asia_scalp_setup() guard chain into 8 predicate
  functions registered in GateRegistry for the ARS cartridge.

mapping_from_deep_dive: |
  GATE_ASIA_RANGE_VALID     → predicate: asia_range_valid(state) → state.asia_range_pips <= 30.0
  GATE_LIQUIDITY_SWEEP      → predicate: sweep_detected(state)   → state.recent_sweep and state.sweep_age_bars <= window
  GATE_SWEEP_EXTENSION_VALID→ predicate: extension_valid(state)  → 1.0 <= state.sweep_extension_pips <= 20.0
  GATE_LTF_PDA_ENGAGED      → predicate: re_acceptance(state)    → state.re_acceptance == True
  GATE_FVG_ACTIVE            → predicate: fvg_valid(state)       → fvg_present and state.fvg_untouched_pips >= 1.0
  GATE_CANDLE_C_INSIDE       → predicate: candle_inside(state)   → state.candle_c_inside_range == True
  GATE_RR_VALID              → predicate: rr_valid(state, ctx)   → ctx.rr_ratio >= cartridge.min_rr
  GATE_SESSION_LIMIT         → predicate: session_ok(state, ctx) → ctx.session_tracker.can_trade()

drawer_assignment: |
  Drawer 1 (HTF_BIAS):         GATE_ASIA_RANGE_VALID (ARS has no HTF bias requirement;
                                range validity is the L1 equivalent)
  Drawer 2 (MARKET_STRUCTURE):  GATE_LIQUIDITY_SWEEP + GATE_SWEEP_EXTENSION_VALID
  Drawer 3 (PREMIUM_DISCOUNT):  GATE_LTF_PDA_ENGAGED + GATE_CANDLE_C_INSIDE
  Drawer 4 (ENTRY_MODEL):       GATE_FVG_ACTIVE
  Drawer 5 (CONFIRMATION):      GATE_RR_VALID + GATE_SESSION_LIMIT

note: |
  evaluate_asia_scalp_setup() is NOT deleted — its logic is extracted into
  predicate functions. The function itself becomes a test oracle to verify
  the GateRegistry path produces identical verdicts.

exit_gate: |
  GateRegistry ARS predicates produce IDENTICAL verdicts to
  evaluate_asia_scalp_setup() on all 14 ground truth trades.
  evaluate_asia_scalp_setup() retained as regression oracle only.
  STRICT ASSERTION (OWL): if GateRegistry verdict != evaluate_asia_scalp_setup()
  oracle verdict for ANY of 14 ground truth trades → HALT build.
  No tolerance for silent divergence.
```

### P1.2 — TradeProposal → ExecutionIntent Adapter

```yaml
what: "Bridge the two execution vocabularies"
audit_ref: Section 4.5 field mapping table

adapter_spec: |
  TradeProposal fields → ExecutionIntent fields:
    direction (TradeDirection) → direction (Direction.LONG/SHORT)
    entry_price → entry_price
    stop_loss → stop_loss
    take_profit → take_profit
    position_size_lots → size
    (generated) → intent_id ("INT-{source}-{timestamp}-{counter}")
    (hardcoded) → intent_type (ENTRY)
    (hardcoded) → status (PENDING)
    (from context) → symbol
    (from MarketState) → source_state_hash (MarketState.compute_hash())
    (computed) → intent_hash (SHA256 of deterministic fields)

invariant: INV-CONTRACT-1
  rule: "Same signal + same MarketState → same intent_hash"
  enforcement: "deterministic hash computation, no timestamps in hash input"

action: "Create execution/intent_adapter.py — pure function, no side effects"

exit_gate: |
  TradeProposal converts to ExecutionIntent with full provenance.
  intent_hash is deterministic (same inputs → same hash).
  Round-trip test: known proposal → known intent → verify all fields.
```

### P1.3 — Production Orchestrator

```yaml
what: |
  daemons/strategy_orchestrator.py — watches River staging JSONL,
  chains the full constitutional path on each new bar.

flow: |
  1. PRE-FLIGHT HEARTBEAT (OWL):
     - IBKR gateway socket open? (127.0.0.1:4002)
     - River heartbeat healthy? (connected=true, subscribed=true)
     - Enrichment importable? (B1 must be fixed)
     - Halt state clear? (check_halt_signal())
     IF ANY FAIL → log, wait, retry

  2. WATCH: staging JSONL for new 1m bar (watchdog, same as MIRROR)

  3. ENRICH: load bars via RiverReader → L1→L7 enrichment chain

  4. BUILD STATE: build_market_state(df, pair, now)
     - INV-PIT-JOIN-ONLY enforced
     - INV-RIVER-FRESHNESS enforced
     - INV-RACE-BAR-SYNC: enrichment watermark ≥ current bar (BOAR)
     - HYDRATION BARRIER (BOAR): assert enrichment_watermark >= current_bar_time
       before ANY CSO evaluation call. Single line, prevents 90% of
       race + ghost conditions.

  5. EVALUATE: GateEvaluator with GateRegistry + ARS cartridge
     - 5-drawer evaluation → FiveDrawerResult
     - all drawers must pass (no optional hack)

  6. PROPOSE: if VALID → create TradeProposal from predicate outputs

  7. ADAPT: TradeProposal → ExecutionIntent via intent_adapter.py
     - INV-CONTRACT-1: deterministic hash

  8. GOVERN:
     - check_halt_signal() (INV-GOV-HALT-BEFORE-ACTION)
     - sovereign_gate check
     - shadow_mode check (INV-SHADOW-MODE-RESPECTED)
     - lease bounds check
     - IF shadow_mode=True → record ShadowObservation, STOP

  9. EXECUTE: (only if shadow_mode=False AND governance passes)
     - HaltGate.check_before()
     - broker_stub.submit_order(intent)
     - PaperPosition lifecycle begins

  10. RECORD:
      - CSE bead (provenance: River → enrichment → evaluation → intent)
      - IF rejected → PROPOSAL_REJECTED bead (Dream Cycle fuel)
      - WAG: bead durable BEFORE state change (OWL)

pre_flight_invariant: INV-PRE-FLIGHT-HEARTBEAT (new, from OWL)
  rule: "orchestrator halts if IBKR gateway, River, or enrichment unhealthy"
  enforcement: "pre-flight check before each bar processing cycle"

exit_gate: |
  Orchestrator processes historical bars (replay known ARS trade).
  Full chain: River → enrichment → MarketState → CSO → intent → paper broker.
  Pre-flight catches missing gateway.
  Shadow mode prevents execution (ShadowObservation recorded).
```

### P1.4 — ARS Paper Lease

```yaml
what: "Create paper trading lease for Asia Range Scalp"
bounds:
  per_trade_risk: "1% (from strategy spec)"
  max_trades_per_session: 1
  max_daily_trades: 1
  max_daily_loss: "1R (-1%)"
  shadow_mode: true (initial)
  duration: "1 week (PERISH_BY_DEFAULT)"
ceremony: "G signs, weekly renewal required"

exit_gate: "lease ACTIVE, first ceremony scheduled"
```

### P1.5 — End-to-End Smoke Test

```yaml
what: "BOAR's Monday readiness gate"
test: |
  Replay known ARS trade (trade 004 or 009) through full orchestrator path.
  Input: historical River bars for that date.
  Expected: orchestrator detects setup, CSO passes all 5 drawers,
  TradeProposal created, ExecutionIntent created, shadow mode blocks execution,
  ShadowObservation recorded.

also_test: |
  - pre-flight catches missing IBKR gateway
  - halt signal blocks execution
  - invalid setup (range > 30 pips) → correctly rejected
  - rejected setup → PROPOSAL_REJECTED bead emitted
  - CHAOS (BOAR): kill enrichment mid-bar → orchestrator halts loudly (not silent)
  - CHAOS (BOAR): inject ghost bar mismatch → adapter rejects gracefully (not crash)

exit_gate: |
  Full constitutional path exercised on known data.
  Paper position would open if shadow_mode=False.
  All governance gates verified.
  BOAR's "0 trades + dashboard green" scenario impossible.
```

---

## PHASE 2: SIGNAL ESCALATION ADAPTER (2-3 days)

```yaml
name: "DEXTER_TO_PHOENIX_CONSTITUTIONAL"
rationale: |
  HTF Directional signals enter Phoenix through constitutional governance.
  Dexter observes. Adapter escalates. Phoenix governs. Bridge records.
  "Telescopes do not fire rockets."
owner: Opus (Factory — clear spec from Appendix B)
prerequisite: Phase 1 complete (GateRegistry, orchestrator, intent adapter proven)
```

### P2.1 — Signal Escalation Adapter

```yaml
what: |
  Converts Dexter DIAGNOSTIC_SIGNAL into a Phoenix governance proposal.
  Follows GPT's Escalation Ladder pattern.

  DIAGNOSTIC_SIGNAL (analytical claim)
    → concurrent Phoenix enrichment snapshot
    → price discovery (entry, SL, TP, size)
    → TradeProposal (governance-grade)
    → CSO 5-drawer evaluation
    → ExecutionIntent (if passes)
    → governance gates (halt, shadow, lease, capital)

implementation_spec: "Appendix B.4 — 10-step call sequence"

critical_fields:
  entry_price: "df['close'].iloc[-1] at PIT boundary"
  stop_loss: "reconstructed from MarketState (asia_low/high ± sweep_extension ± buffer)"
  take_profit: "state.asia_high (long) / state.asia_low (short)"
  size: "(equity × 1%) / (|entry-SL| × pip_value × 10000)"

pit_boundary: "phoenix_now = signal.bar_time + timedelta(minutes=5)"
  reason: "aligns Dexter inclusive timing with Phoenix strict < filter"

invariants:
  - INV-SHADOW-MODE-RESPECTED: "shadow=True → ShadowObservation only"
  - INV-GOV-HALT-BEFORE-ACTION: "halt check before any intent creation"
  - INV-T2-GATE-1: "no broker submission without T2 token (live mode)"
  - INV-CONTRACT-1: "same signal + same state → same intent_hash"
  - INV-BUILDER-PURE-ADAPTER: "maps fields only, no scoring/inference"
  - INV-NO-FORMING-CANDLE: "signal.bar_time must reference closed bar"
  - INV-RACE-BAR-SYNC: "enrichment watermark ≥ signal.bar_time"
  - INV-CSE-PROVENANCE-1: "CSE carries River provenance from Phoenix"
  - INV-ATTR-CAUSAL-BAN: "no causal attribution in human-visible signal text"

pit_drift_monitor: |
  Monitor PIT drift: time between signal.bar_time and enrichment snapshot
  timestamp. If drift > 4min → Performance Warning in morning briefing.
  Prevents phantom missed trades from stale enrichment. (OWL)

exit_gate: |
  DIAGNOSTIC_SIGNAL from known historical data → enrichment snapshot →
  price discovery → TradeProposal → CSO evaluation → ExecutionIntent.
  Shadow mode blocks execution. PROPOSAL_REJECTED emitted on governance failure.
  Intent hash deterministic across replays.
  PIT drift logged on every adapter call; > 4min triggers warning.
```

### P2.2 — HTF Directional Cartridge

```yaml
what: "5-drawer cartridge configuration for HTF Directional strategy"

gate_mapping: |
  This cartridge uses DIFFERENT gate IDs than ARS — registered in same GateRegistry.
  Predicate functions read from WorldState (via signal) + MarketState (via enrichment).

  Drawer 1 (HTF_BIAS):         GATE_HTF_EXPANSION_OR_RETRACE (F1 bias check)
  Drawer 2 (MARKET_STRUCTURE):  GATE_LIQUIDITY_SWEPT_IN_KZ (F2 sweep in kill zone)
  Drawer 3 (PREMIUM_DISCOUNT):  GATE_PDA_ENGAGED (F4 PDA in OTE zone)
  Drawer 4 (ENTRY_MODEL):       GATE_MSS_CONFIRMED (F3 structure break + displacement)
  Drawer 5 (CONFIRMATION):      GATE_TARGET_REACHABLE + GATE_RR_VALID (F5 target + risk)

  Note: this is a DESIGN SKETCH. Final gate definitions shaped by
  Olya's shadow mode observation week and Dream Cycle findings.

exit_gate: |
  Cartridge YAML loads. GateRegistry resolves all HTF gate IDs.
  Historical signal → CSO evaluation → correct pass/fail verdict.
```

### P2.3 — Signal Friction Tracking

```yaml
what: "Track why valid analytical signals fail governance gates (OWL insight)"
output: "SIGNAL_FRICTION bead — governance-side rejection with structured reason"

value: |
  Dream Cycle already tracks analytical rejections (why chains were skipped).
  Signal Friction tracks governance rejections (why valid signals failed CSO).
  Together: complete learning surface across both economies.

exit_gate: |
  Every governance rejection produces SIGNAL_FRICTION bead.
  Morning briefing includes friction analysis alongside rejection analysis.
```

### P2.4 — Shadow Graduation Ceremony

```yaml
what: "Constitutional mechanism to transition shadow → paper → live"

ceremony_spec: |
  SHADOW → PAPER:
    requires:
      - CSO_SIGNOFF bead (Olya reviews shadow output, confirms alignment)
      - minimum_shadow_days >= 5 (configurable per lease)
      - minimum_shadow_signals >= 3 (OWL: days alone insufficient —
        5 quiet days with 0 trades is 0 data points)
      - Dream Cycle MFE/MAE summary (evidence of signal quality)
      - G approval (sovereign gate)
    mechanism: lease.shadow_mode = false (lease amendment, G signs)

  PAPER → LIVE:
    requires:
      - minimum_paper_days >= 10 (configurable per lease)
      - paper trading performance summary (win rate, drawdown, expectancy)
      - Olya confirmation (INV-OLYA-ABSOLUTE)
      - G activation (signed bead, INV-LIVE-REQUIRES-T2)
      - HaltMesh clearance window
    mechanism: lease.execution_mode = LIVE (new lease, full ceremony)

invariants:
  - INV-SHADOW-GRADUATION-ONCE: "graduation requires ceremony, cannot be undone without new lease"
  - INV-LIVE-REQUIRES-T2: "live execution requires human T2 token"
  - INV-SHADOW-MODE-RESPECTED: "shadow_mode at lease level, not code level"

exit_gate: |
  Ceremony mechanism exists.
  shadow_mode hardcode removed from signal_builder.py.
  shadow_mode read from active lease instead.
  Graduation requires signed bead from G.
```

---

## PHASE 3: OPERATIONAL HARDENING (ongoing, week 2+)

```yaml
name: "DAEMON_AND_FLEET"
rationale: "Promote batch processes to daemons, deploy across fleet, monitor"
```

### P3.1 — Batch → Daemon Promotion

```yaml
components:
  dexter_pipeline: "batch CLI → daemon watching staging JSONL (MIRROR pattern)"
  bridge: "batch orchestrator.cycle() → daemon on cadence (e.g. 1 min poll)"
  dream_cycle: "manual CLI → nightly cron (market close + 30min)"
```

### P3.2 — Fleet Deployment

```yaml
channels: "M4 + DGX (same pattern as M3 — bun symlink + bun install)"
m3_sync: "git pull dexter + phoenix, pipeline run, COO serves data"
mirror_on_m3: "optional — Olya access from M3 if needed"
```

### P3.3 — Veto Feedback Channel (OWL insight)

```yaml
what: "governance rejections flow back to Dexter via Bridge for refinery training"
mechanism: "new governance event type in existing Bridge (not a new channel)"
deferred_to: "Phase 3 — after signal channel is proven"
```

### P3.4 — Canon Doc Refresh

```yaml
documents:
  UNIFIED_ROADMAP: "update S66 section, add DEPLOYMENT_ROADMAP reference"
  SYSTEM_MANIFEST: "add S66 Track A/C/D, MIRROR, Dream Cycle, Channels"
  SPRINT_ROADMAP: "record S66 track completions + Phase 0-2 as sprints"
  vLOCK: "merge kill_zone_gate_v2 amendment into canonical YAML"
```

### P3.5 — Operational Watchdog

```yaml
what: "pre-session health check across all components"
pattern: OWL's Pre-Flight Heartbeat extended
checks:
  - IBKR gateway socket (127.0.0.1:4002)
  - River heartbeat (connected, subscribed, last_bar_time)
  - enrichment importable
  - halt state clear
  - lease active and not expired
  - DGX reachable (if Dream Cycle running there)
delivery: "morning health report via COO bot before market open"
```

---

## NEW INVARIANTS REGISTRY

```yaml
# From this deployment roadmap — to be registered in INVARIANT_REGISTRY

INV-GATE-NAMESPACE-SINGLETON:
  source: GPT
  rule: "Cartridge gate IDs are the ONLY gate namespace in the evaluator"
  enforcement: "GateRegistry rejects unregistered gate IDs"

INV-NO-PARALLEL-EVAL-PATHS:
  source: GPT
  rule: "No strategy evaluator may bypass the 5-drawer CSO system"
  enforcement: "evaluate_asia_scalp_setup() refactored into GateRegistry predicates"

INV-RACE-BAR-SYNC:
  source: BOAR
  rule: "Enrichment watermark must reach signal.bar_time before adapter fires"
  enforcement: "adapter blocks until enrichment confirms bar N processed"

INV-GHOST-CANON:
  source: BOAR
  rule: "All River consumers agree on bar count for any time window"
  enforcement: "adapter validates bar count alignment or errors"

INV-SHADOW-GRADUATION-ONCE:
  source: GPT
  rule: "Shadow→paper graduation requires ceremony, cannot self-reverse"
  enforcement: "lease amendment with signed bead"

INV-LIVE-REQUIRES-T2:
  source: GPT
  rule: "Live execution requires human T2 approval token"
  enforcement: "execution engine checks T2 before broker submission"

INV-PRE-FLIGHT-HEARTBEAT:
  source: OWL
  rule: "Orchestrator halts if gateway, River, or enrichment unhealthy"
  enforcement: "pre-flight check at orchestrator startup and each cycle"

INV-SHADOW-MODE-RESPECTED:
  source: RP Audit
  rule: "shadow_mode=True → ShadowObservation only, no ExecutionIntent"
  enforcement: "checked at adapter boundary AND governance gate"

INV-STATE-COMPLETENESS:
  source: GPT
  rule: "MarketState must have zero None values for any field referenced by active cartridge gates before CSO evaluation"
  enforcement: "pre-evaluation assertion, fail-closed"
```

---

## TIMELINE ESTIMATE

```yaml
phase_0: "1-2 days (mechanical fixes + GateRegistry design)"
phase_1: "2-3 days (ARS canonical path + orchestrator + smoke test)"
phase_2: "2-3 days (signal adapter + HTF cartridge + ceremony)"
phase_3: "ongoing (operational hardening, daemon promotion, fleet)"

total_to_paper_trading: "~5-8 days of Opus build time"
first_paper_trade: "end of Phase 1 (ARS in shadow mode through constitutional path)"
first_dexter_signal_trade: "end of Phase 2 (HTF Directional through escalation adapter)"

parallel_work_during_build:
  olya: "observes MIRROR dashboard, trades live, annotates"
  dream_cycle: "runs nightly on existing detection output"
  channels: "COO operational on M3 for coordination"
  calibration: "Olya visual sessions on PROPOSED HTF params"
```

---

## REFERENCE APPENDICES

```yaml
appendix_a: "Gate Wiring Table — in SYSTEM_ARCHITECTURE_AUDIT_v1.md Appendix A"
appendix_b: "Signal Adapter Data Requirements — in SYSTEM_ARCHITECTURE_AUDIT_v1.md Appendix B"
```

---

*No shortcuts. No parallel paths. Every strategy through constitutional governance.*
*Telescopes do not fire rockets.*
*OINK OINK.* 🐗🔥
