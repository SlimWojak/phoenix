"""
Narrator Renderer — S40 Track D
===============================

Jinja2-based template rendering with strict mode.
Undefined variables raise, not silent.

INVARIANT: INV-NARRATOR-3: Undefined → error, not empty
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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
    TemplateRegistry,
    get_template_registry,
    validate_template_content,
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

    def render(self, template_name: str, data: dict[str, Any]) -> str:
        """
        Render a template with data.

        INV-NARRATOR-3: Undefined variables raise UndefinedVariableError.

        Args:
            template_name: Name of template (without .jinja2)
            data: Data dictionary for template

        Returns:
            Rendered string

        Raises:
            UndefinedVariableError: If template uses undefined variable
            TemplateRenderError: If rendering fails
        """
        template_file = f"{template_name}.jinja2"

        try:
            template = self._env.get_template(template_file)

            # Validate template content if requested
            if self.validate_on_load:
                source = template.module.__loader__.get_source(
                    self._env, template_file
                )[0]
                violations = validate_template_content(source)
                if violations:
                    raise TemplateValidationError(template_name, violations)

            return template.render(**data)

        except UndefinedError as e:
            # INV-NARRATOR-3: Convert to our exception
            raise UndefinedVariableError(template_name, str(e))
        except TemplateValidationError:
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

    def render_trade(self, trade_event: dict[str, Any]) -> str:
        """
        Render trade event notification.

        Args:
            trade_event: Trade event data

        Returns:
            Formatted trade notification
        """
        return self.render("trade", trade_event)

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
            }
        else:
            data = alert

        return self.render("alert", data)

    def render_string(self, template_str: str, data: dict[str, Any]) -> str:
        """
        Render a template from string.

        Useful for testing or dynamic templates.

        Args:
            template_str: Template content as string
            data: Data dictionary

        Returns:
            Rendered string
        """
        # Validate content first
        violations = validate_template_content(template_str)
        if violations:
            raise TemplateValidationError("inline", violations)

        try:
            template = self._env.from_string(template_str)
            return template.render(**data)
        except UndefinedError as e:
            raise UndefinedVariableError("inline", str(e))

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
