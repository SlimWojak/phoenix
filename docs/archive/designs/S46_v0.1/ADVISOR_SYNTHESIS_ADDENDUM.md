# ADVISOR SYNTHESIS ADDENDUM — S46 CANONICAL MERGE

```yaml
document: ADVISOR_SYNTHESIS_ADDENDUM
version: 1.0
date: 2026-01-31
purpose: Opus merge into CARTRIDGE_AND_LEASE_DESIGN_v1.0_CANONICAL
sources: [GPT_ARCHITECT, GROK_CHAOS, GEMINI_PANEL]
synthesized_by: CTO_CLAUDE
```

---

## MERGE INSTRUCTIONS FOR OPUS

Weave these amendments into the canonical document. 
Preserve existing structure; ADD these elements at appropriate locations.
Flag any conflicts for CTO review.

---

## 1. SCHEMA AMENDMENTS

### 1.1 Cartridge Manifest Additions

```yaml
# ADD to identity section:
identity:
  methodology_hash:
    type: string
    description: "SHA256(normalized_manifest_yaml)"
    normalization_rule: |
      1. Sort all keys alphabetically
      2. Remove comments and whitespace
      3. UTF-8 encode
      4. SHA256 hash
    # GPT: Explicit normalization prevents ambiguity

# ADD to scope section:
scope:
  session_windows:
    # ADD invariant note:
    invariant: INV-NO-SESSION-OVERLAP
    description: "Windows cannot overlap unless explicitly declared"
    # GPT: Prevents ambiguous state during transitions

# ADD new field to cso_integration:
cso_integration:
  primitive_set:
    type: array[enum]
    values: [FVG, SWEEP, RE_ACCEPTANCE, MSS, PD_ARRAY, DISPLACEMENT, KZ_TIMING]
    description: "Declared primitives for guard dog verification"
    # GEMINI: Allows verification strategy does what it claims

# ADD new field to research_hooks:
research_hooks:
  calibration_threshold_pct:
    type: float
    default: 5.0
    description: "Drift % threshold for WARN (2x for BLOCK)"
    # GROK: Make configurable, not assumed

# ADD new field to scope:
scope:
  regime_affinity:
    type: enum
    values: [VOLATILITY_HIGH, VOLATILITY_LOW, TRENDING, RANGING, ANY]
    default: ANY
    description: "Expected market regime for valid calibration"
    # GEMINI: Prevents calibration during wrong regime
```

### 1.2 Lease Schema Additions

```yaml
# ADD to bounds section:
bounds:
  allowed_pairs_mode:
    type: enum
    values: [ALL, SUBSET]
    description: "Explicit mode instead of magic 'ALL' string"
    # GPT: Cleaner validation logic
    
  allowed_sessions_mode:
    type: enum
    values: [ALL, SUBSET]

# ADD new field to bounds:
bounds:
  priority_weight:
    type: float
    min: 0.0
    max: 1.0
    default: 1.0
    description: "Margin contention priority (higher = preferred)"
    # GEMINI: Resolves multi-strategy margin conflicts

# ADD to halt_integration:
halt_integration:
  governance_buffer_seconds:
    type: integer
    default: 60
    description: "Software halt N seconds BEFORE legal expiry"
    # GEMINI: Prevents zombie lease race condition
    
  expiry_behavior:
    type: enum
    values: [MARKET_CLOSE, FREEZE_AND_WAIT]
    default: MARKET_CLOSE
    description: "What happens to open positions on expiry"
    # GEMINI: WarBoar philosophy = protect capital floor

# ADD to governance:
governance:
  state_lock_hash:
    type: string
    description: "Hash of prior state for renew/revoke race protection"
    # GROK: Prevents concurrent operation collision
```

---

## 2. NEW INVARIANTS

