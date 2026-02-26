"""
S53 T2: CSE Contract Fidelity Tests.

EXIT_GATE: GATE_S53_2
Proves:
  - Scanner emits schema-valid CSE (emit-time validation)
  - Consumer accepts valid CSE
  - Consumer rejects invalid CSE with reason enum
  - cse_version has single source

INVARIANTS:
  INV-CSE-EMIT-COMPLETENESS-1: scanner CSE matches schema requireds
  INV-CSE-VERSION-SINGLE-SOURCE-1: cse_version defined once, imported everywhere
"""

from __future__ import annotations

from datetime import UTC, datetime

from cso.constants import CSE_VERSION
from cso.consumer import (
    CSEValidator,
    CSOConsumer,
    RejectionReason,
)
from cso.scanner import CSESignal


def _make_valid_cse_dict(
    *,
    include_version: bool = True,
    include_provenance: bool = True,
    river_kt: datetime | None = None,
) -> dict:
    """Build a schema-valid CSE dict."""
    now = river_kt or datetime.now(UTC)
    cse: dict = {
        "signal_id": "CSE-test0001",
        "timestamp": now.isoformat(),
        "pair": "EURUSD",
        "source": "CSO",
        "setup_type": "asia_range_scalp",
        "readiness_reasons": ["trend_aligned", "fvg_present", "liquidity_swept", "bos_confirmed"],
        "parameters": {
            "entry": 1.0850,
            "stop": 1.0840,
            "target": 1.0870,
            "risk_percent": 1.0,
        },
        "evidence_hash": "a" * 64,
    }
    if include_version:
        cse["cse_version"] = CSE_VERSION
    if include_provenance:
        cse["river_latest_bar_timestamp"] = now.isoformat()
        cse["river_knowledge_time"] = now.isoformat()
        cse["river_bar_hash_sample"] = "abc123def456"
    return cse


class TestScannerEmitsSchemaCompleteCSE:
    """INV-CSE-EMIT-COMPLETENESS-1: Scanner CSE must match schema requireds."""

    def test_cse_signal_includes_version(self):
        """CSESignal default includes cse_version from constant."""
        sig = CSESignal(
            signal_id="CSE-test",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            source="CSO",
            setup_type="test",
            readiness_reasons=["trend_aligned", "fvg_present", "bos_confirmed"],
            parameters={"entry": 1.0, "stop": 0.99, "target": 1.02, "risk_percent": 1.0},
            evidence_hash="a" * 64,
            river_latest_bar_timestamp=datetime.now(UTC).isoformat(),
            river_knowledge_time=datetime.now(UTC).isoformat(),
            river_bar_hash_sample="abc123",
        )
        d = sig.to_dict()
        assert d["cse_version"] == CSE_VERSION
        assert d["river_latest_bar_timestamp"] is not None
        assert d["river_knowledge_time"] is not None
        assert d["river_bar_hash_sample"] is not None

    def test_cse_signal_to_dict_validates(self):
        """CSESignal.to_dict() passes CSEValidator when fully populated."""
        now = datetime.now(UTC)
        sig = CSESignal(
            signal_id="CSE-test",
            timestamp=now,
            pair="EURUSD",
            source="CSO",
            setup_type="test",
            readiness_reasons=["trend_aligned", "fvg_present", "bos_confirmed"],
            parameters={"entry": 1.0850, "stop": 1.0840, "target": 1.0870, "risk_percent": 1.0},
            evidence_hash="a" * 64,
            river_latest_bar_timestamp=now.isoformat(),
            river_knowledge_time=now.isoformat(),
            river_bar_hash_sample="abc123",
        )
        validator = CSEValidator()
        result = validator.validate(sig.to_dict())
        assert result.valid, f"Unexpected errors: {result.errors}"


class TestScannerToConsumerAcceptsValidCSE:
    """Contract: valid CSE passes consumer pipeline."""

    def test_valid_cse_accepted(self):
        consumer = CSOConsumer()
        cse = _make_valid_cse_dict()
        result = consumer.consume(cse)
        assert result.success, f"Unexpected failure: {result.error}"
        assert len(consumer.rejections) == 0


class TestScannerToConsumerRejectsInvalidCSE:
    """Contract: invalid CSE rejected with structured reason."""

    def test_missing_version_rejected(self):
        consumer = CSOConsumer()
        cse = _make_valid_cse_dict(include_version=False)
        result = consumer.consume(cse)
        assert not result.success
        assert len(consumer.rejections) == 1
        assert consumer.rejections[0].reason == RejectionReason.MISSING_VERSION

    def test_missing_provenance_rejected(self):
        consumer = CSOConsumer()
        cse = _make_valid_cse_dict(include_provenance=False)
        result = consumer.consume(cse)
        assert not result.success
        assert len(consumer.rejections) == 1
        assert consumer.rejections[0].reason == RejectionReason.MISSING_PROVENANCE

    def test_rejection_record_structured(self):
        """Rejection record has all required fields."""
        consumer = CSOConsumer()
        cse = _make_valid_cse_dict(include_version=False)
        consumer.consume(cse)
        rec = consumer.rejections[0]
        assert rec.cse_id == "CSE-test0001"
        assert isinstance(rec.reason, RejectionReason)
        assert isinstance(rec.missing_fields, list)
        assert isinstance(rec.timestamp, datetime)


class TestCSEVersionSingleSource:
    """INV-CSE-VERSION-SINGLE-SOURCE-1: cse_version defined once."""

    def test_constant_is_string(self):
        assert isinstance(CSE_VERSION, str)
        assert len(CSE_VERSION) > 0

    def test_scanner_uses_constant(self):
        sig = CSESignal(
            signal_id="test",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            source="CSO",
            setup_type="test",
            readiness_reasons=["trend_aligned", "fvg_present", "bos_confirmed"],
            parameters={"entry": 1.0, "stop": 0.99, "target": 1.02, "risk_percent": 1.0},
            evidence_hash="a" * 64,
        )
        assert sig.cse_version == CSE_VERSION
