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
    NarratorHeresyError,
    narrator_emit,
    canonicalize_content,
)
from .templates import MANDATORY_FACTS_BANNER
from .surface import (
    GATE_PHRASES,
    gates_to_phrases,
    format_gate_facts,
    DegradedState,
    DEGRADED_MESSAGES,
    get_degraded_message,
    format_alert_oneliner,
    format_health_status,
    format_staleness,
    format_receipts,
    format_circuit_status,
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
    "MANDATORY_FACTS_BANNER",
    "validate_template_content",
    "NarratorRenderer",
    "TemplateRenderError",
    "UndefinedVariableError",
    "NarratorHeresyError",
    "narrator_emit",
    "canonicalize_content",
    # S41 Phase 2E Surface
    "GATE_PHRASES",
    "gates_to_phrases",
    "format_gate_facts",
    "DegradedState",
    "DEGRADED_MESSAGES",
    "get_degraded_message",
    "format_alert_oneliner",
    "format_health_status",
    "format_staleness",
    "format_receipts",
    "format_circuit_status",
]
