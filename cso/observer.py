"""
CSO Observer — Passive read-only market observer.

SPRINT: S27.0
STATUS: SCAFFOLD
MODE: PASSIVE_ONLY

The observer READS from:
- River (enriched market data)
- intake/olya/ (knowledge files)

The observer WRITES to:
- DRAFT beads only (via BeadFactory)
- comprehension_hash emissions

FORBIDDEN:
- execution_state writes
- execution signals
- capital annotations

INVARIANTS:
- INV-GOV-NO-T1-WRITE-EXEC: T1 cannot write execution_state
- INV-CSO-PASSIVE-S27: S27 observer is read-only
"""

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

PHOENIX_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    DegradationAction,
    ErrorAction,
    ErrorCategory,
    ErrorClassification,
    FailureMode,
    GovernanceInterface,
    ModuleTier,
    StateInput,
    StateTransition,
)

from .beads import Bead, BeadFactory

# =============================================================================
# EXCEPTIONS
# =============================================================================


class CSOWriteViolation(Exception):
    """Raised when CSO attempts forbidden write."""

    def __init__(self, target: str, action: str):
        self.target = target
        self.action = action
        super().__init__(
            f"INV-GOV-NO-T1-WRITE-EXEC violated: "
            f"CSO attempted '{action}' on forbidden target '{target}'"
        )


class CSONotReadyError(Exception):
    """Raised when CSO is not in READY warmup state."""

    pass


# =============================================================================
# FORBIDDEN TARGETS (T1 cannot write these)
# =============================================================================

FORBIDDEN_WRITE_TARGETS = frozenset(
    [
        "execution_state",
        "orders",
        "positions",
        "capital",
        "broker",
        "account",
    ]
)


# =============================================================================
# CSO OBSERVER
# =============================================================================


