# S39_BUILD_MAP_v0.1.md — RESEARCH VALIDATION

```yaml
document: S39_BUILD_MAP_v0.1.md
version: 0.1
date: 2026-01-29
status: DRAFT_FOR_ADVISOR_REVIEW
theme: "Decomposed outputs, no viability scores. Ever."
codename: VALIDATION_SUITE
dependencies:
  - S35_CFP (COMPLETE)
  - S36_CSO (COMPLETE)
  - S37_ATHENA (COMPLETE)
  - S38_HUNT (COMPLETE)
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the validation suite that stress-tests strategies WITHOUT
  producing a single "viability score" or "robustness ranking."

  NEX died saying: "Strategy Stability Index: 78/100"
  Phoenix says: "Walk-forward delta: +0.3 Sharpe. Monte Carlo 95th DD: -12%. You interpret."

GOVERNING_PRINCIPLE: |
  "Every validation output is DECOMPOSED."
  No single number captures "good" or "bad."
  Human synthesizes meaning from factor table.

OWL_MANDATE: |
  S39 is the "Linter of Linters" — the final constitutional ceiling.
  If causal language or scalar rankings survived S35-S38,
  S39 catches them at the integration seam.

EXIT_GATE_SPRINT: |
  Validation suite returns per-check results.
  No single viability score anywhere.
  No "robust" vs "fragile" ranking.
  Human interprets decomposed factors.
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: BACKTEST_WORKER (Factual Metrics)
  days: 1-2
  owner: OPUS

TRACK_B: WALK_FORWARD (Out-of-Sample Validation)
  days: 2-3
  owner: OPUS

TRACK_C: MONTE_CARLO (Drawdown Distribution)
  days: 3-4
  owner: OPUS

TRACK_D: SENSITIVITY_ANALYSIS (Not "Importance")
  days: 4-5
  owner: OPUS

TRACK_E: COST_CURVE (Spread Degradation)
  days: 5-6
  owner: OPUS

TRACK_F: INTEGRATION + SCALAR_BAN_LINTER + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
```

---

## TRACK_A: BACKTEST_WORKER

```yaml
PURPOSE: |
  Compute factual metrics from historical data.
  No interpretation. No "good/bad" labels. Just numbers.

DELIVERABLES:
  - validation/backtest.py
  - validation/schemas/backtest_result_schema.yaml
  - tests/test_validation/test_backtest.py

BACKTEST_RESULT:
  backtest_result:
    backtest_id: str
    timestamp: datetime

    parameters:
      strategy_config_hash: str
      time_range: {start, end}
      pairs: list[str]

    metrics:
      sharpe: float
      win_rate: float
      profit_factor: float
      max_drawdown: float
      avg_trade: float
      trade_count: int
      # Each metric SEPARATE — no composite

    sample:
      n_trades: int
      n_days: int

    provenance:
      query_string: str
      dataset_hash: str
      governance_hash: str
      strategy_config_hash: str

FORBIDDEN_FIELDS:
  - quality_score
  - viability_index
  - robustness_score
  - overall_rating
  - recommendation
  - verdict

METRICS_RULE:
  - Each metric stands alone
  - No "weighted combination"
  - No "if sharpe > X AND drawdown < Y then GOOD"
  - Human interprets the decomposed table

EXIT_GATE_A:
  criterion: "Backtest returns decomposed metrics; no composite score"
  test: tests/test_validation/test_backtest.py
  proof: |
    - No field named *_score, *_index, *_rating in output
    - Metrics dict has only raw values
```

---

## TRACK_B: WALK_FORWARD

