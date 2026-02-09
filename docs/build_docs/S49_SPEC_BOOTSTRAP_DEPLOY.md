# S49: BOOTSTRAP & DEPLOY

```yaml
status: SPEC_DRAFT
codename: BOOTSTRAP_AND_DEPLOY
theme: "Bare Mac → operational office in one command"
replaces: "DMG Packaging (vanity — killed)"
target: a8ra v0.1 milestone (sprint 1 of 2)
estimated_duration: 2-3 days
```

---

## Philosophy

```yaml
principle: "Setup should be boring. Operating should be the craft."
anti_goal: "No GUI wizards, no code signing, no .dmg, no polish-before-purpose"
real_goal: |
  G pulls a fresh Mac out of a box.
  Runs one script.
  30 minutes later: office is operational, tests pass, heartbeat is green.
  G's attention goes to USING the system, not INSTALLING it.
```

---

## Deliverables

### D1: bootstrap.sh (Primary)

Single script that takes a bare Mac from zero to operational office.

```bash
Usage: ./bootstrap.sh PHOENIX|DEXTER|ORACLE [--skip-tests]
```

**Steps the script performs:**

```yaml
PHASE_1_DEPS: # ~10 min
  - Check/install Homebrew
  - Install: python@3.11, yq, jq, git, node (via nvm)
  - Install: mcp-memory-keeper (npm global)
  - Verify: all tools available on PATH

PHASE_2_REPOS: # ~5 min
  - Clone phoenix-swarm (coordination)
  - Clone office-specific repo:
    PHOENIX: phoenix
    DEXTER: dexter
    ORACLE: oracle (or create scaffold if no remote)
  - Set up git identity if not configured

PHASE_3_PYTHON: # ~5 min
  - Create venv: ~/.venvs/a8ra/
  - pip install -r requirements.txt (office-specific)
  - Verify: pytest importable, all deps resolved

PHASE_4_IDENTITY: # ~2 min
  - Verify CLAUDE.md exists in project root
  - Create .claude/ directory
  - Deploy hooks config (.claude/settings.local.json)
    → SessionEnd hook pointing to phoenix-swarm/scripts/session_end_hook.sh
  - Verify: hook script exists and is executable

PHASE_5_SECRETS: # Manual step (prompted)
  - Check Keychain for required secrets:
    PHOENIX: a8ra-anthropic, a8ra-ibkr-dev
    DEXTER: a8ra-anthropic, a8ra-openrouter (optional), a8ra-perplexity (optional)
    ORACLE: a8ra-anthropic
  - If missing: print exact `security add-generic-password` commands
  - Do NOT store secrets in files or env

PHASE_6_DAEMONS: # ~1 min
  - Create ~/logs/a8ra/ directory
  - Install launchd plists (office-specific):
    PHOENIX: task watcher
    DEXTER: task watcher + auto-restart + ollama watchdog
    ORACLE: task watcher
  - Load daemons

PHASE_7_VERIFY: # ~5 min (or ~10 with tests)
  - Run verify_office.sh (see D3)
  - Print summary: PASS/FAIL per check
  - Final message: "Office {NAME} operational. Run: ./scripts/status.sh"
```

**Design rules:**
- Idempotent: safe to re-run (skips already-installed components)
- Offline-tolerant: continues with warnings if GitHub/npm unreachable
- No sudo: everything user-space (Homebrew, nvm, pip in venv)
- Verbose but clean: progress indicators, no wall of text
- Exit code 0 = success, 1 = failure with clear message

---

### D2: Config Production Migration

Migrate from dev paths to production-standard locations.

```yaml
CURRENT_STATE:
  config: ~/phoenix/config/ (various .yaml files)
  schema: config/schema.py (Pydantic, from S43)
  secrets: Mixed (env vars, some hardcoded in dev)
  state: ~/phoenix/state/ (health.yaml, orientation, etc.)
  logs: Scattered

PRODUCTION_STATE:
  config: ~/phoenix/config/ (stays — it's the repo)
  secrets: macOS Keychain (via security CLI)
  state: ~/phoenix/state/ (stays — repo-managed)
  logs: ~/logs/a8ra/ (centralized)
  heartbeats: ~/phoenix-swarm/heartbeats/ (already done)
  checkpoints: ~/phoenix-swarm/checkpoints/ (already done)

MIGRATION_TASKS:
  1. Audit config/ for any hardcoded dev paths → parameterize
  2. Ensure config/schema.py validates with production values
  3. Create config/profiles/:
     - config/profiles/paper.yaml (IBKR paper mode)
     - config/profiles/live.yaml (IBKR live — future, placeholder)
  4. Centralize log paths to ~/logs/a8ra/
  5. Remove any .env files or hardcoded secrets (replace with Keychain lookups)
  6. Document: OPERATOR_SETUP.md (what config means, how to change)
```

---

### D3: verify_office.sh (Post-Bootstrap Verification)

```bash
Usage: ./verify_office.sh PHOENIX|DEXTER|ORACLE
```

