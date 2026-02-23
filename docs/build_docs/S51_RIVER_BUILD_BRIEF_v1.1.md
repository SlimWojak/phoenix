# S51 RIVER BUILD BRIEF v1.1 (AMENDED)

```yaml
BRIEF: S51.RIVER.D1
MISSION: RIVER_FOUNDATION
OWNER: OPUS (Cursor)
FORMAT: DENSE
DATE: 2026-02-22
VERSION: 1.1
AMENDED: "Post Opus MAX review — 3 criticals resolved, 5 precision fixes, 6 gaps filled"
AUTHORIZED: CTO + G (Sovereign calls signed, G-items resolved)
```

---

## CHANGELOG FROM v1.0

```yaml
AMENDMENTS:
  C1_OVERLAP: "T2 promoted to day-0 priority. IBKR gateway is LIVE. Start capture immediately."
  C2_PARTITION: "Monthly → Daily. Truly immutable files. phoenix/river/{pair}/{year}/{mm}/{dd}.parquet"
  C3_CONCURRENCY: "Resolved by daily partition. Bright line: one writer per daily file."
  P1_SCHEMA: "Split into RAW_BAR_SCHEMA (9 cols) + MATERIALIZED_BAR_SCHEMA (10 cols, adds is_ghost)"
  P2_PATH: "ICT_DATA_CONTRACT path corrected to phoenix/docs/canon/ICT_DATA_CONTRACT.md"
  P3_PAIRS: "Canonical 6 locked: EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD"
  P4_FILES: "Added existing files to MODIFIED section (river_reader.py, river_adapter.py)"
  P5_NEX_REF: "Added ~/nex/nex_lab/data/vendors/ibkr.py as starting material for T2"
  M1_IBKR: "Added IBKR setup notes (gateway live, port 4002 paper)"
  M2_ROLLBACK: "Added RIVER_SOURCE env flag for legacy fallback"
  M3_HEARTBEAT: "Added streamer heartbeat monitoring"
  M4_DST: "Added DST boundary handling notes to T1/T8"
  M5_DAY_BOUNDARY: "Resolved by daily partition (forex day = 17:00 NY)"
  M6_TESTING: "Added mock strategy guidance"
  DEP_FIX: "T8 now depends on T5 (don't stream into unvalidated river)"
  NEX_DATA: "Dukascopy sourced to 2025-11-23. Dec-Feb gap. Fresh Dukascopy download planned."
```

---

## DOCTRINE (LOCKED — do not revisit)

```yaml
RIVER_DOCTRINE:
  SOURCE: "Dual — Dukascopy (history) + IBKR (recent + live)"
  STORAGE: "Immutable Parquet (daily partition) + DuckDB (query layer)"
  INTEGRITY: "Formal River Integrity Layer — constitutional grade"
  TIMEFRAME: "Store 1m, derive all higher TFs via DuckDB aggregation"
  NEX_DATA: "Formal audit before trust — 7-point checklist"
  IBKR_PRIMACY: "Execution venue = data authority for live trading"
  MULTI_PAIR: "Architecture supports all 6 pairs from day one. Ingest EURUSD first."

  CANONICAL_PAIRS:
    - EURUSD
    - GBPUSD
    - USDJPY
    - USDCHF
    - AUDUSD
    - USDCAD

  NOTE: "NZDUSD in NEX was a test artifact. Not traded. Not canonical."

  SOVEREIGN_SIGNED:
    S1_SEAM_ATTESTATION: "G will sign when overlap validated"
    S2_GHOST_BAR_HYBRID: |
      APPROVED. Raw parquet = gaps remain (no ghost bars).
      Materialized view = ghost bars with is_ghost=True.
      Gates treat ghost bars as SKIP (not PASS/FAIL).
    S3_POLYGON: "DEFERRED to Phase 2"

  NEW_INVARIANTS:
    INV-RIVER-BITEMPORAL: "Every bar carries world_time + knowledge_time"
    INV-RIVER-IMMUTABLE: "Raw parquet files are write-once, never modified"
    INV-RIVER-CONTINUOUS: "No gaps in 1m series during trading hours (ghosts in materialized views)"
    INV-RIVER-SOURCE-TAG: "Every bar carries source provenance forever"
    INV-RIVER-IBKR-PRIMACY: "Execution venue = data authority for live"
```

