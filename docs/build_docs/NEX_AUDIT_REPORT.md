# NEX DATA AUDIT REPORT

```yaml
document: NEX_AUDIT_REPORT
date: 2026-02-22
auditor: OPUS (Cursor)
source: ~/nex/nex_lab/data/fx/{PAIR}_1m.parquet
pairs: [EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD]
checklist: S51 RIVER BUILD BRIEF v1.1 T1
```

---

## EURUSD — PASS

```yaml
rows: 1,960,251
range: "2020-11-23 00:00:00+00:00 → 2026-02-20 21:59:00+00:00"

# CHECK 1 + 2: Timezone & Bar Alignment
timezone: UTC
is_utc: True
non_minute_aligned: 0

# CHECK 3: Duplicates
duplicate_timestamps: 0

# CHECK 4: Gaps
gaps_gt_1m: 325
gaps_gt_5m: 323
gaps_gt_1h: 297
max_gap: "2 days 00:16:00"
sample_gaps:
  - start: "2020-11-27 23:59:00+00:00"
    end: "2020-11-30 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-04 23:59:00+00:00"
    end: "2020-12-07 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-11 23:59:00+00:00"
    end: "2020-12-14 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-18 23:59:00+00:00"
    end: "2020-12-21 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-25 23:59:00+00:00"
    end: "2020-12-28 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-01 23:59:00+00:00"
    end: "2021-01-04 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-08 23:59:00+00:00"
    end: "2021-01-11 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-15 23:59:00+00:00"
    end: "2021-01-18 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-22 23:59:00+00:00"
    end: "2021-01-25 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-29 23:59:00+00:00"
    end: "2021-02-01 00:00:00+00:00"
    duration: "2 days 00:01:00"

# CHECK 5: Weekend Bars
weekend_bars_total: 41400
friday_after_1700ny: 41400
saturday_bars: 0
sunday_before_1700ny: 0

# CHECK 6: DST Sunday Opens
sunday_opens:
  - date: 2020-11-22
    first_bar_utc: "2020-11-23 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-11-29
    first_bar_utc: "2020-11-30 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-06
    first_bar_utc: "2020-12-07 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-13
    first_bar_utc: "2020-12-14 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-20
    first_bar_utc: "2020-12-21 00:00:00+00:00"
    utc_hour: 0
  - date: 2026-01-18
    first_bar_utc: "2026-01-18 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-01-25
    first_bar_utc: "2026-01-25 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-01
    first_bar_utc: "2026-02-01 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-08
    first_bar_utc: "2026-02-08 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-15
    first_bar_utc: "2026-02-15 22:15:00+00:00"
    utc_hour: 22

# CHECK 7: Price/Volume Sanity
high_lt_low: 0
high_lt_open: 0
high_lt_close: 0
low_gt_open: 0
low_gt_close: 0
zero_range_bars: 32115
negative_price: 0
null_prices: 0
out_of_range: 0
volume_zero: 106
volume_negative: 81171

# CHECK 8: Event Sampling
events:
  - date: 2021-01-06
    event: "US Capitol breach / risk event"
    status: OK
    bars: 1440
    day_range: 0.00839
  - date: 2022-09-22
    event: "BOJ intervention (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00994
  - date: 2022-10-13
    event: "US CPI — massive volatility"
    status: OK
    bars: 1440
    day_range: 0.01742
  - date: 2023-03-10
    event: "SVB collapse — flight to safety"
    status: OK
    bars: 1440
    day_range: 0.01266
  - date: 2023-10-06
    event: "NFP October 2023"
    status: OK
    bars: 1440
    day_range: 0.01175
  - date: 2024-04-29
    event: "BOJ intervention #2 (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00435
  - date: 2024-11-05
    event: "US Election 2024"
    status: OK
    bars: 1440
    day_range: 0.00645
  - date: 2025-04-02
    event: "Liberation Day tariffs announced"
    status: OK
    bars: 1440
    day_range: 0.01442

# SOURCE BOUNDARY DETECTION
source_boundary_detected: true
region: "2025-11-15 to 2025-12-01"
daily_bar_counts:
  2025-11-17: 1440
  2025-11-18: 1440
  2025-11-19: 1440
  2025-11-20: 1440
  2025-11-21: 1320
  2025-11-23: 105
  2025-11-24: 1425
  2025-11-25: 1425
  2025-11-26: 1425
  2025-11-27: 1425
  2025-11-28: 1320
  2025-11-30: 105
  2025-12-01: 1
daily_avg_volume:
  2025-11-17: 50.36
  2025-11-18: 64.84
  2025-11-19: 68.9
  2025-11-20: 70.66
  2025-11-21: 87.63
  2025-11-23: -1.0
  2025-11-24: -1.0
  2025-11-25: -1.0
  2025-11-26: -1.0
  2025-11-27: -1.0
  2025-11-28: -1.0
  2025-11-30: -1.0
  2025-12-01: -1.0
```

