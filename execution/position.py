"""
DEPRECATED — S52 HARDENING (RISK-1: Dual Position State Machine)

This module has been relocated. Use the canonical imports:

  Production (10-state FSM with T2 gates):
    from execution.positions import Position, PositionState, PositionLifecycle

  Paper broker (5-state simplified FSM):
    from execution.positions.paper import PaperPosition, PaperPositionState

See FORENSIC_AUDIT.md Section 8 DELTA-6, Section 10 RISK-1.
"""

raise ImportError(
    "execution.position is DEPRECATED (S52 RISK-1 fix). "
    "Use 'from execution.positions import ...' for production FSM, "
    "or 'from execution.positions.paper import ...' for paper broker FSM."
)
