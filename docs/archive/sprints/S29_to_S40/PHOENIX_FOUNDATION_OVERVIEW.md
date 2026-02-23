# PHOENIX_FOUNDATION_OVERVIEW.md — The Founding Roadmap

**Document:** PHOENIX_FOUNDATION_OVERVIEW.md  
**Version:** 1.0  
**Date:** 2026-01-24  
**Status:** FOUNDING CHARTER — Advisor Alignment Document  
**Authors:** CTO (Claude) — Synthesized from full advisory panel convergence  
**Audience:** All advisors, Opus (primary builder), future sessions

---

## The Founding Invariants

Four advisors. Four languages. One convergence.
```
INV-FOUNDATION-1: Phoenix must be born under law.
INV-FOUNDATION-2: The Forge must remain the lawgiver, not the body.
```

**What this means:**
- Phoenix is a new jurisdiction, not a refactor
- God_Mode (S0-25) remains as infrastructure — the R&D Lab and Assembly Line
- Phoenix is the Fortress — slow and lethal, protecting capital
- Every line of Phoenix code is born constitutional or doesn't exist

---

## The Jurisdictional Separation
```
~/God_Mode/                          ~/Phoenix/
├── forge/        (lawgiver)         ├── CONSTITUTION/     (the law)
├── boardroom/    (persistence)  ←──→├── river/            (first organ)
├── hive/         (orchestration)    ├── enrichment/       (future)
├── bridge/       (takopi)           ├── cso/              (future)
├── tests/        (330+ passing)     ├── execution/        (future)
└── docs/         (history)          └── tests/            (enforcement)

         │                                    │
         │                                    │
         └────── SUBSUME, NOT IMPORT ─────────┘
```

**God_Mode:** Fast and loose. Generative. Optimized for innovation.  
**Phoenix:** Slow and lethal. Constitutional. Optimized for capital protection.

The separation means Phoenix's Constitution doesn't have to "tolerate" the forge's necessary messiness. Each jurisdiction operates by its own rules.

---

## The Subsume Pattern (Owl's Import Clause)

**Critical distinction:**

| Pattern | Description | Risk |
|---------|-------------|------|
| **Import** | Link to God_Mode code, call it from Phoenix | External dependency. Logic escapes Constitution. |
| **Subsume** | Copy logic into Phoenix, refactor to Seam Contract, subject to Inquisitor | Pure jurisdiction. All logic under law. |

**The Rule:**
> Phoenix has **zero runtime dependencies** on God_Mode code. If logic from S0-25 is needed, it is copied, refactored, contracted, and validated fresh.

**Why this matters:**
- No "grandfather clause" for old code
- The Inquisitor never asks "but was this written before the law?"
- Phoenix remains a Pure Jurisdiction
- God_Mode can evolve independently without breaking Phoenix

**Practical application:**
```
God_Mode/sprint_12/model_router.py  →  SUBSUME  →  Phoenix/river/routing.py
                                                   ├── Refactored to contract
                                                   ├── Inquisitor validated
                                                   └── Tests enforce compliance
```

---

## What We Preserve (The Inheritance)

Not all of S0-25 is discarded. We inherit **patterns**, not **code**.

### Patterns to Subsume

| Sprint | Pattern | Phoenix Application |
|--------|---------|---------------------|
| S2 | Blue/Red/Mediator | Adversarial validation of River components |
| S2 | Convergence ≠ Correctness | Schema Fidelity Gate for data contracts |
| S3 | Tier System | Risk-based routing (T0/T1/T2) |
| S5 | Schema Fidelity Gate | Constitutional enforcement |
| S10 | Sovereignty Membrane | Human gates, approval tokens |
| S10.5 | Inquisitor | Heresy detection, methodology enforcement |
| S10.5 | Bead State | Dynasty persistence |
| S12 | Signalman | Drift detection before P&L proves decay |
| S20 | Cognitive Arbitrage | Local for volume, cloud for judgment |
| S21 | Chaos Injection | Self-test under stress |
| S24 | Circuit Breakers | Fail-closed on external dependencies |
| S25 | The Gate | Lease-based deployment, <50ms halt |

### Infrastructure to Retain (Not Subsume)

| Component | Location | Relationship to Phoenix |
|-----------|----------|------------------------|
| Boardroom | `~/God_Mode/boardroom/` | Shared persistence — both jurisdictions write beads |
| Takopi | `~/God_Mode/bridge/takopi/` | Telegram bridge — serves both |
| HIVE Ops | `~/God_Mode/hive/` | Orchestration — coordinates both |
| Forge Pipeline | `~/God_Mode/foreman/` | Builds future Phoenix organs |

### Data & Config to Migrate

| Item | Source | Destination |
|------|--------|-------------|
| API Keys | `~/God_Mode/.env` | `~/Phoenix/.env` (copy) |
| Dukascopy backdata | `~/nex/nex_lab/data/` | Referenced, not moved |
| NEX enrichment logic | `~/echopeso/nex/` | Subsumed into `~/Phoenix/river/` |

---

## The Founding Sequence