class CSOObserver(GovernanceInterface):
    """
    Passive CSO Observer.

    TIER: T1 (capital-adjacent, automated gate)
    MODE: PASSIVE_ONLY (S27)

    Reads market data and knowledge, emits DRAFT beads.
    CANNOT affect execution state.
    """

    # ==========================================================================
    # IDENTITY
    # ==========================================================================

    @property
    def module_id(self) -> str:
        return "phoenix.cso.observer"

    @property
    def module_tier(self) -> ModuleTier:
        return ModuleTier.T1

    @property
    def enforced_invariants(self) -> list[str]:
        return [
            "INV-GOV-NO-T1-WRITE-EXEC",
            "INV-CSO-PASSIVE-S27",
            "INV-CONTRACT-1",
            "INV-DYNASTY-5",
        ]

    @property
    def yield_points(self) -> list[str]:
        return [
            "observe_market",
            "process_knowledge",
            "emit_bead",
        ]

    # ==========================================================================
    # INITIALIZATION
    # ==========================================================================

    def __init__(self):
        super().__init__()
        self._bead_factory: BeadFactory | None = None
        self._beads_emitted: list[Bead] = []
        self._knowledge_loaded: dict = {}
        self._comprehension_hashes: list[str] = []
        self._observation_count: int = 0

    def initialize(self, config: dict | None = None) -> "InitResult":
        """Initialize observer."""
        result = super().initialize(config)

        if result.success:
            self._bead_factory = BeadFactory(source_module=self.module_id)

        return result

    # ==========================================================================
    # WRITE GUARD (INV-GOV-NO-T1-WRITE-EXEC)
    # ==========================================================================

    def _guard_write(self, target: str, action: str) -> None:
        """
        Guard against forbidden writes.

        Raises CSOWriteViolation if target is forbidden.
        """
        if target in FORBIDDEN_WRITE_TARGETS:
            raise CSOWriteViolation(target, action)

    # ==========================================================================
    # OBSERVATION (PASSIVE)
    # ==========================================================================

    def observe_bar(self, bar: dict) -> Bead | None:
        """
        Observe a single bar from the River.

        This is PASSIVE — reads only, emits DRAFT bead if interesting.

        Args:
            bar: Enriched bar data from River (L1-L6)

        Returns:
            DRAFT bead if observation noteworthy, else None
        """
        self.check_halt()
        self._observation_count += 1

        # Check for interesting patterns
        observation = self._detect_pattern(bar)

        if observation:
            bead = self._bead_factory.create_observation_bead(
                symbol=bar.get("symbol", "UNKNOWN"),
                observation_type=observation["type"],
                details=observation["details"],
                state_hash=self.compute_state_hash(),
            )
            self._beads_emitted.append(bead)
            return bead

        return None

    def _detect_pattern(self, bar: dict) -> dict | None:
        """
        Detect notable patterns in bar.

        Returns dict with type + details if found.
        """
        patterns = []

        # Check structure breaks
        if bar.get("structure_break_up"):
            patterns.append(
                {
                    "type": "structure_break",
                    "details": {"direction": "up", "bar_time": bar.get("timestamp")},
                }
            )
        if bar.get("structure_break_down"):
            patterns.append(
                {
                    "type": "structure_break",
                    "details": {"direction": "down", "bar_time": bar.get("timestamp")},
                }
            )

        # Check FVG
        if bar.get("fvg_bull"):
            patterns.append(
                {
                    "type": "fvg",
                    "details": {
                        "direction": "bull",
                        "high": bar.get("fvg_bull_high"),
                        "low": bar.get("fvg_bull_low"),
                    },
                }
            )
        if bar.get("fvg_bear"):
            patterns.append(
                {
                    "type": "fvg",
                    "details": {
                        "direction": "bear",
                        "high": bar.get("fvg_bear_high"),
                        "low": bar.get("fvg_bear_low"),
                    },
                }
            )

        # Check displacement
        if bar.get("is_displacement"):
            patterns.append(
                {
                    "type": "displacement",
                    "details": {
                        "direction": "up" if bar.get("displacement_up") else "down",
                        "pips": bar.get("displacement_pips"),
                        "atr_multiple": bar.get("displacement_atr_multiple"),
                    },
                }
            )

        # Check sweeps
        if bar.get("sweep_detected"):
            patterns.append(
                {
                    "type": "sweep",
                    "details": {
                        "target": bar.get("sweep_target_type"),
                        "direction": bar.get("sweep_direction"),
                        "valid": bar.get("sweep_is_valid"),
                    },
                }
            )

        # Return first pattern found (or None)
        return patterns[0] if patterns else None

    # ==========================================================================
    # COMPREHENSION
    # ==========================================================================

    def emit_comprehension_hash(self, understanding: dict) -> str:
        """
        Emit comprehension hash for intertwine verification.

        Args:
            understanding: What CSO understands about current state

        Returns:
            comprehension_hash
        """
        canonical = json.dumps(understanding, sort_keys=True, default=str)
        hash_val = hashlib.sha256(canonical.encode()).hexdigest()[:16]

        self._comprehension_hashes.append(hash_val)

        return hash_val

    def create_comprehension_bead(self, understanding: dict) -> Bead:
        """Create a comprehension bead for intertwine."""
        self.check_halt()

        bead = self._bead_factory.create_comprehension_bead(
            symbol="SYSTEM", understanding=understanding, state_hash=self.compute_state_hash()
        )
        self._beads_emitted.append(bead)

        return bead

    # ==========================================================================
    # KNOWLEDGE INTAKE
    # ==========================================================================

    def load_knowledge(self, knowledge_path: Path) -> dict:
        """
        Load knowledge file from intake.

        This is READ-ONLY — loads and parses, does not modify.
        """
        self.check_halt()

        if not knowledge_path.exists():
            return {}

        content = knowledge_path.read_text()

        # Store in knowledge cache
        knowledge_id = knowledge_path.stem
        self._knowledge_loaded[knowledge_id] = {
            "path": str(knowledge_path),
            "loaded_at": datetime.now(UTC).isoformat(),
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
        }

        return self._knowledge_loaded[knowledge_id]

    # ==========================================================================
    # STATE MACHINE
    # ==========================================================================

    def process_state(self, input: StateInput) -> StateTransition:
        """
        Process input state.

        For PASSIVE observer, this just observes and optionally emits beads.
        NO execution state changes.
        """
        previous_hash = self.compute_state_hash()
        mutations = []

        bar = input.data.get("bar")
        if bar:
            bead = self.observe_bar(bar)
            if bead:
                mutations.append(f"bead_emitted:{bead.bead_id}")

        new_hash = self.compute_state_hash()

        return StateTransition(
            previous_hash=previous_hash,
            new_hash=new_hash,
            mutations=mutations,
            timestamp=datetime.now(UTC),
        )

    def compute_state_hash(self) -> str:
        """Compute observer state hash."""
        hashable = {
            "observation_count": self._observation_count,
            "beads_emitted": len(self._beads_emitted),
            "knowledge_loaded": list(self._knowledge_loaded.keys()),
        }
        canonical = json.dumps(hashable, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    # ==========================================================================
    # ERROR HANDLING
    # ==========================================================================

    def get_failure_modes(self) -> list[FailureMode]:
        return [
            FailureMode(
                id="CSO-OBS-FAIL-1",
                trigger="river_unavailable",
                classification=ErrorClassification(ErrorCategory.DEGRADED, ErrorAction.DEGRADE),
            ),
            FailureMode(
                id="CSO-OBS-FAIL-2",
                trigger="bead_factory_error",
                classification=ErrorClassification(ErrorCategory.RECOVERABLE, ErrorAction.RETRY),
            ),
        ]

    def get_degradation_paths(self) -> dict[str, DegradationAction]:
        return {
            "CSO-OBS-FAIL-1": DegradationAction(
                action_type="skip_observation", params={"log": True}
            ),
        }

    # ==========================================================================
    # TELEMETRY
    # ==========================================================================

    def get_observer_stats(self) -> dict:
        """Get observer statistics."""
        return {
            "observation_count": self._observation_count,
            "beads_emitted": len(self._beads_emitted),
            "knowledge_files": len(self._knowledge_loaded),
            "comprehension_hashes": len(self._comprehension_hashes),
        }
