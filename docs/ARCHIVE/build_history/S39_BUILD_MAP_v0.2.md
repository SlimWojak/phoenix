# S39_BUILD_MAP_v0.2.md — RESEARCH VALIDATION

```yaml
document: S39_BUILD_MAP_v0.2.md
version: 0.2
date: 2026-01-29
status: OPUS_REFINED_FOR_EXECUTION
theme: "Decomposed outputs, no viability scores. Ever."
codename: VALIDATION_SUITE
dependencies: 
  - S35_CFP (COMPLETE)
  - S36_CSO (COMPLETE)
  - S37_ATHENA (COMPLETE)
  - S38_HUNT (COMPLETE)
advisor_synthesis: [GPT_ARCHITECT, GROK_CHAOS, OWL_STRUCTURAL]
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
  No avg_* hiding variance.
  Human interprets decomposed factors.
```

---

## INVARIANTS (9 Total)

```yaml
# ============================================================
# ORIGINAL INVARIANTS (2)
# ============================================================

INV-SCALAR-BAN:
  rule: "No composite scores (0-100); decompose to factor traffic lights"
  enforcement: ScalarBanLinter rejects forbidden patterns

INV-VALIDATION-DECOMPOSED:
  rule: "Every validation check returns separate factor, never combined"
  enforcement: Schema validation

# ============================================================
# NEW INVARIANTS (7) — From Advisor Synthesis
# ============================================================

INV-NO-AGGREGATE-SCALAR:
  rule: "No avg_* fields in walk-forward; return full split arrays"
  source: [GPT, OWL]
  rationale: "Averages hide variance; [-1,-1,-1,4,-1] → 0 looks 'stable'"
  applies_to: Track B
  replacement: "per_split_results with full delta array"

INV-NEUTRAL-ADJECTIVES:
  rule: "Ban evaluative adjectives; mathematical descriptors only"
  source: [GPT, OWL]
  forbidden: [strong, weak, solid, fragile, consistent, healthy, safe, robust]
  allowed: [static, volatile, divergent, convergent, correlated, positive, negative]
  applies_to: Track F (ScalarBanLinter)

INV-VISUAL-PARITY:
  rule: "No color coding by value threshold; monochromatic default"
  source: OWL
  rationale: "P95 drawdown as red stoplight is visual scalar"
  enforcement: API metadata forbids color_scale
  applies_to: Track C, Track F

INV-NO-IMPLICIT-VERDICT:
  rule: "All outputs include 'FACTS_ONLY — NO INTERPRETATION' disclaimer"
  source: GROK
  applies_to: ALL tracks
  enforcement: Output schema requires disclaimer field

INV-CROSS-MODULE-NO-SYNTH:
  rule: "Chained outputs declare 'DECOMPOSED_FACTS_ONLY — NO COMPOSITE MEANING'"
  source: GROK
  applies_to: Track F (cross-module audit)
  enforcement: Chain provenance bead required

INV-SENSITIVITY-SHUFFLE:
  rule: "Sensitivity table rows shuffle opt-in (T2); no delta_magnitude ranking"
  source: GROK
  applies_to: Track D
  forbidden: [abs(delta), magnitude_rank, "most_sensitive"]

INV-RAW-SIM-T2-ONLY:
  rule: "Monte Carlo raw_simulations array access requires T2"
  source: GPT
  default: OFF (percentiles only)
  applies_to: Track C
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
  new_constraints:
    - INV-NO-AGGREGATE-SCALAR (no avg_*)
  
TRACK_C: MONTE_CARLO (Drawdown Distribution)
  days: 3-4
  owner: OPUS
  new_constraints:
    - INV-VISUAL-PARITY
    - INV-RAW-SIM-T2-ONLY
  
TRACK_D: SENSITIVITY_ANALYSIS (Not "Importance")
  days: 4-5
  owner: OPUS
  new_constraints:
    - INV-SENSITIVITY-SHUFFLE
  
TRACK_E: COST_CURVE (Spread Degradation)
  days: 5-6
  owner: OPUS

TRACK_F: INTEGRATION + SCALAR_BAN_LINTER + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
  new_constraints:
    - INV-NEUTRAL-ADJECTIVES
    - INV-NO-IMPLICIT-VERDICT
    - INV-CROSS-MODULE-NO-SYNTH
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
    
    # MANDATORY disclaimer (v0.2)
    disclaimer: "FACTS_ONLY — NO INTERPRETATION OR VERDICT"
    
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
      
    # Visual metadata (v0.2)
    visual_metadata:
      color_scale: null  # FORBIDDEN
      highlight_threshold: null  # FORBIDDEN

FORBIDDEN_FIELDS:
  - quality_score
  - viability_index
  - robustness_score
  - overall_rating
  - recommendation
  - verdict

EXIT_GATE_A:
  criterion: "Backtest returns decomposed metrics; no composite score; disclaimer present"
  test: tests/test_validation/test_backtest.py
  proof: |
    - No field named *_score, *_index, *_rating in output
    - Metrics dict has only raw values
    - Disclaimer field present
```

