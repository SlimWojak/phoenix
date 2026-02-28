# UNIFIED_ROADMAP_v1.md
# a8ra — Post-S60 Forward Path
# Single orientation surface for CTO, Advisors, and G

```yaml
document: UNIFIED_ROADMAP_v1.md
version: 1.0
date: 2026-02-26
status: CANONICAL
author: CTO (synthesized from Phoenix S60 + Dexter Gate 1 + Investigation INV-1/2/3)
audience: Fresh CTO, any advisor, G
supersedes: Forward-looking sections of SPRINT_ROADMAP.md
format: M2M_DENSE
```

---

## 1. SYSTEM STATE

```yaml
PHOENIX (Governance Economy):
  repo: ~/phoenix
  version: a8ra v0.1 — post-S60 hardened
  branch: main @ b2c79e2
  sprints: 32 complete (S28-S44, S46-S60)
  tests: 1887+
  invariants: 259 registered
  chaos_vectors: 273
  risk: ZERO_T1 | ZERO_T2
  key_proven:
    sovereign_gate: ALL capital mutations guarded (single chokepoint)
    write_ahead_governance: Beads durable BEFORE state change
    ceremony: Full lifecycle (schedule→check→attest→advance)
    cso: SCALAR_FREE (enum readiness only, no grades)
    projection: HONEST (fails closed, never optimistic)
    economy_isolation: CI_ENFORCED at commit level
    halt: CONSTITUTIONAL (execution spine, <50ms local, <500ms cascade)
    river: OPERATIONAL (EURUSD 1m streaming, 6 pairs historical, 11.8M bars)
    oracle: PHASE_1 cockpit (Three-Surface: HUD + Chat + Code)
    lease_system: State machine + insertion protocol + halt override
    gateway: HARDENED (IBKR live validated)
  rule: INV-NO-CORE-REWRITES-POST-S44 (foundation validated)

DEXTER (Analytical Economy):
  repo: ~/dexter
  version: Gate 1 PASS + Gate 2 QUERY LAYER BUILT + Bridge OPERATIONAL
  branch: main @ 7099707 (tag: s62-gate2-query-layer)
  tests: 455 (332 bead_field + 79 bridge + 44 query layer)
  genesis: 789 beads (788 CLAIMs + 1 METHODOLOGY_DELTA)
  genesis_merkle_root: 5c4d63f29f667d0b80348e3dfc87204aea6488d034c70dd6ae354a57036e963c
  pqc: ML-DSA-65 Dilithium3 (real, ARM64)
  schema: 8 bead types, 15 enums, 6 supporting models, 1283 lines
  integrity: SHA-256 chain + Merkle tree + dual PQC/ECDSA signing
  store: SQLite bi-temporal (DB-level immutability triggers)
  clock: HLC (microsecond, thread-safe, merge-ready for multi-node)
  freeze: DEC-SUBSTRATE-FREEZE active (expires ~2026-03-24, index carve-out granted)
  extraction: 789 curated from 1178. Olya v0.3 corrections honored.
  synthetic_field: 11,387,568 beads, 6 pairs, 5 years, 66GB (validated)
  bridge: 7 modules, 191 tests, 7/7 invariants (pull-based notary)
  query_layer: 6 modules, 44 tests (chain walk, verify, temporal, cross-pair)

BRIDGE (Inter-System):
  status: S62_BUILT | OPERATIONAL (pull-based notary architecture)
  decisions_locked:
    - Bridge = Notary boundary (proof-bearing container, sig verification)
    - Semantic Firewall (all external data enters Economy 1 as CLAIM, never FACT)
    - No auto-revocation (contradiction surfaces for human action)
    - Provenance layering (Athena + Bead provenance separate, never merged)
    - Two-Economy isolation (CI-enforced)
  invariants_banked: 7 (see Section 3)
  prerequisite: ALL MET (Phoenix v0.1 shipped, Gate 1 passed, investigations closed)

HARDWARE:
  m4_max: OPERATIONAL (Phoenix execution, 64GB)
  m3_ultra: ARRIVED (deploying this week — 512GB, knowledge substrate + control plane)
  dgx_spark: ARRIVED (standing by — Grace-Blackwell, Dream Cycle compute)
  mac_minis: OPERATIONAL (development, G sovereign sessions)
  cluster_install: 2026-02-27 (network switch, UPS, office wiring)
```

