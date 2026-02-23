# RIVER SEAM REPORT

```yaml
document: RIVER_SEAM_REPORT
date: 2026-02-22
auditor: OPUS (Cursor)
method: Three-way cross-validation
checks:
  1: Dukascopy→IBKR source boundary (Nov 21/22 2025)
  2: NEX-IBKR vs T0-IBKR overlap (Jan 18 → Feb 20 2026)
  3: Full River continuity
```

---

## AUDUSD — PASS

```yaml
source_boundary:
  status: PASS
  duka_last_bar: 2025-11-21 21:59:00+00:00
  ibkr_first_bar: 2025-11-23 22:15:00+00:00
  duka_last_close: 0.64539
  ibkr_first_open: 0.64575
  price_gap: 0.00036
  gap_pips: 3.6
  duka_volume_avg: 90.96
  ibkr_volume_avg: -1.0
  note: Weekend gap expected between Friday close and Sunday open
ibkr_overlap:
  status: PASS
  matched_bars: 25779
  nex_bars: 32605
  t0_bars: 27485
  exact_match_pct: 99.3
  within_01_pip_pct: 99.4
  close_median_pips: 0.0
  close_p99_pips: 0.0
  close_max_pips: 4.05
  high_max_pips: 3.4
  low_max_pips: 3.5
  outliers_gt_1pip: 42
  overlap_start: 2026-01-18 22:15:00+00:00
  overlap_end: 2026-02-20 21:59:00+00:00
  note: Same-vendor comparison. 99%+ exact match expected. Outliers at high-vol moments.
continuity:
  status: PASS
  total_bars: 1955996
  first_bar: 2020-11-23 08:00:00+08:00
  last_bar: 2026-02-21 05:59:00+08:00
  sources: 2
```

---

## EURUSD — PASS

```yaml
source_boundary:
  status: PASS
  duka_last_bar: 2025-11-21 21:59:00+00:00
  ibkr_first_bar: 2025-11-23 22:15:00+00:00
  duka_last_close: 1.15155
  ibkr_first_open: 1.15138
  price_gap: 0.00017
  gap_pips: 1.7
  duka_volume_avg: 83.04
  ibkr_volume_avg: -1.0
  note: Weekend gap expected between Friday close and Sunday open
ibkr_overlap:
  status: PASS
  matched_bars: 27582
  nex_bars: 31309
  t0_bars: 30064
  exact_match_pct: 99.3
  within_01_pip_pct: 99.9
  close_median_pips: 0.0
  close_p99_pips: 0.0
  close_max_pips: 7.55
  high_max_pips: 9.3
  low_max_pips: 2.6
  outliers_gt_1pip: 14
  overlap_start: 2026-01-18 22:15:00+00:00
  overlap_end: 2026-02-20 21:59:00+00:00
  note: Same-vendor comparison. 99%+ exact match expected. Outliers at high-vol moments.
continuity:
  status: PASS
  total_bars: 1959006
  first_bar: 2020-11-23 08:00:00+08:00
  last_bar: 2026-02-21 05:59:00+08:00
  sources: 2
```

---

## GBPUSD — PASS

```yaml
source_boundary:
  status: PASS
  duka_last_bar: 2025-11-21 21:59:00+00:00
  ibkr_first_bar: 2025-11-23 22:15:00+00:00
  duka_last_close: 1.30931
  ibkr_first_open: 1.31015
  price_gap: 0.00084
  gap_pips: 8.4
  duka_volume_avg: 78.87
  ibkr_volume_avg: -1.0
  note: Weekend gap expected between Friday close and Sunday open
ibkr_overlap:
  status: PASS
  matched_bars: 29082
  nex_bars: 31360
  t0_bars: 31529
  exact_match_pct: 98.5
  within_01_pip_pct: 99.3
  close_median_pips: 0.0
  close_p99_pips: 0.05
  close_max_pips: 8.7
  high_max_pips: 7.5
  low_max_pips: 4.65
  outliers_gt_1pip: 64
  overlap_start: 2026-01-18 22:15:00+00:00
  overlap_end: 2026-02-20 21:59:00+00:00
  note: Same-vendor comparison. 99%+ exact match expected. Outliers at high-vol moments.
continuity:
  status: PASS
  total_bars: 1959962
  first_bar: 2020-11-23 08:00:00+08:00
  last_bar: 2026-02-21 05:59:00+08:00
  sources: 2
```

