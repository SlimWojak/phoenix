"""
Response Writer — File-Based Response Injection
================================================

Writes structured responses to files for Claude to read.

Pattern:
1. Phoenix components write to responses/{type}.md
2. Claude uses MCP tool to read
3. Files have TTL and auto-expire
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# =============================================================================
# ENUMS
# =============================================================================


class ResponseType(str, Enum):
    """Types of responses."""

    CSO_BRIEFING = "cso_briefing"
    SHADOW_POSITIONS = "shadow_positions"
    DECAY_ALERT = "decay_alert"
    ATHENA_RESULT = "athena_result"
    STATE_ANCHOR = "state_anchor"
    KILL_FLAGS = "kill_flags"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class Response:
    """A response to be written."""

    response_type: ResponseType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    ttl_minutes: int = 30
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_markdown(self) -> str:
        """Format as markdown with frontmatter."""
        expires_at = self.timestamp + timedelta(minutes=self.ttl_minutes)

        lines = [
            "---",
            f"type: {self.response_type.value}",
            f"generated: {self.timestamp.isoformat()}",
            f"expires: {expires_at.isoformat()}",
            f"ttl_minutes: {self.ttl_minutes}",
        ]

        for key, value in self.metadata.items():
            if isinstance(value, dict | list):
                lines.append(f"{key}: {json.dumps(value)}")
            else:
                lines.append(f"{key}: {value}")

        lines.extend(["---", "", self.content])

        return "\n".join(lines)


# =============================================================================
# RESPONSE WRITER
# =============================================================================


class ResponseWriter:
    """
    Writes responses to files for Claude consumption.

    Simple file I/O. No daemon required.
    """

    def __init__(self, responses_dir: Path | None = None) -> None:
        """
        Initialize response writer.

        Args:
            responses_dir: Directory for response files
        """
        if responses_dir is None:
            responses_dir = Path(__file__).parent.parent / "responses"

        self._responses_dir = responses_dir
        self._responses_dir.mkdir(parents=True, exist_ok=True)

    def write(self, response: Response) -> Path:
        """
        Write response to file.

        Args:
            response: Response to write

        Returns:
            Path to written file
        """
        filename = f"{response.response_type.value}.md"
        filepath = self._responses_dir / filename

        content = response.to_markdown()
        filepath.write_text(content)

        return filepath

    def write_cso_briefing(
        self,
        summary: str,
        ready_pairs: list[str],
        forming_pairs: list[str],
    ) -> Path:
        """
        Write CSO briefing response.

        Args:
            summary: Scan summary text
            ready_pairs: Pairs with ready setups
            forming_pairs: Pairs with forming setups

        Returns:
            Path to written file
        """
        content = [
            "# CSO Briefing",
            "",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            "",
            "## Scan Results",
            "",
            summary,
            "",
        ]

        if ready_pairs:
            content.extend(
                [
                    "## Ready Setups",
                    "",
                    *[f"- **{p}** — Ready for entry" for p in ready_pairs],
                    "",
                ]
            )

        if forming_pairs:
            content.extend(
                [
                    "## Forming Setups",
                    "",
                    *[f"- {p} — Watch list" for p in forming_pairs],
                    "",
                ]
            )

        response = Response(
            response_type=ResponseType.CSO_BRIEFING,
            content="\n".join(content),
            metadata={
                "ready_count": len(ready_pairs),
                "forming_count": len(forming_pairs),
            },
            ttl_minutes=30,
        )

        return self.write(response)

    def write_shadow_positions(
        self,
        positions: list[dict],
        total_pnl: float,
    ) -> Path:
        """
        Write shadow positions response.

        Args:
            positions: List of position dicts
            total_pnl: Total P&L across positions

        Returns:
            Path to written file
        """
        content = [
            "# Shadow Positions",
            "",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            "",
            f"**Total P&L:** {total_pnl:+.2f}%",
            "",
            "## Open Positions",
            "",
        ]

        if positions:
            content.append("| Pair | Direction | Entry | Current | P&L |")
            content.append("|------|-----------|-------|---------|-----|")

            for pos in positions:
                content.append(
                    f"| {pos.get('pair', 'N/A')} | "
                    f"{pos.get('direction', 'N/A')} | "
                    f"{pos.get('entry_price', 0):.5f} | "
                    f"{pos.get('current_price', 0):.5f} | "
                    f"{pos.get('pnl_percent', 0):+.2f}% |"
                )
        else:
            content.append("*No open positions*")

        response = Response(
            response_type=ResponseType.SHADOW_POSITIONS,
            content="\n".join(content),
            metadata={
                "position_count": len(positions),
                "total_pnl": total_pnl,
            },
            ttl_minutes=15,
        )

        return self.write(response)

    def write_decay_alert(
        self,
        strategy_id: str,
        decay_type: str,
        severity: str,
        details: str,
    ) -> Path:
        """
        Write decay alert response.

        Args:
            strategy_id: Affected strategy
            decay_type: Type of decay (performance, signal, etc.)
            severity: CRITICAL, WARNING, INFO
            details: Alert details

        Returns:
            Path to written file
        """
        emoji = {"CRITICAL": "🚨", "WARNING": "⚠️", "INFO": "ℹ️"}.get(severity, "ℹ️")

        content = [
            f"# {emoji} Decay Alert",
            "",
            f"**Strategy:** {strategy_id}",
            f"**Type:** {decay_type}",
            f"**Severity:** {severity}",
            f"**Time:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            "",
            "## Details",
            "",
            details,
            "",
        ]

        if severity == "CRITICAL":
            content.extend(
                [
                    "## Action Required",
                    "",
                    "This strategy may require a ONE-WAY-KILL flag.",
                    "Review decay metrics and consider halting new entries.",
                ]
            )

        response = Response(
            response_type=ResponseType.DECAY_ALERT,
            content="\n".join(content),
            metadata={
                "strategy_id": strategy_id,
                "decay_type": decay_type,
                "severity": severity,
            },
            ttl_minutes=60 if severity == "CRITICAL" else 30,
        )

        return self.write(response)

    def write_athena_result(
        self,
        query: str,
        result_count: int,
        results: list[dict],
    ) -> Path:
        """
        Write Athena query result.

        Args:
            query: Original query
            result_count: Number of results
            results: Result beads

        Returns:
            Path to written file
        """
        content = [
            "# Athena Query Result",
            "",
            f"**Query:** {query}",
            f"**Results:** {result_count}",
            f"**Time:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            "",
            "## Results",
            "",
        ]

        for i, result in enumerate(results[:10], 1):  # Limit to 10
            content.extend(
                [
                    f"### {i}. {result.get('bead_type', 'UNKNOWN')}",
                    f"**ID:** {result.get('bead_id', 'N/A')}",
                    f"**Created:** {result.get('timestamp_utc', 'N/A')}",
                    "",
                ]
            )

            if result.get("content"):
                # Show summary of content
                content.append("```")
                content.append(json.dumps(result["content"], indent=2)[:500])
                content.append("```")
                content.append("")

        if result_count > 10:
            content.append(f"*... and {result_count - 10} more results*")

        response = Response(
            response_type=ResponseType.ATHENA_RESULT,
            content="\n".join(content),
            metadata={
                "query": query,
                "result_count": result_count,
            },
            ttl_minutes=15,
        )

        return self.write(response)

    def write_state_anchor(
        self,
        anchor_id: str,
        combined_hash: str,
        ttl_remaining: int,
        components: dict[str, str],
    ) -> Path:
        """
        Write state anchor for T2 intents.

        Args:
            anchor_id: Anchor identifier
            combined_hash: Combined state hash
            ttl_remaining: Minutes until expiry
            components: Component hashes

        Returns:
            Path to written file
        """
        content = [
            "# State Anchor",
            "",
            f"**Anchor ID:** {anchor_id}",
            f"**Combined Hash:** {combined_hash}",
            f"**TTL Remaining:** {ttl_remaining} minutes",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            "",
            "## Component Hashes",
            "",
        ]

        for component, hash_val in components.items():
            content.append(f"- **{component}:** `{hash_val}`")

        content.extend(
            [
                "",
                "## Usage",
                "",
                "Include `state_hash` in T2 intents:",
                "",
                "```json",
                json.dumps({"state_hash": combined_hash}, indent=2),
                "```",
            ]
        )

        response = Response(
            response_type=ResponseType.STATE_ANCHOR,
            content="\n".join(content),
            metadata={
                "anchor_id": anchor_id,
                "combined_hash": combined_hash,
                "ttl_remaining": ttl_remaining,
                "components": components,
            },
            ttl_minutes=ttl_remaining,
        )

        return self.write(response)

    def write_kill_flags(
        self,
        active_flags: list[dict],
    ) -> Path:
        """
        Write active kill flags.

        Args:
            active_flags: List of active kill flag dicts

        Returns:
            Path to written file
        """
        content = [
            "# Active Kill Flags",
            "",
            f"**Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')} UTC",
            f"**Active Flags:** {len(active_flags)}",
            "",
        ]

        if active_flags:
            content.append("## Flags")
            content.append("")

            for flag in active_flags:
                content.extend(
                    [
                        f"### {flag.get('strategy_id', 'N/A')}",
                        f"**Reason:** {flag.get('reason', 'N/A')}",
                        f"**Triggered By:** {flag.get('triggered_by', 'N/A')}",
                        f"**Time:** {flag.get('timestamp', 'N/A')}",
                        "",
                    ]
                )
        else:
            content.append("*No active kill flags*")

        response = Response(
            response_type=ResponseType.KILL_FLAGS,
            content="\n".join(content),
            metadata={
                "flag_count": len(active_flags),
            },
            ttl_minutes=15,
        )

        return self.write(response)

    def read(self, response_type: ResponseType) -> Response | None:
        """
        Read response from file (for MCP tool).

        Args:
            response_type: Type of response to read

        Returns:
            Response if exists and not expired, else None
        """
        filename = f"{response_type.value}.md"
        filepath = self._responses_dir / filename

        if not filepath.exists():
            return None

        content = filepath.read_text()

        # Parse frontmatter
        if not content.startswith("---"):
            return None

        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        # Parse metadata
        metadata: dict[str, Any] = {}
        for line in parts[1].strip().split("\n"):
            if ": " in line:
                key, value = line.split(": ", 1)
                metadata[key] = value

        # Check expiry
        expires = metadata.get("expires", "")
        if expires:
            try:
                expires_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                if datetime.now(UTC) > expires_dt:
                    return None  # Expired
            except ValueError:
                pass

        return Response(
            response_type=response_type,
            content=parts[2].strip(),
            metadata=metadata,
            ttl_minutes=int(metadata.get("ttl_minutes", 30)),
        )

    def clear_expired(self) -> int:
        """
        Clear expired response files.

        Returns:
            Number of files cleared
        """
        cleared = 0

        for filepath in self._responses_dir.glob("*.md"):
            content = filepath.read_text()

            if not content.startswith("---"):
                continue

            parts = content.split("---", 2)
            if len(parts) < 3:
                continue

            for line in parts[1].strip().split("\n"):
                if line.startswith("expires: "):
                    expires = line.replace("expires: ", "")
                    try:
                        expires_dt = datetime.fromisoformat(expires.replace("Z", "+00:00"))
                        if datetime.now(UTC) > expires_dt:
                            filepath.unlink()
                            cleared += 1
                    except ValueError:
                        pass
                    break

        return cleared
