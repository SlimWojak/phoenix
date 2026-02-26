# ═══════════════════════════════════════════════════════════════
# OPUS BRIEF: a8ra HARDENING — S55 through S58
# ═══════════════════════════════════════════════════════════════

```yaml
document: OPUS_BRIEF_HARDENING
version: 1.0
date: 2026-02-25
from: CTO (Claude)
to: OPUS (Cursor, MAX reasoning)
status: G-LOCKED — execute as written
format: DENSE_M2M
priority: CRITICAL — constitutional hardening before any office goes live

CLASSIFICATION: |
  This is not a feature build. This is a HARDENING sprint sequence.
  A forensic audit of all 4 system nodes (phoenix-swarm, phoenix,
  dexter, oracle) revealed 1 T1 risk, 4 T2 risks, and 7 T3 risks.
  Three advisors (GPT/OWL/BOAR) pressure-tested the fix plan.
  G has locked the plan. Execute precisely.

EXECUTION_SEQUENCE:
  S55_HALT_WIRE: "Constitutional kill switch (¾ day)"
  S56_LOUD_FAILS: "Silent fail hardening (¾ day, PARALLEL with S55)"
  BOOT_GATE: "Cold boot validation (2hrs, SEQUENTIAL gate)"
  S57_ORACLE_BOOTSTRAP: "Build what was promised (1 day, AFTER S55)"
  S58_HYGIENE: "Dead code + doc cleanup (½ day, ANYTIME)"

REPOS:
  phoenix: ~/phoenix (capital engine, v0.1 sealed)
  phoenix-swarm: ~/phoenix-swarm (coordination layer)
  dexter: ~/dexter (bead field, Gate 1)
  oracle: ~/oracle (Olya's office — currently 2 files)
```

---

# ═══════════════════════════════════════════════════════════════
# FORENSIC CONTEXT — WHY THIS MATTERS
# ═══════════════════════════════════════════════════════════════

```yaml
AUDIT_FINDINGS:

  phoenix_swarm:
    status: SCAFFOLDED_INFRASTRUCTURE
    real_files: 6 of 28
    T1: "HALT.signal mechanism DESIGNED_NOT_BUILT"
    T2: "Silent git failures in 3 scripts"
    T2: "API keys fall to empty string without abort"
    T2: "BROADCAST.md 16 days stale"

  phoenix:
    status: SUBSTANTIALLY_REAL
    real_dirs: 12 of 17 (non-capital-path)
    T2: "kill_manager.py silent except-pass on bead writes"
    note: "Capital path clean (S54 TRUTH_SWEEP). Non-capital infrastructure solid."

  dexter:
    status: GATE_1_CONFIRMED (7/7 criteria met)
    T2: "pipeline.py broad exception conflates benign and catastrophic"
    note: "DEC-SUBSTRATE-FREEZE active. Bug fixes only."

  oracle:
    status: SKELETON (2 files)
    T1: "HALT authority promised, zero implementation"
    T2: "CLAUDE.md describes CSO-only, BROADCAST promises Three-Surface Cockpit"

  ROOT_CAUSE: |
    The single T1 risk (HALT mechanism) appears in TWO sweeps (swarm + oracle).
    It is ONE problem: Olya was promised a kill switch. Nothing exists.
    Fix it once, resolve both T1s.

ADVISOR_SYNTHESIS:
  accepted_additions: 14 (across all sprints)
  deferred: 4 (analyst sandbox, auto-clear, resource checker, beads mining)
  new_invariants: 5
  key_convergence:
    - "HALT must be FAIL-CLOSED (all 3 advisors)"
    - "All capital paths must check HALT (GPT + OWL)"
    - "Boot-time validation as gate (GPT + BOAR)"
    - "One real query beats 20 pages of docs (GPT)"
```

---

# ═══════════════════════════════════════════════════════════════
# S55: HALT_WIRE — Constitutional Kill Switch
# ═══════════════════════════════════════════════════════════════

```yaml
BRIEF: S55.HALT_WIRE.WED
MISSION: Wire the constitutional kill switch end-to-end
OWNER: OPUS
FORMAT: DENSE
EFFORT: ¾ day

CONTEXT:
  status: |
    INV-OLYA-HALT-AUTHORITY is constitutional — "Olya can trigger
    halt_cascade at any time without G approval."
    INV-HALT-HUMAN-ONLY-RESTART — "No agent/daemon/cron can clear HALT."
    NEITHER IS IMPLEMENTED.
    Phoenix governance/halt.py exists (internal halt, <50ms proven).
    What's missing: the EXTERNAL halt signal that Olya/swarm can write
    and that the execution engine checks.
  proven:
    - governance/halt.py: HaltManager, halt_local < 50ms
    - daemons/routing.py: create_halt_handler() → HaltManager (internal path)
    - tests/daemons/test_halt_priority.py: HALT priority routing proven

PURPOSE:
  build: External HALT.signal mechanism (write + check + clear + audit)
  invariants:
    - INV-HALT-SIGNAL-CHECK: "Execution gate checks HALT.signal before every capital action"
    - INV-HALT-CLEAR-LOGGED: "Every HALT clear event logged with timestamp and operator"
    - INV-HALT-FAIL-CLOSED: "Corrupted/unreadable HALT.signal = HALTED, not bypassed"
    - INV-HALT-ENTROPY-PROOF: "Halt mechanism survives 5 chaos vectors without silent fail"
```

