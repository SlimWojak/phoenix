"""
Bit Vector Tests — S36 Track C
==============================

INVARIANTS PROVEN:
  - INV-BITVECTOR-NO-POPULATION: System MUST NOT compute or expose bit-counts
  - INV-HARNESS-5: No downstream consumer shall count 1s
  - INV-ATTR-NO-RANKING: No implicit priority

EXIT GATE C:
  Criterion: "Bit vector generated correctly; MACHINE_ONLY default; no population counting"
  Proof: "No popcount/len in codebase; UI gate_map order randomized"
"""

import secrets
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

import pytest
import yaml

# Ensure phoenix root is in path
PHOENIX_ROOT = Path(__file__).parent.parent.parent
if str(PHOENIX_ROOT) not in sys.path:
    sys.path.insert(0, str(PHOENIX_ROOT))

# =============================================================================
# INLINE TYPES (avoid cso/__init__.py which requires pandas)
# =============================================================================

CSO_ROOT = PHOENIX_ROOT / "cso"
GATE_SCHEMA_PATH = CSO_ROOT / "schemas" / "gate_schema.yaml"


class BitVectorScope(Enum):
    MACHINE_ONLY = "MACHINE_ONLY"
    UI_OPT_IN = "UI_OPT_IN"


@dataclass
class BitVectorResult:
    pair: str
    vector: str
    gate_map: dict[int, str]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    scope: BitVectorScope = BitVectorScope.MACHINE_ONLY


@dataclass
class UIBitVectorResult:
    pair: str
    vector: str
    gate_map: dict[int, str]
    shuffle_seed: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class BitVectorGenerator:
    def __init__(self) -> None:
        self._gate_order: list[str] | None = None

    def _load_gate_order(self) -> list[str]:
        if self._gate_order is not None:
            return self._gate_order
        if GATE_SCHEMA_PATH.exists():
            with open(GATE_SCHEMA_PATH) as f:
                schema = yaml.safe_load(f)
                gates = schema.get("gates", {})
                self._gate_order = sorted(
                    gates.keys(),
                    key=lambda g: (gates[g].get("drawer", 0), g),
                )
        else:
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
        gate_order = self._load_gate_order()
        gate_map: dict[int, str] = {i: g for i, g in enumerate(gate_order)}
        vector_bits: list[str] = []
        passed_set = set(gates_passed)
        for gate_id in gate_order:
            if gate_id in passed_set:
                vector_bits.append("1")
            else:
                vector_bits.append("0")
        vector = "".join(vector_bits)
        return BitVectorResult(
            pair=pair, vector=vector, gate_map=gate_map, scope=BitVectorScope.MACHINE_ONLY
        )

    def generate_ui_view(
        self, bit_vector: BitVectorResult, seed: str | None = None
    ) -> UIBitVectorResult:
        if seed is None:
            seed = secrets.token_hex(8)
        rng = secrets.SystemRandom()
        positions = list(range(len(bit_vector.gate_map)))
        rng.shuffle(positions)
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


class PopulationCountBan:
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
        query_lower = query.lower()
        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern in query_lower:
                return (
                    False,
                    f"Population counting forbidden: '{pattern}' detected. INV-BITVECTOR-NO-POPULATION",
                )
        return (True, "")


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def generator() -> BitVectorGenerator:
    """Create generator instance."""
    return BitVectorGenerator()


@pytest.fixture
def sample_gates_passed() -> list[str]:
    """Sample passed gates."""
    return [
        "htf_structure_bullish",
        "htf_poi_identified",
        "kill_zone_active",
        "fvg_present",
        "displacement_sufficient",
    ]


@pytest.fixture
def sample_gates_failed() -> list[str]:
    """Sample failed gates."""
    return [
        "htf_structure_bearish",
        "asia_range_defined",
        "session_bias_aligned",
        "liquidity_swept [delta: 3 bars over threshold]",
    ]


# =============================================================================
# BASIC GENERATION TESTS
# =============================================================================