---

## SCHEMAS

```yaml
RAW_BAR_SCHEMA:
  note: "9 columns. Written to parquet. No ghost bars ever appear here."
  columns:
    timestamp:
      type: "datetime64[ns, UTC]"
      semantics: "Bar open time (world_time). Aligned to minute boundary."
      nullable: false
    open:
      type: float64
      nullable: false
    high:
      type: float64
      nullable: false
    low:
      type: float64
      nullable: false
    close:
      type: float64
      nullable: false
    volume:
      type: float64
      semantics: "Tick volume"
      nullable: false
    source:
      type: "string (enum: dukascopy | ibkr)"
      semantics: "Data provenance — permanent, never overwritten"
      nullable: false
    knowledge_time:
      type: "datetime64[ns, UTC]"
      semantics: |
        When Phoenix first learned this bar existed.
        Historical ingestion: script_run_timestamp.
        Live bars: IBKR callback received_timestamp.
        Prevents temporal hallucination in backtesting.
      nullable: false
    bar_hash:
      type: string
      semantics: "sha256(timestamp|open|high|low|close|volume|source)"
      nullable: false

MATERIALIZED_BAR_SCHEMA:
  note: "10 columns. Returned by RiverReader. Adds is_ghost at query time."
  inherits: RAW_BAR_SCHEMA
  additional_columns:
    is_ghost:
      type: bool
      semantics: |
        True = synthetic continuity bar (close=prev_close, volume=0, source=ghost).
        Injected by RiverReader, NEVER written to parquet.
        Gate evaluation: SKIP (not PASS/FAIL).
      default: false

PARTITION_SCHEME:
  pattern: "phoenix/river/{pair}/{year}/{month:02d}/{day:02d}.parquet"
  example: "phoenix/river/EURUSD/2026/02/22.parquet"
  rationale: |
    Daily files are truly write-once immutable. DuckDB handles glob natively.
    Solves concurrency: backfiller writes past days, streamer writes today.
    Forex day boundary = 17:00 NY (Sunday open through Friday close).
  note: "Multi-pair ready. 6 pair folders from day one."
```

---

## DATA TIMELINE

```yaml
DATA_LANDSCAPE:
  dukascopy_nex:
    range: "~2020-11 to 2025-11-23"
    pairs: "6 canonical (EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD)"
    format: "1m parquet (NEX era)"
    trust: "UNAUDITED — T1 audit required"
    note: |
      Some Dec/Jan data may exist from pre-Phoenix join attempts.
      Do NOT trust any post-Nov-23 NEX data without audit evidence.

  gap:
    range: "2025-11-24 to ~2026-01-23"
    status: "NO DATA"
    fill_strategy: |
      Fresh Dukascopy download (free, via Tickstory or direct).
      This fills the gap and extends the Dukascopy side of the seam,
      maximizing the overlap window with IBKR.

  ibkr_historical:
    range: "~2026-01-23 to present (rolling 30-day 1m window)"
    status: "AVAILABLE — gateway is LIVE"
    urgency: |
      IBKR 1m lookback is ~30 days. Window shrinks daily.
      Start capture TODAY to maximize overlap with Dukascopy.

  ibkr_live:
    range: "present → forward"
    status: "Gateway LIVE. Ready to stream."

  SEAM_STRATEGY: |
    1. Audit NEX Dukascopy data (2020-11 to 2025-11-23)
    2. Fresh Dukascopy download: 2025-11-24 to ~2026-02-08
    3. IBKR backfill: ~2026-01-23 to present
    4. Overlap zone: ~2026-01-23 to ~2026-02-08 (≥14 days)
    5. G signs seam attestation at validated join point
    6. IBKR live streaming from present forward

  OVERLAP_ACHIEVED: "~16 days (Jan 23 to Feb 8) — meets 14-day minimum"
```

