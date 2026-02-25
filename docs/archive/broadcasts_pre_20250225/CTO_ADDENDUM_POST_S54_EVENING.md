# ═══════════════════════════════════════════════════════════════
# CTO ADDENDUM — EVENING SESSION 2026-02-24
# COMPANION TO: POST-S54 TUESDAY CLOSEOUT BROADCAST
# FROM: G + CTO (informal strategic session)
# TO: Fresh CTO Session (Wednesday morning)
# PURPOSE: Hardware topology, office architecture, swarm wiring,
#          gap identification. Execute from this + broadcast.
# ═══════════════════════════════════════════════════════════════

SESSION_TYPE: Strategic orientation (not sprint execution)
FORMAT: DENSE_M2M

# ───────────────────────────────────────────────────────────────
# 1. HARDWARE TOPOLOGY — LOCKED
# ───────────────────────────────────────────────────────────────

FLEET:
  sovereign_tier:  # Headless, rack-mounted, UPS-backed, 24/7, no keyboard
    M3_ULTRA:
      role: "The Brain — canonical repo, River/Gateway, Matrix/Conduit, local model serving"
      ram: 512GB
      storage: 4TB
      models: "Kimi 2.5, Qwen3-72B (only machine with RAM for 70B+)"
      status: ARRIVING_WEDNESDAY (DHL, likely afternoon/evening)
      hostname: TBD (decide before first boot)

    DGX_SPARK:
      role: "Research Muscle — DEXTER workloads, GPU inference, heavy compute"
      status: UNWRAPPED_NOT_BOOTED
      os: Ubuntu (headless from get-go, mDNS/DHCP discovery)
      hostname: TBD

  interactive_tier:  # Where humans sit
    M4_MAX_STUDIO:
      role: "G's daily driver — Cursor, Claude Code, terminals, browsers"
      ram: 64GB
      decision: "KEEP AS WORKSTATION. Do NOT rack-mount."
      rationale: "Separation of concerns — daily driver reboot ≠ system outage"

    MAC_MINI_PRO_24GB:
      role: "PHOENIX office node / flexible spare"
      options: [phoenix_entry_point, monitoring_dashboard, hot_spare]

    MAC_MINI_STOCK:
      role: "ORACLE node — Olya's office"
      location: "Olya's office (different part of house, same network)"
      usage: "Sits alongside MacBook. No migration pressure."

    REMAINING_MINIS:
      role: "Spares, future office nodes"

NETWORK:
  internal: "10Gbps — TP-Link TL-SX1008, Cat6a, SolidSteel rack"
  external: "2000/1000 Mbps (fastest available)"
  house: "UniFi Pro XG 10-Port for household, no throttle"
  office_entry: "Being installed Thu/Fri by trusted contractor"
  ups: "APC pure sine wave, floor-mounted adjacent to rack"
  current: "WiFi only until contractor wires Thu/Fri"

SETUP_SEQUENCE:
  wednesday_am: "Strategic planning, doc updates, advisor tasking (M3 not yet arrived)"
  wednesday_pm: "M3 arrives → temporary monitor hookup → first boot → macOS setup → SSH enable → hostname → Homebrew/git/Claude Code"
  wednesday_pm_2: "DGX first boot → same drill → Ubuntu verify → SSH → hostname"
  wednesday_eve: "Both machines SSH-accessible from M4 Max desk. Start model downloads (overnight on wifi)."
  thu_fri: "Contractor wires office. Machines go on rack. 10Gbps verified (iperf3). Static IPs. UPS connected. Sovereign tier physically operational."

KEY_PRINCIPLE: |
  G's M4 Max is the cockpit. Rack machines are engines.
  Configure headless machines FROM M4 Max via SSH.
  Temporary monitor for first boot only — then never again.

# ───────────────────────────────────────────────────────────────
# 2. OFFICE ARCHITECTURE — REFINED
# ───────────────────────────────────────────────────────────────

