# SYSTEM_STATE_200326.md
# a8ra — Current System State
# What exists, where it lives, what the rules are.

```yaml
document: SYSTEM_STATE
version: 2026-03-20
status: CANONICAL — updated post S64 METHODOLOGY CALIBRATION
format: M2M_DENSE
audience: All CTO and Advisor instances
rule: YAML only. No history. No roadmap. No rationale. Current state only.
supersedes: SYSTEM_STATE_280226.md
```

---

## 1. HARDWARE MAP

```yaml
OPERATOR_TERMINAL:
  node: laptop-access
  hardware: MacBook Pro M3 Max 36GB
  os: macOS 15.5
  user: craigmackie
  tailscale_ip: 100.126.129.90
  role: COCKPIT — operator terminal, travels with G, not a server
  access: ET client (connects outward), Ansible local connection
  detail: See CLUSTER_MANIFEST.md §1 TOPOLOGY

NODE_M3_ULTRA:
  node: a8ra-m3
  hardware: Mac Studio M3 Ultra 512GB
  os: macOS 26.3
  user: a8ra_m3
  tailscale_ip: 100.114.164.22
  role: COO STATION — always-on control plane, bead field store, orchestrator
  status: FIELD_DEPLOYED | 455/455 PASS | 69GB synthetic field | SSH mesh operational
  runs: [bead field store, coordination services, COO orchestrator, local models]
  coo: Claude Code 2.1.76 + QMD 2.0.1 + Superpowers 5.0.2 + Ralph Loop 1.0.0
  mcp_server: port 7700 (tools: get_disk_usage, get_memory_usage, list_running_services, get_bead_field_status)
  detail: See CLUSTER_MANIFEST.md §1 KNOWLEDGE_SUBSTRATE

NODE_M4_STUDIO:
  node: m4-studio
  hardware: Mac Studio M4 Max 64GB
  os: macOS 26.3
  user: echopeso
  tailscale_ip: 100.120.83.66
  role: PHOENIX EXECUTION — core dev, sprint execution, test suites
  status: OPERATIONAL
  runs: [development, testing, sprint execution, Opus/Cursor builds]
  mcp_server: port 7700 (tools: get_disk_usage, get_memory_usage, list_running_services, get_git_status)

NODE_DGX_DEXTER:
  node: dexter
  hardware: NVIDIA DGX Spark (Grace-Blackwell GB10) 120GB
  os: Ubuntu 24.04 aarch64
  user: a8ra_dgx
  tailscale_ip: 100.87.225.84
  role: PRODUCTION INFERENCE — Dream Cycle, SkillRL, Monte Carlo (S68+)
  status: OPERATIONAL — Claude Code installed, git configured, GPU verified idle
  gpu: 1x GB10
  storage: 3.6TB root, 2% used
  mcp_server: port 7700 (tools: get_disk_usage, get_memory_usage, list_running_services, get_gpu_status, list_running_models)

NODE_DGX_PLAYGROUND:
  node: playground-dgx
  hardware: NVIDIA DGX Spark (Grace-Blackwell GB10) 120GB
  os: Ubuntu 24.04 aarch64
  user: playground
  tailscale_ip: 100.125.254.45
  role: EXPERIMENTAL SANDBOX — local models, capability mapping, isolated
  status: OPERATIONAL — Qwen3.5-35B-A3B via vLLM on port 8000, FORGE Phase 1.5 bootstrap
  gpu: 1x GB10
  storage: 3.6TB root, 9% used
  isolation: TAILSCALE ACL RESTRICTED — inbound ALLOWED, outbound to cluster BLOCKED
  mcp_server: port 7700 (tools: get_disk_usage, get_memory_usage, list_running_services, get_gpu_status, list_experiment_queue)

CLUSTER_INFRASTRUCTURE:
  mesh: Tailscale (5-node, WireGuard transport)
  transport: Eternal Terminal (ET) — immortal sessions across all nodes
  multiplexer: Zellij — persistent named sessions per node
  iac: Ansible (phoenix-swarm/ansible/ — inventory, snapshot, deploy-mcp playbooks)
  mcp_health: HTTP port 7700 on all 4 server nodes
  mobile_access: Termius Pro (iPhone, 4 hosts, OSC 52 clipboard)
  canonical_reference: phoenix-swarm/CLUSTER_MANIFEST.md (v1.1, 2026-03-19)
```

---

## 2. REPOS

### PHOENIX (Governance Economy)

