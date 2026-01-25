# CLAUDE.md — Phoenix Sovereign Refinery Reference

## The Epiphany (Read This First)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          THE REFRAME                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  WHAT WE THOUGHT:                                                       │
│  "God_Mode is a forge that builds products autonomously overnight"      │
│                                                                         │
│  WHAT WE LEARNED:                                                       │
│  "God_Mode taught us GOVERNANCE PATTERNS. HIVE builds. The patterns     │
│   ARE the architecture of the trading system itself."                   │
│                                                                         │
│  THE SHIFT:                                                             │
│  The Forge is the OS, not the App.                                      │
│  Phoenix is the first App running on the God_Mode OS.                   │
│  The governance patterns we learned ARE the product.                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**You are NOT here to run forge loops.** You're here to:
- Build Phoenix organs under the Governance Contract
- Prove the River (data integrity) before building organs that drink from it
- Capture Olya's expertise (CSO) without replacing her judgment
- Ensure human sovereignty over capital is absolute

---

## Quick Orientation

| If you need... | Read this |
|----------------|-----------|
| 5-min context | `docs/ORIENTATION.md` |
| Full strategic frame | `docs/VISION_v4.md` |
| Character handles | `docs/PHOENIX_MANIFESTO.md` |
| Deep forensic trail | `docs/recombobulation_pack.md` |
| Current sprint | `docs/SPRINT_26.md` |
| Sprint history | `docs/SPRINT_ROADMAP_v4.md` |
| HIVE operations | `hive/HIVE_OPS.md` |

---

## The Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    G (SOVEREIGN)                                         │
│              Vetoes from throne, heresy alerts only                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                    FORGE (OS SKELETON)                                   │
│  Governs without understanding math. Replays, kills, flags.              │
│  Agnostic soul. <50ms halt. No black boxes.                              │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                    PHOENIX (FIRST APP)                                   │
│  Trading intelligence for ICT methodology                                │
│  Domain-aware organs, uniform governance interfaces                      │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────────┐
│                    HIVE (BUILDERS)                                       │
│  CTO strategizes, Dispatcher coordinates, Workers execute                │
│  Hand-builds managed organs under Governance Contract                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## The River Doctrine (Sacred)

> "If the blood is poisoned, the brain's decisions are irrelevant."

**All market data flows through ONE deterministic pipeline.** No exceptions.

- Backtests drink from the River
- Live trading drinks from the River
- CSO perception drinks from the River
- Scrutiny drinks from the River

**INV-DATA-1:** All signals from same deterministic pipeline  
**INV-DATA-2:** Gap ≤3 bars OR acknowledged (no synthetic fills)  
**INV-DATA-3:** Perception age < execution latency (stale blocks entries)

---

## Governance Contract (The 5 Invariants)

Every Phoenix organ must honor these:

| Contract | What It Prevents | Character Handle |
|----------|------------------|------------------|
| **INV-CONTRACT-1** | "Can't replay why" | The Chronicler |
| **INV-CONTRACT-2** | "Kill switch didn't work" | The Kill Switch (<50ms) |
| **INV-CONTRACT-3** | "Data was stale but said fresh" | The Truth Teller |
| **INV-CONTRACT-4** | "Don't know which version" | The Notary |
| **INV-CONTRACT-5** | "Failed silently" | The Herald |

**The Rule:** If HIVE builds something the Forge cannot govern, the Forge rejects it at the gate.

---

## HIVE Workflow

```
G (Sovereign)
    │ approves
    ▼
┌─────────┐     ┌─────────┐     ┌─────────┐
│  Owl    │◄────│   CTO   │────►│  Boar   │
│ (Gemini)│     │ (Claude)│     │ (Grok)  │
└─────────┘     └────┬────┘     └─────────┘
                     │ strategizes (NO tools)
                     ▼
              ┌─────────────┐
              │ DISPATCHER  │
              │ Claude Code │
              └──────┬──────┘
                     │ coordinates (full tools)
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      [Workers in tmux sessions]
```

