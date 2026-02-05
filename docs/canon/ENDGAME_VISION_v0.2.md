# THE REFINERY ENDGAME

```yaml
document: ENDGAME_VISION
version: 0.2
date: 2026-02-05
status: VISION_LOCKED | CARPARK
source: G + CTO synthesis dialogue
gating: Requires Olya Stage 2 validation + v0.1 shipped before design sprint
sprint_target: S53+
```

---

## 1. VISION

### The Reframe

```yaml
today: "Dexter extracts Olya's knowledge from documents"

tomorrow: |
  Autonomous research refinery that:
  1. Ingests Olya's validated logic (FACT_BEADs)
  2. Agents generate hypotheses (Perplexity research, Grok frontier, Opus synthesis)
  3. Tests on synthetic River (backtesting infrastructure — S39 BUILT)
  4. Runs forward paper trades (IBKR paper — S44 PROVEN)
  5. Tracks performance with provenance (CFP — S35 BUILT)
  6. Reports evidence bundles to Sovereign
  7. 24/7. Unattended. Compounding.

output: "Sharpened thesis → evidence bundle → human decision"

NOT_output: "Recommendation" (INV-NO-UNSOLICITED still holds)
```

### The Analogy

```
Olya is the seed.
Dexter is the greenhouse that grows thousands of variants.
Phoenix is the field where proven variants go live.
The Sovereign harvests.
```

---

## 2. WHY THIS IS PROFOUND

### Leverage Multiplication

```yaml
olya_alone: "1 human, 1 methodology, limited hours"

olya_plus_dexter: |
  Same methodology → 1000 variants tested overnight
  Same logic → applied across regimes she hasn't seen yet
  Same principles → stress-tested against frontier conditions
  24/7 → while she sleeps, while G sleeps, while everyone sleeps
```

### Infrastructure Already Built

The key insight: **We didn't build these for Dexter. But Dexter can USE all of them.**

| Sprint | Capability | How Dexter Uses It |
|--------|------------|-------------------|
| **S35 CFP** | Conditional fact projection | WHERE does edge live |
| **S36 CSO** | Gate evaluation framework | Mechanical, no grades |
| **S37 ATHENA** | CLAIM/FACT/CONFLICT memory | Provenance chain |
| **S38 HUNT** | Exhaustive grid computation | Human-declared variants |
| **S39 VALIDATION** | Walk-forward, Monte Carlo | Decomposed outputs |
| **S40 RESILIENCE** | Circuit breakers, self-healing | Degradation handling |
| **S44 LIVE** | IBKR paper trading | Forward testing validated |
| **S47 LEASE** | Bounded autonomy governance | Execution constraints |

The constitutional ceiling (S39) means Dexter's output is ALREADY constrained to facts + provenance.

**The infrastructure IS the moat.**

### Foundry-as-a-Service Unlock

```yaml
insight: |
  If Dexter can run this loop for ICT methodology...
  It can run it for ANY methodology.

  Cartridge = methodology definition
  Dexter = extraction + hypothesis + testing
  Phoenix = governance + execution

  That's the Foundry-as-a-Service vision — now with a proven path.
```

---

## 3. DEXTER CAPABILITIES (Proven 2026-02-05)

### Current State

```yaml
phase: EXTRACTION_COMPLETE
tests: 363+
stage_2_extraction: IN PROGRESS (full corpus)
```

### Shipped Capabilities

| Priority | Capability | What It Enables |
|----------|------------|-----------------|
| **P1** | Chronicler | Recursive summarization, clustering (389 clusters), redundancy detection |
| **P2** | Back-propagation | Olya rejection → NEGATIVE_BEAD → Theorist learns |
| **P4** | Auditor Hardening | 6 falsification checks, 10-12% rejection rate |
| **P5** | Queue Atomicity | Crash corruption eliminated |
| **P6** | Runaway Guards | TurnCap (20), CostCeiling ($1/day), StallWatchdog (5min) |

### Multi-Source Extraction

| Tier | Source | Model | Status |
|------|--------|-------|--------|
| OLYA_PRIMARY | 22 PDFs (notes + charts) | claude-opus-4-5 | Validated |
| LATERAL | 18 PDFs (Blessed Trader) | claude-sonnet-4-5 (vision) | Extracted |
| ICT_LEARNING | 24 videos (2022 Masterclass) | deepseek-chat | Pipeline proven |