---

## 2. UNIFIED GATE SEQUENCE

```yaml
# ═══════════════════════════════════════════════════════════════
# PRE-DGX WORK (M3 Ultra + M4 Max only)
# All architectural. All defining how the system COMPOSES.
# ═══════════════════════════════════════════════════════════════

S61: BRIDGE_SPEC + GATE_2_SCOPE
  track_a: BRIDGE_SPEC_v0.1
    what: Notary envelope contract, temporal snapshot rules, sig verification,
          projection direction (Phoenix→BeadField), ingress direction (Dexter→Phoenix),
          no-mutation rules, mapper interface contracts
    method: CTO drafts → Joist Pattern (GPT lints, OWL audits, BOAR stresses)
    output: BRIDGE_SPEC.md (constitutional artifact, frozen after hardening)
    why_first: |
      Bridge defines the ENVELOPE FORMAT that AIR must align with.
      Building AIR before Bridge = attestation bundle mismatch = translator not notary.
      Building deeper Dexter before Bridge = schema drift + semantic mismatch.
  track_b: GATE_2_SCOPE
    what: Define query interfaces Gate 2 must provide for Bridge consumers
    questions: |
      "What queries does Bridge output need to be useful?"
      "What lineage walks does Dream Cycle need?"
      "What temporal slicing does the CSO projection require?"
    output: GATE_2_QUERY_CONTRACT.md (interface spec, not implementation)
  exit_gate: "BRIDGE_SPEC reviewed by 3 advisors, Gate 2 scope defined"
  hardware: ANY (planning, not compute)

S62: BRIDGE_BUILD + GATE_2_QUERIES — COMPLETE ✅ (2026-02-28)
  track_a: BRIDGE_NOTARY — COMPLETE
    what: |
      Pull-based notary: Phoenix emits governance_log.py → Bridge reads, verifies
      (6-op whitelist, sig, hash chain, replay, monotonic GT, version), seals envelope,
      projects as FACT bead. 7 modules. Full pipeline proven end-to-end.
    tests: 191 (bridge 163 + governance mapper 28)
    invariants: 7/7 proven
    phoenix_commit: 2ed5821 (tag: s62-governance-emitter)
    dexter_commit: 7099707 (tag: s62-gate2-query-layer)
  track_b: GATE_2_QUERY_LAYER — COMPLETE
    what: |
      T1: idx_beads_hash_self (chain walk 10K: 21ms, was ~2 hours)
      T2: Timestamp normalizer (bare ISO → canonical +00:00, misuse impossible)
      T3: walk_chain() — CTE backward traversal with link verification
      T4: verify_bead() — hash + chain + Merkle integrity in one call
      T5: known_at() — bi-temporal query with auto timestamp normalization
      T6: FieldQuery — parallel fan-out to 6 DBs, auto timestamp normalization
    tests: 44
  synthetic_field: 11,387,568 beads, 6 pairs, 5 years, 66GB — VALIDATED
  observation: DEXTER_PHASE_1_OBSERVATION_REPORT.md (evidence-based query design)
  exit_gate: |
    "Chain walk 10K < 1s cold. Bare timestamps impossible.
     walk_chain + verify_bead + known_at + FieldQuery exist and pass.
     All 7 bridge invariants PASS. 455 tests green. Zero regressions."
  hardware: M4 Max (both tracks built here)

S63: GATE_3_AIR (Agent Integrity Runtime)
  what: |
    PQC+ECDSA dual signing on all agent actions.
    Attestation bundle format ALIGNED with Bridge notary envelope.
    Code hash verification against approved builds.
    Unsigned mutation rejection + security event logging.
  why_after_bridge: |
    AIR's attestation envelope inherits Bridge's signing semantics,
    provenance layering, and temporal snapshot format.
    Same contract. Same verification path. Natural alignment.
  exit_gate: |
    "Unsigned mutation rejected and logged"
    "Any bead inspectable with full attestation bundle"
    "Local verification: hash chain + Merkle proof + signature"
  hardware: M3 Ultra

S64: GATE_4_SWARM_AGENTS
  what: |
    Director, Librarian, Researcher, Executor agents operational.
    Event bus (NATS/Kafka on M3 Ultra).
    Saga orchestration for proposal lifecycle.
    Commitment Threshold enforced in agent contracts.
  prerequisites: AIR (agents sign), Bridge (agents consume cross-system data),
                 Gate 2 (agents query the field)
  exit_gate: |
    "FACT → CLAIM → SIGNAL → PROPOSAL lifecycle completes autonomously"
    "Rejections produce full PROPOSAL_REJECTED beads (Shadow Field populated)"
    "Agent failure → graceful degradation + alert (no orphan state)"
  hardware: M3 Ultra (orchestration) + M4 Max (Phoenix execution)
  note: Shadow Field begins accumulating volume here

# ═══════════════════════════════════════════════════════════════
# DGX ACTIVATION LINE
# DGX powers on when Gate 4 is producing Shadow Field volume.
# Not before. Hardware waits for the system to need it.
# ═══════════════════════════════════════════════════════════════

S65+: GATE_5_DREAM_CYCLE_v1 (Counterfactuals)
  what: |
    EnvModels trained on historical FACT beads.
    Counterfactual simulation for PROPOSAL_REJECTED beads.
    Leakage metrics (PC, CI, IDS) computed.
    SKILL candidate beads generated from failure trajectories.
  prerequisite: Sufficient Shadow Field volume (Gate 4 producing rejections)
  exit_gate: |
    "Pick any PROPOSAL_REJECTED → counterfactual replay + failure analysis"
    "SKILL candidates generated and linked to source rejections"
  hardware: DGX_REQUIRED (training + simulation)

FUTURE: GATE_6_DREAM_CYCLE_v2 (GALILEO + SkillRL)
  what: Adversarial EnvModel, GAN synthetic regimes, SkillRL pipeline
  hardware: DGX_HEAVY

FUTURE: GATE_7_SOVEREIGN_READINESS
  what: HSM, daily ledger anchoring, DR, incident response, full audit
  hardware: ALL_NODES
```

