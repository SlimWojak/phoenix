# BRIEF: S50.T1.CABINET_REFACTOR

```yaml
BRIEF: S50.T1.2026-02-22
MISSION: CABINET_REFACTOR — delta model → self-contained cabinet model
OWNER: OPUS (Cursor)
FORMAT: DENSE
AUTHORITY: G (Sovereign) + Olya (CSO) + CTO — three-way approved
```

---

## CONTEXT

```yaml
status: |
  S47 implemented Cartridge/Lease system with drawer_deltas merge model.
  Olya (CSO) identified that conditions.yaml blends methodology and strategy.
  The 5 drawers should be PER-STRATEGY (self-contained), not deltas from a shared base.
  The "base" was actually the first strategy wearing methodology's clothes.

proven:
  - Lease state machine: DRAFT→ACTIVE→EXPIRED|REVOKED|HALTED (118 tests)
  - Insertion protocol: 8-step with rollback (13 tests)
  - All governance invariants (124+ proven)
  - 240 chaos vectors PASS

invariant: INV-NO-CORE-REWRITES-POST-S44
  ruling: THIS IS NOT A REWRITE
  rationale: Schema evolution within S46 design. Removes complexity. Preserves all contracts.
```

---

## TASK

### TASK 0: ORIENTATION (do this first)

```yaml
0.1: cat REPO_MAP.md
0.2: cat cso/knowledge/conditions.yaml  # Understand current 5-drawer structure + 48 gates
0.3: cat governance/lease_types.py  # CartridgeManifest Pydantic model (has drawer_deltas)
0.4: cat governance/cartridge.py  # CartridgeLoader, CartridgeLinter (guard dog)
0.5: cat governance/insertion.py  # InsertionProtocol (step_4 merge, step_6 guard_dog)
0.6: cat cartridges/active/asia_range_scalp.yaml  # Worked example (currently uses drawer_deltas)
0.7: cat docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md | head -200  # Schema reference
0.8: ls tests/test_lease/  # Existing test files

CRITICAL_NAME_CHECK:
  current_drawer_delta_keys: [foundation, context, conditions, entry, management]
  methodology_canonical_names: [HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION]
  action: |
    Check conditions.yaml for which naming convention is actually used.
    The Bead Field Spec uses: HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION
    The v1.0 cartridge schema uses: foundation, context, conditions, entry, management
    drawer_config in v1.1 MUST use the methodology-canonical names from Bead Field Spec.
    Map the existing 48 gates to the canonical drawer names.
```

### TASK 1: SCHEMA — cartridge manifest (drawer_deltas → drawer_config)

```yaml
file: governance/lease_types.py (Pydantic models)
also: schemas/strategy_manifest.schema.yaml (if exists as separate file)

CHANGE:
  old_field: cso_integration.drawer_deltas
    type: optional per-drawer objects (foundation, context, conditions, entry, management)
    semantics: "Modifications to CSO drawers (MERGE, not replace)"

  new_field: cso_integration.drawer_config
    type: REQUIRED object with ALL 5 drawers
    semantics: "Complete 5-drawer cabinet (self-contained, no merge)"
    drawer_names: [HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION]
    all_required: true  # Every cartridge must fill all 5 drawers
    each_drawer:
      type: object
      description: "Complete gate configuration for this drawer"
      required: true

  delete_field: cso_integration.drawer_deltas (remove entirely)

  update_decision:
    old: "D1_DELTA_NOT_REPLACE"
    new: "D1_SELF_CONTAINED_CABINET"
    rule: "Each cartridge carries complete 5-drawer cabinet"
    rationale: "No merge, no conflicts, each strategy owns its full configuration"

VALIDATION_RULE:
  - All 5 drawers present (KeyError if missing)
  - Each drawer is non-empty dict
  - Drawer names match enum exactly
```

### TASK 2: CONDITIONS → METHODOLOGY_TEMPLATE

