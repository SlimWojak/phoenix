#!/usr/bin/env python3
"""
TEST: TIER GATES
SPRINT: 26.TRACK_B
EXIT_GATE: T1 cannot write execution_state

PURPOSE:
  Prove INV-GOV-NO-T1-WRITE-EXEC enforcement.
  Tier permissions are correctly enforced.
"""

import sys
from pathlib import Path

PHOENIX_ROOT = Path.home() / "phoenix"
sys.path.insert(0, str(PHOENIX_ROOT))

from governance import (
    TIER_PERMISSIONS,
    ModuleTier,
    TierViolationError,
)

# =============================================================================
# HELPER
# =============================================================================


def check_tier_permission(tier: ModuleTier, action: str, target: str) -> bool:
    """Check if action is permitted for tier."""
    permissions = TIER_PERMISSIONS.get(tier, {})
    forbidden = permissions.get("forbidden", [])

    if target in forbidden:
        raise TierViolationError(module_tier=tier.name, attempted_action=action, forbidden=target)

    return True


# =============================================================================
# TESTS
# =============================================================================


def test_t0_permissions():
    """T0 is read-only."""
    tier = ModuleTier.T0
    permissions = TIER_PERMISSIONS[tier]

    print("\nT0 Permissions:")
    print(f"  writes: {permissions['writes']}")
    print(f"  reads: {permissions['reads']}")
    print(f"  forbidden: {permissions['forbidden']}")

    # T0 cannot write anything
    assert permissions["writes"] == []

    # T0 can read market data
    assert "market_data" in permissions["reads"]

    # T0 cannot write advisory or execution
    for forbidden in ["advisory_state", "execution_state", "orders", "positions"]:
        try:
            check_tier_permission(tier, "write", forbidden)
            assert False, f"T0 should not be able to write {forbidden}"
        except TierViolationError:
            print(f"  T0 → {forbidden}: BLOCKED ✓")


def test_t1_permissions():
    """T1 can write advisory but not execution."""
    tier = ModuleTier.T1
    permissions = TIER_PERMISSIONS[tier]

    print("\nT1 Permissions:")
    print(f"  writes: {permissions['writes']}")
    print(f"  forbidden: {permissions['forbidden']}")

    # T1 can write advisory_state
    assert "advisory_state" in permissions["writes"]

    # T1 cannot write execution
    for forbidden in ["execution_state", "orders", "positions"]:
        try:
            check_tier_permission(tier, "write", forbidden)
            assert False, f"T1 should not be able to write {forbidden}"
        except TierViolationError as e:
            print(f"  T1 → {forbidden}: BLOCKED ✓")
            assert e.module_tier == "T1"


def test_t2_permissions():
    """T2 can write execution with approval."""
    tier = ModuleTier.T2
    permissions = TIER_PERMISSIONS[tier]

    print("\nT2 Permissions:")
    print(f"  writes: {permissions['writes']}")
    print(f"  requires_approval_token: {permissions.get('requires_approval_token')}")

    # T2 can write execution
    assert "execution_state" in permissions["writes"]
    assert "orders" in permissions["writes"]
    assert "positions" in permissions["writes"]

    # T2 requires approval token
    assert permissions.get("requires_approval_token") is True

    # T2 pre-check: halt_signal == FALSE
    assert permissions.get("pre_check") == "halt_signal == FALSE"

    print("  T2 → execution_state: ALLOWED (with token)")
    print("  T2 → orders: ALLOWED (with token)")
    print("  T2 → positions: ALLOWED (with token)")


def test_tier_violation_error_structure():
    """TierViolationError contains required fields."""
    try:
        check_tier_permission(ModuleTier.T1, "write", "orders")
    except TierViolationError as e:
        assert e.module_tier == "T1"
        assert e.attempted_action == "write"
        assert e.forbidden == "orders"
        print(f"\nTierViolationError: {e}")


def test_inv_gov_no_t1_write_exec():
    """INV-GOV-NO-T1-WRITE-EXEC: T1 may not write execution."""
    print("\nINV-GOV-NO-T1-WRITE-EXEC:")

    exec_targets = ["execution_state", "orders", "positions"]

    for target in exec_targets:
        try:
            check_tier_permission(ModuleTier.T1, "write", target)
            assert False, f"INV violated: T1 wrote {target}"
        except TierViolationError:
            print(f"  T1 → {target}: ENFORCED ✓")


def test_tier_gate_automated_vs_human():
    """T1 has automated gate, T2 has human gate."""
    t1_perms = TIER_PERMISSIONS[ModuleTier.T1]
    t2_perms = TIER_PERMISSIONS[ModuleTier.T2]

    print("\nGate Types:")
    print(f"  T1: {t1_perms.get('gate')}")
    print(f"  T2: {t2_perms.get('gate')}")

    assert t1_perms.get("gate") == "automated"
    assert t2_perms.get("gate") == "human"


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TIER GATES TEST")
    print("=" * 60)
    print("INV-GOV-NO-T1-WRITE-EXEC: T1 may not write execution_state")

    try:
        test_t0_permissions()
        test_t1_permissions()
        test_t2_permissions()
        test_tier_violation_error_structure()
        test_inv_gov_no_t1_write_exec()
        test_tier_gate_automated_vs_human()

        print("\n" + "=" * 60)
        print("VERDICT: PASS")
        print("  - T0: read-only enforced")
        print("  - T1: advisory allowed, execution blocked")
        print("  - T2: execution allowed with approval")
        print("  - INV-GOV-NO-T1-WRITE-EXEC: enforced")
        print("=" * 60)

        sys.exit(0)

    except AssertionError as e:
        print("\n" + "=" * 60)
        print("VERDICT: FAIL")
        print(f"  {e}")
        print("=" * 60)
        sys.exit(1)
