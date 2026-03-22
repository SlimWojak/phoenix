# ═══════════════════════════════════════════════════════════════════════════════
# vLOCK AMENDMENT: KILL_ZONE_GATE_v2
# Date: 2026-03-22
# Source: Olya (CSO) live clarification with G and CTO present
# Status: LOCKED — Olya confirmed in session
# Amends: OTE.kill_zone_gate + NY_WINDOWS sections in SYNTHETIC_OLYA_METHOD_vLOCK.yaml
# ═══════════════════════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────────────────────
# WHAT CHANGED AND WHY
# ─────────────────────────────────────────────────────────────────────────────

amendment_context: |
  S66 Track A regression revealed 4 trades (007, 008, 010, 011) with correct
  WorldState and correct direction that were SKIPPED because entry time fell
  outside the 08:00-09:00 NYOKZ refined window.

  Olya clarified (2026-03-22, live session):
  1. The 08:00-09:00 / 03:00-04:00 windows are PEAK QUALITY zones, not gates
  2. The full session (LOKZ 02:00-05:00, NYOKZ 07:00-10:00) is valid for trading
  3. Her process: confluence forms DURING session, entry may follow AFTER session
  4. Grace window: 30 minutes after session close for entry execution
  5. If entry doesn't present by grace deadline, setup is stale — no entry

  This is a Delta Principle correction: the original vLOCK encoding was
  more restrictive than Olya's actual process. Ground truth trades proved it.

# ─────────────────────────────────────────────────────────────────────────────
# AMENDMENT: OTE.kill_zone_gate (REPLACES existing section)
# ─────────────────────────────────────────────────────────────────────────────

kill_zone_gate_v2:

  rule: |
    TWO-PHASE GATE: confluence must form inside session, entry permitted
    during session or within grace window after session close.

    Phase 1 — CONFLUENCE (must occur INSIDE session):
      Chain anchor components (MSS, sweep, displacement) must fire
      within the active kill zone session window.
      Gate check: chain.mss_time is inside session → confluence_valid = true
      If MSS is absent, use chain.sweep_time or chain.displacement_time.
      At least one structural anchor must be inside the session.

    Phase 2 — ENTRY (session OR grace window):
      Once confluence is established, entry is permitted until
      session_end + 30 minutes (grace window for retrace into PDA).
      Gate check: signal.time <= session_end + 30min → entry_valid = true
      If entry has not presented by grace deadline → setup is STALE, skip.

    Signals inside peak windows receive quality tag (not a gate):
      peak_window: true if signal.time is inside peak reversal window
      This is informational — higher conviction, not a filter.

  sessions:
    LOKZ:
      confluence_window: "02:00-05:00 NY"
      entry_deadline: "05:30 NY"
      peak_reversal: "03:00-04:00 NY"
    NYOKZ:
      confluence_window: "07:00-10:00 NY"
      entry_deadline: "10:30 NY"
      peak_reversal: "08:00-09:00 NY"

  grace_window:
    duration: "30 minutes after session close"
    rationale: |
      Olya's process: during the session she watches patterns form
      (sweep, MSS, displacement, FVG). Once confluence is present,
      she waits for price to retrace into PDA for entry. This retrace
      can take 15-45 minutes. If it hasn't come by 30 minutes post
      session, the opportunity is considered stale.
    LOKZ_deadline: "05:30 NY"
    NYOKZ_deadline: "10:30 NY"

  peak_window_quality_tag:
    what: "Signals where entry occurs during peak reversal window"
    LOKZ_peak: "03:00-04:00 NY"
    NYOKZ_peak: "08:00-09:00 NY"
    output: "peak_window: true/false on DIAGNOSTIC_SIGNAL"
    usage: |
      Informational quality tag. NOT a gate. NOT a filter.
      peak_window=true means the strongest reversal energy window.
      peak_window=false means valid setup, normal conviction.
      Future: Dream Cycle can analyze hit rate by peak_window flag.

  window_b:
    time: "10:00-11:00 NY"
    status: "EXCLUDED — not part of Olya's process (unchanged from vLOCK)"
    note: |
      The NYOKZ grace window extends to 10:30, which overlaps with
      Window B start. This is NOT activating Window B as a strategy.
      The 10:00-10:30 overlap is the grace period for NYOKZ setups
      whose confluence formed during 07:00-10:00. New confluence
      forming after 10:00 is NOT valid under this gate.

  status: "LOCKED — Olya confirmed 2026-03-22"
  provenance: |
    Live session with Olya, G, CTO. Triggered by S66 Track A regression
    showing 4 valid trades skipped by overly restrictive time gate.
    Olya confirmed: sessions are trading windows, peak times are quality
    markers, 30-minute grace for entry after session close.
    Trades 007, 008, 010, 011 validated this interpretation.

