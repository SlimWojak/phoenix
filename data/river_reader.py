"""
River Reader — Read-Only Data Access Layer
===========================================

CANONICAL SOURCE OF TRUTH
Location: phoenix/data/river_reader.py
Created: 2026-01-27 (PRE-S30)

This module provides READ-ONLY access to River data.
ROADMAP lines 342-356 are now HISTORICAL REFERENCE.

CRITICAL CONSTRAINTS (GPT + GROK mandate):
- Physically read-only: Uses read-only database connection
- No INSERT/UPDATE/DELETE methods exist in this module
- Pre-commit hook should verify no write methods added

ALLOWED CALLERS:
- Hunt
- CSO
- Briefing
- Shadow

DENIED CALLERS:
- Execution (uses separate path with T2 gates)

INVARIANT: INV-RIVER-RO-1 "River reader cannot modify data"
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


# =============================================================================
# CONSTANTS
# =============================================================================

# Default River database location (can be overridden)
DEFAULT_RIVER_PATH = Path.home() / "nex" / "river.db"

# Allowed callers for access control
ALLOWED_CALLERS = frozenset({"hunt", "cso", "briefing", "shadow", "athena"})

# Denied callers (enforcement is documentation + code review)
DENIED_CALLERS = frozenset({"execution"})


# =============================================================================
# EXCEPTIONS
# =============================================================================


class RiverReadError(Exception):
    """Raised when River read operation fails."""

    pass


class RiverAccessDeniedError(Exception):
    """Raised when unauthorized caller attempts access."""

    pass


# =============================================================================
# RIVER READER (Read-Only)
# =============================================================================


class RiverReader:
    """
    Read-only access to River data.

    PHYSICAL READ-ONLY ENFORCEMENT:
    - Connection opened with `uri=True` and `?mode=ro`
    - No write methods exist in this class
    - Any attempt to execute write SQL will fail at database level

    Usage:
        reader = RiverReader(caller="hunt")
        df = reader.get_bars("EURUSD", "1H", start, end)
    """

    def __init__(
        self,
        caller: str,
        river_path: Path | None = None,
    ) -> None:
        """
        Initialize River reader.

        Args:
            caller: Identifier of calling module (for access control)
            river_path: Path to River database (default: ~/nex/river.db)

        Raises:
            RiverAccessDeniedError: If caller is in DENIED_CALLERS
        """
        # Access control check
        caller_lower = caller.lower()
        if caller_lower in DENIED_CALLERS:
            raise RiverAccessDeniedError(
                f"Caller '{caller}' denied access to RiverReader. "
                f"Execution must use separate T2-gated path."
            )

        self._caller = caller_lower
        self._river_path = river_path or DEFAULT_RIVER_PATH
        self._conn: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get read-only database connection.

        Returns connection opened in READ-ONLY mode.
        This is physical enforcement — writes will fail at DB level.
        """
        if self._conn is None:
            # READ-ONLY connection via URI
            # https://www.sqlite.org/uri.html
            uri = f"file:{self._river_path}?mode=ro"
            self._conn = sqlite3.connect(uri, uri=True)
            self._conn.row_factory = sqlite3.Row

        return self._conn

    def close(self) -> None:
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> RiverReader:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit."""
        self.close()

    # =========================================================================
    # READ INTERFACE (No write methods exist)
    # =========================================================================

    def get_bars(
        self,
        pair: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """
        Get OHLCV bars for a pair.

        Args:
            pair: Trading pair (e.g., "EURUSD")
            timeframe: Timeframe (e.g., "1H", "4H", "1D")
            start: Start datetime (UTC)
            end: End datetime (UTC)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume

        Raises:
            RiverReadError: If query fails
        """
        import pandas as pd

        conn = self._get_connection()

        # Table name convention: pair_timeframe (e.g., EURUSD_1H)
        table_name = f"{pair}_{timeframe}"

        try:
            # SQLite doesn't support parameterized table names
            # We validate table_name format to prevent injection
            if not self._validate_table_name(table_name):
                raise RiverReadError(f"Invalid table name format: {table_name}")

            # Table name validated above, SQL injection not possible
            safe_query = f"""
                SELECT timestamp, open, high, low, close, volume
                FROM "{table_name}"
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """  # noqa: S608

            df = pd.read_sql_query(
                safe_query,
                conn,
                params=(start.isoformat(), end.isoformat()),
            )
            return df

        except Exception as e:
            raise RiverReadError(f"Failed to get bars: {e}") from e

    def get_enrichment(
        self,
        pair: str,
        layer: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """
        Get enrichment layer data for a pair.

        Args:
            pair: Trading pair (e.g., "EURUSD")
            layer: Enrichment layer (e.g., "L1", "L2", "L3", "L4", "L5", "L6")
            start: Start datetime (UTC)
            end: End datetime (UTC)

        Returns:
            DataFrame with enrichment layer columns

        Raises:
            RiverReadError: If query fails
        """
        import pandas as pd

        conn = self._get_connection()

        # Table name convention: pair_enrichment_layer (e.g., EURUSD_enrichment_L3)
        table_name = f"{pair}_enrichment_{layer}"

        try:
            if not self._validate_table_name(table_name):
                raise RiverReadError(f"Invalid table name format: {table_name}")

            # Table name validated above, SQL injection not possible
            safe_query = f"""
                SELECT *
                FROM "{table_name}"
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """  # noqa: S608

            df = pd.read_sql_query(
                safe_query,
                conn,
                params=(start.isoformat(), end.isoformat()),
            )
            return df

        except Exception as e:
            raise RiverReadError(f"Failed to get enrichment: {e}") from e

    def get_latest_state(self, pair: str) -> dict:
        """
        Get current state for a pair (latest prices, spreads).

        Args:
            pair: Trading pair (e.g., "EURUSD")

        Returns:
            Dict with latest state:
            - timestamp: Last update time
            - bid: Current bid
            - ask: Current ask
            - spread: Current spread
            - mid: Mid price

        Raises:
            RiverReadError: If query fails
        """
        conn = self._get_connection()

        try:
            cursor = conn.cursor()

            # Get latest tick from state table
            cursor.execute(
                """
                SELECT timestamp, bid, ask
                FROM pair_state
                WHERE pair = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (pair,),
            )

            row = cursor.fetchone()

            if row is None:
                raise RiverReadError(f"No state found for pair: {pair}")

            timestamp, bid, ask = row
            spread = ask - bid
            mid = (bid + ask) / 2

            return {
                "pair": pair,
                "timestamp": timestamp,
                "bid": bid,
                "ask": ask,
                "spread": spread,
                "mid": mid,
                "queried_at": datetime.now(UTC).isoformat(),
                "queried_by": self._caller,
            }

        except Exception as e:
            raise RiverReadError(f"Failed to get latest state: {e}") from e

    def list_available_pairs(self) -> list[str]:
        """
        List pairs available in River.

        Returns:
            List of pair symbols
        """
        conn = self._get_connection()

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT pair FROM pair_state ORDER BY pair
                """
            )
            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            raise RiverReadError(f"Failed to list pairs: {e}") from e

    def list_available_timeframes(self, pair: str) -> list[str]:
        """
        List timeframes available for a pair.

        Args:
            pair: Trading pair

        Returns:
            List of timeframe strings
        """
        conn = self._get_connection()

        try:
            cursor = conn.cursor()

            # Query sqlite_master for tables matching pair pattern
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name LIKE ?
                ORDER BY name
                """,
                (f"{pair}_%",),
            )

            timeframes = []
            for (name,) in cursor.fetchall():
                # Extract timeframe from table name (e.g., EURUSD_1H -> 1H)
                if "_enrichment_" not in name:
                    parts = name.split("_")
                    if len(parts) >= 2:
                        timeframes.append(parts[-1])

            return timeframes

        except Exception as e:
            raise RiverReadError(f"Failed to list timeframes: {e}") from e

    # =========================================================================
    # VALIDATION HELPERS
    # =========================================================================

    @staticmethod
    def _validate_table_name(name: str) -> bool:
        """
        Validate table name format to prevent injection.

        Only allows alphanumeric characters and underscores.
        """
        import re

        return bool(re.match(r"^[A-Za-z0-9_]+$", name))


# =============================================================================
# MODULE-LEVEL VERIFICATION
# =============================================================================
# Pre-commit hook should verify this module has no write methods.
# The following assertion documents the contract:

_FORBIDDEN_PATTERNS = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
]

# This comment serves as documentation for pre-commit verification:
# grep -E "INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE" river_reader.py
# Should return 0 matches in actual SQL execution code (this comment excluded)