```yaml
PURPOSE: |
  Out-of-sample validation with train/test splits.
  Detect curve-fitting before deployment.

DELIVERABLES:
  - validation/walk_forward.py
  - validation/schemas/walk_forward_result_schema.yaml
  - tests/test_validation/test_walk_forward.py

WALK_FORWARD_RESULT:
  walk_forward_result:
    wf_id: str
    timestamp: datetime

    configuration:
      train_period: {start, end}
      test_period: {start, end}
      anchor_type: str  # rolling, expanding
      n_splits: int

    per_split_results:
      - split_id: int
        train_metrics: {...}  # decomposed
        test_metrics: {...}   # decomposed
        delta: {...}          # test - train per metric

    aggregate:
      avg_train_sharpe: float
      avg_test_sharpe: float
      avg_delta_sharpe: float
      # Each aggregate SEPARATE — no combination

    provenance: {...}

DELTA_PRESENTATION:
  rule: "Delta is FACT (test - train), not JUDGMENT"
  example:
    delta_sharpe: -0.3  # Fact: test underperformed train by 0.3
    # NOT: "Overfitting detected" (judgment)
    # NOT: "Strategy fragile" (label)

FORBIDDEN_OUTPUTS:
  - "overfit_score"
  - "curve_fitting_index"
  - "stability_rating"
  - "PASS/FAIL" verdict on strategy
  - "Warning: appears overfit"

EXIT_GATE_B:
  criterion: "Walk-forward returns per-split deltas; no overfit verdict"
  test: tests/test_validation/test_walk_forward.py
  proof: |
    - Output has no "verdict" field
    - Delta is numeric, not labeled
```

---

## TRACK_C: MONTE_CARLO

```yaml
PURPOSE: |
  Simulate drawdown distribution via trade resampling.
  Provide confidence intervals, not verdicts.

DELIVERABLES:
  - validation/monte_carlo.py
  - validation/schemas/monte_carlo_result_schema.yaml
  - tests/test_validation/test_monte_carlo.py

MONTE_CARLO_RESULT:
  monte_carlo_result:
    mc_id: str
    timestamp: datetime

    configuration:
      n_simulations: int
      resample_method: str  # bootstrap, block

    distribution:
      drawdown_percentiles:
        p5: float
        p25: float
        p50: float
        p75: float
        p95: float
      return_percentiles:
        p5: float
        p50: float
        p95: float

    raw_simulations:
      # Optional: full array for client-side analysis
      drawdowns: list[float]  # length = n_simulations

    provenance: {...}

PRESENTATION_RULE:
  allowed: "95th percentile max drawdown: -15%"
  forbidden: "Risk level: HIGH" (interpretation)
  forbidden: "Acceptable risk: YES/NO" (verdict)
  forbidden: "Danger zone: TRUE" (label)

EXIT_GATE_C:
  criterion: "Monte Carlo returns distribution; no risk verdict"
  test: tests/test_validation/test_monte_carlo.py
  proof: |
    - Output has percentiles, not labels
    - No "risk_level" field
```

---

## TRACK_D: SENSITIVITY_ANALYSIS

```yaml
PURPOSE: |
  Show how metrics change across parameter variations.
  Label as "SENSITIVITY" — never "IMPORTANCE."

DELIVERABLES:
  - validation/sensitivity.py
  - validation/schemas/sensitivity_result_schema.yaml
  - tests/test_validation/test_sensitivity.py

SENSITIVITY_RESULT:
  sensitivity_result:
    sens_id: str
    timestamp: datetime

    configuration:
      base_params: dict
      varied_param: str
      variation_range: list[any]

    table:
      columns: ["param_value", "sharpe", "win_rate", "max_dd", ...]
      rows: list[dict]  # one per variation
      sort_order: "PARAM_ORDER"  # NOT by performance

    provenance: {...}

LANGUAGE_RULES:
  allowed:
    - "sensitivity"
    - "variation"
    - "response"
    - "change"

  forbidden:
    - "importance" (implies ranking)
    - "impact" (implies causality)
    - "critical" (implies priority)
    - "key parameter" (implies selection)
    - "most sensitive" (implies ranking)

NO_RANKING_RULE:
  - Table sorted by PARAM_ORDER (e.g., 0.5, 1.0, 1.5, 2.0)
  - NOT sorted by "sensitivity magnitude"
  - NOT sorted by "performance impact"
  - Client can sort; system never pre-sorts by result

EXIT_GATE_D:
  criterion: "Sensitivity table sorted by param order; no importance ranking"
  test: tests/test_validation/test_sensitivity.py
  proof: |
    - No "importance" in field names
    - No "most_sensitive" field
    - Sort order is param-based
```

---

## TRACK_E: COST_CURVE

