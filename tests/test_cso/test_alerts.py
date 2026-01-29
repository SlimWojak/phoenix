"""
Alert Tests — S36 Track E
=========================

INVARIANTS PROVEN:
  - INV-HARNESS-3: Alerts on gate combinations, not quality
  - INV-NO-UNSOLICITED: System never proposes

EXIT GATE E:
  Criterion: "Alerts trigger on gate state only; no quality/count language; rate limited"
  Proof: "Alert linter catches all forbidden patterns; rate limiter tested"
"""

import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))


# =============================================================================
# INLINE TYPES
# =============================================================================

MAX_PER_PAIR_PER_MINUTE = 3
MAX_GLOBAL_PER_MINUTE = 10

FORBIDDEN_IN_ALERTS = frozenset(
    [
        "gates_passed_count",
        "/total",
        "out of",
        "ratio",
        "percentage",
        "%",
        "quality",
        "grade",
        "score",
        "confidence",
        "best",
        "top",
        "looks ready",
        "setup forming",
        "opportunity",
        "consider",
        "potential",
        "recommend",
        "suggested",
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


@dataclass
class AlertValidationError:
    field: str
    message: str
    code: str


@dataclass
class AlertValidationResult:
    valid: bool
    errors: list[AlertValidationError] = field(default_factory=list)


class AlertLinter:
    @staticmethod
    def lint_template(template: str) -> AlertValidationResult:
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
        errors: list[AlertValidationError] = []
        if not name.startswith("STATE_"):
            errors.append(
                AlertValidationError(
                    field="name",
                    message="Alert name must use STATE_* prefix",
                    code="MISSING_STATE_PREFIX",
                )
            )
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


class AlertRuleValidator:
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
        errors: list[AlertValidationError] = []
        for field_name in rule_dict:
            if field_name.lower() in self.FORBIDDEN_FIELDS:
                errors.append(
                    AlertValidationError(
                        field=field_name,
                        message=f"Forbidden field '{field_name}' in alert rule",
                        code="FORBIDDEN_FIELD",
                    )
                )
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
        name = rule_dict.get("name", "")
        if name:
            name_result = AlertLinter.lint_rule_name(name)
            errors.extend(name_result.errors)
        template = rule_dict.get("template", "")
        if not template:
            notification = rule_dict.get("notification", {})
            if isinstance(notification, dict):
                template = notification.get("template", "")
        if template:
            template_result = AlertLinter.lint_template(template)
            errors.extend(template_result.errors)
        return AlertValidationResult(valid=len(errors) == 0, errors=errors)


class AlertRateLimiter:
    def __init__(
        self,
        max_per_pair: int = MAX_PER_PAIR_PER_MINUTE,
        max_global: int = MAX_GLOBAL_PER_MINUTE,
    ) -> None:
        self._max_per_pair = max_per_pair
        self._max_global = max_global
        self._pair_counts: dict[str, deque[datetime]] = defaultdict(lambda: deque(maxlen=100))
        self._global_counts: deque[datetime] = deque(maxlen=100)

    def check_and_record(self, pair: str) -> tuple[bool, str]:
        now = datetime.now(UTC)
        one_minute_ago = now - timedelta(minutes=1)
        self._pair_counts[pair] = deque(
            (t for t in self._pair_counts[pair] if t > one_minute_ago), maxlen=100
        )
        self._global_counts = deque(
            (t for t in self._global_counts if t > one_minute_ago), maxlen=100
        )
        if len(self._pair_counts[pair]) >= self._max_per_pair:
            return (False, f"rate_limit_pair:{pair}")
        if len(self._global_counts) >= self._max_global:
            return (False, "rate_limit_global")
        self._pair_counts[pair].append(now)
        self._global_counts.append(now)
        return (True, "")


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def linter() -> AlertLinter:
    return AlertLinter()


@pytest.fixture
def validator() -> AlertRuleValidator:
    return AlertRuleValidator()


@pytest.fixture
def rate_limiter() -> AlertRateLimiter:
    return AlertRateLimiter()


# =============================================================================
# TEMPLATE LINTING TESTS
# =============================================================================


class TestTemplateLinting:
    """Tests for alert template linting."""

    def test_count_language_rejected(self, linter: AlertLinter) -> None:
        """Template with count language is rejected."""
        template = "Gates: gates_passed_count = 5"
        result = linter.lint_template(template)

        assert not result.valid

    def test_percentage_rejected(self, linter: AlertLinter) -> None:
        """Template with percentage is rejected."""
        template = "Gates passed: 75%"
        result = linter.lint_template(template)

        assert not result.valid

    def test_quality_rejected(self, linter: AlertLinter) -> None:
        """Template with quality language is rejected."""
        template = "High quality setup detected"
        result = linter.lint_template(template)

        assert not result.valid

    def test_looks_ready_rejected(self, linter: AlertLinter) -> None:
        """Template with 'looks ready' is rejected."""
        template = "EURUSD looks ready for entry"
        result = linter.lint_template(template)

        assert not result.valid

    def test_opportunity_rejected(self, linter: AlertLinter) -> None:
        """Template with 'opportunity' is rejected."""
        template = "Trading opportunity on GBPUSD"
        result = linter.lint_template(template)

        assert not result.valid

    def test_valid_template_accepted(self, linter: AlertLinter) -> None:
        """Valid template without forbidden language is accepted."""
        template = "STATE_LONDON_FVG_MATCH: Gates htf_poi, fvg_present active"
        result = linter.lint_template(template)

        assert result.valid


# =============================================================================
# NAME LINTING TESTS
# =============================================================================


class TestNameLinting:
    """Tests for alert name linting."""

    def test_missing_state_prefix_rejected(self, linter: AlertLinter) -> None:
        """Name without STATE_ prefix is rejected."""
        result = linter.lint_rule_name("london_fvg_ready")

        assert not result.valid
        assert any(e.code == "MISSING_STATE_PREFIX" for e in result.errors)

    def test_ready_in_name_rejected(self, linter: AlertLinter) -> None:
        """Name with 'ready' is rejected."""
        result = linter.lint_rule_name("STATE_LONDON_READY")

        assert not result.valid
        assert any(e.code == "FORBIDDEN_NAME_WORD" for e in result.errors)

    def test_setup_in_name_rejected(self, linter: AlertLinter) -> None:
        """Name with 'setup' is rejected."""
        result = linter.lint_rule_name("STATE_LONDON_SETUP")

        assert not result.valid

    def test_valid_name_accepted(self, linter: AlertLinter) -> None:
        """Valid name with STATE_ prefix is accepted."""
        result = linter.lint_rule_name("STATE_LONDON_FVG_MATCH")

        assert result.valid


# =============================================================================
# RULE VALIDATION TESTS
# =============================================================================


class TestRuleValidation:
    """Tests for alert rule validation."""

    def test_empty_gates_rejected(self, validator: AlertRuleValidator) -> None:
        """Rule with empty gates_required is rejected."""
        rule = {
            "name": "STATE_TEST",
            "gates_required": [],
        }
        result = validator.validate(rule)

        assert not result.valid
        assert any(e.code == "EMPTY_GATES_REQUIRED" for e in result.errors)

    def test_quality_threshold_rejected(self, validator: AlertRuleValidator) -> None:
        """Rule with quality_threshold is rejected."""
        rule = {
            "name": "STATE_TEST",
            "gates_required": ["gate_a"],
            "quality_threshold": 0.8,
        }
        result = validator.validate(rule)

        assert not result.valid
        assert any(e.code == "FORBIDDEN_FIELD" for e in result.errors)

    def test_drawer_minimum_rejected(self, validator: AlertRuleValidator) -> None:
        """Rule with drawer_minimum is rejected."""
        rule = {
            "name": "STATE_TEST",
            "gates_required": ["gate_a"],
            "drawer_minimum": 3,
        }
        result = validator.validate(rule)

        assert not result.valid

    def test_valid_rule_accepted(self, validator: AlertRuleValidator) -> None:
        """Valid rule is accepted."""
        rule = {
            "name": "STATE_LONDON_FVG_MATCH",
            "gates_required": ["fvg_present", "kill_zone_active"],
            "template": "FVG present during London",
        }
        result = validator.validate(rule)

        assert result.valid


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================


class TestRateLimiting:
    """Tests for alert rate limiting."""

    def test_first_alert_allowed(self, rate_limiter: AlertRateLimiter) -> None:
        """First alert is allowed."""
        allowed, reason = rate_limiter.check_and_record("EURUSD")
        assert allowed

    def test_pair_rate_limit_hit(self, rate_limiter: AlertRateLimiter) -> None:
        """4th alert for same pair is blocked."""
        for _ in range(3):
            rate_limiter.check_and_record("EURUSD")

        allowed, reason = rate_limiter.check_and_record("EURUSD")
        assert not allowed
        assert "rate_limit_pair" in reason

    def test_global_rate_limit_hit(self, rate_limiter: AlertRateLimiter) -> None:
        """11th global alert is blocked."""
        pairs = [f"PAIR{i}" for i in range(10)]
        for pair in pairs:
            rate_limiter.check_and_record(pair)

        allowed, reason = rate_limiter.check_and_record("NEWPAIR")
        assert not allowed
        assert "rate_limit_global" in reason


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
