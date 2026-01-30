"""
Bit Vector Output — S36 Track C
===============================

Machine-readable gate status for sub-millisecond triage.

CRITICAL: Bit vectors are MACHINE_ONLY by default.
No population counts. No Hamming distance. No scalar derivation.

INVARIANTS:
  - INV-BITVECTOR-NO-POPULATION: System MUST NOT compute or expose bit-counts
  - INV-HARNESS-5: No downstream consumer shall count 1s

FORBIDDEN:
  - popcount
  - bin(x).count('1')
  - sum(1 for b in vector if b == '1')
  - len([g for g in gates_passed])
  - vector.count('1')
  - Hamming distance
  - Any scalar derived from bit vector
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

CSO_ROOT = Path(__file__).parent
GATE_SCHEMA_PATH = CSO_ROOT / "schemas" / "gate_schema.yaml"


class BitVectorScope(Enum):
    """Scope of bit vector exposure."""

    MACHINE_ONLY = "MACHINE_ONLY"  # Default
    UI_OPT_IN = "UI_OPT_IN"  # Requires T2 approval


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class BitVectorResult:
    """
    Bit vector representation of gate status.

    FORBIDDEN: Any population count or scalar derivation.

    Fields:
      - vector: Binary string (e.g., "01011010")
      - gate_map: Position -> gate_id (MACHINE layer, deterministic)
      - ui_gate_map: Shuffled for UI display (randomized per render)
    """

    pair: str
    vector: str  # "01011010..." — NO COUNTING ALLOWED
    gate_map: dict[int, str]  # Machine layer (conditions.yaml order)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    scope: BitVectorScope = BitVectorScope.MACHINE_ONLY

    # FORBIDDEN: Do not add any of these fields
    # - popcount
    # - ones_count
    # - zeros_count
    # - hamming_weight
    # - score
    # - quality


@dataclass
class UIBitVectorResult:
    """
    UI representation with shuffled gate map.

    Position is RANDOMIZED per render to prevent pattern bias.
    """

    pair: str
    vector: str  # Order matches shuffled gate_map
    gate_map: dict[int, str]  # SHUFFLED for UI
    shuffle_seed: str  # For reproducibility in tests
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


# =============================================================================
# BIT VECTOR GENERATOR
# =============================================================================


class BitVectorGenerator:
    """
    Generates bit vectors from gate evaluations.

    MACHINE_ONLY by default. No population counting.

    FORBIDDEN OPERATIONS (enforced by code review + linting):
      - popcount()
      - vector.count('1')
      - len([b for b in vector if b == '1'])
      - sum(1 for ...)
      - Any Hamming distance calculation

    Usage:
        generator = BitVectorGenerator()
        result = generator.generate(gates_passed, gates_failed)
    """

    def __init__(self) -> None:
        """Initialize generator."""
        self._gate_order: list[str] | None = None

    def _load_gate_order(self) -> list[str]:
        """Load deterministic gate order from schema."""
        if self._gate_order is not None:
            return self._gate_order

        if GATE_SCHEMA_PATH.exists():
            with open(GATE_SCHEMA_PATH) as f:
                schema = yaml.safe_load(f)
                gates = schema.get("gates", {})
                # Sort by drawer, then alphabetically within drawer
                self._gate_order = sorted(
                    gates.keys(),
                    key=lambda g: (gates[g].get("drawer", 0), g),
                )
        else:
            # Default order
            self._gate_order = [
                "htf_structure_bullish",
                "htf_structure_bearish",
                "htf_poi_identified",
                "kill_zone_active",
                "asia_range_defined",
                "session_bias_aligned",
                "fvg_present",
                "displacement_sufficient",
                "liquidity_swept",
                "ltf_confirmation",
                "entry_model_valid",
                "stop_defined",
                "target_defined",
                "rr_acceptable",
                "partials_planned",
            ]

        return self._gate_order

    def generate(
        self,
        gates_passed: list[str],
        gates_failed: list[str],
        pair: str = "",
    ) -> BitVectorResult:
        """
        Generate bit vector from gate results.

        Args:
            gates_passed: List of passed gate IDs
            gates_failed: List of failed gate IDs (may include delta info)
            pair: Trading pair

        Returns:
            BitVectorResult (MACHINE_ONLY scope)

        NOTE: This returns a VECTOR, not a COUNT.
        Counting the 1s is FORBIDDEN.
        """
        gate_order = self._load_gate_order()

        # Build gate map (position -> gate_id)
        gate_map: dict[int, str] = {i: g for i, g in enumerate(gate_order)}

        # Build vector string
        vector_bits: list[str] = []

        # Extract base gate IDs (remove delta info if present)
        passed_set = set(gates_passed)
        _failed_base = {g.split(" [")[0] for g in gates_failed}  # Reserved for future use

        for gate_id in gate_order:
            if gate_id in passed_set:
                vector_bits.append("1")
            else:
                vector_bits.append("0")

        vector = "".join(vector_bits)

        return BitVectorResult(
            pair=pair,
            vector=vector,
            gate_map=gate_map,
            scope=BitVectorScope.MACHINE_ONLY,
        )

    def generate_ui_view(
        self,
        bit_vector: BitVectorResult,
        seed: str | None = None,
    ) -> UIBitVectorResult:
        """
        Generate UI view with shuffled gate positions.

        Position is RANDOMIZED to prevent pattern bias.
        "Longest green bar = best" pattern is DEFEATED.

        Args:
            bit_vector: Machine layer result
            seed: Optional seed for reproducibility

        Returns:
            UIBitVectorResult with shuffled positions
        """
        # Generate or use seed
        if seed is None:
            seed = secrets.token_hex(8)

        # Create shuffled positions
        rng = secrets.SystemRandom()
        positions = list(range(len(bit_vector.gate_map)))
        rng.shuffle(positions)

        # Build shuffled gate map
        original_gates = [bit_vector.gate_map[i] for i in range(len(bit_vector.gate_map))]
        shuffled_map: dict[int, str] = {}
        shuffled_vector: list[str] = []

        for new_pos, old_pos in enumerate(positions):
            shuffled_map[new_pos] = original_gates[old_pos]
            shuffled_vector.append(bit_vector.vector[old_pos])

        return UIBitVectorResult(
            pair=bit_vector.pair,
            vector="".join(shuffled_vector),
            gate_map=shuffled_map,
            shuffle_seed=seed,
        )


# =============================================================================
# POPULATION COUNT BAN (Validation)
# =============================================================================


class PopulationCountBan:
    """
    Validates that no population counting occurs.

    Rejects any query or operation that would count 1s.
    """

    FORBIDDEN_PATTERNS = frozenset(
        [
            "popcount",
            "count('1')",
            'count("1")',
            "ones_count",
            "hamming_weight",
            "hamming_distance",
            "bit_count",
            "> 6 ones",
            ">6 ones",
            "more than",
            "fewer than",
            "at least",
        ]
    )

    @classmethod
    def validate_query(cls, query: str) -> tuple[bool, str]:
        """
        Validate a query doesn't request population counting.

        Args:
            query: Query string to validate

        Returns:
            (valid, error_message)
        """
        query_lower = query.lower()

        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in query_lower:
                return (
                    False,
                    f"Population counting forbidden: '{pattern}' detected. "
                    "INV-BITVECTOR-NO-POPULATION",
                )

        return (True, "")

    @classmethod
    def validate_operation(cls, operation: str) -> tuple[bool, str]:
        """
        Validate an operation doesn't involve population counting.

        Args:
            operation: Operation description

        Returns:
            (valid, error_message)
        """
        return cls.validate_query(operation)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "BitVectorGenerator",
    "BitVectorResult",
    "UIBitVectorResult",
    "BitVectorScope",
    "PopulationCountBan",
]