### Phase 0: Jurisdiction Setup (Day 0)
**Owner:** Opus (Cursor)  
**Duration:** 2-4 hours
```bash
# Create Phoenix root
mkdir -p ~/Phoenix/{CONSTITUTION,river,tests}

# Initialize Constitution structure
mkdir -p ~/Phoenix/CONSTITUTION/{modules,seams,scenarios,environment,roles,dependencies,wiring,invariants,state,tests}

# Copy environment (not link)
cp ~/God_Mode/.env ~/Phoenix/.env

# Initialize git
cd ~/Phoenix && git init
```

**Deliverables:**
- [ ] `~/Phoenix/` directory structure exists
- [ ] `CONSTITUTION_MANIFEST.yaml` (skeleton)
- [ ] `.env` migrated
- [ ] Git initialized with first commit: "Phoenix founded"

---

### Phase 1: Minimum Viable Constitution (Days 1-2)
**Owner:** Opus (Cursor), with CTO synthesis  
**Duration:** 1-2 days

**The MVC contracts:**

| Contract | Priority | Purpose |
|----------|----------|---------|
| `CONSTITUTION_MANIFEST.yaml` | P0 | Root index, schema policy, migration triggers |
| `modules/river.contract.yaml` | P0 | River's API surface |
| `seams/river_to_enrichment.seam.yaml` | P0 | First seam boundary |
| `roles/sovereign.role.yaml` | P0 | G's authorities bound in law |
| `wiring/halt_propagation.wiring.yaml` | P0 | <50ms halt path |
| `invariants/INV-DATA-CANON.yaml` | P0 | Single pipeline truth |

