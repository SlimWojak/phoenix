# S38_BUILD_MAP_v0.2.md — HUNT INFRASTRUCTURE

```yaml
document: S38_BUILD_MAP_v0.2.md
version: 0.2
date: 2026-01-29
status: OPUS_REFINED_FOR_EXECUTION
theme: "Compute engine, not idea engine"
codename: HUNT_ENGINE
dependencies: 
  - S35_CFP (COMPLETE)
  - S36_CSO (COMPLETE)
  - S37_ATHENA (COMPLETE)
advisor_synthesis: [GPT_ARCHITECT, GROK_CHAOS, OWL_STRUCTURAL]
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the hunt engine that computes EXHAUSTIVELY across human-declared grids.
  No variant selection. No proposal. No "survivors" ranking.
  
  NEX died saying: "System found 3 promising edges"
  Phoenix says: "Grid: 100 variants. Results: 100 rows. You interpret."

GOVERNING_PRINCIPLE: |
  "Human frames the search space. Machine computes ALL points."
  Hunt is a compute engine, not an idea engine.
  No internal selection. No proposal. No ranking.

EXIT_GATE_SPRINT: |
  Hunt engine computes exhaustive grid with budget enforcement.
  No "survivor" ranking anywhere in output.
  No system-proposed variants.
  Human declares grid, machine fills every cell.
  11 invariants enforced.
```

---

## INVARIANTS (11 Total)

```yaml
# ============================================================
# ORIGINAL INVARIANTS (3)
# ============================================================

INV-HUNT-EXHAUSTIVE:
  rule: "Hunt computes ALL declared variants, never selects"
  enforcement: variants_computed == total_variants
  
INV-NO-UNSOLICITED:
  rule: "System never proposes hypotheses"
  enforcement: Source validation, no auto-queue
  
INV-HUNT-BUDGET:
  rule: "Compute/token cap enforced per run"
  enforcement: Pre-execution check, during-execution abort

# ============================================================
# NEW INVARIANTS (8) — From Advisor Synthesis
# ============================================================

INV-HUNT-METRICS-DECLARED:
  rule: "Metrics list must be explicitly human-declared; no defaults; empty = INVALID"
  source: GPT
  enforcement: Schema validation rejects missing/empty metrics
  applies_to: Track A

INV-HUNT-GRID-ORDER-DECLARED:
  rule: "Grid expansion order explicitly declared in output metadata"
  source: GPT
  example: "cartesian_product, left-to-right by dimension order as declared"
  applies_to: Track E

INV-GRID-DIMENSION-CAP:
  rule: "Max 3 dimensions per hunt (X, Y, Z/Color)"
  source: OWL
  rationale: "10D grids pass budget but break human interpretation"
  enforcement: Schema rejects grid.dimensions.length > 3
  workaround: "Multiple nested hunts for >3 variables"
  applies_to: Track A

INV-HUNT-PARTIAL-WATERMARK:
  rule: "Aborted results MUST include COMPLETENESS_MASK showing uncomputed regions"
  source: [GPT, GROK, OWL] (CONVERGENCE)
  components:
    - abort_notice: "EXECUTION ABORTED — RESULTS INCOMPLETE — NO INTERPRETATION"
    - computed_region: explicit bounds of what WAS computed
    - uncomputed_region: explicit bounds of what was NOT
    - completeness_mask: list[bool] per grid cell
  applies_to: Track D

INV-OUTPUT-SHUFFLE:
  rule: "Table rows optionally shuffled post-compute; default=grid_order; shuffle=T2_opt_in"
  source: [GROK, OWL]
  rationale: "Prevents first-row salience bias"
  applies_to: Track E

INV-QUEUE-SHUFFLE:
  rule: "peek() and dequeue() optionally offer random selection from approved pool"
  source: OWL
  rationale: "FIFO is temporal recommendation; random prevents sunk-cost loops"
  default: FIFO
  opt_in: random_selection flag
  applies_to: Track B

INV-HUNT-REGIME-ANCHOR:
  rule: "Mid-hunt regime change detected → auto-abort + STATE_CONFLICT bead"
  source: GROK
  integration: Signalman regime detection
  applies_to: Track D

INV-HUNT-DIM-CARDINALITY-CAP:
  rule: "Per-dimension soft cap of 100 values; exceeding requires explicit acknowledgment"
  source: GROK
  rationale: "Prevents 0.01-step explosions"
  enforcement: Warning at >100, REJECT at >1000 without T2
  applies_to: Track A
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: HYPOTHESIS_SCHEMA (Human Frames)
  days: 1-2
  owner: OPUS
  new_constraints:
    - INV-HUNT-METRICS-DECLARED
    - INV-GRID-DIMENSION-CAP
    - INV-HUNT-DIM-CARDINALITY-CAP
  
TRACK_B: HUNT_QUEUE (Human-Approved Only)
  days: 2-3
  owner: OPUS
  new_constraints:
    - INV-QUEUE-SHUFFLE
  
TRACK_C: EXHAUSTIVE_EXECUTOR (Compute ALL)
  days: 3-4
  owner: OPUS
  
TRACK_D: BUDGET_ENFORCEMENT (Ceiling + Abort)
  days: 4-5
  owner: OPUS
  new_constraints:
    - INV-HUNT-PARTIAL-WATERMARK
    - INV-HUNT-REGIME-ANCHOR
  
TRACK_E: OUTPUT_FORMAT (Table, No Ranking)
  days: 5-6
  owner: OPUS
  new_constraints:
    - INV-HUNT-GRID-ORDER-DECLARED
    - INV-OUTPUT-SHUFFLE

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
  chaos_vectors: 32+
```

