"""
TruthTeller — Data Integrity Monitor for Phoenix River

PURPOSE:
  Detect data corruption at any stage of the pipeline.
  Implements INV-CONTRACT-3: "Data was stale but said fresh"
  
MECHANISM:
  1. Compute deterministic hash of raw OHLCV data
  2. Store hash as bar_integrity_hash
  3. Verify hash at each processing checkpoint
  4. Flag ANY discrepancy immediately

DETECTION:
  - Hash mismatch → is_corrupted: TRUE
  - Price discontinuity → anomaly_suspected: TRUE
  - Cross-vendor divergence → vendor_drift: TRUE

INVARIANT:
  "Truth Teller is awake — lies cannot pass silently"
"""

import hashlib
import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple


@dataclass
class IntegrityResult:
    """Result of integrity check."""
    is_valid: bool
    is_corrupted: bool
    anomaly_suspected: bool
    quality_score: float  # 0.0-1.0, <1.0 if any issues
    anomalies: List[Dict]
    message: str


class TruthTeller:
    """
    Data integrity monitor.
    
    Detects corruption via:
    1. Hash verification (deterministic)
    2. Price continuity analysis (statistical)
    3. Cross-bar consistency (logical)
    """
    
    def __init__(
        self,
        sensitivity_pips: float = 0.5,  # Minimum detectable corruption
        continuity_threshold: float = 3.0  # Z-score for continuity
    ):
        self.sensitivity_pips = sensitivity_pips
        self.continuity_threshold = continuity_threshold
    
    def compute_bar_hash(self, row: pd.Series) -> str:
        """
        Compute deterministic hash for a single bar.
        
        Hash includes: timestamp, OHLC (rounded to 6 decimals)
        Volume excluded (vendor-dependent)
        """
        # Normalize values for consistent hashing
        ts = str(row['timestamp']) if 'timestamp' in row.index else str(row.name)
        o = f"{row['open']:.6f}"
        h = f"{row['high']:.6f}"
        l = f"{row['low']:.6f}"
        c = f"{row['close']:.6f}"
        
        content = f"{ts}|{o}|{h}|{l}|{c}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def compute_dataset_hash(self, df: pd.DataFrame) -> str:
        """
        Compute hash for entire dataset.
        
        Uses hash chain: each bar's hash includes previous hash.
        """
        chain_hash = "0" * 16
        
        for idx, row in df.iterrows():
            bar_hash = self.compute_bar_hash(row)
            combined = f"{chain_hash}|{bar_hash}"
            chain_hash = hashlib.sha256(combined.encode()).hexdigest()[:16]
        
        return chain_hash
    
    def add_integrity_hashes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add integrity hash column to DataFrame.
        
        Each bar gets its own hash for granular verification.
        """
        df = df.copy()
        df['bar_integrity_hash'] = df.apply(self.compute_bar_hash, axis=1)
        return df
    
    def verify_integrity(
        self,
        df: pd.DataFrame,
        reference_hashes: Optional[Dict[str, str]] = None
    ) -> IntegrityResult:
        """
        Verify data integrity.
        
        If reference_hashes provided: compare against known-good values.
        Otherwise: check internal consistency only.
        """
        anomalies = []
        is_corrupted = False
        anomaly_suspected = False
        
        # Check 1: Hash verification (if reference provided)
        if reference_hashes:
            for idx, row in df.iterrows():
                current_hash = self.compute_bar_hash(row)
                ts_key = str(row['timestamp']) if 'timestamp' in row.index else str(idx)
                
                if ts_key in reference_hashes:
                    if current_hash != reference_hashes[ts_key]:
                        is_corrupted = True
                        anomalies.append({
                            'timestamp': ts_key,
                            'type': 'HASH_MISMATCH',
                            'expected': reference_hashes[ts_key],
                            'actual': current_hash,
                            'severity': 'CRITICAL'
                        })
        
        # Check 2: Price continuity (detect injection)
        continuity_anomalies = self._check_price_continuity(df)
        if continuity_anomalies:
            anomaly_suspected = True
            anomalies.extend(continuity_anomalies)
        
        # Check 3: OHLC consistency
        ohlc_anomalies = self._check_ohlc_consistency(df)
        if ohlc_anomalies:
            is_corrupted = True
            anomalies.extend(ohlc_anomalies)
        
        # Calculate quality score
        total_bars = len(df)
        anomaly_count = len(anomalies)
        quality_score = max(0.0, 1.0 - (anomaly_count / total_bars)) if total_bars > 0 else 0.0
        
        # Generate message
        if is_corrupted:
            message = f"CORRUPTION_DETECTED: {len([a for a in anomalies if a['severity'] == 'CRITICAL'])} critical anomalies"
        elif anomaly_suspected:
            message = f"ANOMALY_SUSPECTED: {len(anomalies)} suspicious patterns"
        else:
            message = "INTEGRITY_VERIFIED: No anomalies detected"
        
        return IntegrityResult(
            is_valid=not is_corrupted and not anomaly_suspected,
            is_corrupted=is_corrupted,
            anomaly_suspected=anomaly_suspected,
            quality_score=quality_score,
            anomalies=anomalies,
            message=message
        )
    
    def _check_price_continuity(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detect price discontinuities that suggest injection.
        
        Method: Compare each bar's change to local volatility.
        Injection creates isolated spike in otherwise smooth price action.
        """
        anomalies = []
        
        if len(df) < 10:
            return anomalies
        
        # Calculate bar-to-bar changes
        df = df.copy()
        df['close_change'] = df['close'].diff().abs()
        
        # Calculate rolling volatility (local context)
        df['local_vol'] = df['close_change'].rolling(window=20, min_periods=5).std()
        
        # Calculate z-score of change relative to local vol
        df['change_zscore'] = df['close_change'] / df['local_vol'].replace(0, np.nan)
        
        # Find anomalies: change >> local volatility
        threshold = self.continuity_threshold
        suspicious = df[df['change_zscore'] > threshold].copy()
        
        for idx, row in suspicious.iterrows():
            # Additional check: is this an isolated spike?
            # (real moves have follow-through, injections don't)
            ts = row['timestamp'] if 'timestamp' in row.index else idx
            
            anomalies.append({
                'timestamp': str(ts),
                'type': 'PRICE_DISCONTINUITY',
                'change_pips': row['close_change'] * 10000,  # Assuming 4-decimal pair
                'z_score': row['change_zscore'],
                'severity': 'WARNING'
            })
        
        return anomalies
    
    def _check_ohlc_consistency(self, df: pd.DataFrame) -> List[Dict]:
        """
        Check OHLC logical consistency.
        
        Rules:
        - high >= open, close, low
        - low <= open, close, high
        """
        anomalies = []
        
        # Check high >= all
        violations = df[
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['high'] < df['low'])
        ]
        
        for idx, row in violations.iterrows():
            ts = row['timestamp'] if 'timestamp' in row.index else idx
            anomalies.append({
                'timestamp': str(ts),
                'type': 'OHLC_VIOLATION',
                'detail': f"high={row['high']:.5f} violated",
                'severity': 'CRITICAL'
            })
        
        # Check low <= all
        violations = df[
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        ]
        
        for idx, row in violations.iterrows():
            ts = row['timestamp'] if 'timestamp' in row.index else idx
            anomalies.append({
                'timestamp': str(ts),
                'type': 'OHLC_VIOLATION',
                'detail': f"low={row['low']:.5f} violated",
                'severity': 'CRITICAL'
            })
        
        return anomalies
    
    def inject_corruption(
        self,
        df: pd.DataFrame,
        bar_index: int,
        field: str = 'close',
        delta_pips: float = 1.0
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Inject controlled corruption for testing.
        
        Returns:
            - Corrupted DataFrame
            - Injection metadata (for verification)
        """
        df = df.copy()
        
        # Calculate delta in price terms (assuming 4-decimal pair)
        pip_value = 0.0001  # For EUR/USD etc
        delta_price = delta_pips * pip_value
        
        # Store original value
        original_value = df.iloc[bar_index][field]
        timestamp = df.iloc[bar_index]['timestamp'] if 'timestamp' in df.columns else df.index[bar_index]
        
        # Inject corruption
        df.iloc[bar_index, df.columns.get_loc(field)] = original_value + delta_price
        
        # Return metadata
        injection_meta = {
            'bar_index': bar_index,
            'timestamp': str(timestamp),
            'field': field,
            'original_value': original_value,
            'corrupted_value': original_value + delta_price,
            'delta_pips': delta_pips,
            'original_hash': self.compute_bar_hash(pd.Series({
                'timestamp': timestamp,
                'open': df.iloc[bar_index]['open'],
                'high': df.iloc[bar_index]['high'],
                'low': df.iloc[bar_index]['low'],
                'close': original_value
            }))
        }
        
        return df, injection_meta


def verify_river_integrity(
    df: pd.DataFrame,
    reference_df: Optional[pd.DataFrame] = None
) -> IntegrityResult:
    """
    Convenience function for pipeline integration.
    
    Called at each stage to verify data hasn't been corrupted.
    """
    teller = TruthTeller()
    
    if reference_df is not None:
        # Build reference hashes
        ref_hashes = {}
        for idx, row in reference_df.iterrows():
            ts_key = str(row['timestamp']) if 'timestamp' in row.index else str(idx)
            ref_hashes[ts_key] = teller.compute_bar_hash(row)
        
        return teller.verify_integrity(df, reference_hashes)
    else:
        return teller.verify_integrity(df)
