# CURRENT STRUCTURE AUDIT — Phoenix Repo Filing Cabinet

```yaml
document: CURRENT_STRUCTURE_AUDIT
version: 1.0
date: 2026-01-31
author: OPUS
purpose: Stage 1 of Filing Cabinet project
status: COMPLETE
```

---

## 1. CURRENT FOLDER TREE

```
phoenix/
├── CARPARK.md                    # Future scope parking
├── CLAUDE.md                     # Agent instructions
├── GEMINI.md                     # Agent instructions
├── GRANDFATHERED_FILES.md        # Tech debt tracker
├── README.md                     # Project overview
├── SKILL.md                      # Skill definition
├── pyproject.toml                # Package config
│
├── CONSTITUTION/                 # Constitutional docs (structured)
│   ├── CONSTITUTION_MANIFEST.yaml
│   ├── README.md
│   ├── invariants/              # INV-* YAML files
│   ├── roles/
│   ├── seams/
│   ├── wiring/
│   └── ... (other subfolders)
│
├── docs/                         # Main documentation
│   ├── ARCHIVE/                 # Historical docs
│   │   ├── build_history/       # Old sprint maps (S29-S40)
│   │   ├── explorations/        # R&D docs
│   │   └── sprint_history/      # Sprint reports
│   ├── OPERATOR_INSTRUCTIONS/   # Runbook-adjacent
│   ├── S46_CARTRIDGE_AND_LEASE_DESIGN/  # Design docs (NEW)
│   ├── build_docs/              # Current sprint artifacts
│   ├── olya_skills/             # Olya methodology extracts
│   ├── runbooks/                # RB-* procedures
│   └── [~20 loose MD files]     # Mixed canonical/working
│
├── cso/                          # CSO module
│   ├── knowledge/               # 5-DRAWER YAMLS (CRITICAL)
│   │   ├── foundation.yaml
│   │   ├── context.yaml
│   │   ├── conditions.yaml
│   │   ├── entry.yaml
│   │   ├── management.yaml
│   │   ├── index.yaml
│   │   ├── GATE_GLOSSARY.yaml
│   │   ├── archive/             # Old knowledge versions
│   │   └── updates_from_cso/    # CSO amendments
│   ├── contracts/
│   ├── harness/
│   └── schemas/
│
├── contracts/                    # Data contracts
│   ├── ICT_DATA_CONTRACT.md
│   ├── GOVERNANCE_INTERFACE_CONTRACT.md
│   ├── truth_teller.py
│   └── ...
│
├── schemas/                      # YAML schema definitions
│   ├── beads.yaml
│   ├── t2_token.yaml
│   ├── position_lifecycle.yaml
│   └── ...
│
├── reports/                      # Test/validation reports
│   ├── BUNNY_REPORT_*.md
│   ├── D*_COMPLETION_REPORT.md
│   └── *.json (test results)
│
├── responses/                    # CFP/CSO responses (27 files)
│   └── cfp_response_*.md
│
├── drills/                       # Validation scripts
│   └── *.py (d1-d4, ibkr, s41-s44)
│
└── [30+ module folders]          # Code modules
    (brokers, cfp, execution, governance, narrator, etc.)
```

---

## 2. DOCUMENT TYPE INVENTORY

### 2.1 Canonical Documents (should be locked)

| Location | File | Status |
|----------|------|--------|
| `docs/S46_CARTRIDGE_AND_LEASE_DESIGN/` | `CARTRIDGE_AND_LEASE_DESIGN_v1.0_CANONICAL.md` | ✅ Good location |
| `docs/` | `ARCHITECTURAL_FINALITY.md` | ⚠️ Should be in canon folder |
| `docs/` | `SPRINT_ROADMAP.md` | ⚠️ Should be in canon folder |
| `docs/` | `PHOENIX_MANIFEST.md` | ⚠️ Should be in canon folder |
| `docs/build_docs/` | `CONSTITUTION_AS_CODE.md` | ⚠️ Wrong folder |
| `CONSTITUTION/` | `CONSTITUTION_MANIFEST.yaml` | ✅ Good location |
| `cso/knowledge/` | 5-drawer YAMLs | ✅ Good location |

### 2.2 Working Documents (sprint artifacts)

| Location | Files | Count |
|----------|-------|-------|
| `docs/build_docs/` | `S*_BUILD_MAP_*.md` | 8 |
| `docs/build_docs/` | `S44_*_REPORT.md` | 3 |
| `docs/build_docs/` | Misc working docs | 10 |
| `docs/` | `S40_COMPLETION_REPORT.md`, etc. | 5 |
| `docs/ARCHIVE/build_history/` | Archived sprint maps | 24 |