```yaml
path: ~/phoenix
purpose: Constitutional trading system — governance economy engine
branch: main
head: 3c28211 "S63 EXIT: canon update — field activation complete, roadmap revised"
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
    docs/canon/a8ra_SYSTEM_MANIFEST_v1_0.md: "Cross-system manifest"
    docs/canon/UNIFIED_ROADMAP_v1.md: "Forward-looking gate sequence"
    docs/canon/SPRINT_ROADMAP.md: "Historical sprint record + cumulative metrics"
    docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1_0.md: "Governance architecture spec"
    cso/knowledge/GATE_GLOSSARY.yaml: "48 gates mapped"
    cso/knowledge/conditions.yaml: "Active trading conditions"
    governance/sovereign_gate.py: "Single chokepoint for all capital mutations"
    governance/governance_log.py: "Bridge provenance root — append-only JSONL"
```

### DEXTER (Analytical Economy)

```yaml
path: ~/dexter
purpose: Sovereign evidence refinery — analytical economy engine + bead field
branch: main
head: "(post-Gate 4 — 11 vLOCK producers committed)"
status: |
  Gate 1: PASS (substrate)
  Gate 2: QUERY LAYER BUILT (chain walk, verify, temporal, cross-pair)
  Bridge: OPERATIONAL (notary pipeline, 7/7 invariants)
  S63: FIELD_ACTIVATION COMPLETE (2026-03-03)
  S64: COMPLETE (all 6 gates sealed 2026-03-20)
  S65: NEXT
  Synthetic field: 11.4M FACTs, 0 CLAIMs, 69GB, field-deployed on M3
  Methodology: SYNTHETIC_OLYA_METHOD_vLOCK.yaml (supersedes v0.4, v0.6)
  Analytical state: "11.4M FACTs, 0 CLAIMs — producers operational, S65 will generate CLAIMs on live data"
  Gate 6 Olya confirmed: 2026-03-20 (14/14 trades PASS, 0 unexpected misses)
tests: 651 (332 bead_field + 79 bridge + 44 query + 158 producers)
producers: 11 vLOCK producers (VI retired)
genesis_beads: 789 (788 CLAIMs + 1 METHODOLOGY_DELTA)
genesis_merkle_root: 5c4d63f29f667d0b80348e3dfc87204aea6488d034c70dd6ae354a57036e963c
hardware: M3 Ultra (production — field-deployed) + M4 Max (development)

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
    tools/synthetic/: "Synthetic bead field (11.4M beads, 6 DBs, 66GB)"

  key_files:
    CLAUDE.md: "Dexter CTO orientation"
    bead_field/schema/core.py: "1283 lines — all 8 bead types + enums + validators"
    bead_field/query/__init__.py: "Gate 2 query layer public API"
    bridge/orchestrator.py: "Bridge poll loop — read → verify → seal → project"
```

### RESEARCH_ACCELERATOR (Calibration Proving Ground)

```yaml
path: ~/research_accelerator
purpose: Forensic calibration platform — detection logic proving ground
branch: main
head: 48ca5bd "v2.4: 14/14 phase classification + parameter sweep HOLD_DEFAULTS"
status: OPERATIONAL — all calibration work complete, serves as reference implementation
hardware: M4 Max (primary), accessible from all nodes

key_artifacts:
  SYNTHETIC_OLYA_METHOD_vLOCK.yaml: "Canonical locked methodology (13/13 primitives)"
  research/STATE_DETECTION_LOGIC_v2.yaml: "HTF phase classifier (v2.4)"
  detect.py: "Reference implementation — 13 L1 primitives, all TFs, test oracle for core"
  preprocess_data_v2.py: "Candle data pipeline"
  research/ground_truth/annotated_trades.yaml: "14 Olya-verified trade annotations"
  tools/autoresearch/evaluate.py: "Automated trade evaluation"
  tools/autoresearch/sweep.py: "Staged grid search (27,328 combinations)"
  configs/locked_baseline.yaml: "Locked parameter configuration"

tools:
  calibration: "calibration_bible/site/ (localhost:8787)"
  validation: "site/validate.html (localhost:8200)"
  strategy: "site/strategy.html (localhost:8200)"
  comparison: "site/compare.html (localhost:8200)"

data:
  candles: "site/data/candles/ (29 weeks EURUSD, all TFs)"
  detections: "site/data/detections/ (29 weeks, 116,950 enriched)"
```

### PHOENIX-SWARM (Coordination)