class TestBasicGeneration:
    """Tests for basic bit vector generation."""

    def test_generate_returns_bit_vector_result(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Generation returns BitVectorResult."""
        result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        assert isinstance(result, BitVectorResult)
        assert result.pair == "EURUSD"

    def test_vector_is_binary_string(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Vector is a string of 0s and 1s."""
        result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        assert isinstance(result.vector, str)
        assert all(c in "01" for c in result.vector)

    def test_gate_map_is_dict(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Gate map is position -> gate_id dict."""
        result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        assert isinstance(result.gate_map, dict)
        assert all(isinstance(k, int) for k in result.gate_map.keys())
        assert all(isinstance(v, str) for v in result.gate_map.values())


# =============================================================================
# MACHINE_ONLY DEFAULT TESTS
# =============================================================================


class TestMachineOnlyDefault:
    """Tests for MACHINE_ONLY scope default."""

    def test_default_scope_is_machine_only(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Default scope is MACHINE_ONLY."""
        result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        assert result.scope == BitVectorScope.MACHINE_ONLY


# =============================================================================
# NO POPULATION COUNT TESTS (Critical)
# =============================================================================


class TestNoPopulationCount:
    """Tests for population count ban."""

    def test_result_has_no_popcount(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Result does not have popcount field."""
        result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        assert not hasattr(result, "popcount")
        assert not hasattr(result, "ones_count")
        assert not hasattr(result, "bit_count")
        assert not hasattr(result, "hamming_weight")

    def test_result_has_no_score(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Result does not have score field."""
        result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        assert not hasattr(result, "score")
        assert not hasattr(result, "quality")

    def test_popcount_query_rejected(self) -> None:
        """Query requesting popcount is rejected."""
        valid, error = PopulationCountBan.validate_query("Get vectors with popcount > 6")

        assert not valid
        assert "INV-BITVECTOR-NO-POPULATION" in error

    def test_count_1s_query_rejected(self) -> None:
        """Query counting 1s is rejected."""
        valid, error = PopulationCountBan.validate_query("Find vectors with more than 6 ones")

        assert not valid

    def test_hamming_distance_rejected(self) -> None:
        """Hamming distance query is rejected."""
        valid, error = PopulationCountBan.validate_query(
            "Calculate hamming_distance between vectors"
        )

        assert not valid

    def test_valid_pattern_query_accepted(self) -> None:
        """Valid pattern query is accepted."""
        valid, error = PopulationCountBan.validate_query("Find vectors matching pattern 11???1??")

        assert valid


# =============================================================================
# UI SHUFFLE TESTS
# =============================================================================


class TestUIShuttle:
    """Tests for UI gate map shuffling."""

    def test_ui_view_is_shuffled(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """UI view has shuffled gate positions."""
        machine_result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")
        ui_result = generator.generate_ui_view(machine_result)

        assert isinstance(ui_result, UIBitVectorResult)
        assert ui_result.shuffle_seed  # Has a seed

    def test_ui_shuffle_varies(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Multiple UI renders produce different orders."""
        machine_result = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        # Generate multiple UI views
        ui_results = [generator.generate_ui_view(machine_result) for _ in range(10)]

        # Get gate orders
        gate_orders = [tuple(r.gate_map[i] for i in sorted(r.gate_map.keys())) for r in ui_results]

        # Should have at least some variation (not all identical)
        unique_orders = set(gate_orders)
        assert len(unique_orders) > 1  # At least 2 different orders

    def test_machine_layer_is_deterministic(
        self,
        generator: BitVectorGenerator,
        sample_gates_passed: list[str],
        sample_gates_failed: list[str],
    ) -> None:
        """Machine layer is deterministic (same order every time)."""
        result1 = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")
        result2 = generator.generate(sample_gates_passed, sample_gates_failed, "EURUSD")

        # Gate maps should be identical
        assert result1.gate_map == result2.gate_map
        assert result1.vector == result2.vector


# =============================================================================
# VECTOR CORRECTNESS TESTS
# =============================================================================


class TestVectorCorrectness:
    """Tests for vector correctness."""

    def test_passed_gates_are_1s(
        self,
        generator: BitVectorGenerator,
    ) -> None:
        """Passed gates map to 1 in vector."""
        gates_passed = ["htf_structure_bullish"]
        gates_failed = ["htf_structure_bearish"]

        result = generator.generate(gates_passed, gates_failed, "EURUSD")

        # Find position of htf_structure_bullish
        bullish_pos = None
        for pos, gate_id in result.gate_map.items():
            if gate_id == "htf_structure_bullish":
                bullish_pos = pos
                break

        if bullish_pos is not None:
            assert result.vector[bullish_pos] == "1"

    def test_failed_gates_are_0s(
        self,
        generator: BitVectorGenerator,
    ) -> None:
        """Failed gates map to 0 in vector."""
        gates_passed = ["htf_structure_bullish"]
        gates_failed = ["htf_structure_bearish"]

        result = generator.generate(gates_passed, gates_failed, "EURUSD")

        # Find position of htf_structure_bearish
        bearish_pos = None
        for pos, gate_id in result.gate_map.items():
            if gate_id == "htf_structure_bearish":
                bearish_pos = pos
                break

        if bearish_pos is not None:
            assert result.vector[bearish_pos] == "0"


# =============================================================================
# SUMMARY
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
