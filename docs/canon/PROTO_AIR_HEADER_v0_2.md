# PROTO-AIR HEADER SPECIFICATION

```yaml
document: PROTO_AIR_HEADER
version: 0.2
date: 2026-03-01
status: DRAFT — Joist Pattern Round 1 complete (GPT + OWL + BOAR → CTO synthesis)
purpose: Define the attestation envelope shape for the Agent Integrity Runtime
scope: SCHEMA ONLY — no runtime, no enforcement, no orchestration
owner: CTO (synthesized from 2 rounds: pre-flight inputs + pressure test)
prerequisite: DEC-BRIDGE-BEFORE-AIR (Bridge notary envelope is the alignment target)
feeds_into: S64 GATE_3_AIR (full implementation informed by S63 observation friction)
amendments:
  v0.1: |
    Initial draft. 5-group envelope (identity, build, llm_context, action, signatures).
    Bridge alignment clause. Action taxonomy (HIGH/MEDIUM/LOW). Trust surface definition.
    Anomaly classification vocabulary. 4 open questions for Joist.
  v0.2: |
    Joist Pattern Round 1 complete. GPT lint + OWL strategic audit + BOAR chaos stress.
    +2 fields (thought_log_hash, sequence_index). +5 invariants. +1 anomaly enum.
    4 tightenings (prompt_hash, output_bead_refs, snapshot_hash, llm_context).
    2 future hooks (velocity monitoring, batch signature verification).
    Rejected: chaos_seed nonce, prompt_hash relocation, tag arrays, inline Merkle paths.
    Key decisions: thought_log_hash is breadcrumb-only (no retention mandate),
    ANOMALY_CLASS stays enum (constitutional vocabulary), snapshot_hash non-null
    scoped to bead-lineage actions only.
```

---

## 0. WHAT THIS IS AND WHAT IT IS NOT

```yaml
THIS_IS:
  - The attestation envelope schema that wraps every agent action
  - A declarative trust surface definition
  - Bridge-aligned field specification
  - Input to the S64 AIR implementation sprint

THIS_IS_NOT:
  - A runtime enforcement engine
  - Agent orchestration logic
  - A verification daemon
  - A revocation system
  - Code

DESIGN_PRINCIPLE: |
  The Bridge notary wraps GOVERNANCE EVENTS (Phoenix → Bead Field).
  AIR wraps AGENT ACTIONS (any agent → any bead-producing operation).
  Same philosophy: proof-bearing envelope, cryptographic seal, fail-closed.
  Different trust surface: Bridge trusts Phoenix. AIR trusts nothing.
```

---

## 1. AGENT ATTESTATION ENVELOPE

The core schema. Every agent action that produces or modifies a structural bead
MUST be wrapped in this envelope. Unsigned actions are invalid by definition.