---

## USDCAD — PASS

```yaml
source_boundary:
  status: PASS
  duka_last_bar: 2025-11-21 21:59:00+00:00
  ibkr_first_bar: 2025-11-23 22:15:00+00:00
  duka_last_close: 1.41001
  ibkr_first_open: 1.40996
  price_gap: 5e-05
  gap_pips: 0.5
  duka_volume_avg: 113.23
  ibkr_volume_avg: -1.0
  note: Weekend gap expected between Friday close and Sunday open
ibkr_overlap:
  status: PASS
  matched_bars: 29922
  nex_bars: 32713
  t0_bars: 31569
  exact_match_pct: 98.5
  within_01_pip_pct: 99.2
  close_median_pips: 0.0
  close_p99_pips: 0.05
  close_max_pips: 4.65
  high_max_pips: 5.2
  low_max_pips: 2.75
  outliers_gt_1pip: 46
  overlap_start: 2026-01-18 22:15:00+00:00
  overlap_end: 2026-02-20 21:59:00+00:00
  note: Same-vendor comparison. 99%+ exact match expected. Outliers at high-vol moments.
continuity:
  status: PASS
  total_bars: 1960068
  first_bar: 2020-11-23 08:00:00+08:00
  last_bar: 2026-02-21 05:59:00+08:00
  sources: 2
```

---

## USDCHF — PASS

```yaml
source_boundary:
  status: PASS
  duka_last_bar: 2025-11-21 21:59:00+00:00
  ibkr_first_bar: 2025-11-23 22:15:00+00:00
  duka_last_close: 0.80831
  ibkr_first_open: 0.80835
  price_gap: 4e-05
  gap_pips: 0.4
  duka_volume_avg: 63.39
  ibkr_volume_avg: -1.0
  note: Weekend gap expected between Friday close and Sunday open
ibkr_overlap:
  status: PASS
  matched_bars: 29582
  nex_bars: 32302
  t0_bars: 31593
  exact_match_pct: 99.0
  within_01_pip_pct: 99.3
  close_median_pips: 0.0
  close_p99_pips: 0.0
  close_max_pips: 7.85
  high_max_pips: 11.85
  low_max_pips: 5.4
  outliers_gt_1pip: 55
  overlap_start: 2026-01-18 22:15:00+00:00
  overlap_end: 2026-02-20 21:59:00+00:00
  note: Same-vendor comparison. 99%+ exact match expected. Outliers at high-vol moments.
continuity:
  status: PASS
  total_bars: 1960548
  first_bar: 2020-11-23 08:00:00+08:00
  last_bar: 2026-02-21 05:59:00+08:00
  sources: 2
```

---

## USDJPY — PASS

```yaml
source_boundary:
  status: PASS
  duka_last_bar: 2025-11-21 21:59:00+00:00
  ibkr_first_bar: 2025-11-23 22:15:00+00:00
  duka_last_close: 156.378
  ibkr_first_open: 156.455
  price_gap: 0.077
  gap_pips: 7.7
  duka_volume_avg: 157.09
  ibkr_volume_avg: -1.0
  note: Weekend gap expected between Friday close and Sunday open
ibkr_overlap:
  status: PASS
  matched_bars: 29835
  nex_bars: 32543
  t0_bars: 31625
  exact_match_pct: 98.8
  within_01_pip_pct: 99.1
  close_median_pips: 0.0
  close_p99_pips: 0.05
  close_max_pips: 16.65
  high_max_pips: 9.85
  low_max_pips: 16.5
  outliers_gt_1pip: 139
  overlap_start: 2026-01-18 22:15:00+00:00
  overlap_end: 2026-02-20 21:59:00+00:00
  note: Same-vendor comparison. 99%+ exact match expected. Outliers at high-vol moments.
continuity:
  status: PASS
  total_bars: 1960499
  first_bar: 2020-11-23 08:00:00+08:00
  last_bar: 2026-02-21 05:59:00+08:00
  sources: 2
```

---

## SUMMARY

```yaml
overall: PASS
  AUDUSD: PASS
  EURUSD: PASS
  GBPUSD: PASS
  USDCAD: PASS
  USDCHF: PASS
  USDJPY: PASS

attestation_ready: true
next_step: G signs RIVER_SEAM_ATTESTATION
```
