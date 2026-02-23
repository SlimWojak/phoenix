# S36_BUILD_MAP_v0.2.md — CSO HARNESS

```yaml
document: S36_BUILD_MAP_v0.2.md
version: 0.2
date: 2026-01-29
status: OPUS_EXECUTION_READY
theme: "Gate status per pair, facts not grades — HARDENED"
codename: CSO_HARNESS
dependency: S35_CFP (COMPLETE)
synthesized_from: [GPT_ARCHITECT, OWL_STRUCTURAL, GROK_CHAOS, OPUS_REPO_INTIMACY]
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the harness that evaluates Olya's 5-drawer methodology
  and outputs GATE STATUS — never grades, never quality scores.
  
  NEX died saying: "Grade A setup"
  Phoenix says: "gates_passed: [1,3,5], gates_failed: [2,4]"
  
  CRITICAL HARDENING: Bit-vectors CANNOT become grades by proxy.
  Hamming weight (count of 1s) is the dumbest way grades leak back in.

GOVERNING_PRINCIPLE: |
  "Human interprets the pattern. System reports the facts."
  Gates are predicates. Grades are judgment. We do predicates.

EXIT_GATE_SPRINT: |
  CSO Harness returns gate status per pair.
  No grades anywhere in output (code, logs, responses).
  No bit-counts, no population counts, no scalar derivations.
  Alerts fire on explicit gate combinations only.
  Multi-pair display shuffled to prevent position bias.
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: 5_DRAWER_SCHEMA (Knowledge Structure)
  days: 1-2
  files:
    - cso/schemas/drawer_schema.yaml
    - cso/schemas/gate_schema.yaml
    - cso/knowledge/conditions.yaml (extend)
    - tests/test_cso/test_drawer_schema.py
  
TRACK_B: GATE_EVALUATOR (Predicate Engine)
  days: 2-3
  files:
    - cso/evaluator.py
    - cso/gate_registry.py
    - cso/predicates/__init__.py
    - tests/test_cso/test_evaluator.py
  
TRACK_C: BIT_VECTOR_OUTPUT (Machine-Readable Status)
  days: 3-4
  files:
    - cso/bit_vector.py
    - cso/schemas/bit_vector_schema.yaml
    - tests/test_cso/test_bit_vector.py
  
TRACK_D: MULTI_PAIR_SCANNER (Shuffled, No Ranking)
  days: 4-5
  files:
    - cso/scanner.py (extend existing)
    - cso/multi_pair_result.py
    - tests/test_cso/test_multi_pair_scanner.py
  
TRACK_E: ALERT_INTEGRATION (Gate-Triggered, Not Quality)
  days: 5-6
  files:
    - cso/alerts.py
    - cso/alert_rules.yaml
    - cso/alert_linter.py (extends causal_ban)
    - tests/test_cso/test_alerts.py

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  files:
    - cso/harness.py (public interface)
    - cso/api.py (file seam integration)
    - tests/test_cso/test_harness_integration.py
    - tests/chaos/test_bunny_s36.py
```

---

## TRACK_A: 5_DRAWER_SCHEMA