---

## TASKS

```yaml
TASKS:

  T0_CAPTURE_NOW:
    what: "Start IBKR 1m bar capture immediately (overlap insurance)"
    urgency: CRITICAL — every day of delay shrinks IBKR lookback
    scope:
      - "Minimal viable RiverWriter: fetch EURUSD 1m from IBKR, write parquet"
      - "Use ~/nex/nex_lab/data/vendors/ibkr.py as starting material"
      - "Gateway is LIVE on port 4002 (paper)"
      - "Capture as much 1m history as IBKR will give (~30 days back)"
      - "Write to phoenix/river/EURUSD/ in daily partition format"
      - "knowledge_time = script_run_timestamp"
      - "source = ibkr"
      - "This is insurance — gets hardened into T2 proper"
    note: |
      Known patterns from NEX vendor code:
      - EventKit namespace conflict workaround
      - Pacing delay tracking (1 req/10s)
      - nest_asyncio for async context
      - ib_insync integration
    blocks: "Nothing — this is fire-and-forget capture"
    output: "Raw 1m parquet files in phoenix/river/EURUSD/"

  T1_NEX_AUDIT:
    what: "Audit NEX Dukascopy parquet files — all 6 canonical pairs"
    pairs: [EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD]
    source: "NEX backdata (parquet, ~2020-11 to 2025-11-23)"
    checklist:
      - "Full gap scan across 6 pairs, full date range"
      - "Timezone verification (UTC throughout, no DST artifacts)"
      - "DST boundary bars verified (US DST transitions — Sunday open at 21:00 vs 22:00 UTC)"
      - "Bar boundary verification (1m bars aligned to minute boundaries)"
      - "Weekend handling (no bars Fri 17:00 - Sun 17:00 NY, DST-aware)"
      - "Spread/volume sanity (no impossible prices, no negative spreads)"
      - "Random event sampling (at least 5: NFP dates, flash crash, Brexit, etc.)"
      - "Cross-reference sample bars against known Dukascopy public data"
      - "Verify actual date range end (stated: 2025-11-23, verify)"
      - "Flag any post-Nov-23 data as untrusted"
    output: "phoenix/docs/build_docs/NEX_AUDIT_REPORT.md"
    if_pass: "Adopt as historical base. Tag every bar source=dukascopy."
    if_fail: "Document failures. Fresh Dukascopy download via Tickstory for failed pairs."
    blocks: T3, T5

  T1B_DUKASCOPY_FRESH:
    what: "Download fresh Dukascopy data to fill Nov 2025 → Feb 2026 gap"
    scope:
      - "Source: Dukascopy (free) via Tickstory or direct download"
      - "Range: 2025-11-24 to ~2026-02-08 (extends to overlap with IBKR)"
      - "Pairs: EURUSD minimum, all 6 canonical if feasible"
      - "Convert to RAW_BAR_SCHEMA, write to daily parquet partition"
      - "source = dukascopy, knowledge_time = ingestion_timestamp"
    rationale: |
      Fills the gap between NEX end (Nov 23) and IBKR lookback (~Jan 23).
      Extends Dukascopy side of seam to achieve ≥14 day overlap.
    blocks: T5 (seam needs both sides populated)

  T2_RIVER_WRITER:
    what: "Build River Writer — IBKR reqHistoricalData → parquet (hardened)"
    evolves: "T0 capture script → production-grade writer"
    scope:
      - "RiverWriter class: fetches 1m bars from IBKR, writes daily parquet"
      - "Implements RAW_BAR_SCHEMA (9 columns) exactly"
      - "Write-once: each daily parquet written once, never modified"
      - "knowledge_time = received_timestamp for each bar"
      - "bar_hash computed on write"
      - "source = ibkr"
      - "IBKR pacing: max 1 req/10s for historical, backoff on throttle"
      - "Pair parameter in all function signatures (multi-pair ready)"
      - "Uses ib_insync (reference: ~/nex/nex_lab/data/vendors/ibkr.py)"
    ibkr_notes: |
      Gateway: port 4002 (paper), LIVE as of 2026-02-22.
      Verify reqHistoricalData market data permissions.
      Known patterns in NEX vendor code: EventKit namespace workaround,
      pacing delay tracking, nest_asyncio for async context.
    invariants:
      - "INV-RIVER-IMMUTABLE"
      - "INV-RIVER-SOURCE-TAG"
      - "INV-RIVER-BITEMPORAL"
    location: "phoenix/river/writer.py"
    tests: "phoenix/tests/test_river/test_writer.py"
    testing_strategy: |
      Unit tests: mock ib_insync client (pattern: phoenix/brokers/ibkr/mock_client.py).
      Integration tests: against paper account (separate test file, not in CI).
    blocks: T3

  T3_BACKFILL:
    what: "Backfill IBKR data: capture max available 1m history"
    depends: [T0_or_T2, T1_PASS]
    scope:
      - "Use RiverWriter to fetch all 6 canonical pairs from IBKR"
      - "EURUSD priority (needed for Asia Range Scalp)"
      - "Remaining 5 pairs: best effort within IBKR pacing limits"
      - "Verify no overlap corruption with NEX/Dukascopy data at seam zone"
      - "Log knowledge_time as script execution timestamp"
    note: |
      T0 may have already captured EURUSD. T3 extends to all pairs
      and verifies against T1 audit results.

  T4_DUCKDB_QUERY_LAYER:
    what: "Build DuckDB query layer (replaces SQLite RiverReader)"
    scope:
      - "RiverReader class: DuckDB over parquet glob"
      - "get_bars(pair, timeframe, start, end) → DataFrame (MATERIALIZED_BAR_SCHEMA)"
      - "Timeframe derivation: 1m → 5m, 15m, 1H, 4H, D via SQL aggregation"
      - "Ghost bar injection: detect gaps in 1m series, insert ghost bars with is_ghost=True"
      - "Ghost bar spec: close=prev_close, volume=0, source='ghost', is_ghost=True"
      - "Gap detection utility: returns list of missing 1m timestamps in trading hours"
      - "Read-only — RiverReader never writes"
      - "INV-NO-FORMING-CANDLE: never return incomplete current bar"
      - "DST-aware: weekend gap detection uses DST-adjusted boundaries"
      - "Pair parameter everywhere (multi-pair ready)"
    invariants:
      - "INV-RIVER-CONTINUOUS"
      - "INV-NO-FORMING-CANDLE"
    location: "phoenix/river/reader.py"
    tests: "phoenix/tests/test_river/test_reader.py"

  T5_SEAM_RECONCILIATION:
    what: "Validate Dukascopy-IBKR overlap at join point"
    depends: [T1_PASS, T1B, T3]
    scope:
      - "Identify overlap window (target: ≥14 days, ~Jan 23 to ~Feb 8)"
      - "Compare close prices: tolerance ≤ 0.1 pip (0.00001 for EURUSD)"
      - "Compare high/low: tolerance ≤ 0.2 pip"
      - "IBKR takes precedence in overlap zone"
      - "Generate RIVER_SEAM_REPORT.md: overlap stats, max divergence, bar-by-bar sample"
      - "If tolerance exceeded: HALT and report to G"
    output: "phoenix/docs/build_docs/RIVER_SEAM_REPORT.md"
    sovereign_gate: "G signs RIVER_SEAM_ATTESTATION after review"

  T6_ICT_DATA_CONTRACT_AMENDMENT:
    what: "Amend ICT_DATA_CONTRACT for ghost bar hybrid policy"
    location: "phoenix/docs/canon/ICT_DATA_CONTRACT.md"
    scope:
      - |
        Current: gap_policy: FLAG_ONLY
        Amended:
          gap_policy:
            raw_storage: FLAG_ONLY (gaps remain gaps in parquet)
            materialized_view: GHOST_FILL (is_ghost=True, volume=0, close=prev_close)
            gate_evaluation: SKIP (ghost bars are neither PASS nor FAIL)
      - "Add INV-RIVER-CONTINUOUS to contract"
      - "Add INV-RIVER-BITEMPORAL to contract"
      - "Document rationale: enrichment pipeline continuity (OWL S6 finding)"
    tests: "phoenix/tests/test_river/test_ghost_bars.py"

  T7_ENRICHMENT_WIRING:
    what: "Wire enrichment pipeline to new River"
    depends: [T4, T5_PASS, T6]
    scope:
      - "Replace SQLite RiverReader calls with new DuckDB RiverReader"
      - "Files to modify:"
      - "  phoenix/data/river_reader.py → deprecate (keep as fallback)"
      - "  phoenix/cfp/river_adapter.py → update to new reader"
      - "  phoenix/cso/market_state_builder.py → new River data source"
      - "  Hunt all other callers: cso, briefing, shadow, athena"
      - "Add RIVER_SOURCE env flag: 'parquet' (default) | 'legacy'"
      - "  legacy = old SQLite reader (rollback insurance, remove after 7 days stable)"
      - "Verify L1-L7 enrichment layers work with MATERIALIZED_BAR_SCHEMA"
      - "Ghost bars flow through enrichment with is_ghost preserved"
      - "Gate evaluator: ghost bar → SKIP state"
    tests: "phoenix/tests/test_river/test_enrichment_wiring.py"
    regression: "All 1716 existing tests must still pass"

  T8_LIVE_STREAMING:
    what: "IBKR live 1m bar streaming to daily parquet"
    depends: [T2, T5_PASS, T7]
    scope:
      - "RiverStreamer class: subscribes to IBKR real-time 1m bars"
      - "Intraday: bars accumulate in staging buffer (JSONL)"
      - "  Staging location: phoenix/river/{pair}/.staging/{date}.jsonl"
      - "End of forex day (17:00 NY): consolidate staging → daily parquet"
      - "  Daily parquet is then write-once immutable forever"
      - "knowledge_time = IBKR callback received_timestamp"
      - "Forex day boundary: 17:00 NY (DST-aware)"
      - "Weekend detection: no streaming Fri 17:00 - Sun 17:00 NY (DST-aware)"
      - "Forming bar handling: NEVER emit incomplete bar (INV-NO-FORMING-CANDLE)"
      - "Heartbeat: write phoenix/river/.heartbeat on every bar received"
      - "  If stale > 2 min during trading hours → alert"
      - "Pair parameter ready (multi-pair)"
    location: "phoenix/river/streamer.py"
    tests: "phoenix/tests/test_river/test_streamer.py"
    testing_strategy: |
      Unit: mock ib_insync client (pattern: phoenix/brokers/ibkr/mock_client.py).
      Integration: against paper account (separate test file).
```

