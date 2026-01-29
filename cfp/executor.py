"""
CFP Executor — Query Execution Engine
=====================================

S35 TRACK B DELIVERABLE
Created: 2026-01-29 (Day 2)

The computation engine for Conditional Fact Projector.
Routes queries to appropriate adapters, enforces budgets,
and attaches provenance to all results.

INVARIANTS ENFORCED:
  - INV-ATTR-PROVENANCE: query_string + dataset_hash + bead_id + governance_hash
  - INV-SLICE-MINIMUM-N: Warning on N < 30
  - INV-CFP-BUDGET-ENFORCE: Pre-execution estimate > threshold → REJECT
  - INV-NO-FALSE-PRECISION: Metrics rounded to declared precision
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from cfp.bead_adapter import BeadCFPAdapter
from cfp.budget import BudgetEstimator, BudgetExceededError, BudgetStatus
from cfp.river_adapter import RiverCFPAdapter
from cfp.validation import LensQuery, LensQueryValidator, QuerySource

# =============================================================================
# CONSTANTS
# =============================================================================

PHOENIX_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = PHOENIX_ROOT / "docs" / "PHOENIX_MANIFEST.md"
INVARIANTS_PATH = PHOENIX_ROOT / "CONSTITUTION" / "invariants"

# Minimum sample size for warnings
MIN_SAMPLE_SIZE = 30

# Metric precision definitions (INV-NO-FALSE-PRECISION)
METRIC_PRECISION = {
    "sharpe": 2,
    "win_rate": 2,
    "pnl": 2,
    "profit_factor": 2,
    "max_drawdown": 2,
    "trade_count": 0,
}


# =============================================================================
# TYPES
# =============================================================================


class ResultType(Enum):
    """Type of CFP result."""

    FACT = "FACT"  # Immutable, can be persisted
    VIEW = "VIEW"  # Ephemeral, user-rendered only


@dataclass
class Provenance:
    """
    Provenance quadruplet for CFP results.

    INV-ATTR-PROVENANCE: All results must include this.
    """

    query_string: str
    dataset_hash: str
    governance_hash: str
    computed_at: datetime
    bead_id: str | None = None  # Assigned on persistence
    strategy_config_hash: str = ""

    def is_complete(self) -> bool:
        """Check if provenance is complete."""
        return all(
            [
                self.query_string,
                self.dataset_hash,
                self.governance_hash,
                self.computed_at,
            ]
        )


@dataclass
class CFPResult:
    """
    Result of CFP query execution.

    Contains data, provenance, and metadata flags.
    """

    # Query info
    query: dict[str, Any]
    normalized_query: str

    # Data
    data: dict[str, Any]
    sample_size: int
    time_range: tuple[datetime, datetime] | None

    # Provenance (MANDATORY)
    provenance: Provenance

    # Flags
    low_sample_size: bool = False
    warnings: list[str] = field(default_factory=list)
    result_type: ResultType = ResultType.VIEW

    def is_valid(self) -> bool:
        """Check if result has valid provenance."""
        return self.provenance.is_complete()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query": {
                "original": self.query,
                "normalized": self.normalized_query,
            },
            "data": {
                "metrics": self.data,
                "sample_size": self.sample_size,
                "time_range": (
                    {
                        "start": self.time_range[0].isoformat(),
                        "end": self.time_range[1].isoformat(),
                    }
                    if self.time_range
                    else None
                ),
            },
            "provenance": {
                "query_string": self.provenance.query_string,
                "dataset_hash": self.provenance.dataset_hash,
                "governance_hash": self.provenance.governance_hash,
                "computed_at": self.provenance.computed_at.isoformat(),
                "bead_id": self.provenance.bead_id,
                "strategy_config_hash": self.provenance.strategy_config_hash,
            },
            "flags": {
                "low_sample_size": self.low_sample_size,
                "warnings": self.warnings,
            },
            "result_type": self.result_type.value,
        }


# =============================================================================
# EXECUTOR
# =============================================================================


class CFPExecutor:
    """
    Conditional Fact Projector Executor.

    Routes queries to appropriate data sources, enforces budgets,
    and attaches provenance to all results.

    Usage:
        executor = CFPExecutor()
        result = executor.execute(query)

        if result.low_sample_size:
            print("Warning: Low sample size")
    """

    def __init__(
        self,
        river_adapter: RiverCFPAdapter | None = None,
        bead_adapter: BeadCFPAdapter | None = None,
        budget_estimator: BudgetEstimator | None = None,
    ) -> None:
        """
        Initialize executor.

        Args:
            river_adapter: Adapter for River queries (optional)
            bead_adapter: Adapter for bead queries (optional)
            budget_estimator: Budget estimator (optional)
        """
        self._river = river_adapter
        self._beads = bead_adapter
        self._budget = budget_estimator or BudgetEstimator()
        self._validator = LensQueryValidator()
        self._governance_hash: str | None = None

    def _get_river_adapter(self) -> RiverCFPAdapter:
        """Lazy-load River adapter."""
        if self._river is None:
            self._river = RiverCFPAdapter()
        return self._river

    def _get_bead_adapter(self) -> BeadCFPAdapter:
        """Lazy-load bead adapter."""
        if self._beads is None:
            self._beads = BeadCFPAdapter()
        return self._beads

    def _compute_governance_hash(self) -> str:
        """
        Compute governance hash.

        Hash of PHOENIX_MANIFEST.md + active invariants.
        Proves result was generated while INV-ATTR-CAUSAL-BAN was active.
        """
        if self._governance_hash is not None:
            return self._governance_hash

        hasher = hashlib.sha256()

        # Add manifest
        if MANIFEST_PATH.exists():
            hasher.update(MANIFEST_PATH.read_bytes())

        # Add invariant files
        if INVARIANTS_PATH.exists():
            for inv_file in sorted(INVARIANTS_PATH.glob("*.yaml")):
                hasher.update(inv_file.read_bytes())

        self._governance_hash = hasher.hexdigest()
        return self._governance_hash

    def execute(self, query: LensQuery) -> CFPResult:
        """
        Execute a CFP query.

        Steps:
        1. Validate query against lens_schema
        2. PRE-EXECUTION: Check budget (INV-CFP-BUDGET-ENFORCE)
        3. Route to appropriate adapter
        4. Execute aggregation
        5. Attach provenance (quadruplet)
        6. Check sample size (INV-SLICE-MINIMUM-N)
        7. Round metrics (INV-NO-FALSE-PRECISION)
        8. Return result

        Args:
            query: Validated LensQuery

        Returns:
            CFPResult with data and provenance

        Raises:
            BudgetExceededError: If query exceeds compute budget
        """
        # 1. Validate query
        validation = self._validator.validate(query)
        if not validation.valid:
            raise ValueError(f"Invalid query: {validation.errors}")

        query_dict = query.to_dict()
        query_string = str(query_dict)

        # 2. Budget check
        total_rows = self._estimate_total_rows(query)
        budget_result = self._budget.check(query, total_rows)

        if budget_result.exceeded:
            raise BudgetExceededError(budget_result)

        warnings: list[str] = []
        if budget_result.status == BudgetStatus.WARNING:
            warnings.append(budget_result.suggestion or "Budget warning")

        # 3-4. Route and execute
        if query.source == QuerySource.RIVER:
            river_result = self._get_river_adapter().execute_aggregation(query_dict)
            data = river_result.data
            sample_size = river_result.sample_size
            dataset_hash = river_result.dataset_hash
            time_range = river_result.time_range
        elif query.source == QuerySource.BEADS:
            bead_result = self._get_bead_adapter().execute_query(query_dict)
            data = bead_result.data
            sample_size = bead_result.sample_size
            dataset_hash = bead_result.dataset_hash
            time_range = None
        else:
            # POSITIONS source (deferred)
            data = {}
            sample_size = 0
            dataset_hash = hashlib.sha256(b"").hexdigest()
            time_range = None

        # 5. Attach provenance (quadruplet)
        provenance = Provenance(
            query_string=query_string,
            dataset_hash=dataset_hash,
            governance_hash=self._compute_governance_hash(),
            computed_at=datetime.now(UTC),
            strategy_config_hash=query.strategy_config_hash,
        )

        # 6. Check sample size (INV-SLICE-MINIMUM-N)
        low_sample_size = sample_size < MIN_SAMPLE_SIZE
        if low_sample_size:
            warnings.append(
                f"Low sample size: N={sample_size} (min recommended: {MIN_SAMPLE_SIZE})"
            )

        # 7. Round metrics (INV-NO-FALSE-PRECISION)
        rounded_data = self._round_metrics(data)

        # Determine result type
        result_type = ResultType.VIEW
        if sample_size >= MIN_SAMPLE_SIZE:
            result_type = ResultType.FACT  # Can be persisted

        return CFPResult(
            query=query_dict,
            normalized_query=query_string,
            data=rounded_data,
            sample_size=sample_size,
            time_range=time_range,
            provenance=provenance,
            low_sample_size=low_sample_size,
            warnings=warnings,
            result_type=result_type,
        )

    def _estimate_total_rows(self, query: LensQuery) -> int:
        """Estimate total rows for budget calculation."""
        if query.source == QuerySource.RIVER:
            try:
                return self._get_river_adapter().get_total_rows("EURUSD")
            except Exception:
                return 100_000
        elif query.source == QuerySource.BEADS:
            return self._get_bead_adapter().get_total_beads()
        return 10_000

    def _round_metrics(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Round metrics to declared precision.

        INV-NO-FALSE-PRECISION: No false precision implied.
        """
        rounded: dict[str, Any] = {}

        for metric, value in data.items():
            if value is None:
                rounded[metric] = None
                continue

            precision = METRIC_PRECISION.get(metric, 2)
            if precision == 0:
                rounded[metric] = int(value)
            else:
                rounded[metric] = round(float(value), precision)

        return rounded


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    "CFPExecutor",
    "CFPResult",
    "Provenance",
    "ResultType",
    "MIN_SAMPLE_SIZE",
]