```yaml
PURPOSE: |
  Formalize Olya's 5-drawer knowledge structure as machine-readable schema.
  Each drawer contains gates. Gates are predicates. Predicates return boolean.

DELIVERABLES:
  - cso/schemas/drawer_schema.yaml
  - cso/schemas/gate_schema.yaml
  - cso/knowledge/conditions.yaml (extend existing)
  - tests/test_cso/test_drawer_schema.py

5_DRAWER_STRUCTURE:
  drawer_1_foundation:
    name: "HTF Bias"
    gates:
      - htf_structure_bullish
      - htf_structure_bearish
      - htf_poi_identified
    evaluation:
      type: EXPLICIT_BOOLEAN_RULE
      rule: "at_least_one_directional"
      declaration: "conditions.yaml"
    
  drawer_2_context:
    name: "Session Context"
    gates:
      - kill_zone_active
      - asia_range_defined
      - session_bias_aligned
    evaluation:
      type: EXPLICIT_BOOLEAN_RULE
      rule: "all_gates_independent"
      declaration: "conditions.yaml"
    
  drawer_3_conditions:
    name: "Entry Conditions"
    gates:
      - fvg_present
      - displacement_sufficient
      - liquidity_swept
    evaluation:
      type: EXPLICIT_BOOLEAN_RULE
      rule: ">=2 of [fvg_present, displacement_sufficient, liquidity_swept]"
      declaration: "conditions.yaml"  # NOT runtime configurable
    
  drawer_4_entry:
    name: "Entry Trigger"
    gates:
      - ltf_confirmation
      - entry_model_valid
      - stop_defined
    evaluation:
      type: EXPLICIT_BOOLEAN_RULE
      rule: "all_required"
      declaration: "conditions.yaml"
    
  drawer_5_management:
    name: "Trade Management"
    gates:
      - target_defined
      - rr_acceptable
      - partials_planned
    evaluation:
      type: EXPLICIT_BOOLEAN_RULE
      rule: "all_required"
      declaration: "conditions.yaml"

GATE_SCHEMA:
  gate:
    id: str  # unique identifier
    drawer: int  # 1-5
    name: str  # human-readable
    predicate: str  # reference to conditions.yaml
    required: bool  # must pass for drawer to pass
    weight: null  # FORBIDDEN — no implicit ranking
    
  # v0.2 ADDITION: Gate failure provenance
  gate_evaluation_output:
    passed: bool
    predicate_delta: str | null  # On failure, distance from threshold
    example: "gate_htf_poi: FALSE [delta: 1.2 pips from threshold]"

FORBIDDEN_FIELDS:
  - quality_score
  - confidence
  - grade
  - rank
  - weight
  - priority
  - quality_threshold  # v0.2: EXPLICIT BAN

EXIT_GATE_A:
  criterion: "5-drawer schema validates; no forbidden fields accepted; rules explicit in conditions.yaml"
  test: tests/test_cso/test_drawer_schema.py
  proof: |
    - Schema rejects any gate with quality/confidence/grade fields
    - Drawer rules declared in conditions.yaml, not runtime configurable
    - Gate failure includes predicate_delta

INVARIANTS_PROVEN:
  - INV-HARNESS-1 (gate status only, never grades)
  - INV-DRAWER-RULE-EXPLICIT (v0.2: rules in conditions.yaml only)

OPUS_EXECUTION_NOTES:
  integration_points:
    - Extend existing cso/knowledge/conditions.yaml composite_gates section
    - FourQGateResult in cso/contract.py becomes FiveDrawerResult
    - Predicate delta requires numeric predicates to expose threshold
  
  existing_gates_to_map:
    high_quality_long: "drawer_3_conditions + drawer_4_entry combo"
    high_quality_short: "drawer_3_conditions + drawer_4_entry combo"
    alignment_gate: "drawer_2_context"
    freshness_gate: "drawer_3_conditions"
  
  test_patterns:
    - test_drawer_schema_rejects_quality_field
    - test_drawer_schema_rejects_confidence
    - test_drawer_rule_must_be_in_conditions_yaml
    - test_gate_failure_includes_delta
```

---

## TRACK_B: GATE_EVALUATOR

```yaml
PURPOSE: |
  Evaluate gates against live market state.
  Return boolean per gate. No interpretation. No synthesis.

DELIVERABLES:
  - cso/evaluator.py
  - cso/gate_registry.py
  - cso/predicates/  # predicate implementations
  - tests/test_cso/test_evaluator.py

EVALUATOR_INTERFACE:
  input:
    pair: str  # e.g., "EURUSD"
    market_state: MarketState  # from River
    strategy_config_hash: str  # anchors evaluation
    
  output:
    GateEvaluation:
      pair: str
      timestamp: datetime
      gates_passed: list[str]  # gate IDs
      gates_failed: list[str]  # gate IDs with predicate_delta
      gates_skipped: list[str]  # insufficient data
      drawer_status: dict[int, bool]  # per-drawer rollup
      strategy_config_hash: str
      market_state_hash: str
      provenance: Provenance  # from CFP

EVALUATION_RULES:
  - Each gate evaluates to TRUE | FALSE | SKIPPED
  - SKIPPED only when data insufficient (explicit, not silent)
  - No aggregation beyond drawer-level "rule evaluation"
  - No cross-gate weighting
  - No "overall score"
  
  # v0.2 ADDITION: Forbidden aggregation
  forbidden_in_evaluator:
    - popcount functions
    - sum of gates_passed
    - any scalar derived from gate booleans
    - len(gates_passed) in any context
  
  log_hygiene: "Debug logs must not include gate counts"

PREDICATE_REGISTRY:
  location: cso/knowledge/conditions.yaml
  pattern: |
    gate_id:
      predicate: "htf_bias == 'bullish' AND poi_distance < 50"
      data_requirements: [htf_data, current_price]
      threshold: 50  # For delta calculation
      
BIAS_HANDLING:
  rule: INV-BIAS-PREDICATE
  allowed: "htf_bullish_predicate: PASSED"
  forbidden: "Bullish" as standalone assessment
  implementation: |
    Bias is a gate status, not a direction.
    Output: "gate_htf_structure_bullish: TRUE"
    NOT: "bias: bullish"

EXIT_GATE_B:
  criterion: "Evaluator returns gate status per pair; no scores/grades; no aggregation helpers"
  test: tests/test_cso/test_evaluator.py
  proof: |
    - 6 pairs evaluated correctly
    - All outputs are boolean per gate
    - No confidence/quality fields in output
    - No popcount/sum functions in codebase

INVARIANTS_PROVEN:
  - INV-HARNESS-1 (gate status only)
  - INV-HARNESS-2 (no confidence scores)
  - INV-BIAS-PREDICATE (bias as predicate status)

OPUS_EXECUTION_NOTES:
  integration_points:
    - Extend CSOContract.evaluate_4q_gate to evaluate_5_drawer
    - Wire to existing structure_detector.py for HTF predicates
    - Use params_loader.py for strategy config
  
  predicate_delta_implementation: |
    For numeric predicates (poi_distance < 50):
      delta = actual_value - threshold
      output: "gate_htf_poi: FALSE [delta: 1.2 pips from threshold]"
    
    For boolean predicates (fvg_present):
      delta = null (no numeric threshold)
      output: "gate_fvg_present: FALSE"
    
    For enum predicates (session == 'london'):
      delta = "actual: tokyo"
      output: "gate_kz_active: FALSE [actual: tokyo]"
  
  test_patterns:
    - test_evaluator_no_popcount
    - test_evaluator_no_sum_gates
    - test_evaluator_logs_no_counts
    - test_gate_failure_delta_numeric
    - test_gate_failure_delta_enum
```