---

## EXIT GATES

```yaml
EXIT_GATES:

  GATE_AUDIT:
    criterion: "NEX data passes 7-point audit for all 6 canonical pairs"
    test: "NEX_AUDIT_REPORT.md — all checks PASS per pair"
    proof: "Report artifact with per-check, per-pair evidence"

  GATE_FRESH:
    criterion: "Dukascopy fresh download fills gap to overlap zone"
    test: "Daily parquet files exist from 2025-11-24 to ~2026-02-08"
    proof: "DuckDB query returns continuous 1m bars across gap"

  GATE_WRITE:
    criterion: "RiverWriter produces valid daily parquet matching RAW_BAR_SCHEMA"
    test: "test_writer.py — schema validation, hash verification, write-once proof"
    proof: "Written parquet readable by DuckDB with correct 9 columns"

  GATE_READ:
    criterion: "RiverReader returns correct bars with TF derivation and ghost injection"
    test: "test_reader.py — 1m bars, 5m aggregation, 1H aggregation, ghost injection"
    proof: "Derived 5m bars match manual calculation. Ghost bars appear with is_ghost=True."

  GATE_SEAM:
    criterion: "Dukascopy-IBKR overlap ≥14 days within tolerance"
    test: "RIVER_SEAM_REPORT.md — close ≤ 0.1 pip, HL ≤ 0.2 pip, overlap ≥14 days"
    proof: "Overlap statistics + G attestation signature"

  GATE_GHOST:
    criterion: "Ghost bars injected correctly, gates SKIP on ghosts"
    test: "test_ghost_bars.py — gap → ghost with is_ghost=True, evaluator returns SKIP"
    proof: "Pipeline processes ghost bars without false signal"

  GATE_WIRING:
    criterion: "Enrichment pipeline works on new River, rollback functional"
    test: "test_enrichment_wiring.py + all 1716 existing tests pass"
    proof: "Zero regressions. RIVER_SOURCE=legacy also works."

  GATE_STREAM:
    criterion: "Live 1m bars stage to JSONL, consolidate to daily parquet"
    test: "test_streamer.py — mock IBKR callback, verify staging + consolidation + KT"
    proof: "Bar appears in DuckDB query. Heartbeat file updated."

  GATE_HEALTH:
    criterion: "Health report runs and detects injected faults"
    test: "Inject gap → report flags it. Inject stale bar → alert fires."
    proof: "Report artifact shows fault detection"
```

