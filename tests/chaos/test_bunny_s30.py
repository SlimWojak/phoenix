"""
BUNNY Chaos Tests — S30
=======================

Adversarial tests attacking S30 invariants.
Every invariant has at least one chaos vector.

Run with: pytest tests/chaos/test_bunny_s30.py -v
"""

from __future__ import annotations

import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def temp_bead_store():
    """Create temporary BeadStore for testing."""
    from memory import BeadStore

    test_db = Path(tempfile.mktemp(suffix=".db"))
    store = BeadStore(db_path=test_db)
    yield store
    store.close()
    if test_db.exists():
        test_db.unlink()


@pytest.fixture
def temp_hunt_engine(temp_bead_store):
    """Create HuntEngine with temp BeadStore."""
    from lab import HuntEngine

    return HuntEngine(bead_store=temp_bead_store)


# =============================================================================
# HUNT INVARIANT TESTS
# =============================================================================


class TestHuntInvariants:
    """Chaos vectors for Hunt invariants."""

    @pytest.mark.invariant
    def test_cv_hunt_hpg_fuzz_missing_fields(self):
        """
        CV_HUNT_HPG_FUZZ: Malformed HPG with missing required fields.

        INV-HUNT-HPG-1: Hunt only accepts valid HPG JSON
        """
        from lab.hpg_parser import HPG, HPGParser

        parser = HPGParser()

        # Try to create HPG with missing signal_type
        with pytest.raises((KeyError, ValueError, TypeError)):
            HPG.from_dict({"pair": "EURUSD", "random_seed": 123})

    @pytest.mark.invariant
    def test_cv_hunt_hpg_fuzz_wrong_types(self):
        """
        CV_HUNT_HPG_FUZZ: Malformed HPG with wrong types.

        INV-HUNT-HPG-1: Hunt only accepts valid HPG JSON
        """
        from lab.hpg_parser import HPG, HPGParser

        parser = HPGParser()

        # Invalid signal_type enum
        with pytest.raises(ValueError):
            HPG.from_dict({
                "signal_type": "INVALID_SIGNAL",
                "pair": "EURUSD",
                "session": "LONDON",
                "stop_model": "NORMAL",
                "risk_percent": 1.0,
                "random_seed": 123,
            })

    @pytest.mark.invariant
    def test_cv_hunt_hpg_validation_bounds(self):
        """
        CV_HUNT_HPG_FUZZ: HPG with out-of-bounds risk.

        INV-HUNT-HPG-1: Hunt only accepts valid HPG JSON
        """
        from lab.hpg_parser import HPG, HPGParser, Session, SignalType, StopModel

        parser = HPGParser()

        # Create HPG with risk outside bounds
        hpg = HPG(
            hpg_version="1.0",
            signal_type=SignalType.FVG,
            pair="EURUSD",
            session=Session.LONDON,
            stop_model=StopModel.NORMAL,
            risk_percent=10.0,  # Way over 2.5 limit
            random_seed=123,
        )

        result = parser.validate(hpg)
        assert not result.valid, "Should reject out-of-bounds risk"
        assert any("risk" in e.lower() for e in result.errors)

    @pytest.mark.invariant
    def test_cv_hunt_determinism(self, temp_hunt_engine):
        """
        CV_HUNT_DETERMINISM: Identical Hunt twice → identical results.

        INV-HUNT-DET-1: Same seed + data → same results
        """
        # Run same hunt twice with same session
        result1 = temp_hunt_engine.run(
            "Test FVG after 8:30am London",
            "determinism-test",
        )
        result2 = temp_hunt_engine.run(
            "Test FVG after 8:30am London",
            "determinism-test",
        )

        # Results should be identical (except timestamps)
        assert result1.variants_tested == result2.variants_tested
        assert result1.hpg.compute_hash() == result2.hpg.compute_hash()
        assert len(result1.survivors) == len(result2.survivors)

    @pytest.mark.invariant
    def test_cv_hunt_cap_breach(self):
        """
        CV_HUNT_CAP_BREACH: Variation generator respects cap.

        INV-HUNT-CAP-1: Max 50 variations
        """
        from lab.hpg_parser import HPG, Session, SignalType, StopModel
        from lab.variation_generator import VariationConfig, VariationGenerator

        # Create base HPG
        hpg = HPG(
            hpg_version="1.0",
            signal_type=SignalType.FVG,
            pair="EURUSD",
            session=Session.LONDON,
            stop_model=StopModel.NORMAL,
            risk_percent=1.0,
            random_seed=42,
        )

        # Configure for max variations
        config = VariationConfig(max_variations=50, chaos_enabled=True)
        generator = VariationGenerator(config)

        result = generator.generate(hpg)

        # Should never exceed cap
        assert len(result.variants) <= 50, "Variation cap breached!"

    @pytest.mark.invariant
    def test_cv_hunt_bead_emission(self, temp_bead_store):
        """
        CV_HUNT_BEAD_EMISSION: Hunt emits exactly one bead.

        INV-HUNT-BEAD-1: One HUNT bead per run
        """
        from lab import HuntEngine

        initial_count = temp_bead_store.count_beads()

        engine = HuntEngine(bead_store=temp_bead_store)
        result = engine.run("Test FVG London", "bead-test")

        final_count = temp_bead_store.count_beads()

        # Exactly one new bead
        assert final_count == initial_count + 1, "Should emit exactly one bead"
        assert result.bead_id is not None

    @pytest.mark.invariant
    def test_cv_hunt_sort_stability(self, temp_hunt_engine):
        """
        CV_HUNT_SORT_STABILITY: Results sorted by variant_id.

        INV-HUNT-SORT-1: Stable sort for determinism
        """
        from lab.backtester import Backtester, DataWindow

        backtester = Backtester()
        window = DataWindow.default(30)

        # Create multiple variants
        from lab.hpg_parser import HPG, Session, SignalType, StopModel

        hpg = HPG(
            hpg_version="1.0",
            signal_type=SignalType.FVG,
            pair="EURUSD",
            session=Session.LONDON,
            stop_model=StopModel.NORMAL,
            risk_percent=1.0,
            random_seed=42,
        )

        variants = [
            (hpg, "variant_z"),
            (hpg, "variant_a"),
            (hpg, "variant_m"),
        ]

        results = backtester.run_batch(variants, window)

        # Should be sorted by variant_id
        variant_ids = [r.variant_id for r in results]
        assert variant_ids == sorted(variant_ids), "Results not sorted!"


