# PROPOSED STRUCTURE — Phoenix Repo Filing Cabinet

```yaml
document: PROPOSED_STRUCTURE
version: 1.0
date: 2026-01-31
author: OPUS
purpose: Stage 2 of Filing Cabinet project
status: AWAITING_G_APPROVAL
```

---

## 1. DESIGN PRINCIPLES

```yaml
P1_CANON_SAFE:
  rule: "Canonical docs in dedicated folder, clearly marked"
  
P2_OBVIOUS_HOMES:
  rule: "Every doc type has one obvious place"
  
P3_FLAT_NOT_DEEP:
  rule: "Max 3 levels deep (bias: flat > nested)"
  
P4_README_EVERY_FOLDER:
  rule: "Every folder has README explaining purpose"
  
P5_NAMING_CONVENTIONS:
  rule: "Predictable, greppable, sortable patterns"
  
P6_OPERATIONAL_READY:
  rule: "Structure supports operate mode, not just build mode"
```

---

## 2. PROPOSED FOLDER TREE

```
phoenix/
│
├── README.md                     # Project overview (keep at root)
├── CLAUDE.md                     # Agent instructions (keep at root)
├── pyproject.toml                # Package config (keep at root)
│
├── docs/
│   │
│   ├── canon/                    # LOCKED AUTHORITATIVE DOCS
│   │   ├── README.md
│   │   ├── ARCHITECTURAL_FINALITY.md
│   │   ├── PHOENIX_MANIFEST.md
│   │   ├── SPRINT_ROADMAP.md
│   │   ├── CARPARK.md            # (moved from root)
│   │   └── designs/              # Canonical design docs
│   │       ├── CARTRIDGE_AND_LEASE_DESIGN_v1.0.md
│   │       └── ... (future designs)
│   │
│   ├── operations/               # OPERATIONAL DOCS
│   │   ├── README.md
│   │   ├── runbooks/             # RB-* procedures
│   │   │   └── RB-001_CONNECTION_LOSS.md
│   │   │   └── ...
│   │   └── operator/             # Operator guides
│   │       ├── OPERATOR_EXPECTATIONS.md
│   │       ├── WHEN_TO_IGNORE_PHOENIX.md
│   │       └── START_HERE.md     # (moved)
│   │
│   ├── build/                    # WORKING/SPRINT DOCS
│   │   ├── README.md
│   │   ├── current/              # Active sprint
│   │   │   ├── S44_BUILD_MAP_v0.1.md
│   │   │   └── S44_*_REPORT.md
│   │   └── explorations/         # R&D, ideas
│   │       └── EXPLORING_POST_S42_IDEAS.md
│   │
│   ├── archive/                  # HISTORICAL REFERENCE
│   │   ├── README.md
│   │   ├── sprints/              # Completed sprint docs
│   │   │   ├── S29_to_S40/
│   │   │   ├── S41/
│   │   │   ├── S42/
│   │   │   └── S43/
│   │   ├── designs/              # Superseded designs
│   │   │   └── S46_CARTRIDGE_v0.1/
│   │   └── reports/              # Historical reports
│   │
│   └── reference/                # CROSS-CUTTING REFERENCE
│       ├── README.md
│       ├── ADVISOR_ORIENTATION.md
│       ├── PATTERN_GLOSSARY.md
│       └── olya_skills/          # Methodology reference
│
├── CONSTITUTION/                 # CONSTITUTIONAL (keep as-is)
│   ├── README.md
│   ├── CONSTITUTION_MANIFEST.yaml
│   ├── invariants/
│   └── ...
│
├── cso/
│   └── knowledge/                # 5-DRAWER YAMLS (keep as-is)
│       ├── foundation.yaml
│       ├── context.yaml
│       ├── conditions.yaml
│       ├── entry.yaml
│       ├── management.yaml
│       ├── index.yaml
│       ├── GATE_GLOSSARY.yaml
│       └── archive/
│
├── cartridges/                   # STRATEGY MANIFESTS (NEW)
│   ├── README.md
│   ├── active/                   # Currently slotted
│   │   └── ASIA_RANGE_SCALP_v1.0.0.yaml
│   ├── templates/                # Blank templates
│   │   └── STRATEGY_TEMPLATE.yaml
│   └── archive/                  # Deprecated/retired
│
├── leases/                       # GOVERNANCE WRAPPERS (NEW)
│   ├── README.md
│   ├── active/                   # Currently active
│   │   └── lease_2026_01_31_asia_001.yaml
│   ├── expired/                  # Completed normally
│   └── revoked/                  # Terminated early
│
├── schemas/                      # YAML SCHEMAS (consolidate)
│   ├── README.md
│   ├── beads.yaml
│   ├── t2_token.yaml
│   ├── position_lifecycle.yaml
│   ├── cartridge_manifest.yaml   # (NEW)
│   └── lease.yaml                # (NEW)
│
├── contracts/                    # DATA CONTRACTS (keep, but docs → canon)
│   ├── README.md
│   ├── truth_teller.py
│   └── mirror_markers.py
│
├── reports/                      # TEST RESULTS (keep)
│   ├── README.md
│   └── ... (bunny reports, etc.)
│
├── drills/                       # VALIDATION SCRIPTS (keep)
│   ├── README.md
│   └── ...
│
└── [module folders]              # CODE MODULES (no change)
```

