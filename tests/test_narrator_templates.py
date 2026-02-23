"""
Narrator Template Linter — S43 Track D
=====================================

INV-NARRATOR-FACTS-ONLY enforcement.
No forbidden interpretation words in templates.

Forbidden patterns:
- "edge concentrates", "best", "strongest", "weakest"
- "recommend", "should", "suggests", "indicates"
- "likely", "probably"

These words imply interpretation, violating the facts-only principle.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

# =============================================================================
# FORBIDDEN PATTERNS (INV-NARRATOR-FACTS-ONLY)
# =============================================================================

FORBIDDEN_PATTERNS = [
    r"\bedge concentrates\b",
    r"\bbest\b",
    r"\bstrongest\b",
    r"\bweakest\b",
    r"\brecommend\b",
    r"\bshould\b",
    r"\bsuggests?\b",
    r"\bindicates?\b",
    r"\blikely\b",
    r"\bprobably\b",
    r"\boptimal\b",
    r"\bideal\b",
    r"\bpoor\b",
    r"\bworse\b",
    r"\bbetter\b",
]

# Allowed in specific contexts (e.g., template comments, variable names)
ALLOWED_CONTEXTS = [
    r"\{#.*#\}",  # Jinja2 comments
    r"\{\{.*\}\}",  # Jinja2 variables (might contain user data)
]

TEMPLATES_DIR = Path("narrator/templates")


# =============================================================================
# TEST FUNCTIONS
# =============================================================================


def get_template_files() -> list[Path]:
    """Get all Jinja2 template files."""
    if not TEMPLATES_DIR.exists():
        return []
    return list(TEMPLATES_DIR.glob("*.jinja2"))


def strip_allowed_contexts(content: str) -> str:
    """Remove allowed contexts before checking for forbidden words."""
    result = content
    for pattern in ALLOWED_CONTEXTS:
        result = re.sub(pattern, "", result, flags=re.DOTALL)
    return result


@pytest.mark.parametrize("template", get_template_files(), ids=lambda p: p.name)
def test_no_forbidden_words(template: Path) -> None:
    """
    Test that templates don't contain forbidden interpretation words.

    INV-NARRATOR-FACTS-ONLY: Templates emit facts only, no interpretation.
    """
    content = template.read_text()

    # Strip allowed contexts
    checkable_content = strip_allowed_contexts(content)

    for pattern in FORBIDDEN_PATTERNS:
        match = re.search(pattern, checkable_content, re.IGNORECASE)
        if match:
            pytest.fail(
                f"INV-NARRATOR-FACTS-ONLY violation in {template.name}: "
                f"Found forbidden word '{match.group()}'"
            )


def test_templates_exist() -> None:
    """Test that required templates exist."""
    required = [
        "alert.jinja2",
        "briefing.jinja2",
        "health.jinja2",
        "trade.jinja2",
        # S43 additions
        "research_summary.jinja2",
        "hunt_result.jinja2",
        "weekly_review.jinja2",
    ]

    for name in required:
        path = TEMPLATES_DIR / name
        assert path.exists(), f"Missing required template: {name}"


def test_templates_have_facts_banner() -> None:
    """Test that S43 templates include facts banner (INV-NARRATOR-*)."""
    # Only enforce on S43 templates (existing templates may have different patterns)
    s43_templates = [
        "research_summary.jinja2",
        "hunt_result.jinja2",
        "weekly_review.jinja2",
    ]

    for name in s43_templates:
        template = TEMPLATES_DIR / name
        if not template.exists():
            continue

        content = template.read_text()

        # Should reference facts banner or include mandatory banner comment
        has_banner = (
            "facts_banner" in content.lower()
            or "MANDATORY_FACTS_BANNER" in content
            or "Facts only" in content
        )

        assert has_banner, (
            f"Template {template.name} missing facts banner. "
            "Add: {% include 'facts_banner.jinja2' %} or equivalent"
        )


def test_linter_catches_violations() -> None:
    """Meta-test: verify linter actually catches violations."""
    # Test content with known violation
    bad_content = "This is the best approach and you should try it."

    for pattern in FORBIDDEN_PATTERNS[:3]:  # Test first few patterns
        if re.search(pattern, bad_content, re.IGNORECASE):
            return  # Good, linter would catch this

    pytest.fail("Linter regex patterns not working correctly")


# =============================================================================
# TEMPLATE VALIDATION
# =============================================================================


def test_templates_valid_jinja2() -> None:
    """Test that S43 templates are valid Jinja2 syntax."""
    try:
        from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError
    except ImportError:
        pytest.skip("jinja2 not installed")

    if not TEMPLATES_DIR.exists():
        pytest.skip("Templates directory not found")

    # Only validate S43 templates (existing templates may have custom filters)
    s43_templates = [
        "research_summary.jinja2",
        "hunt_result.jinja2",
        "weekly_review.jinja2",
    ]

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

    for name in s43_templates:
        template_path = TEMPLATES_DIR / name
        if not template_path.exists():
            continue
        try:
            # Parse template source directly to check syntax
            # (avoid filter resolution issues from includes)
            content = template_path.read_text()
            env.parse(content)
        except TemplateSyntaxError as e:
            pytest.fail(f"Invalid Jinja2 syntax in {name}: {e}")
