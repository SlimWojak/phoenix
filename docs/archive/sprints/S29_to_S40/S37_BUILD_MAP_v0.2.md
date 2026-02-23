# S37_BUILD_MAP_v0.2.md — MEMORY DISCIPLINE

```yaml
document: S37_BUILD_MAP_v0.2.md
version: 0.2
date: 2026-01-29
status: OPUS_REFINED_FOR_EXECUTION
theme: "Memory, not myth"
codename: ATHENA_DISCIPLINE
dependencies: 
  - S35_CFP (COMPLETE)
  - S36_CSO (COMPLETE)
synthesized_from: [v0.1_DRAFT, GPT_ARCHITECT, OWL_STRUCTURAL, GROK_CHAOS]
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

PRIMARY_HARDENING_TARGET: |
  CLAIM BECOMES DOCTRINE — zombie path via:
    1. Claim fed to CSO predicates (execution leak)
    2. Claim used in alert rules (action leak)
    3. Auto-surfacing creates perceptual writeback
    4. Semantic "relevance" implies quality ranking

EXIT_GATE_SPRINT: |
  Athena stores claims with explicit type distinction.
  CONFLICT_BEADs surface when claim contradicts fact.
  System never resolves conflicts — human decides.
  No stored claim can mutate doctrine.
  Claims retrieved ONLY via explicit user query.
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
      
    # === ADVISOR ADDITIONS (v0.2) ===
    disclaimer: str  # MANDATORY — "HUMAN_ASSERTION_ONLY — no doctrine impact"
    
    statistical_parameters:  # OPTIONAL — for range-based conflict detection
      type: enum[point_estimate, range, percentage]
      value: any
      bounds: {lower: float, upper: float}  # for range claims
      # confidence_interval: FORBIDDEN — system cannot assign
      
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
      supersession_chain: list[str]  # v0.2: claim evolution context
      
    conflict:
      description: str  # auto-generated: "CLAIM asserts X, FACT shows Y"
      domain: str
      conflict_type: str  # "BOOLEAN" | "NUMERIC" | "STATISTICAL"
      severity: null  # FORBIDDEN — no ranking conflicts
      
    resolution:
      status: "OPEN"  # only value until human acts
      resolved_by: null  # human attribution when resolved
      resolution_action: null  # "CLAIM_UPDATED" | "CLAIM_RETAINED" | "FACT_DISPUTED" | "RESOLVED_BY_SUPERSESSION"
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
    - confidence_interval  # system cannot assign
  conflict_specific:
    - severity
    - urgency
    - auto_resolution

# === v0.2: CLAIM LANGUAGE LINTER ===
CLAIM_LANGUAGE_LINTER:
  banned_phrases:
    - "always"
    - "never"
    - "guaranteed"
    - "definitely"
    - "high probability"
    - "low risk"
    - "certainly"
    - "100%"
    - "impossible"
  enforcement: |
    Claim content must pass linter before storage.
    Reuse cfp/linter.py pattern.
  rationale: "Confidence sneaks in via language, not fields"

EXIT_GATE_A:
  criterion: "Three bead types validated; forbidden fields rejected; disclaimer mandatory"
  test: tests/test_athena/test_bead_types.py
  proof: |
    - CLAIM with verified=true REJECTED
    - CLAIM without disclaimer REJECTED
    - CLAIM with banned language REJECTED
    - FACT without provenance REJECTED
    - CONFLICT with severity REJECTED

INVARIANTS_PROVEN:
  - INV-ATTR-SILENCE (conflicts have no resolution authority)
  - INV-CLAIM-NO-EXECUTION (claims cannot be predicates)
```

### OPUS EXECUTION NOTES — TRACK A

