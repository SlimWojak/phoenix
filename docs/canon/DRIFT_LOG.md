# DRIFT_LOG — Documentation vs Reality Deltas

```yaml
source: FORENSIC_AUDIT.md (2026-02-23, Opus audit)
triage: CTO + OWL/GPT/BOAR advisory panel
last_updated: 2026-02-23
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
disposition: ACKNOWLEDGED (invariants enforced in code, YAML tracking deferred)
owner: PHOENIX
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
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
disposition: COSMETIC
owner: PHOENIX
date_found: 2026-02-23
status: ACKNOWLEDGED
commit_ref: null
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

---

## Summary

| Status | Count |
|--------|-------|
| FIXED | 5 (DELTA-1, DELTA-6, DELTA-8 in S52; DELTA-4, DELTA-5 labeled in spec) |
| LABELED | 5 (DELTA-2, DELTA-3, DELTA-4, DELTA-5, DELTA-9 — all have gate# or SUPERSEDED) |
| ACKNOWLEDGED | 4 (DELTA-7, DELTA-10, DELTA-11, DELTA-12) |

*All 12 forensic deltas tracked. S52 closure: genesis count fixed, spec language downgraded, all DESIGNED_NOT_BUILT features labeled with gate numbers.*
