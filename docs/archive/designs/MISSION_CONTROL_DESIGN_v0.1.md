# MISSION CONTROL DESIGN v0.1

```yaml
document: MISSION_CONTROL_DESIGN
version: 0.1.1
date: 2026-02-09
status: DESIGN_DRAFT | CTO_REVIEWED | AWAITING_PLANNING_SESSION
source: G + CTO + Grok advisor synthesis (2026-02-06 to 2026-02-08)
purpose: Complete design spec for multi-office Opus-led swarm architecture
pattern: Follows CARTRIDGE_AND_LEASE_DESIGN paradigm (measure twice, cut once)
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
    - 1M context + checkpoint pattern = no context death
    - Human as sovereign reviewer at gates
    - Parallel office execution via shared board
    - "Seed vision before sleep, wake to integrated products"

ENABLING_FACTORS:
  opus_4.6: "Plans more carefully, sustains agentic tasks longer, catches own mistakes"
  context_1m: "Entire codebase + history in context (beta)"
  infrastructure: "Phoenix S28-S47 proven, governance patterns operational"
  dexter: "Extraction refinery operational, 981 signatures, Mirror Report ready"

OUTCOME:
  v0.1_acceleration: "2-3 weeks (parallel) vs 3-4 weeks (sequential)"
  operational_model: "Offices compound 24/7 while humans sleep"
  sovereignty: "Human frames, machine computes, human approves"
```

---

## 2. ARCHITECTURE OVERVIEW

### 2.1 Office Model

```yaml
CORE_PRINCIPLE: |
  "Opus leader + subagent team + advisor access per office"
  Each office is self-sufficient, coordinates via shared board.
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
    mode: CAN_RUN_HEADLESS
```

### 2.2 Communication Topology

```yaml
INTER_OFFICE_COMMS:
  medium: Shared git repository (phoenix-swarm/)
  pattern: Async file-based messaging
  routing: Task queue + @mentions (no human routing needed)

  message_types:
    BROADCAST: G → all offices (strategic directive)
    REQUEST: Office → Office ("@DEXTER test hypothesis X")
    RESULT: Office → Board (completed work)
    ALERT: Any → Human sovereigns (requires attention)

INTRA_OFFICE_COMMS:
  pattern: Opus leader spawns subagents via Claude Code
  coordination: Leader manages, subagents execute
  state: Leader holds context, subagents are disposable

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
  - TASK_QUEUE watcher daemon (launchd)
  - Telegram/Matrix (optional — mobile alerts)

LOCAL_MODELS: Not needed

UPTIME: Always-on (Mission Control)

UNIQUE_CAPABILITIES:
  - Broadcast author
  - Veto authority
  - Secrets distribution
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
  - Claude Code CLI
  - Python 3.11+
  - pytest + full dev deps
  - Git + pre-commit hooks
  - launchd (heartbeat)

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
  - Claude Desktop or Code (lighter usage)
  - Git
  - Light Python (review scripts)

LOCAL_MODELS: Not needed

SECRETS:
  - ANTHROPIC_API_KEY

UPTIME: Olya's schedule

WORKLOADS:
  - Mirror Report review
  - Hypothesis drafting (text, not compute)
  - Promotion/rejection workflows
  - conditions.yaml editing

WORKFLOW_TOOLS:
  - Mirror Report viewer (markdown)
  - conditions.yaml editor
  - TASK_QUEUE poster (submit to DEXTER)

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
    - 24/7 headless capability
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
  - Claude Code CLI (headless capable)
  - ollama / llama.cpp (local model runtime)
  - Python 3.11+ (extraction pipeline)
  - launchd/cron (24/7 heartbeat)
  - Git

LOCAL_MODELS:
  primary_reasoning: Kimi 2.5
  code_extraction: Qwen3-72B
  classification: Gemma3-27B
  optional: DeepSeek-V3 local (if available)

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
  HEARTBEAT.md          # Office status log
  TASK_QUEUE.yaml       # Kanban: pending/claimed/done/blocked
  AGENTS.md             # Office identities + souls
  BROADCAST.md          # G directives
  checkpoints/
    CORE_CTO.md         # Last known state
    CSO.md
    DEXTER_CTO.md
  results/
    T001_DEXTER.md      # Task outputs (beads)
    T002_CORE.md
    briefs/
      T001_BRIEF.md     # Task briefs
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
    result_branch: core/T003-lease  # For git merge

blocked:
  - id: T004
    mission: "Setup Phoenix replica"
    blocked_by: DEXTER_CTO
    blocked_at: 2026-02-06T10:00Z
    blocker: "Need IBKR paper credentials from G"
```

### 4.3 HEARTBEAT.md Format

```yaml
# HEARTBEAT — 2026-02-06

## 14:30 — CORE_CTO
status: WORKING
task: T002 (S45 Research UX)
progress: Gate 1-3 complete
context_pct: 45%
blockers: None

## 14:25 — DEXTER_CTO
status: WORKING
task: T001 (Taxonomy extraction)
progress: Schema defined, implementing
context_pct: 30%
blockers: None

## 14:00 — CSO
status: IDLE
waiting_for: Mirror Report from DEXTER
context_pct: 10%
blockers: None

## 12:00 — G
BROADCAST: S45 priority for CORE. Taxonomy fix for DEXTER.
```