# ─────────────────────────────────────────────────────────────────────────────
# AMENDMENT: NY_WINDOWS (REPLACES existing section)
# ─────────────────────────────────────────────────────────────────────────────

ny_windows_v2:

  olya_confirmed_windows:
    lokz:
      session: "02:00-05:00 NY — full session valid for confluence + entry"
      peak_reversal: "03:00-04:00 NY — strongest reversals, HOD/LOD often forms"
      grace_deadline: "05:30 NY — entry must present by this time"
    nyokz:
      session: "07:00-10:00 NY — full session valid for confluence + entry"
      peak_reversal: "08:00-09:00 NY — strongest reversals, HOD/LOD often forms"
      grace_deadline: "10:30 NY — entry must present by this time"
    window_b:
      time: "10:00-11:00 NY"
      status: "EXCLUDED — not part of Olya's process"

  olya_note_updated: |
    Strong reversals happen during LOKZ 03:00-04:00 and NYOKZ 08:00-09:00.
    These are the peak reversal zones where HOD/LOD typically forms.
    But valid setups occur across the full session (02:00-05:00 / 07:00-10:00).

    Her process: during the session, watch for confluence (sweep, MSS,
    displacement). Once confluence is present, wait for retrace entry.
    Entry can come during or up to 30 minutes after session close.
    If entry doesn't present by the grace deadline, the setup is stale.

    Signals in peak windows are higher conviction but the system should
    NOT restrict entries to these windows. Tag them as peak_window quality.

    Window B (10:00-11:00) remains excluded — different pattern (continuation)
    that is not part of her trading process.

  status: "LOCKED — Olya confirmed 2026-03-22 (amends 2026-03-13 lock)"

# ─────────────────────────────────────────────────────────────────────────────
# IMPLEMENTATION NOTES FOR OPUS
# ─────────────────────────────────────────────────────────────────────────────

implementation:

  evaluator_change:
    file: "dexter/checklist/evaluator.py"
    current: "signal.time must be inside kill zone (08:00-09:00 / 03:00-04:00)"
    new: |
      1. chain.mss_time (or anchor event) must be inside full session
         (LOKZ 02:00-05:00, NYOKZ 07:00-10:00)
      2. signal.time must be <= session_end + 30min
         (LOKZ <= 05:30, NYOKZ <= 10:30)
      3. If both pass → signal emits
    note: "The 09:01 cutoff in evaluator.py line 93 is the change target"

  signal_builder_addition:
    file: "dexter/checklist/signal_builder.py"
    add: "peak_window: true/false field to DIAGNOSTIC_SIGNAL"
    logic: "signal.time inside 03:00-04:00 or 08:00-09:00 → true"

  session_boundary_data:
    file: "dexter/bead_field/producers/session_boundary.py (existing)"
    verify: "Session end times available for the two-phase gate check"

  tests:
    - "entry at 09:30 with MSS at 08:45 → PASS (confluence in session, entry in session)"
    - "entry at 10:15 with MSS at 09:50 → PASS (confluence in session, entry in grace)"
    - "entry at 10:45 with MSS at 09:50 → SKIP (entry past grace deadline)"
    - "entry at 09:00 with MSS at 07:30 → PASS + peak_window=true"
    - "entry at 08:30 with MSS at 10:05 → SKIP (confluence outside session)"

# ═══════════════════════════════════════════════════════════════════════════════
# END AMENDMENT
# ═══════════════════════════════════════════════════════════════════════════════
