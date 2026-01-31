"""
Synthetic River — Mock Data Generator for Offline Testing
==========================================================

Sprint: S42 Track D (RIVER_COMPLETION)
Source: Extracted from lab/backtester.py::_generate_mock_bars()

Purpose:
  Provides deterministic mock bar data when real River is unavailable.
  Used for:
  - CI/CD testing without IBKR connection
  - Development without market data
  - Offline demos
  
INVARIANTS:
  INV-SYNTH-DETERMINISM: Same inputs → same outputs (seeded RNG)
  INV-SYNTH-SCHEMA: Output matches real River schema
  INV-SYNTH-PAIRS: Supports all 6 trading pairs

Usage:
    from river.synthetic_river import SyntheticRiver
    
    river = SyntheticRiver()
    bars = river.get_bars("EURUSD", "1H", start_dt, end_dt)
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd


# =============================================================================
# CONSTANTS
# =============================================================================


SUPPORTED_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD"]

BASE_PRICES = {
    "EURUSD": 1.0850,
    "GBPUSD": 1.2650,
    "USDJPY": 148.50,
    "AUDUSD": 0.6550,
    "NZDUSD": 0.6150,
    "USDCAD": 1.3550,
}

TIMEFRAME_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1H": 60,
    "4H": 240,
    "1D": 1440,
}


# =============================================================================
# DATA STRUCTURES
# =============================================================================


@dataclass
class SyntheticBar:
    """Single synthetic OHLCV bar."""
    
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


# =============================================================================
# SYNTHETIC RIVER
# =============================================================================


class SyntheticRiver:
    """
    Mock River implementation for testing and development.
    
    Generates deterministic price data based on seed.
    Same inputs always produce same outputs (INV-SYNTH-DETERMINISM).
    """
    
    def __init__(self, volatility: float = 0.0010, seed_prefix: str = "phoenix"):
        """
        Initialize synthetic river.
        
        Args:
            volatility: Price movement volatility (standard deviation)
            seed_prefix: Prefix for deterministic seed generation
        """
        self.volatility = volatility
        self.seed_prefix = seed_prefix
        self._is_available = True
    
    def is_available(self) -> bool:
        """Check if synthetic river is available (always True)."""
        return self._is_available
    
    def has_data_for_pair(self, pair: str) -> bool:
        """Check if pair is supported."""
        return pair in SUPPORTED_PAIRS
    
    def get_bars(
        self,
        pair: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> pd.DataFrame:
        """
        Generate synthetic bars for a pair and timeframe.
        
        INV-SYNTH-DETERMINISM: Same inputs → same outputs.
        
        Args:
            pair: Trading pair (e.g., "EURUSD")
            timeframe: Bar timeframe (e.g., "1H")
            start: Start datetime (UTC)
            end: End datetime (UTC)
            
        Returns:
            DataFrame with OHLCV data matching real River schema
        """
        if pair not in SUPPORTED_PAIRS:
            raise ValueError(f"Unsupported pair: {pair}. Supported: {SUPPORTED_PAIRS}")
        
        if timeframe not in TIMEFRAME_MINUTES:
            raise ValueError(f"Unsupported timeframe: {timeframe}")
        
        # Ensure UTC
        if start.tzinfo is None:
            start = start.replace(tzinfo=UTC)
        if end.tzinfo is None:
            end = end.replace(tzinfo=UTC)
        
        # Generate bars
        bars = self._generate_bars(pair, timeframe, start, end)
        
        # Convert to DataFrame
        if not bars:
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        df = pd.DataFrame([b.to_dict() for b in bars])
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        
        return df
    
    def _generate_bars(
        self,
        pair: str,
        timeframe: str,
        start: datetime,
        end: datetime,
    ) -> list[SyntheticBar]:
        """
        Generate deterministic synthetic bars.
        
        Uses seeded RNG for reproducibility.
        """
        # Create deterministic seed from inputs
        seed_data = f"{self.seed_prefix}_{pair}_{timeframe}_{start.isoformat()}_{end.isoformat()}"
        seed = int(hashlib.sha256(seed_data.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        
        # Get interval and base price
        interval_minutes = TIMEFRAME_MINUTES[timeframe]
        interval = timedelta(minutes=interval_minutes)
        price = BASE_PRICES.get(pair, 1.0)
        
        bars = []
        current = start
        
        while current < end:
            # Deterministic price movement
            change = rng.gauss(0, self.volatility)
            price = max(price * 0.5, price + change)  # Prevent going negative
            
            # Generate OHLC
            high_offset = abs(rng.gauss(0, self.volatility * 0.5))
            low_offset = abs(rng.gauss(0, self.volatility * 0.5))
            close_offset = rng.gauss(0, self.volatility * 0.3)
            
            bar = SyntheticBar(
                timestamp=current,
                open=round(price, 5),
                high=round(price + high_offset, 5),
                low=round(price - low_offset, 5),
                close=round(price + close_offset, 5),
                volume=rng.randint(100, 10000),
            )
            bars.append(bar)
            
            current += interval
        
        return bars
    
    def get_latest_bar(self, pair: str, timeframe: str = "1H") -> dict | None:
        """
        Get the latest synthetic bar.
        
        Returns:
            Latest bar as dict, or None if no data
        """
        now = datetime.now(UTC)
        start = now - timedelta(hours=2)
        
        df = self.get_bars(pair, timeframe, start, now)
        
        if df.empty:
            return None
        
        return df.iloc[-1].to_dict()
    
    def get_staleness(self) -> float:
        """
        Get staleness in seconds (always 0 for synthetic).
        
        Real River can be stale; synthetic is always "fresh".
        """
        return 0.0


# =============================================================================
# FACTORY FUNCTION
# =============================================================================


def create_synthetic_river(
    volatility: float = 0.0010,
    seed_prefix: str = "phoenix",
) -> SyntheticRiver:
    """
    Create a synthetic river instance.
    
    Args:
        volatility: Price movement volatility
        seed_prefix: Prefix for deterministic seeding
        
    Returns:
        Configured SyntheticRiver instance
    """
    return SyntheticRiver(volatility=volatility, seed_prefix=seed_prefix)


# =============================================================================
# MAIN (for testing)
# =============================================================================


if __name__ == "__main__":
    # Demo usage
    river = SyntheticRiver()
    
    end = datetime.now(UTC)
    start = end - timedelta(days=1)
    
    for pair in ["EURUSD", "GBPUSD"]:
        print(f"\n{pair}:")
        df = river.get_bars(pair, "1H", start, end)
        print(f"  Bars: {len(df)}")
        print(f"  First: {df.iloc[0]['timestamp']}")
        print(f"  Last:  {df.iloc[-1]['timestamp']}")
        print(f"  Close range: {df['close'].min():.5f} - {df['close'].max():.5f}")
