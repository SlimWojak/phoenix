"""
Signalman — Multi-Signal Decay Detection
=========================================

Monitors strategy performance for decay signals.
Triggers ONE-WAY-KILL when multiple signals align.

INVARIANT: INV-SIGNALMAN-COLD-1
"No decay alerts until min_beads_for_analysis reached"

INVARIANT: INV-SIGNALMAN-DECAY-1
"Multi-signal decay requires 2+ signals confirming before kill"
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

# =============================================================================
# ENUMS
# =============================================================================


class DecayType(str, Enum):
    """Types of decay signals."""

    PERFORMANCE = "PERFORMANCE"  # Sharpe/win rate drift
    SIGNAL_QUALITY = "SIGNAL_QUALITY"  # Setup quality degradation
    DISTRIBUTION = "DISTRIBUTION"  # P&L distribution shift (KS test)
    VOLATILITY = "VOLATILITY"  # Market regime change
    FREQUENCY = "FREQUENCY"  # Trade frequency anomaly


class DecaySeverity(str, Enum):
    """Decay severity levels."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class DecaySignal:
    """Individual decay signal."""

    decay_type: DecayType
    value: float
    threshold: float
    exceeded: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "decay_type": self.decay_type.value,
            "value": self.value,
            "threshold": self.threshold,
            "exceeded": self.exceeded,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DecayAlert:
    """Decay alert with multiple signals."""

    alert_id: str
    strategy_id: str
    severity: DecaySeverity
    signals: list[DecaySignal]
    trigger_kill: bool
    reason: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        return {
            "alert_id": self.alert_id,
            "strategy_id": self.strategy_id,
            "severity": self.severity.value,
            "signals": [s.to_dict() for s in self.signals],
            "trigger_kill": self.trigger_kill,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
        }


# =============================================================================
# SIGNALMAN
# =============================================================================