```yaml
path: ~/phoenix-swarm
purpose: Multi-office coordination layer (file-based async messaging) + cluster IaC
branch: main
head: 18f84f5 (post-pull 2026-03-20)
status: OPERATIONAL
hardware: Shared across all nodes (git-based)

codemap:
  dirs:
    ansible/: "Cluster IaC — inventory, snapshot, deploy-mcp playbooks"
    calibration_bible/: "Methodology files (vLOCK canonical, v0.4/v0.6 deprecated)"
    checkpoints/: "Per-office checkpoint files (resume state)"
    claiming/: "Atomic task claim protocol"
    coo/: "COO orchestration (COO.md, plugins, start-coo.sh)"
    heartbeats/: "Per-office heartbeat files"
    mcp/: "MCP server implementations (per-node)"
    results/: "Task result briefs"
    scripts/: "halt.sh, clear_halt.sh, status.sh, launch_office.sh"

  key_files:
    AGENTS.md: "Office identities, contracts, ownership boundaries"
    BROADCAST.md: "Current sovereign broadcast (G writes, all read)"
    CLUSTER_MANIFEST.md: "5-node cluster topology (v1.1, canonical)"
    TASK_QUEUE.yaml: "Inter-office task routing"
    calibration_bible/SYNTHETIC_OLYA_METHOD_vLOCK.yaml: "Locked methodology"
    calibration_bible/STATE_DETECTION_LOGIC_v2.yaml: "HTF phase classifier"
```

### SPITFIRE (Dexter Surface Layer)

```yaml
path: ~/spitfire
purpose: Read-only codebase intelligence + bead field analyst (Dexter character)
branch: main
status: OPERATIONAL
engine: OpenClaw + Codex 5.3 + Opus daily inspection
hardware: VPS (physically isolated from core infrastructure)
access: READ_ONLY OAuth to phoenix, phoenix-swarm, dexter
```

### PHOENIX-RIVER (Market Data)

```yaml
path: ~/phoenix-river
purpose: Immutable parquet market data store (River backdata)
git: NON_GIT (data repository, not code)
status: OPERATIONAL
hardware: M4 Studio (current) → M3 Ultra (production)

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
```

---

## 3. METHODOLOGY STATE

```yaml
methodology_version: vLOCK
supersedes: v0.4 (DEPRECATED), v0.6 (DEPRECATED)
canonical_spec: SYNTHETIC_OLYA_METHOD_vLOCK.yaml
location: ~/research_accelerator/ (source), ~/phoenix-swarm/calibration_bible/ (copy)

primitives_locked: 13
  list: [FVG, IFVG, BPR, SwingPoints, EqualHL, AsiaRange, Displacement,
         MSS, OrderBlock, LiquiditySweep, OTE, ReferenceLevels, NYWindows]

state_detection:
  spec: STATE_DETECTION_LOGIC_v2.yaml (v2.4)
  phases: [EXPANSION, RETRACE, RANGE]
  validation: 14/14 phase classification, 27,328-combination sweep HOLD_DEFAULTS
  daily_direction: 3-mechanism hierarchy (daily swing primary, 4H MSS secondary, 4H sustained tertiary)

detection_rule: Native per-TF (bar-pattern primitives detect on their native timeframe)
  execution_tfs: [5m, 15m]
  direction_tfs: [1H, 4H, Daily, Weekly]

calibration_data: EURUSD 1m, 29 weeks (Sep 2025 – Mar 2026)
ground_truth: 14 Olya-verified annotated trades
reference_impl: detect.py (test oracle for core producers — all 13 primitives, all TFs)
autoresearch: evaluate.py + sweep.py (automated regression + parameter search)
l2_strategy_designer: IN PROGRESS (Opus building — parallel track)

key_decisions:
  DEC-NATIVE-TF: "All bar-pattern primitives detect on native TF arrays"
  DEC-VI-REMOVED: "Volume Imbalance removed entirely (was IBKR workaround noise)"
  DEC-MSS-BOS-UNIFIED: "BOS collapsed into MSS with direction tag (REVERSAL | CONTINUATION)"
  DEC-CONFLUENCE-FIRST: "Pip size is NOT quality gate. Context tags filter."
  DEC-L1-L15-L2: "L2 never rewrites L1. L1.5 is the tuning surface."
```

---

## 4. SPRINT STATUS