```yaml
AGENT_ATTESTATION_ENVELOPE:
  version: "0.2"

  # --- AGENT IDENTITY ---
  agent_identity:
    agent_id: string           # Unique agent instance identifier (UUID v7)
    agent_role: enum           # [DIRECTOR, LIBRARIAN, RESEARCHER, EXECUTOR, MONITOR]
    office: enum               # [PHOENIX, DEXTER, ORACLE]
    node_id: string            # Physical node executing (NODE_M3, NODE_M4, NODE_DGX, etc.)

  # --- BUILD PROVENANCE ---
  build_provenance:
    code_hash: string          # SHA-256 of full executable surface (not partial module)
    build_tag: string          # Git tag or commit hash
    config_hash: string        # SHA-256 of agent configuration at execution time
    container_hash: string | null  # Container digest if containerized, null if bare metal
    # INV-AIR-CONTAINER-CODE: if container_hash != null → code_hash MUST match container image manifest

  # --- LLM CONTEXT (forensic, not enforcement) ---
  # INV-AIR-LLM-ATOMIC: All-or-nothing. If model_id is present, ALL llm_context
  # fields MUST be present. If model_id is null, ALL MUST be null. No partial attestation.
  llm_context:
    model_id: string | null    # e.g., "claude-opus-4-6", "deepseek-r1", null if no LLM
    model_version: string | null  # Provider version string or weight hash
    prompt_hash: string | null # SHA-256 of (system prompt + tool schema + hidden preamble)
    temperature: float | null  # Sampling temperature (null if deterministic or no LLM)
    context_token_count: int | null  # Tokens consumed (cost tracking + anomaly detection)
    reasoning: enum | null     # [STANDARD, EXTENDED, NONE, null] — thinking mode

  # --- ACTION ---
  action:
    action_type: enum          # See Section 2 (ACTION_TAXONOMY)
    action_id: string          # Unique action identifier (UUID v7)
    action_payload_hash: string  # SHA-256 of the action's input/output payload
    input_bead_refs: array[string]  # Bead IDs consumed as input
    # INV-AIR-MERKLE-BEFORE-HASH: input_bead_refs Merkle-verified BEFORE envelope_hash calculation
    output_bead_refs: array[string]  # Bead IDs produced (empty ONLY for read-only actions)
    hlc_timestamp: string      # Hybrid Logical Clock timestamp at action execution
    sequence_index: integer    # Monotonic per agent_id per session, starts at 1
    thought_log_hash: string | null  # SHA-256 of ephemeral reasoning at commit boundary
    # INV-AIR-NO-EPHEMERAL-RETENTION-REQUIREMENT: presence/absence of thought_log_hash
    # MUST NOT gate envelope validity or require ephemeral log storage.
    # Hash computed from canonical serialization of ephemeral bundle at commit time.
    # null = no ephemeral log existed. Non-null = verifiable breadcrumb IF logs retained.

  # --- CRYPTOGRAPHIC SEAL ---
  signature_bundle:
    ecdsa:
      algorithm: "ECDSA-secp256r1"
      public_key: string       # Agent's ECDSA public key
      signature: string        # ECDSA signature over envelope_hash
    pqc:
      algorithm: "ML-DSA-65"   # Dilithium3 (NIST PQC standard)
      public_key: string       # Agent's PQC public key
      signature: string        # PQC signature over envelope_hash
    envelope_hash: string      # SHA-256 of all fields above (excluding signature_bundle)
    signing_cert_chain: array[string]  # Certificate chain for key verification

  # --- BRIDGE ALIGNMENT ---
  bridge_alignment:
    envelope_version: "0.2"    # Must match Bridge notary envelope version
    snapshot_hash: string | null  # Temporal snapshot hash (mirrors INV-BRIDGE-TEMPORAL-SNAPSHOT)
    # Nullability rule: see Section 4 SNAPSHOT_HASH_APPLICABILITY
    governance_event_ref: string | null  # If this action produces a governance event, ref here
```

---

## 2. ACTION TAXONOMY

Actions classified by trust surface. This determines what AIR signs and what it does not.

