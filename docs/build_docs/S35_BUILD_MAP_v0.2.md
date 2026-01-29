# S35_BUILD_MAP_v0.2.md — CONDITIONAL FACT PROJECTOR

```yaml
document: S35_BUILD_MAP_v0.2.md
version: 0.2
date: 2026-01-29
status: EXECUTION_READY
theme: "Where/when does performance concentrate?"
codename: CFP (Conditional Fact Projector)
synthesized_from: [v0.1_BASE, GPT_ARCHITECT, OWL_STRUCTURAL, GROK_CHAOS, OPUS_REPO_INTIMACY]
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the microscope that shows WHERE performance lives
  without claiming WHY it lives there.
  
  NEX died asking: "What should you do?"
  Phoenix asks: "What is true when [condition]?"

GOVERNING_PRINCIPLE: |
  "Human frames the question, machine computes the answer."
  Facts are projections. Meaning is human territory.

EXIT_GATE_SPRINT: |
  CFP returns conditional facts with full provenance (quadruplet).
  Causal-ban linter FAILS on any causal language.
  Conflict display shows best AND worst (randomized position).
  No grades, no rankings, no recommendations anywhere.
  Budget enforcement rejects compute explosions.
  Low-N (< 30) facts cannot persist without T2 override.
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: LENS_SCHEMA (Constitutional Boundary)
  days: 1-2
  owner: OPUS
  files:
    - cfp/schemas/lens_schema.yaml
    - cfp/schemas/lens_schema.json
    - cfp/validation.py
    - tests/cfp/test_lens_schema_validation.py
  
TRACK_B: QUERY_EXECUTOR (Computation Engine)
  days: 2-4
  owner: OPUS
  files:
    - cfp/executor.py
    - cfp/river_adapter.py
    - cfp/bead_adapter.py
    - cfp/budget.py
    - tests/cfp/test_executor.py
  
TRACK_C: OUTPUT_SCHEMA (Provenance First-Class)
  days: 3-4
  owner: OPUS
  files:
    - cfp/schemas/cfp_result_schema.yaml
    - cfp/result.py
    - tests/cfp/test_result_schema.py
  
TRACK_D: CAUSAL_BAN_LINTER (Enforcement Teeth)
  days: 4-5
  owner: OPUS
  files:
    - cfp/linter.py
    - cfp/banned_patterns.yaml
    - tests/cfp/test_causal_ban_linter.py
  
TRACK_E: CONFLICT_DISPLAY (Best/Worst Pairing)
  days: 5-6
  owner: OPUS
  files:
    - cfp/conflict_display.py
    - cfp/schemas/conflict_pair_schema.yaml
    - tests/cfp/test_conflict_display.py

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
  files:
    - cfp/__init__.py
    - cfp/api.py
    - tests/cfp/test_cfp_integration.py
    - tests/chaos/test_bunny_s35.py
```

---

## TRACK_A: LENS_SCHEMA

```yaml
PURPOSE: |
  Define the constitutional boundary for what questions can be asked.
  The Lens schema IS the contract — if it's not in the schema, it can't be queried.

DELIVERABLES:
  - cfp/schemas/lens_schema.yaml
  - cfp/schemas/lens_schema.json (JSON Schema validation)
  - cfp/validation.py
  - tests/cfp/test_lens_schema_validation.py

SCHEMA_STRUCTURE:
  lens_query:
    source: enum[river, beads, positions]
    group_by: list[str]  # e.g., ["session", "kill_zone", "pair"]
    filter:
      conditions: list[predicate]  # explicit predicates only
      time_range: {start: datetime, end: datetime}
    aggregate:
      metrics: list[metric_definition]
    output:
      format: enum[table, single_value]
      include_provenance: true  # MANDATORY
    
    # === NEW IN v0.2 ===
    strategy_config_hash: str  # MANDATORY — from operator's active setup (OWL)
    max_groups: int  # default 100 (GROK)
    override_requires: enum[none, T2]  # T2 for > 100 groups

METRIC_DEFINITIONS:  # NEW (GPT)
  sharpe:
    requires: [explicit_return_series, volatility_definition]
    precision: 2dp
  win_rate:
    requires: [explicit_trade_definition]
    precision: 2dp
  pnl:
    requires: [currency_precision]
    precision: 2dp  # or currency_default

PREDICATE_RULES:
  allowed:
    - Field comparisons: "session == 'London'"
    - Numeric ranges: "entry_time > '08:30'"
    - Gate cardinality: "gates_passed_count >= 3"  # CHANGED (GPT)
    - Explicit regimes: "regime == 'trending'" (from conditions.yaml)
  forbidden:
    - Auto-detected anything
    - Quality scores
    - Confidence thresholds (unless explicit formula)
    - "best", "worst", "optimal" in predicates
    - "gates_passed contains [specific_gate]"  # ADDED (GPT) unless named in conditions.yaml

EXIT_GATE_A:
  criterion: "Lens schema validates all test queries; rejects forbidden patterns"
  test: tests/cfp/test_lens_schema_validation.py
  proof: |
    - 10+ valid queries pass
    - 10+ forbidden queries rejected
    - Strategy config hash required on all queries
    - Max groups enforcement tested

INVARIANTS_PROVEN:
  - INV-REGIME-EXPLICIT (regimes from conditions.yaml only)
  - INV-METRIC-DEFINITION-EXPLICIT (NEW — all metrics have computational definitions)
```

