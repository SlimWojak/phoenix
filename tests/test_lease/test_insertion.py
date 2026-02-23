"""
Tests for Insertion Protocol
============================

Sprint: S47 LEASE_IMPLEMENTATION
EXIT_GATE_S47_5: 8-step insertion completes with valid cartridge

Tests:
  - Full 8-step protocol
  - Schema validation
  - Linter/guard dog scan
  - INV-LEASE-CEILING enforcement
  - Conflict rejection (P5_SLOT_OR_PERISH)
"""

from datetime import UTC, datetime

import pytest

from governance.cartridge import (
    CartridgeLinter,
    CartridgeLoader,
    CartridgeRegistry,
)
from governance.insertion import (
    InsertionProtocol,
    quick_insert,
)
from governance.lease import LeaseManager

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def valid_cartridge_data() -> dict:
    """Valid cartridge data for testing."""
    return {
        "identity": {
            "name": "TEST_STRATEGY",
            "version": "1.0.0",
            "author": "test_author",
            "created_at": datetime.now(UTC).isoformat(),
        },
        "scope": {
            "pairs": ["EUR/USD", "GBP/USD", "USD/JPY"],
        },
        "risk_defaults": {
            "per_trade_pct": 2.0,
            "min_rr": 2.0,
            "max_trades_per_session": 3,
        },
        "cso_integration": {
            "drawer_config": {
                "HTF_BIAS": {"enabled": True},
                "MARKET_STRUCTURE": {"enabled": True},
                "PREMIUM_DISCOUNT": {"enabled": True},
                "ENTRY_MODEL": {"enabled": True},
                "CONFIRMATION": {"enabled": True},
            },
        },
        "constitutional": {
            "invariants_required": ["INV-NO-UNSOLICITED", "INV-HALT-1"],
        },
    }


@pytest.fixture
def valid_bounds() -> dict:
    """Valid lease bounds for testing."""
    return {
        "max_drawdown_pct": 5.0,
        "max_consecutive_losses": 3,
        "allowed_pairs": ["EUR/USD", "GBP/USD"],  # Subset of cartridge
        "allowed_pairs_mode": "SUBSET",
        "position_size_cap": 1.5,  # <= cartridge's 2.0%
    }


@pytest.fixture
def insertion_protocol() -> InsertionProtocol:
    """Fresh insertion protocol for each test."""
    # Reset lease manager singleton
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

    # Cleanup
    manager.reset()
    LeaseManager._instance = None


# =============================================================================
# SUCCESSFUL INSERTION TESTS — EXIT_GATE_S47_5
# =============================================================================


class TestSuccessfulInsertion:
    """Test successful 8-step insertion protocol."""

    def test_full_insertion_from_dict(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
        valid_bounds: dict,
    ):
        """Complete 8-step insertion succeeds."""
        result = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test_user",
            duration_days=7,
            bounds=valid_bounds,
        )

        assert result.success is True
        assert result.step_reached == 8
        assert result.error is None
        assert result.cartridge_ref == "TEST_STRATEGY_v1.0.0"
        assert result.lease_id is not None
        assert result.lint_result is not None
        assert result.lint_result["passed"] is True

    def test_insertion_activates_lease(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
        valid_bounds: dict,
    ):
        """Insertion activates lease via LeaseManager."""
        result = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test_user",
            duration_days=7,
            bounds=valid_bounds,
        )

        assert result.success
        assert insertion_protocol.lease_manager.has_active_lease

    def test_insertion_slots_cartridge(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
        valid_bounds: dict,
    ):
        """Insertion slots cartridge into registry."""
        result = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test_user",
            duration_days=7,
            bounds=valid_bounds,
        )

        assert result.success
        assert insertion_protocol.registry.active_ref == "TEST_STRATEGY_v1.0.0"


# =============================================================================
# SCHEMA VALIDATION TESTS — Step 2
# =============================================================================


class TestSchemaValidation:
    """Test schema validation (Step 2)."""

    def test_missing_required_field(self, insertion_protocol: InsertionProtocol):
        """Missing required field fails at step 2."""
        invalid_data = {
            "identity": {
                "name": "BAD_STRATEGY",
                "version": "1.0.0",
                # Missing: author, created_at
            },
            "scope": {
                "pairs": ["EUR/USD"],
            },
            # Missing: risk_defaults, constitutional
        }

        result = insertion_protocol.insert_from_dict(
            cartridge_data=invalid_data,
            created_by="test",
            duration_days=7,
            bounds={
                "max_drawdown_pct": 5,
                "max_consecutive_losses": 3,
                "allowed_pairs": ["EUR/USD"],
                "allowed_pairs_mode": "SUBSET",
            },
        )

        assert result.success is False
        assert result.step_reached == 2
        assert "Validation failed" in result.error

    def test_invalid_name_format(self, insertion_protocol: InsertionProtocol):
        """Invalid name format fails validation."""
        invalid_data = {
            "identity": {
                "name": "bad-name",  # Must be UPPER_SNAKE_CASE
                "version": "1.0.0",
                "author": "test",
                "created_at": datetime.now(UTC).isoformat(),
            },
            "scope": {"pairs": ["EUR/USD"]},
            "risk_defaults": {"per_trade_pct": 1.0, "min_rr": 2.0, "max_trades_per_session": 3},
            "cso_integration": {
                "drawer_config": {
                    "HTF_BIAS": {"enabled": True},
                    "MARKET_STRUCTURE": {"enabled": True},
                    "PREMIUM_DISCOUNT": {"enabled": True},
                    "ENTRY_MODEL": {"enabled": True},
                    "CONFIRMATION": {"enabled": True},
                },
            },
            "constitutional": {"invariants_required": ["INV-NO-UNSOLICITED", "INV-HALT-1"]},
        }

        result = insertion_protocol.insert_from_dict(
            cartridge_data=invalid_data,
            created_by="test",
            duration_days=7,
            bounds={
                "max_drawdown_pct": 5,
                "max_consecutive_losses": 3,
                "allowed_pairs": ["EUR/USD"],
                "allowed_pairs_mode": "SUBSET",
            },
        )

        assert result.success is False
        assert result.step_reached == 2


