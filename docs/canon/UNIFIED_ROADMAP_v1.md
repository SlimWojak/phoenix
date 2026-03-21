# UNIFIED_ROADMAP_v1.md
# a8ra — Post-S62 Forward Path
# Single orientation surface for CTO, Advisors, and G

```yaml
document: UNIFIED_ROADMAP_v1.md
version: 3.1
date: 2026-03-20
status: CANONICAL — updated post S64 COMPLETE (all 6 gates sealed)
author: CTO (synthesized from S62-S64 + RA calibration detour)
audience: Fresh CTO, any advisor, G
supersedes: Forward-looking sections of SPRINT_ROADMAP.md
format: M2M_DENSE
methodology: SYNTHETIC_OLYA_METHOD_vLOCK.yaml (canonical — supersedes v0.4, v0.6)
```

---

## 1. SYSTEM STATE

```yaml
PHOENIX (Governance Economy):
  repo: ~/phoenix
  version: a8ra v0.1 — post-S60 hardened
  branch: main @ 3c28211
  sprints: 36 (S28-S44, S46-S60, S62-S64)
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
  version: Gate 1 PASS + Gate 2 BUILT + Bridge OPERATIONAL + S64 COMPLETE (all 6 gates)
  branch: main (post-Gate 4 — 11 vLOCK producers committed)
  tests: 651 (332 bead_field + 79 bridge + 44 query layer + 158 producers + 38 legacy)
  genesis: 789 beads (788 CLAIMs + 1 METHODOLOGY_DELTA)
  genesis_merkle_root: 5c4d63f29f667d0b80348e3dfc87204aea6488d034c70dd6ae354a57036e963c
  pqc: ML-DSA-65 Dilithium3 (real, ARM64)
  schema: 8 bead types, 15 enums, 6 supporting models, 1283 lines
  integrity: SHA-256 chain + Merkle tree + dual PQC/ECDSA signing
  store: SQLite bi-temporal (DB-level immutability triggers)
  clock: HLC (microsecond, thread-safe, merge-ready for multi-node)
  freeze: DEC-SUBSTRATE-FREEZE (expires ~2026-03-24, index carve-out granted)
  methodology: SYNTHETIC_OLYA_METHOD_vLOCK.yaml (supersedes v0.4 — VI removed, 13 primitives locked)
  state_detection: STATE_DETECTION_LOGIC_v2.yaml (v2.4 — EXPANSION/RETRACE/RANGE classifier)
  synthetic_field: 11,387,568 FACTs, 0 CLAIMs, 6 pairs, 5 years, 69GB (field-deployed on M3)
  bridge: 7 modules, 191 tests, 7/7 invariants (pull-based notary)
  query_layer: 6 modules, 44 tests (chain walk, verify, temporal, cross-pair)
  spitfire_audit: 14 findings (0 CRITICAL, 3 HIGH — actioned in S64 Track A)
  reference_impl: "detect.py in ~/research_accelerator — test oracle for core producers"
  ground_truth: "14 Olya-annotated trades (Sep 2025 – Mar 2026)"
  producers: "11 vLOCK CLAIM producers operational (VI retired)"
  gate6_olya_confirmed: 2026-03-20
  port_verification: "14/14 trades PASS, 0 unexpected misses"
  analytical_state: "11.4M FACTs, 0 CLAIMs — producers operational, S65 will generate CLAIMs on live data"

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
  cockpit: MacBook Pro M3 Max 36GB — operator terminal (Tailscale, ET, Ansible)
  m4_studio: OPERATIONAL (Phoenix execution, M4 Max 64GB, sprint dev)
  m3_ultra: COO STATION (512GB, 69GB field, Claude Code + QMD + Superpowers + Ralph Loop)
  dgx_dexter: OPERATIONAL (DGX Spark GB10 120GB — production inference, S68+)
  dgx_playground: OPERATIONAL (DGX Spark GB10 120GB — experimental sandbox, Qwen3.5-35B-A3B via vLLM, ACL isolated)
  mac_mini: OPERATIONAL (Oracle/CSO office, G sovereign sessions)
  cluster: 5-node Tailscale mesh, MCP health layer on all nodes, Ansible IaC
  canonical_reference: phoenix-swarm/CLUSTER_MANIFEST.md (v1.1, 2026-03-19)
```

---

## 2. UNIFIED GATE SEQUENCE

