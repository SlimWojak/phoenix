"""
Narrator Renderer — S40 Track D / S41 Phase 2D
==============================================

Jinja2-based template rendering with strict mode.
Undefined variables raise, not silent.

ALL output goes through narrator_emit() chokepoint which:
1. Canonicalizes content (NFKC, whitespace, zero-width strip)
2. Validates with ContentClassifier
3. Verifies FACTS_ONLY banner present
4. Raises ConstitutionalViolation on heresy

INVARIANTS:
  INV-NARRATOR-1: No recommendation, suggest, should
  INV-NARRATOR-2: FACTS_ONLY banner always present
  INV-NARRATOR-3: Undefined → error, not empty
  INV-SLM-NARRATOR-GATE: All output validated by classifier

Date: 2026-01-30
Sprint: S41 Phase 2D
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    StrictUndefined,
    TemplateError,
    UndefinedError,
    select_autoescape,
)

from .data_sources import DataSources, AlertData
from .templates import (
    get_template_registry,
    validate_template_content,
    validate_facts_banner,
    MANDATORY_FACTS_BANNER,
)


# =============================================================================
# EXCEPTIONS
# =============================================================================


class TemplateRenderError(Exception):
    """Base exception for template rendering errors."""

    def __init__(self, template_name: str, message: str):
        self.template_name = template_name
        self.message = message
        super().__init__(f"Template '{template_name}': {message}")


class UndefinedVariableError(TemplateRenderError):
    """
    Raised when template uses undefined variable.

    INV-NARRATOR-3: Undefined → error, not empty string.
    """

    def __init__(self, template_name: str, variable: str):
        self.variable = variable
        super().__init__(template_name, f"Undefined variable: {variable}")


class TemplateValidationError(TemplateRenderError):
    """Raised when template contains forbidden content."""

    def __init__(self, template_name: str, violations: list[str]):
        self.violations = violations
        super().__init__(
            template_name,
            f"Template contains forbidden content: {', '.join(violations)}",
        )


class NarratorHeresyError(Exception):
    """
    Raised when narrator output contains heresy (constitutional violation).
    
    INV-SLM-NARRATOR-GATE: Heresy → hard fail.
    
    Minimal payload per GPT PATCH 3: No verbose errors (teaches attackers).
    """
    
    def __init__(self, category: str, matched_rule: str | None = None):
        self.category = category
        self.matched_rule = matched_rule
        # Minimal message - no details about what was matched
        super().__init__(f"HERESY:{category}")


# =============================================================================
# CONTENT CANONICALIZATION (GPT PATCH 2)
# =============================================================================


# Zero-width characters to strip
ZERO_WIDTH_CHARS = [
    '\u200b',  # Zero-width space
    '\u200c',  # Zero-width non-joiner
    '\u200d',  # Zero-width joiner
    '\ufeff',  # Zero-width no-break space (BOM)
    '\u2060',  # Word joiner
    '\u180e',  # Mongolian vowel separator
]

ZERO_WIDTH_PATTERN = re.compile('[' + ''.join(ZERO_WIDTH_CHARS) + ']')


def canonicalize_content(content: str) -> str:
    """
    Canonicalize content for classification.
    
    GPT PATCH 2 - Preprocessing before classification:
    - NFKC normalization (converts homoglyphs)
    - Collapse whitespace
    - Strip zero-width characters
    
    Args:
        content: Raw content
        
    Returns:
        Canonicalized content (for scanning, not emitting)
    """
    # NFKC normalization - converts homoglyphs to ASCII equivalents
    # e.g., 'ѕcore' (Cyrillic s) → 'score'
    normalized = unicodedata.normalize('NFKC', content)
    
    # Strip zero-width characters
    normalized = ZERO_WIDTH_PATTERN.sub('', normalized)
    
    # Collapse multiple whitespace (but preserve single newlines)
    # Replace \r\n with \n first
    normalized = normalized.replace('\r\n', '\n')
    # Collapse multiple spaces/tabs
    normalized = re.sub(r'[ \t]+', ' ', normalized)
    # Collapse multiple newlines
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    
    return normalized.strip()


# =============================================================================
# NARRATOR EMIT CHOKEPOINT (GPT PATCH 1)
# =============================================================================


# Lazy import to avoid circular dependency
_classifier = None


def get_classifier():
    """Get ContentClassifier instance (lazy load)."""
    global _classifier
    if _classifier is None:
        from governance.slm_boundary import ContentClassifier
        _classifier = ContentClassifier()
    return _classifier


def narrator_emit(content: str, skip_validation: bool = False) -> str:
    """
    Single chokepoint for ALL narrator output.
    
    GPT PATCH 1: One function performs final emission.
    All render_* functions MUST route through this chokepoint.
    
    Process:
    1. Canonicalize content for scanning
    2. Check banner present (GPT PATCH 4)
    3. Run ContentClassifier
    4. BANNED → raise NarratorHeresyError (GPT PATCH 3)
    5. Return ORIGINAL content (not canonicalized)
    
    Args:
        content: Rendered template output
        skip_validation: If True, skip classifier (for testing only)
        
    Returns:
        Original content if valid
        
    Raises:
        NarratorHeresyError: If content contains heresy
    """
    if skip_validation:
        return content
    
    # Canonicalize for scanning
    canonicalized = canonicalize_content(content)
    
    # GPT PATCH 4: Banner post-render check
    if MANDATORY_FACTS_BANNER not in canonicalized:
        raise NarratorHeresyError(category="BANNER_MISSING")
    
    # Run classifier
    classifier = get_classifier()
    from governance.slm_boundary import SLMClassification
    
    result = classifier.classify(canonicalized)
    
    if result.classification == SLMClassification.BANNED:
        # GPT PATCH 3: Minimal payload
        category = result.reason_code.value if result.reason_code else "UNKNOWN"
        # Only include rule ID, not the matched content (teaches attackers)
        matched_rule = None
        if result.violation_details:
            matched_rule = result.violation_details[0].get("reason")
        raise NarratorHeresyError(category=category, matched_rule=matched_rule)
    
    # Return ORIGINAL (preserve formatting, just validated on canonicalized)
    return content


# =============================================================================
# RENDERER
# =============================================================================


class NarratorRenderer:
    """
    Renders narrator templates with strict mode.

    Usage:
        renderer = NarratorRenderer(template_dir=Path("narrator/templates"))
        output = renderer.render_briefing()

    INVARIANTS:
      INV-NARRATOR-1: Templates validated for synthesis words
      INV-NARRATOR-3: Undefined variables raise errors
    """

    def __init__(
        self,
        template_dir: Path | None = None,
        data_sources: DataSources | None = None,
        validate_on_load: bool = True,
    ):
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.data_sources = data_sources or DataSources()
        self.validate_on_load = validate_on_load
        self.registry = get_template_registry()

        # Initialize Jinja2 environment with strict undefined
        # INV-NARRATOR-3: StrictUndefined raises on missing variables
        self._env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            undefined=StrictUndefined,
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._env.filters["format_pnl"] = self._format_pnl
        self._env.filters["format_gates"] = self._format_gates
        self._env.filters["format_staleness"] = self._format_staleness
        
        # S41 Phase 2E: Surface polish filters
        self._env.filters["gate_facts"] = self._format_gate_facts
        self._env.filters["circuit_status"] = self._format_circuit_status
        self._env.filters["health_emoji"] = self._health_emoji

    def render(
        self,
        template_name: str,
        data: dict[str, Any],
        emit: bool = True,
    ) -> str:
        """
        Render a template with data.

        INV-NARRATOR-3: Undefined variables raise UndefinedVariableError.
        INV-SLM-NARRATOR-GATE: All output validated by classifier.

        Args:
            template_name: Name of template (without .jinja2)
            data: Data dictionary for template
            emit: If True, validate through narrator_emit() chokepoint

        Returns:
            Rendered and validated string

        Raises:
            UndefinedVariableError: If template uses undefined variable
            TemplateRenderError: If rendering fails
            NarratorHeresyError: If output contains heresy
        """
        template_file = f"{template_name}.jinja2"

        try:
            template = self._env.get_template(template_file)

            # Validate template content if requested
            if self.validate_on_load:
                source, _, _ = self._env.loader.get_source(
                    self._env, template_file
                )
                violations = validate_template_content(source)
                if violations:
                    raise TemplateValidationError(template_name, violations)

            rendered = template.render(**data)
            
            # Route through chokepoint (GPT PATCH 1)
            if emit:
                return narrator_emit(rendered)
            return rendered

        except UndefinedError as e:
            # INV-NARRATOR-3: Convert to our exception
            raise UndefinedVariableError(template_name, str(e))
        except TemplateValidationError:
            raise
        except NarratorHeresyError:
            raise
        except TemplateError as e:
            raise TemplateRenderError(template_name, str(e))

    def render_briefing(self) -> str:
        """
        Render morning briefing with all data sources.

        Returns:
            Formatted briefing string
        """
        data = self.data_sources.get_all()
        return self.render("briefing", data)

    def render_health(self) -> str:
        """
        Render health check snapshot.

        Returns:
            Formatted health string
        """
        data = self.data_sources.get_all()
        return self.render("health", data)

    def render_trade(
        self,
        trade_event: dict[str, Any],
        show_receipts: bool = False,
    ) -> str:
        """
        Render trade event notification.

        Args:
            trade_event: Trade event data
            show_receipts: If True, include bead_id and provenance

        Returns:
            Formatted trade notification
        """
        # RL5: Receipts hidden by default
        data = {**trade_event, "show_receipts": show_receipts}
        return self.render("trade", data)

    def render_alert(self, alert: AlertData | dict[str, Any]) -> str:
        """
        Render critical system alert.

        Args:
            alert: Alert data (AlertData or dict)

        Returns:
            Formatted alert string
        """
        if isinstance(alert, AlertData):
            data = {
                "severity": alert.severity,
                "component": alert.component,
                "event": alert.event,
                "message": alert.message,
                "action_taken": alert.action_taken,
                "timestamp": alert.timestamp,
                # Optional fields - provide None to satisfy StrictUndefined
                "degradation_level": getattr(alert, "degradation_level", None),
            }
        else:
            # Ensure optional fields have defaults
            data = {**alert}
            if "degradation_level" not in data:
                data["degradation_level"] = None

        return self.render("alert", data)

    def render_string(
        self,
        template_str: str,
        data: dict[str, Any],
        emit: bool = True,
    ) -> str:
        """
        Render a template from string.

        Useful for testing or dynamic templates.

        Args:
            template_str: Template content as string
            data: Data dictionary
            emit: If True, validate through narrator_emit() chokepoint

        Returns:
            Rendered and validated string
            
        Raises:
            NarratorHeresyError: If output contains heresy
        """
        # Validate content first
        violations = validate_template_content(template_str)
        if violations:
            raise TemplateValidationError("inline", violations)

        try:
            template = self._env.from_string(template_str)
            rendered = template.render(**data)
            
            # Route through chokepoint (GPT PATCH 1)
            if emit:
                return narrator_emit(rendered)
            return rendered
        except UndefinedError as e:
            raise UndefinedVariableError("inline", str(e))
        except NarratorHeresyError:
            raise

    # -------------------------------------------------------------------------
    # CUSTOM FILTERS
    # -------------------------------------------------------------------------

    @staticmethod
    def _format_pnl(value: float) -> str:
        """Format P&L with sign and color hint."""
        if value >= 0:
            return f"+${value:,.2f}"
        else:
            return f"-${abs(value):,.2f}"

    @staticmethod
    def _format_gates(gates: list[int]) -> str:
        """Format gates passed list."""
        if not gates:
            return "none"
        return f"[{','.join(str(g) for g in gates)}]"

    @staticmethod
    def _format_staleness(seconds: float) -> str:
        """Format staleness duration."""
        if seconds < 1:
            return "fresh"
        elif seconds < 60:
            return f"{seconds:.1f}s ago"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m ago"
        else:
            return f"{seconds / 3600:.1f}h ago"

    # -------------------------------------------------------------------------
    # S41 PHASE 2E: SURFACE POLISH FILTERS
    # -------------------------------------------------------------------------

    @staticmethod
    def _format_gate_facts(gate_ids: list[int]) -> str:
        """
        Format gate IDs as human-readable facts.
        
        RL2: 1:1 deterministic mapping from gate to phrase.
        """
        from .surface import format_gate_facts
        return format_gate_facts(gate_ids)

    @staticmethod
    def _format_circuit_status(closed: int, total: int) -> str:
        """
        Format circuit breaker status without fractions.
        
        RL1: No "X/Y" patterns in default output.
        """
        from .surface import format_circuit_status
        return format_circuit_status(closed, total)

    @staticmethod
    def _health_emoji(status: str) -> str:
        """Get health status emoji."""
        emoji_map = {
            "HEALTHY": "🟢",
            "DEGRADED": "🟡",
            "CRITICAL": "🔴",
            "HALTED": "🛑",
            "UNKNOWN": "⚪",
            "RUNNING": "🟢",
            "STOPPED": "🔴",
        }
        return emoji_map.get(status.upper(), "⚪")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_renderer(
    template_dir: Path | None = None,
    data_sources: DataSources | None = None,
) -> NarratorRenderer:
    """
    Create a narrator renderer.

    Args:
        template_dir: Path to templates directory
        data_sources: Data sources instance

    Returns:
        Configured NarratorRenderer
    """
    return NarratorRenderer(
        template_dir=template_dir,
        data_sources=data_sources,
    )
