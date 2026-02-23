# a8ra FORENSIC ARCHITECTURAL AUDIT

```yaml
auditor: Opus (Claude claude-4.6-opus-max-thinking)
date: 2026-02-23
scope: phoenix + phoenix-swarm + dexter (post-S51, post-v0.1 SEAL)
source: Machine-generated oracle prompt (RepoPrompt + Codex 5.3)
confidence: HIGH for codemap-visible modules, MEDIUM for compressed/one-line modules
```

---

## 1. SYSTEM TOPOLOGY MAP

### 1.1 Phoenix (Constitutional Trading Engine)

| Module | Purpose | Status | Deps | Reverse Deps |
|--------|---------|--------|------|---------------|
| `governance/halt.py` | Halt signal, cascade, mesh | ACTIVE | threading | execution, lease, daemons |
| `governance/lease.py` | Lease state machine, interpreter, manager | ACTIVE | halt, lease_types | insertion, execution |
| `governance/lease_types.py` | Pydantic models for lease/cartridge/bead types | ACTIVE | pydantic | lease, cartridge, insertion |
| `governance/cartridge.py` | Cartridge loader, registry, linter | ACTIVE | lease_types, yaml | insertion |
| `governance/insertion.py` | 8-step insertion protocol | ACTIVE | cartridge, lease | - |
| `governance/interface.py` | GovernanceInterface ABC | ACTIVE | halt, telemetry, tokens, types | cso/observer, cso/contract |
| `governance/t2/` | T2 approval workflow (tokens, evidence, approval) | ACTIVE | halt, memory/bead_store | execution |
| `governance/health_fsm.py` | Health state machine (HEALTHY→DEGRADED→CRITICAL→HALTED) | ACTIVE | - | monitoring |
| `governance/circuit_breaker.py` | Circuit breaker pattern | ACTIVE | - | brokers |
| `governance/backoff.py` | Exponential backoff + retry | ACTIVE | - | brokers |
| `governance/runtime_assertions.py` | Scalar ban, provenance, ranking, grade enforcement | ACTIVE | - | cfp, hunt, validation |
| `governance/slm_boundary.py` | SLM output boundary checks | ACTIVE | runtime_assertions | - |
| `governance/stale_gate.py` | State freshness enforcement | ACTIVE | - | t2/approval |
| `governance/telemetry.py` | Quality telemetry emitter + aggregator | ACTIVE | types | interface |
| `governance/tokens.py` | ApprovalToken, TokenIssuer, TokenValidator | ACTIVE | halt, errors | interface, t2 |
| `execution/intent.py` | Immutable ExecutionIntent + IntentFactory | ACTIVE | - | broker_stub, halt_gate |
| `execution/halt_gate.py` | Pre-action halt enforcement | ACTIVE | - | broker_stub |
| `execution/position.py` | Position FSM (5 states), PositionRegistry | ACTIVE | - | broker_stub, replay |
| `execution/positions/` | Refactored position lifecycle (separate states, tracker) | ACTIVE | - | reconciliation, execution __init__ |
| `execution/asia_scalp.py` | S51 Asia Range Scalp evaluation engine | ACTIVE | - | tests/test_s51_driveshaft |
| `execution/broker_stub.py` | Paper broker with halt checking | ACTIVE | intent, position | replay |
| `execution/replay.py` | Deterministic replay harness | ACTIVE | broker_stub, intent, position | tests |
| `execution/promotion/` | Promotion ceremony + checklist | ACTIVE | - | - |
| `execution/reconciliation/` | Drift detection vs broker state | ACTIVE | positions, brokers/ibkr | - |
| `river/schema.py` | RAW_BAR_SCHEMA, validation, hashing, get_river_root | ACTIVE | pyarrow, pandas | writer, reader, streamer, seam, nex_ingestor |
| `river/writer.py` | IBKR → daily parquet (RiverWriter) | ACTIVE | schema, ib_insync | - |
| `river/reader.py` | DuckDB query layer + ghost injection (RiverReader) | ACTIVE | schema, duckdb | cso/market_state_builder |
| `river/streamer.py` | Live 1m bars → staging → daily consolidation | ACTIVE | schema, ib_insync | - |
| `river/seam.py` | Cross-source reconciliation (Dukascopy × IBKR) | ACTIVE | schema, duckdb | - |
| `river/nex_ingestor.py` | NEX CSV → River parquet migration | ACTIVE | schema | - |
| `river/synthetic_river.py` | Deterministic synthetic data for testing | ACTIVE | - | tests |
| `cso/evaluator.py` | GateEvaluator: 5-drawer gate evaluation | ACTIVE | drawer, yaml | market_state_builder |
| `cso/market_state_builder.py` | Enrichment→MarketState adapter (S51) | ACTIVE | evaluator, numpy, pandas | tests/test_s51_driveshaft |
| `cso/drawer.py` | Drawer schema validation + rule evaluation | ACTIVE | yaml | evaluator |
| `cso/bit_vector.py` | Gate vector generation, popcount ban | ACTIVE | yaml | - |
| `cso/scanner.py` | Multi-pair CSO scanning | ACTIVE | strategy_core, structure_detector, params_loader | consumer |
| `cso/consumer.py` | CSE validation + routing | ACTIVE | daemons/routing | - |
| `cso/observer.py` | CSO observer (GovernanceInterface) | ACTIVE | governance/interface, beads | - |
| `cso/contract.py` | 4Q gate evaluation contract | ACTIVE | governance/interface | - |
| `cso/strategy_core.py` | Setup scoring, evidence building | ACTIVE | structure_detector | scanner |
| `cso/structure_detector.py` | FVG, BOS, CHoCH, OTE, Liquidity Sweep detection | ACTIVE | pandas | strategy_core, observer |
| `cso/alerts.py` | Alert rules, linting, rate limiting | ACTIVE | - | - |
| `cso/multi_pair.py` | Multi-pair scan with randomized sort + budget | ACTIVE | - | - |
| `cso/beads.py` | CSO bead types (immutable, factory) | ACTIVE | - | observer |
| `enrichment/layers/l1_time_sessions.py` | Session tagging, kill zones, trading day | ACTIVE | pandas, zoneinfo | L2+ |
| `enrichment/layers/l2_reference_levels.py` | Asia range, PDH/PDL, weekly levels | ACTIVE | numpy, pandas | L3+ |
| `enrichment/layers/l3_sweeps.py` | Sweep detection, extension classification | ACTIVE | numpy, pandas | L4+ |
| `enrichment/layers/l4_structure_breaks.py` | Swing detection, BOS/CHoCH identification | ACTIVE | numpy, pandas | L5+ |
| `enrichment/layers/l5_order_blocks.py` | Order block detection | ACTIVE | numpy, pandas | L6+ |
| `enrichment/layers/l6_fvg_imbalances.py` | FVG detection, ATR, fill tracking | ACTIVE | numpy, pandas | L7 |
| `enrichment/layers/l7_asia_scalp.py` | Asia scalp primitives (S51) | ACTIVE | numpy, pandas | market_state_builder |
| `monitoring/` | Heartbeat, semantic health, HUD, kill manager | ACTIVE | - | - |
| `brokers/ibkr/` | IBKR connector, real_client, mock_client, etc. | ACTIVE | ib_insync | execution |
| `daemons/` | Watcher, lens, routing (file seam spine) | ACTIVE | - | cso/consumer |
| `CONSTITUTION/` | Constitutional YAML structure | **SKELETON** | - | - |