---

## 3. BRIDGE INVARIANTS (Canonical)

Banked during Investigation INV-1/2/3 synthesis (2026-02-25). These become test cases in S62.

```yaml
INV-BRIDGE-NOTARY:
  rule: "Phoenix rejects BRIDGE claims lacking verified Dexter signature"
  enforcement: Signature verification at ingress, fail-closed

INV-BRIDGE-NO-FLATTEN:
  rule: "Promotion preserves full cryptographic lineage"
  enforcement: Lineage chain verified pre-promotion, truncation = rejection

INV-BRIDGE-PROVENANCE-LAYER:
  rule: "Athena provenance and Bead provenance are separate fields, never merged"
  enforcement: Schema validation rejects merged provenance

INV-SEMANTIC-FIREWALL:
  rule: "All external data enters Economy 1 as CLAIM, never FACT"
  enforcement: Type check at ingress boundary, FACT type = rejection

INV-BRIDGE-NO-AUTO-REVOKE:
  rule: "Analytical contradiction surfaces for human action, never auto-mutates Economy 1"
  enforcement: No write path from analytical economy to governance economy without human gate

INV-BRIDGE-TEMPORAL-SNAPSHOT:
  rule: "Promotion freezes WT/KT verification state at promotion time"
  enforcement: Snapshot hash included in promotion envelope

INV-BRIDGE-HASH-VALIDATE:
  rule: "hash_self + hash_prev + merkle_proof verified pre-promotion, fail-closed"
  enforcement: Verification function returns PASS/FAIL, FAIL = rejection + security event
```

---