### 4.4 AGENTS.md Format

```yaml
# AGENTS.md — Office Identities

## CORE_CTO
role: Phoenix development lead
owns: S45-S52 execution, codebase integrity
invariants:
  - INV-NO-CORE-REWRITES-POST-S44
  - All shipped code has tests
reports_to: G (sprint gates)
can_summon: GROK, OWL, GPT (via board request)
repo: ~/phoenix/

## CSO
role: Methodology validation
owns: CLAIM→FACT promotion, gate calibration
invariants:
  - INV-DEXTER-ALWAYS-CLAIM
  - Recognition > Recall
reports_to: Olya (domain authority), G (visibility)
feeds_from: DEXTER_CTO (Mirror Reports)
repo: ~/phoenix/ (cso/ modules)

## DEXTER_CTO
role: Evidence refinery, synthetic R&D
owns: Extraction, hypothesis testing, Mirror Reports
invariants:
  - INV-DEXTER-NO-AUTO-PROMOTE
  - INV-VARIANT-PROVENANCE
reports_to: G (strategic), CSO (evidence bundles)
repo: ~/dexter/ + ~/phoenix-synthetic/ (replica)
```

### 4.5 Task Watcher Daemon

```yaml
PURPOSE: "Detect new tasks, wake offices, monitor health"

IMPLEMENTATION:
  type: launchd plist (macOS native)
  interval: 2 minutes (explicit cadence)
  script: watch_tasks.sh

WATCH_SCRIPT:
  #!/bin/bash
  cd ~/phoenix-swarm && git pull -q

  # Check for tasks addressed to this office
  OFFICE="$1"  # CORE_CTO | CSO | DEXTER_CTO
  PENDING=$(yq ".pending[] | select(.to == \"$OFFICE\")" TASK_QUEUE.yaml)

  if [ -n "$PENDING" ]; then
    # New task! Alert or auto-launch
    echo "$(date): New task for $OFFICE" >> ~/logs/task_watcher.log
    # Optional: osascript notification or Telegram ping
  fi

LAUNCHD_PLIST:
  Label: com.phoenix.taskwatcher
  ProgramArguments: [/bin/bash, ~/phoenix-swarm/watch_tasks.sh, CORE_CTO]
  StartInterval: 120  # 2 minutes
  RunAtLoad: true

BENEFIT: "Offices don't poll manually, system wakes them"
```

### 4.6 Checkpoint Pattern

```yaml
CHECKPOINT_TRIGGERS:
  context_threshold: 70% (safety margin before death)
  progress_markers:
    - After gate pass
    - After test suite green
    - After significant milestone
  forced: 90% context (end session gracefully)

CHECKPOINT_FORMAT:
  file: checkpoints/CORE_CTO.md

  content: |
    # CORE_CTO Checkpoint
    timestamp: 2026-02-06T14:30Z
    context_pct: 72%
    state_hash: abc123 (git rev + file hashes)

    ## Active Task
    task_id: T002
    mission: S45 Research UX
    progress: "Gate 1-3 complete, working on Gate 4"

    ## State
    files_modified: [hunt/lens.py, tests/test_lens.py]
    tests_status: 14 passing, 2 failing
    current_focus: "Fix lens preset validation"

    ## Next Actions
    1. Fix test_lens_preset_validation
    2. Implement chunked output
    3. Wire journey UI

    ## Context for Fresh Session
    Read S45 brief: results/briefs/T002_BRIEF.md
    Key decision: Using Pydantic for lens schema (matches S43 pattern)

RESUME_PROTOCOL:
  1: Fresh session starts
  2: Load identity from AGENTS.md
  3: Check checkpoint file for interrupted work
  4: If checkpoint exists: Load context, continue
  5: If no checkpoint: Check TASK_QUEUE for next task
```

### 4.7 Git Operations

```yaml
SYNC_PROTOCOL:
  before_read: git pull
  after_write: git add + commit + push
  conflict: Human resolves (rare if scoped properly)

GIT_WORKTREES (Elevated Pattern):
  purpose: "Parallel edits, zero conflict even on overlapping domains"
  flow: |
    1: Office claims task
    2: git worktree add ../tasks/T001_DEXTER origin/main
    3: cd to worktree, work, commit
    4: Push worktree branch
    5: G/Core merges via PR or fast-forward
  benefit: "Real parallel execution, not turn-taking"

GIT_HOOKS:
  pre-commit: |
    - grep -r "ANTHROPIC_API_KEY" . && exit 1  # Block secrets
    - Run invariant checks
    - Test gate (if configured)
  purpose: "Catch heresy at commit, not review"

BRANCH_LINKING:
  pattern: result_branch in TASK_QUEUE done entry
  merge: git merge --no-ff dexter/T001-taxonomy
  benefit: "Full git provenance on all work"
```

---

## 5. TOOL STACK

### 5.1 Orchestration: n8n

