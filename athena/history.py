"""
Memory History — S37 Track E
============================

Chronological trail of all memory operations.
Full supersession chain, no selective retrieval.

INVARIANTS:
  - INV-HISTORY-NO-BURY: Full chain always returned
  - Bead immutability maintained
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any



# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_DB_PATH = Path.home() / "phoenix" / "data" / "athena.db"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class HistoryError(Exception):
    """Base exception for history operations."""

    pass


class CycleDetectedError(HistoryError):
    """Supersession cycle detected."""

    pass


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class ClaimEvolution:
    """
    Evolution of a claim through supersessions.

    INV-HISTORY-NO-BURY: Full chain always returned, oldest-first.
    """

    chain: list[dict[str, Any]]
    chain_length: int
    current_claim_id: str
    original_claim_id: str


# =============================================================================
# MEMORY HISTORY
# =============================================================================


class MemoryHistory:
    """
    Memory history operations.

    Provides chronological trail of memory operations.
    Full supersession chains. No selective retrieval.

    INVARIANTS:
      - INV-HISTORY-NO-BURY: Full chain always
      - No rewriting history
    """

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize history."""
        self._db_path = db_path or DEFAULT_DB_PATH

    def get_claim_evolution(self, claim_id: str) -> ClaimEvolution:
        """
        Get full evolution of a claim.

        Returns ALL versions, oldest-first.
        INV-HISTORY-NO-BURY: Never returns partial chain.

        Args:
            claim_id: Any claim_id in the chain

        Returns:
            ClaimEvolution with full chain
        """
        with sqlite3.connect(self._db_path) as conn:
            # Find the original claim (no superseder)
            original_id = self._find_original(conn, claim_id)

            # Build chain forward
            chain = self._build_chain_forward(conn, original_id)

        if not chain:
            # Single claim, no chain
            chain = [self._get_claim_data(claim_id) or {"bead_id": claim_id}]

        return ClaimEvolution(
            chain=chain,
            chain_length=len(chain),
            current_claim_id=chain[-1].get("bead_id", "") if chain else "",
            original_claim_id=chain[0].get("bead_id", "") if chain else "",
        )

    def _find_original(self, conn: sqlite3.Connection, claim_id: str) -> str:
        """Find the original claim in a supersession chain."""
        visited = set()
        current = claim_id

        while True:
            if current in visited:
                raise CycleDetectedError(
                    f"Supersession cycle detected at claim '{current}'"
                )
            visited.add(current)

            # Find who supersedes this claim
            cursor = conn.execute(
                """
                SELECT bead_id FROM claim_beads
                WHERE json_extract(data, '$.status.superseded_by') = ?
                """,
                (current,),
            )
            row = cursor.fetchone()

            if row:
                current = row[0]
            else:
                # No one supersedes this — it's the original
                return current

    def _build_chain_forward(
        self,
        conn: sqlite3.Connection,
        original_id: str,
    ) -> list[dict[str, Any]]:
        """Build chain from original forward."""
        chain: list[dict[str, Any]] = []
        current = original_id
        visited = set()

        while current:
            if current in visited:
                raise CycleDetectedError(
                    f"Supersession cycle detected at claim '{current}'"
                )
            visited.add(current)

            # Get claim data
            cursor = conn.execute(
                "SELECT data FROM claim_beads WHERE bead_id = ?",
                (current,),
            )
            row = cursor.fetchone()

            if row:
                data = json.loads(row[0])
                chain.append(data)
                # Get superseded_by
                current = data.get("status", {}).get("superseded_by")
            else:
                break

        return chain

    def _get_claim_data(self, claim_id: str) -> dict[str, Any] | None:
        """Get claim data by ID."""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM claim_beads WHERE bead_id = ?",
                (claim_id,),
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def check_supersession_cycle(
        self,
        new_claim_id: str,
        supersedes_id: str,
    ) -> bool:
        """
        Check if supersession would create a cycle.

        Args:
            new_claim_id: The new claim
            supersedes_id: The claim being superseded

        Returns:
            True if cycle detected

        Raises:
            CycleDetectedError: If cycle found
        """
        if not supersedes_id:
            return False

        with sqlite3.connect(self._db_path) as conn:
            visited = {new_claim_id}
            current = supersedes_id

            while current:
                if current in visited:
                    raise CycleDetectedError(
                        f"Supersession would create cycle: "
                        f"{new_claim_id} -> {supersedes_id} -> ... -> {current}"
                    )
                visited.add(current)

                # Check what this claim supersedes
                cursor = conn.execute(
                    "SELECT data FROM claim_beads WHERE bead_id = ?",
                    (current,),
                )
                row = cursor.fetchone()

                if row:
                    data = json.loads(row[0])
                    current = data.get("status", {}).get("superseded_by")
                else:
                    break

        return False

    def get_timeline(
        self,
        domain: str | None = None,
        bead_type: str | None = None,
        order: str = "REVERSE_CHRONO",
    ) -> list[dict[str, Any]]:
        """
        Get timeline of beads.

        Args:
            domain: Filter by domain
            bead_type: Filter by type
            order: CHRONO or REVERSE_CHRONO

        Returns:
            List of bead data
        """
        # Validate order
        if order not in ["CHRONO", "REVERSE_CHRONO"]:
            order = "REVERSE_CHRONO"

        order_sql = "ASC" if order == "CHRONO" else "DESC"

        results: list[dict[str, Any]] = []

        with sqlite3.connect(self._db_path) as conn:
            # Query each table
            tables = []
            if bead_type is None or bead_type == "CLAIM":
                tables.append("claim_beads")
            if bead_type is None or bead_type == "FACT":
                tables.append("fact_beads")
            if bead_type is None or bead_type == "CONFLICT":
                tables.append("conflict_beads")

            for table in tables:
                if domain:
                    cursor = conn.execute(
                        f"SELECT data FROM {table} WHERE domain = ? ORDER BY timestamp {order_sql}",
                        (domain,),
                    )
                else:
                    cursor = conn.execute(
                        f"SELECT data FROM {table} ORDER BY timestamp {order_sql}"
                    )

                for row in cursor.fetchall():
                    results.append(json.loads(row[0]))

        # Sort combined results
        results.sort(
            key=lambda x: x.get("timestamp", ""),
            reverse=(order == "REVERSE_CHRONO"),
        )

        return results

    def get_conflict_history(
        self,
        include_resolved: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Get all conflicts (open and resolved).

        Args:
            include_resolved: Include resolved conflicts

        Returns:
            List of conflict data
        """
        with sqlite3.connect(self._db_path) as conn:
            if include_resolved:
                cursor = conn.execute(
                    "SELECT data FROM conflict_beads ORDER BY timestamp DESC"
                )
            else:
                cursor = conn.execute(
                    "SELECT data FROM conflict_beads WHERE status = 'OPEN' "
                    "ORDER BY timestamp DESC"
                )

            return [json.loads(row[0]) for row in cursor.fetchall()]


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "MemoryHistory",
    "ClaimEvolution",
    "CycleDetectedError",
    "HistoryError",
]