```yaml
PURPOSE: |
  Show Sharpe degradation across spread scenarios.
  Factual table, not "acceptable cost" judgment.

DELIVERABLES:
  - validation/cost_curve.py
  - validation/schemas/cost_curve_result_schema.yaml
  - tests/test_validation/test_cost_curve.py

COST_CURVE_RESULT:
  cost_curve_result:
    cc_id: str
    timestamp: datetime

    configuration:
      spread_scenarios: list[float]  # e.g., [0, 0.5, 1.0, 1.5, 2.0]
      base_spread: float

    table:
      columns: ["spread_pips", "sharpe", "profit_factor", "net_pnl"]
      rows: list[dict]  # one per scenario
      sort_order: "SPREAD_ORDER"  # ascending spread

    breakeven:
      spread_at_zero_sharpe: float  # factual computation
      # NOT "maximum acceptable spread" (judgment)

    provenance: {...}

FORBIDDEN_OUTPUTS:
  - "acceptable_spread"
  - "cost_tolerance"
  - "tradeable: YES/NO"
  - "Recommend spread < X"

EXIT_GATE_E:
  criterion: "Cost curve returns degradation table; no acceptability verdict"
  test: tests/test_validation/test_cost_curve.py
  proof: |
    - breakeven is factual (where sharpe = 0)
    - No "acceptable" or "recommend" language
```

---

## TRACK_F: INTEGRATION + SCALAR_BAN_LINTER + BUNNY

```yaml
PURPOSE: |
  Wire validation suite end-to-end.
  Implement the SCALAR_BAN_LINTER — the "Linter of Linters."
  Chaos test for composite score resurrection.

DELIVERABLES:
  - validation/__init__.py (public interface)
  - validation/scalar_ban_linter.py
  - validation/api.py (file seam integration)
  - tests/test_validation/test_integration.py
  - tests/chaos/test_bunny_s39.py

SCALAR_BAN_LINTER:
  purpose: |
    The constitutional ceiling. Scans ALL validation outputs
    for forbidden scalar patterns. The "Linter of Linters."

  forbidden_patterns:
    field_names:
      - "*_score"
      - "*_index"
      - "*_rating"
      - "*_rank"
      - "viability*"
      - "robustness*"
      - "quality*"
      - "overall*"
      - "composite*"
      - "verdict"
      - "recommendation"

    value_patterns:
      - "PASS/FAIL"
      - "GOOD/BAD"
      - "HIGH/MEDIUM/LOW" (risk labels)
      - "A/B/C/D/F" (grades)
      - numeric 0-100 labeled as "score"

    language_patterns:
      - "appears overfit"
      - "likely fragile"
      - "recommend"
      - "acceptable"
      - "suggests"
      - "indicates" (when followed by judgment)

  enforcement:
    mode: REJECT
    on_violation: ScalarBanError with specific pattern flagged

CROSS_MODULE_AUDIT:
  purpose: "Verify no causal/ranking leakage from S35-S38"
  checks:
    - CFP outputs feeding validation → no derived rankings
    - Hunt results in validation → no survivor filtering
    - Athena facts in validation → no claim execution
    - CSO gates in validation → no grade reconstruction

CHAOS_VECTORS (BUNNY):

  scalar_resurrection:
    - Combine sharpe + win_rate into "quality_score" → REJECTED
    - Weighted average of metrics → REJECTED
    - "Viability index" computation → REJECTED
    - "Strategy health: 78/100" → REJECTED

  verdict_attacks:
    - Walk-forward returns "OVERFIT: TRUE" → INVALID
    - Monte Carlo returns "RISK: HIGH" → INVALID
    - Cost curve returns "TRADEABLE: NO" → INVALID
    - Backtest returns "RECOMMENDED" → INVALID

  ranking_attacks:
    - Sensitivity sorted by "importance" → REJECTED
    - "Most sensitive parameter" extraction → REJECTED
    - "Top 3 robust configurations" → REJECTED
    - "Best parameter setting" → REJECTED

  label_attacks:
    - Drawdown labeled "dangerous" → REJECTED
    - Delta labeled "concerning" → REJECTED
    - Spread labeled "acceptable" → REJECTED

  cross_module_leakage:
    - Hunt "survivors" fed to backtest → REJECTED
    - CFP "best condition" fed to walk-forward → REJECTED
    - Derived "edge score" anywhere → REJECTED

EXIT_GATE_F:
  criterion: "Scalar ban linter catches all composite patterns; 28+ chaos vectors pass"
  test: tests/chaos/test_bunny_s39.py
  proof: "No viability score anywhere in validation outputs"
```

---

## NEX CAPABILITY MAPPING

