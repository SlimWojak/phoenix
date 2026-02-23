"""
Exponential Backoff — S40 Self-Healing Track A
==============================================

Progressive retry delays to prevent thundering herd.
No 3am wake-ups. System recovers gracefully.

FORMULA:
  delay = min(base * 2^attempt + jitter, max_delay)

INVARIANTS:
  INV-BACKOFF-1: Retry interval doubles each attempt
  INV-BACKOFF-2: Interval capped at max_delay
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from typing import Callable


# =============================================================================
# EXPONENTIAL BACKOFF
# =============================================================================


@dataclass
class ExponentialBackoff:
    """
    Exponential backoff with jitter for retry logic.

    Usage:
        backoff = ExponentialBackoff(base=1.0, max_delay=300.0)

        for attempt in range(max_retries):
            try:
                result = do_operation()
                break
            except RetryableError:
                if attempt < max_retries - 1:
                    delay = backoff.wait(attempt)
                    time.sleep(delay)

    INVARIANTS:
      INV-BACKOFF-1: Interval doubles (base * 2^attempt)
      INV-BACKOFF-2: Interval capped at max_delay
    """

    base: float = 1.0  # Base delay in seconds
    max_delay: float = 300.0  # Max delay (5 minutes)
    jitter: float = 0.1  # 10% jitter
    
    # Internal tracking
    _attempt: int = field(default=0, repr=False)
    _total_wait_time: float = field(default=0.0, repr=False)

    def compute_delay(self, attempt: int) -> float:
        """
        Compute delay for given attempt number.

        INV-BACKOFF-1: delay = base * 2^attempt (before jitter/cap)
        INV-BACKOFF-2: delay <= max_delay

        Args:
            attempt: 0-indexed attempt number

        Returns:
            Delay in seconds (with jitter applied)
        """
        # Base delay doubles each attempt
        base_delay = self.base * (2 ** attempt)

        # Apply jitter (random ±jitter%)
        if self.jitter > 0:
            jitter_range = base_delay * self.jitter
            jitter_offset = random.uniform(-jitter_range, jitter_range)
            base_delay += jitter_offset

        # Cap at max_delay (INV-BACKOFF-2)
        return min(base_delay, self.max_delay)

    def wait(self, attempt: int | None = None) -> float:
        """
        Get delay for this attempt and update internal counter.

        Args:
            attempt: Optional explicit attempt number. If None, uses internal counter.

        Returns:
            Delay in seconds
        """
        if attempt is None:
            attempt = self._attempt
            self._attempt += 1

        delay = self.compute_delay(attempt)
        self._total_wait_time += delay
        return delay

    def sleep_sync(self, attempt: int | None = None) -> float:
        """
        Synchronously sleep for computed delay.

        Args:
            attempt: Optional explicit attempt number

        Returns:
            Actual delay slept
        """
        delay = self.wait(attempt)
        time.sleep(delay)
        return delay

    async def sleep(self, attempt: int | None = None) -> float:
        """
        Asynchronously sleep for computed delay.

        Args:
            attempt: Optional explicit attempt number

        Returns:
            Actual delay slept
        """
        delay = self.wait(attempt)
        await asyncio.sleep(delay)
        return delay

    def reset(self) -> None:
        """Reset attempt counter and total wait time."""
        self._attempt = 0
        self._total_wait_time = 0.0

    @property
    def attempt_count(self) -> int:
        """Current attempt count."""
        return self._attempt

    @property
    def total_wait_time(self) -> float:
        """Total time spent waiting."""
        return self._total_wait_time

    def get_schedule(self, max_attempts: int = 10) -> list[float]:
        """
        Preview delay schedule for first N attempts.

        Useful for documentation/debugging.
        Does NOT include jitter (shows theoretical values).
        """
        schedule = []
        for i in range(max_attempts):
            # Compute without jitter for predictable preview
            base_delay = self.base * (2 ** i)
            capped = min(base_delay, self.max_delay)
            schedule.append(capped)
        return schedule


# =============================================================================
# RETRY WITH BACKOFF
# =============================================================================


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, operation: str, attempts: int, last_error: Exception | None):
        self.operation = operation
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Operation '{operation}' failed after {attempts} attempts. "
            f"Last error: {last_error}"
        )


def retry_with_backoff(
    fn: Callable,
    max_attempts: int = 5,
    base: float = 1.0,
    max_delay: float = 300.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> any:
    """
    Execute function with exponential backoff retry.

    Args:
        fn: Function to execute
        max_attempts: Maximum retry attempts
        base: Base delay in seconds
        max_delay: Maximum delay cap
        retryable_exceptions: Tuple of exception types to retry
        on_retry: Optional callback(attempt, exception, delay)

    Returns:
        Result of fn()

    Raises:
        RetryExhaustedError: All attempts failed
    """
    backoff = ExponentialBackoff(base=base, max_delay=max_delay)
    last_error = None

    for attempt in range(max_attempts):
        try:
            return fn()
        except retryable_exceptions as e:
            last_error = e
            if attempt < max_attempts - 1:
                delay = backoff.wait(attempt)
                if on_retry:
                    on_retry(attempt, e, delay)
                time.sleep(delay)

    raise RetryExhaustedError(
        operation=fn.__name__ if hasattr(fn, "__name__") else "unknown",
        attempts=max_attempts,
        last_error=last_error,
    )


async def retry_with_backoff_async(
    fn: Callable,
    max_attempts: int = 5,
    base: float = 1.0,
    max_delay: float = 300.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Callable[[int, Exception, float], None] | None = None,
) -> any:
    """
    Execute async function with exponential backoff retry.

    Args:
        fn: Async function to execute
        max_attempts: Maximum retry attempts
        base: Base delay in seconds
        max_delay: Maximum delay cap
        retryable_exceptions: Tuple of exception types to retry
        on_retry: Optional callback(attempt, exception, delay)

    Returns:
        Result of fn()

    Raises:
        RetryExhaustedError: All attempts failed
    """
    backoff = ExponentialBackoff(base=base, max_delay=max_delay)
    last_error = None

    for attempt in range(max_attempts):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_error = e
            if attempt < max_attempts - 1:
                delay = backoff.wait(attempt)
                if on_retry:
                    on_retry(attempt, e, delay)
                await asyncio.sleep(delay)

    raise RetryExhaustedError(
        operation=fn.__name__ if hasattr(fn, "__name__") else "unknown",
        attempts=max_attempts,
        last_error=last_error,
    )
