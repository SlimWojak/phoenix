# DRIFT_LOG — Documentation vs Reality Deltas

```yaml
source: FORENSIC_AUDIT.md (2026-02-23, Opus audit) + S54 TRUTH_SWEEP (2026-02-25)
triage: CTO + OWL/GPT/BOAR advisory panel
last_updated: 2026-02-25
```

---

## Categories

| Code | Meaning |
|------|---------|
| A_STALE_SPEC | Spec predates code, needs update |
| B_MISSING_CODE | Doc describes feature, code doesn't exist |
| C_REAL_BUG | Active code has actual defect |

---

## Deltas

### DELTA-1: Genesis Bead Count

```yaml
id: DELTA-1
category: A_STALE_SPEC
description: "BEAD_FIELD_SPEC v0.3 Section 6.1 says 981 CLAIMs. Actual post-curation count is 789."
disposition: FIX_SPEC
owner: DEXTER
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-2: XTDB → SQLite

```yaml
id: DELTA-2
category: A_STALE_SPEC
description: "Spec says 'XTDB-style bitemporal'. Actual: plain SQLite with manual bi-temporal queries."
disposition: FIX_SPEC (acceptable for Gate 1 scale)
owner: DEXTER
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-3: Dolt Work-Tree

```yaml
id: DELTA-3
category: A_STALE_SPEC
description: "Spec defines Dolt as WORK_TREE. Actual: git-based coordination via phoenix-swarm."
disposition: SUPERSEDED_BY_GIT
owner: G
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-4: AIR System

```yaml
id: DELTA-4
category: B_MISSING_CODE
description: "BEAD_FIELD_SPEC Section 7 defines full 5-step AIR. Zero code exists."
disposition: DESIGNED_NOT_BUILT (Gate 3)
owner: DEXTER
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-5: Sovereign Anchor / HSM

```yaml
id: DELTA-5
category: B_MISSING_CODE
description: "BEAD_FIELD_SPEC Section 5.2 defines daily HSM anchor. No code exists."
disposition: DESIGNED_NOT_BUILT (Gate 7)
owner: G
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-6: Two Position State Machines

```yaml
id: DELTA-6
category: C_REAL_BUG
description: "Two coexisting position FSMs — 5-state (S28) and 9-state (S32). Mixed imports."
disposition: FIXED_S52_T1
owner: PHOENIX
date_found: 2026-02-23
status: FIXED
commit_ref: "S52 T1 — execution/position.py → ImportError guard, paper.py created"
```

### DELTA-7: CONSTITUTION/ Directory Skeleton

```yaml
id: DELTA-7
category: A_STALE_SPEC
description: "CONSTITUTION/ directory captures <5% of 159+ invariants. Referenced scripts don't exist."
disposition: MITIGATED (INVARIANT_REGISTRY.yaml now tracks 240 code-referenced INV-* IDs)
owner: PHOENIX
date_found: 2026-02-23
status: MITIGATED
commit_ref: "S54-T3 (41b218f) — 203 INV-* stubs registered, validate_registry.py enforces count"
note: "CONSTITUTION/ directory still skeletal, but INVARIANT_REGISTRY.yaml is now canonical tracking."
```

### DELTA-8: River __init__.py Missing Exports

```yaml
id: DELTA-8
category: C_REAL_BUG
description: "river/__init__.py only exported SyntheticRiver. Real components missing."
disposition: FIXED_S52_T4
owner: PHOENIX
date_found: 2026-02-23
status: FIXED
commit_ref: "S52 T4 — river/__init__.py exports RiverReader, RiverWriter, RiverStreamer, schema"
```

### DELTA-9: Bridge Spec Not Built

```yaml
id: DELTA-9
category: B_MISSING_CODE
description: "SYSTEM_MANIFEST claims Projection bridge. No bridge code in either repo."
disposition: DESIGNED_NOT_BUILT (Gate 3+)
owner: PHOENIX
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-10: ChadBoar INV-DEPLOYMENT-AUDIT