### OPUS EXECUTION NOTES: TRACK_A

```yaml
INTEGRATION_POINTS:
  conditions_yaml: cso/knowledge/conditions.yaml
    - Regime predicates MUST reference signals defined here
    - Example: "bias_framework.bias_synthesis.trade_bias == 'long_only'"
    - Example: "composite_gates.alignment_gate == true"
  
  existing_patterns:
    - Follow schemas/beads.yaml pattern for YAML schema definition
    - Use jsonschema library for validation (same as t2_token.yaml)
    - Schema version field required (pattern: schema_version: "1.0")

FILE_STRUCTURE:
  cfp/
    __init__.py
    schemas/
      lens_schema.yaml
      lens_schema.json
    validation.py  # LensQueryValidator class
  tests/
    cfp/
      __init__.py
      test_lens_schema_validation.py

TEST_PATTERN:  # Mirror tests/chaos/test_bunny_s32.py
  class TestLensSchemaValidation:
    def test_valid_session_groupby(self) -> None: ...
    def test_valid_regime_predicate(self) -> None: ...
    def test_reject_causal_predicate(self) -> None: ...
    def test_reject_missing_strategy_hash(self) -> None: ...
    def test_reject_max_groups_exceeded(self) -> None: ...
```

---

## TRACK_B: QUERY_EXECUTOR

```yaml
PURPOSE: |
  Execute lens queries against River data and bead store.
  Pure computation — no interpretation, no synthesis.

DELIVERABLES:
  - cfp/executor.py
  - cfp/river_adapter.py
  - cfp/bead_adapter.py
  - cfp/budget.py  # NEW (GROK)
  - tests/cfp/test_executor.py

EXECUTOR_INTERFACE:
  input: LensQuery (validated schema)
  output: CFPResult (with provenance)
  
  behavior:
    1. Validate query against lens_schema
    2. PRE-EXECUTION: Estimate cardinality (GROK budget check)
    3. Route to appropriate adapter (river/beads)
    4. Execute aggregation
    5. Attach provenance (quadruplet — OWL)
    6. Check sample size (INV-SLICE-MINIMUM-N)
    7. Round metrics to declared precision (GPT)
    8. Return result

BUDGET_ENFORCEMENT:  # NEW (GROK)
  pre_execution:
    - Sample query to estimate cardinality (Willison datasette pattern)
    - Cap at 10k cells (configurable)
    - Abort with BUDGET_EXCEEDED if exceeded
    - Include suggestion to narrow filter
  
  implementation:
    class BudgetEstimator:
      MAX_CELLS_DEFAULT = 10000
      
      def estimate(self, query: LensQuery) -> int: ...
      def check(self, query: LensQuery) -> BudgetResult: ...

HASH_SPECIFICATION:  # NEW (GPT)
  dataset_hash:
    definition: "hash(sorted(primary_keys + timestamps + values))"
    algorithm: sha256
  test: "Hash mismatch under reordered rows must FAIL"

CROSS_METRIC_BAN:  # NEW (GPT)
  executor_rule:
    - "Metrics returned are independent projections"
    - "Executor MUST NOT compute cross-metric relationships"
    - "Any delta/ratio between metrics → FAIL"
  test: "Request for sharpe_delta or metric_ratio → REJECT"

ASYNC_RESILIENCE:  # NEW (GROK)
  timeout: 30s default
  behavior_on_timeout: DEGRADED (not silent fail)
  retry: "@banteg pattern (exponential backoff, max 3)"
  chaos_vector: "Simulate 10s River delay → expect timeout, not partial fact"

SAMPLE_SIZE_ENFORCEMENT:
  threshold: N >= 30 (configurable)
  behavior_below_threshold:
    - Add WARNING flag to output
    - Do NOT suppress result (human decides significance)
    - Cannot persist as FACT without T2 override (OWL)
  rationale: "Prevent cherry-picking without blocking legitimate exploration"

EXIT_GATE_B:
  criterion: "Executor returns correct aggregations with provenance attached"
  test: tests/cfp/test_executor.py
  proof: |
    - 5+ River queries return expected metrics
    - 5+ Bead queries return expected metrics
    - All outputs include provenance quadruplet
    - Low-N results flagged with WARNING
    - Budget exceeded triggers BUDGET_EXCEEDED
    - Cross-metric requests rejected

INVARIANTS_PROVEN:
  - INV-ATTR-PROVENANCE (query_string + dataset_hash + bead_id + governance_hash)
  - INV-SLICE-MINIMUM-N (warning on N < 30)
  - INV-CFP-BUDGET-ENFORCE (NEW — pre-execution estimate > threshold → REJECT)
```

