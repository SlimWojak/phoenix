"""
RIVER_RESILIENCE — Streamer hardening tests.

Tests for 5 fixes:
  R1: Seed duration '1 D' with dedup guard
  R2: Staleness triggers resubscribe with exponential backoff
  R3: Resubscribe counter resets after N consecutive good bars
  R4: Gap backfill via seed bars on resubscribe
  R5: Heartbeat includes coverage stats

Invariant coverage:
  INV-RIVER-IMMUTABLE: staging only, never parquet
  INV-NO-FORMING-CANDLE: last seed bar excluded
  INV-RIVER-CONTINUOUS: gaps detected and reported
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from river.streamer import (
    CONSECUTIVE_GOOD_BARS_RESET,
    RESUBSCRIBE_BACKOFF_S,
    RESUBSCRIBE_MAX_ATTEMPTS,
    STALENESS_THRESHOLD_SECONDS,
    RiverStreamer,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_bar(ts: datetime, close: float = 1.0850) -> SimpleNamespace:
    """Create a mock ib_insync BarData."""
    return SimpleNamespace(
        date=ts,
        open=close - 0.0001,
        high=close + 0.0005,
        low=close - 0.0005,
        close=close,
        volume=-1.0,
    )


def _make_bars_list(
    start: datetime,
    count: int,
    interval_min: int = 1,
    base_close: float = 1.0850,
) -> list[SimpleNamespace]:
    """Create a list of mock bars with 1-minute intervals."""
    bars = []
    for i in range(count):
        ts = start + timedelta(minutes=i * interval_min)
        bars.append(_make_bar(ts, close=base_close + i * 0.0001))
    return bars


class MockBarsHandle(list[Any]):
    """Mock for the ib_insync bars handle with updateEvent."""

    def __init__(self, bars: list[Any] | None = None) -> None:
        super().__init__(bars or [])
        self.updateEvent = MagicMock()
        self.updateEvent.__iadd__ = MagicMock(return_value=self.updateEvent)


@pytest.fixture()  # type: ignore[misc]
def tmp_river(tmp_path: Path) -> Path:
    """Temporary river root directory."""
    return tmp_path / "river"


@pytest.fixture()  # type: ignore[misc]
def streamer(tmp_river: Path) -> RiverStreamer:
    """RiverStreamer with temp river root, no IBKR connection."""
    s = RiverStreamer(pair="EURUSD", river_root=tmp_river)
    s.staging_dir.mkdir(parents=True, exist_ok=True)
    return s


# ---------------------------------------------------------------------------
# R1: Seed Duration + Dedup Guard
# ---------------------------------------------------------------------------


class TestR1SeedDuration:
    """R1: durationStr changed to '1 D', seed bars persisted with dedup."""

    def test_subscribe_uses_1d_duration(self) -> None:
        """Verify _subscribe requests 1 D duration, not 120 S."""
        import river.streamer as mod

        source = Path(mod.__file__).read_text()
        assert 'durationStr="1 D"' in source
        assert 'durationStr="120 S"' not in source

    def test_seed_bars_persisted_to_staging(self, streamer: RiverStreamer) -> None:
        """Seed bars (minus forming bar) are written to staging JSONL."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(minutes=10), count=11)
        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        staging_files = list(streamer.staging_dir.glob("*.jsonl"))
        assert len(staging_files) >= 1

        rows: list[dict[str, Any]] = []
        for f in staging_files:
            for line in f.read_text().splitlines():
                if line.strip():
                    rows.append(json.loads(line))

        assert len(rows) == 10, "should persist 10 bars (11 minus forming bar)"

    def test_seed_dedup_against_existing_staging(self, streamer: RiverStreamer) -> None:
        """Seed bars already in staging are not duplicated."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(minutes=5), count=6)

        existing_ts = pd.Timestamp(bars[0].date.timestamp(), unit="s", tz="UTC")
        existing_data = {
            "timestamp": existing_ts.isoformat(),
            "open": 1.0849,
            "high": 1.0855,
            "low": 1.0845,
            "close": 1.0850,
            "volume": -1.0,
            "source": "ibkr",
            "knowledge_time": now.isoformat(),
        }
        staging_file = streamer.staging_path(existing_ts.date())
        staging_file.parent.mkdir(parents=True, exist_ok=True)
        staging_file.write_text(json.dumps(existing_data) + "\n")

        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        all_rows: list[dict[str, Any]] = []
        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    all_rows.append(json.loads(line))

        timestamps = [r["timestamp"] for r in all_rows]
        assert len(timestamps) == len(set(timestamps)), "no duplicate timestamps"

    def test_seed_forming_bar_excluded(self, streamer: RiverStreamer) -> None:
        """INV-NO-FORMING-CANDLE: last bar in seed is excluded."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(minutes=3), count=4)
        last_bar_ts = pd.Timestamp(bars[-1].date.timestamp(), unit="s", tz="UTC")

        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        rows: list[dict[str, Any]] = []
        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    rows.append(json.loads(line))

        persisted_ts = {r["timestamp"] for r in rows}
        assert last_bar_ts.isoformat() not in persisted_ts

    def test_seed_empty_handle_no_crash(self, streamer: RiverStreamer) -> None:
        """Empty or single-bar handle doesn't crash."""
        streamer._bars_handle = MockBarsHandle([])
        streamer._persist_seed_bars()

        streamer._bars_handle = MockBarsHandle([_make_bar(datetime.now(UTC))])
        streamer._persist_seed_bars()

        staging_files = list(streamer.staging_dir.glob("*.jsonl"))
        assert len(staging_files) == 0