```yaml
ACTION_TAXONOMY:
  # --- HIGH IMPACT (full AIR envelope required) ---
  HIGH_IMPACT:
    BEAD_COMMIT:
      description: "Agent commits a structural bead to the Bead Field"
      signed: MANDATORY
      snapshot_hash: REQUIRED  # Touches bead lineage
      bead_types: [FACT, CLAIM, SIGNAL, PROPOSAL, PROPOSAL_REJECTED, SKILL, MODEL_VERSION, POLICY]
      # INV-AIR-COMMIT-BOUNDARY: Only BEAD_COMMIT actions produce structural state mutation.

    ORDER_SUBMIT:
      description: "Agent submits a trade order (live or paper)"
      signed: MANDATORY
      snapshot_hash: REQUIRED  # Market-derived, temporal state matters
      governance_gate: T2_HUMAN_APPROVAL
      note: "AIR envelope + T2 gate. Both required. Neither sufficient alone."

    POLICY_CHANGE:
      description: "Agent modifies a POLICY bead (risk rules, limits, regimes)"
      signed: MANDATORY
      snapshot_hash: OPTIONAL  # Administrative — no bead lineage reference
      governance_gate: SOVEREIGN_APPROVAL

    MODEL_DEPLOY:
      description: "Agent deploys a new MODEL_VERSION to production"
      signed: MANDATORY
      snapshot_hash: OPTIONAL  # Administrative — config snapshot, not temporal
      governance_gate: SOVEREIGN_APPROVAL

    SKILL_PROMOTE:
      description: "Agent promotes SKILL from CANDIDATE → VALIDATED"
      signed: MANDATORY
      snapshot_hash: REQUIRED  # Traces to rejection lineage in bead field
      governance_gate: OLYA_APPROVAL  # INV-OLYA-ABSOLUTE

  # --- MEDIUM IMPACT (AIR envelope required, no human gate) ---
  MEDIUM_IMPACT:
    QUERY_CROSS_PAIR:
      description: "Agent executes FieldQuery across multiple pair databases"
      signed: MANDATORY
      snapshot_hash: OPTIONAL
      note: "Read-only but cross-pair access reveals trading intent — sovereignty concern"

    BRIDGE_PROJECT:
      description: "Bridge projects governance event as FACT bead"
      signed: MANDATORY
      snapshot_hash: REQUIRED  # Temporal snapshot at projection time
      note: "Already covered by Bridge notary. AIR adds agent-level attestation."

  # --- LOW IMPACT (envelope optional, logging sufficient) ---
  LOW_IMPACT:
    QUERY_SINGLE:
      description: "Agent queries single pair database"
      signed: OPTIONAL
      snapshot_hash: NOT_APPLICABLE
      note: "Read-only, single scope. Log for audit, don't sign for performance."
      escalation_note: "LOW_IMPACT may be promoted to signed mode by runtime policy (S64)"

    EPHEMERAL_THOUGHT:
      description: "Agent thinking, scratchpad, intermediate computation"
      signed: NEVER
      snapshot_hash: NOT_APPLICABLE
      note: "Ephemeral layer. Unsigned. Disposable. INV-COMMITMENT-THRESHOLD."

AIR_DOES_NOT_SIGN:
  - Ephemeral agent thinking (scratchpad, chain-of-thought)
  - Human chat messages (outside system boundary)
  - Log entries (operational, not constitutional)
  - Health checks and heartbeats
  - Configuration reads (no mutation)
```

---

## 3. TRUST SURFACE DEFINITION

```yaml
WHAT_AIR_ATTESTS:
  1: "This action was executed by agent {agent_id} running code {code_hash}"
  2: "The code was built from {build_tag} with config {config_hash}"
  3: "If an LLM was involved, it was {model_id} at {temperature} with prompt {prompt_hash}"
  4: "The action consumed beads {input_bead_refs} and produced beads {output_bead_refs}"
  5: "The action occurred at HLC time {hlc_timestamp} on node {node_id}"
  6: "This was action #{sequence_index} from this agent in this session"
  7: "If ephemeral reasoning existed, its hash is {thought_log_hash}"
  8: "All of the above is signed with PQC + ECDSA dual signatures"

WHAT_AIR_DOES_NOT_ATTEST:
  1: "Correctness of the action's output (that's the methodology's job)"
  2: "Quality of the LLM's reasoning (that's the Dream Cycle's job)"
  3: "Market outcome of a trade (that's reality's job)"
  4: "Whether the human should approve (that's sovereignty's job)"
  5: "Whether ephemeral logs should be retained (that's operational policy)"
  note: |
    AIR proves WHO did WHAT with WHICH tools at WHEN in WHAT ORDER.
    It does not prove the action was WISE. Wisdom is Olya's domain.

INVALID_ENVELOPE:
  missing_agent_id: REJECT          # Anonymous actions are unconstitutional
  missing_code_hash: REJECT         # Unverifiable code = untrusted
  missing_signatures: REJECT        # Unsigned = unsigned. No exceptions.
  signature_mismatch: REJECT        # Either sig fails = full rejection
  stale_build_tag: REJECT           # Build tag not in approved builds registry
  hlc_non_monotonic: REJECT         # Time must advance. Always.
  input_bead_unverified: REJECT     # Input beads must pass hash + Merkle check
  missing_action_type: REJECT       # Unclassified actions cannot be signed
  sequence_index_non_monotonic: REJECT  # Must strictly increment per agent per session
  partial_llm_context: REJECT       # All-or-nothing. INV-AIR-LLM-ATOMIC.

UNSIGNED_MUTATION_SEMANTICS:
  definition: "Any state change to the Bead Field without a valid AIR envelope"
  response: REJECT + SECURITY_EVENT_BEAD
  note: |
    In S64 implementation, unsigned mutations will be:
    1. Rejected at the ingestion boundary (fail-closed)
    2. Logged as SECURITY_EVENT beads (signed by the system, not the agent)
    3. Surfaced in the next Mirror Report
    This section defines the CONCEPT. S64 builds the ENFORCEMENT.
```

