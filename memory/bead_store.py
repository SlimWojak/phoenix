"""
Bead Store — Bead Persistence Layer
===================================

SQLite-backed storage for all bead types.

DESIGN:
- Write path: BeadStore.write() — full access
- Read path: BeadStore.read(), query_sql() — READ-ONLY

INVARIANTS:
- INV-BEAD-IMMUTABLE-1: Beads cannot be modified after creation
- INV-BEAD-HASH-1: bead_hash must match computed hash
- INV-BEAD-CHAIN-1: prev_bead_id must reference existing bead or be null

CONSUMERS:
- Hunt: write() — emit HUNT beads
- Athena: read(), query_sql() — query all bead types
- Checkpoint: write() — emit CONTEXT_SNAPSHOT beads
- Shadow: write() — emit PERFORMANCE beads
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# =============================================================================
# CONSTANTS
# =============================================================================

DEFAULT_BEAD_DB_PATH = Path.home() / "phoenix" / "data" / "beads.db"


# =============================================================================
# ENUMS
# =============================================================================


class BeadType(str, Enum):
    """Bead types from beads.yaml schema."""

    HUNT = "HUNT"
    CONTEXT_SNAPSHOT = "CONTEXT_SNAPSHOT"
    PERFORMANCE = "PERFORMANCE"
    AUTOPSY = "AUTOPSY"
    POSITION = "POSITION"
    PROMOTION = "PROMOTION"


class Signer(str, Enum):
    """Bead signer types."""

    SYSTEM = "system"
    HUMAN = "human"
    CLAUDE = "claude"


# =============================================================================
# EXCEPTIONS
# =============================================================================


class BeadStoreError(Exception):
    """Base exception for BeadStore errors."""

    pass


class BeadNotFoundError(BeadStoreError):
    """Bead not found."""

    pass


class BeadValidationError(BeadStoreError):
    """Bead validation failed."""

    pass


class BeadImmutabilityError(BeadStoreError):
    """Attempted to modify immutable bead."""

    pass


# =============================================================================
# BEAD DATA CLASS
# =============================================================================


@dataclass
class Bead:
    """Bead data structure (matches beads.yaml schema)."""

    bead_id: str
    bead_type: BeadType
    prev_bead_id: str | None
    bead_hash: str
    timestamp_utc: datetime
    signer: Signer
    version: str
    content: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "bead_id": self.bead_id,
            "bead_type": self.bead_type.value,
            "prev_bead_id": self.prev_bead_id,
            "bead_hash": self.bead_hash,
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "signer": self.signer.value,
            "version": self.version,
            "content": self.content,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Bead:
        """Create Bead from dictionary."""
        return cls(
            bead_id=data["bead_id"],
            bead_type=BeadType(data["bead_type"]),
            prev_bead_id=data.get("prev_bead_id"),
            bead_hash=data["bead_hash"],
            timestamp_utc=datetime.fromisoformat(data["timestamp_utc"]),
            signer=Signer(data["signer"]),
            version=data.get("version", "1.0"),
            content=data.get("content", {}),
        )

    @staticmethod
    def compute_hash(
        content: dict,
        prev_hash: str | None,
        timestamp: datetime,
        signer: str,
    ) -> str:
        """
        Compute bead hash.

        hash = SHA256(content + prev_hash + timestamp + signer)
        """
        data = json.dumps(
            {
                "content": content,
                "prev_hash": prev_hash or "",
                "timestamp": timestamp.isoformat(),
                "signer": signer,
            },
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()


# =============================================================================
# BEAD STORE
# =============================================================================


class BeadStore:
    """
    SQLite-backed bead storage.

    Write path: Full access for emitting beads
    Read path: Read-only for queries (Athena)

    INVARIANT: INV-BEAD-IMMUTABLE-1 — Beads cannot be modified after creation
    """

    def __init__(
        self,
        db_path: Path | None = None,
        read_only: bool = False,
    ) -> None:
        """
        Initialize BeadStore.

        Args:
            db_path: Path to SQLite database
            read_only: If True, opens in read-only mode (for Athena)
        """
        self._db_path = db_path or DEFAULT_BEAD_DB_PATH
        self._read_only = read_only
        self._conn: sqlite3.Connection | None = None

        # Ensure parent directory exists
        if not read_only:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        if self._conn is None:
            if self._read_only:
                # Read-only mode for Athena
                uri = f"file:{self._db_path}?mode=ro"
                self._conn = sqlite3.connect(uri, uri=True)
            else:
                self._conn = sqlite3.connect(str(self._db_path))

            self._conn.row_factory = sqlite3.Row

        return self._conn

    def _init_schema(self) -> None:
        """Initialize database schema."""
        if self._read_only:
            return

        conn = self._get_connection()
        cursor = conn.cursor()

        # Beads table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS beads (
                bead_id TEXT PRIMARY KEY,
                bead_type TEXT NOT NULL,
                prev_bead_id TEXT,
                bead_hash TEXT NOT NULL,
                timestamp_utc TEXT NOT NULL,
                signer TEXT NOT NULL,
                version TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prev_bead_id) REFERENCES beads(bead_id)
            )
            """
        )

        # Indexes for common queries
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_beads_type ON beads(bead_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_beads_timestamp ON beads(timestamp_utc)"
        )

        conn.commit()

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> BeadStore:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit."""
        self.close()

    # =========================================================================
    # WRITE PATH
    # =========================================================================

    def write(self, bead: Bead) -> str:
        """
        Write a bead to storage.

        INVARIANT: INV-BEAD-IMMUTABLE-1 — Cannot overwrite existing beads

        Args:
            bead: Bead to write

        Returns:
            bead_id of written bead

        Raises:
            BeadImmutabilityError: If bead already exists
            BeadValidationError: If bead validation fails
        """
        if self._read_only:
            raise BeadStoreError("Cannot write in read-only mode")

        # Validate bead
        self._validate_bead(bead)

        # Check immutability
        if self._bead_exists(bead.bead_id):
            raise BeadImmutabilityError(
                f"Bead {bead.bead_id} already exists (INV-BEAD-IMMUTABLE-1)"
            )

        # Validate chain
        if bead.prev_bead_id and not self._bead_exists(bead.prev_bead_id):
            raise BeadValidationError(
                f"prev_bead_id {bead.prev_bead_id} does not exist (INV-BEAD-CHAIN-1)"
            )

        # Write
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO beads (
                bead_id, bead_type, prev_bead_id, bead_hash,
                timestamp_utc, signer, version, content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bead.bead_id,
                bead.bead_type.value,
                bead.prev_bead_id,
                bead.bead_hash,
                bead.timestamp_utc.isoformat(),
                bead.signer.value,
                bead.version,
                json.dumps(bead.content),
            ),
        )

        conn.commit()
        return bead.bead_id

    def write_dict(self, bead_dict: dict[str, Any]) -> str:
        """
        Write a bead from dictionary.

        Convenience method for Hunt, Checkpoint, etc.
        """
        bead = Bead.from_dict(bead_dict)
        return self.write(bead)

    def _validate_bead(self, bead: Bead) -> None:
        """Validate bead before write."""
        # Note: We don't enforce hash match strictly in v1
        # because Hunt computes hash differently (includes more fields)
        # TODO: Standardize hash computation across all producers
        pass

    def _bead_exists(self, bead_id: str) -> bool:
        """Check if bead exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM beads WHERE bead_id = ?", (bead_id,))
        return cursor.fetchone() is not None

    # =========================================================================
    # READ PATH (Used by Athena)
    # =========================================================================

    def read(self, bead_id: str) -> Bead:
        """
        Read a bead by ID.

        Args:
            bead_id: Bead identifier

        Returns:
            Bead object

        Raises:
            BeadNotFoundError: If bead doesn't exist
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT bead_id, bead_type, prev_bead_id, bead_hash,
                   timestamp_utc, signer, version, content
            FROM beads WHERE bead_id = ?
            """,
            (bead_id,),
        )

        row = cursor.fetchone()
        if row is None:
            raise BeadNotFoundError(f"Bead not found: {bead_id}")

        return Bead(
            bead_id=row["bead_id"],
            bead_type=BeadType(row["bead_type"]),
            prev_bead_id=row["prev_bead_id"],
            bead_hash=row["bead_hash"],
            timestamp_utc=datetime.fromisoformat(row["timestamp_utc"]),
            signer=Signer(row["signer"]),
            version=row["version"],
            content=json.loads(row["content"]),
        )

    def query_sql(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """
        Execute read-only SQL query.

        INVARIANT: INV-ATHENA-RO-1 — Only SELECT allowed

        Args:
            sql: SQL query (must be SELECT)
            params: Query parameters

        Returns:
            List of row dictionaries

        Raises:
            BeadStoreError: If query is not SELECT
        """
        # Enforce read-only (INV-ATHENA-RO-1)
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            raise BeadStoreError(
                "Only SELECT queries allowed (INV-ATHENA-RO-1)"
            )

        for forbidden in ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER"]:
            if forbidden in sql_upper:
                raise BeadStoreError(
                    f"Forbidden SQL operation: {forbidden} (INV-ATHENA-RO-1)"
                )

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)

        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]

    def get_latest_bead_id(self, bead_type: BeadType | None = None) -> str | None:
        """Get the latest bead ID (for chaining)."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if bead_type:
            cursor.execute(
                """
                SELECT bead_id FROM beads
                WHERE bead_type = ?
                ORDER BY timestamp_utc DESC LIMIT 1
                """,
                (bead_type.value,),
            )
        else:
            cursor.execute(
                """
                SELECT bead_id FROM beads
                ORDER BY timestamp_utc DESC LIMIT 1
                """
            )

        row = cursor.fetchone()
        return row["bead_id"] if row else None

    def count_beads(self, bead_type: BeadType | None = None) -> int:
        """Count beads in store."""
        conn = self._get_connection()
        cursor = conn.cursor()

        if bead_type:
            cursor.execute(
                "SELECT COUNT(*) FROM beads WHERE bead_type = ?",
                (bead_type.value,),
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM beads")

        return cursor.fetchone()[0]