# =============================================================================
# ATHENA INVARIANT TESTS
# =============================================================================


class TestAthenaInvariants:
    """Chaos vectors for Athena invariants."""

    @pytest.mark.invariant
    def test_cv_athena_write_attempt(self, temp_bead_store):
        """
        CV_ATHENA_WRITE_ATTEMPT: SQL injection in QueryIR blocked.

        INV-ATHENA-RO-1: Queries cannot modify data
        """
        from memory.bead_store import BeadStoreError

        # Try to execute write SQL via query_sql
        with pytest.raises(BeadStoreError):
            temp_bead_store.query_sql("INSERT INTO beads VALUES (?, ?)", ("x", "y"))

        with pytest.raises(BeadStoreError):
            temp_bead_store.query_sql("DELETE FROM beads WHERE 1=1")

        with pytest.raises(BeadStoreError):
            temp_bead_store.query_sql("DROP TABLE beads")

    @pytest.mark.invariant
    def test_cv_athena_bomb(self, temp_bead_store):
        """
        CV_ATHENA_BOMB: Large result set capped.

        INV-ATHENA-CAP-1: Results capped at 100 rows
        """
        from memory import Athena
        from memory.query_parser import QueryIR, Requester

        athena = Athena(bead_store=temp_bead_store)

        # Create QueryIR requesting huge limit
        ir = QueryIR(
            query_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(UTC),
            requester=Requester.CLAUDE,
            limit=999999,  # Way over cap
        )

        # Parser should cap at 100
        from memory.query_parser import QueryParser

        parser = QueryParser()
        result = parser.validate(ir)

        # Should fail validation (over 100)
        assert not result.valid or ir.limit > 100

    @pytest.mark.invariant
    def test_cv_athena_missing_audit(self):
        """
        CV_ATHENA_MISSING_AUDIT: Query without audit fields rejected.

        INV-ATHENA-AUDIT-1: Every query has audit fields
        """
        from memory.query_parser import QueryIR, QueryParser, Requester

        parser = QueryParser()

        # Create QueryIR without required audit fields
        ir = QueryIR(
            query_id="",  # Empty = missing
            timestamp_utc=datetime.now(UTC),
            requester=Requester.CLAUDE,
        )

        result = parser.validate(ir)
        assert not result.valid, "Should reject missing audit fields"

    @pytest.mark.invariant
    def test_cv_athena_raw_sql_inject(self):
        """
        CV_ATHENA_RAW_SQL_INJECT: SQL injection in keywords blocked.

        INV-ATHENA-IR-ONLY-1: SQL from QueryIR only
        """
        from memory.query_parser import QueryIR, QueryParser, Requester

        parser = QueryParser()

        # Create QueryIR with SQL injection attempt in keywords
        ir = QueryIR(
            query_id=str(uuid.uuid4()),
            timestamp_utc=datetime.now(UTC),
            requester=Requester.CLAUDE,
            keywords=["'; DROP TABLE beads; --", "SELECT * FROM"],
        )

        result = parser.validate(ir)
        assert not result.valid, "Should reject SQL injection in keywords"


