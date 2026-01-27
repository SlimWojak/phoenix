"""
Phoenix CSO Module — Chief Strategy Officer
============================================

Continuous setup detection across 6 pairs.
Olya's methodology encoded as immutable core.

Components:
- StructureDetector: FVG, BOS, CHoCH, OTE detection
- StrategyCore: Setup detection + quality scoring
- CSOScanner: Multi-pair scanning
- ParamsLoader: Calibratable parameters

INVARIANTS:
- INV-CSO-CORE-1: Strategy logic immutable; only params calibratable
- INV-CSO-6PAIR-1: CSO scans all 6 pairs from pairs.yaml
- INV-CSO-CSE-1: CSO outputs only valid CSE format
- INV-CSO-CAL-1: Param recalibration triggers mandatory shadow period
"""

from .params_loader import CSOParams, ParamsLoader
from .scanner import CSOScanner
from .strategy_core import Setup, SetupResult, StrategyCore
from .structure_detector import BOS, FVG, OTE, CHoCH, LiquiditySweep, StructureDetector

__all__ = [
    "StructureDetector",
    "FVG",
    "BOS",
    "CHoCH",
    "OTE",
    "LiquiditySweep",
    "StrategyCore",
    "Setup",
    "SetupResult",
    "CSOScanner",
    "ParamsLoader",
    "CSOParams",
]
