"""
Paper Broker Stub — Mock broker for execution testing.

SPRINT: S28.C
STATUS: MOCK_SIGNALS
CAPITAL: PAPER_ONLY

Capabilities:
- Receive order intent
- Simulate fill (immediate, for v0)
- Track position state
- Calculate P&L (simplified v0)

P&L_v0 (SIMPLIFIED):
- P&L = (exit_price - entry_price) * size * direction_multiplier
- NO fees (documented limitation)
- NO slippage (documented limitation)

CONSTRAINTS:
- PAPER ONLY — no real broker connection
- Deterministic fills (for replay)
- Halt-integrated

INVARIANTS:
- INV-GOV-HALT-BEFORE-ACTION: halt check before order
- INV-CONTRACT-1: deterministic execution
"""

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from .intent import ExecutionIntent, IntentType
from .position import Position, PositionRegistry

# =============================================================================
# EXCEPTIONS
# =============================================================================


class BrokerHaltedError(Exception):
    """Raised when broker operations attempted during halt."""

    pass


class OrderRejectedError(Exception):
    """Raised when order is rejected."""

    def __init__(self, intent_id: str, reason: str):
        self.intent_id = intent_id
        self.reason = reason
        super().__init__(f"Order {intent_id} rejected: {reason}")


# =============================================================================
# ORDER RESULT
# =============================================================================


class FillType(Enum):
    """Fill execution type."""

    IMMEDIATE = "IMMEDIATE"  # Instant fill at specified price
    MARKET = "MARKET"  # Fill at current market price
    LIMIT = "LIMIT"  # Fill at limit price or better


@dataclass
class OrderResult:
    """Result of order execution."""

    success: bool
    intent_id: str
    position_id: str | None
    fill_price: float | None
    fill_size: float | None
    fill_type: FillType
    timestamp: datetime
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "intent_id": self.intent_id,
            "position_id": self.position_id,
            "fill_price": self.fill_price,
            "fill_size": self.fill_size,
            "fill_type": self.fill_type.value,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


@dataclass
class ExitResult:
    """Result of position exit."""

    success: bool
    position_id: str
    exit_price: float
    realized_pnl: float
    timestamp: datetime
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "position_id": self.position_id,
            "exit_price": self.exit_price,
            "realized_pnl": self.realized_pnl,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error,
        }


# =============================================================================
# PAPER BROKER STUB
# =============================================================================