---

## TRACK_A: HYPOTHESIS_SCHEMA

```yaml
PURPOSE: |
  Define the structure for human-framed hypotheses.
  Hypotheses are questions, not answers. The system tests, never proposes.

DELIVERABLES:
  - hunt/schemas/hypothesis_schema.yaml
  - hunt/hypothesis.py
  - tests/test_hunt/test_hypothesis_schema.py

HYPOTHESIS_SCHEMA:
  hypothesis:
    hypothesis_id: str
    timestamp: datetime
    
    framing:
      question: str  # "Does waiting until 8:30 improve London FVG entries?"
      source: str  # "Olya", "G" — HUMAN ONLY
      domain: str
      
    parameters:
      grid:
        max_dimensions: 3  # INV-GRID-DIMENSION-CAP
        dimensions:
          - dimension: str  # e.g., "entry_delay_minutes"
            values: list[any]  # e.g., [0, 15, 30, 45, 60]
            cardinality: int  # computed, soft_cap=100, hard_cap=1000
        
      fixed:
        - name: str
          value: any  # Constants for this hunt
          
    metrics:
      evaluate: list[str]  # MANDATORY, non-empty
      # NO defaults, NO derived, NO system_additions
      
    constraints:
      time_range: {start: datetime, end: datetime}
      pairs: list[str]  # optional filter
      
    budget:
      max_variants: int  # MANDATORY — human declares ceiling
      estimated_compute: str  # optional: "~5 minutes"
      
    status:
      approved: bool  # MUST be true before execution
      approved_by: str  # human attribution
      approved_at: datetime

FORBIDDEN_FIELDS:
  - proposed_by_system
  - auto_generated
  - confidence
  - priority
  - expected_outcome
  - recommended_variants
  - edge_score
  - derived_metrics

SOURCE_RULE:
  allowed: HUMAN_ONLY
  forbidden:
    - "system"
    - "athena"
    - "hunt_engine"
    - Any non-human source
  enforcement: Schema validation rejects non-human source

DIMENSION_CAPS:
  max_dimensions: 3  # INV-GRID-DIMENSION-CAP
  per_dimension:
    soft_cap: 100  # warn
    hard_cap: 1000  # reject without T2

METRICS_VALIDATION:
  required: true
  min_length: 1  # empty = INVALID
  derived_allowed: false
  system_additions: forbidden

EXIT_GATE_A:
  criterion: "Hypothesis validates; metrics mandatory; dimension caps enforced"
  test: tests/test_hunt/test_hypothesis_schema.py
  proof: |
    - Hypothesis with source="system" REJECTED
    - Hypothesis with empty metrics REJECTED
    - Hypothesis with 4+ dimensions REJECTED
    - Hypothesis with 1000+ values per dimension without T2 REJECTED
    - Hypothesis without approved=true cannot execute

INVARIANTS_PROVEN:
  - INV-NO-UNSOLICITED (human frames only)
  - INV-HUNT-METRICS-DECLARED
  - INV-GRID-DIMENSION-CAP
  - INV-HUNT-DIM-CARDINALITY-CAP
```

