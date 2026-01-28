"""
Phoenix Approval Module — T2 Evidence Display
==============================================

S34: D2 MOCK_ORACLE_PIPELINE_VALIDATION

Displays evidence bundles for human T2 approval,
including 5-drawer gate references for traceability.
"""

from .evidence import CSEEvidenceBuilder, EvidenceDisplay

__all__ = [
    "CSEEvidenceBuilder",
    "EvidenceDisplay",
]
