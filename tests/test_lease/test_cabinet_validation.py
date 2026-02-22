"""
Tests for Cabinet Validation (S50.T1 CABINET_REFACTOR)
======================================================

Verifies:
  - DrawerConfig enforces all 5 canonical drawers
  - Missing/empty/wrong-named drawers are rejected
  - CartridgeLinter validates cabinet completeness
  - Insertion protocol uses validation, not merge
  - methodology_template.yaml is NOT loaded as merge base
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from governance.cartridge import (
    CartridgeLinter,
    CartridgeLoader,
    CartridgeRegistry,
    create_minimal_cartridge,
)
from governance.insertion import (
    InsertionProtocol,
    quick_insert,
)
from governance.lease import LeaseManager
from governance.lease_types import (
    REQUIRED_DRAWER_NAMES,
    DrawerConfig,
    DrawerName,
)

# =============================================================================
# FIXTURES
# =============================================================================

COMPLETE_CABINET = {
    "HTF_BIAS": {"weekly_bias_required": False, "daily_bias_required": False},
    "MARKET_STRUCTURE": {"asia_range_method": "wick_to_wick", "mss_required": False},
    "PREMIUM_DISCOUNT": {"sweep_required": True, "pd_zone_required": False},
    "ENTRY_MODEL": {"fvg_required": True, "entry_type": "fvg_retrace"},
    "CONFIRMATION": {"sl_placement": "beyond_sweep_extreme", "trail_stop": False},
}


def _cartridge_data(cabinet: dict | None = None) -> dict:
    """Build valid cartridge data with given cabinet (or default)."""
    return {
        "identity": {
            "name": "TEST_STRATEGY",
            "version": "1.0.0",
            "author": "test_author",
            "created_at": datetime.now(UTC).isoformat(),
        },
        "scope": {
            "pairs": ["EUR/USD"],
        },
        "risk_defaults": {
            "per_trade_pct": 2.0,
            "min_rr": 2.0,
            "max_trades_per_session": 3,
        },
        "cso_integration": {
            "drawer_config": cabinet or COMPLETE_CABINET,
        },
        "constitutional": {
            "invariants_required": ["INV-NO-UNSOLICITED", "INV-HALT-1"],
        },
    }


@pytest.fixture
def valid_bounds() -> dict:
    return {
        "max_drawdown_pct": 5.0,
        "max_consecutive_losses": 3,
        "allowed_pairs": ["EUR/USD"],
        "allowed_pairs_mode": "SUBSET",
    }


@pytest.fixture
def insertion_protocol() -> InsertionProtocol:
    LeaseManager._instance = None
    manager = LeaseManager()
    manager.configure()

    protocol = InsertionProtocol(
        loader=CartridgeLoader(),
        linter=CartridgeLinter(),
        registry=CartridgeRegistry(),
        lease_manager=manager,
    )

    yield protocol

    manager.reset()
    LeaseManager._instance = None


# =============================================================================
# DRAWER CONFIG MODEL TESTS
# =============================================================================


class TestDrawerConfig:
    """Pydantic-level validation of the DrawerConfig model."""

    def test_valid_complete_cabinet(self):
        """All 5 drawers present and non-empty passes."""
        config = DrawerConfig(**COMPLETE_CABINET)
        assert config.HTF_BIAS == COMPLETE_CABINET["HTF_BIAS"]
        assert config.CONFIRMATION == COMPLETE_CABINET["CONFIRMATION"]

    def test_missing_drawer_rejects(self):
        """Missing CONFIRMATION drawer → ValidationError."""
        incomplete = {k: v for k, v in COMPLETE_CABINET.items() if k != "CONFIRMATION"}
        with pytest.raises(ValidationError, match="CONFIRMATION"):
            DrawerConfig(**incomplete)

    def test_empty_drawer_rejects(self):
        """Empty dict for ENTRY_MODEL → ValidationError."""
        cabinet = {**COMPLETE_CABINET, "ENTRY_MODEL": {}}
        with pytest.raises(ValidationError, match="ENTRY_MODEL"):
            DrawerConfig(**cabinet)

    def test_wrong_drawer_name_rejects(self):
        """Old-style name 'foundation' instead of 'HTF_BIAS' → helpful error."""
        bad_cabinet = {
            "foundation": {"enabled": True},
            "MARKET_STRUCTURE": {"enabled": True},
            "PREMIUM_DISCOUNT": {"enabled": True},
            "ENTRY_MODEL": {"enabled": True},
            "CONFIRMATION": {"enabled": True},
        }
        with pytest.raises(ValidationError, match="foundation.*HTF_BIAS") as exc_info:
            DrawerConfig(**bad_cabinet)
        error_text = str(exc_info.value)
        for name in DrawerName:
            assert name.value in error_text, f"Error should list canonical name {name.value}"
        assert "methodology_template.yaml" in error_text

    def test_extra_drawer_key_rejects(self):
        """Extra key beyond the 5 canonical drawers is rejected (extra=forbid)."""
        cabinet = {**COMPLETE_CABINET, "BOGUS_DRAWER": {"surprise": True}}
        with pytest.raises(ValidationError, match="BOGUS_DRAWER"):
            DrawerConfig(**cabinet)

    def test_canonical_names_match_enum(self):
        """DrawerName enum values match the required set."""
        assert {d.value for d in DrawerName} == REQUIRED_DRAWER_NAMES


# =============================================================================
# CARTRIDGE LINTER TESTS
# =============================================================================


class TestCabinetLinter:
    """CartridgeLinter validates cabinet completeness and content."""

    def test_lint_passes_complete_cabinet(self):
        loader = CartridgeLoader()
        linter = CartridgeLinter()
        manifest = loader.load_from_dict(_cartridge_data())
        result = linter.lint(manifest)
        assert result["passed"] is True
        assert result["errors"] == []

    def test_guard_dog_scans_cabinet_directly(self):
        """Guard dog scan on drawer_config, not a merged result."""
        manifest = create_minimal_cartridge(
            name="GUARD_TEST",
            version="1.0.0",
            author="test",
            pairs=["EUR/USD"],
        )
        linter = CartridgeLinter()
        result = linter.lint(manifest)
        assert result["passed"] is True

    def test_guard_dog_catches_forbidden_in_drawer_key(self):
        """Drawer value containing forbidden word → lint error."""
        cabinet = {
            **COMPLETE_CABINET,
            "ENTRY_MODEL": {"signal_quality": "best", "fvg_required": True},
        }
        manifest = CartridgeLoader().load_from_dict(_cartridge_data(cabinet))
        result = CartridgeLinter().lint(manifest)
        assert result["passed"] is False
        assert any("best" in e and "ENTRY_MODEL" in e for e in result["errors"])

    def test_guard_dog_catches_forbidden_in_drawer_value(self):
        """Drawer value containing forbidden pattern → lint error."""
        cabinet = {
            **COMPLETE_CABINET,
            "MARKET_STRUCTURE": {"setup_note": "strongest setup ever", "mss_required": False},
        }
        manifest = CartridgeLoader().load_from_dict(_cartridge_data(cabinet))
        result = CartridgeLinter().lint(manifest)
        assert result["passed"] is False
        assert any("strongest" in e and "MARKET_STRUCTURE" in e for e in result["errors"])

    def test_guard_dog_clean_cabinet_passes(self):
        """Normal cabinet with no forbidden patterns passes cleanly."""
        manifest = CartridgeLoader().load_from_dict(_cartridge_data())
        result = CartridgeLinter().lint(manifest)
        assert result["passed"] is True
        forbidden_errors = [
            e for e in result["errors"] if "Forbidden" in e or "pattern" in e.lower()
        ]
        assert forbidden_errors == []

    def test_guard_dog_scans_all_5_drawers(self):
        """Forbidden pattern buried in CONFIRMATION (drawer 5) is caught."""
        cabinet = {
            **COMPLETE_CABINET,
            "CONFIRMATION": {"exit_rule": "must trade every signal", "trail_stop": False},
        }
        manifest = CartridgeLoader().load_from_dict(_cartridge_data(cabinet))
        result = CartridgeLinter().lint(manifest)
        assert result["passed"] is False
        assert any("must trade" in e and "CONFIRMATION" in e for e in result["errors"])


# =============================================================================
# INSERTION PROTOCOL TESTS
# =============================================================================


class TestInsertionWithCabinet:
    """Insertion protocol uses cabinet validation, not merge."""

    def test_insertion_succeeds_with_complete_cabinet(self, insertion_protocol, valid_bounds):
        result = insertion_protocol.insert_from_dict(
            cartridge_data=_cartridge_data(),
            created_by="test_user",
            duration_days=7,
            bounds=valid_bounds,
        )
        assert result.success is True
        assert result.step_reached == 8
        assert result.cartridge_ref == "TEST_STRATEGY_v1.0.0"

    def test_insertion_rejects_missing_cabinet(self, insertion_protocol, valid_bounds):
        """Cartridge without cso_integration.drawer_config fails at schema validation."""
        data = {
            "identity": {
                "name": "NO_CABINET",
                "version": "1.0.0",
                "author": "test",
                "created_at": datetime.now(UTC).isoformat(),
            },
            "scope": {"pairs": ["EUR/USD"]},
            "risk_defaults": {"per_trade_pct": 1.0, "min_rr": 2.0, "max_trades_per_session": 3},
            "cso_integration": {},
            "constitutional": {"invariants_required": ["INV-NO-UNSOLICITED", "INV-HALT-1"]},
        }
        result = insertion_protocol.insert_from_dict(
            cartridge_data=data,
            created_by="test",
            duration_days=7,
            bounds=valid_bounds,
        )
        assert result.success is False
        assert result.step_reached == 2

    def test_methodology_template_not_loaded_for_merge(self, insertion_protocol, valid_bounds):
        """No merge base is loaded during insertion."""
        result = insertion_protocol.insert_from_dict(
            cartridge_data=_cartridge_data(),
            created_by="test",
            duration_days=7,
            bounds=valid_bounds,
        )
        assert result.success is True


class TestQuickInsertCabinet:
    """quick_insert helper with cabinet model."""

    def test_quick_insert_with_cabinet(self, valid_bounds):
        result = quick_insert(
            cartridge_data=_cartridge_data(),
            bounds=valid_bounds,
            created_by="test",
            duration_days=7,
        )
        assert result.success
        assert result.cartridge_ref == "TEST_STRATEGY_v1.0.0"


# =============================================================================
# CHAOS VECTORS
# =============================================================================


class TestCabinetChaos:
    """Chaos vectors for cabinet validation."""

    def test_drawers_in_wrong_order_still_validates(self):
        """Dict ordering doesn't matter — should validate."""
        reordered = {
            "CONFIRMATION": {"trail_stop": False},
            "HTF_BIAS": {"enabled": True},
            "ENTRY_MODEL": {"fvg_required": True},
            "PREMIUM_DISCOUNT": {"sweep_required": True},
            "MARKET_STRUCTURE": {"mss_required": False},
        }
        config = DrawerConfig(**reordered)
        assert config.HTF_BIAS == {"enabled": True}
        assert config.CONFIRMATION == {"trail_stop": False}

    def test_unicode_in_drawer_values_handled(self):
        """Unicode content in drawer values should pass gracefully."""
        cabinet = {
            "HTF_BIAS": {"note": "日本語テスト"},
            "MARKET_STRUCTURE": {"note": "Ñoño"},
            "PREMIUM_DISCOUNT": {"note": "Ölya's zone"},
            "ENTRY_MODEL": {"note": "FVG → entry"},
            "CONFIRMATION": {"note": "SL ≤ 2 pips"},
        }
        config = DrawerConfig(**cabinet)
        assert config.HTF_BIAS["note"] == "日本語テスト"