---

## 3. FOLDER PURPOSE DESCRIPTIONS

| Folder | Purpose | Access |
|--------|---------|--------|
| `docs/canon/` | Locked authoritative docs, versioned | Read-only after approval |
| `docs/canon/designs/` | Canonical design specifications | Read-only after approval |
| `docs/operations/` | How to operate Phoenix | Operator reference |
| `docs/operations/runbooks/` | Emergency procedures | RB-* format |
| `docs/operations/operator/` | Operator expectations | Human guidance |
| `docs/build/` | Active sprint work | Working docs |
| `docs/build/current/` | Current sprint artifacts | Active editing |
| `docs/build/explorations/` | R&D and ideas | Experimental |
| `docs/archive/` | Historical reference | Read-only |
| `docs/reference/` | Cross-cutting guides | Stable reference |
| `cartridges/` | Strategy manifests | Hot-swappable |
| `cartridges/active/` | Currently slotted strategies | Runtime read |
| `leases/` | Governance wrappers | Lifecycle managed |
| `leases/active/` | Currently active leases | Runtime read |

---

## 4. MIGRATION TABLE

### 4.1 Files to Move

| Current Location | New Location | Action |
|------------------|--------------|--------|
| `CARPARK.md` | `docs/canon/CARPARK.md` | MOVE |
| `GRANDFATHERED_FILES.md` | `docs/archive/GRANDFATHERED_FILES.md` | MOVE |
| `GEMINI.md` | `docs/reference/GEMINI.md` | MOVE |
| `SKILL.md` | `docs/reference/SKILL.md` | MOVE |
| `docs/ARCHITECTURAL_FINALITY.md` | `docs/canon/ARCHITECTURAL_FINALITY.md` | MOVE |
| `docs/PHOENIX_MANIFEST.md` | `docs/canon/PHOENIX_MANIFEST.md` | MOVE |
| `docs/SPRINT_ROADMAP.md` | `docs/canon/SPRINT_ROADMAP.md` | MOVE |
| `docs/START_HERE.md` | `docs/operations/operator/START_HERE.md` | MOVE |
| `docs/ADVISOR_ORIENTATION.md` | `docs/reference/ADVISOR_ORIENTATION.md` | MOVE |
| `docs/build_docs/CONSTITUTION_AS_CODE.md` | `docs/canon/CONSTITUTION_AS_CODE.md` | MOVE |
| `docs/S46_*/v1.0_CANONICAL.md` | `docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md` | MOVE + RENAME |
| `contracts/ICT_DATA_CONTRACT.md` | `docs/canon/ICT_DATA_CONTRACT.md` | MOVE |
| `contracts/GOVERNANCE_INTERFACE_CONTRACT.md` | `docs/canon/GOVERNANCE_INTERFACE_CONTRACT.md` | MOVE |

### 4.2 Files to Archive

| Current Location | New Location | Reason |
|------------------|--------------|--------|
| `docs/S40_COMPLETION_REPORT.md` | `docs/archive/sprints/S40/` | Historical |
| `docs/S41_COMPLETION_REPORT.md` | `docs/archive/sprints/S41/` | Historical |
| `docs/S42_FAILURE_TRIAGE.md` | `docs/archive/sprints/S42/` | Historical |
| `docs/CHAOS_V3_REPORT.md` | `docs/archive/reports/` | Historical |
| `docs/MONITORING_REPORT.md` | `docs/archive/reports/` | Historical |
| `docs/EXECUTION_PATH_REPORT.md` | `docs/archive/reports/` | Historical |
| `docs/UX_VALIDATION_LOG.md` | `docs/archive/reports/` | Historical |
| `docs/BEYOND_S39_SCOPE.md` | `docs/archive/sprints/S39/` | Historical |
| `docs/INVARIANT_FREEZE_S41.md` | `docs/archive/sprints/S41/` | Historical |
| `docs/COLD_START_STRATEGY.md` | `docs/archive/` | Historical |
| `docs/VISUAL_ANCHOR_MAP.md` | `docs/archive/` | Historical |
| `docs/S46_*/v0.1_CANONICAL.md` | `docs/archive/designs/S46_v0.1/` | Superseded |
| `docs/S46_*/ADVISOR_SYNTHESIS_ADDENDUM.md` | `docs/archive/designs/S46_v0.1/` | Merged |

