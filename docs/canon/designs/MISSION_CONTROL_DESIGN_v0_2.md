# MISSION CONTROL DESIGN v0.2

```yaml
document: MISSION_CONTROL_DESIGN
version: 0.2
date: 2026-02-09
status: CANONICAL | ALL_DECISIONS_LOCKED
brand: a8ra (Phoenix is internal codename)
source: G + CTO + OWL + GPT + BOAR synthesis (2026-02-06 to 2026-02-09)
purpose: Complete design spec for multi-office Opus-led swarm architecture
pattern: Follows CARTRIDGE_AND_LEASE_DESIGN paradigm (measure twice, cut once)
changelog_from_v0.1:
  - Checkpoint mechanism: hooks + --max-turns + --resume (replaces aspirational "Opus monitors")
  - Memory stack: 5-layer native (replaces Letta dependency)
  - Tool stack: 50% fewer deps, 100% more Claude-native
  - Subagents: Native Claude Code (deprecates tmux HIVE_OPS)
  - Heartbeats: File-per-office (fixes merge conflict bug)
  - Task claiming: .claiming lock pattern (fixes race condition)
  - Bootstrap: 4hr hybrid + 30min ground test prefix
  - Invariants: 13 new (124+ total system-wide)
  - 13 decision points: ALL LOCKED
  - New sections: Memory Stack, Session Lifecycle, 3am Resilience, Ground Tests
```

---

## 1. EXECUTIVE SUMMARY

```yaml
THE_TRANSFORMATION:
  from: |
    - G routes every task between Claude instances
    - Sessions die, 15+ min rehydration per context death
    - Human as bottleneck coordinator
    - Single-threaded sprint execution

  to: |
    - Opus-led offices operate autonomously
    - Hooks + MEMORY.md + --resume = session death is a non-event
    - Human as sovereign reviewer at gates
    - Parallel office execution via shared board
    - "Seed vision before sleep, wake to integrated products"

ENABLING_FACTORS:
  opus_4.6: "Plans more carefully, sustains agentic tasks longer, catches own mistakes"
  context_1m: "Entire codebase + history in context (beta)"
  claude_code_native: |
    Hooks system, --headless, --resume, --max-turns, native subagents,
    MCP memory servers, CLAUDE.md + MEMORY.md persistence.
    Feb 2026 Claude Code is MORE capable than v0.1 assumed.
  infrastructure: "Phoenix S28-S47 proven, governance patterns operational"
  dexter: "Extraction refinery operational, 981 signatures, Mirror Report ready"

OUTCOME:
  v0.1_acceleration: "2-3 weeks (parallel) vs 3-4 weeks (sequential)"
  operational_model: "Offices compound 24/7 while humans sleep"
  sovereignty: "Human frames, machine computes, human approves"

KEY_V0.2_INSIGHT: |
  Claude Code's native capabilities (hooks, --resume, MEMORY.md, MCP, subagents)
  eliminate most external tool dependencies. The stack is simpler AND more robust
  than v0.1 designed for. Claude-native > bolted-on.
```

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Office Model

```yaml
CORE_PRINCIPLE: |
  "Opus leader + native subagents + MCP memory per office"
  Each office is self-sufficient, coordinates via shared git board.
  Human sovereign per office (G, Olya) reviews outcomes, not tasks.

OFFICES:

  G_SOVEREIGN:
    role: Mission Control hub
    leader: G (human)
    function: Broadcast, veto, synthesis, secrets distribution
    authority: SUPREME (all offices report to G)

  CORE_OFFICE:
    role: Phoenix development
    leader: Phoenix CTO (Opus 4.6)
    function: S45-S52 execution, codebase integrity, sprint delivery
    sovereign: G (human veto at sprint gates)

  CSO_OFFICE:
    role: Methodology validation
    leader: CSO (Opus 4.6)
    function: CLAIM→FACT promotion, gate calibration, conditions.yaml
    sovereign: Olya (domain authority), G (visibility)

  DEXTER_OFFICE:
    role: R&D / Evidence refinery
    leader: Dexter CTO (Opus 4.6)
    function: Extraction, synthetic Phoenix, hypothesis testing, 24/7 headless
    sovereign: G (promotion gate to core)
    mode: HEADLESS_24_7
```

### 2.2 Communication Topology

```yaml
INTER_OFFICE_COMMS:
  medium: Shared git repository (phoenix-swarm/)
  pattern: Async file-based messaging
  routing: Task queue + @mentions (no human routing needed)
  latency: ~2min (acceptable — async is feature, not bug)

  message_types:
    BROADCAST: G → all offices (strategic directive)
    REQUEST: Office → Office ("@DEXTER test hypothesis X")
    RESULT: Office → Board (completed work)
    ALERT: Any → Human sovereigns (requires attention)

INTRA_OFFICE_COMMS:
  pattern: Opus leader spawns native Claude Code subagents
  coordination: Leader manages, subagents disposable with persistent memory
  state: Leader holds context via MEMORY.md + mcp-memory-keeper

ADVISOR_ACCESS:
  pattern: Any office can summon via API
  advisors:
    GROK: xAI API (chaos/frontier intelligence)
    PERPLEXITY: Perplexity API (research/fact-checking)
    OWL: Gemini API (structural audit)
    GPT: OpenAI API (spec lint)
  results: Posted to shared board with attribution
```

### 2.3 Sovereignty Preservation

```yaml
INVARIANTS:

  INV-SOVEREIGN-1:
    rule: "G veto on all BROADCAST.md directives"
    mechanism: No task enters TASK_QUEUE without G's commit

  INV-NO-AUTO-PROMOTE:
    rule: "CLAIM→FACT requires human gate"
    mechanism: Olya validates, G approves promotion

  INV-HALT-PROPAGATION:
    rule: "Halt from any sovereign propagates to all offices"
    mechanism: BROADCAST.md HALT entry → all offices check on wake

  INV-CAPITAL-GATE:
    rule: "No live execution without human approval"
    mechanism: T2 gates preserved, DEXTER is paper-only
```

---

## 3. OFFICE SPECIFICATIONS

### 3.1 G_SOVEREIGN (Mission Control)

```yaml
HARDWARE:
  recommended: Mac Mini M4 Pro
  ram: 32GB unified memory
  storage: 512GB SSD
  rationale: "Coordination is lightweight, always-on"

REPOS:
  primary: phoenix-swarm/ (coordination hub)
  read_access: phoenix/, dexter/

ACCOUNTS:
  claude: Max x5 (sufficient for coordination)
  credentials: Master keychain (distributes to offices)

SOFTWARE:
  - Claude Desktop/Web (strategic sessions)
  - Git
  - Task watcher daemon (launchd, 2min interval)
  - Telegram/Matrix (optional — mobile alerts)

LOCAL_MODELS: Not needed
UPTIME: Always-on (Mission Control)

UNIQUE_CAPABILITIES:
  - Broadcast author (only G writes to BROADCAST.md)
  - Veto authority
  - Secrets distribution (Keychain master)
  - Cross-office visibility
```

### 3.2 CORE_OFFICE (Phoenix Development)

