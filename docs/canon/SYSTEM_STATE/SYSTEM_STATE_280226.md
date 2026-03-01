# SYSTEM_STATE_280226.md
# a8ra — Current System State
# What exists, where it lives, what the rules are.

```yaml
document: SYSTEM_STATE
version: 2026-02-28
status: CANONICAL
format: M2M_DENSE
audience: All CTO and Advisor instances
rule: YAML only. No history. No roadmap. No rationale. Current state only.
```

---

## 1. HARDWARE MAP

```yaml
NODE_DGX_SPARK:
  role: Bead Field Compute (Dream Cycle, SkillRL — Gate 5+)
  status: ARRIVED — pending cluster wiring + activation
  specs: Grace-Blackwell GPU
  runs: [future analytical workloads, EnvModel training, counterfactual simulation]
  activation_trigger: Gate 4 operational + Shadow Field volume

NODE_M3_ULTRA:
  role: Phoenix Execution + Library (Knowledge Substrate, Control Plane)
  status: SMOKE_TESTED | Dexter 332/332 PASS @ 0.48s | rack install 2026-03-02
  specs: 32-core CPU, 80-core GPU, 512GB unified RAM
  runs: [phoenix runtime, river live data, bead field store, coordination services]
  note: Production home for Bead Field once deployed

NODE_M4_STUDIO:
  role: Development Environment
  status: OPERATIONAL
  specs: M4 Max, 64GB unified RAM
  runs: [development, testing, sprint execution, Opus/Cursor builds]

NODE_VPS:
  role: Dexter Surface Layer (Spitfire — read-only analyst)
  status: OPERATIONAL
  engine: OpenClaw + Codex 5.3 + Opus daily inspection
  access: READ_ONLY OAuth to all repos
  runs: [forensic architecture review, bead field analysis, pattern mining]

NODE_MAC_MINI:
  role: CSO Office + Gateway
  status: OPERATIONAL
  runs: [oracle workspace, Claude Desktop, Olya sovereign sessions, G sessions]
```

---

## 2. REPOS

### PHOENIX (Governance Economy)

```yaml
path: ~/phoenix
purpose: Constitutional trading system — governance economy engine
branch: main
head: b2c79e2 "S59-S60: Sovereign gate, ceremony engine, write-ahead governance"
status: OPERATIONAL (v0.1 sealed, post-S60 hardened)
tests: 1887+
invariants: 259 registered
chaos_vectors: 273
hardware: M4 Studio (dev) → M3 Ultra (production)

codemap:
  dirs:
    CONSTITUTION/: "The Law — invariants, modules, seams, roles, wiring, tests"
    athena/: "Memory discipline (CLAIM/FACT/CONFLICT)"
    brokers/ibkr/: "IBKR integration (gateway, supervisor, degradation)"
    cartridges/: "Strategy manifests (active/ for deployed cartridges)"
    cfp/: "Conditional facts with provenance"
    cso/: "CSO gate evaluation (5-drawer cabinet, harness, knowledge)"
    config/: "Pydantic centralized config + profiles"
    contracts/: "Data contracts (ICT, governance interface)"
    daemons/: "Background services"
    dispatcher/: "Task dispatch, tmux control, heartbeat"
    enrichment/: "Enrichment layers"
    execution/: "Position lifecycle (9-state FSM), promotion, reconciliation"
    governance/: "Lease system, halt, sentinel, ceremony, sovereign gate, T2 gates"
    hunt/: "Exhaustive grid compute for signal generation"
    leases/: "Governance wrappers (state machine, README)"
    monitoring/: "Operational monitoring"
    narrator/: "Template-based facts projection (no opinions)"
    notification/: "Alert taxonomy, formatters"
    river/: "Market data integration"
    schemas/: "Shared data schemas"
    slm/: "Classification API (rule-based)"
    state/: "Manifest writer, health writer, state files"
    surfaces/hud/: "WarBoar HUD (SwiftUI app)"
    tests/: "All test suites (chaos, integration, per-module)"
    tools/hooks/: "Constitutional enforcement (pre-commit, runtime)"
    validation/: "Decomposed outputs + ScalarBanLinter"
    docs/canon/: "Canonical locked documents"
    docs/operations/: "Runbooks + operator guides"
    docs/archive/: "Historical sprint records"

  key_files:
    CLAUDE.md: "CLI orientation for Claude Code instances"
    INVARIANT_REGISTRY.yaml: "259 registered invariants"
    docs/canon/a8ra_SYSTEM_MANIFEST_v1_0.md: "Cross-system manifest (v1.9)"
    docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1_0.md: "Governance architecture spec"
    cso/knowledge/GATE_GLOSSARY.yaml: "48 gates mapped"
    cso/knowledge/conditions.yaml: "Active trading conditions"
    governance/lease.py: "Lease state machine + interpreter"
    governance/cartridge.py: "Cartridge loader + registry"
    governance/insertion.py: "8-step insertion protocol"
    governance/halt.py: "Constitutional halt mechanism"
    governance/ceremony.py: "Ceremony engine lifecycle"
    governance/sovereign_gate.py: "Single chokepoint for all capital mutations"
    governance/governance_log.py: "Bridge provenance root — append-only JSONL governance event emitter (S62)"
    execution/contracts/execution_surface.yaml: "Execution surface contract"
    state/manifest_writer.py: "health.yaml → manifest.json bridge"
```