---

## PASS / FAIL CONDITIONS

```yaml
PASS_CONDITION: |
  ALL exit gates PASS.
  All 1716+ existing tests pass (zero regressions).
  G has signed RIVER_SEAM_ATTESTATION.
  Asia Range Scalp can evaluate on real EURUSD data from River.

FAIL_CONDITION:
  - "Any exit gate FAIL → HALT, report to CTO"
  - "NEX audit fails → Tickstory re-download for failed pairs"
  - "IBKR pacing prevents backfill → document gap, source from Dukascopy"
  - "Seam tolerance exceeded → HALT, escalate to G"
  - "Any existing test regresses → fix before proceeding"
  - "Overlap < 14 days after all fill attempts → escalate to G for waiver"
```

---

## DEPENDENCY GRAPH

```
Day 0 (TODAY):   T0 (IBKR capture — overlap insurance, EURUSD first)
Day 1:           T1 (audit) ‖ T1B (fresh Dukascopy) ‖ T2 (writer harden) ‖ T6 (contract)
Day 2-3:         T3 (backfill all pairs, needs T1+T2) ‖ T4 (reader, needs T2 schema)
Day 4:           T5 (seam, needs T1+T1B+T3) → G signs attestation
Day 5:           T7 (wiring, needs T4+T5+T6) → T8 (streaming, needs T2+T5+T7)
```

