# CARTRIDGE AND LEASE DESIGN v0.1 (CANONICAL)

```yaml
document: CARTRIDGE_AND_LEASE_DESIGN
version: 0.1
date: 2026-01-31
status: DRAFT_FOR_ADVISOR_REVIEW
authors: CTO_CLAUDE + G
specimen: Olya's Asia Range Scalp Strategy
synthesized_from: Two draft versions (compaction recovery)
```

---

## PREAMBLE: CONTEXT FOR REVIEWERS

```yaml
current_state:
  S44_LIVE_VALIDATION: SOAK_RUNNING
    - Real IBKR connection: DUO768070 (paper)
    - Soak started: 2026-01-31T01:47:34 UTC
    - Soak ends: 2026-02-02T01:47:34 UTC
    - Status: 48h boring test in progress
    
  S46_DESIGN: PULLED_FORWARD (parallel)
    - Rationale: Soak is time-bound wait, design work is safe
    - No code changes: Soak remains valid
    - Scope expanded: CARTRIDGE + LEASE together
    
  test_specimen:
    - Olya's Asia Range Scalp Strategy (real, not abstract)
    - Simple but ICT-flavored (FVG, sweep detection, re-acceptance)
    - Perfect for proving primitive
    - Other strategies more complex; this shapes the slot

why_together:
  - Lease governs "THIS strategy, THESE bounds, THIS period"
  - Without cartridge manifest, "THIS strategy" is undefined
  - Cartridge = WHAT | Lease = GOVERNANCE WRAPPER
  - Two schemas, one worked example, concrete beats abstract

request_to_advisors:
  format: TIGHT_DENSE_M2M
  scope:
    - Schema completeness / gaps
    - Failure modes we missed
    - Industry patterns to steal
    - Constitutional violations
  please_no:
    - Prose essays
    - Restating the doc back
```

---

## 1. CORE CONCEPTS

### 1.1 The N64 Cartridge Metaphor

```yaml
metaphor:
  cartridge: "The game" — complete strategy definition
  console: "Phoenix harness" — CSO, gates, execution
  slot: "Insertion protocol" — how cartridge loads
  lease: "Parental controls" — governance wrapper

design_goal: |
  Cartridge slots in with zero jiggle.
  Instant native feel. No restart required.
  Lease governs without micromanaging.
```

### 1.2 The Problem Solved

```yaml
without_cartridge:
  - "What IS a strategy?" = undefined
  - CSO can't evaluate what it can't identify
  - No slot-in architecture
  - Every strategy = custom code

without_lease:
  - "Can I run this?" = manual approval per trade
  - No bounded autonomy
  - No governance ceremony
  - No expiry / revocation model

with_both:
  - Strategy = declarative manifest (the cartridge)
  - Governance = declarative bounds (the lease)
  - N64 slot-in: strategy clicks into harness
  - Weekly ceremony: human reviews, renews or revokes
  - Sovereignty preserved: human always in control
```

### 1.3 Separation of Concerns

```yaml
cartridge_defines:
  WHAT: Strategy identity, methodology, parameters
  HOW: Entry conditions, exit rules, position management
  WHERE: Pairs, sessions, timeframes
  
lease_defines:
  BOUNDS: Max drawdown, streak limits, position caps
  DURATION: Start, expiry, perish-by-default
  GOVERNANCE: Weekly ceremony, attestation requirement
  
neither_defines:
  - Execution mechanics (Phoenix core)
  - Market data (River)
  - Risk engine fundamentals (unchanged)
```

### 1.4 Design Principles

```yaml
cartridge_principles:
  P1_DECLARATIVE: "Strategy is data, not code"
  P2_DELTA_NOT_REPLACE: "Modifies drawers, doesn't overwrite them"
  P3_INVARIANTS_REQUIRED: "Must declare constitutional compliance"
  P4_TIMEZONE_EXPLICIT: "All times include TZ + UTC offset"
  P5_SLOT_OR_PERISH: "Conflicts = rejection, not silent merge"

lease_principles:
  P1_PERISH_BY_DEFAULT: "No auto-renew ever"
  P2_HALT_OVERRIDES: "Halt wins over lease (<50ms)"
  P3_BOUNDS_ONLY_TIGHTEN: "Can constrain, never loosen"
  P4_CEREMONY_REQUIRED: "Weekly review = attestation bead"
  P5_FORENSIC_TRAIL: "All lease actions = beads"

combined_principle:
  "Cartridge defines WHAT. Lease governs WHEN/HOW MUCH."
```

