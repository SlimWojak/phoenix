"""
S52 T3: CSE must carry River provenance.

EXIT_GATE: T3_FRESHNESS
Proof: CSESignal carries river_latest_bar_timestamp, river_knowledge_time,
       river_bar_hash_sample. Consumer rejects CSE without provenance.

CTO ADDENDUM 3_T3_PROVENANCE_REQUIRED:
  Three mandatory fields on every CSE. CSESignal without provenance is INVALID.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cso.consumer import CSEValidator


def _make_valid_cse(
    river_kt: datetime | None = None,
    include_provenance: bool = True,
) -> dict:
    """Build a valid CSE dict with all required fields."""
    now = river_kt or datetime.now(UTC)
    cse = {
        "cse_version": "1.0",
        "signal_id": "CSE-test001",
        "timestamp": now.isoformat(),
        "pair": "EURUSD",
        "source": "CSO",
        "setup_type": "asia_range_scalp",
        "confidence": 0.85,
        "parameters": {
            "entry": 1.0850,
            "stop": 1.0840,
            "target": 1.0870,
            "risk_percent": 1.0,
        },
        "evidence_hash": "a" * 64,
    }
    if include_provenance:
        cse["river_latest_bar_timestamp"] = now.isoformat()
        cse["river_knowledge_time"] = now.isoformat()
        cse["river_bar_hash_sample"] = "abc123def456"
    return cse


class TestCSEProvenanceRequired:
    """INV-CSE-PROVENANCE-1: Provenance fields are REQUIRED."""

    def test_valid_cse_with_provenance_passes(self):
        """CSE with all provenance fields validates."""
        validator = CSEValidator(schema_path=None)
        cse = _make_valid_cse()
        result = validator.validate(cse)
        assert result.valid, f"Unexpected errors: {result.errors}"

    def test_missing_provenance_rejected(self):
        """CSE without provenance fields is INVALID."""
        validator = CSEValidator(schema_path=None)
        cse = _make_valid_cse(include_provenance=False)
        result = validator.validate(cse)
        assert not result.valid
        assert any("river_latest_bar_timestamp" in e for e in result.errors)
        assert any("river_knowledge_time" in e for e in result.errors)
        assert any("river_bar_hash_sample" in e for e in result.errors)

    def test_partial_provenance_rejected(self):
        """CSE with only some provenance fields is still INVALID."""
        validator = CSEValidator(schema_path=None)
        cse = _make_valid_cse(include_provenance=False)
        cse["river_latest_bar_timestamp"] = datetime.now(UTC).isoformat()
        result = validator.validate(cse)
        assert not result.valid
        assert any("river_knowledge_time" in e for e in result.errors)

    def test_empty_string_provenance_rejected(self):
        """Empty string provenance is treated as missing."""
        validator = CSEValidator(schema_path=None)
        cse = _make_valid_cse(include_provenance=False)
        cse["river_latest_bar_timestamp"] = ""
        cse["river_knowledge_time"] = ""
        cse["river_bar_hash_sample"] = ""
        result = validator.validate(cse)
        assert not result.valid


class TestStaleCSERefused:
    """INV-CSE-FRESHNESS-1: Stale CSE refused at consumer (defense-in-depth)."""

    def test_fresh_cse_accepted(self):
        """CSE with recent river_knowledge_time passes."""
        validator = CSEValidator(schema_path=None)
        cse = _make_valid_cse(river_kt=datetime.now(UTC))
        result = validator.validate(cse)
        assert result.valid, f"Unexpected errors: {result.errors}"

    def test_stale_cse_rejected(self):
        """CSE with old river_knowledge_time is rejected."""
        validator = CSEValidator(schema_path=None)
        stale_time = datetime.now(UTC) - timedelta(minutes=15)
        cse = _make_valid_cse(river_kt=stale_time)
        result = validator.validate(cse)
        assert not result.valid
        assert any("stale" in e for e in result.errors)

    def test_very_stale_cse_rejected(self):
        """CSE from hours ago is definitively rejected."""
        validator = CSEValidator(schema_path=None)
        stale_time = datetime.now(UTC) - timedelta(hours=2)
        cse = _make_valid_cse(river_kt=stale_time)
        result = validator.validate(cse)
        assert not result.valid

    def test_borderline_cse_accepted(self):
        """CSE at 5 minutes old is still fresh enough."""
        validator = CSEValidator(schema_path=None)
        recent = datetime.now(UTC) - timedelta(minutes=5)
        cse = _make_valid_cse(river_kt=recent)
        result = validator.validate(cse)
        assert result.valid, f"Unexpected errors: {result.errors}"
