"""
HPG Parser — Hunt Parameter Grammar Parser
==========================================

Parses natural language hypotheses into HPG (Hunt Parameter Grammar).

INVARIANT: INV-HUNT-HPG-1 "Hunt only accepts valid HPG JSON"

The parser:
1. Takes natural language hypothesis
2. Uses LLM to extract structured parameters
3. Validates against hpg_schema.yaml
4. Returns validated HPG or validation errors

CLOSED-WORLD: No free-text fields. All parameters from closed enum/range.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# =============================================================================
# ENUMS (Closed-world from hpg_schema.yaml)
# =============================================================================


class SignalType(str, Enum):
    """ICT signal types."""

    FVG = "FVG"
    BOS = "BOS"
    CHOCH = "CHoCH"
    OTE = "OTE"
    LIQUIDITY_SWEEP = "LIQUIDITY_SWEEP"


class Session(str, Enum):
    """Trading sessions."""

    LONDON = "LONDON"
    NY = "NY"
    ASIA = "ASIA"
    ANY = "ANY"


class TimeFilterOperator(str, Enum):
    """Time filter operators."""

    AFTER = "AFTER"
    BEFORE = "BEFORE"
    BETWEEN = "BETWEEN"


class StopModel(str, Enum):
    """Stop loss placement strategies."""

    TIGHT = "TIGHT"
    NORMAL = "NORMAL"
    WIDE = "WIDE"
    ATR_BASED = "ATR_BASED"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class TimeFilter:
    """Time filter specification."""

    operator: TimeFilterOperator
    value: str  # HH:MM or HH:MM-HH:MM

    def validate(self) -> list[str]:
        """Validate time filter format."""
        errors = []
        pattern = r"^([01]?[0-9]|2[0-3]):[0-5][0-9](-([01]?[0-9]|2[0-3]):[0-5][0-9])?$"
        if not re.match(pattern, self.value):
            errors.append(f"Invalid time format: {self.value}")

        if self.operator == TimeFilterOperator.BETWEEN and "-" not in self.value:
            errors.append("BETWEEN operator requires HH:MM-HH:MM format")

        return errors


@dataclass
class HPG:
    """
    Hunt Parameter Grammar — structured hypothesis parameters.

    All fields are closed-world (enums or bounded ranges).
    No free-text parameters allowed.
    """

    hpg_version: str
    signal_type: SignalType
    pair: str
    session: Session
    stop_model: StopModel
    risk_percent: float
    random_seed: int
    time_filter: TimeFilter | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result = {
            "hpg_version": self.hpg_version,
            "signal_type": self.signal_type.value,
            "pair": self.pair,
            "session": self.session.value,
            "stop_model": self.stop_model.value,
            "risk_percent": self.risk_percent,
            "random_seed": self.random_seed,
        }
        if self.time_filter:
            result["time_filter"] = {
                "operator": self.time_filter.operator.value,
                "value": self.time_filter.value,
            }
        return result

    def compute_hash(self) -> str:
        """Compute deterministic hash of HPG."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HPG:
        """Create HPG from dictionary."""
        time_filter = None
        if "time_filter" in data and data["time_filter"]:
            time_filter = TimeFilter(
                operator=TimeFilterOperator(data["time_filter"]["operator"]),
                value=data["time_filter"]["value"],
            )

        return cls(
            hpg_version=data.get("hpg_version", "1.0"),
            signal_type=SignalType(data["signal_type"]),
            pair=data["pair"],
            session=Session(data.get("session", "ANY")),
            stop_model=StopModel(data.get("stop_model", "NORMAL")),
            risk_percent=float(data.get("risk_percent", 1.0)),
            random_seed=int(data["random_seed"]),
            time_filter=time_filter,
        )


