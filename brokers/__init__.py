"""
Brokers — External broker integrations
======================================

Contains broker-specific adapters. Currently:
- IBKR (Interactive Brokers)
"""

from .ibkr import IBKRConnector, MockIBKRClient

__all__ = ["IBKRConnector", "MockIBKRClient"]
