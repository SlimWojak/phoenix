# ═══════════════════════════════════════════════════════════════════════════════
# BRIEF: S66.A.1
# MISSION: STATE_FLAGS_AND_REGRESSION
# OWNER: Opus (Cursor — step-through mode)
# FROM: CTO
# DATE: 2026-03-22
# FORMAT: DENSE
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# 0. ORIENTATION — READ BEFORE BUILDING
# ─────────────────────────────────────────────────────────────────────────────

orientation:
  you_are: "Opus, builder for a8ra constitutional trading system"
  this_is: "S66 Track A — fix 2 flags from S65, re-run 14-trade regression"

  system_state: |
    S65 sealed (be2a06e). Detection pipeline operational:
    River → HTF producers → state classifier → checklist → DIAGNOSTIC_SIGNAL.
    218 tests passing. Shadow mode active.

    Gate B3C: 4/8 addressable trades produce signal.
    Bottleneck: state classifier (daily snapshot, not checklist).

    MIRROR dashboard built and verified (overnight). Olya's observation
    surface for Monday. What we fix here is what MIRROR displays.

  read_these_files:
    spec: "STATE_DETECTION_LOGIC_v2.yaml — sections: htf_phase_detection, phase_transitions, h1_alignment"
    classifier: "~/dexter/dexter/state/classifier.py — classify_day(), WorldState output"
    evaluator: "~/dexter/dexter/checklist/evaluator.py — five-factor evaluator, skip table"
    signal_builder: "~/dexter/dexter/checklist/signal_builder.py — DIAGNOSTIC_SIGNAL emission"
    pipeline: "~/dexter/scripts/daily_detection_export.py — end-to-end pipeline"
    regression: "~/dexter/scripts/gate6_verification.py — 14-trade regression harness"
    ground_truth: "~/dexter/research/ground_truth/annotated_trades.yaml — 14 Olya-annotated trades"
    locked_params: "~/dexter/configs/locked_baseline.yaml — vLOCK parameters"

# ─────────────────────────────────────────────────────────────────────────────
# 1. FLAG 1 — INTRADAY STATE EVOLUTION (HIGH PRIORITY)
# ─────────────────────────────────────────────────────────────────────────────

flag_1:
  name: "STATE_CLASSIFIER_INTRADAY_EVOLUTION"
  priority: HIGH — fixes B3C misses, highest signal impact

  problem: |
    classify_day() currently computes WorldState ONCE per forex day using
    end-of-day HTF CLAIMs. Intraday state transitions are missed.

    Example: morning is RANGE, then 4H MSS fires at 09:00 → should
    transition to EXPANSION. But classifier only sees this at day close.
    Trades 3, 7, 9, 11 (the 4 B3C misses) are believed to fail because
    the state at execution time differs from the end-of-day snapshot.

  spec_reference: |
    STATE_DETECTION_LOGIC_v2.yaml, section phase_transitions:
    "Phase transitions are event-driven. A phase changes when a structural
     primitive fires, not on a fixed clock."

    The spec already says stale_after_bars=1 for WorldState. The implementation
    may have defaulted to daily cadence.

  fix: |
    The classifier must re-evaluate WorldState at each new HTF bar close:
    - On each new 1H bar close: re-run h1_alignment computation
    - On each new 4H bar close: re-run full phase classification
    - WorldState output should carry a timestamp showing WHEN it was computed
    - Pipeline should produce WorldState snapshots at each HTF bar close,
      not just one per day

    IMPORTANT: The classification LOGIC is already correct (trade_001 proves
    it fires perfectly when state matches). The fix is WHEN it runs, not
    WHAT it computes.

  approach: |
    1. Read classify_day() in classifier.py — understand current trigger cadence
    2. Read daily_detection_export.py — understand how pipeline calls classifier
    3. Modify pipeline to call classifier at each 1H/4H bar boundary
    4. WorldState becomes a LIST of snapshots per day, not a single dict
    5. Checklist evaluator receives the WorldState snapshot NEAREST to chain time
       (not end-of-day WorldState)
    6. Add tests: same day, different WorldState at 08:00 vs 16:00

  files_to_modify:
    - "~/dexter/dexter/state/classifier.py — add incremental re-eval"
    - "~/dexter/scripts/daily_detection_export.py — call classifier at HTF boundaries"
    - "~/dexter/dexter/checklist/evaluator.py — consume time-indexed WorldState"

  DO_NOT:
    - "Change the classification logic itself (it's correct)"
    - "Change locked_baseline.yaml parameters"
    - "Change any L1 producer logic"

  test: |
    - Unit test: given bars where 4H MSS fires mid-day, WorldState transitions
      from RANGE→EXPANSION at the correct bar
    - Regression: gate6_verification.py re-run (target below)

