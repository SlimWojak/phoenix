"""
S52 T2: Bounds auto-feed — sentinel fires on state update.

EXIT_GATE: T2_PASSIVE_BOUNDS
Proof: Bounds breach during position update → immediate halt.
       No manual caller needed.
"""

from __future__ import annotations

from datetime import UTC, datetime

from governance.lease import (
    LeaseInterpreter,
    LeaseStateMachine,
    NullBeadEmitter,
    create_lease_from_cartridge,
)
from governance.sentinel import (
    BoundsSentinel,
    GovernanceVerdict,
)


def _make_active_interpreter() -> LeaseInterpreter:
    """Create an active lease interpreter for testing."""
    lease = create_lease_from_cartridge(
        cartridge_ref="TEST_CARTRIDGE_v1.0.0",
        cartridge_hash="abc123",
        created_by="TEST",
        starts_at=datetime.now(UTC),
        duration_days=7,
        bounds={
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "daily_loss_limit_pct": 2.0,
            "allowed_pairs": ["EURUSD"],
            "allowed_pairs_mode": "ALL",
        },
    )
    emitter = NullBeadEmitter()
    sm = LeaseStateMachine(lease=lease, bead_emitter=emitter)
    sm.activate()
    return LeaseInterpreter(sm)


class TestBoundsAutoFeed:
    """INV-BOUNDS-PASSIVE-1: Bounds fire on every state update."""

    def test_pass_on_healthy_state(self):
        """No breach → PASS verdict."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
                "daily_loss_pct": 0.5,
            }
        )

        assert result.verdict == GovernanceVerdict.PASS

    def test_breach_drawdown(self):
        """Drawdown breach → FAIL verdict."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 6.0,
                "consecutive_losses": 0,
            }
        )

        assert result.verdict == GovernanceVerdict.FAIL_BOUNDS_BREACH
        assert "max_drawdown_pct" in result.breach_detail

    def test_breach_consecutive_losses(self):
        """Consecutive losses breach → FAIL verdict."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 5,
            }
        )

        assert result.verdict == GovernanceVerdict.FAIL_BOUNDS_BREACH
        assert "max_consecutive_losses" in result.breach_detail

    def test_breach_daily_loss(self):
        """Daily loss breach → FAIL verdict."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
                "daily_loss_pct": 3.0,
            }
        )

        assert result.verdict == GovernanceVerdict.FAIL_BOUNDS_BREACH
        assert "daily_loss_limit_pct" in result.breach_detail

    def test_halt_callback_fires_on_breach(self):
        """Halt callback is invoked on bounds breach."""
        interpreter = _make_active_interpreter()
        halts = []
        sentinel = BoundsSentinel(
            lease_interpreter=interpreter,
            halt_callback=lambda msg: halts.append(msg),
        )

        sentinel.intercept(
            {
                "current_drawdown_pct": 10.0,
                "consecutive_losses": 0,
            }
        )

        assert len(halts) == 1
        assert "SENTINEL_BOUNDS_BREACH" in halts[0]

    def test_no_callback_on_pass(self):
        """No halt callback when bounds are OK."""
        interpreter = _make_active_interpreter()
        halts = []
        sentinel = BoundsSentinel(
            lease_interpreter=interpreter,
            halt_callback=lambda msg: halts.append(msg),
        )

        sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
            }
        )

        assert len(halts) == 0

    def test_no_lease_returns_fail(self):
        """No active lease → FAIL_NO_LEASE."""
        sentinel = BoundsSentinel(lease_interpreter=None)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
            }
        )

        assert result.verdict == GovernanceVerdict.FAIL_NO_LEASE

    def test_metrics_track_checks(self):
        """Metrics track check count and breach count."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        sentinel.intercept({"current_drawdown_pct": 1.0, "consecutive_losses": 0})
        sentinel.intercept({"current_drawdown_pct": 6.0, "consecutive_losses": 0})
        sentinel.intercept({"current_drawdown_pct": 2.0, "consecutive_losses": 0})

        metrics = sentinel.get_metrics()
        assert metrics["check_count"] == 3
        assert metrics["breach_count"] == 1
