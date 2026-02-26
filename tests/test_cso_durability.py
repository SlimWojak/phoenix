"""
Tests for CSO rejection/signal durability (S60 T2).

Pre-bridge preparation: CSERejectionRecord persists to disk.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cso.consumer import CSOConsumer


@pytest.fixture()
def rejection_store(tmp_path: Path) -> Path:
    return tmp_path / "cso_rejections.jsonl"


def _make_invalid_cse() -> dict:
    """CSE that will fail validation (missing required fields)."""
    return {
        "signal_id": "CSE-test-reject",
        "timestamp": datetime.now(UTC).isoformat(),
        "pair": "EURUSD",
        "source": "CSO",
        "setup_type": "test",
        "readiness_reasons": ["trend_aligned"],
        "parameters": {"entry": 1.0, "stop": 0.99, "target": 1.02, "risk_percent": 1.0},
        "evidence_hash": "abc123",
    }


def _make_valid_cse() -> dict:
    return {
        "cse_version": "1.0.0",
        "signal_id": "CSE-test-valid",
        "timestamp": datetime.now(UTC).isoformat(),
        "pair": "EURUSD",
        "source": "CSO",
        "setup_type": "test",
        "readiness_reasons": ["trend_aligned", "fvg_present"],
        "parameters": {"entry": 1.0, "stop": 0.99, "target": 1.02, "risk_percent": 1.0},
        "evidence_hash": "abc123",
        "river_latest_bar_timestamp": datetime.now(UTC).isoformat(),
        "river_knowledge_time": datetime.now(UTC).isoformat(),
        "river_bar_hash_sample": "deadbeef",
    }


class TestRejectionDurability:
    """CSO rejection records persist to disk."""

    def test_rejection_persists_to_jsonl(self, rejection_store: Path) -> None:
        consumer = CSOConsumer(rejection_store_path=rejection_store)

        cse = _make_invalid_cse()
        result = consumer.consume(cse)

        assert not result.success
        assert rejection_store.exists()

        lines = [line for line in rejection_store.read_text().strip().split("\n") if line]
        assert len(lines) == 1

        data = json.loads(lines[0])
        assert data["cse_id"] == "CSE-test-reject"
        assert "reason" in data
        assert "timestamp" in data

    def test_multiple_rejections_accumulate(self, rejection_store: Path) -> None:
        consumer = CSOConsumer(rejection_store_path=rejection_store)

        for i in range(3):
            cse = _make_invalid_cse()
            cse["signal_id"] = f"CSE-reject-{i}"
            consumer.consume(cse)

        lines = [line for line in rejection_store.read_text().strip().split("\n") if line]
        assert len(lines) == 3

    def test_valid_cse_no_rejection_stored(self, rejection_store: Path) -> None:
        consumer = CSOConsumer(rejection_store_path=rejection_store)

        cse = _make_valid_cse()
        result = consumer.consume(cse)

        assert result.success
        assert not rejection_store.exists()

    def test_no_store_path_still_works(self) -> None:
        """Consumer without rejection_store_path works (in-memory only)."""
        consumer = CSOConsumer()
        cse = _make_invalid_cse()
        result = consumer.consume(cse)
        assert not result.success
        assert len(consumer.rejections) == 1
