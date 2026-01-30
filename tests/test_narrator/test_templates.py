"""
Template Tests — S40 Track D
============================

Proves INV-NARRATOR-1: Facts only, no synthesis.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from narrator.templates import (
    FORBIDDEN_WORDS,
    FORBIDDEN_PATTERNS,
    MANDATORY_FACTS_BANNER,
    validate_template_content,
    validate_facts_banner,
    TemplateRegistry,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def registry() -> TemplateRegistry:
    """Create fresh template registry."""
    return TemplateRegistry()


@pytest.fixture
def template_dir() -> Path:
    """Get templates directory."""
    return Path(__file__).parent.parent.parent / "narrator" / "templates"


# =============================================================================
# INV-NARRATOR-1: NO SYNTHESIS
# =============================================================================


class TestNoSynthesis:
    """Prove INV-NARRATOR-1: Templates contain facts only, no synthesis."""

    def test_catches_recommend(self):
        """'recommend' is forbidden."""
        content = "We recommend taking this trade."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        assert any("recommend" in v.lower() for v in violations)
        print("✓ 'recommend' caught")

    def test_catches_suggest(self):
        """'suggest' is forbidden."""
        content = "This suggests a bullish bias."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ 'suggest' caught")

    def test_catches_should(self):
        """'should' is forbidden."""
        content = "You should close this position."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ 'should' caught")

    def test_catches_advise(self):
        """'advise' is forbidden."""
        content = "We advise caution here."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ 'advise' caught")

    def test_catches_probably(self):
        """'probably' is forbidden."""
        content = "This will probably work."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ 'probably' caught")

    def test_catches_likely(self):
        """'likely' is forbidden."""
        content = "This is likely to succeed."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ 'likely' caught")

    def test_catches_better_worse(self):
        """'better'/'worse' are forbidden."""
        content1 = "This is better than the other."
        content2 = "This is worse than expected."

        v1 = validate_template_content(content1)
        v2 = validate_template_content(content2)

        assert len(v1) >= 1
        assert len(v2) >= 1
        print("✓ 'better'/'worse' caught")

    def test_clean_content_passes(self):
        """Factual content passes validation."""
        content = """
        SYSTEM: HEALTHY
        MODE: PAPER
        POSITIONS: 0
        P&L: $0.00
        """
        violations = validate_template_content(content)

        assert len(violations) == 0
        print("✓ Factual content passes")


# =============================================================================
# TEMPLATE FILES VALIDATION
# =============================================================================


class TestTemplateFiles:
    """Validate actual template files."""

    def test_briefing_template_clean(self, template_dir: Path):
        """briefing.jinja2 contains no forbidden content."""
        template_path = template_dir / "briefing.jinja2"
        if template_path.exists():
            content = template_path.read_text()
            violations = validate_template_content(content)

            assert len(violations) == 0, f"Violations: {violations}"
            print("✓ briefing.jinja2 is clean")

    def test_health_template_clean(self, template_dir: Path):
        """health.jinja2 contains no forbidden content."""
        template_path = template_dir / "health.jinja2"
        if template_path.exists():
            content = template_path.read_text()
            violations = validate_template_content(content)

            assert len(violations) == 0, f"Violations: {violations}"
            print("✓ health.jinja2 is clean")

    def test_trade_template_clean(self, template_dir: Path):
        """trade.jinja2 contains no forbidden content."""
        template_path = template_dir / "trade.jinja2"
        if template_path.exists():
            content = template_path.read_text()
            violations = validate_template_content(content)

            assert len(violations) == 0, f"Violations: {violations}"
            print("✓ trade.jinja2 is clean")

    def test_alert_template_clean(self, template_dir: Path):
        """alert.jinja2 contains no forbidden content."""
        template_path = template_dir / "alert.jinja2"
        if template_path.exists():
            content = template_path.read_text()
            violations = validate_template_content(content)

            assert len(violations) == 0, f"Violations: {violations}"
            print("✓ alert.jinja2 is clean")


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestTemplateRegistry:
    """Test template registry."""

    def test_default_templates_registered(self, registry: TemplateRegistry):
        """Default templates are registered."""
        templates = registry.list_templates()

        assert "briefing" in templates
        assert "health" in templates
        assert "trade" in templates
        assert "alert" in templates
        print(f"✓ {len(templates)} templates registered")

    def test_get_template(self, registry: TemplateRegistry):
        """Can get template definition."""
        template = registry.get("briefing")

        assert template is not None
        assert template.name == "briefing"
        assert len(template.required_fields) > 0
        print("✓ Get template works")

    def test_required_fields_defined(self, registry: TemplateRegistry):
        """Templates have required fields defined."""
        for name in registry.list_templates():
            template = registry.get(name)
            assert template is not None
            # All templates should have at least one required field
            assert len(template.required_fields) >= 1

        print("✓ All templates have required fields")


# =============================================================================
# FORBIDDEN PATTERNS
# =============================================================================


class TestForbiddenPatterns:
    """Test forbidden pattern definitions."""

    def test_forbidden_words_list(self):
        """Forbidden words list is populated."""
        assert len(FORBIDDEN_WORDS) >= 10
        print(f"✓ {len(FORBIDDEN_WORDS)} forbidden words defined")

    def test_patterns_compiled(self):
        """Patterns are compiled regex."""
        assert len(FORBIDDEN_PATTERNS) == len(FORBIDDEN_WORDS)
        for pattern in FORBIDDEN_PATTERNS:
            assert hasattr(pattern, "search")
        print("✓ Patterns compiled")

    def test_case_insensitive(self):
        """Patterns are case insensitive."""
        # Should catch RECOMMEND, Recommend, recommend
        content = "RECOMMEND this action"
        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ Case insensitive matching")


# =============================================================================
# CHAOS: OBFUSCATION ATTEMPTS
# =============================================================================


class TestObfuscationChaos:
    """Chaos tests for obfuscation attempts."""

    def test_catches_multiple_forbidden(self):
        """Catches multiple forbidden words."""
        content = "You should probably recommend this better option."

        violations = validate_template_content(content)

        assert len(violations) >= 4  # should, probably, recommend, better
        print(f"✓ Caught {len(violations)} violations")

    def test_catches_in_multiline(self):
        """Catches forbidden in multiline content."""
        content = """
        Line 1: Clean content
        Line 2: This is fine
        Line 3: You should do this
        Line 4: More clean content
        """

        violations = validate_template_content(content)

        assert len(violations) >= 1
        print("✓ Caught in multiline")


# =============================================================================
# GPT TIGHTENINGS (Track E)
# =============================================================================


class TestGPTTightenings:
    """Tests for GPT-recommended tightenings."""

    def test_catches_best(self):
        """'best' is forbidden (GPT tightening)."""
        content = "This is the best strategy."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        assert any("best" in v.lower() for v in violations)
        print("✓ 'best' caught (GPT tightening)")

    def test_catches_worst(self):
        """'worst' is forbidden (GPT tightening)."""
        content = "This is the worst outcome."
        violations = validate_template_content(content)

        assert len(violations) >= 1
        assert any("worst" in v.lower() for v in violations)
        print("✓ 'worst' caught (GPT tightening)")

    def test_catches_strong_weak(self):
        """'strong'/'weak' are forbidden (GPT tightening)."""
        content1 = "This is a strong signal."
        content2 = "This is a weak pattern."

        v1 = validate_template_content(content1)
        v2 = validate_template_content(content2)

        assert len(v1) >= 1
        assert len(v2) >= 1
        print("✓ 'strong'/'weak' caught (GPT tightening)")

    def test_catches_safe_unsafe(self):
        """'safe'/'unsafe' are forbidden (GPT tightening)."""
        content1 = "This is a safe trade."
        content2 = "This is unsafe to execute."

        v1 = validate_template_content(content1)
        v2 = validate_template_content(content2)

        assert len(v1) >= 1
        assert len(v2) >= 1
        print("✓ 'safe'/'unsafe' caught (GPT tightening)")

    def test_catches_good_bad(self):
        """'good'/'bad' are forbidden (GPT tightening)."""
        content1 = "This is a good setup."
        content2 = "This is a bad idea."

        v1 = validate_template_content(content1)
        v2 = validate_template_content(content2)

        assert len(v1) >= 1
        assert len(v2) >= 1
        print("✓ 'good'/'bad' caught (GPT tightening)")

    def test_facts_banner_present(self):
        """FACTS_ONLY banner is validated."""
        output_with_banner = f"""
        OINK OINK!
        {MANDATORY_FACTS_BANNER}
        HEALTH: OK
        """
        output_without_banner = """
        OINK OINK!
        HEALTH: OK
        """

        v1 = validate_facts_banner(output_with_banner)
        v2 = validate_facts_banner(output_without_banner)

        assert len(v1) == 0, "Banner present should pass"
        assert len(v2) >= 1, "Missing banner should fail"
        print("✓ FACTS_ONLY banner validation works")

    def test_all_templates_have_banner(self, template_dir: Path):
        """All templates have FACTS_ONLY banner."""
        template_files = ["briefing.jinja2", "health.jinja2", "trade.jinja2", "alert.jinja2"]

        for template_name in template_files:
            template_path = template_dir / template_name
            if template_path.exists():
                content = template_path.read_text()
                assert MANDATORY_FACTS_BANNER in content, f"{template_name} missing banner"

        print("✓ All templates have FACTS_ONLY banner")

    def test_cso_no_count_proxy(self, template_dir: Path):
        """CSO output shows gates list only, no (X/Y) count proxy."""
        template_path = template_dir / "briefing.jinja2"
        if template_path.exists():
            content = template_path.read_text()
            # Should NOT have (X/Y) pattern after gates_passed
            import re
            # Check for count proxy patterns like (3/7), (5/7)
            count_pattern = re.compile(r'gates_passed.*\(\s*\{\{.*\}\}\s*/\s*\d+\s*\)')
            matches = count_pattern.search(content)
            assert matches is None, "CSO output should not have (X/Y) count proxy"

        print("✓ CSO output has no count proxy")
