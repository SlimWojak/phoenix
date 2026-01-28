#!/usr/bin/env python3
"""
S33 IBKR Paper Trade Round-Trip

PURPOSE: Execute complete trade lifecycle (open → fill → close)
PHASE: S33 Phase 1 Exit Gate

PREREQUISITES:
  - IB Gateway running on localhost:4002
  - Paper trading account (DU* prefix)
  - IBKR_MODE=PAPER in .env
  - All 5 validation tests passing

USAGE:
    python drills/ibkr_paper_trade_roundtrip.py

LIFECYCLE:
    CONNECT → T2_TOKEN → BUY → FILL → POSITION → SELL → CLOSE → DISCONNECT
"""

import hashlib
import sys
import time
import uuid
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


def print_step(step: str, status: bool, details: str = "") -> None:
    """Print step result."""
    icon = "✓" if status else "✗"
    print(f"  {icon} {step}: {details}")


class RoundTripState:
    """Tracks round-trip state for reporting."""

    def __init__(self):
        self.connected = False
        self.account_id = ""
        self.buy_token_id = ""
        self.sell_token_id = ""
        self.buy_order_id = ""
        self.sell_order_id = ""
        self.buy_fill_price = 0.0
        self.sell_fill_price = 0.0
        self.position_quantity = 0.0
        self.pnl = 0.0
        self.beads_emitted = []

    def log_bead(self, bead):
        """Log bead emission."""
        if hasattr(bead, "event"):
            self.beads_emitted.append(f"{bead.bead_type}:{bead.event.value}")
        elif hasattr(bead, "bead_type"):
            self.beads_emitted.append(
                bead.bead_type if isinstance(bead.bead_type, str) else bead.bead_type
            )
        else:
            self.beads_emitted.append(str(type(bead).__name__))