```yaml
HARDWARE:
  recommended: Mac Studio M4 Max
  ram: 64GB+ unified memory
  storage: 1TB SSD
  rationale: "Fastest single-thread for compile/test, bursty workloads"

REPOS:
  primary: phoenix/ (codebase)
  coordination: phoenix-swarm/

ACCOUNTS:
  claude: Max x20 (heavy CTO sessions)
  ibkr: Paper account (dev/test)
  github: Repo access

SOFTWARE:
  - Claude Code CLI (interactive mode)
  - Python 3.11+, pytest + full dev deps
  - Git + pre-commit hooks
  - mcp-memory-keeper (MCP server)
  - launchd (session management)

CLAUDE_CODE_CONFIG:
  flags: "--max-turns=80 --project ~/phoenix/"
  mcp_servers: [mcp-memory-keeper]
  files:
    CLAUDE.md: Office identity, invariants, repo map, sprint context
    MEMORY.md: Current task, progress, decisions (auto-persists 200 lines)

LOCAL_MODELS: Optional (API-primary for dev quality)

SECRETS:
  - ANTHROPIC_API_KEY
  - IBKR_DEV_CREDENTIALS

UPTIME: Human-paced (business hours+)

WORKLOADS:
  - Code development (S45-S52)
  - Test suite execution (1620+ tests)
  - Integration work
  - Sprint deliverables
```

### 3.3 CSO_OFFICE (Methodology Validation)

```yaml
HARDWARE:
  recommended: Mac Mini (M4 or M2 sufficient)
  ram: 16-32GB unified memory
  storage: 256-512GB SSD
  rationale: "Review-heavy, not compute-heavy"

REPOS:
  primary: phoenix/ (cso/ modules, conditions.yaml)
  coordination: phoenix-swarm/

ACCOUNTS:
  claude: Max x5 (Opus for articulation assistance)
  ibkr: Not needed

SOFTWARE:
  - Claude Code CLI (interactive mode)
  - Git
  - Light Python (review scripts)
  - mcp-memory-keeper (MCP server)

CLAUDE_CODE_CONFIG:
  flags: "--max-turns=60 --project ~/phoenix/"
  mcp_servers: [mcp-memory-keeper]
  files:
    CLAUDE.md: CSO identity, methodology context, gate glossary
    MEMORY.md: Review state, pending promotions, Olya directives

LOCAL_MODELS: Not needed

SECRETS:
  - ANTHROPIC_API_KEY

UPTIME: Olya's schedule

WORKLOADS:
  - Mirror Report review
  - Hypothesis drafting (text, not compute)
  - Promotion/rejection workflows
  - conditions.yaml editing

CRITICAL_INSIGHT: |
  "Olya commands, doesn't compute"
  Heavy compute pushed to DEXTER.
  CSO submits hypothesis → DEXTER executes → CSO reviews evidence.
```

### 3.4 DEXTER_OFFICE (R&D / Evidence Refinery)

```yaml
HARDWARE:
  recommended: M3 Ultra Mac Studio
  ram: 512GB unified memory
  storage: 2TB+ SSD (corpus + synthetic data)
  rationale: |
    - 512GB RAM = run 70B+ local models comfortably
    - 24/7 headless capability via Claude Code --headless
    - Extraction + backtesting + Monte Carlo = memory hungry
    - Synthetic Phoenix + full corpus in memory

REPOS:
  primary: dexter/ (extraction system)
  synthetic: phoenix-synthetic/ (full Phoenix clone for R&D)
  coordination: phoenix-swarm/

ACCOUNTS:
  claude: Max x20 (Opus for high-judgment tasks)
  openrouter: DeepSeek, Gemini for volume
  perplexity: Research enrichment
  ibkr: Paper SEPARATE account (synthetic, not dev)

SOFTWARE:
  - Claude Code CLI (--headless for 24/7)
  - ollama / llama.cpp (local model runtime)
  - Python 3.11+ (extraction pipeline)
  - mcp-memory-keeper (MCP server)
  - launchd (auto-restart daemon)
  - Git
  - n8n (OPTIONAL — pipeline monitoring dashboard only)

CLAUDE_CODE_CONFIG:
  flags: "--headless --max-turns=100 --project ~/dexter/"
  mcp_servers: [mcp-memory-keeper]
  files:
    CLAUDE.md: DEXTER identity, extraction protocols, evidence standards
    MEMORY.md: Current batch, extraction progress, hypothesis queue

LOCAL_MODELS:
  primary_reasoning: Kimi 2.5
  code_extraction: Qwen3-72B
  classification: Gemma3-27B

SECRETS:
  - ANTHROPIC_API_KEY
  - OPENROUTER_API_KEY
  - PERPLEXITY_API_KEY
  - IBKR_SYNTHETIC_CREDENTIALS

UPTIME: 24/7 headless

WORKLOADS:
  - Extraction pipeline (24/7)
  - Backtests (Olya's hypothesis tests)
  - Monte Carlo simulations (memory intensive)
  - Evidence bundle generation
  - Mirror Report generation

SOVEREIGN_POSTURE: |
  DEXTER can operate WITHOUT any external API (local models + local compute).
  Enhanced BY Claude API for high-judgment tasks.
  Result: "24/7 refinery that degrades gracefully if APIs unavailable"
```

---

## 4. COORDINATION LAYER (phoenix-swarm/)

### 4.1 Repository Structure

```yaml
phoenix-swarm/
  BROADCAST.md              # G directives (only G writes)
  TASK_QUEUE.yaml           # Kanban: pending/claimed/done/blocked
  AGENTS.md                 # Office identities + contracts
  heartbeats/               # Per-office status (zero merge conflicts)
    CORE_CTO.yaml
    CSO.yaml
    DEXTER_CTO.yaml
    G_SOVEREIGN.yaml
  checkpoints/              # Structured state snapshots
    CORE_CTO.yaml
    CSO.yaml
    DEXTER_CTO.yaml
  results/
    T001_DEXTER.md          # Task outputs (beads)
    T002_CORE.md
    briefs/
      T001_BRIEF.md         # Task briefs
  hooks/
    pre-commit              # Invariant linter + secret scanner
    validate_task_queue.py  # YAML schema + claim validation
```

### 4.2 TASK_QUEUE.yaml Schema

```yaml
# TASK_QUEUE.yaml

pending:
  - id: T001
    from: G
    to: DEXTER_CTO
    mission: "Implement taxonomy-aware extraction"
    brief_path: results/briefs/T001_BRIEF.md
    priority: P1
    created: 2026-02-06T12:00Z

claimed:
  - id: T002
    from: G
    to: CORE_CTO
    mission: "Execute S45 Research UX"
    claimed_by: CORE_CTO
    claimed_at: 2026-02-06T12:05Z

done:
  - id: T003
    mission: "S47 Lease Implementation"
    completed_by: CORE_CTO
    completed_at: 2026-02-05T18:00Z
    result_path: results/T003_CORE.md
    result_branch: core/T003-lease

blocked:
  - id: T004
    mission: "Setup Phoenix replica"
    blocked_by: DEXTER_CTO
    blocked_at: 2026-02-06T10:00Z
    blocker: "Need IBKR paper credentials from G"
```

### 4.3 Task Claiming Protocol

```yaml
ATOMIC_CLAIM_PATTERN:
  purpose: "Prevent race conditions on task claims"
  source: OWL structural audit

  protocol:
    1: Office pulls latest (git pull)
    2: Office checks for .claiming file: phoenix-swarm/claiming/T001.lock
    3: If no lock → create lock file with office name + timestamp
    4: git add + commit + push the lock file
    5: If push succeeds → claim is valid, update TASK_QUEUE.yaml
    6: If push fails (conflict) → another office claimed first → back off
    7: On task complete → remove lock file

  lock_format:
    file: claiming/T{id}.lock
    content: |
      claimed_by: CORE_CTO
      claimed_at: 2026-02-06T12:05Z

  janitor:
    cron: "Every 30 min, purge .lock files older than 2 hours with no matching claimed task"
    prevents: Stale locks from crashed sessions

INVARIANT: "INV-ATOMIC-CLAIM: No agent writes task state without holding filesystem lock"
```

