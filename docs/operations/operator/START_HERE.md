# START_HERE.md — Phoenix Orientation

**Purpose**: Single entry point for new advisors  
**Target**: Orient in <10 minutes  
**Last Updated**: 2026-01-30

---

## 1. WHAT IS PHOENIX?

```yaml
identity:
  name: Phoenix / WarBoar
  type: Constitutional Trading System
  status: S42_COMPLETE | PRODUCTION_READY
  
relationship:
  sibling: God_Mode (in ~/God_Mode)
  pattern: "Forge builds tools, Phoenix protects capital"
  
metrics:
  tests: 1465+ passing
  invariants: 95+ proven
  chaos_vectors: 224 handled
  runbooks: 8 operational
```

Phoenix is a **constitutional trading system** — meaning execution is bounded by machine-enforced invariants, not operator trust. It connects to Interactive Brokers (IBKR), executes based on validated signals from the CSO (Conditional Strategy Orchestrator), and maintains strict human sovereignty over all capital decisions.

---

## 2. CORE PRINCIPLES

### The Non-Negotiables

| Principle | Invariant | Meaning |
|-----------|-----------|---------|
| **Human Sovereignty** | INV-SOVEREIGN-1 | Human sovereignty over capital is absolute |
| **Human Frames** | INV-NO-UNSOLICITED | System never says "I noticed" — human asks, machine computes |
| **Facts Over Stories** | INV-ATTR-CAUSAL-BAN | No causal claims ("X caused Y"), only correlations with provenance |
| **Halt Always Works** | INV-HALT-1 | halt_local < 50ms (proven: 0.003ms) |
| **Quality Over Speed** | INV-CONTRACT-1 | Deterministic state machine, no racing for alpha |

### Tier Gates

```yaml
T0: Automated (read-only operations)
T1: Human-approved defaults (can be automated with prior approval)
T2: Human-gated (ALWAYS requires human approval for capital actions)
```

---

## 3. WHAT PHOENIX IS NOT

```yaml
- NOT an AI trader (logic lives in CSO + operator, not autonomous)
- NOT a recommendation engine (never says "you should consider...")
- NOT self-improving without oversight (all learning requires human gate)
- NOT a dashboard (no control surfaces, only state projection)
- NOT an authority on meaning (human frames, machine computes)
```

**Reference**: `docs/ARCHITECTURAL_FINALITY.md` for the full freeze state.

---

## 4. KEY FILES (Read In Order)

| Priority | File | Purpose |
|----------|------|---------|
| 1 | `docs/START_HERE.md` | This file — orientation |
| 2 | `docs/PHOENIX_MANIFEST.md` | System topology, modules, authority map |
| 3 | `docs/SPRINT_ROADMAP.md` | Current state, sprint history, what's complete |
| 4 | `SKILL.md` | Operating patterns, brief templates, role map |
| 5 | `docs/build_docs/CONSTITUTION_AS_CODE.md` | Governance architecture |
| 6 | `docs/ARCHITECTURAL_FINALITY.md` | S42 freeze, what's allowed |

### For Specific Domains

```yaml
trading_methodology: docs/olya_skills/LAYER_0_HTF_CONTEXT_CLEAN.md
failure_response: docs/runbooks/
product_vision: docs/build_docs/PRODUCT_VISION.md
operator_docs: docs/OPERATOR_INSTRUCTIONS/  # Expectations + when to ignore
gate_glossary: cso/knowledge/GATE_GLOSSARY.yaml  # Gate name → meaning
```

---

## 5. THE TEAM

| Role | Entity | Authority |
|------|--------|-----------|
| **G (Sovereign)** | Human | Vision, veto, capital decisions — FINAL SAY |
| **Olya (Oracle)** | Human | ICT methodology, CSO calibration, trading knowledge |
| **CTO (Claude)** | AI | Synthesis, coordination, coherence — receives DENSE only |
| **OWL (Gemini)** | AI | Contract law, structural audit, clause-level review |
| **GPT (Architect Lint)** | AI | Spec tightening, edge cases, flag tables |
| **GROK (BOAR)** | AI | Chaos audit, adversarial stress, "dumbest failure" finder |
| **OPUS (Cursor)** | AI | Primary builder — executes briefs, dense reports |

**Key rule**: G and Olya are humans with final authority. AI advisors propose, humans dispose.