---

## TRACK_C: BIT_VECTOR_OUTPUT

```yaml
PURPOSE: |
  Machine-readable gate status for sub-millisecond triage.
  Map gates to bit positions. Output as binary string.
  
  CRITICAL: Bit vectors are MACHINE_ONLY by default.
  No population counts. No Hamming distance. No scalar derivation.

DELIVERABLES:
  - cso/bit_vector.py
  - cso/schemas/bit_vector_schema.yaml
  - tests/test_cso/test_bit_vector.py

BIT_VECTOR_STRUCTURE:
  format: "01011010..."  # position = gate index
  mapping: |
    Position 0: gate_htf_structure_bullish
    Position 1: gate_htf_structure_bearish
    Position 2: gate_htf_poi_identified
    ... (defined in conditions.yaml order)
    
  output:
    BitVectorResult:
      pair: str
      vector: str  # "01011010"
      gate_map: dict[int, str]  # position → gate_id (MACHINE LAYER)
      timestamp: datetime
      provenance: Provenance  # from CFP
      
  # v0.2 ADDITIONS
  exposure:
    scope: MACHINE_ONLY
    ui_exposure: EXPLICIT_OPT_IN  # requires T2 approval
    display_default: DISABLED
    
  gate_map_ui:
    order: RANDOMIZED_PER_RENDER  # Not conditions.yaml order
    rationale: "Prevents 'longest green bar' pattern recognition"

USE_CASE:
  - Rapid multi-pair comparison (machine layer)
  - Pattern matching ("find all pairs with vector matching 11???1??")
  - No interpretation — human reads the pattern

FORBIDDEN:
  - Counting 1s as "score"
  - Sorting by 1-count
  - "Best" vector determination
  - Hamming distance comparisons (implies ranking)
  - popcount() function anywhere
  - len([g for g in gates if g == 1])
  
  # v0.2 ADDITIONS
  - Any downstream consumer counting 1s
  - S38 hunt matching "vectors with >6 ones"
  - Similarity scoring between vectors

EXIT_GATE_C:
  criterion: "Bit vector generated correctly; MACHINE_ONLY default; no population counting"
  test: tests/test_cso/test_bit_vector.py
  proof: |
    - Vector matches gate evaluation
    - No popcount/len in codebase
    - Attempt to count 1s rejected at schema
    - UI gate_map order randomized per render

INVARIANTS_PROVEN:
  - INV-HARNESS-1 (no grades)
  - INV-ATTR-NO-RANKING (no implicit priority)
  - INV-BITVECTOR-NO-POPULATION (v0.2: no counting 1s)
  - INV-HARNESS-5 (v0.2: no downstream scalar derivation)

OPUS_EXECUTION_NOTES:
  population_ban_implementation: |
    # FORBIDDEN patterns to grep/lint for:
    - popcount
    - bin(x).count('1')
    - sum(1 for b in vector if b == '1')
    - len([g for g in gates_passed])
    - vector.count('1')
    
    # Enforcement:
    1. Code review checklist
    2. Pre-commit linter rule
    3. Schema validation rejects count-based queries
  
  randomized_gate_map: |
    # Per-render shuffle for UI display
    import secrets
    shuffled_positions = list(range(len(gates)))
    secrets.SystemRandom().shuffle(shuffled_positions)
    
    # Machine layer keeps conditions.yaml order (deterministic)
    machine_gate_map = {i: gate_id for i, gate_id in enumerate(gates)}
    
    # UI layer uses shuffled order
    ui_gate_map = {shuffled_positions[i]: gate_id for i, gate_id in enumerate(gates)}
  
  test_patterns:
    - test_bit_vector_no_popcount_function
    - test_bit_vector_rejects_count_query
    - test_ui_gate_map_randomized
    - test_machine_gate_map_deterministic
    - test_hamming_distance_rejected
```

