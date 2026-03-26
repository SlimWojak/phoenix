# OPUS M3 — TWO PARALLEL TASKS
## Date: 2026-03-26 | Owner: CTO

---

## TASK A: CANON DOC REFRESH (1-2 hours)

### What
Update the three canonical documents that orientate fresh CTO/advisor sessions.
These docs are stale — they don't reflect the work from Mar 25-26.

### Documents to Update

**1. SYSTEM_MANIFEST (a8ra_SYSTEM_MANIFEST_v1_0.md)**

Add DELTA entry covering:
```yaml
- date: 2026-03-25
  office: CTO_SESSION + OPUS_FACTORY
  change: |
    MIRROR polish + canonical pipeline build.
    
    PIPELINE:
    - Export bug fixed: FVG/OB silently dropped due to reasoning_trace key mismatch
      (bar_time vs detect_time/ob_time). 2-line fix in daily_detection_export.py.
    - claim_writer.py BUILT: 265 lines, 34 tests. End-state module.
      ClaimSpec → signed CLAIM beads (PQC+ECDSA, bi-temporal, chain-linked).
    - Pipeline dual-write: JSON + beads from same producer run.
    - eurusd_claims.db created: SEPARATE DB for analytical CLAIMs.
    - 5-year historical backfill: 564,471 beads (563,187 CLAIM + 1,284 SIGNAL).
      Jan 2021 → Mar 2026. One unbroken chain. Zero anomalies.
    - Bead field: analytically void → analytically rich.
    
    MIRROR:
    - Architectural audit: complete state machine X-ray (state inventory,
      conflict map, 11 issues found including 3 P0 crashes).
    - Root cause: 4 competing date mechanisms, sequential/real timestamp mismatch.
    - Phase A surgical fixes: 6 fixes (HTF scroll, sequential timestamps,
      feed navigation, mode switch reset, timezone docs, WS subscribe).
    - Phase B setView() refactor: unified state management architecture.
    - MIRROR now reliable real-time observation surface.
    
    VERIFICATION (Mar 26):
    - 7-angle bead field integrity verification (advisor-enriched).
    - Angle 7 (raw bar ground truth): 899/900 correct against River candles.
    - Angle 4 (vLOCK compliance): 5/5 core rules, zero violations.
    - Angle 3 (statistical consistency): zero anomalies across 63 months.
    - Angle 5 (temporal integrity): 5/5 bi-temporal tests perfect.
    - Named findings: SWEEP_PRODUCER_NEAR_NONFUNCTIONAL (70/5yr),
      WARMUP_BEADS (9,457 in unreliable window), SIGNAL_CHAIN_EMPTY.
    - Permanent verification suite: 6 scripts at ~/dexter/scripts/verification/
    - BEAD_FIELD_CALIBRATION_REPORT.md produced.
    
    Dexter tests: 1088 + 34 claim_writer = 1122.
    New modules: claim_writer.py, 6 verification scripts.
    New DB: eurusd_claims.db (4.4GB, 564K beads).
```

Update the Dexter section to reflect:
- claim_writer and dual-write pipeline
- eurusd_claims.db as new bead store
- Verification suite existence
- MIRROR status upgrade

Update M3 services list to reflect current operational state.

**2. SPRINT_ROADMAP (SPRINT_ROADMAP.md)**

Add new sprint entry:
```yaml
S67: CANONICAL_PIPELINE_AND_VERIFICATION — COMPLETE ✅ (2026-03-26)
  status: COMPLETE
  dates: 2026-03-25 to 2026-03-26
  theme: "End-state pipeline, bead field population, integrity verification"
  tracks:
    pipeline: "Export bug fix + claim_writer + dual-write + 5yr backfill"
    mirror: "Architectural audit + Phase A/B fixes + setView() refactor"
    verification: "7-angle integrity battery, advisor-enriched (GPT+OWL+BOAR)"
  deliverables:
    - "claim_writer.py (265 lines, 34 tests — end-state ClaimSpec → CLAIM bead)"
    - "eurusd_claims.db (4.4GB, 564,471 beads — Jan 2021 → Mar 2026)"
    - "Pipeline dual-write (JSON + beads from same producer run)"
    - "MIRROR setView() refactor (unified state management)"
    - "BEAD_FIELD_CALIBRATION_REPORT.md (7 angles, all PASS or documented)"
    - "6 permanent verification scripts (~/dexter/scripts/verification/)"
  findings:
    - "SWEEP_PRODUCER_NEAR_NONFUNCTIONAL: 70 beads / 5 years"
    - "WARMUP_BEADS: 9,457 in first 30 days (ATR unreliable)"
    - "SIGNAL_CHAIN_EMPTY: provenance links not populated"
  tests: "1122 dexter (was 1088), 389 verification suite"
```

