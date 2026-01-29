"""
Bead CFP Adapter — Query Execution Against Bead Store
=====================================================

S35 TRACK B DELIVERABLE
Created: 2026-01-29 (Day 2)

Executes CFP queries against the bead store.
For S35: PERFORMANCE_BEAD queries only (complexity deferred to S37).

INVARIANTS:
  - INV-BEAD-CHAIN-1: prev_bead_id must reference existing bead or be null
  - INV-ATTR-PROVENANCE: All results include provenance
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# =============================================================================
# CONSTANTS
# =============================================================================

PHOENIX_ROOT = Path(__file__).parent.parent
BEAD_STORE_PATH = PHOENIX_ROOT / "state" / "beads.json"


# =============================================================================
# TYPES
# =============================================================================


@dataclass
class BeadQueryResult:
    """Result of bead store query."""

    data: dict[str, Any]
    sample_size: int
    dataset_hash: str
    bead_ids: list[str]
    query_string: str
    computed_at: datetime


# =============================================================================
# BEAD CFP ADAPTER
# =============================================================================


class BeadCFPAdapter:
    """
    CFP adapter for bead store queries.

    For S35, focuses on PERFORMANCE_BEAD queries.
    Complex cross-type queries deferred to S37 (Memory Discipline).

    Usage:
        adapter = BeadCFPAdapter()
        result = adapter.execute_query(query)
    """

    # Supported bead types for S35
    SUPPORTED_BEAD_TYPES = frozenset(["PERFORMANCE", "HUNT", "AUTOPSY"])

    def __init__(self, bead_store_path: Path | None = None) -> None:
        """
        Initialize adapter.

        Args:
            bead_store_path: Path to bead store (optional)
        """
        self._store_path = bead_store_path or BEAD_STORE_PATH
        self._beads: list[dict[str, Any]] | None = None

    def _load_beads(self) -> list[dict[str, Any]]:
        """Load beads from store."""
        if self._beads is not None:
            return self._beads

        if not self._store_path.exists():
            self._beads = []
            return self._beads

        try:
            with open(self._store_path) as f:
                self._beads = json.load(f)
        except (json.JSONDecodeError, OSError):
            self._beads = []

        return self._beads

    def is_available(self) -> bool:
        """Check if bead store is available."""
        return self._store_path.exists()

    def get_total_beads(self, bead_type: str | None = None) -> int:
        """
        Get total bead count for cardinality estimation.

        Args:
            bead_type: Filter by bead type (optional)

        Returns:
            Total bead count
        """
        beads = self._load_beads()

        if bead_type:
            return sum(1 for b in beads if b.get("bead_type") == bead_type)

        return len(beads)

    def execute_query(
        self,
        query_dict: dict[str, Any],
        bead_type: str = "PERFORMANCE",
    ) -> BeadQueryResult:
        """
        Execute aggregation query against bead store.

        Args:
            query_dict: Validated LensQuery as dict
            bead_type: Type of bead to query

        Returns:
            BeadQueryResult with data and provenance
        """
        beads = self._load_beads()

        # Filter by bead type
        filtered = [b for b in beads if b.get("bead_type") == bead_type]

        # Apply time range filter
        if "filter" in query_dict and query_dict["filter"]:
            tr = query_dict["filter"].get("time_range")
            if tr:
                start = datetime.fromisoformat(tr["start"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(tr["end"].replace("Z", "+00:00"))
                filtered = [b for b in filtered if self._bead_in_range(b, start, end)]

        # Apply condition filters
        conditions = query_dict.get("filter", {}).get("conditions", [])
        for cond in conditions:
            filtered = self._apply_condition(filtered, cond)

        if not filtered:
            return BeadQueryResult(
                data={},
                sample_size=0,
                dataset_hash=self._compute_hash(b""),
                bead_ids=[],
                query_string=str(query_dict),
                computed_at=datetime.now(UTC),
            )

        # Compute dataset hash
        dataset_hash = self._compute_beads_hash(filtered)
        bead_ids = [b.get("bead_id", "") for b in filtered]

        # Compute metrics
        metrics = query_dict.get("aggregate", {}).get("metrics", [])
        result_data = self._compute_metrics(filtered, metrics, bead_type)

        return BeadQueryResult(
            data=result_data,
            sample_size=len(filtered),
            dataset_hash=dataset_hash,
            bead_ids=bead_ids,
            query_string=str(query_dict),
            computed_at=datetime.now(UTC),
        )

    def _bead_in_range(
        self,
        bead: dict[str, Any],
        start: datetime,
        end: datetime,
    ) -> bool:
        """Check if bead timestamp is in range."""
        ts_str = bead.get("timestamp_utc")
        if not ts_str:
            return False

        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            return start <= ts <= end
        except ValueError:
            return False

    def _apply_condition(
        self,
        beads: list[dict[str, Any]],
        condition: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Apply a single condition filter."""
        field = condition.get("field", "")
        op = condition.get("op", "==")
        value = condition.get("value")

        result = []
        for bead in beads:
            bead_value = self._get_nested_field(bead, field)

            if bead_value is None:
                continue

            if self._compare(bead_value, op, value):
                result.append(bead)

        return result

    def _get_nested_field(self, bead: dict[str, Any], field: str) -> Any:
        """Get potentially nested field value."""
        parts = field.split(".")
        value: Any = bead
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _compare(self, bead_value: Any, op: str, target: Any) -> bool:
        """Compare values using operator."""
        try:
            if op == "==":
                return bool(bead_value == target)
            elif op == "!=":
                return bool(bead_value != target)
            elif op == ">":
                return bool(bead_value > target)
            elif op == "<":
                return bool(bead_value < target)
            elif op == ">=":
                return bool(bead_value >= target)
            elif op == "<=":
                return bool(bead_value <= target)
            elif op == "in":
                return bool(bead_value in target)
            elif op == "not_in":
                return bool(bead_value not in target)
        except (TypeError, ValueError):
            return False
        return False

    def _compute_metrics(
        self,
        beads: list[dict[str, Any]],
        metrics: list[str],
        bead_type: str,
    ) -> dict[str, Any]:
        """Compute metrics from beads."""
        if not beads:
            return {m: None for m in metrics}

        result: dict[str, Any] = {}

        for metric in metrics:
            if bead_type == "PERFORMANCE":
                result[metric] = self._compute_performance_metric(beads, metric)
            elif bead_type == "HUNT":
                result[metric] = self._compute_hunt_metric(beads, metric)
            else:
                result[metric] = None

        return result

    def _compute_performance_metric(
        self,
        beads: list[dict[str, Any]],
        metric: str,
    ) -> float | int | None:
        """Compute metric from PERFORMANCE beads."""
        if metric == "sharpe":
            sharpes: list[float] = [
                float(b.get("metrics", {}).get("sharpe"))
                for b in beads
                if b.get("metrics", {}).get("sharpe") is not None
            ]
            if sharpes:
                return round(sum(sharpes) / len(sharpes), 2)
            return None

        elif metric == "win_rate":
            rates: list[float] = [
                float(b.get("metrics", {}).get("win_rate"))
                for b in beads
                if b.get("metrics", {}).get("win_rate") is not None
            ]
            if rates:
                return round(sum(rates) / len(rates), 2)
            return None

        elif metric == "pnl":
            pnls: list[float] = [float(b.get("metrics", {}).get("pnl", 0)) for b in beads]
            return round(sum(pnls), 2)

        elif metric == "trade_count":
            counts: list[int] = [int(b.get("metrics", {}).get("trades", 0)) for b in beads]
            return sum(counts)

        return None

    def _compute_hunt_metric(
        self,
        beads: list[dict[str, Any]],
        metric: str,
    ) -> float | int | None:
        """Compute metric from HUNT beads."""
        if metric == "trade_count":
            return len(beads)

        # Extract from survivors
        if metric == "sharpe":
            all_sharpes: list[float] = []
            for b in beads:
                survivors = b.get("survivors", [])
                for s in survivors:
                    if s.get("sharpe") is not None:
                        all_sharpes.append(float(s["sharpe"]))
            if all_sharpes:
                return round(sum(all_sharpes) / len(all_sharpes), 2)

        return None

    def _compute_beads_hash(self, beads: list[dict[str, Any]]) -> str:
        """Compute hash of beads for provenance."""
        # Sort by bead_id and serialize
        sorted_beads = sorted(beads, key=lambda b: b.get("bead_id", ""))
        data_bytes = json.dumps(sorted_beads, sort_keys=True).encode("utf-8")
        return self._compute_hash(data_bytes)

    def _compute_hash(self, data: bytes) -> str:
        """Compute SHA256 hash."""
        return hashlib.sha256(data).hexdigest()

    def verify_chain(self, bead_id: str) -> bool:
        """
        Verify bead chain integrity.

        INV-BEAD-CHAIN-1: prev_bead_id must reference existing bead or be null

        Returns:
            True if chain is valid
        """
        beads = self._load_beads()
        bead_ids = {b.get("bead_id") for b in beads}

        for bead in beads:
            if bead.get("bead_id") == bead_id:
                prev_id = bead.get("prev_bead_id")
                if prev_id is not None and prev_id not in bead_ids:
                    return False  # Broken chain
                return True

        return False  # Bead not found


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "BeadCFPAdapter",
    "BeadQueryResult",
]