### OPUS EXECUTION NOTES: TRACK_B

```yaml
INTEGRATION_POINTS:
  river_reader: data/river_reader.py
    - CFP adapter wraps RiverReader with caller="cfp"
    - Inherits read-only enforcement (INV-RIVER-RO-1)
    - Uses same connection pattern (context manager)
    
  bead_store: schemas/beads.yaml
    - Query against HUNT_BEAD, PERFORMANCE_BEAD, AUTOPSY_BEAD
    - Hash chain verification required on bead queries
    - bead_adapter.py uses same pattern as memory/athena.py
  
  governance: governance/interface.py
    - Inherit GovernanceInterface for halt checks
    - check_halt() at yield points (query execution, aggregation)

FILE_STRUCTURE:
  cfp/
    executor.py       # CFPExecutor class
    river_adapter.py  # RiverCFPAdapter (wraps RiverReader)
    bead_adapter.py   # BeadCFPAdapter
    budget.py         # BudgetEstimator class

PATTERN_FROM_REPO:
  # Follow data/river_reader.py pattern
  class RiverCFPAdapter:
      def __init__(self, caller: str = "cfp"):
          self._reader = RiverReader(caller=caller)
      
      def execute_aggregation(
          self,
          query: LensQuery,
      ) -> AggregationResult: ...
```

---

## TRACK_C: OUTPUT_SCHEMA

```yaml
PURPOSE: |
  Define the shape of CFP results.
  Provenance is FIRST-CLASS — not optional metadata.

DELIVERABLES:
  - cfp/schemas/cfp_result_schema.yaml
  - cfp/result.py (dataclass)
  - tests/cfp/test_result_schema.py

RESULT_STRUCTURE:
  cfp_result:
    query:
      original_query: str  # exact query as submitted
      normalized_query: str  # canonical form
    
    data:
      metrics: dict[str, float]  # e.g., {"sharpe": 1.6, "win_rate": 0.61}
      sample_size: int
      time_range: {start: datetime, end: datetime}
    
    provenance:  # MANDATORY — result invalid without this
      query_string: str
      dataset_hash: str  # hash of data slice used (SHA256)
      bead_id: str  # if result persisted
      governance_hash: str  # NEW (OWL) — hash of PHOENIX_MANIFEST.md + active invariants
      computed_at: datetime
      strategy_config_hash: str  # anchors fact to specific strategy version
      
    flags:
      low_sample_size: bool  # true if N < threshold
      warnings: list[str]
    
    # === NEW IN v0.2 ===
    result_type: enum[FACT, VIEW]  # GPT
    persistence_rule: "FACT persisted ONLY on explicit user command"

PRECISION_ROUNDING:  # NEW (GPT)
  metrics:
    sharpe: 2dp
    win_rate: 2dp  
    pnl: currency_precision (2dp default)

VALIDATION_RULES:
  - provenance block MUST be present
  - dataset_hash MUST be computed (not placeholder)
  - bead_id assigned on persistence (optional for ephemeral queries)
  - governance_hash MUST match current PHOENIX_MANIFEST.md hash

EXIT_GATE_C:
  criterion: "All CFP results include valid provenance; schema validation passes"
  test: tests/cfp/test_result_schema.py
  proof: |
    - Result without provenance fails validation
    - Result without governance_hash fails validation
    - Metrics rounded to declared precision
    - FACT vs VIEW correctly classified

INVARIANTS_PROVEN:
  - INV-ATTR-PROVENANCE (structural enforcement — quadruplet)
  - INV-NO-FALSE-PRECISION (NEW — metrics rounded to declared precision)
```

### OPUS EXECUTION NOTES: TRACK_C