```yaml
# ADD to constitutional section:

INV-NO-SESSION-OVERLAP:
  rule: "Session windows cannot overlap unless explicitly declared"
  enforcement: Schema validation on insertion
  source: GPT

INV-LEASE-CEILING:
  rule: "Lease defines HARD CEILING; Cartridge defines LOWER FLOOR"
  enforcement: |
    lease.max_drawdown_pct >= cartridge.risk_defaults.max_drawdown_pct
    (Lease can only be STRICTER, not looser)
  source: GEMINI
  rationale: "Prevents autonomy leakage"

INV-BEAD-COMPLETENESS:
  rule: "Calibration bead MUST link to lease_id immutably"
  enforcement: calibration_bead.lease_id is required field
  source: GEMINI
  rationale: "Prevents spoofed calibration from previous lease"

INV-EXPIRY-BUFFER:
  rule: "Software halt governance_buffer_seconds BEFORE legal expiry"
  enforcement: Pre-trade check includes buffer
  default: 60 seconds
  source: GEMINI
  rationale: "Prevents zombie lease race condition"

INV-STATE-LOCK:
  rule: "Renew/revoke operations must hash-check prior state"
  enforcement: state_lock_hash verified before state transition
  source: GROK
  rationale: "Prevents concurrent operation collision"
```

---

## 3. STATE MACHINE AMENDMENTS

```yaml
# AMEND HALTED state:
HALTED:
  description: "Auto-halted due to bounds breach"
  transitions:
    - REVOKED (requires human review)
  # CANNOT transition back to ACTIVE
  # GPT: Must REVOKE then create NEW LEASE
  recovery_path: |
    1. Human reviews halt trigger
    2. REVOKE current lease
    3. Create NEW lease if desired
    4. No resurrection of halted lease

# ADD to all state transitions:
state_transitions:
  guard: |
    All transitions require state_lock_hash verification.
    Concurrent operations that fail hash check = REJECT.
  # GROK: Prevents race conditions
```

---

## 4. INSERTION PROTOCOL AMENDMENTS

```yaml
# ADD new step after step_2_lint:
step_2b_dependency_check:
  action: "Verify all imports/dependencies are Phoenix-approved"
  guard: "Environment hash validation"
  on_fail: "REJECT — unapproved dependency"
  # GEMINI: Prevents "missing DLL" failure
  # GROK: Banteg zero-jank dep check

# AMEND step_7_calibration_smoke:
step_7_calibration_smoke:
  drift_pct_definition: |
    drift_pct = |actual_signals - expected_signals| / expected_signals
    where signals = count of gate activations during shadow session
  # GPT: Formal definition prevents later disagreement
  
  regime_check: |
    If current regime != cartridge.regime_affinity:
      calibration_status = DEFERRED
      reason = "Regime mismatch — recalibrate when affinity matches"
  # GEMINI: Prevents irrelevant calibration
```

---

## 5. NEW BEAD TYPES

```yaml
# ADD these beads:

STATE_LOCK_BEAD:
  trigger: Any state transition attempt
  fields:
    - lease_id
    - prior_state
    - prior_state_hash
    - requested_transition
    - transition_result: [SUCCESS, REJECTED_HASH_MISMATCH]
  # GROK: Yegge-immutable timestamp for race protection

STRATEGY_DEPRECATION_BEAD:
  trigger: Cartridge removed for non-technical reasons
  fields:
    - cartridge_ref
    - deprecated_by
    - reason: [BEHAVIORAL_MISMATCH, TRUST_LOSS, METHODOLOGY_DRIFT]
    - final_performance_summary
  # GPT: Distinct from removal for technical reasons

MARGIN_CONTENTION_BEAD:
  trigger: Multiple strategies compete for margin
  fields:
    - competing_leases: [lease_id_1, lease_id_2]
    - winner: lease_id
    - resolution: priority_weight comparison
    - loser_action: [DEFERRED, SKIPPED]
  # GEMINI: Audit trail for multi-strategy margin decisions
```

---

## 6. CEREMONY AMENDMENTS

```yaml
# ADD to ceremony flow:
ceremony:
  olya_checklist:
    description: "Physical checklist Olya must complete"
    items:
      - checkbox: "I have reviewed every HALT alert this period"
      - checkbox: "The drift % matches expected calibration"
      - checkbox: "The strategy stayed within its declared lane"
    enforcement: |
      All checkboxes must be TRUE for attestation.
      UI/CLI enforces this before ATTESTATION_BEAD creation.
    # GEMINI: Human accountability mechanism

  sovereign_override:
    description: "G's Red Button"
    capability: |
      Force-eject cartridge without killing Phoenix process.
      Creates EMERGENCY_EJECT_BEAD.
      Does not require ceremony.
    guard: "Sovereign-only capability (G)"
    # GEMINI: Operational safety valve
```