CONCEPT_PROJECTION:
  definition: |
    Every office operates on a PROJECTION of system state.
    Projections are read-only, timestamped, refreshed at cadences
    appropriate to the office's role. No office assumes its projection
    is current — it verifies freshness and surfaces staleness.
  origin: "NEX failure analysis — confident-but-wrong is worse than uncertain"
  constitutional: "INV-PROJECTION-PROVENANCE: No data presented without source + timestamp"

PROJECTIONS_BY_OFFICE:
  ORACLE:
    contains: [river_status, active_leases, strategy_state, recent_decisions, trade_rationales]
    refresh: "Human-paced (morning, midday, on-demand)"
    consumer: "Olya + her Claude"
    format: "CSO_BRIEFING.md — curated, provenance-stamped"
  DEXTER:
    contains: [invariant_registry, research_queue, hypothesis_status, river_data_access]
    refresh: "Near-continuous (before each research task)"
    consumer: "DEXTER CTO agent"
  PHOENIX:
    contains: [sprint_state, test_results, risk_registry, codebase_health]
    refresh: "Per-session (git pull)"
    consumer: "Phoenix CTO agent"
  G_SOVEREIGN:
    contains: "Everything — full system view"
    refresh: "On-demand"

CONTEXT_BEADS_PRINCIPLE: |
  There is no such thing as "context" in the swarm.
  There are only context beads with provenance.
  Anything without provenance is untrusted by default.

  context_bead:
    key: "{identifier}"
    value: "{data}"
    source: "{origin_system}"
    updated_at: "{ISO_timestamp}"
    max_age_seconds: "{staleness_threshold}"
    stale_action: "REFUSE | WARN | CONTINUE"

  Market data stale >5min → REFUSE_TO_QUOTE
  Sprint state stale >24h → WARN_AND_CONTINUE
  Staleness tolerance is domain-specific, mechanism is universal.

# ───────────────────────────────────────────────────────────────
# 3. OLYA / ORACLE OFFICE — DESIGN LOCKED
# ───────────────────────────────────────────────────────────────

ORACLE_ENTRY_POINT: "Claude.ai Project OR Claude Desktop (NOT Claude Code CLI)"
  rationale: |
    Olya commands, doesn't compute.
    She needs a chat interface, not a terminal.
    Project gives: custom system instructions, file uploads,
    built-in memory, MCP connectors if needed.

ORACLE_CONTEXT:
  system_instructions: "CSO identity, methodology context, gate glossary, provenance rules"
  reference_docs: "conditions.yaml, Mirror Reports, ICT methodology notes"
  projection: "CSO_BRIEFING.md (auto-refreshed, timestamped)"

ORACLE_COCKPIT_FEEL:
  problem: "Isolation from system = consultant, not commander"
  solution: "Projection gives read view. Direction authority gives write authority (into DEXTER task queue)."
  freshness: "30min stale = fine for her cadence. 3 days stale = NEX failure."
  trust_chain: |
    1. Every number carries provenance + timestamp
    2. She can ask "why" and get decision trace
    3. She can say "no" and it matters (rejection → system correction)

BRIDGE_TO_SWARM: "G is the sovereign bridge. Olya's validated outputs flow through G into git/system."

OLYA_TO_DEXTER: |
  Olya has WRITE authority into DEXTER's research queue.
  Mechanism: hypothesis brief → task queue (via G or direct).
  This is the path from "domain expert" to "research director."

# ───────────────────────────────────────────────────────────────
# 4. CLAUDE CODE FEATURES — SWEEP (as of 2026-02-24)
# ───────────────────────────────────────────────────────────────

