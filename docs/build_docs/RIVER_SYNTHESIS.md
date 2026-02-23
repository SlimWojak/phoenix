# RIVER_SYNTHESIS.md — Advisor Returns Synthesis

```yaml
document: RIVER_SYNTHESIS
version: 1.0
date: 2026-02-22
author: OPUS (Cursor — Synthesis Agent)
input: OWL (Gemini), GPT (Architect), BOAR (Grok)
status: RECOMMENDATION ONLY — CTO + G lock decisions
format: DENSE
```

---

## 1. CONVERGENCE MAP (All 3 Agree)

These are settled. No further debate needed unless CTO/G see something the advisors missed.

```yaml
UNANIMOUS:

  Q1_SOURCE: "Dual source — Dukascopy history + IBKR forward"
    OWL: "IBKR for logic, secondary for audit"
    GPT: "Correct institutional pattern IF seam becomes first-class artifact"
    BOAR: "Quants swear by it for backtests"
    strength: STRONG (all 3 converge independently, GPT cites institutional benchmark)

  Q2_STORAGE: "Parquet as immutable base"
    OWL: "Immutable blob storage, re-materializable"
    GPT: "Parquet 1m partitioned by pair/date, DuckDB read layer"
    BOAR: "NautilusTrader uses it, avoids SQLite jank at scale"
    strength: STRONG (no dissent, aligns with Bead Field philosophy)

  Q3_INTEGRITY: "Formal validation layer is non-negotiable"
    OWL: "Checksum of Reality — River State Beads"
    GPT: "Per-bar source + ingestion_time + sha256, daily checks"
    BOAR: "Multi-source validation, automated alerts, point-in-time"
    strength: STRONG (all emphasize this is constitutional, not optional)

  Q4_TIMEFRAME: "Store 1m, derive higher TFs"
    OWL: "1m is minimum Atom of ICT logic — can't reconstruct intra-candle from 5m"
    GPT: "Start with A. DuckDB aggregation fast enough. Profile before optimizing."
    BOAR: "Fidelity wins. Watch for bar boundary mismatches in aggregation."
    strength: STRONG (OWL gives the kill argument — sweep dynamics invisible at 5m)

  Q5_NEX_AUDIT: "Formal audit required before trust"
    OWL: (implicit — build fresh perception, don't inherit jank)
    GPT: "Do not trust prior Claude validation. Trust-but-verify."
    BOAR: "Sweep it — gaps, vol sanity, cross-ref IBKR/Polygon"
    strength: STRONG (no one says "just use it")

  IBKR_PRIMACY: "Execution venue = data authority for live trading"
    OWL: "If Polygon says sweep at 1.0850 but IBKR peaked at 1.0849, system triggers unfillable trade"
    GPT: "IBKR = highest trust (execution venue)"
    BOAR: "Server mismatches across brokers (200-300 pip differences observed)"
    strength: STRONG (BOAR's field evidence is particularly compelling)

  RIVER_IS_CONSTITUTIONAL: "Not plumbing — epistemic root of Phoenix"
    OWL: "Sovereignty Boundary — auditable by court of law"
    GPT: "River is the epistemic root of Phoenix"
    BOAR: "River's the moat — pollute it, Phoenix dies"
    strength: STRONG (rare philosophical convergence)
```

---

## 2. DIVERGENCE MAP (Where They Disagree)

These need CTO judgment calls. Evidence quality varies.

