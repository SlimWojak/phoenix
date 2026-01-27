"""
Shadow — Paper Trading Engine
==============================

CSE consumer + paper position tracking + divergence analysis.

INVARIANTS:
- INV-SHADOW-ISO-1: NEVER affects live capital
- INV-SHADOW-CSE-1: Only consumes validated CSE signals
- INV-SHADOW-BEAD-1: Emits PERFORMANCE beads

DESIGN:
1. Receives CSE signal
2. Creates paper position
3. Tracks position lifecycle
4. Emits PERFORMANCE bead on close
5. Tracks divergence (paper vs live)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .paper_position import (
    PaperPosition,
    PositionState,
    create_paper_position,
)

# Import BeadStore for bead emission
try:
    from memory.bead_store import BeadStore
except ImportError:
    BeadStore = None  # type: ignore[misc, assignment]


# =============================================================================
# CONFIG
# =============================================================================


@dataclass
class ShadowConfig:
    """Shadow engine configuration."""

    initial_balance: float = 10000.0
    max_positions: int = 5
    max_risk_per_trade: float = 2.0  # Max 2% per trade
    enable_bead_emission: bool = True


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CSESignal:
    """Canonical Signal Envelope (for consumption)."""

    signal_id: str
    timestamp: datetime
    pair: str
    direction: str  # LONG or SHORT
    entry: float
    stop: float
    target: float
    risk_percent: float
    confidence: float
    source: str  # e.g., "HUNT", "MANUAL"
    evidence_hash: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CSESignal:
        """Create from dictionary."""
        return cls(
            signal_id=data["signal_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            pair=data["pair"],
            direction=data["direction"],
            entry=data["parameters"]["entry"],
            stop=data["parameters"]["stop"],
            target=data["parameters"]["target"],
            risk_percent=data["parameters"]["risk_percent"],
            confidence=data.get("confidence", 0.5),
            source=data.get("source", "unknown"),
            evidence_hash=data.get("evidence_hash", ""),
        )


@dataclass
class ShadowResult:
    """Result of shadow operation."""

    status: str  # ACCEPTED, REJECTED, CLOSED
    position_id: str | None = None
    message: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass
class DivergenceRecord:
    """Record of paper vs live divergence."""

    position_id: str
    signal_id: str
    paper_result: float  # Paper P&L
    live_result: float | None  # Live P&L (None if not tracked)
    divergence: float | None  # paper - live
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# SHADOW ENGINE
# =============================================================================


class Shadow:
    """
    Shadow (Paper) Trading Engine.

    Consumes CSE signals, manages paper positions, tracks performance.

    INVARIANT: INV-SHADOW-ISO-1 — Paper only, no live capital
    """

    def __init__(
        self,
        config: ShadowConfig | None = None,
        bead_store: Any | None = None,
        autopsy: Any | None = None,
    ) -> None:
        """
        Initialize shadow engine.

        Args:
            config: Shadow configuration
            bead_store: BeadStore for PERFORMANCE beads
            autopsy: Autopsy engine for post-trade analysis (WIRING)
        """
        self._config = config or ShadowConfig()
        self._bead_store = bead_store
        self._autopsy = autopsy

        # State
        self._balance = self._config.initial_balance
        self._positions: dict[str, PaperPosition] = {}  # position_id -> position
        self._closed_positions: list[PaperPosition] = []

        # Performance tracking
        self._total_pnl = 0.0
        self._total_trades = 0
        self._winning_trades = 0

        # Divergence tracking (paper vs live)
        self._divergence_log: list[DivergenceRecord] = []

    @property
    def balance(self) -> float:
        """Current paper balance."""
        return self._balance

    @property
    def open_positions(self) -> list[PaperPosition]:
        """List of open positions."""
        return [p for p in self._positions.values() if p.state == PositionState.OPEN]

    @property
    def stats(self) -> dict[str, Any]:
        """Performance statistics."""
        win_rate = (
            self._winning_trades / self._total_trades
            if self._total_trades > 0 else 0.0
        )
        return {
            "balance": self._balance,
            "initial_balance": self._config.initial_balance,
            "total_pnl": self._total_pnl,
            "total_trades": self._total_trades,
            "winning_trades": self._winning_trades,
            "win_rate": win_rate,
            "open_positions": len(self.open_positions),
        }

    def consume_signal(self, signal: CSESignal) -> ShadowResult:
        """
        Consume CSE signal and create paper position.

        INVARIANT: INV-SHADOW-CSE-1 — Only validated signals

        Args:
            signal: CSE signal to consume

        Returns:
            ShadowResult
        """
        # Validate signal
        errors = self._validate_signal(signal)
        if errors:
            return ShadowResult(
                status="REJECTED",
                message="Signal validation failed",
                errors=errors,
            )

        # Check position limits
        if len(self.open_positions) >= self._config.max_positions:
            return ShadowResult(
                status="REJECTED",
                message=f"Max positions ({self._config.max_positions}) reached",
            )

        # Create paper position
        position = create_paper_position(
            signal_id=signal.signal_id,
            pair=signal.pair,
            side=signal.direction,
            entry_price=signal.entry,
            stop_price=signal.stop,
            target_price=signal.target,
            risk_percent=min(signal.risk_percent, self._config.max_risk_per_trade),
            account_balance=self._balance,
        )

        # Open position immediately (paper trading)
        position.open_position(signal.entry)

        # Track position
        self._positions[position.position_id] = position

        return ShadowResult(
            status="ACCEPTED",
            position_id=position.position_id,
            message=f"Paper position opened: {position.pair} {position.side.value}",
        )

    def update_prices(self, prices: dict[str, float]) -> list[ShadowResult]:
        """
        Update with current prices, check stops/targets.

        Args:
            prices: Dict of pair -> current_price

        Returns:
            List of ShadowResults for closed positions
        """
        results: list[ShadowResult] = []

        for position in list(self.open_positions):
            if position.pair not in prices:
                continue

            current_price = prices[position.pair]
            close_result = position.check_stops(current_price)

            if close_result is not None:
                # Position was closed
                self._handle_closed_position(position)

                results.append(ShadowResult(
                    status="CLOSED",
                    position_id=position.position_id,
                    message=(
                        f"Closed {position.pair}: {close_result.pnl_pips:.1f} pips "
                        f"({position.exit_reason})"
                    ),
                ))

        return results

    def close_position(
        self,
        position_id: str,
        exit_price: float,
        reason: str = "manual",
    ) -> ShadowResult:
        """
        Manually close a position.

        Args:
            position_id: Position to close
            exit_price: Exit price
            reason: Close reason

        Returns:
            ShadowResult
        """
        if position_id not in self._positions:
            return ShadowResult(
                status="REJECTED",
                message=f"Position {position_id} not found",
            )

        position = self._positions[position_id]
        result = position.close_position(exit_price, reason)

        if result.errors:
            return ShadowResult(
                status="REJECTED",
                position_id=position_id,
                errors=result.errors,
            )

        self._handle_closed_position(position)

        return ShadowResult(
            status="CLOSED",
            position_id=position_id,
            message=f"Closed: {result.pnl_pips:.1f} pips ({reason})",
        )

    def record_live_result(
        self,
        position_id: str,
        live_pnl: float,
    ) -> DivergenceRecord | None:
        """
        Record live result for divergence tracking.

        Args:
            position_id: Paper position ID
            live_pnl: Actual live P&L

        Returns:
            DivergenceRecord or None if position not found
        """
        # Find in closed positions
        position = next(
            (p for p in self._closed_positions if p.position_id == position_id),
            None,
        )

        if position is None:
            return None

        record = DivergenceRecord(
            position_id=position_id,
            signal_id=position.signal_id,
            paper_result=position.realized_pnl,
            live_result=live_pnl,
            divergence=position.realized_pnl - live_pnl,
        )

        self._divergence_log.append(record)
        return record

    def _validate_signal(self, signal: CSESignal) -> list[str]:
        """Validate CSE signal."""
        errors: list[str] = []

        if not signal.signal_id:
            errors.append("signal_id required")

        if signal.risk_percent <= 0 or signal.risk_percent > 10:
            errors.append("risk_percent must be 0-10%")

        if signal.entry <= 0:
            errors.append("Invalid entry price")

        if signal.direction not in ("LONG", "SHORT"):
            errors.append(f"Invalid direction: {signal.direction}")

        # Validate stop/target relationship
        if signal.direction == "LONG":
            if signal.stop >= signal.entry:
                errors.append("Stop must be below entry for LONG")
            if signal.target <= signal.entry:
                errors.append("Target must be above entry for LONG")
        else:
            if signal.stop <= signal.entry:
                errors.append("Stop must be above entry for SHORT")
            if signal.target >= signal.entry:
                errors.append("Target must be below entry for SHORT")

        return errors

    def _handle_closed_position(self, position: PaperPosition) -> None:
        """Handle position closure: update stats, emit bead, trigger autopsy."""
        # Update stats
        self._total_trades += 1
        self._total_pnl += position.realized_pnl
        self._balance += position.realized_pnl

        if position.realized_pnl > 0:
            self._winning_trades += 1

        # Move to closed
        self._closed_positions.append(position)
        if position.position_id in self._positions:
            del self._positions[position.position_id]

        # Emit PERFORMANCE bead (INV-SHADOW-BEAD-1)
        if self._config.enable_bead_emission:
            self._emit_performance_bead(position)

        # WIRING: Shadow → Autopsy
        self._trigger_autopsy(position)

    def _trigger_autopsy(self, position: PaperPosition) -> None:
        """
        Trigger autopsy analysis for closed position.

        WIRING: Shadow → Autopsy
        """
        if self._autopsy is None:
            return

        try:
            # Build entry thesis from position
            risk_pct = getattr(position, "initial_risk_percent", 1.0)
            entry_thesis = {
                "confidence": min(risk_pct / 2.0, 1.0),  # Approx
                "setup_type": "CSO_SIGNAL",
                "reasoning_hash": "",
            }

            # Build outcome
            pnl = getattr(position, "realized_pnl", 0)
            result = "WIN" if pnl > 0 else "LOSS"
            if abs(pnl) < 0.01:
                result = "BREAKEVEN"

            # Calculate pnl_percent safely
            size = getattr(position, "size", 1.0) or 1.0
            entry = getattr(position, "entry_price", 1.0) or 1.0
            position_value = size * entry if size and entry else 1.0
            pnl_percent = (pnl / position_value * 100) if position_value else 0

            outcome = {
                "result": result,
                "pnl_percent": pnl_percent,
                "duration": "PT24H",  # Would calculate actual duration
            }

            # Trigger autopsy (async/non-blocking)
            self._autopsy.analyze(
                position_id=position.position_id,
                entry_thesis=entry_thesis,
                outcome=outcome,
            )
        except Exception:  # noqa: S110
            pass  # Non-blocking - autopsy is supplementary

    def _emit_performance_bead(self, position: PaperPosition) -> None:
        """Emit PERFORMANCE bead for closed position."""
        bead_id = f"PERF-{uuid.uuid4().hex[:8]}"
        now = datetime.now(UTC)

        # Build content (nested under 'content' for BeadStore)
        content = {
            "position": position.to_dict(),
            "metrics": {
                "pnl": position.realized_pnl,
                "pnl_pips": position.realized_pnl_pips,
                "exit_reason": position.exit_reason,
            },
            "cumulative": {
                "balance": self._balance,
                "total_pnl": self._total_pnl,
                "total_trades": self._total_trades,
                "win_rate": (
                    self._winning_trades / self._total_trades
                    if self._total_trades > 0 else 0.0
                ),
            },
        }

        # Compute hash
        bead_hash = hashlib.sha256(
            json.dumps(content, sort_keys=True).encode()
        ).hexdigest()[:16]

        bead_dict = {
            "bead_id": bead_id,
            "bead_type": "PERFORMANCE",
            "prev_bead_id": None,
            "bead_hash": bead_hash,
            "timestamp_utc": now.isoformat(),
            "signer": "system",
            "version": "1.0",
            "content": content,
        }

        # Store bead
        if self._bead_store is not None:
            try:
                self._bead_store.write_dict(bead_dict)
            except Exception:  # noqa: S110
                pass  # Non-blocking