### 4.4 Heartbeat Format (File-Per-Office)

```yaml
# heartbeats/CORE_CTO.yaml
# SINGLE WRITER — only CORE_CTO writes this file

office: CORE_CTO
updated_at: 2026-02-06T14:30Z
status: WORKING          # WORKING | IDLE | BLOCKED | CHECKPOINTING | OFFLINE
task_id: T002
task_mission: "S45 Research UX"
progress: "Gate 1-3 complete, working on Gate 4"
context_pct: 45           # estimated if available
blockers: []
next_checkpoint: "After Gate 4 tests pass"

# History (last 5 entries, older auto-pruned)
history:
  - at: 2026-02-06T14:00Z
    status: WORKING
    note: "Gate 3 tests green (14/14)"
  - at: 2026-02-06T13:00Z
    status: WORKING
    note: "Gate 2 complete, starting Gate 3"
```

```yaml
AGGREGATION:
  pattern: "G or any office reads all heartbeats/ files for overview"
  script: |
    # Quick status check
    for f in heartbeats/*.yaml; do
      echo "$(yq '.office' $f): $(yq '.status' $f) — $(yq '.progress' $f)"
    done

  output: |
    CORE_CTO: WORKING — Gate 1-3 complete, working on Gate 4
    CSO: IDLE — Waiting for Mirror Report from DEXTER
    DEXTER_CTO: WORKING — Taxonomy extraction batch 3/7

INVARIANT: "INV-SINGLE-WRITER-LOG: Each office owns exactly one heartbeat file"
```

### 4.5 Task Watcher Daemon

```yaml
PURPOSE: "Detect new tasks, wake offices, monitor health"

IMPLEMENTATION:
  type: launchd plist (macOS native)
  interval: 120 seconds (2 minutes — explicit cadence)
  script: watch_tasks.sh

WATCH_SCRIPT: |
  #!/bin/bash
  set -euo pipefail
  cd ~/phoenix-swarm

  # Robust git pull with retry
  git pull -q || { sleep 5 && git pull -q; } || echo "$(date): git pull failed" >> ~/logs/watcher.log

  # Check for tasks addressed to this office
  OFFICE="$1"  # CORE_CTO | CSO | DEXTER_CTO
  PENDING=$(yq ".pending[] | select(.to == \"$OFFICE\")" TASK_QUEUE.yaml 2>/dev/null)

  if [ -n "$PENDING" ]; then
    echo "$(date): New task for $OFFICE" >> ~/logs/task_watcher.log
    # Optional: notification
    # osascript -e 'display notification "New task available" with title "Phoenix"'
  fi

  # Check for HALT in BROADCAST
  if grep -q "HALT" BROADCAST.md; then
    echo "$(date): HALT detected — stopping" >> ~/logs/task_watcher.log
    # Kill running Claude Code session if active
  fi

LAUNCHD_PLIST:
  Label: com.a8ra.taskwatcher
  ProgramArguments: [/bin/bash, ~/phoenix-swarm/watch_tasks.sh, CORE_CTO]
  StartInterval: 120
  RunAtLoad: true
```

### 4.6 Git Operations

```yaml
SYNC_PROTOCOL:
  before_read: git pull (with retry)
  after_write: git add + commit + push
  conflict: Retry once, then alert sovereign

GIT_WORKTREES:
  purpose: "Parallel edits, zero conflict on overlapping domains"
  flow: |
    1: Office claims task
    2: git worktree add ../tasks/T001_DEXTER origin/main
    3: cd to worktree, work, commit
    4: Push worktree branch
    5: G/Core merges via PR or fast-forward

GIT_HOOKS:
  pre-commit: |
    #!/bin/bash
    # Block secrets
    if grep -rE "(ANTHROPIC_API_KEY|OPENROUTER|sk-ant-)" --include="*.yaml" --include="*.md" .; then
      echo "ERROR: Secret pattern detected. Commit blocked."
      exit 1
    fi
    # Validate TASK_QUEUE schema
    python3 hooks/validate_task_queue.py || exit 1

BRANCH_LINKING:
  pattern: result_branch in TASK_QUEUE done entry
  merge: git merge --no-ff dexter/T001-taxonomy
```

---

## 5. MEMORY & PERSISTENCE STACK

```yaml
PURPOSE: |
  Memory persistence is the #1 enemy of buttery smooth operation.
  This 5-layer stack ensures session death is a non-event.
  All layers are Claude Code native — zero heavy external dependencies.
```

### 5.1 Layer 1: Identity (CLAUDE.md)

```yaml
WHAT: Project instructions file, auto-loaded by Claude Code at every session start
WHERE: Root of each office's project directory
PERSISTS: Always (file in repo, never changes mid-sprint)
LOADS: Automatically — Claude Code reads CLAUDE.md on session start

CONTENT_TEMPLATE: |
  # {OFFICE_NAME} — a8ra Mission Control

  ## Identity
  You are {role}. You report to {sovereign}.
  Your office: {OFFICE_NAME}
  Contract version: {version}

  ## Invariants
  {office-specific invariants}

  ## Coordination
  - Check TASK_QUEUE.yaml in phoenix-swarm/ for assignments
  - Write heartbeat to heartbeats/{OFFICE}.yaml on state changes
  - Checkpoint to checkpoints/{OFFICE}.yaml at milestones
  - All results go to results/ with provenance

  ## Current Sprint Context
  {brief summary of active work}

SIZE: ~100-150 lines (concise, high-signal)
UPDATE_CADENCE: Per sprint or major scope change (not per session)
```

### 5.2 Layer 2: Session Memory (MEMORY.md)

```yaml
WHAT: Auto-persisting session state — first 200 lines loaded at every session start
WHERE: Root of each office's project directory
PERSISTS: Across sessions (Claude Code native feature)
LOADS: Automatically — first 200 lines injected at session start

CONTENT_TEMPLATE: |
  # Current State
  task_id: T002
  mission: S45 Research UX
  progress: Gate 3 complete, starting Gate 4

  # Key Decisions This Session
  - Using Pydantic for lens schema (matches S43 pattern)
  - Chunked output format: max 50 beads per response

  # Blockers
  - None

  # Files Modified
  - hunt/lens.py (new preset validation)
  - tests/test_lens.py (14 tests added)

  # Next Actions
  1. Fix test_lens_preset_validation
  2. Implement chunked output
  3. Wire journey UI

WRITES:
  - on-session-end hook (automatic)
  - Agent writes manually at milestones
  - on-error hook (best effort on crash)

SIZE: Keep under 200 lines (only first 200 auto-load)
DISCIPLINE: Agent overwrites with current state, not appends history
```

### 5.3 Layer 3: Structured Checkpoint (checkpoints/)

