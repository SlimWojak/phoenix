# a8ra SYSTEM MANIFEST

```yaml
document: SYSTEM_MANIFEST
version: 2.6
date: 2026-03-26
status: CANONICAL — updated post S69 COMPLETE (faithful sweep port, backfill initiated)
purpose: Single M2M orientation for every Claude instance in the a8ra ecosystem
update_discipline: Any session making a significant decision appends a MANIFEST DELTA
owner: G (Sovereign Operator)
supersedes: SYSTEM_MANIFEST v2.0
methodology: SYNTHETIC_OLYA_METHOD_vLOCK.yaml (canonical — supersedes v0.4, v0.6)
```

---

## 0. READ THIS FIRST

You are a Claude instance serving one office in the a8ra ecosystem. You do not have access to other offices' conversation histories. This document is the single source of truth for the system as a whole.

```yaml
PRECEDENCE:
  cross_cutting: This manifest wins (invariants, data schema, security)
  office_specific: Your office docs win (implementation details)
  world_view: Read a8ra_MASTER_PLAN.md for strategic context
```

---

## 1. WHAT a8ra IS

```yaml
NAME: a8ra (pronounced "a-eight-ra")
TYPE: Sovereign Intelligence Refinery
CORE_PRINCIPLE: "Human frames. Machine computes. Human promotes."

TWO_ECONOMIES:
  governance: Deterministic system state (Phoenix, 17+ bead types, battle-tested)
  analytical: Mineable knowledge substrate (Bead Field, 8 types, bi-temporal, signed)
  bridge: One-way valve — analytical→governance only via validated SKILL beads
  detail: See a8ra_MASTER_PLAN.md Section 2
```

---

## 2. HUMANS

```yaml
G:
  role: Sovereign Operator
  authority: SUPREME
  function: Strategic direction, capital allocation, cross-context bridge, sprint approval
  veto: BROADCAST.md → all offices halt on wake

OLYA:
  role: CSO / Oracle
  authority: DOMAIN — sovereign over trading methodology
  function: CLAIM→FACT promotion, gate calibration, curriculum curation
  veto: Absolute and final. No appeal. Rejection → NEGATIVE_BEAD → Dream Cycle.
  principle: "Recognition over recall. Forensic surgeon, not morgue consumer."
```

---

## 3. HARDWARE TOPOLOGY

```yaml
NODE_DGX — NVIDIA DGX Spark (Grace-Blackwell):
  status: ARRIVED (2026-02-21) — standing by for Gate 5+
  role: Compute Plane (Economy 2 heavy lifting)
  office: DEXTER_OFFICE

NODE_M3 — Mac Studio M3 Ultra (512GB):
  status: FIELD_DEPLOYED (455/455 PASS, 69GB field, 2026-03-03)
  role: Knowledge Substrate + Control Plane
  office: DEXTER_OFFICE (knowledge + control)

NODE_M4 — Mac Studio M4 Max (64GB):
  status: OPERATIONAL
  role: Core Development + Phoenix Execution
  office: CORE_OFFICE

NODE_MINIS — Mac Mini Gateway Nodes:
  status: OPERATIONAL
  role: Lightweight coordination, CSO, G sovereign
  offices: G_SOVEREIGN, CSO_OFFICE

NODE_VPS — ChadBoar (Singapore):
  status: OPERATIONAL (live trading)
  role: Disposable canary testbed
  sovereignty: Sandboxed. 14 SOL. No core connection.

CONNECTIVITY:
  core: Encrypted LAN (10GbE) DGX ↔ M3 Ultra
  coordination: Git-based (phoenix-swarm/)
  fallback: API-first ($1-3/day OpenRouter) before local hardware
```

---

## 4. COMPONENT STATUS

### 4.1 Phoenix (Constitutional Trading System)