# =============================================================================
# LINTER TESTS — Step 4
# =============================================================================


class TestLinterStep:
    """Test linter/guard dog scan (Step 4)."""

    def test_lint_passes_valid_cartridge(
        self,
        valid_cartridge_data: dict,
    ):
        """Valid cartridge passes lint."""
        loader = CartridgeLoader()
        linter = CartridgeLinter()

        manifest = loader.load_from_dict(valid_cartridge_data)
        result = linter.lint(manifest)

        assert result["passed"] is True
        assert result["errors"] == []

    def test_lint_warns_on_high_risk(self, valid_cartridge_data: dict):
        """High per_trade_pct triggers warning."""
        valid_cartridge_data["risk_defaults"]["per_trade_pct"] = 4.5

        loader = CartridgeLoader()
        linter = CartridgeLinter()

        manifest = loader.load_from_dict(valid_cartridge_data)
        result = linter.lint(manifest)

        assert result["passed"] is True  # Warnings don't fail
        assert any("per_trade_pct" in w for w in result["warnings"])


# =============================================================================
# SLOT CONFLICT TESTS — Step 5 (P5_SLOT_OR_PERISH)
# =============================================================================


class TestSlotConflict:
    """Test slot conflict rejection (P5_SLOT_OR_PERISH)."""

    def test_second_cartridge_rejected(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
        valid_bounds: dict,
    ):
        """Second cartridge insertion rejected (v1.0 single cartridge)."""
        # First insertion succeeds
        result1 = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test",
            duration_days=7,
            bounds=valid_bounds,
        )
        assert result1.success

        # Second cartridge with different name
        second_data = valid_cartridge_data.copy()
        second_data["identity"] = {
            "name": "SECOND_STRATEGY",
            "version": "1.0.0",
            "author": "test",
            "created_at": datetime.now(UTC).isoformat(),
        }

        result2 = insertion_protocol.insert_from_dict(
            cartridge_data=second_data,
            created_by="test",
            duration_days=7,
            bounds=valid_bounds,
        )

        assert result2.success is False
        assert result2.step_reached == 5
        assert "Slot failed" in result2.error

    def test_same_cartridge_version_rejected_when_active(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
        valid_bounds: dict,
    ):
        """Same cartridge version blocked when already active."""
        # First insertion
        result1 = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test",
            duration_days=7,
            bounds=valid_bounds,
        )
        assert result1.success

        # Try same cartridge again
        result2 = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test",
            duration_days=7,
            bounds=valid_bounds,
        )

        # Should fail because lease already active
        assert result2.success is False


# =============================================================================
# INV-LEASE-CEILING TESTS — Step 6
# =============================================================================


class TestLeaseCeilingValidation:
    """Test INV-LEASE-CEILING enforcement."""

    def test_position_size_exceeds_ceiling(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
    ):
        """Position size > cartridge default is rejected."""
        # Cartridge has per_trade_pct = 2.0%
        bounds_with_high_size = {
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "allowed_pairs": ["EUR/USD"],
            "allowed_pairs_mode": "SUBSET",
            "position_size_cap": 3.0,  # > 2.0% — VIOLATION
        }

        result = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test",
            duration_days=7,
            bounds=bounds_with_high_size,
        )

        assert result.success is False
        assert result.step_reached == 6
        assert "INV-LEASE-CEILING" in result.error

    def test_pairs_not_in_cartridge(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
    ):
        """Pairs not in cartridge are rejected."""
        bounds_with_extra_pairs = {
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "allowed_pairs": ["EUR/USD", "AUD/NZD"],  # AUD/NZD not in cartridge
            "allowed_pairs_mode": "SUBSET",
        }

        result = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test",
            duration_days=7,
            bounds=bounds_with_extra_pairs,
        )

        assert result.success is False
        assert result.step_reached == 6


# =============================================================================
# ROLLBACK TESTS
# =============================================================================


class TestRollback:
    """Test rollback on failure."""

    def test_slot_removed_on_bounds_failure(
        self,
        insertion_protocol: InsertionProtocol,
        valid_cartridge_data: dict,
    ):
        """Slot is removed if bounds validation fails."""
        # Valid cartridge, invalid bounds
        bad_bounds = {
            "max_drawdown_pct": 5.0,
            "max_consecutive_losses": 3,
            "allowed_pairs": ["EUR/USD"],
            "allowed_pairs_mode": "SUBSET",
            "position_size_cap": 10.0,  # >> cartridge default — VIOLATION
        }

        result = insertion_protocol.insert_from_dict(
            cartridge_data=valid_cartridge_data,
            created_by="test",
            duration_days=7,
            bounds=bad_bounds,
        )

        assert result.success is False

        # Slot should be rolled back
        assert insertion_protocol.registry.active_cartridge is None


# =============================================================================
# QUICK INSERT HELPER
# =============================================================================


class TestQuickInsert:
    """Test quick_insert helper function."""

    def test_quick_insert_success(self, valid_cartridge_data: dict, valid_bounds: dict):
        """quick_insert helper works for valid inputs."""
        result = quick_insert(
            cartridge_data=valid_cartridge_data,
            bounds=valid_bounds,
            created_by="test",
            duration_days=7,
        )

        assert result.success
        assert result.cartridge_ref == "TEST_STRATEGY_v1.0.0"