### 1.5 Constitutional Anchors

```yaml
invariants_governing_design:
  INV-NO-UNSOLICITED: "System never proposes"
  INV-HALT-OVERRIDES-LEASE: "Halt always wins (<50ms)"
  INV-NO-CORE-REWRITES-POST-S44: "No architecture changes after soak"
  INV-HARNESS-1: "Gate status only, never grades"
  
lease_invariants:
  PERISH_BY_DEFAULT: "No auto-renew, ever"
  BOUNDS_ONLY_TIGHTEN: "Lease constrains, cannot loosen strategy"
  WEEKLY_CEREMONY_REQUIRED: "Human attestation or expire"
  HALT_IS_ABSOLUTE: "Halt overrides lease in <50ms"
```

---

## 2. CARTRIDGE MANIFEST SCHEMA

### 2.1 Schema Definition

```yaml
# schemas/strategy_manifest.schema.yaml

schema_version: "1.0"
description: "Strategy cartridge manifest — the N64 game label"

required_fields:
  - identity
  - scope
  - risk_defaults
  - cso_integration
  - constitutional

# ========================================
# IDENTITY
# ========================================
identity:
  description: "What is this strategy?"
  properties:
    name:
      type: string
      pattern: "^[A-Z][A-Z0-9_]+$"  # UPPER_SNAKE_CASE
      example: "ASIA_RANGE_SCALP"
    version:
      type: string
      pattern: "^\\d+\\.\\d+\\.\\d+$"  # semver
      example: "1.0.0"
    author:
      type: string
      example: "Olya"
    description:
      type: string
      max_length: 500
    created_at:
      type: datetime
      format: ISO8601
    methodology_hash:
      type: string
      description: "SHA256 of strategy logic for integrity"

# ========================================
# SCOPE
# ========================================
scope:
  description: "Where and when does this strategy operate?"
  properties:
    pairs:
      type: array[string]
      min_items: 1
      example: ["EURUSD"]
      
    session_windows:
      type: array
      items:
        type: object
        required: [name, start, end, timezone, utc_offset_winter, utc_offset_summer]
        properties:
          name:
            type: string
            example: "asia_definition"
          start:
            type: string
            pattern: "^\\d{2}:\\d{2}$"  # HH:MM
            example: "19:00"
          end:
            type: string
            pattern: "^\\d{2}:\\d{2}$"
            example: "00:00"
          timezone:
            type: string
            example: "America/New_York"
          utc_offset_winter:
            type: string
            description: "Explicit UTC offset for DST safety"
            example: "-05:00"
          utc_offset_summer:
            type: string
            example: "-04:00"

# ========================================
# RISK DEFAULTS
# ========================================
risk_defaults:
  description: "Default risk parameters (lease can tighten)"
  properties:
    per_trade_pct:
      type: float
      min: 0.1
      max: 5.0
      example: 1.0
    min_rr:
      type: float
      min: 1.0
      example: 1.5
    max_trades_per_session:
      type: integer
      min: 1
      example: 1
    max_daily_trades:
      type: integer
      optional: true
      example: 3

# ========================================
# CSO INTEGRATION
# ========================================
cso_integration:
  description: "How strategy modifies CSO evaluation"
  properties:
    drawer_deltas:
      description: "Modifications to CSO drawers (MERGE, not replace)"
      properties:
        foundation:
          type: object
          optional: true
          description: "Market structure definitions"
        context:
          type: object
          optional: true
          description: "HTF context requirements"
        conditions:
          type: object
          optional: true
          description: "Setup conditions / gates"
        entry:
          type: object
          optional: true
          description: "Entry trigger rules"
        management:
          type: object
          optional: true
          description: "SL/TP/position management"
          
    gate_requirements:
      type: array[string]
      description: "Gates that must pass for valid setup"
      example: ["GATE_SWEEP_DETECTED", "GATE_FVG_VALID"]

# ========================================
# RESEARCH HOOKS
# ========================================
research_hooks:
  description: "Hunt/CFP integration (optional)"
  properties:
    hunt_grid_enabled:
      type: boolean
      default: true
    cfp_lens_presets:
      type: array[string]
      optional: true
      description: "Pre-defined CFP queries for this strategy"
      example: ["P&L when extension_pips > 10"]
    backtest_min_trades:
      type: integer
      default: 30

# ========================================
# NARRATOR OVERRIDES
# ========================================
narrator_overrides:
  description: "Custom narrator templates (optional)"
  properties:
    templates:
      type: object
      optional: true
      additionalProperties: string
      example:
        sweep_detected: "Asia {{direction}} swept {{extension_pips}} pips"

# ========================================
# CONSTITUTIONAL
# ========================================
constitutional:
  description: "Required invariants (non-negotiable)"
  properties:
    invariants_required:
      type: array[string]
      pattern: "^INV-[A-Z0-9-]+$"
      min_items: 1
      description: "Invariants this strategy must comply with"
      example: ["INV-NO-UNSOLICITED", "INV-HALT-1"]
    forbidden_patterns:
      type: array[string]
      description: "Patterns that would violate constitution"
      example: ["score", "grade", "recommend", "edge concentrates"]
    guard_dog_scan:
      type: boolean
      default: true
```

