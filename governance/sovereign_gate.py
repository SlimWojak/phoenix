"""
Sovereign Gate — Single chokepoint for ALL capital mutations.

Sprint: S59 LEASE_WIRE (Track 1: CAPITAL_GUARD)

No capital path is reachable while:
  1. HALT.signal is present (filesystem check, fail-closed)
  2. Lease state is not ACTIVE
  3. Ceremony review is overdue (S59 T5 stub)

INVARIANTS:
  INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS
  INV-ACTIVATION-ONLY-VIA-GUARD
  INV-GOV-HALT-BEFORE-ACTION (extended scope)
  INV-CEREMONY-BLOCKS-ACTIVE (T5 wiring point)

DESIGN:
  - Python decorator @sovereign_gate usable on any capital-affecting method
  - Composes WITH execution/halt_gate.py (in-process signal), does NOT replace it
  - sovereign_gate = filesystem halt + lease state + ceremony
  - HaltGate = in-process signal + sentinel wiring
"""

from __future__ import annotations

import functools
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from .halt import check_halt_signal

log = logging.getLogger(__name__)

_P = ParamSpec("_P")
_R = TypeVar("_R")


class SovereignGateError(Exception):
    """Base error for sovereign gate rejections."""

    def __init__(self, reason: str, *, invariant: str = ""):
        self.reason = reason
        self.invariant = invariant
        super().__init__(
            f"SovereignGate REJECT: {reason}" + (f" [{invariant}]" if invariant else "")
        )


class HaltActiveError(SovereignGateError):
    """HALT.signal is present — all capital mutations blocked."""

    def __init__(self, source: str | None, detail: str | None):
        self.source = source
        self.detail = detail
        super().__init__(
            f"HALT active (source={source}, detail={detail})",
            invariant="INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS",
        )


class LeaseNotActiveError(SovereignGateError):
    """Lease is not in ACTIVE state — capital mutations blocked."""

    def __init__(self, current_state: str):
        self.current_state = current_state
        super().__init__(
            f"Lease state is {current_state}, not ACTIVE",
            invariant="INV-ACTIVATION-ONLY-VIA-GUARD",
        )


class CeremonyOverdueError(SovereignGateError):
    """Ceremony review is overdue — capital mutations blocked until human reviews."""

    def __init__(self, overdue_since: datetime):
        self.overdue_since = overdue_since
        super().__init__(
            f"Ceremony overdue since {overdue_since.isoformat()}",
            invariant="INV-CEREMONY-BLOCKS-ACTIVE",
        )


def _check_gate(
    *,
    require_active_lease: bool,
    swarm_path: Path | None,
    lease_manager_fn: Callable[[], Any] | None,
) -> None:
    """
    Core gate logic. Raises on any failure. Never returns silently on error.

    Checks in order:
      1. HALT.signal (filesystem, fail-closed)
      2. Lease state == ACTIVE (if required)
      3. Ceremony not overdue (if next_review_due is set)

    On ANY exception during gate checks: fail closed (treat as HALT).
    """
    # --- CHECK 1: External HALT signal ---
    try:
        halt_result = check_halt_signal(swarm_path)
    except Exception as exc:
        log.error("Sovereign gate: halt check raised, failing closed: %s", exc)
        raise SovereignGateError(
            f"Gate check exception (fail-closed): {exc}",
            invariant="INV-HALT-APPLIES-TO-ALL-CAPITAL-MUTATIONS",
        ) from exc

    if halt_result.halted:
        raise HaltActiveError(
            source=halt_result.source,
            detail=halt_result.reason or halt_result.error,
        )

    # --- CHECK 2: Lease state ---
    if require_active_lease:
        if lease_manager_fn is None:
            raise SovereignGateError(
                "require_active_lease=True but no lease_manager_fn provided",
                invariant="INV-ACTIVATION-ONLY-VIA-GUARD",
            )

        try:
            manager = lease_manager_fn()
        except Exception as exc:
            log.error("Sovereign gate: lease manager access failed, failing closed: %s", exc)
            raise SovereignGateError(
                f"Lease manager access failed (fail-closed): {exc}",
                invariant="INV-ACTIVATION-ONLY-VIA-GUARD",
            ) from exc

        from .lease_types import LeaseState

        active_sm = getattr(manager, "active_lease", None)
        if active_sm is None:
            raw_sm = getattr(manager, "_active_lease", None)
            if raw_sm is not None:
                raise LeaseNotActiveError(raw_sm.state.value)
            raise LeaseNotActiveError("ABSENT")

        current_state = active_sm.state
        if current_state != LeaseState.ACTIVE:
            raise LeaseNotActiveError(current_state.value)

        # --- CHECK 3: Ceremony not overdue ---
        lease = active_sm.lease
        governance = getattr(lease, "governance", None)
        if governance is not None:
            next_review = getattr(governance, "next_review_due", None)
            if next_review is not None:
                now = datetime.now(UTC)
                if now > next_review:
                    raise CeremonyOverdueError(next_review)


def sovereign_gate(
    *,
    require_active_lease: bool = True,
    swarm_path: Path | None = None,
    lease_manager_fn: Callable[[], Any] | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """
    Decorator enforcing sovereign gate on capital-affecting methods.

    Usage:
        @sovereign_gate()
        def activate(self, ...):
            ...

        @sovereign_gate(require_active_lease=False)
        def some_setup_method(self, ...):
            ...

    On failure: raises SovereignGateError (or subclass). Never continues.
    On exception during check: fail closed (raises SovereignGateError).
    """

    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
        @functools.wraps(fn)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            _resolve_and_check(
                require_active_lease=require_active_lease,
                swarm_path=swarm_path,
                lease_manager_fn=lease_manager_fn,
            )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def check_sovereign_gate(
    *,
    require_active_lease: bool = True,
    swarm_path: Path | None = None,
    lease_manager_fn: Callable[[], Any] | None = None,
) -> None:
    """
    Imperative gate check for call sites that can't use the decorator.

    Raises SovereignGateError on any failure.
    """
    _resolve_and_check(
        require_active_lease=require_active_lease,
        swarm_path=swarm_path,
        lease_manager_fn=lease_manager_fn,
    )


def _resolve_and_check(
    *,
    require_active_lease: bool,
    swarm_path: Path | None,
    lease_manager_fn: Callable[[], Any] | None,
) -> None:
    """Resolve defaults and delegate to core gate logic."""
    mgr_fn = lease_manager_fn
    if mgr_fn is None and require_active_lease:

        def _default_manager() -> Any:
            from .lease import LeaseManager

            return LeaseManager()

        mgr_fn = _default_manager

    _check_gate(
        require_active_lease=require_active_lease,
        swarm_path=swarm_path,
        lease_manager_fn=mgr_fn,
    )
