# ═══════════════════════════════════════════════════════════════════════════════
# BRIEF: S66.C.1
# MISSION: DREAM_CYCLE_V1 — REJECTION MINING + MORNING BRIEFING
# OWNER: Opus (Factory — autonomous run, clear scope)
# FROM: CTO
# DATE: 2026-03-22
# FORMAT: DENSE
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# 0. ORIENTATION
# ─────────────────────────────────────────────────────────────────────────────

orientation:
  you_are: "Opus, builder for a8ra constitutional trading system"
  this_is: "Dream Cycle v1 — the system's learning engine"

  context: |
    The full Dream Cycle vision (EnvModels, counterfactual simulation,
    SkillRL, adversarial agents) is Gate 5+. This is NOT that.

    Dream Cycle v1 is the MINIMUM that makes the system learn from day 1:
    - Pipeline runs daily, produces detection JSON with signals + skips
    - A nightly analysis job reviews what happened
    - A morning briefing surfaces findings for G + Olya
    - Every day of operation makes the system smarter

    The 99.8% Principle: in a system that scans 1,000 setups and picks 2,
    the 998 rejections are more valuable than the 2 successes.

  system_state: |
    S66 Track A complete. Pipeline produces detection JSON with:
    - All L1 primitives per TF
    - Composite chains (REVERSAL_CHAIN, CONTINUATION_CHAIN)
    - WorldState snapshots (time-indexed, intraday transitions)
    - DIAGNOSTIC_SIGNALs (shadow_mode=true, five-factor breakdown)
    - Skip reasons for chains that didn't produce signals

    4 days exported: Mar 17-20. 15 signals across those days.
    Detection JSON lives at: ~/dexter/output/detections/{date}.json

  read_these_files:
    pipeline_output: "~/dexter/output/detections/2026-03-19.json — sample with signals + snapshots"
    pipeline_script: "~/dexter/scripts/daily_detection_export.py — what produces the JSON"
    evaluator: "~/dexter/dexter/checklist/evaluator.py — skip reasons, factor breakdown"
    signal_builder: "~/dexter/dexter/checklist/signal_builder.py — DIAGNOSTIC_SIGNAL schema"
    design_intent: "~/dexter/docs/DREAM_CYCLE_DESIGN_INTENT_v0_1.md — long-term vision (context only)"

# ─────────────────────────────────────────────────────────────────────────────
# 1. WHAT DREAM CYCLE V1 DOES
# ─────────────────────────────────────────────────────────────────────────────

what_it_does: |
  After market close each day, Dream Cycle v1:

  1. Loads today's detection JSON
  2. Loads today's actual price bars (from River parquet/staging)
  3. For each DIAGNOSTIC_SIGNAL that fired:
     - What happened after? (price moved how far, in what direction)
     - Would a paper trade have hit TP or SL?
     - How long until TP/SL was reached?
     - Was the signal inside peak_window?
  4. For each composite chain that was SKIPPED (no signal):
     - What was the skip reason? (from evaluator skip table)
     - What happened after the skip? (price action post-chain)
     - Was the skip correct? (would the trade have won or lost?)
     - Classification: FALSE_REJECTION | CORRECT_REJECTION | INCONCLUSIVE
  5. For each WorldState transition during the day:
     - Did the market confirm the phase? (price action aligned with state?)
     - Were there transitions the classifier missed? (detectable post-hoc)
  6. Produces a structured MORNING BRIEFING

  The briefing is the deliverable. It's what G and Olya read with coffee
  on Tuesday morning (first full day is Monday).

# ─────────────────────────────────────────────────────────────────────────────
# 2. MORNING BRIEFING FORMAT
# ─────────────────────────────────────────────────────────────────────────────

