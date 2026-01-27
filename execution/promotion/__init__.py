"""
Promotion — Shadow to Live Ceremony
====================================

S32: EXECUTION_PATH

Promotion workflow with safety checks and evidence bundle.

INVARIANTS:
- INV-PROMOTION-EVIDENCE-1: Every promotion needs evidence bundle
- INV-PROMOTION-T2-1: Promotion requires T2 approval
- INV-PROMOTION-SAFE-1: Block if kill flags active
- INV-PROMOTION-SAFE-2: Block if unresolved drift

WATCHPOINTS:
- WP_D1: Promotion hard blocks (kill flags, STALLED, drift)
- WP_D2: Promotion is one-way (no automatic demotion)
"""

from .ceremony import PromotionCeremony, PromotionRequest, PromotionResponse
from .checklist import CheckResult, PromotionChecklist

__all__ = [
    "PromotionChecklist",
    "CheckResult",
    "PromotionCeremony",
    "PromotionRequest",
    "PromotionResponse",
]