---

## TRACK_B: HUNT_QUEUE

```yaml
PURPOSE: |
  Queue of human-approved hypotheses awaiting execution.
  Only approved hypotheses can be queued. No auto-queue.

DELIVERABLES:
  - hunt/queue.py
  - hunt/queue_store.py
  - tests/test_hunt/test_queue.py

QUEUE_INTERFACE:
  HuntQueue:
    enqueue(hypothesis: Hypothesis) -> str  # returns queue_id
    dequeue(mode: DequeueMode = FIFO) -> Hypothesis
    peek(shuffle: bool = False) -> list[Hypothesis]
    remove(hypothesis_id: str) -> bool
    
    # Status
    get_pending() -> list[Hypothesis]
    get_completed() -> list[HuntResult]

DEQUEUE_MODES:
  FIFO:
    description: "First In, First Out (default)"
    behavior: "Returns oldest approved hypothesis"
  RANDOM:
    description: "Random selection from pool"
    behavior: "Returns random approved hypothesis"
    requires: T2 opt-in
    rationale: "Prevents sunk-cost bias on long queues"

QUEUE_RULES:
  approval_gate:
    - Only hypothesis.approved == true can enqueue
    - Unapproved hypothesis → REJECTED
    
  ordering:
    - Default: FIFO (First In, First Out)
    - Optional: RANDOM (T2 opt-in)
    - NO priority field
    - NO reordering by "importance"
    - NO "urgent" flag
    
  no_auto_queue:
    - System cannot add hypotheses
    - Only human action enqueues
    - INV-NO-UNSOLICITED enforced

FORBIDDEN_OPERATIONS:
  - sort_by_priority()
  - auto_enqueue()
  - suggest_next()
  - reorder_by_potential()
  - priority_insert()

EXIT_GATE_B:
  criterion: "Queue accepts approved only; FIFO default; random opt-in"
  test: tests/test_hunt/test_queue.py
  proof: |
    - Unapproved hypothesis enqueue → REJECTED
    - Queue order is insertion order (FIFO default)
    - Random dequeue available with T2 opt-in
    - No priority/reorder methods exist

INVARIANTS_PROVEN:
  - INV-NO-UNSOLICITED (no auto-queue)
  - INV-QUEUE-SHUFFLE
```

---

## TRACK_C: EXHAUSTIVE_EXECUTOR