```yaml
DIVERGENCE:

  D1_LAKE_RIVER_SEPARATION:
    question: "Should raw API responses be stored separately from materialized views?"
    OWL: "YES — API → Immutable Lake (JSONL) → Materialized River (SQLite/parquet)"
    GPT: "Not explicitly proposed. Focuses on parquet-as-base."
    BOAR: "Not addressed."

    evidence_for: |
      OWL's argument is structural: if the materialized view is corrupt,
      you delete it and re-derive from raw. This is the Bead Field pattern
      (immutable substrate → fluid analysis). Adds ~1 extra file per day.
    evidence_against: |
      For forex OHLCV, the "raw API response" IS the bar data. There's no
      richer raw form to preserve (unlike tick data). The parquet file IS
      the immutable record. Lake/River separation adds complexity without
      clear benefit at OHLCV granularity.
    recommendation: |
      SKIP for Phase 1. Parquet IS the immutable lake. If we later ingest
      tick-level data, revisit. The re-derivation benefit exists but the
      cost of dual storage isn't justified when parquet = immutable source.
    needs_sovereign_call: NO (architectural, CTO can decide)

  D2_BITEMPORAL:
    question: "Does every bar need world_time AND knowledge_time?"
    OWL: "YES — emphatically. Only way to kill lookahead in backtesting."
    GPT: "Mentions ingestion_time per bar but doesn't frame it as bitemporal."
    BOAR: "Not addressed."

    evidence_for: |
      OWL's argument is precise: during backtesting, filtering by knowledge_time
      ensures you can't see a bar that was backfilled after the fact. This is
      the same bitemporal pattern proven in the Bead Field (WT + KT).
      Without it, a backfill script that fills a gap at T+24h creates
      data that "existed" at T+0 in a backtest — classic lookahead.
    evidence_against: |
      For IBKR live streaming, knowledge_time ≈ world_time + network latency
      (milliseconds). The distinction matters primarily for backfilled bars.
      For historical Dukascopy data, knowledge_time is "ingestion date" which
      is useful but not as precise as live KT.
    recommendation: |
      ADOPT. Add knowledge_time column. Low cost, high integrity value.
      Aligns with Bead Field pattern. For historical ingestion, KT =
      script_run_timestamp. For live bars, KT = received_timestamp.
      This is a INV-RIVER-BITEMPORAL invariant.
    needs_sovereign_call: NO (clear engineering win, CTO decides)

  D3_GHOST_BARS:
    question: "Missing 1m bar: insert ghost bar or flag gap?"
    OWL: "Insert GHOST_BAR (close = previous_close, volume = 0)"
    GPT: "FLAG_ONLY per ICT_DATA_CONTRACT (existing constitutional doc)"
    BOAR: "Gaps cause issues (implicit: need handling)"

    evidence_for_ghost: |
      OWL's argument: ghost bars make the time-series mathematically
      continuous, preventing asof_merge failures in enrichment. Without
      them, L2 reference level groupby breaks on gaps.
    evidence_for_flag: |
      GPT cites existing ICT_DATA_CONTRACT.md which says gap_policy: FLAG_ONLY.
      This is already a constitutional document. Ghost bars = synthetic data,
      which violates INV-DATA-2 (no synthetic without flag).
    recommendation: |
      HYBRID — reconcile both positions:
      1. Raw parquet: gaps remain gaps (FLAG_ONLY, per constitution)
      2. Materialized view: ghost bars inserted WITH is_ghost=True flag
      3. Enrichment pipeline: sees continuous series but can filter ghosts
      4. Gate evaluation: ghost bars trigger SKIP (not PASS/FAIL)
      This preserves raw integrity while giving enrichment continuity.
    needs_sovereign_call: YES — modifies existing ICT_DATA_CONTRACT policy

  D4_SECONDARY_AUDIT_FEED:
    question: "Should Phoenix maintain a secondary data feed for divergence detection?"
    OWL: "YES — Polygon as audit feed. Divergence beyond threshold → Sovereign Halt."
    GPT: "Mentions cross-source overlap for seam validation, not ongoing audit."
    BOAR: "Multi-source validation recommended but no ongoing dual-feed proposal."

    evidence_for: |
      OWL's Divergence Guard is a novel invariant: if execution-venue data
      and market-consensus data disagree, something is wrong. This catches
      IBKR-specific issues (API bugs, pacing-induced gaps, revision).
    evidence_against: |
      Adds ongoing cost (Polygon subscription), complexity (second ingestion
      pipeline), and a new failure mode (audit feed fails → false halt).
      For Phase 1 with single pair, may be overengineered.
    recommendation: |
      DEFER to Phase 2. Compelling concept but premature for EURUSD-only
      Phase 1. Capture as INV-RIVER-DIVERGENCE-GUARD (future) and revisit
      when multi-pair goes live. The seam reconciliation at join point
      provides initial cross-source validation.
    needs_sovereign_call: NO (timing decision, CTO decides)

  D5_RIVER_STATE_BEAD:
    question: "Should market data be anchored into the Bead Field via Merkle roots?"
    OWL: "YES — hourly River_State_Bead, Merkle root of last 12 bars."
    GPT: "Not proposed."
    BOAR: "Not proposed."

    evidence_for: |
      Proves data used for a trade on Tuesday is identical to data used
      in audit on Friday. Constitutional-grade auditability. Aligns with
      Bead Field philosophy. Prevents silent repainting.
    evidence_against: |
      Crosses the Economy 1/Economy 2 boundary in a new direction
      (River → Bead Field, vs current Phoenix → Bead Field).
      Adds coupling between River writer and Bead Field ingestion.
    recommendation: |
      ADOPT IN PRINCIPLE, defer implementation to post-Phase 1.
      The integrity layer (per-bar hashes + daily reports) provides
      equivalent auditability without Bead Field coupling. Once both
      systems are stable, bridging them via River_State_Beads is natural.
    needs_sovereign_call: NO (phasing decision)

  D6_DUCKDB_ROLE:
    question: "DuckDB as query layer, or just raw parquet reads?"
    OWL: "Doesn't mention DuckDB. Proposes materialized SQLite views."
    GPT: "DuckDB as query layer over parquet. Elegant — SQL + immutable."
    BOAR: "Doesn't opine specifically."

    recommendation: |
      ADOPT DuckDB. GPT's reasoning is sound: SQL over immutable parquet,
      zero server infrastructure, fast aggregation. DuckDB reads parquet
      natively, handles the 1m → 5m/1H derivation, and replaces SQLite
      without the mutability risk. RiverReader refactor is straightforward.
    needs_sovereign_call: NO (clear engineering choice)
```