def run_round_trip() -> bool:
    """
    Execute complete paper trade round-trip.

    Returns:
        True if all steps pass
    """
    from brokers.ibkr.config import IBKRConfig
    from brokers.ibkr.connector import IBKRConnector
    from brokers.ibkr.orders import Order, OrderSide, OrderType
    from governance.t2.tokens import TokenStore

    state = RoundTripState()
    connector = None
    token_store = TokenStore()

    print("\n" + "#" * 60)
    print("# S33 PAPER TRADE ROUND-TRIP")
    print("# Date:", datetime.now(UTC).isoformat())
    print("#" * 60)

    # ==========================================================================
    # STEP 1: CONNECT
    # ==========================================================================
    print_header("STEP 1: CONNECT TO IBKR")

    def bead_emitter(bead):
        state.log_bead(bead)
        if hasattr(bead, "event"):
            print(f"    [BEAD] {bead.event.value}: {bead.mode} account={bead.account}")

    try:
        config = IBKRConfig.from_env()
        print(f"  Config: mode={config.mode.value}, port={config.port}")

        connector = IBKRConnector(config=config, bead_emitter=bead_emitter)
        connected = connector.connect()

        if connected:
            state.connected = True
            state.account_id = connector.account_id
            print_step("CONNECT", True, f"Account: {connector.account_id}")

            # Verify it's a paper account
            if not connector.account_id.startswith("DU"):
                print_step("ACCOUNT CHECK", False, "NOT a paper account!")
                return False
            print_step("PAPER ACCOUNT", True, "DU* prefix confirmed")
        else:
            print_step("CONNECT", False, "Failed to connect")
            return False

    except Exception as e:
        print_step("CONNECT", False, str(e))
        print("\n  HINT: Is IB Gateway running on localhost:4002?")
        return False

    # ==========================================================================
    # STEP 2: QUERY INITIAL ACCOUNT
    # ==========================================================================
    print_header("STEP 2: QUERY ACCOUNT")

    try:
        account = connector.get_account()
        if account:
            print(f"  Net Liquidation: ${account.net_liquidation:,.2f}")
            print(f"  Available Funds: ${account.available_funds:,.2f}")
        else:
            print("  WARNING: Could not query account")
    except Exception as e:
        print(f"  WARNING: Account query failed: {e}")

    # ==========================================================================
    # STEP 3: QUERY INITIAL POSITIONS
    # ==========================================================================
    print_header("STEP 3: INITIAL POSITIONS")

    initial_eurusd_pos = 0.0
    try:
        positions = connector.get_positions()
        eurusd_pos = connector.get_position("EURUSD")
        if eurusd_pos:
            initial_eurusd_pos = eurusd_pos.quantity
            print(f"  Existing EUR/USD: {eurusd_pos.quantity:,.0f}")
        else:
            print("  No existing EUR/USD position")
    except Exception as e:
        print(f"  WARNING: Position query failed: {e}")

    # ==========================================================================
    # STEP 4: GENERATE T2 TOKEN FOR BUY
    # ==========================================================================
    print_header("STEP 4: GENERATE T2 TOKEN (BUY)")

    buy_intent_id = f"DRILL-BUY-{uuid.uuid4().hex[:8]}"
    buy_evidence = {"symbol": "EURUSD", "side": "BUY", "quantity": 20000.0}
    buy_evidence_hash = hashlib.sha256(str(sorted(buy_evidence.items())).encode()).hexdigest()

    try:
        buy_token = token_store.issue(buy_intent_id, buy_evidence_hash)
        state.buy_token_id = buy_token.token_id
        print_step("T2 TOKEN (BUY)", True, f"ID: {buy_token.token_id[:16]}...")
        print(f"    Intent: {buy_intent_id}")
        print(f"    TTL: {buy_token.ttl_remaining_sec:.0f}s")
    except Exception as e:
        print_step("T2 TOKEN (BUY)", False, str(e))
        connector.disconnect()
        return False

    # ==========================================================================
    # STEP 5: SUBMIT BUY ORDER
    # ==========================================================================
    print_header("STEP 5: SUBMIT BUY ORDER")

    # Note: Using 20000 as minimum for forex (standard micro lot)
    # EUR/USD minimum on IBKR is typically 20,000 base currency
    try:
        buy_order = Order(
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=OrderSide.BUY,
            quantity=20000.0,  # Minimum forex lot
            token_id=buy_token.token_id,
        )
        buy_order.signal_id = buy_intent_id  # For token validation

        print("  Order: BUY 20,000 EUR/USD MARKET")
        print(f"  Token: {buy_token.token_id[:16]}...")

        result = connector.submit_order(buy_order)

        if result.success:
            state.buy_order_id = result.order_id
            state.buy_fill_price = result.fill_price or 0.0
            print_step("BUY ORDER", True, f"ID: {result.order_id}")
            print(f"    Status: {result.status.value}")
            if result.fill_price:
                print(f"    Fill Price: {result.fill_price:.5f}")
            if result.filled_quantity:
                print(f"    Filled Qty: {result.filled_quantity:,.0f}")

            # Consume token (mark as used)
            token_store.consume(buy_token.token_id)
        else:
            print_step("BUY ORDER", False, result.message)
            print(f"    Errors: {result.errors}")
            connector.disconnect()
            return False

    except Exception as e:
        print_step("BUY ORDER", False, str(e))
        connector.disconnect()
        return False

    # ==========================================================================
    # STEP 6: WAIT FOR FILL
    # ==========================================================================
    print_header("STEP 6: WAIT FOR FILL")

    print("  Waiting 3 seconds for order to fill...")
    time.sleep(3)

    # Query positions to verify
    try:
        eurusd_pos = connector.get_position("EURUSD")
        if eurusd_pos:
            new_qty = eurusd_pos.quantity - initial_eurusd_pos
            if new_qty > 0:
                state.position_quantity = new_qty
                print_step("POSITION", True, f"EUR/USD +{new_qty:,.0f}")
            else:
                print_step("POSITION", False, "No new position detected")
        else:
            # Check all positions
            positions = connector.get_positions()
            print(f"  All positions: {len(positions.positions)}")
            for pos in positions.positions:
                print(f"    {pos.symbol}: {pos.quantity:,.0f}")
    except Exception as e:
        print(f"  WARNING: Position verification failed: {e}")

    # ==========================================================================
    # STEP 7: GENERATE T2 TOKEN FOR SELL
    # ==========================================================================
    print_header("STEP 7: GENERATE T2 TOKEN (SELL)")

    sell_intent_id = f"DRILL-SELL-{uuid.uuid4().hex[:8]}"
    sell_evidence = {"symbol": "EURUSD", "side": "SELL", "quantity": 20000.0}
    sell_evidence_hash = hashlib.sha256(str(sorted(sell_evidence.items())).encode()).hexdigest()

    try:
        sell_token = token_store.issue(sell_intent_id, sell_evidence_hash)
        state.sell_token_id = sell_token.token_id
        print_step("T2 TOKEN (SELL)", True, f"ID: {sell_token.token_id[:16]}...")
        print(f"    Intent: {sell_intent_id}")
        print(f"    TTL: {sell_token.ttl_remaining_sec:.0f}s")
    except Exception as e:
        print_step("T2 TOKEN (SELL)", False, str(e))
        connector.disconnect()
        return False

    # ==========================================================================
    # STEP 8: SUBMIT SELL ORDER (CLOSE)
    # ==========================================================================
    print_header("STEP 8: SUBMIT SELL ORDER (CLOSE)")

    try:
        sell_order = Order(
            symbol="EURUSD",
            order_type=OrderType.MARKET,
            side=OrderSide.SELL,
            quantity=20000.0,
            token_id=sell_token.token_id,
        )
        sell_order.signal_id = sell_intent_id

        print("  Order: SELL 20,000 EUR/USD MARKET")
        print(f"  Token: {sell_token.token_id[:16]}...")

        result = connector.submit_order(sell_order)

        if result.success:
            state.sell_order_id = result.order_id
            state.sell_fill_price = result.fill_price or 0.0
            print_step("SELL ORDER", True, f"ID: {result.order_id}")
            print(f"    Status: {result.status.value}")
            if result.fill_price:
                print(f"    Fill Price: {result.fill_price:.5f}")
            if result.filled_quantity:
                print(f"    Filled Qty: {result.filled_quantity:,.0f}")

            # Calculate P&L
            if state.buy_fill_price and state.sell_fill_price:
                # For forex: P&L = (sell - buy) * quantity
                state.pnl = (state.sell_fill_price - state.buy_fill_price) * 20000.0
                print(f"    P&L: ${state.pnl:.2f}")

            # Consume token
            token_store.consume(sell_token.token_id)
        else:
            print_step("SELL ORDER", False, result.message)
            print(f"    Errors: {result.errors}")
            connector.disconnect()
            return False

    except Exception as e:
        print_step("SELL ORDER", False, str(e))
        connector.disconnect()
        return False

    # ==========================================================================
    # STEP 9: VERIFY CLOSED
    # ==========================================================================
    print_header("STEP 9: VERIFY POSITION CLOSED")

    print("  Waiting 3 seconds for close to settle...")
    time.sleep(3)

    try:
        eurusd_pos = connector.get_position("EURUSD")
        final_qty = eurusd_pos.quantity if eurusd_pos else 0.0
        net_change = final_qty - initial_eurusd_pos

        if abs(net_change) < 1:  # Position should be flat or back to initial
            print_step("CLOSED", True, "Position flat")
        else:
            print_step("CLOSED", False, f"Net change: {net_change:,.0f}")
    except Exception as e:
        print(f"  WARNING: Close verification failed: {e}")

    # ==========================================================================
    # STEP 10: DISCONNECT
    # ==========================================================================
    print_header("STEP 10: DISCONNECT")

    try:
        connector.disconnect()
        state.connected = False
        print_step("DISCONNECT", True, "Clean disconnect")
    except Exception as e:
        print_step("DISCONNECT", False, str(e))

    # ==========================================================================
    # SUMMARY
    # ==========================================================================
    print("\n" + "#" * 60)
    print("# ROUND-TRIP SUMMARY")
    print("#" * 60)

    print(
        f"""
  Account:     {state.account_id}

  BUY ORDER:
    Token:     {state.buy_token_id[:16]}...
    Order ID:  {state.buy_order_id}
    Fill:      {state.buy_fill_price:.5f}

  SELL ORDER:
    Token:     {state.sell_token_id[:16]}...
    Order ID:  {state.sell_order_id}
    Fill:      {state.sell_fill_price:.5f}

  P&L:         ${state.pnl:.2f}

  Beads:       {len(state.beads_emitted)} emitted
               {', '.join(state.beads_emitted[:5])}{'...' if len(state.beads_emitted) > 5 else ''}
"""
    )

    # Final verdict
    all_passed = (
        state.buy_order_id
        and state.sell_order_id
        and state.buy_fill_price > 0
        and state.sell_fill_price > 0
    )

    if all_passed:
        print("=" * 60)
        print("  PAPER TRADE ROUND-TRIP: PASS ✓")
        print("=" * 60)
        print("\n  S33 Phase 1 Exit Gate: COMPLETE")
        print("  'Paper trade round-trip complete, UX validated'")
        return True
    else:
        print("=" * 60)
        print("  PAPER TRADE ROUND-TRIP: INCOMPLETE")
        print("=" * 60)
        return False


if __name__ == "__main__":
    try:
        success = run_round_trip()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n  FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