NEW_SINCE_MC_v0_2: # Mission Control v0.2 locked 2026-02-09

  AGENT_TEAMS:
    what: "Native multi-agent coordination in Claude Code"
    enable: "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1"
    pattern: "Lead + teammates, shared task list, peer messaging, worktree isolation"
    relevance: "Intra-machine parallelism for DEXTER research workers"
    status: EXPERIMENTAL (known limitations: session resume, shutdown)
    action: "Ground-test on M3 Wednesday"

  AUTOMATIC_SESSION_MEMORY:
    what: "Claude Code auto-writes session summaries to ~/.claude/projects/<hash>/memory/MEMORY.md"
    behavior: "Recalled X memories on start, Wrote X memories periodically"
    limit: "200-line hard cap on auto-load"
    risk: "Parallel memory system may conflict with deliberate MEMORY.md"
    action: "SET CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 initially. Evaluate later."

  GIT_WORKTREE_ISOLATION:
    what: "claude --worktree gives each session isolated git worktree"
    relevance: "Solves concurrent mutation seam (Seam 1). Subagents get isolation: worktree in frontmatter."
    action: "Ground-test Wednesday"

  CLAUDE_AI_MCP_IN_CODE:
    what: "MCP connectors configured at claude.ai/settings/connectors auto-available in Claude Code CLI"
    relevance: "Low priority for Phase 1. Nice for future ORACLE integration."

  AGENT_MEMORY_FRONTMATTER:
    what: "Custom agents support memory field with scopes: user, project, local"
    relevance: "Per-office agent memory that persists correctly per scope"
    action: "Evaluate during ground testing"

  MEMORY_LEAK_FIXES:
    what: "6 leaks fixed Feb 19-21 (task state, LSP diagnostics, agent teams GC)"
    relevance: "CRITICAL for 24/7 headless on M3/DGX"

  PRECOMPACT_HOOKS:
    what: "Community pattern — hook fires before context compaction, spawns fresh Claude to write handover summary"
    relevance: "Potential upgrade to session continuity for long DEXTER runs"
    action: "Phase 2 evaluation"

STACK_IMPACT:
  mcp_memory_keeper: "MAY be replaceable by native auto-memory + agent memory. Ground-test."
  manual_memory_md: "KEEP — disable auto-memory to avoid collision"
  subagent_model: "Agent Teams may replace for DEXTER parallelism. Ground-test."
  tmux_hive_ops: "CONFIRMED KILL (already deprecated in v0.2)"

REPOPROMPT:
  discovered: "Post MC v0.2 (mid-Feb)"
  role: "Cartridge builder — generates context snapshots from repo state"
  usage: "Cron to rebuild projections (STATE.yaml, CSO_BRIEFING.md, office cartridges)"
  integration: "Complementary to all above — generates content, Claude Code consumes it"

# ───────────────────────────────────────────────────────────────
# 5. DEXTER RESEARCH PIPELINE — GAP IDENTIFIED
# ───────────────────────────────────────────────────────────────

GAP_STATUS: SPEC_NEEDED

WHAT_EXISTS:
  river: "LIVE — 11.8M bars, 6 pairs, RiverReader with DuckDB (Phoenix module)"
  extraction: "789 Genesis beads, knowledge pipeline operational"
  synthetic_river_py: "Deterministic fake data for UNIT TESTS ONLY (not research)"
  office_spec: "References backtests, Monte Carlo, hypothesis testing"

WHAT_DOES_NOT_EXIST:
  gap_1_river_access: |
    DEXTER cannot read the river. River lives in Phoenix (~/phoenix-river/).
    DEXTER runs in ~/dexter/. No bridge, no read access, no copy mechanism.
  gap_2_research_loop: |
    "CSO submits hypothesis → DEXTER executes → CSO reviews evidence"
    is stated but not specified. No mechanism for: how Olya formulates questions,
    how they reach DEXTER, what output format, how she reviews.
  gap_3_synthetic_confusion: |
    "Synthetic river" means two things:
    a) synthetic_river.py = fake data for unit tests (exists, not research)
    b) Historical replay of real river for backtests (does not exist)

