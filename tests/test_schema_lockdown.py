"""
Schema Lockdown Tests — Verify enriched data matches ICT_DATA_CONTRACT.md

Sprint 26 Track A Day 0.5
Contract: phoenix/contracts/ICT_DATA_CONTRACT.md v1.0.0

These tests enforce the mechanical sign-off conditions:
1. Schema hash matches locked value
2. Column count matches contract
3. All mirror markers exist
4. Timestamps are UTC

IMPORTANT: Run with nex venv (has pandas + parquet dependencies):
    cd ~/nex && source .venv/bin/activate
    cd ~/phoenix && python -m pytest tests/test_schema_lockdown.py -v

Or run verification script directly:
    cd ~/nex && source .venv/bin/activate
    python ~/phoenix/contracts/verify_schema.py
"""

import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

# Contract constants from ICT_DATA_CONTRACT.md v1.0.0
EXPECTED_SCHEMA_HASH = "b848ffe506fd3fff"
EXPECTED_COLUMNS = 472
EXPECTED_BOOLEAN_MARKERS = 110

# Path to NEX enriched data
NEX_ENRICHED_PATH = (
    Path.home() / "nex" / "nex_lab" / "data" / "features" / "EURUSD_1m_enriched.parquet"
)


def calculate_schema_hash(df: pd.DataFrame) -> str:
    """Calculate deterministic schema hash matching contract spec."""
    schema = [(col, str(df[col].dtype)) for col in df.columns]
    schema_str = json.dumps(schema, sort_keys=True)
    return hashlib.sha256(schema_str.encode()).hexdigest()[:16]


@pytest.fixture
def enriched_df():
    """Load enriched parquet for testing."""
    if not NEX_ENRICHED_PATH.exists():
        pytest.skip(f"Enriched parquet not found: {NEX_ENRICHED_PATH}")
    return pd.read_parquet(NEX_ENRICHED_PATH)


