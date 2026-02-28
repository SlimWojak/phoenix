"""
Durable Bead Emitter — Write-ahead governance bead persistence.

Sprint: S59 LEASE_WIRE (Track 2: WRITE_AHEAD_GOVERNANCE)

Design: Governance beads persist to disk BEFORE state mutation returns.
Pattern: Append-only JSONL file, one file per governance action type.

Boot recovery: On boot, check for orphaned active leases (started_bead
exists but no committed_bead AND non-terminal state). Orphan → auto-HALT.

INVARIANTS:
  INV-GOVERNANCE-MUTATION-ATOMIC: State mutates only after durable bead write succeeds
  INV-GOV-BEAD-IDEMPOTENT: Deterministic bead ID prevents retry duplicates
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .governance_log import GovernanceLog
    from .lease_types import BeadType

log = logging.getLogger(__name__)

DEFAULT_GOV_BEAD_DIR = Path.home() / "phoenix" / "data" / "governance_beads"


def _compute_bead_id(bead_data: dict[str, Any]) -> str:
    """
    Deterministic bead ID from content hash.

    INV-GOV-BEAD-IDEMPOTENT: Same bead content → same ID.
    Retries produce the same write, not duplicates.
    """
    canonical = json.dumps(bead_data, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class DurableBeadEmitter:
    """
    Durable governance bead emitter — append-only JSONL on disk.

    Replaces NullBeadEmitter for production use.
    Implements the BeadEmitter protocol from governance/lease.py.

    Each emit():
      1. Serialize bead to JSON
      2. Compute deterministic bead_id
      3. Append to JSONL file (with fsync)
      4. Return only after durable write confirms

    On failure: raises (never silently drops beads).
    """

    def __init__(
        self,
        bead_dir: Path | None = None,
        governance_log: GovernanceLog | None = None,
    ) -> None:
        self._bead_dir = bead_dir or DEFAULT_GOV_BEAD_DIR
        self._bead_dir.mkdir(parents=True, exist_ok=True)
        self._governance_log = governance_log
        self.beads: list[BeadType] = []

    def emit(self, bead: BeadType) -> None:
        """
        Persist bead to disk, then keep in memory for assertions.

        INV-GOVERNANCE-MUTATION-ATOMIC: This must succeed before caller mutates state.
        Raises on any write failure (disk full, permissions, etc.).
        """
        bead_data = bead.model_dump(mode="json")
        bead_type = bead_data.get("bead_type", "UNKNOWN")

        bead_id = _compute_bead_id(bead_data)
        bead_data["_bead_id"] = bead_id
        bead_data["_persisted_at"] = datetime.now(UTC).isoformat()

        jsonl_path = self._bead_dir / f"{bead_type}.jsonl"

        if self._bead_id_exists(jsonl_path, bead_id):
            log.info("Bead %s already persisted (idempotent skip)", bead_id)
            self.beads.append(bead)
            return

        line = json.dumps(bead_data, default=str, sort_keys=True) + "\n"

        fd = os.open(str(jsonl_path), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        try:
            os.write(fd, line.encode("utf-8"))
            os.fsync(fd)
        finally:
            os.close(fd)

        self.beads.append(bead)
        log.info("Governance bead persisted: type=%s id=%s path=%s", bead_type, bead_id, jsonl_path)

        if self._governance_log is not None:
            try:
                self._governance_log.append_bead(bead_type, bead_data)
            except Exception:
                log.exception(
                    "Governance log append failed for %s (per-type write succeeded)",
                    bead_type,
                )

    def _bead_id_exists(self, jsonl_path: Path, bead_id: str) -> bool:
        """Check if bead_id already exists in the JSONL file (idempotency guard)."""
        if not jsonl_path.exists():
            return False
        try:
            with open(jsonl_path) as f:
                for raw_line in f:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        entry = json.loads(raw_line)
                        if entry.get("_bead_id") == bead_id:
                            return True
                    except json.JSONDecodeError:
                        continue
        except OSError:
            return False
        return False

    def read_beads(self, bead_type: str) -> list[dict[str, Any]]:
        """Read all persisted beads of a given type (for boot recovery / queries)."""
        jsonl_path = self._bead_dir / f"{bead_type}.jsonl"
        if not jsonl_path.exists():
            return []

        beads: list[dict[str, Any]] = []
        with open(jsonl_path) as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    beads.append(json.loads(raw_line))
                except json.JSONDecodeError:
                    log.warning("Corrupt bead entry in %s, skipping", jsonl_path)
        return beads


def check_orphaned_leases(bead_dir: Path | None = None) -> list[dict[str, Any]]:
    """
    Boot recovery: detect orphaned active leases.

    Orphan criteria (formalized per Advisory Flag 3):
      - LEASE_ACTIVATION_BEAD exists (started)
      - No corresponding terminal bead (LEASE_EXPIRY_BEAD or LEASE_REVOCATION_BEAD)
      - Not currently ACTIVE in LeaseManager

    Returns list of orphan records (empty = clean boot).
    """
    bead_dir = bead_dir or DEFAULT_GOV_BEAD_DIR
    emitter = DurableBeadEmitter(bead_dir)

    activations = emitter.read_beads("LEASE_ACTIVATION_BEAD")
    expiries = emitter.read_beads("LEASE_EXPIRY_BEAD")
    revocations = emitter.read_beads("LEASE_REVOCATION_BEAD")
    halts = emitter.read_beads("LEASE_HALT_BEAD")

    terminal_lease_ids: set[str] = set()
    for bead in expiries + revocations:
        lid = bead.get("lease_id")
        if lid:
            terminal_lease_ids.add(lid)

    halted_lease_ids: set[str] = set()
    for bead in halts:
        lid = bead.get("lease_id")
        if lid:
            halted_lease_ids.add(lid)

    orphans: list[dict[str, Any]] = []
    for activation in activations:
        lease_id = activation.get("lease_id")
        if lease_id and lease_id not in terminal_lease_ids:
            orphans.append(
                {
                    "lease_id": lease_id,
                    "activated_at": activation.get("timestamp"),
                    "halted": lease_id in halted_lease_ids,
                    "reason": "activation_without_terminal_bead",
                }
            )

    return orphans