---

## 7. GUARDS — ADDITIONAL FAILURES

```yaml
# ADD to failure guards:

F11_CONCURRENT_CEREMONY_TRADE:
  failure: "Lease renew ceremony concurrent with trade execution"
  likelihood: LOW
  guard: STATE_LOCK_BEAD with hash verification
  source: GROK

F12_DST_EXPIRY_SKEW:
  failure: "Expiry timestamp DST skew (NY vs UTC) causes premature perish"
  likelihood: MEDIUM
  guard: All expiry times in UTC; governance_buffer provides safety margin
  source: GROK

F13_MULTI_OPERATOR_COLLISION:
  failure: "Olya + G both attempt revoke simultaneously"
  likelihood: LOW
  guard: STATE_LOCK_BEAD rejects second operation
  source: GROK

F14_BEAD_QUERY_OVERLOAD:
  failure: "Willison palace query on long lease forensics = archaeology death"
  likelihood: LOW
  guard: Query pagination; summary views for common patterns
  source: GROK

F15_MANIFEST_EDIT_WITHOUT_VERSION:
  failure: "Strategy manifest edited in-place without version bump"
  likelihood: MEDIUM
  guard: Hash mismatch blocks lease activation
  source: GPT

F16_CLOCK_DRIFT:
  failure: "System clock drift allows trade to leak through expiry"
  likelihood: LOW
  guard: governance_buffer + server-side time only (no local clock trust)
  source: GPT + GEMINI
```

---

## 8. OPEN QUESTIONS — RESOLVED

```yaml
Q1_MULTI_CARTRIDGE:
  resolution: A (Single active cartridge)
  consensus: GPT said B, GROK said A, GEMINI implied multi with priority
  final_decision: |
    v1.0 = Single active cartridge (GROK rationale: YOLO simple)
    v1.1+ = Multi-cart with priority_weight if proven needed
  rationale: "Start simple; complexity earned by operator friction"

Q2_LEASE_REFERENCES_LATEST:
  resolution: A (STRICT — new lease for ANY version change)
  consensus: UNANIMOUS
  rationale: "Operational friction is intentional sovereignty protection"

Q3_BOUNDS_LOGIC:
  resolution: OR (any bound breach = halt)
  consensus: UNANIMOUS
  rationale: "AND logic invites tail-risk bleed"

Q4_PARTIAL_SESSION:
  resolution: A (Session-level only)
  consensus: UNANIMOUS
  rationale: "Push precision into cartridge; keep lease simple"

Q5_CALIBRATION_THRESHOLD:
  resolution: 5% WARN / 10% BLOCK (configurable in cartridge)
  consensus: GPT + GROK aligned
  implementation: calibration_threshold_pct field in manifest

Q6_EXTENSION_TRACKING:
  resolution: Per-direction tracking (high/low independent)
  consensus: UNANIMOUS
  fields:
    - sweep_extension_high_pips
    - sweep_extension_low_pips
  rationale: "Over 20 pips invalidates THAT side only"
```

---

## 9. SUMMARY FOR OPUS

```yaml
merge_priority:
  CRITICAL:
    - INV-LEASE-CEILING (Gemini constitutional fix)
    - INV-STATE-LOCK (Grok race condition)
    - governance_buffer_seconds (zombie lease prevention)
    - expiry_behavior enum (MARKET_CLOSE default)
    
  HIGH:
    - calibration_threshold_pct in manifest
    - primitive_set enum
    - STATE_LOCK_BEAD
    - Olya checklist in ceremony
    
  MEDIUM:
    - allowed_pairs_mode / allowed_sessions_mode enums
    - priority_weight for margin contention
    - regime_affinity field
    - Additional failure guards F11-F16
    
  LOW:
    - STRATEGY_DEPRECATION_BEAD
    - MARGIN_CONTENTION_BEAD
    - sovereign_override red button

document_version_after_merge: v1.0_CANONICAL
status: READY_FOR_OPUS_MERGE
```

---

**OINK OINK — SYNTHESIS COMPLETE 🐗🔥**