```yaml
CHECKS:
  deps:
    - python3 --version (≥3.11)
    - yq --version
    - jq --version
    - git --version
    - node --version
    - claude --version (Claude Code CLI)

  repos:
    - ~/phoenix-swarm/ exists and is git repo
    - Office repo exists and is git repo
    - Both repos have clean working tree (warn if dirty)

  identity:
    - CLAUDE.md exists in project root
    - .claude/settings.local.json exists with SessionEnd hook
    - Hook script exists and is executable

  secrets:
    - Required Keychain entries exist (office-specific)
    - Print WARNING (not FAIL) for optional secrets

  connectivity:
    - git pull on phoenix-swarm (can reach GitHub)
    - IBKR paper gateway (PHOENIX only, optional)

  daemons:
    - launchd plists loaded (launchctl list | grep a8ra)
    - Log directory exists

  tests:
    - PHOENIX: pytest --co (collection only, fast) — confirms test suite loads
    - DEXTER: pytest --co (if test suite exists)
    - ORACLE: skip (no test suite)

  heartbeat:
    - Write test heartbeat → phoenix-swarm/heartbeats/
    - Verify file written correctly
    - Git commit + push (verify push works)

OUTPUT:
  Per-check: ✓ PASS | ✗ FAIL | ⚠ WARN
  Summary: "12/14 checks passed, 2 warnings, 0 failures"
  Exit code: 0 if no FAILs, 1 if any FAILs
```

---

### D4: OPERATOR_SETUP.md

Clear, concise operator guide.

```yaml
SECTIONS:
  1_prerequisites: "What you need before running bootstrap.sh"
  2_quick_start: "3 commands to go from zero to operational"
  3_secrets_setup: "How to add Keychain entries (exact commands)"
  4_config_profiles: "Paper vs live, how to switch"
  5_daemons: "What's running, how to check, how to restart"
  6_daily_operations: "status.sh, launching offices, checking heartbeats"
  7_troubleshooting: "Common issues and fixes"

TONE: Operator manual, not developer docs. Short sentences. Copy-paste commands.
```

---

## Exit Gates

```yaml
GATE_S49_1:
  name: "Fresh bootstrap"
  criterion: "bootstrap.sh PHOENIX on clean user account → verify_office.sh PASS"
  test: "Create test user on Mac Studio, run bootstrap, verify"

GATE_S49_2:
  name: "Idempotent re-run"
  criterion: "bootstrap.sh run twice → no errors, no duplicates"
  test: "Run bootstrap.sh PHOENIX twice consecutively"

GATE_S49_3:
  name: "Config migration"
  criterion: "No hardcoded dev paths in config/. Secrets in Keychain only."
  test: "grep -r '/Users/echopeso' config/ → 0 results"

GATE_S49_4:
  name: "Verify suite green"
  criterion: "verify_office.sh PHOENIX → 0 failures"
  test: "Run verify_office.sh on bootstrapped machine"

GATE_S49_5:
  name: "Daemon health"
  criterion: "Task watcher running, hook fires on session exit"
  test: "Start Claude Code session, exit, check heartbeat updated"

GATE_S49_6:
  name: "Operator docs"
  criterion: "G can follow OPERATOR_SETUP.md cold and bootstrap successfully"
  test: "G reads doc, follows steps, confirms clarity"
```

---

## Invariants

```yaml
INV-BOOTSTRAP-IDEMPOTENT:
  rule: "bootstrap.sh can be run N times without damage"
  enforcement: Skip-if-exists checks for all install steps

INV-NO-SECRETS-IN-FILES:
  rule: "Zero secrets in any repo file. Keychain only."
  enforcement: pre-commit hook (already in phoenix-swarm) + grep audit

INV-SINGLE-COMMAND-SETUP:
  rule: "One command + secrets entry = operational office"
  enforcement: Gate S49_1
```

---

## Non-Scope (Explicitly Killed)

```yaml
KILLED:
  - DMG packaging (vanity)
  - Code signing / notarization ($99/yr for no benefit)
  - First-run wizard GUI (bootstrap.sh replaces)
  - py2app / PyInstaller / Nuitka bundling
  - HUD .app bundling (separate concern, separate sprint if ever needed)
  - Automated secret provisioning (Keychain is manual, intentionally)
```

---

## Build Approach

```yaml
TRACKS:
  A_BOOTSTRAP:
    files: [bootstrap.sh, verify_office.sh]
    owner: Opus
    deps: phoenix-swarm scripts (already built)

  B_CONFIG:
    files: [config/profiles/paper.yaml, config/profiles/live.yaml, config audit]
    owner: Opus
    deps: config/schema.py (S43)

  C_DOCS:
    files: [OPERATOR_SETUP.md]
    owner: Opus (draft) → G (review for clarity)
    deps: Tracks A+B complete

SEQUENCE:
  1. A (bootstrap.sh) — this is 70% of the sprint
  2. B (config migration) — while testing bootstrap
  3. C (operator docs) — last, informed by actual experience
  4. Gates — G runs through on Mac Studio
```

---

## Success Criteria

```yaml
done_when: |
  G can pull a Mac out of a box (or wipe a user account),
  run bootstrap.sh PHOENIX, enter Keychain secrets,
  and have a fully operational Phoenix office in <30 minutes.
  verify_office.sh shows green.
  Heartbeat is updating.
  Tests pass.
  G's attention is on trading, not on setup.
```