---

## 3. SURPRISES (Things None of Us Considered)

```yaml
SURPRISES:

  S1_BITEMPORAL_BACKTEST_INTEGRITY:
    source: OWL
    insight: |
      knowledge_time on every bar prevents a whole class of lookahead
      bias that INV-NO-FORMING-CANDLE only partially addresses. If you
      backfill 3 months of missing data today, and then backtest yesterday's
      session, those bars "existed" in your backtest even though they didn't
      exist at T-0 when the real session ran. Bitemporal is the only fix.
    impact: HIGH — changes how we think about backfill integrity

  S2_SEVENTY_FOUR_PERCENT_STAT:
    source: BOAR (Acuiti/Exegy reports)
    insight: |
      74% of quantitative traders have experienced data quality issues
      during peak market volatility. This is not a theoretical risk.
      Market data is the #1 operational failure surface.
    impact: MEDIUM — validates the "no corners cut" investment posture

  S3_TICKSTORY_TOOL:
    source: BOAR
    insight: |
      Tickstory is an automated Dukascopy tick data downloader with
      MT4/MT5 integration. Could solve the historical data acquisition
      problem with minimal custom code.
    impact: MEDIUM — potential tool for NEX data refresh or replacement

  S4_CROSS_BROKER_PIP_DIVERGENCE:
    source: BOAR (field reports)
    insight: |
      Real-world reports of 200-300 pip differences between brokers
      during events. "Exness correct, FXCM/FXTM off — stops hit on
      ghosts, 200-300 pip winners nuked." This is why execution-venue
      data must be the authority for trading logic.
    impact: HIGH — reinforces IBKR-primacy for live, and explains why
      cross-source tolerance must be defined precisely

  S5_DIVERGENCE_GUARD_AS_INVARIANT:
    source: OWL
    insight: |
      If primary (IBKR) and secondary (Polygon/Dukascopy) feeds diverge
      beyond threshold during live trading → Sovereign Halt. The "map"
      and "territory" no longer match. This is a new invariant class
      nobody had proposed before.
    impact: MEDIUM — compelling for multi-pair Phase 2, premature for Phase 1

  S6_GHOST_BAR_PIPELINE_FRAGILITY:
    source: OWL
    insight: |
      asof_merge in enrichment pipeline assumes continuous time series.
      A missing 1m bar doesn't just create a gap — it causes L2 groupby
      to compute wrong Asia ranges, L3 to miss sweep events, L4 to
      miscalculate swing points. The failure is SILENT. Ghost bars
      (flagged) prevent this cascade.
    impact: HIGH — reveals a fragility in the current enrichment pipeline
      that would only surface in production with real data gaps
```

---

## 4. DRAFT RECOMMENDATIONS (Q1-Q5)

