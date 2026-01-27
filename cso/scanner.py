"""
CSO Scanner — Multi-Pair Setup Detection
=========================================

Scans all 6 pairs for setups using StrategyCore.
Emits CSE signals to Shadow.

INVARIANT: INV-CSO-6PAIR-1
"CSO scans all 6 pairs defined in pairs.yaml"
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from .params_loader import CSOParams, ParamsLoader
from .strategy_core import Setup, SetupResult, SetupStatus, StrategyCore
from .structure_detector import StructureDetector

# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class ScanResult:
    """Result of scanning all pairs."""

    timestamp: datetime
    pairs_scanned: int
    ready_setups: list[SetupResult]
    forming_setups: list[SetupResult]
    none_setups: list[SetupResult]

    def to_summary(self) -> str:
        """Generate summary for briefing."""
        lines = [
            f"CSO SCAN — {self.timestamp.strftime('%Y-%m-%d %H:%M')} UTC",
            f"Pairs scanned: {self.pairs_scanned}",
            "",
        ]

        if self.ready_setups:
            lines.append("READY:")
            for sr in self.ready_setups:
                setup = sr.setup
                if setup:
                    lines.append(
                        f"  {sr.pair} ({sr.quality_score:.2f}): "
                        f"{setup.setup_type.value} {setup.direction.value}"
                    )

        if self.forming_setups:
            lines.append("FORMING:")
            for sr in self.forming_setups:
                lines.append(f"  {sr.pair} ({sr.quality_score:.2f}): {sr.reason}")

        if self.none_setups:
            lines.append("NONE:")
            for sr in self.none_setups:
                lines.append(f"  {sr.pair} ({sr.quality_score:.2f})")

        return "\n".join(lines)


@dataclass
class CSESignal:
    """Canonical Signal Envelope for Shadow."""

    signal_id: str
    timestamp: datetime
    pair: str
    source: str
    setup_type: str
    confidence: float
    parameters: dict[str, float]
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "pair": self.pair,
            "source": self.source,
            "setup_type": self.setup_type,
            "confidence": self.confidence,
            "parameters": self.parameters,
            "evidence_hash": self.evidence_hash,
        }


# =============================================================================
# CSO SCANNER
# =============================================================================


class CSOScanner:
    """
    Scans all pairs for trading setups.

    INVARIANT: INV-CSO-6PAIR-1
    Scans all pairs from pairs.yaml, not hardcoded list.
    """

    def __init__(
        self,
        river_reader: Any | None = None,
        params: CSOParams | None = None,
        shadow: Any | None = None,
        telegram: Any | None = None,
    ) -> None:
        """
        Initialize scanner.

        Args:
            river_reader: RiverReader for market data
            params: CSO parameters (loads default if None)
            shadow: Shadow engine for CSE signals
            telegram: TelegramNotifier for alerts
        """
        self._river = river_reader
        self._params = params or ParamsLoader().load()
        self._shadow = shadow
        self._telegram = telegram

        # Load pairs from config
        self._pairs = self._load_pairs()

        # Initialize components
        self._detector = StructureDetector()
        self._core = StrategyCore(
            ready_threshold=self._params.ready_min,
            forming_threshold=self._params.forming_min,
        )

    def scan_all_pairs(self) -> ScanResult:
        """
        Scan all 6 pairs.

        INVARIANT: INV-CSO-6PAIR-1
        """
        ready: list[SetupResult] = []
        forming: list[SetupResult] = []
        none: list[SetupResult] = []

        for pair in self._pairs:
            result = self.scan_pair(pair)

            if result.status == SetupStatus.READY:
                ready.append(result)
                self._emit_cse(result)
            elif result.status == SetupStatus.FORMING:
                forming.append(result)
            else:
                none.append(result)

        return ScanResult(
            timestamp=datetime.now(UTC),
            pairs_scanned=len(self._pairs),
            ready_setups=ready,
            forming_setups=forming,
            none_setups=none,
        )

    def scan_pair(self, pair: str) -> SetupResult:
        """
        Scan single pair for setup.

        Args:
            pair: Currency pair (e.g., "EURUSD")

        Returns:
            SetupResult
        """
        # Get market data
        htf_bars, ltf_bars, current_price = self._get_market_data(pair)

        if htf_bars is None or ltf_bars is None:
            return SetupResult(
                pair=pair,
                status=SetupStatus.NONE,
                quality_score=0.0,
                reason="No market data available",
            )

        # Detect structure
        pip_value = 0.01 if "JPY" in pair else 0.0001
        detector = StructureDetector(pip_value=pip_value)

        htf_structure = detector.detect_all(htf_bars, pair, "4H")
        ltf_structure = detector.detect_all(ltf_bars, pair, "1H")

        # Detect setup
        result = self._core.detect_setup(pair, htf_structure, ltf_structure, current_price)

        # Apply pair weight
        weight = self._params.pair_weights.get(pair, 1.0)
        result.quality_score *= weight

        return result

    def get_ready_setups(self, threshold: float | None = None) -> list[Setup]:
        """
        Get all ready setups.

        Args:
            threshold: Override ready threshold

        Returns:
            List of Setup objects
        """
        result = self.scan_all_pairs()

        setups = []
        for sr in result.ready_setups:
            if sr.setup:
                if threshold is None or sr.quality_score >= threshold:
                    setups.append(sr.setup)

        return setups

    def _load_pairs(self) -> list[str]:
        """Load pairs from pairs.yaml."""
        pairs_path = Path(__file__).parent.parent / "config" / "pairs.yaml"

        if not pairs_path.exists():
            # Default pairs
            return ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD"]

        with open(pairs_path) as f:
            data = yaml.safe_load(f)

        return [p["symbol"] for p in data.get("pairs", []) if p.get("status") == "ACTIVE"]

    def _get_market_data(
        self,
        pair: str,
    ) -> tuple[Any, Any, float]:
        """Get market data for pair."""
        if self._river is None:
            return None, None, 0.0

        try:
            end = datetime.now(UTC)
            start_htf = end - timedelta(days=30)  # 30 days for HTF
            start_ltf = end - timedelta(days=7)  # 7 days for LTF

            htf_bars = self._river.get_bars(pair, "4H", start_htf, end)
            ltf_bars = self._river.get_bars(pair, "1H", start_ltf, end)

            # Current price from latest bar
            if not ltf_bars.empty:
                current_price = float(ltf_bars.iloc[-1]["close"])
            else:
                current_price = 0.0

            return htf_bars, ltf_bars, current_price

        except Exception:
            return None, None, 0.0

    def _emit_cse(self, result: SetupResult) -> None:
        """
        Emit CSE signal to Shadow and Telegram.

        WIRING: CSO → Shadow + Telegram
        INVARIANT: INV-CSO-CSE-1
        """
        if result.setup is None:
            return

        setup = result.setup

        cse = CSESignal(
            signal_id=f"CSE-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(UTC),
            pair=setup.pair,
            source="CSO",
            setup_type=setup.setup_type.value,
            confidence=setup.confidence,
            parameters={
                "entry": setup.entry_price,
                "stop": setup.stop_price,
                "target": setup.target_price,
                "risk_percent": setup.risk_percent,
            },
            evidence_hash=setup.evidence.evidence_hash,
        )

        # WIRING: Send to Shadow
        if self._shadow is not None:
            try:
                from shadow.shadow import CSESignal as ShadowCSE

                shadow_signal = ShadowCSE(
                    signal_id=cse.signal_id,
                    timestamp=cse.timestamp,
                    pair=cse.pair,
                    direction="LONG" if setup.direction.value == "BULLISH" else "SHORT",
                    entry=cse.parameters["entry"],
                    stop=cse.parameters["stop"],
                    target=cse.parameters["target"],
                    risk_percent=cse.parameters["risk_percent"],
                    confidence=cse.confidence,
                    source=cse.source,
                    evidence_hash=cse.evidence_hash,
                )
                self._shadow.consume_signal(shadow_signal)
            except Exception:  # noqa: S110
                pass  # Non-blocking

        # WIRING: Send to Telegram (READY setups only)
        if self._telegram is not None and setup.confidence >= 0.8:
            try:
                self._telegram.send_sync(
                    message=self._format_setup_alert(setup),
                    level="INFO",
                    category=f"setup:{setup.pair}",
                )
            except Exception:  # noqa: S110
                pass  # Non-blocking

    def _format_setup_alert(self, setup: Any) -> str:
        """Format setup alert for Telegram."""
        direction = setup.direction.value
        emoji = "📈" if direction == "BULLISH" else "📉"

        return f"""
{emoji} <b>SETUP READY</b>

<b>Pair:</b> {setup.pair}
<b>Type:</b> {setup.setup_type.value}
<b>Direction:</b> {direction}
<b>Confidence:</b> {setup.confidence:.1%}
<b>Entry:</b> {setup.entry_price:.5f}
<b>Stop:</b> {setup.stop_price:.5f}
<b>Target:</b> {setup.target_price:.5f}
"""
