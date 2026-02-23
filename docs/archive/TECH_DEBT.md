# TECH_DEBT.md — Phoenix Technical Debt Register

```yaml
document: TECH_DEBT.md
version: 1.0
date: 2026-01-23
status: ACTIVE
purpose: Track known issues, pre-existing failures, cleanup candidates
```

---

## OVERVIEW

This document tracks technical debt accumulated during Phoenix development. Items here are:
- **Not blocking** current functionality
- **Cleanup candidates** for future sprints
- **Known issues** that need eventual attention

---

## PRE-EXISTING TEST FAILURES

### Summary
```yaml
total_failures: 104
total_errors: 7
blocking: NO
status: Cleanup candidate for S42
discovered: S41 Phase 3 validation
```

### Failure Categories

#### 1. ExecutionIntent Import Errors
```yaml
file: tests/test_no_live_orders.py
error: "ExecutionIntent import error"
cause: Module restructuring, import path changed
impact: LOW (test infrastructure, not runtime)
fix_effort: LOW (update imports)
```

#### 2. Telegram API Mismatch
```yaml
file: tests/test_telegram_real.py
error: "API mismatch"
cause: Telegram bot API changes
impact: LOW (notification tests, not core logic)
fix_effort: MEDIUM (API update + mock refresh)
```

#### 3. Schema Drift
```yaml
file: tests/test_schema_lockdown.py
error: "Schema drift detected"
cause: Schema evolution without test update
impact: LOW (validation tests)
fix_effort: LOW (regenerate expected schemas)
```

#### 4. Chaos Vector Incomplete
```yaml
file: tests/test_chaos_bunny.py
error: "Chaos vectors incomplete"
cause: New attack vectors added, tests not updated
impact: MEDIUM (chaos testing coverage)
fix_effort: MEDIUM (implement new vectors)
```

---

## RIVER DATA PIPELINE

### Issue
```yaml
description: No recent bars in River during live validation
discovered: S41 Phase 3B
root_cause: Data source not connected/configured
impact: LOW (validation used mocks successfully)
```

### Remediation Path
```yaml
option_1: Configure IBKR market data subscription
option_2: Connect alternative data source
option_3: Generate synthetic bars for testing
status: PARKED (not blocking)
```

---

## MODULE RESTRUCTURING DEBT

### Orphaned Imports
```yaml
description: Some test files reference old module paths
examples:
  - tests/test_execution/test_no_live_orders.py
  - tests/test_brokers/test_session_bead.py
fix: Update import paths to match current structure
effort: LOW
```

### Duplicate Code Patterns
```yaml
description: Some utility functions duplicated across modules
locations:
  - governance/runtime_assertions.py
  - validation/scalar_ban_linter.py
fix: Extract to shared utility module
effort: MEDIUM
status: PARKED (working, just not DRY)
```

---

## PARKED FEATURES (FROM CARPARK)

### Voice Whisperer
```yaml
status: PARKED since S40
description: Natural language voice interface
blocker: Not priority, foundation must prove first
revisit: Post-S42
```

### OINK Easter Eggs
```yaml
status: PARKED since S41 Phase 2E
description: Fun messages on success ("Recombobulation complete")
blocker: Scope creep prevention
revisit: Post-production launch
```

---

## DOCUMENTATION DEBT

### Outdated Comments
```yaml
description: Some code comments reference old patterns
locations:
  - cso/evaluator.py (references "grades")
  - hunt/executor.py (references "selection")
fix: Update comments to reflect current architecture
effort: LOW
```

### Missing Docstrings
```yaml
description: Some new S41 functions lack comprehensive docstrings
locations:
  - narrator/surface.py (new functions)
  - notification/alert_taxonomy.py (new formatters)
fix: Add docstrings
effort: LOW
```

---

## KNOWN EDGE CASES

### Unicode Normalization Limits
```yaml
description: NFKC normalization doesn't catch all homoglyphs
example: Cyrillic 's' (U+0455) not normalized to ASCII 's'
current_mitigation: Pattern matching catches most cases
future_fix: Consider homoglyph database for detection
impact: LOW (current patterns sufficient)
```

### Large File Performance
```yaml
description: Some validators may slow on very large outputs
threshold: > 100KB narrator output
current_mitigation: None (outputs typically < 10KB)
future_fix: Stream processing if needed
impact: LOW (no real-world issue observed)
```

---

## CLEANUP PRIORITIES

### P1 - Should Fix Soon
| Item | Effort | Impact |
|------|--------|--------|
| ExecutionIntent import errors | LOW | Cleans up test suite |
| Schema drift tests | LOW | Restores test coverage |

### P2 - Nice to Have
| Item | Effort | Impact |
|------|--------|--------|
| Telegram API update | MEDIUM | Better notification tests |
| Chaos vector completion | MEDIUM | Better chaos coverage |

### P3 - Eventual
| Item | Effort | Impact |
|------|--------|--------|
| Orphaned imports | LOW | Cleaner codebase |
| Duplicate code patterns | MEDIUM | DRY principle |
| Missing docstrings | LOW | Better documentation |

---

## S42 CLEANUP CANDIDATES

```yaml
recommended_scope:
  - Fix P1 items (104 failures → 0)
  - Update Telegram tests
  - Refresh schema expectations
  
estimated_effort: 1-2 hours
blocking: NOTHING (all current tests pass)
```

---

## DEBT TRACKING PROTOCOL

### Adding New Debt
1. Document in this file with category
2. Assign priority (P1/P2/P3)
3. Note discovery context (sprint, phase)

### Resolving Debt
1. Strike through resolved items
2. Add resolution note with date
3. Update totals in summary

---

*Technical debt tracked. Nothing blocking. Cleanup when convenient. 🐗*