```yaml
file: cso/knowledge/conditions.yaml

ACTION:
  1. Copy conditions.yaml → cso/knowledge/methodology_template.yaml
  2. Add header comment to methodology_template.yaml:
     # METHODOLOGY TEMPLATE — Reference for drawer structure and gate definitions
     # Cartridges do NOT merge against this. They carry their own complete cabinet.
     # This serves as: (a) documentation of the 5-drawer structure,
     # (b) reference for gate naming conventions, (c) template for new cartridge authoring.
  3. Rename drawer sections to canonical names if needed:
     foundation → HTF_BIAS
     context → MARKET_STRUCTURE
     conditions → PREMIUM_DISCOUNT
     entry → ENTRY_MODEL
     management → CONFIRMATION
  4. Keep original conditions.yaml as-is (reference, no orphan — other code may import it)
     Add deprecation header: "# DEPRECATED: Use methodology_template.yaml. This file retained for reference."

NOTE: Check all imports of conditions.yaml across codebase before deprecating.
  grep -r "conditions.yaml" --include="*.py" --include="*.yaml"
```

### TASK 3: INSERTION PROTOCOL — merge → validate

```yaml
file: governance/insertion.py

STEP_4 CHANGE:
  old: step_4_drawer_merge
    action: "Check drawer_deltas for conflicts"
    guard: "merger.merge(base_drawers, manifest.drawer_deltas)"
    conflict_resolution: PERISH (no silent merge)
    on_conflict: "REJECT — drawer conflict (explicit)"

  new: step_4_cabinet_validation
    action: "Validate drawer_config is complete and methodology-compliant"
    guards:
      - All 5 drawers present in cartridge.drawer_config
      - Each drawer is non-empty
      - Drawer names match canonical enum exactly
      - Gate keys within each drawer are valid (reference methodology_template.yaml for valid gate names)
      - No forbidden patterns in drawer values (delegate to guard_dog)
    on_fail: "REJECT — cabinet incomplete or non-compliant"
    on_pass: "Cabinet validated, proceed to step_5"

  DELETE:
    - merger.merge() function (or entire merger module if dedicated)
    - merge_algorithm implementation (Section 5.1 of design doc)
    - Any base_drawers loading from conditions.yaml for merge purposes

STEP_6 CHANGE:
  old: "Full guard dog scan on merged drawers"
    guard: "guard_dog.full_scan()"

  new: "Full guard dog scan on cartridge.drawer_config directly"
    guard: "guard_dog.full_scan(cartridge.drawer_config)"
    note: Simpler — no merged result to construct, scan the cabinet as-is

WHAT STAYS IDENTICAL:
  - step_1_validation (schema validation — updated schema)
  - step_2_constitutional_check (invariants_required)
  - step_2b_dependency_check (environment hash)
  - step_3_forbidden_patterns (narrator templates)
  - step_5_index_update (index.yaml)
  - step_7_calibration_smoke (shadow session)
  - step_8_ready (cartridge available for lease)
  - Rollback logic
  - Removal steps
```

### TASK 4: WORKED EXAMPLE — Asia Range Scalp

```yaml
file: cartridges/active/asia_range_scalp.yaml

CHANGE: Convert drawer_deltas to drawer_config with COMPLETE cabinet.

old:
  cso_integration:
    drawer_deltas:
      foundation:
        asia_range_method: wick_to_wick
      conditions:
        sweep_required: true
        # ... partial
      entry:
        fvg_required: true
        # ... partial
      management:
        sl_placement: beyond_sweep_extreme
        # ... partial

new:
  cso_integration:
    drawer_config:
      HTF_BIAS:
        # Complete HTF bias configuration for Asia Range Scalp
        # Reference: methodology_template.yaml HTF_BIAS section
        # Must include ALL gates relevant to HTF bias evaluation
        # Populate from conditions.yaml foundation + context sections
        # This strategy: regime_affinity ANY, so HTF gates are permissive
        weekly_bias_required: false  # Asia scalp doesn't require weekly alignment
        daily_bias_required: false
        session_bias: asia_sweep_direction  # Derived from sweep direction

      MARKET_STRUCTURE:
        # Complete market structure configuration
        asia_range_method: wick_to_wick
        asia_range_start: "19:00"
        asia_range_end: "00:00"
        asia_range_timezone: America/New_York
        asia_range_max_pips: 30
        mss_required: false  # Asia scalp uses sweep, not MSS

      PREMIUM_DISCOUNT:
        # Complete premium/discount zone configuration
        sweep_required: true
        sweep_extension_min_pips: 1
        sweep_extension_max_pips: 20
        sweep_direction: [high, low]
        sweep_extension_high_pips: null
        sweep_extension_low_pips: null
        pd_zone_required: false  # Sweep IS the zone filter for this strategy

      ENTRY_MODEL:
        # Complete entry model configuration
        fvg_required: true
        fvg_timeframe: 5min
        re_acceptance_required: true
        re_acceptance_candle: 5min_close_inside
        limit_order: true
        entry_type: fvg_retrace

      CONFIRMATION:
        # Complete confirmation/management configuration
        sl_placement: beyond_sweep_extreme
        sl_buffer_pips: 2
        tp_placement: opposite_asia_extreme
        max_trades_per_session: 1
        trail_stop: false

    gate_requirements:
      - GATE_ASIA_RANGE_FORMED
      - GATE_SWEEP_DETECTED
      - GATE_FVG_VALID
      - GATE_RE_ACCEPTANCE

    primitive_set: [FVG, SWEEP, RE_ACCEPTANCE, KZ_TIMING]

IMPORTANT:
  - Verify gate values against conditions.yaml / methodology_template.yaml
  - Every gate referenced in conditions.yaml that maps to a drawer MUST appear
  - If you're unsure about a gate's correct value for Asia Range Scalp,
    check SYNTHETIC_OLYA_METHOD_v0.3.yaml (if available in repo) or flag for CTO review
  - The example above is INDICATIVE — use actual gate names from the codebase
```