```yaml
INTEGRATION_POINTS:
  bead_schema: schemas/beads.yaml
    - CFP_FACT_BEAD to be added (S37 prep)
    - For now, VIEW results are ephemeral
    - FACT persistence deferred to explicit command
  
  governance_hash:
    - Hash of: docs/PHOENIX_MANIFEST.md + CONSTITUTION/invariants/*.yaml
    - Proves fact generated while INV-ATTR-CAUSAL-BAN was active
    - Implementation: governance/telemetry.py pattern

FILE_STRUCTURE:
  cfp/
    schemas/
      cfp_result_schema.yaml
    result.py  # CFPResult dataclass

DATACLASS_PATTERN:
  @dataclass
  class CFPResult:
      query: QueryInfo
      data: DataPayload
      provenance: Provenance  # MANDATORY
      flags: ResultFlags
      result_type: ResultType  # FACT | VIEW
      
      def validate(self) -> bool:
          """Validate provenance completeness."""
          return all([
              self.provenance.query_string,
              self.provenance.dataset_hash,
              self.provenance.governance_hash,
              self.provenance.computed_at,
          ])
```

---

## TRACK_D: CAUSAL_BAN_LINTER

```yaml
PURPOSE: |
  Mechanical enforcement of INV-ATTR-CAUSAL-BAN.
  If it smells causal, it fails. No exceptions.

DELIVERABLES:
  - cfp/linter.py
  - cfp/banned_patterns.yaml
  - tests/cfp/test_causal_ban_linter.py

BANNED_PATTERNS:
  phrases:
    - "contributed"
    - "caused"
    - "responsible for"
    - "because"
    - "drove"
    - "explains"
    - "factor"
    - "attribution" (without "conditional" prefix)
    # === NEW IN v0.2 (GPT) ===
    - "predicts"
    - "leads to"
    - "drives outcomes"
    - "signal"
    - "edge"
    - "alpha"
    - "outperforms X because"
    - "improvement explained by"
    
  structures:
    - "X contributed Y%" 
    - "due to X"
    - "X explains Y"
    - Any percentage attribution to a factor
    # === NEW IN v0.2 (GPT) ===
    - Metric + agent noun: "Sharpe improved after London open" → FAIL

TEMPORAL_IMPLICATION_RULE:  # NEW (OWL)
  rule: "Flag 'after'/'following' unless paired with explicit time_range or session anchor"
  example_fail: "Result after news event"
  example_pass: "Result when time_range=[08:30, 09:00] AND news_flag=true"

ALLOWED_PATTERNS:
  phrases:
    - "when [condition]"
    - "conditional on"
    - "given that"
    - "filtered by"
    - "where"
    
  structures:
    - "P&L when [condition]"
    - "Sharpe conditional on [predicate]"
    - "Win rate where [filter]"

LINTER_BEHAVIOR:
  input: Any string (query, output label, UI text)
  output: PASS | FAIL + specific violation
  
  integration_points:
    - Query submission (lint query text)
    - Result generation (lint output labels)
    - UI rendering (lint display text)

EXIT_GATE_D:
  criterion: "Linter catches all causal patterns; allows all conditional patterns"
  test: tests/cfp/test_causal_ban_linter.py
  proof: |
    - 30+ causal phrases FAIL (expanded from 20)
    - 20+ conditional phrases PASS
    - Temporal implication rules tested
    - Metric + agent noun combinations tested
    - Edge cases documented and handled

INVARIANTS_PROVEN:
  - INV-ATTR-CAUSAL-BAN (mechanical enforcement)
```

### OPUS EXECUTION NOTES: TRACK_D

```yaml
IMPLEMENTATION_APPROACH:
  # Pattern-based with regex + structural analysis
  class CausalBanLinter:
      def __init__(self, patterns_path: Path = None):
          self._banned = self._load_patterns(patterns_path)
      
      def lint(self, text: str) -> LintResult:
          """Check text for causal violations."""
          violations = []
          for pattern in self._banned.phrases:
              if self._match_pattern(text, pattern):
                  violations.append(Violation(pattern=pattern, text=text))
          # ... structure checks ...
          return LintResult(passed=len(violations) == 0, violations=violations)

METRIC_AGENT_RULE:  # GPT special case
  # Detect: "Sharpe improved after London"
  # Pattern: metric_name + past_tense_verb + temporal_phrase
  METRICS = {"sharpe", "win_rate", "pnl", "profit_factor", "drawdown"}
  AGENT_VERBS = {"improved", "increased", "decreased", "changed", "moved"}
  
  def check_metric_agent(self, text: str) -> bool:
      # If metric + agent verb found → FAIL
      ...

FILE_STRUCTURE:
  cfp/
    linter.py
    banned_patterns.yaml  # Separate for maintainability
```

---

## TRACK_E: CONFLICT_DISPLAY