```yaml
status: v0.1 SEALED + S62 COMPLETE (ZERO TIER_1, ZERO TIER_2, HALT OPERATIONAL, BRIDGE OPERATIONAL)
repo: phoenix/ (private, tag: v0.1)
current_sprint: S62 COMPLETE — BRIDGE_BUILD + GATE_2 (2026-02-28)

cumulative_metrics:
  sprints_complete: 33 (S28-S44, S46-S60, S62)
  tests_passing: 1887+
  chaos_vectors: 273/273 PASS
  invariants_registered: 259 Phoenix + 7 Bridge + 1 DEC-FREEZE-INDEX-CARVEOUT
  mypy_strict_capital_path: 0 errors (governance/ execution/ cso/)
  halt_mechanism: OPERATIONAL (constitutional, chaos-proven, boot-gate validated)
  bead_types: 17+
  gates_mapped: 48
  seal_date: 2026-02-22
  s52_hardening_date: 2026-02-23
  river_phase_1: COMPLETE (2026-02-22)
  s59_completion_date: 2026-02-25   # LEASE_WIRE
  s60_completion_date: 2026-02-25   # CEREMONY_AND_HYGIENE
  s62_completion_date: 2026-02-28   # BRIDGE_BUILD + GATE_2

architecture:
  governance: |
    Lease/Cartridge system (S46 design locked, S47 implemented).
    Cartridge = WHAT (strategy identity). Lease = WHEN/HOW MUCH (governance wrapper).
    State machine: DRAFT→ACTIVE→EXPIRED|REVOKED|HALTED.
    Insertion: 8-step protocol with rollback.
    Ceremony: Weekly attestation, PERISH_BY_DEFAULT.
  execution: |
    9-state position lifecycle (canonical: execution/positions/). T2 human gate for capital.
    Paper broker uses 5-state FSM (execution/positions/paper.py). S52 deprecated execution/position.py.
    IBKR integration (paper mode validated, live ready).
    Halt: <50ms local, <500ms cascade.
    S51: Asia Range Scalp execution engine (entry, SL/TP, position sizing, session limits).
    S52: GovernanceSentinel — passive bounds enforcement, <2ms, dead-man's switch.
  cso: |
    5-drawer gate evaluation via cabinet model v1.1 (48 gates).
    Each cartridge carries complete self-contained DrawerConfig.
    Canonical drawers: HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION.
    S51 drawer aliases accepted at parser: CONTEXT/MONITORING/SETUP/EXECUTION/MANAGEMENT.
    methodology_template.yaml as reference (conditions.yaml retained for imports).
    Boolean only (INV-HARNESS-1). No grades, no confidence scores.
    CSE emission with evidence. Multi-pair scan.
    S51: market_state_builder.py bridges enrichment→evaluator (was gap).
  river: |
    RIVER PHASE 1 COMPLETE (S51). Epistemic root of Phoenix — all trading
    decisions trace to data that flows through the River. Constitutional
    grade: immutable parquet, bitemporal, source-tagged, seam-attested.
    See river architecture section below (4.1.1) for full detail.
  enrichment: |
    S51: Pipeline now WIRED end-to-end via River (parquet → DuckDB → DataFrame).
    L1-L6: Production (155 columns from OHLCV via River).
    L7: Asia Scalp primitives (RE_ACCEPTANCE, sweep extension, FVG validation, state machine).
    market_state_builder.py: Frozen dataclass factory, pure adapter, point-in-time join.
    INV-RIVER-FRESHNESS: Refuses stale data (staleness gate in builder).
  monitoring: |
    Heartbeat, semantic health, HUD surface (SwiftUI, <500ms latency).
    manifest_writer.py bridges state to HUD.
  memory: |
    Athena: CLAIM/FACT/CONFLICT bead separation (S37).
    BeadStore: Append-only, provenance-linked.
    CFP: Conditional fact projector with causal ban (S35).
    Hunt: Exhaustive grid, no survivor ranking (S38).

s51_driveshaft:
  theme: "Wire the engine to the gearbox. First strategy runs end-to-end."
  strategy: Asia Range Scalp (mean reversion, no daily bias, set-and-forget)
  new_components:
    - cso/market_state_builder.py (enrichment→evaluator bridge)
    - enrichment/layers/l7_asia_scalp.py (RE_ACCEPTANCE + Asia primitives)
    - execution/asia_scalp.py (trade lifecycle engine)
    - cartridges/active/asia_range_scalp.yaml (v2.0, Olya canonical)
  new_invariants:
    - INV-NO-FORMING-CANDLE
    - INV-BUILDER-PURE-ADAPTER
    - INV-PIT-JOIN-ONLY
    - INV-ALIAS-PARSER-BOUNDARY
  next: S52 CSO_SURFACE (HUD gates, alerts, CSO Claude wiring)

river_phase_1:
  status: COMPLETE (2026-02-22)
  theme: "The epistemic root of Phoenix. All trading decisions trace to River data."
  doctrine: RIVER_SYNTHESIS.md (3-advisor convergence, G-locked)
  seam_attestation: SIGNED (G, 2026-02-22, three-way validated)

  purpose: |
    The River is Phoenix's market data foundation — immutable, bitemporal,
    source-tagged parquet files queried via DuckDB. Every enrichment column,
    every gate evaluation, every trade proposal traces back to River bars.
    "River is the epistemic root of Phoenix" (GPT advisor). Pollute it,
    Phoenix dies. Constitutional infrastructure, not plumbing.

  data_flow: |
    Dukascopy (5yr history, 2020-11 to 2025-11) ──┐
                                                    ├──→ Daily Parquet Files
    IBKR Historical (reqHistoricalData, ~30 days) ──┤    ~/phoenix-river/{pair}/{year}/{mm}/{dd}.parquet
                                                    │
    IBKR Live (reqHistoricalData keepUpToDate=True, 1m) ┘
        → Staging JSONL → Daily Parquet (at 17:00 NY forex day close)
                    │
                    ▼
    DuckDB Query Layer (read-only, SQL over parquet glob)
        → Ghost bar injection (is_ghost=True for gaps)
        → Timeframe derivation (1m → 5m/15m/1H/4H/1D)
        → Enrichment L1-L7 → MarketState → Gate Evaluation

  schema:
    RAW_BAR_SCHEMA: |
      9 columns written to parquet (write-once, never modified):
      timestamp (WT, UTC), open, high, low, close, volume,
      source (dukascopy|ibkr), knowledge_time (KT, UTC), bar_hash (sha256)
    MATERIALIZED_BAR_SCHEMA: |
      10 columns returned by RiverReader (RAW + is_ghost):
      Ghost bars injected at query time for missing 1m slots.
      close=prev_close, volume=0, source='ghost', is_ghost=True.

  volume_semantics: |
    volume > 0  → real tick count (Dukascopy)
    volume = -1 → IBKR MIDPOINT (no tick data for forex midpoint)
    volume = 0  → ghost bar (synthetic continuity, never in raw parquet)
    Three distinct states. Do NOT compare across vendors.

  ghost_bar_policy: |
    Raw parquet: gaps remain gaps (FLAG_ONLY, per ICT_DATA_CONTRACT §7.2)
    Materialized view: ghost bars injected (is_ghost=True, volume=0, source='ghost')
    Gate evaluation: ghost bars → SKIP (neither PASS nor FAIL)
    Rationale: enrichment pipeline (asof_merge, L2 groupby) requires continuous 1m series.

  bitemporal_model: |
    Every bar carries two timestamps:
      world_time (WT): When the bar occurred in the market (timestamp column)
      knowledge_time (KT): When Phoenix first learned this bar existed
    Historical ingestion: KT = script_run_timestamp
    Live streaming: KT = IBKR callback received_timestamp
    Prevents temporal hallucination: backfilled bars don't "exist" at T-0 in backtests.

  source_boundary: |
    Dukascopy: 2020-11-23 to 2025-11-21 (positive tick volume, Sunday open 00:00 UTC)
    IBKR: 2025-11-22 onwards (volume=-1, Sunday open ~22:15 UTC)
    Boundary is razor-sharp across all 6 pairs (T1 audit confirmed).

  seam_attestation: |
    Three-way cross-validation (unprecedented — wasn't in original brief):
    1. Dukascopy→IBKR at source boundary (Nov 21/22) — price continuity PASS
    2. NEX-IBKR vs T0-IBKR in overlap zone (Jan 18→Feb 20) — 99.3% exact match
    3. Full River continuity — ~1.96M bars per pair, no unexpected gaps
    G signed RIVER_SEAM_ATTESTATION 2026-02-22.
    Report: docs/build_docs/RIVER_SEAM_REPORT.md

  health_monitoring: |
    RIVER_HEALTH_REPORT: Daily automated integrity check (gap count, ghost count,
      staleness, hash sample verification, source distribution, seam zone)
    Streamer heartbeat: ~/phoenix-river/.heartbeat.json (atomic JSON, state machine: STARTED→STREAMING→DEGRADED→STOPPED)
    INV-RIVER-FRESHNESS: market_state_builder refuses data older than threshold
    Real-time gap alert: consecutive ghost-eligible gaps during trading → immediate alert

  canonical_pairs: [EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD]
  partition: "~/phoenix-river/{pair}/{year}/{mm}/{dd}.parquet (RIVER_ROOT env override)"
  data_volume: "~1.96M bars per pair (5.3 years), ~11.8M bars total"

  invariants:
    INV-RIVER-BITEMPORAL: "Every bar carries world_time + knowledge_time"
    INV-RIVER-IMMUTABLE: "Raw parquet files are write-once, never modified"
    INV-RIVER-CONTINUOUS: "No gaps in materialized 1m series (ghosts flagged)"
    INV-RIVER-SOURCE-TAG: "Every bar carries source provenance forever"
    INV-RIVER-IBKR-PRIMACY: "Execution venue = data authority for live"
    INV-RIVER-FRESHNESS: "market_state_builder refuses stale data"

  code:
    new_files:
      - "river/schema.py (RAW_BAR_SCHEMA, hashing, validation, get_river_root)"
      - "river/writer.py (RiverWriter — IBKR → daily parquet)"
      - "river/reader.py (RiverReader — DuckDB, ghost injection, TF derivation)"
      - "river/streamer.py (RiverStreamer — live 1m → staging → daily)"
      - "river/nex_ingestor.py (NEX → River migration with source tags)"
      - "river/seam.py (three-way seam reconciliation)"
    modified_files:
      - "data/river_reader.py (RIVER_SOURCE bridge — parquet default, legacy fallback)"
      - "docs/canon/ICT_DATA_CONTRACT.md (§7.2-7.5 ghost bar amendment + invariants)"

s62_governance_emitter:
  file: governance/governance_log.py
  purpose: "Bridge provenance root — append-only JSONL emitter for governance events"
  commit: 2ed5821 (tag: s62-governance-emitter)
  tests: 28
  note: "Phoenix-side of the inter-economy Bridge. Dexter bridge/reader.py polls this."

key_blockers:
  s45: BLOCKED (Olya CSO calibration — CoE model accepted, not required for v0.1)
  rule: INV-NO-CORE-REWRITES-POST-S44 ACTIVE
  note: v0.1 shipped without S45. S45 is post-v0.1 enhancement.

integration_with_bead_field:
  status: S62_BUILT — BRIDGE OPERATIONAL (2026-02-28)
  pattern: Projection, not participation (proven in S48 HUD, now built for Bridge)
  mechanism: "governance_log.py emit → Bridge reader → verify → seal → FACT bead"
  phoenix_change: "governance/governance_log.py (145 lines, 28 tests)"
  dexter_modules: "bridge/ (7 modules, 191 tests, 7/7 invariants)"
  pipeline_proven: "Full end-to-end: emit → read → verify → seal → project → FACT bead in Bead Field"
```

