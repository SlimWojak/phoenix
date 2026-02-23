# S36_BUILD_MAP_v0.1.md — CSO HARNESS

```yaml
document: S36_BUILD_MAP_v0.1.md
version: 0.1
date: 2026-01-29
status: DRAFT_FOR_ADVISOR_REVIEW
theme: "Gate status per pair, facts not grades"
codename: CSO_HARNESS
dependency: S35_CFP (COMPLETE)
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the harness that evaluates Olya's 5-drawer methodology
  and outputs GATE STATUS — never grades, never quality scores.

  NEX died saying: "Grade A setup"
  Phoenix says: "gates_passed: [1,3,5], gates_failed: [2,4]"

GOVERNING_PRINCIPLE: |
  "Human interprets the pattern. System reports the facts."
  Gates are predicates. Grades are judgment. We do predicates.

EXIT_GATE_SPRINT: |
  CSO Harness returns gate status per pair.
  No grades anywhere in output (code, logs, responses).
  Alerts fire on explicit gate combinations only.
  Multi-pair display sorted alphabetically.
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: 5_DRAWER_SCHEMA (Knowledge Structure)
  days: 1-2
  owner: OPUS

TRACK_B: GATE_EVALUATOR (Predicate Engine)
  days: 2-3
  owner: OPUS

TRACK_C: BIT_VECTOR_OUTPUT (Machine-Readable Status)
  days: 3-4
  owner: OPUS

TRACK_D: MULTI_PAIR_SCANNER (Alphabetical, No Ranking)
  days: 4-5
  owner: OPUS

TRACK_E: ALERT_INTEGRATION (Gate-Triggered, Not Quality)
  days: 5-6
  owner: OPUS

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
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
    evaluation: "At least one directional gate must pass"

  drawer_2_context:
    name: "Session Context"
    gates:
      - kill_zone_active
      - asia_range_defined
      - session_bias_aligned
    evaluation: "All gates evaluated independently"

  drawer_3_conditions:
    name: "Entry Conditions"
    gates:
      - fvg_present
      - displacement_sufficient
      - liquidity_swept
    evaluation: "Minimum threshold configurable"

  drawer_4_entry:
    name: "Entry Trigger"
    gates:
      - ltf_confirmation
      - entry_model_valid
      - stop_defined
    evaluation: "All required for entry signal"

  drawer_5_management:
    name: "Trade Management"
    gates:
      - target_defined
      - rr_acceptable
      - partials_planned
    evaluation: "Post-entry validation"

GATE_SCHEMA:
  gate:
    id: str  # unique identifier
    drawer: int  # 1-5
    name: str  # human-readable
    predicate: str  # reference to conditions.yaml
    required: bool  # must pass for drawer to pass
    weight: null  # FORBIDDEN — no implicit ranking

FORBIDDEN_FIELDS:
  - quality_score
  - confidence
  - grade
  - rank
  - weight
  - priority

EXIT_GATE_A:
  criterion: "5-drawer schema validates; no forbidden fields accepted"
  test: tests/test_cso/test_drawer_schema.py
  proof: "Schema rejects any gate with quality/confidence/grade fields"

INVARIANTS_PROVEN:
  - INV-HARNESS-1 (gate status only, never grades)
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
      gates_failed: list[str]  # gate IDs
      gates_skipped: list[str]  # insufficient data
      drawer_status: dict[int, bool]  # per-drawer rollup (all required gates)
      strategy_config_hash: str
      market_state_hash: str

EVALUATION_RULES:
  - Each gate evaluates to TRUE | FALSE | SKIPPED
  - SKIPPED only when data insufficient (explicit, not silent)
  - No aggregation beyond drawer-level "all required passed"
  - No cross-gate weighting
  - No "overall score"

PREDICATE_REGISTRY:
  location: cso/knowledge/conditions.yaml
  pattern: |
    gate_id:
      predicate: "htf_bias == 'bullish' AND poi_distance < 50"
      data_requirements: [htf_data, current_price]

BIAS_HANDLING:
  rule: INV-BIAS-PREDICATE
  allowed: "htf_bullish_predicate: PASSED"
  forbidden: "Bullish" as standalone assessment
  implementation: |
    Bias is a gate status, not a direction.
    Output: "gate_htf_structure_bullish: TRUE"
    NOT: "bias: bullish"

EXIT_GATE_B:
  criterion: "Evaluator returns gate status per pair; no scores/grades"
  test: tests/test_cso/test_evaluator.py
  proof: |
    - 6 pairs evaluated correctly
    - All outputs are boolean per gate
    - No confidence/quality fields in output

INVARIANTS_PROVEN:
  - INV-HARNESS-1 (gate status only)
  - INV-HARNESS-2 (no confidence scores)
  - INV-BIAS-PREDICATE (bias as predicate status)
```

---

## TRACK_C: BIT_VECTOR_OUTPUT