```yaml
Q1_SOURCE_OF_TRUTH:
  recommendation: "B — DUAL_SOURCE_MANAGED_SEAM"
  confidence: HIGH (unanimous)
  rationale: |
    All three advisors converge. Dukascopy for deep history (5+ years, 1m),
    IBKR for recent + live. The seam is the pressure point — must be
    explicit, overlap-validated, and signed. Once joined, IBKR is sole
    forward authority.
  seam_contract: |
    - 14-day minimum overlap window
    - Close price tolerance: ≤0.1 pip
    - High/low tolerance: ≤0.2 pip
    - IBKR takes precedence in overlap
    - RIVER_SEAM_ATTESTATION artifact signed by G
    - Seam is permanent record, never deleted
  sovereign_call_needed: YES — G must sign seam attestation

Q2_STORAGE_FORMAT:
  recommendation: "B — PARQUET (immutable, partitioned) + DuckDB (query layer)"
  confidence: HIGH (unanimous on parquet, GPT specific on DuckDB)
  rationale: |
    Immutable parquet files = no corruption risk, natural versioning,
    checksum-able, compatible with DuckDB. DuckDB provides SQL over
    immutable files with zero server infrastructure. Replaces SQLite
    without the mutability problems. Aligns with Bead Field philosophy.
  partition_scheme: "pair/year/month/ (one parquet file per month per pair)"
  sovereign_call_needed: NO

Q3_VALIDATION_CONTRACT:
  recommendation: "Formal River Integrity Layer"
  confidence: HIGH (unanimous)
  components:
    per_bar:
      - "source (dukascopy | ibkr)"
      - "knowledge_time (when Phoenix learned this bar)"
      - "sha256 hash"
    continuous_checks:
      - "1m gap scan (no missing bars in trading hours)"
      - "Weekend rule validation (no bars Fri 17:00 - Sun 17:00 NY)"
      - "DST boundary validation"
      - "Staleness check (alert if last bar > N minutes old)"
      - "Forming bar ban (INV-NO-FORMING-CANDLE)"
    aggregation_checks:
      - "1m → 5m consistency (derived bars match)"
      - "5m → 1H consistency"
    cross_source:
      - "Seam overlap tolerance comparison"
    reporting:
      - "RIVER_HEALTH_REPORT emitted daily"
  new_invariants:
    - "INV-RIVER-BITEMPORAL: Every bar has world_time + knowledge_time"
    - "INV-RIVER-IMMUTABLE: Raw parquet files are append-only, never modified"
    - "INV-RIVER-CONTINUOUS: No gaps in 1m series during trading hours (ghost bars flagged)"
    - "INV-RIVER-SOURCE-TAG: Every bar carries source provenance forever"
  sovereign_call_needed: YES — ghost bar policy modifies ICT_DATA_CONTRACT

Q4_TIMEFRAME_ARCHITECTURE:
  recommendation: "A — STORE 1m, DERIVE ALL HIGHER TFs"
  confidence: HIGH (unanimous)
  rationale: |
    OWL's kill argument: "If you store only 5m bars, you lose the ability
    to see HOW the sweep happened inside the candle." At our data volume
    (6 pairs × 5 years × ~365K 1m bars/year ≈ 11M rows), DuckDB
    aggregation is effectively instant. No materialization needed.
  fallback: |
    If profiling reveals DuckDB aggregation is too slow for real-time
    evaluation (unlikely), materialize 5m as cached view (Option C).
    But start with A and measure.
  sovereign_call_needed: NO

Q5_NEX_DATA_AUDIT:
  recommendation: "Formal audit before adoption"
  confidence: HIGH (unanimous)
  audit_checklist:
    - "Full gap scan across 6 pairs, full 5-year range"
    - "Timezone verification (UTC throughout, no DST artifacts)"
    - "Cross-reference sample bars against IBKR for overlap period"
    - "Random event sampling (NFP dates, flash crash dates)"
    - "Weekend handling (no bars Fri 17:00 - Sun 17:00 NY)"
    - "Spread/volume sanity (no impossible prices)"
    - "Bar boundary verification (1m bars aligned to minute boundaries)"
  if_audit_passes: |
    Adopt as historical base. Tag every bar with source=dukascopy.
    Join with IBKR at seam point with 14-day overlap reconciliation.
  if_audit_fails: |
    Download fresh from Dukascopy (Tickstory tool — BOAR recommendation).
    Re-ingest with proper provenance. Cost: time only (Dukascopy is free).
  sovereign_call_needed: NO (audit is execution, CTO decides)
```

---

## 5. SOVEREIGN CALLS NEEDED (G Must Decide)