```yaml
TOOL: n8n
ROLE: Orchestration backbone
STATUS: RECOMMENDED (Grok frontier sweep winner)

WHY_CLAUDE_LOVES_IT: |
  Visual canvas = zero hallucination on flow logic.
  Drag-drop nodes (HTTP, GitHub, Telegram, Execute Command, OpenAI/Anthropic, local Python).
  Claude describes flow → Cursor builds in minutes.

SETUP:
  command: docker run -d -p 5678:5678 n8n
  import: JSON workflow from prompt
  headless: Native cron triggers, webhook listeners

SOVEREIGN: Local instance per office, no cloud leak

USE_CASES:
  DEXTER: Heavy backtest/Monte Carlo/evidence pipelines (local Python exec + git push)
  CSO: Light review gates (Telegram trigger → Opus judgment → promote/reject)
  CORE: Dev handoff flows (pull promoted facts → code gen → test gate → push)
  G: Oversight dashboard + veto webhooks

ALTERNATIVE: Node-RED (lighter, if n8n feels heavy on Minis)
```

**DECISION_POINT_1:**
```yaml
CHOICE: n8n deployment scope
OPTIONS:
  a: All offices get n8n
  b: DEXTER only (heavy), others use git heartbeat
  c: DEXTER + CORE, CSO/G stay light
RECOMMENDATION: Option B initially, expand if valuable
```

### 5.2 Secretless Tool Calling: Composio

```yaml
TOOL: Composio
ROLE: MCP-style tool broker
STATUS: HIGH_VALUE (bleeding edge quant favorite)

WHY: |
  Claude calls Composio MCP endpoints instead of raw API keys.
  Broker injects creds, scopes, retries, logs without exposure.
  Agent NEVER touches secrets.

SETUP:
  local: Docker self-hosted broker
  cloud: Private keys option (if needed)

FLOW:
  1: Agent configured with placeholder endpoints
  2: Agent calls http://localhost:composio/anthropic/v1/messages
  3: Composio validates request, injects real key
  4: Composio forwards to real API
  5: Response returns to agent
  6: Real key never in agent memory

NODE_FIT: |
  DEXTER calls Composio for Perplexity/OpenRouter/Anthropic/IBKR paper.
  Zero secret exposure even if agent context is compromised.
```

**DECISION_POINT_2:**
```yaml
CHOICE: Composio deployment timing
OPTIONS:
  a: Phase 1 (deploy with Mission Control)
  b: Phase 2 (after v0.1, security hardening)
RECOMMENDATION: Phase 2 (Phase 1 uses Keychain + launch script)
```

### 5.3 Persistent Memory: Letta (MemGPT)

```yaml
TOOL: Letta (formerly MemGPT)
ROLE: Persistent memory + self-editing agents
STATUS: HIGH_VALUE (emerging in pro quant threads)

WHY: |
  Claude instance gets infinite context via external memory server.
  Auto-summarizes, retrieves, edits own memory.
  Never forgets long-term state.

SETUP:
  local: Docker per node, SQLite backend
  interface: Simple chat API

NODE_FIT:
  CSO: Recognition patterns (similar past setups promoted)
  DEXTER: Evidence history (hypothesis tracking)

BENEFIT: "Buttery persistence without token death"
```

**DECISION_POINT_3:**
```yaml
CHOICE: Letta deployment
OPTIONS:
  a: All offices get Letta
  b: DEXTER only (longest context needs)
  c: Defer to Phase 2
RECOMMENDATION: Option C (checkpoints sufficient for Phase 1)
```

### 5.4 Local Inference: Ollama + Open WebUI

```yaml
TOOL: Ollama + Open WebUI
ROLE: Local LLM dashboard + API
STATUS: REQUIRED (for DEXTER sovereign operation)

WHY: |
  Claude calls Ollama API for local Kimi/Qwen/Gemma routing.
  No OpenRouter tax on grunt work.
  24/7 sovereign operation if APIs unavailable.

SETUP:
  ollama: brew install ollama (or Docker)
  models: ollama pull kimi-2.5, qwen3-72b, gemma3-27b
  webui: Docker for management dashboard

NODE_FIT: DEXTER only (needs 512GB RAM for large models)

MODEL_ROUTING:
  local_sovereign:
    use_when:
      - High volume, low judgment (extraction batches)
      - 24/7 continuous operation required
      - Cost sensitivity (>1000 calls/day)
      - Privacy critical (Olya's notes stay local)
    examples:
      - Transcript → claim extraction (volume)
      - Classification tasks (bead routing)
      - Summarization (Chronicler)
      - Schema validation
      - Similarity/clustering

  claude_api:
    use_when:
      - High judgment required
      - Complex reasoning chains
      - Agentic task execution
      - Code generation/review
      - Strategic synthesis
    examples:
      - CTO sessions (architecture decisions)
      - Auditor (falsification checks)
      - Theorist on complex documents
      - Hypothesis evaluation
```

### 5.5 Retrieval: Qdrant

