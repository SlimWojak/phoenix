# PRE-M3 PREPARATION ROADMAP
# "When the beast lands, we execute — not fumble"

```yaml
document: PRE_M3_PREP
date: 2026-02-09
from: CTO
status: PLANNING_SESSION
context: M3 Ultra ETA ~1 week. G has time this week. What prep = maximum readiness?
```

---

## 1. THE LANDSCAPE

```yaml
PHOENIX_STATE:
  complete: S28-S44, S46-S48 (19 sprints, 1618 tests, 111 invariants)
  foundation: VALIDATED (S44 soak — 0 arch flaws, 0 invariant violations)
  core_rewrites: FROZEN (INV-NO-CORE-REWRITES-POST-S44)

SPRINT_QUEUE:
  S49: DMG_PACKAGING — pending (no blocker)
  S45: RESEARCH_UX — blocked (Olya CSO calibration, unblock via COE)
  S50: RUNBOOKS_CALIBRATION — pending
  S51: PRO_FLOURISHES — pending
  S52: WARBOAR_SEAL — v0.1 TARGET

PARALLEL_TRACKS:
  mission_control: v0.2 CANONICAL (design locked, ready to execute)
  dexter: OPERATIONAL (Mac Mini, extraction running)
  cso_coe: MODEL_SHIFT_ACCEPTED (recognition > recall)
  brand: a8ra OPERATIONAL (website + X auto-publishing)

HARDWARE:
  available_now: Mac Studio M4 (G's primary), Mac Mini (Dexter current)
  inbound: M3 Ultra 512GB (~1 week)

THE_QUESTION: |
  What work this week gives us maximum velocity when M3 lands?
  What can we build/prep NOW vs what's blocked on hardware?
```

---

## 2. WORK CLASSIFICATION

### CAN DO NOW (No M3 dependency)

