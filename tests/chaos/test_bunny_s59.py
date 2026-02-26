"""
Chaos Bunny S59 — Sovereign Gate race conditions and concurrent stress.

CV1: Halt fires mid-activate() call
CV2: Halt fires mid-execution-entry
CV3: Halt fires mid-position-scaling
CV4: 10 threads — 5 activating, 5 firing halt simultaneously
"""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.halt import HaltSignalResult
from governance.lease import LeaseStateMachine, NullBeadEmitter
from governance.lease_types import (
    Lease,
    LeaseBounds,
    LeaseDuration,
    LeaseIdentity,
    LeaseSubject,
    TransitionResult,
)
from governance.sovereign_gate import (
    HaltActiveError,
    SovereignGateError,
    sovereign_gate,
)


def _make_lease() -> Lease:
    return Lease(
        identity=LeaseIdentity(created_at=datetime.now(UTC), created_by="CHAOS"),
        subject=LeaseSubject(strategy_ref="CHAOS_STRAT_v1.0.0", strategy_hash="chaos"),
        duration=LeaseDuration(
            starts_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            duration_days=7,
        ),
        bounds=LeaseBounds(
            max_drawdown_pct=5.0,
            max_consecutive_losses=3,
            allowed_pairs=["EURUSD"],
            allowed_pairs_mode="ALL",
        ),
    )


@pytest.fixture()
def swarm_dir(tmp_path: Path) -> Path:
    swarm = tmp_path / "phoenix-swarm"
    swarm.mkdir()
    return swarm


@pytest.fixture()
def signal_file(swarm_dir: Path) -> Path:
    return swarm_dir / "HALT.signal"


class TestCV1HaltMidActivate:
    """CV1: Halt fires mid-activate() — race condition."""

    def test_halt_during_activation_rejects(self, swarm_dir: Path, signal_file: Path) -> None:
        """Halt signal appearing during activate() causes rejection."""
        call_count = 0

        def halt_appears_on_second_call(path: Path | None = None) -> HaltSignalResult:
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                return HaltSignalResult(halted=True, source="OLYA", reason="mid-activate")
            return HaltSignalResult(halted=False)

        sm = LeaseStateMachine(lease=_make_lease(), bead_emitter=NullBeadEmitter())

        with patch(
            "governance.sovereign_gate.check_halt_signal", side_effect=halt_appears_on_second_call
        ):
            result1 = sm.activate()

        assert result1 == TransitionResult.SUCCESS

        sm2 = LeaseStateMachine(lease=_make_lease(), bead_emitter=NullBeadEmitter())
        with patch(
            "governance.sovereign_gate.check_halt_signal", side_effect=halt_appears_on_second_call
        ):
            result2 = sm2.activate()

        assert result2 == TransitionResult.REJECTED_INVALID_TRANSITION


class TestCV2HaltMidExecution:
    """CV2: Halt fires mid-execution-entry."""

    def test_halt_blocks_decorated_entry(self, swarm_dir: Path, signal_file: Path) -> None:
        signal_file.write_text(
            json.dumps({"source": "G", "reason": "mid-exec", "schema_version": 1})
        )

        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def execute_entry(pair: str) -> str:
            return f"entered {pair}"

        with pytest.raises(HaltActiveError):
            execute_entry("EURUSD")


class TestCV3HaltMidScaling:
    """CV3: Halt fires mid-position-scaling."""

    def test_halt_blocks_scaling_operation(self, swarm_dir: Path, signal_file: Path) -> None:
        signal_file.write_text(
            json.dumps({"source": "OLYA", "reason": "scaling halt", "schema_version": 1})
        )

        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def scale_position(current: float, factor: float) -> float:
            return current * factor

        with pytest.raises(HaltActiveError):
            scale_position(0.1, 2.0)


class TestCV4ConcurrentHaltActivate:
    """CV4: 10 threads — 5 activating, 5 firing halt simultaneously."""

    def test_concurrent_activate_and_halt(self, swarm_dir: Path, signal_file: Path) -> None:
        results: list[str] = []
        lock = threading.Lock()
        halt_fired = threading.Event()

        def activator(thread_id: int) -> None:
            sm = LeaseStateMachine(lease=_make_lease(), bead_emitter=NullBeadEmitter())
            try:
                time.sleep(0.01 * thread_id)

                def check_with_file(path: Path | None = None) -> HaltSignalResult:
                    if signal_file.exists():
                        return HaltSignalResult(halted=True, source="CV4")
                    return HaltSignalResult(halted=False)

                with patch(
                    "governance.sovereign_gate.check_halt_signal", side_effect=check_with_file
                ):
                    result = sm.activate()

                with lock:
                    results.append(f"activate_{thread_id}={result.value}")
            except SovereignGateError:
                with lock:
                    results.append(f"activate_{thread_id}=GATE_REJECT")

        def halt_writer(thread_id: int) -> None:
            time.sleep(0.01 * thread_id)
            signal_file.write_text(
                json.dumps({"source": "CV4", "reason": f"halt_{thread_id}", "schema_version": 1})
            )
            halt_fired.set()
            with lock:
                results.append(f"halt_{thread_id}=WRITTEN")

        threads: list[threading.Thread] = []
        for i in range(5):
            threads.append(threading.Thread(target=activator, args=(i,)))
        for i in range(5):
            threads.append(threading.Thread(target=halt_writer, args=(i,)))

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        success_count = sum(1 for r in results if "SUCCESS" in r)
        reject_count = sum(1 for r in results if "REJECT" in r or "GATE_REJECT" in r)
        halt_count = sum(1 for r in results if "WRITTEN" in r)

        assert halt_count >= 1, "At least one halt should have been written"
        assert success_count + reject_count == 5, f"All 5 activators should resolve: {results}"