### DEXTER (Analytical Economy)

```yaml
path: ~/dexter
purpose: Sovereign evidence refinery — analytical economy engine + bead field
branch: main
head: 7099707 "S62: Gate 2 query layer + Bridge notary" (tag: s62-gate2-query-layer)
status: |
  Gate 1: PASS (substrate frozen)
  Gate 2: QUERY LAYER BUILT (chain walk, verify, temporal, cross-pair)
  Bridge: OPERATIONAL (notary pipeline, 7/7 invariants)
  Synthetic field: 11.4M beads, 66GB, validated
tests: 455 (332 bead_field + 79 bridge + 44 query layer)
genesis_beads: 789 (788 CLAIMs + 1 METHODOLOGY_DELTA)
genesis_merkle_root: 5c4d63f29f667d0b80348e3dfc87204aea6488d034c70dd6ae354a57036e963c
hardware: Mac Mini (current) → M3 Ultra (production target)

codemap:
  dirs:
    bead_field/: "Analytical substrate (Gate 1 — schema, store, integrity, clock, ingestion, genesis)"
    bead_field/schema/: "8 bead types, 15 enums, Pydantic v2 models (core.py)"
    bead_field/store/: "SQLite bi-temporal store with DB-level immutability triggers"
    bead_field/integrity/: "Hash chain, Merkle tree, dual PQC+ECDSA signing"
    bead_field/clock/: "Hybrid Logical Clock (microsecond, thread-safe)"
    bead_field/ingestion/: "Validate → UUID → HLC → hash → sign → store → Merkle trigger"
    bead_field/genesis/: "Genesis ceremony tooling + 789 curated beads"
    bead_field/query/: "Gate 2 query layer (timestamps, chain, verify, temporal, field_query)"
    bead_field/tests/: "332 tests covering Gate 1 + Gate 2 exit criteria"
    bridge/: "Inter-economy notary (types, verification, state_store, reader, envelope, orchestrator)"
    bridge/tests/: "79 bridge tests"
    bead_field/ingestion/governance_mapper.py: "FACT projection from governance events"
    bundles/: "Extraction output bundles"
    core/: "Extraction pipeline (Theorist→Auditor→Bundler)"
    corpus/: "Source material for extraction"
    memory/: "Bead chain (JSONL) + THEORY.md"
    roles/: "Agent role definitions"
    scripts/: "Operational scripts"
    skills/: "Extraction skill definitions"
    tools/synthetic/: "Synthetic bead field (11.4M beads, 6 DBs, 66GB)"
    docs/: "Bead field plans, sprint docs, role contracts"

  key_files:
    CLAUDE.md: "Dexter CTO orientation"
    bead_field/schema/core.py: "1283 lines — all 8 bead types + enums + validators"
    bead_field/store/bitemporal.py: "Bi-temporal SQLite proxy"
    bead_field/integrity/signing.py: "Dual PQC (ML-DSA-65) + ECDSA signing"
    bead_field/integrity/merkle.py: "Binary Merkle tree + inclusion proofs"
    bead_field/clock/hlc.py: "Hybrid Logical Clock"
    bead_field/ingestion/pipeline.py: "Ingestion pipeline orchestrator"
    bead_field/query/__init__.py: "Gate 2 query layer public API"
    bridge/orchestrator.py: "Bridge poll loop — read → verify → seal → project"
    docs/ROLE_CONTRACTS.md: "Agent role contracts"
    docs/beadfields_plan/BRIDGE_SPEC_v0.2.md: "Bridge specification (canonical)"
    docs/beadfields_plan/DREAM_CYCLE_DESIGN_INTENT_v0_1.md: "Gate 5+ design fence"
```

### PHOENIX-SWARM (Coordination)

