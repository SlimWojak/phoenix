"""
GovernanceSentinel — Passive Bounds Enforcement (S52 T2)
========================================================

AUDIT REF: FORENSIC_AUDIT.md RISK-3
BRIEF REF: S52_HARDENING_BRIEF.md T2: PASSIVE BOUNDS

Design (OWL advisor contract):
  The GovernanceSentinel wraps state updates. State cannot update
  without passing through bounds enforcement. This is NOT a cron job —
  it fires ON EVERY STATE UPDATE.

CTO ADDENDUM 1_T2_EXTERNAL_HEARTBEAT:
  Heartbeat detection lives in the EXECUTION LOOP, not inside the sentinel.
  A crashed sentinel cannot self-report. Track last_sentinel_execution_timestamp
  externally. If now - last_execution > threshold → HALT.

CTO ADDENDUM 2_T2_LATENCY_CEILING:
  sentinel_check_latency < 2ms. Prevents invisible latency creep.

INVARIANTS:
  INV-BOUNDS-PASSIVE-1: Bounds fire on every state update, not on cron.
  INV-BOUNDS-HEARTBEAT-1: External liveness tracking. Silent > threshold → HALT.
  INV-SENTINEL-LATENCY-1: sentinel_check_latency < 2ms.
"""

from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# =============================================================================
# GOVERNANCE VERDICT
# =============================================================================


class GovernanceVerdict(Enum):
    """Result of sentinel check."""

    PASS = "PASS"
    FAIL_BOUNDS_BREACH = "FAIL_BOUNDS_BREACH"
    FAIL_SENTINEL_STALE = "FAIL_SENTINEL_STALE"
    FAIL_NO_LEASE = "FAIL_NO_LEASE"


@dataclass(frozen=True)
class SentinelResult:
    """Immutable result from sentinel intercept."""

    verdict: GovernanceVerdict
    check_latency_ns: int
    breach_detail: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def check_latency_ms(self) -> float:
        return self.check_latency_ns / 1_000_000


# =============================================================================
# ABSTRACT GOVERNANCE SENTINEL
# =============================================================================


class GovernanceSentinel(ABC):
    """
    Abstract sentinel interface.

    Implementations intercept state updates and enforce governance rules.
    """

    @abstractmethod
    def intercept(self, state: dict[str, Any]) -> SentinelResult:
        """
        Passive check on state update.

        FAIL verdict → execution engine MUST transition to HALTED.
        """
        ...

    @abstractmethod
    def get_last_execution_timestamp(self) -> datetime | None:
        """
        External heartbeat: when did sentinel last execute?

        CTO ADDENDUM: This is read by the EXECUTION LOOP, not by the sentinel.
        A crashed sentinel cannot self-report.
        """
        ...


# =============================================================================
# BOUNDS SENTINEL — Wraps LeaseInterpreter
# =============================================================================


