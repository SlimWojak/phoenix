"""
Phoenix Data Module
===================

Read-only data access layer.

INVARIANT: INV-RIVER-RO-1 "River reader cannot modify data"
"""

from .river_reader import (
    ALLOWED_CALLERS,
    DENIED_CALLERS,
    RiverAccessDeniedError,
    RiverReader,
    RiverReadError,
)

__all__ = [
    "RiverReader",
    "RiverReadError",
    "RiverAccessDeniedError",
    "ALLOWED_CALLERS",
    "DENIED_CALLERS",
]