```yaml
id: DELTA-10
category: B_MISSING_CODE
description: "ChadBoar canary finding: deployment config must be audited. No test exists."
disposition: DEFERRED (pre-live, not Gate 1 scope)
owner: PHOENIX
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-11: Test Count Discrepancy

```yaml
id: DELTA-11
category: A_STALE_SPEC
description: "SYSTEM_MANIFEST says 1690+, MASTER_PLAN says 1716. Docs updated at different times."
disposition: FIXED (validate_manifest.py now auto-syncs manifest count with pytest)
owner: PHOENIX
date_found: 2026-02-23
status: FIXED
commit_ref: "S53 — scripts/validate_manifest.py enforces manifest=pytest count"
```

### DELTA-12: CSO Observer Module Status

```yaml
id: DELTA-12
category: A_STALE_SPEC
description: "CONSTITUTION_MANIFEST lists CSO as 'skeleton'. CSO has comprehensive implementation."
disposition: REGISTRATION_STALE
owner: PHOENIX
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
```

### DELTA-13: Execution Surface Contract Stale

```yaml
id: DELTA-13
category: A_STALE_SPEC
description: "execution/contracts/execution_surface.yaml described 5-state S28.C lifecycle. Production uses 10-state FSM."
disposition: FIXED_S54_T1
owner: PHOENIX
date_found: 2026-02-24
status: FIXED
commit_ref: "S54-T1 (cbd5a48) — contract updated to 10-state canonical FSM from execution/positions/states.py"
```

### DELTA-14: CSE Source Enum Drift

```yaml
id: DELTA-14
category: A_STALE_SPEC
description: "cse_schema.yaml source enum [CSO, HUNT_SURVIVOR, MANUAL] missing MOCK_5DRAWER used in consumer.py"
disposition: FIXED_S54_T2
owner: PHOENIX
date_found: 2026-02-24
status: FIXED
commit_ref: "S54-T2 (c410424) — MOCK_5DRAWER added to canonical schema"
```

### DELTA-15: River Streamer Wrong Primitive

```yaml
id: DELTA-15
category: C_REAL_BUG
description: "RiverStreamer used reqRealTimeBars(barSize=5) delivering 5-second bars. Docstring said '1m bars'."
disposition: FIXED_S54_RIVER_PATCH
owner: PHOENIX
date_found: 2026-02-24
status: FIXED
commit_ref: "RIVER-P0P1P2 (000633a) — replaced with reqHistoricalData(keepUpToDate=True, barSizeSetting='1 min')"
```

### DELTA-16: BEAD_FIELD_SPRINT Running Score Contradictory

```yaml
id: DELTA-16
category: A_STALE_SPEC
description: "BEAD_FIELD_SPRINT.md running-score contained duplicate YAML keys with contradictory values (invariants_proven: 12 vs 3, genesis_status: SIGNED vs NOT_STARTED)"
disposition: FIXED_S58
owner: DEXTER
date_found: 2026-02-25
status: FIXED
commit_ref: "S58-T2 — removed stale duplicate entries, kept final (correct) values"
```

### DELTA-17: Dexter src/ Extraction Pipeline Missing

```yaml
id: DELTA-17
category: B_MISSING_CODE
description: "BEAD_FIELD_SPRINT.md says 'preserved: src/ (extraction pipeline, COMPLETE)' but ~/dexter/src/ does not exist"
disposition: ACKNOWLEDGED
owner: DEXTER
date_found: 2026-02-25
status: ACKNOWLEDGED
note: "May have been in different repo structure or different machine. Investigate when M3 operational."
```

---

## Summary

| Status | Count |
|--------|-------|
| FIXED | 7 (DELTA-6, DELTA-8, DELTA-11, DELTA-13, DELTA-14, DELTA-15, DELTA-16) |
| MITIGATED | 1 (DELTA-7 — registry now tracks 240 INV-* IDs) |
| LABELED | 5 (DELTA-2, DELTA-3, DELTA-4, DELTA-5, DELTA-9 — gate# or SUPERSEDED) |
| ACKNOWLEDGED | 4 (DELTA-1, DELTA-10, DELTA-12, DELTA-17) |

### DELTA-18: Leases README State Diagram Incorrect

```yaml
id: DELTA-18
category: A_DOC_DRIFT
description: "leases/README.md showed HALTED as terminal and REVOKED→HALTED path. Both wrong."
disposition: FIXED
owner: OPUS
date_found: 2026-02-25
status: FIXED
commit_ref: "S60-T4 — state diagram corrected: HALTED is non-terminal, only → REVOKED"
```

---

## Summary

| Status | Count |
|--------|-------|
| FIXED | 8 (DELTA-6, DELTA-8, DELTA-11, DELTA-13, DELTA-14, DELTA-15, DELTA-16, DELTA-18) |
| MITIGATED | 1 (DELTA-7 — registry now tracks 259 INV-* IDs, S59/S60 additions) |
| LABELED | 5 (DELTA-2, DELTA-3, DELTA-4, DELTA-5, DELTA-9 — gate# or SUPERSEDED) |
| ACKNOWLEDGED | 4 (DELTA-1, DELTA-10, DELTA-12, DELTA-17) |

*18 deltas tracked. S60: DELTA-18 fixed.*
