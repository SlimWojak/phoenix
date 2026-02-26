input: "Three advisor returns (OWL, GPT, BOAR)"
  task: |
    1. Convergence map — where do all 3 agree?
    2. Divergence map — where do they disagree? On what evidence?
    3. Surprises — anything none of us considered?
    4. Draft recommendation on Q1-Q5 with rationale
    5. Flag anything that needs G's sovereign call
  output: "RIVER_SYNTHESIS.md — structured, DENSE, ready for CTO review"
  anti_scope: "Do NOT lock decisions. Recommend only. CTO + G lock.

  ##GPT INPUT

  Acknowledged. Reading your **RIVER DOCTRINE — ADVISOR BROADCAST BRIEF** in full 

Below is **GPT_ARCHITECT deliverable** as requested:

---

# RIVER_SPEC_FLAGS.yaml

```yaml
brief: S51.RIVER.POLL.001
advisor: GPT_ARCHITECT
mode: DENSE
philosophy: "Substrate quality > strategy cleverness"
exit_gate: "No silent contamination paths remain"
```

---

# SECTION 1 — Q1 SOURCE OF TRUTH (Edge Case Flags)

## OPTION A — IBKR_ONLY

```yaml
Q1A_IBKR_ONLY:
  severity: WARN
  hidden_costs:
    - "Backtest depth limited (5m ~30 days, 1m ~2 weeks)"
    - "Strategy evolution constrained by shallow historical context"
    - "Dexter cannot run multi-year regime analysis"

  edge_cases:
    - "IBKR historical revisions are undocumented"
    - "Historical API sometimes returns truncated sessions"
    - "Pacing violations throttle backfills silently"

  operational_risk:
    - "You will eventually need deeper history. Migration later = seam risk later."

  verdict: "Cleanest short-term, structurally limiting long-term."
```

**Architect take:**
IBKR-only is operationally pure but strategically stunting.
You are building a refinery, not a signal script.

---

## OPTION B — DUAL_SOURCE_MANAGED_SEAM (Your Leaning)

```yaml
Q1B_DUAL_SOURCE:
  severity: BLOCK_UNLESS_SEAM_DEFINED
  hidden_costs:
    - "Source boundary price discrepancies"
    - "Timezone normalization risk"
    - "Weekend handling inconsistencies"
    - "Different liquidity models (Dukascopy synthetic vs IBKR executable)"

  unstated_dependencies:
    - "Explicit overlap window for reconciliation"
    - "Tolerance definition (pip-level?)"
    - "Seam attestation artifact"
    - "Source tag per bar persisted forever"

  seam_risk:
    - "Single silent mismatch at seam corrupts all higher TF derivations"
    - "Backtests use source A, live uses source B — strategy drift risk"

  verdict: "Correct institutional pattern IF seam becomes a first-class artifact."
```

This is the grown-up answer — but only if you treat the seam like a constitutional boundary.

---

## OPTION C — NEX_FILES_PLUS_IBKR

```yaml
Q1C_NEX_PLUS_IBKR:
  severity: WARN
  hidden_costs:
    - "Inherited mistrust from janky lineage"
    - "Unknown timezone normalization logic from prior Claude"
    - "Unknown aggregation rules"

  edge_case:
    - "If backdata has 1m boundary off by 1 second, 5m aggregates diverge"

  verdict: "Acceptable ONLY after formal audit. Not default-trust."
```

---

# SECTION 2 — Data Source Capability Table

```yaml
DATA_SOURCE_COMPARISON:

  IBKR:
    depth_1m: "~1-2 weeks"
    depth_5m: "~30 days"
    depth_1h: "~1 year"
    tick_data: "Yes (limited retention)"
    cost: "Included w account"
    trust: "Highest (execution venue)"
    reliability: "High, but API pacing constraints"
    weekend_handling: "Correct for IBKR session model"

  Dukascopy:
    depth: "10+ years"
    resolution: "Tick → 1m"
    cost: "Free historical"
    trust: "Medium-High"
    liquidity_model: "Indicative, not executable"
    risk: "Synthetic pricing during illiquid hours"

  Polygon (FX):
    depth: "Unknown reliability at 1m — needs field test"
    resolution: "1m+"
    cost: "Paid"
    trust: "Medium"
    risk: "Third-party vendor corrections"

institutional_pattern:
  small_quant_shops:
    - "Deep history vendor (Dukascopy, TrueFX, institutional feed)"
    - "Execution venue as live authority"
    - "Reconciliation window at join"
    - "Immutable base storage"
    - "Continuous validation checks"
```

