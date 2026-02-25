# ═══════════════════════════════════════════════════════════════
# a8ra BROADCAST — WEDNESDAY 2026-02-25
# FROM: G (synthesised from CTO Tuesday closeout + 2 strategic sessions)
# TO: All offices, CTO, Advisors
# PURPOSE: Single orientation doc. Execute from this. No other docs needed.
# ═══════════════════════════════════════════════════════════════

FORMAT: DENSE_M2M
SUPERSEDES: [CTO_BROADCAST_240226.md, CTO_ADDENDUM_POST_S54_EVENING.md, CTO_ADDENDUM_2_WEDNESDAY_MORNING.md]

# ───────────────────────────────────────────────────────────────
# 1. SYSTEM STATE
# ───────────────────────────────────────────────────────────────

SYSTEM:
  version: "a8ra v0.1 — post-S54"
  branch: main
  repo: github.com/SlimWojak/phoenix
  tests: 1786 (1750 pass, 25 xfail, 2 skip)
  sprints_complete: 24 (S28-S44, S46-S54)
  invariants_registered: 240
  risk: "ZERO TIER_1. ZERO TIER_2."
  river: OPERATIONAL (EURUSD 1m bars, keepUpToDate, launchd KeepAlive)
  gateway: HARDENED (primaryoverride, competing session resolved)
  phase: "OPERATIONAL — build-and-prove complete, operate-and-expand begins"

DEBT:
  - "ruff: 34 lint issues (non-capital-path)"
  - "mypy: non-capital-path dirs still untyped"
  - "chaos_bunny: 1 flaky test (pre-existing)"
  - "ib_insync 0.9.86: unmaintained (ib_async fork = migration candidate)"
  - "IB password in config.ini plaintext — ROTATE"

# ───────────────────────────────────────────────────────────────
# 2. S54 DELIVERY SUMMARY (Tuesday — complete, do not re-derive)
# ───────────────────────────────────────────────────────────────

S54_TRUTH_SWEEP:
  T1: "Execution contract updated (5-state → 10-state FSM from code)"
  T2: "MOCK_5DRAWER added to cse_schema.yaml"
  T3: "Invariant registry 37 → 240 (programmatic discovery)"
  T4: "mypy --strict on governance/ execution/ cso/ → 0 errors (209 eliminated)"

RIVER_FIX:
  primitive: "reqRealTimeBars (wrong) → reqHistoricalData keepUpToDate (correct)"
  tz_bug: "Double tz application on ib_insync datetimes → fixed"
  gateway: "primaryoverride in config.ini → zombie session resolved"
  validation: "20/20 river tests, consecutive bars confirmed"
  logs: "~/logs/river.stdout.log, heartbeat file"

# ───────────────────────────────────────────────────────────────
# 3. HARDWARE TOPOLOGY — LOCKED
# ───────────────────────────────────────────────────────────────

SOVEREIGN_TIER: # Headless, rack-mounted, UPS-backed, 24/7
  M3_ULTRA:
    role: "The Brain — canonical repo, River/Gateway, Matrix/Conduit, local model serving"
    ram: 512GB | storage: 4TB
    models: "See Section 3a — LOCAL MODEL SELECTION"
    status: ARRIVING_WEDNESDAY (DHL, afternoon/evening likely)
  DGX_SPARK:
    role: "Research Muscle — DEXTER workloads, GPU inference"
    status: UNWRAPPED_NOT_BOOTED (Ubuntu headless, mDNS discovery)

INTERACTIVE_TIER: # Where humans sit
  M4_MAX_STUDIO: "G's daily driver — Cursor, Claude Code, terminals. KEEP AS WORKSTATION."
  MAC_MINI_PRO_24GB: "PHOENIX office node / flexible spare"
  MAC_MINI_STOCK: "ORACLE node — Olya's office (alongside MacBook)"
  REMAINING_MINIS: "Spares, future office nodes"

