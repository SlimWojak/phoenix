#!/usr/bin/env python3
"""
Deployment Audit — Pre-live environment check.

INV-DEPLOYMENT-AUDIT: Security invariants cover deployment config, not just code.

Usage: python scripts/deployment_audit.py
Output: structured JSON {pass: bool, checks: [...]}
Exit: 0 = PASS, 1 = FAIL
"""

from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _check_env_var(name: str, required: bool = True) -> dict:
    """Check if an environment variable is set."""
    value = os.environ.get(name)
    present = value is not None and value != ""
    return {
        "check": f"env:{name}",
        "pass": present or not required,
        "detail": "set" if present else ("MISSING (required)" if required else "not set (optional)"),
    }


def _check_port(host: str, port: int, label: str) -> dict:
    """Check if a port is reachable."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        reachable = result == 0
    except OSError:
        reachable = False

    return {
        "check": f"port:{label}({host}:{port})",
        "pass": reachable,
        "detail": "reachable" if reachable else "not reachable",
    }


def _check_path(path: Path, label: str) -> dict:
    """Check if a path exists."""
    return {
        "check": f"path:{label}",
        "pass": path.exists(),
        "detail": str(path),
    }


def _check_config_mode() -> dict:
    """Check that no live mode is enabled accidentally."""
    mode = os.environ.get("PHOENIX_MODE", "PAPER")
    valid_modes = {"PAPER", "SHADOW", "LIVE", "BACKTEST"}
    return {
        "check": "config:PHOENIX_MODE",
        "pass": mode in valid_modes,
        "detail": f"mode={mode}" + (" (WARNING: LIVE)" if mode == "LIVE" else ""),
    }


def main() -> int:
    checks: list[dict] = []

    # Environment variables
    checks.append(_check_env_var("RIVER_ROOT", required=False))
    checks.append(_check_env_var("IBKR_PORT", required=False))

    # Config mode
    checks.append(_check_config_mode())

    # Key paths
    river_root = Path(os.environ.get("RIVER_ROOT", str(Path.home() / "phoenix-river")))
    checks.append(_check_path(river_root, "RIVER_ROOT"))
    checks.append(_check_path(REPO_ROOT / "schemas" / "cse_schema.yaml", "CSE_SCHEMA"))
    checks.append(_check_path(REPO_ROOT / "config" / "pairs.yaml", "PAIRS_CONFIG"))

    # IBKR Gateway ports
    ibkr_port = int(os.environ.get("IBKR_PORT", "4002"))
    checks.append(_check_port("127.0.0.1", ibkr_port, "IBKR_GATEWAY"))

    all_pass = all(c["pass"] for c in checks)

    output = {
        "pass": all_pass,
        "checks": checks,
        "repo_root": str(REPO_ROOT),
    }

    print(json.dumps(output, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