---

## TRACK_D: MULTI_PAIR_SCANNER

```yaml
PURPOSE: |
  Scan all pairs simultaneously.
  Output SHUFFLED — never by "quality" or gate count.
  Position bias prevention through randomization.

DELIVERABLES:
  - cso/scanner.py (extend existing)
  - cso/multi_pair_result.py
  - tests/test_cso/test_multi_pair_scanner.py

SCANNER_INTERFACE:
  input:
    pairs: list[str]  # default: ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"]
    market_state: MarketState
    strategy_config_hash: str
    
  output:
    MultiPairScan:
      timestamp: datetime
      results: list[GateEvaluation]  # SHUFFLED ORDER
      sort_order: str  # "randomized_alphabetical" or "strict_random"
      sort_seed: str  # For reproducibility in tests
      provenance: Provenance

# v0.2: SHUFFLE RULES
SORT_RULES:
  default: RANDOMIZED_ALPHABETICAL
  behavior: "Random starting letter, then alphabetical from there"
  alternative: STRICT_RANDOM  # Per refresh
  declaration: sort_order field in output (explicit)
  
  forbidden_sorts:
    - by gates_passed count
    - by "quality"
    - by "readiness"
    - by any derived metric
    - by bit_vector population count
    
  user_override: T2_REQUIRED (human must explicitly request)

# v0.2: BUDGET LIMIT
BUDGET:
  max_pairs: 12  # default
  override_requires: T2
  on_exceed: BUDGET_EXCEEDED error
  
DISPLAY_FORMAT:
  # Shuffled — starting position randomized
  GBPUSD: gates_passed=[1,3], gates_failed=[2,4,5]
  NZDUSD: gates_passed=[1,2,3,4], gates_failed=[5]
  AUDUSD: gates_passed=[1], gates_failed=[2,3,4,5]
  ... (continues in shuffle order)
  
  # v0.2: EQUAL WEIGHT RENDERING
  display_rules:
    - No bold on high gate count
    - No color intensity by count
    - No emoji/heatmaps implying quality
    - Fixed-width gate display (pad shorter lists)

FORBIDDEN_PATTERNS:
  - "Top pairs"
  - "Best setups"
  - "Ranked by readiness"
  - Any ordering implying preference

EXIT_GATE_D:
  criterion: "Multi-pair output shuffled; budget enforced; no ranking"
  test: tests/test_cso/test_multi_pair_scanner.py
  proof: |
    - 6 pairs always in randomized order
    - Attempt to sort by gate_count rejected
    - Output declares sort_order explicitly
    - 100 pairs request → BUDGET_EXCEEDED

INVARIANTS_PROVEN:
  - INV-HARNESS-4 (randomized default, not alphabetical)
  - INV-ATTR-NO-RANKING (no implied priority)
  - INV-NO-DEFAULT-SALIENCE (equal visual weight)
  - INV-DISPLAY-SHUFFLE (v0.2: position bias prevention)
  - INV-CSO-BUDGET (v0.2: max_pairs=12 default)

OPUS_EXECUTION_NOTES:
  randomized_alphabetical: |
    # Implementation
    import secrets
    pairs = ["AUDUSD", "EURUSD", "GBPUSD", "NZDUSD", "USDCAD", "USDCHF"]
    start_letter = secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    
    # Rotate alphabet to start at random letter
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    start_idx = alphabet.index(start_letter)
    rotated = alphabet[start_idx:] + alphabet[:start_idx]
    
    # Sort pairs by rotated alphabet
    sorted_pairs = sorted(pairs, key=lambda p: rotated.index(p[0]))
  
  existing_scanner_extension: |
    # cso/scanner.py already exists
    # Extend with:
    - MultiPairScan dataclass
    - sort_order parameter
    - budget enforcement
  
  test_patterns:
    - test_scanner_output_shuffled
    - test_scanner_sort_by_gate_count_rejected
    - test_scanner_budget_exceeded_100_pairs
    - test_scanner_equal_weight_display
```

---

## TRACK_E: ALERT_INTEGRATION

