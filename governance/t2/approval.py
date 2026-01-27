"""
T2 Approval — Approval workflow
===============================

S32: EXECUTION_PATH

Main T2 workflow: request → display → approve → token → execute.
This is where human sovereignty over capital is enforced.

INVARIANTS:
- INV-T2-TOKEN-1: Single-use, 5-min expiry
- INV-T2-GATE-1: No order without valid token
- INV-T2-TOKEN-AUDIT-1: Bead at every state change
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from .evidence import EvidenceBuilder, EvidenceBundle
from .tokens import Token, TokenStore, ValidationResult


class ApprovalStatus(Enum):
    """Approval request status."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    BLOCKED = "BLOCKED"  # Blocked by kill flag or drift


@dataclass
class ApprovalRequest:
    """
    Request for T2 approval.

    Represents an intent awaiting human approval.
    """

    request_id: str = field(default_factory=lambda: f"REQ-{uuid.uuid4().hex[:8]}")
    intent_id: str = ""
    signal_id: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    evidence: EvidenceBundle | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING

    # Trade details
    pair: str = ""
    side: str = ""
    quantity: float = 0.0
    entry_price: float = 0.0
    stop_price: float = 0.0
    target_price: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "intent_id": self.intent_id,
            "signal_id": self.signal_id,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "pair": self.pair,
            "side": self.side,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "target_price": self.target_price,
            "evidence": self.evidence.to_dict() if self.evidence else None,
        }


@dataclass
class ApprovalResponse:
    """Response from T2 approval."""

    approved: bool
    request_id: str
    token: Token | None = None
    blockers: list[str] = field(default_factory=list)
    message: str = ""

    @classmethod
    def success(cls, request_id: str, token: Token) -> ApprovalResponse:
        """Create success response."""
        return cls(
            approved=True,
            request_id=request_id,
            token=token,
            message="Approved",
        )

    @classmethod
    def blocked(cls, request_id: str, blockers: list[str]) -> ApprovalResponse:
        """Create blocked response."""
        return cls(
            approved=False,
            request_id=request_id,
            blockers=blockers,
            message=f"Blocked: {', '.join(blockers)}",
        )

    @classmethod
    def rejected(cls, request_id: str, reason: str) -> ApprovalResponse:
        """Create rejection response."""
        return cls(
            approved=False,
            request_id=request_id,
            message=f"Rejected: {reason}",
        )