```yaml
WHAT: Full structured state snapshot for deep recovery
WHERE: phoenix-swarm/checkpoints/{OFFICE}.yaml
PERSISTS: In git (committed + pushed)
LOADS: Agent reads on resume if MEMORY.md insufficient

CONTENT:
  file: checkpoints/CORE_CTO.yaml
  schema: |
    office: CORE_CTO
    timestamp: 2026-02-06T14:30Z
    session_id: sess_abc123

    task:
      id: T002
      mission: "S45 Research UX"
      progress: "Gate 3 complete, Gate 4 in progress"
      gates_passed: [1, 2, 3]
      gates_remaining: [4, 5]

    state:
      files_modified: [hunt/lens.py, tests/test_lens.py]
      tests_passing: 14
      tests_failing: 2
      current_focus: "Fix lens preset validation"

    context_for_fresh_session: |
      Read S45 brief: results/briefs/T002_BRIEF.md
      Key decision: Using Pydantic for lens schema (matches S43 pattern)
      Gate 4 spec: chunked output with max 50 beads per response

    next_actions:
      1: "Fix test_lens_preset_validation"
      2: "Implement chunked output"
      3: "Wire journey UI"

WRITES: on-session-end hook + milestone triggers
VALIDATION: Timestamp + checksum on load (stale/corrupt detection)
```

### 5.4 Layer 4: Searchable Memory (mcp-memory-keeper)

```yaml
WHAT: MCP server providing persistent, searchable memory across sessions
WHERE: Local SQLite database per office
PERSISTS: Indefinitely (until pruned)
LOADS: On-demand via MCP tool calls

TOOL: mcp-memory-keeper
  repo: github.com/mkreyman/mcp-memory-keeper
  stars: 1.2k+ (production adoption)
  backend: SQLite (local, no network dependency)
  integration: Native Claude Code MCP

SETUP_PER_OFFICE:
  install: "npm install -g mcp-memory-keeper (or Docker)"
  config: |
    # .claude/mcp_servers.json
    {
      "mcp-memory-keeper": {
        "command": "mcp-memory-keeper",
        "args": ["--db", "~/.a8ra/memory/{OFFICE}.db"]
      }
    }

USE_CASES:
  - "What was the key decision on lens schema 3 sessions ago?"
  - "Show me all blockers encountered during S45"
  - "What patterns did DEXTER find for OTE + FVG confluence?"

WRITES: Auto-save on hooks (configurable)
PRUNE: Auto-prune entries older than 30 days (configurable)
```

### 5.5 Layer 5: Coordination State (Git)

```yaml
WHAT: Shared board state (tasks, heartbeats, results, broadcasts)
WHERE: phoenix-swarm/ git repository
PERSISTS: Permanent (git history)
LOADS: git pull on session start and before any read

CONTAINS:
  TASK_QUEUE.yaml: Current assignments
  heartbeats/: Office status
  checkpoints/: Recovery snapshots
  results/: Completed work
  BROADCAST.md: G directives
  AGENTS.md: Office contracts

SYNC: Pull before read, commit+push after write
```

### 5.6 Layer Summary

```yaml
RECOVERY_SCENARIOS:

  graceful_exit:
    trigger: "--max-turns reached or task complete"
    saves: MEMORY.md + checkpoint + mcp-memory-keeper + git push
    resume: "--resume SESSION_ID → full continuity"

  crash:
    trigger: "Process kill, OOM, network death"
    saves: "on-error hook (best effort) → partial MEMORY.md + checkpoint"
    resume: "Fresh session → loads CLAUDE.md + MEMORY.md + checkpoint + mcp-memory-keeper"

  cold_start:
    trigger: "No prior session, first boot"
    saves: "N/A"
    resume: "CLAUDE.md (identity) + TASK_QUEUE (assignment) + brief (context)"

VERDICT: |
  Session dies → restarts → resumes → continues.
  5 layers of persistence, zero heavy dependencies.
  Memory persistence #1 enemy: DEFEATED.
```

---

## 6. SESSION LIFECYCLE

### 6.1 Launch Protocol

```yaml
LAUNCH_SCRIPT: launch_office.sh

#!/bin/bash
set -euo pipefail

OFFICE="$1"  # CORE_CTO | CSO | DEXTER_CTO

# 1. Inject secrets from Keychain
export ANTHROPIC_API_KEY=$(security find-generic-password -s "a8ra-anthropic" -w)
case "$OFFICE" in
  DEXTER_CTO)
    export OPENROUTER_API_KEY=$(security find-generic-password -s "a8ra-openrouter" -w)
    export PERPLEXITY_API_KEY=$(security find-generic-password -s "a8ra-perplexity" -w)
    export IBKR_PAPER_ACCOUNT=$(security find-generic-password -s "a8ra-ibkr-synth" -w)
    ;;
  CORE_CTO)
    export IBKR_DEV_ACCOUNT=$(security find-generic-password -s "a8ra-ibkr-dev" -w)
    ;;
esac

# 2. Export identity for self-verification
export OFFICE_ROLE="$OFFICE"
export CONTRACT_VERSION="v0.2"

# 3. Sync coordination repo
cd ~/phoenix-swarm && git pull -q

# 4. Determine session mode
HEADLESS=""
MAX_TURNS="80"
case "$OFFICE" in
  DEXTER_CTO) HEADLESS="--headless"; MAX_TURNS="100" ;;
  CSO) MAX_TURNS="60" ;;
esac

# 5. Check for resume
LAST_SESSION=$(cat checkpoints/${OFFICE}_session_id 2>/dev/null || echo "")
RESUME_FLAG=""
if [ -n "$LAST_SESSION" ]; then
  RESUME_FLAG="--resume $LAST_SESSION"
fi

# 6. Launch Claude Code
claude $HEADLESS \
  --max-turns=$MAX_TURNS \
  $RESUME_FLAG \
  --project ~/phoenix/ \
  --mcp-server mcp-memory-keeper

INVARIANT: "INV-IDENTITY-PROVENANCE: Office verifies ENV identity against AGENTS.md at boot"
```

### 6.2 Hooks Configuration

```yaml
# .claude/hooks.json (per office)

hooks:
  on-session-start:
    script: |
      #!/bin/bash
      # Sync coordination repo
      cd ~/phoenix-swarm && git pull -q
      # Log session start
      echo "$(date): Session started for $OFFICE_ROLE" >> ~/logs/office.log

  on-session-end:
    script: |
      #!/bin/bash
      # Auto-checkpoint on graceful exit
      cd ~/phoenix-swarm
      # Save session ID for --resume
      echo "$CLAUDE_SESSION_ID" > checkpoints/${OFFICE_ROLE}_session_id
      # Commit checkpoint + heartbeat
      git add checkpoints/ heartbeats/
      git commit -m "checkpoint: ${OFFICE_ROLE} session end $(date -u +%Y-%m-%dT%H:%MZ)" -q
      git push -q
      echo "$(date): Session ended, checkpoint saved" >> ~/logs/office.log

  on-error:
    script: |
      #!/bin/bash
      # Best-effort crash checkpoint
      cd ~/phoenix-swarm 2>/dev/null && {
        git add checkpoints/ heartbeats/ 2>/dev/null
        git commit -m "CRASH checkpoint: ${OFFICE_ROLE} $(date -u)" -q 2>/dev/null
        git push -q 2>/dev/null
      }
      echo "$(date): ERROR — crash checkpoint attempted" >> ~/logs/office.log

  on-tool-use:
    # Optional: milestone-based saves after significant operations
    # Configure per office based on workload patterns
    enabled: false  # Enable after ground testing
```

### 6.3 Auto-Restart Daemon

