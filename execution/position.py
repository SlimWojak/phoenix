"""
Position Lifecycle — State machine for position tracking.

SPRINT: S28.C
STATUS: MOCK_SIGNALS
CAPITAL: PAPER_ONLY

Position lifecycle states and transitions:
- PENDING → OPEN → PARTIAL → CLOSED
- Any state → HALTED (system halt)

CONSTRAINTS (S28.C):
- Paper only (no real capital)
- Simplified P&L v0 (no fees/slippage)
- Deterministic state transitions

INVARIANTS:
- INV-CONTRACT-1: deterministic state machine
- INV-EXEC-LIFECYCLE-1: valid transitions only
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, List, Set
import hashlib
import json


# =============================================================================
# EXCEPTIONS
# =============================================================================

class InvalidTransitionError(Exception):
    """Raised when attempting invalid state transition."""
    def __init__(self, from_state: 'PositionState', to_state: 'PositionState'):
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(
            f"INV-EXEC-LIFECYCLE-1 violated: "
            f"Invalid transition {from_state.value} → {to_state.value}"
        )


class PositionMutationError(Exception):
    """Raised when attempting to mutate closed/halted position."""
    pass


# =============================================================================
# POSITION STATE ENUM
# =============================================================================

class PositionState(Enum):
    """
    Position lifecycle states.
    
    GPT_LINT L28-C2: enum required for lifecycle states.
    """
    PENDING = "PENDING"     # Intent received, order not yet filled
    OPEN = "OPEN"           # Order filled, position active
    PARTIAL = "PARTIAL"     # Partial fill received
    CLOSED = "CLOSED"       # Exit complete, position closed
    HALTED = "HALTED"       # System halt killed position


# =============================================================================
# STATE MACHINE TRANSITIONS
# =============================================================================

# Valid state transitions (INV-EXEC-LIFECYCLE-1)
VALID_TRANSITIONS: Dict[PositionState, Set[PositionState]] = {
    PositionState.PENDING: {
        PositionState.OPEN,      # Full fill
        PositionState.PARTIAL,   # Partial fill
        PositionState.CLOSED,    # Cancelled before fill
        PositionState.HALTED,    # System halt
    },
    PositionState.OPEN: {
        PositionState.PARTIAL,   # Partial exit
        PositionState.CLOSED,    # Full exit
        PositionState.HALTED,    # System halt
    },
    PositionState.PARTIAL: {
        PositionState.OPEN,      # Re-filled remaining
        PositionState.CLOSED,    # Exit remaining
        PositionState.HALTED,    # System halt
    },
    PositionState.CLOSED: set(),  # Terminal state
    PositionState.HALTED: set(),  # Terminal state
}


def validate_transition(from_state: PositionState, to_state: PositionState) -> bool:
    """
    Validate state transition.
    
    INV-EXEC-LIFECYCLE-1: only valid transitions allowed.
    
    Args:
        from_state: Current state
        to_state: Target state
    
    Returns:
        True if valid, False otherwise
    """
    valid_targets = VALID_TRANSITIONS.get(from_state, set())
    return to_state in valid_targets


# =============================================================================
# POSITION DATA CLASS
# =============================================================================

@dataclass
class Position:
    """
    Position tracking with lifecycle state machine.
    
    P&L_v0 (SIMPLIFIED):
    - No fees
    - No slippage
    - P&L = (exit_price - entry_price) * size * direction_multiplier
    
    NOTE: This is PAPER ONLY for S28.C.
    """
    
    # Identity (required)
    position_id: str
    intent_id: str          # Source intent
    state: PositionState
    symbol: str
    direction: str          # "LONG" or "SHORT"
    
    # Optional fields with defaults
    state_history: List[Dict] = field(default_factory=list)
    
    # Fills
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    size: float = 0.0
    filled_size: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # P&L (simplified v0 — NO fees, NO slippage)
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Hash for determinism
    position_hash: str = ""
    
    def __post_init__(self):
        """Record initial state in history."""
        if not self.state_history:
            self._record_state_change(None, self.state, "created")
        if not self.position_hash:
            self.position_hash = self._compute_hash()
    
    def _record_state_change(
        self, 
        from_state: Optional[PositionState], 
        to_state: PositionState, 
        reason: str
    ) -> None:
        """Record state transition in history."""
        self.state_history.append({
            'from': from_state.value if from_state else None,
            'to': to_state.value,
            'reason': reason,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })
    
    def _compute_hash(self) -> str:
        """
        Compute deterministic position hash.
        
        INV-CONTRACT-1: Same state → same hash.
        """
        hashable = {
            'position_id': self.position_id,
            'intent_id': self.intent_id,
            'state': self.state.value,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'size': self.size,
            'filled_size': self.filled_size,
            'realized_pnl': self.realized_pnl,
        }
        canonical = json.dumps(hashable, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]
    
    def transition_to(self, new_state: PositionState, reason: str = "") -> None:
        """
        Transition to new state.
        
        INV-EXEC-LIFECYCLE-1: Validates transition before applying.
        
        Args:
            new_state: Target state
            reason: Reason for transition
        
        Raises:
            InvalidTransitionError: If transition is invalid
        """
        if not validate_transition(self.state, new_state):
            raise InvalidTransitionError(self.state, new_state)
        
        old_state = self.state
        self.state = new_state
        self._record_state_change(old_state, new_state, reason)
        self.position_hash = self._compute_hash()
    
    def fill(self, price: float, size: float) -> None:
        """
        Record fill.
        
        Args:
            price: Fill price
            size: Fill size
        """
        if self.state in (PositionState.CLOSED, PositionState.HALTED):
            raise PositionMutationError(f"Cannot fill {self.state.value} position")
        
        if self.entry_price is None:
            self.entry_price = price
        
        self.filled_size += size
        
        if self.state == PositionState.PENDING:
            if self.filled_size >= self.size:
                self.transition_to(PositionState.OPEN, f"filled at {price}")
                self.opened_at = datetime.now(timezone.utc)
            else:
                self.transition_to(PositionState.PARTIAL, f"partial fill at {price}")
    
    def close(self, exit_price: float, reason: str = "exit") -> None:
        """
        Close position.
        
        Calculates realized P&L (simplified v0).
        
        Args:
            exit_price: Exit price
            reason: Close reason
        """
        if self.state in (PositionState.CLOSED, PositionState.HALTED):
            raise PositionMutationError(f"Cannot close {self.state.value} position")
        
        self.exit_price = exit_price
        self.closed_at = datetime.now(timezone.utc)
        
        # Calculate P&L (simplified v0 — no fees, no slippage)
        # GPT_LINT L28-C1: documented as "simplified P&L v0"
        if self.entry_price is not None:
            direction_mult = 1.0 if self.direction == "LONG" else -1.0
            self.realized_pnl = (exit_price - self.entry_price) * self.filled_size * direction_mult
        
        self.unrealized_pnl = 0.0
        self.transition_to(PositionState.CLOSED, reason)
    
    def halt(self, halt_id: str) -> None:
        """
        Halt position due to system halt.
        
        Args:
            halt_id: Halt signal ID
        """
        if self.state in (PositionState.CLOSED, PositionState.HALTED):
            return  # Already terminal
        
        self.transition_to(PositionState.HALTED, f"system halt: {halt_id}")
        self.closed_at = datetime.now(timezone.utc)
    
    def update_unrealized(self, current_price: float) -> float:
        """
        Update unrealized P&L based on current price.
        
        Args:
            current_price: Current market price
        
        Returns:
            Unrealized P&L
        """
        if self.state not in (PositionState.OPEN, PositionState.PARTIAL):
            return 0.0
        
        if self.entry_price is None:
            return 0.0
        
        direction_mult = 1.0 if self.direction == "LONG" else -1.0
        self.unrealized_pnl = (current_price - self.entry_price) * self.filled_size * direction_mult
        return self.unrealized_pnl
    
    def to_dict(self) -> Dict:
        """Serialize position to dict."""
        return {
            'position_id': self.position_id,
            'intent_id': self.intent_id,
            'state': self.state.value,
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'size': self.size,
            'filled_size': self.filled_size,
            'created_at': self.created_at.isoformat(),
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'position_hash': self.position_hash,
            'state_history': self.state_history,
        }


# =============================================================================
# POSITION REGISTRY
# =============================================================================

class PositionRegistry:
    """
    Registry for tracking active and closed positions.
    
    S28.C: Paper only.
    """
    
    def __init__(self):
        self._positions: Dict[str, Position] = {}
        self._counter = 0
    
    def create_position(
        self,
        intent_id: str,
        symbol: str,
        direction: str,
        size: float
    ) -> Position:
        """
        Create new position from intent.
        
        Args:
            intent_id: Source intent ID
            symbol: Trading symbol
            direction: "LONG" or "SHORT"
            size: Target size
        
        Returns:
            New Position in PENDING state
        """
        self._counter += 1
        now = datetime.now(timezone.utc)
        position_id = f"POS-{now.strftime('%Y%m%d%H%M%S')}-{self._counter:04d}"
        
        position = Position(
            position_id=position_id,
            intent_id=intent_id,
            state=PositionState.PENDING,
            symbol=symbol,
            direction=direction,
            size=size,
        )
        
        self._positions[position_id] = position
        return position
    
    def get_position(self, position_id: str) -> Optional[Position]:
        """Get position by ID."""
        return self._positions.get(position_id)
    
    def get_by_intent(self, intent_id: str) -> Optional[Position]:
        """Get position by source intent ID."""
        for pos in self._positions.values():
            if pos.intent_id == intent_id:
                return pos
        return None
    
    def get_active_positions(self) -> List[Position]:
        """Get all non-terminal positions."""
        return [
            p for p in self._positions.values()
            if p.state not in (PositionState.CLOSED, PositionState.HALTED)
        ]
    
    def get_closed_positions(self) -> List[Position]:
        """Get all closed positions."""
        return [
            p for p in self._positions.values()
            if p.state == PositionState.CLOSED
        ]
    
    def halt_all(self, halt_id: str) -> int:
        """
        Halt all active positions.
        
        Args:
            halt_id: Halt signal ID
        
        Returns:
            Count of positions halted
        """
        count = 0
        for position in self.get_active_positions():
            position.halt(halt_id)
            count += 1
        return count
    
    def get_total_pnl(self) -> Dict[str, float]:
        """
        Get total P&L across all positions.
        
        Returns:
            Dict with 'realized' and 'unrealized' P&L
        """
        realized = sum(p.realized_pnl for p in self._positions.values())
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        return {
            'realized': realized,
            'unrealized': unrealized,
            'total': realized + unrealized,
        }
    
    def get_state_hash(self) -> str:
        """
        Compute hash of all positions for determinism check.
        
        INV-CONTRACT-1: Same state → same hash.
        """
        position_hashes = sorted([p.position_hash for p in self._positions.values()])
        combined = "|".join(position_hashes)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Serialize registry state."""
        return {
            'positions': {pid: p.to_dict() for pid, p in self._positions.items()},
            'count': len(self._positions),
            'state_hash': self.get_state_hash(),
        }
