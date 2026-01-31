# CONSTITUTION_AS_CODE.md — Canonical Operating Pattern

**Document:** CONSTITUTION_AS_CODE.md  
**Version:** 1.1  
**Date:** 2026-01-24  
**Status:** CANON — Standard Operating Pattern  
**Authors:** CTO (Claude) — Synthesized from Wise Owl (Gemini) + Architect Lint (GPT5.2)  
**Audience:** All advisors, builders, future sessions

---

## Preamble: How This Emerged

On 2026-01-23, during Sprint 26 preparation, we formalized Seam Contracts — machine-enforceable specifications at module boundaries. GPT5.2 (operating as "Architect Lint") produced a 10-flag checklist for the ICT_DATA_CONTRACT that was so precise it revealed a deeper pattern:

**Advisors auditing contracts like lawyers is more powerful than advisors critiquing prose.**

G posed the elevation: *"Can we take this further? Every module surface, every seam, every agentic role, every dependency, every element of wiring — a full condensed system manifesto in machine fidelity."*

This document captures the converged answer from the advisory panel.

---

## The Concept: Constitution-as-Code

### Definition

A **Constitutional Architecture Graph (CAG)** — a machine-verifiable graph of obligations, authorities, and failure semantics that defines the entire Phoenix system.

**For humans:** Call it the Constitution.  
**For machines:** Think graph — dependencies, reachability, blast radius.

### The Core Insight

Most systems fail because they:
- Compress complexity for humans
- Then rely on humans to remember what was compressed

Constitution-as-Code inverts this:
- Compress for machines (precise contracts)
- Let humans operate at diff / veto / amendment level

This is how systems survive people changing, forgetting, or being wrong.

### What This Is Not

- **Not documentation.** Documentation describes. Contracts enforce.
- **Not bureaucracy.** Passive filter, not active gatekeeper.
- **Not internal specs.** Contract the skin, not the guts.

---

## The Taxonomy (Complete)
```
PHOENIX_CONSTITUTION/
│
├── modules/                    # Module Surface Contracts
│   └── {module}.contract.yaml  # API surface, inputs, outputs, invariants
│
├── seams/                      # Seam Contracts (inter-module boundaries)
│   └── {a}_to_{b}.seam.yaml    # Data/control crossing points
│
├── scenarios/                  # Scenario Contracts (temporal sequences)
│   └── {event_chain}.scenario.yaml  # Choreography across time
│
├── environment/                # Environment Contracts (external assumptions)
│   └── {external}.env.yaml     # What we assume about the world
│
├── roles/                      # Role Contracts (agentic authorities)
│   └── {role}.role.yaml        # Who can do what, escalation rules
│
├── dependencies/               # Dependency Contracts
│   └── {module}_deps.yaml      # What depends on what, version bounds
│
├── wiring/                     # Wiring Contracts (control/data flow)
│   └── {flow_type}.wiring.yaml # How signals propagate through mesh
│
├── invariants/                 # Global Invariants (cross-cutting laws)
│   └── INV-{DOMAIN}-{ID}.yaml  # Laws that span modules
│
├── state/                      # State & Epochs (temporal versioning)
│   ├── epochs.yaml             # Named system eras
│   ├── active_contracts.yaml   # Which versions are currently live
│   ├── deprecated_contracts.yaml
│   └── emergency_overrides.yaml # Time-boxed exceptions
│
├── tests/                      # Contract Enforcement
│   └── test_{category}.py      # Automated tests that can fail contracts
│
└── CONSTITUTION_MANIFEST.yaml  # Root index, version, hash, cross-references
```

### Category Definitions