---

## FILE PLAN

```yaml
DELIVERABLES:

  code_new:
    - "phoenix/river/__init__.py"
    - "phoenix/river/schema.py            # RAW + MATERIALIZED schemas, hash computation"
    - "phoenix/river/writer.py            # RiverWriter (IBKR → daily parquet)"
    - "phoenix/river/reader.py            # RiverReader (DuckDB over parquet, ghost injection)"
    - "phoenix/river/streamer.py          # RiverStreamer (live 1m bars → staging → daily)"
    - "phoenix/river/health_report.py     # Daily integrity check + heartbeat monitoring"
    - "phoenix/river/nex_ingestor.py      # NEX parquet → River daily parquet migration"
    - "phoenix/river/dukascopy_ingestor.py # Fresh Dukascopy download → River parquet"
    - "phoenix/river/seam.py              # Overlap reconciliation + attestation support"

  code_modified:
    - "phoenix/docs/canon/ICT_DATA_CONTRACT.md    # Ghost bar amendment"
    - "phoenix/data/river_reader.py                # Deprecate (keep as legacy fallback)"
    - "phoenix/cfp/river_adapter.py                # Update to new RiverReader"
    - "phoenix/cso/market_state_builder.py         # New River data source"
    - "phoenix/enrichment/ (L1-L7 as needed)       # DataFrame format compatibility"

  tests:
    - "phoenix/tests/test_river/__init__.py"
    - "phoenix/tests/test_river/test_schema.py"
    - "phoenix/tests/test_river/test_writer.py"
    - "phoenix/tests/test_river/test_reader.py"
    - "phoenix/tests/test_river/test_streamer.py"
    - "phoenix/tests/test_river/test_ghost_bars.py"
    - "phoenix/tests/test_river/test_enrichment_wiring.py"
    - "phoenix/tests/test_river/test_nex_audit.py"

  docs:
    - "phoenix/docs/build_docs/NEX_AUDIT_REPORT.md"
    - "phoenix/docs/build_docs/RIVER_SEAM_REPORT.md"
    - "phoenix/docs/build_docs/RIVER_HEALTH_REPORT.md"
```