### Vision Extraction (Breakthrough)

```yaml
capability: Two-pass chart reading (Opus vision → Theorist extraction)
proven: 29 IF-THEN signatures from Olya's annotated charts
terminology_preserved: MMM, IFVG, FVG, MSS, OB, BPR, OTE
cost: ~$0.24/page (Opus), ~$0.08/page (Sonnet)
```

### Invariants Held

```yaml
INV-DEXTER-ALWAYS-CLAIM: TRUE (all output = CLAIM)
INV-DEXTER-NO-PROMOTE: TRUE (human gate mandatory)
INV-DEXTER-SOURCE-LINK: TRUE (full provenance on every bead)
INV-DEXTER-CROSS-FAMILY: TRUE (Theorist ≠ Auditor family)
```

---

## 4. THE S33_P2 UNLOCK

### The Paradigm Shift

```yaml
old_model: "Mine Olya's brain via articulation sessions"
  problem: HARD — blocks progress, requires recall

new_model: "Dexter extracts → Mirror Report → Olya validates"
  advantage: Recognition > Recall
  olya_effort: "Review and correct" vs "articulate from scratch"
  estimated_time: Hours, not days
```

### The Path

```yaml
step_1: Stage 2 completes (full corpus → CLAIM_BEADs)
step_2: Mirror Report generated (readable synthesis)
step_3: Olya reviews (validate/reject/correct — recognition mode)
step_4: Promotions → FACT_BEADs → conditions.yaml updates
step_5: S33_P2 UNBLOCKED
```

This was the COE thesis. Dexter now PROVES it.

---

## 5. RISKS (Load-Bearing — Do Not Dilute)

### RISK_1: HYPOTHESIS_GENERATION

```yaml
issue: "Agents generate hypotheses" = dangerously close to INV-NO-UNSOLICITED

mitigation: |
  - Dexter hypotheses are ALWAYS CLAIM_BEADs
  - They NEVER auto-promote to execution
  - Evidence bundles are presented, human decides
  - The loop is: generate → test → evidence → HUMAN GATE

invariant_needed: INV-DEXTER-NO-AUTO-PROMOTE-TO-LIVE
  rule: "No Dexter-generated thesis can enter live execution without explicit human promotion"
```

### RISK_2: METHODOLOGY_DRIFT

```yaml
issue: 1000 variants may drift from Olya's actual logic

mitigation: |
  - All variants must trace to source FACT_BEADs (Olya-validated)
  - Variant parameters bounded by Cartridge constraints
  - Periodic Olya review of variant population (recognition, not recall)

invariant_needed: INV-VARIANT-PROVENANCE
  rule: "Every variant must link to root FACT_BEAD validated by Olya"
```

### RISK_3: OVERFITTING_AT_SCALE

```yaml
issue: 24/7 testing = 24/7 opportunity to curve-fit

mitigation: |
  - S39 validation suite (walk-forward, Monte Carlo) applies to ALL variants
  - INV-HUNT-EXHAUSTIVE prevents cherry-picking
  - INV-SCALAR-BAN prevents "best variant" ranking
  - Sample size minimums (INV-SLICE-MINIMUM-N)

existing_governance: SUFFICIENT (constitutional ceiling holds)
```

### RISK_4: COST_RUNAWAY

```yaml
issue: 24/7 agents = 24/7 API spend

mitigation: |
  - INV-HUNT-BUDGET already exists
  - Dexter guards already built (TurnCap, CostCeiling, StallWatchdog)
  - Cognitive arbitrage (DeepSeek for volume, Opus for judgment)

existing_governance: SUFFICIENT (extend budget caps)
```

### RISK_5: AUTHORITY_CREEP

```yaml
issue: "Sharpened thesis → recommendation" is one step from NEX-047 (Actionability Engine — KILLED)

mitigation: |
  - Output = evidence bundle + conditional facts
  - NEVER = "you should trade this"
  - Human frames the question of what to act on
  - The bundle is a MENU, not a RECOMMENDATION

invariant_needed: INV-DEXTER-EVIDENCE-NOT-ADVICE
  rule: "Dexter outputs are evidence bundles, never recommendations or advice"
```

---

## 6. NEW INVARIANTS NEEDED