## S55 Track 1: HALT.signal Write Mechanism

```yaml
TASK:
  1: |
    Create phoenix-swarm/scripts/halt.sh
    Usage: ./halt.sh <SOURCE> <REASON>
    SOURCE must be: OLYA | G | GOVERNANCE | SYSTEM_WATCHDOG
    Writes JSON to phoenix-swarm/HALT.signal:
      {"source": "<SOURCE>", "timestamp": "<ISO8601>", "reason": "<REASON>", "schema_version": 1}
  2: |
    halt.sh must be IDEMPOTENT — multiple invocations overwrite cleanly.
    No append. Overwrite-safe. Double-click safe.
  3: |
    halt.sh must VALIDATE source argument against allowed enum.
    Invalid source → exit 1 with clear error, no file written.
  4: |
    After writing HALT.signal, also append structured entry to
    ~/logs/a8ra/halt_history.log:
      {"event": "HALT_SET", "actor": "<SOURCE>", "timestamp": "<ISO>", "reason": "<REASON>"}

DELIVERABLES:
  code:
    - phoenix-swarm/scripts/halt.sh
  tests:
    - "Manual: ./halt.sh OLYA 'test halt' → HALT.signal exists with valid JSON"
    - "Manual: ./halt.sh INVALID 'test' → exit 1, no file"
    - "Manual: ./halt.sh OLYA 'first' && ./halt.sh OLYA 'second' → file contains 'second' only"
```

## S55 Track 2: Execution Gate Check

```yaml
TASK:
  1: |
    Add to governance/halt.py:
      def check_halt_signal(swarm_path: Path = Path.home() / "phoenix-swarm") -> HaltSignalResult:
    Returns: HaltSignalResult(halted: bool, source: str | None, reason: str | None, error: str | None)
  2: |
    FAIL-CLOSED BEHAVIOR (critical):
      - HALT.signal exists with valid JSON → halted=True, populate source/reason
      - HALT.signal exists but JSON invalid → halted=True, error="corrupt signal"
      - HALT.signal exists but unreadable (permissions) → halted=True, error="unreadable"
      - HALT.signal does not exist → halted=False (normal operation)
      - swarm_path does not exist → halted=True, error="swarm path missing"
    RULE: ANY error condition = HALTED. Only clean absence = proceed.
  3: |
    GREP ALL CAPITAL-ENTRY FUNCTIONS across phoenix/:
      - execution/asia_scalp.py (or any execution engine entry)
      - governance/insertion.py (lease insertion)
      - Any function that can place, modify, or cancel an order
    WRAP each with check_halt_signal() call at entry.
    If halted: log warning, return HALTED status, take no action.
  4: |
    Also add check to governance/lease.py LeaseStateMachine:
      - DRAFT→ACTIVE transition must check halt signal
      - If halted: refuse activation, return error

DELIVERABLES:
  code:
    - governance/halt.py (check_halt_signal function + HaltSignalResult dataclass)
    - Modifications to every capital-entry function identified by grep
  tests:
    - tests/test_halt_signal.py:
      - test_halt_signal_present → check returns halted=True
      - test_halt_signal_absent → check returns halted=False
      - test_halt_signal_corrupt_json → check returns halted=True (FAIL-CLOSED)
      - test_halt_signal_unreadable → check returns halted=True (FAIL-CLOSED)
      - test_halt_signal_missing_swarm → check returns halted=True (FAIL-CLOSED)
      - test_execution_refuses_when_halted → execution gate returns HALTED
      - test_lease_activation_refuses_when_halted → lease stays DRAFT

EXIT_GATE: |
  check_halt_signal() returns correct result for ALL 5 cases.
  Every capital-entry function refuses action when HALT.signal present.
  Fail-closed: corrupt/missing/unreadable → HALTED, not bypassed.
```

## S55 Track 3: Restart Guard