### TASK 5: DESIGN DOC UPDATE

```yaml
file: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md

ACTION: Inline update to v1.1. DO NOT create separate file.

CHANGES:
  header:
    old: "document_status: v1.0_CANONICAL"
    new: "document_status: v1.1_CANONICAL"
    add_changelog: |
      v1.1 (2026-02-22): Cabinet model refactor.
        - drawer_deltas → drawer_config (complete self-contained cabinet per strategy)
        - conditions.yaml → methodology_template.yaml (reference, not merge base)
        - Insertion step_4: merge logic → cabinet validation
        - D1_DELTA_NOT_REPLACE → D1_SELF_CONTAINED_CABINET
        - Section 5.1 Drawer Merge Algorithm: DELETED (no longer applicable)
        - Origin: Olya (CSO) identified methodology/strategy blending.
          Three-way approval: G + CTO + Olya.

  section_2_cartridge_schema:
    - Replace drawer_deltas with drawer_config in schema definition
    - All 5 drawers REQUIRED (not optional)
    - Use canonical names: HTF_BIAS, MARKET_STRUCTURE, PREMIUM_DISCOUNT, ENTRY_MODEL, CONFIRMATION

  section_2.2_decisions:
    - Replace D1_DELTA_NOT_REPLACE with D1_SELF_CONTAINED_CABINET
    - Add rationale: "Each cartridge carries its own homework. No merge, no conflicts."

  section_5_insertion:
    - step_4: Replace drawer_merge with cabinet_validation
    - step_6: Update guard_dog to scan drawer_config directly

  section_5.1:
    - DELETE Drawer Merge Algorithm entirely
    - Replace with: "## 5.1 Cabinet Validation" describing the validation rules

  section_6_worked_example:
    - Update Asia Range Scalp to use drawer_config (from Task 4)

  section_9_resolved_questions:
    - Add: Q7_CABINET_MODEL
      resolution: "Self-contained cabinet per strategy (not deltas from shared base)"
      consensus: "G + CTO + Olya (three-way approval)"
      rationale: "Base was first strategy wearing methodology's clothes"
```

### TASK 6: TESTS