---

## 4. BRIDGE ALIGNMENT CLAUSE

```yaml
GOVERNING_DECISION: DEC-BRIDGE-BEFORE-AIR
CONSTRAINT: "AIR aligns to Bridge. Bridge does not change for AIR."

FIELD_SUPERSET_RULE:
  rule: |
    Every field in the Bridge notary NotarizedEnvelope MUST have
    a corresponding field or derivable mapping in the AIR envelope.
    AIR may add fields. AIR may NOT omit Bridge fields.
  rationale: |
    Bridge is proven (7/7 invariants, 191 tests). AIR is speculative.
    The proven system constrains the new system, not vice versa.

BRIDGE_FIELD_MAPPING:
  bridge_governance_event → action.action_type + action.action_payload_hash
  bridge_signature → signature_bundle (superset — Bridge has single sig, AIR has dual)
  bridge_hash_chain → envelope_hash (same role — integrity anchor)
  bridge_replay_guard → action.action_id + action.sequence_index (monotonic + unique + ordered)
  bridge_monotonic_gt → action.hlc_timestamp (HLC subsumes GT monotonicity)
  bridge_version → bridge_alignment.envelope_version
  bridge_temporal_snapshot → bridge_alignment.snapshot_hash

NO_CONTRADICTION_RULE:
  rule: |
    No AIR envelope field may assert a value that contradicts
    the Bridge notary's verification of the same event.
  example: |
    If Bridge says governance_event.gt = 1000,
    AIR cannot wrap that event with hlc_timestamp < 1000.
    The envelope timestamps must be monotonically consistent.

SNAPSHOT_HASH_APPLICABILITY:
  rule: |
    snapshot_hash captures WT/KT verification state frozen at action time.
    Applicability determined by whether the action references bead field state.
  required_actions: [BEAD_COMMIT, ORDER_SUBMIT, SKILL_PROMOTE, BRIDGE_PROJECT]
  optional_actions: [POLICY_CHANGE, MODEL_DEPLOY, QUERY_CROSS_PAIR]
  not_applicable: [QUERY_SINGLE, EPHEMERAL_THOUGHT]
  rationale: |
    Actions that touch bead lineage or market-derived outputs MUST capture
    temporal state. Administrative actions (policy, deployment) operate on
    config state, not bead field state — snapshot is available but not mandated.
    Prevents ritual non-null compliance on actions with no meaningful temporal slice.

SNAPSHOT_FREEZE_ALIGNMENT:
  rule: |
    AIR snapshot_hash uses the same freeze semantics as
    INV-BRIDGE-TEMPORAL-SNAPSHOT: WT/KT verification state
    frozen at action time, hash included in envelope.
  rationale: "One temporal truth. Two consumers. Zero drift."
```

---

## 5. ANOMALY CLASSIFICATION

Envelope fields that enable future anomaly detection without implementing it now.

