"""
Tests for CSO scalar field ban (S59 T4).

INV-CSO-NO-SCALAR-DECISIONS: No scalar fields in emitted CSESignal.
INV-CSO-NO-SCALAR-CONSUMPTION: No float/int score in routing/gating paths.
"""

from __future__ import annotations

from pathlib import Path

from cso.strategy_core import ReadinessReason, SetupResult, SetupStatus


class TestCSESignalNoScalars:
    """CSESignal emission boundary has no quality_score or confidence fields."""

    def test_cse_signal_has_readiness_reasons(self) -> None:
        from datetime import UTC, datetime

        from cso.scanner import CSESignal

        cse = CSESignal(
            signal_id="test-001",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            source="CSO",
            setup_type="FVG_ENTRY",
            readiness_reasons=["trend_aligned", "fvg_present", "bos_confirmed"],
            parameters={"entry": 1.1, "stop": 1.09, "target": 1.12, "risk_percent": 1.0},
            evidence_hash="abc123",
        )
        d = cse.to_dict()
        assert "readiness_reasons" in d
        assert "confidence" not in d
        assert "quality_score" not in d
        assert isinstance(d["readiness_reasons"], list)

    def test_cse_signal_readiness_are_strings(self) -> None:
        from datetime import UTC, datetime

        from cso.scanner import CSESignal

        cse = CSESignal(
            signal_id="test-002",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            source="CSO",
            setup_type="OTE_ENTRY",
            readiness_reasons=[r.value for r in ReadinessReason],
            parameters={"entry": 1.1, "stop": 1.09, "target": 1.12, "risk_percent": 1.0},
            evidence_hash="def456",
        )
        d = cse.to_dict()
        for reason in d["readiness_reasons"]:
            assert isinstance(reason, str), f"Expected str, got {type(reason)}"


class TestSetupResultEnum:
    """SetupResult uses readiness_reasons, not quality_score."""

    def test_setup_result_has_readiness_reasons(self) -> None:
        result = SetupResult(
            pair="EURUSD",
            status=SetupStatus.READY,
            readiness_reasons=[ReadinessReason.TREND_ALIGNED, ReadinessReason.FVG_PRESENT],
        )
        d = result.to_dict()
        assert "readiness_reasons" in d
        assert "quality_score" not in d

    def test_readiness_reasons_are_string_enum(self) -> None:
        for reason in ReadinessReason:
            assert isinstance(reason.value, str)
            assert not reason.value.isdigit(), f"Enum value {reason.value} looks numeric"


class TestScalarConsumptionLint:
    """CI-level lint: quality_score|confidence must not be used in routing paths."""

    def test_no_quality_score_in_cso_emission_code(self) -> None:
        """Scan cso/ Python files for quality_score in non-comment, non-test code."""
        cso_dir = Path(__file__).parent.parent / "cso"
        violations: list[str] = []

        allowlist = {
            "@property",
            "Deprecated",
            "def quality_score",
            "forbidden",
            "FORBIDDEN",
            "replacing",
            "replaces",
            '"quality_score"',
        }

        for py_file in cso_dir.rglob("*.py"):
            if "test" in py_file.name:
                continue
            for i, line in enumerate(py_file.read_text().splitlines(), 1):
                stripped = line.lstrip()
                if (
                    stripped.startswith("#")
                    or stripped.startswith('"""')
                    or stripped.startswith("'''")
                ):
                    continue
                if "quality_score" in stripped:
                    if not any(term in stripped for term in allowlist):
                        violations.append(f"{py_file.name}:{i}: {stripped}")

        assert violations == [], "quality_score found in CSO emission code:\n" + "\n".join(
            violations
        )

    def test_no_confidence_in_cse_signal_dict(self) -> None:
        """CSESignal.to_dict() must not contain 'confidence' key."""
        from datetime import UTC, datetime

        from cso.scanner import CSESignal

        cse = CSESignal(
            signal_id="lint-test",
            timestamp=datetime.now(UTC),
            pair="GBPUSD",
            source="CSO",
            setup_type="SWEEP_ENTRY",
            readiness_reasons=["trend_aligned"],
            parameters={"entry": 1.3, "stop": 1.29, "target": 1.32, "risk_percent": 1.0},
            evidence_hash="lint123",
        )
        d = cse.to_dict()
        assert "confidence" not in d, "CSESignal.to_dict() still emits 'confidence' field"