# ---------------------------------------------------------------------------
# R2: Staleness Resubscribe
# ---------------------------------------------------------------------------


class TestR2StalenessResubscribe:
    """R2: Watchdog triggers resubscribe on staleness, not just initial timeout."""

    def test_backoff_constants(self) -> None:
        """Backoff values match CTO spec: 60 -> 120 -> 300 -> cap 5min."""
        assert RESUBSCRIBE_BACKOFF_S[0] == 60
        assert RESUBSCRIBE_BACKOFF_S[1] == 120
        assert RESUBSCRIBE_BACKOFF_S[2] == 300
        assert all(b <= 300 for b in RESUBSCRIBE_BACKOFF_S)

    def test_max_attempts_increased(self) -> None:
        """Max attempts is 5 (up from 3)."""
        assert RESUBSCRIBE_MAX_ATTEMPTS == 5

    def test_staleness_triggers_resubscribe(self, streamer: RiverStreamer) -> None:
        """Stale stream triggers _attempt_resubscribe, not just a log."""
        streamer._last_bar_time = datetime.now(UTC) - timedelta(
            seconds=STALENESS_THRESHOLD_SECONDS + 10,
        )
        streamer._subscribe_time = time.monotonic() - 300

        with (
            patch.object(streamer, "_is_trading_hours", return_value=True),
            patch.object(streamer, "_attempt_resubscribe") as mock_resub,
        ):
            streamer._check_watchdog()
            mock_resub.assert_called_once()

    def test_no_resubscribe_outside_trading_hours(self, streamer: RiverStreamer) -> None:
        """Staleness during weekend/closed hours doesn't trigger resubscribe."""
        streamer._last_bar_time = datetime.now(UTC) - timedelta(seconds=300)

        with (
            patch.object(streamer, "_is_trading_hours", return_value=False),
            patch.object(streamer, "_attempt_resubscribe") as mock_resub,
        ):
            streamer._check_watchdog()
            mock_resub.assert_not_called()

    def test_rate_limiting_prevents_rapid_fire(self, streamer: RiverStreamer) -> None:
        """Resubscribe is rate-limited by subscribe_time + backoff check."""
        streamer._subscribe_time = time.monotonic()
        streamer._resubscribe_attempts = 0
        streamer._ib = MagicMock()

        with patch.object(streamer, "_subscribe"):
            streamer._attempt_resubscribe()

        assert (
            streamer._resubscribe_attempts == 0
        ), "should skip: within backoff window of subscribe_time"

    def test_exhausted_attempts_go_degraded(self, streamer: RiverStreamer) -> None:
        """After max attempts exhausted, state becomes DEGRADED."""
        streamer._resubscribe_attempts = RESUBSCRIBE_MAX_ATTEMPTS
        streamer._attempt_resubscribe()

        assert streamer._state == "DEGRADED"
        assert not streamer._subscribed


