# CONSTITUTION/

**STATUS: SKELETON**

This directory contains the aspirational Constitutional Architecture Graph.
Currently <5% populated (6 invariant YAMLs, 3 role YAMLs, 1 wiring file).

The canonical invariant list lives in: `/INVARIANT_REGISTRY.yaml`
Invariants are enforced in code and proven by tests, not by YAML in this directory.

Referenced scripts (`validate_constitution.py`, `blast_radius.py`) do not yet exist.

See: `docs/canon/DRIFT_LOG.md` (DELTA-7) for full disposition.

---

## What Exists

| Component | Status | Count |
|-----------|--------|-------|
| Manifest | Skeleton | 1 file |
| Modules | Empty (README placeholders) | 0 populated |
| Invariants | Partial | 6 of 163+ |
| Roles | Partial | 3 files |
| Wiring | Minimal | 1 file |
| Scenarios | Empty | 0 |
| Environment | Empty | 0 |
| Dependencies | Empty | 0 |
| State | Empty | 0 |

## Where Invariants Actually Live

Invariants are **enforced in code** and **proven by tests**:

- **INVARIANT_REGISTRY.yaml** (repo root) — canonical list with status and test refs
- **governance/** — halt, lease, sentinel, runtime assertions
- **tests/** — 1690+ tests proving invariant compliance
- **docs/canon/DRIFT_LOG.md** — documentation vs reality tracking

## Structure (Aspirational)

```
CONSTITUTION/
├── CONSTITUTION_MANIFEST.yaml
├── invariants/   (6 of 163+ populated)
├── roles/        (3 populated)
├── wiring/       (1 populated)
└── (modules/, seams/, scenarios/, environment/, dependencies/, state/ — empty)
```

---

*S52 Hardening — honest status documented. See DRIFT_LOG DELTA-7.*
