# ═══════════════════════════════════════════════════════════════
# CTO ADDENDUM #2 — WEDNESDAY MORNING SESSION 2026-02-25
# COMPANION TO: POST-S54 BROADCAST + ADDENDUM #1 (Evening 02-24)
# FROM: G + CTO (strategic session, mobile)
# TO: Fresh CTO Session + Opus synthesis
# PURPOSE: CLI-first principle, Olya cockpit design, halt authority,
#          sprint items identified. Critical refinements to Addendum #1.
# ═══════════════════════════════════════════════════════════════

SESSION_TYPE: Strategic refinement (Olya aligned in real-time)
FORMAT: DENSE_M2M

# ───────────────────────────────────────────────────────────────
# 1. CLI-FIRST PRINCIPLE — NEW ARCHITECTURAL PRINCIPLE
# ───────────────────────────────────────────────────────────────

ORIGIN: Karpathy thesis ("Build for agents — CLIs are legacy tech agents natively use")

PRINCIPLE:
  statement: "Files > MCP. CLI > abstractions. If an agent can cat/grep/pipe it, don't wrap it."
  exception: "MCP only for genuinely external authenticated services"

STACK_REVISION:
  mcp_memory_keeper: "KILL from Phase 1 → replace with file-based memory directory"
  projection_mechanism: "File at known path, not tool call. cat, not MCP."
  river_queries: "DuckDB CLI, not MCP wrapper"
  memory_store: |
    ~/office-memory/{office}/
      index.md
      decisions/
      patterns/
      research/
    Agent searches with grep. Reads with cat. Checks freshness with stat/git log.

RATIONALE: |
  Everything working well in the stack is file-based and CLI-composable.
  The filesystem IS the API. Git IS the coordination protocol.
  Unix pipes ARE the composition layer. 50 years of hardening, text-native.
  Every MCP server is a step away from transparency.

# ───────────────────────────────────────────────────────────────
# 2. OLYA'S THREE-SURFACE COCKPIT — DESIGN LOCKED
# ───────────────────────────────────────────────────────────────

PATTERN: "G has CTO (Chat) + COO (Code). Olya has CSO (Chat) + Analyst (Code) + HUD."

SURFACES:

  HUD:
    status: BUILT (S48) — needs tuning sprint
    tech: SwiftUI app, reads manifest.json, <500ms refresh
    shows: [river_status, positions, pnl, leases, conditions_armed, dexter_status, killzone_times, health]
    kill_switch: RED HALT BUTTON (confirmation dialog → HALT.signal)
    location: "Always visible on Olya's screen"

  CSO_CHAT:
    interface: "Claude Desktop → Chat tab"
    role: "Strategy discussion, methodology validation, research direction"
    context: "System instructions with CSO identity, methodology, gate glossary"
    connectors: "MCP connectors if needed (Google Drive, etc.)"
    mode: "Conversational, async, human-paced"

  ANALYST:
    interface: "Claude Desktop → Code tab"
    role: "Live system queries, data analysis, hypothesis drafting, task submission"
    project_folder: "~/phoenix/ (with read-only mounts to M3)"
    cli_native: true
    can_do: [query_river, read_leases, run_market_state_builder, search_memory, draft_briefs, add_tasks_to_queue, trigger_HALT]
    cannot_do: [modify_py_files, git_push_to_phoenix, install_packages, restart_daemons, modify_configs]

COCKPIT_LAYOUT:
  # TV:        TradingView charts (6 pairs, familiar pro tool)
  # HUD:       System state + positions + PnL + kill switch (always on)
  # Desktop:   CSO (Chat tab) + Analyst (Code tab) side by side

OLYA_ALIGNED: true (confirmed in real-time this morning)

# ───────────────────────────────────────────────────────────────
# 3. ANALYST IDENTITY + PERMISSIONS — SPEC
# ───────────────────────────────────────────────────────────────

CLAUDE_MD_IDENTITY: |
  You are Olya's Research Analyst. You serve the Chief Strategy Officer.
  You are NOT a developer. You do NOT write code, refactor, or engineer.

  YOU CAN: query river (duckdb), read lease/conditions/evaluations,
  run market_state_builder.py, search memory, draft hypothesis briefs,
  add tasks to TASK_QUEUE.yaml, trigger HALT on Olya's instruction.

  YOU CANNOT: modify .py files, git commit/push to phoenix or dexter,
  install packages, modify configs, restart daemons.

  When asked anything outside scope: "That's an engineering task —
  flag it for G or Phoenix CTO."

PERMISSIONS_JSON:
  allow: ["Read", "Bash(duckdb*)", "Bash(python3 */market_state_builder*)", "Bash(cat*)", "Bash(grep*)", "Bash(stat*)", "Bash(git pull*)"]
  deny: ["Write", "Edit", "Bash(git push*)", "Bash(git commit*)", "Bash(rm*)", "Bash(pip*)", "Bash(npm*)"]

HALT_EXCEPTION: |
  ONE write operation permitted: echo HALT signal to phoenix-swarm/HALT.signal
  Only on Olya's explicit instruction. Always confirm before executing.

# ───────────────────────────────────────────────────────────────
# 4. NETWORK MOUNT — OPTION 1 SELECTED
# ───────────────────────────────────────────────────────────────

DECISION: "Read-only network mount from M3 Ultra to Olya's Mini over 10Gbps LAN"