### 2.2 Key Design Decisions

```yaml
decisions:
  D1_DELTA_NOT_REPLACE:
    rule: "drawer_deltas merge INTO existing drawers"
    rationale: "Preserves base CSO; strategy adds, doesn't destroy"
    guard: "Merge tool rejects conflicts"
    
  D2_EXPLICIT_TIMEZONE:
    rule: "tz name + winter offset + summer offset required"
    rationale: "DST transitions cause silent bugs"
    guard: "Schema rejects ambiguous times"
    
  D3_INVARIANTS_MANDATORY:
    rule: "constitutional.invariants_required is REQUIRED field"
    rationale: "No strategy can bypass constitution"
    minimum: [INV-NO-UNSOLICITED, INV-HALT-1]
    
  D4_SEMVER_REQUIRED:
    rule: "Version must be semver (X.Y.Z)"
    rationale: "Lease references exact version; upgrades need new lease"
    
  D5_METHODOLOGY_HASH:
    rule: "SHA256 hash of strategy logic stored in manifest"
    rationale: "Integrity verification; lease binds to exact manifest"
```

---

## 3. LEASE SCHEMA

### 3.1 Schema Definition

```yaml
# schemas/lease.schema.yaml

schema_version: "1.0"
description: "Governance wrapper — bounds, duration, ceremony"

required_fields:
  - identity
  - subject
  - duration
  - bounds
  - governance
  - halt_integration
  - status

# ========================================
# IDENTITY
# ========================================
identity:
  description: "Lease identification"
  properties:
    lease_id:
      type: string
      format: uuid
      example: "lease_2026_01_31_001"
    created_at:
      type: datetime
      format: ISO8601
    created_by:
      type: string
      description: "Human who created the lease"
      example: "G"

# ========================================
# SUBJECT
# ========================================
subject:
  description: "What strategy is being leased?"
  properties:
    strategy_ref:
      type: string
      pattern: "^[A-Z][A-Z0-9_]+_v\\d+\\.\\d+\\.\\d+$"
      example: "ASIA_RANGE_SCALP_v1.0.0"
    strategy_hash:
      type: string
      description: "SHA256 of manifest at lease creation"

# ========================================
# DURATION
# ========================================
duration:
  description: "When is this lease valid?"
  properties:
    starts_at:
      type: datetime
      format: ISO8601
    expires_at:
      type: datetime
      format: ISO8601
    duration_days:
      type: integer
      min: 1
      max: 30
      default: 7
    renewal_type:
      type: enum
      values: [PERISH]
      immutable: true
      description: "Always PERISH — no auto-renew"

# ========================================
# BOUNDS
# ========================================
bounds:
  description: "Risk constraints (can only tighten strategy defaults)"
  properties:
    max_drawdown_pct:
      type: float
      example: 3.0
      description: "Auto-halt if exceeded"
    max_consecutive_losses:
      type: integer
      example: 3
      description: "Auto-halt if exceeded"
    allowed_pairs:
      type: array[string] | "ALL"
      description: "Subset of strategy pairs"
    allowed_sessions:
      type: array[string] | "ALL"
      description: "Subset of strategy sessions"
    position_size_cap:
      type: float
      optional: true
      rule: "Must be <= strategy.per_trade_pct"
    daily_loss_limit_pct:
      type: float
      optional: true

# ========================================
# GOVERNANCE
# ========================================
governance:
  description: "Ceremony and attestation requirements"
  properties:
    weekly_review_required:
      type: boolean
      default: true
      immutable: true
    attestation_required:
      type: boolean
      default: true
    last_review_at:
      type: datetime
      optional: true
    last_attestation_bead:
      type: string
      optional: true
    next_review_due:
      type: datetime
      description: "Calculated from last attestation"
    reviewer:
      type: string
      example: "Olya + G"

# ========================================
# HALT INTEGRATION
# ========================================
halt_integration:
  description: "How lease interacts with halt system"
  properties:
    auto_halt_on_drawdown:
      type: boolean
      default: true
    auto_halt_on_streak:
      type: boolean
      default: true
    halt_overrides_lease:
      type: boolean
      const: true
      description: "INV-HALT-OVERRIDES-LEASE"
    halt_latency_ms:
      type: integer
      max: 50

# ========================================
# STATUS
# ========================================
status:
  description: "Current lease state"
  properties:
    current:
      type: enum
      values: [DRAFT, ACTIVE, EXPIRED, REVOKED, HALTED]
    activated_at:
      type: datetime
      optional: true
    revoked_at:
      type: datetime
      optional: true
    revocation_reason:
      type: string
      optional: true
    halted_at:
      type: datetime
      optional: true
    halt_trigger:
      type: string
      optional: true
```