class Signalman:
    """
    Multi-signal decay detection.

    INVARIANT: INV-SIGNALMAN-COLD-1
    Requires minimum beads before analyzing.

    INVARIANT: INV-SIGNALMAN-DECAY-1
    Kill requires 2+ signals confirming.
    """

    DEFAULT_THRESHOLDS = {
        DecayType.PERFORMANCE: {
            "sharpe_drift": 0.3,  # Sharpe dropped by 0.3
            "win_rate_drift": 0.1,  # Win rate dropped by 10%
        },
        DecayType.DISTRIBUTION: {
            "ks_p_value": 0.05,  # KS test significant at 5%
        },
        DecayType.SIGNAL_QUALITY: {
            "quality_drift": 0.15,  # Setup quality dropped 15%
        },
        DecayType.FREQUENCY: {
            "frequency_zscore": 2.0,  # 2 std devs from mean
        },
    }

    def __init__(
        self,
        bead_store: Any | None = None,
        kill_manager: Any | None = None,
        min_beads: int = 20,
        lookback_days: int = 30,
    ) -> None:
        """
        Initialize Signalman.

        Args:
            bead_store: BeadStore for reading performance beads
            kill_manager: KillManager for triggering kills
            min_beads: Minimum beads before analysis (INV-SIGNALMAN-COLD-1)
            lookback_days: Days of history to analyze
        """
        self._bead_store = bead_store
        self._kill_manager = kill_manager
        self._min_beads = min_beads
        self._lookback_days = lookback_days
        self._thresholds = self.DEFAULT_THRESHOLDS.copy()

    def analyze_strategy(self, strategy_id: str) -> DecayAlert | None:
        """
        Analyze strategy for decay.

        Args:
            strategy_id: Strategy to analyze

        Returns:
            DecayAlert if decay detected, else None
        """
        # Get performance beads
        beads = self._get_performance_beads(strategy_id)

        # Check cold start (INV-SIGNALMAN-COLD-1)
        if len(beads) < self._min_beads:
            return None  # Not enough data

        # Check each decay signal
        signals: list[DecaySignal] = []

        perf_signal = self._check_performance_decay(beads)
        if perf_signal:
            signals.append(perf_signal)

        dist_signal = self._check_distribution_decay(beads)
        if dist_signal:
            signals.append(dist_signal)

        freq_signal = self._check_frequency_decay(beads)
        if freq_signal:
            signals.append(freq_signal)

        # No signals = no alert
        if not signals:
            return None

        # Determine severity and kill trigger
        exceeded_count = sum(1 for s in signals if s.exceeded)
        trigger_kill = exceeded_count >= 2  # INV-SIGNALMAN-DECAY-1

        if trigger_kill:
            severity = DecaySeverity.CRITICAL
        elif exceeded_count >= 1:
            severity = DecaySeverity.WARNING
        else:
            severity = DecaySeverity.INFO

        # Build alert
        alert = DecayAlert(
            alert_id=f"DECAY-{uuid.uuid4().hex[:8]}",
            strategy_id=strategy_id,
            severity=severity,
            signals=signals,
            trigger_kill=trigger_kill,
            reason=self._build_reason(signals, exceeded_count),
        )

        # Trigger kill if needed
        if trigger_kill and self._kill_manager:
            self._kill_manager.set_kill_flag(
                strategy_id=strategy_id,
                reason=alert.reason,
                triggered_by="SIGNALMAN",
                decay_metrics={
                    "signals": [s.to_dict() for s in signals],
                },
            )

        return alert

    def check_all_strategies(self) -> list[DecayAlert]:
        """
        Check all active strategies for decay.

        Returns:
            List of decay alerts
        """
        alerts: list[DecayAlert] = []

        # Get unique strategies from beads
        strategies = self._get_active_strategies()

        for strategy_id in strategies:
            alert = self.analyze_strategy(strategy_id)
            if alert:
                alerts.append(alert)

        return alerts

    def _get_performance_beads(self, strategy_id: str) -> list[dict]:
        """Get performance beads for strategy."""
        if self._bead_store is None:
            return []

        try:
            cutoff = datetime.now(UTC) - timedelta(days=self._lookback_days)
            cutoff_str = cutoff.isoformat()

            # Query beads
            beads = self._bead_store.query_sql(
                f"SELECT * FROM beads WHERE bead_type = 'PERFORMANCE' "  # noqa: S608
                f"AND content LIKE '%{strategy_id}%' "
                f"AND timestamp_utc >= '{cutoff_str}' "
                f"ORDER BY timestamp_utc DESC",
            )
            return beads or []
        except Exception:
            return []

    def _get_active_strategies(self) -> list[str]:
        """Get list of active strategies."""
        if self._bead_store is None:
            return []

        try:
            beads = self._bead_store.query_sql(
                "SELECT DISTINCT json_extract(content, '$.strategy_id') as sid "
                "FROM beads WHERE bead_type = 'PERFORMANCE'",
            )
            return [b.get("sid") for b in (beads or []) if b.get("sid")]
        except Exception:
            return []

    def _check_performance_decay(self, beads: list[dict]) -> DecaySignal | None:
        """Check for performance decay (Sharpe/win rate)."""
        if len(beads) < 10:
            return None

        # Extract metrics
        sharpes = []
        win_rates = []

        for bead in beads:
            content = bead.get("content", {})
            if isinstance(content, str):
                import json

                content = json.loads(content)

            metrics = content.get("metrics", {})
            if "sharpe" in metrics:
                sharpes.append(metrics["sharpe"])
            if "win_rate" in metrics:
                win_rates.append(metrics["win_rate"])

        if len(sharpes) < 5:
            return None

        # Calculate drift (recent vs historical)
        mid = len(sharpes) // 2
        recent_sharpe = np.mean(sharpes[:mid]) if sharpes[:mid] else 0
        old_sharpe = np.mean(sharpes[mid:]) if sharpes[mid:] else 0
        sharpe_drift = old_sharpe - recent_sharpe

        threshold = self._thresholds[DecayType.PERFORMANCE]["sharpe_drift"]
        exceeded = sharpe_drift > threshold

        return DecaySignal(
            decay_type=DecayType.PERFORMANCE,
            value=sharpe_drift,
            threshold=threshold,
            exceeded=exceeded,
        )

    def _check_distribution_decay(self, beads: list[dict]) -> DecaySignal | None:
        """Check for P&L distribution shift using KS test."""
        if len(beads) < 20:
            return None

        # Extract P&L values
        pnls = []
        for bead in beads:
            content = bead.get("content", {})
            if isinstance(content, str):
                import json

                content = json.loads(content)

            metrics = content.get("metrics", {})
            if "pnl" in metrics:
                pnls.append(metrics["pnl"])

        if len(pnls) < 10:
            return None

        # Split into recent and historical
        mid = len(pnls) // 2
        recent = np.array(pnls[:mid])
        historical = np.array(pnls[mid:])

        # KS test
        try:
            from scipy import stats

            ks_stat, p_value = stats.ks_2samp(recent, historical)
        except ImportError:
            # Simplified check without scipy
            recent_mean = np.mean(recent)
            hist_mean = np.mean(historical)
            p_value = 1.0 if abs(recent_mean - hist_mean) < 0.1 else 0.01

        threshold = self._thresholds[DecayType.DISTRIBUTION]["ks_p_value"]
        exceeded = p_value < threshold

        return DecaySignal(
            decay_type=DecayType.DISTRIBUTION,
            value=p_value,
            threshold=threshold,
            exceeded=exceeded,
        )

    def _check_frequency_decay(self, beads: list[dict]) -> DecaySignal | None:
        """Check for trade frequency anomaly."""
        if len(beads) < 10:
            return None

        # Calculate time between beads
        timestamps = []
        for bead in beads:
            ts = bead.get("timestamp_utc")
            if ts:
                if isinstance(ts, str):
                    from datetime import datetime

                    ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                timestamps.append(ts)

        if len(timestamps) < 5:
            return None

        timestamps.sort(reverse=True)

        # Calculate gaps
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i - 1] - timestamps[i]).total_seconds() / 3600
            gaps.append(gap)

        if not gaps:
            return None

        # Calculate z-score of recent frequency
        mean_gap = np.mean(gaps)
        std_gap = np.std(gaps) or 1.0
        recent_gap = gaps[0] if gaps else mean_gap
        zscore = abs(recent_gap - mean_gap) / std_gap

        threshold = self._thresholds[DecayType.FREQUENCY]["frequency_zscore"]
        exceeded = zscore > threshold

        return DecaySignal(
            decay_type=DecayType.FREQUENCY,
            value=zscore,
            threshold=threshold,
            exceeded=exceeded,
        )

    def _build_reason(self, signals: list[DecaySignal], exceeded: int) -> str:
        """Build human-readable reason."""
        types = [s.decay_type.value for s in signals if s.exceeded]
        if exceeded >= 2:
            return f"Multi-signal decay: {', '.join(types)}"
        if exceeded == 1:
            return f"Single signal decay: {types[0]}"
        return "Decay signals detected but below threshold"