```yaml
# Required before design sprint

INV-DEXTER-NO-AUTO-PROMOTE-TO-LIVE:
  rule: "No Dexter-generated thesis can enter live execution without explicit human promotion"
  enforcement: Promotion ceremony requires human bead + audit trail
  rationale: Prevents autonomous trading from hypothesis generation

INV-VARIANT-PROVENANCE:
  rule: "Every variant must link to root FACT_BEAD validated by Olya"
  enforcement: Variant schema requires source_fact_bead_id
  rationale: Prevents methodology drift from Olya's validated logic

INV-DEXTER-EVIDENCE-NOT-ADVICE:
  rule: "Dexter outputs are evidence bundles, never recommendations or advice"
  enforcement: Output schema validation, no imperative language
  rationale: Maintains "human frames, machine computes" boundary
```

---

## 7. THE FLYWHEEL

```
Dexter extracts → claims accumulate →
mirror report surfaces → Olya validates →
facts promote → conditions.yaml updates →
CSO harness evaluates → Phoenix operates →
variants tested → evidence accumulates →
Sovereign reviews → learnings compound

"The refinery that turns raw expertise into compounding wealth"
```

---

## 8. GATING & TIMELINE

### Prerequisites (Must Be True)

```yaml
gate_1: v0.1 shipped (S47-S52 complete)
gate_2: Olya Stage 2 validation complete (Dexter extraction proven)
gate_3: Mirror Report → Olya review cycle validated
gate_4: S33_P2 unblocked (methodology in conditions.yaml)
```

### Sprint Target

```yaml
design_sprint: S53+ (earliest)
priority: Post-v0.1 strategic horizon
status: CARPARK — capture vision, defer design
```

### What NOT To Do Now

```yaml
- Don't design the full system yet
- Don't allocate sprint time yet
- Don't let it distract from v0.1 (S47-S52)
- Let Dexter Stage 2 + Olya validation PROVE the extraction loop first
```

---

## 9. ARCHITECTURE SKETCH (Future Design Sprint)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DEXTER (Sibling System — Mac Mini)                                      │
│  ├── Extraction: Olya materials → CLAIM_BEADs                            │
│  ├── Hypothesis: Agents generate variants (Perplexity, Grok, Opus)       │
│  ├── Testing: Synthetic River backtests                                  │
│  ├── Forward: IBKR paper trades                                          │
│  └── Output: Evidence bundles → CLAIM_BEADs                              │
├─────────────────────────────────────────────────────────────────────────┤
│  BRIDGE (File-Based)                                                     │
│  ├── dexter/outbox/ → CLAIM_BEADs                                        │
│  ├── phoenix/inbox/ ← reads                                              │
│  └── Zero coupling, observable, greppable                                │
├─────────────────────────────────────────────────────────────────────────┤
│  PHOENIX (Execution — Main System)                                       │
│  ├── Promotion: CLAIM → FACT (human ceremony)                            │
│  ├── Governance: Lease bounds, halt override                             │
│  ├── Execution: Live trading (post-promotion only)                       │
│  └── Output: Performance data → Dexter learns                            │
├─────────────────────────────────────────────────────────────────────────┤
│  SOVEREIGN (Human)                                                       │
│  ├── Reviews: Evidence bundles, Mirror Reports                           │
│  ├── Decides: Promote / Reject / Modify                                  │
│  ├── Frames: What questions to explore                                   │
│  └── Sleeps: While the refinery runs                                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 10. THE BOTTOM LINE

```yaml
what_dexter_is_today:
  "Knowledge extraction from Olya's materials"

what_dexter_becomes:
  "24/7 autonomous research refinery — extract, hypothesize, test, evidence, human gate"

what_this_enables:
  - Olya's expertise compounded while she sleeps
  - 1000 variants tested per night
  - Recognition-based calibration (not recall)
  - Methodology that improves faster than competitors can copy

what_we_already_built:
  - The constitutional ceiling (S35-S39)
  - The execution infrastructure (S40-S44)
  - The governance framework (S46-S47)
  - The proof that Dexter extraction works

what_remains:
  - Olya Stage 2 validation
  - v0.1 shipped
  - Design sprint (S53+)
  - Build the loop

the_scale:
  "The Sovereign Intellectual Refinery isn't a metaphor anymore. It's running."
```

---

*Captured: 2026-02-05*
*Source: G + CTO (Phoenix) + CTO (Dexter) synthesis*
*Status: VISION_LOCKED | CARPARK*
*Gate: Olya Stage 2 + v0.1 shipped*

**OINK OINK.** 🐗🔥
