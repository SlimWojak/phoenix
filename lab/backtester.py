"""
Backtester — Deterministic Strategy Backtesting
================================================

Backtests HPG variants against River data.

INVARIANTS:
- INV-HUNT-DET-1: Identical HPG + data_window → identical results
- INV-HUNT-SORT-1: Results sorted by variant_id before filtering

Data source: RiverReader (read-only)
Determinism: Fixed random_seed from HPG
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from .hpg_parser import HPG, SignalType

if TYPE_CHECKING:
    pass


# =============================================================================
# RESULT TYPES
# =============================================================================


@dataclass
class Trade:
    """Single simulated trade."""

    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    direction: str  # LONG or SHORT
    pnl_pips: float
    pnl_percent: float
    win: bool


@dataclass
class BacktestResult:
    """Result of backtesting a single HPG variant."""

    variant_id: str
    hpg_hash: str
    data_window_hash: str

    # Metrics
    sharpe: float
    win_rate: float
    profit_factor: float
    max_drawdown: float
    total_trades: int
    total_pnl_percent: float

    # Trade details (optional)
    trades: list[Trade] = field(default_factory=list)

    # Metadata
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "variant_id": self.variant_id,
            "hpg_hash": self.hpg_hash,
            "sharpe": self.sharpe,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "max_drawdown": self.max_drawdown,
            "total_trades": self.total_trades,
            "total_pnl_percent": self.total_pnl_percent,
        }


@dataclass
class DataWindow:
    """Data window specification."""

    start: datetime
    end: datetime

    def compute_hash(self) -> str:
        """Compute deterministic hash of data window."""
        data = json.dumps(
            {"start": self.start.isoformat(), "end": self.end.isoformat()},
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @classmethod
    def default(cls, days: int = 90) -> DataWindow:
        """Create default data window (last N days)."""
        end = datetime.now(UTC)
        start = end - timedelta(days=days)
        return cls(start=start, end=end)


# =============================================================================
# BACKTESTER
# =============================================================================


class Backtester:
    """
    Backtests HPG variants against River data.

    INVARIANT: INV-HUNT-DET-1
    Identical (HPG + data_window) → identical results.
    Determinism achieved via:
    - Fixed random_seed from HPG
    - Sorted data processing
    - No floating point randomness
    """

    def __init__(self, river_reader: object | None = None) -> None:
        """
        Initialize backtester.

        Args:
            river_reader: RiverReader instance (optional, uses mock if None)
        """
        self._river = river_reader

    def run(
        self,
        hpg: HPG,
        variant_id: str,
        data_window: DataWindow,
    ) -> BacktestResult:
        """
        Run backtest for a single HPG variant.

        Args:
            hpg: Hunt Parameter Grammar
            variant_id: Unique variant identifier
            data_window: Time range for backtest

        Returns:
            BacktestResult with metrics
        """
        import time

        start_time = time.perf_counter()

        # Get data (mock for now)
        bars = self._get_bars(hpg.pair, data_window)

        # Find signals
        signals = self._find_signals(bars, hpg)

        # Simulate trades
        trades = self._simulate_trades(signals, bars, hpg)

        # Calculate metrics
        metrics = self._calculate_metrics(trades)

        execution_time = (time.perf_counter() - start_time) * 1000

        return BacktestResult(
            variant_id=variant_id,
            hpg_hash=hpg.compute_hash(),
            data_window_hash=data_window.compute_hash(),
            sharpe=metrics["sharpe"],
            win_rate=metrics["win_rate"],
            profit_factor=metrics["profit_factor"],
            max_drawdown=metrics["max_drawdown"],
            total_trades=len(trades),
            total_pnl_percent=metrics["total_pnl"],
            trades=trades,
            execution_time_ms=execution_time,
        )

    def run_batch(
        self,
        variants: list[tuple[HPG, str]],
        data_window: DataWindow,
    ) -> list[BacktestResult]:
        """
        Run backtest for multiple variants.

        Results are SORTED by variant_id for determinism (INV-HUNT-SORT-1).

        Args:
            variants: List of (HPG, variant_id) tuples
            data_window: Time range for backtest

        Returns:
            Sorted list of BacktestResults
        """
        results = []
        for hpg, variant_id in variants:
            result = self.run(hpg, variant_id, data_window)
            results.append(result)

        # Sort by variant_id for determinism (INV-HUNT-SORT-1)
        results.sort(key=lambda r: r.variant_id)

        return results

    def _get_bars(self, pair: str, window: DataWindow) -> list[dict]:
        """
        Get price bars from River.

        Returns mock data for now (real implementation uses RiverReader).
        """
        if self._river:
            # Real implementation
            # df = self._river.get_bars(pair, "1H", window.start, window.end)
            # return df.to_dict('records')
            pass

        # Mock data generation (deterministic)
        return self._generate_mock_bars(pair, window)

    def _generate_mock_bars(self, pair: str, window: DataWindow) -> list[dict]:
        """Generate deterministic mock bar data."""
        import random

        # Seed from pair + window for determinism
        seed_data = f"{pair}_{window.start.isoformat()}_{window.end.isoformat()}"
        seed = int(hashlib.sha256(seed_data.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)

        bars = []
        current = window.start
        price = 1.1000 if "USD" in pair else 150.0  # Base price

        while current < window.end:
            # Deterministic price movement
            change = rng.gauss(0, 0.0010)
            price = max(0.5, price + change)

            bar = {
                "timestamp": current,
                "open": price,
                "high": price + abs(rng.gauss(0, 0.0005)),
                "low": price - abs(rng.gauss(0, 0.0005)),
                "close": price + rng.gauss(0, 0.0003),
                "volume": rng.randint(100, 1000),
            }
            bars.append(bar)
            current += timedelta(hours=1)

        return bars

    def _find_signals(self, bars: list[dict], hpg: HPG) -> list[dict]:
        """
        Find signals in bar data based on HPG parameters.

        Mock implementation — real implementation uses enrichment layers.
        """
        import random

        signals = []

        # Seed from HPG for determinism
        rng = random.Random(hpg.random_seed)

        for i, bar in enumerate(bars):
            # Skip first few bars
            if i < 10:
                continue

            # Deterministic signal probability based on HPG
            prob = 0.02  # Base probability

            # Adjust by signal type
            if hpg.signal_type == SignalType.FVG:
                prob = 0.03
            elif hpg.signal_type == SignalType.BOS:
                prob = 0.025

            # Deterministic signal generation
            if rng.random() < prob:
                direction = "LONG" if rng.random() > 0.5 else "SHORT"
                signals.append(
                    {
                        "bar_index": i,
                        "timestamp": bar["timestamp"],
                        "price": bar["close"],
                        "direction": direction,
                        "signal_type": hpg.signal_type.value,
                    }
                )

        return signals

    def _simulate_trades(
        self, signals: list[dict], bars: list[dict], hpg: HPG
    ) -> list[Trade]:
        """Simulate trades from signals."""
        import random

        trades = []
        rng = random.Random(hpg.random_seed + 1000)  # Different seed for exits

        for signal in signals:
            bar_idx = signal["bar_index"]

            # Skip if not enough bars for exit
            if bar_idx + 10 >= len(bars):
                continue

            entry_price = signal["price"]
            direction = signal["direction"]

            # Calculate stop based on stop_model
            if hpg.stop_model.value == "TIGHT":
                stop_pips = 15
            elif hpg.stop_model.value == "WIDE":
                stop_pips = 40
            else:
                stop_pips = 25

            # Simulate exit (deterministic based on subsequent bars)
            exit_bar_idx = bar_idx + rng.randint(3, 10)
            exit_bar = bars[min(exit_bar_idx, len(bars) - 1)]
            exit_price = exit_bar["close"]

            # Calculate P&L
            if direction == "LONG":
                pnl_pips = (exit_price - entry_price) * 10000
            else:
                pnl_pips = (entry_price - exit_price) * 10000

            pnl_percent = pnl_pips * hpg.risk_percent / stop_pips
            win = pnl_pips > 0

            trade = Trade(
                entry_time=signal["timestamp"],
                exit_time=exit_bar["timestamp"],
                entry_price=entry_price,
                exit_price=exit_price,
                direction=direction,
                pnl_pips=pnl_pips,
                pnl_percent=pnl_percent,
                win=win,
            )
            trades.append(trade)

        return trades

    def _calculate_metrics(self, trades: list[Trade]) -> dict:
        """Calculate backtest metrics from trades."""
        if not trades:
            return {
                "sharpe": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "total_pnl": 0.0,
            }

        # Win rate
        wins = sum(1 for t in trades if t.win)
        win_rate = wins / len(trades)

        # P&L
        returns = [t.pnl_percent for t in trades]
        total_pnl = sum(returns)

        # Profit factor
        gross_profit = sum(r for r in returns if r > 0)
        gross_loss = abs(sum(r for r in returns if r < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Sharpe (simplified)
        if len(returns) > 1:
            import statistics

            mean_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            sharpe = (mean_return / std_return) * (252**0.5) if std_return > 0 else 0.0
        else:
            sharpe = 0.0

        # Max drawdown
        equity = 0.0
        peak = 0.0
        max_dd = 0.0
        for r in returns:
            equity += r
            peak = max(peak, equity)
            dd = (peak - equity) / max(peak, 1.0)
            max_dd = max(max_dd, dd)

        return {
            "sharpe": round(sharpe, 3),
            "win_rate": round(win_rate, 3),
            "profit_factor": round(profit_factor, 3),
            "max_drawdown": round(max_dd, 3),
            "total_pnl": round(total_pnl, 3),
        }