### 2.3 Reports (test/validation results)

| Location | Type | Count |
|----------|------|-------|
| `reports/` | Bunny reports | 5 |
| `reports/` | D* completion reports | 4 |
| `reports/` | Track reports | 3 |
| `reports/` | JSON results | 4 |

### 2.4 Operational Documents

| Location | Type | Count |
|----------|------|-------|
| `docs/runbooks/` | RB-* procedures | 8 |
| `docs/OPERATOR_INSTRUCTIONS/` | Operator guides | 2 |
| `drills/` | Validation scripts | 15 |

### 2.5 Generated/Transient Files

| Location | Type | Count | Recommendation |
|----------|------|-------|----------------|
| `responses/` | CFP responses | 27 | Should be .gitignored or archived |

---

## 3. MISPLACED FILES

### 3.1 Canonical Docs in Wrong Location

| File | Current | Should Be |
|------|---------|-----------|
| `docs/ARCHITECTURAL_FINALITY.md` | docs/ | canon/ |
| `docs/PHOENIX_MANIFEST.md` | docs/ | canon/ |
| `docs/SPRINT_ROADMAP.md` | docs/ | canon/ |
| `docs/build_docs/CONSTITUTION_AS_CODE.md` | build_docs/ | CONSTITUTION/ |

### 3.2 Sprint Artifacts Not Archived

| File | Current | Should Be |
|------|---------|-----------|
| `docs/S40_COMPLETION_REPORT.md` | docs/ | ARCHIVE/sprint_history/ |
| `docs/S41_COMPLETION_REPORT.md` | docs/ | ARCHIVE/sprint_history/ |
| `docs/S42_FAILURE_TRIAGE.md` | docs/ | ARCHIVE/sprint_history/ |
| `docs/CHAOS_V3_REPORT.md` | docs/ | ARCHIVE/sprint_history/ |
| `docs/MONITORING_REPORT.md` | docs/ | ARCHIVE/sprint_history/ |
| `docs/EXECUTION_PATH_REPORT.md` | docs/ | ARCHIVE/sprint_history/ |
| `docs/UX_VALIDATION_LOG.md` | docs/ | ARCHIVE/sprint_history/ |

### 3.3 Superseded Docs to Archive

| File | Reason |
|------|--------|
| `docs/S46_*/CARTRIDGE_AND_LEASE_DESIGN_v0.1_CANONICAL.md` | Superseded by v1.0 |
| `docs/S46_*/ADVISOR_SYNTHESIS_ADDENDUM.md` | Merged into v1.0 |
| `docs/BEYOND_S39_SCOPE.md` | Historical context only |
| `docs/INVARIANT_FREEZE_S41.md` | Specific to S41, now complete |
| `docs/COLD_START_STRATEGY.md` | Likely historical |
| `docs/CSO_DYNASTY_SPEC.md` | Should be checked if current |

---

## 4. REDUNDANT/DUPLICATE CONCERNS

### 4.1 Duplicate Naming Patterns

| Pattern | Issue |
|---------|-------|
| `docs/PHOENIX_MANIFEST.md` vs `CONSTITUTION/CONSTITUTION_MANIFEST.yaml` | Different formats, similar purpose? |
| `docs/PHOENIX_MANIFESTO.md` vs `docs/PHOENIX_MANIFEST.md` | Confusing naming |

### 4.2 Multiple Schema Locations

| Location | Content |
|----------|---------|
| `schemas/` | Top-level YAML schemas |
| `cso/schemas/` | CSO-specific schemas |
| `cfp/schemas/` | CFP-specific schemas |
| `athena/schemas/` | Athena schemas |
| `hunt/schemas/` | Hunt schemas |
| `validation/schemas/` | Validation schemas |
| `execution/contracts/` | Execution schemas |

**Question:** Should there be one canonical `schemas/` folder?

---

## 5. HOMELESS IMPORTANT DOCS

| File | Current | Issue |
|------|---------|-------|
| `CARPARK.md` | root | Should be in docs/ or canon/ |
| `SKILL.md` | root | Should be in docs/ or .cursor/ |
| `GRANDFATHERED_FILES.md` | root | Should be in docs/ or ARCHIVE/ |
| `contracts/*.md` | contracts/ | Mix of code and docs in same folder |

---

## 6. CSO KNOWLEDGE STRUCTURE (Critical)