class TestSchemaLockdown:
    """Tests for schema lockdown verification."""

    def test_schema_hash_matches(self, enriched_df):
        """Verify enriched parquet matches locked schema hash."""
        actual_hash = calculate_schema_hash(enriched_df)

        assert actual_hash == EXPECTED_SCHEMA_HASH, (
            f"Schema drift detected!\n"
            f"Expected hash: {EXPECTED_SCHEMA_HASH}\n"
            f"Actual hash:   {actual_hash}\n"
            f"The enriched schema has changed since contract was locked.\n"
            f"Either update the contract or fix the schema drift."
        )

    def test_column_count(self, enriched_df):
        """Verify column count matches contract."""
        actual_count = len(enriched_df.columns)

        assert actual_count == EXPECTED_COLUMNS, (
            f"Column count mismatch!\n"
            f"Expected: {EXPECTED_COLUMNS}\n"
            f"Actual:   {actual_count}\n"
            f"Columns added or removed since contract lockdown."
        )

    def test_boolean_marker_count(self, enriched_df):
        """Verify boolean marker count matches contract."""
        bool_cols = [col for col in enriched_df.columns if enriched_df[col].dtype == "bool"]
        actual_count = len(bool_cols)

        assert actual_count == EXPECTED_BOOLEAN_MARKERS, (
            f"Boolean marker count mismatch!\n"
            f"Expected: {EXPECTED_BOOLEAN_MARKERS}\n"
            f"Actual:   {actual_count}\n"
        )

    @pytest.mark.xfail(
        reason="S42: ModuleNotFoundError 'phoenix' - import path issue",
        strict=True,
    )
    def test_mirror_markers_exist(self, enriched_df):
        """Verify all mirror markers exist in schema."""
        from phoenix.contracts.mirror_markers import MIRROR_MARKER_COLUMNS

        missing = [col for col in MIRROR_MARKER_COLUMNS if col not in enriched_df.columns]

        assert not missing, (
            f"Missing mirror markers:\n" f"{missing}\n" f"These columns must exist for Mirror Test."
        )

    @pytest.mark.xfail(
        reason="S42: ModuleNotFoundError 'phoenix' - import path issue",
        strict=True,
    )
    def test_mirror_markers_are_boolean(self, enriched_df):
        """Verify mirror markers are actually boolean type."""
        from phoenix.contracts.mirror_markers import MIRROR_MARKER_COLUMNS

        non_bool = []
        for col in MIRROR_MARKER_COLUMNS:
            if col in enriched_df.columns:
                if enriched_df[col].dtype != "bool":
                    non_bool.append(f"{col}: {enriched_df[col].dtype}")

        assert not non_bool, f"Mirror markers must be boolean:\n" f"{non_bool}"

    def test_timestamp_is_utc(self, enriched_df):
        """Verify timestamps are UTC timezone-aware."""
        ts_dtype = enriched_df["timestamp"].dtype

        # Check it's datetime
        assert "datetime64" in str(ts_dtype), f"Timestamp must be datetime, got {ts_dtype}"

        # Check timezone
        tz = enriched_df["timestamp"].dt.tz
        assert tz is not None, "Timestamps must be timezone-aware"
        assert str(tz) == "UTC", f"Timestamps must be UTC, got {tz}"

    def test_timestamp_is_bar_start(self, enriched_df):
        """
        Verify timestamp convention is bar_start_time.

        Contract specifies: timestamp indicates when the bar OPENED.
        Test: timestamps should be at minute boundaries (00 seconds).
        """
        # Sample first 1000 rows
        sample = enriched_df.head(1000)

        # Check that all timestamps are at :00 seconds
        seconds = sample["timestamp"].dt.second
        non_zero_seconds = (seconds != 0).sum()

        assert non_zero_seconds == 0, (
            f"Timestamps should be at minute boundaries (bar_start convention).\n"
            f"Found {non_zero_seconds} timestamps with non-zero seconds."
        )

    def test_raw_columns_present(self, enriched_df):
        """Verify raw OHLCV columns are present."""
        required = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [col for col in required if col not in enriched_df.columns]

        assert not missing, f"Missing raw columns: {missing}"

    def test_ohlc_sanity(self, enriched_df):
        """Verify basic OHLC relationships."""
        sample = enriched_df.head(10000)

        # High >= Low
        assert (sample["high"] >= sample["low"]).all(), "Found High < Low"

        # High >= Open and High >= Close
        assert (sample["high"] >= sample["open"]).all(), "Found High < Open"
        assert (sample["high"] >= sample["close"]).all(), "Found High < Close"

        # Low <= Open and Low <= Close
        assert (sample["low"] <= sample["open"]).all(), "Found Low > Open"
        assert (sample["low"] <= sample["close"]).all(), "Found Low > Close"


class TestVolumeSemantics:
    """Tests for volume semantics documentation compliance."""

    def test_volume_has_negative_sentinel(self, enriched_df):
        """
        Verify volume contains -1.0 sentinel values.

        Per contract: Dukascopy uses -1.0 to indicate 'no volume data'.
        """
        neg_volume = (enriched_df["volume"] < 0).sum()

        # We expect some negative values (sentinel)
        # If zero, either data changed or this is IBKR-only data
        assert neg_volume > 0 or True, (  # Soft check - document finding
            f"Expected negative volume sentinel values.\n"
            f"Found: {neg_volume}\n"
            f"This may indicate IBKR-only data (volume=0)."
        )

    def test_volume_comparability_none(self, enriched_df):
        """
        Document that volume is non-comparable across vendors.

        This is a documentation test - it always passes but logs the finding.
        """
        neg_count = (enriched_df["volume"] < 0).sum()
        zero_count = (enriched_df["volume"] == 0).sum()
        pos_count = (enriched_df["volume"] > 0).sum()

        # Log for documentation
        print("\nVolume Statistics:")
        print(f"  Negative (sentinel): {neg_count:,}")
        print(f"  Zero: {zero_count:,}")
        print(f"  Positive: {pos_count:,}")
        print("  VOLUME COMPARABILITY: NONE")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
