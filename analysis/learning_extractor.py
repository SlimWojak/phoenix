"""
Learning Extractor — Extract Learnings from Trades
==================================================

Extracts learnings from trade outcomes.
Uses LLM when available, falls back to rule-based.

INVARIANT: INV-AUTOPSY-FALLBACK-1
"If LLM unavailable, use rule-based extraction instead of failing"
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class LearningType(str, Enum):
    """Types of learnings."""

    ENTRY_TIMING = "ENTRY_TIMING"
    EXIT_TIMING = "EXIT_TIMING"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"
    SETUP_QUALITY = "SETUP_QUALITY"
    MARKET_CONTEXT = "MARKET_CONTEXT"
    EXECUTION = "EXECUTION"


class ExtractionMethod(str, Enum):
    """How learning was extracted."""

    LLM = "LLM"
    RULE_BASED = "RULE_BASED"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Learning:
    """Individual learning from a trade."""

    learning_type: LearningType
    description: str
    confidence: float
    actionable: bool
    extraction_method: ExtractionMethod
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "learning_type": self.learning_type.value,
            "description": self.description,
            "confidence": self.confidence,
            "actionable": self.actionable,
            "extraction_method": self.extraction_method.value,
            "evidence": self.evidence,
        }


@dataclass
class ExtractionResult:
    """Result from learning extraction."""

    learnings: list[Learning]
    method_used: ExtractionMethod
    llm_available: bool
    processing_time_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "learnings": [learn.to_dict() for learn in self.learnings],
            "method_used": self.method_used.value,
            "llm_available": self.llm_available,
            "processing_time_ms": self.processing_time_ms,
        }


# =============================================================================
# LEARNING EXTRACTOR
# =============================================================================


class LearningExtractor:
    """
    Extracts learnings from trade outcomes.

    INVARIANT: INV-AUTOPSY-FALLBACK-1
    Falls back to rule-based extraction if LLM unavailable.
    """

    def __init__(self, llm_client: Any | None = None) -> None:
        """
        Initialize extractor.

        Args:
            llm_client: LLMClient for AI extraction (optional)
        """
        self._llm_client = llm_client

    def extract(
        self,
        trade_data: dict[str, Any],
        market_context: dict[str, Any] | None = None,
    ) -> ExtractionResult:
        """
        Extract learnings from trade.

        INVARIANT: INV-AUTOPSY-FALLBACK-1
        Uses LLM if available, otherwise rule-based.

        Args:
            trade_data: Trade outcome data
            market_context: Optional market context

        Returns:
            ExtractionResult
        """
        start = datetime.now(UTC)

        # Try LLM extraction first
        llm_available = self._is_llm_available()

        if llm_available:
            try:
                learnings = self._llm_extract(trade_data, market_context)
                if learnings:
                    elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
                    return ExtractionResult(
                        learnings=learnings,
                        method_used=ExtractionMethod.LLM,
                        llm_available=True,
                        processing_time_ms=elapsed,
                    )
            except Exception:  # noqa: S110
                pass  # Fall through to rule-based

        # Fallback: Rule-based extraction (INV-AUTOPSY-FALLBACK-1)
        learnings = self._rule_based_extract(trade_data, market_context)

        elapsed = (datetime.now(UTC) - start).total_seconds() * 1000
        return ExtractionResult(
            learnings=learnings,
            method_used=ExtractionMethod.RULE_BASED,
            llm_available=llm_available,
            processing_time_ms=elapsed,
        )

    def _is_llm_available(self) -> bool:
        """Check if LLM client is available."""
        if self._llm_client is None:
            return False

        try:
            return self._llm_client.is_available()
        except Exception:
            return False

    def _llm_extract(
        self,
        trade_data: dict[str, Any],
        market_context: dict[str, Any] | None,
    ) -> list[Learning]:
        """Extract learnings using LLM."""
        if self._llm_client is None:
            return []

        prompt = self._build_extraction_prompt(trade_data, market_context)
        system = self._build_system_prompt()

        schema = {
            "type": "object",
            "properties": {
                "learnings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string"},
                            "description": {"type": "string"},
                            "confidence": {"type": "number"},
                            "actionable": {"type": "boolean"},
                            "evidence": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["type", "description"],
                    },
                }
            },
            "required": ["learnings"],
        }

        response = self._llm_client.complete_json(prompt, schema=schema, system=system)

        if not response.parsed:
            return []

        learnings: list[Learning] = []
        for item in response.parsed.get("learnings", []):
            try:
                learning_type = LearningType(item.get("type", "ENTRY_TIMING"))
            except ValueError:
                learning_type = LearningType.ENTRY_TIMING

            learnings.append(
                Learning(
                    learning_type=learning_type,
                    description=item.get("description", ""),
                    confidence=item.get("confidence", 0.5),
                    actionable=item.get("actionable", False),
                    extraction_method=ExtractionMethod.LLM,
                    evidence=item.get("evidence", []),
                )
            )

        return learnings

    def _rule_based_extract(
        self,
        trade_data: dict[str, Any],
        market_context: dict[str, Any] | None,
    ) -> list[Learning]:
        """
        Extract learnings using rule-based logic.

        This is the fallback when LLM is unavailable.
        """
        learnings: list[Learning] = []

        outcome = trade_data.get("outcome", {})
        entry_thesis = trade_data.get("entry_thesis", {})
        result = outcome.get("result", "UNKNOWN")
        pnl = outcome.get("pnl_percent", 0)

        # Rule 1: Entry timing based on result
        if result == "WIN":
            if pnl > 2.0:  # Big win
                learnings.append(
                    Learning(
                        learning_type=LearningType.ENTRY_TIMING,
                        description="Entry timing was good - captured significant move",
                        confidence=0.7,
                        actionable=True,
                        extraction_method=ExtractionMethod.RULE_BASED,
                        evidence=[f"P&L: {pnl:.2f}%"],
                    )
                )
            else:
                learnings.append(
                    Learning(
                        learning_type=LearningType.ENTRY_TIMING,
                        description="Entry was acceptable but move was limited",
                        confidence=0.6,
                        actionable=False,
                        extraction_method=ExtractionMethod.RULE_BASED,
                        evidence=[f"P&L: {pnl:.2f}%"],
                    )
                )
        elif result == "LOSS":
            learnings.append(
                Learning(
                    learning_type=LearningType.ENTRY_TIMING,
                    description="Entry timing may need review - position went against",
                    confidence=0.6,
                    actionable=True,
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence=[f"P&L: {pnl:.2f}%"],
                )
            )

        # Rule 2: Risk management
        max_adverse = trade_data.get("max_adverse_excursion", 0)
        if max_adverse and abs(max_adverse) > 50:  # pips
            learnings.append(
                Learning(
                    learning_type=LearningType.RISK_MANAGEMENT,
                    description="Position experienced significant adverse excursion",
                    confidence=0.8,
                    actionable=True,
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence=[f"Max adverse: {max_adverse} pips"],
                )
            )

        # Rule 3: Setup quality
        thesis_confidence = entry_thesis.get("confidence", 0.5)
        if result == "WIN" and thesis_confidence < 0.6:
            learnings.append(
                Learning(
                    learning_type=LearningType.SETUP_QUALITY,
                    description="Won despite low confidence - review setup quality",
                    confidence=0.5,
                    actionable=True,
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence=[f"Entry confidence: {thesis_confidence:.2f}"],
                )
            )
        elif result == "LOSS" and thesis_confidence > 0.8:
            learnings.append(
                Learning(
                    learning_type=LearningType.SETUP_QUALITY,
                    description="Lost despite high confidence - review what was missed",
                    confidence=0.7,
                    actionable=True,
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence=[f"Entry confidence: {thesis_confidence:.2f}"],
                )
            )

        # Rule 4: Market context
        if market_context:
            volatility = market_context.get("volatility", "normal")
            if volatility == "high" and result == "LOSS":
                learnings.append(
                    Learning(
                        learning_type=LearningType.MARKET_CONTEXT,
                        description="Loss in high volatility - consider tighter stops",
                        confidence=0.6,
                        actionable=True,
                        extraction_method=ExtractionMethod.RULE_BASED,
                        evidence=["High volatility market"],
                    )
                )

        # Rule 5: Duration-based learning
        duration_hours = trade_data.get("duration_hours", 0)
        if duration_hours > 48:  # Long trade
            learnings.append(
                Learning(
                    learning_type=LearningType.EXECUTION,
                    description="Extended hold - review if earlier exit was available",
                    confidence=0.5,
                    actionable=False,
                    extraction_method=ExtractionMethod.RULE_BASED,
                    evidence=[f"Duration: {duration_hours:.0f} hours"],
                )
            )

        return learnings

    def _build_extraction_prompt(
        self,
        trade_data: dict[str, Any],
        market_context: dict[str, Any] | None,
    ) -> str:
        """Build extraction prompt for LLM."""
        context_str = json.dumps(market_context or {}, indent=2)
        trade_str = json.dumps(trade_data, indent=2)

        return f"""Analyze this trade and extract actionable learnings.

TRADE DATA:
{trade_str}

MARKET CONTEXT:
{context_str}

Extract learnings about:
- Entry timing (was the entry good?)
- Exit timing (was exit optimal?)
- Risk management (was risk appropriate?)
- Setup quality (was the setup valid?)
- Market context (did conditions affect outcome?)

Return structured learnings with confidence scores.
"""

    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM."""
        return """You are a trading analysis assistant.
Extract learnings from trade outcomes.
Focus on actionable insights.
Be concise and specific.
Rate confidence 0.0-1.0 based on evidence strength.
"""
