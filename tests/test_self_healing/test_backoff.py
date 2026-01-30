"""
Exponential Backoff Tests — S40 Track A
=======================================

Proves INV-BACKOFF-1 and INV-BACKOFF-2.
"""

from __future__ import annotations

import pytest
import time

from governance.backoff import (
    ExponentialBackoff,
    RetryExhaustedError,
    retry_with_backoff,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def backoff() -> ExponentialBackoff:
    """Create backoff with default settings."""
    return ExponentialBackoff(base=1.0, max_delay=300.0, jitter=0.0)


@pytest.fixture
def backoff_with_jitter() -> ExponentialBackoff:
    """Create backoff with jitter."""
    return ExponentialBackoff(base=1.0, max_delay=300.0, jitter=0.1)


# =============================================================================
# INV-BACKOFF-1: INTERVAL DOUBLES
# =============================================================================


class TestBackoffDoubles:
    """Prove INV-BACKOFF-1: Retry interval doubles each attempt."""

    def test_delay_doubles_each_attempt(self, backoff: ExponentialBackoff):
        """INV-BACKOFF-1: delay = base * 2^attempt."""
        delays = [backoff.compute_delay(i) for i in range(5)]

        # Expected: 1, 2, 4, 8, 16
        expected = [1.0, 2.0, 4.0, 8.0, 16.0]

        assert delays == expected
        print(f"✓ INV-BACKOFF-1: Delays double: {delays}")

    def test_delay_formula_correct(self, backoff: ExponentialBackoff):
        """Verify formula: base * 2^attempt."""
        for attempt in range(10):
            expected = backoff.base * (2 ** attempt)
            actual = backoff.compute_delay(attempt)

            # Should match exactly (no jitter)
            assert actual == min(expected, backoff.max_delay)

        print("✓ Formula: base * 2^attempt verified for 10 attempts")

    def test_attempt_0_is_base(self, backoff: ExponentialBackoff):
        """First attempt uses base delay."""
        delay = backoff.compute_delay(0)
        assert delay == backoff.base
        print(f"✓ Attempt 0 = base ({delay}s)")

    def test_schedule_preview(self, backoff: ExponentialBackoff):
        """Schedule preview shows doubling."""
        schedule = backoff.get_schedule(8)

        # Verify doubling (before cap kicks in)
        for i in range(1, 8):
            if schedule[i] < backoff.max_delay:
                assert schedule[i] == schedule[i - 1] * 2

        print(f"✓ Schedule preview: {schedule}")


# =============================================================================
# INV-BACKOFF-2: INTERVAL CAPPED
# =============================================================================


class TestBackoffCapped:
    """Prove INV-BACKOFF-2: Interval capped at max_delay."""

    def test_delay_capped_at_max(self, backoff: ExponentialBackoff):
        """INV-BACKOFF-2: delay <= max_delay."""
        # Attempt 10: 2^10 = 1024s > 300s max
        delay = backoff.compute_delay(10)

        assert delay == backoff.max_delay
        assert delay == 300.0
        print(f"✓ INV-BACKOFF-2: Attempt 10 capped at {delay}s")

    def test_all_delays_under_max(self, backoff: ExponentialBackoff):
        """All delays must be <= max_delay."""
        for attempt in range(100):
            delay = backoff.compute_delay(attempt)
            assert delay <= backoff.max_delay

        print("✓ All 100 attempts capped at max_delay")

    def test_cap_applies_at_right_point(self, backoff: ExponentialBackoff):
        """Cap kicks in when 2^attempt > max_delay."""
        # With base=1.0 and max=300.0:
        # 2^8 = 256 (under cap)
        # 2^9 = 512 (over cap)

        assert backoff.compute_delay(8) == 256.0  # Under cap
        assert backoff.compute_delay(9) == 300.0  # Capped
        print("✓ Cap kicks in at attempt 9")


# =============================================================================
# JITTER TESTS
# =============================================================================


class TestBackoffJitter:
    """Test jitter application."""

    def test_jitter_varies_delay(self, backoff_with_jitter: ExponentialBackoff):
        """Jitter causes variation in delays."""
        delays = [backoff_with_jitter.compute_delay(3) for _ in range(10)]

        # With 10% jitter, delays should vary
        unique_delays = set(delays)

        # Should have some variation (probabilistic, but very likely)
        assert len(unique_delays) > 1
        print(f"✓ Jitter created {len(unique_delays)} unique delays")

    def test_jitter_within_bounds(self, backoff_with_jitter: ExponentialBackoff):
        """Jitter stays within ±jitter%."""
        base_delay = 8.0  # 2^3
        jitter = backoff_with_jitter.jitter

        for _ in range(100):
            delay = backoff_with_jitter.compute_delay(3)
            min_expected = base_delay * (1 - jitter)
            max_expected = base_delay * (1 + jitter)

            assert min_expected <= delay <= max_expected

        print("✓ Jitter stays within bounds")


# =============================================================================
# WAIT AND SLEEP TESTS
# =============================================================================


class TestBackoffWait:
    """Test wait() method with internal counter."""

    def test_wait_increments_counter(self, backoff: ExponentialBackoff):
        """wait() increments internal counter."""
        assert backoff.attempt_count == 0

        backoff.wait()
        assert backoff.attempt_count == 1

        backoff.wait()
        assert backoff.attempt_count == 2

        print("✓ wait() increments counter")

    def test_wait_tracks_total_time(self, backoff: ExponentialBackoff):
        """wait() tracks total wait time."""
        assert backoff.total_wait_time == 0.0

        backoff.wait(0)  # 1s
        backoff.wait(1)  # 2s
        backoff.wait(2)  # 4s

        assert backoff.total_wait_time == 7.0
        print(f"✓ Total wait time tracked: {backoff.total_wait_time}s")

    def test_reset_clears_state(self, backoff: ExponentialBackoff):
        """reset() clears counter and total time."""
        backoff.wait()
        backoff.wait()
        backoff.wait()

        backoff.reset()

        assert backoff.attempt_count == 0
        assert backoff.total_wait_time == 0.0
        print("✓ reset() clears state")


# =============================================================================
# RETRY WITH BACKOFF
# =============================================================================


class TestRetryWithBackoff:
    """Test retry_with_backoff utility."""

    def test_success_on_first_try(self):
        """No retry needed on success."""
        call_count = 0

        def fn():
            nonlocal call_count
            call_count += 1
            return "success"

        result = retry_with_backoff(fn, max_attempts=3, base=0.01)

        assert result == "success"
        assert call_count == 1
        print("✓ Success on first try")

    def test_success_after_retry(self):
        """Success after initial failures."""
        call_count = 0

        def fn():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("fail")
            return "success"

        result = retry_with_backoff(fn, max_attempts=5, base=0.01)

        assert result == "success"
        assert call_count == 3
        print(f"✓ Success after {call_count} attempts")

    def test_exhausted_raises_error(self):
        """All retries exhausted raises RetryExhaustedError."""
        call_count = 0

        def fn():
            nonlocal call_count
            call_count += 1
            raise ValueError("always_fail")

        with pytest.raises(RetryExhaustedError) as exc_info:
            retry_with_backoff(fn, max_attempts=3, base=0.01)

        assert exc_info.value.attempts == 3
        assert call_count == 3
        print("✓ RetryExhaustedError raised after exhaustion")

    def test_on_retry_callback(self):
        """on_retry callback is invoked."""
        retries = []

        def on_retry(attempt, error, delay):
            retries.append((attempt, str(error), delay))

        def fn():
            if len(retries) < 2:
                raise ValueError("retry_me")
            return "done"

        retry_with_backoff(fn, max_attempts=5, base=0.01, on_retry=on_retry)

        assert len(retries) == 2
        print(f"✓ on_retry called {len(retries)} times")

    def test_retryable_exceptions_filter(self):
        """Only retryable exceptions trigger retry."""
        call_count = 0

        def fn():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("retryable")
            raise TypeError("not_retryable")

        with pytest.raises(TypeError):
            retry_with_backoff(
                fn,
                max_attempts=5,
                base=0.01,
                retryable_exceptions=(ValueError,),
            )

        assert call_count == 2  # First retry, then TypeError
        print("✓ Non-retryable exceptions pass through")


# =============================================================================
# EDGE CASES
# =============================================================================


class TestBackoffEdgeCases:
    """Test edge cases and boundaries."""

    def test_zero_base_delay(self):
        """Zero base delay works."""
        backoff = ExponentialBackoff(base=0.0, max_delay=100.0)

        # All delays should be 0
        for i in range(10):
            assert backoff.compute_delay(i) == 0.0

        print("✓ Zero base delay works")

    def test_very_small_max_delay(self):
        """Very small max_delay caps correctly."""
        backoff = ExponentialBackoff(base=1.0, max_delay=0.5)

        # Should cap immediately
        assert backoff.compute_delay(0) == 0.5
        assert backoff.compute_delay(1) == 0.5

        print("✓ Small max_delay caps correctly")

    def test_large_attempt_numbers(self):
        """Large attempt numbers don't overflow."""
        backoff = ExponentialBackoff(base=1.0, max_delay=300.0, jitter=0.0)

        # 2^1000 would overflow, but cap should prevent
        delay = backoff.compute_delay(1000)
        assert delay == 300.0

        print("✓ Large attempts capped correctly")