### 4.3 Folders to Reorganize

| Current | New | Notes |
|---------|-----|-------|
| `docs/ARCHIVE/` | `docs/archive/` | Lowercase for consistency |
| `docs/build_docs/` | `docs/build/current/` | Clearer naming |
| `docs/runbooks/` | `docs/operations/runbooks/` | Under operations |
| `docs/OPERATOR_INSTRUCTIONS/` | `docs/operations/operator/` | Under operations |
| `docs/olya_skills/` | `docs/reference/olya_skills/` | Reference material |
| `docs/S46_CARTRIDGE_AND_LEASE_DESIGN/` | DELETE (contents moved) | Cleanup |

### 4.4 Files to Delete (After Archive)

| File | Reason |
|------|--------|
| `docs/PHOENIX_MANIFESTO.md` | Duplicate of PHOENIX_MANIFEST.md? |
| `docs/CSO_DYNASTY_SPEC.md` | Check if superseded |

### 4.5 New Folders to Create

| Folder | Purpose |
|--------|---------|
| `docs/canon/` | Canonical documents |
| `docs/canon/designs/` | Design specifications |
| `docs/operations/` | Operational docs |
| `docs/operations/operator/` | Operator guides |
| `docs/build/current/` | Current sprint |
| `docs/build/explorations/` | R&D docs |
| `docs/reference/` | Cross-cutting reference |
| `cartridges/` | Strategy manifests |
| `cartridges/active/` | Active strategies |
| `cartridges/templates/` | Blank templates |
| `cartridges/archive/` | Retired strategies |
| `leases/` | Governance wrappers |
| `leases/active/` | Active leases |
| `leases/expired/` | Completed leases |
| `leases/revoked/` | Terminated leases |

---

## 5. NAMING CONVENTIONS

```yaml
canonical_docs:
  pattern: "UPPER_SNAKE_CASE.md"
  versioned: "NAME_v1.0.md"
  examples:
    - ARCHITECTURAL_FINALITY.md
    - CARTRIDGE_AND_LEASE_DESIGN_v1.0.md

sprint_docs:
  pattern: "S{number}_*.md"
  examples:
    - S44_BUILD_MAP_v0.1.md
    - S44_PHASE1_REPORT.md

runbooks:
  pattern: "RB-{number}_{TITLE}.md"
  examples:
    - RB-001_CONNECTION_LOSS.md
    - RB-008_PACING_VIOLATION.md

cartridges:
  pattern: "{STRATEGY_NAME}_v{semver}.yaml"
  examples:
    - ASIA_RANGE_SCALP_v1.0.0.yaml
    - FVG_LONDON_v1.2.0.yaml

leases:
  pattern: "lease_{date}_{strategy}_{id}.yaml"
  examples:
    - lease_2026_01_31_asia_001.yaml
    - lease_2026_02_07_asia_002.yaml
```

---

## 6. README TEMPLATES

### 6.1 docs/canon/README.md

```markdown
# Canon — Authoritative Documents

This folder contains **locked, authoritative** documents that define Phoenix.

## Contents

| File | Purpose | Last Updated |
|------|---------|--------------|
| ARCHITECTURAL_FINALITY.md | System architecture freeze | 2026-01-XX |
| SPRINT_ROADMAP.md | Sprint history and roadmap | 2026-01-XX |
| PHOENIX_MANIFEST.md | Product definition | 2026-01-XX |
| CARPARK.md | Future scope parking | 2026-01-XX |

## Designs (designs/)

Canonical design specifications, versioned.

## Rules

1. **No edits without explicit approval**
2. **Version progression**: v0.1 → v1.0 → v1.1
3. **Superseded versions go to archive/**
```

### 6.2 docs/operations/README.md

```markdown
# Operations — How to Run Phoenix

Operational documentation for running Phoenix in production.

## Runbooks (runbooks/)

Emergency procedures. Format: `RB-{number}_{TITLE}.md`

## Operator Guides (operator/)

Human guidance for operators (G, Olya).
```

### 6.3 docs/build/README.md

```markdown
# Build — Working Documents

Sprint artifacts and explorations. These are **working docs**, not canonical.

## Current (current/)

Active sprint work. Move to archive/ when sprint completes.

## Explorations (explorations/)

R&D, ideas, experiments. May graduate to canon or be archived.
```