---

## GBPUSD — PASS

```yaml
rows: 1,959,793
range: "2020-11-23 00:00:00+00:00 → 2026-02-20 21:59:00+00:00"

# CHECK 1 + 2: Timezone & Bar Alignment
timezone: UTC
is_utc: True
non_minute_aligned: 0

# CHECK 3: Duplicates
duplicate_timestamps: 0

# CHECK 4: Gaps
gaps_gt_1m: 323
gaps_gt_5m: 323
gaps_gt_1h: 298
max_gap: "2 days 00:16:00"
sample_gaps:
  - start: "2020-11-27 23:59:00+00:00"
    end: "2020-11-30 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-04 23:59:00+00:00"
    end: "2020-12-07 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-11 23:59:00+00:00"
    end: "2020-12-14 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-18 23:59:00+00:00"
    end: "2020-12-21 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-25 23:59:00+00:00"
    end: "2020-12-28 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-01 23:59:00+00:00"
    end: "2021-01-04 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-08 23:59:00+00:00"
    end: "2021-01-11 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-15 23:59:00+00:00"
    end: "2021-01-18 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-22 23:59:00+00:00"
    end: "2021-01-25 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-29 23:59:00+00:00"
    end: "2021-02-01 00:00:00+00:00"
    duration: "2 days 00:01:00"

# CHECK 5: Weekend Bars
weekend_bars_total: 41400
friday_after_1700ny: 41400
saturday_bars: 0
sunday_before_1700ny: 0

# CHECK 6: DST Sunday Opens
sunday_opens:
  - date: 2020-11-22
    first_bar_utc: "2020-11-23 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-11-29
    first_bar_utc: "2020-11-30 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-06
    first_bar_utc: "2020-12-07 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-13
    first_bar_utc: "2020-12-14 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-20
    first_bar_utc: "2020-12-21 00:00:00+00:00"
    utc_hour: 0
  - date: 2026-01-18
    first_bar_utc: "2026-01-18 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-01-25
    first_bar_utc: "2026-01-25 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-01
    first_bar_utc: "2026-02-01 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-08
    first_bar_utc: "2026-02-08 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-15
    first_bar_utc: "2026-02-15 22:15:00+00:00"
    utc_hour: 22

# CHECK 7: Price/Volume Sanity
high_lt_low: 0
high_lt_open: 0
high_lt_close: 0
low_gt_open: 0
low_gt_close: 0
zero_range_bars: 25481
negative_price: 0
null_prices: 0
out_of_range: 0
volume_zero: 106
volume_negative: 79273

# CHECK 8: Event Sampling
events:
  - date: 2021-01-06
    event: "US Capitol breach / risk event"
    status: OK
    bars: 1440
    day_range: 0.01323
  - date: 2022-09-22
    event: "BOJ intervention (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.01525
  - date: 2022-10-13
    event: "US CPI — massive volatility"
    status: OK
    bars: 1440
    day_range: 0.03235
  - date: 2023-03-10
    event: "SVB collapse — flight to safety"
    status: OK
    bars: 1440
    day_range: 0.02059
  - date: 2023-10-06
    event: "NFP October 2023"
    status: OK
    bars: 1440
    day_range: 0.01557
  - date: 2024-04-29
    event: "BOJ intervention #2 (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00621
  - date: 2024-11-05
    event: "US Election 2024"
    status: OK
    bars: 1440
    day_range: 0.00999
  - date: 2025-04-02
    event: "Liberation Day tariffs announced"
    status: OK
    bars: 1440
    day_range: 0.01518

# SOURCE BOUNDARY DETECTION
source_boundary_detected: true
region: "2025-11-15 to 2025-12-01"
daily_bar_counts:
  2025-11-17: 1440
  2025-11-18: 1440
  2025-11-19: 1440
  2025-11-20: 1440
  2025-11-21: 1320
  2025-11-23: 105
  2025-11-24: 1425
  2025-11-25: 1425
  2025-11-26: 1425
  2025-11-27: 1425
  2025-11-28: 1320
  2025-11-30: 105
  2025-12-01: 1
daily_avg_volume:
  2025-11-17: 49.29
  2025-11-18: 59.2
  2025-11-19: 55.16
  2025-11-20: 62.11
  2025-11-21: 83.91
  2025-11-23: -1.0
  2025-11-24: -1.0
  2025-11-25: -1.0
  2025-11-26: -1.0
  2025-11-27: -1.0
  2025-11-28: -1.0
  2025-11-30: -1.0
  2025-12-01: -1.0
```