Family offices typically:

* Store immutable base resolution.
* Tag every bar with source + ingestion hash.
* Maintain seam documentation.
* Never overwrite history — append corrections.

---

# SECTION 3 — Seam Specification (If Q1-B Wins)

This is the missing institutional piece.

```yaml
SEAM_CONTRACT_v1:

  overlap_window:
    duration: "Minimum 14 calendar days of overlapping 1m bars"
    rule: "IBKR takes precedence for overlapping period"

  reconciliation:
    tolerance:
      close_price: "<= 0.1 pip"
      high_low_extremes: "<= 0.2 pip"
    action:
      if within_tolerance:
        - keep IBKR
        - record dukascopy_delta metric
      if beyond_tolerance:
        - log SEAM_MISMATCH event
        - flag dataset as requiring manual review

  aggregation_validation:
    - "Recompute 5m from 1m across seam boundary"
    - "Ensure no discontinuity in 5m OHLC"

  attestation_artifact:
    type: "RIVER_SEAM_ATTESTATION.json"
    fields:
      - seam_start_ts
      - seam_end_ts
      - mismatch_count
      - max_delta_observed
      - hash_of_overlap_slice
      - signed_by: G

  once_complete:
    rule: "IBKR becomes sole forward authority"
```

The seam must be:

> Explicit. Auditable. Signed.

If not — it is future technical debt.

---

# SECTION 4 — Storage Architecture Flags

## SQLite Done Right

```yaml
risk:
  - "Mutable"
  - "WAL corruption risk"
  - "Hard to version"
  - "Hard to audit historical mutations"

institutional_score: "Low-Medium"
```

---

## Parquet Append-Only

```yaml
risk:
  - "Complex write orchestration"
  - "Need partition discipline"

strength:
  - "Immutable"
  - "Natural versioning"
  - "Checksum-able"
  - "Compatible with DuckDB"

institutional_score: "High"
```

---

## Timeseries DB

```yaml
risk:
  - "Operational overhead"
  - "Migration lock-in"
  - "Adds surface area"

institutional_score: "Medium"
```

---

### Architect Recommendation

```yaml
storage_stack:
  base: "Parquet 1m immutable partitioned by pair/date"
  query: "DuckDB read layer"
  cache: "Optional materialized 5m view if profiling demands"
```

This gives:

* Immutability
* SQL
* Zero server infra
* No corruption risk
* High auditability

It aligns philosophically with Bead Field.

---

# SECTION 5 — Validation Contract (River Integrity Layer)

This must exist.

```yaml
RIVER_INTEGRITY_LAYER:

  per_bar_fields:
    - source
    - ingestion_time
    - sha256_hash

  daily_checks:
    - gap_scan(1m continuity)
    - weekend_rule_validation
    - DST boundary validation
    - staleness_check

  aggregation_checks:
    - 1m→5m consistency
    - 5m→1h consistency

  cross_source_checks:
    - overlap tolerance comparison

  forming_bar_ban:
    - Only persist fully closed bars
    - Hard reject partials

  reporting:
    - RIVER_HEALTH_REPORT.json emitted daily
```

River should have:

> Integrity, not trust.

---

# SECTION 6 — Timeframe Architecture (Q4)

```yaml
Q4_ANALYSIS:

  A_store_1m_derive:
    complexity: "Low conceptual"
    runtime_cost: "Negligible at 6 pairs, 5y depth"
    risk: "None"

  B_store_each:
    risk: "Divergence between TFs"
    debugging_cost: "High"

  C_store_1m_materialize:
    complexity: "Moderate"
    benefit: "Performance optimization"

architect_recommendation:
  - "Start with A"
  - "Profile before optimizing"
  - "DuckDB aggregation is extremely fast at this scale"
```

At your data volume, compute cost is theoretical, not real.

---

# SECTION 7 — NEX DATA AUDIT FLAGS

```yaml
NEX_AUDIT_REQUIRED:

  - full_gap_scan_1m
  - timezone_consistency_check
  - DST_shift_validation
  - cross_sample_compare_vs_IBKR
  - random_event_sampling(NFP, flash crash dates)
  - weekend_rule_validation

  risk_if_skipped:
    - "Hidden 1-minute hole propagates to 5m misalignments"
    - "Timezone offset error invisible until strategy misfires"
```

