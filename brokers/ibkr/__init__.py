"""
IBKR — Interactive Brokers Integration
======================================

S33: FIRST_BLOOD

Provides broker connectivity for order submission, position tracking,
and account queries with paper-first guards.

INVARIANTS:
- INV-IBKR-MOCK-1: All tests use mock client (no real API in tests)
- INV-T2-GATE-1: No order submission without valid T2 token
- INV-IBKR-PAPER-GUARD-1: Live mode requires IBKR_ALLOW_LIVE=true + restart
- INV-IBKR-ACCOUNT-CHECK-1: Every order submit validates account matches mode
- INV-IBKR-RECONNECT-1: Max 3 reconnect attempts, then human escalation

LIBRARY: ib_insync (wrapped behind Phoenix interface)
IMPORTS: Only within this module (zero leakage)
"""

from .account import AccountState
from .config import IBKRConfig, IBKRMode, ReconnectConfig, ReconnectState, ReconnectTracker
from .connector import ConnectionConfig, IBKRConnector
from .mock_client import ChaosMode, MockIBKRClient
from .orders import Order, OrderResult, OrderStatus, OrderType
from .positions import Position, PositionQuery
from .session_bead import SessionBeadData, SessionBeadEmitter, SessionEvent

__all__ = [
    # Connector
    "IBKRConnector",
    "ConnectionConfig",  # Legacy compatibility
    # Config (S33)
    "IBKRConfig",
    "IBKRMode",
    "ReconnectConfig",
    "ReconnectState",
    "ReconnectTracker",
    # Mock client
    "MockIBKRClient",
    "ChaosMode",
    # Orders
    "Order",
    "OrderResult",
    "OrderStatus",
    "OrderType",
    # Positions
    "Position",
    "PositionQuery",
    # Account
    "AccountState",
    # Session beads (S33)
    "SessionBeadData",
    "SessionBeadEmitter",
    "SessionEvent",
]