class T2Workflow:
    """
    T2 approval workflow.

    Flow:
    1. CSO emits CSE signal (READY)
    2. Intent created from CSE
    3. Evidence bundle assembled
    4. Human reviews evidence
    5. Human approves/rejects
    6. Token issued (if approved)
    7. Token used for order
    8. Beads emitted at each step

    INVARIANTS:
    - INV-T2-TOKEN-1: Single-use, 5-min expiry
    - INV-T2-GATE-1: No order without valid token
    - INV-T2-TOKEN-AUDIT-1: Bead at every state change
    """

    def __init__(
        self,
        token_store: TokenStore | None = None,
        stale_gate: Any = None,
        notify: Callable[[str, str], None] | None = None,
    ) -> None:
        """
        Initialize workflow.

        Args:
            token_store: Token storage (created if not provided)
            stale_gate: Stale gate for context freshness
            notify: Notification callback (message, level)
        """
        self._token_store = token_store or TokenStore()
        self._stale_gate = stale_gate
        self._notify = notify
        self._pending: dict[str, ApprovalRequest] = {}

    @property
    def token_store(self) -> TokenStore:
        """Get token store."""
        return self._token_store

    def create_request(
        self,
        signal_id: str,
        pair: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_price: float,
        target_price: float,
    ) -> ApprovalRequest:
        """
        Create approval request.

        Args:
            signal_id: CSE signal ID
            pair: Currency pair
            side: LONG or SHORT
            quantity: Position size
            entry_price: Entry price
            stop_price: Stop loss
            target_price: Take profit

        Returns:
            ApprovalRequest ready for evidence assembly
        """
        request = ApprovalRequest(
            intent_id=f"INT-{uuid.uuid4().hex[:8]}",
            signal_id=signal_id,
            pair=pair,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
        )

        self._pending[request.request_id] = request
        return request

    def assemble_evidence(
        self,
        request: ApprovalRequest,
        setup_quality: float,
        setup_type: str,
        htf_bias: str,
        htf_confirmed: bool,
        ltf_setup: str,
        state_hash: str,
        state_captured_at: datetime,
        state_ttl_sec: int = 1800,
        kill_flags_active: bool = False,
        kill_flag_details: list[str] | None = None,
        unresolved_drift: bool = False,
    ) -> EvidenceBundle:
        """
        Assemble evidence bundle for request.

        Args:
            request: Approval request
            setup_quality: CSO quality score
            setup_type: Setup type (FVG_ENTRY, OTE_ENTRY, etc.)
            htf_bias: Higher timeframe bias
            htf_confirmed: HTF structure confirmed
            ltf_setup: LTF setup type
            state_hash: State anchor hash
            state_captured_at: When state was captured
            state_ttl_sec: State TTL in seconds
            kill_flags_active: Any kill flags active
            kill_flag_details: Kill flag details
            unresolved_drift: Unresolved reconciliation drift

        Returns:
            Evidence bundle ready for display
        """
        builder = EvidenceBuilder(request.intent_id)

        evidence = (
            builder
            .with_setup(
                quality_score=setup_quality,
                setup_type=setup_type,
                pair=request.pair,
            )
            .with_alignment(
                htf_bias=htf_bias,
                htf_confirmed=htf_confirmed,
                ltf_setup=ltf_setup,
                ltf_level=request.entry_price,
            )
            .with_risk(
                entry_price=request.entry_price,
                stop_price=request.stop_price,
                target_price=request.target_price,
                risk_percent=1.0,  # Default, can be calculated
            )
            .with_state(
                state_hash=state_hash,
                captured_at=state_captured_at,
                ttl_sec=state_ttl_sec,
            )
            .with_safety(
                kill_flags_active=kill_flags_active,
                kill_flag_details=kill_flag_details,
                unresolved_drift=unresolved_drift,
            )
            .build()
        )

        request.evidence = evidence
        return evidence

    def check_approvalable(self, request: ApprovalRequest) -> list[str]:
        """
        Check if request can be approved.

        Returns list of blockers (empty if approvable).
        """
        if request.evidence is None:
            return ["No evidence assembled"]

        blockers = request.evidence.approval_blockers

        # Check stale gate
        if self._stale_gate is not None:
            stale_result = self._stale_gate.check(request.evidence.state.state_hash)
            if not stale_result.fresh:
                blockers.append(f"Stale context: {stale_result.reason}")

        return blockers

    def approve(self, request_id: str) -> ApprovalResponse:
        """
        Approve a request and issue token.

        Args:
            request_id: Request to approve

        Returns:
            ApprovalResponse with token or blockers
        """
        request = self._pending.get(request_id)
        if request is None:
            return ApprovalResponse.rejected(request_id, "Request not found")

        if request.evidence is None:
            return ApprovalResponse.rejected(request_id, "No evidence assembled")

        # Check blockers
        blockers = self.check_approvalable(request)
        if blockers:
            request.status = ApprovalStatus.BLOCKED
            return ApprovalResponse.blocked(request_id, blockers)

        # Issue token
        evidence_hash = request.evidence.compute_hash()

        try:
            token = self._token_store.issue(
                intent_id=request.intent_id,
                evidence_hash=evidence_hash,
            )
        except ValueError as e:
            return ApprovalResponse.rejected(request_id, str(e))

        request.status = ApprovalStatus.APPROVED

        # Notify
        if self._notify:
            self._notify(
                f"T2 approved: {request.pair} {request.side} (token valid 5min)",
                "INFO",
            )

        return ApprovalResponse.success(request_id, token)

    def reject(self, request_id: str, reason: str = "Manual rejection") -> ApprovalResponse:
        """
        Reject a request.

        Args:
            request_id: Request to reject
            reason: Rejection reason

        Returns:
            ApprovalResponse
        """
        request = self._pending.get(request_id)
        if request is not None:
            request.status = ApprovalStatus.REJECTED

        return ApprovalResponse.rejected(request_id, reason)

    def validate_for_execution(
        self,
        token_id: str,
        intent_id: str,
        evidence_hash: str,
    ) -> ValidationResult:
        """
        Validate token for order execution.

        INVARIANT: INV-T2-GATE-1
        Called by IBKR connector before order submission.

        Args:
            token_id: Token to validate
            intent_id: Expected intent
            evidence_hash: Expected evidence hash

        Returns:
            ValidationResult
        """
        return self._token_store.validate(token_id, intent_id, evidence_hash)

    def consume_token(self, token_id: str) -> bool:
        """
        Consume token after successful order.

        Args:
            token_id: Token to consume

        Returns:
            True if consumed
        """
        return self._token_store.consume(token_id)

    def get_pending_requests(self) -> list[ApprovalRequest]:
        """Get all pending requests."""
        return [
            r for r in self._pending.values()
            if r.status == ApprovalStatus.PENDING
        ]

    def expire_stale_tokens(self) -> int:
        """Expire stale tokens."""
        return self._token_store.expire_stale()

    def cleanup(self, max_age_sec: int = 3600) -> int:
        """
        Clean up old requests and tokens.

        Args:
            max_age_sec: Remove items older than this

        Returns:
            Number of items removed
        """
        # Clean tokens
        tokens_removed = self._token_store.cleanup(max_age_sec)

        # Clean requests
        cutoff = datetime.now(UTC)
        from datetime import timedelta
        cutoff = cutoff - timedelta(seconds=max_age_sec)

        requests_removed = 0
        for req_id, req in list(self._pending.items()):
            if req.created_at < cutoff:
                del self._pending[req_id]
                requests_removed += 1

        return tokens_removed + requests_removed
