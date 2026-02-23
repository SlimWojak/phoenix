"""
Alert Integration — S36 Track E
===============================

Alerts fire on EXPLICIT gate combinations only.
NO quality language. NO count language.

INVARIANTS:
  - INV-HARNESS-3: Alerts on gate combinations, not quality
  - INV-NO-UNSOLICITED: System never proposes
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

# =============================================================================
# CONSTANTS
# =============================================================================

CSO_ROOT = Path(__file__).parent
ALERT_RULES_PATH = CSO_ROOT / "alert_rules.yaml"

# Rate limits
MAX_PER_PAIR_PER_MINUTE = 3
MAX_GLOBAL_PER_MINUTE = 10


class AlertChannel(Enum):
    """Alert notification channel."""

    TELEGRAM = "telegram"
    LOG = "log"
    BEAD = "bead"


# =============================================================================
# FORBIDDEN PHRASES
# =============================================================================

FORBIDDEN_IN_ALERTS = frozenset(
    [
        # Count language
        "gates_passed_count",
        "/total",
        "out of",
        "ratio",
        "percentage",
        "%",
        # Quality language
        "quality",
        "grade",
        "score",
        "confidence",
        "best",
        "top",
        # Action language
        "looks ready",
        "setup forming",
        "opportunity",
        "consider",
        "potential",
        "recommend",
        "suggested",
        # Readiness language
        "ready",
        "setup",
    ]
)

FORBIDDEN_NAME_WORDS = frozenset(
    [
        "ready",
        "setup",
        "opportunity",
        "best",
        "top",
        "quality",
    ]
)


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class AlertRule:
    """
    Alert rule definition.

    FORBIDDEN:
      - drawer_minimum
      - quality_threshold
      - confidence_threshold
    """

    id: str
    name: str  # Must use STATE_* prefix
    gates_required: list[str]  # Minimum 1
    gates_forbidden: list[str] = field(default_factory=list)
    channel: AlertChannel = AlertChannel.LOG
    template: str = ""


@dataclass
class AlertValidationError:
    """Alert validation error."""

    field: str
    message: str
    code: str


@dataclass
class AlertValidationResult:
    """Result of alert validation."""

    valid: bool
    errors: list[AlertValidationError] = field(default_factory=list)


@dataclass
class Alert:
    """Fired alert."""

    rule_id: str
    pair: str
    gates_passed: list[str]
    gates_failed: list[str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    suppressed: bool = False
    suppression_reason: str = ""


# =============================================================================
# ALERT LINTER
# =============================================================================


class AlertLinter:
    """
    Lints alert rules and templates for forbidden language.

    Extends causal ban patterns with alert-specific bans.
    """

    @staticmethod
    def lint_template(template: str) -> AlertValidationResult:
        """
        Lint an alert template.

        Args:
            template: Template string

        Returns:
            AlertValidationResult
        """
        errors: list[AlertValidationError] = []
        template_lower = template.lower()

        for phrase in FORBIDDEN_IN_ALERTS:
            if phrase.lower() in template_lower:
                errors.append(
                    AlertValidationError(
                        field="template",
                        message=f"Forbidden phrase '{phrase}' in template",
                        code="FORBIDDEN_PHRASE",
                    )
                )

        return AlertValidationResult(valid=len(errors) == 0, errors=errors)

    @staticmethod
    def lint_rule_name(name: str) -> AlertValidationResult:
        """
        Lint an alert rule name.

        Must use STATE_* prefix, no readiness words.

        Args:
            name: Rule name

        Returns:
            AlertValidationResult
        """
        errors: list[AlertValidationError] = []

        # Must have STATE_ prefix
        if not name.startswith("STATE_"):
            errors.append(
                AlertValidationError(
                    field="name",
                    message="Alert name must use STATE_* prefix",
                    code="MISSING_STATE_PREFIX",
                )
            )

        # Check for forbidden words
        name_lower = name.lower()
        for word in FORBIDDEN_NAME_WORDS:
            if word in name_lower:
                errors.append(
                    AlertValidationError(
                        field="name",
                        message=f"Forbidden word '{word}' in alert name",
                        code="FORBIDDEN_NAME_WORD",
                    )
                )

        return AlertValidationResult(valid=len(errors) == 0, errors=errors)


# =============================================================================
# ALERT RULE VALIDATOR
# =============================================================================


class AlertRuleValidator:
    """
    Validates alert rules.

    Ensures no forbidden fields and required fields present.
    """

    FORBIDDEN_FIELDS = frozenset(
        [
            "drawer_minimum",
            "quality_threshold",
            "confidence_threshold",
            "score_threshold",
            "grade_minimum",
        ]
    )

    def validate(self, rule_dict: dict[str, Any]) -> AlertValidationResult:
        """
        Validate an alert rule.

        Args:
            rule_dict: Rule dictionary

        Returns:
            AlertValidationResult
        """
        errors: list[AlertValidationError] = []

        # Check forbidden fields
        for field_name in rule_dict:
            if field_name.lower() in self.FORBIDDEN_FIELDS:
                errors.append(
                    AlertValidationError(
                        field=field_name,
                        message=f"Forbidden field '{field_name}' in alert rule",
                        code="FORBIDDEN_FIELD",
                    )
                )

        # Check trigger structure
        trigger = rule_dict.get("trigger", {})
        if isinstance(trigger, dict):
            for field_name in trigger:
                if field_name.lower() in self.FORBIDDEN_FIELDS:
                    errors.append(
                        AlertValidationError(
                            field=f"trigger.{field_name}",
                            message=f"Forbidden field '{field_name}' in trigger",
                            code="FORBIDDEN_FIELD",
                        )
                    )

        # Check gates_required is not empty
        gates_required = rule_dict.get("gates_required", [])
        if trigger:
            gates_required = trigger.get("gates_required", gates_required)

        if not gates_required:
            errors.append(
                AlertValidationError(
                    field="gates_required",
                    message="gates_required must have at least 1 gate",
                    code="EMPTY_GATES_REQUIRED",
                )
            )

        # Validate name
        name = rule_dict.get("name", "")
        if name:
            name_result = AlertLinter.lint_rule_name(name)
            errors.extend(name_result.errors)

        # Validate template
        template = rule_dict.get("template", "")
        if not template:
            notification = rule_dict.get("notification", {})
            if isinstance(notification, dict):
                template = notification.get("template", "")

        if template:
            template_result = AlertLinter.lint_template(template)
            errors.extend(template_result.errors)

        return AlertValidationResult(valid=len(errors) == 0, errors=errors)


# =============================================================================
# RATE LIMITER
# =============================================================================


class AlertRateLimiter:
    """
    Rate limits alert firing.

    Prevents spam (3/pair/min, 10/global/min).
    """

    def __init__(
        self,
        max_per_pair: int = MAX_PER_PAIR_PER_MINUTE,
        max_global: int = MAX_GLOBAL_PER_MINUTE,
    ) -> None:
        """Initialize rate limiter."""
        self._max_per_pair = max_per_pair
        self._max_global = max_global
        self._pair_counts: dict[str, deque[datetime]] = defaultdict(lambda: deque(maxlen=100))
        self._global_counts: deque[datetime] = deque(maxlen=100)

    def check_and_record(self, pair: str) -> tuple[bool, str]:
        """
        Check if alert can fire, record if yes.

        Args:
            pair: Trading pair

        Returns:
            (allowed, suppression_reason)
        """
        now = datetime.now(UTC)
        one_minute_ago = now - timedelta(minutes=1)

        # Clean old entries
        self._pair_counts[pair] = deque(
            (t for t in self._pair_counts[pair] if t > one_minute_ago),
            maxlen=100,
        )
        self._global_counts = deque(
            (t for t in self._global_counts if t > one_minute_ago),
            maxlen=100,
        )

        # Check pair limit
        if len(self._pair_counts[pair]) >= self._max_per_pair:
            return (False, f"rate_limit_pair:{pair}")

        # Check global limit
        if len(self._global_counts) >= self._max_global:
            return (False, "rate_limit_global")

        # Record
        self._pair_counts[pair].append(now)
        self._global_counts.append(now)

        return (True, "")


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "AlertRule",
    "Alert",
    "AlertChannel",
    "AlertLinter",
    "AlertRuleValidator",
    "AlertRateLimiter",
    "AlertValidationResult",
    "AlertValidationError",
    "FORBIDDEN_IN_ALERTS",
]