```yaml
# com.a8ra.office.CORE_CTO.plist (launchd)

PURPOSE: "Restart office session on crash or graceful exit"

PLIST:
  Label: com.a8ra.office.CORE_CTO
  ProgramArguments: [/bin/bash, ~/phoenix-swarm/launch_office.sh, CORE_CTO]
  RunAtLoad: true
  KeepAlive: true              # Restart on exit
  ThrottleInterval: 30         # Wait 30s between restarts (prevent rapid loop)
  StandardOutPath: ~/logs/core_cto_stdout.log
  StandardErrorPath: ~/logs/core_cto_stderr.log

DEXTER_OVERRIDE:
  KeepAlive: true              # 24/7 headless — always restart
  ThrottleInterval: 60         # Longer cooldown for heavy workloads

CORE_CSO_OVERRIDE:
  KeepAlive: false             # Human-paced — don't auto-restart
  # Use KeepAlive: true only during active sprint execution
```

---

## 7. TOOL STACK

```yaml
DESIGN_PRINCIPLE: |
  Claude-native > bolted-on.
  Claude Code's Feb 2026 capabilities (hooks, MCP, subagents, --headless)
  eliminate most external tool dependencies.
  Minimum viable stack, maximum smooth.
```

### 7.1 Phase 1 — Required

```yaml
CLAUDE_CODE_CLI:
  role: Primary agent runtime
  features_used: --headless, --resume, --max-turns, hooks, MCP servers, native subagents
  status: PRODUCTION_READY

MCP_MEMORY_KEEPER:
  role: Persistent searchable memory per office
  integration: Native Claude Code MCP server
  backend: SQLite (local)
  status: PRODUCTION_READY (1.2k GitHub stars, active development)
  deployment: ALL offices

OLLAMA:
  role: Local model runtime for DEXTER
  models: Kimi 2.5, Qwen3-72B, Gemma3-27B
  deployment: DEXTER only (requires M3 Ultra 512GB)
  status: PRODUCTION_READY

GIT:
  role: Coordination layer (phoenix-swarm/) + code repos
  deployment: ALL offices
  status: PROVEN

LAUNCHD:
  role: Process management, auto-restart, cron daemons
  deployment: ALL offices
  status: macOS native, PROVEN

KEYCHAIN:
  role: Secret storage (Phase 1 security)
  deployment: ALL Macs
  status: macOS native, PROVEN
```

### 7.2 Phase 1 — Optional

```yaml
N8N:
  role: Pipeline monitoring dashboard (DEXTER only)
  deployment: DEXTER only, IF visual monitoring proves valuable
  setup: docker run -d -p 5678:5678 n8n
  note: "n8n observes Claude, doesn't orchestrate Claude"
  status: OPTIONAL — evaluate after first operational week
```

### 7.3 Phase 2 — Future Additions

```yaml
COMPOSIO:
  role: Secretless tool calling (MCP broker)
  timing: Post v0.1, dedicated security hardening sprint
  replaces: Keychain + launch script pattern

QDRANT:
  role: Vector search for recognition queries
  timing: Post v0.1, IF SQLite FTS5 proves insufficient
  replaces: mcp-memory-keeper for complex similarity queries

CLAUDE_MEMORY_MCP:
  role: Vector search + timeline memory (upgrade from mcp-memory-keeper)
  timing: Post v0.1, IF deeper memory capabilities needed
  repo: github.com/WhenMoon-afk/claude-memory-mcp (2.3k stars)

GATEWAY_PROXY:
  role: Localhost proxy for secretless API calls
  timing: Post v0.1
  implementation: ~100 LOC Go/Node service
```

### 7.4 Deprecated (From v0.1)

```yaml
REMOVED_FROM_PHASE_1:
  letta: "mcp-memory-keeper is lighter, Claude-native, no Docker server dependency"
  composio: "Keychain sufficient for Phase 1. Composio deferred to Phase 2."
  qdrant: "SQLite FTS5 + mcp-memory-keeper cover 80% of recognition use cases"
  tmux_orchestration: "Native Claude Code subagents replace HIVE_OPS pattern"

RATIONALE: |
  v0.1 designed around external tools because we didn't know Claude Code's native capabilities.
  v0.2 designs around Claude Code's actual capabilities (Feb 2026).
  Result: 50% fewer dependencies, 100% more buttery.
```

---

## 8. SUBAGENT MODEL

```yaml
PATTERN: Native Claude Code subagents (replaces HIVE_OPS tmux)

LEADER_SPAWNS_WORKERS:
  mechanism: Claude Code native /delegate or subagent API
  persistence: Each subagent gets own persistent memory
  coordination: Leader manages scope, subagents execute

CONSTRAINTS:
  INV-SUBAGENT-TURN-CAP: "Max 20 turns per subagent task"
  INV-SUBAGENT-HEARTBEAT: "Subagent emits status; leader kills on silence >5min"
  token_ceiling: "Per-subagent token budget (configurable per office)"

FAILURE_HANDLING:
  hang: "Leader detects via heartbeat silence → kill + retry"
  bad_output: "Leader validates before accepting → reject + re-delegate"
  context_bloat: "Turn cap prevents runaway consumption"

ANTI_PATTERN: |
  CrewAI, AutoGen, LangChain agents: Too chatty, high hallucination tax.
  Custom tmux Dispatcher→Planner→Worker: Replaced by native capabilities.
  Infinite delegation loops: Turn cap + leader oversight prevents.
```

---

## 9. SECURITY MODEL

### 9.1 Phase 1: MVP Security

```yaml
STATUS: "Good enough for controlled environment"

PATTERN: "Keychain + launch script + git hooks"

HOW_IT_WORKS:
  1: Real secrets stored in macOS Keychain (per Mac)
  2: launch_office.sh reads from Keychain, sets env vars
  3: Script launches Claude Code with env vars injected
  4: Agent sees env vars, uses them
  5: Session ends, env vars gone

SECURITY_POSTURE:
  - Keys never in repo (git hooks enforce)
  - Keys never in agent's persistent memory
  - Keys in Keychain (encrypted at rest)
  - Agent could theoretically echo them (Phase 2 fixes this)
  - ACCEPTABLE for controlled dev environment

GIT_HOOKS:
  pre-commit: |
    grep -rE "(ANTHROPIC_API_KEY|OPENROUTER|sk-ant-|sk-or-)" . && exit 1
  purpose: Block any secrets from entering repo

VERSION_PINNING:
  claude_code: Pin to specific version in launch script
  docker_images: Pin with sha256 digest (not :latest)
  mcp_servers: Pin npm versions
```

### 9.2 Phase 2: Hardened Security

```yaml
STATUS: "Production-grade, 24/7 safe"
TIMELINE: Post v0.1, dedicated sprint

UPGRADES:
  1_gateway_proxy: "Localhost service injects creds — agent never possesses keys"
  2_scoped_tokens: "Each office gets minimum necessary permissions"
  3_audit_trail: "Every API call logged with provenance (no secrets logged)"
  4_composio: "Full MCP broker for secretless tool calling"
```

---

## 10. INFRASTRUCTURE BOOTSTRAP

### 10.1 Ground Test Protocol (First 30 Minutes)

