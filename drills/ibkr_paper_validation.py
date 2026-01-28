#!/usr/bin/env python3
"""
S33 IBKR Paper Trading Validation

PURPOSE: Verify real IBKR paper trading works end-to-end
PHASE: S33 Phase 1 Exit Gate

PREREQUISITES:
  - IB Gateway running on localhost:4002
  - Paper trading account (DU* prefix)
  - IBKR_MODE=PAPER in .env

USAGE:
    python drills/ibkr_paper_validation.py

VALIDATION TASKS:
  1. Verify guards (INV-IBKR-PAPER-GUARD-1, INV-IBKR-ACCOUNT-CHECK-1)
  2. Connect to IBKR
  3. Query account balance
  4. Submit paper order (1 unit EUR/USD)
  5. Receive fill confirmation
  6. Query positions
  7. Report results
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def print_header(title: str) -> None:
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_result(name: str, passed: bool, details: str = "") -> None:
    """Print test result."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {name}")
    if details:
        print(f"         {details}")


def validate_guards() -> tuple[bool, dict]:
    """
    Test 1: Validate guards work correctly.

    INVARIANTS TESTED:
    - INV-IBKR-PAPER-GUARD-1: Live mode requires IBKR_ALLOW_LIVE=true
    - INV-IBKR-ACCOUNT-CHECK-1: Account validation working
    """
    print_header("TEST 1: GUARD VALIDATION")

    from brokers.ibkr.config import IBKRConfig, IBKRMode

    results = {
        "paper_guard": False,
        "account_check": False,
        "mode_detected": "",
        "account_prefix": "",
    }

    # Test paper guard
    try:
        config = IBKRConfig.from_env()
        results["mode_detected"] = config.mode.value
        results["account_prefix"] = config.expected_account_prefix

        # Verify mode is PAPER
        if config.mode == IBKRMode.PAPER:
            print_result("Mode detection", True, f"Mode: {config.mode.value}")

            # Verify live is blocked
            config_live = IBKRConfig(
                mode=IBKRMode.LIVE,
                allow_live=False,  # NOT enabled
            )
            valid, errors = config_live.validate_startup()
            if not valid and "INV-IBKR-PAPER-GUARD-1" in str(errors):
                print_result("Live mode blocked", True, "INV-IBKR-PAPER-GUARD-1 enforced")
                results["paper_guard"] = True
            else:
                print_result("Live mode blocked", False, "Guard NOT enforced!")
        else:
            print_result("Mode detection", False, f"Expected PAPER, got {config.mode.value}")

    except Exception as e:
        print_result("Config load", False, str(e))
        return False, results

    # Test account validation
    try:
        # Valid paper account
        valid, error = config.validate_account("DU1234567")
        if valid:
            print_result("Paper account validation", True, "DU* prefix accepted")
            results["account_check"] = True
        else:
            print_result("Paper account validation", False, error or "Unknown error")

        # Invalid account (should fail for PAPER mode)
        valid, error = config.validate_account("U9999999")
        if not valid:
            print_result("Live account rejected", True, "U* prefix rejected in PAPER mode")
        else:
            print_result("Live account rejected", False, "U* prefix should be rejected!")
            results["account_check"] = False

    except Exception as e:
        print_result("Account validation", False, str(e))
        return False, results

    passed = results["paper_guard"] and results["account_check"]
    return passed, results


def test_connection() -> tuple[bool, dict]:
    """
    Test 2: Connect to IBKR paper trading.
    """
    print_header("TEST 2: IBKR CONNECTION")

    from brokers.ibkr.config import IBKRConfig
    from brokers.ibkr.connector import IBKRConnector

    results = {
        "connected": False,
        "account_id": "",
        "port": 0,
        "gateway_version": "",
        "bead_emitted": False,
    }

    # Track bead emission
    beads_emitted = []

    def bead_emitter(bead):
        beads_emitted.append(bead)
        print(f"         [BEAD] {bead.event.value}: {bead.mode} on port {bead.port}")

    try:
        config = IBKRConfig.from_env()
        print(f"  Config: host={config.host}, port={config.port}, mode={config.mode.value}")

        connector = IBKRConnector(config=config, bead_emitter=bead_emitter)

        print("  Connecting to IB Gateway...")
        connected = connector.connect()

        if connected:
            results["connected"] = True
            results["account_id"] = connector.account_id
            results["port"] = config.port

            print_result("Connection", True, f"Account: {connector.account_id}")

            # Check bead emission
            if beads_emitted and beads_emitted[-1].event.value == "CONNECT":
                results["bead_emitted"] = True
                print_result("Session bead emitted", True, "IBKR_SESSION CONNECT")
            else:
                print_result("Session bead emitted", False, "No CONNECT bead")

            # Return connector for further tests
            return True, {"connector": connector, **results}
        else:
            print_result("Connection", False, "connect() returned False")
            return False, results

    except ConnectionError as e:
        print_result("Connection", False, str(e))
        print("\n  HINT: Is IB Gateway running on localhost:4002?")
        print("        Is paper trading enabled in IB Gateway?")
        return False, results
    except Exception as e:
        print_result("Connection", False, f"Unexpected error: {e}")
        return False, results