```yaml
TOOL: Qdrant (local vector DB)
ROLE: Evidence & hypothesis retrieval
STATUS: VALUABLE (boosts CSO recognition)

WHY: |
  DEXTER embeds evidence bundles → stores in local Qdrant.
  Claude queries for similar past patterns before new backtest.
  CSO: "Show me similar OTE+FVG setups we promoted"

SETUP: Docker local instance

NODE_FIT:
  DEXTER: Evidence embedding and storage
  CSO: Recognition queries
```

**DECISION_POINT_4:**
```yaml
CHOICE: Qdrant deployment
OPTIONS:
  a: Phase 1 (enable recognition from day one)
  b: Phase 2 (after core coordination stable)
RECOMMENDATION: Option B (nice-to-have, not blocking)
```

### 5.6 Browser Automation: Playwright

```yaml
TOOL: Playwright (headless browser)
ROLE: IBKR paper login, data pulls, external scraping
STATUS: OPTIONAL (if needed)

WHY: |
  Claude automates IBKR paper login, data pulls without manual eyes.
  DEXTER pulls fresh market context if needed.

SETUP: Local Playwright or self-hosted Browserless

NODE_FIT: DEXTER only (if IBKR automation needed)
```

### 5.7 Tool Stack Summary

```yaml
PHASE_1_REQUIRED:
  - n8n: DEXTER (orchestration)
  - Ollama: DEXTER (local models)
  - Git + launch scripts: ALL (coordination)

PHASE_1_OPTIONAL:
  - n8n: CORE (if workflow complexity warrants)
  - Qdrant: DEXTER (recognition boost)

PHASE_2_ADDITIONS:
  - Composio: ALL (secretless tool calling)
  - Letta: DEXTER + CSO (persistent memory)
  - Playwright: DEXTER (if needed)

AVOID:
  - CrewAI / AutoGen: Too chatty, high hallucination tax
  - Zapier / Make: Cloud-heavy, not sovereign
  - OpenClaw full stack: Bloat + security risks
```

---

## 6. SECURITY MODEL

### 6.1 Phase 1: MVP Security

```yaml
STATUS: "Good enough for controlled environment"
TIMELINE: Deploy with Mission Control bootstrap

PATTERN: "Wrapper script + macOS Keychain"

HOW_IT_WORKS:
  1: Real secrets stored in macOS Keychain (per Mac)
  2: launch_office.sh reads from Keychain, sets env vars
  3: Script launches Claude Code with env vars injected
  4: Agent sees env vars, uses them, but CAN'T persist or echo
  5: Session ends, env vars gone

LAUNCH_SCRIPT:
  #!/bin/bash
  # launch_office.sh — run this, not raw Claude

  export ANTHROPIC_API_KEY=$(security find-generic-password -s "phoenix-anthropic" -w)
  export OPENROUTER_API_KEY=$(security find-generic-password -s "phoenix-openrouter" -w)
  export IBKR_PAPER_ACCOUNT=$(security find-generic-password -s "phoenix-ibkr-paper" -w)

  # Launch Claude Code with identity
  OFFICE_IDENTITY="$1"  # CORE_CTO | CSO | DEXTER_CTO
  claude --project ~/phoenix-swarm --system-prompt "$(cat AGENTS.md | grep -A50 $OFFICE_IDENTITY)"

SECURITY_POSTURE:
  - Keys never in repo
  - Keys never in agent's persistent memory
  - Keys in Keychain (encrypted at rest)
  - Agent could theoretically echo them (Phase 2 fixes this)
  - ACCEPTABLE for controlled dev environment

GIT_HOOKS:
  pre-commit: grep -r "ANTHROPIC_API_KEY\|OPENROUTER\|IBKR" . && exit 1
  purpose: Block any secrets from entering repo

VERSION_PINNING:
  claude_code: Pin to specific version in launch script
  pattern: |
    CLAUDE_VERSION="1.2.3"  # Lock version to avoid breaking changes
    claude --version | grep -q "$CLAUDE_VERSION" || {
      echo "ERROR: Expected Claude Code $CLAUDE_VERSION"
      exit 1
    }
  docker_images: Pin all images with sha256 digest (not :latest)
  rationale: "Dependency hell avoidance — reproducible across all Macs"
```

### 6.2 Phase 2: Hardened Security

```yaml
STATUS: "Production-grade, 24/7 safe"
TIMELINE: Post v0.1, dedicated sprint

UPGRADE_1_GATEWAY_PROXY:
  what: Tiny localhost service intercepts API calls, injects credentials

  architecture:
    agent_config: |
      ANTHROPIC_API_BASE=http://localhost:9001/anthropic
      OPENROUTER_API_BASE=http://localhost:9001/openrouter

    proxy_flow:
      1: Agent calls http://localhost:9001/anthropic/v1/messages
      2: Proxy validates request (basic sanity)
      3: Proxy reads real key from Keychain
      4: Proxy forwards to https://api.anthropic.com with real key
      5: Proxy returns response to agent
      6: Real key NEVER in agent memory

  implementation:
    - ~100 LOC Go/Node service
    - Runs as launchd daemon on each Mac
    - Reads from Keychain, never logs keys
    - Logs call metadata (for audit) without secrets

UPGRADE_2_SCOPED_TOKENS:
  what: Each office gets minimum necessary access

  scopes:
    CORE_CTO: Anthropic (full), IBKR (paper only)
    CSO: Anthropic (read-heavy), no IBKR
    DEXTER_CTO: Anthropic + OpenRouter + Perplexity, IBKR (paper replica)

  enforcement: Proxy checks office identity, applies scope

UPGRADE_3_AUDIT_TRAIL:
  what: Every API call logged with provenance

  log_format:
    timestamp: 2026-02-06T14:30:00Z
    office: DEXTER_CTO
    endpoint: anthropic/v1/messages
    model: claude-opus-4-5
    tokens_in: 1200
    tokens_out: 800
    task_id: T001
    # NO secrets logged

  storage: Shared Datasette DB or append-only log file

UPGRADE_4_AUTO_SPAWN_DAEMON:
  what: Watchdog that restarts offices on checkpoint

  flow:
    1: Daemon monitors checkpoints/ for recent writes
    2: If checkpoint + no heartbeat in 5 min → session died
    3: Daemon launches fresh session for that office
    4: Fresh session loads checkpoint, continues
```