```yaml
PURPOSE: |
  When showing "best", must show "worst".
  Prevents selective presentation that becomes implicit recommendation.

DELIVERABLES:
  - cfp/conflict_display.py
  - cfp/schemas/conflict_pair_schema.yaml
  - tests/cfp/test_conflict_display.py

CONFLICT_PAIR_STRUCTURE:
  conflict_pair:
    dimension: str  # e.g., "session", "kill_zone"
    best:
      value: str  # e.g., "London"
      metrics: dict[str, float]
      sample_size: int
      provenance: {...}
    worst:
      value: str  # e.g., "Tokyo"
      metrics: dict[str, float]
      sample_size: int
      provenance: {...}
    spread:
      metric: str  # e.g., "sharpe"
      delta: float  # e.g., 0.8
      status: DISABLED_BY_DEFAULT  # NEW (GPT)
      requires_explicit_request: true
    scope:
      comparison_domain: explicit  # NEW (GPT) — declared slice only, never global

DISPLAY_RULES:
  - NEVER show best without worst
  - NEVER rank beyond top/bottom (no ordered list)
  - ALWAYS show sample sizes (low-N visible)
  - Alphabetical sort for any multi-item display (INV-HARNESS-4 pattern)
  # === NEW IN v0.2 ===
  - RANDOMIZE best/worst position per render (OWL)
  - Spread.delta DISABLED by default (GPT)

RANDOMIZED_POSITIONING:  # NEW (OWL)
  display_rule: "Best/Worst placement RANDOMIZED per render"
  implementation: "Shuffle side assignment — user must read label, not position"
  rationale: "Enforces INV-NO-DEFAULT-SALIENCE via positional neutrality"

LOW_N_PERSISTENCE_GATE:  # NEW (OWL)
  governance_gate:
    rule: "N < 30 → cannot persist as FACT (VIEW only)"
    override: "explicit T2 approval"
  rationale: "Prevents Noise Pollution — anecdotes don't become beads"

UI_INTEGRATION:
  - Conflict pairs render side-by-side
  - No visual emphasis on "best" (INV-NO-DEFAULT-SALIENCE)
  - Equal visual weight to both sides
  - Position randomized per render

EXIT_GATE_E:
  criterion: "Any 'best' query automatically returns 'worst' pair"
  test: tests/cfp/test_conflict_display.py
  proof: |
    - Query for "best session" returns London AND Tokyo
    - Unpaired best request rejected or auto-paired
    - Spread disabled by default
    - Low-N facts blocked from persistence
    - Randomized positioning verified

INVARIANTS_PROVEN:
  - INV-ATTR-CONFLICT-DISPLAY
  - INV-ATTR-NO-RANKING (no ordered lists)
  - INV-NO-DEFAULT-SALIENCE (equal visual weight + random position)
  - INV-CFP-LOW-N-GATE (NEW — N < 30 cannot persist as FACT without T2)
```

### OPUS EXECUTION NOTES: TRACK_E