### 4.2 Dexter (Sovereign Evidence Refinery)

```yaml
status: GATE_1_PASS + GATE_2_BUILT + BRIDGE_OPERATIONAL + S66 COMPLETE (2026-03-22)
repo: dexter/ (private)
head: b7bef38 (post-S66 — state snapshots, KZ gate v2, Dream Cycle v1)

extraction: COMPLETE (789 Genesis beads curated from 1178 extractions, 73 bundles, 363 tests)
bead_field_spec: v0.3 (OPEN_SOURCE enum added)
bead_field:
  tests: 1088 (332 bead_field + 79 bridge + 44 query + 651 S64 + 218 S65 + 219 S66 — overlapping with prior counts)
  genesis_beads: 789 (curated from 1178 extractions)
  genesis_merkle_root: 5c4d63f29f667d0b80348e3dfc87204aea6488d034c70dd6ae354a57036e963c
  pqc: ML-DSA-65 Dilithium3 (real, ARM64)
  substrate_freeze: 30 days (expires ~2026-03-24, index carve-out granted)

bridge:
  status: OPERATIONAL (S62 Track A)
  modules: 7 (types, verification, state_store, reader, envelope, orchestrator, governance_mapper)
  tests: 191
  invariants: 7/7 proven
  pattern: Pull-based notary (reader polls governance JSONL, verifies, seals, projects)
  pipeline: "governance_log.py emit → reader → verify (6 checks) → seal envelope → project FACT bead"

query_layer:
  status: BUILT (S62 Track B)
  modules: 6 (timestamps, chain, verify, temporal, field_query, __init__)
  tests: 44
  capabilities:
    - "walk_chain: CTE backward traversal, 10K steps in 21ms"
    - "verify_bead: hash + chain + Merkle integrity"
    - "known_at: bi-temporal query (WT range + KT cutoff)"
    - "FieldQuery: parallel cross-pair fan-out (ThreadPoolExecutor)"
    - "Timestamp normalization: canonical YYYY-MM-DDTHH:MM:SS+00:00"

synthetic_field:
  status: VALIDATED (2026-02-28)
  beads: 11,387,568
  pairs: 6 (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD)
  range: 2020-2025 (5 years)
  storage: 66GB (6 SQLite databases)
  location: ~/dexter/tools/synthetic/

architecture:
  pipeline: Theorist→Auditor→Bundler→CLAIM_BEADs
  model_routing: DeepSeek (extraction) + Gemini (audit)
  memory: Bead chain (JSONL) + THEORY.md (recursive summary)
  security: Docker sandboxed, 4-layer injection guard, runaway caps

end_state: 24/7 R&D on M3 Ultra + DGX Spark
```

### 4.3 ChadBoar (Canary Testbed)

```yaml
status: LIVE TRADING — ~5000 beads/day, ~1800 rejections/day
purpose: Real-world Bead Field validation

canary_findings:
  1: "Integration tests must cover actual signing API"
  2: "Deployment config must be audited (INV-DEPLOYMENT-AUDIT)"
  3: "Migration tooling needed from Gate 1"
  4: "Refinery Latency catches hallucination (zero latency = suspicious)"
  5: "FACT beads need quality flag enum"

cannot_test: [multi-agent, cross-node HLC, PQC, XTDB, DGX compute, agent handoff, HSM]
```

