# OPUS M3 BUILD BRIEF — CANONICAL PIPELINE
## Date: 2026-03-25 | Owner: CTO | Sovereign: G
## Principle: "Go slow to go fast. End-state logic, not workarounds."

---

## MISSION

Build the canonical detection-to-bead-field pipeline. When this is done:
- Every detection CLAIM exists as a signed bead in the Bead Field
- 5 years of historical detections are mineable
- MIRROR displays what Dexter sees on any date
- The "analytically void" field becomes analytically rich
- Dream Cycle has its fuel

---

## ORIENTATION

You are Opus on M3 Ultra. Workspace: `~/dexter`, `~/phoenix`, `~/research_accelerator`.
M3 is the production machine. Bead Field (69GB, 11.4M FACTs) lives here.

```yaml
KEY_FILES:
  # Detection pipeline
  pipeline: dexter/scripts/daily_detection_export.py
  producers: dexter/dexter/bead_field/producers/  # 11 vLOCK producers
  output_json: ~/dexter/output/detections/{forex_day}.json
  
  # Bead Field infrastructure (ALREADY BUILT)
  bead_store: dexter/dexter/bead_field/store/       # append-only SQLite
  ingestion: dexter/dexter/bead_field/ingestion/     # FACT bead writer exists
  schema: dexter/dexter/bead_field/schema/           # bead_core, type schemas
  query: dexter/dexter/bead_field/query/             # chain walk, temporal, verify
  signing: dexter/dexter/bead_field/signing/         # PQC + ECDSA (ML-DSA-65 Dilithium3)
  
  # Bridge (for reference — similar pattern)
  bridge_mapper: dexter/dexter/bridge/               # governance events → FACT beads
  governance_mapper: dexter/dexter/bead_field/ingestion/governance_mapper.py
  
  # River (data source)
  river_data: ~/phoenix-river/EURUSD/                # 1,405 parquets, Nov 2020 → Mar 2026
  river_adapter: dexter/dexter/bead_field/river/river_adapter.py
  
  # MIRROR
  mirror_backend: research_accelerator/mirror/backend/server.py
  mirror_frontend: research_accelerator/mirror/frontend/js/mirror-chart.js
  
  # Methodology (READ ONLY — do not modify)
  vlock: phoenix-swarm/calibration_bible/SYNTHETIC_OLYA_METHOD_vLOCK.yaml
  state_detection: phoenix-swarm/calibration_bible/STATE_DETECTION_LOGIC_v2.yaml
  detect_oracle: research_accelerator/src/ra/detectors/detect.py
```

---

## PHASE 1: FIX EXPORT BUG (30 min)

### What
`daily_detection_export.py` hardcodes `bar_time` as the reasoning_trace time key.
FVG uses `detect_time`, OB uses `ob_time`. Claims are silently dropped.

### Fix
```python
def _get_bar_time(claim):
    """Resolve canonical bar time from claim, handling producer-specific key names."""
    rt = claim.reasoning_trace
    return (rt.get("bar_time") or rt.get("detect_time") or 
            rt.get("ob_time") or rt.get("anchor_time") or "")
```
Replace `c.reasoning_trace.get("bar_time", "")` with `_get_bar_time(c)` in:
- `_filter_claims_by_day()` (line ~351)
- `_build_export()` (line ~376)

### Validate
```bash
cd ~/dexter
.venv/bin/python3 scripts/daily_detection_export.py 2026-03-24 2026-03-24

# Verify FVG and OB now appear:
python3 -c "
import json
with open('output/detections/2026-03-24.json') as f:
    data = json.load(f)
from collections import Counter
types = Counter()
for tf_data in data.get('detections', {}).values():
    for d in tf_data:
        types[d.get('primitive_type', 'unknown')] += 1
for t, c in types.most_common():
    print(f'  {t}: {c}')
"
```

### Exit Gate
FVG and order_block appear in exported JSON for Mar 24 with correct timestamps.

---

## PHASE 2: BUILD CLAIM BEAD WRITER (core build)

### Context
The Bead Field already ingests FACT beads. The infrastructure exists:
- Schema validation (bead_core + type-specific schemas)
- Hash chain (hash_self, hash_prev)
- Merkle batching
- PQC + ECDSA signing (ML-DSA-65 Dilithium3, real ARM64)
- Bi-temporal fields (world_time, knowledge_time)
- Append-only SQLite store

