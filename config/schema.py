"""
Phoenix Configuration Schema — S43 Track C
==========================================

Central configuration schema using Pydantic.
Zero new dependencies (Pydantic already in pyproject.toml).

Validation on startup. Clear errors on invalid config.
Virgin VM concept: must work on clean machine with defaults.

INV-CONFIG-1: All config in central schema
INV-CONFIG-2: Startup validates config
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# =============================================================================
# IBKR CONFIGURATION
# =============================================================================


class IBKRConfig(BaseModel):
    """IBKR connection configuration."""

    account_id: str = Field(default="", description="IBKR account ID")
    host: str = Field(default="127.0.0.1", description="TWS/Gateway host")
    port: int = Field(default=7497, description="TWS/Gateway port (7497=paper, 7496=live)")
    paper_mode: bool = Field(default=True, description="Use paper trading (INV-IBKR-PAPER-GUARD-1)")
    timeout_seconds: int = Field(default=30, description="Connection timeout")
    client_id: int = Field(default=1, description="Client ID for multiple connections")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port range."""
        if not 1 <= v <= 65535:
            raise ValueError(f"Invalid port: {v}")
        return v


# =============================================================================
# RIVER CONFIGURATION
# =============================================================================


class RiverConfig(BaseModel):
    """River data pipeline configuration."""

    data_path: str = Field(default="~/nex/river.db", description="Path to River SQLite database")
    refresh_interval_seconds: int = Field(default=60, description="Data refresh interval")
    stale_threshold_hours: float = Field(
        default=1.0, description="Hours before data considered stale"
    )

    @field_validator("data_path")
    @classmethod
    def expand_path(cls, v: str) -> str:
        """Expand ~ in path."""
        return str(Path(v).expanduser())


# =============================================================================
# GOVERNANCE CONFIGURATION
# =============================================================================


class GovernanceConfig(BaseModel):
    """Governance and halt configuration."""

    halt_timeout_ms: int = Field(default=50, description="Max halt response time (INV-HALT-1)")
    alert_cooldown_seconds: int = Field(default=60, description="Min seconds between same alerts")
    circuit_breaker_threshold: int = Field(default=5, description="Failures before circuit opens")
    circuit_breaker_timeout_seconds: int = Field(
        default=60, description="Circuit half-open timeout"
    )


# =============================================================================
# NOTIFICATION CONFIGURATION
# =============================================================================


class NotificationConfig(BaseModel):
    """Notification and alert configuration."""

    bundle_window_seconds: int = Field(
        default=1800,  # 30 minutes
        description="Alert bundling window (S43: configurable)",
    )
    telegram_enabled: bool = Field(default=True, description="Enable Telegram notifications")
    telegram_chat_id: str | None = Field(default=None, description="Telegram chat ID")
    telegram_bot_token: str | None = Field(default=None, description="Telegram bot token")


# =============================================================================
# NARRATOR CONFIGURATION
# =============================================================================


class NarratorConfig(BaseModel):
    """Narrator template configuration."""

    templates_path: str = Field(
        default="narrator/templates", description="Path to Jinja2 templates"
    )
    emit_receipts: bool = Field(default=False, description="Include receipts links in output")


# =============================================================================
# CSO CONFIGURATION
# =============================================================================


class CSOConfig(BaseModel):
    """CSO (Conditional Strategy Orchestrator) configuration."""

    knowledge_path: str = Field(
        default="cso/knowledge", description="Path to 5-drawer filing cabinet"
    )
    refresh_on_startup: bool = Field(default=True, description="Refresh CSO cache on startup")


# =============================================================================
# ROOT CONFIGURATION
# =============================================================================


class PhoenixConfig(BaseModel):
    """
    Root Phoenix configuration.

    All config sections are optional with sensible defaults.
    This enables virgin VM startup with zero configuration.
    """

    ibkr: IBKRConfig = Field(default_factory=IBKRConfig)
    river: RiverConfig = Field(default_factory=RiverConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    narrator: NarratorConfig = Field(default_factory=NarratorConfig)
    cso: CSOConfig = Field(default_factory=CSOConfig)

    class Config:
        """Pydantic config."""

        extra = "forbid"  # Reject unknown fields