### 3.2 Key Design Decisions

```yaml
decisions:
  D1_PERISH_BY_DEFAULT:
    rule: "renewal_type ONLY allows PERISH"
    rationale: "No auto-renew prevents forgotten autonomy"
    enforcement: "Enum schema, no other values"
    
  D2_HALT_ALWAYS_WINS:
    rule: "halt_overrides_lease is CONST true"
    rationale: "INV-HALT-OVERRIDES-LEASE, <50ms"
    enforcement: "Schema const, not configurable"
    
  D3_BOUNDS_ONLY_TIGHTEN:
    rule: "Lease bounds must be stricter than strategy"
    rationale: "Cannot use lease to bypass strategy limits"
    example: |
      strategy.per_trade_pct = 1.0
      lease.position_size_cap = 0.5  ✓ (tighter)
      lease.position_size_cap = 2.0  ✗ (looser)
      
  D4_STRATEGY_HASH:
    rule: "Lease captures SHA256 of manifest at creation"
    rationale: "Manifest evolves; lease bound to EXACT version"
    enforcement: "Hash mismatch → lease invalid"
    
  D5_MAX_30_DAYS:
    rule: "Maximum lease duration = 30 days"
    rationale: "Forces regular governance review"
    typical: "7 days (weekly ceremony)"
    
  D6_NEXT_REVIEW_DUE:
    rule: "Calculated field tracking when review is required"
    rationale: "Enables execution blocking when overdue"
    enforcement: "Overdue attestation → execution blocked"
```

---

## 4. LEASE STATE MACHINE

