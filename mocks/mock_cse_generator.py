#!/usr/bin/env python3
"""
Mock CSE Generator — 5-Drawer Gate Pipeline Validation
========================================================

S34: D2 MOCK_ORACLE_PIPELINE_VALIDATION

Generates mock CSE (Canonical Signal Envelope) signals from 5-drawer gates
for testing the Phoenix approval workflow before Olya arrives.

INVARIANTS:
- INV-D2-FORMAT-1: Mock CSE schema == production CSE schema
- INV-D2-TRACEABLE-1: Evidence refs resolvable to conditions.yaml
- INV-D2-NO-INTELLIGENCE-1: Zero market analysis logic
- INV-D2-NO-COMPOSITION-1: Whitelist gate IDs only (no synthesis)

Usage:
    python mock_cse_generator.py --gate GATE-COND-001 --pair EURUSD
    python mock_cse_generator.py --list-gates
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# CONSTANTS
# =============================================================================

# Source identifier for mock signals
MOCK_SOURCE = "MOCK_5DRAWER"

# Path to 5-drawer conditions
CONDITIONS_PATH = Path(__file__).parent.parent / "cso" / "knowledge" / "conditions.yaml"


# =============================================================================
# ENUMS
# =============================================================================


class CSESource(str, Enum):
    """Valid CSE sources."""

    CSO = "CSO"  # Production: Olya's CSO
    HUNT_SURVIVOR = "HUNT_SURVIVOR"  # Production: Promoted strategy
    MANUAL = "MANUAL"  # Production: Human-entered
    MOCK_5DRAWER = "MOCK_5DRAWER"  # Mock: 5-drawer gate simulation


class Pair(str, Enum):
    """Supported trading pairs."""

    EURUSD = "EURUSD"
    GBPUSD = "GBPUSD"
    USDJPY = "USDJPY"
    AUDUSD = "AUDUSD"
    USDCAD = "USDCAD"
    NZDUSD = "NZDUSD"


# =============================================================================
# 5-DRAWER GATE LOADER
# =============================================================================


@dataclass
class GateDefinition:
    """Definition of a composite gate from conditions.yaml."""

    gate_id: str
    name: str
    requires: list[str]
    output: str
    source_ref: str = ""

    def to_evidence_ref(self) -> dict[str, Any]:
        """Create evidence reference for traceability."""
        return {
            "gate_id": self.gate_id,
            "name": self.name,
            "source": "conditions.yaml",
            "ref": self.source_ref,
            "requires": self.requires,
        }


class GateLoader:
    """
    Loads and validates gate definitions from conditions.yaml.

    INVARIANT: INV-D2-NO-COMPOSITION-1
    Only whitelisted gate IDs from conditions.yaml are valid.
    """

    def __init__(self, conditions_path: Path | None = None) -> None:
        """Load gates from conditions.yaml."""
        self._path = conditions_path or CONDITIONS_PATH
        self._gates: dict[str, GateDefinition] = {}
        self._load_gates()

    def _load_gates(self) -> None:
        """Parse composite_gates from conditions.yaml."""
        if not self._path.exists():
            raise FileNotFoundError(f"Conditions file not found: {self._path}")

        with open(self._path) as f:
            data = yaml.safe_load(f)

        composite_gates = data.get("composite_gates", {})

        for gate_key, gate_def in composite_gates.items():
            gate_id = gate_def.get("id", f"GATE-UNKNOWN-{gate_key}")
            self._gates[gate_id] = GateDefinition(
                gate_id=gate_id,
                name=gate_def.get("name", gate_key),
                requires=gate_def.get("requires", []),
                output=gate_def.get("output", ""),
                source_ref=gate_def.get("ref", "conditions.yaml"),
            )

    @property
    def valid_gate_ids(self) -> list[str]:
        """Return list of valid (whitelisted) gate IDs."""
        return list(self._gates.keys())

    def get_gate(self, gate_id: str) -> GateDefinition | None:
        """Get gate definition by ID."""
        return self._gates.get(gate_id)

    def is_valid_gate(self, gate_id: str) -> bool:
        """
        Check if gate ID is in whitelist.

        INV-D2-NO-COMPOSITION-1: Reject non-whitelisted gates.
        """
        return gate_id in self._gates


# =============================================================================
# CSE DATA CLASSES
# =============================================================================


@dataclass
class CSEParameters:
    """Trade parameters within CSE."""

    entry: float
    stop: float
    target: float
    risk_percent: float = 1.0


@dataclass
class CSE:
    """
    Canonical Signal Envelope.

    INV-D2-FORMAT-1: This must match cse_schema.yaml exactly.
    Both mock and production validate against the same schema.
    """

    # Identity
    cse_version: str = "1.0"
    signal_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    # Source
    pair: Pair = Pair.EURUSD
    source: CSESource = CSESource.MOCK_5DRAWER
    setup_type: str = ""

    # Confidence
    confidence: float = 0.75

    # Parameters
    parameters: CSEParameters = field(default_factory=lambda: CSEParameters(0, 0, 0))

    # Evidence chain
    evidence_hash: str = ""

    # Mock-specific: 5-drawer traceability
    gate_id: str = ""
    gate_ref: dict[str, Any] = field(default_factory=dict)

    def compute_evidence_hash(self) -> str:
        """
        Compute evidence hash from gate reference.

        INV-D2-TRACEABLE-1: Hash links to source refs.
        """
        evidence = {
            "gate_id": self.gate_id,
            "gate_ref": self.gate_ref,
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
        }
        json_str = str(sorted(evidence.items()))
        return hashlib.sha256(json_str.encode()).hexdigest()

    @property
    def direction(self) -> str:
        """Derived: LONG or SHORT."""
        if self.parameters.entry < self.parameters.target:
            return "LONG"
        return "SHORT"

    @property
    def risk_reward(self) -> float:
        """Derived: Risk/reward ratio."""
        entry = self.parameters.entry
        stop = self.parameters.stop
        target = self.parameters.target

        stop_dist = abs(entry - stop)
        target_dist = abs(target - entry)

        if stop_dist == 0:
            return 0.0
        return target_dist / stop_dist

    def validate(self) -> list[str]:
        """
        Validate CSE against schema rules.

        Returns list of validation errors (empty if valid).
        """
        errors: list[str] = []

        # Required fields
        if not self.signal_id:
            errors.append("signal_id is required")
        if not self.pair:
            errors.append("pair is required")
        if not self.source:
            errors.append("source is required")
        if not self.setup_type:
            errors.append("setup_type is required")
        if not self.evidence_hash:
            errors.append("evidence_hash is required")

        # Confidence range
        if not 0.0 <= self.confidence <= 1.0:
            errors.append(f"confidence must be 0-1, got {self.confidence}")

        # Risk percent range
        if not 0.5 <= self.parameters.risk_percent <= 2.5:
            errors.append(f"risk_percent must be 0.5-2.5, got {self.parameters.risk_percent}")

        # Entry != stop
        if self.parameters.entry == self.parameters.stop:
            errors.append("entry and stop cannot be equal")

        # Entry != target
        if self.parameters.entry == self.parameters.target:
            errors.append("entry and target cannot be equal")

        # Stop on correct side
        if self.direction == "LONG" and self.parameters.stop >= self.parameters.entry:
            errors.append("LONG: stop must be below entry")
        if self.direction == "SHORT" and self.parameters.stop <= self.parameters.entry:
            errors.append("SHORT: stop must be above entry")

        # Target on correct side
        if self.direction == "LONG" and self.parameters.target <= self.parameters.entry:
            errors.append("LONG: target must be above entry")
        if self.direction == "SHORT" and self.parameters.target >= self.parameters.entry:
            errors.append("SHORT: target must be below entry")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary matching cse_schema.yaml."""
        return {
            "cse_version": self.cse_version,
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "pair": self.pair.value,
            "source": self.source.value,
            "setup_type": self.setup_type,
            "confidence": self.confidence,
            "parameters": {
                "entry": self.parameters.entry,
                "stop": self.parameters.stop,
                "target": self.parameters.target,
                "risk_percent": self.parameters.risk_percent,
            },
            "evidence_hash": self.evidence_hash,
            # Mock extension for traceability
            "_mock_metadata": {
                "gate_id": self.gate_id,
                "gate_ref": self.gate_ref,
            },
        }