```yaml
PREP-1_PHOENIX_SWARM_REPO:
  what: Create the phoenix-swarm/ coordination repository
  effort: 2-3 hours
  blocks: Nothing — this is pure prep
  deliverables:
    - Git repo with full structure from MC v0.2 Section 4.1
    - BROADCAST.md, TASK_QUEUE.yaml, AGENTS.md
    - heartbeats/ directory (per-office YAML files)
    - checkpoints/ directory
    - results/ + results/briefs/
    - claiming/ directory
    - hooks/ (pre-commit, validate_task_queue.py)
    - ground_tests/ directory
    - launch_office.sh (template — secrets placeholders)
    - watch_tasks.sh (task watcher script)
    - launchd plist templates
  why_now: "This is scaffolding. Zero hardware dependency. Ready to clone to M3 day one."

PREP-2_CLAUDE_MD_AUTHORING:
  what: Write CLAUDE.md files for each office
  effort: 2-3 hours
  blocks: Nothing — these are identity documents
  deliverables:
    - CLAUDE.md for CORE_CTO (Phoenix dev identity + invariants + sprint context)
    - CLAUDE.md for CSO (methodology validation identity + gate glossary)
    - CLAUDE.md for DEXTER_CTO (evidence refinery identity + extraction protocols)
    - CLAUDE.md for G_SOVEREIGN (coordination identity — if G uses Claude Code)
  why_now: |
    These are the "soul" documents. They define how each Opus instance behaves.
    Getting these RIGHT matters more than most technical prep.
    Can iterate and refine without hardware.

PREP-3_GROUND_TESTS_ON_EXISTING_HARDWARE:
  what: Run GT-1 through GT-6 on Mac Studio (don't wait for M3)
  effort: 30-60 min
  blocks: Confirms v0.2 design assumptions BEFORE M3 arrives
  deliverables:
    - GT-1: MEMORY.md persistence test
    - GT-2: --resume functionality test
    - GT-3: mcp-memory-keeper installation + integration test
    - GT-4: Hooks (on-session-end) test
    - GT-5: --headless mode test
    - GT-6: Native subagent test
    - ground_tests/RESULTS.yaml with pass/fail + notes
  why_now: |
    CRITICAL. If any of these fail, we need to know NOW — not during bootstrap.
    Failing GT-1 or GT-4 would change our checkpoint strategy.
    Running on existing hardware is identical to running on M3.
    This is the highest-value 30 minutes we can spend this week.

PREP-4_MCP_MEMORY_KEEPER_EVALUATION:
  what: Deep evaluation of mcp-memory-keeper (install, test, stress)
  effort: 1-2 hours
  blocks: Confirms our memory stack choice
  deliverables:
    - Installation docs (npm/Docker)
    - .claude/mcp_servers.json configuration template
    - Test: store → retrieve across sessions
    - Test: search capability
    - Test: behavior under load (many writes)
    - Assessment: production-ready or need alternative?
  why_now: |
    This is Layer 4 of our memory stack. If it's flaky,
    we pivot to SQLite + manual queries before M3 lands.

PREP-5_S49_DMG_PACKAGING:
  what: Execute S49 sprint (DMG build for Phoenix)
  effort: 1-2 days (sprint scope)
  blocks: No hardware dependency — this is Mac Studio work
  deliverables:
    - One-command DMG build
    - Signed DMG
    - First-run wizard
    - Config migration
  why_now: |
    S49 is next in queue, not blocked, and doesn't need M3.
    Completing S49 this week means CORE_OFFICE starts S45 immediately
    when Mission Control goes live — no sprint queue delay.
    Plus: S49 shipped = 20 sprints complete. Momentum.

PREP-6_SPRINT_ROADMAP_UPDATE:
  what: Update SPRINT_ROADMAP.md with Mission Control context
  effort: 1 hour
  blocks: Nothing
  deliverables:
    - Add Mission Control bootstrap as enabling work
    - Update parallel_tracks with v0.2 reference
    - Update invariant count (124+)
    - Add brand_identity completion status
    - Clean up current_sprint references
  why_now: "Housekeeping. Fresh advisors/instances get accurate state."

PREP-7_LAUNCHD_PLISTS:
  what: Write all launchd plist files for office management
  effort: 1 hour
  blocks: Nothing — these are config files
  deliverables:
    - com.a8ra.taskwatcher.{office}.plist (per office)
    - com.a8ra.office.{office}.plist (auto-restart daemons)
    - com.a8ra.watchdog.ollama.plist (DEXTER)
    - com.a8ra.watchdog.disk.plist (DEXTER)
    - Installation script (launchctl load/unload)
  why_now: "Config that just works on any Mac. Copy to M3, load, done."
```

### BLOCKED ON M3 ULTRA

```yaml
BLOCKED-1_DEXTER_OFFICE_SETUP:
  what: Full DEXTER office bootstrap
  needs: M3 Ultra 512GB
  includes:
    - Ollama + model pulls (Kimi 2.5, Qwen3-72B, Gemma3-27B)
    - phoenix-synthetic/ clone + test suite verification
    - IBKR synthetic paper account connection
    - --headless 24/7 configuration
    - launchd auto-restart setup
  prep_we_can_do: Everything else in PREP-1 through PREP-7

BLOCKED-2_FULL_MULTI_OFFICE_INTEGRATION:
  what: All offices running, coordinating via phoenix-swarm/
  needs: M3 Ultra (for DEXTER) + bootstrap execution
  prep_we_can_do: |
    Repo ready (PREP-1), identities ready (PREP-2),
    ground tests passed (PREP-3), all configs ready (PREP-7).
    Bootstrap becomes: clone repos, load plists, launch.
    Target: 2-3 hours instead of 4.
```

### COULD DO NOW (Lower Priority)

```yaml
COULD-1_HOOKS_JSON_TEMPLATES:
  what: Write .claude/hooks.json for each office
  effort: 1 hour
  value: Medium — hooks config ready to drop in

COULD-2_VALIDATE_TASK_QUEUE_SCRIPT:
  what: Write the validate_task_queue.py YAML linter
  effort: 1-2 hours
  value: Medium — INV-STRICT-COMMIT enforcement

COULD-3_ALERT_TAXONOMY_IMPLEMENTATION:
  what: Telegram bot setup for WARN/ALERT/HALT notifications
  effort: 2-3 hours
  value: Low for Phase 1 (log files sufficient initially)

COULD-4_ENDGAME_VISION_UPDATE:
  what: Update ENDGAME_VISION with GPT's Dexter invariants + MC v0.2 link
  effort: 1 hour
  value: Low — housekeeping
```