NETWORK:
  internal: "10Gbps (TP-Link TL-SX1008, Cat6a)"
  external: "2000/1000 Mbps"
  current: "WiFi only until contractor wires Thu/Fri"
  ups: "APC pure sine wave, floor-mounted"

KEY_PRINCIPLE: "M4 Max = cockpit. Rack machines = engines. Configure headless via SSH."

SETUP_SEQUENCE:
  wed_am: "Strategic planning, specs, advisor tasking (M3 not yet arrived)"
  wed_pm: "M3 arrives → temp monitor → first boot → macOS → SSH → Homebrew/git/Claude Code"
  wed_pm_2: "DGX first boot → Ubuntu verify → SSH → hostname"
  wed_eve: "Both SSH-accessible from M4 Max. Start model downloads (overnight wifi)."
  thu_fri: "Contractor wires. Rack. 10Gbps verified. Static IPs. UPS. Sovereign tier operational."

# ───────────────────────────────────────────────────────────────
# 3a. LOCAL MODEL SELECTION — PROPOSED (REVIEW REQUESTED)
# ───────────────────────────────────────────────────────────────

# Source: Grok frontier scout assessment (2026-02-25), informed by Qwen 3.5 release (2026-02-24).
# Status: PROPOSAL — CTO and Advisors to pressure-test before download begins.
# Criteria: coding/agentic (swarm offices), reasoning (oracle, Bead Field), long context (research), efficiency (local inference).
# Principle: MoE for efficiency, dense for depth, open-source only, start small → scale to beasts.

M3_ULTRA_512GB: # Apple Silicon, MLX-optimized, GGUF/EXL2 quantized
  SLOT_1:
    model: "Kimi K2.5 (dense, ~70B equiv)"
    role: "Agent core — coding, swarm office brains, oracle linting"
    why_first: "SWE-bench 43.8%, LiveCodeBench 83%, agentic 60.2% (>GPT-5), lowest agent harness friction"
    fit: "MLX-quantized ~40GB RAM"
  SLOT_2:
    model: "Qwen 3.5 35B-A3B (MoE)"
    role: "Mid-tier tester — quick swarm prototyping, oracle mini-runs"
    why: "Active 3B = snappy on Apple Silicon, near-122B on several benches"
    fit: "~20GB quantized"
  SLOT_3:
    model: "Qwen 3.5 27B (dense)"
    role: "Lightweight probe — test bed for sub-agent patterns"
    why: "Fast dense, 262k context, math/code solid"
    fit: "Native MLX"

DGX_SPARK: # NVIDIA GPU, FP16/8-bit native
  SLOT_1:
    model: "Qwen 3.5 122B-A10B (MoE)"
    role: "Scale beast — Dream Cycle sims, oracle rebuilds, heavy research"
    why_first: "SOTA MoE (active 10B = dense speed, GPQA ~84%), 262k context, SWE-bench 67%, NVIDIA-optimized"
    advantage: "MoE = multi-agent cheap (low active params per query = swarm parallel)"
  SLOT_2:
    model: "GLM-5 (dense, ~70B)"
    role: "Reasoning backup — research mining alt if Kimi unavailable"
    why: "Tops open-source alongside Kimi, tool-calling 90.6%, SWE-bench 42.1%"
  SLOT_3:
    model: "Kimi K2.5 (if DGX-ported)"
    role: "Agent depth on GPU — contingent on port availability"

HYBRID_STRATEGY: |
  Kimi = agent brains (coding/agentic leader across 10/14 benchmarks).
  Qwen 122B MoE = heavy research/oracle (efficient scale, beats Sonnet 4.5 in math/code).
  Not either/or — complementary. Kimi for depth, Qwen for throughput.

DOWNLOAD_ORDER: |
  M3 first boot: Kimi K2.5 → Qwen 35B-A3B → Qwen 27B
  DGX first boot: Qwen 122B-A10B → GLM-5
  Overnight on wifi. Verify inference before contractor wiring.