**FINDING-1**: `CONSTITUTION/` directory is status "skeleton" per `CONSTITUTION_MANIFEST.yaml:377`. Modules, seams, scenarios, environment, dependencies, state directories all contain only README placeholders with "Files (to be created)". Only 6 invariant YAMLs and 3 role YAMLs are populated. The wiring directory has 1 file (halt_propagation). For a system claiming 159+ invariants, the formal CONSTITUTION directory captures <5% of them.

### 1.2 Dexter (Bead Field)

| Module | Purpose | Status |
|--------|---------|--------|
| `bead_field/schema/` | 8 typed bead schemas (Pydantic) + enums | ACTIVE |
| `bead_field/store/bitemporal.py` | SQLite bi-temporal store | ACTIVE |
| `bead_field/store/queries.py` | WT/KT range queries, lineage, refinery latency | ACTIVE |
| `bead_field/store/migrations.py` | Version-tracked schema migrations | ACTIVE |
| `bead_field/integrity/hashing.py` | SHA-256 canonical JSON hashing | ACTIVE |
| `bead_field/integrity/chain.py` | Per-stream hash chain + tamper detection | ACTIVE |
| `bead_field/integrity/merkle.py` | Merkle tree + hybrid batch anchoring | ACTIVE |
| `bead_field/integrity/signing.py` | Dual PQC (ML-DSA-65) + ECDSA signing | ACTIVE |
| `bead_field/clock/hlc.py` | Hybrid Logical Clock | ACTIVE |
| `bead_field/ingestion/pipeline.py` | Raw → validated → signed → stored | ACTIVE |
| `bead_field/genesis/curator.py` | 1178 → 789 claim curation | ACTIVE |
| `bead_field/genesis/snapshot.py` | Genesis Merkle tree + signing ceremony | ACTIVE |
| `bead_field/genesis/delta.py` | Methodology delta bead builder | ACTIVE |

### 1.3 Phoenix-Swarm

| Component | Purpose | Status |
|-----------|---------|--------|
| `TASK_QUEUE.yaml` | Shared kanban (pending/claimed/done/blocked) | ACTIVE (empty) |
| `BROADCAST.md` | G sovereign directives | ACTIVE |
| `AGENTS.md` | Office identities and contracts | ACTIVE |
| `heartbeats/` | Per-office status (4 files exist) | ACTIVE |
| `checkpoints/` | Structured state snapshots | ACTIVE (empty) |
| `claiming/` | Atomic task claim locks | ACTIVE (empty) |
| `scripts/` | Launch, monitoring, hooks | ACTIVE |
| `launchd/` | macOS daemon configs (8 plists) | ACTIVE |

**FINDING-2**: TASK_QUEUE.yaml at `phoenix-swarm/TASK_QUEUE.yaml:10000-10034` is completely empty — all queues (pending, claimed, done, blocked) are `[]`. The multi-office coordination layer has infrastructure but zero operational evidence of task flow.

---

## 2. CROSS-REPO WIRING DIAGRAM

| Integration Point | Status | Evidence |
|-------------------|--------|----------|
| River → Enrichment L1-L7 → MarketState → Evaluator | **BUILT** | `cso/market_state_builder.py:57` `build_market_state()` takes enriched DataFrame |
| CSO Evaluator → FiveDrawerResult → BitVector | **BUILT** | `cso/evaluator.py:180`, `cso/bit_vector.py:160` |
| Execution Intent → HaltGate → Broker | **BUILT** | `execution/halt_gate.py:89`, `execution/broker_stub.py:175` |
| Cartridge → Insertion → Lease activation | **BUILT** | `governance/insertion.py:181-295`, `governance/lease.py:164` |
| Lease bounds → Halt trigger | **BUILT** | `governance/lease.py:396-468` `LeaseInterpreter.enforce_bounds()` |
| Phoenix governance → Bead Field FACT projection | **DESIGNED, NOT BUILT** | SYSTEM_MANIFEST claims "pattern: Projection, not participation". No bridge code exists in either repo. |
| Dexter evidence → Oracle review → Phoenix gates | **DESIGNED, NOT BUILT** | AGENTS.md defines the flow. TASK_QUEUE empty. No integration code. |
| CSO Scanner → T2 Approval workflow | **PARTIALLY BUILT** | Scanner at `cso/scanner.py:268` emits CSE. Consumer at `cso/consumer.py:333` routes via daemons. T2Workflow at `governance/t2/approval.py:164` exists. The stitching between consumer and T2 is through `daemons/routing.py` (compressed, limited visibility). |
| Reconciler → IBKR broker state | **BUILT** | `execution/reconciliation/reconciler.py:55` takes `IBKRConnector` |
| Phoenix-Swarm heartbeat → Office status | **BUILT** | `phoenix-swarm/heartbeats/` has 4 YAML files, `scripts/status.sh` exists |
| Dream Cycle → Shadow Field mining | **DESIGNED, NOT BUILT** | BEAD_FIELD_SPEC Section 8 defines full intake/output. Gate 5+ scope. |
| AIR (Agent Integrity Runtime) | **DESIGNED, NOT BUILT** | BEAD_FIELD_SPEC Section 7 defines full gate protocol. No code exists. |
| Sovereign Anchor (daily HSM signing) | **DESIGNED, NOT BUILT** | BEAD_FIELD_SPEC Section 5.2 defines daily HSM anchor. No HSM code exists. |