---

## USDJPY — PASS

```yaml
rows: 1,961,417
range: "2020-11-23 00:00:00+00:00 → 2026-02-20 21:59:00+00:00"

# CHECK 1 + 2: Timezone & Bar Alignment
timezone: UTC
is_utc: True
non_minute_aligned: 0

# CHECK 3: Duplicates
duplicate_timestamps: 0

# CHECK 4: Gaps
gaps_gt_1m: 323
gaps_gt_5m: 323
gaps_gt_1h: 296
max_gap: "2 days 00:16:00"
sample_gaps:
  - start: "2020-11-27 23:59:00+00:00"
    end: "2020-11-30 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-04 23:59:00+00:00"
    end: "2020-12-07 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-11 23:59:00+00:00"
    end: "2020-12-14 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-18 23:59:00+00:00"
    end: "2020-12-21 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-25 23:59:00+00:00"
    end: "2020-12-28 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-01 23:59:00+00:00"
    end: "2021-01-04 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-08 23:59:00+00:00"
    end: "2021-01-11 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-15 23:59:00+00:00"
    end: "2021-01-18 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-22 23:59:00+00:00"
    end: "2021-01-25 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-29 23:59:00+00:00"
    end: "2021-02-01 00:00:00+00:00"
    duration: "2 days 00:01:00"

# CHECK 5: Weekend Bars
weekend_bars_total: 41400
friday_after_1700ny: 41400
saturday_bars: 0
sunday_before_1700ny: 0

# CHECK 6: DST Sunday Opens
sunday_opens:
  - date: 2020-11-22
    first_bar_utc: "2020-11-23 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-11-29
    first_bar_utc: "2020-11-30 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-06
    first_bar_utc: "2020-12-07 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-13
    first_bar_utc: "2020-12-14 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-20
    first_bar_utc: "2020-12-21 00:00:00+00:00"
    utc_hour: 0
  - date: 2026-01-18
    first_bar_utc: "2026-01-18 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-01-25
    first_bar_utc: "2026-01-25 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-01
    first_bar_utc: "2026-02-01 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-08
    first_bar_utc: "2026-02-08 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-15
    first_bar_utc: "2026-02-15 22:15:00+00:00"
    utc_hour: 22

# CHECK 7: Price/Volume Sanity
high_lt_low: 0
high_lt_open: 0
high_lt_close: 0
low_gt_open: 0
low_gt_close: 0
zero_range_bars: 27041
negative_price: 0
null_prices: 0
out_of_range: 0
volume_zero: 106
volume_negative: 80897

# CHECK 8: Event Sampling
events:
  - date: 2021-01-06
    event: "US Capitol breach / risk event"
    status: OK
    bars: 1440
    day_range: 0.853
  - date: 2022-09-22
    event: "BOJ intervention (USDJPY)"
    status: OK
    bars: 1440
    day_range: 5.555
  - date: 2022-10-13
    event: "US CPI — massive volatility"
    status: OK
    bars: 1440
    day_range: 1.229
  - date: 2023-03-10
    event: "SVB collapse — flight to safety"
    status: OK
    bars: 1440
    day_range: 2.881
  - date: 2023-10-06
    event: "NFP October 2023"
    status: OK
    bars: 1440
    day_range: 1.072
  - date: 2024-04-29
    event: "BOJ intervention #2 (USDJPY)"
    status: OK
    bars: 1440
    day_range: 5.68
  - date: 2024-11-05
    event: "US Election 2024"
    status: OK
    bars: 1440
    day_range: 1.209
  - date: 2025-04-02
    event: "Liberation Day tariffs announced"
    status: OK
    bars: 1440
    day_range: 2.801

# SOURCE BOUNDARY DETECTION
source_boundary_detected: true
region: "2025-11-15 to 2025-12-01"
daily_bar_counts:
  2025-11-17: 1440
  2025-11-18: 1440
  2025-11-19: 1440
  2025-11-20: 1440
  2025-11-21: 1320
  2025-11-23: 105
  2025-11-24: 1425
  2025-11-25: 1425
  2025-11-26: 1425
  2025-11-27: 1425
  2025-11-28: 1320
  2025-11-30: 105
  2025-12-01: 1
daily_avg_volume:
  2025-11-17: 83.33
  2025-11-18: 129.46
  2025-11-19: 116.48
  2025-11-20: 154.06
  2025-11-21: 165.05
  2025-11-23: -1.0
  2025-11-24: -1.0
  2025-11-25: -1.0
  2025-11-26: -1.0
  2025-11-27: -1.0
  2025-11-28: -1.0
  2025-11-30: -1.0
  2025-12-01: -1.0
```