## 4. GOVERNING DECISIONS

Decisions that constrain all remaining gates. Not exhaustive — only those that affect sequencing and architecture.

```yaml
STRUCTURAL:
  DEC-TWO-ECONOMIES: "Governance beads and analytical beads are separate systems with a one-way bridge"
  DEC-PROJECTION-NOT-PARTICIPATION: "Phoenix projects into Bead Field. Bead Field doesn't modify Phoenix internals"
  DEC-BRIDGE-IS-NOTARY: "Proof-bearing container with sig verification, not translation layer"
  DEC-SUBSTRATE-FREEZE: "30-day no-schema-change window post Gate 1 (expires ~2026-03-24)"
  DEC-ENERGY-NOT-STORED: "Energy/coherence COMPUTED over Bead Field. NEVER stored on beads"

SOVEREIGNTY:
  INV-HUMAN-FRAMES: "Human frames. Machine computes. Human promotes."
  INV-SOVEREIGN-VETO: "G can halt any task via BROADCAST"
  INV-OLYA-ABSOLUTE: "Olya's NO on methodology is absolute"
  INV-CAPITAL-GATE: "No live execution without human T2 approval"

SEQUENCING:
  DEC-BRIDGE-BEFORE-AIR: "AIR envelope aligns TO Bridge format, not the reverse"
  DEC-GATE2-PARALLEL-BRIDGE: "Query layer developed alongside Bridge, not after"
  DEC-DGX-AT-GATE5: "DGX activates when Shadow Field has volume, not before"

QUALITY:
  INV-NO-CORE-REWRITES-POST-S44: "Foundation validated. No rewrites."
  DEC-MEASURE-TWICE: "Spec hardens (Joist Pattern) before Opus builds"
  DEC-CONSTITUTIONAL-MUZZLE: "SELF_UPGRADING_META is parked. Months of trust first."
```

---

## 5. DOCUMENT HYGIENE

```yaml
# ═══════════════════════════════════════════════════════════════
# ACTIVE ORIENTATION (load for every session)
# ═══════════════════════════════════════════════════════════════

orientation:
  UNIFIED_ROADMAP_v1.md: "THIS FILE — what's next and why"
  a8ra_SYSTEM_MANIFEST_v1_0.md: "System topology, cross-system invariants, component status"
  SPRINT_ROADMAP.md: "Historical sprint record + cumulative metrics"

# ═══════════════════════════════════════════════════════════════
# ACTIVE REFERENCE (search when needed, don't preload)
# ═══════════════════════════════════════════════════════════════

reference:
  BEAD_FIELD_SPEC_v0_3.md: "Analytical bead schema (FROZEN — Gate 1 baseline)"
  CARTRIDGE_AND_LEASE_DESIGN_v1_0.md: "Governance architecture (LOCKED)"
  DREAM_CYCLE_DESIGN_INTENT_v0_1.md: "Gate 5+ design fence (DO NOT BUILD YET)"
  a8ra_MASTER_PLAN_v0_1.md: "Strategic vision (update DELTA LOG only)"
  SYNTHETIC_OLYA_METHOD_v0_3.yaml: "ICT methodology reference"
  SKILL.md: "Operating patterns, templates, advisor coordination"

# ═══════════════════════════════════════════════════════════════
# RETIRE FROM ADVISOR CONTEXT (keep in repo, not in project knowledge)
# ═══════════════════════════════════════════════════════════════

retire:
  BeadField_Gate_1_Status.md: "Historical — Gate 1 is done. Findings actioned."
  dexter_CTO_advisor_reviews.md: "Historical — review complete, risks addressed."
  DRIFT_LOG.md: "Keep in repo for audit trail. Not needed in advisor context."
  MISSION_CONTROL_DESIGN_v0_2.md: "Largely superseded by SYSTEM_MANIFEST + UNIFIED_ROADMAP."
```
---

## 6. DEXTER SURFACE LAYER

