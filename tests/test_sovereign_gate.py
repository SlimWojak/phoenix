"""
Tests for @sovereign_gate decorator and check_sovereign_gate (S59 T1).

INVARIANTS:
  INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS
  INV-ACTIVATION-ONLY-VIA-GUARD
  INV-CEREMONY-BLOCKS-ACTIVE
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from governance.halt import HaltSignalResult
from governance.lease import LeaseManager, LeaseStateMachine, NullBeadEmitter
from governance.lease_types import LeaseState
from governance.sovereign_gate import (
    CeremonyOverdueError,
    HaltActiveError,
    LeaseNotActiveError,
    SovereignGateError,
    check_sovereign_gate,
    sovereign_gate,
)

# ═══════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture()
def swarm_dir(tmp_path: Path) -> Path:
    swarm = tmp_path / "phoenix-swarm"
    swarm.mkdir()
    return swarm


@pytest.fixture()
def signal_file(swarm_dir: Path) -> Path:
    return swarm_dir / "HALT.signal"


def _write_halt(signal_file: Path, source: str = "TEST", reason: str = "testing") -> None:
    signal_file.write_text(json.dumps({"source": source, "reason": reason, "schema_version": 1}))


def _make_active_lease() -> LeaseStateMachine:
    from governance.lease_types import (
        Lease,
        LeaseBounds,
        LeaseDuration,
        LeaseIdentity,
        LeaseSubject,
    )

    lease = Lease(
        identity=LeaseIdentity(created_at=datetime.now(UTC), created_by="TEST"),
        subject=LeaseSubject(
            strategy_ref="TEST_STRAT_v1.0.0",
            strategy_hash="abc123",
        ),
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
    sm = LeaseStateMachine(lease=lease, bead_emitter=NullBeadEmitter())
    return sm


def _make_manager_with_active_lease(swarm_dir: Path) -> LeaseManager:
    """Create a LeaseManager with an active lease, patching halt for activation."""
    LeaseManager._instance = None
    manager = LeaseManager()

    no_halt = HaltSignalResult(halted=False)
    with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
        sm = _make_active_lease()
        sm.activate()
        manager._active_lease = sm

    return manager


# ═══════════════════════════════════════════════════════════════════════════
# HALT SIGNAL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestHaltBlocksCapital:
    """INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS"""

    def test_halt_present_blocks_activation(self, swarm_dir: Path, signal_file: Path) -> None:
        _write_halt(signal_file)
        with pytest.raises(HaltActiveError) as exc:
            check_sovereign_gate(
                require_active_lease=False,
                swarm_path=swarm_dir,
            )
        assert exc.value.source == "TEST"

    def test_halt_present_blocks_execution_entry(self, swarm_dir: Path, signal_file: Path) -> None:
        _write_halt(signal_file, source="OLYA", reason="suspicious activity")

        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def enter_position() -> str:
            return "should_not_reach"

        with pytest.raises(HaltActiveError) as exc:
            enter_position()
        assert exc.value.source == "OLYA"

    def test_halt_present_blocks_position_scaling(self, swarm_dir: Path, signal_file: Path) -> None:
        _write_halt(signal_file)

        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def scale_position(lots: float) -> float:
            return lots * 2

        with pytest.raises(HaltActiveError):
            scale_position(0.1)

    def test_halt_present_blocks_position_modification(
        self, swarm_dir: Path, signal_file: Path
    ) -> None:
        _write_halt(signal_file)

        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def modify_sl(new_sl: float) -> float:
            return new_sl

        with pytest.raises(HaltActiveError):
            modify_sl(1.1050)

    def test_halt_clear_proceeds(self, swarm_dir: Path) -> None:
        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def safe_action() -> str:
            return "ok"

        assert safe_action() == "ok"

    def test_gate_check_exception_fails_closed(self, swarm_dir: Path) -> None:
        with patch(
            "governance.sovereign_gate.check_halt_signal",
            side_effect=OSError("disk on fire"),
        ):
            with pytest.raises(SovereignGateError, match="fail-closed"):
                check_sovereign_gate(
                    require_active_lease=False,
                    swarm_path=swarm_dir,
                )


# ═══════════════════════════════════════════════════════════════════════════
# LEASE STATE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestLeaseStateGuard:
    """INV-ACTIVATION-ONLY-VIA-GUARD"""

    def test_no_active_lease_rejects(self, swarm_dir: Path) -> None:
        LeaseManager._instance = None
        manager = LeaseManager()

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(LeaseNotActiveError, match="ABSENT"):
                check_sovereign_gate(
                    require_active_lease=True,
                    swarm_path=swarm_dir,
                    lease_manager_fn=lambda: manager,
                )

    def test_expired_lease_rejects(self, swarm_dir: Path) -> None:
        manager = _make_manager_with_active_lease(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.expire()

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(LeaseNotActiveError, match="EXPIRED"):
                check_sovereign_gate(
                    require_active_lease=True,
                    swarm_path=swarm_dir,
                    lease_manager_fn=lambda: manager,
                )

    def test_draft_lease_rejects(self, swarm_dir: Path) -> None:
        LeaseManager._instance = None
        manager = LeaseManager()

        sm = _make_active_lease()
        manager._active_lease = sm

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(LeaseNotActiveError, match="DRAFT"):
                check_sovereign_gate(
                    require_active_lease=True,
                    swarm_path=swarm_dir,
                    lease_manager_fn=lambda: manager,
                )

    def test_active_lease_proceeds(self, swarm_dir: Path) -> None:
        manager = _make_manager_with_active_lease(swarm_dir)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            check_sovereign_gate(
                require_active_lease=True,
                swarm_path=swarm_dir,
                lease_manager_fn=lambda: manager,
            )


# ═══════════════════════════════════════════════════════════════════════════
# CEREMONY STUB TESTS (T5 wiring point)
# ═══════════════════════════════════════════════════════════════════════════


class TestCeremonyStub:
    """INV-CEREMONY-BLOCKS-ACTIVE"""

    def test_ceremony_future_proceeds(self, swarm_dir: Path) -> None:
        manager = _make_manager_with_active_lease(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = datetime.now(UTC) + timedelta(days=3)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            check_sovereign_gate(
                require_active_lease=True,
                swarm_path=swarm_dir,
                lease_manager_fn=lambda: manager,
            )

    def test_ceremony_overdue_blocks(self, swarm_dir: Path) -> None:
        manager = _make_manager_with_active_lease(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = datetime.now(UTC) - timedelta(hours=1)

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            with pytest.raises(CeremonyOverdueError):
                check_sovereign_gate(
                    require_active_lease=True,
                    swarm_path=swarm_dir,
                    lease_manager_fn=lambda: manager,
                )

    def test_ceremony_none_proceeds(self, swarm_dir: Path) -> None:
        """No ceremony requirement set → execution proceeds."""
        manager = _make_manager_with_active_lease(swarm_dir)
        sm = manager._active_lease
        assert sm is not None
        sm.lease.governance.next_review_due = None

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            check_sovereign_gate(
                require_active_lease=True,
                swarm_path=swarm_dir,
                lease_manager_fn=lambda: manager,
            )


# ═══════════════════════════════════════════════════════════════════════════
# DECORATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestDecoratorBehavior:
    """Decorator correctly wraps and preserves function behavior."""

    def test_decorator_passes_args(self, swarm_dir: Path) -> None:
        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def add(a: int, b: int) -> int:
            return a + b

        assert add(3, 4) == 7

    def test_decorator_passes_kwargs(self, swarm_dir: Path) -> None:
        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def greet(name: str, prefix: str = "Hello") -> str:
            return f"{prefix} {name}"

        assert greet("G", prefix="Yo") == "Yo G"

    def test_decorator_preserves_function_name(self, swarm_dir: Path) -> None:
        @sovereign_gate(require_active_lease=False, swarm_path=swarm_dir)
        def my_function() -> None:
            pass

        assert my_function.__name__ == "my_function"


# ═══════════════════════════════════════════════════════════════════════════
# LEASE ACTIVATION WIRING
# ═══════════════════════════════════════════════════════════════════════════


class TestActivationWiring:
    """LeaseStateMachine.activate() checks sovereign gate."""

    def test_activate_blocked_when_halted(self, swarm_dir: Path, signal_file: Path) -> None:
        _write_halt(signal_file)

        sm = _make_active_lease()
        with patch(
            "governance.sovereign_gate.check_halt_signal",
            return_value=HaltSignalResult(halted=True, source="G", reason="test"),
        ):
            result = sm.activate()

        from governance.lease_types import TransitionResult

        assert result == TransitionResult.REJECTED_INVALID_TRANSITION

    def test_activate_proceeds_when_clear(self) -> None:
        sm = _make_active_lease()

        no_halt = HaltSignalResult(halted=False)
        with patch("governance.sovereign_gate.check_halt_signal", return_value=no_halt):
            result = sm.activate()

        from governance.lease_types import TransitionResult

        assert result == TransitionResult.SUCCESS
        assert sm.state == LeaseState.ACTIVE
