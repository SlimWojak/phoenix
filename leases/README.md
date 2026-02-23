# Leases — Governance Wrappers

Governance bounds for strategy execution.

## Structure

| Folder | Purpose |
|--------|---------|
| `active/` | Currently active leases (checked before every trade) |
| `expired/` | Completed normally (kept for forensics) |
| `revoked/` | Terminated early by human or system (kept for forensics) |

## Naming Convention

```
lease_{date}_{strategy}_{id}.yaml
```

Examples:
- `lease_2026_01_31_asia_001.yaml`
- `lease_2026_02_07_asia_002.yaml`

## Schema

See `schemas/lease.yaml` for full schema.

## State Machine

```
DRAFT → ACTIVE → EXPIRED
              ↓
           REVOKED
              ↓
           HALTED (terminal, no resurrection)
```

## Rules

1. Leases are governance, not strategy
2. Active lease bounds override cartridge defaults
3. Expired/revoked leases kept for audit trail
4. Never edit active leases — revoke and create new
