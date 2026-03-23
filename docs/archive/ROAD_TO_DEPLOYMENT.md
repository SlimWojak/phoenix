# ═══════════════════════════════════════════════════════════════════════════════
# a8ra — ROAD TO DEPLOYMENT
# From: G + Claude (RA instance, S64-S65 context holder)
# To: Fresh CTO (Opus, Sunday morning orientation)
# Date: 2026-03-21 (Saturday evening)
# Purpose: Sunday is deployment day. This document is your mission brief.
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# 1. WHERE WE ARE — WHAT HAPPENED TODAY
# ─────────────────────────────────────────────────────────────────────────────

saturday_delivery: |
  Two sprints sealed in one day. S64 (morning) and S65 (evening).

  S64 delivered: 13 locked L1 primitives ported to core producers,
  verified against 14 Olya-annotated ground truth trades, methodology
  locked end-to-end from research tool to core system.

  S65 delivered: full detection pipeline on live River data, HTF producers
  on all timeframes, state detection classifier (EXPANSION/RETRACE/RANGE),
  five-factor checklist with two entry models (REVERSAL/CONTINUATION),
  DIAGNOSTIC_SIGNAL generation in shadow mode, cartridge + conditions
  updated to vLOCK names. 218 tests. 47 files. 11,791 lines.

  A critical HTF displacement bug (inverted close_location formula +
  missing DECISIVE_OVERRIDE path) was found and fixed — signals went
  from 0 to functional immediately.

  Gate B3C: 4/8 addressable trades produce DIAGNOSTIC_SIGNALs.
  The 4 misses are state classifier mismatches (end-of-day snapshot
  vs intraday state evolution). Checklist is proven correct.

commit: be2a06e — S65 sealed, main branch, ready to push

# ─────────────────────────────────────────────────────────────────────────────
# 2. THE STRATEGIC SHIFT — BUILD MODE → OPERATE MODE
# ─────────────────────────────────────────────────────────────────────────────

pivot: |
  Sunday marks the transition from "system under construction" to
  "deployed live system trading on paper."

  The foundations are solid:
    - Constitutional governance: v0.1 sealed, halt operational, 273 chaos vectors
    - Bead field: 11.4M FACTs, bridge operational, query layer built
    - Methodology: 13/13 primitives locked, 14 ground truth trades
    - Detection: full pipeline River → producers → state → checklist → signals
    - Hardware: 5-node cluster wired, DGX Sparks operational
    - Factory model: proven today — Opus builds full sprints in hours

  What remains is NOT architectural. It's operational:
    - Fix 4 known flags (mechanical, not design)
    - Wire signals to paper execution (engine already exists)
    - Deploy each service to its final hardware home
    - Stand up the communication layer (Claude Channels via Telegram)
    - Start the feedback loop (Dream Cycle v1 rejection mining)

  The paper trading period IS the safety net:
    - INV-CAPITAL-GATE: no live capital without human T2 approval
    - Shadow mode → paper mode → live mode (graduated, human-gated)
    - Olya compares system output to her own trading daily
    - Every week of paper trading adds ground truth data

  We learn by operating, not by building more infrastructure.

olya_direction: |
  "Run in parallel to live trading. Continue annotating.
   System finds my logic in live IBKR data on an expanding trade pool."

  This is the north star for Sunday. Everything we deploy serves this.

# ─────────────────────────────────────────────────────────────────────────────
# 3. SUNDAY PLAN — ONE DEPLOYMENT, FOUR PARALLEL TRACKS
# ─────────────────────────────────────────────────────────────────────────────

framing: |
  This is NOT four sequential sprints. It is one deployment manifest
  with four tracks that can run in parallel. Opus builds Tracks A-C
  as briefs. G deploys Track D (ops work, not code).

  Target: system fully operational by Sunday evening.
  Monday: Olya trades live, system runs paper alongside her.

# ─── TRACK A: PAPER TRADING LIVE ──────────────────────────────────────────

