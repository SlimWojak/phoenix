# RIVER DOCTRINE — ADVISOR BROADCAST BRIEF

```yaml
BRIEF: S51.RIVER.POLL.001
MISSION: RIVER_ARCHITECTURE_DESIGN
FORMAT: DENSE
PATTERN: BROADCAST (parallel, independent responses)
DATE: 2026-02-22

# ═══════════════════════════════════════════════════════════════════════════
# SITUATION
# ═══════════════════════════════════════════════════════════════════════════

SITUATION:
  discovery: |
    During S51 DRIVESHAFT delivery, we discovered that Phoenix has
    NO market data writer. The enrichment pipeline, evaluator, and
    execution engine are all built and tested — but the fuel line
    from IBKR to the system was never ported from NEX (predecessor).

    The River DB (sqlite) contains only 1H EURUSD bars, last updated
    2026-01-27. No 5m bars exist. Asia Range Scalp needs 5m as primary TF.

  history: |
    NEX's River was the single biggest source of operational mistrust.
    "Always unclear whether it was clean." Floppy, janky, unclear provenance.
    We will NOT patch this. We will design it right.

  stakes: |
    River is the PRIMARY INPUT to everything Phoenix computes.
    If the raw data is bad, every gate evaluation, every trade proposal,
    every bead downstream is contaminated. This is our ChadBoar insight
    applied to market data: substrate quality IS the moat.

  budget: |
    G is willing to pay for robust data APIs and infrastructure.
    No corners cut. Family office grade. Institutional where it matters.

# ═══════════════════════════════════════════════════════════════════════════
# EXISTING ASSETS
# ═══════════════════════════════════════════════════════════════════════════

EXISTING_ASSETS:

  nex_backdata:
    location: "~/nex/nex_lab/data/fx"
    content: "5 years, 6 pairs, 1-minute bars"
    format: "Parquet files + CSV in ~/raw"
    freshness: "Up to ~mid-November 2025 (3 months stale)"
    source: "Dukascopy (validated at time of ingestion by Claude)"
    trust: "Believed clean — checked for dupes and zero-volume bars. May benefit from integrity sweep."

  nex_pipeline:
    polygon_key: "Available in NEX .env (paid API)"
    backfill_function: "Existed but unclear reliability"
    enrichment: "Over-engineered for current needs"
    river_db: "sqlite, EURUSD_1H only, always felt janky"

  ibkr:
    historical_api: "reqHistoricalData"
    forex_5m_depth: "~30 days"
    forex_1h_depth: "~1 year"
    forex_1m_depth: "Limited (~1-2 weeks)"
    rate_limits: "60 requests per 10 minutes (pacing)"
    trust: "HIGHEST — execution venue = data venue, prices match fills"
    live_streaming: "Available (5s bars or tick-by-tick)"

  polygon:
    capabilities: "Unknown for forex 1m fidelity — needs investigation"
    cost: "Paid tier, key exists"
    trust: "MEDIUM — third party, not execution venue"

  dukascopy:
    historical: "Deep forex history (10+ years, tick-level available)"
    cost: "Free for historical, requires download tooling"
    trust: "MEDIUM-HIGH — widely used by retail/semi-pro, well-validated"

# ═══════════════════════════════════════════════════════════════════════════
# FIVE ARCHITECTURAL QUESTIONS
# ═══════════════════════════════════════════════════════════════════════════

QUESTIONS:

  Q1_SOURCE_OF_TRUTH:
    question: "What is the canonical data source for Phoenix market data?"

    options:
      A_IBKR_ONLY:
        description: "IBKR for everything — history and live"
        pro: "Single source, highest trust, matches execution fills"
        con: "Limited depth for sub-1H (5m ~30 days, 1m ~2 weeks)"

      B_DUAL_SOURCE_MANAGED_SEAM:
        description: "Dukascopy/Polygon for deep history + IBKR for recent + live"
        pro: "5 years of 1m data available. Rich backtesting substrate."
        con: "Seam between sources. Price discrepancies at boundary."

      C_NEX_FILES_PLUS_IBKR:
        description: "Trust existing NEX parquet files + IBKR from Nov 2025 forward"
        pro: "Zero cost, data already exists, minimal new work"
        con: "NEX data trust level uncertain. Inherits janky lineage."

    g_leaning: |
      Option B — but the seam must be managed carefully. Once joined,
      IBKR becomes single source of truth going forward. History gives
      Dexter deep exploration substrate. The seam is the pressure point.

    cto_note: |
      The seam question is critical. Advisors should address: How do
      institutional shops handle the history/live source boundary? What's
      the standard pattern? Is there a "seam attestation" that proves
      consistency at the join point?

  Q2_STORAGE_FORMAT:
    question: "What storage format for the River?"

    options:
      A_SQLITE_DONE_RIGHT:
        description: "SQLite with WAL mode, schema validation, checksums"
        pro: "Simple, portable, single-file, good enough for many quant shops"
        con: "Mutable (corruption risk), concurrent access fragile, hard to audit"

      B_PARQUET_APPEND_ONLY:
        description: "Immutable parquet files, partitioned by date/pair/timeframe"
        pro: "Immutable = auditable. Natural versioning. Fast columnar reads."
        con: "More complex write pattern. Not great for 'latest bar' queries."

      C_TIMESERIES_DB:
        description: "DuckDB, TimescaleDB, QuestDB, or InfluxDB"
        pro: "Purpose-built for time-series. Fast range queries. Gap detection built in."
        con: "Heavier dependency. Migration risk. Overkill for single-pair start."

    g_leaning: |
      Parquet feels like what a pro shop would use. But open to advisor
      input on what elevates this to institutional / family office level.

    cto_note: |
      DuckDB is interesting — reads parquet natively, gives SQL interface
      over immutable files. Could be "best of B and C." Advisors should
      consider operational simplicity alongside capability.

  Q3_VALIDATION_CONTRACT:
    question: "How does Phoenix KNOW the River is clean at all times?"

    requirements:
      provenance: "Every bar tagged with: source, ingestion_time, hash"
      gap_detection: "No missing bars in any timeframe, continuous coverage"
      consistency: "1m bars aggregate to matching 5m, 15m, 1H, 4H, D, W bars"
      staleness: "Alert if last bar > N minutes old"
      forming_bar_ban: "Incomplete bars NEVER in store (INV-NO-FORMING-CANDLE)"
      cross_source: "Where two sources overlap, they must agree within tolerance"

    g_view: "This is the River equivalent of Bead Field attestation."

    cto_note: |
      The Bead Field has hash chains, Merkle anchoring, PQC signatures.
      River needs its own integrity layer — lighter weight but same
      philosophy: "trust but verify, continuously."

  Q4_TIMEFRAME_ARCHITECTURE:
    question: "Store 1m and derive higher TFs, or store each independently?"

    options:
      A_STORE_1M_DERIVE_ALL:
        description: "Store only 1m bars. Compute 5m/15m/1H/4H/D/W on read."
        pro: "Single source of truth. No consistency risk between TFs."
        con: "Compute cost on every read. Need careful caching."

      B_STORE_EACH_TF:
        description: "Store 1m, 5m, 15m, 1H, 4H, D, W independently."
        pro: "Fast reads. Pre-computed."
        con: "Consistency risk. 7x storage. Possible divergence."

      C_STORE_1M_MATERIALIZE_VIEWS:
        description: "Store 1m as base. Materialize higher TFs as validated views."
        pro: "Single source + fast reads. Views re-derivable from 1m."
        con: "Materialization pipeline needed. Views could go stale."

    g_leaning: "Option A for purity, but unclear if Option C is better operationally."

    cto_note: |
      Option C with DuckDB could be elegant — 1m parquet as immutable base,
      DuckDB views that aggregate on demand (DuckDB is fast enough that
      materialization may be unnecessary). Advisors should consider whether
      the compute cost of A is real or theoretical at our data volume.

  Q5_NEX_DATA_AUDIT:
    question: "Can we trust the existing 5-year NEX dataset?"

    known:
      source: "Dukascopy"
      validated: "Checked for dupes and zero-volume bars at ingestion"
      format: "Parquet (1m bars, 6 pairs)"
      age: "Up to ~mid-November 2025"

    audit_needed:
      - "Gap analysis across all 6 pairs, full 5-year range"
      - "Cross-reference sample bars (random + known events) against IBKR or Polygon"
      - "Timezone verification (UTC throughout? Any DST artifacts?)"
      - "Spread/volume sanity (no impossible prices, no suspicious gaps around news)"
      - "Weekend handling (no bars Fri 17:00 - Sun 17:00 NY)"

    g_view: |
      Believed clean but worth a sweep. Dukascopy is reputable for retail/semi-pro.
      The data was validated at time, but that was by an earlier Claude instance —
      we should trust-but-verify.

# ═══════════════════════════════════════════════════════════════════════════
# ADVISOR-SPECIFIC LENSES
# ═══════════════════════════════════════════════════════════════════════════

ADVISOR_ASSIGNMENTS:

  OWL_GEMINI:
    role: "Structural Architect"
    focus: |
      1. SEAM INTEGRITY: If we use dual sources (Q1-B), what's the
         structural contract at the join? How do institutional data
         pipelines handle the history/live boundary?
      2. STORAGE ARCHITECTURE: Ripple analysis of each Q2 option against
         Phoenix's existing code (RiverReader, enrichment layers, evaluator).
      3. TIMEFRAME DERIVATION: Structural opinion on Q4 options — where
         does complexity hide? What's the failure surface of each?
      4. VALIDATION CONTRACT: Design the River integrity layer (Q3).
         What's the minimum viable attestation that gives G confidence?
    deliverable: "RIVER_STRUCTURAL_AUDIT.yaml"

  GPT_ARCHITECT:
    role: "Spec Tightener"
    focus: |
      1. FLAG TABLE: For each Q1-Q5 option, what are the edge cases,
         hidden costs, and required-but-unstated dependencies?
      2. DATA SOURCE COMPARISON: Dukascopy vs Polygon vs IBKR — concrete
         capabilities table (depth, resolution, cost, reliability, forex coverage).
      3. SEAM SPECIFICATION: If Q1-B wins, specify the exact seam contract
         (overlap window, tolerance, reconciliation rules, attestation).
      4. INSTITUTIONAL BENCHMARK: What do family offices and small quant
         funds actually use for forex data infrastructure? What's the
         "grown-up" version of what we're building?
    deliverable: "RIVER_SPEC_FLAGS.yaml"

  BOAR_GROK:
    role: "Chaos Auditor + Field Intelligence"
    focus: |
      1. SOCIAL RECON: What are quant traders on Reddit (r/algotrading,
         r/quant), X, and forums actually using for forex data? What
         do they complain about? What do they recommend? What fails
         in production that looks fine in backtests?
      2. DUMBEST FAILURE MODES: For each architecture option, what's
         the failure that wastes the most time to diagnose? DST bugs?
         Timezone mismatches between sources? Missing Sunday opens?
         Incorrect bar boundaries?
      3. HIDDEN GEMS: Are there data sources or tools we're not
         considering? Open-source forex data projects? Cheaper/better
         alternatives to Polygon?
      4. REAL-WORLD STRESS: What happens to data quality during flash
         crashes, NFP releases, liquidity gaps? How do different sources
         handle these?
    deliverable: "RIVER_CHAOS_RECON.yaml"

# ═══════════════════════════════════════════════════════════════════════════
# META
# ═══════════════════════════════════════════════════════════════════════════

TIMELINE: "No rush. Get it right. This week is design, not build."
RETURN_FORMAT: DENSE (structured findings, not essays)
ANTI_SCOPE: "Do NOT build anything. Research and recommend only."
SYNTHESIS: "G curates advisor returns → DENSE for CTO → CTO synthesizes position"

CONTEXT_FOR_ADVISORS: |
  Phoenix is a constitutional trading system. v0.1 is sealed with 1716 tests
  and 154+ invariants. S51 just wired the first strategy (Asia Range Scalp)
  end-to-end — but discovered the market data pipeline was never built.

  We are designing the River (market data substrate) with the same rigor
  we applied to the Bead Field (analytical substrate). This is foundation
  infrastructure. Budget available for proper tooling and data.
  No corners cut.

  The system currently needs EURUSD 5m bars as primary timeframe, with
  1m as base resolution for future strategies. Six pairs in the backdata.
  IBKR is the execution venue (paper trading now, live later).
```