```yaml
# ═══════════════════════════════════════════════════════════════
# PRE-DGX WORK (M3 Ultra + M4 Max only)
# All architectural. All defining how the system COMPOSES.
# ═══════════════════════════════════════════════════════════════

S61: BRIDGE_SPEC + GATE_2_SCOPE — COMPLETE ✅ (spec phase, delivered as input to S62)
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

S63: FIELD_ACTIVATION — COMPLETE ✅ (2026-03-03)
  what: |
    T1: M3 Ultra migration — 69GB field deployed, 455/455 PASS, SSH mesh
    T2: Observation report — 11 patterns, field is 100% FACT, analytical void confirmed
    T3A: Spitfire audit — 14 findings, 0 CRITICAL, container sound
    T3B: CLAIM_PIPELINE_SPEC v0.1 — Joist-hardened, 6 types, 7 questions resolved
    T4: Canon reconciliation — 12/12 deltas applied
    T5: Proto-AIR v0.2 — schema only, 6 INV-AIR-* invariants
  why_reframe: |
    Advisor poll (GPT+OWL+BOAR) unanimous: signing on unmined substrate = premature.
    Field is 66GB idle asset. Prove methodology↔data fit before agent infrastructure.
  outcome: |
    Field deployed on M3. Analytical void confirmed (11.4M FACTs, 0 CLAIMs).
    Container audited sound. CLAIM pipeline spec ready. AIR header drafted.
    5 local models validated, 1 disqualified.
  dexter_commit: 21b48a4 (tag: s63-field-activation)
  hardware: M3 Ultra (field) + M4 Max (dev) + VPS (Spitfire)

S64: CLAIM_PIPELINE Phase 1 + METHODOLOGY CALIBRATION — COMPLETE ✓ (2026-03-20)
  status: "All 6 gates sealed. vLOCK methodology operational in core dexter."
  what: |
    Original scope: 6 deterministic CLAIM producers.
    Actual scope expanded: Full methodology rewrite (v0.4 → vLOCK),
    native multi-TF detection, 13 L1 primitives calibrated,
    State Detection logic discovered and specified (v2.4),
    reference implementation (detect.py) built,
    14 Olya-verified ground truth trades captured.
  tracks:
    A: Container hardening (SPF-005, SPF-006, SPF-012) — COMPLETE
    B: 6 Phase 1 producers (v0.4 definitions) — COMPLETE (superseded by vLOCK)
    C: CSO validation — triggered methodology recalibration
    D: Methodology calibration (2-week detour, Mar 5-19) — COMPLETE
  deliverables:
    - SYNTHETIC_OLYA_METHOD_vLOCK.yaml (locked L1/L1.5 spec, 13 primitives)
    - STATE_DETECTION_LOGIC_v2.yaml (HTF phase classifier — EXPANSION/RETRACE/RANGE)
    - detect.py reference implementation (13 primitives, all TFs, test oracle)
    - 14 Olya-annotated ground truth trades (Sep 2025 – Mar 2026)
    - Research Accelerator platform (~/research_accelerator)
    - Autoresearch harness (evaluate.py + sweep.py)
  exit_gates:
    gate_1: MET — Track A+B shipped (493 tests)
    gate_2: MET — Session/reference levels CSO-validated
    gate_3: MET — vLOCK methodology Olya-locked (walk-forward PASS, 14/14 trades)
    gate_4: SEALED — 11 vLOCK producers built, 158 tests, VI retired, oracle comparison PASS
    gate_5: SEALED — v0.4 vs vLOCK diff report (FVG 5m 337→236, VI 4886→0, 6 new primitives)
    gate_6: SEALED — 14/14 annotated trades PASS, 0 unexpected misses (Olya confirmed)
  hardware: M4 Max (build) + M3 Ultra (production field)

S65: STRATEGY_ASSEMBLY — ACTIVE (NEXT)
  status: NEXT
  prerequisite: S64 COMPLETE ✓
  what: |
    Detection pipeline wiring + HTF producers + composition layer + strategy assembly.
    Run in parallel to live trading. Expand ground truth pool.
    System finds Olya's logic in live IBKR data.
  tracks:
    track_A: "Detection Pipeline — River→producer wiring, HTF producers, state detection"
    track_B: "Composition Layer — level lifecycle, spatial queries, composite CLAIMs"
    track_C: "Strategy Assembly — five-factor checklist, cartridge update, SIGNAL generation"
  includes:
    - River→producer wiring (live EURUSD 1m → dexter producers)
    - HTF producers (1H, 4H, Daily, Weekly detection)
    - State Detection integration (EXPANSION/RETRACE/RANGE from v2.4)
    - Level lifecycle tracking (equal H/L, PWH/PWL — ACTIVE → SWEPT)
    - Spatial query predicates (price vs zone/level filtering)
    - Composite CLAIM generation (MSS + OB + Sweep chains)
    - OTE producer (derived from MSS dealing range)
    - Strategy assembly from L2 Strategy Designer output
    - Cartridge template update to vLOCK primitive names
  carried_from_s64:
    - DEC-CE-TOUCHED-WICK-PENDING-OLYA
    - HTF_MSS_PROPOSED (1H/4H params)
    - LIQUIDITY_SWEEP_level_pool
    - MSS_15m_cascade (monitor)
  first_gate: "HTF detection running on live EURUSD — Olya visual confirm"
  exit_gate: |
    "HTF + LTF producers operational. State Detection integrated.
     Five-factor checklist computable. Strategy assembly generates SIGNALs."
  hardware: M4 Max + M3 Ultra

S66: GATE_3_AIR (Agent Integrity Runtime) — was S64
  what: |
    PQC+ECDSA dual signing on all agent actions.
    Attestation bundle format ALIGNED with Bridge notary envelope.
    Code hash verification against approved builds.
    Unsigned mutation rejection + security event logging.
  why_after_pipeline: |
    S63-S65 observation + production friction shapes AIR spec.
    Proto-AIR header from S63.T5 becomes input to full AIR design.
    "Don't build the passport office until the citizens have something to say."
  exit_gate: |
    "Unsigned mutation rejected and logged"
    "Any bead inspectable with full attestation bundle"
    "Local verification: hash chain + Merkle proof + signature"
  hardware: M3 Ultra

S67: GATE_4_SWARM_AGENTS — was S65
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
# DGX PRODUCTION ACTIVATION LINE
# DGX playground is operational (Qwen3.5-35B, experiments).
# DGX dexter (production inference) activates when Gate 4
# is producing Shadow Field volume. Not before.
# ═══════════════════════════════════════════════════════════════

S68+: GATE_5_DREAM_CYCLE_v1 (Counterfactuals)
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
  SYNTHETIC_OLYA_METHOD_vLOCK.yaml: "ICT methodology — CANONICAL (13 primitives locked)"
  STATE_DETECTION_LOGIC_v2.yaml: "HTF phase classifier (v2.4 — EXPANSION/RETRACE/RANGE)"
  CLUSTER_MANIFEST.md: "5-node cluster topology (v1.1)"
  SKILL.md: "Operating patterns, templates, advisor coordination"

deprecated:
  SYNTHETIC_OLYA_METHOD_v0_3.yaml: "Superseded by vLOCK"
  SYNTHETIC_OLYA_METHOD_v0_4.yaml: "Superseded by vLOCK (audit trail only)"
  SYNTHETIC_OLYA_METHOD_v0_6.yaml: "Superseded by vLOCK (audit trail only)"

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
    - Gate sequence (S61-S68+)
    - Bridge spec work
    - Dream Cycle architecture (Dexter is complementary, not replacement)
    - Any constitutional invariant
    - Write authority on any repo
```
## 7. HARDWARE STATUS