```yaml
INTEGRATION_POINTS:
  - Extend memory/bead_store.py BeadType enum with CLAIM, FACT, CONFLICT
  - Create athena/ directory parallel to memory/ (or as submodule)
  - Reuse cfp/linter.py pattern for ClaimLanguageLinter

FILE_PATHS:
  - athena/schemas/claim_bead_schema.yaml
  - athena/schemas/fact_bead_schema.yaml  
  - athena/schemas/conflict_bead_schema.yaml
  - athena/bead_types.py
  - athena/claim_linter.py  # Reuse S35 linter pattern

TEST_PATTERNS:
  - test_claim_without_disclaimer_rejected()
  - test_claim_with_banned_language_rejected()
  - test_claim_with_statistical_parameters_accepted()
  - test_fact_without_provenance_rejected()
  - test_conflict_with_severity_rejected()

CONCERN_MITIGATION:
  statistical_parameters:
    - Optional field for range-based claims
    - bounds field enables statistical conflict detection
    - System cannot assign confidence_interval — only human-declared bounds
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
    get_open_conflicts() -> list[ConflictBead]  # SHUFFLED by default
    
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

# === v0.2: RATE LIMITING ===
RATE_LIMITS:
  max_claims_per_hour: 100
  max_facts_per_hour: 500
  max_conflicts_per_hour: 50  # per domain
  on_exceed: RATE_LIMIT + suppression_bead
  rationale: "Calibration storm → 1000+ beads in one session"

# === v0.2: NO AUTO-SURFACE ===
NO_AUTO_SURFACE:
  new_invariant: INV-NO-AUTO-SURFACE
  rule: "Claims retrieved ONLY via explicit user query"
  forbidden:
    - Auto-surface claim when chart opens
    - Auto-surface claim matching current market state
    - Push claim to notification plane without request
  rationale: "Auto-surfacing = unsolicited proposal = INV-NO-UNSOLICITED violation"

PERSISTENCE:
  backend: SQLite (consistent with BeadStore pattern)
  tables:
    - claim_beads
    - fact_beads
    - conflict_beads
    - bead_index (full-text search)
    - bead_embeddings (semantic search)

EXIT_GATE_B:
  criterion: "Store enforces type separation; no writeback possible; rate limited"
  test: tests/test_athena/test_store.py
  proof: |
    - Claim stored, retrieved with correct type
    - Fact stored with full provenance
    - Attempt to mutate doctrine from claim → REJECTED
    - 101st claim in hour → RATE_LIMIT
    - Auto-surface attempt → REJECTED

INVARIANTS_PROVEN:
  - INV-ATTR-NO-WRITEBACK (claims cannot mutate doctrine)
  - INV-NO-AUTO-SURFACE (no unsolicited surfacing)
```

### OPUS EXECUTION NOTES — TRACK B

