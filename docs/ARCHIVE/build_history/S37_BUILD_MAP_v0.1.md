# S37_BUILD_MAP_v0.1.md — MEMORY DISCIPLINE

```yaml
document: S37_BUILD_MAP_v0.1.md
version: 0.1
date: 2026-01-29
status: DRAFT_FOR_ADVISOR_REVIEW
theme: "Memory, not myth"
codename: ATHENA_DISCIPLINE
dependencies:
  - S35_CFP (COMPLETE)
  - S36_CSO (COMPLETE)
```

---

## MISSION

```yaml
OBJECTIVE: |
  Build the memory system that separates CLAIMS from FACTS.
  Olya's observations are human wisdom (claims).
  Machine computations are verified outputs (facts).
  When they conflict, the system surfaces — never resolves.

  NEX died saying: "The system learned X"
  Phoenix says: "CLAIM_123 asserts X. FACT_456 shows Y. CONFLICT detected."

GOVERNING_PRINCIPLE: |
  "Memory is storage. Myth is interpretation."
  Claims are queryable, not executable.
  Facts have provenance. Conflicts have no resolution authority.

EXIT_GATE_SPRINT: |
  Athena stores claims with explicit type distinction.
  CONFLICT_BEADs surface when claim contradicts fact.
  System never resolves conflicts — human decides.
  No stored claim can mutate doctrine.
```

---

## TRACK STRUCTURE

```yaml
TRACK_A: BEAD_TYPE_SCHEMA (Claim/Fact/Conflict)
  days: 1-2
  owner: OPUS

TRACK_B: ATHENA_STORE (Typed Storage Engine)
  days: 2-3
  owner: OPUS

TRACK_C: CONFLICT_DETECTION (Surface, Never Resolve)
  days: 3-4
  owner: OPUS

TRACK_D: SEMANTIC_QUERY (Distance Scores, Not Relevance)
  days: 4-5
  owner: OPUS

TRACK_E: MEMORY_HISTORY (Chronological Trail)
  days: 5-6
  owner: OPUS

TRACK_F: INTEGRATION + BUNNY
  days: 6-7
  owner: OPUS + BUNNY
```

---

## TRACK_A: BEAD_TYPE_SCHEMA

```yaml
PURPOSE: |
  Define the three memory bead types with strict semantic boundaries.
  A CLAIM is human wisdom. A FACT is machine truth. A CONFLICT is tension.

DELIVERABLES:
  - athena/schemas/claim_bead_schema.yaml
  - athena/schemas/fact_bead_schema.yaml
  - athena/schemas/conflict_bead_schema.yaml
  - athena/bead_types.py
  - tests/test_athena/test_bead_types.py

CLAIM_BEAD_SCHEMA:
  claim_bead:
    bead_id: str  # unique identifier
    bead_type: "CLAIM"  # constant
    timestamp: datetime

    source:
      type: "HUMAN"  # always human
      attribution: str  # e.g., "Olya", "G"
      context: str  # session/conversation reference

    content:
      assertion: str  # the claim text
      domain: str  # e.g., "ICT", "risk", "timing"
      confidence_declared: null  # FORBIDDEN — no self-rating

    status:
      verified: false  # claims are never "verified" by system
      superseded_by: null  # optional: newer claim_id

    provenance:
      session_id: str
      created_at: datetime

FACT_BEAD_SCHEMA:
  fact_bead:
    bead_id: str
    bead_type: "FACT"
    timestamp: datetime

    source:
      type: "COMPUTATION"  # always machine
      module: str  # e.g., "cfp", "river", "cso"
      formula: str  # explicit computation description

    content:
      statement: str  # the fact
      value: any  # numeric/boolean result
      domain: str

    provenance:  # MANDATORY — from CFP pattern
      query_string: str
      dataset_hash: str
      governance_hash: str
      strategy_config_hash: str
      computed_at: datetime

    status:
      valid_until: datetime  # optional: expiry
      recomputed_from: str  # optional: prior fact_id

CONFLICT_BEAD_SCHEMA:
  conflict_bead:
    bead_id: str
    bead_type: "CONFLICT"
    timestamp: datetime

    references:
      claim_bead_id: str  # the claim
      fact_bead_id: str  # the contradicting fact

    conflict:
      description: str  # auto-generated: "CLAIM asserts X, FACT shows Y"
      domain: str
      severity: null  # FORBIDDEN — no ranking conflicts

    resolution:
      status: "OPEN"  # only value until human acts
      resolved_by: null  # human attribution when resolved
      resolution_action: null  # "CLAIM_UPDATED" | "CLAIM_RETAINED" | "FACT_DISPUTED"
      resolved_at: null

FORBIDDEN_FIELDS:
  all_types:
    - importance
    - priority
    - weight
    - score
    - quality
  claim_specific:
    - verified: true  # claims cannot be system-verified
    - confidence (system-assigned)
  conflict_specific:
    - severity
    - urgency
    - auto_resolution

EXIT_GATE_A:
  criterion: "Three bead types validated; forbidden fields rejected"
  test: tests/test_athena/test_bead_types.py
  proof: |
    - CLAIM with verified=true REJECTED
    - FACT without provenance REJECTED
    - CONFLICT with severity REJECTED

INVARIANTS_PROVEN:
  - INV-ATTR-SILENCE (conflicts have no resolution authority)
```

