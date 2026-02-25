"""
Tests for config boot-time validation (S56 Track 4).

INV-CONFIG-VALID-ON-BOOT: Boot-time validation fails loud on missing critical config.
"""

import pytest

from config.schema import ExecutionMode, PhoenixConfig


def test_offline_mode_validates_clean() -> None:
    """Offline mode requires no IB credentials."""
    config = PhoenixConfig(execution_mode=ExecutionMode.OFFLINE)
    errors = config.validate_boot()
    assert errors == []


def test_paper_mode_missing_ib_creds_raises() -> None:
    """Paper mode without account_id raises ValueError."""
    config = PhoenixConfig(
        execution_mode=ExecutionMode.PAPER,
        ibkr={"account_id": ""},
    )
    with pytest.raises(ValueError, match="INV-CONFIG-VALID-ON-BOOT"):
        config.validate_boot()


def test_live_mode_missing_ib_creds_raises() -> None:
    """Live mode without account_id raises ValueError."""
    config = PhoenixConfig(
        execution_mode=ExecutionMode.LIVE,
        ibkr={"account_id": ""},
    )
    with pytest.raises(ValueError, match="INV-CONFIG-VALID-ON-BOOT"):
        config.validate_boot()


def test_paper_mode_with_creds_validates() -> None:
    """Paper mode with account_id validates clean."""
    config = PhoenixConfig(
        execution_mode=ExecutionMode.PAPER,
        ibkr={"account_id": "DU1234567"},
    )
    errors = config.validate_boot()
    assert errors == []


def test_invalid_db_path_raises() -> None:
    """Invalid river data path raises ValueError."""
    config = PhoenixConfig(
        river={"data_path": "/nonexistent/deeply/nested/path/river.db"},
    )
    with pytest.raises(ValueError, match="river.data_path parent does not exist"):
        config.validate_boot()
