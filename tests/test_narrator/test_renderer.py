"""
Renderer Tests — S40 Track D
============================

Proves INV-NARRATOR-2 and INV-NARRATOR-3.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from narrator.renderer import (
    NarratorRenderer,
    UndefinedVariableError,
    TemplateValidationError,
    create_renderer,
)
from narrator.data_sources import (
    DataSources,
    OrientationData,
    RiverData,
    TradeData,
    HuntData,
    CSOData,
    TestData,
    SupervisorData,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def template_dir() -> Path:
    """Get templates directory."""
    return Path(__file__).parent.parent.parent / "narrator" / "templates"


@pytest.fixture
def renderer(template_dir: Path) -> NarratorRenderer:
    """Create renderer with real templates."""
    return NarratorRenderer(
        template_dir=template_dir,
        validate_on_load=False,  # Disable for testing
    )


@pytest.fixture
def data_sources() -> DataSources:
    """Create data sources."""
    return DataSources()


@pytest.fixture
def sample_briefing_data() -> dict:
    """Sample data for briefing template."""
    return {
        "orientation": OrientationData(
            execution_phase="PRODUCTION",
            kill_flags=[],
            health_status="HEALTHY",
            mode="PAPER",
        ),
        "trades": TradeData(
            open_positions=2,
            daily_pnl=150.50,
        ),
        "cso": CSOData(
            gates_per_pair={"EURUSD": [1, 3, 5], "GBPUSD": [1, 2, 3, 5, 6]},
        ),
        "hunt": HuntData(pending_hypotheses=3),
        "tests": TestData(collected=967, passed=851, failed=0),
        "timestamp_str": "2026-01-30 10:00:00 UTC",
    }


@pytest.fixture
def sample_health_data() -> dict:
    """Sample data for health template."""
    return {
        "river": RiverData(
            health_status="HEALTHY",
            staleness_seconds=2.5,
        ),
        "supervisor": SupervisorData(
            state="RUNNING",
            ibkr_connected=True,
            heartbeat_ok=True,
            degradation_level="NONE",
            circuit_breakers_closed=5,
            circuit_breakers_total=5,
        ),
        "tests": TestData(collected=967, passed=851, failed=0),
        "timestamp_str": "2026-01-30 10:00:00 UTC",
    }


@pytest.fixture
def sample_trade_data() -> dict:
    """Sample data for trade template."""
    return {
        "action": "ENTRY",
        "pair": "GBPUSD",
        "direction": "LONG",
        "entry": 1.2655,
        "stop": 1.2625,
        "target": 1.2715,
        "risk_pct": 0.5,
        "gates_passed": [1, 2, 3, 5, 6],
        "evidence_bead": "TRADE_2026_01_30_001",
    }


@pytest.fixture
def sample_alert_data() -> dict:
    """Sample data for alert template."""
    return {
        "severity": "CRITICAL",
        "component": "IBKR",
        "event": "CONNECTION_LOST",
        "message": "Lost connection to IBKR gateway",
        "action_taken": "T2 BLOCKED",
        "degradation_level": "SOFT",
    }


# =============================================================================
# INV-NARRATOR-3: UNDEFINED RAISES
# =============================================================================


class TestUndefinedRaises:
    """Prove INV-NARRATOR-3: Undefined variables raise errors."""

    def test_missing_variable_raises(self, renderer: NarratorRenderer):
        """INV-NARRATOR-3: Missing variable raises UndefinedVariableError."""
        template_str = "Value: {{ missing_var }}"

        with pytest.raises(UndefinedVariableError):
            renderer.render_string(template_str, {})
        print("✓ INV-NARRATOR-3: Missing variable raises")

    def test_missing_nested_variable_raises(self, renderer: NarratorRenderer):
        """INV-NARRATOR-3: Missing nested variable raises."""
        template_str = "Value: {{ data.nested.value }}"

        with pytest.raises(UndefinedVariableError):
            renderer.render_string(template_str, {"data": {}})
        print("✓ INV-NARRATOR-3: Missing nested raises")

    def test_partial_data_raises(
        self, renderer: NarratorRenderer, sample_trade_data: dict
    ):
        """INV-NARRATOR-3: Partial data raises."""
        # Remove required field
        del sample_trade_data["entry"]

        with pytest.raises(UndefinedVariableError):
            renderer.render("trade", sample_trade_data)
        print("✓ INV-NARRATOR-3: Partial data raises")


# =============================================================================
# TEMPLATE RENDERING
# =============================================================================


class TestTemplateRendering:
    """Test template rendering."""

    def test_render_briefing(
        self, renderer: NarratorRenderer, sample_briefing_data: dict
    ):
        """Briefing template renders correctly."""
        output = renderer.render("briefing", sample_briefing_data)

        assert "OINK OINK MOTHERFUCKER" in output
        assert "HEALTHY" in output
        assert "PAPER" in output
        print("✓ Briefing renders")

    def test_render_health(
        self, renderer: NarratorRenderer, sample_health_data: dict
    ):
        """Health template renders correctly."""
        output = renderer.render("health", sample_health_data)

        assert "HEALTH CHECK" in output
        assert "RUNNING" in output
        assert "CLOSED" in output
        print("✓ Health renders")

    def test_render_trade(
        self, renderer: NarratorRenderer, sample_trade_data: dict
    ):
        """Trade template renders correctly."""
        output = renderer.render("trade", sample_trade_data)

        assert "TRADE EVENT" in output
        assert "ENTRY" in output
        assert "GBPUSD" in output
        assert "LONG" in output
        print("✓ Trade renders")

    def test_render_alert(
        self, renderer: NarratorRenderer, sample_alert_data: dict
    ):
        """Alert template renders correctly."""
        output = renderer.render("alert", sample_alert_data)

        assert "ALERT" in output
        assert "CRITICAL" in output
        assert "IBKR" in output
        assert "T2 BLOCKED" in output
        print("✓ Alert renders")


# =============================================================================
# DATA SOURCES INTEGRATION
# =============================================================================


class TestDataSourcesIntegration:
    """Test data sources integration."""

    def test_data_sources_get_all(self, data_sources: DataSources):
        """get_all returns all sources."""
        data = data_sources.get_all()

        assert "orientation" in data
        assert "athena" in data
        assert "river" in data
        assert "trades" in data
        assert "cso" in data
        assert "hunt" in data
        assert "supervisor" in data
        assert "timestamp" in data
        print("✓ get_all returns all sources")

    def test_data_has_source_tracing(self, data_sources: DataSources):
        """INV-NARRATOR-2: All data has source field."""
        orientation = data_sources.get_orientation()
        assert hasattr(orientation, "source_file")
        assert orientation.source_file != ""
        print("✓ INV-NARRATOR-2: Source tracing present")


# =============================================================================
# VALIDATION
# =============================================================================


class TestValidation:
    """Test template validation."""

    def test_forbidden_content_raises(self, renderer: NarratorRenderer):
        """Forbidden content raises TemplateValidationError."""
        # Create renderer with validation enabled
        renderer_strict = NarratorRenderer(
            template_dir=renderer.template_dir,
            validate_on_load=True,
        )

        template_str = "You should do this: {{ value }}"

        with pytest.raises(TemplateValidationError):
            renderer_strict.render_string(template_str, {"value": "test"})
        print("✓ Forbidden content raises")


# =============================================================================
# CUSTOM FILTERS
# =============================================================================


class TestCustomFilters:
    """Test custom Jinja2 filters."""

    def test_format_pnl_positive(self, renderer: NarratorRenderer):
        """format_pnl formats positive values."""
        template_str = "{{ value | format_pnl }}"
        output = renderer.render_string(template_str, {"value": 150.50})

        assert output == "+$150.50"
        print("✓ format_pnl positive")

    def test_format_pnl_negative(self, renderer: NarratorRenderer):
        """format_pnl formats negative values."""
        template_str = "{{ value | format_pnl }}"
        output = renderer.render_string(template_str, {"value": -50.25})

        assert output == "-$50.25"
        print("✓ format_pnl negative")

    def test_format_gates(self, renderer: NarratorRenderer):
        """format_gates formats gate list."""
        template_str = "{{ gates | format_gates }}"
        output = renderer.render_string(template_str, {"gates": [1, 2, 3, 5]})

        assert output == "[1,2,3,5]"
        print("✓ format_gates")

    def test_format_staleness(self, renderer: NarratorRenderer):
        """format_staleness formats duration."""
        template_str = "{{ seconds | format_staleness }}"

        output1 = renderer.render_string(template_str, {"seconds": 0.5})
        assert output1 == "fresh"

        output2 = renderer.render_string(template_str, {"seconds": 30})
        assert "30.0s ago" == output2

        print("✓ format_staleness")


# =============================================================================
# CHAOS: GRACEFUL ERRORS
# =============================================================================


class TestGracefulErrors:
    """Chaos tests for graceful error handling."""

    def test_missing_orientation_graceful(self, template_dir: Path):
        """Missing orientation.yaml handled gracefully."""
        # Create data sources with non-existent path
        ds = DataSources(base_path=Path("/nonexistent"))
        orientation = ds.get_orientation()

        # Should return default data, not crash
        assert orientation.execution_phase == "UNKNOWN"
        print("✓ Missing orientation graceful")

    def test_render_with_empty_data(self, renderer: NarratorRenderer):
        """Render with empty optional fields."""
        template_str = "{% if value %}Value: {{ value }}{% else %}No value{% endif %}"
        output = renderer.render_string(template_str, {"value": None})

        assert "No value" in output
        print("✓ Empty data handled")

    def test_stale_river_flagged(self, renderer: NarratorRenderer):
        """Stale River data is flagged in output."""
        data = {
            "river": RiverData(
                health_status="HEALTHY",
                staleness_seconds=60.0,  # Stale!
            ),
            "supervisor": SupervisorData(
                state="RUNNING",
                ibkr_connected=True,
                heartbeat_ok=True,
                circuit_breakers_closed=5,
                circuit_breakers_total=5,
            ),
            "tests": TestData(),
            "timestamp_str": "2026-01-30 10:00:00 UTC",
        }

        output = renderer.render("health", data)

        # Should indicate staleness
        assert "STALE" in output or "60.0" in output or "1.0m" in output
        print("✓ Stale data flagged")


# =============================================================================
# FACTORY
# =============================================================================


class TestFactory:
    """Test factory function."""

    def test_create_renderer(self, template_dir: Path):
        """create_renderer creates configured renderer."""
        renderer = create_renderer(template_dir=template_dir)

        assert renderer is not None
        assert renderer.template_dir == template_dir
        print("✓ Factory creates renderer")