@dataclass
class ValidationResult:
    """Result of HPG validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# HPG PARSER
# =============================================================================


class HPGParser:
    """
    Parses natural language hypotheses into HPG.

    Uses LLM (configurable: Gemma local or Claude API) to extract
    structured parameters, then validates against schema.

    INVARIANT: Output MUST match hpg_schema.yaml
    """

    def __init__(
        self,
        valid_pairs: list[str] | None = None,
        llm_backend: str = "mock",  # "gemma", "claude", "mock"
    ) -> None:
        """
        Initialize parser.

        Args:
            valid_pairs: List of valid pair symbols (from pairs.yaml)
            llm_backend: LLM backend to use for parsing
        """
        self._valid_pairs = valid_pairs or self._load_valid_pairs()
        self._llm_backend = llm_backend

    def _load_valid_pairs(self) -> list[str]:
        """Load valid pairs from config."""
        pairs_path = Path(__file__).parent.parent / "config" / "pairs.yaml"
        if pairs_path.exists():
            with open(pairs_path) as f:
                config = yaml.safe_load(f)
                return [
                    p["symbol"]
                    for p in config.get("pairs", [])
                    if p.get("status") == "ACTIVE"
                ]
        return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]

    def parse(self, natural_language: str, seed: int | None = None) -> HPG | None:
        """
        Parse natural language hypothesis into HPG.

        Args:
            natural_language: Hypothesis text (e.g., "Test FVG entries after 8:30am London")
            seed: Random seed (required for determinism)

        Returns:
            HPG object or None if parsing fails
        """
        if seed is None:
            # Generate deterministic seed from input
            seed = int(hashlib.sha256(natural_language.encode()).hexdigest()[:8], 16)

        # Parse using LLM backend
        if self._llm_backend == "mock":
            hpg_dict = self._mock_parse(natural_language, seed)
        else:
            hpg_dict = self._llm_parse(natural_language, seed)

        if hpg_dict is None:
            return None

        try:
            return HPG.from_dict(hpg_dict)
        except (KeyError, ValueError):
            return None

    def _mock_parse(self, text: str, seed: int) -> dict[str, Any] | None:
        """
        Mock parser for testing (no LLM call).

        Extracts parameters from structured text patterns.
        """
        text_lower = text.lower()

        # Detect signal type
        signal_type = "FVG"  # default
        for st in SignalType:
            if st.value.lower() in text_lower:
                signal_type = st.value
                break

        # Detect session
        session = "ANY"
        for s in Session:
            if s.value.lower() in text_lower:
                session = s.value
                break

        # Detect pair
        pair = "EURUSD"  # default
        for p in self._valid_pairs:
            if p.lower() in text_lower:
                pair = p
                break

        # Detect stop model
        stop_model = "NORMAL"
        if "tight" in text_lower:
            stop_model = "TIGHT"
        elif "wide" in text_lower:
            stop_model = "WIDE"

        # Detect time filter
        time_filter = None
        time_match = re.search(r"(\d{1,2}:\d{2})", text)
        if time_match:
            time_value = time_match.group(1)
            if "after" in text_lower:
                time_filter = {"operator": "AFTER", "value": time_value}
            elif "before" in text_lower:
                time_filter = {"operator": "BEFORE", "value": time_value}

        return {
            "hpg_version": "1.0",
            "signal_type": signal_type,
            "pair": pair,
            "session": session,
            "stop_model": stop_model,
            "risk_percent": 1.0,
            "random_seed": seed,
            "time_filter": time_filter,
        }

    def _llm_parse(self, text: str, seed: int) -> dict[str, Any] | None:
        """
        Parse using LLM backend.

        TODO: Implement Gemma/Claude integration in S30.
        """
        # Placeholder for LLM integration
        # Will use structured output/JSON mode
        return self._mock_parse(text, seed)

    def validate(self, hpg: HPG) -> ValidationResult:
        """
        Validate HPG against schema.

        Args:
            hpg: HPG to validate

        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Version check
        if hpg.hpg_version != "1.0":
            warnings.append(f"Unknown HPG version: {hpg.hpg_version}")

        # Pair validation
        if hpg.pair not in self._valid_pairs:
            errors.append(f"Invalid pair: {hpg.pair}. Valid: {self._valid_pairs}")

        # Risk bounds
        if not 0.5 <= hpg.risk_percent <= 2.5:
            errors.append(f"Risk percent {hpg.risk_percent} outside bounds [0.5, 2.5]")

        # Time filter validation
        if hpg.time_filter:
            time_errors = hpg.time_filter.validate()
            errors.extend(time_errors)

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