```yaml
RANDOMIZATION_IMPL:
  import secrets
  
  def render_conflict_pair(pair: ConflictPair) -> RenderedPair:
      # Randomize which side gets "left" vs "right"
      if secrets.randbelow(2) == 0:
          left, right = pair.best, pair.worst
      else:
          left, right = pair.worst, pair.best
      
      return RenderedPair(
          left=left,
          right=right,
          labels_required=True,  # Force user to read labels
      )

SCOPE_LOCK:  # GPT
  # comparison_domain must be explicit — prevents "global best"
  def validate_scope(pair: ConflictPair) -> bool:
      return pair.scope.comparison_domain != "global"
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire everything together. Chaos test the whole system.
  Prove CFP works end-to-end under adversarial conditions.

DELIVERABLES:
  - cfp/__init__.py (public interface)
  - cfp/api.py (file seam integration)
  - tests/cfp/test_cfp_integration.py
  - tests/chaos/test_bunny_s35.py

INTEGRATION_POINTS:
  file_seam:
    - Intent: type=CFP_QUERY, payload=LensQuery
    - Response: CFPResult written to /responses/
    - Path: intents/incoming/ → responses/
    
  orientation:
    - CFP health included in orientation.yaml
    - "cfp_status: NOMINAL | DEGRADED | BUDGET_EXCEEDED"

  dispatcher:
    - New intent type: CFP_QUERY
    - Route to CFPExecutor
    - Pattern: dispatcher/routes.py

CHAOS_VECTORS (BUNNY): 20+ VECTORS

  # === ORIGINAL 12 (v0.1) ===
  MALFORMED_QUERY:
    description: "Invalid JSON/YAML in lens query"
    expect: "Schema REJECT with specific error"
    
  CAUSAL_INJECTION:
    description: "Query text contains 'contributed', 'because'"
    expect: "Linter FAIL before execution"
    
  LOW_N_EDGE:
    description: "Query returns N=5 result"
    expect: "WARNING flag, VIEW only (not FACT)"
    
  MISSING_PROVENANCE:
    description: "Result missing dataset_hash"
    expect: "Schema validation FAIL"
    
  REGIME_NOT_IN_CONDITIONS:
    description: "Predicate 'regime == unknown_regime'"
    expect: "Schema REJECT — regime not in conditions.yaml"
    
  BEST_WITHOUT_WORST:
    description: "Request for 'best session' only"
    expect: "Auto-pair with worst OR reject"
    
  DATASET_HASH_MISMATCH:
    description: "Stale data detection"
    expect: "Provenance FAIL"

  # === NEW IN v0.2 ===
  REGIME_NUKE:
    source: GROK
    description: "Inject conditions.yaml corruption (regime cap exceeded)"
    expect: "Schema REJECT, not sprawl explosion"
    
  ASYNC_HELL:
    source: GROK
    description: "Simulate River/bead_adapter 10s delay"
    expect: "Timeout with DEGRADED, not partial fact"
    implementation: "Mock RiverReader with asyncio.sleep(10)"
    
  BUDGET_BLACKHOLE:
    source: GROK
    description: "Unbounded group_by (per-tick over 1yr)"
    expect: "Hard abort with BUDGET_EXCEEDED"
    query: "group_by: [timestamp] over 365 days"
    
  MYTH_INFLATION:
    source: GROK
    description: "Flood 100 CLAIM_BEADs conflicting FACTs"
    expect: "Conflict display scales without 'top N conflicts' ranking"
    
  BEAD_CHAIN_BREAK:
    source: GROK
    description: "Nuke mid-chain bead, query spans it"
    expect: "Provenance FAIL, not silent forward-fill"
    
  CARTESIAN_EXPLOSION:
    source: GPT
    description: "group_by x filter x metrics cartesian product"
    expect: "Hard FAIL with budget error"
    query: "group_by: [session, kill_zone, pair, regime] with 5 metrics"
    
  TEMPORAL_OVERLAP:
    source: GPT
    description: "Overlapping time windows in query"
    expect: "Executor rejects ambiguous ranges"
    query: "time_range: [08:00-10:00] AND time_range: [09:00-11:00]"
    
  STALE_BEAD_REFERENCE:
    source: GROK
    description: "bead_id references deleted/corrupted bead"
    expect: "Provenance FAIL with explicit error"

  CROSS_METRIC_REQUEST:
    source: GPT
    description: "Request sharpe_delta or metric_ratio"
    expect: "REJECT — cross-metric relationships forbidden"
    
  PRECISION_OVERFLOW:
    source: GPT
    description: "Metric returns 1.666666667"
    expect: "Rounded to 1.67 (2dp)"
    
  GOVERNANCE_HASH_MISMATCH:
    source: OWL
    description: "governance_hash doesn't match current MANIFEST"
    expect: "STALE_GOVERNANCE error"
    
  RANDOMIZATION_VERIFICATION:
    source: OWL
    description: "Render conflict pair 100 times"
    expect: "Approximately 50/50 left/right distribution"

EXIT_GATE_F:
  criterion: "CFP passes all chaos vectors; integration complete"
  test: tests/chaos/test_bunny_s35.py
  proof: "20+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S35 invariants (integration test)
```

### OPUS EXECUTION NOTES: TRACK_F

```yaml
TEST_FILE_PATTERN:  # Mirror tests/chaos/test_bunny_s32.py
  """
  BUNNY S35 — Chaos Vectors for Conditional Fact Projector
  =========================================================
  
  20+ chaos vectors proving CFP resilience.
  
  WAVE ORDER:
    Wave 1: Schema Security (4 vectors)
    Wave 2: Budget Enforcement (4 vectors)
    Wave 3: Linter Enforcement (4 vectors)
    Wave 4: Provenance Chain (4 vectors)
    Wave 5: Conflict Display (4 vectors)
    Wave 6: Async Resilience (2 vectors)
  
  EXIT GATE: 20+/20+ PASS
  """
  
  import pytest
  
  class TestWave1SchemaSecurity:
      def test_cv_malformed_query(self) -> None: ...
      def test_cv_regime_not_in_conditions(self) -> None: ...
      def test_cv_missing_strategy_hash(self) -> None: ...
      def test_cv_temporal_overlap(self) -> None: ...

  class TestWave2BudgetEnforcement:
      def test_cv_budget_blackhole(self) -> None: ...
      def test_cv_cartesian_explosion(self) -> None: ...
      def test_cv_max_groups_exceeded(self) -> None: ...
      def test_cv_cross_metric_request(self) -> None: ...
  
  # ... etc ...

INTEGRATION_WITH_DISPATCHER:
  # Add to dispatcher/routes.py
  INTENT_ROUTES = {
      "CFP_QUERY": cfp.api.handle_cfp_query,
      # ... existing routes ...
  }

FILE_SEAM_PATTERN:
  # Intent structure
  intent:
    type: CFP_QUERY
    payload:
      lens_query: {...}
    timestamp: datetime
    state_hash: str
```