track_a:
  name: "PAPER_TRADING_OPERATIONAL"
  owner: Opus
  deploys_to: M4 Studio (Phoenix execution)
  priority: HIGHEST — this is the core deliverable

  part_1_fix_flags:
    flag_1_intraday_state:
      what: |
        State classifier currently runs once per day (end-of-day snapshot).
        Must re-evaluate on each new 1H and 4H bar close.
        The logic is already correct — trade_001 proved it fires perfectly
        when state matches. The fix is WHEN it runs, not WHAT it computes.
      impact: 4 state classifier mismatches in B3C become hits
      scope: classifier.py trigger frequency change + test

    flag_2_signal_direction:
      what: |
        Signals currently emit for all chains, not just those matching
        WorldState direction permission. The contradiction skip exists
        in the skip table but may not be catching all cases.
      scope: evaluator.py bug fix + test

    flag_3_htf_proposed_params:
      what: |
        HTF displacement/MSS params are PROPOSED (body 0.55, close_gate
        0.40/0.45). For paper trading, PROPOSED is acceptable — these
        produce a superset of detect.py's locked output (13 vs 9 on 1H).
        Olya calibrates from real shadow/paper output over first week.
      scope: NO CODE CHANGE — run with PROPOSED, document in output

    flag_4_sweep_level_pool:
      what: |
        SESSION_LIQUIDITY box params need promoted swings and session
        levels populated for full sweep detection.
      scope: level pool population in level_lifecycle.py

  part_2_wire_to_execution:
    what: |
      Connect DIAGNOSTIC_SIGNAL output to Phoenix paper execution engine.

      The execution engine already exists (S51 Asia Range Scalp):
        - 9-state position lifecycle (canonical: execution/positions/)
        - Paper broker with 5-state FSM (execution/positions/paper.py)
        - IBKR integration validated in paper mode
        - GovernanceSentinel (passive bounds, <2ms, dead-man's switch)

      The adapter needed:
        - DIAGNOSTIC_SIGNAL fires → create paper position
        - Entry: signal price at chain time
        - Stop loss: swing beyond PDA (from chain source_refs)
        - Take profit: F5 primary_target level
        - Position sizing: fixed lot for paper (e.g. 0.01)
        - Kill zone validation: signal must be in LOKZ/NYOKZ

      shadow_mode flag progression:
        Week 1: shadow_mode=true (DIAGNOSTIC_SIGNAL, observe only)
        Week 2+: shadow_mode=false (paper execution, G + Olya approval)
        Future: live execution (INV-CAPITAL-GATE, T2 human approval)

  exit_gate: |
    Paper position opens on DIAGNOSTIC_SIGNAL.
    Position managed by existing lifecycle engine.
    SL/TP from signal metadata. Rate limit 3 per 4H window.
    Run on Monday market data. At least one paper trade if signal fires.

# ─── TRACK B: AIR (Agent Integrity Runtime) ───────────────────────────────

track_b:
  name: "AIR_OPERATIONAL"
  owner: Opus
  deploys_to: M3 Ultra (bead field integrity)

  context: |
    This sounds heavier than it is. The components exist:
      - PQC signing: ML-DSA-65 Dilithium3, real, ARM64 (Gate 1, proven)
      - Attestation envelope: Proto-AIR v0.2 schema (S63 T5)
      - Bridge notary: signature verification on every bead (191 tests)
      - Bead signing: already operational on all structural beads

    AIR extends signing to cover agent actions — the same mechanism
    that beads already use, applied to a wider surface.

  scope:
    - Agent action signing (same PQC pipeline as bead signing)
    - Unsigned mutation rejection + security event logging
    - Code hash verification against approved builds
    - Attestation bundle format aligned with bridge notary envelope
    - INV-AIR invariants from Proto-AIR v0.2 (6 defined, implement)

  does_NOT_include:
    - New cryptographic infrastructure (already built)
    - HSM integration (future — software signing sufficient for v0.1)
    - Hardware security module (S69+ sovereign readiness)

  exit_gate: |
    Unsigned agent mutation rejected and logged.
    Any bead inspectable with full attestation bundle.
    Local verification: hash chain + Merkle proof + signature.
    Existing bead field tests still pass.

# ─── TRACK C: DREAM CYCLE v1 (Rejection Mining) ──────────────────────────

track_c:
  name: "DREAM_CYCLE_V1"
  owner: Opus
  deploys_to: DGX Dexter (production inference)

  context: |
    The full Dream Cycle vision (EnvModels, counterfactual simulation,
    GAN synthetic regimes, SkillRL) is a multi-month research programme.

    The operational minimum that makes the system LEARN is simpler:
    paper trading produces rejections. A nightly job reviews them.
    Findings surface for human review in the morning. This is the
    feedback loop that compounds — every day of operation makes the
    system smarter.

  scope_v1_rejection_mining:
    input: PROPOSAL_REJECTED beads from paper trading day
    process:
      - Scan day's rejections (which setups were skipped, why)
      - Compute basic diagnostics per rejection:
          what_was_the_skip_reason (from skip_table)
          what_happened_after (price moved how far in what direction)
          was_the_rejection_correct (would the trade have hit TP or SL)
      - Flag interesting patterns:
          false_rejections (skipped but would have been profitable)
          correct_rejections (skipped and would have lost)
          state_mismatches (classifier said X, market did Y)
      - Produce structured morning briefing
    output: DREAM_CYCLE_BRIEFING bead (daily, surfaces to G + Olya)

    compute: Qwen3.5-27B on DGX (already running via vLLM)
    alternative: Opus API call for higher quality analysis if needed

  does_NOT_include:
    - EnvModel training (S69+)
    - Counterfactual simulation (S69+)
    - GAN synthetic regimes (S69+)
    - SkillRL distillation (S69+)
    - Adversarial agents (S69+)

  exit_gate: |
    Nightly job runs on DGX after market close.
    Morning briefing produced with rejection analysis.
    At least one week of paper trading data before meaningful patterns.
    Briefing accessible via COO Telegram bot.

# ─── TRACK D: CHANNELS DEPLOYMENT (Ops, not code) ────────────────────────

track_d:
  name: "CHANNELS_COORDINATION_LAYER"
  owner: G (with COO Claude Code on M3)
  deploys_to: all nodes

  context: |
    Claude Code Channels shipped March 20, 2026 (yesterday).
    Telegram/Discord integration via MCP plugins. Two-way bridge:
    message a bot, Claude Code session picks it up, executes, replies.

    This REPLACES the planned NATS/Kafka event bus from the original
    S67 swarm agents design. For paper trading with human oversight,
    Telegram bots on persistent Claude Code sessions is simpler, faster,
    and gives G + Olya mobile access as a bonus.

    The custom swarm architecture can be added later if Telegram
    coordination proves insufficient for autonomous operation.

  deployment:
    coo_bot:
      name: "@a8ra_coo"
      node: M3 Ultra
      role: orchestrator, bead field access, pipeline runner, daily exports
      session: "claude --channels plugin:telegram@claude-plugins-official"
      zellij: persistent session, always-on
      mcp: bead field query, River reader, detection pipeline

    phoenix_bot:
      name: "@a8ra_phoenix"
      node: M4 Studio
      role: execution engine, position management, governance
      session: same channels pattern
      zellij: persistent session

    dexter_bot:
      name: "@a8ra_dexter"
      node: DGX Dexter
      role: analysis, Dream Cycle briefing, rejection mining
      session: same channels pattern
      zellij: persistent session

  user_access:
    G: messages any bot from phone (Telegram DM)
    Olya: messages COO or dedicated surface for detection review

  operational_pattern:
    morning: G messages COO "what happened overnight?" → briefing
    during_session: Olya trades, system runs parallel, COO monitors
    end_of_day: G messages COO "run daily export" → detection summary
    overnight: Dream Cycle runs on DGX, produces morning briefing
    next_morning: cycle repeats

  setup_requirements:
    - Claude Code v2.1.80+ on all nodes (verify/update)
    - Telegram bot created per node via @BotFather
    - Bun installed on each node (MCP server runtime)
    - Plugin installed: /plugin marketplace add anthropics/claude-plugins-official
    - Allowlist configured (G + Olya only, no stranger access)
    - Persistent Zellij sessions with --channels flag

  constraint: |
    Events only arrive while session is open. Zellij persistent sessions
    handle this. If a session dies, messages sent during downtime are lost
    (Telegram Bot API has no message history). MCP health layer on all
    nodes monitors liveness. Restart procedure documented.

# ─────────────────────────────────────────────────────────────────────────────
# 4. WHAT THIS REPLACES ON THE UNIFIED ROADMAP
# ─────────────────────────────────────────────────────────────────────────────

roadmap_reframe:

  S66_was: "GATE_3_AIR (Agent Integrity Runtime)"
  S66_now: "a8ra v0.1 OPERATIONAL — paper trading + AIR + Dream Cycle v1 + Channels"
    rationale: |
      The remaining sprints (S66 AIR, S67 Swarm, S68+ Dream Cycle) were
      scoped when each was weeks of work. The RA detour + factory model
      collapsed build time. The components exist. Sunday is integration
      and deployment, not greenfield.

  S67_was: "GATE_4_SWARM_AGENTS (Director, Librarian, Researcher, Executor)"
  S67_now: DEFERRED — Channels replaces event bus for near-term coordination
    rationale: |
      NATS/Kafka event bus + saga orchestration was designed for autonomous
      multi-agent operation. Paper trading with human oversight doesn't need
      autonomous agents. Telegram Channels provides the coordination surface.
      Swarm agents return when the system graduates from paper to autonomous.

  S68_was: "GATE_5_DREAM_CYCLE_v1 (Counterfactuals)"
  S68_now: "Dream Cycle v1 deployed as rejection mining in Track C"
    rationale: |
      Full EnvModels + counterfactual simulation needs Shadow Field volume
      from weeks of paper trading. Rejection mining starts accumulating
      that data from day 1. SkillRL builds on top once volume exists.

  future_sprints:
    S67: "SWARM_AGENTS — when paper trading graduates to autonomous"
    S68: "DREAM_CYCLE_v2 — EnvModels + counterfactual + SkillRL"
    S69: "SOVEREIGN_READINESS — HSM, DR, incident response, full audit"

# ─────────────────────────────────────────────────────────────────────────────
# 5. KNOWN ITEMS — CARRY INTO OPERATIONAL PHASE
# ─────────────────────────────────────────────────────────────────────────────

operational_tuning: |
  These are NOT blockers. They are items that get tuned through operation.
  Each improves signal quality. None compromise system integrity.

items:
  htf_displacement_calibration:
    status: PROPOSED params running in paper mode
    action: Olya visual session after first week of live output
    impact: upstream_claim path activates, state classifier sharpens

  htf_mss_params:
    status: PROPOSED (same session as displacement)
    action: Olya confirms thresholds from real HTF detections

  state_classifier_intraday:
    status: flag_1 fix in Track A
    action: mechanical — trigger on 1H/4H bar close instead of daily

  sweep_level_pool:
    status: incomplete (SESSION_LIQUIDITY box params)
    action: flag_4 fix in Track A

  14_trade_regression:
    status: Gate B3C produced 4/8, needs gate6_verification.py extended
    action: after flag fixes, re-run full pipeline on all 14 trades
    target: ≥8/10 addressable trades produce DIAGNOSTIC_SIGNAL

  smt_primitive:
    status: 2/14 trades used DXY divergence as sweep substitute
    action: monitor frequency, revisit if pattern recurs in paper trading

  weekly_monthly_detection:
    status: deferred (Daily/4H/1H sufficient for all validated trades)
    action: add if Olya's live annotations surface need

  ce_touched_wick_vs_close:
    status: CLOSED by Olya L2 session (FILLED state added)
    action: none — implemented in Brief 2 amendments

# ─────────────────────────────────────────────────────────────────────────────
# 6. SAFETY INVARIANTS — NON-NEGOTIABLE
# ─────────────────────────────────────────────────────────────────────────────

safety: |
  The pace is fast. The invariants are not relaxed.

invariants_active:
  INV-CAPITAL-GATE: "No live execution without human T2 approval"
  INV-HUMAN-FRAMES: "Human frames. Machine computes. Human promotes."
  INV-OLYA-ABSOLUTE: "Olya's NO on methodology is absolute"
  INV-SOVEREIGN-VETO: "G can halt any task via BROADCAST"
  INV-HALT-OVERRIDES-LEASE: "Constitutional halt, <50ms local"
  INV-NO-FORMING-BAR-CONSUMPTION: "Closed bars only"
  INV-WARMUP-MANDATORY: "No HTF CLAIM until minimum bars seeded"
  INV-REPLAY-LIVE-PARITY: "Same bars → same CLAIMs"
  INV-IDEMPOTENT-CLAIM-EMIT: "No duplicate CLAIMs on re-run"

graduated_trust:
  week_1: shadow mode — DIAGNOSTIC_SIGNAL only, Olya observes
  week_2_plus: paper trading — G + Olya approve transition
  future: live trading — T2 human approval, capital gate enforced

  nothing_skips_a_step: |
    The factory model means builds are fast.
    The trust model means deployment is graduated.
    These are independent. Fast builds. Careful promotion.

# ─────────────────────────────────────────────────────────────────────────────
# 7. SUNDAY EXECUTION SEQUENCE
# ─────────────────────────────────────────────────────────────────────────────

sequence:

  sunday_morning:
    cto_orient: "Read this document. Read S65_SPRINT_SEAL.md. Read S65 interface contracts."
    confirm: "River streaming (21.parquet accumulating after market open ~22:15 UTC Sunday)"

  parallel_execution:
    opus_track_a: "Paper trading brief — fix 4 flags + wire signal→execution adapter"
    opus_track_b: "AIR brief — extend PQC signing to agent actions"
    opus_track_c: "Dream Cycle v1 brief — rejection mining nightly job"
    g_track_d: "Channels deployment — Telegram bots on each node"

  verification:
    track_a: "Paper position opens on signal. Existing tests pass."
    track_b: "Unsigned mutation rejected. Attestation bundle inspectable."
    track_c: "Nightly job runs. Morning briefing produced."
    track_d: "G messages COO from phone. Response received."

  sunday_evening:
    confirm: "All 4 tracks operational"
    run: "Full pipeline on Sunday/Monday live data"
    observe: "DIAGNOSTIC_SIGNALs flowing? Paper positions managed?"

  monday:
    olya: "Trades live as normal"
    system: "Runs in parallel — detections, signals, paper positions"
    evening: "G reviews day 1 output with Olya"
    overnight: "Dream Cycle v1 runs first rejection analysis"
    tuesday_am: "Morning briefing — the machine is learning"

# ─────────────────────────────────────────────────────────────────────────────
# 8. KEY FILES — CURRENT STATE
# ─────────────────────────────────────────────────────────────────────────────

files:

  methodology:
    canonical: "SYNTHETIC_OLYA_METHOD_vLOCK.yaml — DO NOT MODIFY"
    state_detection: "STATE_DETECTION_LOGIC_v2.yaml (v2.4)"
    locked_params: "configs/locked_baseline.yaml"

  s65_deliverables:
    river_adapter: "dexter/bead_field/river/river_adapter.py"
    htf_producers: "dexter/bead_field/producers/htf_producers.py"
    htf_config: "dexter/bead_field/producers/htf_config.py"
    state_classifier: "dexter/state/classifier.py"
    level_lifecycle: "dexter/state/level_lifecycle.py"
    ote_producer: "dexter/bead_field/producers/ote.py"
    spatial_predicates: "dexter/bead_field/query/spatial.py"
    composite_chains: "dexter/bead_field/producers/composite.py"
    checklist: "dexter/checklist/evaluator.py"
    signal_builder: "dexter/checklist/signal_builder.py"
    pipeline: "scripts/daily_detection_export.py"
    contracts: "docs/s65_interface_contracts.md"

  ground_truth:
    trades: "research/ground_truth/annotated_trades.yaml (14 trades)"
    gate6_verification: "scripts/gate6_verification.py"

  phoenix_updated:
    cartridge: "cartridges/active/asia_range_scalp.yaml (vLOCK names)"
    conditions: "cso/knowledge/conditions.yaml (vLOCK gates)"
    methodology: "cso/knowledge/methodology_template.yaml (vLOCK primitives)"

  broadcasts:
    s64_seal: "CTO_BROADCAST_S64_SEAL_S65_POLL.md"
    s65_seal: "docs/S65_SPRINT_SEAL.md"
    this: "ROAD_TO_DEPLOYMENT.md — you are here"

# ═══════════════════════════════════════════════════════════════════════════════
# END
#
# The system is built. The methodology is locked. The hardware is wired.
# The invariants hold. The paper trading period is the safety net.
#
# Sunday we turn the machine on.
# ═══════════════════════════════════════════════════════════════════════════════
