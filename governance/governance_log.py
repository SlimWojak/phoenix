"""
Governance Log — Unified append-only event log for Bridge consumption.

Sprint: S62 BRIDGE_BUILD (Track A, Phase 1)

Single sequential JSONL file with monotonic counters, hash chaining, and
HMAC-SHA256 signatures. Composes with DurableBeadEmitter (per-type JSONL
files continue unchanged).

Entry fields:
  seq             — Monotonic counter (replay_guard source, athena_index)
  event_type      — String from closed whitelist (BRIDGE_SPEC_v0.2 Section 2.1)
  payload         — Canonical JSON of governance event content
  timestamp       — ISO 8601 server-side monotonic (GT source)
  hash_prev       — SHA-256 of previous entry's hashable content
  athena_index    — = seq (sequence position in log)
  athena_hash     — SHA-256 of this entry's hashable content
  source_signature — {sig, algorithm, key_id}

INVARIANTS:
  INV-GOV-LOG-SEQUENTIAL: seq never decreases, gap-free
  INV-GOV-LOG-CHAINED: Each entry carries hash of previous entry
  INV-GOV-LOG-SIGNED: Each entry carries HMAC-SHA256 over athena_hash
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import secrets
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

DEFAULT_LOG_DIR = Path.home() / "phoenix" / "data"
DEFAULT_KEY_DIR = Path.home() / "phoenix" / "data" / "governance_keys"
GENESIS_HASH = "0" * 64

GOVERNANCE_EVENT_TYPES = frozenset(
    {
        "CARTRIDGE_INSERTION",
        "CARTRIDGE_REMOVAL",
        "CALIBRATION",
        "STRATEGY_DEPRECATION",
        "LEASE_ACTIVATION",
        "LEASE_EXPIRY",
        "LEASE_REVOCATION",
        "LEASE_HALT",
        "ATTESTATION",
        "CEREMONY",
        "STATE_LOCK",
        "MARGIN_CONTENTION",
        "EMERGENCY_EJECT",
    }
)

BEAD_TYPE_TO_EVENT_TYPE: dict[str, str] = {
    "CARTRIDGE_INSERTION_BEAD": "CARTRIDGE_INSERTION",
    "CARTRIDGE_REMOVAL_BEAD": "CARTRIDGE_REMOVAL",
    "CALIBRATION_BEAD": "CALIBRATION",
    "LEASE_ACTIVATION_BEAD": "LEASE_ACTIVATION",
    "LEASE_EXPIRY_BEAD": "LEASE_EXPIRY",
    "LEASE_REVOCATION_BEAD": "LEASE_REVOCATION",
    "LEASE_HALT_BEAD": "LEASE_HALT",
    "ATTESTATION_BEAD": "ATTESTATION",
    "CEREMONY_ATTESTATION_BEAD": "CEREMONY",
    "STATE_LOCK_BEAD": "STATE_LOCK",
    "EMERGENCY_EJECT_BEAD": "EMERGENCY_EJECT",
}


class GovernanceLogError(Exception):
    """Raised on log integrity failures — caller should HALT."""


def _canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _compute_entry_hash(
    seq: int,
    event_type: str,
    payload: dict[str, Any],
    timestamp: str,
    hash_prev: str,
) -> str:
    hashable = {
        "seq": seq,
        "event_type": event_type,
        "payload": payload,
        "timestamp": timestamp,
        "hash_prev": hash_prev,
    }
    return _sha256_hex(_canonical_json(hashable))


def _hmac_sign(key: bytes, hash_hex: str) -> str:
    return hmac.new(key, hash_hex.encode("utf-8"), hashlib.sha256).hexdigest()


def load_or_create_key(key_dir: Path, key_id: str = "phoenix-gov-v1") -> bytes:
    """Load signing key from disk, or generate and persist a new one."""
    key_dir.mkdir(parents=True, exist_ok=True)
    key_path = key_dir / f"{key_id}.key"
    if key_path.exists():
        return key_path.read_bytes()
    key = secrets.token_bytes(32)
    fd = os.open(str(key_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, key)
    finally:
        os.close(fd)
    log.info("Generated governance signing key: %s", key_path)
    return key


def verify_entry_signature(key: bytes, athena_hash: str, signature: str) -> bool:
    """Verify HMAC-SHA256 signature on a governance log entry."""
    expected = _hmac_sign(key, athena_hash)
    return hmac.compare_digest(expected, signature)


class GovernanceLog:
    """Unified append-only governance event log.

    Thread-safe. Recovery from last entry on startup. Raises on corruption.
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        key_dir: Path | None = None,
        key_id: str = "phoenix-gov-v1",
    ) -> None:
        self._log_dir = log_dir or DEFAULT_LOG_DIR
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._log_dir / "governance_log.jsonl"
        self._key_id = key_id
        self._key = load_or_create_key(key_dir or DEFAULT_KEY_DIR, key_id)
        self._lock = threading.Lock()
        self._seq, self._hash_prev = self._recover_state()

    def _recover_state(self) -> tuple[int, str]:
        if not self._log_path.exists() or self._log_path.stat().st_size == 0:
            return 0, GENESIS_HASH

        last_line = ""
        try:
            with open(self._log_path) as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
        except OSError as exc:
            raise GovernanceLogError(f"Cannot read governance log: {exc}") from exc

        if not last_line:
            return 0, GENESIS_HASH

        try:
            entry = json.loads(last_line)
            seq = entry["seq"]
            hash_self = _compute_entry_hash(
                seq=entry["seq"],
                event_type=entry["event_type"],
                payload=entry["payload"],
                timestamp=entry["timestamp"],
                hash_prev=entry["hash_prev"],
            )
            return seq, hash_self
        except (json.JSONDecodeError, KeyError) as exc:
            raise GovernanceLogError(
                f"Corrupt governance log — cannot recover from last entry: {exc}"
            ) from exc

    @property
    def sequence(self) -> int:
        return self._seq

    @property
    def last_hash(self) -> str:
        return self._hash_prev

    @property
    def log_path(self) -> Path:
        return self._log_path

    @property
    def key_id(self) -> str:
        return self._key_id

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Append a governance event. Returns the complete entry.

        Raises GovernanceLogError on unknown event_type or write failure.
        """
        if event_type not in GOVERNANCE_EVENT_TYPES:
            raise GovernanceLogError(
                f"Unknown event_type '{event_type}'. "
                f"Closed whitelist: {sorted(GOVERNANCE_EVENT_TYPES)}"
            )

        with self._lock:
            self._seq += 1
            timestamp = datetime.now(UTC).isoformat()

            hash_self = _compute_entry_hash(
                seq=self._seq,
                event_type=event_type,
                payload=payload,
                timestamp=timestamp,
                hash_prev=self._hash_prev,
            )

            entry = {
                "seq": self._seq,
                "event_type": event_type,
                "payload": payload,
                "timestamp": timestamp,
                "hash_prev": self._hash_prev,
                "athena_index": self._seq,
                "athena_hash": hash_self,
                "source_signature": {
                    "sig": _hmac_sign(self._key, hash_self),
                    "algorithm": "hmac-sha256",
                    "key_id": self._key_id,
                },
            }

            line = _canonical_json(entry) + "\n"

            fd = os.open(str(self._log_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
            try:
                os.write(fd, line.encode("utf-8"))
                os.fsync(fd)
            finally:
                os.close(fd)

            self._hash_prev = hash_self
            log.info(
                "Governance log: seq=%d event=%s hash=%s",
                self._seq,
                event_type,
                hash_self[:16],
            )
            return entry

    def append_bead(self, bead_type: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """Map Phoenix bead_type to Bridge event_type and append.

        Returns None if bead_type has no governance event mapping.
        """
        event_type = BEAD_TYPE_TO_EVENT_TYPE.get(bead_type)
        if event_type is None:
            return None
        return self.append(event_type, payload)

    def verify_chain(self) -> tuple[bool, int, str]:
        """Walk entire log, verify hash chain and signatures.

        Returns: (valid, entries_verified, error_description)
        """
        if not self._log_path.exists():
            return True, 0, ""

        prev_hash = GENESIS_HASH
        count = 0
        expected_seq = 0

        with open(self._log_path) as f:
            for line_num, raw_line in enumerate(f, 1):
                stripped = raw_line.strip()
                if not stripped:
                    continue

                try:
                    entry = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    return False, count, f"Line {line_num}: invalid JSON: {exc}"

                expected_seq += 1
                if entry.get("seq") != expected_seq:
                    return (
                        False,
                        count,
                        (
                            f"Line {line_num}: seq gap — "
                            f"expected {expected_seq}, got {entry.get('seq')}"
                        ),
                    )

                if entry.get("hash_prev") != prev_hash:
                    return (
                        False,
                        count,
                        (
                            f"Line {line_num}: hash_prev mismatch — "
                            f"expected {prev_hash[:16]}..., got "
                            f"{str(entry.get('hash_prev', 'MISSING'))[:16]}..."
                        ),
                    )

                computed = _compute_entry_hash(
                    seq=entry["seq"],
                    event_type=entry["event_type"],
                    payload=entry["payload"],
                    timestamp=entry["timestamp"],
                    hash_prev=entry["hash_prev"],
                )

                sig_data = entry.get("source_signature", {})
                if not verify_entry_signature(self._key, computed, sig_data.get("sig", "")):
                    return False, count, f"Line {line_num}: signature verification failed"

                prev_hash = computed
                count += 1

        return True, count, ""