---

## NEX CAPABILITY MAPPING

```yaml
NEX_ADDRESSED:

  NEX-020_SIGNAL_REPLAY:
    fate: REIMAGINE
    s35_delivery: "Forensic primitives via bead queries"
    constraint: "Raw state snapshots, no narrative"
    
  NEX-021_COMPARE_BACKTESTS:
    fate: KEEP
    s35_delivery: "Side-by-side metrics via conflict_display"
    constraint: "No 'winner' declared"
    
  NEX-022_GRADE_COMPARISON:
    fate: REIMAGINE
    s35_delivery: "Performance when gates_passed_count >= N"
    constraint: "Not 'Grade A/B/C' — gate counts only"
    
  NEX-024_REGIME_BREAKDOWN:
    fate: REIMAGINE
    s35_delivery: "Performance when [explicit_predicate]"
    constraint: "Regimes from conditions.yaml only"
    
  NEX-025_SESSION_KZ_BREAKDOWN:
    fate: KEEP
    s35_delivery: "group_by: session, kill_zone"
    constraint: "Standard time slice"
    
  NEX-026_PL_ATTRIBUTION:
    fate: REIMAGINE
    s35_delivery: "P&L when [condition] — conditional facts"
    constraint: "NOT 'factor X contributed Y%'"
```

---

## INVARIANTS CHECKLIST

```yaml
S35_INVARIANTS: 12 (8 original + 4 new)

  # === ORIGINAL 8 ===
  INV-ATTR-CAUSAL-BAN:
    track: D
    enforcement: Linter (mechanical)
    test: test_causal_ban_linter.py
    
  INV-ATTR-PROVENANCE:
    track: B, C
    enforcement: Schema validation (quadruplet)
    test: test_result_schema.py
    
  INV-ATTR-NO-RANKING:
    track: E
    enforcement: Conflict display rules
    test: test_conflict_display.py
    
  INV-ATTR-SILENCE:
    track: ALL
    enforcement: "CFP never resolves conflicts"
    test: Integration tests
    
  INV-ATTR-CONFLICT-DISPLAY:
    track: E
    enforcement: Auto-pairing
    test: test_conflict_display.py
    
  INV-REGIME-EXPLICIT:
    track: A
    enforcement: Schema validation
    test: test_lens_schema_validation.py
    
  INV-REGIME-GOVERNANCE:
    track: A
    enforcement: conditions.yaml reference
    test: test_lens_schema_validation.py
    
  INV-SLICE-MINIMUM-N:
    track: B
    enforcement: Warning flag
    test: test_executor.py

  # === NEW IN v0.2 ===
  INV-METRIC-DEFINITION-EXPLICIT:
    track: A
    enforcement: Schema requires metric definitions
    test: test_lens_schema_validation.py
    source: GPT
    
  INV-NO-FALSE-PRECISION:
    track: C
    enforcement: Metrics rounded to declared precision
    test: test_result_schema.py
    source: GPT
    
  INV-CFP-BUDGET-ENFORCE:
    track: B
    enforcement: Pre-execution estimate > threshold → REJECT
    test: test_executor.py
    source: GROK
    
  INV-CFP-LOW-N-GATE:
    track: E
    enforcement: N < 30 cannot persist as FACT without T2 override
    test: test_conflict_display.py
    source: OWL
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion | v0.2 Additions |
|-------|------|------------------|----------------|
| A | LENS_SCHEMA | Schema validates valid, rejects forbidden | + strategy_hash required, + max_groups |
| B | EXECUTOR | Correct metrics + provenance attached | + budget enforcement, + async resilience |
| C | OUTPUT | Result without provenance fails validation | + governance_hash, + precision rounding |
| D | LINTER | Catches causal, allows conditional | + 10 new patterns, + temporal rules |
| E | CONFLICT | Best always paired with worst | + randomized position, + low-N gate |
| F | INTEGRATION | 20+ chaos vectors pass | + 8 new vectors |

**Sprint Exit:** ALL tracks GREEN → S35 COMPLETE

---

## DAY-BY-DAY BUILD SEQUENCE

```yaml
DAY_1:
  track: A (LENS_SCHEMA)
  deliverables:
    - cfp/ directory structure
    - cfp/schemas/lens_schema.yaml (draft)
    - cfp/validation.py (skeleton)
  parallel: Read conditions.yaml for predicate reference