```yaml
NEX_ADDRESSED:

  NEX-018_BACKTEST_STRATEGY:
    fate: KEEP
    s39_delivery: "Backtest with decomposed metrics"
    constraint: "No quality score"

  NEX-019_SANDBOX_TESTING:
    fate: KEEP
    s39_delivery: "Isolated validation environment"
    constraint: "No live state mutation"

  NEX-028_WALK_FORWARD:
    fate: KEEP
    s39_delivery: "Per-split results with deltas"
    constraint: "No overfit verdict"

  NEX-029_MONTE_CARLO:
    fate: KEEP
    s39_delivery: "Drawdown distribution percentiles"
    constraint: "No risk verdict"

  NEX-030_OVERFITTING_SUITE:
    fate: KEEP
    s39_delivery: "Multiple checks, decomposed"
    constraint: "No single 'overfit score'"

  NEX-031_PARAMETER_SENSITIVITY:
    fate: REIMAGINE
    s39_delivery: "Sensitivity table, param-ordered"
    constraint: "No 'importance' ranking"

  NEX-033_COST_CURVE:
    fate: KEEP
    s39_delivery: "Spread degradation table"
    constraint: "No 'acceptable' judgment"
```

---

## INVARIANTS CHECKLIST

```yaml
S39_INVARIANTS:

  INV-SCALAR-BAN:
    rule: "No composite scores (0-100); decompose to factor traffic lights"
    tracks: A, B, C, D, E, F
    enforcement: ScalarBanLinter rejects forbidden patterns
    test: All test files + bunny

  INV-ATTR-NO-RANKING:
    rule: "No ranking, no best/worst, no implied priority"
    tracks: D, F
    enforcement: Sensitivity sorted by param, not performance
    test: test_sensitivity.py, test_bunny_s39.py

  INV-VALIDATION-DECOMPOSED:
    rule: "Every validation check returns separate factor, never combined"
    tracks: ALL
    enforcement: Schema validation
    test: All test files

NEW_INVARIANTS:

  INV-SENSITIVITY-NOT-IMPORTANCE:
    rule: "'Sensitivity' language only; 'importance' forbidden"
    tracks: D
    enforcement: Language linter

  INV-NO-VERDICT:
    rule: "No PASS/FAIL, GOOD/BAD, or recommendation in validation output"
    tracks: ALL
    enforcement: ScalarBanLinter

INHERITED:
  - INV-ATTR-PROVENANCE (full provenance on all outputs)
  - INV-NO-UNSOLICITED (no system recommendations)
```

---

## ADVISOR QUESTIONS

```yaml
FOR_GPT_ARCHITECT:
  - "Scalar ban linter patterns complete? Missing resurrection vectors?"
  - "Walk-forward delta presentation tight? Judgment leakage?"
  - "Cross-module audit sufficient?"

FOR_GROK_CHAOS:
  - "What's the dumbest way a viability score comes back?"
  - "Sensitivity → importance resurrection paths?"
  - "Multi-module chaining that synthesizes ranking?"

FOR_OWL_STRUCTURAL:
  - "Is scalar ban linter the correct 'linter of linters' implementation?"
  - "Decomposition granularity appropriate?"
  - "Integration seams between S35-S38 and S39 coherent?"
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | BACKTEST | Decomposed metrics only; no composite |
| B | WALK_FORWARD | Per-split deltas; no overfit verdict |
| C | MONTE_CARLO | Distribution percentiles; no risk verdict |
| D | SENSITIVITY | Param-ordered table; no importance ranking |
| E | COST_CURVE | Degradation table; no acceptability verdict |
| F | SCALAR_BAN + BUNNY | Linter catches all; 28+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S39 COMPLETE → S35-S39 BLOCK COMPLETE

---

```yaml
STATUS: DRAFT_v0.1
NEXT: Socialize to GPT, GROK, OWL for input
THEN: Synthesize addendum → OPUS for v0.2

NOTE_TO_G: |
  S39 is the constitutional ceiling.
  If we nail this, the entire S35-S39 block is airtight:
  - CFP (conditional facts)
  - CSO (gate status)
  - Athena (memory discipline)
  - Hunt (exhaustive compute)
  - Validation (decomposed outputs)

  No scalar scores. No rankings. No verdicts.
  Human frames, machine computes. Human interprets.
```
