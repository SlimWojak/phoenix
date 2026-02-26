#!/usr/bin/env python3
"""
Validate INVARIANT_REGISTRY.yaml — count matches declared, test refs resolve.

INV-REGISTRY-CONSISTENCY-1: registry count matches file entries.

Usage: python scripts/validate_registry.py
Exit: 0 = PASS, 1 = FAIL
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY_PATH = REPO_ROOT / "INVARIANT_REGISTRY.yaml"


def main() -> int:
    if not REGISTRY_PATH.exists():
        print(f"FAIL: Registry not found: {REGISTRY_PATH}")
        return 1

    with open(REGISTRY_PATH) as f:
        data = yaml.safe_load(f)

    invariants = data.get("invariants", [])
    actual_count = len(invariants)

    # Extract declared count from header comment
    declared_count: int | None = None
    with open(REGISTRY_PATH) as f:
        for line in f:
            if "Declared count:" in line:
                try:
                    declared_count = int(line.split("Declared count:")[1].strip().split()[0])
                except (ValueError, IndexError):
                    pass
                break

    errors: list[str] = []

    if declared_count is not None and declared_count != actual_count:
        errors.append(
            f"Declared count {declared_count} != actual {actual_count}"
        )

    # Verify test_refs paths resolve (skip cross-repo refs)
    missing_tests: list[str] = []
    cross_repo_refs: list[str] = []
    for inv in invariants:
        inv_id = inv.get("id", "UNKNOWN")
        for ref in inv.get("test_refs", []):
            if ref.startswith("dexter/") or ref.startswith("../"):
                cross_repo_refs.append(f"{inv_id}: {ref}")
                continue
            ref_path = REPO_ROOT / ref
            if not ref_path.exists():
                missing_tests.append(f"{inv_id}: {ref}")

    if missing_tests:
        errors.append(f"Missing test files: {missing_tests}")

    # Verify all entries have required fields
    for inv in invariants:
        for field in ("id", "tier", "domain", "status"):
            if field not in inv:
                errors.append(f"{inv.get('id', 'UNKNOWN')}: missing field '{field}'")

    if errors:
        print("FAIL: Registry validation errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    note = f" ({len(cross_repo_refs)} cross-repo refs skipped)" if cross_repo_refs else ""
    print(f"PASS: {actual_count} invariants, all fields valid, test refs checked{note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