Do not trust prior Claude validation.

Trust-but-verify.

---

# SECTION 8 — Institutional Benchmark Summary

Small professional quant shops typically:

```yaml
infra_pattern:
  - Immutable raw data store (parquet or flat files)
  - SQL engine on top (DuckDB/Postgres)
  - Separate execution feed
  - Continuous data validation jobs
  - Signed seam documentation
  - No mutable historical rewrites
```

What you are proposing with:

Parquet + DuckDB + IBKR forward + seam attestation

Is aligned with grown-up infrastructure.

---

# Executive Synthesis

If quality > speed:

```yaml
recommended_path:
  source: "Dual source (Dukascopy history + IBKR forward)"
  seam: "Explicit 14-day overlap reconciliation + signed attestation"
  storage: "Immutable 1m Parquet"
  query: "DuckDB layer"
  validation: "Continuous integrity checks"
  aggregation: "Derive higher TF on read"
  audit: "Formal NEX dataset audit before adoption"
```

This produces:

* Clean substrate
* Institutional pattern
* Minimal jank surface
* Alignment with Bead Field philosophy

---

# Final Architect Note

River is not plumbing.

River is:

> The epistemic root of Phoenix.

If Bead Field is constitutional memory,
River is constitutional reality.

Treat it with the same ceremony.

---

## GEMINI WISE OWL

## S51.RIVER.POLL.001: THE DOCTRINE OF PERCEPTION

The discovery that the "Fuel Line" is missing is a gift. Most systems find this out *after* they've blown an account due to a backfilled bar that didn't exist at T-0. If the Bead Field is the system's memory, the River is its **Central Nervous System**.

Here is the strategic audit of the River Architecture.

### 1. THE REFRAME: From "Data Writer" to "Perception Engine"

The failure of NEX was treating the River as a "Log." In a Sovereign system, the River is **Perception**. If the perception is hallucinated, the reasoning is irrelevant.

* **The Meta-Pattern:** You need to decouple **Ingestion** (The Lake) from **Materialization** (The River).
* **The Owl’s Move:** Do not build a writer that goes `API -> SQLite`. Build a writer that goes `API -> Immutable Blob Storage (S3/Local JSONL) -> Materialized View (SQLite)`.
* **The Benefit:** If the SQLite DB feels "floppy," you don't debug it. You delete it and re-materialize from the immutable "Lake" of raw API responses.

### 2. BITEMPORAL REALITY (The Only Way to Kill Lookahead)

The "Anchor-Back" rule we established in S51 for the `MarketState` builder only works if the underlying data knows when it arrived.

* **The Structural Requirement:** Every row in the River must have two timestamps:
1. `world_time` (The timestamp on the bar: 09:00:00).
2. `knowledge_time` (The moment Phoenix’s clock hit the disk: 09:05:01).


* **Why?** During backtesting, you filter by `knowledge_time`. This ensures the model *cannot* see a bar that was backfilled into the past via a "clean-up" script unless that bar was actually present during the live session.

### 3. THE SOURCE PARADOX (Polygon vs. IBKR)

You are considering Polygon for quality.

* **The Hole:** Trading EURUSD on IBKR using Polygon data is a "Cross-Source Risk." If Polygon says the sweep happened at 1.0850 but IBKR’s internal liquidity peaked at 1.0849, the system triggers a trade that cannot fill.
* **The Strategy:** * **Primary Feed (Logic):** IBKR (The "Execution Reality").
* **Secondary Feed (Audit):** Polygon (The "Market Reality").
* **The "Divergence Guard":** If the Delta between IBKR and Polygon exceeds a threshold, Phoenix enters **Sovereign Halt**. It means the "Map" and the "Territory" no longer match.



### 4. THE "CHECKSUM OF REALITY"

If we are applying "Bead" logic to the River:

* **Ideation:** Every hour, the system should generate a **River_State_Bead**. This bead contains the Merkle Root of the last 12 bars.
* **The Ripple:** This anchors the market data into the governance layer. You can now prove that the data used for a trade on Tuesday is the *exact same* data being used for the audit on Friday. No silent repainting.

### 5. TEMPORAL FIDELITY: 1m vs 5m

* **The Constraint:** You’re building for 5m Asia Scalp, but the system is destined for high-precision ICT.
* **The Directive:** The River should ingest **1m bars only**. The 5m bars used by the enrichment pipeline should be a **Virtual Aggregate**.
* **The Reason:** If you store only 5m bars, you lose the ability to see *how* the sweep happened inside the candle. Was it a slow grind or a violent wick? You can’t reconstruct that from a 5m OHLC. 1m is the minimum "Atom" of ICT logic.