```yaml
INTEGRATION_POINTS:
  - Can extend existing memory/bead_store.py or create separate athena/store.py
  - Reuse S36 AlertRateLimiter pattern for rate limiting
  - SQLite same pattern as existing BeadStore

FILE_PATHS:
  - athena/store.py (main store, delegates to type stores)
  - athena/claim_store.py
  - athena/fact_store.py
  - athena/conflict_store.py
  - athena/rate_limiter.py  # Reuse S36 pattern

EXECUTION_GUARD_IMPLEMENTATION:
  - Add _validate_no_execution() check in store_claim()
  - Block: claim_bead_id cannot appear in cso/predicates
  - Block: claim_bead_id cannot appear in alert rules
  - Block: claim_bead_id cannot appear in hunt parameters

TEST_PATTERNS:
  - test_claim_in_cso_predicate_rejected()
  - test_claim_in_alert_rule_rejected()
  - test_claim_in_hunt_parameter_rejected()
  - test_rate_limit_claims_per_hour()
  - test_auto_surface_rejected()
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
    
  # === v0.2: STATISTICAL CONFLICT ===
  statistical_conflict:
    trigger: "Fact value outside claim bounds (2-sigma default)"
    example: |
      CLAIM: "FVGs work 70% [bounds: 60-80%]"
      FACT: "FVGs worked 40% this week"
      RESULT: CONFLICT (40% < 60% lower bound)
    enforcement: Conflict detector checks bounds if statistical_parameters present
    
  domain_matching:
    - Conflicts only detected within same domain
    - Cross-domain claims/facts do not conflict
    
  threshold:
    - Boolean contradiction is binary
    - Statistical contradiction uses declared bounds
    - Ambiguous cases do NOT create conflicts (human must assert)

CONFLICT_CREATION:
  on_new_claim:
    1. Scan facts in same domain
    2. Check for direct contradictions
    3. Check statistical bounds if present
    4. If found: create CONFLICT_BEAD, status=OPEN
    5. Notify (bead emission, optional alert)
    
  on_new_fact:
    1. Scan claims in same domain
    2. Check for contradictions
    3. Check statistical bounds
    4. If found: create CONFLICT_BEAD, status=OPEN
    5. Notify

# === v0.2: RECURSIVE CONFLICT MAPPING ===
SUPERSESSION_CONFLICT_RULE:
  on_supersession:
    1. Re-evaluate conflict against new claim
    2. If conflict persists → update CONFLICT_BEAD provenance with chain
    3. If conflict resolved → mark as RESOLVED_BY_SUPERSESSION
    4. Historical conflict context preserved
  rationale: "Maintains conflict integrity across claim evolution"

# === v0.2: CONFLICT SHUFFLE ===
CONFLICT_SHUFFLE:
  new_invariant: INV-CONFLICT-SHUFFLE
  rule: "get_open_conflicts() MUST shuffle by default"
  override: Explicit chrono request requires T2
  rationale: "Same pattern as S36 display shuffle"

# === v0.2: NO AGGREGATION ===
CONFLICT_NO_AGGREGATION:
  new_invariant: INV-CONFLICT-NO-AGGREGATION
  forbidden:
    - Count of conflicts per domain
    - "Time open" sorting
    - Conflict frequency queries
    - "Domains with most conflicts"
    - "Oldest unresolved conflicts"
  rationale: "Prevents implicit severity via aggregation"

RESOLUTION_PROTOCOL:
  system_authority: NONE
  
  human_actions:
    CLAIM_UPDATED: "Human revises claim based on fact"
    CLAIM_RETAINED: "Human asserts claim despite fact (edge case)"
    FACT_DISPUTED: "Human questions fact methodology"
    RESOLVED_BY_SUPERSESSION: "Claim superseded, conflict moot"
    
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
  - Counting conflicts per domain
  - Sorting by time open

EXIT_GATE_C:
  criterion: "Conflicts detected (including statistical); shuffled output; no resolution authority"
  test: tests/test_athena/test_conflict_detection.py
  proof: |
    - Claim contradicting fact creates CONFLICT_BEAD
    - 70% claim vs 40% fact → CONFLICT (statistical)
    - Within-bounds fact → NO conflict
    - CONFLICT_BEAD has status=OPEN
    - get_open_conflicts() returns shuffled
    - No auto-resolution attempted
    - Conflict count query → REJECTED

INVARIANTS_PROVEN:
  - INV-ATTR-SILENCE (system does not resolve conflicts)
  - INV-CONFLICT-SHUFFLE (shuffled by default)
  - INV-CONFLICT-NO-AGGREGATION (no counts/sorting)
```

### OPUS EXECUTION NOTES — TRACK C

