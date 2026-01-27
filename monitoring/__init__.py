"""
Phoenix Monitoring Module — Decay Detection
============================================

Multi-signal decay detection with ONE-WAY-KILL trigger.

Components:
- Signalman: Decay detection across signals
- KillManager: Kill flag management via BeadStore
- StateAnchor: State binding for T2 intents

INVARIANTS:
- INV-SIGNALMAN-COLD-1: No decay alerts until min_beads_for_analysis reached
- INV-SIGNALMAN-DECAY-1: Multi-signal decay triggers ONE-WAY-KILL
- INV-STATE-ANCHOR-1: T2 intents require valid state_hash
"""

from .kill_manager import KillFlag, KillManager
from .signalman import DecayAlert, DecayType, Signalman
from .state_anchor import StateAnchor, StateAnchorManager

__all__ = [
    "Signalman",
    "DecayAlert",
    "DecayType",
    "KillManager",
    "KillFlag",
    "StateAnchor",
    "StateAnchorManager",
]