```yaml
states: [DRAFT, ACTIVE, EXPIRED, REVOKED, HALTED]

transitions:
  DRAFT → ACTIVE:
    trigger: "Activation ceremony"
    requires: [cartridge_active, attestation_bead]
    creates: LEASE_ACTIVATION_BEAD
    
  ACTIVE → EXPIRED:
    trigger: "expires_at reached"
    automatic: true
    creates: LEASE_EXPIRY_BEAD
    behavior: "No new trades; exits allowed"
    
  ACTIVE → REVOKED:
    trigger: "Human revocation"
    creates: LEASE_REVOCATION_BEAD
    behavior: "No new trades; exits allowed"
    
  ACTIVE → HALTED:
    trigger: "Bounds exceeded OR global halt"
    automatic: true
    latency: "<50ms"
    creates: LEASE_HALT_BEAD
    behavior: "All activity stopped"

terminal_states: [EXPIRED, REVOKED]
  recovery: "Requires new lease creation"
  
halted_state:
  recovery: "Human review, then REVOKE or create new lease"
  
invariant: |
  Only ACTIVE state allows strategy execution.
  All other states = blocked.
```

---

## 5. INSERTION PROTOCOL

```yaml
# How a cartridge "clicks" into the harness

insertion_steps:

  step_1_validation:
    action: "Validate manifest against schema"
    guard: "schema_validator.validate(manifest)"
    on_fail: "REJECT with specific errors"
    
  step_2_constitutional_check:
    action: "Verify invariants_required is non-empty"
    guard: "len(manifest.constitutional.invariants_required) > 0"
    required: [INV-NO-UNSOLICITED, INV-HALT-1]
    on_fail: "REJECT — missing required invariants"
    
  step_3_forbidden_patterns:
    action: "Scan narrator templates for forbidden patterns"
    guard: "guard_dog.scan(manifest.narrator_overrides)"
    forbidden:
      - /\b(best|worst|strongest|weakest)\b/i
      - /\b(recommend|should|must trade)\b/i
      - /\b(grade|score|rating)\b/i
      - /\bedge concentrates\b/i
    on_fail: "REJECT with pattern matches"
    
  step_4_drawer_merge:
    action: "Check drawer_deltas for conflicts"
    guard: "merger.merge(base_drawers, manifest.drawer_deltas)"
    conflict_resolution: PERISH (no silent merge)
    on_conflict: "REJECT — drawer conflict (explicit)"
    
  step_5_index_update:
    action: "Update index.yaml with new cartridge"
    result: "CSO can now reference cartridge gates"
    
  step_6_guard_dog_final:
    action: "Full guard dog scan on merged drawers"
    guard: "guard_dog.full_scan()"
    on_fail: "ROLLBACK insertion"
    
  step_7_calibration_smoke:
    action: "Auto-shadow 1 session"
    purpose: "Detect drift from expected behavior"
    output: CALIBRATION_BEAD with drift_pct
    threshold: ">5% drift = WARN; >10% = BLOCK"
    
  step_8_ready:
    action: "Cartridge available for lease"
    bead: CARTRIDGE_INSERTION_BEAD with manifest_hash

no_restart_required: true
rollback: "Remove from active/ → index refreshes"

removal_steps:
  - Deactivate any active leases (REVOKE)
  - Remove from index.yaml
  - Archive manifest
  - CARTRIDGE_REMOVAL_BEAD with reason
```

### 5.1 Drawer Merge Algorithm

```yaml
merge_algorithm:
  1: Load base drawer (e.g., conditions.yaml)
  2: Load cartridge delta (drawer_deltas.conditions)
  3: For each key in delta:
     - Key not in base → ADD
     - Key in base, values match → SKIP
     - Key in base, values conflict → CONFLICT
  4: Any CONFLICT → PERISH cartridge
  
conflict_resolution: NONE
  rule: "No silent overwrite"
  human_action: "Modify cartridge or base drawer explicitly"
```

---

## 6. WORKED EXAMPLE: ASIA RANGE SCALP

### 6.1 Cartridge Manifest