```yaml
path: ~/phoenix-swarm
purpose: Multi-office coordination layer (file-based async messaging)
branch: main
head: 8a853fe "docs: BROADCAST counts updated + GIT_HYGIENE_REPORT"
status: OPERATIONAL
hardware: Shared across all nodes (git-based)

codemap:
  dirs:
    checkpoints/: "Per-office checkpoint files (resume state)"
    claiming/: "Atomic task claim protocol"
    docs/broadcasts/: "Historical broadcasts"
    forensic_review/: "Forensic review outputs"
    heartbeats/: "Per-office heartbeat files"
    hooks/: "Session hooks (start, end)"
    launchd/: "Launch daemon configs"
    results/briefs/: "Task result briefs"
    scripts/: "halt.sh, clear_halt.sh, status.sh, launch_office.sh, session_end_hook.sh"
    templates/: "Brief and report templates"

  key_files:
    AGENTS.md: "Office identities, contracts, ownership boundaries"
    BROADCAST.md: "Current sovereign broadcast (G writes, all read)"
    TASK_QUEUE.yaml: "Inter-office task routing"
    scripts/halt.sh: "Constitutional halt (writes HALT.signal)"
    scripts/clear_halt.sh: "G-only halt clear"
    scripts/status.sh: "System status check"
    scripts/launch_office.sh: "Office bootstrap with dep checks"
```

### SPITFIRE (Dexter Surface Layer)

```yaml
path: ~/spitfire
purpose: Read-only codebase intelligence + bead field analyst (Dexter character)
branch: main
head: 3da08b4
status: OPERATIONAL
engine: OpenClaw + Codex 5.3 + Opus daily inspection
hardware: VPS (physically isolated from core infrastructure)
access: READ_ONLY OAuth to phoenix, phoenix-swarm, dexter

codemap:
  dirs:
    claude_cto_docs/: "CTO document references"
    prompts/: "Analysis prompt templates"
    reference/: "Reference material"
    schemas/: "Schema definitions for analysis"

  key_files:
    README.md: "Spitfire identity + operational docs"
    ARCHITECTURE.md: "System architecture reference"
    coverage.yaml: "Analysis coverage tracking"
    learning.yaml: "Accumulated findings + patterns"
```

### PHOENIX-RIVER (Market Data)

```yaml
path: ~/phoenix-river
purpose: Immutable parquet market data store (River backdata)
git: NON_GIT (data repository, not code)
status: OPERATIONAL
hardware: M4 Studio (current) → M3 Ultra (production)
heartbeat: STARTED (connected, subscribed, active pair EURUSD)
last_update: 2026-02-27T23:46:11Z

structure:
  pairs: [AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF, USDJPY]
  layout: "{PAIR}/{YEAR}/{MONTH}/*.parquet"
  bars: 11.8M+ (1m resolution)
  rule: INV-RIVER-IMMUTABLE (write-once, never modified)
  sources: Dukascopy (historical) + IBKR (live streaming)
```

### ORACLE (CSO Office)

```yaml
path: ~/oracle
purpose: Olya methodology validation office + CSO cockpit
git: NON_GIT (workspace, not versioned)
status: OPERATIONAL (Phase 1 cockpit)
hardware: Mac Mini
owner: Olya + CSO

codemap:
  dirs:
    .claude/: "Claude session state"
    examples/: "Query examples (first_query.sh, gate_status.sh, dry_run.sh)"
    forensic_report/: "Forensic review outputs"
    memory/: "MEMORY.md + archive.md + patterns.md"
    notes/: "Working documents"

  key_files:
    CLAUDE.md: "Oracle office contract — HALT authority, read-only analyst, workflows"
```

---

## 3. DATA FLOWS

```yaml
flows:
  river_to_phoenix:
    path: "phoenix-river/ parquets → Phoenix river/ module → execution"
    type: READ_ONLY (immutable parquets)
    rule: INV-RIVER-IMMUTABLE, INV-RIVER-BITEMPORAL

  phoenix_to_bridge_to_dexter:
    path: "Phoenix governance_log.py → Bridge reader → verify → seal → FACT bead in Bead Field"
    type: PROJECTION (one-way, Phoenix emits, Bridge reads and enriches)
    status: OPERATIONAL (S62 — pull-based notary, 7 modules, 191 tests, 7/7 invariants)
    rule: DEC-PROJECTION-NOT-PARTICIPATION, DEC-BRIDGE-PULL-NOTARY

  dexter_to_oracle_to_phoenix:
    path: "Dexter CLAIM beads → Oracle/Olya review → PROMOTE/REJECT → Phoenix conditions"
    type: HUMAN-GATED (Olya is promotion authority)
    rule: INV-DEXTER-ALWAYS-CLAIM, INV-SEMANTIC-FIREWALL

  swarm_coordination:
    path: "phoenix-swarm/ ← all offices (heartbeats, tasks, results, broadcasts)"
    type: FILE-BASED ASYNC (git-coordinated)
    rule: "G owns BROADCAST.md. Each office single-writer for its heartbeat."

  spitfire_observation:
    path: "All repos → Spitfire (read-only OAuth)"
    type: READ_ONLY (can observe, cannot modify)
    rule: "All Spitfire output = CLAIM (INV-SEMANTIC-FIREWALL applies)"
```