CLAIM beads use the same infrastructure, different `bead_type` enum.
Study the existing FACT ingestion path and the governance_mapper.py 
(which maps governance events → FACT beads) as your pattern.

### What To Build

New module: `dexter/dexter/bead_field/ingestion/claim_writer.py`

Maps detection pipeline ClaimSpec objects → CLAIM beads.

### CLAIM Bead Field Mapping

Per BEAD_FIELD_SPEC_v0.3, a CLAIM bead requires:

```yaml
# bead_core fields:
bead_id: "UUID v7 (time-ordered)"
bead_type: CLAIM

# bi-temporal:
world_time_valid_from: "bar timestamp of detection (the market moment)"
world_time_valid_to: "bar timestamp (point-in-time observation, from=to)"
knowledge_time_recorded_at: "pipeline execution timestamp (when we computed this)"
temporal_class: OBSERVATION  # these are tied to specific market time

# provenance:
source_ref:
  source_type: AGENT
  source_id: "dexter-{producer_name}"  # e.g. "dexter-fvg_producer"
  source_version: "{git_commit_hash}"   # dexter repo HEAD at pipeline run

# claim-specific content:
content:
  conclusion: "{primitive_type} detected on {pair} {timeframe}"
  reasoning_trace: "{full reasoning_trace dict from ClaimSpec}"
  premises_ref: []  # populated later when we link to FACT bar beads
  confidence_basis: "deterministic vLOCK detection"
  drawer: "{map primitive to drawer enum}"
  icm_terms: ["{primitive_type}"]  # FVG, MSS, DISPLACEMENT, etc.

# integrity (computed by existing infrastructure):
hash_self: "SHA-256 of content + metadata"
hash_prev: "previous CLAIM bead hash in this stream"
attestation: "PQC + ECDSA signatures"

# lineage:
lineage: []  # empty for now; future: link to FACT bar beads

# tags (for query):
tags:
  - "{pair}"           # EURUSD
  - "{timeframe}"      # 5m, 15m, 1H, 4H, 1D
  - "{primitive_type}" # FVG, MSS, SWING_POINT, etc.
  - "{session}"        # LOKZ, NYOKZ, ASIA (if applicable)
  - "{direction}"      # BULLISH, BEARISH (if applicable)
```

### Drawer Mapping
```yaml
# Map vLOCK primitives to BEAD_FIELD_SPEC drawer enum
SWING_POINT: MARKET_STRUCTURE
FVG: PREMIUM_DISCOUNT         # FVG is PDA zone
DISPLACEMENT: ENTRY_MODEL
MSS: MARKET_STRUCTURE
ORDER_BLOCK: ENTRY_MODEL
IFVG: PREMIUM_DISCOUNT
BPR: PREMIUM_DISCOUNT
SESSION_BOUNDARY: HTF_BIAS
ASIA_RANGE: HTF_BIAS
PDH_PDL: HTF_BIAS
LIQUIDITY_SWEEP: MARKET_STRUCTURE
OTE: ENTRY_MODEL
DIAGNOSTIC_SIGNAL: CONFIRMATION
```

### Stream Design
Detection CLAIMs should form per-pair, per-date hash chains:
- Stream key: `{pair}:{forex_day}:claims`
- Each day's CLAIMs chain together (hash_prev links within the day)
- First CLAIM of a new day has hash_prev = last CLAIM of previous day (or null for first ever)

### Key Design Decisions

```yaml
DECISION_1_SEPARATE_DB:
  question: "New SQLite DB for CLAIM beads, or add to existing FACT DBs?"
  recommendation: SEPARATE_DB
  reasoning: |
    Existing 6 DBs hold OHLCV FACTs (11.4M beads, 69GB).
    Detection CLAIMs are a different analytical category.
    Separate DB keeps the field organized, queryable, and allows
    independent Merkle anchoring cadence.
    Name: ~/dexter/tools/synthetic/eurusd_claims.db (or similar)
    Follow same pattern as existing pair DBs.
  CTO_NOTE: "Check with G if this feels right vs adding to existing DBs.
    The bead_field_spec doesn't mandate either way. Separate is cleaner
    for query performance and backup granularity."

DECISION_2_BATCH_VS_INDIVIDUAL:
  question: "Write beads one at a time or batch per pipeline run?"
  recommendation: BATCH_PER_DAY
  reasoning: |
    Pipeline produces all CLAIMs for a forex day in one run.
    Batch write with single Merkle anchor per day is natural.
    Matches DEC-MERKLE-HYBRID: "Decision Boundary + fallback caps."
    A forex day completion IS a decision boundary.

DECISION_3_SIGNING:
  question: "Sign every CLAIM bead, or sign the batch Merkle root only?"
  recommendation: SIGN_EVERY_BEAD
  reasoning: |
    Per BEAD_FIELD_SPEC: attestation field is REQUIRED on every bead.
    Individual signing enables per-bead verification.
    ML-DSA-65 on ARM64 (M3 Ultra) is fast enough.
    This is what the existing FACT ingestion does.
```

