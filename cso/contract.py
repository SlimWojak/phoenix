"""
CSO Contract — Skeleton for Chief Strategy Officer

SPRINT: 26.TRACK_C
VERSION: 0.1 (skeleton)
STATUS: Ready for implementation post-Track C

This is the contract definition. Implementation follows after:
1. Olya calibration session
2. NEX salvage integration
3. Cold start procedure verification
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from enum import Enum
import sys
from pathlib import Path

# Add governance to path
PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    GovernanceInterface,
    ModuleTier,
    StateInput,
    StateTransition,
    FailureMode,
    DegradationAction,
    ErrorClassification,
    ErrorCategory,
    ErrorAction,
)


# =============================================================================
# CSO TYPES
# =============================================================================

class Direction(Enum):
    """Trade direction."""
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class WarmupState(Enum):
    """CSO warmup states."""
    COLD = "COLD"           # No data
    WARMING = "WARMING"     # <1440 bars
    LIMITED = "LIMITED"     # 1440-2880 bars
    PARTIAL = "PARTIAL"     # 2880-10080 bars
    READY = "READY"         # >10080 bars


@dataclass
class FourQGateResult:
    """Result of 4Q Gate evaluation."""
    q1_htf_order_flow: bool
    q2_dealing_range: bool
    q3_pda_destination: bool
    q4_timing: bool
    
    q1_detail: Dict = field(default_factory=dict)
    q2_detail: Dict = field(default_factory=dict)
    q3_detail: Dict = field(default_factory=dict)
    q4_detail: Dict = field(default_factory=dict)
    
    @property
    def all_pass(self) -> bool:
        return all([
            self.q1_htf_order_flow,
            self.q2_dealing_range,
            self.q3_pda_destination,
            self.q4_timing
        ])


@dataclass
class CSODecision:
    """CSO decision artifact (maps to bead)."""
    decision_id: str
    timestamp: datetime
    symbol: str
    direction: Direction
    confidence: float
    gate_result: FourQGateResult
    state_hash: str
    
    # Set after outcome
    outcome: Optional[str] = None
    outcome_pips: Optional[float] = None
    outcome_timestamp: Optional[datetime] = None


# =============================================================================
# CSO CONTRACT (Abstract)
# =============================================================================

class CSOContract(GovernanceInterface, ABC):
    """
    Chief Strategy Officer Contract.
    
    Olya's methodology encoded as machine-readable invariants.
    
    TIER: T1 (capital-adjacent, automated gate)
    WRITES: advisory_state
    FORBIDDEN: execution_state, orders, positions
    
    INVARIANTS:
    - INV-CSO-1: No signal during COLD/WARMING state
    - INV-CSO-2: 4Q Gate must pass for non-NEUTRAL direction
    - INV-CSO-3: Confidence calibrated to historical accuracy
    - INV-CSO-4: Every decision emits bead
    - INV-CONTRACT-1: Deterministic (same input → same output)
    """
    
    # ==========================================================================
    # IDENTITY
    # ==========================================================================
    
    @property
    def module_id(self) -> str:
        return "phoenix.cso"
    
    @property
    def module_tier(self) -> ModuleTier:
        return ModuleTier.T1  # Capital-adjacent
    
    @property
    def enforced_invariants(self) -> List[str]:
        return [
            "INV-CSO-1",      # No signal during warmup
            "INV-CSO-2",      # 4Q Gate requirement
            "INV-CSO-3",      # Confidence calibration
            "INV-CSO-4",      # Bead emission
            "INV-CONTRACT-1", # Determinism
        ]
    
    @property
    def yield_points(self) -> List[str]:
        return [
            "evaluate_4q_gate",
            "compute_confidence",
            "emit_decision",
        ]
    
    # ==========================================================================
    # WARMUP
    # ==========================================================================
    
    @property
    @abstractmethod
    def warmup_state(self) -> WarmupState:
        """Current warmup state."""
        pass
    
    @property
    @abstractmethod
    def bars_loaded(self) -> int:
        """Number of bars currently loaded."""
        pass
    
    @abstractmethod
    def check_warmup(self) -> bool:
        """
        Check if warmup is complete.
        
        Returns:
            True if READY state, False otherwise
        """
        pass
    
    # ==========================================================================
    # 4Q GATE
    # ==========================================================================
    
    @abstractmethod
    def evaluate_q1_htf_order_flow(self, bar: Dict) -> tuple[bool, Dict]:
        """
        Q1: Where is HTF order flow pointing?
        
        Returns:
            (passed, detail_dict)
        """
        pass
    
    @abstractmethod
    def evaluate_q2_dealing_range(self, bar: Dict) -> tuple[bool, Dict]:
        """
        Q2: Are we in premium or discount?
        
        Returns:
            (passed, detail_dict)
        """
        pass
    
    @abstractmethod
    def evaluate_q3_pda_destination(self, bar: Dict) -> tuple[bool, Dict]:
        """
        Q3: Where is price going (PDA target)?
        
        Returns:
            (passed, detail_dict)
        """
        pass
    
    @abstractmethod
    def evaluate_q4_timing(self, bar: Dict) -> tuple[bool, Dict]:
        """
        Q4: Is this the right time (kill zone)?
        
        Returns:
            (passed, detail_dict)
        """
        pass
    
    def evaluate_4q_gate(self, bar: Dict) -> FourQGateResult:
        """
        Run full 4Q Gate evaluation.
        
        This is a yield point - check_halt() called.
        """
        self.check_halt()
        
        q1_pass, q1_detail = self.evaluate_q1_htf_order_flow(bar)
        q2_pass, q2_detail = self.evaluate_q2_dealing_range(bar)
        q3_pass, q3_detail = self.evaluate_q3_pda_destination(bar)
        q4_pass, q4_detail = self.evaluate_q4_timing(bar)
        
        return FourQGateResult(
            q1_htf_order_flow=q1_pass,
            q2_dealing_range=q2_pass,
            q3_pda_destination=q3_pass,
            q4_timing=q4_pass,
            q1_detail=q1_detail,
            q2_detail=q2_detail,
            q3_detail=q3_detail,
            q4_detail=q4_detail,
        )
    
    # ==========================================================================
    # DECISION
    # ==========================================================================
    
    @abstractmethod
    def determine_direction(self, gate_result: FourQGateResult) -> Direction:
        """
        Determine trade direction from gate result.
        
        Returns NEUTRAL if gate doesn't pass.
        """
        pass
    
    @abstractmethod
    def compute_confidence(
        self,
        direction: Direction,
        gate_result: FourQGateResult,
        bar: Dict
    ) -> float:
        """
        Compute confidence score 0.0-1.0.
        
        This is a yield point.
        """
        pass
    
    @abstractmethod
    def emit_decision_bead(self, decision: CSODecision) -> str:
        """
        Emit decision to Boardroom.
        
        Returns:
            bead_id
        """
        pass
    
    # ==========================================================================
    # STATE MACHINE
    # ==========================================================================
    
    def process_state(self, input: StateInput) -> StateTransition:
        """
        Core CSO processing.
        
        1. Check warmup
        2. Evaluate 4Q Gate
        3. Determine direction
        4. Compute confidence
        5. Emit decision bead
        
        Returns:
            StateTransition with mutations
        """
        previous_hash = self.compute_state_hash()
        mutations = []
        
        bar = input.data.get('bar', {})
        
        # INV-CSO-1: No signal during warmup
        if not self.check_warmup():
            return StateTransition(
                previous_hash=previous_hash,
                new_hash=previous_hash,  # No state change
                mutations=['warmup_incomplete'],
                timestamp=datetime.now(timezone.utc)
            )
        
        # Evaluate 4Q Gate (yield point inside)
        gate_result = self.evaluate_4q_gate(bar)
        mutations.append('4q_gate_evaluated')
        
        # Determine direction
        direction = self.determine_direction(gate_result)
        
        # INV-CSO-2: 4Q Gate must pass for non-NEUTRAL
        if direction != Direction.NEUTRAL and not gate_result.all_pass:
            direction = Direction.NEUTRAL
        
        # Compute confidence (yield point)
        self.check_halt()
        confidence = self.compute_confidence(direction, gate_result, bar)
        mutations.append('confidence_computed')
        
        # Create decision
        decision = CSODecision(
            decision_id=self._generate_decision_id(),
            timestamp=datetime.now(timezone.utc),
            symbol=bar.get('symbol', 'UNKNOWN'),
            direction=direction,
            confidence=confidence,
            gate_result=gate_result,
            state_hash=previous_hash
        )
        
        # INV-CSO-4: Emit bead
        self.check_halt()
        bead_id = self.emit_decision_bead(decision)
        mutations.append(f'bead_emitted:{bead_id}')
        
        new_hash = self.compute_state_hash()
        
        return StateTransition(
            previous_hash=previous_hash,
            new_hash=new_hash,
            mutations=mutations,
            timestamp=datetime.now(timezone.utc)
        )
    
    @abstractmethod
    def _generate_decision_id(self) -> str:
        """Generate unique decision ID."""
        pass
    
    # ==========================================================================
    # ERROR HANDLING
    # ==========================================================================
    
    def get_failure_modes(self) -> List[FailureMode]:
        return [
            FailureMode(
                id="CSO-FAIL-1",
                trigger="warmup_incomplete",
                classification=ErrorClassification(
                    ErrorCategory.DEGRADED,
                    ErrorAction.DEGRADE
                )
            ),
            FailureMode(
                id="CSO-FAIL-2",
                trigger="river_stale",
                classification=ErrorClassification(
                    ErrorCategory.DEGRADED,
                    ErrorAction.DEGRADE
                )
            ),
            FailureMode(
                id="CSO-FAIL-3",
                trigger="boardroom_unavailable",
                classification=ErrorClassification(
                    ErrorCategory.CRITICAL,
                    ErrorAction.HALT
                )
            ),
        ]
    
    def get_degradation_paths(self) -> Dict[str, DegradationAction]:
        return {
            "CSO-FAIL-1": DegradationAction(
                action_type="emit_neutral",
                params={"reason": "warmup_incomplete"}
            ),
            "CSO-FAIL-2": DegradationAction(
                action_type="reduce_confidence",
                params={"multiplier": 0.5}
            ),
        }


# =============================================================================
# WARMUP CONSTANTS
# =============================================================================

WARMUP_THRESHOLDS = {
    WarmupState.COLD: 0,
    WarmupState.WARMING: 1,
    WarmupState.LIMITED: 1440,      # 24h
    WarmupState.PARTIAL: 2880,      # 48h
    WarmupState.READY: 10080,       # 7 days
}


def get_warmup_state(bars_loaded: int) -> WarmupState:
    """Determine warmup state from bar count."""
    if bars_loaded >= WARMUP_THRESHOLDS[WarmupState.READY]:
        return WarmupState.READY
    elif bars_loaded >= WARMUP_THRESHOLDS[WarmupState.PARTIAL]:
        return WarmupState.PARTIAL
    elif bars_loaded >= WARMUP_THRESHOLDS[WarmupState.LIMITED]:
        return WarmupState.LIMITED
    elif bars_loaded >= WARMUP_THRESHOLDS[WarmupState.WARMING]:
        return WarmupState.WARMING
    else:
        return WarmupState.COLD