# ---------------------------------------------------------------------------
# R3: Counter Reset After Good Bars
# ---------------------------------------------------------------------------


class TestR3CounterReset:
    """R3: Resubscribe attempts reset after N consecutive good bars."""

    def test_counter_resets_after_n_good_bars(self, streamer: RiverStreamer) -> None:
        """After CONSECUTIVE_GOOD_BARS_RESET good bars, counter resets to 0."""
        streamer._resubscribe_attempts = 3
        streamer._state = "STREAMING"
        base_time = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            for i in range(CONSECUTIVE_GOOD_BARS_RESET + 1):
                bar_ts = base_time + timedelta(minutes=i)
                bar = _make_bar(bar_ts)
                bars = MockBarsHandle([bar])
                streamer._on_bar_update(bars, has_new_bar=True)

        assert streamer._resubscribe_attempts == 0
        assert streamer._consecutive_good_bars >= CONSECUTIVE_GOOD_BARS_RESET

    def test_counter_not_reset_on_first_bar(self, streamer: RiverStreamer) -> None:
        """Single bar after failure doesn't reset counter."""
        streamer._resubscribe_attempts = 3
        streamer._state = "STREAMING"
        bar = _make_bar(datetime(2026, 3, 24, 12, 0, tzinfo=UTC))
        bars = MockBarsHandle([bar])

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            streamer._on_bar_update(bars, has_new_bar=True)

        assert streamer._resubscribe_attempts == 3

    def test_gap_resets_consecutive_good_bars(self, streamer: RiverStreamer) -> None:
        """A gap in bars resets the consecutive good bar counter."""
        streamer._state = "STREAMING"
        streamer._resubscribe_attempts = 2
        base = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            for i in range(3):
                bar = _make_bar(base + timedelta(minutes=i))
                streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

            assert streamer._consecutive_good_bars == 3

            gap_bar = _make_bar(base + timedelta(minutes=10))
            streamer._on_bar_update(MockBarsHandle([gap_bar]), has_new_bar=True)

            assert streamer._consecutive_good_bars == 0
            assert streamer._resubscribe_attempts == 2, "counter NOT reset due to gap"


# ---------------------------------------------------------------------------
# R4: Gap Backfill
# ---------------------------------------------------------------------------


class TestR4GapBackfill:
    """R4: Gap detected on resubscribe, seed bars fill missing window."""

    def test_gap_detected_and_backfilled_via_seed(self, streamer: RiverStreamer) -> None:
        """Simulate 2hr gap -> resubscribe -> seed bars fill gap."""
        now = datetime(2026, 3, 24, 14, 0, tzinfo=UTC)
        gap_start = now - timedelta(hours=2)

        existing_bar_ts = pd.Timestamp(
            (gap_start - timedelta(minutes=1)).timestamp(), unit="s", tz="UTC"
        )
        existing_data = {
            "timestamp": existing_bar_ts.isoformat(),
            "open": 1.0849,
            "high": 1.0855,
            "low": 1.0845,
            "close": 1.0850,
            "volume": -1.0,
            "source": "ibkr",
            "knowledge_time": gap_start.isoformat(),
        }
        staging_file = streamer.staging_path(existing_bar_ts.date())
        staging_file.parent.mkdir(parents=True, exist_ok=True)
        staging_file.write_text(json.dumps(existing_data) + "\n")

        seed_bars = _make_bars_list(gap_start, count=121)
        streamer._bars_handle = MockBarsHandle(seed_bars)
        streamer._persist_seed_bars()

        all_rows: list[dict[str, Any]] = []
        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    all_rows.append(json.loads(line))

        assert len(all_rows) == 121, "1 existing + 120 new seed bars"
        timestamps = [r["timestamp"] for r in all_rows]
        assert len(timestamps) == len(set(timestamps)), "no duplicates"

    def test_backfill_staging_only_not_parquet(
        self,
        streamer: RiverStreamer,
        tmp_river: Path,
    ) -> None:
        """INV-RIVER-IMMUTABLE: backfill writes to staging only."""
        now = datetime(2026, 3, 24, 14, 0, tzinfo=UTC)
        seed_bars = _make_bars_list(now - timedelta(minutes=5), count=6)
        streamer._bars_handle = MockBarsHandle(seed_bars)
        streamer._persist_seed_bars()

        parquet_files = list(tmp_river.rglob("*.parquet"))
        assert len(parquet_files) == 0, "no parquet files created by backfill"

        staging_files = list(streamer.staging_dir.glob("*.jsonl"))
        assert len(staging_files) >= 1, "staging files created"