```yaml
# cartridges/active/asia_range_scalp.yaml

identity:
  name: ASIA_RANGE_SCALP
  version: "1.0.0"
  author: Olya
  description: |
    Mean-reversion scalp on Asia session range sweeps.
    Requires FVG entry + re-acceptance confirmation.
  created_at: "2026-01-31T00:00:00Z"
  methodology_hash: "sha256:abc123..."

scope:
  pairs: [EURUSD]
  session_windows:
    - name: asia_definition
      start: "19:00"
      end: "00:00"
      timezone: America/New_York
      utc_offset_winter: "-05:00"
      utc_offset_summer: "-04:00"
    - name: sweep_window
      start: "00:00"
      end: "04:00"
      timezone: America/New_York
      utc_offset_winter: "-05:00"
      utc_offset_summer: "-04:00"

risk_defaults:
  per_trade_pct: 1.0
  min_rr: 1.5
  max_trades_per_session: 1
  max_daily_trades: 1

cso_integration:
  drawer_deltas:
    foundation:
      asia_range_method: wick_to_wick
    conditions:
      sweep_required: true
      sweep_extension_min_pips: 1
      sweep_extension_max_pips: 20
      sweep_direction: [high, low]  # track both
    entry:
      fvg_required: true
      fvg_timeframe: 5min
      re_acceptance_required: true
      re_acceptance_candle: 5min_close_inside
    management:
      sl_placement: beyond_sweep_extreme
      sl_buffer_pips: 2
      tp_placement: opposite_asia_extreme
      
  gate_requirements:
    - GATE_ASIA_RANGE_VALID
    - GATE_SWEEP_DETECTED
    - GATE_SWEEP_EXTENSION_VALID
    - GATE_FVG_PRESENT
    - GATE_RE_ACCEPTANCE_CONFIRMED
    - GATE_RR_MINIMUM_MET

research_hooks:
  hunt_grid_enabled: true
  cfp_lens_presets:
    - "P&L when sweep_extension_pips BETWEEN 1 AND 10"
    - "P&L when sweep_extension_pips BETWEEN 11 AND 20"
    - "P&L by sweep_direction"

narrator_overrides:
  templates:
    sweep_detected: |
      Asia {{direction}} swept {{extension_pips}} pips
      Re-acceptance: {{re_acceptance_status}}
      FVG: {{fvg_status}}

constitutional:
  invariants_required:
    - INV-NO-UNSOLICITED
    - INV-ATTR-CAUSAL-BAN
    - INV-HALT-1
    - INV-HARNESS-1
    - INV-NARRATOR-1
  forbidden_patterns:
    - "grade"
    - "score"
    - "recommend"
    - "edge concentrates"
  guard_dog_scan: true
```

### 6.2 Lease Instance

```yaml
# leases/active/asia_range_scalp_2026w05.yaml

identity:
  lease_id: "lease_2026_01_31_asia_001"
  created_at: "2026-01-31T08:00:00Z"
  created_by: G

subject:
  strategy_ref: "ASIA_RANGE_SCALP_v1.0.0"
  strategy_hash: "sha256:abc123..."

duration:
  starts_at: "2026-01-31T00:00:00Z"
  expires_at: "2026-02-07T00:00:00Z"
  duration_days: 7
  renewal_type: PERISH

bounds:
  max_drawdown_pct: 3.0
  max_consecutive_losses: 3
  allowed_pairs: [EURUSD]
  allowed_sessions: [asia_definition, sweep_window]
  position_size_cap: 1.0
  daily_loss_limit_pct: 2.0

governance:
  weekly_review_required: true
  attestation_required: true
  last_review_at: "2026-01-31T08:00:00Z"
  next_review_due: "2026-02-07T08:00:00Z"
  reviewer: "Olya + G"

halt_integration:
  auto_halt_on_drawdown: true
  auto_halt_on_streak: true
  halt_overrides_lease: true
  halt_latency_ms: 50

status:
  current: ACTIVE
  activated_at: "2026-01-31T08:00:00Z"
```

### 6.3 Weekly Ceremony Flow

