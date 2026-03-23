"""
Intent Adapter — DEPLOY.P1.2
=============================

Pure function: TradeProposal → ExecutionIntent.
Bridges the two execution vocabularies.

INV-CONTRACT-1: Same signal + same MarketState → same intent_hash.
INV-BUILDER-PURE-ADAPTER: Maps fields only. No scoring/inference.
"""

from __future__ import annotations

from cso.evaluator import MarketState
from execution.asia_scalp import TradeDirection, TradeProposal
from execution.intent import (
    Direction,
    ExecutionIntent,
    IntentFactory,
)

_DIRECTION_MAP: dict[TradeDirection, Direction] = {
    TradeDirection.LONG: Direction.LONG,
    TradeDirection.SHORT: Direction.SHORT,
}

_factory = IntentFactory(source_module="ARS")


def adapt_proposal_to_intent(
    proposal: TradeProposal,
    symbol: str,
    market_state: MarketState,
    source_bead_id: str | None = None,
    ttl_minutes: int = 60,
) -> ExecutionIntent:
    """
    Convert a TradeProposal into an ExecutionIntent.

    INV-CONTRACT-1: Deterministic — same inputs → same intent_hash.
    INV-BUILDER-PURE-ADAPTER: Field mapping only.

    Args:
        proposal: Validated TradeProposal from strategy evaluator
        symbol: Trading pair (e.g. "EURUSD")
        market_state: MarketState used for evaluation (provides state hash)
        source_bead_id: Optional provenance bead ID
        ttl_minutes: Intent time-to-live

    Returns:
        Frozen ExecutionIntent with deterministic hash
    """
    direction = _DIRECTION_MAP[proposal.direction]
    state_hash = market_state.compute_hash()

    return _factory.create_entry_intent(
        symbol=symbol,
        direction=direction,
        size=proposal.position_size_lots,
        state_hash=state_hash,
        bead_id=source_bead_id,
        entry_price=proposal.entry_price,
        stop_loss=proposal.stop_loss,
        take_profit=proposal.take_profit,
        ttl_minutes=ttl_minutes,
    )


def reset_factory(source_module: str = "ARS") -> None:
    """Reset the factory counter (for testing determinism)."""
    global _factory
    _factory = IntentFactory(source_module=source_module)


__all__ = [
    "adapt_proposal_to_intent",
    "reset_factory",
]