---

## TRACK_B: WALK_FORWARD

```yaml
PURPOSE: |
  Out-of-sample validation with train/test splits.
  Detect curve-fitting before deployment.
  Full arrays, NO averages (INV-NO-AGGREGATE-SCALAR).

DELIVERABLES:
  - validation/walk_forward.py
  - validation/schemas/walk_forward_result_schema.yaml
  - tests/test_validation/test_walk_forward.py

# ============================================================
# CRITICAL v0.2 CHANGE: No avg_* fields
# ============================================================

WALK_FORWARD_RESULT:
  walk_forward_result:
    wf_id: str
    timestamp: datetime
    
    # MANDATORY disclaimer
    disclaimer: "FACTS_ONLY — NO INTERPRETATION OR VERDICT"
    
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
        
    # v0.2: FULL ARRAYS instead of averages
    split_distribution:
      train_sharpes: list[float]    # full array
      test_sharpes: list[float]     # full array
      deltas: list[float]           # full array (test - train)
      
    # v0.2: Explicitly labeled as descriptive
    descriptive_summary:
      median_delta: float
      delta_std: float
      n_positive_splits: int
      n_negative_splits: int
      # Explicitly labeled "descriptive", not "verdict"
      
    provenance: {...}
    
    visual_metadata:
      color_scale: null  # FORBIDDEN

# REMOVED FIELDS (v0.2):
#   - aggregate.avg_train_sharpe (HIDDEN VARIANCE)
#   - aggregate.avg_test_sharpe (HIDDEN VARIANCE)
#   - aggregate.avg_delta_sharpe (HIDDEN VARIANCE)

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
  - "PASS/FAIL" verdict
  - "Warning: appears overfit"
  - avg_train_sharpe  # v0.2: FORBIDDEN
  - avg_test_sharpe   # v0.2: FORBIDDEN
  - avg_delta_sharpe  # v0.2: FORBIDDEN

EXIT_GATE_B:
  criterion: "Walk-forward returns full arrays; no avg_*; no overfit verdict"
  test: tests/test_validation/test_walk_forward.py
  proof: |
    - Output has no "verdict" field
    - Output has no "avg_*" field
    - Delta is numeric, not labeled
    - Full arrays returned
```

---

## TRACK_C: MONTE_CARLO

