"""
T2 Evidence — Evidence bundle assembly
======================================

S32: EXECUTION_PATH

Assembles the evidence bundle that humans approve before
capital-affecting operations.

What human sees:
- Setup quality score + breakdown
- HTF/LTF alignment summary
- Risk parameters
- State anchor freshness
- Kill flag status
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class SetupEvidence:
    """Evidence from CSO setup detection."""

    quality_score: float = 0.0
    setup_type: str = ""
    pair: str = ""
    confidence: float = 0.0
    breakdown: dict[str, float] = field(default_factory=dict)


@dataclass
class AlignmentEvidence:
    """Evidence of timeframe alignment."""

    htf_bias: str = ""  # BULLISH, BEARISH, NEUTRAL
    htf_confirmed: bool = False
    htf_structure: str = ""  # BOS, CHOCH, etc.
    ltf_setup: str = ""  # FVG, OTE, etc.
    ltf_level: float = 0.0


@dataclass
class RiskEvidence:
    """Risk parameters for the trade."""

    entry_price: float = 0.0
    stop_price: float = 0.0
    target_price: float = 0.0
    risk_percent: float = 0.0
    reward_ratio: float = 0.0

    @property
    def stop_distance_pips(self) -> float:
        """Calculate stop distance in pips."""
        return abs(self.entry_price - self.stop_price) * 10000

    @property
    def target_distance_pips(self) -> float:
        """Calculate target distance in pips."""
        return abs(self.target_price - self.entry_price) * 10000


@dataclass
class StateEvidence:
    """Evidence of state anchor freshness."""

    state_hash: str = ""
    captured_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl_remaining_sec: int = 0
    is_fresh: bool = True


@dataclass
class SafetyEvidence:
    """Safety check results."""

    kill_flags_active: bool = False
    kill_flag_details: list[str] = field(default_factory=list)
    red_checks_passed: int = 0
    red_checks_total: int = 0
    unresolved_drift: bool = False


@dataclass
class EvidenceBundle:
    """
    Complete evidence bundle for T2 approval.

    This is what humans see before approving a trade.
    The hash of this bundle binds the approval to the context.
    """

    bundle_id: str = ""
    intent_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Evidence components
    setup: SetupEvidence = field(default_factory=SetupEvidence)
    alignment: AlignmentEvidence = field(default_factory=AlignmentEvidence)
    risk: RiskEvidence = field(default_factory=RiskEvidence)
    state: StateEvidence = field(default_factory=StateEvidence)
    safety: SafetyEvidence = field(default_factory=SafetyEvidence)

    @property
    def is_approvable(self) -> bool:
        """Check if bundle passes minimum requirements."""
        return (
            self.safety.kill_flags_active is False
            and self.safety.unresolved_drift is False
            and self.state.is_fresh
            and self.setup.quality_score > 0
        )

    @property
    def approval_blockers(self) -> list[str]:
        """Get list of blockers preventing approval."""
        blockers = []
        if self.safety.kill_flags_active:
            blockers.append("Active kill flag(s)")
        if self.safety.unresolved_drift:
            blockers.append("Unresolved reconciliation drift")
        if not self.state.is_fresh:
            blockers.append("Stale state anchor")
        if self.setup.quality_score <= 0:
            blockers.append("Invalid setup quality")
        return blockers

    def compute_hash(self) -> str:
        """
        Compute hash of evidence bundle.

        This hash binds the approval to the exact context.
        Any change in evidence invalidates the approval.
        """
        # Deterministic JSON for hashing
        evidence_dict = {
            "intent_id": self.intent_id,
            "setup": {
                "quality_score": self.setup.quality_score,
                "setup_type": self.setup.setup_type,
                "pair": self.setup.pair,
            },
            "alignment": {
                "htf_bias": self.alignment.htf_bias,
                "htf_confirmed": self.alignment.htf_confirmed,
            },
            "risk": {
                "entry_price": self.risk.entry_price,
                "stop_price": self.risk.stop_price,
                "target_price": self.risk.target_price,
                "risk_percent": self.risk.risk_percent,
            },
            "state": {
                "state_hash": self.state.state_hash,
            },
            "safety": {
                "kill_flags_active": self.safety.kill_flags_active,
                "unresolved_drift": self.safety.unresolved_drift,
            },
        }

        json_str = json.dumps(evidence_dict, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()

    def to_display(self) -> dict[str, str]:
        """
        Format evidence for human display.

        Returns dictionary of display strings.
        """
        return {
            "Quality": f"{self.setup.quality_score:.2f} ({self.setup.setup_type})",
            "Pair": self.setup.pair,
            "HTF": f"{self.alignment.htf_bias} ({'+' if self.alignment.htf_confirmed else '-'})",
            "LTF": f"{self.alignment.ltf_setup} at {self.alignment.ltf_level:.5f}",
            "Entry": f"{self.risk.entry_price:.5f}",
            "Stop": f"{self.risk.stop_price:.5f} ({self.risk.stop_distance_pips:.1f} pips)",
            "Target": f"{self.risk.target_price:.5f} ({self.risk.target_distance_pips:.1f} pips)",
            "Risk": f"{self.risk.risk_percent:.2f}%",
            "R:R": f"1:{self.risk.reward_ratio:.1f}",
            "State": f"{'OK' if self.state.is_fresh else 'OLD'} ({self.state.ttl_remaining_sec}s)",
            "Kill Flags": "NONE" if not self.safety.kill_flags_active else "ACTIVE",
            "Red Checks": f"{self.safety.red_checks_passed}/{self.safety.red_checks_total} passed",
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "bundle_id": self.bundle_id,
            "intent_id": self.intent_id,
            "created_at": self.created_at.isoformat(),
            "is_approvable": self.is_approvable,
            "blockers": self.approval_blockers,
            "hash": self.compute_hash(),
            "setup": {
                "quality_score": self.setup.quality_score,
                "setup_type": self.setup.setup_type,
                "pair": self.setup.pair,
                "confidence": self.setup.confidence,
            },
            "alignment": {
                "htf_bias": self.alignment.htf_bias,
                "htf_confirmed": self.alignment.htf_confirmed,
                "htf_structure": self.alignment.htf_structure,
                "ltf_setup": self.alignment.ltf_setup,
                "ltf_level": self.alignment.ltf_level,
            },
            "risk": {
                "entry_price": self.risk.entry_price,
                "stop_price": self.risk.stop_price,
                "target_price": self.risk.target_price,
                "risk_percent": self.risk.risk_percent,
                "reward_ratio": self.risk.reward_ratio,
            },
            "state": {
                "state_hash": self.state.state_hash,
                "captured_at": self.state.captured_at.isoformat(),
                "ttl_remaining_sec": self.state.ttl_remaining_sec,
                "is_fresh": self.state.is_fresh,
            },
            "safety": {
                "kill_flags_active": self.safety.kill_flags_active,
                "kill_flag_details": self.safety.kill_flag_details,
                "red_checks_passed": self.safety.red_checks_passed,
                "red_checks_total": self.safety.red_checks_total,
                "unresolved_drift": self.safety.unresolved_drift,
            },
        }


class EvidenceBuilder:
    """
    Builder for assembling evidence bundles.

    Gathers evidence from various sources and assembles
    a complete bundle for human approval.
    """

    def __init__(self, intent_id: str) -> None:
        """
        Initialize builder.

        Args:
            intent_id: Intent this evidence is for
        """
        self._intent_id = intent_id
        self._bundle = EvidenceBundle(intent_id=intent_id)
        self._bundle.bundle_id = f"EVD-{intent_id[:8]}"

    def with_setup(
        self,
        quality_score: float,
        setup_type: str,
        pair: str,
        confidence: float = 0.0,
        breakdown: dict[str, float] | None = None,
    ) -> EvidenceBuilder:
        """Add setup evidence."""
        self._bundle.setup = SetupEvidence(
            quality_score=quality_score,
            setup_type=setup_type,
            pair=pair,
            confidence=confidence,
            breakdown=breakdown or {},
        )
        return self

    def with_alignment(
        self,
        htf_bias: str,
        htf_confirmed: bool,
        htf_structure: str = "",
        ltf_setup: str = "",
        ltf_level: float = 0.0,
    ) -> EvidenceBuilder:
        """Add alignment evidence."""
        self._bundle.alignment = AlignmentEvidence(
            htf_bias=htf_bias,
            htf_confirmed=htf_confirmed,
            htf_structure=htf_structure,
            ltf_setup=ltf_setup,
            ltf_level=ltf_level,
        )
        return self

    def with_risk(
        self,
        entry_price: float,
        stop_price: float,
        target_price: float,
        risk_percent: float,
    ) -> EvidenceBuilder:
        """Add risk evidence."""
        # Calculate reward ratio
        stop_dist = abs(entry_price - stop_price)
        target_dist = abs(target_price - entry_price)
        reward_ratio = target_dist / stop_dist if stop_dist > 0 else 0.0

        self._bundle.risk = RiskEvidence(
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            risk_percent=risk_percent,
            reward_ratio=reward_ratio,
        )
        return self

    def with_state(
        self,
        state_hash: str,
        captured_at: datetime,
        ttl_sec: int,
    ) -> EvidenceBuilder:
        """Add state evidence."""
        elapsed = (datetime.now(UTC) - captured_at).total_seconds()
        ttl_remaining = max(0, ttl_sec - int(elapsed))

        self._bundle.state = StateEvidence(
            state_hash=state_hash,
            captured_at=captured_at,
            ttl_remaining_sec=ttl_remaining,
            is_fresh=ttl_remaining > 0,
        )
        return self

    def with_safety(
        self,
        kill_flags_active: bool = False,
        kill_flag_details: list[str] | None = None,
        red_checks_passed: int = 0,
        red_checks_total: int = 0,
        unresolved_drift: bool = False,
    ) -> EvidenceBuilder:
        """Add safety evidence."""
        self._bundle.safety = SafetyEvidence(
            kill_flags_active=kill_flags_active,
            kill_flag_details=kill_flag_details or [],
            red_checks_passed=red_checks_passed,
            red_checks_total=red_checks_total,
            unresolved_drift=unresolved_drift,
        )
        return self

    def build(self) -> EvidenceBundle:
        """Build the evidence bundle."""
        return self._bundle