REVIEW_NEEDED: "CTO + Advisors: validate model choices against a8ra workloads before downloads commit."

# ───────────────────────────────────────────────────────────────
# 4. ARCHITECTURAL PRINCIPLES — LOCKED
# ───────────────────────────────────────────────────────────────

CLI_FIRST:
  statement: "Files > MCP. CLI > abstractions. If an agent can cat/grep/pipe it, don't wrap it."
  exception: "MCP only for genuinely external authenticated services"
  stack_impact:
    mcp_memory_keeper: "KILL from Phase 1 → file-based memory directory"
    projections: "File at known path. cat, not MCP."
    river_queries: "DuckDB CLI, not MCP wrapper"
    memory_store: "~/office-memory/{office}/ — agent searches with grep, reads with cat"
  rationale: "Filesystem IS the API. Git IS the coordination protocol."

PROJECTION_NOT_PARTICIPATION:
  statement: "Offices consume projections of state, not raw system access"
  revision: "Projections = summary layer (morning briefing, digest). NOT primary interface."
  primary: "Live CLI queries via Analyst + HUD ambient display"
  rule: "Every projection timestamped, sourced, with staleness threshold"

CONTEXT_BEADS:
  rule: "No context without provenance. Anything without provenance = untrusted."
  schema: "{key, value, source, updated_at, max_age_seconds, stale_action}"
  examples: "Market data stale >5min → REFUSE_TO_QUOTE. Sprint state stale >24h → WARN."

SEPARATION_OF_TIERS:
  statement: "Sovereign tier never shares hardware with interactive tier"
  corollary: "G's reboot ≠ system outage"

BUILD_OBSERVE_HARDEN:
  statement: "V1 simple. Friction announces itself. Harden at observed seams."

# ───────────────────────────────────────────────────────────────
# 5. OLYA / ORACLE — THREE-SURFACE COCKPIT (LOCKED)
# ───────────────────────────────────────────────────────────────

PATTERN: "G has CTO (Chat) + COO (Code). Olya has CSO (Chat) + Analyst (Code) + HUD."

SURFACES:
  HUD:
    status: "BUILT (S48) — needs tuning sprint"
    tech: "SwiftUI, reads manifest.json, <500ms refresh"
    shows: [river_status, positions, pnl, leases, conditions_armed, dexter_status, killzone_times, health]
    kill_switch: "RED HALT BUTTON → confirmation → HALT.signal"
  CSO_CHAT:
    interface: "Claude Desktop → Chat tab"
    role: "Strategy discussion, methodology validation, research direction"
    mode: "Conversational, async, human-paced"
  ANALYST:
    interface: "Claude Desktop → Code tab"
    role: "Live queries, data analysis, hypothesis drafting, task submission"
    project_folder: "~/phoenix/ (read-only mounts to M3)"
    can: [query_river, read_leases, run_market_state_builder, search_memory, draft_briefs, add_tasks_to_queue, trigger_HALT]
    cannot: [modify_py_files, git_push, install_packages, restart_daemons, modify_configs]

ANALYST_PERMISSIONS:
  allow: ["Read", "Bash(duckdb*)", "Bash(python3 */market_state_builder*)", "Bash(cat*)", "Bash(grep*)", "Bash(stat*)", "Bash(git pull*)"]
  deny: ["Write", "Edit", "Bash(git push*)", "Bash(git commit*)", "Bash(rm*)", "Bash(pip*)", "Bash(npm*)"]
  halt_exception: "ONE write: echo HALT signal to phoenix-swarm/HALT.signal (Olya's explicit instruction only)"

NETWORK_MOUNT:
  decision: "Read-only SMB/NFS from M3 Ultra to Olya's Mini over 10Gbps"
  mounts: ["/Volumes/phoenix-river/ → M3 ~/phoenix-river/", "/Volumes/phoenix-state/ → M3 ~/phoenix/state/"]
  timing: "Thu/Fri with contractor"