### Tests Required
- ClaimSpec → CLAIM bead mapping (all 13 primitive types)
- Bi-temporal fields correct (WT from bar, KT from pipeline run)
- Hash chain integrity (chain walk after batch write)
- Signature verification (PQC + ECDSA round-trip)
- Drawer mapping covers all primitives
- Tags queryable via existing query layer
- Edge case: empty day (no detections) → no beads written, chain unbroken

---

## PHASE 3: WIRE PIPELINE (connect producers → beads + JSON)

### What
Modify `daily_detection_export.py` to write BOTH:
1. JSON files (backward compatible, MIRROR reads these)
2. CLAIM beads via claim_writer.py (end-state path)

### Where
In `run_pipeline()` (or equivalent orchestration function), after producers run:

```python
# Existing: JSON export (keep for MIRROR backward compatibility)
_build_export(claims, forex_day, output_dir)

# NEW: Bead Field write
from dexter.bead_field.ingestion.claim_writer import write_claims_as_beads
write_claims_as_beads(
    claims=all_claims,          # same ClaimSpec objects
    pair="EURUSD",
    forex_day=forex_day,
    pipeline_commit=get_git_hash(),
    pipeline_run_time=datetime.utcnow(),
)
```

### State Detection & Diagnostic Signals
The pipeline also produces WorldState snapshots and DIAGNOSTIC_SIGNALs.
These should ALSO become beads:
- WorldState snapshots → CLAIM beads (drawer: HTF_BIAS, content: full state dict)
- DIAGNOSTIC_SIGNALs → SIGNAL beads (per BEAD_FIELD_SPEC signal_content schema)

This maps to the canonical bead type progression:
`FACT (bars) → CLAIM (detections) → SIGNAL (diagnostic signals)`

### Exit Gate
Pipeline run produces BOTH JSON file AND CLAIM beads for same date.
Bead count matches CLAIM count in JSON (minus any legitimate filter differences).
Beads pass `verify_bead()` from query layer.
Chain walk succeeds across a multi-day run.

---

## PHASE 4: HISTORICAL BACKFILL (5 years)

### Prerequisites
- Phase 1 DONE (export bug fixed)
- Phase 2 DONE (claim_writer tested)
- Phase 3 DONE (pipeline wired to both outputs)
- G approves running the backfill (significant compute + storage)

### Execution
```bash
cd ~/dexter

# Start from Jan 2021 (skip first 30 days of Nov-Dec 2020 for warmup)
# Run in batches to monitor progress and catch issues early:

# Batch 1: 2021 (test year)
.venv/bin/python3 scripts/daily_detection_export.py 2021-01-04 2021-12-31

# Verify batch 1:
# - Check JSON count matches expected trading days (~260)
# - Check bead count via query layer
# - Spot-check a known date (FVG counts, primitive types)
# - Verify chain integrity: walk_chain across full year

# Batch 2: 2022
.venv/bin/python3 scripts/daily_detection_export.py 2022-01-03 2022-12-30

# Batch 3: 2023
.venv/bin/python3 scripts/daily_detection_export.py 2023-01-02 2023-12-29

# Batch 4: 2024
.venv/bin/python3 scripts/daily_detection_export.py 2024-01-01 2024-12-31

# Batch 5: 2025-2026
.venv/bin/python3 scripts/daily_detection_export.py 2025-01-02 2026-03-24
```

