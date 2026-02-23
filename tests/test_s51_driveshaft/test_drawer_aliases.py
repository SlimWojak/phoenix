"""
T3 Tests: Drawer Name Aliases — S51 DRIVESHAFT
================================================

Tests that drawer alias compatibility layer works correctly.
INV-ALIAS-PARSER-BOUNDARY: Aliases die at parser. Never persisted.
"""

from __future__ import annotations

import pytest

from governance.lease_types import DrawerConfig, DrawerName

SAMPLE_DRAWER_CONTENT = {"some_key": "some_value"}


def _make_config(**overrides) -> dict:
    """Build a complete 5-drawer config dict."""
    base = {
        "HTF_BIAS": {"bias_required": True},
        "MARKET_STRUCTURE": {"mss_required": True},
        "PREMIUM_DISCOUNT": {"sweep_required": True},
        "ENTRY_MODEL": {"fvg_required": True},
        "CONFIRMATION": {"sl_placement": "swing"},
    }
    base.update(overrides)
    return base


class TestNewAliasNames:
    """S51 Olya-proposed names load correctly."""

    def test_new_names_parse(self):
        config = DrawerConfig(
            CONTEXT={"bias_required": False},
            MONITORING={"range_method": "wick"},
            SETUP={"sweep": True},
            EXECUTION={"entry_type": "market"},
            MANAGEMENT={"trail": False},
        )
        assert config.HTF_BIAS == {"bias_required": False}
        assert config.MARKET_STRUCTURE == {"range_method": "wick"}
        assert config.PREMIUM_DISCOUNT == {"sweep": True}
        assert config.ENTRY_MODEL == {"entry_type": "market"}
        assert config.CONFIRMATION == {"trail": False}

    def test_old_canonical_names_still_work(self):
        config = DrawerConfig(**_make_config())
        assert config.HTF_BIAS == {"bias_required": True}

    def test_mixed_names_parse(self):
        """Mix of old canonical and new alias names."""
        config = DrawerConfig(
            HTF_BIAS={"bias": True},
            MONITORING={"range": True},
            PREMIUM_DISCOUNT={"sweep": True},
            EXECUTION={"entry": True},
            CONFIRMATION={"sl": True},
        )
        assert config.HTF_BIAS == {"bias": True}
        assert config.MARKET_STRUCTURE == {"range": True}
        assert config.ENTRY_MODEL == {"entry": True}

    def test_legacy_names_parse(self):
        """Pre-S44 legacy names still accepted."""
        config = DrawerConfig(
            foundation={"bias": True},
            context={"range": True},
            conditions={"sweep": True},
            entry={"fvg": True},
            management={"sl": True},
        )
        assert config.HTF_BIAS == {"bias": True}
        assert config.MARKET_STRUCTURE == {"range": True}


class TestAliasNormalization:
    """Aliases normalize to canonical enum names internally."""

    def test_canonical_names_on_model(self):
        """After parsing, only canonical field names exist."""
        config = DrawerConfig(
            CONTEXT={"a": 1},
            MONITORING={"b": 2},
            SETUP={"c": 3},
            EXECUTION={"d": 4},
            MANAGEMENT={"e": 5},
        )
        for name in DrawerName:
            assert hasattr(config, name.value)
            assert getattr(config, name.value) is not None

    def test_alias_not_stored_as_attribute(self):
        """Alias names do not persist as attributes."""
        config = DrawerConfig(
            CONTEXT={"a": 1},
            MONITORING={"b": 2},
            SETUP={"c": 3},
            EXECUTION={"d": 4},
            MANAGEMENT={"e": 5},
        )
        assert not hasattr(config, "CONTEXT")
        assert not hasattr(config, "MONITORING")
        assert not hasattr(config, "SETUP")
        assert not hasattr(config, "EXECUTION")
        assert not hasattr(config, "MANAGEMENT")


class TestEmptyDrawerRejection:
    """Empty drawers still rejected regardless of naming."""

    def test_empty_drawer_raises(self):
        with pytest.raises(ValueError, match="non-empty"):
            DrawerConfig(
                CONTEXT={},
                MONITORING={"b": 2},
                SETUP={"c": 3},
                EXECUTION={"d": 4},
                MANAGEMENT={"e": 5},
            )
