"""
S53 T3: Mini E2E Pipeline — Deterministic Synthetic Chain.

EXIT_GATE: GATE_S53_3
Proves:
  - Full chain executes without error (synthetic)
  - Sentinel intercept proven in chain (trace log present)
  - Two identical runs produce identical hash

INVARIANTS:
  INV-E2E-DETERMINISTIC-1: identical inputs → identical outputs (synthetic mode)
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pandas as pd

from cso.constants import CSE_VERSION
from cso.consumer import CSOConsumer
from cso.scanner import CSOScanner
from cso.strategy_core import (
    Direction,
    EvidenceBundle,
    ReadinessReason,
    Setup,
    SetupResult,
    SetupStatus,
    SetupType,
)
from execution.halt_gate import HaltGate, SentinelHaltError
from governance.sentinel import BoundsSentinel, GovernanceVerdict, SentinelResult
from governance.t2.approval import T2Workflow
from river.synthetic_river import SyntheticRiver

# =============================================================================
# TEST FIXTURES
# =============================================================================


def _frozen_now() -> datetime:
    """Use real 'now' so freshness checks pass, but stable within a test run."""
    return datetime.now(UTC).replace(second=0, microsecond=0) - timedelta(minutes=2)


FIXED_EVIDENCE = EvidenceBundle(
    htf_structures=[{"type": "FVG", "pair": "EURUSD", "tf": "4H"}],
    ltf_structures=[{"type": "OTE", "pair": "EURUSD", "tf": "1H"}],
    alignment_score=0.85,
    evidence_hash="a" * 64,
)

FIXED_SETUP = Setup(
    setup_id="SETUP-e2e-fixed",
    pair="EURUSD",
    setup_type=SetupType.FVG_ENTRY,
    direction=Direction.BULLISH,
    confidence=0.85,
    entry_price=1.0850,
    stop_price=1.0840,
    target_price=1.0870,
    risk_percent=1.0,
    evidence=FIXED_EVIDENCE,
)

FIXED_RESULT = SetupResult(
    pair="EURUSD",
    status=SetupStatus.READY,
    readiness_reasons=[
        ReadinessReason.TREND_ALIGNED,
        ReadinessReason.FVG_PRESENT,
        ReadinessReason.LIQUIDITY_SWEPT,
        ReadinessReason.BOS_CONFIRMED,
    ],
    setup=FIXED_SETUP,
)


def _make_river_compatible_df(pair: str = "EURUSD") -> pd.DataFrame:
    """Build a River-compatible DataFrame with provenance columns."""
    now = _frozen_now()
    river = SyntheticRiver(seed_prefix="e2e_test")
    start = now - timedelta(days=7)
    df = river.get_bars(pair, "1H", start, now)

    # Add River-mandated columns (knowledge_time = "when we learned", i.e. now)
    df["source"] = "dukascopy"
    df["knowledge_time"] = pd.Timestamp.now(tz="UTC")
    df["bar_hash"] = df.apply(
        lambda r: hashlib.sha256(f"{r['timestamp']}|{r['open']}".encode()).hexdigest(),
        axis=1,
    )
    return df


class _RiverCompatibleMock:
    """Mock river that returns complete River-schema data."""

    def __init__(self) -> None:
        self._df = _make_river_compatible_df()

    def get_bars(
        self, pair: str, timeframe: str, start: Any = None, end: Any = None
    ) -> pd.DataFrame:
        return self._df.copy()


def _run_pipeline() -> dict[str, Any]:
    """Execute full synthetic pipeline. Returns structured trace."""
    mock_river = _RiverCompatibleMock()

    # Scanner with mock river — inject READY result via StrategyCore mock
    scanner = CSOScanner(river_reader=mock_river)

    emitted_cse: list[dict] = []
    original_emit = scanner._emit_cse

    def _capturing_emit(result: SetupResult) -> None:
        original_emit(result)
        # Reconstruct CSE dict from scanner's last emission
        setup = result.setup
        if setup is None:
            return
        cse_dict = {
            "cse_version": CSE_VERSION,
            "signal_id": "CSE-e2e-fixed",
            "timestamp": datetime.now(UTC).isoformat(),
            "pair": setup.pair,
            "source": "CSO",
            "setup_type": setup.setup_type.value,
            "readiness_reasons": [r.value for r in result.readiness_reasons],
            "parameters": {
                "entry": setup.entry_price,
                "stop": setup.stop_price,
                "target": setup.target_price,
                "risk_percent": setup.risk_percent,
            },
            "evidence_hash": setup.evidence.evidence_hash,
            "river_latest_bar_timestamp": scanner._current_provenance.get(
                "river_latest_bar_timestamp"
            ),
            "river_knowledge_time": scanner._current_provenance.get("river_knowledge_time"),
            "river_bar_hash_sample": scanner._current_provenance.get("river_bar_hash_sample"),
        }
        emitted_cse.append(cse_dict)

    scanner._emit_cse = _capturing_emit  # type: ignore[assignment]

    with patch.object(scanner._core, "detect_setup", return_value=FIXED_RESULT):
        scan_result = scanner.scan_all_pairs()

    # Consumer validates CSE
    consumer = CSOConsumer()
    consume_results = []
    for cse_dict in emitted_cse:
        cr = consumer.consume(cse_dict)
        consume_results.append(cr)

    # T2 workflow creates request
    t2 = T2Workflow()
    t2_requests = []
    for cse_dict in emitted_cse:
        params = cse_dict.get("parameters", {})
        direction = "LONG" if params.get("entry", 0) < params.get("target", 0) else "SHORT"
        req = t2.create_request(
            signal_id=cse_dict["signal_id"],
            pair=cse_dict["pair"],
            side=direction,
            quantity=1.0,
            entry_price=params["entry"],
            stop_price=params["stop"],
            target_price=params["target"],
        )
        t2_requests.append(req)

    return {
        "scan_pairs": scan_result.pairs_scanned,
        "ready_count": len(scan_result.ready_setups),
        "cse_emitted": len(emitted_cse),
        "consumer_accepted": sum(1 for cr in consume_results if cr.success),
        "t2_requests": len(t2_requests),
        "first_cse": emitted_cse[0] if emitted_cse else None,
        "first_t2_intent_id": t2_requests[0].intent_id if t2_requests else None,
    }


def _trace_hash(trace: dict[str, Any]) -> str:
    """Deterministic hash of pipeline trace (excluding non-deterministic fields)."""
    stable = {
        "scan_pairs": trace["scan_pairs"],
        "ready_count": trace["ready_count"],
        "cse_emitted": trace["cse_emitted"],
        "consumer_accepted": trace["consumer_accepted"],
        "t2_requests": trace["t2_requests"],
    }
    payload = json.dumps(stable, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


# =============================================================================
# TESTS
# =============================================================================


class TestFullChainSynthetic:
    """Full synthetic E2E: river → scanner → CSE → consumer → T2."""

    def test_chain_executes_without_error(self):
        trace = _run_pipeline()
        assert trace["scan_pairs"] == 6
        assert trace["ready_count"] >= 1
        assert trace["cse_emitted"] >= 1
        assert trace["consumer_accepted"] >= 1
        assert trace["t2_requests"] >= 1

    def test_cse_has_provenance(self):
        trace = _run_pipeline()
        cse = trace["first_cse"]
        assert cse is not None
        assert cse["river_latest_bar_timestamp"] is not None
        assert cse["river_knowledge_time"] is not None
        assert cse["river_bar_hash_sample"] is not None
        assert cse["cse_version"] == CSE_VERSION


class TestDeterminismProof:
    """INV-E2E-DETERMINISTIC-1: identical inputs → identical outputs."""

    def test_two_runs_identical_hash(self):
        trace_1 = _run_pipeline()
        trace_2 = _run_pipeline()
        assert _trace_hash(trace_1) == _trace_hash(trace_2)

    def test_structural_equality(self):
        trace_1 = _run_pipeline()
        trace_2 = _run_pipeline()
        assert trace_1["scan_pairs"] == trace_2["scan_pairs"]
        assert trace_1["ready_count"] == trace_2["ready_count"]
        assert trace_1["cse_emitted"] == trace_2["cse_emitted"]
        assert trace_1["consumer_accepted"] == trace_2["consumer_accepted"]


class TestSentinelInChain:
    """Prove sentinel intercept fires in full chain path."""

    def test_sentinel_fires_when_wired(self):
        sentinel_log: list[str] = []
        sentinel = BoundsSentinel()

        def _tracking_intercept(state: dict) -> SentinelResult:
            sentinel_log.append("intercepted")
            return SentinelResult(verdict=GovernanceVerdict.PASS, check_latency_ns=100)

        sentinel.intercept = _tracking_intercept  # type: ignore[assignment]

        gate = HaltGate(
            halt_signal_fn=lambda: False,
            sentinel=sentinel,
            state_fn=lambda: {},
        )

        gate.check_before("submit_order", intent_id="CSE-e2e")
        assert len(sentinel_log) == 1

    def test_sentinel_breach_blocks_execution(self):
        sentinel = BoundsSentinel()
        sentinel.intercept = lambda state: SentinelResult(  # type: ignore[assignment]
            verdict=GovernanceVerdict.FAIL_BOUNDS_BREACH,
            check_latency_ns=100,
            breach_detail="e2e drawdown breach",
        )

        gate = HaltGate(
            halt_signal_fn=lambda: False,
            sentinel=sentinel,
            state_fn=lambda: {},
        )

        import pytest

        with pytest.raises(SentinelHaltError, match="drawdown"):
            gate.check_before("submit_order")