---

## REFERENCE

```yaml
REF:
  doctrine:
    - "phoenix/docs/build_docs/RIVER_SYNTHESIS.md (advisor convergence — LOCKED)"
  contracts:
    - "phoenix/docs/canon/ICT_DATA_CONTRACT.md (current, pre-amendment)"
  existing_code:
    - "phoenix/data/river_reader.py (current SQLite reader — to deprecate)"
    - "phoenix/cfp/river_adapter.py (current adapter — to update)"
    - "phoenix/cso/market_state_builder.py (current wiring — to update)"
    - "phoenix/cso/enrichment_to_state_map.yaml"
    - "phoenix/brokers/ibkr/ (existing IBKR integration — orders/positions only)"
    - "phoenix/brokers/ibkr/mock_client.py (mock pattern for testing)"
  nex_reference:
    - "~/nex/nex_lab/data/vendors/ibkr.py (IBKR historical data patterns — starting material)"
    - "~/nex/nex_lab/data/raw/ (original Dukascopy CSVs, 2020-11 to 2025-11-23)"
    - "~/nex/backdata/ (parquet files — audit target)"
  ibkr:
    - "Gateway: port 4002 (paper), LIVE as of 2026-02-22"
    - "API: reqHistoricalData (1m bars, ~30 day lookback)"
    - "API: reqRealTimeBars (live streaming)"
    - "Pacing: max 1 req/10s for historical data"
```

---

## NOTES FOR BUILDER

```yaml
CRITICAL:

  1_START_CAPTURE_NOW: |
    T0 is time-sensitive. IBKR gateway is live. Start EURUSD 1m capture
    immediately using NEX vendor code as reference. Every day of delay
    loses a day of overlap. This is the single highest priority action.

  2_BITEMPORAL_IS_NON_NEGOTIABLE: |
    Every bar gets knowledge_time. Historical: script_run_timestamp.
    Live: IBKR callback received_timestamp. This prevents temporal
    hallucination in backtesting. The session's crown jewel insight.

  3_GHOST_BARS_MATERIALIZED_ONLY: |
    Ghost bars NEVER appear in raw parquet. RiverReader injects them
    at query time into MATERIALIZED_BAR_SCHEMA. The raw files are
    the constitution — ghosts are the reading glasses.

  4_DAILY_PARTITION_IS_IMMUTABLE: |
    Each daily parquet file is written once. Live bars stage in JSONL,
    consolidate at forex day close (17:00 NY). Never rewrite a daily file.
    Forex day boundary is DST-aware.

  5_EXISTING_TESTS: |
    1716 tests exist. Zero regressions tolerated. Run full suite after
    T7 (enrichment wiring). If anything breaks, fix before proceeding.

  6_MULTI_PAIR_READY: |
    Pair parameter in every function signature. 6 canonical pair folders
    from day one. When Olya says "now do GBPUSD" the answer is
    "already works, just need to ingest."

  7_ROLLBACK_INSURANCE: |
    Keep old river_reader.py working. RIVER_SOURCE env flag: 'parquet'
    (default) or 'legacy'. Remove legacy path after 7 days stable.

  8_HALT_ON_AMBIGUITY: |
    If anything in this brief is unclear, HALT and ask CTO.
    The River is constitutional — "epistemic root of Phoenix."
    Get it right.

REPORT_FORMAT: DENSE
```
