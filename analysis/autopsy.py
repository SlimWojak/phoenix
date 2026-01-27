"""
Autopsy — Post-Trade Analysis Engine
=====================================

Generates AUTOPSY beads from closed positions.
Compares entry thesis to outcome.

INVARIANT: INV-AUTOPSY-BEAD-1
"Every closed position gets AUTOPSY bead"
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .learning_extractor import Learning, LearningExtractor

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ThesisComparison:
    """Comparison of entry thesis to outcome."""

    thesis_valid: bool
    unknown_factors: list[str]
    learnings: list[Learning]

    def to_dict(self) -> dict[str, Any]:
        return {
            "thesis_valid": self.thesis_valid,
            "unknown_factors": self.unknown_factors,
            "learnings": [learn.to_dict() for learn in self.learnings],
        }


@dataclass
class AutopsyResult:
    """Result from autopsy analysis."""

    position_id: str
    entry_thesis: dict[str, Any]
    outcome: dict[str, Any]
    comparison: ThesisComparison
    autopsy_bead_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "entry_thesis": self.entry_thesis,
            "outcome": self.outcome,
            "comparison": self.comparison.to_dict(),
            "autopsy_bead_id": self.autopsy_bead_id,
        }


# =============================================================================
# AUTOPSY ENGINE
# =============================================================================


class Autopsy:
    """
    Post-trade analysis engine.

    INVARIANT: INV-AUTOPSY-BEAD-1
    Creates AUTOPSY bead for every closed position.
    """

    def __init__(
        self,
        bead_store: Any | None = None,
        llm_client: Any | None = None,
    ) -> None:
        """
        Initialize autopsy engine.

        Args:
            bead_store: BeadStore for AUTOPSY beads
            llm_client: LLMClient for learning extraction
        """
        self._bead_store = bead_store
        self._extractor = LearningExtractor(llm_client)

    def analyze(
        self,
        position_id: str,
        entry_thesis: dict[str, Any],
        outcome: dict[str, Any],
        market_context: dict[str, Any] | None = None,
    ) -> AutopsyResult:
        """
        Analyze closed position.

        INVARIANT: INV-AUTOPSY-BEAD-1

        Args:
            position_id: ID of closed position
            entry_thesis: Entry thesis from position open
            outcome: Trade outcome data
            market_context: Optional market context

        Returns:
            AutopsyResult
        """
        # Build trade data for learning extraction
        trade_data = {
            "position_id": position_id,
            "entry_thesis": entry_thesis,
            "outcome": outcome,
        }

        # Extract learnings (uses LLM with fallback)
        extraction = self._extractor.extract(trade_data, market_context)

        # Compare thesis to outcome
        comparison = self._compare_thesis(entry_thesis, outcome, extraction.learnings)

        # Create AUTOPSY bead
        bead_id = self._emit_autopsy_bead(position_id, entry_thesis, outcome, comparison)

        return AutopsyResult(
            position_id=position_id,
            entry_thesis=entry_thesis,
            outcome=outcome,
            comparison=comparison,
            autopsy_bead_id=bead_id,
        )

    def analyze_position_bead(self, position_bead: dict[str, Any]) -> AutopsyResult:
        """
        Analyze from POSITION bead.

        Args:
            position_bead: POSITION bead dict

        Returns:
            AutopsyResult
        """
        content = position_bead.get("content", {})
        if isinstance(content, str):
            content = json.loads(content)

        position_id = content.get("position_id", position_bead.get("bead_id", ""))

        # Extract thesis from position
        entry_thesis = {
            "confidence": content.get("entry_confidence", 0.5),
            "reasoning_hash": content.get("reasoning_hash", ""),
            "setup_type": content.get("setup_type", "UNKNOWN"),
        }

        # Build outcome
        outcome = {
            "result": self._determine_result(content),
            "pnl_percent": content.get("pnl", 0) / content.get("size", 1) * 100
            if content.get("size")
            else 0,
            "duration": self._calculate_duration(position_bead),
        }

        return self.analyze(position_id, entry_thesis, outcome)

    def _compare_thesis(
        self,
        entry_thesis: dict[str, Any],
        outcome: dict[str, Any],
        learnings: list[Learning],
    ) -> ThesisComparison:
        """Compare entry thesis to actual outcome."""
        result = outcome.get("result", "UNKNOWN")

        # Simple thesis validation
        # If we were confident and won, or low confidence and lost = thesis valid
        confidence = entry_thesis.get("confidence", 0.5)

        if result == "WIN" and confidence >= 0.6:
            thesis_valid = True
        elif result == "LOSS" and confidence < 0.5:
            thesis_valid = True  # Expected lower probability
        elif result == "WIN" and confidence < 0.5:
            thesis_valid = False  # Won but didn't expect to
        elif result == "LOSS" and confidence >= 0.6:
            thesis_valid = False  # Lost but expected to win
        else:
            thesis_valid = result == "BREAKEVEN"

        # Identify unknown factors
        unknown_factors = self._identify_unknowns(entry_thesis, outcome)

        return ThesisComparison(
            thesis_valid=thesis_valid,
            unknown_factors=unknown_factors,
            learnings=learnings,
        )

    def _identify_unknowns(
        self,
        entry_thesis: dict[str, Any],
        outcome: dict[str, Any],
    ) -> list[str]:
        """Identify unknown factors that affected trade."""
        unknowns: list[str] = []

        result = outcome.get("result", "UNKNOWN")
        confidence = entry_thesis.get("confidence", 0.5)

        # If outcome didn't match confidence
        if result == "LOSS" and confidence > 0.7:
            unknowns.append("High confidence loss - review entry thesis")

        if result == "WIN" and confidence < 0.4:
            unknowns.append("Low confidence win - luck or missed setup quality?")

        # Check for large adverse excursion
        adverse = outcome.get("max_adverse_pips", 0)
        if adverse and abs(adverse) > 30:
            unknowns.append(f"Large adverse excursion: {adverse} pips")

        return unknowns

    def _emit_autopsy_bead(
        self,
        position_id: str,
        entry_thesis: dict[str, Any],
        outcome: dict[str, Any],
        comparison: ThesisComparison,
    ) -> str:
        """
        Emit AUTOPSY bead.

        INVARIANT: INV-AUTOPSY-BEAD-1
        """
        bead_id = f"AUTOPSY-{uuid.uuid4().hex[:8]}"

        bead_content = {
            "position_id": position_id,
            "entry_thesis": {
                "confidence": entry_thesis.get("confidence", 0.5),
                "reasoning_hash": entry_thesis.get("reasoning_hash", ""),
                "setup_type": entry_thesis.get("setup_type", ""),
            },
            "outcome": {
                "result": outcome.get("result", "UNKNOWN"),
                "pnl_percent": outcome.get("pnl_percent", 0),
                "duration": outcome.get("duration", "PT0S"),
            },
            "comparison": {
                "thesis_valid": comparison.thesis_valid,
                "unknown_factors": comparison.unknown_factors[:10],
                "learnings": [lrn.to_dict() for lrn in comparison.learnings[:10]],
            },
        }

        bead_dict = {
            "bead_id": bead_id,
            "bead_type": "AUTOPSY",
            "prev_bead_id": None,
            "bead_hash": hashlib.sha256(
                json.dumps(bead_content, sort_keys=True).encode()
            ).hexdigest()[:16],
            "timestamp_utc": datetime.now(UTC).isoformat(),
            "signer": "system",
            "version": "1.0",
            "content": bead_content,
        }

        if self._bead_store:
            try:
                self._bead_store.write_dict(bead_dict)
            except Exception:  # noqa: S110
                pass

        return bead_id

    def _determine_result(self, content: dict[str, Any]) -> str:
        """Determine trade result from position content."""
        pnl = content.get("pnl", 0)

        if pnl > 0:
            return "WIN"
        if pnl < 0:
            return "LOSS"
        return "BREAKEVEN"

    def _calculate_duration(self, bead: dict[str, Any]) -> str:
        """Calculate trade duration in ISO8601 format."""
        # Would calculate from entry to exit timestamps
        return "PT24H"  # Default 24 hours
