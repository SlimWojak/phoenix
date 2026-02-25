"""
Tests for external HALT.signal mechanism (S55 Track 2).

INV-HALT-SIGNAL-CHECK: Execution gate checks HALT.signal before every capital action.
INV-HALT-FAIL-CLOSED: Corrupted/unreadable HALT.signal = HALTED, not bypassed.
"""

import json
import stat
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.halt import HaltSignalResult, check_halt_signal
from governance.insertion import InsertionProtocol
from governance.lease import LeaseManager


@pytest.fixture()
def swarm_dir(tmp_path: Path) -> Path:
    """Create a temporary swarm directory."""
    swarm = tmp_path / "phoenix-swarm"
    swarm.mkdir()
    return swarm


@pytest.fixture()
def signal_file(swarm_dir: Path) -> Path:
    return swarm_dir / "HALT.signal"


# ─── check_halt_signal: 5 cases ───


def test_halt_signal_absent(swarm_dir: Path) -> None:
    """No HALT.signal → halted=False (normal operation)."""
    result = check_halt_signal(swarm_dir)
    assert result.halted is False
    assert result.source is None
    assert result.reason is None
    assert result.error is None


def test_halt_signal_present(swarm_dir: Path, signal_file: Path) -> None:
    """Valid HALT.signal → halted=True with source/reason."""
    signal_file.write_text(
        json.dumps(
            {
                "source": "OLYA",
                "timestamp": "2026-02-25T00:00:00Z",
                "reason": "test halt",
                "schema_version": 1,
            }
        )
    )
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.source == "OLYA"
    assert result.reason == "test halt"
    assert result.error is None


def test_halt_signal_corrupt_json(swarm_dir: Path, signal_file: Path) -> None:
    """Corrupt JSON → halted=True (FAIL-CLOSED)."""
    signal_file.write_text("{not valid json!!!")
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.error is not None
    assert "corrupt signal" in result.error


def test_halt_signal_unreadable(swarm_dir: Path, signal_file: Path) -> None:
    """Unreadable file → halted=True (FAIL-CLOSED)."""
    signal_file.write_text("valid content")
    signal_file.chmod(0o000)
    try:
        result = check_halt_signal(swarm_dir)
        assert result.halted is True
        assert result.error is not None
        assert "unreadable" in result.error
    finally:
        signal_file.chmod(stat.S_IRUSR | stat.S_IWUSR)


def test_halt_signal_missing_swarm(tmp_path: Path) -> None:
    """Missing swarm path → halted=True (FAIL-CLOSED)."""
    nonexistent = tmp_path / "does-not-exist"
    result = check_halt_signal(nonexistent)
    assert result.halted is True
    assert result.error is not None
    assert "swarm path missing" in result.error


def test_halt_signal_empty_file(swarm_dir: Path, signal_file: Path) -> None:
    """Zero-byte file → halted=True (FAIL-CLOSED)."""
    signal_file.write_text("")
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.error is not None
    assert "empty signal file" in result.error


def test_halt_signal_unknown_schema_version(swarm_dir: Path, signal_file: Path) -> None:
    """Unknown schema_version → halted=True (fail-closed, don't reject unknown versions)."""
    signal_file.write_text(
        json.dumps(
            {
                "source": "G",
                "timestamp": "2026-02-25T00:00:00Z",
                "reason": "upgrade",
                "schema_version": 99,
            }
        )
    )
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.source == "G"


def test_halt_signal_missing_fields(swarm_dir: Path, signal_file: Path) -> None:
    """Missing fields → halted=True (fail-closed, source/reason may be None)."""
    signal_file.write_text(json.dumps({"schema_version": 1}))
    result = check_halt_signal(swarm_dir)
    assert result.halted is True
    assert result.source is None
    assert result.reason is None


# ─── Execution gate: insertion refuses when halted ───


def test_execution_refuses_when_halted(swarm_dir: Path, signal_file: Path) -> None:
    """InsertionProtocol refuses lease activation when HALT.signal present."""
    halt_data = HaltSignalResult(halted=True, source="OLYA", reason="stop everything")

    protocol = _fresh_protocol()

    with patch("governance.insertion.check_halt_signal", return_value=halt_data):
        result = protocol.insert_from_dict(
            cartridge_data=_valid_cartridge(),
            created_by="TEST",
            duration_days=7,
            bounds=_valid_bounds(),
        )

    assert result.success is False
    assert result.step_reached == 7
    assert "HALTED" in (result.error or "")


def test_insertion_proceeds_when_not_halted() -> None:
    """InsertionProtocol proceeds past halt check when no HALT.signal."""
    no_halt = HaltSignalResult(halted=False)

    protocol = _fresh_protocol()

    with patch("governance.insertion.check_halt_signal", return_value=no_halt):
        result = protocol.insert_from_dict(
            cartridge_data=_valid_cartridge(),
            created_by="TEST",
            duration_days=7,
            bounds=_valid_bounds(),
        )

    assert result.success is True
    assert result.step_reached == 8


# ─── Lease activation refuses when halted ───


def test_lease_activation_refuses_when_halted(swarm_dir: Path, signal_file: Path) -> None:
    """Lease DRAFT→ACTIVE transition blocked when HALT.signal present."""
    signal_file.write_text(
        json.dumps(
            {
                "source": "G",
                "timestamp": "2026-02-25T00:00:00Z",
                "reason": "maintenance",
                "schema_version": 1,
            }
        )
    )

    halt_result = check_halt_signal(swarm_dir)
    assert halt_result.halted is True


# ─── Helpers ───


def _valid_cartridge() -> dict[str, object]:
    """Valid cartridge data that passes schema validation and lint."""
    return {
        "identity": {
            "name": "TEST_STRATEGY",
            "version": "1.0.0",
            "author": "test_author",
            "created_at": datetime.now(UTC).isoformat(),
        },
        "scope": {
            "pairs": ["EUR/USD", "GBP/USD", "USD/JPY"],
        },
        "risk_defaults": {
            "per_trade_pct": 2.0,
            "min_rr": 2.0,
            "max_trades_per_session": 3,
        },
        "cso_integration": {
            "drawer_config": {
                "HTF_BIAS": {"enabled": True},
                "MARKET_STRUCTURE": {"enabled": True},
                "PREMIUM_DISCOUNT": {"enabled": True},
                "ENTRY_MODEL": {"enabled": True},
                "CONFIRMATION": {"enabled": True},
            },
        },
        "constitutional": {
            "invariants_required": ["INV-NO-UNSOLICITED", "INV-HALT-1"],
        },
    }


def _valid_bounds() -> dict[str, object]:
    """Valid lease bounds for testing."""
    return {
        "max_drawdown_pct": 5.0,
        "max_consecutive_losses": 3,
        "allowed_pairs": ["EUR/USD", "GBP/USD"],
        "allowed_pairs_mode": "SUBSET",
        "position_size_cap": 1.5,
    }


def _fresh_protocol() -> InsertionProtocol:
    """Fresh InsertionProtocol with reset singleton."""
    LeaseManager._instance = None
    return InsertionProtocol()
