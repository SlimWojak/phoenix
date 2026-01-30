# S35_BUILD_MAP_v0.1.md — CONDITIONAL FACT PROJECTOR

```yaml
document: S35_BUILD_MAP_v0.1.md
version: 0.1
date: 2026-01-29
status: DRAFT_FOR_ADVISOR_REVIEW
theme: "Where/when does performance concentrate?"
codename: CFP (Conditional Fact Projector)
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
  CFP returns conditional facts with full provenance.
  Causal-ban linter FAILS on any causal language.
  Conflict display shows best AND worst.
  No grades, no rankings, no recommendations anywhere.
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: LENS_SCHEMA (Constitutional Boundary)
  days: 1-2
  owner: OPUS
  
TRACK_B: QUERY_EXECUTOR (Computation Engine)
  days: 2-4
  owner: OPUS
  
TRACK_C: OUTPUT_SCHEMA (Provenance First-Class)
  days: 3-4
  owner: OPUS
  
TRACK_D: CAUSAL_BAN_LINTER (Enforcement Teeth)
  days: 4-5
  owner: OPUS
  
TRACK_E: CONFLICT_DISPLAY (Best/Worst Pairing)
  days: 5-6
  owner: OPUS

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
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
  - tests/test_lens_schema_validation.py

SCHEMA_STRUCTURE:
  lens_query:
    source: enum[river, beads, positions]
    group_by: list[str]  # e.g., ["session", "kill_zone", "pair"]
    filter:
      conditions: list[predicate]  # explicit predicates only
      time_range: {start: datetime, end: datetime}
    aggregate:
      metrics: list[enum[count, sum, mean, sharpe, win_rate, pnl]]
    output:
      format: enum[table, single_value]
      include_provenance: true  # MANDATORY

PREDICATE_RULES:
  allowed:
    - Field comparisons: "session == 'London'"
    - Numeric ranges: "entry_time > '08:30'"
    - Gate references: "gates_passed contains 3"
    - Explicit regimes: "regime == 'trending'" (from conditions.yaml)
  forbidden:
    - Auto-detected anything
    - Quality scores
    - Confidence thresholds (unless explicit formula)
    - "best", "worst", "optimal" in predicates

EXIT_GATE_A:
  criterion: "Lens schema validates all test queries; rejects forbidden patterns"
  test: tests/test_lens_schema_validation.py
  proof: "10+ valid queries pass, 10+ forbidden queries rejected"

INVARIANTS_PROVEN:
  - INV-REGIME-EXPLICIT (regimes from conditions.yaml only)
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
  - tests/test_executor.py

EXECUTOR_INTERFACE:
  input: LensQuery (validated schema)
  output: CFPResult (with provenance)
  
  behavior:
    1. Validate query against lens_schema
    2. Route to appropriate adapter (river/beads)
    3. Execute aggregation
    4. Attach provenance (query_string, dataset_hash, bead_id)
    5. Check sample size (INV-SLICE-MINIMUM-N)
    6. Return result

SAMPLE_SIZE_ENFORCEMENT:
  threshold: N >= 30 (configurable)
  behavior_below_threshold:
    - Add WARNING flag to output
    - Do NOT suppress result (human decides significance)
  rationale: "Prevent cherry-picking without blocking legitimate exploration"

EXIT_GATE_B:
  criterion: "Executor returns correct aggregations with provenance attached"
  test: tests/test_executor.py
  proof: |
    - 5+ River queries return expected metrics
    - 5+ Bead queries return expected metrics
    - All outputs include provenance triplet
    - Low-N results flagged with WARNING

INVARIANTS_PROVEN:
  - INV-ATTR-PROVENANCE (query_string + dataset_hash + bead_id)
  - INV-SLICE-MINIMUM-N (warning on N < 30)
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
  - tests/test_result_schema.py

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
      dataset_hash: str  # hash of data slice used
      bead_id: str  # if result persisted
      computed_at: datetime
      
    flags:
      low_sample_size: bool  # true if N < threshold
      warnings: list[str]

VALIDATION_RULES:
  - provenance block MUST be present
  - dataset_hash MUST be computed (not placeholder)
  - bead_id assigned on persistence (optional for ephemeral queries)

EXIT_GATE_C:
  criterion: "All CFP results include valid provenance; schema validation passes"
  test: tests/test_result_schema.py
  proof: "Result without provenance fails validation"

INVARIANTS_PROVEN:
  - INV-ATTR-PROVENANCE (structural enforcement)
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
  - tests/test_causal_ban_linter.py

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
    
  structures:
    - "X contributed Y%" 
    - "due to X"
    - "X explains Y"
    - Any percentage attribution to a factor

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
  test: tests/test_causal_ban_linter.py
  proof: |
    - 20+ causal phrases FAIL
    - 20+ conditional phrases PASS
    - Edge cases documented and handled

INVARIANTS_PROVEN:
  - INV-ATTR-CAUSAL-BAN (mechanical enforcement)
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
  - tests/test_conflict_display.py

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

DISPLAY_RULES:
  - NEVER show best without worst
  - NEVER rank beyond top/bottom (no ordered list)
  - ALWAYS show sample sizes (low-N visible)
  - Alphabetical sort for any multi-item display (INV-HARNESS-4 pattern)

UI_INTEGRATION:
  - Conflict pairs render side-by-side
  - No visual emphasis on "best" (INV-NO-DEFAULT-SALIENCE)
  - Equal visual weight to both sides

EXIT_GATE_E:
  criterion: "Any 'best' query automatically returns 'worst' pair"
  test: tests/test_conflict_display.py
  proof: |
    - Query for "best session" returns London AND Tokyo
    - Unpaired best request rejected or auto-paired

INVARIANTS_PROVEN:
  - INV-ATTR-CONFLICT-DISPLAY
  - INV-ATTR-NO-RANKING (no ordered lists)
  - INV-NO-DEFAULT-SALIENCE (equal visual weight)
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
  - tests/test_cfp_integration.py
  - tests/test_cfp_chaos.py (BUNNY)

INTEGRATION_POINTS:
  file_seam:
    - Intent: type=CFP_QUERY, payload=LensQuery
    - Response: CFPResult written to /responses/
    
  orientation:
    - CFP health included in orientation.yaml
    - "cfp_status: NOMINAL | DEGRADED"

CHAOS_VECTORS (BUNNY):
  - Malformed queries (should reject gracefully)
  - Causal language injection (linter should catch)
  - Low-N edge cases (warning should appear)
  - Missing provenance (should fail validation)
  - Regime not in conditions.yaml (should reject)
  - Best-without-worst request (should auto-pair or reject)
  - Dataset hash mismatch (stale data detection)

EXIT_GATE_F:
  criterion: "CFP passes all chaos vectors; integration complete"
  test: tests/test_cfp_chaos.py
  proof: "12+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S35 invariants (integration test)
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
    s35_delivery: "Performance when gates_passed >= N"
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
S35_INVARIANTS:

  INV-ATTR-CAUSAL-BAN:
    track: D
    enforcement: Linter (mechanical)
    test: test_causal_ban_linter.py
    
  INV-ATTR-PROVENANCE:
    track: B, C
    enforcement: Schema validation
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
```

---

## ADVISOR QUESTIONS

```yaml
FOR_GPT_ARCHITECT:
  - "Is the banned_patterns list complete? Edge cases?"
  - "Schema validation tight enough for regime governance?"
  - "Any implicit ranking patterns I'm missing?"

FOR_GROK_CHAOS:
  - "What's the dumbest way CFP could leak causality?"
  - "Chaos vectors sufficient? What am I missing?"
  - "Compute explosion risks in query executor?"

FOR_OWL_STRUCTURAL:
  - "Lens schema constitutional soundness?"
  - "Provenance triplet sufficient for audit trail?"
  - "Conflict display symmetry — any gaps?"
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | LENS_SCHEMA | Schema validates valid, rejects forbidden |
| B | EXECUTOR | Correct metrics + provenance attached |
| C | OUTPUT | Result without provenance fails validation |
| D | LINTER | Catches causal, allows conditional |
| E | CONFLICT | Best always paired with worst |
| F | INTEGRATION | 12+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S35 COMPLETE

---

```yaml
STATUS: DRAFT_v0.1
NEXT: Socialize to GPT, GROK, OWL for input
THEN: Synthesize addendum → OPUS for v0.2
```