class BoundsSentinel(GovernanceSentinel):
    """
    Passive bounds enforcement wrapping LeaseInterpreter.

    INV-BOUNDS-PASSIVE-1: Fires on every state update.
    INV-SENTINEL-LATENCY-1: < 2ms per check.
    """

    def __init__(
        self,
        lease_interpreter: Any | None = None,
        halt_callback: Any | None = None,
        staleness_threshold_sec: float = 30.0,
    ) -> None:
        self._interpreter = lease_interpreter
        self._halt_callback = halt_callback
        self._staleness_threshold_sec = staleness_threshold_sec

        # External heartbeat state (read by execution loop)
        self._last_execution_timestamp: datetime | None = None
        self._lock = threading.Lock()

        # Metrics
        self._check_count: int = 0
        self._breach_count: int = 0
        self._max_latency_ns: int = 0

    def attach_interpreter(self, interpreter: Any) -> None:
        """Attach or replace the LeaseInterpreter."""
        self._interpreter = interpreter

    def intercept(self, state: dict[str, Any]) -> SentinelResult:
        """
        Check bounds against current state.

        State must provide:
          - current_drawdown_pct: float
          - consecutive_losses: int
          - daily_loss_pct: float | None (optional)
        """
        start_ns = time.perf_counter_ns()

        try:
            if self._interpreter is None or not self._interpreter.is_active:
                elapsed_ns = time.perf_counter_ns() - start_ns
                self._record_execution(elapsed_ns)
                return SentinelResult(
                    verdict=GovernanceVerdict.FAIL_NO_LEASE,
                    check_latency_ns=elapsed_ns,
                    breach_detail="No active lease or interpreter",
                )

            drawdown = state.get("current_drawdown_pct", 0.0)
            losses = state.get("consecutive_losses", 0)
            daily = state.get("daily_loss_pct")

            breaches = self._interpreter.check_all_bounds(
                current_drawdown_pct=drawdown,
                consecutive_losses=losses,
                daily_loss_pct=daily,
            )

            elapsed_ns = time.perf_counter_ns() - start_ns
            self._record_execution(elapsed_ns)

            if breaches:
                self._breach_count += 1
                breach = breaches[0]

                if self._halt_callback:
                    self._halt_callback(f"SENTINEL_BOUNDS_BREACH: {breach.bound_name}")

                self._interpreter.enforce_bounds(drawdown, losses, daily)

                return SentinelResult(
                    verdict=GovernanceVerdict.FAIL_BOUNDS_BREACH,
                    check_latency_ns=elapsed_ns,
                    breach_detail=f"{breach.bound_name}: {breach.current_value} > {breach.limit}",
                )

            return SentinelResult(
                verdict=GovernanceVerdict.PASS,
                check_latency_ns=elapsed_ns,
            )

        except Exception as exc:
            elapsed_ns = time.perf_counter_ns() - start_ns
            self._record_execution(elapsed_ns)
            return SentinelResult(
                verdict=GovernanceVerdict.FAIL_BOUNDS_BREACH,
                check_latency_ns=elapsed_ns,
                breach_detail=f"Sentinel error: {exc}",
            )

    def get_last_execution_timestamp(self) -> datetime | None:
        """CTO ADDENDUM: External heartbeat read point."""
        with self._lock:
            return self._last_execution_timestamp

    def _record_execution(self, latency_ns: int) -> None:
        """Record execution for heartbeat and metrics."""
        with self._lock:
            self._last_execution_timestamp = datetime.now(UTC)
            self._check_count += 1
            if latency_ns > self._max_latency_ns:
                self._max_latency_ns = latency_ns

    def get_metrics(self) -> dict[str, Any]:
        """Observable metrics for monitoring."""
        with self._lock:
            return {
                "check_count": self._check_count,
                "breach_count": self._breach_count,
                "max_latency_ms": self._max_latency_ns / 1_000_000,
                "last_execution": (
                    self._last_execution_timestamp.isoformat()
                    if self._last_execution_timestamp
                    else None
                ),
                "staleness_threshold_sec": self._staleness_threshold_sec,
            }


# =============================================================================
# DEAD-MAN'S SWITCH — External Heartbeat Monitor
# =============================================================================


class SentinelHeartbeatMonitor:
    """
    External dead-man's switch for sentinel liveness.

    CTO ADDENDUM 1_T2_EXTERNAL_HEARTBEAT:
      Heartbeat detection lives in the EXECUTION LOOP, not inside the sentinel.
      A crashed sentinel cannot self-report.

    Usage:
      monitor = SentinelHeartbeatMonitor(sentinel, halt_fn, threshold_sec=30)
      # Call from execution loop:
      monitor.check_liveness()  # → True if alive, triggers HALT if dead
    """

    def __init__(
        self,
        sentinel: GovernanceSentinel,
        halt_callback: Any,
        threshold_sec: float = 30.0,
    ) -> None:
        self._sentinel = sentinel
        self._halt_callback = halt_callback
        self._threshold_sec = threshold_sec
        self._halted = False

    def check_liveness(self) -> bool:
        """
        Check if sentinel is alive (called from EXECUTION LOOP).

        Returns True if sentinel is alive, False if stale → triggers HALT.
        """
        if self._halted:
            return False

        last_exec = self._sentinel.get_last_execution_timestamp()

        if last_exec is None:
            return True

        now = datetime.now(UTC)
        staleness_sec = (now - last_exec).total_seconds()

        if staleness_sec > self._threshold_sec:
            self._halted = True
            if self._halt_callback:
                self._halt_callback(
                    f"SENTINEL_DEAD: no execution for {staleness_sec:.1f}s "
                    f"(threshold: {self._threshold_sec}s)"
                )
            return False

        return True

    @property
    def is_halted(self) -> bool:
        return self._halted

    def reset(self) -> None:
        """Reset for testing."""
        self._halted = False