```yaml
SOVEREIGN_CALL_1:
  question: "Sign the seam attestation when dual-source join is validated?"
  context: |
    The seam between Dukascopy history and IBKR live is a permanent
    constitutional artifact. Once signed, it asserts: "I, G, attest
    that the data join at [timestamp] has been validated within
    [tolerance] and is fit for trading decisions."
  advisors_say: "All 3 agree this must be signed by G"
  recommendation: "YES — this is analogous to the Bead Field Genesis signing"

SOVEREIGN_CALL_2:
  question: "Approve ghost bar policy modification to ICT_DATA_CONTRACT?"
  context: |
    Current constitution says gap_policy: FLAG_ONLY.
    OWL argues enrichment pipeline breaks silently on gaps.
    Proposed hybrid: raw files = FLAG_ONLY, materialized view = ghost bars
    with is_ghost=True flag. Gates see ghosts as SKIP not PASS/FAIL.
  advisors_say: "OWL wants ghosts. GPT cites existing FLAG_ONLY. BOAR neutral."
  recommendation: |
    Amend ICT_DATA_CONTRACT to allow FLAGGED ghost bars in materialized
    views while preserving FLAG_ONLY in raw storage. This reconciles both
    positions without violating the spirit of the constitution.

SOVEREIGN_CALL_3:
  question: "Budget allocation: pay for Polygon ongoing, or IBKR-only for live?"
  context: |
    OWL proposes secondary audit feed (Polygon) with divergence guard.
    Adds monthly cost + second ingestion pipeline.
    All agree IBKR is primary authority for live.
  recommendation: |
    DEFER Polygon to Phase 2. For Phase 1 (EURUSD only), IBKR alone
    is sufficient for live data. The seam reconciliation provides
    initial cross-source validation. Revisit when multi-pair goes live.
  budget_impact: "None for Phase 1. Polygon subscription (~$200/mo) for Phase 2."
```

---

## 6. RECOMMENDED BUILD SEQUENCE

```yaml
PHASE_1_IMMEDIATE:
  goal: "Asia Range Scalp gets real data"
  steps:
    1: "Audit NEX Dukascopy parquet files (EURUSD 1m)"
    2: "Build River Writer — IBKR reqHistoricalData → parquet (1m, EURUSD)"
    3: "Backfill gap: Jan 27 → now from IBKR (~30 days of 5m available)"
    4: "Build DuckDB query layer (replaces SQLite RiverReader)"
    5: "Seam reconciliation: validate Dukascopy-IBKR overlap"
    6: "G signs seam attestation"
    7: "Wire enrichment pipeline to new River (parquet → DuckDB → DataFrame)"
    8: "Live streaming: IBKR 1m bars appended to daily parquet"
  estimate: "3-5 days build, 1 day audit, 1 day validation"

PHASE_2_MULTI_PAIR:
  goal: "All 6 pairs, secondary audit feed"
  steps:
    - "Extend to GBPUSD, USDJPY, AUDUSD, NZDUSD, USDCAD"
    - "Polygon audit feed + divergence guard"
    - "River State Bead integration with Bead Field"
  timing: "After Phase 1 stable, operator confidence established"
```

---

## 7. ARCHITECTURE SKETCH (Phase 1)

```
┌─────────────┐     ┌──────────────────────┐     ┌─────────────────┐
│  Dukascopy   │────▶│  Immutable Parquet    │◀────│  IBKR Gateway   │
│  (history)   │     │  ~/phoenix/river/     │     │  (live 1m bars) │
│  5yr 1m bars │     │  pair/year/month/     │     │  reqHistorical  │
└─────────────┘     │  EURUSD/2026/02.pqt   │     └─────────────────┘
                    │                        │
                    │  Columns:              │
                    │   timestamp (WT)       │
                    │   open, high, low,     │
                    │   close, volume        │
                    │   source               │
                    │   knowledge_time (KT)  │
                    │   bar_hash             │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │  DuckDB Query Layer     │
                    │  (read-only views)      │
                    │                        │
                    │  SELECT * FROM          │
                    │  read_parquet(glob)     │
                    │  WHERE ...             │
                    │                        │
                    │  Derived TFs:          │
                    │  5m, 15m, 1H, 4H, D   │
                    │  (aggregated on read)  │
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼─────────────┐
                    │  Enrichment L1-L7       │
                    │  (existing pipeline)    │
                    │                        │
                    │  market_state_builder   │
                    │  → MarketState          │
                    │  → GateEvaluator        │
                    │  → Asia Scalp Engine    │
                    └────────────────────────┘
```

---

## 8. FINAL NOTE

```yaml
meta_observation: |
  The advisors converged more strongly than expected. On all 5 questions,
  there is no fundamental disagreement — only differences in how far to
  go in Phase 1 vs Phase 2. The core architecture (immutable parquet,
  DuckDB query, 1m base resolution, dual source with seam, formal
  integrity layer) has unanimous support.

  The two genuinely novel contributions are:
  1. OWL's bitemporal requirement (knowledge_time) — adopt immediately
  2. OWL's ghost bar concept — needs sovereign call to amend constitution

  The rest is execution. The design is clear. The advisors agree.
  CTO + G can lock and build.
```

---

*RIVER_SYNTHESIS v1.0 — RECOMMENDATION ONLY. CTO + G lock decisions.*