```yaml
PURPOSE: |
  Simulate drawdown distribution via trade resampling.
  Provide confidence intervals, not verdicts.
  Raw simulations T2-gated (INV-RAW-SIM-T2-ONLY).

DELIVERABLES:
  - validation/monte_carlo.py
  - validation/schemas/monte_carlo_result_schema.yaml
  - tests/test_validation/test_monte_carlo.py

MONTE_CARLO_RESULT:
  monte_carlo_result:
    mc_id: str
    timestamp: datetime
    
    # MANDATORY disclaimer
    disclaimer: "FACTS_ONLY — NO INTERPRETATION OR VERDICT"
    
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
        
    # v0.2: Raw simulations T2-gated
    raw_simulations:
      access_tier: T2  # default OFF
      drawdowns: list[float] | null  # length = n_simulations
      # Only populated if include_raw=True AND tier=T2
      
    provenance: {...}
    
    # v0.2: Visual parity
    visual_metadata:
      color_scale: null  # FORBIDDEN
      highlight_threshold: null  # FORBIDDEN

PRESENTATION_RULE:
  allowed: "95th percentile max drawdown: -15%"
  forbidden: "Risk level: HIGH" (interpretation)
  forbidden: "Acceptable risk: YES/NO" (verdict)
  forbidden: "Danger zone: TRUE" (label)

EXIT_GATE_C:
  criterion: "Monte Carlo returns distribution; no risk verdict; raw T2-gated"
  test: tests/test_validation/test_monte_carlo.py
  proof: |
    - Output has percentiles, not labels
    - No "risk_level" field
    - Raw simulations null by default (T2 required)
```

---

## TRACK_D: SENSITIVITY_ANALYSIS

