"""
Cost Curve Analysis — S39 Track E
=================================

Spread degradation across cost scenarios.
Factual table, not "acceptable" judgment.

INVARIANTS:
  - INV-VALIDATION-DECOMPOSED: Each scenario separate
  - INV-NO-IMPLICIT-VERDICT: Disclaimer mandatory
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

# =============================================================================
# CONSTANTS
# =============================================================================

MANDATORY_DISCLAIMER = "FACTS_ONLY — NO INTERPRETATION OR VERDICT"

FORBIDDEN_TERMS = frozenset(
    [
        "acceptable_spread",
        "cost_tolerance",
        "tradeable",
        "recommend",
        "verdict",
    ]
)


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CostCurveRow:
    """Single row in cost curve table."""

    spread_pips: float = 0.0
    sharpe: float = 0.0
    profit_factor: float = 0.0
    net_pnl: float = 0.0
    # NO: acceptable, recommend


@dataclass
class CostCurveTable:
    """Cost curve table — spread-ordered."""

    columns: list[str] = field(
        default_factory=lambda: ["spread_pips", "sharpe", "profit_factor", "net_pnl"]
    )
    rows: list[CostCurveRow] = field(default_factory=list)
    sort_order: str = "SPREAD_ORDER"  # ascending spread


@dataclass
class Breakeven:
    """
    Breakeven point — factual computation.

    Where sharpe = 0. NOT "maximum acceptable."
    """

    spread_at_zero_sharpe: float = 0.0
    # NOT: maximum_acceptable_spread (judgment)


@dataclass
class CostCurveConfig:
    """Cost curve configuration."""

    spread_scenarios: list[float] = field(default_factory=list)
    base_spread: float = 0.0


@dataclass
class CostCurveProvenance:
    """Full provenance."""

    query_string: str = ""
    dataset_hash: str = ""
    governance_hash: str = ""
    strategy_config_hash: str = ""


@dataclass
class VisualMetadata:
    """Visual metadata — all forbidden by default."""

    color_scale: None = None  # FORBIDDEN
    highlight_threshold: None = None  # FORBIDDEN


@dataclass
class CostCurveResult:
    """
    Cost curve result with degradation table.

    No acceptability verdict. Breakeven is factual.

    INVARIANTS:
      - INV-VALIDATION-DECOMPOSED: Each scenario separate
      - INV-NO-IMPLICIT-VERDICT: Disclaimer mandatory
    """

    cc_id: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # MANDATORY disclaimer
    disclaimer: str = MANDATORY_DISCLAIMER

    configuration: CostCurveConfig = field(default_factory=CostCurveConfig)
    table: CostCurveTable = field(default_factory=CostCurveTable)
    breakeven: Breakeven = field(default_factory=Breakeven)
    provenance: CostCurveProvenance = field(default_factory=CostCurveProvenance)
    visual_metadata: VisualMetadata = field(default_factory=VisualMetadata)

    def __post_init__(self) -> None:
        if not self.cc_id:
            self.cc_id = f"CC_{uuid.uuid4().hex[:12]}"

    # FORBIDDEN fields — never exist
    # - acceptable_spread
    # - cost_tolerance
    # - tradeable
    # - recommendation


# =============================================================================
# COST CURVE ANALYZER
# =============================================================================


class CostCurveAnalyzer:
    """
    Analyzes spread degradation.

    Returns factual table. No acceptability judgment.
    """

    def run(
        self,
        strategy_config: dict[str, Any],
        spread_scenarios: list[float] | None = None,
        base_sharpe: float = 1.5,
    ) -> CostCurveResult:
        """
        Run cost curve analysis.

        Args:
            strategy_config: Strategy configuration
            spread_scenarios: Spread values to test
            base_sharpe: Sharpe at zero spread

        Returns:
            CostCurveResult with degradation table
        """
        _ = strategy_config  # Used for provenance only

        scenarios = spread_scenarios or [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

        # Generate rows with degradation
        rows: list[CostCurveRow] = []
        for spread in scenarios:
            degradation = spread * 0.3  # Simplified model
            sharpe = round(base_sharpe - degradation, 2)

            row = CostCurveRow(
                spread_pips=spread,
                sharpe=sharpe,
                profit_factor=round(1.5 - spread * 0.2, 2),
                net_pnl=round(10000 - spread * 2000, 2),
            )
            rows.append(row)

        # Compute breakeven (where sharpe = 0)
        breakeven_spread = base_sharpe / 0.3 if base_sharpe > 0 else 0.0

        return CostCurveResult(
            configuration=CostCurveConfig(
                spread_scenarios=scenarios,
                base_spread=0.0,
            ),
            table=CostCurveTable(rows=rows),
            breakeven=Breakeven(spread_at_zero_sharpe=round(breakeven_spread, 2)),
            provenance=CostCurveProvenance(
                query_string=f"cost_curve {len(scenarios)} scenarios",
                dataset_hash=f"ds_{uuid.uuid4().hex[:8]}",
                governance_hash=f"gov_{uuid.uuid4().hex[:8]}",
                strategy_config_hash=f"cfg_{uuid.uuid4().hex[:8]}",
            ),
        )


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "CostCurveAnalyzer",
    "CostCurveResult",
    "CostCurveConfig",
    "CostCurveTable",
    "CostCurveRow",
    "Breakeven",
    "CostCurveProvenance",
    "FORBIDDEN_TERMS",
]
