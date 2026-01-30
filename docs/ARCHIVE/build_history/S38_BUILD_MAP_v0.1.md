# S38_BUILD_MAP_v0.1.md — HUNT INFRASTRUCTURE

```yaml
document: S38_BUILD_MAP_v0.1.md
version: 0.1
date: 2026-01-29
status: DRAFT_FOR_ADVISOR_REVIEW
theme: "Compute engine, not idea engine"
codename: HUNT_ENGINE
dependencies:
  - S35_CFP (COMPLETE)
  - S36_CSO (COMPLETE)
  - S37_ATHENA (COMPLETE)
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
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: HYPOTHESIS_SCHEMA (Human Frames)
  days: 1-2
  owner: OPUS

TRACK_B: HUNT_QUEUE (Human-Approved Only)
  days: 2-3
  owner: OPUS

TRACK_C: EXHAUSTIVE_EXECUTOR (Compute ALL)
  days: 3-4
  owner: OPUS

TRACK_D: BUDGET_ENFORCEMENT (Ceiling + Abort)
  days: 4-5
  owner: OPUS

TRACK_E: OUTPUT_FORMAT (Table, No Ranking)
  days: 5-6
  owner: OPUS

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
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
        - dimension: str  # e.g., "entry_delay_minutes"
          values: list[any]  # e.g., [0, 15, 30, 45, 60]
        - dimension: str  # e.g., "stop_multiplier"
          values: list[any]  # e.g., [1.0, 1.5, 2.0]

      fixed:
        - name: str
          value: any  # Constants for this hunt

    metrics:
      evaluate: list[str]  # e.g., ["sharpe", "win_rate", "max_drawdown"]

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

SOURCE_RULE:
  allowed: HUMAN_ONLY
  forbidden:
    - "system"
    - "athena"
    - "hunt_engine"
    - Any non-human source
  enforcement: Schema validation rejects non-human source

EXIT_GATE_A:
  criterion: "Hypothesis schema validates human-framed only; rejects system-proposed"
  test: tests/test_hunt/test_hypothesis_schema.py
  proof: |
    - Hypothesis with source="system" REJECTED
    - Hypothesis without approved=true cannot execute
    - Hypothesis without max_variants REJECTED

INVARIANTS_PROVEN:
  - INV-NO-UNSOLICITED (human frames only)
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
    dequeue() -> Hypothesis  # FIFO, no priority
    peek() -> list[Hypothesis]  # view queue
    remove(hypothesis_id: str) -> bool

    # Status
    get_pending() -> list[Hypothesis]
    get_completed() -> list[HuntResult]

QUEUE_RULES:
  approval_gate:
    - Only hypothesis.approved == true can enqueue
    - Unapproved hypothesis → REJECTED

  ordering:
    - FIFO (First In, First Out)
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

EXIT_GATE_B:
  criterion: "Queue accepts approved only; FIFO order; no priority"
  test: tests/test_hunt/test_queue.py
  proof: |
    - Unapproved hypothesis enqueue → REJECTED
    - Queue order is insertion order
    - No priority/reorder methods exist

INVARIANTS_PROVEN:
  - INV-NO-UNSOLICITED (no auto-queue)
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
      variants_computed: int  # MUST equal total_variants
      variants_skipped: 0  # ALWAYS ZERO — we compute ALL

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

EXIT_GATE_C:
  criterion: "Executor computes ALL variants; no selection; grid order output"
  test: tests/test_hunt/test_executor.py
  proof: |
    - 6-variant grid → 6 rows output
    - No variants_skipped (always 0)
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

DELIVERABLES:
  - hunt/budget.py
  - hunt/estimator.py
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
    - Hard abort at ceiling (default: 30 minutes)
    - Write ABORT bead with partial results

  system_ceilings:
    max_variants_default: 10000
    max_variants_t2_override: 100000  # requires T2
    max_compute_seconds: 1800  # 30 minutes
    max_memory_mb: 4096

ABORT_BEHAVIOR:
  on_budget_exceeded:
    - HALT execution immediately
    - Write HuntResult with status=ABORTED
    - Include partial results computed
    - Include reason: "BUDGET_EXCEEDED: [detail]"
    - DO NOT return "best so far" — just raw partial

EXIT_GATE_D:
  criterion: "Budget enforced; exceeding ceiling → REJECT or ABORT"
  test: tests/test_hunt/test_budget.py
  proof: |
    - 100,000 variant grid without T2 → REJECTED
    - Execution exceeding time ceiling → ABORTED
    - Partial results on abort (no ranking)

INVARIANTS_PROVEN:
  - INV-HUNT-BUDGET (compute ceiling enforced)
```

---

## TRACK_E: OUTPUT_FORMAT