```yaml
PURPOSE: |
  Alerts fire when EXPLICIT gate combinations pass.
  NOT when "quality" threshold met. Gates, not grades.
  
  CRITICAL: No count language in alerts.
  "{gates_passed_count}/{total_gates}" is implicit quality signal.

DELIVERABLES:
  - cso/alerts.py
  - cso/alert_rules.yaml
  - cso/alert_linter.py (extends causal_ban)
  - cso/takopi_integration.py (Telegram bridge)
  - tests/test_cso/test_alerts.py

ALERT_RULE_SCHEMA:
  alert_rule:
    id: str
    name: str  # Must use STATE_* prefix
    trigger:
      gates_required: list[str]  # explicit gate IDs (minimum 1)
      gates_forbidden: list[str]  # must NOT pass
      drawer_minimum: null  # FORBIDDEN
      quality_threshold: null  # FORBIDDEN
    notification:
      channel: enum[telegram, log, bead]
      template: str  # Must pass alert linter

# v0.2: NAMING CONVENTION
ALERT_NAMING:
  prefix: "STATE_"
  pattern: "STATE_{SESSION}_{CONDITION}_MATCH"
  example: "STATE_LONDON_FVG_MATCH"
  forbidden:
    - "ready"
    - "setup"
    - "opportunity"
    - Any readiness-implying adjective

# v0.2: CONTENT RULES
ALERT_CONTENT:
  forbidden_in_templates:
    - gates_passed_count
    - ratios (/total)
    - fractions
    - percentages
    - "looks ready"
    - "setup forming"
    - "opportunity"
    - "consider"
    - "potential"
    
  allowed_format: |
    Gates Passed: [gate_ids]
    Gates Failed: [gate_ids]

EXAMPLE_RULES:
  STATE_LONDON_FVG_MATCH:  # Renamed from london_fvg_ready
    gates_required:
      - gate_kill_zone_active  # must be London
      - gate_htf_structure_bullish OR gate_htf_structure_bearish
      - gate_fvg_present
      - gate_displacement_sufficient
    gates_forbidden:
      - gate_news_imminent
    notification:
      channel: telegram
      template: |
        [STATE] {pair}
        Matched: STATE_LONDON_FVG_MATCH
        Gates Passed: {gates_passed}
        Gates Failed: {gates_failed}

# v0.2: RATE LIMITING
RATE_LIMITER:
  max_per_pair: 3/minute
  max_global: 10/minute
  on_exceed: SUPPRESS + write suppression_bead
  
# v0.2: EMPTY GATES GUARD
VALIDATION:
  gates_required: minimum 1 gate
  reject_empty: TRUE

# ALERT LINTER (extends causal_ban)
ALERT_LINTER:
  extends: cfp/linter.py
  additional_banned_phrases:
    - "looks ready"
    - "setup forming"
    - "opportunity"
    - "consider"
    - "potential"
    - "quality"
    - "grade"
    - "score"

EXIT_GATE_E:
  criterion: "Alerts fire on gate combinations only; no quality/count language; rate limited"
  test: tests/test_cso/test_alerts.py
  proof: |
    - Alert with quality_threshold rejected at config
    - Alert with gates_required: [] rejected
    - Alert output contains no forbidden phrases
    - Template with {gates_passed_count} rejected by linter
    - 100 alerts in 1 minute → rate limit kicks in

INVARIANTS_PROVEN:
  - INV-HARNESS-3 (alerts on gate combinations)
  - INV-NO-UNSOLICITED (no recommendations)

OPUS_EXECUTION_NOTES:
  alert_linter_extension: |
    # Extend cfp/linter.py CausalBanLinter
    class AlertLinter(CausalBanLinter):
        def __init__(self):
            super().__init__()
            # Add alert-specific banned phrases
            self._additional_banned = [
                "looks ready", "setup forming", "opportunity",
                "consider", "potential", "quality", "grade", "score",
                "gates_passed_count", "/total", "%"
            ]
        
        def lint_alert_template(self, template: str) -> LintResult:
            # First check causal language
            result = self.lint(template)
            if not result.passed:
                return result
            
            # Then check alert-specific bans
            for phrase in self._additional_banned:
                if phrase.lower() in template.lower():
                    return LintResult(passed=False, ...)
            
            return LintResult(passed=True, ...)
  
  rate_limiter_storage: |
    # In-memory with bead backup for persistence
    class AlertRateLimiter:
        def __init__(self):
            self._pair_counts: dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
            self._global_counts: deque = deque(maxlen=100)
        
        def check_and_increment(self, pair: str) -> bool:
            now = datetime.now(UTC)
            one_minute_ago = now - timedelta(minutes=1)
            
            # Clean old entries
            self._pair_counts[pair] = deque(
                t for t in self._pair_counts[pair] if t > one_minute_ago
            )
            
            if len(self._pair_counts[pair]) >= 3:
                self._emit_suppression_bead(pair, "rate_limit_pair")
                return False
            
            if len(self._global_counts) >= 10:
                self._emit_suppression_bead(pair, "rate_limit_global")
                return False
            
            self._pair_counts[pair].append(now)
            self._global_counts.append(now)
            return True
  
  test_patterns:
    - test_alert_rejects_quality_threshold
    - test_alert_rejects_empty_gates
    - test_alert_template_no_count
    - test_alert_name_state_prefix
    - test_alert_rate_limit_per_pair
    - test_alert_rate_limit_global
    - test_alert_linter_catches_ready
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire CSO Harness end-to-end. Chaos test for grade leakage.
  Prove the harness holds under adversarial conditions.
  
  PRIMARY CHAOS TARGET: Bit-vector population count.
  "What's the dumbest way grades leak through? Counting 1s."

DELIVERABLES:
  - cso/harness.py (public interface)
  - cso/api.py (file seam integration)
  - tests/test_cso/test_harness_integration.py
  - tests/chaos/test_bunny_s36.py

INTEGRATION_POINTS:
  file_seam:
    - Intent: type=CSO_SCAN, payload={pairs, strategy_config_hash}
    - Response: MultiPairScan written to /responses/
    
  cfp_integration:
    - GateEvaluation can feed CFP queries
    - "Performance when gate_htf_bullish=TRUE"
    
  orientation:
    - CSO status in orientation.yaml
    - "cso_status: NOMINAL | DEGRADED | UNCALIBRATED"

# v0.2: EXPANDED CHAOS VECTORS (24+)
CHAOS_VECTORS:

  # WAVE 1: BIT-COUNT ATTACKS (PRIMARY TARGET)
  BIT_COUNT_ATTEMPT:
    description: "Request popcount or sum of gates_passed"
    expect: "REJECT — INV-BITVECTOR-NO-POPULATION"
    
  DOWNSTREAM_VECTOR_SCORING:
    description: "Query 'vectors with >6 ones'"
    expect: "REJECT — INV-HARNESS-5"
    
  HAMMING_DISTANCE_QUERY:
    description: "Request similarity between bit vectors"
    expect: "REJECT — implies ranking"
    
  LEN_GATES_PASSED:
    description: "Request len(gates_passed) as metric"
    expect: "REJECT — scalar derivation from booleans"
    
  SORT_BY_BIT_COUNT:
    description: "Request sort by gates_passed length"
    expect: "REJECT — alphabetical/shuffle only"

  # WAVE 2: SCHEMA ATTACKS
  GRADE_INJECTION:
    description: "Inject 'grade: A' into gate schema"
    expect: "REJECT at schema validation"
    
  QUALITY_SCORE_INJECTION:
    description: "Inject 'quality_score' into evaluator output"
    expect: "FAIL validation"
    
  CONFIDENCE_INJECTION:
    description: "Add 'confidence: 0.87' to output"
    expect: "FAIL validation"
    
  DRAWER_THRESHOLD_DRIFT:
    description: "Inject 'quality_threshold' into drawer config"
    expect: "REJECT at schema validation"
    
  RANKING_INJECTION:
    description: "Inject 'rank' field"
    expect: "FAIL validation"

  # WAVE 3: ALERT ATTACKS
  ALERT_COUNT_INJECTION:
    description: "Template with {gates_passed_count}"
    expect: "REJECT by alert linter"
    
  ALERT_RATIO_INJECTION:
    description: "Template with {passed}/{total}"
    expect: "REJECT by alert linter"
    
  ALERT_READY_INJECTION:
    description: "Alert template with 'looks ready'"
    expect: "FAIL linter"
    
  ALERT_SPAM_FLOOD:
    description: "100 alerts in 1 minute"
    expect: "Rate limit + suppression_bead"
    
  EMPTY_GATES_RULE:
    description: "Alert rule with gates_required: []"
    expect: "REJECT at config validation"

  # WAVE 4: DISPLAY ATTACKS
  SORT_GATE_COUNT:
    description: "Request sort by gates_passed count"
    expect: "REJECT — shuffle only"
    
  SALIENCE_INJECTION:
    description: "Attempt to highlight 'best' pair"
    expect: "REJECT — equal weight"
    
  100_PAIR_EXPLOSION:
    description: "Request scan of 100 pairs"
    expect: "BUDGET_EXCEEDED — INV-CSO-BUDGET"

  # WAVE 5: PREDICATE ATTACKS
  PREDICATE_CORRUPTION_MID_EVAL:
    description: "Edit conditions.yaml during scan"
    expect: "Graceful fail, explicit error"
    
  BIAS_LANGUAGE_INJECTION:
    description: "Output 'bullish' without predicate reference"
    expect: "FAIL linter"

  # WAVE 6: MISC
  DRAWER_RULE_RUNTIME_CHANGE:
    description: "Attempt to change drawer rule at runtime"
    expect: "REJECT — rules in conditions.yaml only"
    
  GATE_MAP_POSITION_ATTACK:
    description: "Request fixed gate_map position (not shuffled)"
    expect: "Machine layer only; UI always shuffled"

EXIT_GATE_F:
  criterion: "Harness passes all 24+ chaos vectors; no grades leak through"
  test: tests/chaos/test_bunny_s36.py
  proof: "24+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S36 invariants (integration test)
  - INV-HARNESS-1 through INV-HARNESS-5
  - INV-BITVECTOR-NO-POPULATION
  - INV-DRAWER-RULE-EXPLICIT
  - INV-DISPLAY-SHUFFLE
  - INV-CSO-BUDGET

OPUS_EXECUTION_NOTES:
  chaos_test_structure: |
    # Follow S35 BUNNY pattern
    class TestWave1BitCountAttacks:
        def test_cv_bit_count_attempt(self): ...
        def test_cv_downstream_vector_scoring(self): ...
        def test_cv_hamming_distance_query(self): ...
        def test_cv_len_gates_passed(self): ...
        def test_cv_sort_by_bit_count(self): ...
    
    class TestWave2SchemaAttacks: ...
    class TestWave3AlertAttacks: ...
    class TestWave4DisplayAttacks: ...
    class TestWave5PredicateAttacks: ...
    class TestWave6Misc: ...
  
  population_count_enforcement: |
    # Pre-commit hook addition
    # Grep for forbidden patterns:
    FORBIDDEN_PATTERNS = [
        r'popcount',
        r'\.count\([\'"]1[\'"]\)',
        r'bin\(.+\)\.count',
        r'sum\(1 for',
        r'len\(\[.+gates_passed',
    ]
```

