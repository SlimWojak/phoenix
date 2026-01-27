"""
Test No Live Orders — Verify INV-EXEC-NO-CAPITAL.

SPRINT: S27.0
EXIT_GATE: no_capital
INVARIANT: INV-EXEC-NO-CAPITAL
"""

import subprocess
import sys
from pathlib import Path

import pytest

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))


class TestNoLiveOrders:
    """Test execution has no capital actions."""

    def test_guard_blocks_submit_order(self):
        """guard_capital_action blocks submit_order."""
        from execution import CapitalActionForbiddenError, guard_capital_action

        with pytest.raises(CapitalActionForbiddenError) as exc:
            guard_capital_action("submit_order")

        assert "INV-EXEC-NO-CAPITAL" in str(exc.value)

    def test_guard_blocks_execute_order(self):
        """guard_capital_action blocks execute_order."""
        from execution import CapitalActionForbiddenError, guard_capital_action

        with pytest.raises(CapitalActionForbiddenError):
            guard_capital_action("execute_order")

    def test_guard_blocks_broker_connect(self):
        """guard_capital_action blocks broker connect."""
        from execution import CapitalActionForbiddenError, guard_capital_action

        with pytest.raises(CapitalActionForbiddenError):
            guard_capital_action("broker.connect")

    def test_guard_blocks_send_order(self):
        """guard_capital_action blocks send_order."""
        from execution import CapitalActionForbiddenError, guard_capital_action

        with pytest.raises(CapitalActionForbiddenError):
            guard_capital_action("send_order")

    def test_guard_allows_create_intent(self):
        """guard_capital_action allows creating intents."""
        from execution import guard_capital_action

        # These should NOT raise
        guard_capital_action("create_intent")
        guard_capital_action("gate_intent")
        guard_capital_action("log_blocked")


class TestGrepForbiddenPatterns:
    """Test codebase for forbidden patterns."""

    def test_no_submit_order_in_execution(self):
        """No submit_order calls in execution module."""
        exec_dir = PHOENIX_ROOT / "execution"

        result = subprocess.run(
            ["grep", "-r", "submit_order", str(exec_dir)], capture_output=True, text=True
        )

        # Filter out comments and test files
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        actual_calls = [
            line
            for line in lines
            if "#" not in line.split("submit_order")[0]
            and "test_" not in line
            and ".yaml" not in line
        ]

        assert len(actual_calls) == 0, f"Found submit_order: {actual_calls}"

    def test_no_execute_order_in_execution(self):
        """No execute_order calls in execution module."""
        exec_dir = PHOENIX_ROOT / "execution"

        result = subprocess.run(
            ["grep", "-r", "execute_order", str(exec_dir)], capture_output=True, text=True
        )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        actual_calls = [
            line
            for line in lines
            if "#" not in line.split("execute_order")[0]
            and "test_" not in line
            and ".yaml" not in line
        ]

        assert len(actual_calls) == 0, f"Found execute_order: {actual_calls}"

    def test_no_broker_connect_in_execution(self):
        """No broker.connect calls in execution module."""
        exec_dir = PHOENIX_ROOT / "execution"

        result = subprocess.run(
            ["grep", "-r", "broker.connect", str(exec_dir)], capture_output=True, text=True
        )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        actual_calls = [
            line
            for line in lines
            if "#" not in line.split("broker")[0] and "test_" not in line and ".yaml" not in line
        ]

        assert len(actual_calls) == 0


class TestIntentNotOrder:
    """Test that intents are not orders."""

    def test_intent_has_no_execute_method(self):
        """ExecutionIntent has no execute method."""
        from execution import ExecutionIntent

        assert not hasattr(ExecutionIntent, "execute")
        assert not hasattr(ExecutionIntent, "submit")
        assert not hasattr(ExecutionIntent, "send")

    def test_factory_has_no_submit_method(self):
        """IntentFactory has no submit method."""
        from execution import IntentFactory

        assert not hasattr(IntentFactory, "submit_order")
        assert not hasattr(IntentFactory, "execute")
        assert not hasattr(IntentFactory, "send_to_broker")
