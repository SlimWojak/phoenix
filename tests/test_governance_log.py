"""
Tests for GovernanceLog — S62 Bridge Build exit gate.

EXIT GATE CRITERIA (from CTO ruling):
  - Write 3 events → verify monotonic counter
  - Verify signature on each entry
  - Verify hash_prev chain links
  - Corrupt one entry → verification fails on next read
  - Existing DurableBeadEmitter tests still pass

INVARIANTS:
  INV-GOV-LOG-SEQUENTIAL: seq never decreases, gap-free
  INV-GOV-LOG-CHAINED: Each entry carries hash of previous entry
  INV-GOV-LOG-SIGNED: Each entry carries HMAC-SHA256 over athena_hash
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

import pytest

from governance.governance_log import (
    BEAD_TYPE_TO_EVENT_TYPE,
    GENESIS_HASH,
    GOVERNANCE_EVENT_TYPES,
    GovernanceLog,
    GovernanceLogError,
)


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    d = tmp_path / "gov_log"
    d.mkdir()
    return d


@pytest.fixture()
def key_dir(tmp_path: Path) -> Path:
    d = tmp_path / "gov_keys"
    d.mkdir()
    return d


@pytest.fixture()
def gov_log(log_dir: Path, key_dir: Path) -> GovernanceLog:
    return GovernanceLog(log_dir=log_dir, key_dir=key_dir)


def _sample_payload(lease_id: str = "lease_001") -> dict[str, Any]:
    return {
        "lease_id": lease_id,
        "strategy_ref": "TEST_STRAT_v1.0.0",
        "bounds_snapshot": {"max_drawdown_pct": 5.0},
    }


class TestMonotonicCounter:
    """INV-GOV-LOG-SEQUENTIAL"""

    def test_three_events_have_sequential_counters(self, gov_log: GovernanceLog) -> None:
        e1 = gov_log.append("LEASE_ACTIVATION", _sample_payload())
        e2 = gov_log.append(
            "CALIBRATION",
            {"cartridge_ref": "X_v1.0.0", "lease_id": "l1", "drift_pct": 2.1, "verdict": "PASS"},
        )
        e3 = gov_log.append("LEASE_EXPIRY", {"lease_id": "lease_001", "final_stats": {}})

        assert e1["seq"] == 1
        assert e2["seq"] == 2
        assert e3["seq"] == 3
        assert gov_log.sequence == 3

    def test_athena_index_equals_seq(self, gov_log: GovernanceLog) -> None:
        entry = gov_log.append("LEASE_ACTIVATION", _sample_payload())
        assert entry["athena_index"] == entry["seq"]

    def test_seq_never_resets_within_instance(self, gov_log: GovernanceLog) -> None:
        for i in range(5):
            entry = gov_log.append(
                "STATE_LOCK",
                {
                    "lease_id": f"l{i}",
                    "prior_state": "ACTIVE",
                    "prior_state_hash": "abc",
                    "requested_transition": "ACTIVE→HALTED",
                    "transition_result": "SUCCESS",
                },
            )
            assert entry["seq"] == i + 1


class TestSignatureVerification:
    """INV-GOV-LOG-SIGNED"""

    def test_each_entry_has_valid_signature(self, gov_log: GovernanceLog) -> None:
        gov_log.append("LEASE_ACTIVATION", _sample_payload())
        gov_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})
        gov_log.append("ATTESTATION", {"lease_id": "l1", "decision": "RENEW", "new_lease_id": None})

        valid, count, err = gov_log.verify_chain()
        assert valid, f"Chain verification failed: {err}"
        assert count == 3

    def test_signature_algorithm_and_key_id_present(self, gov_log: GovernanceLog) -> None:
        entry = gov_log.append("LEASE_ACTIVATION", _sample_payload())
        sig = entry["source_signature"]
        assert sig["algorithm"] == "hmac-sha256"
        assert sig["key_id"] == "phoenix-gov-v1"
        assert len(sig["sig"]) == 64  # SHA-256 hex

    def test_tampered_signature_detected(
        self, gov_log: GovernanceLog, log_dir: Path, key_dir: Path
    ) -> None:
        gov_log.append("LEASE_ACTIVATION", _sample_payload())
        gov_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        log_path = log_dir / "governance_log.jsonl"
        lines = log_path.read_text().strip().split("\n")
        entry = json.loads(lines[1])
        entry["source_signature"]["sig"] = "f" * 64
        lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        log_path.write_text("\n".join(lines) + "\n")

        verifier = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        valid, count, err = verifier.verify_chain()
        assert not valid
        assert "signature verification failed" in err


class TestHashChain:
    """INV-GOV-LOG-CHAINED"""

    def test_first_entry_links_to_genesis(self, gov_log: GovernanceLog) -> None:
        entry = gov_log.append("LEASE_ACTIVATION", _sample_payload())
        assert entry["hash_prev"] == GENESIS_HASH

    def test_subsequent_entries_chain_to_previous(self, gov_log: GovernanceLog) -> None:
        e1 = gov_log.append("LEASE_ACTIVATION", _sample_payload())
        e2 = gov_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})
        assert e2["hash_prev"] == e1["athena_hash"]
        assert e2["hash_prev"] != GENESIS_HASH

    def test_full_chain_verifies(self, gov_log: GovernanceLog) -> None:
        for i in range(10):
            gov_log.append(
                "STATE_LOCK",
                {
                    "lease_id": f"l{i}",
                    "prior_state": "ACTIVE",
                    "prior_state_hash": "a" * 16,
                    "requested_transition": "test",
                    "transition_result": "SUCCESS",
                },
            )

        valid, count, err = gov_log.verify_chain()
        assert valid, f"Chain failed at entry {count}: {err}"
        assert count == 10


class TestCorruptionDetection:
    """EXIT GATE: Corrupt one entry → verification fails on next read"""

    def test_corrupted_payload_breaks_chain(
        self, gov_log: GovernanceLog, log_dir: Path, key_dir: Path
    ) -> None:
        gov_log.append("LEASE_ACTIVATION", _sample_payload("lease_a"))
        gov_log.append("LEASE_ACTIVATION", _sample_payload("lease_b"))
        gov_log.append("LEASE_ACTIVATION", _sample_payload("lease_c"))

        log_path = log_dir / "governance_log.jsonl"
        lines = log_path.read_text().strip().split("\n")
        entry = json.loads(lines[1])
        entry["payload"]["lease_id"] = "TAMPERED"
        lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        log_path.write_text("\n".join(lines) + "\n")

        verifier = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        valid, count, err = verifier.verify_chain()
        assert not valid
        assert count == 1  # first entry OK, second fails

    def test_corrupted_hash_prev_detected(
        self, gov_log: GovernanceLog, log_dir: Path, key_dir: Path
    ) -> None:
        gov_log.append("LEASE_ACTIVATION", _sample_payload())
        gov_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        log_path = log_dir / "governance_log.jsonl"
        lines = log_path.read_text().strip().split("\n")
        entry = json.loads(lines[1])
        entry["hash_prev"] = "dead" * 16
        lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        log_path.write_text("\n".join(lines) + "\n")

        verifier = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        valid, count, err = verifier.verify_chain()
        assert not valid
        assert "hash_prev mismatch" in err

    def test_corrupted_seq_detected(
        self, gov_log: GovernanceLog, log_dir: Path, key_dir: Path
    ) -> None:
        gov_log.append("LEASE_ACTIVATION", _sample_payload())
        gov_log.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})

        log_path = log_dir / "governance_log.jsonl"
        lines = log_path.read_text().strip().split("\n")
        entry = json.loads(lines[1])
        entry["seq"] = 99
        lines[1] = json.dumps(entry, sort_keys=True, separators=(",", ":"))
        log_path.write_text("\n".join(lines) + "\n")

        verifier = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        valid, count, err = verifier.verify_chain()
        assert not valid
        assert "seq gap" in err

    def test_invalid_json_in_middle_detected(
        self, gov_log: GovernanceLog, log_dir: Path, key_dir: Path
    ) -> None:
        gov_log.append("LEASE_ACTIVATION", _sample_payload("l1"))
        gov_log.append("LEASE_ACTIVATION", _sample_payload("l2"))
        gov_log.append("LEASE_ACTIVATION", _sample_payload("l3"))

        log_path = log_dir / "governance_log.jsonl"
        lines = log_path.read_text().strip().split("\n")
        lines[1] = "{not valid json"
        log_path.write_text("\n".join(lines) + "\n")

        verifier = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        valid, _, err = verifier.verify_chain()
        assert not valid
        assert "invalid JSON" in err


class TestRecoveryAfterRestart:
    """GovernanceLog resumes from last entry across instances."""

    def test_new_instance_continues_sequence(self, log_dir: Path, key_dir: Path) -> None:
        log1 = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        log1.append("LEASE_ACTIVATION", _sample_payload())
        log1.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})
        assert log1.sequence == 2

        log2 = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        assert log2.sequence == 2

        e3 = log2.append(
            "ATTESTATION", {"lease_id": "l1", "decision": "RENEW", "new_lease_id": None}
        )
        assert e3["seq"] == 3

        valid, count, _ = log2.verify_chain()
        assert valid
        assert count == 3

    def test_hash_prev_continuity_across_restart(self, log_dir: Path, key_dir: Path) -> None:
        log1 = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        e1 = log1.append("LEASE_ACTIVATION", _sample_payload())
        last_hash = e1["athena_hash"]

        log2 = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        assert log2.last_hash == last_hash

        e2 = log2.append("LEASE_EXPIRY", {"lease_id": "l1", "final_stats": {}})
        assert e2["hash_prev"] == last_hash

    def test_corrupt_last_entry_raises_on_recovery(self, log_dir: Path, key_dir: Path) -> None:
        log1 = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        log1.append("LEASE_ACTIVATION", _sample_payload())

        log_path = log_dir / "governance_log.jsonl"
        log_path.write_text("{corrupt\n")

        with pytest.raises(GovernanceLogError, match="Corrupt"):
            GovernanceLog(log_dir=log_dir, key_dir=key_dir)


class TestEventTypeWhitelist:
    """Bridge spec closed whitelist enforcement."""

    def test_all_13_event_types_accepted(self, gov_log: GovernanceLog) -> None:
        for event_type in sorted(GOVERNANCE_EVENT_TYPES):
            entry = gov_log.append(event_type, {"test": True})
            assert entry["event_type"] == event_type
        assert gov_log.sequence == 13

    def test_unknown_event_type_rejected(self, gov_log: GovernanceLog) -> None:
        with pytest.raises(GovernanceLogError, match="Unknown event_type"):
            gov_log.append("INVENTED_EVENT", {"test": True})
        assert gov_log.sequence == 0

    def test_heartbeat_not_in_phoenix_log(self, gov_log: GovernanceLog) -> None:
        with pytest.raises(GovernanceLogError, match="Unknown event_type"):
            gov_log.append("HEARTBEAT", {})


class TestBeadTypeMapping:
    """Phoenix bead_type → Bridge event_type mapping."""

    def test_all_known_bead_types_map(self, gov_log: GovernanceLog) -> None:
        for bead_type, event_type in BEAD_TYPE_TO_EVENT_TYPE.items():
            entry = gov_log.append_bead(bead_type, {"mapped": True})
            assert entry is not None
            assert entry["event_type"] == event_type

    def test_unknown_bead_type_returns_none(self, gov_log: GovernanceLog) -> None:
        result = gov_log.append_bead("UNKNOWN_BEAD_TYPE", {"test": True})
        assert result is None
        assert gov_log.sequence == 0

    def test_mapping_covers_all_governance_events(self) -> None:
        mapped_events = set(BEAD_TYPE_TO_EVENT_TYPE.values())
        unmapped = GOVERNANCE_EVENT_TYPES - mapped_events
        expected_unmapped = {"STRATEGY_DEPRECATION", "MARGIN_CONTENTION"}
        assert (
            unmapped == expected_unmapped
        ), f"Unexpected unmapped events: {unmapped - expected_unmapped}"


class TestThreadSafety:
    """Concurrent appends produce gap-free sequential counters."""

    def test_concurrent_appends_are_sequential(self, log_dir: Path, key_dir: Path) -> None:
        gov_log = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        n_threads = 8
        n_per_thread = 10
        errors: list[str] = []

        def writer(thread_id: int) -> None:
            try:
                for i in range(n_per_thread):
                    gov_log.append(
                        "STATE_LOCK",
                        {
                            "thread": thread_id,
                            "iter": i,
                            "lease_id": f"l_{thread_id}_{i}",
                            "prior_state": "ACTIVE",
                            "prior_state_hash": "a" * 16,
                            "requested_transition": "test",
                            "transition_result": "SUCCESS",
                        },
                    )
            except Exception as exc:
                errors.append(str(exc))

        threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        assert gov_log.sequence == n_threads * n_per_thread

        valid, count, err = gov_log.verify_chain()
        assert valid, f"Chain broken: {err}"
        assert count == n_threads * n_per_thread


class TestEmptyLogBehavior:
    """Edge cases for fresh / empty logs."""

    def test_fresh_log_has_zero_seq_and_genesis_hash(self, gov_log: GovernanceLog) -> None:
        assert gov_log.sequence == 0
        assert gov_log.last_hash == GENESIS_HASH

    def test_verify_chain_on_empty_log(self, gov_log: GovernanceLog) -> None:
        valid, count, err = gov_log.verify_chain()
        assert valid
        assert count == 0

    def test_log_path_correct(self, gov_log: GovernanceLog, log_dir: Path) -> None:
        assert gov_log.log_path == log_dir / "governance_log.jsonl"


class TestDurableBeadEmitterIntegration:
    """GovernanceLog called by DurableBeadEmitter after per-type write."""

    def test_emitter_writes_to_both_per_type_and_unified_log(self, tmp_path: Path) -> None:
        bead_dir = tmp_path / "beads"
        bead_dir.mkdir()
        log_dir = tmp_path / "log"
        log_dir.mkdir()
        key_dir = tmp_path / "keys"
        key_dir.mkdir()

        from governance.bead_emitter import DurableBeadEmitter
        from governance.governance_log import GovernanceLog
        from governance.lease_types import LeaseActivationBead

        gov_log = GovernanceLog(log_dir=log_dir, key_dir=key_dir)
        emitter = DurableBeadEmitter(bead_dir=bead_dir, governance_log=gov_log)

        bead = LeaseActivationBead(
            lease_id="lease_int_001",
            strategy_ref="INT_STRAT_v1.0.0",
            bounds_snapshot={"max_drawdown_pct": 5.0},
        )
        emitter.emit(bead)

        per_type = bead_dir / "LEASE_ACTIVATION_BEAD.jsonl"
        assert per_type.exists()
        unified = log_dir / "governance_log.jsonl"
        assert unified.exists()

        entry = json.loads(unified.read_text().strip())
        assert entry["event_type"] == "LEASE_ACTIVATION"
        assert entry["seq"] == 1
        assert entry["payload"]["lease_id"] == "lease_int_001"

    def test_emitter_without_governance_log_unchanged(self, tmp_path: Path) -> None:
        bead_dir = tmp_path / "beads"
        bead_dir.mkdir()

        from governance.bead_emitter import DurableBeadEmitter
        from governance.lease_types import LeaseActivationBead

        emitter = DurableBeadEmitter(bead_dir=bead_dir)
        bead = LeaseActivationBead(
            lease_id="lease_no_log",
            strategy_ref="NOLOG_v1.0.0",
            bounds_snapshot={},
        )
        emitter.emit(bead)

        per_type = bead_dir / "LEASE_ACTIVATION_BEAD.jsonl"
        assert per_type.exists()
