# contracts/

Phoenix data and governance contracts.

---

## River Contracts (Data Layer)

| Contract | Purpose | Status |
|----------|---------|--------|
| `ICT_DATA_CONTRACT.md` | Schema lockdown — 472 columns | LOCKED |
| `mirror_markers.py` | 107 boolean markers for XOR test | LOCKED |
| `truth_teller.py` | Data integrity monitor | IMPLEMENTED |
| `verify_schema.py` | Schema verification script | IMPLEMENTED |

### River Architecture

River = single, deterministic data pipeline.

```
Raw Data (IBKR/Dukascopy)
    ↓
    River (contracts/)
    ↓
Enriched Bars (472 columns)
    ↓
    CSO drinks from River
```

**Note:** River implementation follows NEX enrichment subsumption.
See `reports/NEX_SALVAGE_REPORT.md` for salvage plan.

---

## Governance Contracts

| Contract | Purpose | Status |
|----------|---------|--------|
| `GOVERNANCE_INTERFACE_CONTRACT.md` | GovernanceInterface ABC | LOCKED |

---

## Invariants

- **INV-DATA-1:** Single source of truth (River)
- **INV-DATA-2:** No synthetic data without `is_synthetic=TRUE`
- **INV-CONTRACT-1:** Deterministic (same input → same output)

---

*Sprint 26 — Foundation Proof*