OLYA_STATED_NEEDS:
  - "In-the-moment knowledge of what's happening"
  - "Live positions, entry/exit confirmed on IBKR"
  - "Current PnL on live positions"
  - "Setups forming"
  - "Kill switch without calling G"
  - "All over the detail of the trading system"

# ───────────────────────────────────────────────────────────────
# 6. HALT AUTHORITY — CONSTITUTIONAL
# ───────────────────────────────────────────────────────────────

NEW_INVARIANTS:
  INV-OLYA-HALT-AUTHORITY: "Olya can trigger halt_cascade at any time without G approval"
  INV-HALT-HUMAN-ONLY-RESTART: "No agent/daemon/cron can clear HALT. G manual action only."

HALT_HIERARCHY:
  can_halt: [G, Olya, governance_invariant_breach_automatic]
  can_restart: [G_only]
  can_never: [any_agent, any_daemon, any_cron]

HALT_MECHANISM: |
  Any surface writes: phoenix-swarm/HALT.signal
  Content: {"source": "OLYA|G|GOVERNANCE", "timestamp": "ISO", "reason": "..."}
  Execution engine checks pre-action. On detect: flatten, cancel, log, stop.
  System defaults STOPPED. Restart requires human who understands why it stopped.

# ───────────────────────────────────────────────────────────────
# 7. DEXTER RESEARCH PIPELINE — GAP (SPEC NEEDED)
# ───────────────────────────────────────────────────────────────

GAP_STATUS: SPEC_NEEDED

EXISTS:
  river: "LIVE — 11.8M bars, 6 pairs, RiverReader+DuckDB (Phoenix module)"
  extraction: "789 Genesis beads, knowledge pipeline operational"
  synthetic_river_py: "Deterministic fake data for UNIT TESTS ONLY"

MISSING:
  gap_1: "DEXTER cannot read the river (lives in ~/phoenix-river/, no bridge)"
  gap_2: "Research loop (Olya→hypothesis→DEXTER→evidence→review) stated but not specified"
  gap_3: "Synthetic river ambiguity: test fake data ≠ historical replay for backtests"

PROPOSED_SPEC:
  name: DEXTER_RESEARCH_PIPELINE
  components: [river_readonly_access, direction_flow, research_types, evidence_output]
  invariant: "INV-DEXTER-RIVER-READONLY: DEXTER never writes to production river"
  action: "Draft spec Wednesday. OWL audit. Build as sprint when hardened."

# ───────────────────────────────────────────────────────────────
# 8. CLAUDE CODE FEATURES — GROUND-TEST WEDNESDAY
# ───────────────────────────────────────────────────────────────

AGENT_TEAMS: "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 — lead+teammates, worktree isolation. Ground-test on M3."
WORKTREE_ISOLATION: "claude --worktree → per-session git isolation. Solves concurrent mutation seam."
NATIVE_AUTO_MEMORY: "Auto session summaries to MEMORY.md (200-line cap). SET CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 initially."
AGENT_MEMORY_FRONTMATTER: "Per-office memory with scopes (user, project, local). Evaluate during ground testing."
MEMORY_LEAK_FIXES: "6 leaks fixed Feb 19-21. CRITICAL for 24/7 headless on M3/DGX."
REPOPROMPT: "Cartridge builder — cron to rebuild projections. Complementary to CLI-first."
STACK_KILLS: "mcp_memory_keeper: DEAD. tmux_hive_ops: DEAD."

# ───────────────────────────────────────────────────────────────
# 9. WEDNESDAY PRIORITIES
# ───────────────────────────────────────────────────────────────

