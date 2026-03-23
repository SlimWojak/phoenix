"""
Ghost Bar Canonical Policy — INV-GHOST-CANON
=============================================

DEPLOY.P0.4 — Defines and enforces ghost bar behavior across River consumers.

POLICY:
  Phoenix Reader: Ghost injection ON (enrichment requires continuous 1m series).
  Dexter Adapter: Ghost injection OFF (analytical claims must not contain synthetic data).
  RA Adapter: Ghost injection OFF (flags volume==0, no injection).

  This is an INTENTIONAL divergence. Phoenix and Dexter serve different purposes:
  - Phoenix enrichment layers (L1-L7) expect continuous bars for rolling window
    calculations (e.g., swing detection needs N consecutive bars).
  - Dexter produces CLAIMs from real market observations only.

INV-GHOST-CANON:
  "For any time window, bar count divergence between consumers is EXPECTED
  and must be validated at adapter boundaries. Any adapter that bridges
  Phoenix and Dexter data must validate bar count alignment or explicitly
  document the expected divergence."

INVARIANT ENFORCEMENT:
  The validate_bar_count_alignment() function checks that the non-ghost bar count
  from Phoenix matches Dexter's total bar count for the same time window.
  If they differ, the adapter must handle the mismatch explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

GHOST_POLICY_VERSION = "1.0"

PHOENIX_GHOST_INJECTION = True
DEXTER_GHOST_INJECTION = False


@dataclass(frozen=True)
class BarCountAlignment:
    """Result of bar count alignment check between two consumers."""

    start: datetime
    end: datetime
    phoenix_total: int
    phoenix_real: int
    phoenix_ghost: int
    dexter_total: int
    aligned: bool
    divergence: int
    message: str


def validate_bar_count_alignment(
    phoenix_total: int,
    phoenix_ghost: int,
    dexter_total: int,
    start: datetime,
    end: datetime,
) -> BarCountAlignment:
    """
    Validate bar count alignment between Phoenix and Dexter for a time window.

    Phoenix real bars (total - ghost) should equal Dexter total bars.
    Divergence beyond this indicates a data integrity issue.

    Returns:
        BarCountAlignment with diagnostic information
    """
    phoenix_real = phoenix_total - phoenix_ghost

    aligned = phoenix_real == dexter_total
    divergence = abs(phoenix_real - dexter_total)

    if aligned:
        msg = f"ALIGNED: {phoenix_real} real bars match Dexter {dexter_total} bars"
    else:
        msg = (
            f"DIVERGENCE: Phoenix {phoenix_real} real bars "
            f"(of {phoenix_total} total, {phoenix_ghost} ghost) "
            f"vs Dexter {dexter_total} bars — delta={divergence}"
        )

    return BarCountAlignment(
        start=start,
        end=end,
        phoenix_total=phoenix_total,
        phoenix_real=phoenix_real,
        phoenix_ghost=phoenix_ghost,
        dexter_total=dexter_total,
        aligned=aligned,
        divergence=divergence,
        message=msg,
    )


__all__ = [
    "GHOST_POLICY_VERSION",
    "PHOENIX_GHOST_INJECTION",
    "DEXTER_GHOST_INJECTION",
    "BarCountAlignment",
    "validate_bar_count_alignment",
]
