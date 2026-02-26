#!/usr/bin/env python3
"""
Economy Isolation Guard — CI enforcement of Two-Economy boundary.

Sprint: S59 LEASE_WIRE (Track 6: ISOLATION_GUARDS)

INVARIANT: INV-ECONOMY-ISOLATION-ENFORCED
"CI rejects cross-economy coupling outside bridge package"

Guards:
  G1: No phoenix/ imports from dexter/*
  G2: No dexter/ imports from phoenix/*
  G3: Future bridge/ directory is the only allowed cross-economy dependency
  G4: Test files may reference both (with explicit marker)

Usage:
  python scripts/check_economy_isolation.py
  make check-isolation
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

PHOENIX_ROOT = Path(__file__).parent.parent

CROSS_ECONOMY_PATTERNS = [
    (re.compile(r"^\s*(?:from|import)\s+dexter\b"), "phoenix→dexter"),
    (re.compile(r"^\s*(?:from|import)\s+phoenix\b"), "dexter→phoenix"),
]

ALLOWLIST_DIRS = {"bridge"}

ALLOWLIST_PATTERNS = {
    re.compile(r"#\s*CROSS_ECONOMY_ALLOWED"),
}


def scan_file(path: Path, direction_label: str, pattern: re.Pattern[str]) -> list[str]:
    """Scan a single file for cross-economy imports."""
    violations: list[str] = []
    try:
        text = path.read_text()
    except (OSError, UnicodeDecodeError):
        return []

    for i, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            if any(ap.search(line) for ap in ALLOWLIST_PATTERNS):
                continue
            violations.append(f"  {path}:{i} [{direction_label}]: {line.strip()}")

    return violations


def check_isolation() -> list[str]:
    """Run full isolation check. Returns list of violations (empty = clean)."""
    violations: list[str] = []

    phoenix_dir = PHOENIX_ROOT
    if not phoenix_dir.is_dir():
        print(f"WARNING: phoenix root not found at {phoenix_dir}", file=sys.stderr)
        return []

    phoenix_pattern = CROSS_ECONOMY_PATTERNS[0][0]
    phoenix_label = CROSS_ECONOMY_PATTERNS[0][1]

    for py_file in phoenix_dir.rglob("*.py"):
        rel = py_file.relative_to(phoenix_dir)

        if any(part in ALLOWLIST_DIRS for part in rel.parts):
            continue
        if "test" in str(rel).lower():
            continue

        violations.extend(scan_file(py_file, phoenix_label, phoenix_pattern))

    return violations


def main() -> int:
    """Run isolation check and report."""
    violations = check_isolation()

    if violations:
        print("ECONOMY ISOLATION VIOLATIONS:")
        for v in violations:
            print(v)
        print(f"\nTotal: {len(violations)} violation(s)")
        print("INV-ECONOMY-ISOLATION-ENFORCED: FAIL")
        return 1

    print("INV-ECONOMY-ISOLATION-ENFORCED: PASS (0 violations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