---

## 7. INFRASTRUCTURE BOOTSTRAP

### 7.1 Monorepo Pattern

```yaml
INSIGHT: "One repo, one script, infinite nodes, zero spaghetti"

STRUCTURE:
  phoenix-swarm/  # OR a8ra-infra/ as sibling
    docker-compose.yml           # Base services
    .env.example                 # Template secrets
    nodes/
      dexter/
        docker-compose.override.yml   # DEXTER-specific (heavy)
        n8n-workflows/                # JSON exports
      cso/
        docker-compose.override.yml   # Light
      core/
        docker-compose.override.yml
      g-sovereign/
        docker-compose.override.yml
    bootstrap.sh                 # One-command node slurper
    README.md                    # "How to become a node in 60 seconds"
```

### 7.2 Bootstrap Script

```bash
#!/usr/bin/env bash
# bootstrap.sh — the divine slurper (run on every Mac)
set -euo pipefail

echo "Phoenix Mission Control bootstrap"

# 1. Pull latest master plan
if [ ! -d "phoenix-swarm" ]; then
  git clone https://github.com/YOUR_ORG/phoenix-swarm.git
fi
cd phoenix-swarm
git pull origin main

# 2. Pick node identity (or pass as arg)
NODE_ID="${1:-dexter}"  # default to dexter
echo "Becoming node: $NODE_ID"

# 3. Copy .env from template if missing
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "→ .env created — FILL SECRETS NOW (Keychain or manual)"
  exit 1
fi

# 4. Merge node-specific compose + run
docker compose -f docker-compose.yml -f "nodes/$NODE_ID/docker-compose.override.yml" up -d --remove-orphans

echo "Node $NODE_ID awake — heartbeat should pulse in 30s"
echo "Check: docker ps | grep phoenix"
echo "n8n UI: http://localhost:5678 (if enabled)"
echo "Ollama: http://localhost:11434 (if enabled)"
```

### 7.3 Bootstrap Sequence

```yaml
HOUR_1_SHARED_REPO:
  - Create phoenix-swarm/ on G's Mac
  - git init, add structure (HEARTBEAT, TASK_QUEUE, AGENTS, etc.)
  - Push to private remote (GitHub private or self-hosted)
  - Clone to other Macs

HOUR_2_SECRETS_SETUP:
  - Add secrets to macOS Keychain on each Mac
  - Write launch_office.sh script
  - Test: script launches Claude with env vars
  - Verify: agent can call Anthropic API

HOUR_3_OFFICE_IDENTITIES:
  - Write AGENTS.md with office definitions
  - Test: fresh Claude session loads identity correctly
  - Test: session orients from HEARTBEAT + TASK_QUEUE

HOUR_4_TASK_FLOW:
  - G writes first task to TASK_QUEUE
  - Target office claims task
  - Office completes, writes result
  - Verify: full cycle works with git sync

HOUR_5_CHECKPOINT_PATTERN:
  - Test: Opus writes checkpoint at 70%
  - Test: Fresh session loads checkpoint
  - Test: Work continues from checkpoint

HOUR_6_DEXTER_REPLICA:
  - Clone phoenix/ to Dexter Mac as phoenix-synthetic/
  - Configure separate paper IBKR account
  - Run test suite, verify green
  - DEXTER_CTO confirms synthetic environment ready

HOUR_7_8_INTEGRATION_TEST:
  - G broadcasts task to all offices
  - Each office claims appropriate work
  - Offices execute in parallel
  - Results appear in shared repo
  - Verify: no conflicts, clean merge

TOTAL_BOOTSTRAP: ~6-8 hours focused work
```

---

## 8. WORKFLOW EXAMPLES

### 8.1 Olya Hypothesis → Evidence Bundle

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
    TASK_QUEUE.yaml:
      pending:
        - id: T042
          from: CSO
          to: DEXTER_CTO
          mission: "Backtest hypothesis: OTE + FVG confluence"
          brief_path: results/briefs/T042_OTE_FVG.md
          data_scope: "2023-2024 London session"
          validation: "S39 full suite"
  compute: None (git push)