```
cso/knowledge/
├── foundation.yaml       # Drawer 1: Market structure
├── context.yaml          # Drawer 2: HTF context  
├── conditions.yaml       # Drawer 3: Setup conditions
├── entry.yaml            # Drawer 4: Entry rules
├── management.yaml       # Drawer 5: Position management
├── index.yaml            # Signal counts, relationships
├── GATE_GLOSSARY.yaml    # Gate definitions
├── CSO_HEALTH_PROMPT.md  # CSO health check
├── 5DRAWER_EXTRACTION_LOG.md  # Historical
├── archive/              # Old versions
└── updates_from_cso/     # Amendment tracking
```

**Status:** Well-organized. This is the template for cartridge structure.

---

## 7. FUTURE STRUCTURE NEEDS

### 7.1 Cartridges (not yet implemented)

```yaml
need:
  - cartridges/active/       # Active strategy manifests
  - cartridges/templates/    # Blank templates
  - cartridges/archive/      # Deprecated strategies
```

### 7.2 Leases (not yet implemented)

```yaml
need:
  - leases/active/           # Currently active leases
  - leases/expired/          # Completed leases (forensic)
  - leases/revoked/          # Revoked leases (forensic)
```

---

## 8. QUESTIONS TO ANSWER

```yaml
Q1: "Where should canonical design docs live?"
  current: docs/S46_CARTRIDGE_AND_LEASE_DESIGN/
  options:
    - Keep in docs/ with clear naming
    - Create docs/canon/ for locked docs
    - Create top-level canon/

Q2: "What's the relationship between contracts/ and schemas/?"
  observation: Both contain interface definitions
  question: Should they merge?

Q3: "Should responses/ be gitignored?"
  observation: 27 generated files
  question: Transient or forensic?

Q4: "Where do runbooks belong?"
  current: docs/runbooks/
  question: Keep in docs/ or move to operations/?

Q5: "Should agent files (CLAUDE.md, GEMINI.md) stay at root?"
  current: root
  convention: Many repos use .cursor/ or similar
  
Q6: "How to handle version progression?"
  example: v0.1 → v1.0 → v1.1
  question: Archive superseded or delete?
```

---

## 9. ARCHIVE CANDIDATES

### 9.1 Ready to Archive (Historical)

| File | Reason |
|------|--------|
| `docs/S40_COMPLETION_REPORT.md` | Sprint complete |
| `docs/S41_COMPLETION_REPORT.md` | Sprint complete |
| `docs/S42_FAILURE_TRIAGE.md` | Sprint complete |
| `docs/CHAOS_V3_REPORT.md` | Historical |
| `docs/MONITORING_REPORT.md` | Historical |
| `docs/EXECUTION_PATH_REPORT.md` | Historical |
| `docs/UX_VALIDATION_LOG.md` | Historical |
| `docs/BEYOND_S39_SCOPE.md` | Historical |
| `docs/INVARIANT_FREEZE_S41.md` | S41 specific |
| `docs/COLD_START_STRATEGY.md` | Check if still relevant |
| `docs/VISUAL_ANCHOR_MAP.md` | Check if still relevant |

### 9.2 Superseded (Delete or Archive)

| File | Reason |
|------|--------|
| `docs/S46_*/CARTRIDGE_AND_LEASE_DESIGN_v0.1_CANONICAL.md` | Superseded by v1.0 |
| `docs/S46_*/ADVISOR_SYNTHESIS_ADDENDUM.md` | Merged into v1.0 |

### 9.3 Review Needed

| File | Question |
|------|----------|
| `docs/PHOENIX_MANIFESTO.md` | vs PHOENIX_MANIFEST.md? |
| `docs/CSO_DYNASTY_SPEC.md` | Still current? |
| `docs/olya_skills/*.md` | Archive or active reference? |
| `GRANDFATHERED_FILES.md` | Still tracking tech debt? |

---

## 10. SUMMARY

```yaml
current_state: ORGANIC
  - Structure evolved during build phase
  - Mixed canonical/working docs in same folders
  - Some historical docs not archived
  - Missing cartridge/lease structure
  - Multiple schema locations

strengths:
  - CONSTITUTION/ well-organized
  - cso/knowledge/ well-organized (5-drawer model)
  - docs/ARCHIVE/ structure exists
  - docs/runbooks/ clear purpose

weaknesses:
  - docs/ has ~20 loose files (mixed purpose)
  - Canonical docs not separated from working docs
  - No clear cartridge/lease home
  - Some superseded docs still in main tree
  - responses/ generates clutter

recommendation: |
  Create clear separation between:
  1. CANON (locked, authoritative)
  2. OPERATIONAL (runbooks, procedures)
  3. BUILD (sprint artifacts, working docs)
  4. ARCHIVE (historical reference)
  
  Plus future:
  5. CARTRIDGES (strategy manifests)
  6. LEASES (governance wrappers)
```

---

**STAGE 1 COMPLETE — Ready for PROPOSED_STRUCTURE.md**