```yaml
ANOMALY_CLASS: enum
  values:
    NONE: "No anomaly detected"
    REFINERY_LATENCY_SPIKE: "WT-KT delta exceeds threshold"
    ZERO_LATENCY: "WT ≈ KT (suspicious — hallucinated timestamps?)"
    INPUT_CHAIN_BREAK: "Input bead hash chain verification failed"
    MODEL_DRIFT: "Same prompt_hash + different model_version producing divergent outputs"
    CONTEXT_OVERFLOW: "context_token_count approaching or exceeding model limit"
    UNSIGNED_MUTATION_ATTEMPT: "State change attempted without valid envelope"
    HALLUCINATED_PAYLOAD: "Structurally valid but factually impossible output"

  governance:
    amendment_process: |
      New anomaly categories require a spec amendment with:
      1. Name and description
      2. Detection criteria (what makes this distinct)
      3. At least one concrete example
      4. CTO approval
      This is constitutional vocabulary. No silent additions.
    rationale: |
      Enums force classification discipline. Every new category creates
      an audit trail of WHY it was needed. Tag arrays invite unstructured
      drift that destroys comparability and enables quiet governance erosion.

  # INV-AIR-ANOMALY-EXCLUDED: ANOMALY_CLASS is advisory metadata.
  # NOT included in envelope_hash. Anomaly classification changes
  # MUST NOT invalidate existing signatures.

  note: |
    This enum is INFORMATIONAL in Proto-AIR. It exists so that:
    1. S64 AIR implementation has a defined vocabulary for anomalies
    2. Dream Cycle can classify failures by anomaly type
    3. Future anomaly detection has named categories to target
    No daemon. No enforcement. Just the dictionary.

FUTURE_HOOKS:
  proof_of_computation:
    description: "Verify agent followed methodology before signing"
    status: DEFERRED_TO_S64
    note: |
      OWL provocation. This requires runtime verification —
      checking that a SIGNAL bead actually traces through the
      correct gate sequence. Proto defines the action_type taxonomy
      that makes this checkable. S64 builds the checker.

  anomaly_triggered_halt:
    description: "AIR triggers HALT_OPERATIONAL on critical anomaly"
    status: DEFERRED_TO_S64+
    note: |
      OWL provocation. Requires wiring AIR → Phoenix halt system.
      Proto defines the ANOMALY_CLASS vocabulary.
      S64+ builds the escalation path.

  velocity_monitoring:
    description: "Rate-based impact escalation (LOW × volume → HIGH system threat)"
    status: DEFERRED_TO_S64
    note: |
      OWL + BOAR convergence. sequence_index enables burst detection
      without runtime enforcement. S64 builds the rate-limiting policy.
      LOW_IMPACT actions may be promoted to signed mode by runtime policy.

  batch_signature_verification:
    description: "Amortize signing cost across query fan-out operations"
    status: DEFERRED_TO_S64
    note: |
      BOAR proposal. QUERY_CROSS_PAIR signing at scale may impact
      the 21ms query path. Batch verification amortizes cost without
      envelope redesign. S64 benchmarks and implements if needed.
```

---

## 6. INVARIANT REGISTRY

All invariants introduced or referenced by Proto-AIR.