STEP_3_EXECUTE (DEXTER Office):
  dexter_action: Claims task, runs backtest
  compute: HEAVY
    - Load synthetic Phoenix
    - Parse hypothesis into test parameters
    - Run walk-forward validation
    - Run Monte Carlo (1000 iterations)
    - Generate evidence bundle
  time: Minutes to hours (depending on scope)
  output: results/T042_DEXTER_EVIDENCE.md

STEP_4_NOTIFY (DEXTER → CSO):
  dexter_action: Updates TASK_QUEUE (done), posts to HEARTBEAT
  format: "@CSO evidence bundle T042 ready for review"
  optional: Telegram notification to Olya

STEP_5_REVIEW (CSO Office):
  olya_action: Reviews evidence bundle
  surface: Markdown with decomposed metrics (no scalars)
  decision:
    - PROMOTE → becomes FACT_BEAD
    - REJECT → becomes NEGATIVE_BEAD (reason captured)
    - REQUEST_MORE → new task to DEXTER
  compute: Minimal (reading, judgment)

STEP_6_INTEGRATE (CSO → CORE):
  if_promoted:
    - CSO updates conditions.yaml with new gate
    - Posts to TASK_QUEUE: "@CORE integrate validated gate"
    - CORE picks up, adds to production Phoenix
  if_rejected:
    - NEGATIVE_BEAD feeds back to DEXTER Theorist context
    - Learning loop closes
```

### 8.2 Sprint Execution Flow

```yaml
SCENARIO: "Execute S45 Research UX"

STEP_1_BROADCAST (G):
  action: G posts sprint brief to TASK_QUEUE
  format: |
    TASK_QUEUE.yaml:
      pending:
        - id: T050
          from: G
          to: CORE_CTO
          mission: "Execute S45 Research UX sprint"
          brief_path: results/briefs/S45_BRIEF.md
          priority: P1
          gates: [1, 2, 3, 4, 5]

STEP_2_CLAIM (CORE Office):
  action: CORE_CTO claims task
  loads: S45 brief, existing context
  plans: Gate-by-gate execution

STEP_3_EXECUTE (CORE Office):
  action: Sequential gate execution
  pattern: Build → Test → Checkpoint → Next gate
  checkpoints: After each gate pass
  blockers: Posted to TASK_QUEUE as blocked (if any)

STEP_4_GATE_REVIEWS (G):
  action: G reviews at sprint boundary
  decision: Approve / Request changes
  timing: Async (G checks when available)

STEP_5_COMPLETE (CORE Office):
  action: Mark task done, post result
  output: results/T050_S45_COMPLETE.md
  branch: core/S45-research-ux (ready for merge)

STEP_6_MERGE (G):
  action: G reviews and merges to main
  verification: Tests pass, gates met
```

---

## 9. NEW INVARIANTS

### 9.1 Coordination Invariants

```yaml
INV-TASK-QUEUE-ATOMIC:
  rule: "Task claims use atomic git operations"
  mechanism: TASK_QUEUE.lock during claim, retry on conflict
  prevents: Duplicate claims, race conditions

INV-CHECKPOINT-BEFORE-DEATH:
  rule: "Checkpoint at 70% context, forced at 90%"
  mechanism: Opus monitors own context, writes checkpoint
  prevents: Lost work, orphaned tasks

INV-IDENTITY-INJECTION:
  rule: "Agent loads soul + state + tasks on every session start"
  mechanism: launch_office.sh injects from AGENTS.md + checkpoints/
  prevents: Disoriented sessions, wrong identity

INV-BRANCH-LINKING:
  rule: "All task results live in git branches, merged via PR"
  mechanism: result_branch in TASK_QUEUE → G merges --no-ff
  prevents: Untraceable changes, lost provenance

INV-HEARTBEAT-CADENCE:
  rule: "Update HEARTBEAT on start, claim, progress, blocker, end"
  mechanism: Office appends status on key events
  prevents: Stale awareness, coordination gaps
```

### 9.2 Security Invariants

```yaml
INV-NO-SECRETS-IN-REPO:
  rule: "Git hooks block credential patterns"
  mechanism: pre-commit grep for API keys, exit 1 if found
  prevents: Accidental secret commits

INV-KEYCHAIN-ONLY:
  rule: "Secrets never in agent persistent memory"
  mechanism: Keychain → env vars → session end → gone
  prevents: Secret persistence across sessions

INV-PROXY-INJECTION (Phase 2):
  rule: "Agent never possesses credentials"
  mechanism: Gateway proxy injects on request
  prevents: Secret exposure even if agent compromised

INV-SCOPED-ACCESS (Phase 2):
  rule: "Each office gets minimum necessary permissions"
  mechanism: Proxy validates office identity, applies scope
  prevents: Privilege escalation
```

### 9.3 Operational Invariants

```yaml
INV-OFFICE-SCOPED-WORK:
  rule: "Each office only claims tasks addressed to them"
  mechanism: to: field in TASK_QUEUE entries
  prevents: Duplicate work, authority confusion

INV-G-BROADCAST-ONLY:
  rule: "Only G writes to pending tasks"
  mechanism: Git commit author verification (optional)
  prevents: Unauthorized task injection

