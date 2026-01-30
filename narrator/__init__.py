"""
WarBoar Narrator — S40 Track D
==============================

Template-based state projection in boar dialect.
Facts only, no synthesis, no hallucination.

Pre-distillation foundation for S41 WarBoar LLM.

INVARIANTS:
  - INV-NARRATOR-1: Facts only, no synthesis
  - INV-NARRATOR-2: All fields trace to sources
  - INV-NARRATOR-3: Undefined → error, not empty

OINK OINK MOTHERFUCKER! 🐗🔥
"""

from .data_sources import (
    DataSources,
    OrientationData,
    AthenaData,
    RiverData,
    TestData,
    TradeData,
    CSOData,
    HuntData,
)
from .templates import (
    TemplateRegistry,
    FORBIDDEN_WORDS,
    validate_template_content,
)
from .renderer import (
    NarratorRenderer,
    TemplateRenderError,
    UndefinedVariableError,
)

__all__ = [
    "DataSources",
    "OrientationData",
    "AthenaData",
    "RiverData",
    "TestData",
    "TradeData",
    "CSOData",
    "HuntData",
    "TemplateRegistry",
    "FORBIDDEN_WORDS",
    "validate_template_content",
    "NarratorRenderer",
    "TemplateRenderError",
    "UndefinedVariableError",
]