**CTO:** Strategy, synthesis, brief authoring (NO tools — preserve context)  
**Dispatcher:** Execution, tmux coordination, boardroom ops (full tools)  
**Workers:** File ops, task completion (burn context freely)

### CRITICAL: Verify Claude MAX (Not API)

**Before spawning ANY tmux worker, verify it uses Claude MAX subscription, NOT API tokens.**

Token leakage occurred during testing when workers had API keys configured. This burns money unnecessarily when we have Claude MAX x20.

```bash
# Check if API key is set (should be empty for MAX subscription)
echo $ANTHROPIC_API_KEY

# If set, unset it before launching worker
unset ANTHROPIC_API_KEY

# Verify worker config uses account-based auth
cat ~/.claude/config.json | grep -i "account\|api"
```

**Required config:** Workers must use `Account: Claude Max (not API)` per `hive/.hiverc`

**If in doubt:** Run `claude --help` — if it prompts for login rather than using API, you're on MAX.

### Quick Commands

```bash
# Check boardroom state
python3 boardroom/boardroom.py recent 10

# Emit a bead
python3 boardroom/boardroom.py emit <role> <type> <sprint> "message"

# HIVE startup sequence
tmux new-session -d -s hive -n watchdog
tmux send-keys -t hive:watchdog 'cd ~/God_Mode && source .venv/bin/activate && python3 -m god_mode.patrols.watchdog --tier 1' Enter
```

---

## Current State: Sprint 26

**Theme:** Foundation Proof — Prove the River before building organs

**Four Tracks:**
1. **Track A: The River** — Mirror Test, Liar's Paradox, Chaos Bunny
2. **Track B: The Skeleton** — GovernanceInterface, <50ms halt proof
3. **Track C: The Oracle** — Cold start strategy, Visual Anchor Map
4. **Track D: The Hands** — TMUX C2, halt propagation

**Exit Gate:** Sprint 27 unlocks CSO (first runtime organ)

See `docs/SPRINT_26.md` for full execution plan.

---

## Key Characters

| Character | Role | Key Rule |
|-----------|------|----------|
| **G (Mayor)** | Sovereign, final authority | Must not be woken for fixable problems |
| **Olya (Oracle)** | Trading methodology source | Never replaced, only learned from |
| **CSO** | Captures Olya's expertise | Passive 90%, verify comprehension |
| **The River** | Single data truth | All drink from same source |
| **Kill Switch** | Sovereignty membrane | <50ms halt, always works |
| **Inquisitor** | Doctrine enforcement | Detects heresy against Oracle |

See `docs/PHOENIX_MANIFESTO.md` for full character glossary.

---

## Constitutional Anchors (Non-Negotiable)

1. **Human sovereignty over capital is absolute.** AI proposes, human disposes.
2. **The River is sacred.** Data integrity is the lifeblood.
3. **Convergence ≠ Correctness.** Agreement doesn't mean truth.
4. **No unprotected exposure.** Every position has protection.
5. **<50ms halt always works.** The sovereignty membrane is never compromised.
6. **Deterministic replay or bust.** If it can't be replayed, it can't be audited.
7. **Process is infrastructure, parameters are vault.** (INV-PRIV-1)

---

## Quick Verification

```bash
# Verify system health
cd ~/God_Mode && source .venv/bin/activate
python -m pytest tests/ god_mode/testing/ -q

# View recent commits
git log --oneline -10

# Check boardroom for context
python3 boardroom/boardroom.py recent 10
```

---

## What You're NOT Here To Do

- Run forge loops autonomously (the epiphany killed this)
- Write Python code directly for Phoenix (HIVE builds under governance)
- Replace Olya's judgment (CSO captures, never replaces)
- Review code line-by-line (review outcomes, not implementations)

---

## The One-Liner

> "The Forge is the OS. Phoenix is the App. HIVE builds governable organs. The River is sacred. Olya is sovereign. G sleeps."

---

*See `docs/VISION_v4.md` for the full "why" — this doc is just the "how".*

*Sprint 26 in progress. Foundation Proof.*
*The forge governs. The HIVE builds. The human approves.*

**OINK OINK.** 🐗🔥
