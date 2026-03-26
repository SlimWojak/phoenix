# TASK B ADDENDUM — CALIBRATION CTO HYPOTHESIS
## Source: CTO Claude who led the 2-week calibration exercise (S64 Track D)
## Status: HYPOTHESIS — verify, don't assume

---

## CONTEXT

We polled the CTO instance that ran the original sweep calibration with Olya.
That session had deep context on detect.py's sweep implementation, the curated
level pool architecture, and Olya's specific feedback on sweep sensitivity.

The calibration CTO's diagnosis is below. **Treat this as a hypothesis to
verify or refute, not as a conclusion.** Complete your investigation steps
as briefed — but use this to avoid chasing dead ends if the evidence aligns.

---

## HYPOTHESIS: POOL STARVATION

The calibration CTO believes the sweep producer logic is likely CORRECT
(it passed calibration on detect.py). The root cause is that the curated
level pool feeding the Dexter sweep producer is dramatically underpopulated
compared to what detect.py's pool contained during calibration.

**Design target:** 15-20 active levels per day feeding the sweep detector.
**Likely reality:** 1-3 levels per day (explaining 70 sweeps / 5 years).

### Specific Pool Gaps Identified

```yaml
EQH_EQL_NOT_IMPLEMENTED:
  status: "DEFERRED — listed as stub in codebase"
  file: "research_accelerator/src/ra/detectors/equal_hl.py (stub)"
  impact: |
    Equal highs and equal lows are the richest pool source.
    These are the levels Olya most frequently marks as sweepable.
    Without them, the pool is missing its primary fuel.

SESSION_LIQUIDITY_GAPS:
  status: "Partially implemented"
  finding: |
    Calibration Investigations 3+4 found Asia boxes and Pre-NY
    levels missing from the pool on certain days. These were
    SESSION_BOUNDARY detector issues. May not have been fully
    resolved in the port from detect.py to Dexter producers.

PROMOTED_SWINGS_NOT_FEEDING:
  status: "Unknown — needs verification"
  question: "Are HTF swing points being promoted into the sweep pool?"

SWEEP_EVENT_LEVELS_DISABLED:
  status: "Shipped disabled by default"
  finding: "enabled: False in cascade.py"
  context: |
    Recursive sweep-of-sweep chain. Olya confirmed she trades
    this pattern. Deliberately disabled at ship time.
    Needs activation decision.
```

### Calibration Context

```yaml
calibration_sweep_rates: |
  On the 5-day calibration week (Jan 8-12 2024), detect.py produced
  roughly 5 base sweeps on 15m and 27 delayed sweeps on 15m per week.
  This is dramatically higher than the 14/year bead field rate.
  "Something broke in the port."

wick_threshold: "Locked at 0.40 (rejection_wick_pct), Olya confirmed"

olya_feedback: |
  Olya did NOT flag sweeps as too quiet during calibration.
  But calibration was on a single week with detect.py, not
  on the full bead field. The sparsity is a port/pool issue.

ltf_pool_constraint: |
  "LTF must not generate own liquidity pools" — locked Mar 12
  with Olya confirmation. This is CORRECT and should be preserved.
  It is NOT the cause of the sparsity.
```

### Suggested Investigation Reframe

If your Step 1 (oracle sweep count comparison) confirms that detect.py
finds significantly more sweeps than the bead field on the same dates,
the hypothesis is confirmed and you can focus your remaining steps on:

1. **Count pool levels per day** in Dexter vs detect.py
2. **Identify which pool sources are missing** (EQH/EQL, session gaps, promoted swings, cascade)
3. **Quantify the impact** of each missing source

If Step 1 shows detect.py is ALSO sparse on these dates, the hypothesis
is wrong and the issue is in the methodology definition (needs Olya input).

---

## CONSTRAINTS (unchanged)

- This addendum is a HYPOTHESIS, not a directive
- Complete all investigation steps as briefed
- If evidence contradicts the hypothesis, report that
- Do NOT modify any code
- Document everything for CTO synthesis