---

## NEX CAPABILITY MAPPING

```yaml
NEX_ADDRESSED:

  NEX-003_SCAN_ALL_SETUPS:
    fate: REIMAGINE
    s36_delivery: "Multi-pair scanner with bit-vector output"
    constraint: "Shuffled sort, no quality grades, no population counts"
    
  NEX-008_4Q_GATE_ANALYSIS:
    fate: REIMAGINE
    s36_delivery: "5-drawer evaluation with boolean gates"
    constraint: "gates_passed/failed only, no A/B/C/F, no counts"
    
  NEX-012_MULTI_PAIR_SCAN:
    fate: REIMAGINE
    s36_delivery: "Scanner returns all pairs in shuffled order"
    constraint: "No ranking by 'quality' or gate count"
    
  NEX-060_GRADE_A_ALERTS:
    fate: REIMAGINE
    s36_delivery: "Alerts on explicit gate combinations"
    constraint: "No 'Grade A' language anywhere, STATE_* naming"
```

---

## INVARIANTS CHECKLIST

```yaml
S36_INVARIANTS:

  # ORIGINAL (v0.1)
  INV-HARNESS-1:
    rule: "CSO outputs gate status only, never grades"
    tracks: A, B, C, D, E, F
    
  INV-HARNESS-2:
    rule: "No confidence scores unless explicit formula"
    tracks: B, E
    
  INV-HARNESS-3:
    rule: "Alerts fire on gate combinations, not quality"
    tracks: E
    
  INV-HARNESS-4:
    rule: "Multi-pair display randomized (not sorted by anything)"
    tracks: D
    
  INV-BIAS-PREDICATE:
    rule: "HTF bias as predicate status, not directional words"
    tracks: B
    
  INV-NO-UNSOLICITED:
    rule: "System never proposes"
    tracks: E
    
  # NEW (v0.2)
  INV-DRAWER-RULE-EXPLICIT:
    rule: "All drawer rollups declare exact boolean logic in conditions.yaml"
    tracks: A
    source: GPT + OWL
    
  INV-BITVECTOR-NO-POPULATION:
    rule: "System MUST NOT compute or expose bit-counts"
    tracks: C
    source: GPT + OWL + GROK (CONVERGENCE)
    
  INV-HARNESS-5:
    rule: "No downstream consumer shall count 1s or derive scalar from bit_vector"
    tracks: C
    source: GROK
    
  INV-DISPLAY-SHUFFLE:
    rule: "Multi-pair display uses randomized order to prevent position bias"
    tracks: D
    source: OWL
    
  INV-CSO-BUDGET:
    rule: "max_pairs=12 default, T2 override required for more"
    tracks: D
    source: GROK

TOTAL_S36_INVARIANTS: 11 (6 original + 5 new)
```