briefing_format:

  output_file: "~/dexter/output/dream_cycle/{date}_briefing.json"
  human_readable: "~/dexter/output/dream_cycle/{date}_briefing.md"

  sections:

    header:
      date: "forex day analyzed"
      pipeline_version: "commit hash"
      signals_fired: "count"
      chains_skipped: "count"
      worldstate_transitions: "count"

    signal_outcomes:
      description: "For each DIAGNOSTIC_SIGNAL that fired"
      per_signal:
        signal_time: "timestamp"
        direction: "BULLISH/BEARISH"
        model_type: "REVERSAL/CONTINUATION"
        chain_type: "chain identifier"
        peak_window: "true/false"
        entry_price: "price at signal time (chain MSS area)"
        factors: "F1-F5 breakdown"
        outcome:
          price_after_30m: "price 30 minutes later"
          price_after_1h: "price 1 hour later"
          price_after_4h: "price 4 hours later (or day close if sooner)"
          max_favorable: "maximum favorable excursion (pips)"
          max_adverse: "maximum adverse excursion (pips)"
          would_hit_tp: "true/false (if target from F5 was reached)"
          would_hit_sl: "true/false (if stop from swing beyond PDA was reached)"
          time_to_tp: "minutes (if TP hit)"
          time_to_sl: "minutes (if SL hit)"
          net_result: "WIN/LOSS/OPEN (if neither TP nor SL hit by day close)"

    skip_analysis:
      description: "For each composite chain that was evaluated but SKIPPED"
      per_skip:
        chain_time: "timestamp of chain anchor (MSS)"
        chain_direction: "BULLISH/BEARISH"
        chain_type: "REVERSAL_CHAIN/CONTINUATION_CHAIN"
        skip_reason: "from evaluator skip table"
        factors_at_skip: "which of F1-F5 passed/failed"
        worldstate_at_time: "phase/direction/permission at chain time"
        outcome:
          price_after_30m: "same as above"
          price_after_1h: ""
          max_favorable: ""
          max_adverse: ""
          hypothetical_result: "WOULD_WIN/WOULD_LOSE/INCONCLUSIVE"
        classification: "FALSE_REJECTION | CORRECT_REJECTION | INCONCLUSIVE"
        note: |
          FALSE_REJECTION: skipped but max_favorable > 2x max_adverse
          CORRECT_REJECTION: skipped and max_adverse > max_favorable
          INCONCLUSIVE: neither clear win nor clear loss

    state_review:
      description: "WorldState accuracy assessment"
      per_transition:
        time: "when state changed"
        from_state: "previous phase/direction"
        to_state: "new phase/direction"
        trigger: "what caused the transition (which primitive)"
        confirmed: "did subsequent price action align? YES/NO/PARTIAL"

    daily_summary:
      total_signals: "count"
      signal_wins: "count"
      signal_losses: "count"
      false_rejections: "count — THIS IS THE GOLD"
      correct_rejections: "count"
      state_accuracy: "transitions confirmed / total transitions"
      top_finding: "single most important observation (1-2 sentences)"
      action_items: "specific tuning suggestions (if any)"

# ─────────────────────────────────────────────────────────────────────────────
# 3. ARCHITECTURE
# ─────────────────────────────────────────────────────────────────────────────

architecture:

  location: "~/dexter/dream_cycle/"

  files:
    analyzer: "dream_cycle/analyzer.py — core analysis engine"
    briefing: "dream_cycle/briefing.py — morning briefing generator"
    runner: "scripts/dream_cycle_nightly.py — entry point (cron-able)"

  data_flow: |
    1. Runner loads detection JSON for target date
       (~/dexter/output/detections/{date}.json)
    2. Runner loads price bars for target date + next day
       (via RiverBarAdapter — same bars pipeline used)
       Need next day bars to evaluate "what happened after" for
       late-day signals. If next day not available, use available bars.
    3. Analyzer processes signals → outcomes
    4. Analyzer processes skipped chains → classifications
    5. Analyzer processes WorldState transitions → confirmations
    6. Briefing generator produces JSON + Markdown
    7. Files land in ~/dexter/output/dream_cycle/

  price_source: |
    RiverBarAdapter (same adapter the pipeline uses).
    For "what happened after" computation:
    - Load 1m bars from signal time to +4 hours (or day close)
    - Compute max favorable/adverse excursion from 1m granularity
    - Check if price crossed TP/SL levels

  tp_sl_computation: |
    For signals (which have chain source_refs):
    - TP: from F5 primary_target level in signal metadata
    - SL: swing beyond PDA (from chain components)
    If TP/SL not available in signal metadata:
    - TP: use a default R:R (e.g. 2:1 from entry to SL)
    - SL: nearest swing high/low beyond entry (from detection data)
    Document which method was used.

    For skipped chains (hypothetical):
    - Use same TP/SL logic as if the signal had fired
    - This is approximate — that's fine for v1 classification

# ─────────────────────────────────────────────────────────────────────────────
# 4. RUNNING THE JOB
# ─────────────────────────────────────────────────────────────────────────────

execution:

  manual_run: |
    python scripts/dream_cycle_nightly.py --date 2026-03-19

    Produces:
      output/dream_cycle/2026-03-19_briefing.json
      output/dream_cycle/2026-03-19_briefing.md

  batch_run: |
    python scripts/dream_cycle_nightly.py --date-range 2026-03-17 2026-03-20

    Processes all 4 available days. Useful for backfill.

  future_cron: |
    After market close (~22:00 UTC weekdays):
    1. daily_detection_export.py runs (produces detection JSON)
    2. dream_cycle_nightly.py runs (produces morning briefing)
    3. Briefing available for morning review

    Cron setup is NOT in scope for this brief — manual run is v1.
    Cron can be added trivially once manual run is proven.

  telegram_delivery: |
    STRETCH GOAL: COO bot on M3 can serve the briefing on request.
    G messages @a8ra_COO_bot: "morning briefing"
    COO reads ~/dexter/output/dream_cycle/{latest}_briefing.md
    COO replies with summary.

    This requires detection output to be on M3 (git pull + pipeline run)
    OR COO reads from M4 via SSH. Either works.

    NOT blocking this brief — briefing files on M4 are the v1 deliverable.