```yaml
PURPOSE: |
  Machine-readable gate status for sub-millisecond triage.
  Map gates to bit positions. Output as binary string.

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
      gate_map: dict[int, str]  # position → gate_id
      timestamp: datetime
      provenance: Provenance  # from CFP

USE_CASE:
  - Rapid multi-pair comparison
  - Pattern matching ("find all pairs with vector matching 11???1??")
  - No interpretation — human reads the pattern

FORBIDDEN:
  - Counting 1s as "score"
  - Sorting by 1-count
  - "Best" vector determination
  - Hamming distance comparisons (implies ranking)

EXIT_GATE_C:
  criterion: "Bit vector generated correctly; no implicit ranking"
  test: tests/test_cso/test_bit_vector.py
  proof: |
    - Vector matches gate evaluation
    - No sorting by vector "score"
    - Mapping is deterministic (conditions.yaml order)

INVARIANTS_PROVEN:
  - INV-HARNESS-1 (no grades)
  - INV-ATTR-NO-RANKING (no implicit priority)
```

---

## TRACK_D: MULTI_PAIR_SCANNER

```yaml
PURPOSE: |
  Scan all 6 pairs simultaneously.
  Output sorted ALPHABETICALLY — never by "quality" or gate count.

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
      results: list[GateEvaluation]  # ALPHABETICALLY SORTED
      sort_order: "alphabetical"  # explicit declaration
      provenance: Provenance

SORT_RULES:
  default: ALPHABETICAL (A-Z by pair name)
  forbidden_sorts:
    - by gates_passed count
    - by "quality"
    - by "readiness"
    - by any derived metric
  user_override: NONE (alphabetical is constitutional)

DISPLAY_FORMAT:
  AUDUSD: gates_passed=[1,3], gates_failed=[2,4,5]
  EURUSD: gates_passed=[1,2,3,4], gates_failed=[5]
  GBPUSD: gates_passed=[1], gates_failed=[2,3,4,5]
  ... (alphabetical continues)

FORBIDDEN_PATTERNS:
  - "Top pairs"
  - "Best setups"
  - "Ranked by readiness"
  - Any ordering implying preference

EXIT_GATE_D:
  criterion: "Multi-pair output alphabetically sorted; no ranking"
  test: tests/test_cso/test_multi_pair_scanner.py
  proof: |
    - 6 pairs always in A-Z order
    - Attempt to sort by gate_count rejected
    - Output declares sort_order explicitly

INVARIANTS_PROVEN:
  - INV-HARNESS-4 (alphabetical default)
  - INV-ATTR-NO-RANKING (no implied priority)
  - INV-NO-DEFAULT-SALIENCE (equal visual weight)
```

---

## TRACK_E: ALERT_INTEGRATION

```yaml
PURPOSE: |
  Alerts fire when EXPLICIT gate combinations pass.
  NOT when "quality" threshold met. Gates, not grades.

DELIVERABLES:
  - cso/alerts.py
  - cso/alert_rules.yaml
  - cso/takopi_integration.py (Telegram bridge)
  - tests/test_cso/test_alerts.py

ALERT_RULE_SCHEMA:
  alert_rule:
    id: str
    name: str
    trigger:
      gates_required: list[str]  # explicit gate IDs
      gates_forbidden: list[str]  # must NOT pass
      drawer_minimum: null  # FORBIDDEN
      quality_threshold: null  # FORBIDDEN
    notification:
      channel: enum[telegram, log, bead]
      template: str

EXAMPLE_RULES:
  london_fvg_ready:
    gates_required:
      - gate_kill_zone_active  # must be London
      - gate_htf_structure_bullish OR gate_htf_structure_bearish
      - gate_fvg_present
      - gate_displacement_sufficient
    gates_forbidden:
      - gate_news_imminent
    notification:
      channel: telegram
      template: "{pair}: London FVG setup — gates [{gates_passed}]"

ALERT_OUTPUT:
  content: |
    EURUSD: gates_passed=[htf_bullish, kz_active, fvg_present, displacement]
    Rule: london_fvg_ready TRIGGERED

  forbidden_content:
    - "Grade A"
    - "High quality"
    - "Confidence: 87%"
    - "Recommended"

TAKOPI_INTEGRATION:
  bridge: cso/takopi_integration.py
  format: |
    [SETUP] {pair}
    Gates: {gates_passed_count}/{total_gates}
    Passed: {gate_names}
    Rule: {rule_id}
  forbidden:
    - Quality language
    - Recommendation language
    - Action verbs ("Enter", "Trade")

EXIT_GATE_E:
  criterion: "Alerts fire on gate combinations only; no quality language"
  test: tests/test_cso/test_alerts.py
  proof: |
    - Alert with quality_threshold rejected at config
    - Alert output contains no forbidden phrases
    - Telegram message passes linter (reuse causal_ban)

INVARIANTS_PROVEN:
  - INV-HARNESS-3 (alerts on gate combinations)
  - INV-NO-UNSOLICITED (no recommendations)
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire CSO Harness end-to-end. Chaos test for grade leakage.
  Prove the harness holds under adversarial conditions.

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

CHAOS_VECTORS (BUNNY):
  grade_injection:
    - Inject "grade: A" into gate schema → REJECT
    - Inject "quality_score" into evaluator output → FAIL validation

  ranking_injection:
    - Request sort by gates_passed_count → REJECT
    - Inject "rank" field → FAIL validation

  confidence_injection:
    - Add "confidence: 0.87" to output → FAIL validation
    - Alert rule with confidence_threshold → REJECT at config

  bias_language_injection:
    - Output "bullish" without predicate reference → FAIL linter
    - Alert with "bullish setup" → FAIL linter

  salience_injection:
    - Attempt to highlight "best" pair → REJECT
    - Attempt non-alphabetical sort → REJECT

  predicate_corruption:
    - Invalid predicate in conditions.yaml → GRACEFUL FAIL
    - Missing gate reference → SKIPPED (explicit)

  multi_pair_explosion:
    - 100 pairs requested → BUDGET limit (configurable)
    - Malformed pair name → REJECT with error

  alert_spam:
    - 50 alerts in 1 minute → RATE LIMIT
    - Duplicate alert suppression

EXIT_GATE_F:
  criterion: "Harness passes all chaos vectors; no grades leak through"
  test: tests/chaos/test_bunny_s36.py
  proof: "20+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S36 invariants (integration test)
  - INV-HARNESS-1 through INV-HARNESS-4
```