---

## TRACK_B: ATHENA_STORE

```yaml
PURPOSE: |
  Storage engine that enforces type discipline.
  Claims stored separately from facts. Cross-referencing enabled.

DELIVERABLES:
  - athena/store.py
  - athena/claim_store.py
  - athena/fact_store.py
  - athena/conflict_store.py
  - tests/test_athena/test_store.py

STORE_INTERFACE:
  AthenaStore:
    store_claim(claim: ClaimBead) -> str  # returns bead_id
    store_fact(fact: FactBead) -> str
    store_conflict(conflict: ConflictBead) -> str

    get_bead(bead_id: str) -> Bead
    get_claims_by_domain(domain: str) -> list[ClaimBead]
    get_facts_by_domain(domain: str) -> list[FactBead]
    get_open_conflicts() -> list[ConflictBead]

    # Query interface
    query(query: AthenaQuery) -> list[Bead]

STORAGE_RULES:
  separation:
    - Claims and facts in separate tables/collections
    - Cross-reference by bead_id only
    - No implicit merging

  immutability:
    - Beads are append-only
    - Updates create new beads with superseded_by reference
    - No in-place modification

  no_doctrine_mutation:
    - INV-ATTR-NO-WRITEBACK enforced
    - Stored claims cannot modify conditions.yaml
    - Stored claims cannot modify alert rules
    - Stored claims cannot modify drawer definitions
    - Claims are QUERYABLE, never EXECUTABLE

PERSISTENCE:
  backend: SQLite (consistent with BeadStore pattern)
  tables:
    - claim_beads
    - fact_beads
    - conflict_beads
    - bead_index (full-text search)

EXIT_GATE_B:
  criterion: "Store enforces type separation; no writeback possible"
  test: tests/test_athena/test_store.py
  proof: |
    - Claim stored, retrieved with correct type
    - Fact stored with full provenance
    - Attempt to mutate doctrine from claim → REJECTED

INVARIANTS_PROVEN:
  - INV-ATTR-NO-WRITEBACK (claims cannot mutate doctrine)
```

---

## TRACK_C: CONFLICT_DETECTION

```yaml
PURPOSE: |
  Detect when claims contradict facts. Surface without resolving.
  The system has NO authority to decide which is correct.

DELIVERABLES:
  - athena/conflict_detector.py
  - athena/conflict_rules.yaml
  - tests/test_athena/test_conflict_detection.py

DETECTION_INTERFACE:
  ConflictDetector:
    check_claim_against_facts(claim: ClaimBead) -> list[ConflictBead]
    check_fact_against_claims(fact: FactBead) -> list[ConflictBead]
    scan_all_conflicts() -> list[ConflictBead]

DETECTION_RULES:
  trigger_conditions:
    - Claim asserts X, Fact shows NOT X (direct contradiction)
    - Claim asserts "A > B", Fact shows "A <= B" (numeric contradiction)
    - Claim asserts timing pattern, Fact shows opposite pattern

  domain_matching:
    - Conflicts only detected within same domain
    - Cross-domain claims/facts do not conflict

  threshold:
    - No "similarity threshold" — contradiction is binary
    - Ambiguous cases do NOT create conflicts (human must assert)

CONFLICT_CREATION:
  on_new_claim:
    1. Scan facts in same domain
    2. Check for direct contradictions
    3. If found: create CONFLICT_BEAD, status=OPEN
    4. Notify (bead emission, optional alert)

  on_new_fact:
    1. Scan claims in same domain
    2. Check for contradictions
    3. If found: create CONFLICT_BEAD, status=OPEN
    4. Notify

RESOLUTION_PROTOCOL:
  system_authority: NONE

  human_actions:
    CLAIM_UPDATED: "Human revises claim based on fact"
    CLAIM_RETAINED: "Human asserts claim despite fact (edge case)"
    FACT_DISPUTED: "Human questions fact methodology"

  on_resolution:
    - Update CONFLICT_BEAD with resolved_by, resolution_action, resolved_at
    - Status changes from OPEN to RESOLVED
    - Original claim/fact beads UNCHANGED (immutable)

FORBIDDEN_BEHAVIORS:
  - Auto-resolution based on recency
  - Auto-resolution based on "confidence"
  - Suggesting which to trust
  - Ranking conflicts by importance
  - Suppressing conflicts
  - Batching conflicts into "conflict score"

EXIT_GATE_C:
  criterion: "Conflicts detected and surfaced; no resolution authority"
  test: tests/test_athena/test_conflict_detection.py
  proof: |
    - Claim contradicting fact creates CONFLICT_BEAD
    - CONFLICT_BEAD has status=OPEN
    - No auto-resolution attempted
    - Resolution only via explicit human action

INVARIANTS_PROVEN:
  - INV-ATTR-SILENCE (system does not resolve conflicts)
```

