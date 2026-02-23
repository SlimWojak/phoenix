"""
Validation Suite — S39 Constitutional Ceiling
==============================================

Decomposed outputs. No viability scores. Ever.
The "Linter of Linters" — final constitutional ceiling.

INVARIANTS:
  - INV-SCALAR-BAN: No composite scores (0-100)
  - INV-VALIDATION-DECOMPOSED: Every check returns separate factors
  - INV-NO-AGGREGATE-SCALAR: No avg_* fields
  - INV-NEUTRAL-ADJECTIVES: No evaluative words
  - INV-VISUAL-PARITY: No color coding by threshold
  - INV-NO-IMPLICIT-VERDICT: All outputs include disclaimer
  - INV-CROSS-MODULE-NO-SYNTH: Chain outputs decomposed only
  - INV-SENSITIVITY-SHUFFLE: Shuffle opt-in (T2)
  - INV-RAW-SIM-T2-ONLY: Raw simulations require T2
"""

__version__ = "1.0.0"
__status__ = "S39_COMPLETE"

from validation.backtest import (
    MANDATORY_DISCLAIMER,
    BacktestMetrics,
    BacktestResult,
    BacktestValidator,
    BacktestWorker,
)
from validation.cost_curve import (
    Breakeven,
    CostCurveAnalyzer,
    CostCurveResult,
    CostCurveTable,
)
from validation.monte_carlo import (
    DrawdownPercentiles,
    MonteCarloResult,
    MonteCarloSimulator,
    RawSimulations,
    ReturnPercentiles,
)
from validation.scalar_ban_linter import (
    EVALUATIVE_ADJECTIVES,
    ScalarBanError,
    ScalarBanLinter,
    ScalarBanResult,
    ScalarBanViolation,
    ViolationType,
)
from validation.sensitivity import (
    SensitivityAnalyzer,
    SensitivityResult,
    SensitivityRow,
    SensitivityTable,
)
from validation.walk_forward import (
    DescriptiveSummary,
    SplitDistribution,
    WalkForwardResult,
    WalkForwardValidator,
    validate_no_avg_fields,
)

__all__ = [
    # Version
    "__version__",
    "__status__",
    # Backtest
    "BacktestResult",
    "BacktestMetrics",
    "BacktestWorker",
    "BacktestValidator",
    "MANDATORY_DISCLAIMER",
    # Walk-Forward
    "WalkForwardResult",
    "WalkForwardValidator",
    "SplitDistribution",
    "DescriptiveSummary",
    "validate_no_avg_fields",
    # Monte Carlo
    "MonteCarloResult",
    "MonteCarloSimulator",
    "DrawdownPercentiles",
    "ReturnPercentiles",
    "RawSimulations",
    # Sensitivity
    "SensitivityResult",
    "SensitivityAnalyzer",
    "SensitivityTable",
    "SensitivityRow",
    # Cost Curve
    "CostCurveResult",
    "CostCurveAnalyzer",
    "CostCurveTable",
    "Breakeven",
    # Scalar Ban Linter
    "ScalarBanLinter",
    "ScalarBanResult",
    "ScalarBanViolation",
    "ScalarBanError",
    "ViolationType",
    "EVALUATIVE_ADJECTIVES",
]
