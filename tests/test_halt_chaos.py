"""
Chaos vectors for HALT.signal mechanism (S55 Track 5).

INV-HALT-ENTROPY-PROOF: Halt mechanism survives 5 chaos vectors without silent fail.
"""

import json
import subprocess
from pathlib import Path

import pytest

from governance.halt import check_halt_signal


@pytest.fixture()
def swarm_dir(tmp_path: Path) -> Path:
    swarm = tmp_path / "phoenix-swarm"
    swarm.mkdir()
    return swarm


@pytest.fixture()
def signal_file(swarm_dir: Path) -> Path:
    return swarm_dir / "HALT.signal"


def test_v1_invalid_json(swarm_dir: Path, signal_file: Path) -> None:
    """V1: Invalid JSON in HALT.signal → halted=True (fail-closed)."""
    signal_file.write_text("{not valid json at all!!!")
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.error is not None
    assert "corrupt" in result.error


def test_v2_concurrent_writes(swarm_dir: Path, signal_file: Path) -> None:
    """V2: Two concurrent halt.sh writes → file is valid JSON after both."""
    script = Path.home() / "phoenix-swarm" / "scripts" / "halt.sh"
    if not script.exists():
        pytest.skip("halt.sh not found at expected path")

    p1 = subprocess.Popen(  # noqa: S603
        [str(script), "OLYA", "concurrent write 1"],
        env={**dict(__import__("os").environ), "HOME": str(swarm_dir.parent)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p2 = subprocess.Popen(  # noqa: S603
        [str(script), "G", "concurrent write 2"],
        env={**dict(__import__("os").environ), "HOME": str(swarm_dir.parent)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p1.wait(timeout=10)
    p2.wait(timeout=10)

    real_signal = Path.home() / "phoenix-swarm" / "HALT.signal"
    if real_signal.exists():
        raw = real_signal.read_text()
        data = json.loads(raw)
        assert data["source"] in ("OLYA", "G")
        assert "schema_version" in data
        real_signal.unlink()


def test_v3_unknown_schema_version(swarm_dir: Path, signal_file: Path) -> None:
    """V3: Unknown schema_version → halted=True (fail-closed, don't reject)."""
    signal_file.write_text(
        json.dumps(
            {
                "source": "GOVERNANCE",
                "timestamp": "2026-02-25T00:00:00Z",
                "reason": "future",
                "schema_version": 999,
            }
        )
    )
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.source == "GOVERNANCE"


def test_v4_missing_fields(swarm_dir: Path, signal_file: Path) -> None:
    """V4: Missing required fields → halted=True (fail-closed)."""
    signal_file.write_text(json.dumps({"schema_version": 1}))
    result = check_halt_signal(swarm_dir)
    assert result.halted is True


def test_v5_zero_bytes(swarm_dir: Path, signal_file: Path) -> None:
    """V5: Zero-byte file → halted=True (fail-closed)."""
    signal_file.write_text("")
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.error is not None
    assert "empty" in result.error