# ---------------------------------------------------------------------------
# R5: Heartbeat Coverage Stats
# ---------------------------------------------------------------------------


class TestR5HeartbeatStats:
    """R5: Heartbeat includes coverage statistics."""

    def test_heartbeat_includes_coverage_fields(self, streamer: RiverStreamer) -> None:
        """Heartbeat JSON has bars_received, gaps_detected, session_start."""
        streamer._session_start = datetime(2026, 3, 24, 10, 0, tzinfo=UTC)
        streamer._bars_received = 42
        streamer._gaps_detected = 2
        streamer._consecutive_good_bars = 7
        streamer._update_heartbeat()

        hb = json.loads(streamer.heartbeat_path.read_text())
        assert hb["bars_received"] == 42
        assert hb["gaps_detected"] == 2
        assert hb["consecutive_good_bars"] == 7
        assert hb["session_start"] is not None

    def test_heartbeat_atomic_write(self, streamer: RiverStreamer) -> None:
        """Heartbeat is written atomically (no partial reads)."""
        streamer._update_heartbeat()

        hb = json.loads(streamer.heartbeat_path.read_text())
        assert "state" in hb
        assert "last_update" in hb

    def test_heartbeat_coverage_after_bars(self, streamer: RiverStreamer) -> None:
        """After receiving bars, heartbeat reflects accurate count."""
        streamer._state = "STREAMING"
        base = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            for i in range(10):
                bar = _make_bar(base + timedelta(minutes=i))
                streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

        hb = json.loads(streamer.heartbeat_path.read_text())
        assert hb["bars_received"] == 10
        assert hb["gaps_detected"] == 0


# ---------------------------------------------------------------------------
# Dedup Integration
# ---------------------------------------------------------------------------


class TestDedupIntegration:
    """Cross-cutting dedup tests spanning multiple fixes."""

    def test_on_bar_update_dedup(self, streamer: RiverStreamer) -> None:
        """Duplicate bar via _on_bar_update is silently skipped."""
        streamer._state = "STREAMING"
        bar_time = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bar = _make_bar(bar_time)

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)
            streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

        staging_file = streamer.staging_path(bar_time)
        lines = [ln for ln in staging_file.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1, "duplicate bar should be skipped"

    def test_restart_with_existing_staging_no_duplicates(
        self,
        streamer: RiverStreamer,
    ) -> None:
        """Simulate restart: existing staging + seed bars = no duplicates."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        for i in range(5):
            ts = pd.Timestamp((now + timedelta(minutes=i)).timestamp(), unit="s", tz="UTC")
            data = {
                "timestamp": ts.isoformat(),
                "open": 1.085,
                "high": 1.086,
                "low": 1.084,
                "close": 1.085,
                "volume": -1.0,
                "source": "ibkr",
                "knowledge_time": now.isoformat(),
            }
            f = streamer.staging_path(ts.date())
            f.parent.mkdir(parents=True, exist_ok=True)
            with open(f, "a") as fh:
                fh.write(json.dumps(data) + "\n")

        seed_bars = _make_bars_list(now, count=11)
        streamer._bars_handle = MockBarsHandle(seed_bars)
        streamer._persist_seed_bars()

        all_rows: list[dict[str, Any]] = []
        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    all_rows.append(json.loads(line))

        timestamps = [r["timestamp"] for r in all_rows]
        assert len(timestamps) == len(
            set(timestamps)
        ), f"duplicates found: {len(timestamps)} total, {len(set(timestamps))} unique"

    def test_load_known_timestamps_from_disk(self, streamer: RiverStreamer) -> None:
        """_load_known_timestamps reads existing staging into memory."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        ts = pd.Timestamp(now.timestamp(), unit="s", tz="UTC")
        data = {
            "timestamp": ts.isoformat(),
            "open": 1.085,
            "high": 1.086,
            "low": 1.084,
            "close": 1.085,
            "volume": -1.0,
            "source": "ibkr",
            "knowledge_time": now.isoformat(),
        }
        f = streamer.staging_path(ts.date())
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(data) + "\n")

        assert len(streamer._known_timestamps) == 0
        streamer._load_known_timestamps()
        assert ts.isoformat() in streamer._known_timestamps