# =============================================================================
# MOCK CSE GENERATOR
# =============================================================================


class MockCSEGenerator:
    """
    Generates mock CSE signals from 5-drawer gates.

    INVARIANT: INV-D2-NO-INTELLIGENCE-1
    This generator contains ZERO market analysis logic.
    It only maps gate IDs to mock trade parameters.
    """

    # Default prices per pair (static, no market logic)
    DEFAULT_PRICES: dict[Pair, float] = {
        Pair.EURUSD: 1.0850,
        Pair.GBPUSD: 1.2700,
        Pair.USDJPY: 150.00,
        Pair.AUDUSD: 0.6500,
        Pair.USDCAD: 1.3500,
        Pair.NZDUSD: 0.5800,
    }

    def __init__(
        self,
        gate_loader: GateLoader | None = None,
        intent_dir: Path | None = None,
    ) -> None:
        """
        Initialize generator.

        Args:
            gate_loader: Loader for 5-drawer gates
            intent_dir: Directory for intent output
        """
        self._gate_loader = gate_loader or GateLoader()
        self._intent_dir = intent_dir or (Path(__file__).parent.parent / "intents" / "incoming")
        self._intent_dir.mkdir(parents=True, exist_ok=True)

    @property
    def valid_gate_ids(self) -> list[str]:
        """Return list of valid (whitelisted) gate IDs."""
        return self._gate_loader.valid_gate_ids

    def create_cse_from_gate(
        self,
        gate_id: str,
        pair: Pair = Pair.EURUSD,
        risk_percent: float = 1.0,
    ) -> CSE:
        """
        Create a mock CSE from a 5-drawer gate.

        INVARIANT: INV-D2-NO-COMPOSITION-1
        Only whitelisted gate IDs accepted.

        Args:
            gate_id: Gate ID from conditions.yaml (e.g., GATE-COND-001)
            pair: Trading pair
            risk_percent: Risk per trade

        Returns:
            Valid CSE

        Raises:
            ValueError: If gate_id not in whitelist
        """
        # Enforce whitelist (INV-D2-NO-COMPOSITION-1)
        if not self._gate_loader.is_valid_gate(gate_id):
            raise ValueError(
                f"Gate ID '{gate_id}' not in whitelist. "
                f"Valid gates: {self._gate_loader.valid_gate_ids}"
            )

        gate = self._gate_loader.get_gate(gate_id)
        if gate is None:
            raise ValueError(f"Gate {gate_id} not found")

        # Derive direction from gate output
        direction = self._derive_direction(gate)

        # Generate static prices (NO market logic - INV-D2-NO-INTELLIGENCE-1)
        entry, stop, target = self._generate_prices(pair, direction)

        # Create CSE
        cse = CSE(
            pair=pair,
            source=CSESource.MOCK_5DRAWER,
            setup_type=gate.output,
            confidence=0.75,  # Static confidence (no intelligence)
            parameters=CSEParameters(
                entry=entry,
                stop=stop,
                target=target,
                risk_percent=risk_percent,
            ),
            gate_id=gate_id,
            gate_ref=gate.to_evidence_ref(),
        )

        # Compute evidence hash (INV-D2-TRACEABLE-1)
        cse.evidence_hash = cse.compute_evidence_hash()

        return cse

    def _derive_direction(self, gate: GateDefinition) -> str:
        """
        Derive trade direction from gate output.

        NO market analysis - just pattern matching on gate name.
        """
        output = gate.output.upper()
        if "LONG" in output:
            return "LONG"
        if "SHORT" in output:
            return "SHORT"
        # Default to LONG for ambiguous gates
        return "LONG"

    def _generate_prices(
        self,
        pair: Pair,
        direction: str,
    ) -> tuple[float, float, float]:
        """
        Generate static trade prices.

        INVARIANT: INV-D2-NO-INTELLIGENCE-1
        NO market analysis. Static offsets only.
        """
        base_price = self.DEFAULT_PRICES.get(pair, 1.0)

        # Static pip offsets (no intelligence)
        pip_value = 0.0001 if "JPY" not in pair.value else 0.01
        stop_pips = 30
        target_pips = 60  # 2:1 R:R

        if direction == "LONG":
            entry = base_price
            stop = entry - (stop_pips * pip_value)
            target = entry + (target_pips * pip_value)
        else:
            entry = base_price
            stop = entry + (stop_pips * pip_value)
            target = entry - (target_pips * pip_value)

        return entry, stop, target

    def write_cse_intent(self, cse: CSE, filename: str | None = None) -> Path:
        """
        Write CSE as intent file for D1 watcher.

        Args:
            cse: CSE to write
            filename: Optional filename

        Returns:
            Path to written file
        """
        # Validate CSE (INV-D2-FORMAT-1)
        errors = cse.validate()
        if errors:
            raise ValueError(f"CSE validation failed: {errors}")

        # Create intent wrapper
        intent = {
            "type": "CSE",
            "payload": cse.to_dict(),
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": f"mock_cse_{cse.signal_id[:8]}",
        }

        # Generate filename
        if filename is None:
            ts = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            filename = f"cse_{cse.gate_id}_{ts}.yaml"

        # Write file
        output_path = self._intent_dir / filename
        with open(output_path, "w") as f:
            yaml.dump(intent, f, default_flow_style=False)

        return output_path