**FINDING-3**: The two-economy bridge (Phoenix governance → Bead Field analytical) is the most critical DESIGNED-but-NOT-BUILT integration. Until this exists, Phoenix and Dexter are architecturally isolated. The system is two separate systems that share a vision document.

---

## 3. INVARIANT AUDIT

### 3.1 Sovereignty Invariants

| Invariant | Status | Test Evidence |
|-----------|--------|---------------|
| INV-SOVEREIGN-1 (human sovereignty absolute) | ENFORCED | `governance/tokens.py:87` TokenValidator checks halt before state hash. T2 gate in `governance/t2/approval.py:275` |
| INV-SOVEREIGN-2 (T2 requires human gate) | ENFORCED | `tests/test_halt_blocks_t2_action.py:32-120` — 4 tests proving halt blocks T2 |
| INV-CAPITAL-GATE | ENFORCED | `execution/halt_gate.py:89` `check_before()` required. `tests/test_halt_before_exec.py:21` — action without check raises |

### 3.2 Halt Invariants

| Invariant | Status | Test Evidence |
|-----------|--------|---------------|
| INV-HALT-1 (<50ms local) | **PROVEN** | `CONSTITUTION/invariants/INV-HALT-1.yaml` — proven at 0.003ms. `tests/test_lease/test_halt_override.py:157` — 10 iterations parametrized |
| INV-HALT-2 (<500ms cascade) | **PROVEN** | `CONSTITUTION/invariants/INV-HALT-2.yaml` — proven at 22.59ms. `tests/test_halt_propagation.py:106` — cascade latency SLO |
| INV-HALT-OVERRIDES-LEASE | **PROVEN** | `tests/test_lease/test_halt_override.py:93-155` — halt succeeds on active, bypasses state lock, from any active state |
| INV-GOV-HALT-BEFORE-ACTION | **PROVEN** | `tests/test_halt_before_exec.py:21-77` — 5 tests. `tests/test_halt_blocks_t2_action.py:32-120` — 4 tests |

### 3.3 Data Integrity Invariants

| Invariant | Status | Test Evidence |
|-----------|--------|---------------|
| INV-BEAD-IMMUTABLE | **PROVEN** (Dexter) | `dexter/bead_field/tests/test_invariants.py:72-107` — content + KT tamper detection via SQLite triggers |
| INV-BEAD-SIGNED | **PROVEN** (Dexter) | `dexter/bead_field/tests/test_invariants.py:169-227` — tampered hash fails sig, wrong keys fail |
| INV-BEAD-TEMPORAL | ENFORCED | `dexter/bead_field/schema/core.py:60` `validate_temporal_class()` — Pydantic model_validator |
| INV-CONTRACT-1 (deterministic) | **PROVEN** | `tests/test_execution_path.py:175-219` — 3 tests for deterministic replay |
| INV-RIVER-IMMUTABLE | ENFORCED | River writes daily parquet (write-once). No update path in `river/writer.py`. |
| INV-RIVER-BITEMPORAL | ENFORCED | `river/schema.py:32` `RAW_BAR_SCHEMA` includes `knowledge_time` column |

### 3.4 Operational Invariants

| Invariant | Status | Test Evidence |
|-----------|--------|---------------|
| INV-STATE-LOCK | **PROVEN** | `tests/test_lease/test_state_machine.py:263-316` — valid/invalid hash checks on transitions |
| INV-EXEC-LIFECYCLE-1 | **PROVEN** | `tests/test_execution_path.py:384-448` — 7 lifecycle tests |
| INV-PERISH-BY-DEFAULT | ENFORCED | `governance/lease_types.py` — `RenewalType` enum has only `PERISH` value |
| INV-NO-GRADES / INV-SCALAR-BAN | **PROVEN** | `tests/test_cso/test_evaluator.py:501-551` — TestNoAggregation: no count, no score, no confidence, no grade |

### 3.5 UNTESTED_INVARIANT Flags

| Invariant | Gap |
|-----------|-----|
| INV-SOVEREIGN-ANCHOR | No HSM integration code. No test. **UNTESTED_INVARIANT** |
| INV-EXECUTION-FIDELITY (>50bps alert) | No test asserting intent vs fill delta tracking. **UNTESTED_INVARIANT** |
| INV-BRIDGE-PROMOTION-GATE | Bridge NOT BUILT. Untestable. **UNTESTED_INVARIANT** |
| INV-NO-ORPHAN-INSIGHTS | No test proving all rejections are captured + routed. **UNTESTED_INVARIANT** |
| INV-COMMITMENT-THRESHOLD | Conceptual (Bead Field spec only). No enforcement code. **UNTESTED_INVARIANT** |
| INV-CHECKPOINT-BEFORE-DEATH | No test asserting context-window checkpoint behavior. **UNTESTED_INVARIANT** |
| INV-REFINERY-LATENCY-TRACKED | `store/queries.py:155` has `refinery_latency()` function. No dashboard, no alerting, no test for regression detection. **PARTIALLY_IMPLEMENTED** |
| INV-RIVER-FRESHNESS | `market_state_builder.py:107` has `STALENESS_THRESHOLD_MINUTES`. No test asserting stale data is refused. **UNTESTED_INVARIANT** |
| INV-DEPLOYMENT-AUDIT | No test. ChadBoar canary finding not actioned. **UNTESTED_INVARIANT** |

---

## 4. END-TO-END DATA FLOW TRACE

### 4.1 Market Data → River

```
IBKR API (reqHistoricalData / reqRealTimeBars)
  ↓
river/writer.py:91 capture_all() — historical backfill
river/streamer.py:109 start() — live 1m bars
  ↓
river/schema.py:74 validate_raw_bars() — column/type validation
river/schema.py:54 compute_bar_hashes() — SHA-256 per bar
  ↓
Daily parquet partitions: ~/phoenix-river/{pair}/{year}/{mm}/{dd}.parquet
9 columns: timestamp, open, high, low, close, volume, source, knowledge_time, bar_hash
```