```yaml
STATISTICAL_CONFLICT_IMPLEMENTATION:
  - Check if claim has statistical_parameters
  - If bounds present: fact.value < bounds.lower OR fact.value > bounds.upper → CONFLICT
  - 2-sigma default means bounds = [mean - 2*std, mean + 2*std]
  - Human declares bounds — system doesn't compute them

SUPERSESSION_CHAIN:
  - On claim supersession, traverse conflict graph
  - Update CONFLICT_BEAD.references.supersession_chain
  - Simple cycle detection: if claim_id in chain → REJECT supersession

TEST_PATTERNS:
  - test_statistical_conflict_outside_bounds()
  - test_statistical_no_conflict_within_bounds()
  - test_conflict_list_shuffled()
  - test_conflict_count_query_rejected()
  - test_supersession_updates_conflict()
  - test_supersession_cycle_rejected()
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
    search(query: str, domain: str = None, bead_type: str = None, k: int = 5) -> list[SemanticResult]

  SemanticResult:
    bead: Bead
    distance: float  # embedding distance (lower = closer)
    # NOT "relevance" or "score" or "match_quality"

EMBEDDING_STRATEGY:
  model: sentence-transformers (local, no API dependency)
  recommended: all-MiniLM-L6-v2 (384 dim, fast, good quality)
  storage: Pre-computed embeddings in bead_embeddings table
  update: On bead creation
  
  fallback: If embedding unavailable, graceful degradation to keyword search

# === v0.2: UNORDERED NEIGHBORHOOD ===
UNORDERED_NEIGHBORHOOD:
  new_invariant: INV-SEMANTIC-NO-SINGLE-BEST
  rule: |
    - Results returned in bounded window (k=5 default)
    - Must declare: "unordered neighborhood"
    - Shuffle-within-band (distance ± 0.05) allowed
  forbidden:
    - "Top result"
    - "Best match"
    - "Most relevant"
    - Single-result queries

# === v0.2: DISTANCE NOISE ===
DISTANCE_NOISE:
  noise: ±0.01 random on render
  precision: 2dp only
  forbidden: percentage conversion
  rationale: "Breaks mental ranking"

# === v0.2: ASCENDING ONLY ===
ASCENDING_ONLY:
  rule: "sort_order: ASCENDING_ONLY (by distance)"
  reject: "ORDER BY distance DESC"
  chaos_vector: "Request sorted by distance descending → REJECT"

# === v0.2: SEMANTIC POLARITY ===
SEMANTIC_POLARITY:
  new_invariant: INV-SEMANTIC-POLARITY
  rule: "Domain opposites must maintain minimum distance threshold"
  implementation: |
    - Pre-built polar pairs: bullish/bearish, long/short, buy/sell
    - If polar match found at low distance (<0.2), flag as AMBIGUOUS
    - Do not return opposites as "similar"
  example: |
    Query: "Bullish FVG"
    Result with "Bearish Order Block" at distance 0.15
    Action: FLAG_AMBIGUOUS, not return as match

QUERY_RULES:
  output_order:
    - By distance (ascending) — factual, not "best"
    - Declare sort explicitly in response
    - Shuffle within band
    
  forbidden_language:
    - "most relevant"
    - "best match"
    - "top results"
    - "recommended"
    
  allowed_language:
    - "nearest semantic neighbors"
    - "unordered neighborhood (distance ≤ X)"
    - "ordered by distance (ascending)"

DISTANCE_DISPLAY:
  format: "distance: 0.23"  # raw number with noise
  forbidden:
    - Percentage conversion
    - "Match: 77%"
    - Color coding by distance
    - Bucketing ("High/Medium/Low match")

EXIT_GATE_D:
  criterion: "Semantic search returns unordered neighborhood; no relevance ranking; polarity handled"
  test: tests/test_athena/test_semantic_query.py
  proof: |
    - Results include distance field (with noise)
    - Results do NOT include relevance/score/quality
    - Output declares "unordered neighborhood"
    - Descending sort request → REJECTED
    - Polar match at low distance → FLAG_AMBIGUOUS

INVARIANTS_PROVEN:
  - INV-ATTR-NO-RANKING (distance, not relevance)
  - INV-SEMANTIC-NO-SINGLE-BEST (unordered neighborhood)
  - INV-SEMANTIC-POLARITY (polar handling)
```

### OPUS EXECUTION NOTES — TRACK D

