# Grandfathered Files (>300 Lines)

**Policy:** S28 code is PROVEN (tests pass, chaos validated). Refactoring proven code introduces risk before production. New code in S30+ must comply with ≤300 line limit.

**Cleanup Target:** Post-S34 (see CARPARK)

---

## Grandfathered Files (as of 2026-01-23)

| File | Lines | Reason |
|------|-------|--------|
| tests/chaos/chaos_suite_v3.py | 938 | Chaos V3 suite - proven, comprehensive |
| contracts/truth_teller.py | 845 | Truth validation - proven |
| tests/test_execution_path.py | 738 | Integration tests - proven |
| tests/test_chaos_bunny.py | 725 | Chaos tests - proven |
| tests/test_historical_nukes.py | 705 | Historical stress tests - proven |
| tests/test_mirror.py | 625 | Mirror tests - proven |
| dispatcher/dispatcher.py | 609 | Core dispatcher - proven |
| execution/replay.py | 586 | Replay harness - proven |
| monitoring/dashboard.py | 585 | Dashboard - proven |
| execution/position.py | 515 | Position lifecycle - proven |
| monitoring/alerts.py | 486 | Alert system - proven |
| tests/test_worker_lifecycle.py | 479 | Worker tests - proven |
| execution/broker_stub.py | 470 | Paper broker - proven |
| tests/chaos/chaos_suite_v2.py | 428 | Chaos V2 - proven |
| cso/contract.py | 428 | CSO contract - proven |
| cso/observer.py | 408 | CSO observer - proven |
| governance/interface.py | 403 | Gov interface - proven |
| dispatcher/worker_base.py | 381 | Worker base - proven |
| dispatcher/tmux_control.py | 361 | TMUX control - proven |
| tests/test_liar_paradox.py | 357 | Paradox tests - proven |

---

## New File Requirements (S30+)

- Maximum 300 lines per file
- Enforced via code review (ruff doesn't have native check)
- If approaching limit, decompose into modules
- Exception requires CTO approval + documented rationale

---

## Decomposition Candidates (Post-S34)

| File | Suggested Split |
|------|-----------------|
| chaos_suite_v3.py | chaos/vectors/, chaos/harness.py |
| truth_teller.py | validators/, truth_engine.py |
| dispatcher.py | dispatch/scheduler.py, dispatch/queue.py |

---

*Last updated: 2026-01-23 (Pre-S30 hygiene)*
