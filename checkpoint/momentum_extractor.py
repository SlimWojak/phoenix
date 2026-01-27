"""
Momentum Extractor — Extract Learnings from Session
====================================================

Analyzes session history to extract momentum (learnings).

DESIGN:
- Input: Session checkpoints, hunt results
- Output: Structured momentum for next session
- Uses: Athena queries + local analysis

Momentum persists across sessions, building cumulative knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Learning:
    """Single learning from session."""

    category: str  # e.g., "signal_timing", "pair_behavior", "regime"
    insight: str
    confidence: float  # 0.0 to 1.0
    evidence_refs: list[str] = field(default_factory=list)  # Bead IDs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category,
            "insight": self.insight,
            "confidence": self.confidence,
            "evidence_refs": self.evidence_refs,
        }


@dataclass
class Momentum:
    """Accumulated momentum from session(s)."""

    session_ids: list[str]
    extracted_at: datetime
    learnings: list[Learning]

    # Summary stats
    total_hunts: int
    successful_hunts: int  # With survivors
    hypothesis_refinements: int

    # Next session guidance
    suggested_focus: str
    avoid_patterns: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "session_ids": self.session_ids,
            "extracted_at": self.extracted_at.isoformat(),
            "learnings": [learn.to_dict() for learn in self.learnings],
            "total_hunts": self.total_hunts,
            "successful_hunts": self.successful_hunts,
            "hypothesis_refinements": self.hypothesis_refinements,
            "suggested_focus": self.suggested_focus,
            "avoid_patterns": self.avoid_patterns,
        }

    def to_summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Momentum from {len(self.session_ids)} session(s)",
            f"Extracted: {self.extracted_at.isoformat()}",
            "",
            f"Hunts: {self.total_hunts} total, {self.successful_hunts} successful",
            f"Refinements: {self.hypothesis_refinements}",
            "",
            "Key Learnings:",
        ]

        for learning in self.learnings[:5]:  # Top 5
            lines.append(f"  [{learning.category}] {learning.insight}")
            lines.append(f"    Confidence: {learning.confidence:.1%}")

        lines.extend([
            "",
            f"Suggested focus: {self.suggested_focus}",
            "",
            "Patterns to avoid:",
        ])

        for pattern in self.avoid_patterns[:3]:
            lines.append(f"  - {pattern}")

        return "\n".join(lines)


# =============================================================================
# MOMENTUM EXTRACTOR
# =============================================================================


class MomentumExtractor:
    """
    Extracts momentum (learnings) from session history.

    Uses:
    - Session checkpoints
    - Hunt bead content
    - Athena queries (optional)
    """

    def __init__(self, athena: Any | None = None) -> None:
        """
        Initialize extractor.

        Args:
            athena: Athena instance for querying history
        """
        self._athena = athena

    def extract_from_session(
        self,
        session_id: str,
        checkpoints: list[dict[str, Any]],
        hunt_results: list[dict[str, Any]],
    ) -> Momentum:
        """
        Extract momentum from single session.

        Args:
            session_id: Session identifier
            checkpoints: List of checkpoint data
            hunt_results: List of hunt result data

        Returns:
            Momentum object
        """
        learnings: list[Learning] = []

        # Analyze hunt results
        successful_hunts = 0
        for hunt in hunt_results:
            survivors = hunt.get("survivors", [])
            if survivors:
                successful_hunts += 1

                # Extract learning from successful hunt
                learning = self._analyze_successful_hunt(hunt)
                if learning:
                    learnings.append(learning)

        # Analyze failed hunts for patterns to avoid
        avoid_patterns = self._extract_avoid_patterns(hunt_results)

        # Count hypothesis refinements
        refinements = sum(
            1 for c in checkpoints
            if c.get("transition_type") == "HYPOTHESIS_UPDATE"
        )

        # Generate suggested focus
        suggested_focus = self._suggest_focus(learnings, hunt_results)

        return Momentum(
            session_ids=[session_id],
            extracted_at=datetime.now(UTC),
            learnings=learnings,
            total_hunts=len(hunt_results),
            successful_hunts=successful_hunts,
            hypothesis_refinements=refinements,
            suggested_focus=suggested_focus,
            avoid_patterns=avoid_patterns,
        )

    def extract_cumulative(
        self,
        session_ids: list[str],
    ) -> Momentum:
        """
        Extract cumulative momentum across multiple sessions.

        Uses Athena to query historical data.

        Args:
            session_ids: List of session IDs to analyze

        Returns:
            Cumulative Momentum object
        """
        # If no Athena, return empty momentum
        if self._athena is None:
            return Momentum(
                session_ids=session_ids,
                extracted_at=datetime.now(UTC),
                learnings=[],
                total_hunts=0,
                successful_hunts=0,
                hypothesis_refinements=0,
                suggested_focus="Connect Athena for cumulative analysis",
                avoid_patterns=[],
            )

        # Query Athena for session data
        # TODO: Implement Athena query integration
        learnings: list[Learning] = []

        return Momentum(
            session_ids=session_ids,
            extracted_at=datetime.now(UTC),
            learnings=learnings,
            total_hunts=0,
            successful_hunts=0,
            hypothesis_refinements=0,
            suggested_focus="Cumulative analysis pending",
            avoid_patterns=[],
        )

    def _analyze_successful_hunt(
        self,
        hunt: dict[str, Any],
    ) -> Learning | None:
        """Analyze successful hunt for learning."""
        survivors = hunt.get("survivors", [])
        if not survivors:
            return None

        # Extract common parameters from survivors
        hpg = hunt.get("hpg_json", {})
        signal_type = hpg.get("signal_type", "unknown")
        session = hpg.get("session", "unknown")
        pair = hpg.get("pair", "unknown")

        # Best survivor metrics
        best = max(survivors, key=lambda s: s.get("sharpe", 0))
        sharpe = best.get("sharpe", 0)

        insight = (
            f"{signal_type} on {pair} during {session} shows promise "
            f"(Sharpe {sharpe:.2f}, {len(survivors)} survivors)"
        )

        return Learning(
            category="signal_timing",
            insight=insight,
            confidence=min(0.9, 0.5 + len(survivors) * 0.1),
            evidence_refs=[hunt.get("bead_id", "unknown")],
        )

    def _extract_avoid_patterns(
        self,
        hunt_results: list[dict[str, Any]],
    ) -> list[str]:
        """Extract patterns to avoid from failed hunts."""
        patterns: list[str] = []

        for hunt in hunt_results:
            survivors = hunt.get("survivors", [])
            if not survivors:
                hpg = hunt.get("hpg_json", {})
                signal_type = hpg.get("signal_type", "unknown")
                session = hpg.get("session", "unknown")
                pair = hpg.get("pair", "unknown")

                patterns.append(f"{signal_type} on {pair} during {session}")

        # Return unique patterns (max 5)
        return list(set(patterns))[:5]

    def _suggest_focus(
        self,
        learnings: list[Learning],
        hunt_results: list[dict[str, Any]],
    ) -> str:
        """Generate suggested focus for next session."""
        if not learnings:
            return "Explore new signal types and timing combinations"

        # Find highest confidence learning
        best = max(learnings, key=lambda x: x.confidence)
        return f"Continue exploring: {best.insight[:80]}..."