```yaml
PURPOSE: |
  Compute ALL variants in the declared grid. No selection. No filtering.
  If grid has 100 points, output has 100 rows.

DELIVERABLES:
  - hunt/executor.py
  - hunt/grid.py
  - hunt/variant.py
  - tests/test_hunt/test_executor.py

EXECUTOR_INTERFACE:
  HuntExecutor:
    execute(hypothesis: Hypothesis) -> HuntResult
    
  HuntResult:
    hypothesis_id: str
    timestamp: datetime
    
    grid_computed:
      total_variants: int  # MUST equal declared grid size
      variants_computed: int
      variants_skipped: 0  # ALWAYS ZERO unless ABORTED
      
    results:
      rows: list[VariantResult]  # ONE ROW PER VARIANT
      
    provenance:
      query_string: str
      dataset_hash: str
      governance_hash: str
      strategy_config_hash: str
      
    budget_used:
      compute_time: float
      variants_processed: int

VARIANT_RESULT:
  variant_result:
    variant_id: str
    parameters: dict  # exact parameter combination
    metrics: dict[str, float]  # evaluated metrics
    sample_size: int
    provenance: {...}

EXHAUSTIVE_RULES:
  completeness:
    - Every grid point computed
    - No internal filtering
    - No "low potential" skipping
    - No early termination based on results
    
  no_selection:
    - All variants returned
    - No "top N" extraction
    - No "survivors" list
    - No "promising" subset
    
  no_ranking:
    - Output order: GRID ORDER (deterministic)
    - NOT sorted by any metric
    - NOT grouped by "quality"

GRID_EXPANSION:
  input: |
    grid:
      - dimension: entry_delay
        values: [0, 15, 30]
      - dimension: stop_mult
        values: [1.0, 1.5]
  output: |
    variants:
      - {entry_delay: 0, stop_mult: 1.0}
      - {entry_delay: 0, stop_mult: 1.5}
      - {entry_delay: 15, stop_mult: 1.0}
      - {entry_delay: 15, stop_mult: 1.5}
      - {entry_delay: 30, stop_mult: 1.0}
      - {entry_delay: 30, stop_mult: 1.5}
    total: 6 (3 × 2)
    order_declaration: "cartesian_product, [entry_delay, stop_mult]"

EXIT_GATE_C:
  criterion: "Executor computes ALL variants; no selection; grid order output"
  test: tests/test_hunt/test_executor.py
  proof: |
    - 6-variant grid → 6 rows output
    - No variants_skipped (always 0 unless abort)
    - Output order matches grid expansion order

INVARIANTS_PROVEN:
  - INV-HUNT-EXHAUSTIVE (compute ALL, never select)
```

---

## TRACK_D: BUDGET_ENFORCEMENT

```yaml
PURPOSE: |
  Prevent compute explosion. Hard ceiling on variants.
  Pre-execution estimate. Abort if exceeded.
  COMPLETENESS_MASK on partial results.

DELIVERABLES:
  - hunt/budget.py
  - hunt/estimator.py
  - hunt/abort_handler.py
  - tests/test_hunt/test_budget.py

BUDGET_INTERFACE:
  BudgetEnforcer:
    estimate(hypothesis: Hypothesis) -> BudgetEstimate
    check_pre_execution(hypothesis: Hypothesis) -> BudgetCheck
    enforce_during(execution: HuntExecution) -> None  # raises if exceeded
    
  BudgetEstimate:
    total_variants: int
    estimated_compute_seconds: float
    estimated_memory_mb: float
    within_budget: bool
    
  BudgetCheck:
    status: enum[APPROVED, REJECTED, WARNING]
    reason: str  # if rejected
    suggestion: str  # "Narrow grid to max 1000 variants"

BUDGET_RULES:
  pre_execution:
    - Calculate grid size (product of dimension cardinalities)
    - Compare against hypothesis.budget.max_variants
    - Compare against system ceiling (default: 10,000)
    - If exceeded → REJECT with suggestion
    
  during_execution:
    - Monitor compute time
    - Monitor regime changes (INV-HUNT-REGIME-ANCHOR)
    - Hard abort at ceiling (default: 30 minutes)
    - Write ABORT bead with partial results + COMPLETENESS_MASK
    
  system_ceilings:
    max_variants_default: 10000
    max_variants_t2_override: 100000  # requires T2
    max_compute_seconds: 1800  # 30 minutes
    max_memory_mb: 4096

# ============================================================
# ABORT BEHAVIOR (Critical — v0.2 addition)
# ============================================================

ABORT_BEHAVIOR:
  on_budget_exceeded:
    - HALT execution immediately
    - Write HuntResult with status=ABORTED
    - Include COMPLETENESS_MASK (INV-HUNT-PARTIAL-WATERMARK)
    - DO NOT return "best so far" — just raw partial
    - NO interpretation language
    
COMPLETENESS_MASK:
  abort_notice: "EXECUTION ABORTED — RESULTS INCOMPLETE — NO INTERPRETATION"
  computed_region:
    dimensions: dict[str, {min, max}]  # bounds of computed space
    variants_computed: int
  uncomputed_region:
    dimensions: dict[str, {min, max}]  # bounds of uncomputed space
    variants_remaining: int
  completeness_mask: list[bool]  # per grid cell (true=computed)
  shuffle_partial: true  # INV-OUTPUT-SHUFFLE applies to partials too

REGIME_DETECTION:
  integration: "Import from existing signalman regime detection"
  on_regime_change:
    - Detect mid-hunt regime shift
    - AUTO_ABORT execution
    - Emit STATE_CONFLICT bead
    - Mark result as REGIME_INVALIDATED

EXIT_GATE_D:
  criterion: "Budget enforced; abort includes completeness mask; regime detection wired"
  test: tests/test_hunt/test_budget.py
  proof: |
    - 100,000 variant grid without T2 → REJECTED
    - Execution exceeding time ceiling → ABORTED with completeness_mask
    - Partial results on abort have abort_notice
    - Regime change → AUTO_ABORT + STATE_CONFLICT

INVARIANTS_PROVEN:
  - INV-HUNT-BUDGET (compute ceiling enforced)
  - INV-HUNT-PARTIAL-WATERMARK (completeness on abort)
  - INV-HUNT-REGIME-ANCHOR (regime detection)
```