PROPOSED_SPEC:
  name: DEXTER_RESEARCH_PIPELINE
  components:
    river_access: "Read-only mount or copy of phoenix-river/ parquet data"
    direction_flow: "Olya → hypothesis brief → task queue → DEXTER → evidence bundle → projection → Olya reviews"
    research_types: [backtest, hypothesis_test, pattern_scan, monte_carlo]
    output: "Evidence bundles with provenance → CSO_BRIEFING projection"
    invariant: "INV-DEXTER-RIVER-READONLY: DEXTER never writes to production river"

  action: "Draft spec Wednesday morning. OWL audit. Build as sprint when spec hardened."

# ───────────────────────────────────────────────────────────────
# 6. WEDNESDAY MORNING PLAN (pre-M3 arrival)
# ───────────────────────────────────────────────────────────────

WEDNESDAY_AM_PRIORITIES:

  P1_MANIFEST_UPDATE:
    what: "Add projection concept + DEXTER research pipeline gap to system manifest"
    owner: CTO
    deliverable: "Updated a8ra_SYSTEM_MANIFEST sections"

  P2_DEXTER_RESEARCH_SPEC:
    what: "Draft DEXTER_RESEARCH_PIPELINE spec v0.1"
    owner: CTO
    advisor_input: "OWL (structure), GPT (spec lint), BOAR (chaos vectors)"

  P3_GROUND_TEST_UPDATE:
    what: "Update GT-1 through GT-6 for Feb 21 Claude Code capabilities"
    additions: [agent_teams, worktree_isolation, native_auto_memory, agent_memory_frontmatter]
    owner: CTO

  P4_ORACLE_PROJECT_INSTRUCTIONS:
    what: "Draft Olya's Claude Project system instructions"
    owner: CTO + G
    deliverable: "Ready to paste into Claude.ai Project"

  P5_ADVISOR_TASKING:
    owl: "M3 topology brief + DEXTER research pipeline structural audit"
    gpt: "Spec-lint research pipeline + projection schema"
    boar: "River chaos vectors (from broadcast) + DEXTER isolation vectors"

# ───────────────────────────────────────────────────────────────
# 7. KEY PRINCIPLES ESTABLISHED THIS SESSION
# ───────────────────────────────────────────────────────────────

PRINCIPLES:

  PROJECTION_NOT_PARTICIPATION:
    statement: "Offices consume projections of state, not raw system access"
    corollary: "Every projection is timestamped, sourced, with staleness thresholds"

  OBSERVABLE_DEGRADATION:
    statement: "Sufficient fidelity with observable degradation > assumed full fidelity"
    origin: "NEX failure — confident-but-wrong destroyed trust"

  BUILD_OBSERVE_HARDEN:
    statement: "V1 is simple. Friction points announce themselves. Harden at observed seams."
    corollary: "Don't pre-engineer the perfect context system. Run it, watch it, fix what breaks."

  SEPARATION_OF_TIERS:
    statement: "Sovereign tier (headless, 24/7) never shares hardware with interactive tier"
    corollary: "G's reboot ≠ system outage"

  OLYA_COMMANDS_NOT_COMPUTES:
    statement: "ORACLE is chat-first, not terminal-first. Claude.ai Project, not Claude Code."
    corollary: "Heavy work pushed to DEXTER. Olya reviews evidence, not raw data."

  CODE_IS_FAST_DESIGN_IS_HARD:
    statement: "Clear brief + locked scope = 20 min build. The thinking is the work."
    corollary: "Wednesday morning = spec. Wednesday evening = execute."

# ═══════════════════════════════════════════════════════════════
# END ADDENDUM
# COMPANION TO: POST-S54 TUESDAY CLOSEOUT BROADCAST
# FRESH CTO: Read broadcast FIRST, then this addendum.
# WEDNESDAY: Specs in morning, hardware in afternoon, build in evening.
# ═══════════════════════════════════════════════════════════════
