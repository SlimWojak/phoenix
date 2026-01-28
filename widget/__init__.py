"""
Phoenix Widget Module — Surface Renderer POC
=============================================

S34: D4 SURFACE_RENDERER_POC

UI is projection of state, not participant in reasoning.

INVARIANTS:
- INV-D4-GLANCEABLE-1: Update <100ms
- INV-D4-ACCURATE-1: Matches actual state
- INV-D4-NO-ACTIONS-1: Read-only, no actions
- INV-D4-NO-DERIVATION-1: Every field verbatim from OrientationBead
- INV-D4-EPHEMERAL-1: Renderer must not persist state locally
"""

from .surface_renderer import (
    RenderState,
    SurfaceRenderer,
)

__all__ = [
    "SurfaceRenderer",
    "RenderState",
]