```yaml
PURPOSE: |
  Hunt output is a TABLE. Not a ranking. Not a recommendation.
  Every variant, every metric, no selection.

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
    - Grid order (deterministic)
    - User can sort client-side
    - System never pre-sorts by performance

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

EXIT_GATE_E:
  criterion: "Output is flat table; no ranking; no synthesis"
  test: tests/test_hunt/test_output.py
  proof: |
    - Output has no "top_variants" field
    - Output has no "recommendation" field
    - Sort order declared as "GRID_ORDER"

INVARIANTS_PROVEN:
  - INV-ATTR-NO-RANKING (flat table)
  - INV-NO-UNSOLICITED (no synthesis/recommendation)
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire Hunt end-to-end. Chaos test for proposal leakage.
  Prove the engine computes, never proposes.

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

  athena_integration:
    - Hunt results stored as FACT_BEADs
    - Hypotheses can reference CLAIM_BEADs (but not execute them)

CHAOS_VECTORS (BUNNY):

  proposal_attacks:
    - System-sourced hypothesis → REJECTED
    - Auto-generated hypothesis → REJECTED
    - "Suggest next hypothesis" request → REJECTED

  selection_attacks:
    - Request "top 5 variants" → REJECTED
    - Request "survivors only" → REJECTED
    - Request "promising variants" → REJECTED
    - Output with variants_skipped > 0 → INVALID

  ranking_attacks:
    - Request sort by sharpe → REJECTED (output is grid order)
    - Output with "best_variant" field → INVALID
    - Output with "ranking" field → INVALID

  priority_attacks:
    - Enqueue with priority field → REJECTED
    - Request "most important hypothesis" → REJECTED
    - Reorder queue by potential → REJECTED

  budget_attacks:
    - 100,000 variants without T2 → REJECTED
    - Bypass budget check → BLOCKED
    - Partial abort returns "best so far" → INVALID (raw partial only)

  synthesis_attacks:
    - Output with "key_finding" → INVALID
    - Output with "recommendation" → INVALID
    - Output with "pattern_detected" → INVALID

  approval_bypass:
    - Execute unapproved hypothesis → REJECTED
    - Enqueue unapproved → REJECTED

EXIT_GATE_F:
  criterion: "Hunt passes all chaos vectors; no proposal leakage"
  test: tests/chaos/test_bunny_s38.py
  proof: "24+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S38 invariants (integration test)
  - INV-HUNT-EXHAUSTIVE
  - INV-NO-UNSOLICITED
  - INV-HUNT-BUDGET
```

---

## NEX CAPABILITY MAPPING

```yaml
NEX_ADDRESSED:

  NEX-035_HYPOTHESIS_FRAMING:
    fate: REIMAGINE
    s38_delivery: "Structured hypothesis schema with grid parameters"
    constraint: "Human frames, system never proposes"

  NEX-037_PENDING_QUEUE:
    fate: KEEP
    s38_delivery: "FIFO queue of approved hypotheses"
    constraint: "No priority, no auto-queue"

  NEX-038_HUNT_ENGINE_RUN:
    fate: REIMAGINE
    s38_delivery: "Exhaustive grid computation"
    constraint: "Compute ALL, no selection, no 'survivors'"

  NEX-040_EPOCH_PROCESSING:
    fate: KEEP
    s38_delivery: "Batch execution from queue"
    constraint: "Process queue in order, no prioritization"

  NEX-041_PARAMETER_SWEEP:
    fate: REIMAGINE
    s38_delivery: "Grid expansion with table output"
    constraint: "No 'optimal' selection, no ranking"
```

---

## INVARIANTS CHECKLIST

```yaml
S38_INVARIANTS:

  INV-HUNT-EXHAUSTIVE:
    rule: "Hunt computes ALL declared variants, never selects"
    tracks: C, F
    enforcement: variants_computed == total_variants
    test: test_executor.py, test_bunny_s38.py

  INV-NO-UNSOLICITED:
    rule: "System never proposes hypotheses"
    tracks: A, B, E, F
    enforcement: Source validation, no auto-queue
    test: All test files

  INV-HUNT-BUDGET:
    rule: "Compute/token cap enforced per run"
    tracks: D, F
    enforcement: Pre-execution check, during-execution abort
    test: test_budget.py, test_bunny_s38.py

INHERITED_INVARIANTS:
  - INV-ATTR-NO-RANKING (flat table output)
  - INV-ATTR-PROVENANCE (full provenance on results)
```

---

## ADVISOR QUESTIONS

```yaml
FOR_GPT_ARCHITECT:
  - "Hypothesis schema complete? Missing rejection patterns?"
  - "Output format tight enough? Synthesis leakage vectors?"
  - "Budget abort behavior — partial results handling correct?"

FOR_GROK_CHAOS:
  - "What's the dumbest way Hunt becomes idea engine?"
  - "Grid explosion scenarios beyond budget — edge cases?"
  - "Survivor ranking resurrection vectors?"

FOR_OWL_STRUCTURAL:
  - "Queue FIFO appropriate? Any ordering needed?"
  - "Exhaustive computation provenance complete?"
  - "Integration with CFP/Athena coherent?"
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | HYPOTHESIS | Human-framed only; system-proposed rejected |
| B | QUEUE | Approved only; FIFO; no priority |
| C | EXECUTOR | ALL variants computed; no selection |
| D | BUDGET | Ceiling enforced; abort on exceed |
| E | OUTPUT | Flat table; no ranking; no synthesis |
| F | BUNNY | 24+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S38 COMPLETE

---

```yaml
STATUS: DRAFT_v0.1
NEXT: Socialize to GPT, GROK, OWL for input
THEN: Synthesize addendum → OPUS for v0.2
```

---