---

## TRACK_D: SEMANTIC_QUERY

```yaml
PURPOSE: |
  Query memory by meaning, not just keywords.
  Return DISTANCE SCORES, not "relevance" — no ranking by quality.

DELIVERABLES:
  - athena/semantic.py
  - athena/embeddings.py
  - tests/test_athena/test_semantic_query.py

SEMANTIC_INTERFACE:
  SemanticQuery:
    search(query: str, domain: str = None, bead_type: str = None) -> list[SemanticResult]

  SemanticResult:
    bead: Bead
    distance: float  # embedding distance (lower = closer)
    # NOT "relevance" or "score" or "match_quality"

EMBEDDING_STRATEGY:
  model: sentence-transformers (local, no API dependency)
  storage: Pre-computed embeddings in bead_index table
  update: On bead creation

  fallback: If embedding unavailable, graceful degradation to keyword search

QUERY_RULES:
  output_order:
    - By distance (ascending) — factual, not "best"
    - Declare sort explicitly in response

  forbidden_language:
    - "most relevant"
    - "best match"
    - "top results"
    - "recommended"

  allowed_language:
    - "closest by embedding distance"
    - "nearest semantic neighbors"
    - "ordered by distance (ascending)"

DISTANCE_DISPLAY:
  format: "distance: 0.23"  # raw number
  forbidden:
    - Percentage conversion
    - "Match: 77%"
    - Color coding by distance
    - Bucketing ("High/Medium/Low match")

EXIT_GATE_D:
  criterion: "Semantic search returns distance scores; no relevance ranking"
  test: tests/test_athena/test_semantic_query.py
  proof: |
    - Results include distance field
    - Results do NOT include relevance/score/quality
    - Output declares sort order explicitly

INVARIANTS_PROVEN:
  - INV-ATTR-NO-RANKING (distance, not relevance)
```

---

## TRACK_E: MEMORY_HISTORY

```yaml
PURPOSE: |
  Chronological trail of all memory operations.
  See evolution of understanding over time.

DELIVERABLES:
  - athena/history.py
  - tests/test_athena/test_history.py

HISTORY_INTERFACE:
  MemoryHistory:
    get_timeline(domain: str = None, bead_type: str = None) -> list[Bead]
    get_claim_evolution(claim_id: str) -> list[ClaimBead]  # supersession chain
    get_fact_recomputations(fact_id: str) -> list[FactBead]
    get_conflict_history() -> list[ConflictBead]  # all conflicts, open and resolved

TIMELINE_RULES:
  order: CHRONOLOGICAL (oldest first) or REVERSE_CHRONO (newest first)
  default: REVERSE_CHRONO (most recent context)
  explicit: Declare order in response

  content:
    - Full bead data
    - Provenance intact
    - Supersession chains visible

EVOLUTION_TRACKING:
  claim_chain:
    - Original claim → superseded_by → current claim
    - All versions preserved
    - No rewriting history

  fact_chain:
    - Original fact → recomputed_from → current fact
    - Methodology changes visible
    - Provenance differences highlighted

CONFLICT_HISTORY:
  includes:
    - When detected
    - Resolution (if any)
    - Time to resolution
  excludes:
    - "Conflict frequency score"
    - "Domains with most conflicts"
    - Any aggregation implying quality

EXIT_GATE_E:
  criterion: "History returns chronological trail with provenance"
  test: tests/test_athena/test_history.py
  proof: |
    - Timeline returns beads in declared order
    - Supersession chains intact
    - No history rewriting possible

INVARIANTS_PROVEN:
  - Bead immutability maintained
```

---

## TRACK_F: INTEGRATION + BUNNY

