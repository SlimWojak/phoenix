"""
S52 T2: Heartbeat liveness — normal operation proves sentinel is alive.

EXIT_GATE: T2_PASSIVE_BOUNDS
Proof: Sentinel heartbeat observable under normal operation.
"""

from __future__ import annotations

from datetime import UTC, datetime

from governance.lease import (
    LeaseInterpreter,
    LeaseStateMachine,
    NullBeadEmitter,
    create_lease_from_cartridge,
)
from governance.sentinel import BoundsSentinel


def _make_active_interpreter() -> LeaseInterpreter:
    lease = create_lease_from_cartridge(
        cartridge_ref="TEST_SENTINEL_v1.0.0",
        cartridge_hash="abc",
        created_by="TEST",
        starts_at=datetime.now(UTC),
        duration_days=7,
        bounds={
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "allowed_pairs": ["EURUSD"],
            "allowed_pairs_mode": "ALL",
        },
    )
    emitter = NullBeadEmitter()
    sm = LeaseStateMachine(lease=lease, bead_emitter=emitter)
    sm.activate()
    return LeaseInterpreter(sm)


class TestHeartbeatLiveness:
    """Sentinel updates heartbeat on every intercept."""

    def test_heartbeat_updated_on_intercept(self):
        """Intercept updates last_execution_timestamp."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        assert sentinel.get_last_execution_timestamp() is None

        sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
            }
        )

        ts = sentinel.get_last_execution_timestamp()
        assert ts is not None
        assert (datetime.now(UTC) - ts).total_seconds() < 1.0

    def test_heartbeat_updates_on_every_call(self):
        """Each intercept updates the timestamp."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        sentinel.intercept({"current_drawdown_pct": 1.0, "consecutive_losses": 0})
        ts1 = sentinel.get_last_execution_timestamp()

        sentinel.intercept({"current_drawdown_pct": 2.0, "consecutive_losses": 0})
        ts2 = sentinel.get_last_execution_timestamp()

        assert ts2 >= ts1

    def test_heartbeat_updates_even_on_breach(self):
        """Heartbeat updates even when bounds are breached."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        sentinel.intercept({"current_drawdown_pct": 10.0, "consecutive_losses": 0})

        ts = sentinel.get_last_execution_timestamp()
        assert ts is not None

    def test_heartbeat_updates_even_on_no_lease(self):
        """Heartbeat updates even when no lease is active."""
        sentinel = BoundsSentinel(lease_interpreter=None)

        sentinel.intercept({"current_drawdown_pct": 1.0, "consecutive_losses": 0})

        ts = sentinel.get_last_execution_timestamp()
        assert ts is not None

    def test_latency_tracked(self):
        """Sentinel result includes latency measurement."""
        interpreter = _make_active_interpreter()
        sentinel = BoundsSentinel(lease_interpreter=interpreter)

        result = sentinel.intercept(
            {
                "current_drawdown_pct": 1.0,
                "consecutive_losses": 0,
            }
        )

        assert result.check_latency_ns > 0
        assert result.check_latency_ms >= 0
