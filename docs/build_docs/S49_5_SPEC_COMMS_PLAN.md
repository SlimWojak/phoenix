# S49.5: MISSION CONTROL COMMUNICATIONS

```yaml
status: SPEC_LOCKED
codename: COMMS_PLAN
theme: "Sovereign mobile command — G pings from beach, swarm oinks back"
classification: BUILD_DAY (not full sprint)
target: Deploy on M3 Ultra arrival alongside swarm bootstrap
estimated_duration: Half day build + one evening polish
depends_on: S49 (bootstrap.sh operational)
```

---

## Philosophy

```yaml
principle: "Sovereign comms. No cloud middleman. No data you don't own."
anti_goal: "No Telegram (no E2EE in groups), no Signal (bot-hostile), no SaaS"
real_goal: |
  G commands from phone on a beach in Surat Thani.
  Olya reviews in Element from her desk.
  The swarm responds in seconds. E2EE everywhere.
  100 lines of Python, not a framework.
```

---

## Architecture Decision Record

```yaml
ARCHITECTURE_LOCKED:

  server: Conduit (self-hosted on M3 Ultra, Docker, ~500MB RAM)
  bot: matrix-nio Python bot (custom, ~100 LOC)
  e2ee: Pantalaimon proxy (handles key management for bots)
  clients: Element app (iOS for G, desktop for Olya)
  secrets: macOS Keychain (existing pattern)
  alerts: ntfy (Phase 1 immediate value, bridges to Matrix in Phase 2)
```

### Clear Winners

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Chat server | **Conduit** (Rust) | 500MB RAM, Docker, sovereign, runs alongside swarm on M3 |
| Bot framework | **matrix-nio** (Python) | Production-proven, async, 12K+ GitHub stars, Feb 2026 releases active |
| E2EE proxy | **Pantalaimon** | Handles bot key management transparently |
| Secrets | **macOS Keychain** | Already our pattern (INV-NO-SECRETS-IN-FILES) |
| Mobile alerts | **ntfy** (Phase 1) | 30 min deploy, immediate mobile push, bridges to Matrix later |

### Clear Kills

| Option | Verdict | Reason |
|--------|---------|--------|
| Telegram | **KILLED** | No E2EE in groups, not sovereign |
| Signal | **KILLED** | Bot-hostile, no framework |
| ntfy bidirectional | **KILLED** | One-way only (pair with Matrix instead) |
| OpenClaw | **KILLED** | 147K stars = massive dependency surface. We need 50 lines, not a framework |
| Native iOS app | **KILLED** | Kills Olya access. Matrix gives both users same experience |

### Why Not OpenClaw

```yaml
reasoning: |
  147K stars means massive dependency surface.
  We need 50 lines of Python, not a framework.
  Our bot is: receive message → claude -p → post response.
  OpenClaw solves problems we don't have.
```

### Why Not Native iOS

```yaml
reasoning: |
  Kills Olya access (she needs the same interface).
  Matrix gives both users same experience.
  Element iOS app already exists and is polished.
```

---

## The Bot Is Trivial

```yaml
receive: matrix-nio async message handler
process: subprocess.run(["claude", "-p", message, "--project", "~/phoenix-swarm/"])
respond: post stdout back to room
state: --resume SESSION_ID per channel (multi-turn works)
total_code: ~100 lines of Python + config
```

```python
# Pseudocode — the actual bot
async def on_message(room, event):
    if event.sender == bot_user:
        return

    message = event.body
    office = room_to_office(room.room_id)

    result = subprocess.run(
        ["claude", "-p", message, "--project", f"~/{office}/"],
        capture_output=True, text=True, timeout=300
    )

    await client.room_send(room.room_id, "m.room.message", {
        "msgtype": "m.text",
        "body": result.stdout
    })
```

---

## Phased Deployment

### Phase 1: ntfy Alerts (DEPLOY NOW — 30 min)

```yaml
scope: Mobile push alerts from swarm heartbeats
when: NOW (Mac Studio, pre-M3)
effort: 30 minutes
value: Immediate mobile alerts — 3am wake-ups handled

deliverables:
  - ntfy topic configured
  - Heartbeat alert hook → ntfy push
  - G's phone receives swarm alerts
  - One-way only (alert → phone, no response)

implementation:
  - Self-hosted ntfy or ntfy.sh (public, no secrets in message)
  - Pipe from watchdog scripts → curl ntfy endpoint
  - iOS/Android ntfy app for push notifications
```

### Phase 2: Matrix + Bot (ON M3 ARRIVAL — half day)