### 4.2 River → Enrichment → MarketState

```
river/reader.py:49 get_bars() — DuckDB SQL over parquet glob
  → ghost injection at river/reader.py:235 _inject_ghosts()
  → timeframe aggregation at river/reader.py:288 _aggregate()
  ↓
enrichment/layers/l1_time_sessions.py:52 enrich() → sessions, kill zones, trading day
enrichment/layers/l2_reference_levels.py:51 enrich() → asia range, PDH/PDL
enrichment/layers/l3_sweeps.py:94 enrich() → sweep detection
enrichment/layers/l4_structure_breaks.py:69 enrich() → BOS/CHoCH
enrichment/layers/l5_order_blocks.py:128 enrich() → OB detection
enrichment/layers/l6_fvg_imbalances.py:133 enrich() → FVG/ATR
enrichment/layers/l7_asia_scalp.py:33 enrich() → RE_ACCEPTANCE, sweep extension, FVG validation
  ↓
cso/market_state_builder.py:57 build_market_state()
  → point-in-time filter (no lookahead)
  → frozen MarketState dataclass
  → MarketStateBuildReport (provenance tracking)
```

### 4.3 MarketState → Gate Evaluation → Signal

```
cso/evaluator.py:180 GateEvaluator.evaluate()
  → loads conditions from cso/knowledge/conditions.yaml
  → evaluates each gate against MarketState fields
  → produces FiveDrawerResult (gates_passed, gates_failed, drawer_status)
  ↓
cso/scanner.py:171 scan_pair() → SetupResult
cso/scanner.py:268 _emit_cse() → CSESignal
```

### 4.4 Signal → T2 → Execution

```
cso/consumer.py:333 CSOConsumer.consume()
  → CSEValidator.validate() at cso/consumer.py:120
  → EvidenceResolver.resolve() at cso/consumer.py:252
  → ApprovalHandler.submit_for_approval() [Protocol interface]
  ↓
governance/t2/approval.py:164 T2Workflow.create_request()
governance/t2/approval.py:203 assemble_evidence()
governance/t2/approval.py:294 approve() → issues Token
  ↓
execution/halt_gate.py:89 HaltGate.check_before("submit_order")
execution/broker_stub.py:175 submit_order() or brokers/ibkr/real_client.py
  ↓
execution/position.py:268 transition_to() (state machine)
  or
execution/positions/lifecycle.py:176 transition() (refactored state machine)
```

**FINDING-4**: Two position state machines coexist. `execution/position.py` defines a 5-state FSM (PENDING, OPEN, PARTIAL, CLOSED, HALTED) at line 91+. `execution/positions/states.py` defines a separate `PositionState` enum at line 53+. `execution/__init__.py` imports from `execution.positions` (the new one). `execution/broker_stub.py:194` imports from `execution.position` (the old one). Both are live code. The docs claim "9-state position lifecycle" — this likely refers to `execution/positions/states.py` which has states including SUBMITTED, FILLED, STALLED, etc. The old `execution/position.py` is unreferenced by the new positions package but is still imported by broker_stub and replay.

---

## 5. BEAD FIELD REALITY CHECK

### 5.1 Schema Implementation vs Spec

| Spec Claim | Code Reality |
|------------|-------------|
| 8 analytical bead types | **BUILT**: FACT, CLAIM, SIGNAL, PROPOSAL, PROPOSAL_REJECTED, SKILL, MODEL_VERSION, POLICY — all as Pydantic models in `dexter/bead_field/schema/` |
| Bi-temporal (WT span + KT point) | **BUILT**: `BeadCore` at `schema/core.py:60` has `world_time_valid_from`, `world_time_valid_to`, `knowledge_time_recorded_at` with `validate_temporal_class()` |
| Three temporal classes (OBSERVATION, PATTERN, DERIVED) | **BUILT**: `schema/enums.py` — `TemporalClass` enum |
| Dual PQC + ECDSA signing | **BUILT**: `integrity/signing.py:5224-5226` imports real `pqcrypto.sign.ml_dsa_65`. ML-DSA-65 (Dilithium3) + ECDSA secp256r1. **This is real PQC, not a stub.** Note: `PQC_STUB` global var exists at line 5263 — suggests fallback path. |
| Per-stream hash chain | **BUILT**: `integrity/chain.py:21-61` — `verify_chain()` walks hash_prev links, `append_to_chain()` links beads |
| Merkle tree with hybrid triggers | **BUILT**: `integrity/merkle.py:114-179` — `BatchAnchor` with `AnchorConfig(max_beads=500, max_time_seconds=3600)` matches spec exactly |
| SHA-256 canonical JSON hashing | **BUILT**: `integrity/hashing.py:19-35` — canonical_json() with EXCLUDED_FROM_HASH fields |
| HLC (Hybrid Logical Clock) | **BUILT**: `clock/hlc.py:24-55` — tick(), merge(), last() |
| Ingestion pipeline | **BUILT**: `ingestion/pipeline.py:75-141` — validates schema, signs, chains, anchors, stores |
| Genesis snapshot (789 beads) | **BUILT**: `genesis/snapshot.py:73-124` — builds genesis beads, `genesis/curator.py:122` curates from raw extractions |
| PROPOSAL_REJECTED = full PROPOSAL + rejection context (INV-SHADOW-RICH) | **BUILT**: `schema/proposal_rejected.py:44` has model_validator enforcing `rejection_policy_ref` for RISK_BREACH |

### 5.2 Spec Claims NOT Built