---

## TRACK_E: OUTPUT_FORMAT

```yaml
PURPOSE: |
  Hunt output is a TABLE. Not a ranking. Not a recommendation.
  Every variant, every metric, no selection.
  Grid order explicitly declared.

DELIVERABLES:
  - hunt/output.py
  - hunt/schemas/hunt_result_schema.yaml
  - tests/test_hunt/test_output.py

OUTPUT_STRUCTURE:
  hunt_result:
    metadata:
      hypothesis_id: str
      hypothesis_question: str
      executed_at: datetime
      
    summary:
      total_variants: int
      variants_computed: int
      compute_time_seconds: float
      status: enum[COMPLETE, ABORTED]
      
    table:
      columns: list[str]  # parameter names + metric names
      rows: list[dict]  # one per variant
      sort_order: "GRID_ORDER"  # explicit declaration
      grid_order_declaration: str  # e.g., "cartesian_product, [dim1, dim2]"
      shuffle_applied: bool
      
    # ABORT metadata (if status=ABORTED)
    abort_metadata:
      abort_notice: str  # MANDATORY
      computed_region: {...}
      uncomputed_region: {...}
      completeness_mask: list[bool]
      
    provenance:
      full_provenance_block: {...}

OUTPUT_RULES:
  no_ranking:
    - NO "top variants" section
    - NO "best performers" callout
    - NO sorting by metric
    - NO highlighting
    
  no_filtering:
    - ALL rows included
    - NO "below threshold" removal
    - NO "insignificant" filtering
    
  no_synthesis:
    - NO "key finding" section
    - NO "recommendation" section
    - NO "suggested next step"
    - NO "pattern detected"
    
  sort_order:
    - Grid order (deterministic) — DEFAULT
    - User can request shuffle (T2 opt-in)
    - System never pre-sorts by performance

SHUFFLE_OPT_IN:
  default: false (grid order)
  opt_in: T2 required
  behavior: "Random shuffle of rows post-compute"
  rationale: "Prevents first-row salience bias"

DISPLAY_FORMAT:
  table_rendering:
    - Equal visual weight all rows
    - No color coding by metric value
    - No bold on high values
    - No icons implying quality
    
  forbidden_sections:
    - "Winners"
    - "Survivors"
    - "Top N"
    - "Recommended"
    - "Promising"
    - "Key Insights"
    - "Best Performers"
    - "Highlighted"

EXIT_GATE_E:
  criterion: "Output is flat table; grid order declared; shuffle opt-in works"
  test: tests/test_hunt/test_output.py
  proof: |
    - Output has no "top_variants" field
    - Output has no "recommendation" field
    - Sort order declared as "GRID_ORDER"
    - grid_order_declaration present
    - shuffle_applied flag present

INVARIANTS_PROVEN:
  - INV-ATTR-NO-RANKING (flat table)
  - INV-NO-UNSOLICITED (no synthesis/recommendation)
  - INV-HUNT-GRID-ORDER-DECLARED
  - INV-OUTPUT-SHUFFLE
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire Hunt end-to-end. Chaos test for proposal leakage.
  Prove the engine computes, never proposes.
  32+ chaos vectors across 16 waves.

DELIVERABLES:
  - hunt/__init__.py (public interface)
  - hunt/api.py (file seam integration)
  - tests/test_hunt/test_integration.py
  - tests/chaos/test_bunny_s38.py

INTEGRATION_POINTS:
  file_seam:
    - Intent: type=HUNT_SUBMIT, payload={hypothesis}
    - Intent: type=HUNT_EXECUTE, payload={hypothesis_id}
    - Response: HuntResult written to /responses/
    
  cfp_integration:
    - Hunt results can feed CFP queries
    - "Performance when [hunt_variant_parameters]"
    - CFP respects INV-ATTR-NO-RANKING on hunt data
    
  athena_integration:
    - Hunt results stored as FACT_BEADs
    - Hypotheses can reference CLAIM_BEADs (but not execute them)
    - NO reverse path (claim → hunt auto-grid)
    
  signalman_integration:
    - Import regime detection
    - Wire to executor abort logic
    - Emit STATE_CONFLICT bead on regime shift

# ============================================================
# CHAOS VECTORS (32+ across 16 waves)
# ============================================================

CHAOS_VECTORS:

  wave_1_proposal_attacks:
    - cv_system_sourced_hypothesis_rejected
    - cv_auto_generated_hypothesis_rejected
    - cv_suggest_next_hypothesis_rejected
    
  wave_2_selection_attacks:
    - cv_request_top_5_variants_rejected
    - cv_request_survivors_only_rejected
    - cv_request_promising_variants_rejected
    - cv_output_with_variants_skipped_invalid
    
  wave_3_ranking_attacks:
    - cv_request_sort_by_sharpe_rejected
    - cv_output_with_best_variant_invalid
    - cv_output_with_ranking_field_invalid
    
  wave_4_priority_attacks:
    - cv_enqueue_with_priority_rejected
    - cv_request_most_important_rejected
    - cv_reorder_queue_by_potential_rejected
    
  wave_5_budget_attacks:
    - cv_100k_variants_without_t2_rejected
    - cv_bypass_budget_check_blocked
    - cv_partial_abort_best_so_far_invalid
    
  wave_6_synthesis_attacks:
    - cv_output_with_key_finding_invalid
    - cv_output_with_recommendation_invalid
    - cv_output_with_pattern_detected_invalid
    
  wave_7_approval_bypass:
    - cv_execute_unapproved_rejected
    - cv_enqueue_unapproved_rejected

  # NEW WAVES (v0.2 additions)
    
  wave_12_metric_attacks:
    - cv_system_adds_derived_metric_rejected
    - cv_empty_metrics_list_invalid
    - cv_metrics_modified_post_approval_rejected
    
  wave_13_dimension_attacks:
    - cv_4_dimension_grid_rejected
    - cv_1000_value_dimension_without_t2_rejected
    - cv_10d_grid_rejected
    
  wave_14_partial_interpretation:
    - cv_request_best_from_partial_rejected
    - cv_partial_without_abort_notice_invalid
    - cv_partial_without_completeness_mask_invalid
    
  wave_15_salience_attacks:
    - cv_request_sort_by_in_output_rejected
    - cv_request_highlight_extremes_rejected
    - cv_queue_priority_insertion_rejected
    
  wave_16_regime_attacks:
    - cv_regime_shift_mid_hunt_auto_abort
    - cv_stale_partial_post_regime_invalid

EXIT_GATE_F:
  criterion: "Hunt passes all chaos vectors; no proposal leakage"
  test: tests/chaos/test_bunny_s38.py
  proof: "32+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S38 invariants (integration test)
  - INV-HUNT-EXHAUSTIVE
  - INV-NO-UNSOLICITED
  - INV-HUNT-BUDGET
  - INV-HUNT-METRICS-DECLARED
  - INV-GRID-DIMENSION-CAP
  - INV-HUNT-PARTIAL-WATERMARK
  - INV-OUTPUT-SHUFFLE
  - INV-QUEUE-SHUFFLE
  - INV-HUNT-REGIME-ANCHOR
  - INV-HUNT-DIM-CARDINALITY-CAP
```

