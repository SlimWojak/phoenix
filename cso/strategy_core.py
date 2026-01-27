"""
Strategy Core — Immutable Setup Detection Logic
================================================

CSO's immutable core logic. Detects setups from market structure.

INVARIANT: INV-CSO-CORE-1
"Strategy logic is immutable; only parameters are calibratable"

This file contains NO dynamic code execution.
Parameters affect thresholds only, not logic.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .structure_detector import (
    BOS,
    FVG,
    OTE,
    Direction,
    LiquiditySweep,
    StructureOutput,
)

# =============================================================================
# ENUMS
# =============================================================================


class SetupStatus(str, Enum):
    """Setup detection status."""

    READY = "READY"
    FORMING = "FORMING"
    NONE = "NONE"


class SetupType(str, Enum):
    """ICT setup types."""

    FVG_ENTRY = "FVG_ENTRY"
    OTE_ENTRY = "OTE_ENTRY"
    SWEEP_ENTRY = "SWEEP_ENTRY"
    BOS_CONTINUATION = "BOS_CONTINUATION"


class RedFlagType(str, Enum):
    """Red flag types that reduce confidence."""

    COUNTER_TREND = "COUNTER_TREND"
    OVEREXTENDED = "OVEREXTENDED"
    NEWS_PROXIMITY = "NEWS_PROXIMITY"
    LOW_VOLUME = "LOW_VOLUME"
    STRUCTURE_CONFLICT = "STRUCTURE_CONFLICT"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class RedFlag:
    """Red flag that reduces confidence."""

    flag_type: RedFlagType
    description: str
    confidence_penalty: float  # 0.0-0.5


@dataclass
class EvidenceBundle:
    """Evidence supporting a setup."""

    htf_structures: list[dict]
    ltf_structures: list[dict]
    alignment_score: float
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "htf_structures": self.htf_structures,
            "ltf_structures": self.ltf_structures,
            "alignment_score": self.alignment_score,
            "evidence_hash": self.evidence_hash,
        }


@dataclass
class Setup:
    """Detected trading setup."""

    setup_id: str
    pair: str
    setup_type: SetupType
    direction: Direction
    confidence: float
    entry_price: float
    stop_price: float
    target_price: float
    risk_percent: float
    evidence: EvidenceBundle
    red_flags: list[RedFlag] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "setup_id": self.setup_id,
            "pair": self.pair,
            "setup_type": self.setup_type.value,
            "direction": self.direction.value,
            "confidence": self.confidence,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "target_price": self.target_price,
            "risk_percent": self.risk_percent,
            "evidence": self.evidence.to_dict(),
            "red_flags": [
                {"type": rf.flag_type.value, "description": rf.description} for rf in self.red_flags
            ],
        }


@dataclass
class SetupResult:
    """Result from setup detection."""

    pair: str
    status: SetupStatus
    quality_score: float
    setup: Setup | None = None
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "pair": self.pair,
            "status": self.status.value,
            "quality_score": self.quality_score,
            "setup": self.setup.to_dict() if self.setup else None,
            "reason": self.reason,
        }


# =============================================================================
# STRATEGY CORE (IMMUTABLE)
# =============================================================================


class StrategyCore:
    """
    Immutable strategy core.

    INVARIANT: INV-CSO-CORE-1
    This class has NO dynamic code execution.
    Parameters are passed in, not imported.
    Logic is frozen at deployment.
    """

    def __init__(
        self,
        ready_threshold: float = 0.8,
        forming_threshold: float = 0.5,
        pip_value: float = 0.0001,
    ) -> None:
        """
        Initialize strategy core.

        Args:
            ready_threshold: Minimum score for READY status
            forming_threshold: Minimum score for FORMING status
            pip_value: Pip value for the pair
        """
        self._ready_threshold = ready_threshold
        self._forming_threshold = forming_threshold
        self._pip_value = pip_value

    def detect_setup(
        self,
        pair: str,
        htf_structure: StructureOutput,
        ltf_structure: StructureOutput,
        current_price: float,
    ) -> SetupResult:
        """
        Detect setup from HTF and LTF structure.

        Args:
            pair: Currency pair
            htf_structure: Higher timeframe structure
            ltf_structure: Lower timeframe structure
            current_price: Current price

        Returns:
            SetupResult with status and optional Setup
        """
        # Score the setup quality
        quality_score = self.score_quality(htf_structure, ltf_structure)

        # Determine status
        if quality_score >= self._ready_threshold:
            status = SetupStatus.READY
        elif quality_score >= self._forming_threshold:
            status = SetupStatus.FORMING
        else:
            return SetupResult(
                pair=pair,
                status=SetupStatus.NONE,
                quality_score=quality_score,
                reason="Insufficient structure alignment",
            )

        # Build setup details for READY/FORMING
        setup = self._build_setup(pair, htf_structure, ltf_structure, current_price, quality_score)

        # Check red flags
        red_flags = self.check_red_flags(htf_structure, ltf_structure)
        if setup:
            setup.red_flags = red_flags

            # Apply red flag penalties
            for rf in red_flags:
                setup.confidence -= rf.confidence_penalty
            setup.confidence = max(0.0, setup.confidence)

        return SetupResult(
            pair=pair,
            status=status,
            quality_score=quality_score,
            setup=setup,
            reason=f"Setup detected: {setup.setup_type.value}" if setup else "",
        )

    def score_quality(
        self,
        htf_structure: StructureOutput,
        ltf_structure: StructureOutput,
    ) -> float:
        """
        Score setup quality.

        Components:
        - Structure alignment (30%)
        - FVG quality (20%)
        - Liquidity context (20%)
        - Session timing (15%)
        - Recent BOS (15%)
        """
        score = 0.0

        # 1. Structure alignment (30%)
        alignment = self._score_alignment(htf_structure, ltf_structure)
        score += alignment * 0.30

        # 2. FVG quality (20%)
        fvg_score = self._score_fvg(ltf_structure)
        score += fvg_score * 0.20

        # 3. Liquidity context (20%)
        liquidity_score = self._score_liquidity(ltf_structure)
        score += liquidity_score * 0.20

        # 4. Session timing (15%) - simplified, would need time context
        session_score = 0.7  # Default moderate score
        score += session_score * 0.15

        # 5. Recent BOS (15%)
        bos_score = self._score_bos(ltf_structure)
        score += bos_score * 0.15

        return min(1.0, score)

    def build_evidence(
        self,
        htf_structure: StructureOutput,
        ltf_structure: StructureOutput,
    ) -> EvidenceBundle:
        """Build evidence bundle for setup."""
        htf_dict = [s.to_dict() for s in htf_structure.structures[-5:]]
        ltf_dict = [s.to_dict() for s in ltf_structure.structures[-10:]]

        alignment = self._score_alignment(htf_structure, ltf_structure)

        # Compute evidence hash
        evidence_data = json.dumps(
            {"htf": htf_dict, "ltf": ltf_dict, "alignment": alignment},
            sort_keys=True,
        )
        evidence_hash = hashlib.sha256(evidence_data.encode()).hexdigest()[:16]

        return EvidenceBundle(
            htf_structures=htf_dict,
            ltf_structures=ltf_dict,
            alignment_score=alignment,
            evidence_hash=evidence_hash,
        )

    def check_red_flags(
        self,
        htf_structure: StructureOutput,
        ltf_structure: StructureOutput,
    ) -> list[RedFlag]:
        """Check for red flags that reduce confidence."""
        red_flags: list[RedFlag] = []

        # Counter-trend flag
        if htf_structure.htf_bias != ltf_structure.htf_bias:
            if ltf_structure.htf_bias != Direction.NEUTRAL:
                red_flags.append(
                    RedFlag(
                        flag_type=RedFlagType.COUNTER_TREND,
                        description="LTF bias differs from HTF",
                        confidence_penalty=0.15,
                    )
                )

        # Structure conflict
        htf_bos = [s for s in htf_structure.structures if isinstance(s, BOS)]
        ltf_bos = [s for s in ltf_structure.structures if isinstance(s, BOS)]

        if htf_bos and ltf_bos:
            if htf_bos[-1].direction != ltf_bos[-1].direction:
                red_flags.append(
                    RedFlag(
                        flag_type=RedFlagType.STRUCTURE_CONFLICT,
                        description="BOS directions conflict",
                        confidence_penalty=0.10,
                    )
                )

        return red_flags

    def _build_setup(
        self,
        pair: str,
        htf_structure: StructureOutput,
        ltf_structure: StructureOutput,
        current_price: float,
        quality_score: float,
    ) -> Setup | None:
        """Build setup from structure."""
        # Determine setup type and direction
        setup_type, direction = self._determine_setup_type(ltf_structure)

        if setup_type is None:
            return None

        # Calculate entry, stop, target
        entry, stop, target = self._calculate_levels(ltf_structure, current_price, direction)

        # Calculate risk percent (using default)
        risk_percent = 1.0

        # Build evidence
        evidence = self.build_evidence(htf_structure, ltf_structure)

        return Setup(
            setup_id=f"SETUP-{uuid.uuid4().hex[:8]}",
            pair=pair,
            setup_type=setup_type,
            direction=direction,
            confidence=quality_score,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
            risk_percent=risk_percent,
            evidence=evidence,
        )

    def _determine_setup_type(
        self,
        structure: StructureOutput,
    ) -> tuple[SetupType | None, Direction]:
        """Determine setup type from structure."""
        # Priority: OTE > FVG > Sweep > BOS

        # Check for OTE
        ote_list = [s for s in structure.structures if isinstance(s, OTE)]
        if ote_list:
            recent_ote = ote_list[-1]
            if recent_ote.current_in_zone:
                return SetupType.OTE_ENTRY, recent_ote.direction

        # Check for unfilled FVG
        fvg_list = [s for s in structure.structures if isinstance(s, FVG)]
        valid_fvgs = [f for f in fvg_list if f.fill_percent < 0.5 and f.age_bars < 20]
        if valid_fvgs:
            recent_fvg = valid_fvgs[-1]
            return SetupType.FVG_ENTRY, recent_fvg.direction

        # Check for sweep
        sweep_list = [s for s in structure.structures if isinstance(s, LiquiditySweep)]
        if sweep_list:
            recent_sweep = sweep_list[-1]
            return SetupType.SWEEP_ENTRY, recent_sweep.direction

        # Check for BOS
        bos_list = [s for s in structure.structures if isinstance(s, BOS)]
        if bos_list:
            recent_bos = bos_list[-1]
            return SetupType.BOS_CONTINUATION, recent_bos.direction

        return None, Direction.NEUTRAL

    def _calculate_levels(
        self,
        structure: StructureOutput,
        current_price: float,
        direction: Direction,
    ) -> tuple[float, float, float]:
        """Calculate entry, stop, target levels."""
        # Find relevant structure for levels
        fvg_list = [s for s in structure.structures if isinstance(s, FVG)]

        # Default values
        entry = current_price
        stop_distance = 30 * self._pip_value  # 30 pips default

        # Use FVG for entry if available
        if fvg_list:
            recent_fvg = fvg_list[-1]
            if direction == Direction.BULLISH:
                entry = recent_fvg.gap_high  # Enter at top of bullish FVG
            else:
                entry = recent_fvg.gap_low  # Enter at bottom of bearish FVG

        # Use swing levels for stop if available
        if structure.swing_lows and direction == Direction.BULLISH:
            stop = min(structure.swing_lows[-3:]) - 5 * self._pip_value
        elif structure.swing_highs and direction == Direction.BEARISH:
            stop = max(structure.swing_highs[-3:]) + 5 * self._pip_value
        elif direction == Direction.BULLISH:
            stop = entry - stop_distance
        else:
            stop = entry + stop_distance

        # Calculate target based on 2:1 RR
        risk = abs(entry - stop)
        if direction == Direction.BULLISH:
            target = entry + (risk * 2)
        else:
            target = entry - (risk * 2)

        return entry, stop, target

    def _score_alignment(
        self,
        htf: StructureOutput,
        ltf: StructureOutput,
    ) -> float:
        """Score HTF/LTF alignment."""
        if htf.htf_bias == ltf.htf_bias:
            return 1.0
        if htf.htf_bias == Direction.NEUTRAL or ltf.htf_bias == Direction.NEUTRAL:
            return 0.5
        return 0.0  # Opposing biases

    def _score_fvg(self, structure: StructureOutput) -> float:
        """Score FVG quality."""
        fvg_list = [s for s in structure.structures if isinstance(s, FVG)]
        if not fvg_list:
            return 0.0

        # Score based on recency and fill
        recent_fvgs = [f for f in fvg_list if f.age_bars < 20]
        unfilled = [f for f in recent_fvgs if f.fill_percent < 0.3]

        if unfilled:
            return 1.0
        if recent_fvgs:
            return 0.5
        return 0.2

    def _score_liquidity(self, structure: StructureOutput) -> float:
        """Score liquidity context."""
        sweeps = [s for s in structure.structures if isinstance(s, LiquiditySweep)]
        if not sweeps:
            return 0.3  # Neutral

        # Recent sweep is bullish for setup
        recent_sweep = sweeps[-1]
        if recent_sweep.close_respected:
            return 1.0
        return 0.6

    def _score_bos(self, structure: StructureOutput) -> float:
        """Score recent BOS."""
        bos_list = [s for s in structure.structures if isinstance(s, BOS)]
        if not bos_list:
            return 0.2

        recent_bos = bos_list[-1]
        if recent_bos.confirmation_bars < 5:
            return 1.0
        if recent_bos.confirmation_bars < 15:
            return 0.7
        return 0.4