---

## NEX CAPABILITY MAPPING

```yaml
NEX_ADDRESSED:

  NEX-003_SCAN_ALL_SETUPS:
    fate: REIMAGINE
    s36_delivery: "Multi-pair scanner with bit-vector output"
    constraint: "Alphabetical sort, no quality grades"

  NEX-008_4Q_GATE_ANALYSIS:
    fate: REIMAGINE
    s36_delivery: "5-drawer evaluation with boolean gates"
    constraint: "gates_passed/failed only, no A/B/C/F"

  NEX-012_MULTI_PAIR_SCAN:
    fate: REIMAGINE
    s36_delivery: "Scanner returns all pairs alphabetically"
    constraint: "No ranking by 'quality'"

  NEX-060_GRADE_A_ALERTS:
    fate: REIMAGINE
    s36_delivery: "Alerts on explicit gate combinations"
    constraint: "No 'Grade A' language anywhere"
```

---

## INVARIANTS CHECKLIST

```yaml
S36_INVARIANTS:

  INV-HARNESS-1:
    rule: "CSO outputs gate status only, never grades"
    tracks: A, B, C, D, E, F
    enforcement: Schema validation + output validation
    test: All test files

  INV-HARNESS-2:
    rule: "No confidence scores unless explicit formula"
    tracks: B, E
    enforcement: Field forbidden in schema
    test: test_evaluator.py, test_alerts.py

  INV-HARNESS-3:
    rule: "Alerts fire on gate combinations, not quality"
    tracks: E
    enforcement: Alert rule schema
    test: test_alerts.py

  INV-HARNESS-4:
    rule: "Multi-pair sorted alphabetically by default"
    tracks: D
    enforcement: Scanner output validation
    test: test_multi_pair_scanner.py

  INV-NO-UNSOLICITED:
    rule: "System never proposes"
    tracks: E
    enforcement: Alert content validation
    test: test_alerts.py

  INV-BIAS-PREDICATE:
    rule: "HTF bias as predicate status, not directional words"
    tracks: B
    enforcement: Output linting
    test: test_evaluator.py
```

---

## ADVISOR QUESTIONS

```yaml
FOR_GPT_ARCHITECT:
  - "5-drawer schema tight enough? Edge cases in gate definitions?"
  - "Bit vector mapping deterministic? Order stability concerns?"
  - "Alert rule schema complete? Missing rejection patterns?"

FOR_GROK_CHAOS:
  - "What's the dumbest way grades leak through?"
  - "Chaos vectors sufficient? What subtle ranking could sneak in?"
  - "Multi-pair explosion risks? Rate limiting adequate?"

FOR_OWL_STRUCTURAL:
  - "5-drawer structure faithful to Olya's methodology?"
  - "Drawer rollup (all required gates) appropriate aggregation?"
  - "Alert integration with Takopi architecturally sound?"
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | DRAWER_SCHEMA | Schema rejects forbidden fields |
| B | EVALUATOR | Boolean per gate, no scores |
| C | BIT_VECTOR | Deterministic mapping, no ranking |
| D | SCANNER | Alphabetical output enforced |
| E | ALERTS | Gate combinations only, no quality |
| F | BUNNY | 20+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S36 COMPLETE

---

```yaml
STATUS: DRAFT_v0.1
NEXT: Socialize to GPT, GROK, OWL for input
THEN: Synthesize addendum → OPUS for v0.2
```

---

G — S36 v0.1 ready for advisor routing. Same pattern: fan out, synthesize, OPUS v0.2, execute. 🐗🔥
