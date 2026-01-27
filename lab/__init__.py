"""
Phoenix Lab Module
==================

Hypothesis testing and strategy development.

Components:
- HuntEngine: NL hypothesis → HPG → variations → backtest → survivors
- HPGParser: Natural language → Hunt Parameter Grammar
- VariationGenerator: Systematic + seeded chaos variations
- Backtester: Deterministic strategy backtesting
- ShadowBoxer: Paper position tracking
"""

from .backtester import Backtester, BacktestResult
from .hpg_parser import HPG, HPGParser, ValidationResult
from .hunt import HuntEngine, HuntResult
from .variation_generator import VariationConfig, VariationGenerator

__all__ = [
    "HuntEngine",
    "HuntResult",
    "HPGParser",
    "HPG",
    "ValidationResult",
    "VariationGenerator",
    "VariationConfig",
    "Backtester",
    "BacktestResult",
]