DAY_2:
  track: A + B (LENS_SCHEMA complete, EXECUTOR start)
  deliverables:
    - cfp/schemas/lens_schema.json (JSON Schema)
    - tests/cfp/test_lens_schema_validation.py (10+ tests)
    - cfp/executor.py (skeleton)
    - cfp/river_adapter.py (wraps RiverReader)
  gate: Track A EXIT

DAY_3:
  track: B + C (EXECUTOR + OUTPUT_SCHEMA)
  deliverables:
    - cfp/bead_adapter.py
    - cfp/budget.py (BudgetEstimator)
    - cfp/schemas/cfp_result_schema.yaml
    - cfp/result.py (dataclass)
  parallel: Hash computation impl

DAY_4:
  track: B + C + D (EXECUTOR complete, LINTER start)
  deliverables:
    - tests/cfp/test_executor.py (10+ tests)
    - tests/cfp/test_result_schema.py
    - cfp/linter.py (skeleton)
    - cfp/banned_patterns.yaml
  gate: Track B EXIT, Track C EXIT

DAY_5:
  track: D + E (LINTER complete, CONFLICT_DISPLAY)
  deliverables:
    - tests/cfp/test_causal_ban_linter.py (30+ tests)
    - cfp/conflict_display.py
    - cfp/schemas/conflict_pair_schema.yaml
  gate: Track D EXIT

DAY_6:
  track: E + F (CONFLICT complete, INTEGRATION start)
  deliverables:
    - tests/cfp/test_conflict_display.py
    - cfp/__init__.py (public interface)
    - cfp/api.py (file seam)
    - tests/cfp/test_cfp_integration.py (skeleton)
  gate: Track E EXIT

DAY_7:
  track: F (BUNNY)
  deliverables:
    - tests/chaos/test_bunny_s35.py (20+ vectors)
    - Integration with dispatcher/routes.py
    - orientation.yaml update
  gate: Track F EXIT → S35 COMPLETE
```

---

## OPUS EXECUTION CONCERNS

```yaml
FLAGGED_CONCERNS:

  CONCERN_1_GOVERNANCE_HASH:
    issue: "How to compute governance_hash efficiently?"
    recommendation: |
      Pre-compute on PHOENIX_MANIFEST.md change.
      Store in state/governance_hash.txt.
      governance/telemetry.py pattern already exists.
    risk: LOW
    
  CONCERN_2_BUDGET_ESTIMATION:
    issue: "Sample query approach may be slow on large datasets"
    recommendation: |
      Use SQLite EXPLAIN QUERY PLAN for cardinality estimate.
      Cache estimates for similar query patterns.
      Willison datasette pattern: COUNT(*) on filtered subset first.
    risk: MEDIUM
    mitigation: "Default to conservative estimate if slow"
    
  CONCERN_3_BEAD_ADAPTER_COMPLEXITY:
    issue: "Bead queries span multiple bead types (HUNT, PERFORMANCE, AUTOPSY)"
    recommendation: |
      Start with single bead type queries.
      Complex cross-type queries deferred to S37 (Memory Discipline).
      For S35: PERFORMANCE_BEAD queries only.
    risk: LOW
    
  CONCERN_4_RANDOMIZATION_TESTING:
    issue: "Verifying 'approximately 50/50' is probabilistic"
    recommendation: |
      Use chi-squared test with p > 0.05 threshold.
      Or simpler: abs(count_left - count_right) / total < 0.2 over 100 renders.
    risk: LOW

NO_BLOCKERS_IDENTIFIED: true
```

---

## ADVISOR CONVERGENCE CONFIRMATION

| Delta | GPT | OWL | GROK | Status |
|-------|-----|-----|------|--------|
| Metric definitions | ✓ | - | - | INTEGRATED |
| Strategy config hash | - | ✓ | - | INTEGRATED |
| Governance hash | - | ✓ | - | INTEGRATED |
| Budget enforcement | - | - | ✓ | INTEGRATED |
| Randomized display | - | ✓ | ✓ | INTEGRATED |
| Extended linter | ✓ | ✓ | - | INTEGRATED |
| Low-N gate | - | ✓ | - | INTEGRATED |
| Async resilience | - | - | ✓ | INTEGRATED |
| 20+ chaos vectors | ✓ | - | ✓ | INTEGRATED |

**All advisor feedback integrated. No divergence. Ready to execute.**

---

```yaml
STATUS: v0.2_EXECUTION_READY
CONFIDENCE: HIGH
BLOCKERS: NONE
NEXT_ACTION: Day 1 — Track A (LENS_SCHEMA)
```

**OINK OINK.** 🐗🔥