```yaml
TASK:
  1: |
    Create phoenix-swarm/scripts/clear_halt.sh
    Requires interactive confirmation: "HALT was set by <source> for: <reason>. Clear? [y/N]"
    On confirm: removes HALT.signal, logs to halt_history.log:
      {"event": "HALT_CLEARED", "actor": "G_MANUAL", "timestamp": "<ISO>", "original_source": "<source>", "original_reason": "<reason>"}
  2: |
    clear_halt.sh must NOT be callable from:
      - cron (check: if tty not attached, exit 1)
      - piped input (check: if not interactive terminal, exit 1)
    REQUIRES human at keyboard.
  3: |
    If HALT.signal doesn't exist, clear_halt.sh exits with: "No active HALT."

DELIVERABLES:
  code:
    - phoenix-swarm/scripts/clear_halt.sh
  tests:
    - "Manual: ./clear_halt.sh with HALT.signal → prompts, clears on 'y'"
    - "Manual: echo 'y' | ./clear_halt.sh → rejects (not interactive)"
    - "Manual: ./clear_halt.sh without HALT.signal → 'No active HALT'"
```

## S55 Track 4: Oracle HALT Surface

```yaml
TASK:
  1: |
    Update ~/oracle/CLAUDE.md to include HALT authority section:
      ## HALT Authority (Constitutional)
      You have HALT authority. Olya can halt the system at any time.
      Command: Run ~/phoenix-swarm/scripts/halt.sh OLYA "<reason>"
      This immediately stops all capital actions system-wide.
      Only G can clear the halt.
  2: |
    Verify: Oracle agent can execute halt.sh from ~/oracle/ context.
    The ~/phoenix-swarm/scripts/ path must be accessible.

DELIVERABLES:
  code:
    - ~/oracle/CLAUDE.md (HALT section added)
  tests:
    - "Manual: from oracle context, run halt.sh → HALT.signal created"
```

## S55 Track 5: Chaos Vectors

```yaml
TASK:
  1: |
    Create tests/test_halt_chaos.py with 5 vectors:
      V1: Invalid JSON in HALT.signal → check_halt_signal returns halted=True
      V2: Race condition — two concurrent halt.sh writes → file is valid JSON after both complete
      V3: HALT.signal with unknown schema_version → check returns halted=True (fail-closed, don't reject unknown versions)
      V4: HALT.signal with missing fields → check returns halted=True (fail-closed)
      V5: HALT.signal is zero bytes → check returns halted=True (fail-closed)
  2: |
    Create tests/test_halt_active_interrupt.py:
      Design test for future active interrupt pattern:
      - Function exists: halt_interrupt(execution_pids: list[int]) → sends SIGTERM
      - 2s grace → SIGKILL
      - Test with mock subprocess
      NOTE: This function is DESIGNED AND TESTED but NOT wired into daemon loop.
      Daemon wiring is a future sprint when execution daemon runs on M3.

DELIVERABLES:
  tests:
    - tests/test_halt_chaos.py (5 vectors)
    - tests/test_halt_active_interrupt.py (design + test, not wired)

EXIT_GATE_S55: |
  ALL of:
    - halt.sh writes valid HALT.signal ✓
    - check_halt_signal fail-closed on ALL error cases ✓
    - Every capital-entry function checked (grep audit documented) ✓
    - clear_halt.sh requires interactive human ✓
    - 5 chaos vectors pass ✓
    - halt_interrupt function exists and tested ✓
    - Oracle CLAUDE.md has HALT instructions ✓
    - halt_history.log captures all events ✓

PASS_CONDITION: "Olya can halt from Oracle. Phoenix refuses actions. Only G clears. Chaos-proven."
FAIL_CONDITION: "Any capital path bypasses HALT check. Any error case = not-halted."

NEW_INVARIANTS:
  INV-HALT-SIGNAL-CHECK: "Execution gate checks HALT.signal before every capital action"
  INV-HALT-CLEAR-LOGGED: "Every HALT clear event logged with timestamp and operator"
  INV-HALT-FAIL-CLOSED: "Corrupted/unreadable HALT.signal = HALTED, not bypassed"
  INV-HALT-ENTROPY-PROOF: "Halt mechanism survives 5 chaos vectors without silent fail"

HALT_SIGNAL_SCHEMA:
  version: 1
  sources: [OLYA, G, GOVERNANCE, SYSTEM_WATCHDOG]
  note: "SYSTEM_WATCHDOG included for future auto-halt (river heartbeat timeout, resource exhaustion). Not implemented in S55 but schema must accommodate."
```

---

# ═══════════════════════════════════════════════════════════════
# S56: LOUD_FAILS — Silent Fail Hardening
# ═══════════════════════════════════════════════════════════════