---

## 4. WRITE AUTHORITY

```yaml
phoenix:
  writers: [OPUS_CURSOR, CTO_SESSION]
  read_only: [SPITFIRE, ORACLE, CSO]
  rule: "INV-NO-CORE-REWRITES-POST-S44 constrains scope of changes"

dexter:
  writers: [OPUS_CURSOR, DEXTER_CTO_SESSION]
  read_only: [SPITFIRE, ORACLE]
  rule: "DEC-SUBSTRATE-FREEZE (expires ~2026-03-24) — bug fixes only on bead_field/"

phoenix_swarm:
  writers: [ALL_OFFICES (own heartbeat + results only), G (BROADCAST.md)]
  rule: "Single-writer per heartbeat file. G owns BROADCAST."

spitfire:
  writers: [SPITFIRE_SELF (own learning.yaml, coverage.yaml)]
  read_only_to: [phoenix, dexter, phoenix-swarm]
  rule: "CANNOT write to any other repo. Physical isolation on VPS."

phoenix_river:
  writers: [RIVER_DAEMON (append-only parquets)]
  read_only: [PHOENIX, SPITFIRE]
  rule: "INV-RIVER-IMMUTABLE — write-once, never modified"

oracle:
  writers: [OLYA, CSO_SESSION]
  read_only: [SPITFIRE]
  rule: "Analyst CANNOT modify .py, git commit/push, install packages, restart daemons"
```

---

## 5. ACTIVE CONTRACTS

```yaml
constraints:
  - name: INV-NO-CORE-REWRITES-POST-S44
    scope: phoenix
    rule: "Foundation validated. No architectural rewrites."
    expires: PERMANENT

  - name: DEC-SUBSTRATE-FREEZE
    scope: dexter/bead_field/
    rule: "No schema changes. Bug fixes only. Read-performance indices allowed (DEC-FREEZE-INDEX-CARVEOUT)."
    expires: ~2026-03-24

  - name: DEC-FREEZE-INDEX-CARVEOUT
    scope: dexter/bead_field/
    rule: "Read-performance indices allowed under DEC-SUBSTRATE-FREEZE"
    expires: ~2026-03-24

  - name: DEC-TIMESTAMP-CANON
    scope: dexter/bead_field/query/
    rule: "Single canonical form YYYY-MM-DDTHH:MM:SS+00:00 for all query layer timestamps"
    expires: PERMANENT

  - name: DEC-FIELDQUERY-ONLY
    scope: dexter/bead_field/query/
    rule: "Parallel fan-out is the only supported cross-pair query path (no ATTACH)"
    expires: PERMANENT

  - name: DEC-CHAIN-BACKWARD-ONLY
    scope: dexter/bead_field/query/
    rule: "Forward chain traversal intentionally not supported (append-only invariant)"
    expires: PERMANENT

  - name: INV-DEXTER-ALWAYS-CLAIM
    scope: dexter → phoenix boundary
    rule: "All Dexter output enters Phoenix as CLAIM, never FACT"
    expires: PERMANENT

  - name: INV-SEMANTIC-FIREWALL
    scope: all external → phoenix boundary
    rule: "All external data enters Economy 1 as CLAIM, never FACT"
    expires: PERMANENT

  - name: INV-HALT-OVERRIDES-LEASE
    scope: phoenix governance
    rule: "Halt wins. Always. <50ms."
    expires: PERMANENT

  - name: INV-OLYA-HALT-AUTHORITY
    scope: system-wide
    rule: "Olya can trigger halt_cascade at any time without G approval"
    expires: PERMANENT

  - name: INV-HALT-HUMAN-ONLY-RESTART
    scope: system-wide
    rule: "No agent/daemon/cron can clear HALT. G manual action only."
    expires: PERMANENT

  - name: DEC-TWO-ECONOMIES
    scope: system-wide
    rule: "Governance beads and analytical beads are separate systems with one-way bridge"
    expires: PERMANENT

  - name: DEC-PROJECTION-NOT-PARTICIPATION
    scope: phoenix ↔ dexter boundary
    rule: "Phoenix projects into Bead Field. Bead Field doesn't modify Phoenix internals."
    expires: PERMANENT

  - name: INV-RIVER-IMMUTABLE
    scope: phoenix-river
    rule: "Raw parquet files are write-once, never modified"
    expires: PERMANENT
```

---

*What exists. Where it lives. What the rules are. Nothing more.*