```yaml
PURPOSE: |
  Wire Athena end-to-end. Chaos test for myth leakage.
  Prove memory stays memory — never becomes doctrine.

DELIVERABLES:
  - athena/__init__.py (public interface)
  - athena/api.py (file seam integration)
  - tests/test_athena/test_integration.py
  - tests/chaos/test_bunny_s37.py

INTEGRATION_POINTS:
  file_seam:
    - Intent: type=ATHENA_STORE, payload={bead_type, content}
    - Intent: type=ATHENA_QUERY, payload={query, domain}
    - Response: Query results or store confirmation

  cfp_integration:
    - Facts can be stored from CFP results
    - Claims can reference CFP queries

  cso_integration:
    - Claims about gate effectiveness
    - Facts from gate evaluation history

CHAOS_VECTORS (BUNNY):

  writeback_attacks:
    - Store claim, attempt doctrine mutation → REJECTED
    - Store claim referencing conditions.yaml → REJECTED
    - Store claim with "verified: true" → REJECTED

  resolution_attacks:
    - Trigger conflict, attempt auto-resolve → REJECTED
    - Inject severity into conflict → REJECTED
    - Request "most important conflicts" → REJECTED

  ranking_attacks:
    - Request "most relevant claims" → REJECTED
    - Request claims "sorted by quality" → REJECTED
    - Request "top conflicts" → REJECTED

  type_confusion:
    - Store fact as claim → REJECTED (type validation)
    - Store claim without attribution → REJECTED
    - Store fact without provenance → REJECTED

  semantic_attacks:
    - Request "best matching" beads → REJECTED
    - Request "relevance score" → REJECTED
    - Request bucketed results → REJECTED

  history_attacks:
    - Attempt bead modification → REJECTED (immutable)
    - Attempt history deletion → REJECTED
    - Request "claims that were wrong" → REJECTED (implies judgment)

  flood_attacks:
    - 1000 claims in 1 minute → Rate limit
    - 100 conflicts open → No "conflict overload score"

EXIT_GATE_F:
  criterion: "Athena passes all chaos vectors; no myth leakage"
  test: tests/chaos/test_bunny_s37.py
  proof: "24+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S37 invariants (integration test)
  - INV-ATTR-NO-WRITEBACK
  - INV-ATTR-SILENCE
```

---

## NEX CAPABILITY MAPPING

```yaml
NEX_ADDRESSED:

  NEX-013_TEACH_ATHENA:
    fate: REIMAGINE
    s37_delivery: "Store as CLAIM_BEAD with attribution"
    constraint: "Claims are queryable, not executable"

  NEX-014_RECALL_MEMORY:
    fate: KEEP
    s37_delivery: "Query interface with type filtering"
    constraint: "Verbatim retrieval with provenance"

  NEX-015_SEMANTIC_SEARCH:
    fate: REIMAGINE
    s37_delivery: "Embedding distance, not relevance"
    constraint: "No quality ranking in results"

  NEX-016_CONTRADICTION_DETECTION:
    fate: REIMAGINE
    s37_delivery: "CONFLICT_BEAD with no resolution authority"
    constraint: "Surface and wait — human decides"

  NEX-017_MEMORY_HISTORY:
    fate: KEEP
    s37_delivery: "Chronological timeline with supersession chains"
    constraint: "Immutable history, no rewriting"
```

---

## INVARIANTS CHECKLIST

```yaml
S37_INVARIANTS:

  INV-ATTR-NO-WRITEBACK:
    rule: "Stored facts/claims cannot mutate doctrine"
    tracks: B, F
    enforcement: Store validation
    test: test_store.py, test_bunny_s37.py

  INV-ATTR-SILENCE:
    rule: "System does not resolve conflicts; surfaces and waits"
    tracks: C, F
    enforcement: Resolution protocol
    test: test_conflict_detection.py, test_bunny_s37.py

INHERITED_INVARIANTS:
  - INV-ATTR-PROVENANCE (facts require full provenance)
  - INV-ATTR-NO-RANKING (distance, not relevance)
```

---

## ADVISOR QUESTIONS

```yaml
FOR_GPT_ARCHITECT:
  - "CLAIM_BEAD schema tight enough? Missing rejection patterns?"
  - "Conflict detection rules complete? Edge cases in contradiction logic?"
  - "Writeback prevention comprehensive? Other mutation vectors?"

FOR_GROK_CHAOS:
  - "What's the dumbest way claims become doctrine?"
  - "Conflict flood scenarios — what breaks?"
  - "Semantic search gaming — how to extract implicit ranking?"

FOR_OWL_STRUCTURAL:
  - "Claim/Fact/Conflict separation architecturally sound?"
  - "Supersession chain design appropriate?"
  - "Integration with CFP/CSO provenance coherent?"
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | BEAD_TYPES | Three types validated; forbidden fields rejected |
| B | STORE | Type separation enforced; no writeback |
| C | CONFLICT | Detected and surfaced; no resolution |
| D | SEMANTIC | Distance scores; no relevance ranking |
| E | HISTORY | Chronological trail; immutable |
| F | BUNNY | 24+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S37 COMPLETE

---

```yaml
STATUS: DRAFT_v0.1
NEXT: Socialize to GPT, GROK, OWL for input
THEN: Synthesize addendum → OPUS for v0.2
```