```yaml
# --- NEW (Proto-AIR v0.2) ---
INV-AIR-CONTAINER-CODE:
  rule: "If container_hash != null → code_hash MUST match container image manifest"
  enforcement: Schema validation at envelope creation
  source: GPT lint round 1

INV-AIR-MERKLE-BEFORE-HASH:
  rule: "input_bead_refs Merkle-verified BEFORE envelope_hash calculation"
  enforcement: "S64 implementation MUST prove ordering via test"
  note: "Schema says WHAT. S64 proves HOW."
  source: GPT lint round 1

INV-AIR-ANOMALY-EXCLUDED:
  rule: "ANOMALY_CLASS is advisory metadata, NOT included in envelope_hash"
  enforcement: "envelope_hash computation excludes anomaly fields"
  rationale: "Prevent anomaly classification drift from invalidating signatures"
  source: GPT + OWL convergence

INV-AIR-COMMIT-BOUNDARY:
  rule: "Only BEAD_COMMIT actions produce structural state mutation in the Bead Field"
  enforcement: "Ingestion boundary rejects mutations without BEAD_COMMIT action_type"
  source: GPT lint round 1

INV-AIR-NO-EPHEMERAL-RETENTION-REQUIREMENT:
  rule: "Presence/absence of thought_log_hash MUST NOT gate envelope validity or require log storage"
  enforcement: "Envelope validation ignores thought_log_hash null/non-null status"
  rationale: "Prevents creation of de facto third substrate or retention norm"
  source: GPT pressure test + CTO synthesis

INV-AIR-LLM-ATOMIC:
  rule: "LLM context is all-or-nothing. model_id present → all fields present. model_id null → all null."
  enforcement: "Schema validation rejects partial llm_context population"
  source: CTO v0.1 + GPT tightening

# --- REFERENCED (existing, not modified) ---
INV-BRIDGE-TEMPORAL-SNAPSHOT:
  rule: "Promotion freezes WT/KT verification state at promotion time"
  source: Bridge invariants (S62)

INV-COMMITMENT-THRESHOLD:
  rule: "Only Formal Handoffs become beads. commit() is bright line."
  source: BEAD_FIELD_SPEC v0.3

INV-HUMAN-FRAMES:
  rule: "Human frames. Machine computes. Human promotes."
  source: Master Plan

INV-OLYA-ABSOLUTE:
  rule: "Olya's NO on methodology is absolute"
  source: Master Plan
```

---

## 7. VERIFICATION CHECKLIST (Schema-Level)

What a valid envelope looks like. Not how to verify it — that's S64.

```yaml
ENVELOPE_VALIDITY_CHECKLIST:
  identity:
    - agent_id: present, UUID v7 format
    - agent_role: present, in enum
    - office: present, in enum
    - node_id: present, matches known topology

  provenance:
    - code_hash: present, SHA-256 format, covers full executable surface
    - build_tag: present, non-empty
    - config_hash: present, SHA-256 format
    - container_hash: if present, code_hash matches container manifest (INV-AIR-CONTAINER-CODE)

  llm_context:
    - if model_id present: ALL fields (model_version, prompt_hash, temperature,
      context_token_count, reasoning) MUST be present (INV-AIR-LLM-ATOMIC)
    - if model_id null: ALL llm_context fields MUST be null
    - prompt_hash scope: system prompt + tool schema + hidden preamble

  action:
    - action_type: present, in ACTION_TAXONOMY
    - action_id: present, UUID v7 format
    - action_payload_hash: present, SHA-256 format
    - hlc_timestamp: present, canonical format (YYYY-MM-DDTHH:MM:SS.ffffff+00:00)
    - sequence_index: present, integer, strictly monotonic per agent_id per session
    - input_bead_refs: present (may be empty for root actions), Merkle-verified (INV-AIR-MERKLE-BEFORE-HASH)
    - output_bead_refs: present (empty ONLY for read-only actions QUERY_*)
    - thought_log_hash: present (null permitted — does NOT affect validity)

  signatures:
    - ecdsa.signature: present, valid format
    - pqc.signature: present, valid format
    - envelope_hash: SHA-256 of all non-signature fields, EXCLUDING anomaly metadata
    - signing_cert_chain: present, non-empty

  bridge_alignment:
    - envelope_version: present, matches current Bridge version
    - snapshot_hash: see Section 4 SNAPSHOT_HASH_APPLICABILITY for nullability rules
    - governance_event_ref: present if action produces governance-relevant output
```

---

## 8. RELATIONSHIP TO EXISTING SPECS

