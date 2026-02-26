"""
Tests for manifest_writer projection honesty (S59 T3).

INV-PROJECTION-NEVER-OPTIMISTIC: Projection degrades to stale/unknown/error
on exception, never GREEN/ABSENT.
"""

from __future__ import annotations

from unittest.mock import patch

from state.manifest_writer import (
    _calculate_age_seconds,
    _get_lease_component_color,
    get_lease_state,
    get_next_seq,
)


class TestLeaseComponentColor:
    """_get_lease_component_color never returns GREEN on exception."""

    def test_runtime_error_returns_red(self) -> None:
        from governance.lease import LeaseManager

        original_new = LeaseManager.__new__

        def _exploding_new(cls: type) -> object:
            raise RuntimeError("lease subsystem crash")

        LeaseManager.__new__ = _exploding_new  # type: ignore[assignment]
        try:
            result = _get_lease_component_color()
        finally:
            LeaseManager.__new__ = original_new  # type: ignore[assignment]

        assert result == "RED", f"Expected RED on RuntimeError, got {result}"


class TestGetLeaseState:
    """get_lease_state never returns ABSENT on exception."""

    def test_import_error_returns_error_not_absent(self) -> None:
        with patch("builtins.__import__", side_effect=ImportError("no governance")):
            result = get_lease_state()
        assert result["status"] == "ERROR"

    def test_runtime_error_returns_error_not_absent(self) -> None:
        with patch("governance.lease.LeaseManager", side_effect=RuntimeError("boom")):
            result = get_lease_state()
        assert result["status"] == "ERROR"


class TestCalculateAgeSeconds:
    """_calculate_age_seconds returns -1 sentinel, not 9999."""

    def test_empty_string_returns_sentinel(self) -> None:
        assert _calculate_age_seconds("") == -1

    def test_invalid_format_returns_sentinel(self) -> None:
        assert _calculate_age_seconds("not-a-date") == -1

    def test_valid_iso_returns_positive(self) -> None:
        from datetime import UTC, timedelta
        from datetime import datetime as dt

        recent = (dt.now(UTC) - timedelta(seconds=30)).isoformat()
        result = _calculate_age_seconds(recent)
        assert 25 <= result <= 35

    def test_z_suffix_parsed(self) -> None:
        from datetime import UTC, timedelta
        from datetime import datetime as dt

        recent = (dt.now(UTC) - timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        result = _calculate_age_seconds(recent)
        assert 5 <= result <= 15


class TestGetNextSeq:
    """get_next_seq returns -1 sentinel, not 1."""

    def test_corrupt_seq_file_returns_sentinel(self) -> None:
        with patch("state.manifest_writer.SEQ_FILE") as mock_file:
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = "not_a_number"
            result = get_next_seq()
        assert result == -1

    def test_write_failure_returns_sentinel(self) -> None:
        with patch("state.manifest_writer.SEQ_FILE") as mock_file:
            mock_file.exists.return_value = True
            mock_file.read_text.return_value = "5"
            mock_file.write_text.side_effect = OSError("disk full")
            result = get_next_seq()
        assert result == -1