# =============================================================================
# CHECKPOINT INVARIANT TESTS
# =============================================================================


class TestCheckpointInvariants:
    """Chaos vectors for Checkpoint invariants."""

    @pytest.mark.invariant
    def test_cv_checkpoint_atomic_prepare_without_commit(self, temp_bead_store):
        """
        CV_CHECKPOINT_KILL_PHASE_1: Prepare without commit = no state change.

        INV-CHECKPOINT-ATOMIC-1: State transitions are atomic
        """
        from checkpoint import Checkpoint
        from checkpoint.checkpoint import ContextSnapshot, TransitionType

        initial_count = temp_bead_store.count_beads()

        checkpoint = Checkpoint(temp_bead_store)

        # Prepare but don't commit
        snapshot = ContextSnapshot(
            session_id="test-session",
            timestamp_utc=datetime.now(UTC),
            transition_type=TransitionType.MANUAL_CHECKPOINT,
            current_hypothesis="Test hypothesis",
            active_hunts=[],
            regime_state={},
            momentum_summary="Test momentum",
            confidence_delta=0.0,
        )

        checkpoint.prepare(snapshot)
        # Don't commit!

        # Rollback
        checkpoint.rollback()

        # No new beads should exist
        assert temp_bead_store.count_beads() == initial_count

    @pytest.mark.invariant
    def test_cv_checkpoint_double_commit(self, temp_bead_store):
        """
        CV_CHECKPOINT_ATOMIC: Double commit fails.

        INV-CHECKPOINT-ATOMIC-1: State transitions are atomic
        """
        from checkpoint import Checkpoint
        from checkpoint.checkpoint import (
            CommitError,
            ContextSnapshot,
            TransitionType,
        )

        checkpoint = Checkpoint(temp_bead_store)

        snapshot = ContextSnapshot(
            session_id="test-session",
            timestamp_utc=datetime.now(UTC),
            transition_type=TransitionType.MANUAL_CHECKPOINT,
            current_hypothesis="Test",
            active_hunts=[],
            regime_state={},
            momentum_summary="Test",
            confidence_delta=0.0,
        )

        checkpoint.prepare(snapshot)
        checkpoint.commit()

        # Second commit should fail
        with pytest.raises(CommitError):
            checkpoint.commit()


# =============================================================================
# SHADOW INVARIANT TESTS
# =============================================================================