# ─────────────────────────────────────────────────────────────────────────────
# 2. FLAG 2 — SIGNAL DIRECTION FILTERING (MEDIUM PRIORITY)
# ─────────────────────────────────────────────────────────────────────────────

flag_2:
  name: "SIGNAL_DIRECTION_GUARD"
  priority: MEDIUM — small fix, high safety value

  problem: |
    DIAGNOSTIC_SIGNAL currently emits for ALL composite chains,
    regardless of whether chain direction matches WorldState direction
    permission. Known case: trade_014 (SHORT context) gets bullish signal.
    trade_011 also flagged.

    The skip table has a CONTRADICTION skip reason but it may not be
    catching all direction mismatches.

  fix: |
    Before signal emission, verify:
      chain.direction == WorldState.daily_direction → PASS
      chain.direction != WorldState.daily_direction → SKIP (reason: DIRECTION_MISMATCH)

    Also respect direction_permission:
      WITH_EXPANSION: only chains matching expansion direction
      COUNTER_ALLOWED: both directions (retrace phase)
      BOTH: both directions (range phase — delegated authority TF)

  approach: |
    1. Read signal_builder.py — find where DIAGNOSTIC_SIGNAL is emitted
    2. Read evaluator.py skip table — find existing CONTRADICTION logic
    3. Add explicit direction_match check BEFORE signal emission
    4. If skip table already has this logic, find why it's not catching all cases
    5. Add test: bullish chain + bearish WorldState → SKIP

  files_to_modify:
    - "~/dexter/dexter/checklist/signal_builder.py — direction guard"
    - "~/dexter/dexter/checklist/evaluator.py — skip table entry if needed"

  test: |
    - Unit test: bearish chain in bullish EXPANSION → no signal emitted
    - Unit test: bullish chain in RETRACE (COUNTER_ALLOWED) → signal emitted
    - Regression: trade_011, trade_014 no longer produce wrong-direction signals

# ─────────────────────────────────────────────────────────────────────────────
# 3. FLAG 4 — SWEEP LEVEL POOL (LOW PRIORITY, IF TIME)
# ─────────────────────────────────────────────────────────────────────────────

flag_4:
  name: "SWEEP_LEVEL_POOL_POPULATION"
  priority: LOW — do only if flags 1+2 ship clean with time remaining

  problem: |
    SESSION_LIQUIDITY box params need promoted swings and session
    levels populated for full sweep detection completeness.

  scope: |
    Level pool in level_lifecycle.py needs:
    - Promoted swing points (swing highs/lows that become reference levels)
    - Session levels (Asia H/L, PDH/PDL) fed into the level pool
    - HTF EQH/EQL fed into the level pool
    These are all EXISTING producers — the gap is wiring their output
    into the level lifecycle tracker.

  impact: "Improves sweep detection. Does not break existing signals."

  defer_if: "Flag 1 or Flag 2 take longer than expected"

# ─────────────────────────────────────────────────────────────────────────────
# 4. REGRESSION — 14-TRADE VERIFICATION
# ─────────────────────────────────────────────────────────────────────────────