```yaml
BEAD_FIELD_SPEC_v0_3:
  section_3_1_attestation:
    current_fields: [air_node_id, code_hash, model_hash, container_hash, ecdsa_sig, pqc_sig, signing_cert_chain]
    proto_air_relationship: |
      The bead-level attestation fields in BEAD_FIELD_SPEC v0.3 Section 3.1
      are a SUBSET of the Proto-AIR envelope. When S64 implements AIR:
      - Bead attestation fields are POPULATED FROM the AIR envelope
      - The envelope is the source of truth; the bead fields are projections
      - This maintains backward compatibility with Gate 1 + Gate 2 code
    new_fields_not_in_bead_spec: |
      sequence_index, thought_log_hash, prompt_hash (expanded scope),
      temperature, context_token_count, reasoning — these live in the
      ENVELOPE only. They do not need to be added to the bead schema.
      Beads reference envelopes. Envelopes carry the full attestation.
    migration_note: |
      Existing beads (Genesis 789 + 11.4M synthetic) were created pre-AIR.
      Their attestation fields use the ingestion pipeline's signing keys.
      Post-AIR beads will have attestation populated from agent envelopes.
      Both are valid. The signing authority differs, not the format.

BRIDGE_NOTARY:
  relationship: "AIR envelope is a superset. See Section 4 BRIDGE ALIGNMENT CLAUSE."
  sequence_index_benefit: |
    Bridge replay guard now has two defenses: action_id (uniqueness) +
    sequence_index (ordering). Burst detection possible without runtime daemon.
  invariant: "INV-BRIDGE-TEMPORAL-SNAPSHOT semantics preserved."

CARTRIDGE_AND_LEASE:
  relationship: |
    Lease state transitions (DRAFT→ACTIVE→EXPIRED|REVOKED|HALTED)
    are governance actions that produce governance events.
    Bridge notarizes these. AIR attests the agent that triggered them.
    Three layers: action (AIR) → event (Bridge) → state (Lease).
```

---

## 9. NON-GOALS

```yaml
NON_GOALS:
  - No runtime enforcement engine (S64)
  - No agent orchestration or lifecycle management (S65)
  - No mutation pathways (append-only invariant unchanged)
  - No security daemon or anomaly watchdog (S64+)
  - No revocation system (FUTURE — sovereign key management)
  - No key rotation protocol (FUTURE — operational security)
  - No TEE/hardware attestation binding (FUTURE — DGX Confidential Compute)
  - No network-level verification (out of scope — AIR is application-level)
  - No performance benchmarks (S64 implementation will benchmark)
  - No ephemeral log retention policy (S64 operational decision)
  - No velocity rate limiting (S64 runtime enforcement)

WHY_NON_GOALS_MATTER: |
  Proto-AIR is input to S64, not a product. Every field in this spec
  must earn its place by being necessary for the attestation envelope.
  If a field exists to support runtime logic, it belongs in S64.
  If a field exists to support future capabilities, it's in FUTURE_HOOKS.
  The envelope is the deliverable. Nothing else.
```

---

## 10. OPEN QUESTIONS FOR CONTINUED JOIST