```yaml
DEXTER_SURFACE:
  identity: |
    "Dexter" is the researcher behind the glass. He can see everything
    in the repos and bead field, but cannot open the door. He observes,
    analyses, hypothesises, and taps the glass when something's interesting.
    He cannot write beads, modify code, or promote his own ideas.

  engine: Spitfire (OpenClaw on VPS)
  repo: ~/spitfire
  models: Codex 5.3 (primary analysis) + Opus (daily inspection/review)
  access: READ_ONLY OAuth to phoenix, phoenix-swarm, dexter
  hardware: VPS (physically isolated from core infrastructure)
  status: OPERATIONAL

  glass_wall:
    physical: VPS — cannot touch office hardware
    access: READ_ONLY OAuth — cannot write to any repo
    output: ALL output = CLAIM (INV-SEMANTIC-FIREWALL applies)
    promotion: NONE — ideas route through G/Olya for consideration

  modes:
    on_demand: "G or Olya asks Dexter a question — pattern check, contradiction scan, lineage walk"
    autonomous: "Periodic passes over bead exports — surfaces anomalies, flags drift, spots patterns"
    exploration: "Olya browses beads through Dexter's lens (recognition over recall)"

  current_capability:
    - Repo-level forensic architecture review (all 3 repos visible)
    - Bead field analysis (via exported snapshots)
    - Pattern mining across bead types, drawers, regimes
    - Contradiction and drift detection
    - Hypothesis drafts with evidence references

  future_expansion:
    gate_2: "DONE — Gate 2 query layer gives Dexter richer structured queries (S62 Track B)"
    bridge: "DONE — Bridge gives Dexter cross-economy visibility (S62 Track A)"
    shadow_field: "Gate 4+ Shadow Field accumulation gives Dexter failure trajectories to mine"

  constitutional_position:
    - Dexter is a TOOL, not an office (no new coordination surface)
    - No CLAUDE.md, no heartbeat, no TASK_QUEUE integration yet
    - Earns formalization through proven value over weeks
    - If Spitfire engine disappoints, swap it — Dexter character persists
    - Zero architectural debt — read-only observer with advisory output

  does_not_change:
    - Gate sequence (S61-S65+)
    - Bridge spec work
    - Dream Cycle architecture (Dexter is complementary, not replacement)
    - Any constitutional invariant
    - Write authority on any repo
```
## 7. HARDWARE DEPLOYMENT SEQUENCE

```yaml
FRIDAY_2026_02_27:
  action: Installers wire office (network switch, UPS, cluster space)
  no_rush: Let them finish. Clean install > fast install.

WEEKEND:
  m3_ultra_deploy:
    1: Clone dexter repo to M3
    2: pip install -r bead_field/requirements.txt
    3: pytest bead_field/tests/ -v (274 tests PASS)
    4: Copy genesis.db + keys (secure transfer, INV-NO-SECRETS-IN-REPO)
    5: Verify Genesis Merkle root: 5c4d63f29f667d0b80348e3dfc87204aea6488d034c70dd6ae354a57036e963c
    6: Bead Field service operational
  result: Gate 1 OPERATIONAL on production hardware (hours, not weeks)

DGX_ACTIVATION:
  trigger: Gate 4 operational + Shadow Field accumulating volume
  not_before: S64 complete
  first_use: Gate 5 Dream Cycle v1 (EnvModel training + counterfactual simulation)
  note: "Standing by is not waste. It's discipline."
```

---

## 8. NEXT SESSION

```yaml
S62_COMPLETE: |
  Sprint 62 delivered: Bridge notary (13 modules, 191 tests, 7/7 invariants)
  + Gate 2 query layer (6 modules, 44 tests) + 11.4M synthetic field.
  455 total Dexter tests. Zero regressions.
next_sprint_pending: |
  S63 AIR (Agent Integrity Runtime) — sequencing decision pending.
  Bridge is now the reference for AIR envelope alignment.
  Alternative: Dexter Phase 2 deeper analytics or Spitfire retarget.
```

---

*Two economies. One bridge. Seven invariants. The notary holds the line.*

*OINK OINK.* 🐗🔥