| Spec Claim | Reality |
|------------|---------|
| XTDB-style bitemporal engine | SQLite with manual bi-temporal queries (`store/bitemporal.py:39`). Acceptable for Gate 1 but spec should be updated. |
| Dolt Work-Tree for coordination | **NOT BUILT**. No Dolt anywhere in codebase. Phoenix-swarm uses git. |
| AIR (Agent Integrity Runtime) | **NOT BUILT**. Spec Section 7 defines full 5-step gate protocol. Zero code. |
| Dream Cycle intake/output | **NOT BUILT**. Acknowledged as Gate 5+ scope. |
| Sovereign Anchor (daily HSM) | **NOT BUILT**. No HSM integration. No offline signing ceremony. |
| Refinery Latency dashboard | **PARTIALLY BUILT**. Query function exists at `store/queries.py:155`. No dashboard, no alerting. |
| CLAIM → FACT promotion pipeline | **NOT BUILT**. Dexter produces CLAIMs. No code path promotes them to FACTs through Olya ceremony. |

### 5.3 Genesis Count Discrepancy

BEAD_FIELD_SPEC v0.3 Section 6.1 header reads "THE_981_CLAIMS" (oracle line ~7754). SYSTEM_MANIFEST v1.3 says "789 (curated from 1178 extractions)". MASTER_PLAN v0.2 delta log confirms "Genesis count corrected: 981→789 (post-curation)". The spec predates curation and was not updated. **DRIFT_RISK: The canonical data constitution references the wrong bead count.**

---

## 6. GOVERNANCE STACK DEEP READ

### 6.1 Cartridge → Lease Lifecycle

**Cartridge loading**: `governance/cartridge.py:110` `CartridgeLoader.load_from_file()` → YAML parse → Pydantic `CartridgeManifest` validation → `compute_hash()` at line 176 (SHA-256 of normalized manifest).

**Insertion protocol**: `governance/insertion.py:181-295` implements a multi-step protocol:
- Step 1-2: Schema validation + Pydantic
- Step 3-4: Linter scan (forbidden patterns)
- Step 5: Cabinet validation (5 drawers present)
- Step 6-7: Registry slot + hash verification
- Step 8: Lease creation via `create_lease_from_cartridge()` at `governance/lease.py:633`

**Lease state machine**: `governance/lease.py:104-368` — `LeaseStateMachine` with transitions:
- DRAFT → ACTIVE (activate with hash check)
- ACTIVE → EXPIRED (with stats)
- ACTIVE → REVOKED (by human, with hash check)
- ACTIVE → HALTED (bounds breach, **bypasses hash check** — line 311)
- `VALID_TRANSITIONS` at line 2323 and `TERMINAL_STATES` at line 2324

**State lock**: Every transition except HALT verifies `expected_hash` against `lease.compute_state_hash()`. HALT bypasses this — proven at `tests/test_lease/test_halt_override.py:110`.

**Bead emission**: All transitions emit typed beads (`LeaseActivationBead`, `LeaseExpiryBead`, `LeaseRevocationBead`, `LeaseHaltBead`, `StateLockBead`). Emission verified in `tests/test_lease/test_state_machine.py:336-427`.

### 6.2 T2 Human Gate

`governance/t2/approval.py:140-401` — `T2Workflow`:
- `create_request()` builds `ApprovalRequest`
- `assemble_evidence()` builds `EvidenceBundle` (setup, alignment, risk, state, safety)
- `check_approvalable()` returns blockers (kill flags, stale state, unresolved drift)
- `approve()` issues token via `TokenStore`
- `validate_for_execution()` checks token validity before order

**Token lifecycle**: `governance/t2/tokens.py:161-340` — `TokenStore` with TTL, max-per-intent limits, bead emission on token events.

### 6.3 Halt Cascade

`governance/halt.py:46-309`:
- `HaltSignal.set()` — threading.Event, ~0.003ms (no IO, no logging)
- `HaltManager.propagate_halt()` — parallel fan-out to registered dependents
- `HaltMesh` — singleton, registers all managers, `global_halt()` propagates to all
- Retry: `_call_with_retry()` at line 190 — max 2 retries, 10ms backoff per hop

### 6.4 Bounds Enforcement

`governance/lease.py:396-468` — `LeaseInterpreter`:
- `check_all_bounds()` — checks drawdown, consecutive losses, daily loss
- `enforce_bounds()` — any breach triggers `state_machine.halt()`
- `is_pair_allowed()`, `is_session_allowed()` — whitelist enforcement
- `check_position_size()` — cap enforcement

**FINDING-5**: `LeaseInterpreter.check_all_bounds()` at line 396 takes `current_drawdown_pct`, `consecutive_losses`, and optional `daily_loss_pct`. These values must be provided by the caller — there is no automatic sourcing from broker/position state. The integration that feeds live metrics into bounds checking is not visible in the codemap.

---

## 7. TEST INFRASTRUCTURE ASSESSMENT

### 7.1 Test Profile

| Category | Scope | Evidence |
|----------|-------|----------|
| Unit tests | Comprehensive across governance, execution, CSO, enrichment | 1690+ tests claimed, breadth visible in codemap |
| Chaos tests | 264 vectors across S30-S39, S47 | `tests/chaos/` — 15+ chaos test files |
| Integration tests | 5 E2E flows | `tests/integration/` — autopsy, cso_shadow, full_flywheel, signalman_kill, telegram |
| Chain tests | Cross-module integration | `tests/chain/` — 5 chain test files |
| S51 Driveshaft | Asia scalp E2E | `tests/test_s51_driveshaft/` — 4 files, 30+ test methods |
| Lease/governance | State machine, halt, bounds | `tests/test_lease/` — 6 files, comprehensive |
| Bead field integrity | Tamper detection, signing, store | `dexter/bead_field/tests/test_invariants.py` — 7 test classes, compound corruption |
| Validation suite | Backtest, Monte Carlo, walk-forward, sensitivity | `tests/test_validation/` — 7 files |

### 7.2 Test Strengths

- **Halt path**: Extensively tested across 6+ test files, including multi-process cascade, race conditions (concurrent halt), halt-during-revoke
- **Lease state machine**: Comprehensive — valid transitions, invalid transitions, state lock, bead emission, transition map completeness
- **Bead integrity**: 7-class tamper detection (content, KT, chain, merkle, signing, LLM-removal, compound corruption)
- **Scalar ban**: Actively tested — no scores, no grades, no confidence, no rankings in evaluator output
- **Determinism**: Proven via replay harness (`DeterminismVerifier` at `execution/replay.py:540`)

### 7.3 Critical Under-Tested Paths