Update the FORWARD PLAN section:
```yaml
NEXT_PRIORITIES:
  observation_week: "Olya validating via MIRROR (live, in progress)"
  sweep_investigation: "Forensic audit of LiquiditySweepProducer (see Task B)"
  bridge_daemon: "E.1 — governance events → bead field (deferred from S66)"
  graduation_metrics: "Tracking shadow mode toward graduation criteria"
  canon_architecture: "Claude Channels + agentic layer rethink (design phase)"
```

**3. UNIFIED_ROADMAP (UNIFIED_ROADMAP_v1.md)**

Add S67 entry matching sprint roadmap format.
Update HARDWARE STATUS if any changes.
Update CURRENT STATE section.

### Constraints
- Keep entries DENSE (M2M format, no prose)
- Follow existing document patterns exactly
- Preserve all existing content, append only
- Commit to git after updating all three

---

## TASK B: SWEEP PRODUCER FORENSIC INVESTIGATION

### Mission
Determine WHY LiquiditySweepProducer generates only 70 beads across 5 years
when the expected count is ~500-1000/year.

This is a DIAGNOSTIC task, not a fix task. Report findings.

### Background
- vLOCK defines liquidity sweep with a curated level pool architecture
- Sweep depends on upstream levels: SESSION_BOUNDARY, PDH_PDL, equal H/L, HTF promoted swings
- detect.py (research_accelerator) is the reference oracle
- Dexter producers were built to match detect.py (S64 Gate 4)
- S65 flagged "sweep level pool incomplete"
- Verification Angle 1: ALL sweep steps MISSED in annotated trades

### Investigation Steps

**Step 1: Oracle sweep count comparison**

Pick 5 dates where Olya annotated sweeps in her trades:
```
2025-10-01 (trade_001)
2025-12-12 (trade_005)
2026-02-04 (trade_014)
2026-03-12 (trade_013)
2025-11-12 (trade_010)
```

For each date:
```python
# Run detect.py
from ra.detectors.detect import detect_all
oracle_result = detect_all(bars, date)
oracle_sweep_count = count(oracle_result, type='LIQUIDITY_SWEEP')

# Query bead field
bead_sweep_count = query(claims_db, date, type='LIQUIDITY_SWEEP')

# Compare
print(f"{date}: oracle={oracle_sweep_count}, beads={bead_sweep_count}")
```

**This immediately answers: is it Scenario A (both sparse) or Scenario B (oracle finds more)?**

**Step 2: Trace the level pool**

Examine `LiquiditySweepProducer` in `dexter/dexter/bead_field/producers/`:
```
1. What levels does it receive as input? (curated pool)
2. How is the curated pool constructed?
3. What level sources feed it?
   - SESSION_BOUNDARY highs/lows
   - PDH_PDL (previous day high/low)
   - Equal highs/lows
   - HTF promoted swings
4. Are ALL vLOCK-specified level sources actually implemented?
5. Is the pool passed correctly to the sweep detector?
```

**Step 3: Trace the detection logic**

For one of the 5 dates where Olya marked a sweep:
```
1. What levels were in the curated pool for that session?
2. Did price actually breach any of them?
3. If yes, why didn't the producer fire?
4. Compare against detect.py's sweep logic for the same date
5. Identify the specific divergence point
```

**Step 4: Compare detect.py sweep vs producer sweep**

Side-by-side code diff:
```
- detect.py sweep detection function
- LiquiditySweepProducer.detect()

Specifically compare:
- Level pool construction
- Breach detection logic
- Return window (how many bars after breach to confirm sweep)
- Direction logic
- Filtering criteria
```

### Output

```yaml
SWEEP_FORENSIC_REPORT:
  verdict: "SCENARIO_A | SCENARIO_B | SCENARIO_C"
  oracle_counts: "{date: oracle_count, bead_count} for 5 dates"
  root_cause: "specific finding"
  level_pool_analysis:
    sources_implemented: [list]
    sources_missing: [list]
    levels_per_day: "average count"
  code_divergence: "specific lines/logic that differ"
  recommendation: "fix producer | expand pool | consult Olya"
```

### Constraints
- Do NOT modify any producer code
- Do NOT modify detect.py
- This is forensic analysis only
- Report findings for CTO synthesis
