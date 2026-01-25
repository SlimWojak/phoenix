#!/usr/bin/env python3
"""
Schema Verification Script — Standalone verification of ICT_DATA_CONTRACT.md

Run with nex venv:
    cd ~/nex && source .venv/bin/activate
    python ~/phoenix/contracts/verify_schema.py

Returns exit code 0 if all checks pass, 1 otherwise.
"""

import sys
from pathlib import Path

def main():
    try:
        import pandas as pd
        import hashlib
        import json
    except ImportError as e:
        print(f"ERROR: Missing dependency: {e}")
        print("Run with nex venv: cd ~/nex && source .venv/bin/activate")
        return 1
    
    # Contract constants
    EXPECTED_SCHEMA_HASH = "b848ffe506fd3fff"
    EXPECTED_COLUMNS = 472
    EXPECTED_BOOLEAN_MARKERS = 110
    
    # Path to enriched data
    NEX_ENRICHED_PATH = Path.home() / "nex" / "nex_lab" / "data" / "features" / "EURUSD_1m_enriched.parquet"
    
    if not NEX_ENRICHED_PATH.exists():
        print(f"ERROR: Enriched parquet not found: {NEX_ENRICHED_PATH}")
        return 1
    
    print("=" * 60)
    print("ICT DATA CONTRACT VERIFICATION")
    print("Contract: phoenix/contracts/ICT_DATA_CONTRACT.md v1.0.0")
    print("=" * 60)
    print()
    
    # Load data
    print(f"Loading: {NEX_ENRICHED_PATH}")
    df = pd.read_parquet(NEX_ENRICHED_PATH)
    print(f"Loaded {len(df):,} rows")
    print()
    
    all_pass = True
    
    # 1. Schema hash
    schema = [(col, str(df[col].dtype)) for col in df.columns]
    schema_str = json.dumps(schema, sort_keys=True)
    actual_hash = hashlib.sha256(schema_str.encode()).hexdigest()[:16]
    
    hash_match = actual_hash == EXPECTED_SCHEMA_HASH
    print(f"[{'PASS' if hash_match else 'FAIL'}] Schema Hash")
    print(f"       Expected: {EXPECTED_SCHEMA_HASH}")
    print(f"       Actual:   {actual_hash}")
    all_pass = all_pass and hash_match
    print()
    
    # 2. Column count
    col_count = len(df.columns)
    col_match = col_count == EXPECTED_COLUMNS
    print(f"[{'PASS' if col_match else 'FAIL'}] Column Count")
    print(f"       Expected: {EXPECTED_COLUMNS}")
    print(f"       Actual:   {col_count}")
    all_pass = all_pass and col_match
    print()
    
    # 3. Boolean markers
    bool_cols = [col for col in df.columns if df[col].dtype == 'bool']
    bool_match = len(bool_cols) == EXPECTED_BOOLEAN_MARKERS
    print(f"[{'PASS' if bool_match else 'FAIL'}] Boolean Markers")
    print(f"       Expected: {EXPECTED_BOOLEAN_MARKERS}")
    print(f"       Actual:   {len(bool_cols)}")
    all_pass = all_pass and bool_match
    print()
    
    # 4. Timestamp UTC
    ts_tz = str(df['timestamp'].dt.tz)
    tz_match = ts_tz == "UTC"
    print(f"[{'PASS' if tz_match else 'FAIL'}] Timestamp Timezone")
    print(f"       Expected: UTC")
    print(f"       Actual:   {ts_tz}")
    all_pass = all_pass and tz_match
    print()
    
    # 5. Volume semantics (informational)
    neg_vol = (df['volume'] < 0).sum()
    zero_vol = (df['volume'] == 0).sum()
    print(f"[INFO] Volume Semantics")
    print(f"       Negative (sentinel): {neg_vol:,}")
    print(f"       Zero: {zero_vol:,}")
    print(f"       Comparability: NONE (per contract)")
    print()
    
    # Summary
    print("=" * 60)
    if all_pass:
        print("CONTRACT VERIFICATION: PASS")
        print("Schema lockdown confirmed. Mirror Test may proceed.")
    else:
        print("CONTRACT VERIFICATION: FAIL")
        print("Schema drift detected. Fix before Mirror Test.")
    print("=" * 60)
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