### 4.4 Mission Control

```yaml
status: v0.2 LOCKED (13/13 decisions, 32 invariants)
ground_tests: 6/6 PASS (2026-02-09)
coordination: phoenix-swarm/ (30 files)
persistence: 5-layer (CLAUDE.md, /memory, hooks, MCP, git)
```

---

## 5. CROSS-SYSTEM INVARIANTS

### Sovereignty
```yaml
INV-HUMAN-FRAMES: "Human frames. Machine computes. Human promotes."
INV-SOVEREIGN-VETO: "G can halt any task via BROADCAST"
INV-OLYA-ABSOLUTE: "Olya's NO on methodology is absolute"
INV-CAPITAL-GATE: "No live execution without human T2 approval"
```

### Bridge
```yaml
INV-BRIDGE-PROMOTION-GATE: "Economy 2→1 only via validated SKILL beads"
INV-DEXTER-ALWAYS-CLAIM: "All Dexter output enters Phoenix as CLAIM, never FACT"
```

### River
```yaml
INV-RIVER-BITEMPORAL: "Every bar carries world_time + knowledge_time"
INV-RIVER-IMMUTABLE: "Raw parquet files are write-once, never modified"
INV-RIVER-CONTINUOUS: "No gaps in materialized 1m series (ghosts flagged)"
INV-RIVER-SOURCE-TAG: "Every bar carries source provenance forever"
INV-RIVER-IBKR-PRIMACY: "Execution venue = data authority for live"
INV-RIVER-FRESHNESS: "market_state_builder refuses stale data"
```

### Data Integrity
```yaml
INV-BEAD-IMMUTABLE: "Append-only. No mutation."
INV-BEAD-SIGNED: "Dual PQC+ECDSA on every structural bead"
INV-BEAD-TEMPORAL: "Every bead has KT. OBSERVATION requires WT."
INV-SHADOW-RICH: "PROPOSAL_REJECTED = full PROPOSAL + rejection context"
INV-TEMPORAL-BOUNDING: "DERIVED WT = intersection of OBSERVATION inputs only"
INV-COMMITMENT-THRESHOLD: "Only Formal Handoffs become beads"
INV-NO-ORPHAN-INSIGHTS: "All rejections captured, routed to Dream Cycle"
INV-REJECTION-POLICY-REF: "RISK_BREACH must reference active POLICY version"
INV-ANCESTRAL-PRESERVED: "789 Genesis beads (curated from 1178 extractions) = Genesis Snapshot, G-signed"
INV-SOVEREIGN-ANCHOR: "Daily ledger root signed offline HSM"
```

### Halt (S55 Constitutional Hardening)
```yaml
INV-HALT-SIGNAL-CHECK: "Execution gate checks HALT.signal before every capital action"
INV-HALT-CLEAR-LOGGED: "Every HALT clear event logged with timestamp and operator"
INV-HALT-FAIL-CLOSED: "Corrupted/unreadable HALT.signal = HALTED, not bypassed"
INV-HALT-ENTROPY-PROOF: "Halt mechanism survives 5 chaos vectors without silent fail"
INV-OLYA-HALT-AUTHORITY: "Olya can trigger halt_cascade at any time without G approval"
INV-HALT-HUMAN-ONLY-RESTART: "No agent/daemon/cron can clear HALT. G manual action only."
INV-CONFIG-VALID-ON-BOOT: "Boot-time config validation fails loud on missing critical config"
```

### Operational
```yaml
INV-HALT-1: "halt_local < 50ms"
INV-HALT-2: "halt_cascade < 500ms"
INV-HALT-OVERRIDES-LEASE: "Halt wins. Always."
INV-NO-SESSION-OVERLAP: "One lease per session"
INV-LEASE-CEILING: "Lease = ceiling, Cartridge = floor"
INV-STATE-LOCK: "State transitions hash-check prior state"
INV-PERISH-BY-DEFAULT: "No auto-renew. Ceremony or expire."
INV-NO-CORE-REWRITES-POST-S44: "Foundation validated."
```

### Quality
```yaml
INV-EXECUTION-FIDELITY: "Intent vs fill delta tracked. >50bps = alert."
INV-REFINERY-LATENCY-TRACKED: "WT-KT delta first-class. Near-zero = anomaly."
INV-NO-GRADES: "PASS/FAIL boolean only."
INV-ATTR-CAUSAL-BAN: "No causal attribution without controlled experiment"
INV-CLAIM-FACT-SEPARATION: "Binary. No gray."
```

### Security
```yaml
INV-NO-SECRETS-IN-REPO: "Git hooks block credentials"
INV-DEPLOYMENT-AUDIT: "Audit deployment config, not just code"
INV-RUNAWAY-CAP: "Hard-capped loops. Cost ceiling."
INV-CHECKPOINT-BEFORE-DEATH: "70% checkpoint, 90% forced"
```

---

## 6. DECISION LOG