| Gap | Risk |
|-----|------|
| **Scanner → T2 → Order E2E**: No visible integration test proving a CSO signal flows through T2 approval to broker order submission | The claimed E2E path through `tests/integration/test_e2e_full_flywheel.py` exists but its internals are compressed. The Scanner→Consumer→T2Workflow stitching has no dedicated test. |
| **River staleness enforcement**: `market_state_builder.py:107` has `STALENESS_THRESHOLD_MINUTES` but no test asserting stale data is actually refused | Silent stale data could reach gate evaluation |
| **Bounds auto-feed**: No test proving live position metrics (drawdown, consecutive losses) automatically flow into `LeaseInterpreter.check_all_bounds()` | Bounds checking may require manual invocation |
| **Real IBKR order path**: `brokers/ibkr/real_client.py` exists but test coverage is in `tests/test_ibkr/` (degradation, heartbeat, supervisor) — no visible test for actual order submission/fill | Paper mode validated, live order path untested in test suite |
| **CONSTITUTION/ validation**: `scripts/validate_constitution.py` referenced in CONSTITUTION README does not appear in the file tree | Constitutional validation is aspirational |

---

## 8. DOCUMENTATION VS REALITY DELTA (FULL FIDELITY)

### DELTA-1: Genesis Bead Count (DRIFT)
- **Doc claim**: BEAD_FIELD_SPEC v0.3 Section 6.1: "THE_981_CLAIMS"
- **Code reality**: `genesis/curator.py:122` curates to 789. SYSTEM_MANIFEST and MASTER_PLAN correctly state 789.
- **Impact**: Spec is stale. Anyone reading the data constitution gets the wrong count.
- **Severity**: LOW (number, not architecture)

### DELTA-2: XTDB → SQLite (DRIFT)
- **Doc claim**: BEAD_FIELD_SPEC Section 1.2: "XTDB-style bitemporal layer"
- **Code reality**: `store/bitemporal.py:39` — plain SQLite with manual bi-temporal queries
- **Impact**: Spec overpromises storage engine. Current implementation is acceptable for Gate 1 scale.
- **Severity**: LOW (implementation choice, not missing capability)

### DELTA-3: Dolt Work-Tree (MISSING)
- **Doc claim**: BEAD_FIELD_SPEC Section 1.2 defines Dolt as WORK_TREE for agent coordination
- **Code reality**: No Dolt dependency, no Dolt code anywhere. Phoenix-swarm uses git.
- **Impact**: Coordination layer design document doesn't match implementation
- **Severity**: LOW (git works, Dolt was aspirational)