---

## OPUS EXECUTION CONCERNS + MITIGATIONS

```yaml
CONCERNS:

  C1_PREDICATE_DELTA_NON_NUMERIC:
    concern: "How to compute 'distance from threshold' for non-numeric predicates?"
    mitigation: |
      - Numeric predicates: delta = actual - threshold (e.g., "1.2 pips")
      - Boolean predicates: delta = null
      - Enum predicates: delta = "actual: {value}" (e.g., "actual: tokyo")
    risk: LOW
    
  C2_DISPLAY_SHUFFLE_IMPLEMENTATION:
    concern: "Per-render randomization or session-seeded?"
    mitigation: |
      - Default: Per-render (secrets.SystemRandom)
      - For test reproducibility: Accept seed parameter
      - Machine layer always deterministic (conditions.yaml order)
    risk: LOW
    
  C3_RATE_LIMITER_PERSISTENCE:
    concern: "In-memory rate limiter loses state on restart"
    mitigation: |
      - Primary: In-memory (deque with timestamps)
      - Backup: Write suppression_bead to persist knowledge of spam
      - On restart: Conservative rate limit until warm
    risk: LOW
    
  C4_EXISTING_CSO_CONFLICTS:
    concern: "Existing cso/contract.py has FourQGateResult, CSODecision"
    mitigation: |
      - FourQGateResult → FiveDrawerResult (rename + extend)
      - CSODecision.confidence field — needs review
      - Existing composite_gates in conditions.yaml can map to drawers
    risk: MEDIUM (requires careful refactoring)
    
  C5_24_CHAOS_VECTORS:
    concern: "24+ vectors is ambitious"
    mitigation: |
      - Follow S35 BUNNY pattern (proven)
      - Group into 6 waves (manageable)
      - Some vectors share test infrastructure
    risk: LOW (S35 did 24 in ~1hr)
```

