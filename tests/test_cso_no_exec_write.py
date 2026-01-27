"""
Test CSO No Exec Write — Verify T1 cannot write execution_state.

SPRINT: S27.0
EXIT_GATE: read_only_proven
INVARIANT: INV-GOV-NO-T1-WRITE-EXEC
"""

import sys
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestCSONoExecWrite:
    """Test CSO cannot write to execution_state."""

    def test_write_to_execution_state_raises(self):
        """
        Attempting to write execution_state raises CSOWriteViolation.

        EXIT_GATE: read_only_proven
        """
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation) as exc:
            observer._guard_write("execution_state", "set_position")

        assert exc.value.target == "execution_state"
        assert "INV-GOV-NO-T1-WRITE-EXEC" in str(exc.value)

    def test_write_to_orders_raises(self):
        """Attempting to write orders raises CSOWriteViolation."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("orders", "submit_order")

    def test_write_to_positions_raises(self):
        """Attempting to write positions raises CSOWriteViolation."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("positions", "update_position")

    def test_write_to_capital_raises(self):
        """Attempting to write capital raises CSOWriteViolation."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("capital", "allocate")

    def test_write_to_broker_raises(self):
        """Attempting to write broker raises CSOWriteViolation."""
        from cso import CSOObserver, CSOWriteViolation

        observer = CSOObserver()

        with pytest.raises(CSOWriteViolation):
            observer._guard_write("broker", "connect")

    def test_read_is_allowed(self):
        """Reading is allowed (no exception)."""
        from cso import CSOObserver

        observer = CSOObserver()

        # These should NOT raise (not forbidden targets)
        observer._guard_write("observation", "emit")
        observer._guard_write("bead", "create")
        observer._guard_write("comprehension", "hash")

    def test_observer_tier_is_t1(self):
        """Observer is T1 tier."""
        from cso import CSOObserver
        from governance import ModuleTier

        observer = CSOObserver()
        assert observer.module_tier == ModuleTier.T1

    def test_observer_enforces_no_write_exec(self):
        """Observer declares INV-GOV-NO-T1-WRITE-EXEC."""
        from cso import CSOObserver

        observer = CSOObserver()
        assert "INV-GOV-NO-T1-WRITE-EXEC" in observer.enforced_invariants