# =============================================================================
# CSE VALIDATOR
# =============================================================================


class CSEValidator:
    """
    Validates CSE against schema.

    INV-D2-FORMAT-1: Mock and production use same validation.
    """

    @staticmethod
    def validate(cse_dict: dict[str, Any]) -> tuple[bool, list[str]]:
        """
        Validate CSE dictionary against schema.

        Returns:
            (is_valid, list of errors)
        """
        errors: list[str] = []

        # Required fields
        required = [
            "cse_version",
            "signal_id",
            "timestamp",
            "pair",
            "source",
            "setup_type",
            "confidence",
            "parameters",
            "evidence_hash",
        ]

        for field_name in required:
            if field_name not in cse_dict:
                errors.append(f"Missing required field: {field_name}")

        if errors:
            return False, errors

        # Type validations
        if not isinstance(cse_dict.get("confidence"), (int, float)):
            errors.append("confidence must be numeric")
        elif not 0.0 <= cse_dict["confidence"] <= 1.0:
            errors.append("confidence must be 0-1")

        params = cse_dict.get("parameters", {})
        for param in ["entry", "stop", "target", "risk_percent"]:
            if param not in params:
                errors.append(f"Missing parameter: {param}")

        if errors:
            return False, errors

        # Risk percent range
        risk = params.get("risk_percent", 0)
        if not 0.5 <= risk <= 2.5:
            errors.append(f"risk_percent must be 0.5-2.5, got {risk}")

        # Price validations
        entry = params.get("entry", 0)
        stop = params.get("stop", 0)
        target = params.get("target", 0)

        if entry == stop:
            errors.append("entry and stop cannot be equal")
        if entry == target:
            errors.append("entry and target cannot be equal")

        return len(errors) == 0, errors