MORNING (pre-M3 arrival):

  P1_MANIFEST_UPDATE:
    what: "Add projection concept + DEXTER research pipeline gap to system manifest"
    owner: CTO

  P2_DEXTER_RESEARCH_SPEC:
    what: "Draft DEXTER_RESEARCH_PIPELINE spec v0.1"
    owner: CTO
    advisor_input: "OWL (structure), GPT (spec lint), BOAR (chaos)"

  P3_GROUND_TEST_UPDATE:
    what: "Update GT-1 through GT-6 for Feb 21 Claude Code capabilities"
    additions: [agent_teams, worktree_isolation, native_auto_memory, agent_memory_frontmatter]
    owner: CTO

  P4_ORACLE_PROJECT_INSTRUCTIONS:
    what: "Draft Olya's Claude Desktop system instructions (CSO + Analyst identities)"
    owner: CTO + G

  P5_RIVER_MONITORING:
    checks: [heartbeat_updating, no_crash_loop, no_competing_session, bars_continuous_across_sessions]

  P6_HOUSEKEEPING:
    - "Rotate IB password (config.ini plaintext)"
    - "Clean Mac Mini IB daemons when powered on"

AFTERNOON/EVENING (post-M3 arrival):
  - "M3 first boot → macOS setup → SSH → tools"
  - "DGX first boot → Ubuntu verify → SSH"
  - "Both SSH-accessible from M4 Max"
  - "Model downloads overnight (wifi)"

# ───────────────────────────────────────────────────────────────
# 10. SPRINT ITEMS IDENTIFIED (not yet scheduled)
# ───────────────────────────────────────────────────────────────

HUD_TUNING:
  scope: "Wire manifest_writer.py to live data sources"
  wiring: [river_status_from_heartbeat, conditions_from_evaluator, lease_state_from_yaml]
  swiftui_changes: NONE
  effort: "Half day"

IB_ACCOUNT_QUERY:
  scope: "Poll IBKR for positions/PnL/fills → write to manifest"
  status: NEW_CAPABILITY
  dependency: "Gateway already running"
  effort: Small

HALT_SURFACE:
  scope: "HUD button + Analyst exception + HALT.signal mechanism"
  components: [hud_red_button, signal_check_pre_action, analyst_scoped_write]
  effort: Small

NETWORK_MOUNT:
  scope: "Read-only share M3 → Olya Mini"
  timing: "Thu/Fri"
  effort: "~10 min"

# ───────────────────────────────────────────────────────────────
# 11. ADVISOR TASKING
# ───────────────────────────────────────────────────────────────

FOR_OWL:
  - "M3 topology brief — confirm Cognitive Master / Computational Worker split"
  - "Sync protocol V1 (git-based)"
  - "DEXTER research pipeline structural audit"
  - "Projection schema + staleness thresholds"
  - "Section 3a model selection — validate Kimi-as-agent-core + Qwen-MoE-as-research-scale split against a8ra workload profiles"

FOR_GPT:
  - "Spot-check 10-20 of 240 registry entries for status accuracy"
  - "Spec-lint DEXTER research pipeline"
  - "River heartbeat schema — missing production monitoring fields?"
  - "Section 3a model selection — spec-lint: quantization format choices (GGUF vs EXL2 vs MLX native), RAM budget math, any missing candidates?"

FOR_BOAR:
  - "River chaos vectors: Gateway restart mid-stream, competing session despite override, contract roll/symbology change, disk full on parquet write"
  - "DEXTER isolation vectors"
  - "Section 3a model selection — chaos vectors: model OOM on M3 under concurrent agents, MoE routing instability on DGX, inference latency under swarm parallel load"

FOR_OPUS:
  - "M3 integration work (from CTO briefs)"
  - "ib_async migration scoping"
  - "git_reminder: branch workflow for pre-commit hooks, --no-verify only for hotfixes"

# ═══════════════════════════════════════════════════════════════
# END BROADCAST
# STATUS: S54 SEALED. ZERO T1/T2. RIVER LIVE. M3 ARRIVING TODAY.
# EXECUTE FROM THIS DOC. Source docs archived.
# ═══════════════════════════════════════════════════════════════