```yaml
BRIEF: S56.LOUD_FAILS.WED
MISSION: Convert silent failures to loud failures across all repos
OWNER: OPUS
FORMAT: DENSE
EFFORT: ¾ day
PARALLEL: Can execute simultaneously with S55 (different files)

CONTEXT:
  status: |
    Forensic audit found pattern: except Exception → pass/log/continue
    across capital-adjacent paths. Kill state can be lost silently.
    Alert delivery failures invisible. Scripts exit 0 on partial failure.
  proven:
    - phoenix capital path: mypy strict clean (governance/ execution/ cso/)
    - Tests: 1786 passing
    - Pattern is in INFRASTRUCTURE code, not capital path

PURPOSE:
  build: Loud-fail wrappers on all silent-fail paths
  invariant: INV-CONFIG-VALID-ON-BOOT
```

## S56 Track 1: Global Exception Scan

```yaml
TASK:
  1: |
    Run across BOTH repos:
      grep -rn "except Exception" ~/phoenix/
      grep -rn "except:" ~/phoenix/
      grep -rn "except Exception" ~/phoenix-swarm/
    Also check dexter (but DO NOT modify — DEC-SUBSTRATE-FREEZE):
      grep -rn "except Exception" ~/dexter/dexter/bead_field/
  2: |
    Classify EVERY hit into:
      A: BENIGN_BEST_EFFORT — alert delivery, logging, cleanup (acceptable)
      B: CAPITAL_ADJACENT — kill state, halt checks, execution paths (MUST FIX)
      C: DATA_INTEGRITY — bead writes, river writes, state mutations (MUST FIX)
    Document in: phoenix/docs/forensic_audit/audit_250226/exception_scan.yaml
  3: |
    For every B and C classification: apply fix per tracks below.
    For every A classification: add comment "# BEST-EFFORT: exception logged but non-blocking"

DELIVERABLES:
  docs:
    - phoenix/docs/forensic_audit/audit_250226/exception_scan.yaml
```

## S56 Track 2: Phoenix kill_manager.py

```yaml
TASK:
  1: |
    File: monitoring/kill_manager.py
    Find all `except Exception: pass` around bead writes.
    Replace with: except Exception as e: log.error(f"Kill bead write failed: {e}"); raise
  2: |
    Capital-adjacent bead writes MUST propagate failure.
    If kill state cannot be persisted, caller must know.

DELIVERABLES:
  code:
    - monitoring/kill_manager.py (silent pass → loud error)
  tests:
    - tests/test_kill_manager_loud.py:
      - test_bead_write_failure_propagates → injected failure raises, not swallowed
```

## S56 Track 3: Swarm Script Hardening

```yaml
TASK:
  1: |
    File: phoenix-swarm/scripts/launch_office.sh
    Changes:
      a. git pull failure → set STALE_COORDINATION=true, print BOLD WARNING
      b. DEXTER: empty OPENROUTER_API_KEY → exit 1 (DEXTER needs API)
      c. PHOENIX/ORACLE: empty optional keys → WARN but continue
      d. Add: command -v yq >/dev/null 2>&1 || { echo "ERROR: yq required. brew install yq"; exit 1; }
  2: |
    File: phoenix-swarm/scripts/session_end_hook.sh
    Changes:
      a. git add/commit/push failure → write to LOCAL fallback:
         ~/logs/a8ra/failed_checkpoints.log with timestamp, session_id, office
      b. Do NOT lose checkpoint data on push failure
      c. Git push: use lock-and-rebase pattern:
         flock -n .git/a8ra_push.lock || { log "push locked, saving locally"; exit 0; }
         git pull --rebase && git push || { log "push failed, saved locally"; }
         NOTE: flock may not be available on macOS — use mkdir lock pattern instead:
         mkdir .git/a8ra_push.lock 2>/dev/null || { log "locked"; exit 0; }
         trap "rmdir .git/a8ra_push.lock 2>/dev/null" EXIT
  3: |
    File: phoenix-swarm/scripts/status.sh
    Changes:
      a. Check yq installed at top, exit 1 with install instruction if missing
      b. git pull failure → print WARNING, continue with local state but flag output as STALE
  4: |
    ALL SCRIPTS: ensure explicit exit codes. No silent exit 0 on partial failure.
    Success = exit 0. Partial failure = exit 1. Fatal = exit 2.

DELIVERABLES:
  code:
    - phoenix-swarm/scripts/launch_office.sh (hardened)
    - phoenix-swarm/scripts/session_end_hook.sh (hardened + lock pattern)
    - phoenix-swarm/scripts/status.sh (hardened)
  tests:
    - "Manual: remove yq → launch_office.sh exits with clear message"
    - "Manual: empty OPENROUTER_API_KEY → DEXTER launch aborts, PHOENIX continues"
```

## S56 Track 4: Config Validation on Boot