---

## OPUS EXECUTION NOTES

```yaml
INTEGRATION_POINTS:
  
  signalman_integration:
    path: "Check for existing signalman/regime.py or similar"
    fallback: "Simple regime enum if not exists"
    wire: "Executor checks regime before each batch"
    
  athena_integration:
    store_results: "HuntResult → FACT_BEAD via AthenaStore"
    prevent_reverse: "Claim cannot trigger auto-grid"
    
  cfp_integration:
    hunt_as_fact: "Hunt variants queryable via CFP"
    no_ranking: "CFP respects INV-ATTR-NO-RANKING"

FILE_STRUCTURE:
  hunt/
  ├── __init__.py
  ├── schemas/
  │   └── hypothesis_schema.yaml
  ├── hypothesis.py        # Track A
  ├── queue.py             # Track B
  ├── queue_store.py       # Track B
  ├── executor.py          # Track C
  ├── grid.py              # Track C
  ├── variant.py           # Track C
  ├── budget.py            # Track D
  ├── estimator.py         # Track D
  ├── abort_handler.py     # Track D
  ├── regime_monitor.py    # Track D
  ├── output.py            # Track E
  └── api.py               # Track F
  
  tests/test_hunt/
  ├── __init__.py
  ├── conftest.py
  ├── test_hypothesis_schema.py
  ├── test_queue.py
  ├── test_executor.py
  ├── test_budget.py
  ├── test_output.py
  └── test_integration.py
  
  tests/chaos/
  └── test_bunny_s38.py    # 32+ vectors

DAY_BY_DAY:
  day_1:
    - hunt/schemas/hypothesis_schema.yaml
    - hunt/hypothesis.py (dataclasses + validation)
    - tests/test_hunt/test_hypothesis_schema.py
    
  day_2:
    - hunt/queue.py
    - hunt/queue_store.py
    - tests/test_hunt/test_queue.py
    
  day_3:
    - hunt/grid.py
    - hunt/variant.py
    - hunt/executor.py
    - tests/test_hunt/test_executor.py
    
  day_4:
    - hunt/budget.py
    - hunt/estimator.py
    - hunt/abort_handler.py
    - hunt/regime_monitor.py
    - tests/test_hunt/test_budget.py
    
  day_5:
    - hunt/output.py
    - hunt/schemas/hunt_result_schema.yaml
    - tests/test_hunt/test_output.py
    
  day_6-7:
    - hunt/__init__.py
    - hunt/api.py
    - tests/test_hunt/test_integration.py
    - tests/chaos/test_bunny_s38.py (32+ vectors)
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | HYPOTHESIS | Human-framed only; metrics mandatory; dims capped |
| B | QUEUE | Approved only; FIFO default; shuffle opt-in |
| C | EXECUTOR | ALL variants computed; no selection |
| D | BUDGET | Ceiling enforced; abort with completeness_mask |
| E | OUTPUT | Flat table; grid order declared; shuffle opt-in |
| F | BUNNY | 32+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S38 COMPLETE

---

```yaml
STATUS: OPUS_REFINED_v0.2
INVARIANTS: 11 (3 original + 8 new)
CHAOS_VECTORS: 32+ (16 waves)
TARGET: Sub-45min execution
PATTERN: PROVEN x3
READY: EXECUTE
```

---