class PaperBrokerStub:
    """
    Paper broker for testing execution flow.

    S28.C: MOCK_SIGNALS mode — synthetic signals only.

    Execution model (v0):
    - IMMEDIATE fills (no market simulation)
    - Fill price = intent price or current price
    - NO slippage, NO fees

    This is documented as "simplified P&L v0" per GPT_LINT L28-C1.
    """

    def __init__(
        self,
        halt_check_fn: Callable[[], bool],
        current_price_fn: Callable[[str], float] | None = None,
    ):
        """
        Initialize paper broker.

        Args:
            halt_check_fn: Function returning True if system halted
            current_price_fn: Function returning current price for symbol
                              (defaults to using intent price)
        """
        self._halt_check_fn = halt_check_fn
        self._current_price_fn = current_price_fn or (lambda s: None)

        self._registry = PositionRegistry()
        self._order_history: list[OrderResult] = []
        self._exit_history: list[ExitResult] = []

        # Halt state
        self._halted = False
        self._halt_id: str | None = None

    def _check_halt(self) -> None:
        """
        Check halt before any operation.

        INV-GOV-HALT-BEFORE-ACTION enforced.
        """
        if self._halt_check_fn():
            if not self._halted:
                self._halted = True
                self._halt_id = f"HALT-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
            raise BrokerHaltedError(f"Broker halted: {self._halt_id}")

    def submit_order(self, intent: ExecutionIntent) -> OrderResult:
        """
        Submit order from intent.

        S28.C: Immediate fill (no market simulation).

        Args:
            intent: ExecutionIntent for order

        Returns:
            OrderResult with fill details

        Raises:
            BrokerHaltedError: If system halted
        """
        self._check_halt()

        now = datetime.now(UTC)

        # Validate intent type
        if intent.intent_type not in (IntentType.ENTRY,):
            return OrderResult(
                success=False,
                intent_id=intent.intent_id,
                position_id=None,
                fill_price=None,
                fill_size=None,
                fill_type=FillType.IMMEDIATE,
                timestamp=now,
                error=f"Unsupported intent type: {intent.intent_type.value}",
            )

        # Determine fill price
        fill_price = intent.entry_price
        if fill_price is None:
            fill_price = self._current_price_fn(intent.symbol)

        if fill_price is None:
            return OrderResult(
                success=False,
                intent_id=intent.intent_id,
                position_id=None,
                fill_price=None,
                fill_size=None,
                fill_type=FillType.IMMEDIATE,
                timestamp=now,
                error="No fill price available",
            )

        # Create position
        position = self._registry.create_position(
            intent_id=intent.intent_id,
            symbol=intent.symbol,
            direction=intent.direction.value,
            size=intent.size,
        )

        # Immediate fill (v0 — no market simulation)
        position.fill(fill_price, intent.size)

        result = OrderResult(
            success=True,
            intent_id=intent.intent_id,
            position_id=position.position_id,
            fill_price=fill_price,
            fill_size=intent.size,
            fill_type=FillType.IMMEDIATE,
            timestamp=now,
        )

        self._order_history.append(result)
        return result

    def exit_position(
        self, position_id: str, exit_price: float | None = None, reason: str = "exit_signal"
    ) -> ExitResult:
        """
        Exit a position.

        Args:
            position_id: Position to exit
            exit_price: Exit price (or current price if None)
            reason: Exit reason

        Returns:
            ExitResult with P&L

        Raises:
            BrokerHaltedError: If system halted
        """
        self._check_halt()

        now = datetime.now(UTC)
        position = self._registry.get_position(position_id)

        if position is None:
            return ExitResult(
                success=False,
                position_id=position_id,
                exit_price=0.0,
                realized_pnl=0.0,
                timestamp=now,
                error=f"Position not found: {position_id}",
            )

        # Determine exit price
        if exit_price is None:
            exit_price = self._current_price_fn(position.symbol)

        if exit_price is None:
            return ExitResult(
                success=False,
                position_id=position_id,
                exit_price=0.0,
                realized_pnl=0.0,
                timestamp=now,
                error="No exit price available",
            )

        try:
            position.close(exit_price, reason)
            result = ExitResult(
                success=True,
                position_id=position_id,
                exit_price=exit_price,
                realized_pnl=position.realized_pnl,
                timestamp=now,
            )
            self._exit_history.append(result)
            return result
        except Exception as e:
            return ExitResult(
                success=False,
                position_id=position_id,
                exit_price=exit_price,
                realized_pnl=0.0,
                timestamp=now,
                error=str(e),
            )

    def on_halt(self, halt_id: str) -> int:
        """
        Handle system halt.

        Halts all active positions.

        Args:
            halt_id: Halt signal ID

        Returns:
            Count of positions halted
        """
        self._halted = True
        self._halt_id = halt_id
        return self._registry.halt_all(halt_id)

    def clear_halt(self) -> None:
        """Clear halt state (for testing)."""
        self._halted = False
        self._halt_id = None

    def get_position(self, position_id: str) -> Position | None:
        """Get position by ID."""
        return self._registry.get_position(position_id)

    def get_active_positions(self) -> list[Position]:
        """Get all active (non-terminal) positions."""
        return self._registry.get_active_positions()

    def get_total_pnl(self) -> dict[str, float]:
        """
        Get total P&L.

        P&L_v0 (simplified):
        - realized: Sum of closed position P&L
        - unrealized: Sum of open position P&L at current prices

        Returns:
            Dict with 'realized', 'unrealized', 'total'
        """
        return self._registry.get_total_pnl()

    def update_unrealized_pnl(self, prices: dict[str, float]) -> dict[str, float]:
        """
        Update unrealized P&L for all positions.

        Args:
            prices: Dict of symbol → current price

        Returns:
            Updated P&L summary
        """
        for position in self.get_active_positions():
            if position.symbol in prices:
                position.update_unrealized(prices[position.symbol])
        return self.get_total_pnl()

    def get_state_hash(self) -> str:
        """
        Get state hash for determinism verification.

        INV-CONTRACT-1: Same state → same hash.
        """
        components = {
            "positions_hash": self._registry.get_state_hash(),
            "order_count": len(self._order_history),
            "exit_count": len(self._exit_history),
            "halted": self._halted,
        }
        canonical = json.dumps(components, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def get_history(self) -> dict:
        """Get order and exit history."""
        return {
            "orders": [o.to_dict() for o in self._order_history],
            "exits": [e.to_dict() for e in self._exit_history],
        }

    def reset(self) -> None:
        """Reset broker state (for testing)."""
        self._registry = PositionRegistry()
        self._order_history.clear()
        self._exit_history.clear()
        self._halted = False
        self._halt_id = None

    def to_dict(self) -> dict:
        """Serialize broker state."""
        return {
            "positions": self._registry.to_dict(),
            "order_history": [o.to_dict() for o in self._order_history],
            "exit_history": [e.to_dict() for e in self._exit_history],
            "halted": self._halted,
            "halt_id": self._halt_id,
            "state_hash": self.get_state_hash(),
            "pnl": self.get_total_pnl(),
        }


# =============================================================================
# P&L CALCULATOR (v0 SIMPLIFIED)
# =============================================================================


class PnLCalculator:
    """
    P&L calculation utilities.

    P&L_v0 (SIMPLIFIED) — GPT_LINT L28-C1 compliance:
    - P&L = (exit_price - entry_price) * size * direction_mult
    - NO fees
    - NO slippage
    - NO commission

    Documented as simplified v0 for testing.
    """

    @staticmethod
    def calculate_pnl(entry_price: float, exit_price: float, size: float, direction: str) -> float:
        """
        Calculate P&L (simplified v0).

        Args:
            entry_price: Entry price
            exit_price: Exit price
            size: Position size
            direction: "LONG" or "SHORT"

        Returns:
            P&L value (positive = profit)
        """
        direction_mult = 1.0 if direction == "LONG" else -1.0
        return (exit_price - entry_price) * size * direction_mult

    @staticmethod
    def calculate_pnl_percent(entry_price: float, exit_price: float, direction: str) -> float:
        """
        Calculate P&L as percentage.

        Args:
            entry_price: Entry price
            exit_price: Exit price
            direction: "LONG" or "SHORT"

        Returns:
            P&L percentage
        """
        if entry_price == 0:
            return 0.0
        direction_mult = 1.0 if direction == "LONG" else -1.0
        return ((exit_price - entry_price) / entry_price) * 100 * direction_mult