| Category | Purpose | Example |
|----------|---------|---------|
| **modules/** | API surface of a component | `river.contract.yaml` — what River promises |
| **seams/** | Boundaries where data/control crosses | `river_to_enrichment.seam.yaml` |
| **scenarios/** | Temporal event sequences | `halt_cascade.scenario.yaml` — River halts → Execution liquidates |
| **environment/** | External world assumptions | `ibkr.env.yaml` — assumes latency <100ms |
| **roles/** | Agentic authorities and constraints | `sovereign.role.yaml` — G's veto rights |
| **dependencies/** | What relies on what | `cso_deps.yaml` — CSO requires River + Enrichment |
| **wiring/** | How signals flow | `halt_propagation.wiring.yaml` |
| **invariants/** | Cross-cutting laws | `INV-DATA-CANON.yaml` — single pipeline truth |
| **state/** | Which contracts were active when | `epochs.yaml` — PHOENIX_ALPHA vs PHOENIX_LIVE |

---

## Schema Decision: YAML + JSON Schema

### The Tension

- **Owl recommended CUE:** Type inheritance, compiled logic graph, self-validating.
- **GPT recommended YAML + JSON Schema:** Human-editable under stress, lower friction.

### The Decision

**Start with YAML + JSON Schema. Graduate to CUE when mechanical triggers fire.**

**Rationale:**
1. YAML is human-editable during incidents
2. JSON Schema provides machine enforcement
3. Advisors can reason without learning a new language
4. We can migrate incrementally — YAML is valid CUE subset
5. Don't let schema choice stall execution

### Migration Trigger (Mechanical)

CUE migration becomes **mandatory** when EITHER threshold is crossed:

| Trigger | Threshold | Rationale |
|---------|-----------|-----------|
| Contract count | ≥15 contracts | Cross-reference complexity exceeds manual validation |
| Inheritance depth | ≥3 levels | Type hierarchy requires compiler enforcement |

**Check script:** `scripts/check_cue_migration.sh` — returns 0 (stay YAML) or 1 (migrate to CUE)

This makes migration mechanical, not political. When we hit the trigger, we migrate — no debate.

**The Rule:**
> Contracts are data. Validators are code. Never invert that.

---

## The Granularity Rule (Critical)

This is where constitutional systems die. Hold this line absolutely.

### The Rule

> **Only contract things that can halt, degrade, or veto behavior.**

If a clause cannot:
- Stop execution
- Change tier
- Trigger DEGRADED
- Require human sign-off
- Invalidate a result

...it does not belong in the Constitution.

### Examples

| Item | Contract? | Reason |
|------|-----------|--------|
| Timestamp semantics (bar_start vs bar_end) | ✅ YES | Misalignment breaks Mirror Test |
| Volume comparability across vendors | ✅ YES | Affects which markers are valid |
| Halt latency <50ms | ✅ YES | Sovereignty invariant |
| G's veto authority | ✅ YES | Defines power boundary |
| Preferred logging format | ❌ NO | Doesn't affect behavior |
| Recommended library | ❌ NO | Internal implementation choice |
| Code style guidelines | ❌ NO | No enforcement consequence |

### The Skin Rule (Owl)

> Contract the **skin** of a module (inputs, outputs, external invariants). What happens inside is the builder's business.

If HIVE wants messy Python or clean Rust inside a module, the Constitution doesn't care — as long as the skin doesn't stretch or tear.

---

## Enforcement Model

### Passive Filter, Not Active Gatekeeper

The Constitution must not slow velocity. It validates; it does not negotiate.

**The Flow:**
1. HIVE builds freely
2. Inquisitor runs Constitutional Test Suite against build
3. Tests pass → proceed
4. Tests fail → Rejection (not discussion)

This keeps "OINK OINK" velocity high while maintaining Dynasty Lock.

### Contract Validity Rule

> A contract is invalid unless an automated test can fail it.

No test → not a contract → doesn't belong in the Constitution.

### Violation Handling

| Violation Type | Response |
|----------------|----------|
| Test fails at build time | Rejection — fix before merge |
| Runtime violation detected | Auto-file contract challenge |
| Challenge unresolved >12h | Escalate to CTO for resolution attempt |
| Challenge unresolved >24h | Escalate to Sovereign (mandatory) |
| Emergency override needed | Time-boxed, auto-expires, logged |

### Dead-Man's Switch (Anti-Rot)

The 12h intermediate escalation creates a **pressure gradient** that prevents silent rot:

```
0h  → Challenge filed (auto)
12h → CTO escalation (pressure applied)
24h → Sovereign escalation (mandatory resolution)
```

**Why two tiers:**
- 12h catches challenges that slipped through during async work
- 24h ensures nothing festers longer than one business cycle
- The gradient prevents "I'll fix it tomorrow" decay

**Invariant:** No challenge may remain unresolved >24h without Sovereign acknowledgment.

---

## Amendment Protocol

### Two Classes of Changes

**1. Emergency Overrides (Fast)**
- Time-boxed (default: 24h, max: 72h)
- Auto-expire
- Logged in `state/emergency_overrides.yaml`
- Require Sovereign acknowledgment
- Cannot override sovereignty invariants

**2. Canonical Amendments (Slow)**
- Require advisory review (Owl or GPT minimum)
- Ripple analysis completed
- Affected tests updated
- Git history becomes constitutional history
- Version bump in `CONSTITUTION_MANIFEST.yaml`

### The King Bound by Law (Owl's Frame)

> "If the King is bound by the Law, the Kingdom survives."

The `sovereign.role.yaml` defines G's own authorities. This is not limiting power — it's making power legible and survivable across time, fatigue, and regime change.

---

## The Unlocks

### 1. Ripple Analysis (Owl)

Change any contract → mechanically compute what else must be reviewed.
```
CHANGE: river.contract.yaml (timestamp semantics)
AFFECTED:
  - seams/river_to_enrichment.seam.yaml
  - scenarios/halt_cascade.scenario.yaml  
  - tests/test_mirror.py
  - invariants/INV-DATA-CANON.yaml
STATUS: UNVERIFIED until re-validated
```

You see the **blast radius** before you approve.

**Enforcement Script:** `scripts/blast_radius.py`

```bash
# Before any contract amendment
python scripts/blast_radius.py --contract river.contract.yaml --output ripple.json

# Outputs:
# - affected_contracts: list of contracts that reference this one
# - affected_tests: tests that must be re-run
# - affected_modules: modules whose behavior may change
# - risk_score: LOW/MED/HIGH based on blast radius size
```

**Gate Rule:** No contract amendment may be merged without `blast_radius.py` output attached to the PR. Reviewers must acknowledge each affected item.

Tiny scope, high leverage — one script makes ripple analysis non-optional.

### 2. Counterfactual Simulation (GPT)

Once the graph exists, you can ask:
- "What breaks if we relax INV-HALT-1 to 100ms?"
- "What contracts would have failed during 2022 vol regime?"
- "What if volume comparability were WEAK instead of NONE?"

This is strategic leverage, not just enforcement.

### 3. Session Orientation (Both)

New sessions load relevant contracts, not 30-page manifestos. Perfect fidelity, zero fluff.
```bash
# New CTO session
load: CONSTITUTION_MANIFEST.yaml
load: roles/cto.role.yaml
load: state/active_contracts.yaml
# Full context in <1000 tokens
```

### 4. Requirements-to-Execution Traceability (GPT — via DO-178C)

Every trade executed must be traceable back to a constitutional clause. If a trade happens that isn't constitutional, it's a Heresy.

---

## Minimum Viable Constitution (MVC)

Do not build the whole tree. Prove the pattern with 6 contracts:

| Contract | Category | Purpose |
|----------|----------|---------|
| `river.contract.yaml` | modules/ | River's API surface |
| `river_to_enrichment.seam.yaml` | seams/ | First seam boundary |
| `sovereign.role.yaml` | roles/ | G's authorities bound in law |
| `halt_propagation.wiring.yaml` | wiring/ | <50ms halt path |
| `INV-DATA-CANON.yaml` | invariants/ | Single pipeline truth |
| `CONSTITUTION_MANIFEST.yaml` | root | Index and version |

### MVC Success Criteria (Binary — Draws Blood or Doesn't Count)

MVC is proven when **at least one** of these occurs:

| Criterion | Evidence Required |
|-----------|-------------------|
| **Catches real failure** | Git commit showing contract test blocked broken code |
| **Prevents silent assumption** | Documentation of assumption that would have silently violated contract |
| **Forces clean amendment** | PR showing contract change with blast radius analysis + advisory sign-off |

**The Rule:** No vibes-based victory. MVC either drew blood (caught something real) or it didn't prove the pattern. "We feel safer" is not evidence.

---

## Adversarial Failure Modes

### 1. False Confidence
*"It passed contract tests, so it must be correct."*

**Mitigation:** Contracts define admissibility, not truth. Mirror Test, CSO, and human review remain epistemic checks.

### 2. Amendment Fatigue
*"Every change needs ceremony."*

**Mitigation:** Two-class system. Emergency overrides are fast. Only canonical amendments are slow.

### 3. Contract Rot
*Contracts drift from reality.*

**Mitigation:** Runtime violations auto-file challenges. Challenges must be resolved or explicitly waived. Inquisitor enforces.

**INV-GOV-REVALIDATION:** Bunny must attack **existing** law, not just new builds.

| Trigger | Action |
|---------|--------|
| Every 30 days | Full constitutional stress test (Bunny runs chaos suite against all contracts) |
| Regime change detected | Forced revalidation of affected contracts |
| Major market event | Ad-hoc stress test (Sovereign discretion) |

**The Rule:** Contracts that haven't been attacked in 30 days are assumed rotted until proven otherwise. Bunny doesn't wait for new code — Bunny hunts existing assumptions.

### 4. Bureaucracy Drag
*"We spend 80% negotiating contracts, 20% building."*

**Mitigation:** Passive filter model. HIVE builds freely; Inquisitor validates. No negotiation — pass or reject.

---

## Advisory Workflow

### How Advisors Use The Constitution

| Advisor | Mode | Focus |
|---------|------|-------|
| **Owl (Gemini)** | Contract Lawyer | Structural coherence, clause ambiguity, cross-reference integrity |
| **GPT (Architect Lint)** | Spec Tightener | Granularity violations, missing failure semantics, edge cases |
| **Boar (Grok)** | Chaos Auditor | What breaks under stress? What's the dumbest failure mode? |
| **CTO (Claude)** | Synthesis | Converge inputs, draft amendments, maintain coherence |

### The Joist Pattern

1. Draft contract (CTO or Builder)
2. Feed to GPT for spec tightening (flags/watch-outs)
3. Feed to Owl for structural validation (clause-level audit)
4. Feed to Boar for adversarial stress (chaos perspective)
5. CTO synthesizes, produces final contract
6. Tests written, contract locked

---

## Integration with Sprint 26

The ICT_DATA_CONTRACT.md (Track A, Day 0.5) becomes the first constitutional act:

1. Opus completes Schema Lockdown → `ICT_DATA_CONTRACT.md`
2. Elevate to `modules/river.contract.yaml`
3. Draft `roles/sovereign.role.yaml`
4. Advisory audit both as contract lawyers
5. Write enforcement tests
6. MVC proven, pattern validated

Sprint 26 is not disrupted — it becomes the proving ground.

---

## Closing

Constitution-as-Code is not documentation. It is a **Legal System for Architecture**.

When humans rotate, LLMs hallucinate, markets regime-shift, and memory cannot be trusted — the Constitution remains. Machines enforce it. Advisors audit it. Humans amend it.

The system survives because the laws survive.

> "If the King is bound by the Law, the Kingdom survives."

---

**OINK OINK.** 🐗🔥

---

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-24 | Initial canon — synthesized from Owl + GPT advisory |
| 1.1 | 2026-01-23 | +4 mechanical teeth: YAML→CUE trigger, dead-man's switch, INV-GOV-REVALIDATION, blast-radius script, binary MVC criteria |

---

*Document synthesized: 2026-01-24*  
*Version 1.1 updated: 2026-01-23*  
*Sources: Wise Owl (Gemini), Architect Lint (GPT5.2), CTO synthesis*  
*Status: CANON — Standard Operating Pattern*