# =============================================================================
# CLI
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate mock CSE signals from 5-drawer gates",
    )

    parser.add_argument(
        "--gate",
        type=str,
        help="Gate ID from conditions.yaml (e.g., GATE-COND-001)",
    )

    parser.add_argument(
        "--pair",
        type=str,
        choices=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"],
        default="EURUSD",
        help="Trading pair (default: EURUSD)",
    )

    parser.add_argument(
        "--risk",
        type=float,
        default=1.0,
        help="Risk percent (default: 1.0)",
    )

    parser.add_argument(
        "--list-gates",
        action="store_true",
        help="List valid gate IDs",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print CSE without writing file",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory for intent file",
    )

    return parser.parse_args()


def main() -> int:
    """Main entry point."""
    args = parse_args()

    try:
        generator = MockCSEGenerator(intent_dir=Path(args.output_dir) if args.output_dir else None)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    # List gates
    if args.list_gates:
        print("Valid gate IDs (from conditions.yaml):")
        for gate_id in generator.valid_gate_ids:
            print(f"  - {gate_id}")
        return 0

    # Require gate ID for CSE generation
    if not args.gate:
        print("ERROR: --gate is required (use --list-gates to see options)")
        return 1

    # Generate CSE
    try:
        cse = generator.create_cse_from_gate(
            gate_id=args.gate,
            pair=Pair(args.pair),
            risk_percent=args.risk,
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    # Output
    if args.dry_run:
        print("=== DRY RUN - CSE would be written: ===")
        print(yaml.dump(cse.to_dict(), default_flow_style=False))
        print(f"\nValidation: {'PASS' if not cse.validate() else 'FAIL'}")
        return 0

    # Write file
    output_path = generator.write_cse_intent(cse)
    print(f"CSE written to: {output_path}")
    print(f"Signal ID: {cse.signal_id}")
    print(f"Gate: {cse.gate_id}")
    print(f"Direction: {cse.direction}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