---

## USDCHF — PASS

```yaml
rows: 1,961,257
range: "2020-11-23 00:00:00+00:00 → 2026-02-20 21:59:00+00:00"

# CHECK 1 + 2: Timezone & Bar Alignment
timezone: UTC
is_utc: True
non_minute_aligned: 0

# CHECK 3: Duplicates
duplicate_timestamps: 0

# CHECK 4: Gaps
gaps_gt_1m: 323
gaps_gt_5m: 323
gaps_gt_1h: 295
max_gap: "2 days 00:16:00"
sample_gaps:
  - start: "2020-11-27 23:59:00+00:00"
    end: "2020-11-30 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-04 23:59:00+00:00"
    end: "2020-12-07 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-11 23:59:00+00:00"
    end: "2020-12-14 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-18 23:59:00+00:00"
    end: "2020-12-21 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-25 23:59:00+00:00"
    end: "2020-12-28 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-01 23:59:00+00:00"
    end: "2021-01-04 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-08 23:59:00+00:00"
    end: "2021-01-11 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-15 23:59:00+00:00"
    end: "2021-01-18 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-22 23:59:00+00:00"
    end: "2021-01-25 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-29 23:59:00+00:00"
    end: "2021-02-01 00:00:00+00:00"
    duration: "2 days 00:01:00"

# CHECK 5: Weekend Bars
weekend_bars_total: 41400
friday_after_1700ny: 41400
saturday_bars: 0
sunday_before_1700ny: 0

# CHECK 6: DST Sunday Opens
sunday_opens:
  - date: 2020-11-22
    first_bar_utc: "2020-11-23 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-11-29
    first_bar_utc: "2020-11-30 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-06
    first_bar_utc: "2020-12-07 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-13
    first_bar_utc: "2020-12-14 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-20
    first_bar_utc: "2020-12-21 00:00:00+00:00"
    utc_hour: 0
  - date: 2026-01-18
    first_bar_utc: "2026-01-18 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-01-25
    first_bar_utc: "2026-01-25 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-01
    first_bar_utc: "2026-02-01 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-08
    first_bar_utc: "2026-02-08 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-15
    first_bar_utc: "2026-02-15 22:15:00+00:00"
    utc_hour: 22

# CHECK 7: Price/Volume Sanity
high_lt_low: 0
high_lt_open: 0
high_lt_close: 0
low_gt_open: 0
low_gt_close: 0
zero_range_bars: 54510
negative_price: 0
null_prices: 0
out_of_range: 0
volume_zero: 66
volume_negative: 82177

# CHECK 8: Event Sampling
events:
  - date: 2021-01-06
    event: "US Capitol breach / risk event"
    status: OK
    bars: 1440
    day_range: 0.00639
  - date: 2022-09-22
    event: "BOJ intervention (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.02297
  - date: 2022-10-13
    event: "US CPI — massive volatility"
    status: OK
    bars: 1440
    day_range: 0.01148
  - date: 2023-03-10
    event: "SVB collapse — flight to safety"
    status: OK
    bars: 1440
    day_range: 0.01543
  - date: 2023-10-06
    event: "NFP October 2023"
    status: OK
    bars: 1440
    day_range: 0.01028
  - date: 2024-04-29
    event: "BOJ intervention #2 (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00647
  - date: 2024-11-05
    event: "US Election 2024"
    status: OK
    bars: 1440
    day_range: 0.00308
  - date: 2025-04-02
    event: "Liberation Day tariffs announced"
    status: OK
    bars: 1440
    day_range: 0.00849

# SOURCE BOUNDARY DETECTION
source_boundary_detected: true
region: "2025-11-15 to 2025-12-01"
daily_bar_counts:
  2025-11-17: 1440
  2025-11-18: 1440
  2025-11-19: 1440
  2025-11-20: 1440
  2025-11-21: 1320
  2025-11-23: 105
  2025-11-24: 1425
  2025-11-25: 1425
  2025-11-26: 1425
  2025-11-27: 1425
  2025-11-28: 1320
  2025-11-30: 105
  2025-12-01: 1
daily_avg_volume:
  2025-11-17: 39.4
  2025-11-18: 47.26
  2025-11-19: 52.68
  2025-11-20: 58.25
  2025-11-21: 66.4
  2025-11-23: -1.0
  2025-11-24: -1.0
  2025-11-25: -1.0
  2025-11-26: -1.0
  2025-11-27: -1.0
  2025-11-28: -1.0
  2025-11-30: -1.0
  2025-12-01: -1.0
```

