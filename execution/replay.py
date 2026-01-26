"""
Replay Harness — Deterministic replay for execution testing.

SPRINT: S28.C
STATUS: MOCK_SIGNALS
CAPITAL: PAPER_ONLY

Process:
1. Feed historical price data
2. Generate mock signals (synthetic, NOT Olya methodology)
3. Signal → Intent → Broker Stub → Position → P&L
4. Verify determinism (same data + same signals = same result)

CONSTRAINTS:
- MOCK_SIGNALS mode (synthetic patterns only)
- Deterministic (same replay = same output hash)
- Halt-integrated (halt stops replay cleanly)

INVARIANTS:
- INV-CONTRACT-1: deterministic (hash match on repeat)
- INV-GOV-HALT-BEFORE-ACTION: halt respected
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, List, Callable, Generator
from enum import Enum
import hashlib
import json

from .intent import ExecutionIntent, IntentFactory, IntentType, IntentStatus, Direction
from .broker_stub import PaperBrokerStub, OrderResult, ExitResult
from .position import Position, PositionState


# =============================================================================
# REPLAY STATE
# =============================================================================

class ReplayState(Enum):
    """State of replay execution."""
    IDLE = "IDLE"           # Not started
    RUNNING = "RUNNING"     # Replay in progress
    PAUSED = "PAUSED"       # Paused (can resume)
    HALTED = "HALTED"       # System halt triggered
    COMPLETED = "COMPLETED" # Finished
    ERROR = "ERROR"         # Error occurred


# =============================================================================
# MOCK SIGNAL GENERATOR
# =============================================================================

@dataclass
class MockSignal:
    """
    Mock trading signal for testing.
    
    NOTE: These are SYNTHETIC signals for S28.C testing.
    NOT Olya methodology.
    """
    signal_id: str
    timestamp: datetime
    signal_type: str        # "ENTRY_LONG", "ENTRY_SHORT", "EXIT"
    symbol: str
    price: float
    size: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'signal_id': self.signal_id,
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type,
            'symbol': self.symbol,
            'price': self.price,
            'size': self.size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
        }


class MockSignalGenerator:
    """
    Generate mock signals for testing execution flow.
    
    S28.C: Synthetic patterns only — NOT Olya methodology.
    
    Patterns:
    - FIXED: Signal at fixed intervals
    - ALTERNATING: Alternate long/short
    - RANDOM_SEED: Pseudo-random based on seed (deterministic)
    """
    
    def __init__(self, symbol: str = "TEST/USD", seed: int = 42):
        self.symbol = symbol
        self.seed = seed
        self._counter = 0
        self._state = "neutral"  # "neutral", "long", "short"
        self._rng_state = seed
    
    def _next_random(self) -> float:
        """Deterministic pseudo-random number generator."""
        # Linear congruential generator (deterministic)
        self._rng_state = (self._rng_state * 1103515245 + 12345) % (2 ** 31)
        return (self._rng_state % 1000) / 1000.0
    
    def generate_from_prices(
        self,
        prices: List[Dict],
        entry_threshold: float = 0.001,
        exit_after_bars: int = 10
    ) -> List[MockSignal]:
        """
        Generate signals from price data.
        
        Simple momentum strategy (for testing):
        - Entry when price moves > threshold from previous
        - Exit after N bars
        
        Args:
            prices: List of {'timestamp': datetime, 'close': float}
            entry_threshold: Price move threshold for entry
            exit_after_bars: Bars to hold before exit
        
        Returns:
            List of MockSignal
        """
        signals = []
        position_bar = None
        
        for i, bar in enumerate(prices):
            self._counter += 1
            
            if i == 0:
                continue
            
            prev_close = prices[i - 1]['close']
            curr_close = bar['close']
            price_change = (curr_close - prev_close) / prev_close
            
            # Generate entry signal
            if self._state == "neutral" and abs(price_change) > entry_threshold:
                signal_type = "ENTRY_LONG" if price_change > 0 else "ENTRY_SHORT"
                signals.append(MockSignal(
                    signal_id=f"SIG-{self._counter:04d}",
                    timestamp=bar['timestamp'],
                    signal_type=signal_type,
                    symbol=self.symbol,
                    price=curr_close,
                    size=1.0,
                ))
                self._state = "long" if price_change > 0 else "short"
                position_bar = i
            
            # Generate exit signal
            elif self._state != "neutral" and position_bar is not None:
                if i - position_bar >= exit_after_bars:
                    signals.append(MockSignal(
                        signal_id=f"SIG-{self._counter:04d}",
                        timestamp=bar['timestamp'],
                        signal_type="EXIT",
                        symbol=self.symbol,
                        price=curr_close,
                    ))
                    self._state = "neutral"
                    position_bar = None
        
        return signals
    
    def generate_fixed_pattern(
        self,
        count: int,
        base_price: float = 1.0,
        interval_bars: int = 10
    ) -> List[MockSignal]:
        """
        Generate fixed pattern signals (deterministic).
        
        Args:
            count: Number of signal pairs (entry + exit)
            base_price: Starting price
            interval_bars: Bars between signals
        
        Returns:
            List of MockSignal
        """
        signals = []
        price = base_price
        now = datetime.now(timezone.utc)
        
        for i in range(count):
            self._counter += 1
            
            # Entry signal
            direction = "LONG" if i % 2 == 0 else "SHORT"
            entry_price = price * (1 + self._next_random() * 0.01)
            signals.append(MockSignal(
                signal_id=f"SIG-{self._counter:04d}",
                timestamp=now,
                signal_type=f"ENTRY_{direction}",
                symbol=self.symbol,
                price=entry_price,
                size=1.0,
            ))
            
            self._counter += 1
            
            # Exit signal (after interval)
            exit_price = entry_price * (1 + (self._next_random() - 0.5) * 0.02)
            signals.append(MockSignal(
                signal_id=f"SIG-{self._counter:04d}",
                timestamp=now,
                signal_type="EXIT",
                symbol=self.symbol,
                price=exit_price,
            ))
            
            price = exit_price
        
        return signals
    
    def reset(self) -> None:
        """Reset generator state."""
        self._counter = 0
        self._state = "neutral"
        self._rng_state = self.seed


# =============================================================================
# REPLAY RESULT
# =============================================================================

@dataclass
class ReplayResult:
    """Result of replay execution."""
    success: bool
    state: ReplayState
    
    # Counts
    signals_processed: int
    orders_submitted: int
    positions_opened: int
    positions_closed: int
    
    # P&L (simplified v0)
    total_pnl: float
    
    # Determinism
    state_hash: str
    
    # Timing
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    
    # Halt (if applicable)
    halted_at_signal: Optional[int] = None
    halt_reason: Optional[str] = None
    
    # Errors
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'success': self.success,
            'state': self.state.value,
            'signals_processed': self.signals_processed,
            'orders_submitted': self.orders_submitted,
            'positions_opened': self.positions_opened,
            'positions_closed': self.positions_closed,
            'total_pnl': self.total_pnl,
            'state_hash': self.state_hash,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat(),
            'duration_ms': self.duration_ms,
            'halted_at_signal': self.halted_at_signal,
            'halt_reason': self.halt_reason,
            'errors': self.errors,
        }


# =============================================================================
# REPLAY HARNESS
# =============================================================================

class ReplayHarness:
    """
    Deterministic replay harness for execution testing.
    
    Flow:
    1. Load historical price data
    2. Generate mock signals (synthetic)
    3. Signal → Intent → Broker → Position → P&L
    4. Verify determinism via hash comparison
    
    REQUIREMENT: DETERMINISTIC
    Same data + same signals = same result.
    Proven via hash comparison.
    """
    
    def __init__(
        self,
        halt_signal_fn: Optional[Callable[[], bool]] = None,
        symbol: str = "TEST/USD"
    ):
        """
        Initialize replay harness.
        
        Args:
            halt_signal_fn: Function returning True if system halted
            symbol: Default symbol for testing
        """
        self._halt_fn = halt_signal_fn or (lambda: False)
        self._symbol = symbol
        
        # Components
        self._broker = PaperBrokerStub(
            halt_check_fn=self._halt_fn,
            current_price_fn=self._get_current_price
        )
        self._intent_factory = IntentFactory("REPLAY")
        self._signal_gen = MockSignalGenerator(symbol)
        
        # State
        self._state = ReplayState.IDLE
        self._current_price: Dict[str, float] = {}
        self._signals_processed = 0
        self._errors: List[str] = []
        
        # Position tracking for exits
        self._active_position_id: Optional[str] = None
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for symbol."""
        return self._current_price.get(symbol)
    
    def _check_halt(self) -> bool:
        """Check if system halted."""
        return self._halt_fn()
    
    def _process_signal(self, signal: MockSignal) -> Optional[str]:
        """
        Process a single signal.
        
        Args:
            signal: Mock signal to process
        
        Returns:
            Error message if failed, None if success
        """
        # Update current price
        self._current_price[signal.symbol] = signal.price
        
        # Check halt before action (INV-GOV-HALT-BEFORE-ACTION)
        if self._check_halt():
            self._state = ReplayState.HALTED
            return "System halted"
        
        if signal.signal_type in ("ENTRY_LONG", "ENTRY_SHORT"):
            # Create entry intent
            direction = Direction.LONG if "LONG" in signal.signal_type else Direction.SHORT
            
            # Skip if already in position
            if self._active_position_id is not None:
                return None  # Ignore entry when in position
            
            intent = self._intent_factory.create_entry_intent(
                symbol=signal.symbol,
                direction=direction,
                size=signal.size,
                state_hash=f"REPLAY-{self._signals_processed}",
                entry_price=signal.price,
                stop_loss=signal.stop_loss,
                take_profit=signal.take_profit,
            )
            
            # Submit to broker
            result = self._broker.submit_order(intent)
            if result.success:
                self._active_position_id = result.position_id
            else:
                return result.error
        
        elif signal.signal_type == "EXIT":
            # Exit active position
            if self._active_position_id is None:
                return None  # Ignore exit when no position
            
            result = self._broker.exit_position(
                position_id=self._active_position_id,
                exit_price=signal.price,
                reason="exit_signal"
            )
            if result.success:
                self._active_position_id = None
            else:
                return result.error
        
        return None
    
    def run(
        self,
        signals: List[MockSignal],
        halt_at_signal: Optional[int] = None
    ) -> ReplayResult:
        """
        Run replay with provided signals.
        
        Args:
            signals: List of mock signals to process
            halt_at_signal: Inject halt at this signal index (for testing)
        
        Returns:
            ReplayResult with outcome
        """
        import time
        
        self._state = ReplayState.RUNNING
        self._signals_processed = 0
        self._errors = []
        self._active_position_id = None
        
        started_at = datetime.now(timezone.utc)
        start_time = time.perf_counter()
        
        orders_submitted = 0
        
        for i, signal in enumerate(signals):
            # Check for injected halt (testing)
            if halt_at_signal is not None and i >= halt_at_signal:
                self._state = ReplayState.HALTED
                # Halt all positions
                self._broker.on_halt(f"INJECT-{i}")
                break
            
            # Check system halt
            if self._check_halt():
                self._state = ReplayState.HALTED
                self._broker.on_halt("SYSTEM")
                break
            
            # Process signal
            error = self._process_signal(signal)
            if error:
                self._errors.append(f"Signal {i}: {error}")
            else:
                if signal.signal_type in ("ENTRY_LONG", "ENTRY_SHORT"):
                    orders_submitted += 1
            
            self._signals_processed = i + 1
            
            # Check if halted during processing
            if self._state == ReplayState.HALTED:
                break
        
        # Finalize
        end_time = time.perf_counter()
        completed_at = datetime.now(timezone.utc)
        
        if self._state == ReplayState.RUNNING:
            self._state = ReplayState.COMPLETED
        
        # Get final stats
        positions = list(self._broker._registry._positions.values())
        opened = len([p for p in positions if p.state != PositionState.PENDING])
        closed = len([p for p in positions if p.state == PositionState.CLOSED])
        
        pnl = self._broker.get_total_pnl()
        
        return ReplayResult(
            success=(self._state == ReplayState.COMPLETED and len(self._errors) == 0),
            state=self._state,
            signals_processed=self._signals_processed,
            orders_submitted=orders_submitted,
            positions_opened=opened,
            positions_closed=closed,
            total_pnl=pnl['total'],
            state_hash=self._broker.get_state_hash(),
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=(end_time - start_time) * 1000,
            halted_at_signal=self._signals_processed if self._state == ReplayState.HALTED else None,
            halt_reason="halt_signal" if self._state == ReplayState.HALTED else None,
            errors=self._errors,
        )
    
    def run_from_prices(
        self,
        prices: List[Dict],
        entry_threshold: float = 0.001,
        exit_after_bars: int = 10
    ) -> ReplayResult:
        """
        Run replay generating signals from price data.
        
        Args:
            prices: List of {'timestamp': datetime, 'close': float}
            entry_threshold: Price move threshold for entry
            exit_after_bars: Bars to hold before exit
        
        Returns:
            ReplayResult
        """
        self._signal_gen.reset()
        signals = self._signal_gen.generate_from_prices(
            prices=prices,
            entry_threshold=entry_threshold,
            exit_after_bars=exit_after_bars
        )
        return self.run(signals)
    
    def reset(self) -> None:
        """Reset harness for new replay."""
        self._broker.reset()
        self._signal_gen.reset()
        self._state = ReplayState.IDLE
        self._current_price.clear()
        self._signals_processed = 0
        self._errors.clear()
        self._active_position_id = None
    
    def get_broker(self) -> PaperBrokerStub:
        """Get broker for inspection."""
        return self._broker
    
    def get_state_hash(self) -> str:
        """
        Get current state hash.
        
        INV-CONTRACT-1: Same state → same hash.
        """
        return self._broker.get_state_hash()


# =============================================================================
# DETERMINISM VERIFIER
# =============================================================================

class DeterminismVerifier:
    """
    Verify replay determinism.
    
    GATE_C2_DETERMINISTIC: same replay = same result.
    """
    
    @staticmethod
    def verify(
        harness_factory: Callable[[], ReplayHarness],
        signals: List[MockSignal],
        runs: int = 2
    ) -> Dict:
        """
        Verify determinism across multiple runs.
        
        Args:
            harness_factory: Function returning fresh ReplayHarness
            signals: Signals to replay
            runs: Number of runs to compare
        
        Returns:
            Dict with 'deterministic' bool and hashes
        """
        results = []
        
        for i in range(runs):
            harness = harness_factory()
            result = harness.run(signals)
            results.append({
                'run': i,
                'state_hash': result.state_hash,
                'pnl': result.total_pnl,
                'signals_processed': result.signals_processed,
            })
        
        # Compare hashes
        hashes = [r['state_hash'] for r in results]
        deterministic = len(set(hashes)) == 1
        
        return {
            'deterministic': deterministic,
            'runs': results,
            'hash_match': deterministic,
            'unique_hashes': list(set(hashes)),
        }