```yaml
PURPOSE: |
  Show how metrics change across parameter variations.
  Label as "SENSITIVITY" — never "IMPORTANCE."
  Shuffle opt-in (INV-SENSITIVITY-SHUFFLE).

DELIVERABLES:
  - validation/sensitivity.py
  - validation/schemas/sensitivity_result_schema.yaml
  - tests/test_validation/test_sensitivity.py

SENSITIVITY_RESULT:
  sensitivity_result:
    sens_id: str
    timestamp: datetime
    
    # MANDATORY disclaimer
    disclaimer: "FACTS_ONLY — NO INTERPRETATION OR VERDICT"
    
    configuration:
      base_params: dict
      varied_param: str
      variation_range: list[any]
      
    table:
      columns: ["param_value", "sharpe", "win_rate", "max_dd", ...]
      rows: list[dict]  # one per variation
      sort_order: "PARAM_ORDER"  # NOT by performance
      shuffle_applied: bool  # v0.2
      
    provenance: {...}
    
    visual_metadata:
      color_scale: null  # FORBIDDEN

LANGUAGE_RULES:
  allowed:
    - "sensitivity" 
    - "variation"
    - "response"
    - "change"
    - "delta"
    
  forbidden:
    - "importance" (implies ranking)
    - "impact" (implies causality)
    - "critical" (implies priority)
    - "key parameter" (implies selection)
    - "most sensitive" (implies ranking)
    - abs(delta)  # v0.2
    - magnitude_rank  # v0.2

NO_RANKING_RULE:
  - Table sorted by PARAM_ORDER (e.g., 0.5, 1.0, 1.5, 2.0)
  - NOT sorted by "sensitivity magnitude"
  - NOT sorted by "performance impact"
  - Shuffle opt-in (T2) for position neutrality
  - Client can sort; system never pre-sorts by result

EXIT_GATE_D:
  criterion: "Sensitivity table param-ordered; shuffle opt-in; no importance ranking"
  test: tests/test_validation/test_sensitivity.py
  proof: |
    - No "importance" in field names
    - No "most_sensitive" field
    - Sort order is param-based
    - Shuffle available with T2
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
    
    # MANDATORY disclaimer
    disclaimer: "FACTS_ONLY — NO INTERPRETATION OR VERDICT"
    
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
    
    visual_metadata:
      color_scale: null  # FORBIDDEN

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
  36+ chaos vectors across 16 waves.

DELIVERABLES:
  - validation/__init__.py (public interface)
  - validation/scalar_ban_linter.py
  - validation/api.py (file seam integration)
  - tests/test_validation/test_integration.py
  - tests/chaos/test_bunny_s39.py

# ============================================================
# SCALAR BAN LINTER (v0.2 Enhanced)
# ============================================================

SCALAR_BAN_LINTER:
  purpose: |
    The constitutional ceiling. Scans ALL validation outputs
    for forbidden scalar patterns. The "Linter of Linters."
    
  forbidden_patterns:
  
    # Field names
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
      - "avg_*"  # v0.2: HIDDEN VARIANCE
      
    # Value patterns
    value_patterns:
      - "PASS/FAIL"
      - "GOOD/BAD"
      - "HIGH/MEDIUM/LOW" (risk labels)
      - "A/B/C/D/F" (grades)
      - numeric 0-100 labeled as "score"
      
    # v0.2: Evaluative adjectives (INV-NEUTRAL-ADJECTIVES)
    evaluative_adjectives:
      - strong, weak
      - solid, fragile
      - consistent, inconsistent
      - healthy, unhealthy
      - safe, unsafe
      - concerning, promising
      - robust, brittle
      - stable, unstable (as judgment)
      - reliable, unreliable
      
    # v0.2: Threshold implications
    threshold_implications:
      - "if X > Y then"
      - "above threshold"
      - "below acceptable"
      - "within tolerance"
      - "exceeds limit"
      
    # v0.2: Comparison superlatives
    comparison_superlatives:
      - "most sensitive"
      - "least robust"
      - "best performing"
      - "worst case" (as verdict)
      
    # v0.2: Summary synthesis
    summary_synthesis:
      - "overall"
      - "in summary"
      - "taken together"
      - "combined"
      - "net assessment"
      
    # Language patterns
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

# ============================================================
# CROSS-MODULE AUDIT (v0.2)
# ============================================================

CROSS_MODULE_AUDIT:
  purpose: "Verify no causal/ranking leakage from S35-S38"
  
  s35_cfp:
    - Verify no causal language inherited
    - Check provenance chain intact
    - Flag any "best condition" terminology
    
  s36_cso:
    - Verify no grades reconstructed
    - Check bit-vector not counted
    - Flag any "quality" terminology
    
  s37_athena:
    - Verify claims not executed
    - Check no auto-surfacing
    - Flag any "suggests" terminology
    
  s38_hunt:
    - Verify no survivors ranked
    - Check exhaustive output
    - Flag any "top variant" terminology
    
  chain_provenance:
    - All chained outputs require "DECOMPOSED_FACTS_ONLY" declaration
    - No composite meaning downstream
    - Provenance bead for chain tracking

# ============================================================
# CHAOS VECTORS (36+ across 16 waves)
# ============================================================

CHAOS_VECTORS:

  # Original waves
  wave_1_scalar_resurrection:
    - cv_quality_score_rejected
    - cv_weighted_average_rejected
    - cv_viability_index_rejected
    - cv_strategy_health_78_rejected
    
  wave_2_verdict_attacks:
    - cv_walkforward_overfit_true_rejected
    - cv_montecarlo_risk_high_rejected
    - cv_costcurve_tradeable_no_rejected
    - cv_backtest_recommended_rejected
    
  wave_3_ranking_attacks:
    - cv_sensitivity_sorted_by_importance_rejected
    - cv_most_sensitive_parameter_rejected
    - cv_top_3_robust_rejected
    - cv_best_parameter_rejected
    
  wave_4_label_attacks:
    - cv_drawdown_dangerous_rejected
    - cv_delta_concerning_rejected
    - cv_spread_acceptable_rejected
    
  wave_5_cross_module:
    - cv_hunt_survivors_to_backtest_rejected
    - cv_cfp_best_condition_rejected
    - cv_edge_score_anywhere_rejected

  # New waves (v0.2)
  wave_13_aggregate_attacks:
    - cv_avg_delta_sharpe_field_not_found
    - cv_avg_field_injected_rejected
    - cv_aggregate_section_emphasized_rejected
    
  wave_14_adjective_attacks:
    - cv_robust_results_rejected
    - cv_consistent_performance_rejected
    - cv_healthy_metrics_rejected
    - cv_strong_sharpe_rejected
    - cv_fragile_strategy_rejected
    
  wave_15_visual_attacks:
    - cv_color_scale_metadata_rejected
    - cv_highlight_threshold_rejected
    - cv_row_emphasis_rules_rejected
    
  wave_16_chain_synthesis:
    - cv_cfp_hunt_validation_without_disclaimer_rejected
    - cv_downstream_composite_rejected
    - cv_missing_chain_provenance_rejected

EXIT_GATE_F:
  criterion: "Scalar ban linter catches all; 36+ chaos vectors pass"
  test: tests/chaos/test_bunny_s39.py
  proof: "No viability score anywhere in validation outputs"
```