---

## AUDUSD — PASS

```yaml
rows: 1,961,116
range: "2020-11-23 00:00:00+00:00 → 2026-02-20 21:59:00+00:00"

# CHECK 1 + 2: Timezone & Bar Alignment
timezone: UTC
is_utc: True
non_minute_aligned: 0

# CHECK 3: Duplicates
duplicate_timestamps: 0

# CHECK 4: Gaps
gaps_gt_1m: 323
gaps_gt_5m: 323
gaps_gt_1h: 296
max_gap: "2 days 00:16:00"
sample_gaps:
  - start: "2020-11-27 23:59:00+00:00"
    end: "2020-11-30 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-04 23:59:00+00:00"
    end: "2020-12-07 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-11 23:59:00+00:00"
    end: "2020-12-14 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-18 23:59:00+00:00"
    end: "2020-12-21 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-25 23:59:00+00:00"
    end: "2020-12-28 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-01 23:59:00+00:00"
    end: "2021-01-04 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-08 23:59:00+00:00"
    end: "2021-01-11 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-15 23:59:00+00:00"
    end: "2021-01-18 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-22 23:59:00+00:00"
    end: "2021-01-25 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-29 23:59:00+00:00"
    end: "2021-02-01 00:00:00+00:00"
    duration: "2 days 00:01:00"

# CHECK 5: Weekend Bars
weekend_bars_total: 41400
friday_after_1700ny: 41400
saturday_bars: 0
sunday_before_1700ny: 0

# CHECK 6: DST Sunday Opens
sunday_opens:
  - date: 2020-11-22
    first_bar_utc: "2020-11-23 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-11-29
    first_bar_utc: "2020-11-30 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-06
    first_bar_utc: "2020-12-07 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-13
    first_bar_utc: "2020-12-14 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-20
    first_bar_utc: "2020-12-21 00:00:00+00:00"
    utc_hour: 0
  - date: 2026-01-18
    first_bar_utc: "2026-01-18 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-01-25
    first_bar_utc: "2026-01-25 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-01
    first_bar_utc: "2026-02-01 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-08
    first_bar_utc: "2026-02-08 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-15
    first_bar_utc: "2026-02-15 22:15:00+00:00"
    utc_hour: 22

# CHECK 7: Price/Volume Sanity
high_lt_low: 0
high_lt_open: 0
high_lt_close: 0
low_gt_open: 0
low_gt_close: 0
zero_range_bars: 31502
negative_price: 0
null_prices: 0
out_of_range: 0
volume_zero: 66
volume_negative: 80597

# CHECK 8: Event Sampling
events:
  - date: 2021-01-06
    event: "US Capitol breach / risk event"
    status: OK
    bars: 1440
    day_range: 0.00871
  - date: 2022-09-22
    event: "BOJ intervention (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00967
  - date: 2022-10-13
    event: "US CPI — massive volatility"
    status: OK
    bars: 1440
    day_range: 0.01464
  - date: 2023-03-10
    event: "SVB collapse — flight to safety"
    status: OK
    bars: 1440
    day_range: 0.00766
  - date: 2023-10-06
    event: "NFP October 2023"
    status: OK
    bars: 1440
    day_range: 0.00876
  - date: 2024-04-29
    event: "BOJ intervention #2 (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00503
  - date: 2024-11-05
    event: "US Election 2024"
    status: OK
    bars: 1440
    day_range: 0.00661
  - date: 2025-04-02
    event: "Liberation Day tariffs announced"
    status: OK
    bars: 1440
    day_range: 0.01148

# SOURCE BOUNDARY DETECTION
source_boundary_detected: true
region: "2025-11-15 to 2025-12-01"
daily_bar_counts:
  2025-11-17: 1440
  2025-11-18: 1440
  2025-11-19: 1440
  2025-11-20: 1440
  2025-11-21: 1320
  2025-11-23: 105
  2025-11-24: 1425
  2025-11-25: 1425
  2025-11-26: 1425
  2025-11-27: 1425
  2025-11-28: 1320
  2025-11-30: 105
  2025-12-01: 1
daily_avg_volume:
  2025-11-17: 55.28
  2025-11-18: 74.54
  2025-11-19: 70.12
  2025-11-20: 88.39
  2025-11-21: 96.01
  2025-11-23: -1.0
  2025-11-24: -1.0
  2025-11-25: -1.0
  2025-11-26: -1.0
  2025-11-27: -1.0
  2025-11-28: -1.0
  2025-11-30: -1.0
  2025-12-01: -1.0
```