```yaml
EMBEDDING_MODEL_SELECTION:
  recommended: sentence-transformers/all-MiniLM-L6-v2
  rationale: |
    - Local execution (no API dependency)
    - 384 dimensions (compact)
    - Good semantic quality
    - Fast inference (~5ms per query)
  installation: pip install sentence-transformers
  
POLAR_PAIRS_IMPLEMENTATION:
  pre_built_pairs:
    - (bullish, bearish)
    - (long, short)
    - (buy, sell)
    - (support, resistance)
    - (continuation, reversal)
  detection: |
    - Check query terms against polar set
    - Check result bead content against opposite polar
    - If match AND distance < 0.2 → FLAG_AMBIGUOUS

SHUFFLE_WITHIN_BAND:
  - Group results by distance band (±0.05)
  - Shuffle within each band
  - Return bands in ascending order

TEST_PATTERNS:
  - test_results_have_distance_not_relevance()
  - test_descending_sort_rejected()
  - test_polar_match_flagged_ambiguous()
  - test_results_shuffled_within_band()
  - test_distance_has_noise()
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
    get_claim_evolution(claim_id: str) -> list[ClaimBead]  # FULL chain, oldest-first
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

# === v0.2: NO BURY ===
HISTORY_NO_BURY:
  new_invariant: INV-HISTORY-NO-BURY
  rule: "get_claim_evolution() ALWAYS returns full chain oldest-first"
  forbidden:
    - Return only latest
    - Skip intermediate versions
    - Filter by "current only"
  output_addition:
    chain_length: int  # raw count, no judgment
  rationale: "Selective history = myth rewriting"

# === v0.2: CYCLE PREVENTION ===
CYCLE_PREVENTION:
  validation_rule:
    on_supersession: Check for cycle
    if_cycle_detected: REJECT with error
  implementation: Simple graph traversal on supersession write

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
  criterion: "History returns full chain oldest-first; no selective retrieval"
  test: tests/test_athena/test_history.py
  proof: |
    - get_claim_evolution() returns full chain
    - Latest-only request → full chain anyway
    - Supersession cycle → REJECTED
    - Chain includes chain_length count

INVARIANTS_PROVEN:
  - Bead immutability maintained
  - INV-HISTORY-NO-BURY (full chain always)
```

### OPUS EXECUTION NOTES — TRACK E

```yaml
CYCLE_DETECTION:
  algorithm: DFS from new claim through supersession chain
  complexity: O(chain_length) — acceptable for typical chains
  implementation: |
    def check_cycle(new_claim_id, supersedes_id):
        visited = {new_claim_id}
        current = supersedes_id
        while current:
            if current in visited:
                raise CycleDetectedError()
            visited.add(current)
            current = get_claim(current).superseded_by

TEST_PATTERNS:
  - test_evolution_returns_full_chain()
  - test_latest_only_returns_full_chain()
  - test_supersession_cycle_rejected()
  - test_chain_includes_length()
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
    - CRITICAL: Claims cannot be CSO predicates

CHAOS_VECTORS (BUNNY) — 28+:

  # Wave 1: Claim Execution Attacks (Critical)
  claim_execution_attacks:
    - Feed claim to CSO predicates → REJECT (INV-CLAIM-NO-EXECUTION)
    - Use claim in alert rule → REJECT
    - Reference claim in hunt parameters → REJECT
    
  # Wave 2: Writeback Attacks
  writeback_attacks:
    - Store claim, attempt doctrine mutation → REJECTED
    - Store claim referencing conditions.yaml → REJECTED
    - Store claim with "verified: true" → REJECTED
    
  # Wave 3: Resolution Attacks
  resolution_attacks:
    - Trigger conflict, attempt auto-resolve → REJECTED
    - Inject severity into conflict → REJECTED
    - Request "most important conflicts" → REJECTED
    
  # Wave 4: Conflict Aggregation Attacks
  conflict_aggregation_attacks:
    - Request "conflicts per domain count" → REJECT
    - Request "oldest unresolved conflicts" → REJECT
    - Request "domains with most conflicts" → REJECT
    
  # Wave 5: Semantic Ranking Attacks
  semantic_ranking_attacks:
    - Request "most similar" → REJECT
    - Request "top match" → REJECT
    - Request distance descending → REJECT
    - Request "claims closest AND recent" → REJECT
    
  # Wave 6: Auto-Surface Attacks
  auto_surface_attacks:
    - Trigger claim surface on chart open → REJECT
    - Push claim matching market state → REJECT
    
  # Wave 7: History Attacks
  history_attacks:
    - Request "claims that were contradicted most" → REJECT
    - Request "facts that disproved claims" → REJECT
    - Request latest-only from evolution → full chain returned
    - Create supersession cycle → REJECT
    
  # Wave 8: Statistical Conflict
  statistical_conflict:
    - 70% claim vs 40% fact → CONFLICT detected
    - Within-bounds fact → NO conflict
    
  # Wave 9: Polarity Attacks
  polarity_attacks:
    - Query "Bullish" returns "Bearish" match → FLAG_AMBIGUOUS
    
  # Wave 10: Flood Attacks
  flood_attacks:
    - 101 claims in 1 hour → Rate limit
    - 51 conflicts in domain/hour → Rate limit
    
  # Wave 11: Type Confusion
  type_confusion:
    - Store fact as claim → REJECTED (type validation)
    - Store claim without attribution → REJECTED
    - Store fact without provenance → REJECTED
    - Store claim without disclaimer → REJECTED

EXIT_GATE_F:
  criterion: "Athena passes all chaos vectors; no myth leakage"
  test: tests/chaos/test_bunny_s37.py
  proof: "28+ chaos vectors handled correctly"

INVARIANTS_PROVEN:
  - All S37 invariants (integration test)
  - INV-ATTR-NO-WRITEBACK
  - INV-ATTR-SILENCE
  - INV-CLAIM-NO-EXECUTION
  - INV-NO-AUTO-SURFACE
```

