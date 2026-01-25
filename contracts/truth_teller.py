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
  - Gap detection → gap_count increments
  - Latency detection → staleness_flag: TRUE
  - Sequence violation → sequence_error: TRUE
  - Spike detection → spike_flag: TRUE

CHAOS_VECTORS (v2 — BOAR audit):
  1. GAPS: missing bars (5-30 min)
  2. LATENCY: stale data (>60s behind)
  3. SPIKE: price spike (>50 pips)
  4. SEQUENCE: out-of-order timestamps
  5. CORRELATED: simultaneous chaos → escalation

HEALTH_STATES:
  HEALTHY: quality_score >= 0.95
  DEGRADED: 0.7 <= quality_score < 0.95
  CRITICAL: quality_score < 0.7
  HALT: unrecoverable or correlated chaos

INVARIANT:
  "Truth Teller is awake — lies cannot pass silently"
  "System degrades gracefully, never lies about health"
"""

import hashlib
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum


class HealthState(Enum):
    """System health states."""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"
    HALT = "HALT"


@dataclass
class IntegrityResult:
    """Result of integrity check."""
    is_valid: bool
    is_corrupted: bool
    anomaly_suspected: bool
    quality_score: float  # 0.0-1.0, <1.0 if any issues
    anomalies: List[Dict]
    message: str


@dataclass
class ChaosResult:
    """Result of chaos detection."""
    health_state: HealthState
    quality_score: float
    
    # Chaos vectors detected
    gaps_detected: int
    latency_detected: bool
    spikes_detected: int
    sequence_errors: int
    
    # Correlated chaos
    correlated_chaos: bool
    chaos_vectors_active: int
    
    # Recovery
    cycles_since_healthy: int
    recovery_possible: bool
    
    # Details
    anomalies: List[Dict]
    message: str
    
    # Thresholds used (for documentation)
    thresholds: Dict = field(default_factory=dict)


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


# =============================================================================
# CHAOS BUNNY — Chaos Detection Extension
# =============================================================================

class ChaosBunny:
    """
    Chaos detection and stress testing for Phoenix River.
    
    Implements SPRINT_26.TRACK_A.DAY_2 chaos vectors:
      1. GAPS: missing bars
      2. LATENCY: stale data
      3. SPIKE: price spikes
      4. SEQUENCE: out-of-order timestamps
      5. CORRELATED: simultaneous chaos
      7. RECOVERY_LAG: cycles to recover
    
    QUALITY_THRESHOLD_RATIONALE:
      - 0.95 (HEALTHY): Normal operation, all data valid
      - 0.90 (DEGRADED boundary): Minor gaps acceptable for non-critical ops
      - 0.70 (CRITICAL boundary): Significant data issues, block entries
      - Why not 0.9? We allow 5% tolerance for normal market gaps (weekends, maintenance)
      - Why 0.70 for CRITICAL? Below 70% means >30% data unusable, unacceptable for trading
    
    INVARIANT: "System degrades gracefully, never lies about health"
    """
    
    # Thresholds (documented per BOAR requirement)
    THRESHOLD_HEALTHY = 0.95  # >= this is HEALTHY
    THRESHOLD_DEGRADED = 0.70  # >= this but < HEALTHY is DEGRADED
    THRESHOLD_CRITICAL = 0.70  # < this is CRITICAL
    
    # Detection parameters
    GAP_THRESHOLD_MINUTES = 2  # > 2 min between bars = gap (1 min bars)
    LATENCY_THRESHOLD_SECONDS = 60  # > 60s behind = stale
    SPIKE_THRESHOLD_PIPS = 50  # > 50 pips = spike
    RECOVERY_MAX_CYCLES = 5  # Max cycles to recover
    
    def __init__(self):
        self.cycles_unhealthy = 0
        self.last_health_state = HealthState.HEALTHY
        
    def detect_chaos(
        self,
        df: pd.DataFrame,
        current_time: Optional[datetime] = None
    ) -> ChaosResult:
        """
        Run all chaos detection vectors.
        
        Returns comprehensive chaos analysis.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        anomalies = []
        
        # Vector 1: GAPS
        gap_anomalies, gap_count = self._detect_gaps(df)
        anomalies.extend(gap_anomalies)
        
        # Vector 2: LATENCY
        latency_anomalies, latency_detected = self._detect_latency(df, current_time)
        anomalies.extend(latency_anomalies)
        
        # Vector 3: SPIKE
        spike_anomalies, spike_count = self._detect_spikes(df)
        anomalies.extend(spike_anomalies)
        
        # Vector 4: SEQUENCE
        sequence_anomalies, sequence_errors = self._detect_sequence_errors(df)
        anomalies.extend(sequence_anomalies)
        
        # Calculate quality score
        total_bars = len(df)
        issues = gap_count + spike_count + sequence_errors + (1 if latency_detected else 0)
        quality_score = max(0.0, 1.0 - (issues / max(total_bars, 1)))
        
        # Determine health state
        chaos_vectors_active = sum([
            gap_count > 0,
            latency_detected,
            spike_count > 0,
            sequence_errors > 0
        ])
        
        # Vector 5: CORRELATED_CHAOS
        correlated_chaos = chaos_vectors_active >= 2
        
        if correlated_chaos:
            # Escalate: multiple simultaneous chaos vectors
            health_state = HealthState.HALT
            anomalies.append({
                'timestamp': str(current_time),
                'type': 'CORRELATED_CHAOS',
                'vectors_active': chaos_vectors_active,
                'detail': f"Multiple chaos vectors ({chaos_vectors_active}) detected simultaneously",
                'severity': 'CRITICAL'
            })
        elif quality_score >= self.THRESHOLD_HEALTHY:
            health_state = HealthState.HEALTHY
        elif quality_score >= self.THRESHOLD_DEGRADED:
            health_state = HealthState.DEGRADED
        else:
            health_state = HealthState.CRITICAL
        
        # Vector 7: RECOVERY_LAG
        if health_state == HealthState.HEALTHY:
            self.cycles_unhealthy = 0
        else:
            self.cycles_unhealthy += 1
        
        recovery_possible = self.cycles_unhealthy < self.RECOVERY_MAX_CYCLES
        
        if not recovery_possible and health_state != HealthState.HALT:
            health_state = HealthState.HALT
            anomalies.append({
                'timestamp': str(current_time),
                'type': 'RECOVERY_EXCEEDED',
                'cycles': self.cycles_unhealthy,
                'detail': f"Recovery exceeded {self.RECOVERY_MAX_CYCLES} cycles",
                'severity': 'CRITICAL'
            })
        
        # Generate message
        if health_state == HealthState.HEALTHY:
            message = "HEALTHY: All chaos vectors clear"
        elif health_state == HealthState.DEGRADED:
            message = f"DEGRADED: {chaos_vectors_active} chaos vector(s) active, quality={quality_score:.3f}"
        elif health_state == HealthState.CRITICAL:
            message = f"CRITICAL: quality={quality_score:.3f} below threshold"
        else:
            message = f"HALT: {len([a for a in anomalies if a['severity'] == 'CRITICAL'])} critical issues"
        
        self.last_health_state = health_state
        
        return ChaosResult(
            health_state=health_state,
            quality_score=quality_score,
            gaps_detected=gap_count,
            latency_detected=latency_detected,
            spikes_detected=spike_count,
            sequence_errors=sequence_errors,
            correlated_chaos=correlated_chaos,
            chaos_vectors_active=chaos_vectors_active,
            cycles_since_healthy=self.cycles_unhealthy,
            recovery_possible=recovery_possible,
            anomalies=anomalies,
            message=message,
            thresholds={
                'healthy': self.THRESHOLD_HEALTHY,
                'degraded': self.THRESHOLD_DEGRADED,
                'critical': self.THRESHOLD_CRITICAL,
                'gap_minutes': self.GAP_THRESHOLD_MINUTES,
                'latency_seconds': self.LATENCY_THRESHOLD_SECONDS,
                'spike_pips': self.SPIKE_THRESHOLD_PIPS,
                'recovery_max_cycles': self.RECOVERY_MAX_CYCLES,
                'rationale': {
                    'healthy_0.95': 'Normal operation, 5% tolerance for market gaps',
                    'degraded_0.70': '30% issue threshold — beyond this, entries blocked',
                    'spike_50_pips': 'Single-bar 50+ pip move rare outside news — flag for review'
                }
            }
        )
    
    def _detect_gaps(self, df: pd.DataFrame) -> Tuple[List[Dict], int]:
        """
        Vector 1: Detect missing bars (gaps).
        
        A gap is when time between consecutive bars > expected interval.
        For 1-minute bars: gap > 2 minutes (allowing 1 min tolerance)
        """
        anomalies = []
        gap_count = 0
        
        if len(df) < 2:
            return anomalies, gap_count
        
        # Ensure timestamp column
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], utc=True)
        else:
            timestamps = pd.to_datetime(df.index, utc=True)
        
        # Calculate time differences
        time_diffs = timestamps.diff()
        gap_threshold = timedelta(minutes=self.GAP_THRESHOLD_MINUTES)
        
        # Find gaps
        gaps = time_diffs[time_diffs > gap_threshold]
        
        for idx in gaps.index:
            gap_minutes = gaps[idx].total_seconds() / 60
            ts = timestamps[idx]
            
            anomalies.append({
                'timestamp': str(ts),
                'type': 'GAP_DETECTED',
                'gap_minutes': gap_minutes,
                'detail': f"Gap of {gap_minutes:.1f} minutes detected",
                'severity': 'WARNING'
            })
            gap_count += 1
        
        return anomalies, gap_count
    
    def _detect_latency(
        self,
        df: pd.DataFrame,
        current_time: datetime
    ) -> Tuple[List[Dict], bool]:
        """
        Vector 2: Detect stale data (latency).
        
        Data is stale if most recent timestamp > threshold behind current time.
        """
        anomalies = []
        latency_detected = False
        
        if len(df) == 0:
            return anomalies, True  # Empty data is stale
        
        # Get most recent timestamp
        if 'timestamp' in df.columns:
            latest_ts = pd.to_datetime(df['timestamp'].max(), utc=True)
        else:
            latest_ts = pd.to_datetime(df.index.max(), utc=True)
        
        # Calculate staleness
        staleness = (current_time - latest_ts).total_seconds()
        
        if staleness > self.LATENCY_THRESHOLD_SECONDS:
            latency_detected = True
            anomalies.append({
                'timestamp': str(current_time),
                'type': 'LATENCY_DETECTED',
                'staleness_seconds': staleness,
                'latest_data': str(latest_ts),
                'detail': f"Data is {staleness:.0f}s behind current time",
                'severity': 'CRITICAL'
            })
        
        return anomalies, latency_detected
    
    def _detect_spikes(self, df: pd.DataFrame) -> Tuple[List[Dict], int]:
        """
        Vector 3: Detect price spikes.
        
        A spike is a single-bar move > threshold pips.
        """
        anomalies = []
        spike_count = 0
        
        if len(df) < 2:
            return anomalies, spike_count
        
        # Calculate bar-to-bar changes in pips
        pip_value = 0.0001  # For 4-decimal pairs
        changes_pips = df['close'].diff().abs() / pip_value
        
        # Find spikes
        spikes = changes_pips[changes_pips > self.SPIKE_THRESHOLD_PIPS]
        
        for idx in spikes.index:
            ts = df.loc[idx, 'timestamp'] if 'timestamp' in df.columns else idx
            
            anomalies.append({
                'timestamp': str(ts),
                'type': 'SPIKE_DETECTED',
                'spike_pips': spikes[idx],
                'detail': f"Price spike of {spikes[idx]:.1f} pips detected",
                'severity': 'WARNING'
            })
            spike_count += 1
        
        return anomalies, spike_count
    
    def _detect_sequence_errors(self, df: pd.DataFrame) -> Tuple[List[Dict], int]:
        """
        Vector 4: Detect out-of-order timestamps.
        
        ZERO_TOLERANCE: Any out-of-order timestamp is a sequence error.
        """
        anomalies = []
        sequence_errors = 0
        
        if len(df) < 2:
            return anomalies, sequence_errors
        
        # Get timestamps
        if 'timestamp' in df.columns:
            timestamps = pd.to_datetime(df['timestamp'], utc=True)
        else:
            timestamps = pd.to_datetime(df.index, utc=True)
        
        # Check monotonicity
        diffs = timestamps.diff()
        out_of_order = diffs[diffs < timedelta(0)]
        
        for idx in out_of_order.index:
            ts = timestamps[idx]
            prev_ts = timestamps[idx - 1] if idx > 0 else None
            
            anomalies.append({
                'timestamp': str(ts),
                'type': 'SEQUENCE_ERROR',
                'current': str(ts),
                'previous': str(prev_ts),
                'detail': f"Out-of-order: {ts} comes after {prev_ts}",
                'severity': 'CRITICAL'
            })
            sequence_errors += 1
        
        return anomalies, sequence_errors
    
    # =========================================================================
    # CHAOS INJECTION (for testing)
    # =========================================================================
    
    def inject_gaps(
        self,
        df: pd.DataFrame,
        gap_positions: List[int],
        gap_duration_minutes: int = 15
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Inject gaps by removing bars.
        
        Args:
            df: Original DataFrame
            gap_positions: Bar indices where gaps start
            gap_duration_minutes: Duration of each gap
            
        Returns:
            - DataFrame with gaps
            - Injection metadata
        """
        df = df.copy()
        
        # Calculate bars to remove per gap
        bars_per_gap = gap_duration_minutes  # 1-minute bars
        
        indices_to_drop = []
        for pos in gap_positions:
            indices_to_drop.extend(range(pos, min(pos + bars_per_gap, len(df))))
        
        # Remove duplicates and sort
        indices_to_drop = sorted(set(indices_to_drop))
        
        # Drop bars
        df_gapped = df.drop(df.index[indices_to_drop]).reset_index(drop=True)
        
        return df_gapped, {
            'type': 'GAP_INJECTION',
            'positions': gap_positions,
            'duration_minutes': gap_duration_minutes,
            'bars_removed': len(indices_to_drop)
        }
    
    def inject_latency(
        self,
        df: pd.DataFrame,
        shift_seconds: int = 120
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Inject latency by shifting timestamps backward.
        
        Makes data appear stale.
        """
        df = df.copy()
        
        # Shift timestamps backward
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']) - timedelta(seconds=shift_seconds)
        else:
            df.index = df.index - timedelta(seconds=shift_seconds)
        
        return df, {
            'type': 'LATENCY_INJECTION',
            'shift_seconds': shift_seconds
        }
    
    def inject_spike(
        self,
        df: pd.DataFrame,
        bar_index: int,
        spike_pips: float = 50.0
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Inject price spike on a single bar.
        """
        df = df.copy()
        
        pip_value = 0.0001
        original_close = df.iloc[bar_index]['close']
        
        # Inject spike
        df.iloc[bar_index, df.columns.get_loc('close')] = original_close + (spike_pips * pip_value)
        
        # Also adjust high if needed
        if df.iloc[bar_index]['close'] > df.iloc[bar_index]['high']:
            df.iloc[bar_index, df.columns.get_loc('high')] = df.iloc[bar_index]['close']
        
        return df, {
            'type': 'SPIKE_INJECTION',
            'bar_index': bar_index,
            'spike_pips': spike_pips,
            'original_close': original_close,
            'spiked_close': df.iloc[bar_index]['close']
        }
    
    def inject_sequence_error(
        self,
        df: pd.DataFrame,
        swap_indices: Tuple[int, int]
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Inject sequence error by swapping timestamps.
        """
        df = df.copy()
        i, j = swap_indices
        
        if 'timestamp' in df.columns:
            ts_i = df.iloc[i]['timestamp']
            ts_j = df.iloc[j]['timestamp']
            df.iloc[i, df.columns.get_loc('timestamp')] = ts_j
            df.iloc[j, df.columns.get_loc('timestamp')] = ts_i
        
        return df, {
            'type': 'SEQUENCE_INJECTION',
            'swapped_indices': swap_indices
        }
    
    def inject_correlated_chaos(
        self,
        df: pd.DataFrame,
        current_time: datetime
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Inject multiple chaos vectors simultaneously.
        
        Vector 5: CORRELATED_CHAOS
        """
        # Start with gaps
        df_chaos, gap_meta = self.inject_gaps(
            df,
            gap_positions=[len(df) // 3],
            gap_duration_minutes=10
        )
        
        # Add spike
        df_chaos, spike_meta = self.inject_spike(
            df_chaos,
            bar_index=len(df_chaos) // 2,
            spike_pips=60.0
        )
        
        # Add latency
        df_chaos, latency_meta = self.inject_latency(
            df_chaos,
            shift_seconds=120
        )
        
        return df_chaos, {
            'type': 'CORRELATED_CHAOS_INJECTION',
            'vectors': ['GAP', 'SPIKE', 'LATENCY'],
            'gap_meta': gap_meta,
            'spike_meta': spike_meta,
            'latency_meta': latency_meta
        }
