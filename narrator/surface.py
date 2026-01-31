"""
Surface Polish — S41 Phase 2E
=============================

Human-readable transformations for narrator output.
Maps technical IDs to factual phrases.

PRINCIPLE: "The boar barks FOR you, not AT you"

RED-LINES (GPT ENFORCED):
  RL1: No grade/count proxies (no "4/5 gates", "near ready")
  RL2: Every phrase maps 1:1 to gate predicate
  RL3: Alert one-liners keep essential facts
  RL4: No jargon in degraded messages
  RL5: Receipts hidden but logged
  RL6: Guard dog still effective

Date: 2026-01-30
Sprint: S41 Phase 2E
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


# =============================================================================
# GATE PHRASE MAPPING (RL2: 1:1 deterministic)
# =============================================================================


# Each gate_id maps to EXACTLY one phrase
# No synthesis, no interpretation — just gate status facts
GATE_PHRASES: dict[int, str] = {
    # HTF Alignment Gates (1-5)
    1: "HTF structure present",
    2: "HTF bias confirmed",
    3: "HTF level identified",
    4: "HTF displacement visible",
    5: "HTF premium/discount zone",
    
    # LTF Confirmation Gates (6-10)
    6: "LTF break of structure",
    7: "LTF FVG present",
    8: "LTF displacement confirmed",
    9: "LTF sweep completed",
    10: "LTF order block identified",
    
    # Risk Gates (11-15)
    11: "Risk within limit",
    12: "Position size valid",
    13: "Correlation check passed",
    14: "Session overlap verified",
    15: "News filter cleared",
}

# Reverse mapping for validation
PHRASE_TO_GATE: dict[str, int] = {v: k for k, v in GATE_PHRASES.items()}


def gates_to_phrases(gate_ids: list[int]) -> list[str]:
    """
    Convert gate IDs to human-readable phrases.
    
    Each phrase maps 1:1 to a gate predicate.
    Unknown gates produce "Gate {id} passed".
    
    Args:
        gate_ids: List of gate IDs that passed
        
    Returns:
        List of deterministic phrase strings
    """
    phrases = []
    for gid in gate_ids:
        phrase = GATE_PHRASES.get(gid, f"Gate {gid} passed")
        phrases.append(phrase)
    return phrases


def format_gate_facts(gate_ids: list[int]) -> str:
    """
    Format gates as comma-separated facts.
    
    Args:
        gate_ids: List of gate IDs
        
    Returns:
        Human-readable string of gate facts
    """
    if not gate_ids:
        return "No gates passed"
    phrases = gates_to_phrases(gate_ids)
    return ", ".join(phrases)


# =============================================================================
# DEGRADED STATE MESSAGES (RL4: No jargon)
# =============================================================================


class DegradedState(str, Enum):
    """System degraded states."""
    
    RIVER_OFFLINE = "RIVER_OFFLINE"
    IBKR_DISCONNECTED = "IBKR_DISCONNECTED"
    STALE_DATA = "STALE_DATA"
    MISSING_DATA = "MISSING_DATA"
    CIRCUIT_OPEN = "CIRCUIT_OPEN"
    UNKNOWN_STATE = "UNKNOWN_STATE"
    HERESY_BLOCKED = "HERESY_BLOCKED"
    SUPERVISOR_DOWN = "SUPERVISOR_DOWN"
    HALT_ACTIVE = "HALT_ACTIVE"


# Human messages for degraded states
# RL4: No "provenance", "bead", "enum", "hash"
DEGRADED_MESSAGES: dict[DegradedState, str] = {
    DegradedState.RIVER_OFFLINE: "Data stream paused — waiting for connection",
    DegradedState.IBKR_DISCONNECTED: "Broker offline — positions frozen",
    DegradedState.STALE_DATA: "Data gap — last update was {minutes}m ago",
    DegradedState.MISSING_DATA: "Waiting for fresh data snapshot",
    DegradedState.CIRCUIT_OPEN: "Circuit open — {component} recovering",
    DegradedState.UNKNOWN_STATE: "System uncertain — verify manually",
    DegradedState.HERESY_BLOCKED: "Blocked — {category} detected",
    DegradedState.SUPERVISOR_DOWN: "Supervisor offline — no new orders",
    DegradedState.HALT_ACTIVE: "System halted — {reason}",
}


def get_degraded_message(state: DegradedState, **kwargs: Any) -> str:
    """
    Get human-readable message for degraded state.
    
    Args:
        state: The degraded state
        **kwargs: Format parameters (minutes, component, category, reason)
        
    Returns:
        Human-readable message with substitutions
    """
    template = DEGRADED_MESSAGES.get(state, "Unknown state")
    try:
        return template.format(**kwargs)
    except KeyError:
        # Missing format key — return template as-is
        return template


# =============================================================================
# SEVERITY INDICATORS (RL3: Keep essential facts)
# =============================================================================


class SeverityEmoji(str, Enum):
    """Severity emoji prefixes."""
    
    CRITICAL = "🔴"
    WARNING = "🟡"
    INFO = "🟢"


SEVERITY_EMOJI_MAP: dict[str, str] = {
    "CRITICAL": SeverityEmoji.CRITICAL.value,
    "WARNING": SeverityEmoji.WARNING.value,
    "INFO": SeverityEmoji.INFO.value,
}


def severity_prefix(severity: str) -> str:
    """Get emoji prefix for severity."""
    return SEVERITY_EMOJI_MAP.get(severity.upper(), "⚪")


# =============================================================================
# ALERT ONE-LINER FORMATTER (RL3: ≤60 chars)
# =============================================================================


@dataclass
class AlertOneLiner:
    """One-line alert with severity emoji."""
    
    severity: str
    component: str
    event: str
    detail: str = ""
    
    def format(self) -> str:
        """
        Format as one-liner (≤60 chars).
        
        Format: {emoji} {COMPONENT} — {event} [{detail}]
        """
        emoji = severity_prefix(self.severity)
        
        # Base: emoji + component + event
        base = f"{emoji} {self.component} — {self.event}"
        
        # Add detail if fits
        if self.detail:
            full = f"{base}: {self.detail}"
            if len(full) <= 60:
                return full
        
        # Truncate if needed
        if len(base) > 60:
            return base[:57] + "..."
        
        return base


def format_alert_oneliner(
    severity: str,
    component: str,
    event: str,
    detail: str = "",
) -> str:
    """
    Format alert as one-liner.
    
    Args:
        severity: CRITICAL/WARNING/INFO
        component: System component (e.g., "IBKR", "RIVER")
        event: Event type (e.g., "offline", "degraded")
        detail: Optional detail
        
    Returns:
        One-liner string ≤60 chars with emoji prefix
    """
    liner = AlertOneLiner(severity, component, event, detail)
    return liner.format()


# =============================================================================
# HEALTH STATE FORMATTERS
# =============================================================================


def format_health_status(status: str, detail: str = "") -> str:
    """Format health status with emoji."""
    emoji_map = {
        "HEALTHY": "🟢",
        "DEGRADED": "🟡",
        "CRITICAL": "🔴",
        "HALTED": "🛑",
        "UNKNOWN": "⚪",
    }
    emoji = emoji_map.get(status.upper(), "⚪")
    if detail:
        return f"{emoji} {status}: {detail}"
    return f"{emoji} {status}"


def format_staleness(seconds: float) -> str:
    """
    Format staleness in human terms.
    
    Args:
        seconds: Staleness in seconds
        
    Returns:
        Human-readable staleness string
    """
    if seconds < 1:
        return "fresh"
    elif seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes}m ago"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h ago"


# =============================================================================
# RECEIPTS FORMATTING (RL5: Hidden by default)
# =============================================================================


def format_receipts(
    bead_id: str | None = None,
    query_hash: str | None = None,
    provenance: str | None = None,
) -> str:
    """
    Format receipts (provenance) block.
    
    Only used when show_receipts=True.
    
    Args:
        bead_id: Evidence bead ID
        query_hash: Query hash
        provenance: Source provenance
        
    Returns:
        Formatted receipts block
    """
    lines = ["─── RECEIPTS ───"]
    
    if bead_id:
        lines.append(f"  BEAD: {bead_id}")
    if query_hash:
        lines.append(f"  HASH: {query_hash}")
    if provenance:
        lines.append(f"  SRC:  {provenance}")
    
    if len(lines) == 1:
        return ""  # No receipts to show
    
    lines.append("────────────────")
    return "\n".join(lines)


# =============================================================================
# CIRCUIT BREAKER FORMATTER
# =============================================================================


def format_circuit_status(closed: int, total: int) -> str:
    """
    Format circuit breaker status without fractions.
    
    RL1: No "X/Y" patterns in default output.
    
    Args:
        closed: Number of closed circuits
        total: Total circuits
        
    Returns:
        Human-readable status
    """
    if closed == total:
        return "All circuits closed"
    elif closed == 0:
        return "All circuits OPEN"
    else:
        open_count = total - closed
        return f"{open_count} circuit(s) OPEN"


# =============================================================================
# MODULE EXPORTS
# =============================================================================


__all__ = [
    # Gate mappings
    "GATE_PHRASES",
    "PHRASE_TO_GATE",
    "gates_to_phrases",
    "format_gate_facts",
    # Degraded states
    "DegradedState",
    "DEGRADED_MESSAGES",
    "get_degraded_message",
    # Severity
    "SeverityEmoji",
    "severity_prefix",
    # Alert formatting
    "AlertOneLiner",
    "format_alert_oneliner",
    # Health formatting
    "format_health_status",
    "format_staleness",
    # Receipts
    "format_receipts",
    # Circuit breakers
    "format_circuit_status",
]
