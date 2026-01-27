"""
Phoenix Mocks — Testing utilities
=================================

S33: FIRST_BLOOD

Mock utilities for UX testing without real CSO signals.
"""

from .mock_cse_generator import MockCSEGenerator, CSESignal

__all__ = [
    "MockCSEGenerator",
    "CSESignal",
]