```yaml
PURPOSE: |
  Validate Claude Code native capabilities BEFORE full bootstrap.
  If any test fails → fallback to v0.1 mechanism for that component.
  These tests confirm our v0.2 design assumptions are real.

TEST_ENVIRONMENT: Any Mac with Claude Code installed

GT-1_MEMORY_MD:
  test: "Create MEMORY.md in project root, write state, kill session, restart"
  expect: "Session loads with MEMORY.md content in context"
  pass: "Agent knows state from previous session without being told"
  fail_fallback: "Manual checkpoint loading via agent prompt"
  time: 3 min

GT-2_RESUME:
  test: "Start session, do work, note session ID, exit. Start with --resume ID"
  expect: "Session continues with full prior context"
  pass: "Agent references prior work naturally"
  fail_fallback: "MEMORY.md + checkpoint file manual loading"
  time: 5 min

GT-3_MCP_MEMORY_KEEPER:
  test: "Install mcp-memory-keeper, configure in .claude/, start session"
  expect: "Agent can store and retrieve memories via MCP tools"
  pass: "Agent saves fact, new session retrieves it via search"
  fail_fallback: "SQLite + manual file reads"
  time: 10 min

GT-4_HOOKS:
  test: "Configure on-session-end hook to write timestamp to file. Start session, exit."
  expect: "File contains timestamp after exit"
  pass: "Hook fires on graceful exit"
  fail_fallback: "Agent manually writes checkpoint before exiting"
  time: 5 min

GT-5_HEADLESS:
  test: "Start Claude Code with --headless, give it a simple task"
  expect: "Task completes without interactive terminal"
  pass: "DEXTER 24/7 mode viable"
  fail_fallback: "tmux non-interactive wrapper"
  time: 3 min

GT-6_SUBAGENTS:
  test: "Opus session delegates subtask to subagent"
  expect: "Subagent completes, returns result to leader"
  pass: "Native multi-agent works"
  fail_fallback: "tmux HIVE_OPS pattern (v0.1 design)"
  time: 5 min

TOTAL_TIME: ~30 minutes
PASS_THRESHOLD: GT-1 + GT-4 must pass (minimum viable). Others enhance.
RECORD: Log results to phoenix-swarm/ground_tests/RESULTS.yaml
```

### 10.2 Bootstrap Sequence (4 Hours)

```yaml
HOUR_0_GROUND_TESTS (30 min):
  - Run GT-1 through GT-6
  - Record results
  - If GT-1 or GT-4 fail: PAUSE — reassess before proceeding
  - Adapt remaining bootstrap based on test results

HOUR_1_SHARED_REPO (60 min):
  - Create phoenix-swarm/ on G's Mac
  - git init, add full structure:
    - BROADCAST.md, TASK_QUEUE.yaml, AGENTS.md
    - heartbeats/ (empty per-office files)
    - checkpoints/ (empty)
    - results/, results/briefs/
    - claiming/ (empty)
    - hooks/ (pre-commit, validate_task_queue.py)
    - ground_tests/
  - Push to private remote (GitHub)
  - Clone to other Macs
  - Verify: all Macs can pull/push

HOUR_2_OFFICE_IDENTITIES (60 min):
  - Write CLAUDE.md per office (in each project root)
  - Write MEMORY.md templates (empty, ready for first session)
  - Configure .claude/mcp_servers.json with mcp-memory-keeper
  - Add secrets to macOS Keychain on each Mac
  - Write launch_office.sh
  - Configure hooks (.claude/hooks.json)
  - Test: launch_office.sh starts Claude Code with correct identity
  - Verify: agent knows who it is, can read TASK_QUEUE

HOUR_3_FIRST_TASK_CYCLE (60 min):
  - G writes first test task to TASK_QUEUE.yaml
  - CORE_OFFICE claims task (using atomic claim protocol)
  - CORE_OFFICE executes simple task (e.g., "create a test file")
  - CORE_OFFICE writes result, updates heartbeat
  - Verify: full cycle works — claim → execute → result → heartbeat
  - Test: session end → checkpoint written → new session resumes
  - Test: DEXTER claims separate task in parallel

HOUR_4_DEXTER_SETUP (60 min):
  - Clone phoenix/ to M3 Ultra as phoenix-synthetic/
  - Configure separate paper IBKR account
  - Install Ollama + pull models (Kimi 2.5, Qwen3-72B, Gemma3-27B)
  - Configure --headless launch for DEXTER
  - Run: DEXTER claims task, executes headless, writes result
  - Verify: headless + auto-restart via launchd works
  - Run test suite on phoenix-synthetic/ → green

POST_BOOTSTRAP:
  - Begin real sprint work (S45 via CORE, extraction via DEXTER)
  - Real work IS the integration test
  - Monitor for first 24h, fix issues as they surface
  - After 48h stable: declare MISSION_CONTROL_OPERATIONAL

TOTAL: ~4 hours focused + 48h monitoring
```

---

## 11. WORKFLOW EXAMPLES

### 11.1 Olya Hypothesis → Evidence Bundle

```yaml
SCENARIO: "Test OTE + FVG confluence hypothesis"

STEP_1_HYPOTHESIS (CSO Office):
  olya_action: Draft hypothesis in Claude session
  claude_helps: Structure into testable IF-THEN format
  output: Hypothesis document (markdown)
  compute: Minimal (Claude conversation)

STEP_2_SUBMIT (CSO Office → TASK_QUEUE):
  olya_action: Post task to shared board
  format: |
    TASK_QUEUE.yaml pending:
      - id: T042
        from: CSO
        to: DEXTER_CTO
        mission: "Backtest hypothesis: OTE + FVG confluence"
        brief_path: results/briefs/T042_OTE_FVG.md
        data_scope: "2023-2024 London session"
        validation: "S39 full suite"

STEP_3_EXECUTE (DEXTER Office):
  dexter_action: Claims task via atomic claim protocol, runs backtest
  compute: HEAVY (walk-forward, Monte Carlo 1000 iterations)
  output: results/T042_DEXTER_EVIDENCE.md

STEP_4_NOTIFY (DEXTER → CSO):
  dexter_action: Updates TASK_QUEUE (done), writes heartbeat
  notification: "@CSO evidence bundle T042 ready" (optional Telegram)

STEP_5_REVIEW (CSO Office):
  olya_action: Reviews evidence bundle
  surface: Decomposed metrics, no scalars
  decision: PROMOTE (FACT_BEAD) | REJECT (NEGATIVE_BEAD) | REQUEST_MORE

STEP_6_INTEGRATE (CSO → CORE):
  if_promoted: CSO updates conditions.yaml → CORE integrates gate
  if_rejected: NEGATIVE_BEAD feeds DEXTER learning loop
```

### 11.2 Sprint Execution Flow

```yaml
SCENARIO: "Execute S45 Research UX"

STEP_1: G posts sprint brief to TASK_QUEUE → CORE_CTO
STEP_2: CORE_CTO claims via atomic protocol, loads brief
STEP_3: Gate-by-gate execution with checkpoint after each gate pass
STEP_4: G reviews at sprint boundary (async)
STEP_5: CORE marks done, posts result on branch
STEP_6: G reviews and merges to main
```

---

## 12. INVARIANTS

### 12.1 Sovereignty Invariants (Preserved)

```yaml
INV-SOVEREIGN-1: "Human sovereignty over capital is absolute"
INV-SOVEREIGN-2: "T2 requires human gate"
INV-HALT-PROPAGATION: "Halt from sovereign propagates to all offices"
INV-CAPITAL-GATE: "No live execution without human approval"
```

### 12.2 Coordination Invariants

```yaml
# Preserved from v0.1
INV-TASK-QUEUE-ATOMIC: "Task claims use atomic lock protocol"
INV-CHECKPOINT-BEFORE-DEATH: "Hooks fire checkpoint on session end/error"
INV-IDENTITY-INJECTION: "Agent loads identity + state + tasks on every session start"
INV-BRANCH-LINKING: "All results in git branches, merged via PR"
INV-HEARTBEAT-CADENCE: "Update heartbeat on start, claim, progress, blocker, end"

# New from OWL audit
INV-ATOMIC-CLAIM: "No agent writes task state without holding filesystem lock"
INV-SINGLE-WRITER-LOG: "Each office owns exactly one heartbeat file"
INV-IDENTITY-PROVENANCE: "Office verifies ENV identity against AGENTS.md at boot"
INV-STRICT-COMMIT: "No state change valid without passing linter gate"
```

