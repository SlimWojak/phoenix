"""
Phoenix Configuration Loader — S43 Track C
==========================================

Central configuration loading and validation.

Usage:
    from config.loader import load_config
    config = load_config()  # Uses defaults
    config = load_config("config/phoenix.yaml")  # From file

INV-CONFIG-1: All config in central schema
INV-CONFIG-2: Startup validates config (ValidationError on invalid)
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from config.schema import PhoenixConfig

# Default config file path
DEFAULT_CONFIG_PATH = "config/phoenix.yaml"

# Cached config (singleton pattern)
_config: PhoenixConfig | None = None


def load_config(path: str | None = None) -> PhoenixConfig:
    """
    Load and validate Phoenix configuration.

    Args:
        path: Optional path to YAML config file. If None, uses defaults.

    Returns:
        Validated PhoenixConfig instance.

    Raises:
        ValidationError: If config is invalid (clear error message).
        FileNotFoundError: If specified path doesn't exist.
        yaml.YAMLError: If YAML parsing fails.
    """
    global _config

    # If no path and config cached, return cached
    if path is None and _config is not None:
        return _config

    # Load from file if path provided and exists
    config_data = {}
    if path:
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(config_path) as f:
            config_data = yaml.safe_load(f) or {}
    elif Path(DEFAULT_CONFIG_PATH).exists():
        # Try default path
        with open(DEFAULT_CONFIG_PATH) as f:
            config_data = yaml.safe_load(f) or {}

    # Validate and create config
    config = PhoenixConfig(**config_data)

    # Cache if using default path
    if path is None:
        _config = config

    return config


def reload_config(path: str | None = None) -> PhoenixConfig:
    """
    Force reload configuration (bypasses cache).

    Args:
        path: Optional path to YAML config file.

    Returns:
        Validated PhoenixConfig instance.
    """
    global _config
    _config = None
    return load_config(path)


def get_config() -> PhoenixConfig:
    """
    Get current configuration (load if not cached).

    Returns:
        Validated PhoenixConfig instance.
    """
    if _config is None:
        return load_config()
    return _config


def validate_config(data: dict) -> tuple[bool, str | None]:
    """
    Validate configuration data without loading.

    Args:
        data: Configuration dictionary to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        PhoenixConfig(**data)
        return True, None
    except ValidationError as e:
        return False, str(e)
