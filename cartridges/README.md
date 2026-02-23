# Cartridges — Strategy Manifests

Strategy definitions that slot into the Phoenix harness.

## Structure

| Folder | Purpose |
|--------|---------|
| `active/` | Currently slotted strategies (CSO evaluates these) |
| `templates/` | Blank templates for creating new strategies |
| `archive/` | Deprecated or retired strategies (forensic) |

## Naming Convention

```
{STRATEGY_NAME}_v{semver}.yaml
```

Examples:
- `ASIA_RANGE_SCALP_v1.0.0.yaml`
- `FVG_LONDON_v1.2.0.yaml`

## Schema

See `schemas/cartridge_manifest.yaml` for full schema.

## Rules

1. Only ONE cartridge in `active/` at a time (v1.0)
2. Version bumps create new files, don't edit in place
3. Deprecated cartridges move to `archive/`
4. Templates are starting points, not runnable