```yaml
# Phoenix Core (S28-S48)
DEC-S35: "Causal ban on attribution (INV-ATTR-CAUSAL-BAN)"
DEC-S36: "Boolean gates only, no confidence (INV-HARNESS-1)"
DEC-S37: "Binary CLAIM/FACT, no PROVISIONAL (INV-CLAIM-FACT-SEPARATION)"
DEC-S38: "Exhaustive grid, no ranking (INV-HUNT-EXHAUSTIVE)"
DEC-S40: "Self-healing, not self-modifying (SLEEP_SAFE)"
DEC-S42: "Convergence ≠ correctness (fidelity > consensus)"
DEC-S46: "Cartridge = WHAT, Lease = WHEN/HOW MUCH"
DEC-S47: "PERISH_BY_DEFAULT + STATE_LOCK hash protection"

# Bead Field & Analytical
DEC-TEMPORAL-BOUNDING: "DERIVED WT = intersection of OBSERVATION spans"
DEC-MERKLE-HYBRID: "Decision Boundary + 500 bead / 1hr fallback"
DEC-GENESIS-SNAPSHOT: "789 CLAIMs (corrected from 981 — see DRIFT_LOG DELTA-1) = single Merkle root = Bead Zero"
DEC-FORMAL-HANDOFF: "commit() is bright line"
DEC-PQC-FOUNDATIONAL: "Software-first signing. TEE additional."

# System
DEC-TWO-ECONOMIES: "Governance and analytical beads = separate systems + one-way bridge"
DEC-PROJECTION: "Phoenix projects into Bead Field. Not vice versa."
DEC-RIVER-INTERNAL: "River stays Phoenix-internal. Event bus is swarm-level."
DEC-RIVER-DUAL-SOURCE: "Dukascopy (history) + IBKR (recent + live). Seam attested by G."
DEC-RIVER-PARQUET-DUCKDB: "Immutable parquet (daily partition) + DuckDB query layer."
DEC-RIVER-GHOST-HYBRID: "Raw = FLAG_ONLY. Materialized = ghost bars (is_ghost=True). Gates = SKIP."
DEC-RIVER-BITEMPORAL: "Every bar has WT + KT. Prevents temporal hallucination in backtesting."
DEC-COE: "Olya validates (recognition), not extracts (recall)"
DEC-PHYSICS-EXPERIMENT: "Bead Field = physics experiment, not log"

# S62 Bridge + Gate 2
DEC-BRIDGE-PULL-NOTARY: "Bridge is pull-based notary (reader polls JSONL, not push-based)"
DEC-FREEZE-INDEX-CARVEOUT: "Read-performance indices allowed under DEC-SUBSTRATE-FREEZE (2026-02-28)"
DEC-TIMESTAMP-CANON: "Single canonical form YYYY-MM-DDTHH:MM:SS+00:00 for all query layer timestamps"
DEC-FIELDQUERY-ONLY: "Parallel fan-out is the only supported cross-pair query path (no ATTACH)"
DEC-CHAIN-BACKWARD-ONLY: "Forward chain traversal intentionally not supported (append-only invariant)"
```

---

## 7. OFFICES

```yaml
G_SOVEREIGN: { human: G, authority: SUPREME, hardware: Mac Mini }
CORE_OFFICE: { leader: Phoenix CTO, sprint: SEALED (v0.1), hardware: M4 Max }
CSO_OFFICE: { leader: CSO + Olya, function: methodology validation, hardware: Mac Mini }
DEXTER_OFFICE: { leader: Dexter CTO, function: R&D refinery, hardware: M3 Ultra + DGX }
ADVISORS: { grok: chaos, owl: structure, gpt: lint, perplexity: research }
```

---

## 8. CANONICAL DOCUMENTS

```yaml
STRATEGIC: [a8ra_MASTER_PLAN.md, BRAND_IDENTITY.md]
TECHNICAL: [BEAD_FIELD_SPEC_v0.3.md, CARTRIDGE_AND_LEASE_DESIGN_v1.1.md, MISSION_CONTROL_DESIGN_v0.2.md]
GOVERNANCE: [INVARIANT_REGISTRY.yaml, ACCEPTANCE_CHECKLIST_v0.1.md, SEAL_v0.1.md, ESCALATION_LADDER.md]
OPERATIONAL: [SYSTEM_MANIFEST.md, SPRINT_ROADMAP.md, PHOENIX_MANIFEST.md]
PHOENIX: [conditions.yaml, methodology_template.yaml, schemas/beads.yaml, governance/lease.py, governance/cartridge.py]
COORDINATION: [phoenix-swarm/AGENTS.md, TASK_QUEUE.yaml, BROADCAST.md]
BUILT: [BRIDGE_SPEC_v0.2.md (Dexter), governance_log.py (Phoenix)]
PLANNED: [REFINERY_CONTRACT.yaml, PULSE_OPERATIONS.md]
```

---

## 9. DELTA LOG

