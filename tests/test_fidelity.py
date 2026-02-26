"""
S53 T5: Execution Fidelity + Deployment Audit tests.

EXIT_GATE: GATE_S53_5 + GATE_S53_6
Proves:
  - FidelityRecord emitted on every fill
  - Deployment audit produces structured JSON pass/fail

INVARIANTS:
  INV-EXECUTION-FIDELITY: Intent vs fill delta tracked
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from execution.broker_stub import PaperBrokerStub
from execution.fidelity import SLIPPAGE_ALERT_BPS, FidelityRecord, compute_fidelity
from execution.intent import Direction, ExecutionIntent, IntentStatus, IntentType


def _make_intent(
    intent_id: str = "INT-test001",
    entry_price: float = 1.0850,
) -> ExecutionIntent:
    """Build a minimal ExecutionIntent for testing."""
    return ExecutionIntent(
        intent_id=intent_id,
        intent_type=IntentType.ENTRY,
        status=IntentStatus.PENDING,
        created_at=datetime.now(UTC),
        expires_at=None,
        symbol="EURUSD",
        direction=Direction.LONG,
        size=1.0,
        entry_price=entry_price,
        stop_loss=1.0840,
        take_profit=1.0870,
        source_bead_id=None,
        source_state_hash="test_hash",
    )


class TestFidelityRecordEmittedOnFill:
    """INV-EXECUTION-FIDELITY: every fill produces a fidelity record."""

    def test_fidelity_record_on_submit(self):
        broker = PaperBrokerStub(halt_check_fn=lambda: False)
        intent = _make_intent()

        result = broker.submit_order(intent)
        assert result.success

        assert len(broker.fidelity_log) == 1
        rec = broker.fidelity_log[0]
        assert rec.intent_id == "INT-test001"
        assert rec.expected_price == 1.0850
        assert rec.actual_price == 1.0850
        assert rec.venue == "PAPER"

    def test_multiple_fills_track_all(self):
        broker = PaperBrokerStub(halt_check_fn=lambda: False)
        broker.submit_order(_make_intent("INT-001"))
        broker.submit_order(_make_intent("INT-002"))

        assert len(broker.fidelity_log) == 2
        assert broker.fidelity_log[0].intent_id == "INT-001"
        assert broker.fidelity_log[1].intent_id == "INT-002"

    def test_paper_mode_zero_slippage(self):
        rec = compute_fidelity("INT-001", 1.0850, 1.0850, "PAPER")
        assert rec.slippage_abs == 0.0
        assert rec.slippage_bps == 0.0
        assert not rec.alert

    def test_slippage_alert_threshold(self):
        rec = compute_fidelity("INT-001", 1.0850, 1.0860, "IBKR")
        assert rec.slippage_bps > 0
        assert abs(rec.slippage_bps) < SLIPPAGE_ALERT_BPS

        big_slip = compute_fidelity("INT-002", 1.0850, 1.0950, "IBKR")
        assert big_slip.alert

    def test_fidelity_record_immutable(self):
        rec = compute_fidelity("INT-001", 1.0850, 1.0850, "PAPER")
        with pytest.raises(AttributeError):
            rec.venue = "IBKR"  # type: ignore[misc]


class TestDeploymentAudit:
    """INV-DEPLOYMENT-AUDIT: structured audit output."""

    def test_audit_produces_json(self):
        result = subprocess.run(
            [sys.executable, "scripts/deployment_audit.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        output = json.loads(result.stdout)
        assert "pass" in output
        assert "checks" in output
        assert isinstance(output["checks"], list)
        assert len(output["checks"]) > 0

    def test_each_check_has_required_fields(self):
        result = subprocess.run(
            [sys.executable, "scripts/deployment_audit.py"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        output = json.loads(result.stdout)
        for check in output["checks"]:
            assert "check" in check
            assert "pass" in check
            assert "detail" in check