### 12.3 Security Invariants

```yaml
INV-NO-SECRETS-IN-REPO: "Git hooks block credential patterns"
INV-KEYCHAIN-ONLY: "Secrets never in agent persistent memory"
INV-PROXY-INJECTION: "Agent never possesses credentials (Phase 2)"
INV-SCOPED-ACCESS: "Minimum necessary permissions per office (Phase 2)"
```

### 12.4 Operational Invariants

```yaml
INV-OFFICE-SCOPED-WORK: "Each office only claims tasks addressed to them"
INV-G-BROADCAST-ONLY: "Only G writes to pending tasks and BROADCAST.md"
INV-SOVEREIGN-VETO: "G can halt/override any task via BROADCAST"
INV-RESULT-PROVENANCE: "All results are beads with full lineage"
INV-COST-CEILING: "Token/cost budget per office with effort param"
INV-WIP-VISIBILITY: "Offices see completed work only, not in-progress WIP"
```

### 12.5 Subagent Invariants

```yaml
INV-SUBAGENT-TURN-CAP: "Subagent limited to 20 turns per task"
INV-SUBAGENT-HEARTBEAT: "Subagent emits status; leader kills on silence >5min"
```

### 12.6 Dexter Bridge Invariants (From GPT)

```yaml
INV-DEXTER-NO-AUTO-PROMOTE-TO-LIVE: "CLAIM→FACT requires explicit human ceremony"
INV-VARIANT-PROVENANCE: "Every variant traces to source FACT_BEAD (Olya-validated)"
INV-DEXTER-EVIDENCE-NOT-ADVICE: "Evidence menu only, never recommendations"
```

### 12.7 Resilience Invariants

```yaml
INV-DISK-CEILING: "Halt at 80% disk usage, auto-prune old checkpoints"
INV-ALERT-TAXONOMY: "Alert levels: INFO/WARN/ALERT/HALT — prevent storm and silence"
INV-ROLLBACK-TRIGGER: "Bad state = failed ground test + stale checkpoint + sovereign override"
INV-JANITOR-CADENCE: "Cron purges stale locks (>2hr), orphan checkpoints (>24hr)"
```

```yaml
INVARIANT_TOTALS:
  sovereignty: 4
  coordination: 9
  security: 4
  operational: 6
  subagent: 2
  dexter_bridge: 3
  resilience: 4
  TOTAL_NEW: 13 (from advisor stress test)
  TOTAL_MISSION_CONTROL: 32
  TOTAL_SYSTEM_WIDE: 124+ (111 Phoenix + 13 MC)
```

---

## 13. 3AM RESILIENCE

```yaml
PURPOSE: |
  DEXTER runs 24/7 headless. G and Olya sleep.
  Every failure mode must either self-heal or gracefully degrade.
```

### 13.1 Watchdog Daemons

```yaml
OLLAMA_WATCHDOG:
  trigger: Ollama process dies or OOM
  action: Restart Ollama, fallback to smaller model if OOM persists
  alert: INFO to log, WARN to sovereign if >3 restarts/hour
  plist: com.a8ra.watchdog.ollama

DISK_MONITOR:
  trigger: Disk usage > 80%
  action: Halt writes, prune old checkpoints + logs, alert sovereign
  alert: ALERT to sovereign immediately
  plist: com.a8ra.watchdog.disk
  schedule: Every 15 min

GIT_CONNECTIVITY:
  trigger: git pull fails >5 min
  action: Continue local work, queue commits, alert on >15 min
  alert: WARN at 5 min, ALERT at 15 min
  fallback: Local-only mode (DEXTER can work offline with local models)

SESSION_HEALTH:
  trigger: Claude Code process exits unexpectedly
  action: launchd auto-restarts (ThrottleInterval: 60s)
  alert: INFO on restart, WARN if >3 restarts/hour
  escalation: HALT if >5 restarts/hour (something is fundamentally broken)
```

### 13.2 Preventive Measures

```yaml
UPS:
  device: UPS for M3 Ultra (30min battery backup)
  purpose: Graceful shutdown on power loss
  action: UPS sends signal → launchd triggers on-session-end hooks → clean checkpoint

KEY_ROTATION:
  schedule: Monthly check (manual for Phase 1)
  pre_batch: Validate all API keys respond before starting extraction batch
  alert: WARN sovereign 7 days before known expiry

BOOT_RECOVERY:
  trigger: Mac restarts (power outage, update, crash)
  sequence: |
    1. launchd starts task watcher
    2. Task watcher pulls phoenix-swarm/
    3. launchd starts office session (if KeepAlive: true)
    4. Session loads CLAUDE.md + MEMORY.md + checkpoint
    5. Agent resumes from last known state
  time_to_recovery: ~2 min from boot to working
```

### 13.3 Alert Taxonomy

```yaml
INFO:
  examples: "Session restarted", "Checkpoint saved", "Task claimed"
  destination: Log file only
  human_action: None

WARN:
  examples: "3+ restarts/hour", "Git pull failed >5min", "API rate limited"
  destination: Log + optional Telegram
  human_action: Review when convenient

ALERT:
  examples: "Disk >80%", "Git unreachable >15min", "Key expiry <7 days"
  destination: Log + Telegram + BROADCAST.md
  human_action: Respond within hours

HALT:
  examples: "5+ restarts/hour", "Checkpoint corrupt + no fallback", "Sovereign override"
  destination: Log + Telegram + BROADCAST.md + kill all sessions
  human_action: Investigate before restart
```

---

## 14. DECISION POINTS — ALL LOCKED

```yaml
DP-1:
  topic: n8n deployment scope
  decision: DEXTER only, monitoring-only (OPTIONAL)
  locked_by: G
  date: 2026-02-09

DP-2:
  topic: Composio deployment timing
  decision: PHASE 2
  locked_by: G (advisor convergence)
  date: 2026-02-09

DP-3:
  topic: Letta deployment
  decision: SKIP — mcp-memory-keeper replaces
  locked_by: G (BOAR R2 ground truth)
  date: 2026-02-09

DP-4:
  topic: Qdrant deployment
  decision: PHASE 2 — SQLite FTS5 for Phase 1
  locked_by: G
  date: 2026-02-09

DP-5:
  topic: Hardware allocation
  decision: AS SPECIFIED (M3 Ultra 512GB for DEXTER)
  locked_by: G (advisor convergence)
  date: 2026-02-09

DP-6:
  topic: Bootstrap sequence
  decision: HYBRID — 30min ground tests + 4hr focused + learn by doing
  locked_by: G
  date: 2026-02-09

DP-7:
  topic: DEXTER replica priority
  decision: IMMEDIATE — parallel with CORE setup
  locked_by: G
  date: 2026-02-09

DP-8:
  topic: Rollback trigger definition
  decision: "Failed ground test + stale checkpoint + sovereign override"
  locked_by: CTO (from OWL flag)
  date: 2026-02-09

DP-9:
  topic: Inter-office WIP visibility
  decision: COMPLETED WORK ONLY (offices see done results, not in-progress)
  locked_by: G
  date: 2026-02-09

DP-10:
  topic: Subagent monitoring
  decision: Leader heartbeat check + turn cap (included in v0.2 invariants)
  locked_by: CTO (from BOAR flag)
  date: 2026-02-09

DP-11:
  topic: Alert taxonomy
  decision: 4-level (INFO/WARN/ALERT/HALT) — defined in Section 13.3
  locked_by: CTO (from BOAR flag)
  date: 2026-02-09

DP-12:
  topic: mcp-memory-keeper deployment scope
  decision: ALL OFFICES
  locked_by: CTO (from BOAR R2)
  date: 2026-02-09

DP-13:
  topic: Subagent model
  decision: NATIVE Claude Code subagents (deprecate tmux HIVE_OPS)
  locked_by: CTO (from BOAR R2)
  date: 2026-02-09

TOTAL: 13 decisions, ALL LOCKED
```