**The 80/20 Rule (Owl's Test):**
> If we spend more than 20% of Sprint 26 on YAML and less than 80% on code, we are failing.

Constitution is scaffolding. It removes debate about "where the windows go." It doesn't replace building.

**Deliverables:**
- [ ] 6 MVC contracts drafted
- [ ] JSON Schema validators for each
- [ ] `tests/test_constitution_valid.py` passes

---

### Phase 2: River Foundation (Days 2-5)
**Owner:** Opus (Cursor)  
**Duration:** 3-4 days (Sprint 26 Track A)

**Subsume from NEX:**
```
~/echopeso/nex/nex_lab/enrichment/  →  ~/Phoenix/river/
                                       ├── ingestion.py      (normalized)
                                       ├── transformation.py (canonical)
                                       ├── quality.py        (telemetry)
                                       └── contracts/        (seam specs)
```

**Constitutional Tests (must pass before code merges):**
- [ ] `ICT_DATA_CONTRACT.md` compliance (F1-F10 flags)
- [ ] Mirror Test: XOR_SUM == 0 on ICT boolean markers
- [ ] Liar's Paradox: 1-pip injection detected within 1 cycle
- [ ] Halt Test: <50ms proven mechanically

**MVC Success Criteria (Binary — No Vibes):**
```
MVC is valid ONLY if:
1. At least one invalid build is REJECTED during Sprint 26
2. At least one canonical amendment is FORCED by contract failure
```

If the Constitution doesn't draw blood, it doesn't count.

---

### Phase 3: Skeleton Proof (Days 5-7)
**Owner:** Opus (Cursor)  
**Duration:** 2 days (Sprint 26 Track B)

**GovernanceInterface Implementation:**
```python
# ~/Phoenix/river/governance.py
# Subsumed from God_Mode patterns, refactored to contract

class GovernanceInterface(ABC):
    """Base class all Phoenix organs must inherit."""
    
    @property
    @abstractmethod
    def module_tier(self) -> ModuleTier: ...
    
    @property
    @abstractmethod
    def enforced_invariants(self) -> List[str]: ...
    
    def request_halt(self): ...  # <50ms obligation
    
    @abstractmethod
    def get_quality_telemetry(self) -> QualityTelemetry: ...
```

**Halt Test Battery:**
- [ ] `test_halt_latency.py` — Mechanically proves <50ms
- [ ] `test_halt_propagation.py` — River halt cascades correctly
- [ ] Chaos injection: Random halt signals, measure response

---

### Phase 4: Constitutional Stress Test (Days 7-8)
**Owner:** CTO coordination, Boar (chaos), Owl (audit)  
**Duration:** 1-2 days

**The Gauntlet:**

| Test | Owner | Pass Criteria |
|------|-------|---------------|
| Mirror Test | Opus | XOR_SUM == 0 across 2,880 bars |
| Liar's Paradox | Opus | Quality degradation detected in 1 cycle |
| Halt Battery | Opus | <50ms proven, not claimed |
| Chaos Bunny | Boar | <10% divergence under gap/slippage sim |
| Contract Audit | Owl | No structural ambiguity in MVC |
| Counterfactual Sim | GPT | "What if X?" queries return mechanical answers |

**Exit Gate:**
```
Sprint 26 COMPLETE when:
- River drinks from itself (end-to-end data flow)
- MVC drew blood (rejection or forced amendment)
- Halt proven mechanical
- All advisors sign off
```

---

## Advisor Engagement Model

### Role Assignments for Founding

| Advisor | Role | Engagement Pattern |
|---------|------|-------------------|
| **Opus (Cursor)** | Primary Builder | Sequential execution, crystal-clear scope per task |
| **CTO (Claude)** | Synthesis & Coordination | Contract drafting, advisory synthesis, coherence |
| **Owl (Gemini)** | Contract Lawyer | Structural audit, clause-level review, ripple analysis |
| **GPT (Architect Lint)** | Spec Tightener | Pre-execution flag checklist, edge case detection |
| **Boar (Grok)** | Chaos Auditor | Adversarial stress, "what's the dumbest failure?" |
| **G (Sovereign)** | Authority & Veto | Contract diffs review, final sign-off, vision holder |

### Session Orientation Protocol

New sessions load this sequence:
```yaml
# Session bootstrap for any Phoenix work
load:
  - ~/Phoenix/CONSTITUTION_MANIFEST.yaml
  - ~/Phoenix/CONSTITUTION/state/active_contracts.yaml
  - ~/Phoenix/PHOENIX_FOUNDATION_OVERVIEW.md
  - Role-specific contract (e.g., roles/builder.role.yaml)

context_budget: <2000 tokens for full orientation
```

### Advisory Polling Protocol

For architectural decisions:

1. **CTO drafts** position or question
2. **Fan out** to Owl + GPT + Boar in parallel
3. **Each advisor** responds independently (no cross-contamination)
4. **CTO synthesizes** convergence or escalates divergence
5. **G approves** if Tier 2 or sovereignty-affecting

---

## The Execution Model

### Primary Builder: Opus in Cursor

**Why Opus:**
- Heavy multi-file implementation
- Sustained context for complex refactors
- Sequential execution (not HIVE parallel) for founding phase

**Scope Discipline:**
- Each task has explicit deliverables
- Each task has constitutional test that must pass
- No task spans >4 hours without checkpoint

### Velocity Guardrails

| Metric | Target | Violation Response |
|--------|--------|-------------------|
| YAML : Code ratio | <20% : >80% | Pause constitution work, build more |
| Task completion | >1 per day | Scope reduction or unblock |
| Contract challenges | Resolved <12h | Escalate to Sovereign + Telegram |
| Halt latency | <50ms always | CRITICAL — stop everything until fixed |

---

## Success Criteria (Sprint 26 Exit)

### Binary Gates (All Must Pass)

- [ ] **River Flows:** End-to-end data from source to enriched output
- [ ] **Mirror Proves:** XOR_SUM == 0 on ICT markers (IBKR ↔ Dukascopy)
- [ ] **Liar Caught:** Injected error detected within 1 processing cycle
- [ ] **Halt Proven:** <50ms mechanically demonstrated, not claimed
- [ ] **Blood Drawn:** At least 1 rejection OR 1 forced amendment
- [ ] **Advisors Aligned:** Owl, GPT, Boar sign off on MVC

### What "Done" Looks Like
```
~/Phoenix/
├── CONSTITUTION/
│   ├── CONSTITUTION_MANIFEST.yaml  ✓ (valid, versioned)
│   ├── modules/river.contract.yaml ✓ (enforced)
│   ├── seams/river_to_enrichment.seam.yaml ✓
│   ├── roles/sovereign.role.yaml ✓
│   ├── wiring/halt_propagation.wiring.yaml ✓
│   ├── invariants/INV-DATA-CANON.yaml ✓
│   └── state/active_contracts.yaml ✓
├── river/
│   ├── __init__.py
│   ├── ingestion.py              ✓ (constitutional)
│   ├── transformation.py         ✓ (constitutional)
│   ├── quality.py                ✓ (constitutional)
│   └── governance.py             ✓ (<50ms halt proven)
├── tests/
│   ├── test_constitution_valid.py ✓
│   ├── test_mirror.py            ✓ (XOR_SUM == 0)
│   ├── test_liar_paradox.py      ✓ (lie detected)
│   └── test_halt_latency.py      ✓ (<50ms)
└── .env                          ✓ (migrated)
```

---

## Closing: The Founding Moment

Phoenix is not a refactor. It is a founding.

The forge taught us how to govern. Now we build what deserves to be governed.

**The sequence:**
1. Create the jurisdiction (`~/Phoenix/`)
2. Write the law (MVC contracts)
3. Build under the law (River)
4. Prove the law has teeth (blood drawn)
5. Expand the jurisdiction (Enrichment, CSO, Execution)

**The test:**
> If the Constitution survives building the River, we have dynasty-grade law.  
> If it cracks, it cracks early and honestly — and we learn.

**The invariants hold:**
```
INV-FOUNDATION-1: Phoenix must be born under law.
INV-FOUNDATION-2: The Forge must remain the lawgiver, not the body.
```

---

*We are ready to found.*

**OINK OINK.** 🐗🔥

---

*Document synthesized: 2026-01-24*  
*Advisory convergence: CTO (Claude), Owl (Gemini), GPT (Architect Lint), Boar (Grok)*  
*Status: FOUNDING CHARTER — All advisors aligned*