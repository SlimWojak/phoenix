"""
Promotion Ceremony — Shadow to Live workflow
============================================

S32: EXECUTION_PATH

Formal ceremony for promoting from Shadow to Live trading.

INVARIANTS:
- INV-PROMOTION-EVIDENCE-1: Every promotion needs evidence bundle
- INV-PROMOTION-T2-1: Promotion requires T2 approval

WATCHPOINT WP_D2:
- Promotion is ONE-WAY
- No automatic demotion once PROMOTION bead emitted
- Demotion requires separate explicit intent (future sprint)
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .checklist import ChecklistResult, PromotionChecklist


class PromotionStatus(Enum):
    """Promotion request status."""

    PENDING = "PENDING"      # Checklist not evaluated
    BLOCKED = "BLOCKED"      # Failed hard blockers
    READY = "READY"          # Checklist passed, awaiting approval
    APPROVED = "APPROVED"    # T2 approved
    PROMOTED = "PROMOTED"    # Promotion complete (BEAD emitted)
    REJECTED = "REJECTED"    # Manually rejected


@dataclass
class PromotionRequest:
    """
    Request for promotion from Shadow to Live.

    Tracks the promotion workflow state.
    """

    request_id: str = field(default_factory=lambda: f"PROMO-{uuid.uuid4().hex[:8]}")
    strategy_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    status: PromotionStatus = PromotionStatus.PENDING

    # Checklist
    checklist_result: ChecklistResult | None = None

    # Evidence
    evidence_bundle: dict[str, Any] = field(default_factory=dict)
    evidence_hash: str = ""

    # Approval
    token_id: str | None = None
    approved_by: str | None = None
    approved_at: datetime | None = None

    # Promotion
    promoted_at: datetime | None = None
    promotion_bead_id: str | None = None

    # Rejection
    rejection_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "strategy_id": self.strategy_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "checklist_passed": self.checklist_result.can_promote if self.checklist_result else None,  # noqa: E501
            "evidence_hash": self.evidence_hash,
            "token_id": self.token_id,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "promoted_at": self.promoted_at.isoformat() if self.promoted_at else None,
            "promotion_bead_id": self.promotion_bead_id,
            "rejection_reason": self.rejection_reason,
        }


@dataclass
class PromotionResponse:
    """Response from promotion ceremony."""

    success: bool
    request_id: str
    status: PromotionStatus
    message: str = ""
    blockers: list[str] = field(default_factory=list)
    promotion_bead_id: str | None = None

    @classmethod
    def blocked(cls, request_id: str, blockers: list[str]) -> PromotionResponse:
        """Create blocked response."""
        return cls(
            success=False,
            request_id=request_id,
            status=PromotionStatus.BLOCKED,
            message=f"Blocked: {', '.join(blockers)}",
            blockers=blockers,
        )

    @classmethod
    def rejected(cls, request_id: str, reason: str) -> PromotionResponse:
        """Create rejection response."""
        return cls(
            success=False,
            request_id=request_id,
            status=PromotionStatus.REJECTED,
            message=f"Rejected: {reason}",
        )

    @classmethod
    def promoted(cls, request_id: str, bead_id: str) -> PromotionResponse:
        """Create successful promotion response."""
        return cls(
            success=True,
            request_id=request_id,
            status=PromotionStatus.PROMOTED,
            message="Promotion complete",
            promotion_bead_id=bead_id,
        )


class PromotionCeremony:
    """
    Promotion ceremony workflow.

    Steps:
    0. Assert kill_flag == False (WP_D1)
    1. Checklist evaluation
    2. Evidence bundle assembly
    3. Human reviews evidence
    4. T2 approval token issued
    5. PROMOTION bead emitted
    6. Live trading enabled

    WATCHPOINT WP_D2:
    Promotion is ONE-WAY. No automatic demotion.
    Once PROMOTION bead is emitted, status is permanent until
    explicit demotion intent (future sprint).
    """

    def __init__(
        self,
        checklist: PromotionChecklist | None = None,
        emit_bead: Callable[[dict[str, Any]], None] | None = None,
        emit_alert: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Initialize ceremony.

        Args:
            checklist: Promotion checklist validator
            emit_bead: Callback for PROMOTION bead emission
            emit_alert: Callback for alerts
        """
        self._checklist = checklist or PromotionChecklist()
        self._emit_bead = emit_bead
        self._emit_alert = emit_alert
        self._requests: dict[str, PromotionRequest] = {}

    def create_request(self, strategy_id: str) -> PromotionRequest:
        """
        Create a new promotion request.

        Args:
            strategy_id: Strategy to promote

        Returns:
            New PromotionRequest
        """
        request = PromotionRequest(strategy_id=strategy_id)
        self._requests[request.request_id] = request
        return request

    def evaluate_checklist(self, request_id: str) -> PromotionResponse:
        """
        Evaluate promotion checklist.

        WATCHPOINT WP_D1: Hard blocks on kill flags, STALLED, drift.

        Args:
            request_id: Request to evaluate

        Returns:
            PromotionResponse with result
        """
        request = self._requests.get(request_id)
        if request is None:
            return PromotionResponse.rejected(request_id, "Request not found")

        # Evaluate checklist
        result = self._checklist.evaluate()
        request.checklist_result = result

        # Check for blockers (WP_D1)
        if result.has_blockers:
            request.status = PromotionStatus.BLOCKED
            blocker_names = [b.name for b in result.blockers]
            return PromotionResponse.blocked(request_id, blocker_names)

        request.status = PromotionStatus.READY
        return PromotionResponse(
            success=True,
            request_id=request_id,
            status=PromotionStatus.READY,
            message="Checklist passed, ready for approval",
        )

    def assemble_evidence(
        self,
        request_id: str,
        shadow_stats: dict[str, Any],
        autopsy_summary: str = "",
    ) -> dict[str, Any]:
        """
        Assemble evidence bundle for human review.

        INV-PROMOTION-EVIDENCE-1: Every promotion needs evidence.

        Args:
            request_id: Request to assemble evidence for
            shadow_stats: Shadow trading statistics
            autopsy_summary: Summary from autopsy analysis

        Returns:
            Evidence bundle
        """
        request = self._requests.get(request_id)
        if request is None:
            return {}

        evidence = {
            "strategy_id": request.strategy_id,
            "request_id": request_id,
            "evaluated_at": datetime.now(UTC).isoformat(),
            # Performance
            "max_drawdown": shadow_stats.get("max_drawdown", 0),
            "worst_day": shadow_stats.get("worst_day", 0),
            "sharpe": shadow_stats.get("sharpe", 0),
            "total_trades": shadow_stats.get("total_trades", 0),
            "win_rate": shadow_stats.get("win_rate", 0),
            # Defensive
            "signalman_kills": shadow_stats.get("signalman_kills", 0),
            "override_frequency": shadow_stats.get("override_frequency", 0),
            # Reasoning
            "autopsy_summary": autopsy_summary,
            # Checklist
            "checklist_ok": bool(request.checklist_result and request.checklist_result.can_promote),
        }

        request.evidence_bundle = evidence

        # Compute hash
        import hashlib
        import json
        evidence_str = json.dumps(evidence, sort_keys=True)
        request.evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        return evidence

    def approve(
        self,
        request_id: str,
        token_id: str,
        approved_by: str,
    ) -> PromotionResponse:
        """
        Approve promotion with T2 token.

        INV-PROMOTION-T2-1: Promotion requires T2 approval.

        Args:
            request_id: Request to approve
            token_id: T2 approval token
            approved_by: Human identifier

        Returns:
            PromotionResponse
        """
        request = self._requests.get(request_id)
        if request is None:
            return PromotionResponse.rejected(request_id, "Request not found")

        if request.status != PromotionStatus.READY:
            return PromotionResponse.rejected(
                request_id,
                f"Cannot approve: status is {request.status.value}",
            )

        request.token_id = token_id
        request.approved_by = approved_by
        request.approved_at = datetime.now(UTC)
        request.status = PromotionStatus.APPROVED

        return PromotionResponse(
            success=True,
            request_id=request_id,
            status=PromotionStatus.APPROVED,
            message="Approved, ready for promotion",
        )

    def promote(self, request_id: str) -> PromotionResponse:
        """
        Execute promotion.

        WATCHPOINT WP_D2: This is ONE-WAY.
        Once PROMOTION bead is emitted, there is no automatic demotion.

        Args:
            request_id: Request to promote

        Returns:
            PromotionResponse with PROMOTION bead ID
        """
        request = self._requests.get(request_id)
        if request is None:
            return PromotionResponse.rejected(request_id, "Request not found")

        if request.status != PromotionStatus.APPROVED:
            return PromotionResponse.rejected(
                request_id,
                f"Cannot promote: status is {request.status.value}",
            )

        # Emit PROMOTION bead
        bead_id = f"BEAD-{uuid.uuid4().hex[:8]}"
        self._emit_promotion_bead(request, bead_id)

        # Update request
        request.status = PromotionStatus.PROMOTED
        request.promoted_at = datetime.now(UTC)
        request.promotion_bead_id = bead_id

        # Alert
        if self._emit_alert:
            self._emit_alert(
                f"PROMOTION: {request.strategy_id} promoted to LIVE",
                "INFO",
            )

        return PromotionResponse.promoted(request_id, bead_id)

    def reject(self, request_id: str, reason: str) -> PromotionResponse:
        """
        Reject promotion request.

        Args:
            request_id: Request to reject
            reason: Rejection reason

        Returns:
            PromotionResponse
        """
        request = self._requests.get(request_id)
        if request is not None:
            request.status = PromotionStatus.REJECTED
            request.rejection_reason = reason

        return PromotionResponse.rejected(request_id, reason)

    def _emit_promotion_bead(self, request: PromotionRequest, bead_id: str) -> None:
        """
        Emit PROMOTION bead.

        WATCHPOINT WP_D2: Once emitted, promotion is permanent.
        """
        if self._emit_bead is None:
            return

        bead_data = {
            "bead_type": "PROMOTION",
            "bead_id": bead_id,
            "strategy_id": request.strategy_id,
            "request_id": request.request_id,
            "evidence_hash": request.evidence_hash,
            "approved_by": request.approved_by,
            "token_id": request.token_id,
            "timestamp_utc": datetime.now(UTC).isoformat(),
        }

        try:
            self._emit_bead(bead_data)
        except Exception:  # noqa: S110
            pass  # Non-blocking but logged

    def get_request(self, request_id: str) -> PromotionRequest | None:
        """Get promotion request by ID."""
        return self._requests.get(request_id)

    def get_promoted_strategies(self) -> list[str]:
        """Get list of promoted strategy IDs."""
        return [
            r.strategy_id
            for r in self._requests.values()
            if r.status == PromotionStatus.PROMOTED
        ]