### 6.4 cartridges/README.md

```markdown
# Cartridges — Strategy Manifests

Strategy definitions that slot into the Phoenix harness.

## Active (active/)

Currently slotted strategies. CSO evaluates these.

## Templates (templates/)

Blank templates for creating new strategies.

## Archive (archive/)

Deprecated or retired strategies. Kept for forensics.

## Schema

See `schemas/cartridge_manifest.yaml` for full schema.
```

### 6.5 leases/README.md

```markdown
# Leases — Governance Wrappers

Governance bounds for strategy execution.

## Active (active/)

Currently active leases. Checked before every trade.

## Expired (expired/)

Completed normally. Kept for forensics.

## Revoked (revoked/)

Terminated early by human or system. Kept for forensics.

## Schema

See `schemas/lease.yaml` for full schema.
```

---

## 7. TOP-LEVEL REPO_MAP.md

```markdown
# REPO_MAP — Phoenix Repository Structure

## Quick Reference

| Need | Location |
|------|----------|
| What is Phoenix? | `docs/canon/PHOENIX_MANIFEST.md` |
| System architecture | `docs/canon/ARCHITECTURAL_FINALITY.md` |
| Sprint roadmap | `docs/canon/SPRINT_ROADMAP.md` |
| Strategy definitions | `cartridges/active/` |
| Active leases | `leases/active/` |
| CSO knowledge | `cso/knowledge/` |
| Runbooks | `docs/operations/runbooks/` |
| Current sprint | `docs/build/current/` |
| Historical docs | `docs/archive/` |

## Folder Structure

- `docs/canon/` — Locked authoritative docs
- `docs/operations/` — Runbooks and operator guides
- `docs/build/` — Sprint work and explorations
- `docs/archive/` — Historical reference
- `docs/reference/` — Cross-cutting guides
- `CONSTITUTION/` — Constitutional definitions
- `cso/knowledge/` — Olya's 5-drawer methodology
- `cartridges/` — Strategy manifests
- `leases/` — Governance wrappers
- `schemas/` — YAML schema definitions

## Naming Conventions

- Canonical: `UPPER_SNAKE_CASE.md`
- Sprints: `S{number}_*.md`
- Runbooks: `RB-{number}_{TITLE}.md`
- Cartridges: `{STRATEGY}_v{semver}.yaml`
- Leases: `lease_{date}_{strategy}_{id}.yaml`
```

---

## 8. EXECUTION CHECKLIST

```yaml
# DO NOT EXECUTE WITHOUT G APPROVAL

pre_execution:
  - [ ] G reviews PROPOSED_STRUCTURE.md
  - [ ] G approves or requests changes
  - [ ] Confirm no code path dependencies on moved files

execution_order:
  1: Create new folder structure
  2: Create README.md in each new folder
  3: Move canonical docs to docs/canon/
  4: Move operational docs to docs/operations/
  5: Archive historical docs
  6: Create cartridges/ and leases/ structure
  7: Delete empty/superseded folders
  8: Create REPO_MAP.md at root
  9: Commit with detailed message
  10: Verify no broken references

post_execution:
  - [ ] All READMEs in place
  - [ ] No orphaned files
  - [ ] REPO_MAP.md accurate
  - [ ] Spot check: find any canonical doc in <10 seconds
```

---

## 9. QUESTIONS FOR G

```yaml
Q1: "Delete or archive PHOENIX_MANIFESTO.md?"
  context: Appears duplicate of PHOENIX_MANIFEST.md
  recommendation: Archive, review later

Q2: "Keep responses/ or .gitignore?"
  context: 27 generated CFP response files
  recommendation: Add to .gitignore (regeneratable)

Q3: "Schema consolidation?"
  context: Multiple schema folders (cso/, cfp/, etc.)
  recommendation: Keep module-specific, add index in schemas/

Q4: "Agent files at root or in .cursor/?"
  context: CLAUDE.md, GEMINI.md at root
  recommendation: Keep at root (convention), move GEMINI/SKILL to reference/
```

---

## 10. SUMMARY

```yaml
total_new_folders: 15
total_file_moves: ~25
total_archives: ~15
total_deletes: ~3 (after review)

key_changes:
  - docs/canon/ for locked docs
  - docs/operations/ for runbooks
  - docs/build/ for sprint work
  - cartridges/ and leases/ for S47+
  - REPO_MAP.md at root

principles_upheld:
  - Flat > deep (max 3 levels)
  - Obvious > elegant
  - README everywhere
  - Clear naming conventions

ready_for: G_APPROVAL
```

---

**STAGE 2 COMPLETE — AWAITING G APPROVAL BEFORE EXECUTION 🐗📁**