```yaml
current_sprint: S64 — COMPLETE (all 6 gates sealed 2026-03-20)
next_sprint: S65 — STRATEGY_ASSEMBLY
gate_status:
  gate_1: MET — Track A+B shipped (493 tests)
  gate_2: MET — Session/reference levels CSO-validated
  gate_3: MET — vLOCK methodology Olya-locked (13/13 primitives, walk-forward PASS)
  gate_4: SEALED — 11 vLOCK producers built, 158 tests, VI retired, oracle comparison PASS
  gate_5: SEALED — v0.4 vs vLOCK diff report delivered
  gate_6: SEALED — 14/14 annotated trades PASS (Olya confirmed 2026-03-20)
s64_exit_gate: ALL_6_GATES_PASS
s64_certification: "METHODOLOGY_vLOCK | 11_PRODUCERS | 158_TESTS | VI_RETIRED | STATE_DETECTION_v2.4 | GATE6_OLYA_CONFIRMED"

next_action: "S65 — River→producer wiring, HTF producers, strategy assembly"
```

---

## 5. DATA FLOWS

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

  dexter_to_oracle_to_phoenix:
    path: "Dexter CLAIM beads → Oracle/Olya review → PROMOTE/REJECT → Phoenix conditions"
    type: HUMAN-GATED (Olya is promotion authority)
    rule: INV-DEXTER-ALWAYS-CLAIM, INV-SEMANTIC-FIREWALL

  swarm_coordination:
    path: "phoenix-swarm/ ← all offices (heartbeats, tasks, results, broadcasts)"
    type: FILE-BASED ASYNC (git-coordinated)

  research_accelerator:
    path: "RA detect.py → enriched detections → core producer rewrite reference"
    type: ONE-WAY REFERENCE (RA is proving ground, core is production)
    rule: "detect.py output = expected result for core producer regression tests"

  spitfire_observation:
    path: "All repos → Spitfire (read-only OAuth)"
    type: READ_ONLY

  coo_orchestration:
    path: "CTO brief → COO (M3) → delegates (M4, DGX) → results → CTO"
    type: HIERARCHICAL (human-initiated, COO routes, delegates execute)
    detail: See CLUSTER_MANIFEST.md §4 COO ORCHESTRATION MODEL
```

---

## 6. WRITE AUTHORITY

```yaml
phoenix:
  writers: [OPUS_CURSOR, CTO_SESSION]
  rule: "INV-NO-CORE-REWRITES-POST-S44 constrains scope of changes"

dexter:
  writers: [OPUS_CURSOR, DEXTER_CTO_SESSION]

phoenix_swarm:
  writers: [ALL_OFFICES (own heartbeat + results only), G (BROADCAST.md)]
  rule: "Single-writer per heartbeat file. G owns BROADCAST."

research_accelerator:
  writers: [CTO_SESSION, OPUS_CURSOR]
  rule: "Reference implementation — modify only via calibration session with Olya"

spitfire:
  writers: [SPITFIRE_SELF]
  read_only_to: [phoenix, dexter, phoenix-swarm]

phoenix_river:
  writers: [RIVER_DAEMON (append-only parquets)]
  rule: "INV-RIVER-IMMUTABLE — write-once, never modified"

oracle:
  writers: [OLYA, CSO_SESSION]
  rule: "Analyst CANNOT modify .py, git commit/push, install packages"
```

---

## 7. ACTIVE CONTRACTS

```yaml
constraints:
  - name: INV-NO-CORE-REWRITES-POST-S44
    scope: phoenix
    rule: "Foundation validated. No architectural rewrites."
    expires: PERMANENT

  - name: DEC-TWO-ECONOMIES
    scope: system-wide
    rule: "Governance beads and analytical beads are separate systems with one-way bridge"
    expires: PERMANENT

  - name: DEC-PROJECTION-NOT-PARTICIPATION
    scope: phoenix ↔ dexter boundary
    rule: "Phoenix projects into Bead Field. Bead Field doesn't modify Phoenix internals."
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

  - name: INV-RIVER-IMMUTABLE
    scope: phoenix-river
    rule: "Raw parquet files are write-once, never modified"
    expires: PERMANENT

  - name: DEC-TIMESTAMP-CANON
    scope: dexter/bead_field/query/
    rule: "Single canonical form YYYY-MM-DDTHH:MM:SS+00:00"
    expires: PERMANENT

  - name: DEC-FIELDQUERY-ONLY
    scope: dexter/bead_field/query/
    rule: "Parallel fan-out is the only supported cross-pair query path"
    expires: PERMANENT
```

---

*What exists. Where it lives. What the rules are. Nothing more.*
