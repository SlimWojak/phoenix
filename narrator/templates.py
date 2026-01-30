"""
Template Registry — S40 Track D
===============================

Template definitions and validation.
No synthesis allowed — facts only.

INVARIANT: INV-NARRATOR-1: No recommend, suggest, should
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


# =============================================================================
# FORBIDDEN PATTERNS (INV-NARRATOR-1)
# =============================================================================


# Words that indicate synthesis/recommendation (HERESY)
FORBIDDEN_WORDS = [
    # Recommendation language
    "recommend",
    "suggests",
    "suggest",
    "should",
    "advise",
    "consider",
    "might want",
    "you could",
    "probably",
    "likely",
    "unlikely",
    "best to",
    "worst to",
    "optimal",
    "suboptimal",
    "better",
    "worse",
    "prefer",
    "avoid",
    # Opinion/judgment language (GPT tightening)
    "best",
    "worst",
    "strong",
    "weak",
    "safe",
    "unsafe",
    "good",
    "bad",
    # Opinion disguised as warning
    "warning:",
    "caution:",  # Unless from system
]

# Mandatory banner for all templates (GPT TIGHTENING_3)
MANDATORY_FACTS_BANNER = "FACTS_ONLY — NO INTERPRETATION"

# Regex patterns for forbidden content
# Create patterns - use word boundary at start only to catch word stems
FORBIDDEN_PATTERNS = []
for word in FORBIDDEN_WORDS:
    # For multi-word phrases, use flexible spacing
    pattern_str = r"\b" + word.replace(" ", r"\s+")
    # Single words: match word and common suffixes (s, ed, ing)
    if " " not in word:
        pattern_str += r"(?:s|ed|ing)?\b"
    FORBIDDEN_PATTERNS.append(re.compile(pattern_str, re.IGNORECASE))


def validate_template_content(content: str) -> list[str]:
    """
    Validate template contains no synthesis language.

    INV-NARRATOR-1: Facts only, no recommendations.

    Args:
        content: Template content to validate

    Returns:
        List of violations found (empty if clean)
    """
    violations = []

    for pattern in FORBIDDEN_PATTERNS:
        matches = pattern.findall(content)
        if matches:
            for match in matches:
                violations.append(f"Forbidden word: '{match}'")

    return violations


def validate_facts_banner(rendered_output: str) -> list[str]:
    """
    Validate rendered output contains mandatory facts banner.

    GPT TIGHTENING_3: All outputs must have disclaimer.

    Args:
        rendered_output: Rendered template output

    Returns:
        List of violations found (empty if banner present)
    """
    violations = []

    if MANDATORY_FACTS_BANNER not in rendered_output:
        violations.append(
            f"Missing mandatory banner: '{MANDATORY_FACTS_BANNER}'"
        )

    return violations


# =============================================================================
# TEMPLATE DEFINITIONS
# =============================================================================


@dataclass
class TemplateDefinition:
    """Definition of a narrator template."""

    name: str
    purpose: str
    required_fields: list[str]
    optional_fields: list[str] = field(default_factory=list)
    dialect: str = "warboar"
    immediate: bool = False  # True for alerts


# Template registry
TEMPLATES = {
    "briefing": TemplateDefinition(
        name="briefing",
        purpose="Morning state summary",
        required_fields=[
            "orientation.health_status",
            "orientation.mode",
            "orientation.kill_flags",
            "trades.open_positions",
            "trades.daily_pnl",
            "hunt.pending_hypotheses",
        ],
        optional_fields=[
            "cso.gates_per_pair",
            "tests.passed",
            "tests.failed",
        ],
    ),
    "health": TemplateDefinition(
        name="health",
        purpose="System health snapshot",
        required_fields=[
            "river.health_status",
            "river.staleness_seconds",
            "supervisor.state",
            "supervisor.ibkr_connected",
            "supervisor.heartbeat_ok",
            "supervisor.circuit_breakers_closed",
            "supervisor.circuit_breakers_total",
        ],
        optional_fields=[
            "tests.collected",
            "tests.passed",
        ],
    ),
    "trade": TemplateDefinition(
        name="trade",
        purpose="Trade event notification",
        required_fields=[
            "action",
            "pair",
            "direction",
            "entry",
            "stop",
            "target",
            "risk_pct",
            "gates_passed",
            "evidence_bead",
        ],
        optional_fields=[],
    ),
    "alert": TemplateDefinition(
        name="alert",
        purpose="Critical system alert",
        required_fields=[
            "severity",
            "component",
            "event",
            "action_taken",
        ],
        optional_fields=[
            "message",
            "degradation_level",
        ],
        immediate=True,
    ),
}


class TemplateRegistry:
    """
    Registry for narrator templates.

    Validates templates on registration.
    """

    def __init__(self):
        self._templates: dict[str, TemplateDefinition] = TEMPLATES.copy()
        self._validators: list[Callable[[str], list[str]]] = [
            validate_template_content
        ]

    def get(self, name: str) -> TemplateDefinition | None:
        """Get template definition by name."""
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        """List all template names."""
        return list(self._templates.keys())

    def register(self, template: TemplateDefinition) -> None:
        """Register a new template."""
        self._templates[template.name] = template

    def add_validator(self, validator: Callable[[str], list[str]]) -> None:
        """Add a content validator."""
        self._validators.append(validator)

    def validate_content(self, content: str) -> list[str]:
        """
        Run all validators on template content.

        Returns list of violations.
        """
        all_violations = []
        for validator in self._validators:
            all_violations.extend(validator(content))
        return all_violations

    def get_required_fields(self, name: str) -> list[str]:
        """Get required fields for a template."""
        template = self.get(name)
        if template:
            return template.required_fields
        return []


# Global registry
_registry = TemplateRegistry()


def get_template_registry() -> TemplateRegistry:
    """Get the global template registry."""
    return _registry