```yaml
CLUSTER_OPERATIONAL: |
  5-node Tailscale mesh fully wired (2026-03-19).
  See phoenix-swarm/CLUSTER_MANIFEST.md v1.1 for full topology.

NODES:
  cockpit: MacBook M3 Max — G's terminal (ET aliases, Ansible, Termius mobile)
  m3_ultra: COO Station — bead field (69GB), Claude Code orchestrator, MCP health
  m4_studio: Phoenix Node — core dev, sprint execution, test suites
  dgx_dexter: Inference Node — production DGX Spark, standing by for S68+ Dream Cycle
  dgx_playground: Sandbox Node — experimental DGX Spark, Qwen3.5-35B-A3B, ACL isolated

INFRASTRUCTURE:
  transport: Eternal Terminal (immortal sessions across all nodes)
  multiplexer: Zellij (persistent named sessions per node)
  iac: Ansible playbooks (phoenix-swarm/ansible/)
  mcp: HTTP health layer port 7700 (all 4 server nodes)
  coo: QMD 2.0.1 + Superpowers 5.0.2 + Ralph Loop 1.0.0 on M3

DGX_PRODUCTION_ACTIVATION:
  trigger: Gate 4 operational + Shadow Field accumulating volume
  not_before: S67 complete (Gate 4 Swarm Agents)
  first_use: Gate 5 Dream Cycle v1 (EnvModel training + counterfactual simulation)
  hardware: dgx_dexter (production), dgx_playground (experiments)
```

---

## 8. NEXT SESSION

```yaml
S64_STATUS: |
  Gates 1-3 MET (2026-03-19). Track A+B shipped (493 tests). Track C triggered
  a 2-week methodology calibration detour that produced vLOCK (13/13 primitives
  locked), State Detection v2.4 (14/14 phase classification), detect.py reference
  implementation, 14 Olya-annotated ground truth trades, and autoresearch harness.

  Methodology is LOCKED. State Detection is VALIDATED. Producer rewrite is de-risked
  by the reference implementation (detect.py output = expected result for core).

GATE_4_NEXT: |
  Port vLOCK L1 algorithms from detect.py to core a8ra CLAIM producers.
  8 core producers + 3 derived (IFVG, BPR, OTE).
  Native multi-TF: each producer runs per-TF on aggregated bars.
  Bar aggregation utility (1m → 5m/15m/1H/4H) — prerequisite.
  TF metadata in CLAIM bead metadata dict.
  ATR lookback pre-seeding for HTF producers.
  Verification: producer output matches detect.py enriched detection JSON.

OPEN_ITEMS_CARRIED_FORWARD:
  - SMT primitive: 2 of 14 trades used DXY divergence as sweep substitute (tolerated)
  - Level lifecycle tracking: ACTIVE → SWEPT (deferred to S65)
  - Monthly/Weekly detection: deferred (Daily/4H/1H sufficient for all 14 trades)
  - Regime validation: 14 trades span 7 months; 5-year data available for future expansion
```

---

*Two economies. One bridge. Seven invariants. Thirteen locked primitives. The notary holds the line.*

*OINK OINK.* 🐗🔥