---

## 3. RECOMMENDED SEQUENCE

```yaml
THIS_WEEK_PRIORITY_ORDER:

  DAY_1 (highest value):
    morning: PREP-3 (Ground Tests) — 30-60 min
      why_first: "Validates EVERYTHING in v0.2. If something fails, we adapt now."
    afternoon: PREP-4 (mcp-memory-keeper eval) — 1-2 hours
      why_second: "Confirms memory stack. Layer 4 proven or pivoted."

  DAY_2:
    PREP-1 (phoenix-swarm/ repo) — 2-3 hours
      "The skeleton. Ready to clone to any Mac."
    PREP-2 (CLAUDE.md authoring) — 2-3 hours
      "The soul. Each office knows who it is."

  DAY_3:
    PREP-5 (S49 DMG Packaging) — begin sprint
      "Ship product. Clear the queue for CORE_OFFICE."

  DAY_4-5:
    PREP-5 continued (S49 completion)
    PREP-7 (launchd plists) — 1 hour
    PREP-6 (roadmap update) — 1 hour
    COULD items if time permits

  M3_ARRIVAL_DAY:
    Hour 0-1: Unbox, setup macOS, install toolchain
    Hour 1-2: Clone repos, pull models, configure secrets
    Hour 2-3: Run ground tests on M3 (verify same results as Mac Studio)
    Hour 3-4: Full bootstrap — DEXTER headless + CORE first task cycle
    Hour 4+: Begin real work — S45 CORE, extraction DEXTER
```

---

## 4. DECISION: S49 vs MISSION CONTROL PREP

```yaml
THE_TENSION:
  option_a: "Focus entirely on Mission Control prep this week"
  option_b: "Ship S49 (DMG Packaging) AND do MC prep"
  option_c: "S49 becomes CORE_OFFICE's first Mission Control task"

CTO_ANALYSIS:
  option_a:
    pro: "100% focused on coordination infrastructure"
    con: "S49 still sitting in queue when MC goes live. CORE_OFFICE starts with backlog."

  option_b:
    pro: "S49 shipped + MC prep done. Clean slate when M3 lands."
    con: "Split focus. Two things in one week."

  option_c:
    pro: "Real sprint = real integration test for Mission Control."
    con: "Risky first task. Debugging sprint + coordination simultaneously."

CTO_LEAN: OPTION B
  rationale: |
    Ground tests + mcp eval + repo scaffolding = 1.5 days.
    S49 = 2-3 days (it's a packaging sprint, not architecture).
    Both fit in a week. Neither is heavy.

    When M3 lands: S49 done, MC scaffold ready, CORE starts S45 immediately.
    That's the cleanest state we can achieve.

DECISION_NEEDED: G to confirm
```

---

## 5. EXIT STATE (End of This Week)

```yaml
IF_PLAN_EXECUTES:
  ground_tests: PASSED (v0.2 assumptions validated)
  mcp_memory_keeper: EVALUATED (production-ready or pivoted)
  phoenix_swarm_repo: READY (skeleton + configs + hooks)
  claude_md_files: AUTHORED (all 4 office identities)
  launchd_plists: WRITTEN (all daemons + watchers)
  s49: COMPLETE (DMG packaging shipped — sprint 20!)
  sprint_roadmap: UPDATED (current state accurate)

  ready_for_m3: |
    Clone repos → load plists → pull models → launch.
    2-3 hour bootstrap (down from 4hr — prep absorbed the scaffold hours).
    CORE_OFFICE starts S45 same day.
    DEXTER starts extraction that night.
    Mission Control OPERATIONAL within 24h of M3 arrival.
```

---

*"Prep is the sprint nobody sees but everyone benefits from."*

**OINK OINK.** 🐗🔥