### DELTA-4: AIR System (DESIGNED, NOT BUILT)
- **Doc claim**: BEAD_FIELD_SPEC Section 7 defines full 5-step Agent Integrity Runtime
- **Code reality**: Zero AIR code exists. No AIR gate, no AIR verification, no unsigned mutation rejection.
- **Impact**: Every structural bead claim about "authenticated execution environment" is aspirational
- **Severity**: MEDIUM (Gate 3 scope, but docs don't say "planned" — they say "required")

### DELTA-5: Sovereign Anchor / HSM (DESIGNED, NOT BUILT)
- **Doc claim**: BEAD_FIELD_SPEC Section 5.2: "Daily ledger root snapshot signed with offline sovereign key (HSM)"
- **Code reality**: No HSM integration. No daily anchor cron. No offline signing ceremony code.
- **Impact**: The highest-level integrity guarantee (daily root anchoring) has no implementation
- **Severity**: MEDIUM (Gate 7 scope, but referenced as active invariant INV-SOVEREIGN-ANCHOR)

### DELTA-6: Two Position State Machines (DEBT)
- **Doc claim**: SYSTEM_MANIFEST: "9-state position lifecycle"
- **Code reality**: TWO coexisting state machines:
  - `execution/position.py` — 5 states (PENDING, OPEN, PARTIAL, CLOSED, HALTED). Imported by `broker_stub.py`, `replay.py`.
  - `execution/positions/states.py` — separate PositionState enum with additional states (SUBMITTED, FILLED, STALLED, etc.). Imported by `execution/__init__.py`.
- **Impact**: Callers import different state machines from different paths. `broker_stub.py:194` imports from `execution.position`, while `execution/__init__.py:3254` exports from `execution.positions`. A consumer could get the wrong FSM.
- **Severity**: HIGH (execution correctness depends on which state machine is used)

### DELTA-7: CONSTITUTION/ Directory (SKELETON)
- **Doc claim**: CONSTITUTION README and `CONSTITUTION_MANIFEST.yaml` define a comprehensive Constitutional Architecture Graph
- **Code reality**: `CONSTITUTION_MANIFEST.yaml:377` — status: "skeleton", created: 2026-01-25. Modules: "pending" or "skeleton". Only 6 of 159+ invariants have YAML files. No scenarios, no environment, no dependencies, no state definitions.
- **Impact**: The machine-verifiable constitution exists as aspiration, not artifact. The referenced `scripts/validate_constitution.py` and `scripts/blast_radius.py` do not appear in the file tree.
- **Severity**: MEDIUM (code enforces invariants even without YAML; YAML was meant for documentation/audit)

### DELTA-8: river/__init__.py Exports (DEBT)
- **Doc claim**: River is a first-class module with reader, writer, streamer, seam
- **Code reality**: `river/__init__.py:3533-3538` exports ONLY `SyntheticRiver` and `create_synthetic_river`. RiverReader, RiverWriter, RiverStreamer are not exported.
- **Impact**: `from river import RiverReader` fails. All callers must use `from river.reader import RiverReader`. This is inconsistent with other modules (governance/, execution/ export comprehensively).
- **Severity**: LOW (works, just inconsistent)

### DELTA-9: Bridge Spec (PLANNED, NOT BUILT)
- **Doc claim**: SYSTEM_MANIFEST Section 4.1: "integration_with_bead_field: pattern: Projection, not participation"
- **Code reality**: No bridge code. No projection mechanism. No event emission from Phoenix to Bead Field.
- **Impact**: The two economies are completely isolated. No governance events reach the analytical store.
- **Severity**: HIGH (core architectural claim of two-economy model is unimplemented)

### DELTA-10: ChadBoar Canary Findings Not Actioned
- **Doc claim**: SYSTEM_MANIFEST Section 4.3 lists 5 canary findings including "Deployment config must be audited (INV-DEPLOYMENT-AUDIT)" and "Integration tests must cover actual signing API"
- **Code reality**: INV-DEPLOYMENT-AUDIT has no test. No deployment config audit code visible.
- **Impact**: Lessons from real-world validation aren't feeding back into codebase
- **Severity**: LOW (awareness exists, prioritization choice)

### DELTA-11: Test Count Discrepancy
- **Doc claim**: SYSTEM_MANIFEST: "1690+ (1665 confirmed, 25 xfailed)". MASTER_PLAN: "1716 tests"
- **Reality**: Counts differ by 26-51 between documents. Without running `pytest`, exact count is unverifiable from codemap alone.
- **Impact**: Cosmetic, but signals docs are updated at different times
- **Severity**: NEGLIGIBLE

### DELTA-12: CSO Observer Module Status (STALE REFERENCE)
- **Doc claim**: CONSTITUTION_MANIFEST.yaml lists CSO module status as "skeleton"
- **Code reality**: CSO has a comprehensive implementation: observer, contract, evaluator, market_state_builder, drawer, scanner, consumer, alerts, bit_vector, strategy_core, structure_detector, multi_pair
- **Impact**: CONSTITUTION registration is 4+ weeks behind code reality
- **Severity**: LOW (code works, registration is cosmetic)

---

## 9. CODEMAP APPENDIX REFERENCES

### Phoenix Critical Path Codemaps

| Module | Lines | Key Signatures |
|--------|-------|----------------|
| `governance/halt.py` | ~310 | `HaltSignal.set()`, `HaltManager.propagate_halt()`, `HaltMesh.global_halt()` |
| `governance/lease.py` | ~640 | `LeaseStateMachine.activate/expire/revoke/halt()`, `LeaseInterpreter.enforce_bounds()`, `LeaseManager` singleton |
| `governance/lease_types.py` | ~560 | `CartridgeManifest`, `Lease`, `DrawerConfig`, `LeaseBounds`, 12 bead types |
| `governance/cartridge.py` | ~400 | `CartridgeLoader.validate()`, `CartridgeRegistry.slot()`, `CartridgeLinter.lint()` |
| `governance/insertion.py` | ~340 | `InsertionProtocol.insert_manifest()`, `validate_bounds_ceiling()`, `quick_insert()` |
| `governance/interface.py` | ~385 | `GovernanceInterface` ABC with 20+ methods |
| `governance/t2/approval.py` | ~400 | `T2Workflow.create_request/approve/reject/validate_for_execution()` |
| `governance/t2/tokens.py` | ~390 | `TokenStore.issue/validate/consume()`, token TTL, bead emission |
| `governance/runtime_assertions.py` | ~400 | `assert_no_scalar_score()`, `assert_provenance()`, `constitutional_boundary()` |
| `execution/position.py` | ~500 | 5-state FSM, `Position.transition_to()`, `PositionRegistry` |
| `execution/positions/lifecycle.py` | ~340 | `PositionLifecycle.transition()`, refactored `Position` |
| `execution/positions/states.py` | ~190 | 9-state FSM, `VALID_TRANSITIONS`, `is_valid_transition()` |
| `execution/asia_scalp.py` | ~240 | `evaluate_asia_scalp_setup()`, `SessionTracker`, `TradeProposal` |
| `execution/halt_gate.py` | ~230 | `HaltGate.check_before()`, `ExecutionGateCoordinator`, `halt_gated` decorator |
| `execution/broker_stub.py` | ~410 | `PaperBrokerStub.submit_order()`, halt check, PnL calculation |
| `river/reader.py` | ~350 | `RiverReader.get_bars()`, `_inject_ghosts()`, `_aggregate()`, `_verify_hash_sample()` |
| `river/writer.py` | ~310 | `RiverWriter.capture_all()`, IBKR pacing, daily partition writes |
| `river/streamer.py` | ~310 | `RiverStreamer.start/stop()`, bar updates, staleness check, consolidation |
| `river/schema.py` | ~120 | `RAW_BAR_SCHEMA`, `compute_bar_hashes()`, `validate_raw_bars()`, `CANONICAL_PAIRS` |
| `cso/evaluator.py` | ~330 | `GateEvaluator.evaluate()`, `MarketState` dataclass, `FiveDrawerResult` |
| `cso/market_state_builder.py` | ~440 | `build_market_state()`, point-in-time filter, cold start, `MarketStateBuildReport` |
| `cso/drawer.py` | ~400 | `DrawerSchemaValidator`, `evaluate_drawer_rule()`, `GateDefinition`, `DrawerDefinition` |

### Dexter Critical Path Codemaps

| Module | Lines | Key Signatures |
|--------|-------|----------------|
| `bead_field/schema/core.py` | ~95 | `BeadCore`, `SourceRef`, `AttestationEnvelope`, `validate_temporal_class()` |
| `bead_field/store/bitemporal.py` | ~170 | `BeadStore.insert/get/update_status/count()` |
| `bead_field/store/queries.py` | ~170 | `query_by_wt_range()`, `query_by_kt_asof()`, `refinery_latency()` |
| `bead_field/integrity/signing.py` | ~140 | `KeyPair`, `sign_hash()`, `verify_dual()`, real ML-DSA-65 |
| `bead_field/integrity/merkle.py` | ~185 | `MerkleTree`, `BatchAnchor`, `AnchorConfig(500, 3600)` |
| `bead_field/integrity/chain.py` | ~65 | `verify_chain()`, `append_to_chain()` |
| `bead_field/ingestion/pipeline.py` | ~150 | `IngestionPipeline.ingest()` — full validate→sign→chain→anchor→store |
| `bead_field/genesis/snapshot.py` | ~130 | `build_genesis_beads()`, `build_genesis_snapshot()` |

---

## 10. RISK REGISTRY (FULL FIDELITY)

```
RISK-1: Dual Position State Machine
  type: LIVE_RISK
  location: execution/position.py + execution/positions/states.py
  impact: Callers import different FSMs. broker_stub.py uses 5-state,
          execution/__init__.py exports 9-state. A code path could
          transition through states that don't exist in the other FSM,
          causing silent state corruption or uncaught exceptions.
  remediation: Deprecate execution/position.py, migrate broker_stub.py
               and replay.py to execution/positions/. ~100 LOC.
```

```
RISK-2: Two-Economy Bridge Not Built
  type: INTEGRITY_RISK
  location: (missing — no bridge code in either repo)
  impact: Phoenix governance events never reach Bead Field. The core
          architectural promise (governance events project as FACT beads)
          is unimplemented. Until built, Phoenix and Dexter are isolated
          systems that happen to share documentation.
  remediation: Implement PROJECTION_BRIDGE per SYSTEM_MANIFEST design.
               Phoenix emits events, bridge enriches to FACT beads,
               Bead Field ingests. ~300-500 LOC.
```

```
RISK-3: Bounds Enforcement Not Auto-Fed
  type: LIVE_RISK
  location: governance/lease.py:396 LeaseInterpreter.check_all_bounds()
  impact: Method requires caller to provide current_drawdown_pct,
          consecutive_losses, daily_loss_pct. No automatic sourcing
          from broker/position state visible. If the caller doesn't
          invoke this with fresh data, bounds violations go undetected.
          Capital at risk.
  remediation: Wire PositionTracker.get_stats() output into
               LeaseInterpreter.check_all_bounds() in a monitoring
               loop. ~50-100 LOC.
```

```
RISK-4: Sovereign Anchor / HSM Not Implemented
  type: INTEGRITY_RISK
  location: (missing — no HSM code)
  impact: INV-SOVEREIGN-ANCHOR claims daily ledger root signed with
          offline HSM. No implementation exists. The highest-level
          integrity guarantee is vapor. External audit cannot verify
          system state at any past day.
  remediation: Gate 7 scope. Requires HSM hardware + daily cron +
               signing ceremony code. ~200 LOC + hardware procurement.
```

```
RISK-5: CONSTITUTION/ Skeleton (4+ weeks stale)
  type: DRIFT_RISK
  location: CONSTITUTION/CONSTITUTION_MANIFEST.yaml
  impact: System claims 159+ invariants but CONSTITUTION/ directory
          captures <5% as formal YAML. Referenced validation scripts
          (validate_constitution.py, blast_radius.py) don't exist.
          The "machine-verifiable constitution" is human-readable only.
  remediation: Either populate CONSTITUTION/ with actual invariant
               YAMLs (significant effort, ~1000 LOC), or downgrade
               the claim to "code-enforced invariants" and archive
               the skeleton directory. ~50 LOC for archival.
```

```
RISK-6: River __init__.py Missing Exports
  type: DEBT_RISK
  location: river/__init__.py:3533-3538
  impact: Only SyntheticRiver exported. Real River components (Reader,
          Writer, Streamer, Seam) require direct submodule imports.
          Inconsistent with other Phoenix modules. New code could
          accidentally import SyntheticRiver thinking it's the real
          thing.
  remediation: Add real River exports to __init__.py. ~10 LOC.
```

```
RISK-7: INV-RIVER-FRESHNESS Untested
  type: LIVE_RISK
  location: cso/market_state_builder.py:107 STALENESS_THRESHOLD_MINUTES
  impact: market_state_builder has a staleness constant but no test
          proves stale data is actually refused. If the threshold
          check has a bug, stale market data reaches gate evaluation
          and produces signals based on outdated state.
  remediation: Add test: feed data older than threshold, assert
               cold_start path taken. ~30 LOC.
```

```
RISK-8: AIR Not Built (INV-BEAD-SIGNED partially enforced)
  type: INTEGRITY_RISK
  location: (missing — BEAD_FIELD_SPEC Section 7)
  impact: Bead signing exists in Dexter (ingestion pipeline signs
          beads). But AIR — the runtime that verifies code hash,
          model version, and rejects unsigned mutations — does not
          exist. A compromised agent could emit beads that are signed
          but with wrong code/model attestation.
  remediation: Gate 3 scope. AIR runtime with code hash verification
               + unsigned rejection. ~500 LOC.
```

```
RISK-9: BEAD_FIELD_SPEC 981→789 Count Not Updated
  type: DRIFT_RISK
  location: BEAD_FIELD_SPEC v0.3 Section 6.1
  impact: Data constitution references wrong genesis count. Any
          implementation reading the spec for genesis validation
          would expect 981 beads, find 789, and potentially flag
          a false integrity violation.
  remediation: Update BEAD_FIELD_SPEC Section 6.1 header and
               temporal class note. ~5 LOC.
```

```
RISK-10: Scanner → T2 Integration Gap
  type: DEBT_RISK
  location: cso/scanner.py → cso/consumer.py → governance/t2/approval.py
  impact: The path from CSO signal emission through to T2 approval
          and order execution traverses scanner → consumer →
          daemons/routing → T2Workflow. No dedicated integration test
          exercises this full chain. The flywheel test may cover it
          (compressed, cannot verify), but targeted test is absent.
  remediation: Write integration test: inject enriched data →
               scanner produces signal → consumer routes → T2
               approves → order submitted. ~100-150 LOC.
```

```
RISK-11: No INV-EXECUTION-FIDELITY Enforcement
  type: LIVE_RISK
  location: (missing — no intent vs fill delta tracking code)
  impact: INV-EXECUTION-FIDELITY claims "PROPOSAL.entry_price vs
          fill delta tracked. Alert on >50bps." No tracking code
          visible. No alert mechanism. Slippage goes undetected.
  remediation: Add fill-vs-intent comparison in position lifecycle
               or reconciler. Emit alert on >50bps. ~50 LOC.
```

```
RISK-12: ChadBoar INV-DEPLOYMENT-AUDIT Unactioned
  type: DEBT_RISK
  location: (missing — no deployment config audit)
  impact: ChadBoar proved deployment config must be audited. No
          test or check exists. A misconfigured deployment (wrong
          API keys, wrong port, wrong env) could silently connect
          to live instead of paper.
  remediation: Add deployment config validation at startup.
               Check env vars, connection targets, mode flags.
               ~50-100 LOC.
```

---

*End of forensic audit. 10 sections. 12 risks. Every material claim cited to path:line where codemap permits. Confidence limits noted where compression reduces visibility.*
