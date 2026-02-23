# Archived Documentation

**Purpose**: Historical reference only  
**For current documentation**: See `docs/START_HERE.md`  
**Date Archived**: 2026-01-30

---

## Why These Are Archived

Files moved here are either:
1. Superseded by newer versions
2. Pre-S35 (before constitutional ceiling)
3. Historical explorations no longer operational
4. Sprint-specific docs now consolidated into SPRINT_ROADMAP.md

---

## Contents

### build_history/

Build maps for completed sprints. Current sprint docs remain in `docs/build_docs/`.

| File | Sprint | Reason |
|------|--------|--------|
| S29_BUILD_MAP_v0.1.md | S29 | Pre-constitutional ceiling |
| S29_BUILD_MAP_v0.2.md | S29 | Pre-constitutional ceiling |
| S31_BUILD_MAPv0.1.md | S31 | Pre-constitutional ceiling |
| S31_BUILD_MAP_v0.2.md | S31 | Pre-constitutional ceiling |
| S32_BUILD_MAP_v0.1.md | S32 | Pre-constitutional ceiling |
| S32_BUILD_MAP_v0.2.md | S32 | Pre-constitutional ceiling |
| S33_BUILD_MAP_v0.1.md | S33 | Pre-constitutional ceiling |
| S33_BUILD_MAP_v0.2.md | S33 | Pre-constitutional ceiling |
| S34_BUILD_MAP_v0.1.md | S34 | Pre-constitutional ceiling |
| S34_BUILD_MAP_v0.2.md | S34 | Pre-constitutional ceiling |
| S35_BUILD_MAP_v0.1.md | S35 | Superseded by S42 |
| S35_BUILD_MAP_v0.2.md | S35 | Superseded by S42 |
| S36_BUILD_MAP_v0.1.md | S36 | Superseded by S42 |
| S36_BUILD_MAP_v0.2.md | S36 | Superseded by S42 |
| S37_BUILD_MAP_v0.1.md | S37 | Superseded by S42 |
| S37_BUILD_MAP_v0.2.md | S37 | Superseded by S42 |
| S38_BUILD_MAP_v0.1.md | S38 | Superseded by S42 |
| S38_BUILD_MAP_v0.2.md | S38 | Superseded by S42 |
| S39_BUILD_MAP_v0.1.md | S39 | Superseded by S42 |
| S39_BUILD_MAP_v0.2.md | S39 | Superseded by S42 |
| S40_BUILD_MAP_v0.1.md | S40 | Superseded by S42 |
| SPRINT_ROADMAP_S30_S33_v0.1.md | S30-S33 | Superseded by SPRINT_ROADMAP.md |
| SPRINT_ROADMAP_S30_S33_v0.2.md | S30-S33 | Superseded by SPRINT_ROADMAP.md |

### sprint_history/

Historical sprint reports and status docs.

| File | Reason |
|------|--------|
| CHAIN_VALIDATION_REPORT.md | S40 validation report (historical) |
| S40_BUNNY_REPORT.md | S40 bunny test report (historical) |
| PHOENIX_FOUNDATION_OVERVIEW.md | Superseded by PHOENIX_MANIFEST.md |
| S28_CONSOLIDATION_REPORT.md | Pre-constitutional ceiling |
| SPRINT_26.md | Pre-constitutional ceiling |
| SPRINT_STATUS_S34.md | Superseded by SPRINT_ROADMAP.md |
| VISION_v4.md | Superseded by PRODUCT_VISION.md |

### explorations/

Historical investigations and experiments.

| File | Reason |
|------|--------|
| IBKR_FLAKEY.md | Historical IBKR troubleshooting |
| S34.5_ORIENTATION_FLEX.md | Historical orientation exploration |
| pilot_exploration.md | Historical pilot study |

---

## Accessing Archived Content

These files retain full git history. To see historical versions:

```bash
git log --follow docs/ARCHIVE/build_history/S35_BUILD_MAP_v0.1.md
git show <commit>:docs/build_docs/S35_BUILD_MAP_v0.1.md  # Original location
```

---

## What Remains in Main Docs Path

After archive sweep, `docs/` contains only:

```yaml
authoritative:
  - START_HERE.md          # Entry point
  - PHOENIX_MANIFEST.md    # System topology
  - SPRINT_ROADMAP.md      # Current state
  - ARCHITECTURAL_FINALITY.md  # S42 freeze
  
reference:
  - build_docs/            # Current build docs (S42)
  - runbooks/              # Operational runbooks
  - olya_skills/           # Trading methodology
```

---

**Total Files Archived**: 30  
**Archive Date**: 2026-01-30  
**Archive Reason**: S42 DOC_SEAL track