```yaml
ceremony: WEEKLY_LEASE_REVIEW
participants: [G, Olya]
cadence: "Before lease expiry (weekly)"

steps:
  1_forensic_review:
    source: Bead queries
    examine:
      - Total trades
      - Win/loss record
      - P&L
      - Max drawdown reached
      - Gates passed/failed distribution
      
  2_olya_autopsy:
    tool: TradingView (external)
    purpose: "Validate every trade against methodology"
    findings: "Would I have taken these trades?"
    
  3_drift_check:
    source: CALIBRATION_BEAD
    threshold: ">5% = concern; >10% = block renewal"
    
  4_bounds_review:
    question: "Are bounds still appropriate?"
    options: [keep, tighten, loosen_if_warranted]
    
  5_renewal_decision:
    options:
      RENEW: "Create new lease (fresh start)"
      MODIFY: "New lease with different bounds"
      REVOKE: "Let expire, no renewal"

outputs:
  - ATTESTATION_BEAD (required)
  - New lease (if renewed)
  - CEREMONY_BEAD (summary)

human_discipline_note: |
  This ceremony is HUMAN-ENFORCED.
  Phoenix reminds; cannot force.
  G's 20+ years operating rhythm = real enforcement.
  
  The governance works because G + Olya
  have the discipline to execute it.
```

---

## 7. GUARDS AND FAILURE MODES

### 7.1 Pre-Slot Linter

```yaml
checks:
  schema_valid:
    test: "Validate against strategy_manifest.schema.yaml"
    on_fail: REJECT
    
  invariants_present:
    test: "invariants_required not empty"
    required: [INV-NO-UNSOLICITED, INV-HALT-1]
    on_fail: REJECT
    
  narrator_clean:
    test: "Regex scan narrator templates"
    forbidden:
      - /\b(best|worst|strongest|weakest)\b/i
      - /\b(recommend|should|must trade)\b/i
      - /\b(grade|score|rating)\b/i
      - /\bedge concentrates\b/i
    on_fail: REJECT
    
  timezone_complete:
    test: "All session_windows have tz + both UTC offsets"
    on_fail: REJECT
```

### 7.2 Dumb Failures → Guards

| # | Failure Mode | Likelihood | Guard |
|---|--------------|------------|-------|
| F1 | Invariants forgotten → heresy slips | MEDIUM | Pre-slot linter REJECTS |
| F2 | Drawer key conflicts → CSO confused | MEDIUM | Merge tool perishes cart |
| F3 | Context bloat (complex cart) | LOW | Index caching, delta-only |
| F4 | No drift detection → slow bleed | HIGH | Auto-shadow → CALIBRATION_BEAD |
| F5 | DST flip → wrong session | MEDIUM | Explicit UTC offsets required |
| F6 | Lease auto-renews | LOW | Schema: PERISH-only enum |
| F7 | Halt races with lease | LOW | HALT_OVERRIDES, <50ms |
| F8 | Bounds creep upward | MEDIUM | Runtime validation (only tighten) |
| F9 | Strategy hash mismatch | MEDIUM | Hash verification on load |
| F10 | Weekly review skipped | MEDIUM | next_review_due blocks execution |

---

## 8. BEAD TYPES (NEW)

```yaml
new_beads:
  CARTRIDGE_INSERTION_BEAD:
    trigger: Cartridge slotted
    fields: [cartridge_ref, hash, linter_result]
    
  CARTRIDGE_REMOVAL_BEAD:
    trigger: Cartridge removed
    fields: [cartridge_ref, removed_by, reason]
    
  CALIBRATION_BEAD:
    trigger: Auto-shadow complete
    fields: [cartridge_ref, drift_pct, verdict]
    
  LEASE_ACTIVATION_BEAD:
    trigger: Lease → ACTIVE
    fields: [lease_id, strategy_ref, bounds_snapshot]
    
  LEASE_EXPIRY_BEAD:
    trigger: Lease expires (automatic)
    fields: [lease_id, final_stats]
    
  LEASE_REVOCATION_BEAD:
    trigger: Human revokes
    fields: [lease_id, revoked_by, reason]
    
  LEASE_HALT_BEAD:
    trigger: Auto-halt from bounds
    fields: [lease_id, trigger, bound_exceeded, value]
    
  ATTESTATION_BEAD:
    trigger: Weekly ceremony
    fields: [lease_id, decision, new_lease_id]
    
  CEREMONY_BEAD:
    trigger: Ceremony complete
    fields: [participants, summary, decisions]
```

---

## 9. OPEN QUESTIONS FOR ADVISORS