### Validation Between Batches
After each batch, before proceeding:
```python
# Chain integrity
from dexter.bead_field.query.chain import walk_chain
from dexter.bead_field.query.verify import verify_bead
# Walk full chain, verify no breaks

# Bead count sanity
# ~50-200 CLAIMs per trading day (rough estimate from 57 FVGs + swings + disp + MSS + OB)
# ~260 trading days per year
# Expected: ~13,000-52,000 CLAIM beads per year
# Total: ~65,000-260,000 CLAIM beads across 5 years
```

### Storage Estimate
- JSON: ~1,400 files × 200KB = ~280MB
- CLAIM beads: 200K beads × (avg 2KB per bead with signatures) = ~400MB
- Total new storage: <1GB — trivial on M3's storage

---

## PHASE 5: MIRROR DISPLAY FIXES

Only after data layer (Phases 1-4) is solid. These are all frontend/display.

### Fix A: Native-TF Detection Display
**File:** `research_accelerator/mirror/frontend/js/mirror-chart.js` (~line 501-512)

**Current (WRONG):**
```javascript
// For HTF views, include detections from all lower TFs
if (htfView) {
    for (var tfKey in byTf) { tfDets = tfDets.concat(byTf[tfKey]); }
}
```

**Correct:** Show only native-TF detections for the current view.
```javascript
// Show only detections native to the displayed timeframe
tfDets = byTf[currentTf] || [];
```

**vLOCK rule:** "All primitives detect NATIVELY on each timeframe's own bar arrays.
5m FVG = gap across 3 consecutive 5m candles. NOT: 1m detection projected onto 5m display."

### Fix B: Session Zone Shading
Per COO diagnostic: likely JS rendering bug after NY time shift. 
Needs browser console inspection. Check line ~944 where active-zone 
highlighting compares now (UTC) against startTS/endTS (NY-shifted).

### Fix C: LTF Multi-Day Range
Frontend currently requests single-day bars for LTF views.
Change to use `/api/bars-range` endpoint (already exists for HTF).
With 5 years of detection JSON, users will want to scroll LTF charts too.

---

## CONSTRAINTS (NON-NEGOTIABLE)

```yaml
DO_NOT_MODIFY:
  - SYNTHETIC_OLYA_METHOD_vLOCK.yaml (locked methodology)
  - STATE_DETECTION_LOGIC_v2.yaml (locked state detection)
  - detect.py (reference oracle)
  - Any producer detection logic (producers work correctly)
  - Existing FACT beads or genesis beads

INVARIANTS_TO_RESPECT:
  - INV-BEAD-IMMUTABLE: "Append-only. No mutation."
  - INV-BEAD-SIGNED: "Dual PQC+ECDSA on every structural bead."
  - INV-BEAD-TEMPORAL: "Every bead has KT. OBSERVATION requires WT."
  - INV-RIVER-IMMUTABLE: "Raw parquet files are write-once, never modified."
  - INV-DEXTER-ALWAYS-CLAIM: "All Dexter output enters as CLAIM, never FACT."
  - INV-COMMITMENT-THRESHOLD: "Only Formal Handoffs become beads."

PRINCIPLES:
  - Measure twice, cut once. Validate each phase before proceeding.
  - Report findings before making architectural decisions.
  - If uncertain about DECISION_1 (separate DB), ask G/CTO before building.
  - The bead path is the END STATE. JSON is backward compatibility.
  - Quality > Speed. Get it right.
```

---

## REPORT FORMAT

After each phase, report:

```yaml
PHASE_N_REPORT:
  status: PASS | FAIL | BLOCKED
  files_changed: [list with line counts]
  tests_added: N
  beads_written: N (for phases 3-4)
  issues_found: [any surprises]
  decision_needed: [anything requiring G/CTO input]
```

---

## SEQUENCING SUMMARY

```
Phase 1: Fix export bug           → 30 min  → UNBLOCKS everything
Phase 2: Build claim_writer.py    → 2-4 hrs → CORE BUILD (end-state module)
Phase 3: Wire pipeline dual-write → 1 hr    → CONNECTS producers to beads
Phase 4: Historical backfill      → 1-2 hrs → POPULATES 5 years of analytical CLAIMs
Phase 5: MIRROR display fixes     → 1-2 hrs → COSMETIC (data is already correct)
```

Phase 2 is the important one. Take your time. Study the existing FACT ingestion
path. Study governance_mapper.py. Follow the same patterns. Get signing right.
Get bi-temporal fields right. This module will ingest millions of beads over time.
It needs to be solid.