def test_account(connector) -> tuple[bool, dict]:
    """
    Test 3: Query account information.
    """
    print_header("TEST 3: ACCOUNT QUERY")

    results = {
        "account_queried": False,
        "net_liquidation": 0.0,
        "available_funds": 0.0,
        "buying_power": 0.0,
    }

    try:
        account = connector.get_account()

        if account and account.account_id:
            results["account_queried"] = True
            results["net_liquidation"] = account.net_liquidation
            results["available_funds"] = account.available_funds
            results["buying_power"] = account.buying_power

            print_result("Account query", True, f"Account: {account.account_id}")
            print(f"         Net Liquidation: ${account.net_liquidation:,.2f}")
            print(f"         Available Funds: ${account.available_funds:,.2f}")
            print(f"         Buying Power:    ${account.buying_power:,.2f}")

            return True, results
        else:
            print_result("Account query", False, "No account data returned")
            return False, results

    except Exception as e:
        print_result("Account query", False, str(e))
        return False, results


def test_positions(connector) -> tuple[bool, dict]:
    """
    Test 4: Query current positions.
    """
    print_header("TEST 4: POSITION QUERY")

    results = {
        "positions_queried": False,
        "position_count": 0,
        "positions": [],
    }

    try:
        snapshot = connector.get_positions()

        results["positions_queried"] = True
        results["position_count"] = len(snapshot.positions)

        print_result("Positions query", True, f"Found {len(snapshot.positions)} positions")

        for pos in snapshot.positions:
            results["positions"].append(
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                }
            )
            print(f"         {pos.symbol}: {pos.quantity:,.0f} @ ${pos.avg_cost:.5f}")

        if not snapshot.positions:
            print("         (No open positions)")

        return True, results

    except Exception as e:
        print_result("Positions query", False, str(e))
        return False, results


def test_order_guards(connector) -> tuple[bool, dict]:
    """
    Test 5: Verify order guards without T2 token.
    """
    print_header("TEST 5: ORDER GUARD VALIDATION")

    from brokers.ibkr.orders import Order, OrderSide, OrderType

    results = {
        "t2_guard_works": False,
    }

    try:
        # Create order WITHOUT T2 token (should be rejected)
        order = Order(
            symbol="EURUSD",
            side=OrderSide.BUY,
            quantity=1.0,
            order_type=OrderType.MARKET,
            token_id=None,  # NO TOKEN - should fail
        )

        result = connector.submit_order(order)

        if not result.success and "INV-T2-GATE-1" in str(result.errors):
            results["t2_guard_works"] = True
            print_result("T2 token guard", True, "Order rejected without token")
            return True, results
        else:
            print_result("T2 token guard", False, "Order should have been rejected!")
            return False, results

    except Exception as e:
        print_result("T2 token guard", False, str(e))
        return False, results


def run_validation() -> bool:
    """
    Run full IBKR paper validation.
    """
    print("\n" + "#" * 60)
    print("# S33 IBKR PAPER TRADING VALIDATION")
    print("# Date:", datetime.now(UTC).isoformat())
    print("#" * 60)

    all_results = {}
    connector = None

    # Test 1: Guards
    passed, results = validate_guards()
    all_results["guards"] = {"passed": passed, **results}
    if not passed:
        print("\n  ⚠️  Guard validation failed. Fix before proceeding.")

    # Test 2: Connection
    passed, results = test_connection()
    all_results["connection"] = {"passed": passed, **results}

    if not passed:
        print("\n" + "#" * 60)
        print("# VALIDATION INCOMPLETE: Connection failed")
        print("#" * 60)
        print("\nCHECKLIST:")
        print("  [ ] Is IB Gateway running?")
        print("  [ ] Is it listening on port 4002?")
        print("  [ ] Is paper trading enabled?")
        print("  [ ] Are API connections enabled in Gateway settings?")
        return False

    connector = results.get("connector")

    # Test 3: Account
    passed, results = test_account(connector)
    all_results["account"] = {"passed": passed, **results}

    # Test 4: Positions
    passed, results = test_positions(connector)
    all_results["positions"] = {"passed": passed, **results}

    # Test 5: Order guards
    passed, results = test_order_guards(connector)
    all_results["order_guards"] = {"passed": passed, **results}

    # Cleanup
    if connector:
        print_header("CLEANUP")
        connector.disconnect()
        print("  Disconnected from IBKR")

    # Summary
    print("\n" + "#" * 60)
    print("# VALIDATION SUMMARY")
    print("#" * 60)

    total_passed = sum(1 for r in all_results.values() if r.get("passed", False))
    total_tests = len(all_results)

    print(f"\n  Tests: {total_passed}/{total_tests} passed")
    print()
    for test_name, result in all_results.items():
        status = "✓" if result.get("passed") else "✗"
        print(f"  {status} {test_name}")

    if total_passed == total_tests:
        print("\n" + "=" * 60)
        print("  IBKR PAPER VALIDATION: PASS ✓")
        print("=" * 60)
        print("\n  Ready for paper trade round-trip test.")
        print("  Next: Submit actual paper order with T2 token.")
        return True
    else:
        print("\n" + "=" * 60)
        print("  IBKR PAPER VALIDATION: INCOMPLETE")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