```yaml
scope: Full sovereign comms — bidirectional command + control
when: M3 Ultra arrival (co-deploy with swarm bootstrap)
effort: Half day build + evening polish
value: G commands from phone, Olya reviews, swarm responds

deliverables:
  D1: Conduit server (Docker on M3 Ultra)
  D2: Pantalaimon E2EE proxy
  D3: Matrix rooms (#mission-control, #oracle, #alerts)
  D4: matrix-nio Python bot (~100 LOC)
  D5: Heartbeat alert bridge (ntfy → Matrix #alerts)
  D6: Test: G commands from phone, Olya reviews in #oracle
```

---

## Build Scope (Phase 2 Detail)

### Step 1: Conduit Server (~30 min)

```yaml
method: Docker on M3 Ultra
resource: ~500MB RAM, minimal CPU
config:
  - docker-compose.yml with volume mounts
  - Federation disabled (private server)
  - Registration disabled (invite-only)
  - TLS via reverse proxy or Tailscale

docker_flags:
  --cpu-shares: 512  # Prevent idle CPU drain (DUMB_1 prevention)
  --restart: unless-stopped
  volumes: /data persistent  # Survives M3 reboot (DUMB_5 prevention)
```

### Step 2: Pantalaimon E2EE Proxy (~30 min)

```yaml
purpose: Handles E2EE key management so bots don't need to
deployment: Docker alongside Conduit
config:
  - Bot connects through Pantalaimon
  - Pantalaimon handles device verification
  - panctl available for key reset (DUMB_2 recovery)

bootstrap_test: GT-7 simulates device add to verify E2EE handshake
```

### Step 3: Rooms

```yaml
rooms:
  "#mission-control":
    purpose: G sovereign command channel
    members: [G, bot]
    bot_behavior: Full claude -p access with --project ~/phoenix-swarm/

  "#oracle":
    purpose: Oracle/CSO review channel
    members: [G, Olya, bot]
    bot_behavior: claude -p with --project ~/oracle/

  "#alerts":
    purpose: Automated alerts from swarm
    members: [G, Olya]
    bot_behavior: Read-only alert posting (heartbeats, watchdogs, task changes)
    source: ntfy bridge + heartbeat hooks
```

### Step 4: Bot (~100 LOC)

```yaml
file: phoenix-swarm/comms/mc_bot.py
framework: matrix-nio (async)
features:
  - Message handler → claude -p subprocess
  - Room-to-office mapping (#mission-control → phoenix-swarm, #oracle → oracle)
  - --resume SESSION_ID per channel (multi-turn state)
  - Timeout wrapper: 300s max per command (DUMB_3 prevention)
  - --max-turns=50 flag to prevent bloat (DUMB_3 prevention)
  - Prefix parser for sensitive commands + confirm hook (DUMB_4 mitigation)
  - Error formatting (subprocess failures → clean Matrix messages)

safeguards:
  - Bot ignores own messages (echo prevention)
  - Sensitive command confirmation: "Are you sure? Reply YES to proceed"
  - Subprocess timeout kills hung claude -p processes
  - Max message length (truncate to Matrix limits)
```

### Step 5: Alert Hooks

```yaml
integration:
  - session_end_hook.sh → post to #alerts
  - watchdog_disk.sh → post to #alerts (>80% usage)
  - watchdog_ollama.sh → post to #alerts (Ollama restart)
  - task_watcher → post to #alerts (new task claimed/completed)

method: curl Matrix API or ntfy bridge
```

### Step 6: Test

```yaml
GT_8_MOBILE_COMMAND:
  test: "G pings from phone, swarm oinks back"
  scenario: |
    G opens Element on iPhone.
    Types: "status" in #mission-control.
    Bot runs: claude -p "status" --project ~/phoenix-swarm/
    Bot posts: status.sh output to room.
    G reads on beach in Surat Thani.
  pass_criteria: Response within 60 seconds, correct status displayed

GT_9_OLYA_REVIEW:
  test: "Olya reviews in #oracle"
  scenario: |
    Olya opens Element desktop.
    Reviews Oracle channel for methodology updates.
    Can ask questions, bot responds via claude -p --project ~/oracle/
  pass_criteria: Olya can interact naturally without technical setup

GT_10_ALERT_FLOW:
  test: "Heartbeat alert reaches both users"
  scenario: |
    Watchdog detects disk >80%.
    Alert posted to #alerts room.
    G and Olya both see notification.
  pass_criteria: Alert received on mobile + desktop within 2 minutes
```

---

## Chaos Injections (Grok)