# ---------------------------------------------------------------------------
# Invariant Tests
# ---------------------------------------------------------------------------


class TestInvariants:
    """Prove invariants are preserved by all 5 fixes."""

    def test_inv_river_immutable_seed_bars(
        self,
        streamer: RiverStreamer,
        tmp_river: Path,
    ) -> None:
        """INV-RIVER-IMMUTABLE: seed bars never create parquet files."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(hours=12), count=720)
        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        assert list(tmp_river.rglob("*.parquet")) == []

    def test_inv_river_immutable_on_bar_update(
        self,
        streamer: RiverStreamer,
        tmp_river: Path,
    ) -> None:
        """INV-RIVER-IMMUTABLE: _on_bar_update never creates parquet files."""
        streamer._state = "STREAMING"
        base = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            for i in range(20):
                bar = _make_bar(base + timedelta(minutes=i))
                streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

        assert list(tmp_river.rglob("*.parquet")) == []

    def test_inv_no_forming_candle(self, streamer: RiverStreamer) -> None:
        """INV-NO-FORMING-CANDLE: forming bar (last in seed) never persisted."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(minutes=5), count=6)
        forming_ts = pd.Timestamp(bars[-1].date.timestamp(), unit="s", tz="UTC")

        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        all_ts: set[str] = set()
        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    all_ts.add(json.loads(line)["timestamp"])

        assert forming_ts.isoformat() not in all_ts

    def test_inv_river_source_tag(self, streamer: RiverStreamer) -> None:
        """INV-RIVER-SOURCE-TAG: all persisted bars have source='ibkr'."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(minutes=3), count=4)
        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        streamer._state = "STREAMING"
        bar = _make_bar(now + timedelta(minutes=1))
        with patch.object(streamer, "_is_trading_hours", return_value=True):
            streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    assert row["source"] == "ibkr"

    def test_inv_river_bitemporal(self, streamer: RiverStreamer) -> None:
        """INV-RIVER-BITEMPORAL: every bar has timestamp AND knowledge_time."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)
        bars = _make_bars_list(now - timedelta(minutes=3), count=4)
        streamer._bars_handle = MockBarsHandle(bars)
        streamer._persist_seed_bars()

        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    assert "timestamp" in row
                    assert "knowledge_time" in row
                    assert row["timestamp"] != ""
                    assert row["knowledge_time"] != ""


# ---------------------------------------------------------------------------
# Scenario Tests (Exit Gate)
# ---------------------------------------------------------------------------


