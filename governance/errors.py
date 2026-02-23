"""
Governance Errors — Error Classification and Exceptions

VERSION: 0.2
CONTRACT: GOVERNANCE_INTERFACE_CONTRACT.md
"""


from .types import ErrorAction, ErrorCategory, ErrorClassification

# =============================================================================
# EXCEPTIONS
# =============================================================================


class GovernanceError(Exception):
    """Base exception for governance errors."""

    pass


class HaltError(GovernanceError):
    """
    Raised when halt signal is active.

    Checked at yield points via check_halt().
    """

    def __init__(self, halt_id: str = "unknown", message: str = "Halt signal active"):
        self.halt_id = halt_id
        self.message = message
        super().__init__(f"{message} (halt_id={halt_id})")


# Alias for backward compatibility
HaltException = HaltError


class TierViolationError(GovernanceError):
    """Raised when tier permissions are violated."""

    def __init__(self, module_tier: str, attempted_action: str, forbidden: str):
        self.module_tier = module_tier
        self.attempted_action = attempted_action
        self.forbidden = forbidden
        super().__init__(f"Tier {module_tier} cannot {attempted_action}: {forbidden} is forbidden")


class ApprovalTokenError(GovernanceError):
    """Base exception for approval token errors."""

    pass


class TokenExpiredError(ApprovalTokenError):
    """Raised when approval token has expired."""

    pass


class TokenStateMismatchError(ApprovalTokenError):
    """Raised when token state_hash doesn't match current state."""

    def __init__(self, token_hash: str, current_hash: str):
        self.token_hash = token_hash
        self.current_hash = current_hash
        super().__init__(f"Token state_hash {token_hash} != current {current_hash}")


class TokenScopeError(ApprovalTokenError):
    """Raised when requested action not in token scope."""

    pass


class HaltBlocksActionError(ApprovalTokenError):
    """
    Raised when T2 action attempted during halt.

    INV-GOV-HALT-BEFORE-ACTION enforcement.
    """

    def __init__(self, action: str, halt_id: str):
        self.action = action
        self.halt_id = halt_id
        super().__init__(f"T2 action '{action}' blocked: halt_signal TRUE (halt_id={halt_id})")


class InvariantViolationError(GovernanceError):
    """Raised when an invariant is violated."""

    def __init__(self, invariant_id: str, evidence: dict | None = None):
        self.invariant_id = invariant_id
        self.evidence = evidence or {}
        super().__init__(f"Invariant {invariant_id} violated: {evidence}")


class InitializationError(GovernanceError):
    """Raised when module initialization fails."""

    pass


class DependencyError(GovernanceError):
    """Raised when dependency resolution fails."""

    pass


# =============================================================================
# ERROR CLASSIFIER
# =============================================================================

# Default error classification rules
DEFAULT_ERROR_CLASSIFICATIONS = {
    # Network/transient errors -> retry
    ConnectionError: ErrorClassification(ErrorCategory.RECOVERABLE, ErrorAction.RETRY),
    TimeoutError: ErrorClassification(ErrorCategory.RECOVERABLE, ErrorAction.RETRY),
    # Resource errors -> degrade
    MemoryError: ErrorClassification(ErrorCategory.DEGRADED, ErrorAction.DEGRADE),
    # Governance errors
    HaltError: ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
    TierViolationError: ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
    HaltBlocksActionError: ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
    InvariantViolationError: ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
    # Token errors -> halt (security)
    ApprovalTokenError: ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT),
}


def classify_error(
    error: Exception, custom_rules: dict[type, ErrorClassification] | None = None
) -> ErrorClassification:
    """
    Classify an error into category and action.

    Args:
        error: The exception to classify
        custom_rules: Optional custom classification rules

    Returns:
        ErrorClassification with category and action
    """
    rules = {**DEFAULT_ERROR_CLASSIFICATIONS}
    if custom_rules:
        rules.update(custom_rules)

    # Check exact type match
    error_type = type(error)
    if error_type in rules:
        return rules[error_type]

    # Check inheritance
    for rule_type, classification in rules.items():
        if isinstance(error, rule_type):
            return classification

    # Default: unknown errors are CRITICAL
    return ErrorClassification(ErrorCategory.CRITICAL, ErrorAction.HALT)
