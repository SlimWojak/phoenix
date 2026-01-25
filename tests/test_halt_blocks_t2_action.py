#!/usr/bin/env python3
"""
TEST: HALT BLOCKS T2 ACTION
SPRINT: 26.TRACK_B
EXIT_GATE: T2 action rejected when halt_signal TRUE

PURPOSE:
  Prove INV-GOV-HALT-BEFORE-ACTION enforcement.
  T2 actions must be blocked when halt is active.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    HaltSignal,
    ApprovalToken,
    TokenValidator,
    TokenIssuer,
    HaltBlocksActionError,
)


# =============================================================================
# TESTS
# =============================================================================

def test_halt_blocks_t2_action():
    """T2 action blocked when halt_signal TRUE."""
    halt_signal = HaltSignal()
    state_hash = "abc123"
    
    validator = TokenValidator(
        halt_signal=halt_signal,
        state_hash_fn=lambda: state_hash
    )
    
    # Create valid token
    issuer = TokenIssuer("sovereign")
    token = issuer.issue(
        state_hash=state_hash,
        scope=["place_order"],
        duration_seconds=3600
    )
    
    # Action should work when halt not set
    result = validator.validate(token, "place_order")
    assert result is True
    print("\nT2 action when halt=FALSE: ALLOWED")
    
    # Set halt signal
    halt_signal.set()
    
    # Action should now be blocked
    try:
        validator.validate(token, "place_order")
        assert False, "Should have raised HaltBlocksActionError"
    except HaltBlocksActionError as e:
        print(f"T2 action when halt=TRUE: BLOCKED")
        print(f"  action: {e.action}")
        print(f"  halt_id: {e.halt_id}")


def test_halt_signal_check_before_state_hash():
    """Halt check happens BEFORE state hash check."""
    halt_signal = HaltSignal()
    
    # Validator with wrong state hash
    validator = TokenValidator(
        halt_signal=halt_signal,
        state_hash_fn=lambda: "current_hash"
    )
    
    # Token with different hash (would fail state check)
    token = ApprovalToken(
        issued_by="sovereign",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope=["*"],
        state_hash="wrong_hash"
    )
    
    # Set halt BEFORE validation
    halt_signal.set()
    
    # Should fail on HALT check, not state hash check
    try:
        validator.validate(token, "any_action")
        assert False, "Should have raised"
    except HaltBlocksActionError:
        print("\nHalt check priority: VERIFIED")
        print("  HaltBlocksActionError raised before TokenStateMismatchError")


def test_multiple_t2_actions_blocked():
    """All T2 actions blocked during halt."""
    halt_signal = HaltSignal()
    state_hash = "hash123"
    
    validator = TokenValidator(
        halt_signal=halt_signal,
        state_hash_fn=lambda: state_hash
    )
    
    # Token with wildcard scope
    token = ApprovalToken(
        issued_by="sovereign",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope=["*"],
        state_hash=state_hash
    )
    
    # Set halt
    halt_signal.set()
    
    # All actions should be blocked
    actions = ["place_order", "cancel_order", "modify_position", "withdraw"]
    
    print("\nBlocking multiple T2 actions:")
    for action in actions:
        try:
            validator.validate(token, action)
            assert False, f"{action} should be blocked"
        except HaltBlocksActionError:
            print(f"  {action}: BLOCKED ✓")


def test_halt_clear_allows_action():
    """Clearing halt allows T2 action again."""
    halt_signal = HaltSignal()
    state_hash = "hash123"
    
    validator = TokenValidator(
        halt_signal=halt_signal,
        state_hash_fn=lambda: state_hash
    )
    
    token = ApprovalToken(
        issued_by="sovereign",
        issued_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        scope=["place_order"],
        state_hash=state_hash
    )
    
    # Set then clear halt
    halt_signal.set()
    assert halt_signal.is_set()
    
    halt_signal.clear()
    assert not halt_signal.is_set()
    
    # Action should work now
    result = validator.validate(token, "place_order")
    assert result is True
    
    print("\nHalt clear → action allowed: VERIFIED")


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HALT BLOCKS T2 ACTION TEST")
    print("=" * 60)
    print("INV-GOV-HALT-BEFORE-ACTION: gate checks halt_signal")
    
    try:
        test_halt_blocks_t2_action()
        test_halt_signal_check_before_state_hash()
        test_multiple_t2_actions_blocked()
        test_halt_clear_allows_action()
        
        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - T2 actions blocked when halt=TRUE")
        print("  - Halt check has priority over other checks")
        print("  - All action types blocked")
        print("  - Clearing halt allows actions")
        print("=" * 60)
        
        sys.exit(0)
        
    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