```yaml
Q1_MULTI_CARTRIDGE:
  question: "Can multiple cartridges be active simultaneously?"
  context: "Olya runs ASIA_RANGE + FVG_LONDON together"
  options:
    A: One active at a time (simple)
    B: Multiple if no drawer conflicts (medium)
    C: Multiple with conflict detection (complex)
  current: "Undefined"
  
Q2_LEASE_REFERENCES_LATEST:
  question: "Can lease reference 'latest' version of strategy?"
  context: "Strategy 1.0.0 → 1.0.1 (minor fix)"
  options:
    A: New lease required for ANY version change (strict)
    B: Patch versions auto-adopt (lenient)
  current: "Strict (hash verification)"
  concern: "Operational friction for minor fixes"
  
Q3_BOUNDS_LOGIC:
  question: "Multiple bounds — OR or AND?"
  context: "max_drawdown AND max_consecutive_losses"
  options:
    A: OR — any bound triggers halt (current)
    B: AND — all bounds must be exceeded
  current: "OR"
  
Q4_PARTIAL_SESSION:
  question: "Can lease restrict to PART of a session?"
  context: "Strategy: 00:00-04:00; Lease wants: 01:00-03:00"
  options:
    A: Session-level only (current)
    B: Custom time subsetting (complex)
  current: "Session-level"
  
Q5_CALIBRATION_THRESHOLD:
  question: "Is 5% drift threshold right?"
  context: "Auto-shadow after insertion"
  concern: "Too tight = false positives; too loose = misses drift"
  
Q6_EXTENSION_TRACKING:
  question: "How to track sweep extension per-direction?"
  context: "Asia can sweep HIGH or LOW; need separate tracking"
  from: Olya's strategy doc
  concern: "Invalidating wrong side = bahts ghosted"
```

---

## 10. ADVISOR REVIEW TEMPLATE

```yaml
# Copy this template for your review

advisor: [GPT / GROK / OWL / G]
reviewed_at: [datetime]

section_verdicts:
  1_core_concepts: [PASS / CONCERN / FAIL]
  2_cartridge_schema: [PASS / CONCERN / FAIL]
  3_lease_schema: [PASS / CONCERN / FAIL]
  4_state_machine: [PASS / CONCERN / FAIL]
  5_insertion_protocol: [PASS / CONCERN / FAIL]
  6_worked_example: [PASS / CONCERN / FAIL]
  7_guards: [PASS / CONCERN / FAIL]
  8_beads: [PASS / CONCERN / FAIL]
  9_open_questions: [answered below]
  10_ceremony: [PASS / CONCERN / FAIL]

specific_flags:
  - section: [which]
    field: [which]
    issue: [what's wrong]
    fix: [suggestion]
    severity: [LOW / MEDIUM / HIGH]

dumb_failures_to_add:
  - [description]

open_question_answers:
  Q1: [answer + rationale]
  Q2: [answer + rationale]
  Q3: [answer + rationale]
  Q4: [answer + rationale]
  Q5: [answer + rationale]
  Q6: [answer + rationale]

missing_elements:
  - [what's not covered]

overall_verdict: [READY / NEEDS_WORK / MAJOR_ISSUES]
```

---

## 11. SUMMARY

```yaml
document_status: DRAFT_v0.1_CANONICAL
purpose: "Battle-test with advisors before commit"
synthesized_from: "Two draft versions (compaction recovery)"

what_this_defines:
  - Cartridge manifest schema (what IS a strategy)
  - Lease schema (governance wrapper)
  - Insertion protocol (how cartridge slots)
  - Lifecycle state machine (lease states)
  - Failure guards (what can go wrong)
  - Weekly ceremony (human governance)

what_this_enables:
  - N64 slot-in architecture
  - Bounded autonomy with sovereignty
  - Professional operating rhythm
  - Forensic trail for all decisions

dependencies:
  - S44 soak must pass (foundation proven)
  - S47 implements these schemas

next_steps:
  1: Advisor review (GPT, GROK, OWL)
  2: G review and amendments
  3: Synthesize into canonical v1.0
  4: Commit to repo
```

---

**OINK OINK — CANONICAL DRAFT READY FOR BATTLE TEST 🐗🔥**