```yaml
DUMB_1:
  attack: "Conduit Docker untuned eats 5% CPU idle on M3"
  prevention: "--cpu-shares=512 flag"
  monitoring: Heartbeat watchdog includes Docker CPU check

DUMB_2:
  attack: "Pantalaimon key mismatch on bot verify"
  blast: E2EE lockout
  recovery: "panctl reset"
  prevention: "Bootstrap GT-7 simulates device add"

DUMB_3:
  attack: "Bot subprocess claude -p hangs on 1M context bloat"
  impact: Room silent
  fix: "--max-turns=50 + timeout wrapper in nio handler (300s)"

DUMB_4:
  attack: "Olya typos command, bot hallucinates"
  risk: Wrong swarm poke
  mitigation: "Bot prefix parser + confirm hook for sensitive commands"

DUMB_5:
  attack: "M3 reboot loses Conduit state"
  prevention: "Volume mount /data persistent, Docker --restart=unless-stopped"
```

---

## Exit Gates

```yaml
GATE_S49_5_1:
  name: "ntfy alerts live"
  criterion: "Heartbeat alert → ntfy → phone notification in <2 min"
  phase: 1

GATE_S49_5_2:
  name: "Conduit operational"
  criterion: "Conduit running in Docker, Federation disabled, rooms created"
  phase: 2

GATE_S49_5_3:
  name: "E2EE verified"
  criterion: "Pantalaimon proxy operational, bot can read/write encrypted rooms"
  phase: 2

GATE_S49_5_4:
  name: "Bot responds"
  criterion: "Message in #mission-control → claude -p → response posted in <60s"
  phase: 2

GATE_S49_5_5:
  name: "Mobile command (GT-8)"
  criterion: "G commands from phone, swarm responds correctly"
  phase: 2

GATE_S49_5_6:
  name: "Olya access (GT-9)"
  criterion: "Olya can interact via Element desktop without technical setup"
  phase: 2

GATE_S49_5_7:
  name: "Alert flow (GT-10)"
  criterion: "Watchdog alert → #alerts room → both users notified"
  phase: 2
```

---

## Invariants

```yaml
INV-COMMS-SOVEREIGN:
  rule: "All communication infrastructure self-hosted. No cloud middleman."
  enforcement: Conduit on M3 Ultra, no external dependencies

INV-COMMS-E2EE:
  rule: "All rooms encrypted end-to-end. No plaintext message storage."
  enforcement: Pantalaimon proxy, Element mandatory verification

INV-BOT-NO-AUTONOMOUS:
  rule: "Bot executes human commands only. Never initiates actions."
  enforcement: Message handler pattern — respond only, never propose

INV-BOT-TIMEOUT:
  rule: "Bot subprocess hard-capped at 300s + 50 turns. No infinite hangs."
  enforcement: subprocess timeout + --max-turns flag
```

---

## Bootstrap Integration

```yaml
bootstrap_addition: |
  bootstrap.sh gains MISSION_CONTROL office type (Phase 2, M3 only):
    - Docker + docker-compose install check
    - Conduit container pull + config
    - Pantalaimon container pull + config
    - Bot virtualenv + matrix-nio install
    - Room creation + user invite
    - Bot service registration (launchd)

  New plist: com.a8ra.comms.conduit.plist (Docker container)
  New plist: com.a8ra.comms.bot.plist (matrix-nio bot)

  verify_office.sh gains:
    - Docker container health check
    - Room accessibility check
    - Bot responsiveness check (ping/pong)
```

---

## Non-Scope

```yaml
NOT_THIS_BUILD:
  - Multi-server federation (private server only)
  - Custom Element theme/branding
  - Voice/video calls
  - File sharing beyond text
  - Bot memory beyond --resume (no custom persistence)
  - Admin dashboard
  - User registration (invite-only, 2 users)
```

---

## Frontier Validation (2026-02-09)

```yaml
conduit: |
  Still gold. Docker Mac deploys seamless, 500MB confirmed.
  conduit.rs docs + Railway templates affirm low-maintenance sovereign.

matrix_nio: |
  Production beasts like nio-bot PyPI (Feb 2026 releases).
  opsdroid/niobot frameworks hammer async bots.
  Examples pipe external procs flawlessly, GitHub stars 12K+.

element_e2ee: |
  Mandatory device verification from April 2026.
  E2EE getting stricter — good for us.

claude_resume: |
  --resume reliable for multi-turn bots in 2026.
  Bot can maintain conversation state per channel.
```

---

## Summary

```yaml
what: Sovereign mobile command for a8ra Mission Control
how: Conduit + matrix-nio bot + Pantalaimon E2EE + Element clients
who: G (iPhone) + Olya (desktop) + bot (claude -p bridge)
when: Phase 1 NOW (ntfy alerts), Phase 2 on M3 arrival
cost: 500MB RAM + 100 lines of Python + half day build
result: "G commands from Surat Thani beach, swarm oinks back"
```

*Patterns locked. Sovereign comms. No cloud middleman. The boar responds from anywhere.*