---

## DAY-BY-DAY BUILD SEQUENCE

```yaml
DAY_1:
  track: A (5_DRAWER_SCHEMA)
  deliverables:
    - cso/schemas/drawer_schema.yaml
    - cso/schemas/gate_schema.yaml
    - Update cso/knowledge/conditions.yaml with drawer rules
  tests: 10+ schema validation tests
  gate: Schema rejects forbidden fields, drawer rules explicit

DAY_2:
  track: A + B (SCHEMA complete, EVALUATOR start)
  deliverables:
    - tests/test_cso/test_drawer_schema.py (complete)
    - cso/evaluator.py (skeleton)
    - cso/gate_registry.py
  gate: Track A EXIT

DAY_3:
  track: B (EVALUATOR complete)
  deliverables:
    - cso/evaluator.py (complete with predicate_delta)
    - cso/predicates/__init__.py
    - tests/test_cso/test_evaluator.py
  tests: 15+ evaluator tests
  gate: Track B EXIT — no aggregation helpers

DAY_4:
  track: C (BIT_VECTOR)
  deliverables:
    - cso/bit_vector.py (MACHINE_ONLY, no popcount)
    - cso/schemas/bit_vector_schema.yaml
    - tests/test_cso/test_bit_vector.py
  tests: 10+ bit vector tests
  gate: Track C EXIT — population count banned

DAY_5:
  track: D (SCANNER)
  deliverables:
    - cso/scanner.py (extend with shuffle, budget)
    - cso/multi_pair_result.py
    - tests/test_cso/test_multi_pair_scanner.py
  tests: 10+ scanner tests
  gate: Track D EXIT — shuffled output, budget enforced

DAY_6:
  track: E (ALERTS)
  deliverables:
    - cso/alerts.py
    - cso/alert_rules.yaml
    - cso/alert_linter.py
    - tests/test_cso/test_alerts.py
  tests: 15+ alert tests
  gate: Track E EXIT — no count language, rate limited

DAY_7:
  track: F (INTEGRATION + BUNNY)
  deliverables:
    - cso/harness.py
    - cso/api.py
    - tests/chaos/test_bunny_s36.py
  tests: 24+ chaos vectors
  gate: S36 EXIT — all invariants proven
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | DRAWER_SCHEMA | Schema rejects forbidden fields; rules in conditions.yaml |
| B | EVALUATOR | Boolean per gate, no aggregation helpers, delta on failure |
| C | BIT_VECTOR | MACHINE_ONLY, no popcount, UI shuffle |
| D | SCANNER | Shuffled output, budget enforced |
| E | ALERTS | Gate combinations only, no count language, rate limited |
| F | BUNNY | 24+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S36 COMPLETE

---

```yaml
STATUS: OPUS_EXECUTION_READY
PATTERN: PROVEN (S35 cooked in 1hr with same flow)
CONFIDENCE: HIGH
PRIMARY_RISK: Bit-vector population count (hardened with 5 dedicated vectors)
```

---

**CLEARED FOR EXECUTION.** 🐗🔥