regression:
  what: "Re-run full pipeline on all 14 Olya-annotated trades after fixes"
  script: "~/dexter/scripts/gate6_verification.py"
  ground_truth: "~/dexter/research/ground_truth/annotated_trades.yaml"

  pre_fix_baseline: "4/8 addressable trades produce DIAGNOSTIC_SIGNAL (S65 B3C)"

  target: "≥6/8 addressable trades produce DIAGNOSTIC_SIGNAL"

  stretch: "≥8/8 addressable (may require Flag 4 for sweep-dependent trades)"

  per_trade_report: |
    For each of the 14 trades, produce:
      trade_id:
      date:
      olya_direction:
      worldstate_at_execution_time:  # NEW — time-indexed, not end-of-day
      phase_match: PASS/FAIL
      signal_emitted: YES/NO
      signal_direction_correct: YES/NO/NA
      skip_reason: (if no signal)
      notes:

  what_to_check_if_target_not_met: |
    - Which trades still miss? What skip reason?
    - Is the miss from state classifier (Flag 1) or direction filter (Flag 2)?
    - Is the miss from sweep level pool (Flag 4)?
    - Document each miss with diagnosis for next iteration.

# ─────────────────────────────────────────────────────────────────────────────
# 5. EXIT GATES
# ─────────────────────────────────────────────────────────────────────────────

exit_gates:

  gate_1_flag_1:
    criterion: "WorldState re-evaluates on each 1H and 4H bar close"
    test: "Unit test — mid-day 4H MSS triggers state transition"
    pass: "WorldState at execution time differs from end-of-day where appropriate"

  gate_2_flag_2:
    criterion: "Signals emit only in matching direction"
    test: "Unit test — wrong-direction chain produces SKIP not SIGNAL"
    pass: "trade_011, trade_014 no longer produce wrong-direction signals"

  gate_3_regression:
    criterion: "≥6/8 addressable trades produce DIAGNOSTIC_SIGNAL"
    test: "gate6_verification.py full run with per-trade report"
    pass: "6+ of 8 addressable trades fire. Each miss documented with diagnosis."

  gate_4_no_regression:
    criterion: "All existing 218 tests still pass"
    test: "pytest ~/dexter/ — full suite"
    pass: "0 failures"

PASS_CONDITION: "Gates 1-4 all PASS"
FAIL_CONDITION: "Any gate FAIL → halt, report diagnosis, do not force"

# ─────────────────────────────────────────────────────────────────────────────
# 6. CONSTRAINTS
# ─────────────────────────────────────────────────────────────────────────────

constraints:
  DO_NOT_MODIFY:
    - "SYNTHETIC_OLYA_METHOD_vLOCK.yaml (methodology canon)"
    - "configs/locked_baseline.yaml (LOCKED parameters)"
    - "Any L1 producer logic (producers are vLOCK)"
    - "PROPOSED HTF params (Flag 3 — NO CODE CHANGE, Olya calibrates)"

  PRESERVE:
    - "INV-NO-FORMING-BAR-CONSUMPTION (closed bars only)"
    - "INV-WARMUP-MANDATORY (minimum bars before HTF CLAIM)"
    - "INV-REPLAY-LIVE-PARITY (same bars → same CLAIMs)"
    - "INV-IDEMPOTENT-CLAIM-EMIT (no duplicate CLAIMs on re-run)"

# ─────────────────────────────────────────────────────────────────────────────
# 7. REPORT FORMAT
# ─────────────────────────────────────────────────────────────────────────────

report:
  format: DENSE
  structure: |
    BRIEF: S66.A.1
    STATUS: PASS/FAIL

    FLAG_1:
      status: PASS/FAIL
      change_summary: (what was modified, which files)
      test_evidence: (test name, output)

    FLAG_2:
      status: PASS/FAIL
      change_summary:
      test_evidence:

    FLAG_4: (if attempted)
      status: PASS/FAIL/SKIPPED

    REGRESSION:
      pre_fix: 4/8
      post_fix: N/8
      per_trade_table: (14 rows)
      misses_diagnosed: (for any remaining misses)

    EXISTING_TESTS: 218/218 PASS

    FILES_MODIFIED: (list with line counts)
    FILES_CREATED: (list)

# ═══════════════════════════════════════════════════════════════════════════════
# END BRIEF
#
# Priority: Flag 1 > Flag 2 > Regression > Flag 4
# Target: ≥6/8 addressable trades. Monday Olya sees correct signals in MIRROR.
# ═══════════════════════════════════════════════════════════════════════════════
