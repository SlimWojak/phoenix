#!/usr/bin/env python3
"""
Mock CSE Generator — Scripted signal generation for UX testing
===============================================================

S33: FIRST_BLOOD

Generates mock CSE (Claude Signal Emission) signals for testing
the Phoenix approval workflow without requiring live CSO analysis.

Usage:
    python mock_cse_generator.py --signal READY --pair EURUSD
    python mock_cse_generator.py --signal FORMING --pair GBPUSD --confidence 0.75
    python mock_cse_generator.py --help

This writes a valid intent YAML to the Phoenix intent directory
for processing by the approval workflow.
"""

from __future__ import annotations

import argparse
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


# =============================================================================
# ENUMS
# =============================================================================


class SignalType(str, Enum):
    """CSE signal types."""

    READY = "READY"       # Full conviction, ready to execute
    FORMING = "FORMING"   # Setup developing, not yet ready
    NONE = "NONE"         # No valid setup detected


class SetupType(str, Enum):
    """Valid setup types from CSO methodology."""

    FVG_ENTRY = "FVG_ENTRY"         # Fair Value Gap entry
    OTE_ENTRY = "OTE_ENTRY"         # Optimal Trade Entry
    BOS_ENTRY = "BOS_ENTRY"         # Break of Structure entry
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"
    ORDER_BLOCK = "ORDER_BLOCK"


class Pair(str, Enum):
    """Supported trading pairs."""

    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    NZDUSD = "NZDUSD"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class CSESignal:
    """
    Claude Signal Emission structure.

    Represents a mock signal from the CSO analysis system.
    """

    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    signal_type: SignalType = SignalType.READY
    pair: Pair = Pair.EURUSD
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Confidence and setup
    confidence: float = 0.85
    setup_type: SetupType = SetupType.FVG_ENTRY

    # Price levels
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0

    # Risk parameters
    risk_percent: float = 1.0
    position_size: float = 0.0  # Calculated or specified

    # Context
    htf_bias: str = "BULLISH"  # Higher timeframe bias
    session: str = "LONDON"    # Trading session
    notes: str = ""

    def validate(self) -> list[str]:
        """Validate signal parameters."""
        errors: list[str] = []

        # Confidence range
        if not 0.0 <= self.confidence <= 1.0:
            errors.append(f"Confidence must be 0-1, got {self.confidence}")

        # Price levels for READY signal
        if self.signal_type == SignalType.READY:
            if self.entry_price <= 0:
                errors.append("READY signal requires entry_price > 0")
            if self.stop_loss <= 0:
                errors.append("READY signal requires stop_loss > 0")

            # Stop loss direction check
            if self.htf_bias == "BULLISH" and self.stop_loss >= self.entry_price:
                errors.append("BULLISH: stop_loss must be below entry_price")
            if self.htf_bias == "BEARISH" and self.stop_loss <= self.entry_price:
                errors.append("BEARISH: stop_loss must be above entry_price")

        # Risk percent
        if not 0.1 <= self.risk_percent <= 5.0:
            errors.append(f"Risk percent should be 0.1-5.0, got {self.risk_percent}")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML output."""
        return {
            "signal_id": self.signal_id,
            "signal_type": self.signal_type.value,
            "pair": self.pair.value,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "setup_type": self.setup_type.value,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_percent": self.risk_percent,
            "position_size": self.position_size,
            "htf_bias": self.htf_bias,
            "session": self.session,
            "notes": self.notes,
        }


@dataclass
class IntentPayload:
    """
    Intent payload for Phoenix approval workflow.

    Wraps CSE signal in intent format.
    """

    intent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    intent_type: str = "DISPATCH"
    action: str = "APPROVE"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    signal: CSESignal = field(default_factory=CSESignal)
    source: str = "mock_cse_generator"
    mock: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for YAML output."""
        return {
            "intent_id": self.intent_id,
            "intent_type": self.intent_type,
            "action": self.action,
            "created_at": self.created_at.isoformat(),
            "signal": self.signal.to_dict(),
            "source": self.source,
            "mock": self.mock,
        }


