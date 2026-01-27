"""
IBKR — Interactive Brokers Integration
======================================

S32: EXECUTION_PATH

Provides broker connectivity for order submission, position tracking,
and account queries.

INVARIANTS:
- INV-IBKR-MOCK-1: All tests use mock client (no real API in tests)
- INV-T2-GATE-1: No order submission without valid T2 token

LIBRARY: ib_insync (wrapped behind Phoenix interface)
IMPORTS: Only within this module (zero leakage)
"""

from .account import AccountState
from .connector import IBKRConnector
from .mock_client import ChaosMode, MockIBKRClient
from .orders import Order, OrderResult, OrderStatus, OrderType
from .positions import Position, PositionQuery

__all__ = [
    "IBKRConnector",
    "MockIBKRClient",
    "ChaosMode",
    "Order",
    "OrderResult",
    "OrderStatus",
    "OrderType",
    "Position",
    "PositionQuery",
    "AccountState",
]