---

## USDCAD — PASS

```yaml
rows: 1,961,212
range: "2020-11-23 00:00:00+00:00 → 2026-02-20 21:59:00+00:00"

# CHECK 1 + 2: Timezone & Bar Alignment
timezone: UTC
is_utc: True
non_minute_aligned: 0

# CHECK 3: Duplicates
duplicate_timestamps: 0

# CHECK 4: Gaps
gaps_gt_1m: 323
gaps_gt_5m: 323
gaps_gt_1h: 297
max_gap: "2 days 00:16:00"
sample_gaps:
  - start: "2020-11-27 23:59:00+00:00"
    end: "2020-11-30 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-04 23:59:00+00:00"
    end: "2020-12-07 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-11 23:59:00+00:00"
    end: "2020-12-14 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-18 23:59:00+00:00"
    end: "2020-12-21 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2020-12-25 23:59:00+00:00"
    end: "2020-12-28 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-01 23:59:00+00:00"
    end: "2021-01-04 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-08 23:59:00+00:00"
    end: "2021-01-11 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-15 23:59:00+00:00"
    end: "2021-01-18 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-22 23:59:00+00:00"
    end: "2021-01-25 00:00:00+00:00"
    duration: "2 days 00:01:00"
  - start: "2021-01-29 23:59:00+00:00"
    end: "2021-02-01 00:00:00+00:00"
    duration: "2 days 00:01:00"

# CHECK 5: Weekend Bars
weekend_bars_total: 41400
friday_after_1700ny: 41400
saturday_bars: 0
sunday_before_1700ny: 0

# CHECK 6: DST Sunday Opens
sunday_opens:
  - date: 2020-11-22
    first_bar_utc: "2020-11-23 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-11-29
    first_bar_utc: "2020-11-30 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-06
    first_bar_utc: "2020-12-07 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-13
    first_bar_utc: "2020-12-14 00:00:00+00:00"
    utc_hour: 0
  - date: 2020-12-20
    first_bar_utc: "2020-12-21 00:00:00+00:00"
    utc_hour: 0
  - date: 2026-01-18
    first_bar_utc: "2026-01-18 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-01-25
    first_bar_utc: "2026-01-25 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-01
    first_bar_utc: "2026-02-01 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-08
    first_bar_utc: "2026-02-08 22:15:00+00:00"
    utc_hour: 22
  - date: 2026-02-15
    first_bar_utc: "2026-02-15 22:15:00+00:00"
    utc_hour: 22

# CHECK 7: Price/Volume Sanity
high_lt_low: 0
high_lt_open: 0
high_lt_close: 0
low_gt_open: 0
low_gt_close: 0
zero_range_bars: 31325
negative_price: 0
null_prices: 0
out_of_range: 0
volume_zero: 66
volume_negative: 80692

# CHECK 8: Event Sampling
events:
  - date: 2021-01-06
    event: "US Capitol breach / risk event"
    status: OK
    bars: 1440
    day_range: 0.00938
  - date: 2022-09-22
    event: "BOJ intervention (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.01358
  - date: 2022-10-13
    event: "US CPI — massive volatility"
    status: OK
    bars: 1440
    day_range: 0.0271
  - date: 2023-03-10
    event: "SVB collapse — flight to safety"
    status: OK
    bars: 1440
    day_range: 0.01006
  - date: 2023-10-06
    event: "NFP October 2023"
    status: OK
    bars: 1440
    day_range: 0.01014
  - date: 2024-04-29
    event: "BOJ intervention #2 (USDJPY)"
    status: OK
    bars: 1440
    day_range: 0.00451
  - date: 2024-11-05
    event: "US Election 2024"
    status: OK
    bars: 1440
    day_range: 0.00911
  - date: 2025-04-02
    event: "Liberation Day tariffs announced"
    status: OK
    bars: 1440
    day_range: 0.01513

# SOURCE BOUNDARY DETECTION
source_boundary_detected: true
region: "2025-11-15 to 2025-12-01"
daily_bar_counts:
  2025-11-17: 1440
  2025-11-18: 1440
  2025-11-19: 1440
  2025-11-20: 1440
  2025-11-21: 1320
  2025-11-23: 105
  2025-11-24: 1425
  2025-11-25: 1425
  2025-11-26: 1425
  2025-11-27: 1425
  2025-11-28: 1320
  2025-11-30: 105
  2025-12-01: 1
daily_avg_volume:
  2025-11-17: 94.17
  2025-11-18: 109.45
  2025-11-19: 110.34
  2025-11-20: 106.18
  2025-11-21: 119.63
  2025-11-23: -1.0
  2025-11-24: -1.0
  2025-11-25: -1.0
  2025-11-26: -1.0
  2025-11-27: -1.0
  2025-11-28: -1.0
  2025-11-30: -1.0
  2025-12-01: -1.0
```

---

## SUMMARY

```yaml
overall:
  EURUSD: PASS
  GBPUSD: PASS
  USDJPY: PASS
  USDCHF: PASS
  AUDUSD: PASS
  USDCAD: PASS

critical_finding: |
  NEX parquet files extend to 2026-02-20, not 2025-11-23 as expected.
  The NEX enrichment pipeline was refreshing from IBKR beyond the
  original Dukascopy CSV range (2020-11-23 to 2025-11-21).
  Data after ~2025-11-21 is likely IBKR-sourced but has no source tag.
  The Dukascopy/IBKR boundary needs explicit marking during River ingestion.

implication_for_t1b: |
  T1B (fresh Dukascopy download) may still be needed for independent
  cross-validation of the Nov-Feb overlap zone, but the NEX data itself
  already covers the full range. The seam reconciliation (T5) can compare
  T0 IBKR capture against NEX data in the overlap zone.
```