```yaml
TASK:
  1: |
    File: phoenix/config/schema.py (Pydantic config)
    Add boot-time validation that FAILS LOUD on:
      a. Missing IB credentials (if execution mode = paper or live)
      b. Missing DB path or invalid path
      c. Missing river path or invalid path
    Use Pydantic validators. Raise on missing required config, don't default.
  2: |
    File: phoenix-swarm/scripts/launch_office.sh
    After env var injection, before launching claude:
      Validate required paths exist:
        - ~/phoenix-swarm/ exists
        - ~/phoenix/ exists (for PHOENIX office)
        - ~/dexter/ exists (for DEXTER office)
        - ~/oracle/ exists (for ORACLE office)
      Missing → exit 1 with clear error

DELIVERABLES:
  code:
    - phoenix/config/schema.py (boot validation)
    - phoenix-swarm/scripts/launch_office.sh (path validation)
  tests:
    - tests/test_config_boot.py:
      - test_missing_ib_creds_raises → ValidationError on missing creds
      - test_invalid_db_path_raises → ValidationError on bad path
  invariant: INV-CONFIG-VALID-ON-BOOT

EXIT_GATE_S56: |
  ALL of:
    - Exception scan documented (every hit classified) ✓
    - Zero silent except-pass on capital-adjacent or data-integrity paths ✓
    - kill_manager propagates bead write failures ✓
    - Scripts fail loud with correct exit codes ✓
    - Config validation rejects missing/invalid on boot ✓
    - yq dependency checked in all scripts that use it ✓

PASS_CONDITION: "grep -r 'except.*pass' on capital paths returns zero hits. All scripts have explicit exit codes."
FAIL_CONDITION: "Any capital-adjacent silent fail remains."
```

---

# ═══════════════════════════════════════════════════════════════
# BOOT_GATE: Cold Boot Validation
# ═══════════════════════════════════════════════════════════════

```yaml
BRIEF: BOOT_GATE.WED
MISSION: Validate all offices boot clean after S55+S56 hardening
OWNER: OPUS + G (manual validation)
FORMAT: DENSE
EFFORT: 2 hours
WHEN: AFTER S55 and S56 both complete. BEFORE S57 starts.

TASK:
  1: |
    Fresh terminal. No pre-existing env vars. Simulate cold boot:
      a. cd ~/phoenix-swarm && ./scripts/status.sh
         Expected: runs without error, shows OFFLINE offices, no HALT
      b. ./scripts/launch_office.sh PHOENIX (just launch, can ctrl-c after boot)
         Expected: env injected, git pull works or warns loud, claude launches
      c. ./scripts/halt.sh OLYA "boot gate test"
         Expected: HALT.signal created
      d. Verify: from phoenix context, any capital function returns HALTED
      e. ./scripts/clear_halt.sh (interactive)
         Expected: prompts, clears, logs
  2: |
    Document results in:
      phoenix-swarm/forensic_review/BOOT_GATE_RESULTS.yaml

EXIT_GATE: "All 5 steps pass. No silent errors. No missing dependencies."
BLOCKING: "If boot gate fails, S57 does not start. Fix first."
```

---

# ═══════════════════════════════════════════════════════════════
# S57: ORACLE_BOOTSTRAP — Build What Was Promised
# ═══════════════════════════════════════════════════════════════

```yaml
BRIEF: S57.ORACLE_BOOTSTRAP.WED
MISSION: Build Olya's Three-Surface Cockpit to operational Phase 1
OWNER: OPUS + CTO (design input)
FORMAT: DENSE
EFFORT: 1 day
DEPENDENCY: S55 complete (HALT must be wired to document in CLAUDE.md)

CONTEXT:
  status: |
    Oracle = 2 files (CLAUDE.md + settings.local.json).
    BROADCAST promises Three-Surface Cockpit: CSO + Analyst + HUD.
    Olya's stated needs: live state, positions, PnL, setups, kill switch, detail.
    Kill switch will exist after S55. Everything else = this sprint.
    PRINCIPLE: "Phase 1 Cockpit — limited automation. Honest about what's real."
  proven:
    - CLAUDE.md has valid CSO foundation (identity, invariants, ICT terms)
    - SessionEnd hook correctly wired
    - River operational (EURUSD 1m, keepUpToDate, launchd)
    - HUD operational (SwiftUI, manifest_writer)
```

## S57 Track 1: CLAUDE.md Full Rewrite

