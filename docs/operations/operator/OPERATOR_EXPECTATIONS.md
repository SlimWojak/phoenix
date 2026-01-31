# OPERATOR_EXPECTATIONS.md
# What Phoenix Tells You, What It Expects From You

---

## What Phoenix Is

A thinking partner backed by infrastructure.

| Layer | What It Does | Your Role |
|-------|--------------|-----------|
| CSO (Claude) | Thinks with you, writes intents, reads responses | Lead the thinking |
| Phoenix (System) | Executes scans, validates setups, manages risk | Trust the mechanics |
| You | Frame questions, make decisions, approve capital | Stay sovereign |

**Mental model:** You're the pilot. CSO is co-pilot. Phoenix is the aircraft.

---

## What CSO Knows

| Domain | Depth | Source |
|--------|-------|--------|
| ICT methodology | Deep | 5-drawer filing cabinet (foundation → management) |
| Gate definitions | Complete | 48 gates mapped to methodology |
| Your intents | As you speak them | Conversation context |
| System health | On-demand | health.yaml check |

**CSO does NOT know:** Phoenix internals, why things break, how to fix them.

---

## What Phoenix Tells You

| Output | Meaning |
|--------|---------|
| `gates_passed: [...]` | These conditions are met |
| `gates_failed: [...]` | These conditions are NOT met |
| `DEGRADED` | Something's wrong — CSO will check health |
| `APPROVED` | Trade intent received and queued |
| Silence (>30s) | System may be down — CSO will inform |

**Phoenix never tells you:** What to do. Only what IS.

---

## What Phoenix Expects From You

### In Conversation (EXPLORE)
- Think out loud — CSO structures with you
- Ask questions — methodology is loaded
- Take your time — no machinery runs until you say

### When Acting (DISPATCH)
- Be clear: "Scan GBPUSD" not "maybe check things"
- CSO will write intent, await response, present findings

### When Approving (T2)
- Confirm details when asked
- Say explicit "yes" / "execute" / "approved"
- **You are the decision-maker. CSO is the scribe.**

---

## What Silence Means

| Situation | Likely Cause | What Happens |
|-----------|--------------|--------------|
| No response (>30s) | System down, watcher stopped | CSO checks health.yaml, informs you |
| DEGRADED response | Data stale, IBKR disconnected | CSO explains what's blocked, offers alternatives |
| Slow response | Heavy computation (HUNT) | Wait — CSO will present when ready |

**Silence is not normal.** CSO will always inform you.

---

## System Health States

| State | Meaning | What Works |
|-------|---------|------------|
| HEALTHY | All systems operational | Everything |
| DEGRADED | Partial functionality | EXPLORE, methodology discussion |
| CRITICAL | Major failure | EXPLORE only, expect limits |
| HALTED | Emergency stop active | Nothing until resolved |

CSO checks `/phoenix/state/health.yaml` and reports naturally.

---

## The Modes

| Mode | Trigger | Machinery |
|------|---------|-----------|
| EXPLORE | Default, thinking | None — pure conversation |
| DISPATCH | "scan", "test", "check" | Intent written, Phoenix responds |
| APPROVE | "execute", "take it", explicit yes | T2 intent, capital affected |

**EXPLORE is always safe.** Think freely.

---

## Trust Calibration

### Trust Phoenix When:
- Gates are clear (passed/failed)
- Health shows HEALTHY
- Response arrives promptly
- Numbers match your chart

### Verify Phoenix When:
- Something feels off
- Gates conflict with what you see
- Response seems stale
- You're about to risk capital

### Override Phoenix When:
- Your read is stronger than the gates
- Market context changed faster than data
- You see something Phoenix can't encode

**You are sovereign. Phoenix serves your clarity, not the reverse.**

---

## Daily Rhythm

| Time | Action | Mode |
|------|--------|------|
| Morning | "Good morning" or MORNING_BRIEF | DISPATCH |
| Session | Think through setups, ask questions | EXPLORE |
| Setup found | "Scan GBPUSD" or manual check | DISPATCH |
| Decision time | Review gates, make call | EXPLORE → APPROVE |
| Post-trade | Autopsy, learnings | EXPLORE |

---

## One-Liners

- **CSO is your thinking partner, not a terminal.**
- **Phoenix tells you what IS, never what to DO.**
- **EXPLORE is always safe.**
- **Silence means something's wrong — CSO will tell you.**
- **You approve. CSO scribes. Phoenix executes.**