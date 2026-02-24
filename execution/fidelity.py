"""
Execution Fidelity Record — INV-EXECUTION-FIDELITY.

Emitted after every fill. Tracks intent vs actual execution delta.

INV-EXECUTION-FIDELITY: Intent vs fill delta tracked. >50bps = alert.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

SLIPPAGE_ALERT_BPS: float = 50.0


@dataclass(frozen=True)
class FidelityRecord:
    """Immutable execution fidelity receipt."""

    intent_id: str
    expected_price: float
    actual_price: float
    slippage_abs: float
    slippage_bps: float
    venue: str
    knowledge_time: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def alert(self) -> bool:
        """INV-EXECUTION-FIDELITY: >50bps triggers alert."""
        return abs(self.slippage_bps) > SLIPPAGE_ALERT_BPS


def compute_fidelity(
    intent_id: str,
    expected_price: float,
    actual_price: float,
    venue: str = "PAPER",
) -> FidelityRecord:
    """Build FidelityRecord from fill data."""
    slippage_abs = actual_price - expected_price
    slippage_bps = (slippage_abs / expected_price) * 10_000 if expected_price else 0.0

    record = FidelityRecord(
        intent_id=intent_id,
        expected_price=expected_price,
        actual_price=actual_price,
        slippage_abs=slippage_abs,
        slippage_bps=slippage_bps,
        venue=venue,
    )

    if record.alert:
        logger.warning(
            "INV-EXECUTION-FIDELITY: slippage %.1fbps intent=%s expected=%.5f actual=%.5f",
            slippage_bps,
            intent_id,
            expected_price,
            actual_price,
        )

    return record