```yaml
TASK:
  1: |
    Rewrite ~/oracle/CLAUDE.md as THREE-SURFACE document.
    PRESERVE from current: ICT terminology, invariants, memory hygiene, identity.
    ADD:
      a. HALT authority section (from S55 — exact command, what it does, who clears)
      b. Analyst surface section:
         - What Analyst CAN do: DuckDB queries, cat/grep phoenix files, market_state_builder, git pull
         - What Analyst CANNOT do: write/edit phoenix files, git push, install packages, restart daemons
         - Enforcement: instruction-based for Phase 1, OS-level read-only mount for Phase 2
      c. HUD section: "Read-only glanceable surface. Shows system state, river status, HALT status."
      d. Current system state: post-S54, v0.1, river live, 1786 tests, 240 invariants
      e. Olya's capabilities mapped:
         - "In-the-moment knowledge" → DuckDB queries via Analyst
         - "Setups forming" → CSO gate evaluation (when running)
         - "Kill switch" → halt.sh command
         - "Detail of trading system" → read-only access to phoenix/
         - "Live positions / PnL" → NOT YET (IB account query = future sprint)
  2: |
    EXPECTATION LABELING (critical for trust):
    Explicitly state in CLAUDE.md:
      "This is Phase 1 Cockpit — limited automation."
      "IB position/PnL polling is not yet implemented."
      "HUD shows Phoenix state, not live market data."
      "Analyst queries require read-only mount from M3 (planned Thu/Fri)."
  3: |
    BOOT SEQUENCE updated:
    Add: "Check HALT.signal — if present, report to Olya and await G clearance."

DELIVERABLES:
  code:
    - ~/oracle/CLAUDE.md (full rewrite)
```

## S57 Track 2: Directory Structure

```yaml
TASK:
  1: |
    Create Oracle workspace directories:
      mkdir -p ~/oracle/notes
      mkdir -p ~/oracle/memory
    Initialize:
      echo "# Oracle Archive — completed tasks and historical decisions" > ~/oracle/memory/archive.md
      echo "# Oracle Patterns — recurring gotchas and learned behaviors" > ~/oracle/memory/patterns.md
  2: |
    Create ~/oracle/.claude/settings.local.json if not exists (it does exist, verify)

DELIVERABLES:
  dirs:
    - ~/oracle/notes/
    - ~/oracle/memory/
    - ~/oracle/memory/archive.md
    - ~/oracle/memory/patterns.md
```

## S57 Track 3: Minimal Real Data Proof

```yaml
TASK:
  1: |
    Create ~/oracle/examples/first_query.sh:
    A WORKING DuckDB query that Olya's Analyst can run:
      duckdb -readonly ~/phoenix-river/EURUSD/2026/02/*.parquet \
        "SELECT bar_time, open, high, low, close FROM read_parquet('*.parquet') ORDER BY bar_time DESC LIMIT 5"
    NOTE: Adjust path if river parquet location differs. Check ~/phoenix-river/ structure.
  2: |
    Create ~/oracle/examples/gate_status.sh:
    Show current CSO gate status (if evaluator available) or conditions.yaml summary:
      cat ~/phoenix/cso/knowledge/conditions.yaml | head -50
    Simple. Real. Proves access works.
  3: |
    NOTE: These examples require the read-only network mount from M3.
    If mount not yet available (Thu/Fri), document as:
      "Run these after network mount configured. Until then, SSH to M4 Max."

DELIVERABLES:
  code:
    - ~/oracle/examples/first_query.sh
    - ~/oracle/examples/gate_status.sh
```

## S57 Track 4: Swarm Broadcast Update

```yaml
TASK:
  1: |
    Update ~/phoenix-swarm/BROADCAST.md to current state:
      - STATUS: NOMINAL
      - FOCUS: Post-forensic-audit hardening (S55-S58)
      - HALT: NONE (mechanism now OPERATIONAL after S55)
      - Standing orders updated to reflect current sprint state
      - Last updated: 2026-02-25 by G (via CTO brief)
  2: |
    Commit with message: "broadcast: update to post-S54 + hardening state"

DELIVERABLES:
  code:
    - ~/phoenix-swarm/BROADCAST.md (updated)
```

## S57 Track 5: Dry-Run Script

```yaml
TASK:
  1: |
    Create ~/oracle/examples/dry_run.sh:
    Olya's confidence-building rehearsal:
      echo "=== a8ra Oracle Dry Run ==="
      echo ""
      echo "1. Checking system state..."
      cat ~/phoenix-swarm/BROADCAST.md | grep -E "STATUS:|HALT:|FOCUS:"
      echo ""
      echo "2. Checking HALT status..."
      if [ -f ~/phoenix-swarm/HALT.signal ]; then
        echo "⚠️  HALT ACTIVE:"
        cat ~/phoenix-swarm/HALT.signal
      else
        echo "✓ No active HALT"
      fi
      echo ""
      echo "3. Testing HALT (will halt and immediately clear)..."
      ~/phoenix-swarm/scripts/halt.sh OLYA "dry run test"
      echo "HALT set. Check:"
      cat ~/phoenix-swarm/HALT.signal
      echo ""
      echo "4. Now G must clear (you cannot):"
      echo "   Run: ~/phoenix-swarm/scripts/clear_halt.sh"
      echo ""
      echo "=== Dry run complete. System is currently HALTED. ==="
      echo "=== Ask G to clear before trading resumes. ==="
  2: |
    NOTE: This script actually HALTs the system. By design.
    It proves the mechanism works. G clears after.

DELIVERABLES:
  code:
    - ~/oracle/examples/dry_run.sh

EXIT_GATE_S57: |
  ALL of:
    - CLAUDE.md rewritten with Three-Surface Cockpit ✓
    - Expectation labeling present ("Phase 1 — limited") ✓
    - HALT authority documented with exact command ✓
    - Workspace directories created ✓
    - At least one real DuckDB query example ✓
    - Dry-run script works end-to-end ✓
    - BROADCAST.md updated to current state ✓

PASS_CONDITION: "Olya opens Oracle, reads CLAUDE.md, knows exactly what she can and can't do, can halt the system, can query the river."
FAIL_CONDITION: "Any stated capability doesn't work. Any expectation mismatch between docs and reality."
```

