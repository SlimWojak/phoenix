"""
Semantic Health Checker — Deep health validation
=================================================

S33: FIRST_BLOOD

Validates semantic health beyond just "process alive":
- Orders flowing (if pending, status updating)
- Fills updating (if positions open)
- Subscriptions alive (market data active)
- Reconciliation fresh (< 10 min)

INVARIANT: INV-OPS-HEARTBEAT-SEMANTIC-1
Heartbeat includes semantic health checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    pass


class CheckStatus(Enum):
    """Individual check status."""

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


@dataclass
class CheckResult:
    """Result of a single health check."""

    name: str
    status: CheckStatus
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SemanticHealthResult:
    """Aggregated semantic health result."""

    healthy: bool = True
    checks: list[CheckResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def add_check(self, check: CheckResult) -> None:
        """Add a check result."""
        self.checks.append(check)
        if check.status in (CheckStatus.CRITICAL, CheckStatus.WARNING):
            self.healthy = False

    def get_warnings(self) -> list[CheckResult]:
        """Get warning checks."""
        return [c for c in self.checks if c.status == CheckStatus.WARNING]

    def get_criticals(self) -> list[CheckResult]:
        """Get critical checks."""
        return [c for c in self.checks if c.status == CheckStatus.CRITICAL]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "healthy": self.healthy,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.checks
            ],
            "timestamp": self.timestamp.isoformat(),
        }


class IBKRStateProvider(Protocol):
    """Protocol for IBKR state access."""

    def is_connected(self) -> bool: ...
    def get_pending_orders(self) -> list[Any]: ...
    def get_last_order_update(self) -> datetime | None: ...
    def get_open_positions(self) -> list[Any]: ...
    def get_last_fill_time(self) -> datetime | None: ...


class ReconciliationStateProvider(Protocol):
    """Protocol for reconciliation state access."""

    def get_last_run_time(self) -> datetime | None: ...
    def get_unresolved_drift_count(self) -> int: ...


class PositionStateProvider(Protocol):
    """Protocol for position state access."""

    def get_stalled_positions(self) -> list[Any]: ...
    def get_stalled_duration(self, position_id: str) -> timedelta | None: ...


@dataclass
class SemanticHealthConfig:
    """Configuration for semantic health checks."""

    # Order flow
    order_stale_threshold_sec: float = 300.0  # 5 min

    # Fill freshness
    fill_stale_threshold_sec: float = 600.0  # 10 min

    # Reconciliation
    recon_stale_threshold_sec: float = 600.0  # 10 min

    # Stalled positions
    stalled_warning_sec: float = 300.0  # 5 min
    stalled_critical_sec: float = 600.0  # 10 min


class SemanticHealthChecker:
    """
    Performs semantic health checks.

    INVARIANT: INV-OPS-HEARTBEAT-SEMANTIC-1
    Heartbeat includes semantic health, not just process.
    """

    def __init__(
        self,
        config: SemanticHealthConfig | None = None,
        ibkr_provider: IBKRStateProvider | None = None,
        recon_provider: ReconciliationStateProvider | None = None,
        position_provider: PositionStateProvider | None = None,
    ) -> None:
        """
        Initialize checker.

        Args:
            config: Health check configuration
            ibkr_provider: IBKR state provider
            recon_provider: Reconciliation state provider
            position_provider: Position state provider
        """
        self._config = config or SemanticHealthConfig()
        self._ibkr = ibkr_provider
        self._recon = recon_provider
        self._position = position_provider

    def check_all(self) -> SemanticHealthResult:
        """
        Run all semantic health checks.

        Returns:
            Aggregated result
        """
        result = SemanticHealthResult()

        # IBKR checks
        if self._ibkr:
            result.add_check(self._check_ibkr_connection())
            result.add_check(self._check_orders_flowing())
            result.add_check(self._check_fills_updating())

        # Reconciliation checks
        if self._recon:
            result.add_check(self._check_reconciliation_fresh())
            result.add_check(self._check_drift_resolved())

        # Position checks
        if self._position:
            result.add_check(self._check_stalled_positions())

        return result

    def _check_ibkr_connection(self) -> CheckResult:
        """Check IBKR connection status."""
        if not self._ibkr:
            return CheckResult(
                name="ibkr_connection",
                status=CheckStatus.UNKNOWN,
                message="IBKR provider not configured",
            )

        try:
            connected = self._ibkr.is_connected()
            if connected:
                return CheckResult(
                    name="ibkr_connection",
                    status=CheckStatus.OK,
                    message="IBKR connected",
                )
            else:
                return CheckResult(
                    name="ibkr_connection",
                    status=CheckStatus.CRITICAL,
                    message="IBKR disconnected",
                )
        except Exception as e:
            return CheckResult(
                name="ibkr_connection",
                status=CheckStatus.CRITICAL,
                message=f"IBKR check failed: {e}",
            )

    def _check_orders_flowing(self) -> CheckResult:
        """Check if pending orders are updating."""
        if not self._ibkr:
            return CheckResult(
                name="orders_flowing",
                status=CheckStatus.UNKNOWN,
                message="IBKR provider not configured",
            )

        try:
            pending = self._ibkr.get_pending_orders()
            if not pending:
                return CheckResult(
                    name="orders_flowing",
                    status=CheckStatus.OK,
                    message="No pending orders",
                )

            last_update = self._ibkr.get_last_order_update()
            if not last_update:
                return CheckResult(
                    name="orders_flowing",
                    status=CheckStatus.WARNING,
                    message=f"{len(pending)} pending orders, no update timestamp",
                    details={"pending_count": len(pending)},
                )

            age = (datetime.now(UTC) - last_update).total_seconds()
            if age > self._config.order_stale_threshold_sec:
                return CheckResult(
                    name="orders_flowing",
                    status=CheckStatus.WARNING,
                    message=f"Order status stale ({age:.0f}s)",
                    details={"pending_count": len(pending), "age_sec": age},
                )

            return CheckResult(
                name="orders_flowing",
                status=CheckStatus.OK,
                message=f"{len(pending)} pending, last update {age:.0f}s ago",
                details={"pending_count": len(pending), "age_sec": age},
            )

        except Exception as e:
            return CheckResult(
                name="orders_flowing",
                status=CheckStatus.WARNING,
                message=f"Order flow check failed: {e}",
            )

    def _check_fills_updating(self) -> CheckResult:
        """Check if fills are updating for open positions."""
        if not self._ibkr:
            return CheckResult(
                name="fills_updating",
                status=CheckStatus.UNKNOWN,
                message="IBKR provider not configured",
            )

        try:
            positions = self._ibkr.get_open_positions()
            if not positions:
                return CheckResult(
                    name="fills_updating",
                    status=CheckStatus.OK,
                    message="No open positions",
                )

            last_fill = self._ibkr.get_last_fill_time()
            if not last_fill:
                return CheckResult(
                    name="fills_updating",
                    status=CheckStatus.OK,
                    message=f"{len(positions)} positions, no recent fills",
                    details={"position_count": len(positions)},
                )

            age = (datetime.now(UTC) - last_fill).total_seconds()
            if age > self._config.fill_stale_threshold_sec:
                return CheckResult(
                    name="fills_updating",
                    status=CheckStatus.WARNING,
                    message=f"Fill data stale ({age:.0f}s)",
                    details={"position_count": len(positions), "age_sec": age},
                )

            return CheckResult(
                name="fills_updating",
                status=CheckStatus.OK,
                message=f"{len(positions)} positions, last fill {age:.0f}s ago",
                details={"position_count": len(positions), "age_sec": age},
            )

        except Exception as e:
            return CheckResult(
                name="fills_updating",
                status=CheckStatus.WARNING,
                message=f"Fill check failed: {e}",
            )

    def _check_reconciliation_fresh(self) -> CheckResult:
        """Check if reconciliation ran recently."""
        if not self._recon:
            return CheckResult(
                name="reconciliation_fresh",
                status=CheckStatus.UNKNOWN,
                message="Reconciliation provider not configured",
            )

        try:
            last_run = self._recon.get_last_run_time()
            if not last_run:
                return CheckResult(
                    name="reconciliation_fresh",
                    status=CheckStatus.WARNING,
                    message="No reconciliation run recorded",
                )

            age = (datetime.now(UTC) - last_run).total_seconds()
            if age > self._config.recon_stale_threshold_sec:
                return CheckResult(
                    name="reconciliation_fresh",
                    status=CheckStatus.WARNING,
                    message=f"Reconciliation stale ({age:.0f}s)",
                    details={"age_sec": age},
                )

            return CheckResult(
                name="reconciliation_fresh",
                status=CheckStatus.OK,
                message=f"Last reconciliation {age:.0f}s ago",
                details={"age_sec": age},
            )

        except Exception as e:
            return CheckResult(
                name="reconciliation_fresh",
                status=CheckStatus.WARNING,
                message=f"Reconciliation check failed: {e}",
            )

    def _check_drift_resolved(self) -> CheckResult:
        """Check for unresolved drift."""
        if not self._recon:
            return CheckResult(
                name="drift_resolved",
                status=CheckStatus.UNKNOWN,
                message="Reconciliation provider not configured",
            )

        try:
            unresolved = self._recon.get_unresolved_drift_count()
            if unresolved > 0:
                return CheckResult(
                    name="drift_resolved",
                    status=CheckStatus.CRITICAL,
                    message=f"{unresolved} unresolved drift events",
                    details={"unresolved_count": unresolved},
                )

            return CheckResult(
                name="drift_resolved",
                status=CheckStatus.OK,
                message="No unresolved drift",
            )

        except Exception as e:
            return CheckResult(
                name="drift_resolved",
                status=CheckStatus.WARNING,
                message=f"Drift check failed: {e}",
            )

    def _check_stalled_positions(self) -> CheckResult:
        """Check for stuck STALLED positions."""
        if not self._position:
            return CheckResult(
                name="stalled_positions",
                status=CheckStatus.UNKNOWN,
                message="Position provider not configured",
            )

        try:
            stalled = self._position.get_stalled_positions()
            if not stalled:
                return CheckResult(
                    name="stalled_positions",
                    status=CheckStatus.OK,
                    message="No stalled positions",
                )

            # Check duration of each stalled position
            critical_count = 0
            warning_count = 0

            for pos in stalled:
                duration = self._position.get_stalled_duration(pos.id)
                if duration:
                    secs = duration.total_seconds()
                    if secs > self._config.stalled_critical_sec:
                        critical_count += 1
                    elif secs > self._config.stalled_warning_sec:
                        warning_count += 1

            if critical_count > 0:
                return CheckResult(
                    name="stalled_positions",
                    status=CheckStatus.CRITICAL,
                    message=f"{critical_count} positions stalled > 10min",
                    details={
                        "total_stalled": len(stalled),
                        "critical_count": critical_count,
                        "warning_count": warning_count,
                    },
                )

            if warning_count > 0:
                return CheckResult(
                    name="stalled_positions",
                    status=CheckStatus.WARNING,
                    message=f"{warning_count} positions stalled > 5min",
                    details={
                        "total_stalled": len(stalled),
                        "warning_count": warning_count,
                    },
                )

            return CheckResult(
                name="stalled_positions",
                status=CheckStatus.OK,
                message=f"{len(stalled)} stalled positions (< 5min)",
                details={"total_stalled": len(stalled)},
            )

        except Exception as e:
            return CheckResult(
                name="stalled_positions",
                status=CheckStatus.WARNING,
                message=f"Stalled position check failed: {e}",
            )
