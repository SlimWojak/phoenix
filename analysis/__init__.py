"""
Phoenix Analysis Module — Post-Trade Autopsy
=============================================

Post-trade analysis with learning extraction.

Components:
- Autopsy: Post-trade analysis engine
- LearningExtractor: Extract learnings with LLM fallback

INVARIANTS:
- INV-AUTOPSY-BEAD-1: Every closed position gets AUTOPSY bead
- INV-AUTOPSY-FALLBACK-1: If LLM unavailable, use rule-based extraction
"""

from .autopsy import Autopsy, AutopsyResult
from .learning_extractor import Learning, LearningExtractor

__all__ = [
    "Autopsy",
    "AutopsyResult",
    "LearningExtractor",
    "Learning",
]