---

## OPUS EXECUTION NOTES

```yaml
FILE_STRUCTURE:
  validation/
  ├── __init__.py
  ├── schemas/
  │   ├── backtest_result_schema.yaml
  │   ├── walk_forward_result_schema.yaml
  │   ├── monte_carlo_result_schema.yaml
  │   ├── sensitivity_result_schema.yaml
  │   └── cost_curve_result_schema.yaml
  ├── backtest.py           # Track A
  ├── walk_forward.py       # Track B
  ├── monte_carlo.py        # Track C
  ├── sensitivity.py        # Track D
  ├── cost_curve.py         # Track E
  ├── scalar_ban_linter.py  # Track F
  └── api.py                # Track F
  
  tests/test_validation/
  ├── __init__.py
  ├── conftest.py
  ├── test_backtest.py
  ├── test_walk_forward.py
  ├── test_monte_carlo.py
  ├── test_sensitivity.py
  ├── test_cost_curve.py
  └── test_integration.py
  
  tests/chaos/
  └── test_bunny_s39.py    # 36+ vectors

DAY_BY_DAY:
  day_1:
    - validation/schemas/*.yaml (all 5)
    - validation/backtest.py
    - tests/test_validation/test_backtest.py
    
  day_2:
    - validation/walk_forward.py (no avg_*, full arrays)
    - tests/test_validation/test_walk_forward.py
    
  day_3:
    - validation/monte_carlo.py (T2-gated raw)
    - tests/test_validation/test_monte_carlo.py
    
  day_4:
    - validation/sensitivity.py (shuffle opt-in)
    - tests/test_validation/test_sensitivity.py
    
  day_5:
    - validation/cost_curve.py
    - tests/test_validation/test_cost_curve.py
    
  day_6-7:
    - validation/scalar_ban_linter.py (enhanced)
    - validation/__init__.py
    - validation/api.py
    - tests/test_validation/test_integration.py
    - tests/chaos/test_bunny_s39.py (36+ vectors)
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | BACKTEST | Decomposed metrics; disclaimer present |
| B | WALK_FORWARD | Full arrays; NO avg_*; no overfit verdict |
| C | MONTE_CARLO | Distribution only; raw T2-gated; no risk verdict |
| D | SENSITIVITY | Param-ordered; shuffle opt-in; no importance |
| E | COST_CURVE | Degradation table; no acceptability verdict |
| F | SCALAR_BAN + BUNNY | Linter catches all; 36+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S39 COMPLETE → S35-S39 BLOCK COMPLETE

---

```yaml
STATUS: OPUS_REFINED_v0.2
INVARIANTS: 9 (2 original + 7 new)
CHAOS_VECTORS: 36+ (16 waves)
TARGET: Sub-25min (beat S38 pace)
PATTERN: PROVEN x4

NOTE: |
  S39 completes the S35-S39 block.
  
  If this lands clean:
  - CFP: Conditional facts with provenance
  - CSO: Gate status, never grades
  - Athena: Memory, not myth
  - Hunt: Compute, not propose
  - Validation: Decomposed, no verdicts
  
  Total: 500+ tests, 150+ chaos vectors, 50+ invariants
  
  Human frames. Machine computes. Human interprets.
  No scalar scores. No rankings. No verdicts. Ever.
```

---
