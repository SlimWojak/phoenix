"""
Tests for kill_manager loud-fail behavior (S56 Track 2).

Verifies that bead write failures propagate instead of being silently swallowed.
"""

from unittest.mock import MagicMock

import pytest

from monitoring.kill_manager import KillManager


class FailingBeadStore:
    """BeadStore that always raises on write."""

    def write_dict(self, bead_dict: dict) -> None:
        raise OSError("Disk full — bead write failed")

    def query_sql(self, sql: str) -> list:
        raise OSError("Database corrupted — query failed")


def test_set_kill_flag_failure_propagates() -> None:
    """set_kill_flag raises when bead store write fails."""
    manager = KillManager(bead_store=FailingBeadStore())

    with pytest.raises(OSError, match="Disk full"):
        manager.set_kill_flag(
            strategy_id="TEST_STRAT",
            reason="test kill",
            triggered_by="SYSTEM",
        )


def test_lift_kill_flag_failure_propagates() -> None:
    """lift_kill_flag raises when bead store write fails."""
    manager = KillManager(bead_store=MagicMock())
    manager._bead_store.write_dict = MagicMock()
    manager.set_kill_flag("TEST_STRAT", "test", "SYSTEM")

    manager._bead_store = FailingBeadStore()

    with pytest.raises(OSError, match="Disk full"):
        manager.lift_kill_flag("TEST_STRAT", "MANUAL", "test lift")


def test_get_kill_flag_query_failure_returns_none() -> None:
    """get_kill_flag returns None on query failure (graceful degradation)."""
    manager = KillManager(bead_store=FailingBeadStore())
    result = manager.get_kill_flag("NONEXISTENT")
    assert result is None


def test_get_active_kills_query_failure_returns_empty() -> None:
    """get_active_kills returns empty list on query failure."""
    manager = KillManager(bead_store=FailingBeadStore())
    result = manager.get_active_kills()
    assert result == []


def test_set_kill_flag_success_with_store() -> None:
    """set_kill_flag succeeds when bead store write works."""
    store = MagicMock()
    manager = KillManager(bead_store=store)

    flag = manager.set_kill_flag("TEST_STRAT", "test", "SYSTEM")

    assert flag.active is True
    assert flag.strategy_id == "TEST_STRAT"
    store.write_dict.assert_called_once()