INV-SOVEREIGN-VETO:
  rule: "G can halt/override any task via BROADCAST"
  mechanism: HALT entry in BROADCAST.md → all offices check on wake
  prevents: Runaway execution without human control

INV-RESULT-PROVENANCE:
  rule: "All results are beads with full lineage"
  mechanism: Standard bead format, hash validation
  prevents: Untraceable outputs

INV-COST-CEILING:
  rule: "Token/cost budget per office with effort param"
  mechanism: Office config includes effort_level (low/medium/high) → maps to daily budget
  budget_tiers:
    low: $1/day (CSO review sessions)
    medium: $10/day (CORE dev work)
    high: $50/day (DEXTER extraction + backtests)
  enforcement: n8n workflow tracks spend, pauses office at ceiling
  override: G can raise ceiling via BROADCAST
  prevents: Runaway API costs, uncontrolled spend
```

---

## 10. DECISION POINTS SUMMARY

```yaml
# For planning session — explicit choices to make

DECISION_POINT_1:
  topic: n8n deployment scope
  options:
    a: All offices get n8n
    b: DEXTER only (heavy), others use git heartbeat
    c: DEXTER + CORE, CSO/G stay light
  recommendation: B
  impact: Setup complexity vs orchestration power

DECISION_POINT_2:
  topic: Composio deployment timing
  options:
    a: Phase 1 (deploy with Mission Control)
    b: Phase 2 (after v0.1, security hardening)
  recommendation: B
  impact: Security posture vs setup speed

DECISION_POINT_3:
  topic: Letta (persistent memory) deployment
  options:
    a: All offices get Letta
    b: DEXTER only (longest context needs)
    c: Defer to Phase 2
  recommendation: C
  impact: Memory richness vs complexity

DECISION_POINT_4:
  topic: Qdrant (vector DB) deployment
  options:
    a: Phase 1 (enable recognition from day one)
    b: Phase 2 (after core coordination stable)
  recommendation: B
  impact: Recognition boost vs focus

DECISION_POINT_5:
  topic: Hardware allocation
  options:
    a: As specified (M3 Ultra for DEXTER, etc.)
    b: Start with existing hardware, upgrade later
  recommendation: A (if M3 Ultra available)
  impact: Sovereign capability vs cost

DECISION_POINT_6:
  topic: Bootstrap sequence
  options:
    a: Full 8-hour bootstrap before any sprint work
    b: Minimal bootstrap (shared repo + identities), iterate
  recommendation: A (measure twice, cut once)
  impact: Time to autonomy vs early progress

DECISION_POINT_7:
  topic: DEXTER Phoenix replica priority
  options:
    a: Immediate (blocks Olya hypothesis testing)
    b: After CORE starts S45 (parallel track)
  recommendation: A (enables CSO workflow immediately)
  impact: Olya productivity vs CORE velocity
```

---

## 11. DEPENDENCIES & PREREQUISITES

```yaml
HARDWARE_PREREQUISITES:
  g_sovereign: Mac Mini M4 Pro (or any modern Mac)
  core_office: Mac Studio M4 Max (or high-spec alternative)
  cso_office: Mac Mini (any M-series)
  dexter_office: M3 Ultra 512GB (critical for local models)

ACCOUNT_PREREQUISITES:
  anthropic: Claude Max x20 for DEXTER + CORE, x5 for G + CSO
  ibkr_paper: TWO accounts (dev + synthetic)
  openrouter: For DEXTER volume routing
  perplexity: For DEXTER research enrichment
  github: Private repo for phoenix-swarm/

SOFTWARE_PREREQUISITES:
  all_macs:
    - macOS with Keychain Access
    - Git + SSH keys
    - Docker Desktop (or Colima)
    - Claude Code CLI + authenticated
    - Python 3.11+ with venv
  dexter_additional:
    - ollama (brew install ollama)
    - Large model weights (Kimi 2.5, Qwen3-72B)

KNOWLEDGE_PREREQUISITES:
  - Understanding of Phoenix architecture (S28-S47)
  - ENDGAME_VISION_v0.2.md context
  - Git workflow proficiency
  - Basic Docker Compose understanding
```

---

## 12. RISK INVENTORY

```yaml
RISK_1_COORDINATION_OVERHEAD:
  issue: Shared board adds latency vs direct conversation
  mitigation:
    - Task watcher daemon (2min poll)
    - Telegram bridge for urgent alerts
    - Offices work async, don't wait for sync
  residual: Acceptable (async is feature, not bug)

RISK_2_SECRET_EXPOSURE:
  issue: Phase 1 env vars could theoretically be echoed
  mitigation:
    - Controlled dev environment only
    - Phase 2 proxy eliminates exposure
    - Git hooks block repo commits
  residual: Acceptable for Phase 1

RISK_3_CONTEXT_DEATH:
  issue: Despite 1M context, complex tasks could still hit limits
  mitigation:
    - 70% checkpoint threshold (safety margin)
    - Progress-marker checkpoints (meaningful, not arbitrary)
    - Auto-spawn daemon (Phase 2)
  residual: Low (1M is substantial, checkpoints proven)