# =============================================================================
# GENERATOR
# =============================================================================


class MockCSEGenerator:
    """
    Generates mock CSE signals for testing.

    Usage:
        generator = MockCSEGenerator()
        signal = generator.create_signal(
            signal_type=SignalType.READY,
            pair=Pair.EURUSD,
            confidence=0.85,
        )
        generator.write_intent(signal)
    """

    # Default prices for pairs
    DEFAULT_PRICES = {
        Pair.EURUSD: 1.0850,
        Pair.GBPUSD: 1.2500,
        Pair.USDJPY: 150.00,
        Pair.AUDUSD: 0.6500,
        Pair.USDCAD: 1.3500,
        Pair.NZDUSD: 0.5800,
    }

    # Default stop distance in pips
    DEFAULT_STOP_PIPS = 30

    # Default target multiplier (R:R)
    DEFAULT_RR_RATIO = 2.0

    def __init__(
        self,
        intent_dir: str | Path | None = None,
    ) -> None:
        """
        Initialize generator.

        Args:
            intent_dir: Directory for intent output (default: phoenix/intents/incoming)
        """
        if intent_dir:
            self._intent_dir = Path(intent_dir)
        else:
            # Default to phoenix/intents/incoming
            self._intent_dir = Path(__file__).parent.parent / "intents" / "incoming"

        # Ensure directory exists
        self._intent_dir.mkdir(parents=True, exist_ok=True)

    def create_signal(
        self,
        signal_type: SignalType = SignalType.READY,
        pair: Pair = Pair.EURUSD,
        confidence: float = 0.85,
        setup_type: SetupType = SetupType.FVG_ENTRY,
        entry_price: float | None = None,
        stop_loss: float | None = None,
        take_profit: float | None = None,
        htf_bias: str = "BULLISH",
        risk_percent: float = 1.0,
        session: str = "LONDON",
        notes: str = "",
    ) -> CSESignal:
        """
        Create a mock CSE signal.

        Args:
            signal_type: READY, FORMING, or NONE
            pair: Trading pair
            confidence: Signal confidence (0-1)
            setup_type: Type of setup
            entry_price: Entry price (auto-calculated if not provided)
            stop_loss: Stop loss price (auto-calculated if not provided)
            take_profit: Take profit price (auto-calculated if not provided)
            htf_bias: Higher timeframe bias (BULLISH/BEARISH)
            risk_percent: Risk per trade (%)
            session: Trading session
            notes: Additional notes

        Returns:
            CSESignal with all parameters set
        """
        # Auto-calculate prices if not provided
        if entry_price is None:
            entry_price = self.DEFAULT_PRICES.get(pair, 1.0)

        if stop_loss is None:
            pip_value = 0.0001 if "JPY" not in pair.value else 0.01
            stop_distance = self.DEFAULT_STOP_PIPS * pip_value

            if htf_bias == "BULLISH":
                stop_loss = entry_price - stop_distance
            else:
                stop_loss = entry_price + stop_distance

        if take_profit is None:
            stop_distance = abs(entry_price - stop_loss)
            target_distance = stop_distance * self.DEFAULT_RR_RATIO

            if htf_bias == "BULLISH":
                take_profit = entry_price + target_distance
            else:
                take_profit = entry_price - target_distance

        signal = CSESignal(
            signal_type=signal_type,
            pair=pair,
            confidence=confidence,
            setup_type=setup_type,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            htf_bias=htf_bias,
            risk_percent=risk_percent,
            session=session,
            notes=notes or f"Mock signal from mock_cse_generator ({signal_type.value})",
        )

        return signal

    def create_intent(self, signal: CSESignal) -> IntentPayload:
        """Wrap signal in intent payload."""
        return IntentPayload(signal=signal)

    def write_intent(
        self,
        signal: CSESignal,
        filename: str | None = None,
    ) -> Path:
        """
        Write intent to file.

        Args:
            signal: CSE signal to wrap
            filename: Output filename (auto-generated if not provided)

        Returns:
            Path to written file
        """
        # Validate signal
        errors = signal.validate()
        if errors:
            raise ValueError(f"Signal validation failed: {errors}")

        # Create intent
        intent = self.create_intent(signal)

        # Generate filename
        if filename is None:
            timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"mock_intent_{timestamp}.yaml"

        # Write file
        output_path = self._intent_dir / filename
        with open(output_path, "w") as f:
            yaml.dump(intent.to_dict(), f, default_flow_style=False)

        return output_path


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate mock CSE signals for Phoenix UX testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate READY signal for EUR/USD
    python mock_cse_generator.py --signal READY --pair EURUSD

    # Generate with custom confidence and entry
    python mock_cse_generator.py --signal READY --pair GBPUSD --confidence 0.90 --entry 1.2550

    # Generate FORMING signal (not ready to execute)
    python mock_cse_generator.py --signal FORMING --pair USDJPY
        """,
    )

    parser.add_argument(
        "--signal",
        type=str,
        choices=["READY", "FORMING", "NONE"],
        default="READY",
        help="Signal type (default: READY)",
    )

    parser.add_argument(
        "--pair",
        type=str,
        choices=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"],
        default="EURUSD",
        help="Trading pair (default: EURUSD)",
    )

    parser.add_argument(
        "--confidence",
        type=float,
        default=0.85,
        help="Signal confidence 0-1 (default: 0.85)",
    )

    parser.add_argument(
        "--entry",
        type=float,
        default=None,
        help="Entry price (auto-calculated if not provided)",
    )

    parser.add_argument(
        "--stop",
        type=float,
        default=None,
        help="Stop loss price (auto-calculated if not provided)",
    )

    parser.add_argument(
        "--target",
        type=float,
        default=None,
        help="Take profit price (auto-calculated if not provided)",
    )

    parser.add_argument(
        "--setup-type",
        type=str,
        choices=["FVG_ENTRY", "OTE_ENTRY", "BOS_ENTRY", "LIQUIDITY_SWEEP", "ORDER_BLOCK"],
        default="FVG_ENTRY",
        help="Setup type (default: FVG_ENTRY)",
    )

    parser.add_argument(
        "--bias",
        type=str,
        choices=["BULLISH", "BEARISH"],
        default="BULLISH",
        help="Higher timeframe bias (default: BULLISH)",
    )

    parser.add_argument(
        "--risk",
        type=float,
        default=1.0,
        help="Risk percent (default: 1.0)",
    )

    parser.add_argument(
        "--session",
        type=str,
        default="LONDON",
        help="Trading session (default: LONDON)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for intent file",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print intent without writing file",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Create generator
    generator = MockCSEGenerator(intent_dir=args.output_dir)

    # Create signal
    signal = generator.create_signal(
        signal_type=SignalType(args.signal),
        pair=Pair(args.pair),
        confidence=args.confidence,
        setup_type=SetupType(args.setup_type),
        entry_price=args.entry,
        stop_loss=args.stop,
        take_profit=args.target,
        htf_bias=args.bias,
        risk_percent=args.risk,
        session=args.session,
    )

    # Validate
    errors = signal.validate()
    if errors:
        print("ERROR: Signal validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    # Output
    intent = generator.create_intent(signal)

    if args.dry_run:
        print("=== DRY RUN - Intent would be written: ===")
        print(yaml.dump(intent.to_dict(), default_flow_style=False))
        return 0

    # Write file
    output_path = generator.write_intent(signal)
    print(f"Intent written to: {output_path}")
    print(f"Signal ID: {signal.signal_id}")
    print(f"Intent ID: {intent.intent_id}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