---

## 15. PATTERN VALIDATION: a8ra_web

```yaml
INSIGHT: |
  Before Mission Control bootstrap, the pattern was proven in production
  via the a8ra.com autonomous art installation (Picasso Forge).

PICASSO_FORGE_MAPS_TO_MISSION_CONTROL:
  sub_agents: → Offices (CORE, CSO, DEXTER)
  curation: → Human gate at sprint boundaries
  bounded_iteration: → INV-NO-CORE-REWRITES (no runaway rework)
  fallback: → Graceful degradation patterns
  delivery: → Git-based coordination + shared board
  epoch_trigger: → Task watcher daemon (2min poll)

STATUS: PRODUCTION_VALIDATED
  running_since: 2026-02
  human_intervention: Zero required
  operational_cost: "$5-9/month"
```

---

## 16. RISK INVENTORY (Updated)

```yaml
RISK_1_COORDINATION_LATENCY:
  issue: 2-min polling adds latency to inter-office communication
  mitigation: Async is a feature. Offices work independently, check board periodically.
  residual: LOW (acceptable for our workload patterns)

RISK_2_SECRET_EXPOSURE:
  issue: Phase 1 env vars could theoretically be echoed
  mitigation: Controlled environment, git hooks, Phase 2 proxy
  residual: LOW (acceptable for Phase 1)

RISK_3_CONTEXT_DEATH:
  issue: Despite 1M context + --max-turns, complex tasks could still hit limits
  mitigation: Hooks auto-checkpoint, --resume recovers, 5-layer memory stack
  residual: LOW (v0.2 mechanisms are concrete, not aspirational)

RISK_4_HARDWARE_DEPENDENCY:
  issue: M3 Ultra critical for DEXTER sovereign operation
  mitigation: API-only mode as fallback. M3 Ultra on order, ETA ~1 week.
  residual: MEDIUM (until M3 arrives, DEXTER runs degraded)

RISK_5_SCOPE_CREEP:
  issue: Mission Control itself is infrastructure, not v0.1 feature
  mitigation: 4hr bootstrap cap. Phase 1 vs Phase 2 separation. INV-NO-CORE-REWRITES.
  residual: LOW

RISK_6_MCP_MEMORY_KEEPER_RELIABILITY:
  issue: mcp-memory-keeper is community project, not Anthropic official
  mitigation: Ground test GT-3 validates before dependency. SQLite fallback.
  residual: MEDIUM (mitigated by ground testing)

RISK_7_GROUND_TEST_FAILURES:
  issue: Claude Code features may not behave exactly as documented
  mitigation: Each ground test has explicit fallback to v0.1 mechanism
  residual: LOW (graceful degradation, not hard failure)
```

---

## 17. DEPENDENCIES & PREREQUISITES

```yaml
HARDWARE:
  g_sovereign: Mac Mini M4 Pro (or any modern Mac)
  core_office: Mac Studio M4 Max (or high-spec alternative)
  cso_office: Mac Mini (any M-series)
  dexter_office: M3 Ultra 512GB (on order, ETA ~1 week)

ACCOUNTS:
  anthropic: Claude Max x20 for DEXTER + CORE, x5 for G + CSO
  ibkr_paper: TWO accounts (dev + synthetic)
  openrouter: For DEXTER volume routing
  perplexity: For DEXTER research enrichment
  github: Private repo for phoenix-swarm/

SOFTWARE (per Mac):
  required:
    - macOS with Keychain Access
    - Git + SSH keys configured
    - Claude Code CLI (pinned version)
    - Python 3.11+ with venv
    - Node.js (for mcp-memory-keeper)
    - yq (YAML processor — brew install yq)
  dexter_additional:
    - ollama (brew install ollama)
    - Large model weights (Kimi 2.5, Qwen3-72B, Gemma3-27B)
    - Docker (optional — for n8n monitoring)
```

---

## 18. RELATIONSHIP TO OTHER DOCS

```yaml
BRAND_IDENTITY.md: "What is a8ra? (public brand)"
PHOENIX_MANIFEST.md: "What is Phoenix? (trading system architecture)"
MISSION_CONTROL_DESIGN.md: "How do offices coordinate? (THIS DOCUMENT)"
ENDGAME_VISION.md: "Where is this going? (24/7 refinery)"
SPRINT_ROADMAP.md: "What are we building now? (execution)"
CARTRIDGE_AND_LEASE_DESIGN.md: "How is autonomy bounded? (governance)"

UPDATE_NEEDED:
  PHOENIX_MANIFEST.md: Add office architecture section
  SPRINT_ROADMAP.md: Add Mission Control bootstrap as enabling work
  ENDGAME_VISION.md: Link to this design + add GPT's Dexter invariants
  HIVE_OPS.md: Mark tmux pattern as DEPRECATED — link to native subagents
```

---

## 19. NEXT ACTIONS

```yaml
IMMEDIATE:
  1: M3 Ultra arrives → execute bootstrap (Section 10)
  2: Ground tests first 30 min (GT-1 through GT-6)
  3: 4hr bootstrap sequence
  4: 48h monitoring period
  5: Declare MISSION_CONTROL_OPERATIONAL

POST_OPERATIONAL:
  6: Begin S45 via CORE_OFFICE
  7: Begin DEXTER extraction (parallel)
  8: CSO workflow activation (when Mirror Report ready)
  9: Phase 2 planning (Composio, Qdrant, security hardening)
```

---

```yaml
DOCUMENT_STATUS:
  version: 0.2
  status: CANONICAL | ALL_DECISIONS_LOCKED
  decisions: 13/13 LOCKED
  invariants: 32 (Mission Control) + 111 (Phoenix) = 124+ total
  ground_tests: 6 defined
  bootstrap: 4hr hybrid + 30min prefix

  advisor_inputs:
    OWL: Structural audit (heartbeats, claiming, identity, invariants)
    GPT: Dexter bridge invariants (bonus material)
    BOAR_R1: Chaos audit, tool revalidation, 3am resilience
    BOAR_R2: Frontier research (Claude Code capabilities, memory stack, MCP ecosystem)

  key_v0.2_changes:
    - 5-layer memory stack (Claude-native, zero heavy deps)
    - Hooks-based checkpoint (concrete mechanism, not aspirational)
    - Native subagents (deprecates tmux HIVE_OPS)
    - Simplified tool stack (3 core vs 6+ in v0.1)
    - 13 new invariants from advisor collision
    - Ground test protocol for bootstrap validation
    - 3am resilience section (watchdogs, UPS, alert taxonomy)
    - All 13 decision points locked
```

---

*Captured: 2026-02-09*
*Source: G + CTO + OWL + GPT + BOAR (R1 + R2) synthesis*
*Pattern: Measure twice, cut once. Claude-native > bolted-on.*

*"The pattern works. Now it sings."*

**OINK OINK.** 🐗🔥