---

## 6. CURRENT STATE

```yaml
sprint: S42_COMPLETE
status: POST_S42_FREEZE ACTIVE
block_status: Constitutional Ceiling achieved

test_suite:
  total: 1502
  passed: 1465
  xfailed: 28 (documented, strict)
  
chaos_vectors: 224/224 PASS

certification: WARBOAR_CERTIFIED | LIVE_GATEWAY_VALIDATED | CSO_PRODUCTION_READY

cso_status:
  methodology_fluency: ✅
  health_awareness: ✅
  gate_glossary: 48 gates mapped
  operator_docs: OPERATOR_INSTRUCTIONS/ ready
```

### What POST_S42_FREEZE Means

```yaml
allowed_without_unfreeze:
  - Bug fixes (fix existing behavior)
  - Calibration (tune thresholds, params)
  - xfail resolution (fix documented failures)
  - Documentation updates

requires_unfreeze:
  - New modules
  - New invariants
  - API changes
  - New features
```

---

## 7. HOW TO CONTRIBUTE

### Communication Format: DENSE M2M

```yaml
format: DENSE_M2M (Machine-to-Machine)

rules:
  - YAML/structured output preferred
  - Zero prose preamble
  - No "I think..." hedging
  - No restating context back
  - Binary verdicts (PASS/FAIL/CONDITIONAL)
  - Explicit refs (file:line, contract:clause)

anti_patterns:
  - "Let me help you with that..."
  - "As we discussed..."
  - Compliments/acknowledgments
  - Rhetorical questions
```

### Brief Template

When requesting work, use:

```yaml
# ============================================================
# BRIEF — [SHORT TITLE]
# ============================================================

brief: [ID]
mission: [ONE_LINE_GOAL]
owner: [AGENT]
format: DENSE
priority: [P0-P5]

# ============================================================
# CONTEXT
# ============================================================

background: |
  [2-3 lines of relevant context]

# ============================================================
# TASK
# ============================================================

task:
  deliverable: [what]
  exit_gate: [how we know it's done]

# ============================================================
# REPORT FORMAT
# ============================================================

report_format: DENSE
```

### When Unclear

```yaml
rule: "Ask if unclear, don't assume"
pattern: |
  If requirements are ambiguous:
    1. State what you understood
    2. List specific questions
    3. Wait for clarification
  
  Do NOT:
    - Guess and proceed
    - Make scope decisions without approval
    - Add "helpful" extras not requested
```

---

## 8. QUICK ANSWERS

**Q: Who approves capital decisions?**  
A: G (Sovereign). Always human-gated via T2.

**Q: Where is trading methodology?**  
A: `docs/olya_skills/LAYER_0_HTF_CONTEXT_CLEAN.md` — Olya's ICT methodology.

**Q: What's the current sprint?**  
A: S42 complete. POST_S42_FREEZE active. See `docs/SPRINT_ROADMAP.md`.

**Q: How do I run tests?**  
A: `cd ~/phoenix && source .venv/bin/activate && python -m pytest tests/ -q`

**Q: How do I check system health?**  
A: `python -m cli.phoenix_status`

**Q: Where are the runbooks?**  
A: `docs/runbooks/` — 8 operational runbooks (RB-001 through RB-008).

---

## 9. GLOSSARY (Minimal)

| Term | Definition |
|------|------------|
| **CSO** | Conditional Strategy Orchestrator — evaluates trading gates |
| **Bead** | Atomic, immutable knowledge unit (like a database row) |
| **INV-*** | Invariant — machine-enforced rule that cannot be violated |
| **T2** | Tier 2 — capital-affecting action requiring human gate |
| **Halt** | Emergency stop — governance/halt.py, <50ms proven |
| **River** | Data pipeline — single source of truth for market data |
| **DENSE** | Communication format — structured, no prose |

---

## 10. NEXT STEPS

After reading this file:

1. **Read `docs/PHOENIX_MANIFEST.md`** — understand the module topology
2. **Read `docs/SPRINT_ROADMAP.md`** — understand what's built and current state
3. **Read `SKILL.md`** — understand operating patterns and templates
4. **Ask CTO** if anything is unclear — don't assume

---

**Document Status**: AUTHORITATIVE  
**Freeze**: POST_S42_FREEZE  
**Validation**: New advisor should orient in <10 minutes using this file.