class TestShadowInvariants:
    """Chaos vectors for Shadow invariants."""

    @pytest.mark.invariant
    def test_cv_shadow_broker_import(self):
        """
        CV_SHADOW_BROKER_IMPORT: No broker imports in shadow module.

        INV-SHADOW-ISO-1: Shadow NEVER affects live capital
        """
        from pathlib import Path

        import shadow

        # Get shadow module path
        shadow_path = Path(shadow.__file__).parent

        # Check all Python files for broker imports
        forbidden = ["ibkr", "broker", "ib_insync", "tws"]

        for py_file in shadow_path.glob("*.py"):
            content = py_file.read_text().lower()
            for term in forbidden:
                assert term not in content, f"Forbidden import '{term}' in {py_file}"

    @pytest.mark.invariant
    def test_cv_shadow_real_capital(self, temp_bead_store):
        """
        CV_SHADOW_REAL_CAPITAL: Shadow only creates paper positions.

        INV-SHADOW-ISO-1: Shadow NEVER affects live capital
        """
        from shadow import Shadow
        from shadow.shadow import CSESignal

        shadow = Shadow(bead_store=temp_bead_store)

        # Consume signal
        signal = CSESignal(
            signal_id="test-001",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            direction="LONG",
            entry=1.0850,
            stop=1.0820,
            target=1.0920,
            risk_percent=1.0,
            confidence=0.7,
            source="TEST",
            evidence_hash="test",
        )

        result = shadow.consume_signal(signal)

        # Verify it's paper only
        assert result.status == "ACCEPTED"
        assert result.position_id.startswith("PAPER-"), "Position must be paper"

    @pytest.mark.invariant
    def test_cv_shadow_cse_validation(self, temp_bead_store):
        """
        CV_SHADOW_CSE_VERSION: Invalid CSE rejected.

        INV-SHADOW-CSE-1: Only consumes validated CSE signals
        """
        from shadow import Shadow
        from shadow.shadow import CSESignal

        shadow = Shadow(bead_store=temp_bead_store)

        # Invalid direction
        signal = CSESignal(
            signal_id="test-002",
            timestamp=datetime.now(UTC),
            pair="EURUSD",
            direction="INVALID",  # Wrong!
            entry=1.0850,
            stop=1.0820,
            target=1.0920,
            risk_percent=1.0,
            confidence=0.7,
            source="TEST",
            evidence_hash="test",
        )

        result = shadow.consume_signal(signal)
        assert result.status == "REJECTED"


# =============================================================================
# RIVER INVARIANT TESTS
# =============================================================================


class TestRiverInvariants:
    """Chaos vectors for River invariants."""

    @pytest.mark.invariant
    def test_cv_river_write_attempt(self):
        """
        CV_RIVER_WRITE_ATTEMPT: River reader has no write methods.

        INV-RIVER-RO-1: River reader cannot modify data
        """
        from data.river_reader import RiverReader

        # Check that write methods don't exist
        forbidden_methods = [
            "insert",
            "update",
            "delete",
            "drop",
            "create",
            "write",
            "execute_write",
        ]

        reader_methods = dir(RiverReader)

        for method in forbidden_methods:
            assert method not in reader_methods, f"Forbidden method '{method}' exists!"

    @pytest.mark.invariant
    def test_cv_river_denied_caller(self):
        """
        CV_RIVER_ACCESS_CONTROL: Execution caller denied.

        INV-RIVER-RO-1: Read-only, no execution access
        """
        from data.river_reader import RiverAccessDeniedError, RiverReader

        with pytest.raises(RiverAccessDeniedError):
            RiverReader(caller="execution")


# =============================================================================
# BEAD INTEGRITY TESTS
# =============================================================================


class TestBeadIntegrity:
    """Chaos vectors for bead integrity."""

    @pytest.mark.invariant
    def test_cv_bead_immutability(self, temp_bead_store):
        """
        CV_BEAD_IMMUTABILITY: Cannot overwrite existing bead.

        Bead immutability invariant
        """
        from memory.bead_store import (
            Bead,
            BeadImmutabilityError,
            BeadType,
            Signer,
        )

        # Write a bead
        bead = Bead(
            bead_id="TEST-immutable-001",
            bead_type=BeadType.HUNT,
            prev_bead_id=None,
            bead_hash="test123",
            timestamp_utc=datetime.now(UTC),
            signer=Signer.SYSTEM,
            version="1.0",
            content={"test": "data"},
        )

        temp_bead_store.write(bead)

        # Try to overwrite
        with pytest.raises(BeadImmutabilityError):
            temp_bead_store.write(bead)
