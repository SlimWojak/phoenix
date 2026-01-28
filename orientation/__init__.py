"""
Phoenix Orientation Module — System State Checksum
===================================================

S34: D3 ORIENTATION_BEAD_CHECKSUM

Machine-verifiable orientation for fresh sessions.
Checksum, not briefing. Verification, not understanding.

INVARIANTS:
- INV-D3-CHECKSUM-1: All fields machine-verifiable, no prose
- INV-D3-CROSS-CHECK-1: Every field verifiable against source
- INV-D3-CORRUPTION-1: Corruption → STATE_CONFLICT
- INV-D3-NO-DERIVED-1: No interpreted/summary fields
"""

from .generator import (
    ExecutionPhase,
    HeartbeatStatusEnum,
    ModeEnum,
    OrientationBead,
    OrientationGenerator,
)
from .validator import (
    ConflictCode,
    OrientationValidator,
    ValidationResult,
)

__all__ = [
    # Generator
    "OrientationGenerator",
    "OrientationBead",
    "ExecutionPhase",
    "ModeEnum",
    "HeartbeatStatusEnum",
    # Validator
    "OrientationValidator",
    "ValidationResult",
    "ConflictCode",
]