RISK_4_HARDWARE_DEPENDENCY:
  issue: M3 Ultra critical for DEXTER sovereign operation
  mitigation:
    - API-only mode as fallback (degraded but functional)
    - Prioritize M3 Ultra acquisition
  residual: Medium (without it, Dexter loses 24/7 local capability)

RISK_5_SCOPE_CREEP:
  issue: Mission Control itself is infrastructure, not v0.1 feature
  mitigation:
    - 6-8 hour bootstrap cap
    - Phase 1 vs Phase 2 separation
    - INV-NO-CORE-REWRITES still applies
  residual: Low (clear phasing, explicit scope)

RISK_6_OLYA_WORKFLOW_GAP:
  issue: CSO workflow depends on DEXTER replica + evidence bundles
  mitigation:
    - Prioritize DEXTER replica setup
    - Existing Mirror Report can bridge
  residual: Medium (workflow incomplete until replica ready)

RISK_7_COORDINATION_RESILIENCE:
  issue: Swarm coordination not stress-tested before production
  mitigation_phase_1:
    - Hour 7-8 integration test validates happy path
    - Manual chaos injection during bootstrap (drop a node, corrupt TASK_QUEUE)
  mitigation_phase_2:
    - CHAOS_BUNNY_OFFICE: Synthetic office that claims random tasks + injects failures
    - Proves: recovery from stale heartbeats, checkpoint resume, conflict resolution
  sprint_target: Phase 2 hardening (post v0.1)
  residual: Low (Phase 1 controlled, Phase 2 proves resilience)
```

---

## 13. RELATIONSHIP TO OTHER DOCS

```yaml
ENDGAME_VISION_v0.2.md:
  relationship: "Mission Control is enabling infrastructure for ENDGAME"
  update_needed: Add section linking to this design doc

SPRINT_ROADMAP.md:
  relationship: "Mission Control bootstrap precedes S45-S52 parallel execution"
  update_needed: Add bootstrap as enabling work

PHOENIX_MANIFEST.md:
  relationship: "Office architecture is new organizational layer"
  update_needed: Add office section, new invariants

CARTRIDGE_AND_LEASE_DESIGN_v1.0.md:
  relationship: "Peer design doc — same pattern (measure twice, cut once)"
  update_needed: None

PRODUCT_VISION.md:
  relationship: "Mission Control enables 24/7 operation vision"
  update_needed: Add Section 13 summary
```

---

## 15. PATTERN VALIDATION: a8ra_web

```yaml
INSIGHT: |
  Before Mission Control bootstrap, the pattern was proven in production
  via the a8ra.com autonomous art installation (Picasso Forge).

PICASSO_FORGE_ARCHITECTURE:
  trigger: "404-minute epochs (6.7 hours)"
  divergent_generation: 3 sub-agents (VISCERAL, DREAMSCAPE, GEOMETRIC)
  optionality: 2 candidates per agent (6 total)
  curation: Harsh Picasso judgment layer (rejects mediocrity)
  bounded_iteration: Max 2 curation loops
  fallback: Procedural generation if forge fails
  delivery: Auto-commit → auto-deploy → auto-publish to X

MAPS_TO_MISSION_CONTROL:
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
  uptime: Continuous

WHAT_THIS_PROVES:
  - Multi-agent coordination works
  - Git-based state management works
  - Cron-triggered autonomy works
  - Bounded iteration prevents runaway
  - Graceful fallback handles failures
  - Self-commit + self-deploy + self-publish is viable

CONFIDENCE_BOOST: |
  Mission Control is Picasso Forge at enterprise scale.
  The pattern is proven. Now we scale it to Phoenix.
```

---

## 16. NEXT ACTIONS

```yaml
IMMEDIATE (planning session):
  1: Review this design doc with CTO
  2: Make decisions on DECISION_POINTs 1-7
  3: Lock design version (v0.2 with decisions)

POST_PLANNING:
  4: Execute bootstrap sequence (6-8 hours)
  5: Verify office coordination with test task
  6: Begin S45 via CORE_OFFICE
  7: Begin DEXTER replica setup (parallel)

POST_V0.1:
  8: Phase 2 security hardening
  9: Tool stack expansion (Composio, Letta, etc.)
  10: Auto-spawn daemon
```

---

```yaml
DOCUMENT_STATUS:
  version: 0.1.1
  status: DESIGN_DRAFT | CTO_REVIEWED
  ready_for: Planning session decisions
  next_version: 0.2 (with locked decisions)
  cto_review: PASSED (4 minor gaps patched)
  gaps_patched:
    - INV-COST-CEILING (Section 9.3)
    - CHAOS_BUNNY_OFFICE (Section 12, RISK_7)
    - VERSION_PINNING (Section 6.1)
    - WATCHER_CADENCE (Section 4.5, explicit 2min interval)
```

---

*Captured: 2026-02-09*
*Source: G + CTO + Grok advisor synthesis (2026-02-06 to 2026-02-08)*
*Pattern: CARTRIDGE_AND_LEASE_DESIGN paradigm*

**OINK OINK.** 🐗🔥