---

# ═══════════════════════════════════════════════════════════════
# S58: HYGIENE — Dead Code, Stale Docs, Cleanup
# ═══════════════════════════════════════════════════════════════

```yaml
BRIEF: S58.HYGIENE.ANYTIME
MISSION: Clean house — no urgency, no risk, just tidy
OWNER: OPUS
FORMAT: DENSE
EFFORT: ½ day
DEPENDENCY: NONE (can run anytime, parallel with anything)

CONTEXT:
  status: "Dead code and stale docs identified in forensic audit. Not risks, but clutter."
```

## S58 Track 1: Dead Code Archival

```yaml
TASK:
  1: |
    Create phoenix/docs/archive/deprecated/ if not exists.
  2: |
    Move (git mv) phoenix/widget/ → phoenix/docs/archive/deprecated/widget/
    Add phoenix/docs/archive/deprecated/widget/__init__.py:
      raise ImportError("widget/ deprecated — superseded by surfaces/hud/ (S48). See SPRINT_ROADMAP.md")
  3: |
    Move phoenix/narrator/data_sources.py → phoenix/docs/archive/deprecated/narrator_data_sources.py
    Add comment at original location or __init__.py note:
      "data_sources.py archived — placeholder fetchers never wired. narrator_emit() (renderer.py) still active."
  4: |
    CONSTITUTION/ directory:
    Add to CONSTITUTION/README.md:
      "NOTE: Canonical invariant tracking moved to INVARIANT_REGISTRY.yaml (240 entries).
       This directory is a historical organizational artifact from S28.
       See: scripts/validate_registry.py for enforcement."
    Do NOT delete CONSTITUTION/ — it has one real entry (INV-GOV-HALT-BEFORE-ACTION.yaml).
```

## S58 Track 2: Doc Fixes

```yaml
TASK:
  1: |
    File: dexter/docs/BEAD_FIELD_SPRINT.md
    Fix contradictory running-score section (lines ~357-380):
    Remove the DUPLICATE entries. Keep ONLY the final (correct) values:
      invariants_proven: 12
      genesis_status: SIGNED (789 beads, Merkle root 5c4d...963c)
    The earlier "invariants_proven: 3" and "genesis_status: NOT_STARTED" are stale.
    NOTE: DEC-SUBSTRATE-FREEZE allows doc fixes. This is not a code change.
  2: |
    Add DELTA-16 to phoenix/docs/canon/DRIFT_LOG.md:
      ### DELTA-16: BEAD_FIELD_SPRINT Running Score Contradictory
      id: DELTA-16
      category: A_STALE_SPEC
      description: "BEAD_FIELD_SPRINT.md running-score contained duplicate YAML keys with contradictory values"
      disposition: FIXED_S58
      owner: DEXTER
      date_found: 2026-02-25
      status: FIXED
      commit_ref: "<this commit>"
```

## S58 Track 3: Dexter src/ Verification

```yaml
TASK:
  1: |
    Verify ~/dexter/src/ exists and extraction pipeline intact:
      ls -la ~/dexter/src/
      python3 -c "import sys; sys.path.insert(0, '.'); from src import <main_module>" 2>&1 || echo "IMPORT FAILED"
    If import works: document as "src/ extraction pipeline intact, ready for Olya content feed"
    If import fails: document what's broken, add to backlog
  2: |
    Record result in phoenix-swarm/forensic_review/dexter_src_verification.yaml
```

## S58 Track 4: Git Push Lock Pattern

