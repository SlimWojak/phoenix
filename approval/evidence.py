"""
CSE Evidence Display — 5-Drawer T2 Evidence
============================================

S34: D2 MOCK_ORACLE_PIPELINE_VALIDATION

Builds and displays evidence bundles for T2 approval,
showing 5-drawer gate requirements and source refs.

INVARIANT: INV-D2-TRACEABLE-1
Evidence refs link to conditions.yaml gate definitions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class GateRequirement:
    """A single requirement from a 5-drawer gate."""

    requirement: str
    status: str = "UNKNOWN"  # MET, NOT_MET, UNKNOWN
    source_ref: str = ""


@dataclass
class GateEvidence:
    """Evidence from a 5-drawer gate."""

    gate_id: str
    gate_name: str
    output: str
    requirements: list[GateRequirement] = field(default_factory=list)
    source_file: str = ""
    resolved: bool = False


@dataclass
class TradeEvidence:
    """Trade-specific evidence."""

    pair: str = ""
    direction: str = ""
    entry: float = 0.0
    stop: float = 0.0
    target: float = 0.0
    risk_percent: float = 1.0
    risk_reward: float = 0.0
    stop_pips: float = 0.0
    target_pips: float = 0.0


@dataclass
class CSEEvidence:
    """
    Complete evidence bundle for CSE approval.

    Contains:
    - Signal metadata
    - 5-drawer gate evidence
    - Trade parameters
    - Approval status
    """

    evidence_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    signal_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Source
    source: str = ""
    setup_type: str = ""
    confidence: float = 0.0

    # 5-drawer gate evidence
    gate_evidence: GateEvidence | None = None

    # Trade parameters
    trade: TradeEvidence = field(default_factory=TradeEvidence)

    # Evidence hash for binding
    evidence_hash: str = ""

    @property
    def is_mock(self) -> bool:
        """Check if this is mock evidence."""
        return self.source == "MOCK_5DRAWER"

    @property
    def is_approvable(self) -> bool:
        """Check if evidence passes minimum requirements."""
        return (
            self.confidence > 0
            and self.trade.entry > 0
            and self.trade.stop > 0
            and self.trade.target > 0
            and self.trade.risk_reward >= 1.0
        )

    @property
    def blockers(self) -> list[str]:
        """Get list of approval blockers."""
        blockers = []
        if self.confidence <= 0:
            blockers.append("Invalid confidence")
        if self.trade.entry <= 0:
            blockers.append("Missing entry price")
        if self.trade.risk_reward < 1.0:
            blockers.append(f"R:R below 1:1 ({self.trade.risk_reward:.2f})")
        return blockers

    def _format_requirement(self, r: GateRequirement) -> str:
        """Format a single gate requirement for display."""
        icon = "✓" if r.status == "MET" else "?" if r.status == "UNKNOWN" else "✗"
        return f"{icon} {r.requirement}"

    def to_display_dict(self) -> dict[str, Any]:
        """Convert to human-readable display format."""
        display = {
            "Evidence ID": self.evidence_id,
            "Signal ID": self.signal_id[:8] + "..." if self.signal_id else "N/A",
            "Source": self.source,
            "Setup": self.setup_type,
            "Confidence": f"{self.confidence:.0%}",
        }

        # Trade parameters
        display["Trade"] = {
            "Pair": self.trade.pair,
            "Direction": self.trade.direction,
            "Entry": f"{self.trade.entry:.5f}",
            "Stop": f"{self.trade.stop:.5f} ({self.trade.stop_pips:.1f} pips)",
            "Target": f"{self.trade.target:.5f} ({self.trade.target_pips:.1f} pips)",
            "Risk": f"{self.trade.risk_percent:.1f}%",
            "R:R": f"1:{self.trade.risk_reward:.1f}",
        }

        # 5-drawer gate evidence
        if self.gate_evidence:
            display["5-Drawer Gate"] = {
                "Gate ID": self.gate_evidence.gate_id,
                "Name": self.gate_evidence.gate_name,
                "Output": self.gate_evidence.output,
                "Source": self.gate_evidence.source_file,
                "Requirements": [
                    self._format_requirement(r) for r in self.gate_evidence.requirements
                ],
            }

        # Approval status
        display["Approval"] = {
            "Approvable": "YES" if self.is_approvable else "NO",
            "Blockers": self.blockers if self.blockers else ["None"],
            "Mock": "YES" if self.is_mock else "NO",
        }

        return display

    def to_dict(self) -> dict[str, Any]:
        """Convert to full dictionary."""
        return {
            "evidence_id": self.evidence_id,
            "signal_id": self.signal_id,
            "created_at": self.created_at.isoformat(),
            "source": self.source,
            "setup_type": self.setup_type,
            "confidence": self.confidence,
            "gate_evidence": {
                "gate_id": self.gate_evidence.gate_id,
                "gate_name": self.gate_evidence.gate_name,
                "output": self.gate_evidence.output,
                "requirements": [
                    {"requirement": r.requirement, "status": r.status}
                    for r in self.gate_evidence.requirements
                ],
                "source_file": self.gate_evidence.source_file,
                "resolved": self.gate_evidence.resolved,
            }
            if self.gate_evidence
            else None,
            "trade": {
                "pair": self.trade.pair,
                "direction": self.trade.direction,
                "entry": self.trade.entry,
                "stop": self.trade.stop,
                "target": self.trade.target,
                "risk_percent": self.trade.risk_percent,
                "risk_reward": self.trade.risk_reward,
            },
            "evidence_hash": self.evidence_hash,
            "is_approvable": self.is_approvable,
            "blockers": self.blockers,
        }


# =============================================================================
# EVIDENCE BUILDER
# =============================================================================


class CSEEvidenceBuilder:
    """
    Builds evidence bundles from CSE signals.

    INV-D2-TRACEABLE-1: Links to 5-drawer source refs.
    """

    def __init__(self, knowledge_dir: Path | None = None) -> None:
        """Initialize builder."""
        self._knowledge_dir = knowledge_dir or (Path(__file__).parent.parent / "cso" / "knowledge")

    def build_from_cse(self, cse: dict[str, Any]) -> CSEEvidence:
        """
        Build evidence from CSE dictionary.

        Args:
            cse: CSE dictionary

        Returns:
            CSEEvidence with all fields populated
        """
        evidence = CSEEvidence(
            signal_id=cse.get("signal_id", ""),
            source=cse.get("source", ""),
            setup_type=cse.get("setup_type", ""),
            confidence=cse.get("confidence", 0.0),
            evidence_hash=cse.get("evidence_hash", ""),
        )

        # Extract trade parameters
        params = cse.get("parameters", {})
        entry = params.get("entry", 0.0)
        stop = params.get("stop", 0.0)
        target = params.get("target", 0.0)
        risk_percent = params.get("risk_percent", 1.0)

        # Calculate derived values
        direction = "LONG" if entry < target else "SHORT"
        stop_dist = abs(entry - stop)
        target_dist = abs(target - entry)
        risk_reward = target_dist / stop_dist if stop_dist > 0 else 0.0

        # Pip calculation
        pair = cse.get("pair", "")
        pip_mult = 10000 if "JPY" not in pair else 100
        stop_pips = stop_dist * pip_mult
        target_pips = target_dist * pip_mult

        evidence.trade = TradeEvidence(
            pair=pair,
            direction=direction,
            entry=entry,
            stop=stop,
            target=target,
            risk_percent=risk_percent,
            risk_reward=risk_reward,
            stop_pips=stop_pips,
            target_pips=target_pips,
        )

        # Extract 5-drawer gate evidence
        mock_meta = cse.get("_mock_metadata", {})
        gate_ref = mock_meta.get("gate_ref", {})

        if gate_ref:
            requirements = [
                GateRequirement(requirement=req, status="UNKNOWN")
                for req in gate_ref.get("requires", [])
            ]

            source_file = gate_ref.get("source", "")
            if source_file == "conditions.yaml":
                source_file = str(self._knowledge_dir / "conditions.yaml")

            evidence.gate_evidence = GateEvidence(
                gate_id=gate_ref.get("gate_id", ""),
                gate_name=gate_ref.get("name", ""),
                output=cse.get("setup_type", ""),
                requirements=requirements,
                source_file=source_file,
                resolved=Path(source_file).exists() if source_file else False,
            )

        return evidence


# =============================================================================
# EVIDENCE DISPLAY
# =============================================================================


class EvidenceDisplay:
    """
    Formats evidence for human display.

    Outputs evidence in readable format for T2 approval.
    """

    @staticmethod
    def to_markdown(evidence: CSEEvidence) -> str:
        """
        Format evidence as Markdown for display.

        Args:
            evidence: CSEEvidence to format

        Returns:
            Markdown string
        """
        lines = [
            "# T2 Approval Evidence",
            "",
            f"**Evidence ID:** {evidence.evidence_id}",
            f"**Signal ID:** {evidence.signal_id[:8]}..." if evidence.signal_id else "",
            f"**Source:** {evidence.source}",
            f"**Created:** {evidence.created_at.strftime('%Y-%m-%d %H:%M')} UTC",
            "",
            "---",
            "",
            "## Trade Setup",
            "",
            f"- **Pair:** {evidence.trade.pair}",
            f"- **Direction:** {evidence.trade.direction}",
            f"- **Setup Type:** {evidence.setup_type}",
            f"- **Confidence:** {evidence.confidence:.0%}",
            "",
            "## Price Levels",
            "",
            f"- **Entry:** {evidence.trade.entry:.5f}",
            f"- **Stop:** {evidence.trade.stop:.5f} ({evidence.trade.stop_pips:.1f} pips)",
            f"- **Target:** {evidence.trade.target:.5f} ({evidence.trade.target_pips:.1f} pips)",
            "",
            "## Risk Parameters",
            "",
            f"- **Risk:** {evidence.trade.risk_percent:.1f}%",
            f"- **R:R:** 1:{evidence.trade.risk_reward:.1f}",
            "",
        ]

        # 5-drawer gate section
        if evidence.gate_evidence:
            lines.extend(
                [
                    "---",
                    "",
                    "## 5-Drawer Gate Evidence",
                    "",
                    f"**Gate ID:** {evidence.gate_evidence.gate_id}",
                    f"**Name:** {evidence.gate_evidence.gate_name}",
                    f"**Output:** {evidence.gate_evidence.output}",
                    "",
                    "### Requirements",
                    "",
                ]
            )

            for req in evidence.gate_evidence.requirements:
                icon = "✓" if req.status == "MET" else "?" if req.status == "UNKNOWN" else "✗"
                lines.append(f"- {icon} {req.requirement}")

            lines.extend(
                [
                    "",
                    f"**Source:** `{evidence.gate_evidence.source_file}`",
                    f"**Resolved:** {'Yes' if evidence.gate_evidence.resolved else 'No'}",
                ]
            )

        # Approval section
        lines.extend(
            [
                "",
                "---",
                "",
                "## Approval Status",
                "",
            ]
        )

        if evidence.is_approvable:
            lines.append("**Status:** ✅ APPROVABLE")
        else:
            lines.append("**Status:** ❌ NOT APPROVABLE")
            lines.append("")
            lines.append("**Blockers:**")
            for blocker in evidence.blockers:
                lines.append(f"- {blocker}")

        if evidence.is_mock:
            lines.extend(
                [
                    "",
                    "⚠️ **This is MOCK evidence from 5-drawer gates, not production CSO.**",
                ]
            )

        return "\n".join(lines)

    @staticmethod
    def to_compact(evidence: CSEEvidence) -> str:
        """
        Format evidence as compact summary.

        Args:
            evidence: CSEEvidence to format

        Returns:
            Compact string
        """
        parts = [
            f"[{evidence.evidence_id}]",
            evidence.trade.pair,
            evidence.trade.direction,
            f"@{evidence.trade.entry:.5f}",
            f"SL:{evidence.trade.stop_pips:.0f}p",
            f"TP:{evidence.trade.target_pips:.0f}p",
            f"RR:1:{evidence.trade.risk_reward:.1f}",
            f"{evidence.confidence:.0%}",
        ]

        if evidence.gate_evidence:
            parts.append(f"[{evidence.gate_evidence.gate_id}]")

        status = "✅" if evidence.is_approvable else "❌"
        parts.append(status)

        if evidence.is_mock:
            parts.append("(MOCK)")

        return " | ".join(parts)

    @staticmethod
    def write_to_file(evidence: CSEEvidence, output_path: Path) -> Path:
        """
        Write evidence to response file for Claude.

        Args:
            evidence: CSEEvidence to write
            output_path: Path to write to

        Returns:
            Path to written file
        """
        content = EvidenceDisplay.to_markdown(evidence)

        # Add frontmatter
        frontmatter = f"""---
type: t2_evidence
evidence_id: {evidence.evidence_id}
signal_id: {evidence.signal_id}
generated: {datetime.now(UTC).isoformat()}
approvable: {evidence.is_approvable}
mock: {evidence.is_mock}
---

"""

        output_path.write_text(frontmatter + content)
        return output_path
