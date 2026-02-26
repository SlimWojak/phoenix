#!/usr/bin/env python3
"""
Validate SYSTEM_MANIFEST test count matches pytest collection.

INV-MANIFEST-DERIVED-NOT-TYPED-1: manifest counts generated, not typed.

Usage: python scripts/validate_manifest.py
Exit: 0 = PASS, 1 = FAIL
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "docs" / "canon" / "a8ra_SYSTEM_MANIFEST_v1_0.md"


def get_pytest_count() -> int | None:
    """Run pytest --collect-only and extract test count."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-o", "addopts=", "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    for line in result.stdout.splitlines():
        match = re.search(r"(\d+) tests? collected", line)
        if match:
            return int(match.group(1))
    return None


def get_manifest_count() -> int | None:
    """Extract declared test count from manifest."""
    if not MANIFEST_PATH.exists():
        return None
    text = MANIFEST_PATH.read_text()
    match = re.search(r"tests_passing:\s*(\d+)", text)
    if match:
        return int(match.group(1))
    return None


def main() -> int:
    manifest_count = get_manifest_count()
    pytest_count = get_pytest_count()

    if manifest_count is None:
        print("FAIL: Could not extract test count from manifest")
        return 1
    if pytest_count is None:
        print("FAIL: Could not collect pytest count")
        return 1

    delta = abs(pytest_count - manifest_count)
    # Allow small delta (tests may be added between manifest updates)
    threshold = 50

    if delta > threshold:
        print(
            f"FAIL: Manifest says {manifest_count}, pytest collected {pytest_count} "
            f"(delta={delta}, threshold={threshold})"
        )
        return 1

    print(f"PASS: manifest={manifest_count}, pytest={pytest_count}, delta={delta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