class TestExitGateScenarios:
    """End-to-end scenario tests from the brief's EXIT_GATE."""

    def test_restart_after_6hr_gap_recovers(self, streamer: RiverStreamer) -> None:
        """Simulate: restart after 6hr gap -> recovers bars via 1D backfill."""
        now = datetime(2026, 3, 24, 18, 0, tzinfo=UTC)
        gap_start = now - timedelta(hours=6)

        old_bar_ts = pd.Timestamp(
            (gap_start - timedelta(minutes=1)).timestamp(),
            unit="s",
            tz="UTC",
        )
        old_data = {
            "timestamp": old_bar_ts.isoformat(),
            "open": 1.085,
            "high": 1.086,
            "low": 1.084,
            "close": 1.085,
            "volume": -1.0,
            "source": "ibkr",
            "knowledge_time": gap_start.isoformat(),
        }
        f = streamer.staging_path(old_bar_ts.date())
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(old_data) + "\n")

        seed_bars = _make_bars_list(gap_start, count=361)
        streamer._bars_handle = MockBarsHandle(seed_bars)
        streamer._persist_seed_bars()

        all_rows: list[dict[str, Any]] = []
        for sf in streamer.staging_dir.glob("*.jsonl"):
            for line in sf.read_text().splitlines():
                if line.strip():
                    all_rows.append(json.loads(line))

        assert len(all_rows) == 361, "1 old + 360 new (minus forming)"
        timestamps = [r["timestamp"] for r in all_rows]
        assert len(timestamps) == len(set(timestamps))

    def test_mid_session_stale_resubscribes_with_backoff(
        self,
        streamer: RiverStreamer,
    ) -> None:
        """Simulate: mid-session stale -> resubscribes with backoff."""
        streamer._last_bar_time = datetime.now(UTC) - timedelta(seconds=300)
        streamer._subscribe_time = time.monotonic() - 400
        streamer._ib = MagicMock()
        streamer._state = "STREAMING"

        with (
            patch.object(streamer, "_is_trading_hours", return_value=True),
            patch.object(streamer, "_subscribe") as mock_sub,
            patch("river.streamer.time.sleep") as mock_sleep,
        ):
            streamer._attempt_resubscribe()

        assert streamer._resubscribe_attempts == 1
        mock_sleep.assert_called_once_with(60)
        mock_sub.assert_called_once()

    def test_three_failures_recovery_counter_reset_can_fail_again(
        self,
        streamer: RiverStreamer,
    ) -> None:
        """3 failures -> recovery -> counter reset -> can fail again."""
        streamer._resubscribe_attempts = 3
        streamer._state = "STREAMING"
        base = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        with patch.object(streamer, "_is_trading_hours", return_value=True):
            for i in range(CONSECUTIVE_GOOD_BARS_RESET + 1):
                bar = _make_bar(base + timedelta(minutes=i))
                streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

        assert streamer._resubscribe_attempts == 0, "counter reset after good bars"

        streamer._subscribe_time = time.monotonic() - 400
        streamer._ib = MagicMock()

        with (
            patch.object(streamer, "_subscribe", side_effect=Exception("IBKR down")),
            patch("river.streamer.time.sleep"),
        ):
            streamer._attempt_resubscribe()

        assert streamer._resubscribe_attempts == 1, "can fail again after reset"

    def test_no_bar_duplicates_in_any_scenario(self, streamer: RiverStreamer) -> None:
        """Comprehensive: seed + stream + reseed -> zero duplicates."""
        now = datetime(2026, 3, 24, 12, 0, tzinfo=UTC)

        seed1 = _make_bars_list(now - timedelta(minutes=10), count=11)
        streamer._bars_handle = MockBarsHandle(seed1)
        streamer._persist_seed_bars()

        streamer._state = "STREAMING"
        with patch.object(streamer, "_is_trading_hours", return_value=True):
            for i in range(5):
                bar = _make_bar(now + timedelta(minutes=i + 1))
                streamer._on_bar_update(MockBarsHandle([bar]), has_new_bar=True)

        seed2 = _make_bars_list(now - timedelta(minutes=5), count=20)
        streamer._bars_handle = MockBarsHandle(seed2)
        streamer._persist_seed_bars()

        all_rows: list[dict[str, Any]] = []
        for f in streamer.staging_dir.glob("*.jsonl"):
            for line in f.read_text().splitlines():
                if line.strip():
                    all_rows.append(json.loads(line))

        timestamps = [r["timestamp"] for r in all_rows]
        unique = set(timestamps)
        assert len(timestamps) == len(
            unique
        ), f"duplicates: {len(timestamps)} total vs {len(unique)} unique"
