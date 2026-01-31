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
- CSOObserver: Read-only observer interface
- Beads: Immutable decision artifacts

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
from .beads import (
    Bead,
    BeadFactory,
    BeadStatus,
    BeadStatusViolation,
    BeadType,
    ImmutabilityViolation,
)
from .observer import (
    CSONotReadyError,
    CSOObserver,
    CSOWriteViolation,
)

__all__ = [
    # Structure detection
    "StructureDetector",
    "FVG",
    "BOS",
    "CHoCH",
    "OTE",
    "LiquiditySweep",
    # Strategy
    "StrategyCore",
    "Setup",
    "SetupResult",
    # Scanner
    "CSOScanner",
    # Params
    "ParamsLoader",
    "CSOParams",
    # Beads
    "Bead",
    "BeadFactory",
    "BeadStatus",
    "BeadStatusViolation",
    "BeadType",
    "ImmutabilityViolation",
    # Observer
    "CSOObserver",
    "CSONotReadyError",
    "CSOWriteViolation",
]