```yaml
TASK:
  1: |
    Update phoenix-swarm/scripts/session_end_hook.sh git push section
    (if not already done in S56 T3 — may overlap, check first):
    Use mkdir lock pattern (macOS compatible):
      LOCK_DIR="$SWARM_DIR/.git/a8ra_push.lock"
      if mkdir "$LOCK_DIR" 2>/dev/null; then
        trap "rmdir '$LOCK_DIR' 2>/dev/null" EXIT
        cd "$SWARM_DIR"
        git pull --rebase -q 2>/dev/null && git push -q 2>/dev/null || {
          echo "$TIMESTAMP: push failed, checkpoint saved locally" >> "$LOGDIR/failed_checkpoints.log"
        }
      else
        echo "$TIMESTAMP: push locked by another office, checkpoint saved locally" >> "$LOGDIR/failed_checkpoints.log"
      fi

DELIVERABLES:
  code:
    - phoenix-swarm/scripts/session_end_hook.sh (if not already fixed in S56)
```

## S58 Track 5: Deprecation Guards

```yaml
TASK:
  1: |
    For any code moved to archive/deprecated/, ensure the original import
    path raises ImportError with migration message.
    Pattern:
      # In original __init__.py or replacement file:
      raise ImportError(
          "This module has been deprecated and archived. "
          "See docs/archive/deprecated/ for history. "
          "Replacement: <replacement module>"
      )

EXIT_GATE_S58: |
  ALL of:
    - Dead code archived with ImportError guards ✓
    - CONSTITUTION/README.md updated with registry pointer ✓
    - BEAD_FIELD_SPRINT.md contradictions fixed + DELTA-16 logged ✓
    - src/ verified or breakage documented ✓
    - Git push lock pattern in session_end_hook ✓

PASS_CONDITION: "No dead code in active paths. Docs match reality."
```

---

# ═══════════════════════════════════════════════════════════════
# REPORTING REQUIREMENTS
# ═══════════════════════════════════════════════════════════════

```yaml
REPORT_FORMAT: DENSE_M2M

PER_SPRINT_REPORT:
  template: |
    S{N}: {STATUS}
    MISSION: {NAME}
    RESULT: PASS|FAIL|CONDITIONAL

    TRACKS:
      T1: {status} — {one-line}
      T2: {status} — {one-line}
      ...

    NEW_FILES:
      - {path}: {purpose}

    MODIFIED_FILES:
      - {path}: {what changed}

    TESTS_ADDED: {count}
    INVARIANTS_PROVEN: [{list}]
    EXIT_GATE: {PASS|FAIL} — {evidence}

    ISSUES_FOUND:
      - {any unexpected findings during build}

FINAL_REPORT:
  after: S58 complete
  include:
    - All sprint reports
    - Updated SYSTEM_MANIFEST delta
    - Updated DRIFT_LOG entries
    - Updated INVARIANT_REGISTRY entries
    - Updated SPRINT_ROADMAP entries

GIT_HYGIENE:
  commits: "Atomic per track. Message format: S{N}-T{N}: {description}"
  branch: "main (these are hardening, not features)"
  pre_commit_hooks: "Must pass. No --no-verify."
```

---

# ═══════════════════════════════════════════════════════════════
# REFERENCE DOCUMENTS
# ═══════════════════════════════════════════════════════════════

```yaml
FORENSIC_AUDIT:
  - phoenix-swarm/forensic_review/swarm_oracle_report.md
  - phoenix-swarm/forensic_review/swarm_CTO_advisor_reviews.md
  - phoenix-swarm/forensic_review/phoenix_core_oracle_report.md
  - phoenix-swarm/forensic_review/phoenix_core_CTO_advisor_reviews.md
  - phoenix-swarm/forensic_review/dexter_oracle_report.md
  - phoenix-swarm/forensic_review/dexter_CTO_advisor_reviews.md
  - phoenix-swarm/forensic_review/oracle_CTO_advisor_reviews.md

SYSTEM_STATE:
  - a8ra_SYSTEM_MANIFEST_v1_0.md (v1.6)
  - SPRINT_ROADMAP.md (v3.0)
  - DRIFT_LOG.md (15 entries)

ARCHITECTURE:
  - a8ra_MASTER_PLAN_v0_1.md
  - BEAD_FIELD_SPEC_v0_3.md
  - CARTRIDGE_AND_LEASE_DESIGN_v1_0.md
  - MISSION_CONTROL_DESIGN_v0_2.md
```

---

```yaml
# ═══════════════════════════════════════════════════════════════
# SOVEREIGN DIRECTIVE
# ═══════════════════════════════════════════════════════════════

FROM: G (Sovereign Operator) via CTO
TO: OPUS (Primary Builder)
DATE: 2026-02-25
STATUS: LOCKED

MESSAGE: |
  This is constitutional hardening. The forensic audit revealed one
  fundamental gap: the kill switch we promised Olya doesn't exist.
  Everything else flows from fixing that.

  Build with precision. Test with paranoia. Report with honesty.
  If something doesn't fit the plan, STOP and report — don't improvise.
  
  Measure twice, cut once.

SIGNED: G
```