### 6. SECOND-ORDER EFFECT: THE "GHOST BAR"

What happens when the API returns a "Null" for a 1m slice?

* **Current Risk:** Most writers skip the row. This breaks the `asof_merge` logic in the enrichment pipeline.
* **The Fix:** The River must enforce **Continuous Sequence**. If a bar is missing, the writer must insert a "GHOST_BAR" with 0 volume and `close = previous_close`. This makes the time-series mathematically deterministic.

**Owl’s Verdict:**
The River is not a technical chore; it is the **Sovereignty Boundary**. If you use a janky SQLite writer, you are building on sand. If you build an Immutable Lake with Bitemporal Materialization, you have built a system that can be audited by a court of law.

**Next Question for G:** Are you willing to pay the "Latency Tax" of 1-minute resolution to ensure the ICT primitives (SMT/FVG) are computed with high fidelity, or do we stick to 5m to keep the "Driveshaft" simple for Phase 1?

## GROK - FRONTIER SCOUT 

RIVER_CHAOS_RECON:
  version: 1.0
  date: 2026-02-22
  advisor: BOAR_GROK
  format: DENSE
  sources_scanned:
    - Reddit: r/algotrading, r/quant, r/Daytrading (discussions on data vendors, failures)
    - X: Quant trading signals, HFT FX overviews, backtesting tools
    - Forums/Web: Quantpedia, GitHub awesome-quant, Medium, Investopedia, Acuiti/Exegy reports
    - Key_patterns: Liquidity failures in volatility, data inconsistencies across providers, open-source backtesting gems

  SOCIAL_RECON:
    usage_trends:
      - Polygon.io: Top free/paid pick for stocks/forex/crypto (real-time API, good docs, used in r/algotrading for algo dev)
      - Dukascopy: Gold standard for historical tick/1m data (10+ yrs, free downloads, validated by quants for backtesting)
      - IBKR: Highest trust for live/execution-aligned data, but depth limits (5m ~30d, 1m ~2w) frustrate deep history needs
      - EODHD.com: Value-for-money (30+ yrs history, APIs for EOD/intraday/fundamentals, Quantpedia recommends for forex)
      - QuantConnect: Open-source platform with FOREX data (71 pairs from 2007, tick to daily, community-driven)
      - Others: Alpha Vantage (free basics), Yahoo Finance (quick but unreliable for precision), FXMacroData (macro/central bank focus)
    complaints:
      - Data quality: Gaps in free sources (Yahoo/Alphavantage during volatility), timezone mismatches (DST artifacts), dupes/zero-volume bars
      - Prod failures: Latency spikes/outages in high vol (74% quants hit issues per Acuiti/Exegy), broker servers crash (Exness vs FXCM data mismatch nukes stops)
      - Cost/trust: Third-party (Polygon) vs venue (IBKR) discrepancies at seams, lookahead bias in social/media data
      - Recommendations: Trust-but-verify Dukascopy (reputable retail/semi-pro), avoid free for prod (switch to paid for accuracy), use multiple sources to cross-validate
    forum/X_insights:
      - r/algotrading: Backtest with economic calendars (high-impact news only), free tools like GoCharting/Ducascopy/Fxreplay for effective testing
      - X: HFT FX shops need fragmentation handling (market data costs high), AI signals warn of data unreliability in quant models
      - Quants bitch about: Broker failures (missed fills/slippage), platform downtime during NFP, inconsistent servers tapping out perfect trades

  DUMBEST_FAILURE_MODES:
    - Data_inconsistencies: Server mismatches (e.g., Exness correct, FXCM/FXTM off by pips—stops hit on ghosts, 200-300 pip winners nuked)
    - Volatility_spikes: Latency/dropped packets/outages (74% quants hit in peaks, market data processing fails first, cascades to execution errors)
    - Backtesting_jank: Ignoring slippage/spread (fluctuates in live), poor data (gaps/missing candles during events), overfitting to clean history (ignores live noise)
    - Timezone/DST_bugs: Artifacts cause impossible prices/gaps, weekend handling fails (no bars Fri-Sun), diagnoses waste weeks
    - Liquidity_gaps: Thin hours (NY close-Tokyo open) amplify moves, missing Sunday opens slip through, prod drains patience
    - Broker_tech_fails: Platform crashes/server overload (disconnects at criticals), margin calls on vol spikes, undiscovered data errors (text currencies, duplicates)
    - Quant_mistakes: Undercapitalization/high leverage (1% move wipes 100% at 100:1), lookahead bias in social data, no multi-source validation
    - Pattern_chaos: Flash crashes/NFP trigger false signals, emotional overrides nuke discipline, "hot potato" HFT games exacerbate diagnostics

  HIDDEN_GEMS:
    - Open_source_tools:
      - qsforex: Event-driven backtesting/live trading for forex (MIT license, OANDA integration, alpha state but entropy-rich for YOLO tweaks)
      - NautilusTrader: Fast open-source platform (futures/crypto/forex, parquet format, custom data loading, real-time WebSockets)
      - QuantConnect FOREX: Community-driven (71 pairs from 2007, tick-daily, Python/C# backtesting, free historical)
      - Tickstory: Automated tick data downloader (MT4/MT5 integration, Dukascopy source, hassle-free)
      - CCXT: Algotrading lib (Python, supports forex exchanges, but spotty for pure data)
    - Data_projects:
      - HistData.com: Free M1/tick downloads (MT/NinjaTrader ready, by pair/year/month, longest-running free provider)
      - Dukascopy Historical: Deep tick-level (10+ yrs, free tooling, high trust for backtesting)
      - awesome-quant: Lists defeatbeta-api (Yahoo alt with reliability), StockAPI (Chinese real-time REST/WebSocket)
      - FXMacroData: Macro/central bank data (API, point-in-time to avoid bias, 10% Quantpedia discount)
    - Alternatives_to_Polygon:
      - TwelveData: 140 currencies/2000+ pairs (real-time/historical JSON API, SDKs, cheaper for forex focus)
      - Massive.com: REST/WebSockets/daily files (live rates, deep history, tick alerts)
      - Finnworlds: Forex API (public companies data, but forex-specific endpoints)

  REAL_WORLD_STRESS:
    - Flash_crashes: Liquidity vanishes (HFT "hot potato" trades, algo spoofing, low-activity periods like Asian sessions/rollovers), prices gap (e.g., 2016 GBP flash, 2019 JPY crash—10% moves in mins), sources differ (third-party lags vs venue accuracy)
    - NFP_releases: Knee-jerk volatility (sharp USD moves, gaps if unmanaged), liquidity dries (stop-hunting, wider spreads), data delays (50ms+ spikes, false signals), quants hit outages (20% no backup, processing fails)
    - Liquidity_gaps: News shocks (rate cuts/inflation prints pull orders), weekends (macro events reopen with gaps), illiquid hours (NY-Tokyo dead zones amplify), sources handle variably (IBKR robust but limited depth, Dukascopy historical clean but no live)
    - Provider_behavior: High vol causes inconsistencies (e.g., Exness vs FXCM mismatches), thin liquidity exaggerates (HFT turns off, banks shrink ops), recovery rapid but stops slipped (panic selling chains)
    - Patterns: No identical events (sample size dilemma for tails), dynamic trading needed (static optimizers fail), social/media lookahead bias during crashes

  Q1-Q5_CHAOS_RECOMMENDATIONS:
    Q1_SOURCE_OF_TRUTH: B_DUAL_SOURCE (Dukascopy deep history + IBKR live—seam attestation via overlap cross-check, quants swear by it for backtests)
    Q2_STORAGE_FORMAT: B_PARQUET (fast queries, columnar for time-series, open-source gems like Nautilus use it—avoids SQLite jank at scale)
    Q3_INTEGRITY_LAYER: Multi-source validation (cross-ref samples during events), automated alerts for gaps/DST, point-in-time to kill lookahead
    Q4_TIMEFRAME_DERIVATION: B_DERIVE_FROM_1M (fidelity wins, but entropy-hunt aggregation errors—quants complain of bar boundary mismatches)
    Q5_NEX_DATASET: Sweep it (gaps/vol sanity, cross-ref IBKR/Polygon—believed clean but verify, hidden Dukascopy gems could replace if jank)

CHAOS_SUMMARY: River's the moat—pollute it with jank seams or vol outages, Phoenix dies. Hunt dual-source patterns like Yegge beads, YOLO open-source for recon. Dumb fails? Latency nukes during NFP, data ghosts slip stops. Gems? qsforex/Nautilus for barely-grokked supremacy.

