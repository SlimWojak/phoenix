# T4: ESCALATION LADDER — a8ra v0.1

```yaml
TRACK: S50.T4.ESCALATION_LADDER
DATE: 2026-02-22
OWNER: CTO (draft) → G (review + sign)
FORMAT: 1-page operational reference
```

---

## ESCALATION LADDER — WHO GETS WOKEN, FOR WHAT

```yaml
# Posted: operator workstation + mobile command plane
# Rule: Every alert maps to exactly ONE escalation path. No ambiguity.
```

### TIER 0: SYSTEM SELF-HEALS (no human)

```yaml
triggers:
  - Heartbeat stale < 60s (watchdog auto-restart)
  - Single component DEGRADED → circuit breaker FSM handles
  - API rate limit hit → exponential backoff
  - Transient network blip → reconnect loop

action: System handles. Logged. No notification.
human_sees: HUD shows DEGRADED briefly, returns to HEALTHY.
```

### TIER 1: NOTIFY G (glanceable, non-urgent)

```yaml
triggers:
  - Component DEGRADED > 5min (not self-healing)
  - Heartbeat stale > 60s (watchdog failed to restart)
  - Disk usage > 80%
  - API key expiry < 7 days
  - Lease expiry < 24hr (attestation reminder)
  - Calibration drift > 5% WARN threshold
  - ChadBoar canary anomaly (informational)

channel: ntfy push notification (Phase 1) → Matrix (Phase 2)
urgency: Check within 1hr during market hours. Next session if off-hours.
action_required: Monitor. Intervene if persists.
```

### TIER 2: ALERT G (requires action)

```yaml
triggers:
  - IBKR Gateway disconnected > 5min
  - Daemon crash (not auto-restarted)
  - Multiple components DEGRADED simultaneously
  - Disk usage > 95%
  - Lease EXPIRED without renewal (no active governance)
  - Calibration drift > 10% BLOCK threshold
  - Guard dog REJECT on live cartridge
  - Test suite regression detected (CI/hook failure)

channel: ntfy HIGH priority → Matrix @mention (Phase 2)
urgency: Respond within 15min during market hours. 1hr off-hours.
action_required: Diagnose + fix or halt.
```

### TIER 3: HALT FIRES (system protects itself, G informed after)

```yaml
triggers:
  - Any INV-HALT-1 / INV-HALT-2 condition
  - Bounds breach (INV-LEASE-CEILING)
  - Position lifecycle invariant violation
  - halt_cascade triggered
  - Unrecoverable state (FSM cannot transition)

channel: ALL channels simultaneously (ntfy CRITICAL + Matrix + HUD red)
urgency: IMMEDIATE — but system has already halted. G confirms + investigates.
action_required: |
  1. Confirm halt is holding (HUD check)
  2. Read halt bead (reason, timestamp, trigger)
  3. Diagnose root cause
  4. Decision: REVOKE lease + new lease, OR fix + restart
  5. NEVER override halt without understanding cause
```

### TIER 4: SOVEREIGN OVERRIDE (G only, manual)

```yaml
triggers:
  - Market event requiring immediate position exit
  - System compromise suspected
  - "Pull the plug" — any reason, no justification needed

action: |
  G has direct IBKR access independent of Phoenix.
  G can flatten all positions manually via IBKR Trader Workstation.
  Phoenix halt is secondary confirmation, not primary control.

rule: INV-SOVEREIGN-1 — Human sovereignty over capital is absolute.
```

---

## CONTACT CHAIN

```yaml
OPERATIONAL_HOURS:
  market: "London 08:00-17:00 UTC / NY 13:00-22:00 UTC"
  monitoring: "System monitors 24/7. Human response expected during market hours."

PRIMARY: G
  channel: [ntfy mobile, Matrix mobile, HUD desktop]
  response_target: T1 (1hr) / T2 (15min) / T3 (immediate-after-halt) / T4 (at will)

SECONDARY: None (v0.1 is single-operator)
  future: "When team grows, secondary on-call rotation"

METHODOLOGY: Olya (CSO)
  when: "Gate calibration questions, methodology drift, CLAIM→FACT promotion"
  channel: "Direct message (not automated)"
  never: "Olya is never woken for system issues. Only methodology."
```

---

## RUNBOOK QUICK REFERENCE

```yaml
IBKR_DISCONNECT:
  check: "IBKR Trader Workstation running? VPN up? API port 4001/4002 open?"
  fix: "Restart TWS → verify_office.sh PHOENIX → check HUD"
  escalate_if: "Won't reconnect after 3 attempts"

DAEMON_CRASH:
  check: "Which daemon? Check logs: tail -50 ~/.phoenix/logs/{daemon}.log"
  fix: "Restart via bootstrap.sh (idempotent) or manual service restart"
  escalate_if: "Crashes repeatedly (>3 in 1hr)"

DISK_FULL:
  check: "df -h / du -sh ~/.phoenix/data/*"
  fix: "Archive old beads, rotate logs, clear tmp"
  escalate_if: "Data growth rate unsustainable — architecture review needed"

API_KEY_EXPIRY:
  check: "Which key? OpenRouter / IBKR / other"
  fix: "Rotate key in macOS Keychain (INV-NO-SECRETS-IN-FILES)"
  note: "7-day warning gives plenty of runway"

LEASE_EXPIRED:
  check: "Intentional (no trading this week) or forgot attestation?"
  fix: "Create new lease (PERISH_BY_DEFAULT — cannot resurrect)"
  note: "System safe without active lease — just won't trade"
```

---

```yaml
SIGNED: CTO (draft)
REQUIRES: G review + sign-off ("I know who to call")
DATE: 2026-02-22
```