---

## NEW INVARIANTS SUMMARY (v0.2)

```yaml
ADDED_INVARIANTS:

  INV-CLAIM-NO-EXECUTION:
    rule: "No consumer may treat CLAIM_BEAD as executable predicate"
    tracks: A, B, F
    source: GROK
    enforcement: |
      - CSO evaluator rejects claim_bead_id as predicate source
      - Alert rules cannot reference claim assertions
      - Hunt engine cannot use claims as parameters
    
  INV-NO-AUTO-SURFACE:
    rule: "Claims retrieved ONLY via explicit user query"
    tracks: B
    source: OWL
    enforcement: Store validation blocks auto-surface intents
    
  INV-CONFLICT-SHUFFLE:
    rule: "get_open_conflicts() MUST shuffle by default"
    tracks: C
    source: GROK
    enforcement: Shuffle in conflict_store.py
    
  INV-CONFLICT-NO-AGGREGATION:
    rule: "No counts, time-sorting, or frequency queries on conflicts"
    tracks: C
    source: GPT
    enforcement: Query validation rejects aggregation patterns
    
  INV-SEMANTIC-NO-SINGLE-BEST:
    rule: "Results as unordered neighborhood, no 'top result'"
    tracks: D
    source: GPT
    enforcement: Response formatter shuffles within band
    
  INV-SEMANTIC-POLARITY:
    rule: "Domain opposites must maintain minimum distance"
    tracks: D
    source: OWL
    enforcement: Pre-built polar pairs, flag ambiguous
    
  INV-HISTORY-NO-BURY:
    rule: "Full supersession chain always returned oldest-first"
    tracks: E
    source: GROK
    enforcement: get_claim_evolution() ignores filters

TOTAL_S37_INVARIANTS: 9 (2 original + 7 new)
```

---

## OPUS REVIEW QUESTIONS — ANSWERED

```yaml
Q1_STATISTICAL_CONFLICT:
  question: "2-sigma default appropriate? Configurable?"
  answer: |
    2-sigma is appropriate as default (95% coverage).
    NOT configurable by system — bounds declared by human.
    Implementation: If claim.bounds exists, use claim.bounds.
    If human declares "about 70%", they implicitly provide bounds.

Q2_SEMANTIC_POLARITY:
  question: "Implementation complexity? Pre-built polar pairs or dynamic?"
  answer: |
    Pre-built polar pairs — simpler, predictable.
    ~10 pairs sufficient: bullish/bearish, long/short, buy/sell, etc.
    Store in athena/polar_pairs.yaml.
    Dynamic detection adds complexity without clear benefit.

Q3_RECURSIVE_CONFLICT_MAPPING:
  question: "Performance concern on deep chains?"
  answer: |
    Typical claim chain < 10 deep.
    Simple graph traversal O(n) is acceptable.
    If chains grow > 50, add chain_depth limit with T2 override.
    Monitor via suppression_bead if limit hit.

Q4_CLAIM_LANGUAGE_LINTER:
  question: "Reuse S35/S36 linter pattern or new module?"
  answer: |
    Reuse cfp/linter.py pattern structure.
    New file: athena/claim_linter.py
    Load banned phrases from athena/claim_banned_phrases.yaml
    Same Violation/LintResult dataclasses.

Q5_EMBEDDING_MODEL:
  question: "sentence-transformers local viable?"
  answer: |
    Yes — all-MiniLM-L6-v2 recommended.
    - Local execution (no API calls)
    - 384 dimensions (compact storage)
    - ~5ms inference per query
    - pip install sentence-transformers (~100MB)
    Fallback to keyword search if embeddings unavailable.
```

