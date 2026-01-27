"""
Governance — Human sovereignty enforcement
==========================================

S32: EXECUTION_PATH

Contains T2 approval workflow and stale gate protection.
This is where human authority over capital is enforced.

CONSTITUTIONAL:
- Human sovereignty over capital is absolute
- Tier 2 (capital-adjacent) always requires human gate
- Forge amplifies judgment, never replaces it
"""

from .stale_gate import StaleCheckResult, StaleGate
from .t2 import EvidenceBundle, T2Workflow, Token, TokenStatus

__all__ = [
    "T2Workflow",
    "Token",
    "TokenStatus",
    "EvidenceBundle",
    "StaleGate",
    "StaleCheckResult",
]