```yaml
Q1_CERT_CHAIN_DEPTH:
  question: "How deep should signing_cert_chain be for agent-level attestation?"
  options:
    - single: "Agent key only (simple, fast)"
    - two: "Agent key → Office key (office-level trust root)"
    - three: "Agent key → Office key → Sovereign key (full chain to G)"
  recommendation: "Two-level for S64. Three-level when HSM arrives (Gate 7)."
  joist_round_1_notes: |
    GPT: enforce cert_chain_depth == 2 in S64.
    BOAR: three-level or bust (test with simulated HSM outage).
    CTO: two-level is correct for S64 scope. Sovereign root requires
    HSM infrastructure that doesn't exist yet. Don't spec what you can't build.

Q2_LLM_CONTEXT_GRANULARITY:
  question: "Is prompt_hash sufficient or do we need prompt content fingerprint?"
  recommendation: "SHA-256 hash is sufficient for Proto. Revisit if Dream Cycle needs more."
  joist_round_1_notes: |
    BOAR: force content fingerprint + differential privacy.
    CTO: Hash is minimal and non-leaking. Content fingerprint is heavier
    and introduces privacy concerns. SHA-256 collision risk is negligible.
    Revisit only if Dream Cycle produces evidence that hash is insufficient.

Q3_QUERY_SIGNING_THRESHOLD:
  question: "Should QUERY_CROSS_PAIR really be MEDIUM_IMPACT (signed)?"
  recommendation: "Signed but with batched verification (S64 benchmarks)."
  joist_round_1_notes: |
    BOAR: sign all, let verifier batch. Benchmark 21ms path.
    CTO: MEDIUM_IMPACT is defensible. Cross-pair reveals intent.
    Performance concern is real but belongs in S64 implementation,
    not Proto schema. batch_signature_verification in FUTURE_HOOKS.

Q4_EPHEMERAL_BOUNDARY:
  question: "Where exactly does ephemeral thinking end and structural commitment begin?"
  answer: "DEC-FORMAL-HANDOFF: commit() is the bright line."
  joist_round_1_notes: |
    GPT: single envelope at commit() — no multi-envelope cascade. Correct.
    BOAR: test with injected Auditor hallucination. Valid chaos vector for S64.
    OWL: thought_log_hash addresses the forensic gap without cascading envelopes.
    CTO: Pipeline steps remain internal to the committing agent's envelope.
    The Bundler signs for the pipeline. If the pipeline hallucinates,
    thought_log_hash provides the forensic breadcrumb. Dream Cycle mines it.
```

---

## 11. DELTA LOG

```yaml
- date: 2026-03-01
  author: CTO (Opus 4.6) — synthesized from GPT + OWL + BOAR pre-flight
  change: |
    v0.1 created. Attestation envelope schema with 5 sections:
    agent_identity, build_provenance, llm_context, action, signature_bundle.
    Bridge alignment clause (DEC-BRIDGE-BEFORE-AIR enforced).
    Action taxonomy (HIGH/MEDIUM/LOW impact classification).
    Trust surface definition (signs/does-not-sign boundary).
    Anomaly classification enum (informational, not enforcement).
    OWL LLM metadata provocation accepted into envelope.
    OWL proof-of-computation and halt trigger deferred to S64/S64+.
    4 open questions staged for Joist Pattern.

- date: 2026-03-01
  author: CTO (Opus 4.6) — Joist Pattern Round 1 synthesis
  change: |
    v0.2. Two rounds of advisor input (pre-flight + pressure test).
    +2 fields: thought_log_hash (forensic breadcrumb, non-normative),
    sequence_index (monotonic counter, velocity detection enabler).
    +6 invariants: INV-AIR-CONTAINER-CODE, INV-AIR-MERKLE-BEFORE-HASH,
    INV-AIR-ANOMALY-EXCLUDED, INV-AIR-COMMIT-BOUNDARY,
    INV-AIR-NO-EPHEMERAL-RETENTION-REQUIREMENT, INV-AIR-LLM-ATOMIC.
    +1 anomaly enum: HALLUCINATED_PAYLOAD.
    Tightenings: prompt_hash scope, output_bead_refs emptiness rule,
    snapshot_hash applicability by action type, llm_context atomicity.
    Future hooks: velocity_monitoring, batch_signature_verification.
    Rejected: chaos_seed (redundant with UUID v7), prompt_hash relocation
    to identity (wrong abstraction), tag arrays for anomaly (constitutional
    vocabulary > flexibility), INV-NO-KNOWN-HALLUCINATION (elevates
    advisory to enforcement), inline Merkle paths (implementation detail).
    Key positions held: ANOMALY_CLASS stays enum, thought_log_hash is
    breadcrumb-only with no retention mandate, prompt_hash stays in
    llm_context (agent identity ≠ instructions received).
```

---

*The envelope is the deliverable. The daemon comes later.*
*Schema earns its fields. Runtime earns its sprint.*

*OINK OINK.* 🐗🔥