MOUNTS_ON_MINI:
  /Volumes/phoenix-river/:   "Read-only mount → M3 ~/phoenix-river/ (live parquet)"
  /Volumes/phoenix-state/:   "Read-only mount → M3 ~/phoenix/state/ (leases, health, evals)"

COORDINATION: "phoenix-swarm/ via git (reports, tasks, heartbeats, projections)"
LOCAL_CLONE: "~/phoenix/cso/ on Mini (market_state_builder, evaluator scripts)"

SETUP_TIMING: "Thu/Fri alongside contractor network install"
EFFORT: "~10 min config on M3 once running"

# ───────────────────────────────────────────────────────────────
# 5. HALT AUTHORITY — CONSTITUTIONAL
# ───────────────────────────────────────────────────────────────

NEW_INVARIANTS:

  INV-OLYA-HALT-AUTHORITY:
    rule: "Olya can trigger halt_cascade at any time without G's approval"
    rationale: "Human sovereignty over capital is absolute. Any human sovereign can halt."
    scope: "HALT only. Cannot restart, reconfigure, or modify."

  INV-HALT-HUMAN-ONLY-RESTART:
    rule: "No agent, daemon, or automated process can clear a HALT state"
    mechanism: "HALT.signal removal requires G's manual action only"
    rationale: "Helpful agents restarting after halt = second disaster"

HALT_HIERARCHY:
  can_halt: [G, Olya, governance_invariant_breach_automatic]
  can_restart: [G_only]
  can_never: [any_agent, any_daemon, any_cron]

HALT_SURFACES:
  hud: "Red button → confirmation → writes HALT.signal"
  analyst: "Scoped exception to read-only policy → writes HALT.signal on Olya's command"
  matrix: "HALT message to bot → writes HALT.signal (Phase 2)"

HALT_MECHANISM: |
  Any surface writes: phoenix-swarm/HALT.signal
  Content: {"source": "OLYA", "timestamp": "ISO", "reason": "manual_kill"}
  Execution engine checks HALT.signal pre-action.
  On detect: flatten all positions, cancel pending, log, stop.
  System defaults to STOPPED. Starting requires human who understands why it stopped.

# ───────────────────────────────────────────────────────────────
# 6. OLYA REQUIREMENTS — CONFIRMED
# ───────────────────────────────────────────────────────────────

OLYA_STATED_NEEDS:
  - "In the moment knowledge of what's happening"
  - "Live positions, entry/exit points confirmed on IBKR"
  - "Current PnL on live positions"
  - "Setups forming"
  - "Kill switch for janky trades without calling G"
  - "Be all over the detail of the trading system"

TRADER_SCOPE_VS_DEV_SCOPE:
  olya_trader: [view_positions, view_pnl, view_conditions, query_data, direct_research, HALT]
  g_developer: [build, configure, deploy, restart, promote, veto]
  overlap: "Both can HALT. Only G restarts."

# ───────────────────────────────────────────────────────────────
# 7. NEW SPRINT ITEMS IDENTIFIED
# ───────────────────────────────────────────────────────────────

SPRINT_ITEMS:

  HUD_TUNING:
    scope: "Wire manifest_writer.py to live data sources"
    wiring_needed:
      river_status: "Read heartbeat file → manifest (river is live, file exists)"
      conditions: "Run CSO evaluator on cadence → manifest (evaluator exists)"
      lease_state: "Read active_leases.yaml → manifest (lease system built S47)"
    swiftui_changes: NONE (app already renders all sections)
    effort: "Half day if brief is tight"

  IB_ACCOUNT_QUERY:
    scope: "Poll IBKR for open positions, PnL, fills → write to manifest"
    status: "NEW CAPABILITY — not yet built"
    dependency: "IBKR Gateway already running on M3"
    effort: "Small — ib_insync account query is well-documented"

  HALT_SURFACE:
    scope: "HUD button + Analyst exception + HALT.signal mechanism"
    components:
      hud_button: "SwiftUI red button → confirmation → write signal file"
      signal_check: "Execution engine checks HALT.signal pre-action"
      analyst_exception: "Scoped write permission for HALT.signal only"
    effort: "Small — mechanism is simple, constitutional weight is high"

  NETWORK_MOUNT:
    scope: "Read-only SMB/NFS share from M3 to Olya's Mini"
    timing: "Thu/Fri with contractor network install"
    effort: "~10 min"

# ───────────────────────────────────────────────────────────────
# 8. ADDENDUM #1 REVISIONS
# ───────────────────────────────────────────────────────────────

REVISIONS_TO_ADDENDUM_1:

  ORACLE_ENTRY_POINT:
    was: "Claude.ai Project (Chat only)"
    now: "Claude Desktop — Chat tab (CSO) + Code tab (Analyst) + HUD (S48 SwiftUI)"
    reason: "Olya needs live system access, not just curated projections"

  MCP_MEMORY_KEEPER:
    was: "Ground-test, evaluate vs native"
    now: "KILL from Phase 1. CLI-first principle. grep > SQLite FTS at our scale."

  PROJECTION_ROLE:
    was: "Primary interface for Olya"
    now: "Summary layer (morning briefing, overnight digest). NOT primary interface."
    primary: "Live CLI queries via Analyst + HUD ambient display"

# ═══════════════════════════════════════════════════════════════
# END ADDENDUM #2
# SYNTHESIS: Broadcast + Addendum #1 + Addendum #2 = unified plan
# G to synthesise in Cursor/Opus before Wednesday sessions begin.
# ═══════════════════════════════════════════════════════════════