```yaml
DELETE:
  - Any test that exercises merge_algorithm / drawer_merge
  - Any test that validates conflict detection in drawer_deltas merge
  - Any test that loads conditions.yaml as merge base
  - Identify these by grep: grep -r "drawer_deltas\|merge\|merger" tests/

CREATE: tests/test_lease/test_cabinet_validation.py

TEST_CASES:
  test_valid_complete_cabinet:
    input: Cartridge with all 5 drawers populated
    expect: PASS validation

  test_missing_drawer_rejects:
    input: Cartridge with 4/5 drawers (missing CONFIRMATION)
    expect: REJECT with specific error naming missing drawer

  test_empty_drawer_rejects:
    input: Cartridge with 5 drawers but one is empty dict
    expect: REJECT with specific error

  test_wrong_drawer_name_rejects:
    input: Cartridge with drawer named "foundation" instead of "HTF_BIAS"
    expect: REJECT — invalid drawer name

  test_extra_drawer_rejects:
    input: Cartridge with 6 drawers (5 valid + 1 unknown)
    expect: REJECT or WARN — unexpected drawer

  test_guard_dog_scans_cabinet_directly:
    input: Cartridge with forbidden pattern in ENTRY_MODEL drawer
    expect: REJECT at step_6 (guard_dog catches it)

  test_insertion_protocol_uses_validation_not_merge:
    input: Valid cartridge through full 8-step insertion
    expect: No merge function called, cabinet validation at step_4

  test_methodology_template_not_loaded_for_merge:
    input: Any insertion flow
    expect: methodology_template.yaml is NOT loaded as merge base

  test_existing_lease_tests_still_pass:
    note: "Run ALL existing lease tests — FSM, bounds, halt override, expiry, chaos"
    expect: "Zero regressions. Cabinet change is schema-level, not governance-level."

CHAOS_VECTORS (add to existing chaos suite):
  bunny_cabinet_1: "Cartridge with drawers in wrong order — should still validate (dict, not list)"
  bunny_cabinet_2: "Cartridge with unicode in drawer values — should handle gracefully"
  bunny_cabinet_3: "Concurrent insertion of two cartridges with different cabinets — serialization holds"
```

---

## DELIVERABLES

```yaml
files_modified:
  - governance/lease_types.py (drawer_deltas → drawer_config)
  - governance/insertion.py (step_4 merge → validate, step_6 simplified)
  - governance/cartridge.py (CartridgeLinter updated for cabinet)
  - cartridges/active/asia_range_scalp.yaml (complete cabinet)
  - docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md → v1.1 inline

files_created:
  - cso/knowledge/methodology_template.yaml (from conditions.yaml)
  - tests/test_lease/test_cabinet_validation.py

files_deprecated:
  - cso/knowledge/conditions.yaml (header added, retained as reference)

files_deleted:
  - Any standalone merger module (if exists)
  - Merge-specific test files (content, not files — may be in shared test files)
```

---

## EXIT GATES

```yaml
GATE_T1_1:
  criterion: "drawer_config field exists in CartridgeManifest, drawer_deltas removed"
  test: "grep -r drawer_deltas governance/ → 0 hits (except comments/changelog)"

GATE_T1_2:
  criterion: "All 5 canonical drawer names enforced as required"
  test: "test_missing_drawer_rejects PASS + test_wrong_drawer_name_rejects PASS"

GATE_T1_3:
  criterion: "Insertion step_4 validates, does not merge"
  test: "test_insertion_protocol_uses_validation_not_merge PASS"

GATE_T1_4:
  criterion: "Asia Range Scalp example uses drawer_config with complete cabinet"
  test: "CartridgeLoader.load('asia_range_scalp.yaml') succeeds with new schema"

GATE_T1_5:
  criterion: "All existing tests pass (zero regressions)"
  test: "pytest tests/ — compare count to baseline 1618+ (minus deleted merge tests, plus new validation tests)"

GATE_T1_6:
  criterion: "Design doc updated to v1.1 with changelog"
  test: "grep 'v1.1_CANONICAL' docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md"
```

---

## PASS / FAIL

```yaml
PASS_CONDITION: "All 6 gates GREEN. Zero regressions in existing test suite."
FAIL_CONDITION: "Any gate RED. Any existing test broken. Any governance invariant violated."
HALT_TRIGGER: "If drawer rename causes cascade beyond governance/ and tests/ — STOP and report to CTO."
```

---

## REPORT FORMAT

```yaml
format: DENSE
include:
  - Gate verdicts (PASS/FAIL per gate)
  - Test count delta (old → new)
  - Files modified (with line counts)
  - Any issues encountered
  - Any decisions made (flag for CTO review)
  - Time taken
```

---

```yaml
SIGNED: CTO (Phoenix)
DATE: 2026-02-22
DIRECTIVE: "Clean, not clever. Simpler, not bigger. Ship it."
```