---

## DAY-BY-DAY BUILD SEQUENCE

```yaml
DAY_1:
  track: A (partial)
  deliverables:
    - athena/schemas/*.yaml (all 3)
    - athena/bead_types.py (dataclasses)
  tests: test_bead_types.py (schema validation)
  checkpoint: "Schemas validate; forbidden fields rejected"

DAY_2:
  track: A (complete) + B (partial)
  deliverables:
    - athena/claim_linter.py
    - athena/store.py (interface)
    - athena/claim_store.py
  tests: test_claim_linter.py, test_claim_store.py
  checkpoint: "Claims stored with disclaimer; banned language rejected"

DAY_3:
  track: B (complete)
  deliverables:
    - athena/fact_store.py
    - athena/conflict_store.py
    - athena/rate_limiter.py
  tests: test_store.py (full)
  checkpoint: "All stores operational; rate limited; no auto-surface"

DAY_4:
  track: C
  deliverables:
    - athena/conflict_detector.py
    - athena/conflict_rules.yaml
  tests: test_conflict_detection.py
  checkpoint: "Conflicts detected (boolean + statistical); shuffled; no aggregation"

DAY_5:
  track: D
  deliverables:
    - athena/embeddings.py
    - athena/semantic.py
    - athena/polar_pairs.yaml
  tests: test_semantic_query.py
  checkpoint: "Semantic search returns unordered neighborhood; polarity handled"

DAY_6:
  track: E
  deliverables:
    - athena/history.py
  tests: test_history.py
  checkpoint: "Full chain returned; cycle prevention works"

DAY_7:
  track: F
  deliverables:
    - athena/__init__.py
    - athena/api.py
    - tests/chaos/test_bunny_s37.py
  tests: test_integration.py, test_bunny_s37.py
  checkpoint: "28+ chaos vectors pass; no myth leakage"
```

---

## EXIT GATES SUMMARY

| Track | Gate | Binary Criterion |
|-------|------|------------------|
| A | BEAD_TYPES | Three types validated; disclaimer mandatory; linter rejects banned language |
| B | STORE | Type separation enforced; no writeback; rate limited; no auto-surface |
| C | CONFLICT | Detected (boolean + statistical); shuffled; no aggregation |
| D | SEMANTIC | Unordered neighborhood; no relevance; polarity flagged |
| E | HISTORY | Full chain always; cycle prevented |
| F | BUNNY | 28+ chaos vectors pass |

**Sprint Exit:** ALL tracks GREEN → S37 COMPLETE

---

## FILES TO CREATE

```yaml
athena/:
  - __init__.py
  - api.py
  - bead_types.py
  - claim_linter.py
  - claim_store.py
  - conflict_detector.py
  - conflict_store.py
  - embeddings.py
  - fact_store.py
  - history.py
  - rate_limiter.py
  - semantic.py
  - store.py
  schemas/:
    - claim_bead_schema.yaml
    - fact_bead_schema.yaml
    - conflict_bead_schema.yaml
  - claim_banned_phrases.yaml
  - conflict_rules.yaml
  - polar_pairs.yaml

tests/:
  test_athena/:
    - __init__.py
    - conftest.py
    - test_bead_types.py
    - test_claim_linter.py
    - test_conflict_detection.py
    - test_history.py
    - test_integration.py
    - test_semantic_query.py
    - test_store.py
  chaos/:
    - test_bunny_s37.py
```

---

```yaml
STATUS: OPUS_REFINED_v0.2
CONFIDENCE: HIGH
PATTERN: PROVEN x3 (S35 + S36 same day)
READY: CLEARED_FOR_EXECUTION_ON_CTO_APPROVAL
```

**Awaiting CTO clearance to execute S37 Day 1.** 🐗🔥