# ─────────────────────────────────────────────────────────────────────────────
# 5. WHAT TO READ FROM DETECTION JSON
# ─────────────────────────────────────────────────────────────────────────────

detection_json_interface: |
  Read the actual JSON at ~/dexter/output/detections/2026-03-19.json.
  Key sections Dream Cycle v1 needs:

  1. diagnostic_signals[] — array of fired signals
     Each has: time, model_type, direction, chain_type, factors, shadow_mode
     May have: primary_target, pda_type, peak_window

  2. chains[] or composite chains in detections_by_primitive
     Each chain has: anchor MSS, components, direction, skip_reason (if skipped)
     The evaluator attaches skip_reason to chains that don't produce signals

  3. worldstate_snapshots[] — time-indexed WorldState list (from Track A Flag 1)
     Each has: timestamp, htf_phase, direction_permission, authority_tf, daily_direction

  4. Raw bar data — Dream Cycle loads separately via RiverBarAdapter
     (not embedded in detection JSON)

  CRITICAL: Read the actual JSON structure first. The schema above is
  approximate from the spec — the real file is the source of truth.
  Adapt the analyzer to whatever structure the JSON actually has.

# ─────────────────────────────────────────────────────────────────────────────
# 6. EXIT GATES
# ─────────────────────────────────────────────────────────────────────────────

exit_gates:

  gate_1_analyzer:
    criterion: "Analyzer processes a detection JSON and produces signal outcomes"
    test: "Run on 2026-03-19.json — 6 signals should each have outcome data"
    pass: "All 6 signals have price_after_30m, max_favorable, max_adverse, net_result"

  gate_2_skip_classification:
    criterion: "Skipped chains are classified as FALSE_REJECTION or CORRECT_REJECTION"
    test: "At least 5 skipped chains classified across the 4 available days"
    pass: "Each has skip_reason, hypothetical_result, classification"

  gate_3_worldstate_review:
    criterion: "WorldState transitions assessed against subsequent price action"
    test: "Mar 19 shows RANGE→EXPANSION transition — did market confirm?"
    pass: "Transition has confirmed: YES/NO/PARTIAL with evidence"

  gate_4_briefing_output:
    criterion: "Morning briefing produced in both JSON and Markdown"
    test: "Run on 2026-03-19 — briefing files exist and are readable"
    pass: |
      Markdown briefing is human-readable, contains all sections
      (header, signal outcomes, skip analysis, state review, daily summary).
      G could read this with coffee and understand what happened.

  gate_5_batch:
    criterion: "Batch mode works across multiple days"
    test: "Run on date-range Mar 17-20"
    pass: "4 briefing files produced. No crashes on days with 0 signals."

  gate_6_no_regression:
    criterion: "Existing test suite unaffected"
    test: "pytest ~/dexter/"
    pass: "1088+ passed, 0 new failures"

PASS_CONDITION: "Gates 1-6 all PASS"
FAIL_CONDITION: "Any gate FAIL → halt, report diagnosis"

# ─────────────────────────────────────────────────────────────────────────────
# 7. CONSTRAINTS
# ─────────────────────────────────────────────────────────────────────────────

constraints:

  DO_NOT_MODIFY:
    - "Any existing dexter producer, classifier, evaluator, or pipeline code"
    - "Detection JSON format (consume it, don't change it)"
    - "RiverBarAdapter (use it as-is, including staging extension from MIRROR)"
    - "SYNTHETIC_OLYA_METHOD_vLOCK.yaml"

  KEEP_SIMPLE:
    - "No ML models, no embeddings, no LLM calls in v1"
    - "Pure deterministic analysis: load data, compute deltas, classify, report"
    - "No database — file-based I/O (Karpathy pattern)"
    - "No DGX required — runs on M4 against local files"

  PRESERVE:
    - "INV-REPLAY-LIVE-PARITY (same data → same analysis)"
    - "Karpathy file-first pattern (all I/O on disk, auditable)"

# ─────────────────────────────────────────────────────────────────────────────
# 8. REPORT FORMAT
# ─────────────────────────────────────────────────────────────────────────────

report:
  format: DENSE
  structure: |
    BRIEF: S66.C.1
    STATUS: PASS/FAIL

    GATES:
      gate_1_analyzer: PASS/FAIL (signal count processed)
      gate_2_skip_classification: PASS/FAIL (skip count classified)
      gate_3_worldstate_review: PASS/FAIL
      gate_4_briefing_output: PASS/FAIL
      gate_5_batch: PASS/FAIL (days processed)
      gate_6_no_regression: PASS/FAIL (test count)

    SAMPLE_OUTPUT:
      best_finding: (paste top_finding from one briefing)
      false_rejections_found: N
      signal_win_rate: N/M

    FILES_CREATED: (list with line counts)

# ═══════════════════════════════════════════════════════════════════════════════
# END BRIEF
#
# Dream Cycle v1: the system learns by watching itself.
# Every day of operation, the briefing gets richer.
# The 998 rejections teach more than the 2 trades.
# ═══════════════════════════════════════════════════════════════════════════════
