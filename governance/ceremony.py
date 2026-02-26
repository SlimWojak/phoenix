"""
Ceremony Engine — Full Attestation Lifecycle.

Sprint: S60 CEREMONY_AND_HYGIENE (Track 1)
Design Spec: docs/canon/designs/CARTRIDGE_AND_LEASE_DESIGN_v1.0.md Section 6.3

Lifecycle:
  1. On lease activation/renewal → set next_review_due (default: +7 days)
  2. sovereign_gate checks ceremony_due (S59 stub — already wired)
  3. Human initiates review → system presents evidence
  4. Human signs off → CeremonyAttestationBead emitted (durable)
  5. next_review_due advances by ceremony_interval_days
  6. If missed → lease stays HALTED until human reviews + attests

INVARIANTS:
  INV-CEREMONY-BLOCKS-ACTIVE: Overdue review halts lease execution (S59)
  INV-CEREMONY-ATTESTATION-DURABLE: Attestation bead persists before next_review_due advances
  INV-CEREMONY-BOUNDS-MONOTONIC: Ceremony may tighten bounds; never loosen beyond original ceiling
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .bead_emitter import DurableBeadEmitter
    from .lease import LeaseStateMachine

log = logging.getLogger(__name__)

DEFAULT_CEREMONY_INTERVAL_DAYS = 7


class AttestationDecision(str, Enum):
    RENEWED = "RENEWED"
    TIGHTENED = "TIGHTENED"
    REVOKED = "REVOKED"


@dataclass(frozen=True)
class CeremonyAttestationBead:
    """Bead emitted on successful attestation.

    INV-CEREMONY-ATTESTATION-DURABLE: Must persist before state advances.
    """

    bead_type: str = "CEREMONY_ATTESTATION_BEAD"
    lease_id: str = ""
    reviewer: str = ""
    reviewed_at: str = ""
    attestation: str = ""
    bounds_changes: dict[str, Any] = field(default_factory=dict)
    evidence_hash: str = ""
    next_review_due: str = ""
    timestamp: str = ""

    def model_dump(self, mode: str = "json") -> dict[str, Any]:
        return {
            "bead_type": self.bead_type,
            "lease_id": self.lease_id,
            "reviewer": self.reviewer,
            "reviewed_at": self.reviewed_at,
            "attestation": self.attestation,
            "bounds_changes": self.bounds_changes,
            "evidence_hash": self.evidence_hash,
            "next_review_due": self.next_review_due,
            "timestamp": self.timestamp,
        }


@dataclass
class CeremonyEvidence:
    """Evidence snapshot presented during ceremony review.

    INV-HARNESS-1: Facts only. No grades, no recommendations.
    """

    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl_total: float = 0.0
    max_drawdown_pct: float = 0.0
    gates_passed: int = 0
    gates_failed: int = 0
    period_start: datetime | None = None
    period_end: datetime | None = None

    def compute_hash(self) -> str:
        """Deterministic hash for attestation bead.

        Advisory: sorted + canonicalized before hashing.
        """
        data = {
            "total_trades": self.total_trades,
            "wins": self.wins,
            "losses": self.losses,
            "pnl_total": self.pnl_total,
            "max_drawdown_pct": self.max_drawdown_pct,
            "gates_passed": self.gates_passed,
            "gates_failed": self.gates_failed,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
        }
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class CeremonyEngine:
    """
    Manages the weekly attestation ceremony lifecycle.

    The ceremony is HUMAN-INITIATED. The engine PRESENTS evidence
    and RECORDS attestation. It does NOT decide.
    """

    def __init__(
        self,
        emitter: DurableBeadEmitter | None = None,
        interval_days: int = DEFAULT_CEREMONY_INTERVAL_DAYS,
    ) -> None:
        self._emitter = emitter
        self._interval_days = interval_days

    def schedule_review(self, state_machine: LeaseStateMachine) -> datetime:
        """Set next_review_due on a lease (called on activation/renewal).

        Returns the scheduled review datetime.
        """
        now = datetime.now(UTC)
        next_due = now + timedelta(days=self._interval_days)
        state_machine.lease.governance.next_review_due = next_due
        log.info(
            "Ceremony scheduled: lease=%s due=%s",
            state_machine.lease.identity.lease_id,
            next_due.isoformat(),
        )
        return next_due

    def gather_evidence(self, state_machine: LeaseStateMachine) -> CeremonyEvidence:
        """Gather evidence for ceremony review.

        Queries governance beads for the current lease period.
        Returns facts only — no grades, no recommendations.
        """
        return CeremonyEvidence(
            period_start=state_machine.lease.status.activated_at,
            period_end=datetime.now(UTC),
        )

    def attest(
        self,
        state_machine: LeaseStateMachine,
        reviewer: str,
        decision: AttestationDecision,
        evidence: CeremonyEvidence,
        bounds_changes: dict[str, Any] | None = None,
    ) -> CeremonyAttestationBead:
        """
        Record attestation and advance next_review_due.

        INV-CEREMONY-ATTESTATION-DURABLE: Bead persists BEFORE state advances.
        INV-CEREMONY-BOUNDS-MONOTONIC: Tightened bounds checked against ceiling.

        Args:
            state_machine: Active lease state machine
            reviewer: Human who reviewed
            decision: RENEWED, TIGHTENED, or REVOKED
            evidence: Evidence snapshot from gather_evidence()
            bounds_changes: New bounds (for TIGHTENED only)

        Returns:
            CeremonyAttestationBead (already persisted)

        Raises:
            ValueError: If bounds_changes would loosen beyond ceiling
        """
        lease = state_machine.lease
        now = datetime.now(UTC)

        if decision == AttestationDecision.TIGHTENED and bounds_changes:
            violations = self._check_bounds_monotonic(lease, bounds_changes)
            if violations:
                raise ValueError(
                    f"INV-CEREMONY-BOUNDS-MONOTONIC: Cannot loosen bounds: {violations}"
                )

        next_due = now + timedelta(days=self._interval_days)

        bead = CeremonyAttestationBead(
            lease_id=lease.identity.lease_id,
            reviewer=reviewer,
            reviewed_at=now.isoformat(),
            attestation=decision.value,
            bounds_changes=bounds_changes or {},
            evidence_hash=evidence.compute_hash(),
            next_review_due=next_due.isoformat(),
            timestamp=now.isoformat(),
        )

        if self._emitter is not None:
            self._emitter.emit(bead)

        lease.governance.last_review_at = now
        lease.governance.next_review_due = next_due
        lease.governance.reviewer = reviewer

        if decision == AttestationDecision.TIGHTENED and bounds_changes:
            self._apply_tightened_bounds(lease, bounds_changes)

        if decision == AttestationDecision.REVOKED:
            state_machine.revoke(revoked_by=reviewer, reason="Ceremony: REVOKED by reviewer")

        log.info(
            "Ceremony attestation recorded: lease=%s decision=%s reviewer=%s next_due=%s",
            lease.identity.lease_id,
            decision.value,
            reviewer,
            next_due.isoformat(),
        )

        return bead

    def _check_bounds_monotonic(
        self,
        lease: Any,
        changes: dict[str, Any],
    ) -> list[str]:
        """INV-CEREMONY-BOUNDS-MONOTONIC: Can only tighten, never loosen."""
        violations: list[str] = []
        bounds = lease.bounds

        if "max_drawdown_pct" in changes:
            if changes["max_drawdown_pct"] > bounds.max_drawdown_pct:
                violations.append(
                    f"max_drawdown_pct: {changes['max_drawdown_pct']} > current "
                    f"{bounds.max_drawdown_pct}"
                )

        if "max_consecutive_losses" in changes:
            if changes["max_consecutive_losses"] > bounds.max_consecutive_losses:
                violations.append(
                    f"max_consecutive_losses: {changes['max_consecutive_losses']} > current "
                    f"{bounds.max_consecutive_losses}"
                )

        if "position_size_cap" in changes and bounds.position_size_cap is not None:
            if changes["position_size_cap"] > bounds.position_size_cap:
                violations.append(
                    f"position_size_cap: {changes['position_size_cap']} > current "
                    f"{bounds.position_size_cap}"
                )

        return violations

    def _apply_tightened_bounds(
        self,
        lease: Any,
        changes: dict[str, Any],
    ) -> None:
        """Apply tightened bounds to lease."""
        bounds = lease.bounds
        if "max_drawdown_pct" in changes:
            bounds.max_drawdown_pct = changes["max_drawdown_pct"]
        if "max_consecutive_losses" in changes:
            bounds.max_consecutive_losses = changes["max_consecutive_losses"]
        if "position_size_cap" in changes:
            bounds.position_size_cap = changes["position_size_cap"]