```yaml
- date: 2026-02-20
  office: CTO_SYNTHESIS
  change: "v1.0. All gaps filled. Two-economy model. 2 new invariants. Full decision log."

- date: 2026-02-22
  office: CTO_SYNTHESIS
  change: "v1.1. Phoenix v0.1 SEALED. Bead Field Gate 1 PASS. DGX arrived. Metrics updated. Cabinet model v1.1. Doc refs corrected."

- date: 2026-02-22
  office: OPUS_CURSOR
  change: |
    v1.3. River Phase 1 COMPLETE. Full river architecture section (4.1.1).
    6 INV-RIVER-* invariants. 4 River decisions. 11.8M bars ingested.
    Three-way seam validation (Dukascopy × NEX-IBKR × T0-IBKR).
    Seam attestation signed by G. ICT_DATA_CONTRACT amended.
    Tests: 1665 pass, 25 xfailed, zero regressions.

- date: 2026-02-23
  office: OPUS_CURSOR
  change: |
    v1.4. S52 HARDENING. Post-forensic-audit hardening sprint.
    T1: Dual FSM killed — execution/position.py deprecated, canonical at execution/positions/.
    T2: GovernanceSentinel — passive bounds, dead-man's switch, <2ms proven.
    T3: Freshness defense — stale data refused, CSE provenance mandatory (3 fields).
    T4: Doc honesty — DRIFT_LOG (12 deltas), INVARIANT_REGISTRY (28 entries), genesis 981→789.
    55 new tests. 4 new invariants. All CTO addenda applied.
    New modules: governance/sentinel.py, execution/positions/paper.py.

- date: 2026-02-24
  office: OPUS_CURSOR
  change: |
    v1.5. S53.1 ORACLE_REMEDIATION. Blind oracle audit → 4 trivial fixes.
    assert→raise on INV-HALT-1. 7 S53 invariants registered (30→37).
    Manifest version 1.3→1.5. DEC-GENESIS-SNAPSHOT 981→789 corrected.

- date: 2026-02-25
  office: OPUS_CURSOR
  change: |
    v1.6. S54 TRUTH_SWEEP + RIVER_PATCH + MYPY_CAPITAL_PATH.
    T1: Execution surface contract → 10-state canonical FSM (was stale 5-state S28.C).
    T2: MOCK_5DRAWER added to CSE schema (enum drift fixed).
    T3: Registry expansion — 203 INV-* stubs registered (37→240).
    RIVER_PATCH: reqRealTimeBars→reqHistoricalData(keepUpToDate=True). IB error callback.
      Watchdog + resubscribe (max 3, exponential backoff). Atomic JSON heartbeat.
    T4: mypy --strict on governance/execution/cso/ → 0 errors (was 209, 37 files).
    Sprints: 23→26. Invariants: 167→240. ZERO TIER_1. ZERO TIER_2.

- date: 2026-02-25
  office: OPUS_CURSOR
  change: |
    v1.7. S55-S58 HARDENING BLOCK (forensic audit remediation).
    S55 HALT_WIRE: Constitutional kill switch operational. halt.sh + check_halt_signal()
      + clear_halt.sh. Fail-closed on 5 error cases. Wired into insertion.py Step 7.
      5 chaos vectors. 19 new tests. 4 new invariants.
    S56 LOUD_FAILS: 14 exception hits classified. kill_manager silent-pass → loud error.
      Swarm scripts hardened (dep checks, lock pattern, staleness flags).
      Config boot validation (INV-CONFIG-VALID-ON-BOOT). 10 new tests.
    BOOT_GATE: 5-step cold boot validation PASS (G confirmed Step E manually).
    S57 ORACLE_BOOTSTRAP: Three-Surface Cockpit (CLAUDE.md rewrite, Phase 1 honest
      labeling, 3 example scripts, BROADCAST updated).
    S58 HYGIENE: BEAD_FIELD_SPRINT contradictions fixed (DELTA-16). dexter src/
      missing documented (DELTA-17). CONSTITUTION pointer updated.
    Sprints: 26→30. Tests: 1786→1815+. Invariants: 240→245. Chaos: 264→269.

- date: 2026-02-25
  office: OPUS_CURSOR
  change: |
    v1.9. S59 LEASE_WIRE + S60 CEREMONY_AND_HYGIENE.
    S59: Sovereign gate (single chokepoint for all capital mutations). DurableBeadEmitter
      (write-ahead governance, fsync, idempotent). Projection honesty (manifest_writer fails
      closed, never GREEN/ABSENT on exception). CSO scalar decapitation (quality_score/confidence
      → ReadinessReason enum, CI lint). Ceremony stub (next_review_due blocks capital).
      Economy isolation CI guard.
    S60: Ceremony engine (schedule, attest, advance, bounds-monotonic, evidence hash).
      CSO rejection durability (JSONL persistence for bridge prep). Legacy deprecation
      guards (cfp/bead_adapter warning, hunt synthetic metadata). Registry/doc hygiene
      (leases README state diagram fixed, CAPITAL_PATH_COVERAGE.md created).
    Tests: 51 (S59) + 21 (S60) = 72 new. Invariants: 15 (S59) + 4 (S60) = 19 new.
    Sprints: 30→32. Total invariants: 264. ZERO regressions.

- date: 2026-02-28
  office: OPUS_CURSOR
  change: |
    v2.0. S62 BRIDGE_BUILD + GATE_2 — both tracks COMPLETE.
    Track A (Bridge): Pull-based notary. Phoenix governance_log.py emitter (2ed5821).
      Dexter bridge/ — 7 modules (types, verification, state_store, reader, envelope,
      orchestrator, governance_mapper). 191 tests. 7/7 invariants proven.
      Full pipeline: emit → read → verify → seal → project → FACT bead.
    Track B (Gate 2 Query Layer): 6 modules (timestamps, chain, verify, temporal,
      field_query, __init__). 44 tests. Chain walk 10K in 21ms (was ~2h without index).
      Timestamp normalization. Merkle verification. Cross-pair parallel fan-out.
    Synthetic field: 11,387,568 beads, 6 pairs, 5 years, 66GB — VALIDATED.
    Observation: DEXTER_PHASE_1_OBSERVATION_REPORT.md (evidence-based design).
    Dexter head: 7099707 (tag: s62-gate2-query-layer). Dexter tests: 455. Zero regressions.
    Decisions: DEC-FREEZE-INDEX-CARVEOUT, DEC-TIMESTAMP-CANON, DEC-FIELDQUERY-ONLY,
      DEC-CHAIN-BACKWARD-ONLY, DEC-BRIDGE-PULL-NOTARY.
    Sprints: 32→33. Next: S63 AIR pending sequencing decision.

- date: 2026-03-01
  office: CTO_SYNTHESIS
  change: |
    S63 reframed: AIR → FIELD_ACTIVATION. M3 Ultra smoke tested (332/332 PASS).
    Advisor poll: GPT+OWL+BOAR unanimous on field-first sequencing.
    Sprint numbering shift: S63=FIELD_ACTIVATION, S64=AIR(was S63),
    S65=SWARM(was S64), S66+=DREAM_CYCLE(was S65+). Gate numbers unchanged.

- date: 2026-03-01
  office: OPUS_CURSOR
  change: |
    v2.1. Section 3 NODE_M3: INCOMING → SMOKE_TESTED.
    Section 4.1 Phoenix body: S58→S62, metrics aligned to SPRINT_ROADMAP v4.0.
    sprints 30→33, tests 1815→1887+, chaos 269→273, invariants 245→267.

- date: 2026-03-01
  office: OPUS_CURSOR
  change: |
    T5 Proto-AIR Header v0.2 committed to canon.
    Attestation envelope schema: 5 groups, 6 invariants,
    8 anomaly classes. Bridge-aligned. Schema only, no runtime.

- date: 2026-03-03
  office: OPUS_CURSOR
  change: |
    T1 M3 migration COMPLETE. 69GB synthetic field (6 DBs, 11.4M beads)
    transferred and integrity verified. 455/455 tests PASS @ 2.30s.
    SSH mesh M3↔M4 established. NODE_M3 status: FIELD_DEPLOYED.

- date: 2026-03-03
  office: CTO_SYNTHESIS
  change: |
    S63 FIELD_ACTIVATION COMPLETE. M3 field-deployed (69GB, 455/455 PASS).
    11 observations documented. Spitfire audit: 14 findings (0 CRITICAL).
    CLAIM_PIPELINE_SPEC v0.1 Joist-hardened. Proto-AIR v0.2 header.
    5 local models validated, 1 disqualified. Olya method updated to v0.4.

- date: 2026-03-19
  office: CTO_SYNTHESIS
  change: |
    v2.2. S64 METHODOLOGY CALIBRATION COMPLETE. 2-week detour from original
    CLAIM pipeline scope. Gates 1-3 MET. Gate 4 (producer rewrite) is next.
    v0.4 DEPRECATED → SYNTHETIC_OLYA_METHOD_vLOCK.yaml canonical.
    13 L1 primitives locked with pseudocode + empirical provenance.
    STATE_DETECTION_LOGIC_v2.yaml added (HTF phase classifier, v2.4).
    Native multi-TF detection rule established (all bar-pattern primitives).
    VI removed entirely. IFVG + BPR added as derived primitives.
    MSS/BOS unified with direction tag (REVERSAL | CONTINUATION).
    Reference implementation: detect.py (test oracle for core producers).
    14 Olya-annotated ground truth trades captured (Sep 2025 – Mar 2026).
    Autoresearch harness: evaluate.py + sweep.py (27,328-combination sweep).
    Research Accelerator platform operational (~/research_accelerator).
    Walk-forward stability PASS (25 weeks, CV 0.08-0.28 on LTF).

- date: 2026-03-20
  office: OPUS_CURSOR
  change: |
    v2.2 cont. Canon update for S64 post-calibration state.
    SPRINT_ROADMAP v5.0: S64 6-gate structure, S65 revised scope.
    SYSTEM_STATE_200326.md: 5-node cluster topology from CLUSTER_MANIFEST v1.1.
    UNIFIED_ROADMAP v3.0: S64/S65/methodology/hardware sections updated.
    v0.4 and v0.6 methodology files deprecated (4 files across 2 repos).
    vLOCK + STATE_DETECTION_LOGIC_v2 copied to phoenix-swarm/calibration_bible/.
    Hardware: 5-node Tailscale mesh (MacBook cockpit, M3 COO, M4 Phoenix,
    DGX dexter inference, DGX playground sandbox). MCP health layer operational.
    COO orchestration model on M3 (QMD + Superpowers + Ralph Loop).
    Sprints: 35 (S28-S44, S46-S60, S62-S63, S64 in progress).
    Tests: 1887+ Phoenix, 493 Dexter. Methodology: vLOCK (13/13 locked).

- date: 2026-03-20
  office: OPUS_FACTORY
  change: |
    v2.3. S64 COMPLETE — all 6 gates sealed.
    Gate 4: 11 vLOCK producers built (FVG, SWING, DISPLACEMENT, MSS, ORDER_BLOCK,
      IFVG, BPR, SESSION_BOUNDARY, ASIA_RANGE, PDH_PDL, LIQUIDITY_SWEEP). VI retired.
      158 new tests. Oracle comparison PASS on all leaf primitives.
    Gate 5: v0.4 vs vLOCK diff report — FVG 5m 337→236 (native TF), VI 4886→0 (retired),
      6 new primitives operational.
    Gate 6: 14/14 Olya-annotated trades verified. 12/13 MSS chain steps reproduced.
      0 unexpected misses. Known items: sweep pool incomplete, OTE not standalone producer.
    Dexter tests: 493→651. Sprints: 35→36. S65 begins (STRATEGY_ASSEMBLY).

  DELTA-22 (2026-03-21): S65 COMPLETE — STRATEGY_ASSEMBLY sealed.
    Five-factor checklist (F1-F5, two-pass evaluator, 18 tests).
    DIAGNOSTIC_SIGNAL bead builder (shadow_mode=true, rate limiter max 3 per 4H).
    HTF displacement critical fix: close_location formula inverted + DECISIVE_OVERRIDE
    path missing. Post-fix: 1H displacement 0→13 (detect.py=9), state classifier
    reaches EXPANSION on real data. 8-36 DIAGNOSTIC_SIGNALs per trade week.
    OTE producer, composite chains (REVERSAL/CONTINUATION routing), level lifecycle,
    7 spatial predicates, MSS dedup, FVG FILLED terminal state.
    Pipeline: daily_detection_export.py (River→producers→state→checklist→signals).
    3 Phoenix cartridge YAMLs updated (vLOCK primitives, gate names).
    Gate B3C: 4/8 addressable trades produce signal (state classifier bottleneck).
    Dexter tests: 651→869. Sprints: 36→37.
    S66 FLAGS: state classifier intraday evolution, signal direction filtering,
    PROPOSED HTF params need Olya visual confirmation, sweep level pool incomplete.
    Dexter commit: be2a06e.

  DELTA-23 (2026-03-22): S66 COMPLETE — STATE_FLAGS + DREAM_CYCLE_V1 + CHANNELS.
    Track A: Time-indexed WorldState snapshots (classify_at_time, 1H/4H boundaries).
    Direction guard in signal_builder. RANGE permission NEUTRAL→BOTH.
    Two-phase kill zone gate (confluence in session, entry in session+30min grace).
    peak_window quality tag. Regression 4/8→6/8 addressable.
    vLOCK amendment: kill_zone_gate_v2 (Olya confirmed).
    Track C: Dream Cycle v1 — analyzer (signal outcomes, skip classification,
    state review), morning briefing (JSON + Markdown), nightly runner.
    5 FALSE_REJECTIONS found across 4 days (first tuning targets).
    Track D: Channels — @a8ra_COO_bot on M3 (Telegram round-trip).
    MIRROR: live observation surface for Olya (localhost:8300).
    DEPLOYMENT_ROADMAP.md v1.1: canonical build plan for paper trading
    (Phase 0-3, 9 new invariants, ~5-8 days to first paper trade).
    Dexter tests: 869→1088. Commits: f01ee8b + b7bef38. Sprints: 37→38.
    Forward sprint planning defers to DEPLOYMENT_ROADMAP.md.

- date: 2026-03-26
  office: CTO_SESSION + OPUS_FACTORY
  change: |
    S67 COMPLETE — CANONICAL_PIPELINE_AND_VERIFICATION.

    PIPELINE:
    - Export bug fixed: FVG/OB silently dropped due to reasoning_trace key mismatch
      (bar_time vs detect_time/ob_time). 2-line fix in daily_detection_export.py.
    - claim_writer.py BUILT: 265 lines, 34 tests. End-state module.
      ClaimSpec → signed CLAIM beads (PQC+ECDSA, bi-temporal, chain-linked).
    - Pipeline dual-write: JSON + beads from same producer run.
    - eurusd_claims.db created: SEPARATE DB for analytical CLAIMs.
    - 5-year historical backfill: 564,471 beads (563,187 CLAIM + 1,284 SIGNAL).
      Jan 2021 → Mar 2026. One unbroken chain. Zero anomalies.
    - Bead field: analytically void → analytically rich.

    MIRROR:
    - Architectural audit: complete state machine X-ray (state inventory,
      conflict map, 11 issues found including 3 P0 crashes).
    - Root cause: 4 competing date mechanisms, sequential/real timestamp mismatch.
    - Phase A surgical fixes: 6 fixes (HTF scroll, sequential timestamps,
      feed navigation, mode switch reset, timezone docs, WS subscribe).
    - Phase B setView() refactor: unified state management architecture.
    - MIRROR now reliable real-time observation surface.

    VERIFICATION (Mar 26):
    - 7-angle bead field integrity verification (advisor-enriched).
    - Angle 7 (raw bar ground truth): 899/900 correct against River candles.
    - Angle 4 (vLOCK compliance): 5/5 core rules, zero violations across 564K beads.
    - Angle 3 (statistical consistency): zero anomalies across 63 months.
    - Angle 5 (temporal integrity): 5/5 bi-temporal tests perfect.
    - Named findings: SWEEP_PRODUCER_NEAR_NONFUNCTIONAL (70/5yr),
      WARMUP_BEADS (9,457 in unreliable window), SIGNAL_CHAIN_EMPTY.
    - Permanent verification suite: 7 scripts at ~/dexter/scripts/verification/
    - BEAD_FIELD_CALIBRATION_REPORT.md produced.

    Dexter tests: 1088 + 34 claim_writer = 1122.
    New modules: claim_writer.py, 7 verification scripts.
    New DB: eurusd_claims.db (4.4GB, 564K beads).
    Sprints: 38→39.

- date: 2026-03-26
  office: OPUS_FACTORY (M3 Ultra)
  change: |
    S68 COMPLETE — SWEEP_POOL_EXPANSION.

    ROOT CAUSE: POOL_STARVATION (confirmed by S67 forensic).
    Dexter LiquiditySweepProducer had 2 level sources (~8 levels/day).
    RA oracle has 7+ sources (~20-28 levels/day). Detection logic was
    correct — only the pool feeding it needed expansion.

    NEW PRODUCERS:
    - htf_liquidity.py (172 lines): HTFLiquidityProducer — EQH/EQL pools
      from H1/H4 fractal swing detection (left=2, right=2) with 5 gates
      (tolerance, min_bars_between, rotation, invalidation, asia filter).
    - utils/htf_pool_builder.py (218 lines): fractal detection + pool
      clustering + merge. Faithful port of ra.detectors.htf_liquidity.
    - utils/level_pool.py (162 lines): pool assembly, dedup by
      (source,side,price±0.1pip), merge by (side,forex_day) within 1.0pip.
      Priority ranking: HTF > PDH/PDL > Session > Swing > Sweep Event.
    - pwh_pwl.py (121 lines): PWHPWLProducer — previous forex week H/L.

    POOL EXPANSION (2 → 6 sources):
    - SESSION_BOUNDARY (existing), PDH_PDL (existing)
    - HTF_EQH/EQL (NEW — H1/H4 structural pools, UNTOUCHED only)
    - PROMOTED_SWING (NEW — vivid-grade, strength>=10, height>=10pip, current day)
    - PWH/PWL (NEW — previous forex week high/low)
    - Displacement (NEW wiring — qualified_sweep check)

    LEVEL LIFECYCLE PORTED:
    - Dedup by (source, side, price within 0.1pip)
    - Merge by (side, forex_day) within 1.0pip tolerance
    - Forex day partitioning (different days never merge)

    PIPELINE WIRING:
    - daily_detection_export.py: HTF_LIQ + PWH_PWL + swing + displacement
      wired into sweep producer. Session + PDH now in all_claims (persisted).

    VALIDATION (5 annotated trade dates):
    - Oct 1: 0→40, Dec 12: 0→45, Feb 4: 0→41, Nov 12: 0→49, Sep 29: 0→40
    - HTF pools: 13-20 per day. Detection logic untouched.

    ARCHITECTURE: All new files ≤300 lines. vLOCK parameters preserved.
    DEFERRED: P5 sweep event recursion (depth 2).
    Tests: 32 new, 207 producer total, zero regressions.
    Sprints: 39→40.

# ─── MANIFEST DELTA: S69 FAITHFUL_SWEEP_PORT (2026-03-26) ───
#
# WHAT: Faithful port of oracle's full 1,416-line liquidity_sweep.py into Dexter.
#   4-phase pipeline: pool construction → detection → dwell lifecycle → post-processing.
#   All 8 calibration engineer flags implemented (two-pass dwell, multi-bar synthetic
#   wick, sweep-would-fire preflight, displacement override, probe exhaustion, etc.).
#
# NEW FILES:
#   sweep_pool_builder.py (233 lines) — Phase 1: dedup, merge, level assembly
#   sweep_detector.py (378 lines) — Phase 2: detection loop (single function, >300 lines accepted)
#   sweep_lifecycle.py (218 lines) — Phase 3-4: dwell consumption + qualification
#   liquidity_sweep.py rewritten (310 lines) — 4-phase orchestrator
#
# DISPLACEMENT QUALIFIES: Added _build_qualifies_grid() to displacement producer.
#   4x4 threshold matrix (ATR x body ratio) with and/or/override gates.
#   Enables dwell displacement override and sweep qualification tagging.
#
# SESSION ALIGNMENT: tf_aggregator.get_session() aligned with RA session_tagger
#   (6 labels: asia, pre_london, lokz, pre_ny, nyokz, other).
#
# VALIDATION:
#   Angle 7 geometric: 15/15 PASS (100%) — every sweep is real
#   Oracle match: 44% (divergence is LTF_BOX level pricing, not detection logic)
#   Tests: 222 passed, 0 failed, zero regressions
#
# BACKFILL: 5-year EURUSD (2021-01 to 2026-03) INITIATED on M3.
#   Post-backfill: Angle 1 + Angle 4 + Angle 7 verification battery.
#
# FORWARD: Resume DEPLOYMENT_ROADMAP Phase 0-2 toward paper trading.
#   Sweep pipeline is the last primitive that needed alignment.
#   All 11 vLOCK producers now operational with faithful detection logic.
#
# Sprints: 40→41.

# --- APPEND BELOW ---
```

---

*One manifest. All offices. No drift.*
