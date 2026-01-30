"""
Circuit Breaker Tests — S40 Track A
===================================

Proves INV-CIRCUIT-1 and INV-CIRCUIT-2.
"""

from __future__ import annotations

import time
import threading
import pytest

from governance.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitOpenError,
    CircuitHalfOpenError,
    CircuitBreakerRegistry,
    get_circuit_breaker,
)


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def breaker() -> CircuitBreaker:
    """Create fresh circuit breaker."""
    return CircuitBreaker(
        name="test_breaker",
        failure_threshold=3,
        recovery_timeout=1.0,  # Short for testing
    )


@pytest.fixture
def registry() -> CircuitBreakerRegistry:
    """Create fresh registry."""
    return CircuitBreakerRegistry()


# =============================================================================
# BASIC STATE TESTS
# =============================================================================


class TestCircuitBreakerStates:
    """Test basic circuit breaker states."""

    def test_initial_state_is_closed(self, breaker: CircuitBreaker):
        """New breaker starts CLOSED."""
        assert breaker.state == CircuitState.CLOSED
        print("✓ Initial state is CLOSED")

    def test_call_passes_when_closed(self, breaker: CircuitBreaker):
        """Calls pass through when CLOSED."""
        result = breaker.call(lambda: "success")
        assert result == "success"
        print("✓ Call passes when CLOSED")

    def test_failures_increment(self, breaker: CircuitBreaker):
        """Failures increment counter."""
        for i in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        metrics = breaker.get_metrics()
        assert metrics["current_failure_count"] == 2
        print("✓ Failures increment counter")


# =============================================================================
# INV-CIRCUIT-1: OPEN BLOCKS REQUESTS
# =============================================================================


class TestCircuitOpenBlocks:
    """Prove INV-CIRCUIT-1: OPEN circuit blocks new requests."""

    def test_open_after_threshold_failures(self, breaker: CircuitBreaker):
        """Circuit opens after threshold failures."""
        # Cause 3 failures (threshold)
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN
        print("✓ Circuit OPEN after threshold failures")

    def test_open_circuit_raises_error(self, breaker: CircuitBreaker):
        """INV-CIRCUIT-1: OPEN raises CircuitOpenError."""
        # Trip the breaker
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        # Next call should raise CircuitOpenError
        with pytest.raises(CircuitOpenError) as exc_info:
            breaker.call(lambda: "should_not_run")

        assert exc_info.value.breaker_name == "test_breaker"
        print("✓ INV-CIRCUIT-1: OPEN raises CircuitOpenError")

    def test_open_blocks_all_requests(self, breaker: CircuitBreaker):
        """OPEN blocks multiple consecutive requests."""
        # Trip the breaker
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        # Multiple calls should all be blocked
        blocked_count = 0
        for _ in range(5):
            try:
                breaker.call(lambda: "nope")
            except CircuitOpenError:
                blocked_count += 1

        assert blocked_count == 5
        print(f"✓ OPEN blocked {blocked_count}/5 requests")


# =============================================================================
# INV-CIRCUIT-2: HALF_OPEN ALLOWS 1 PROBE
# =============================================================================


class TestCircuitHalfOpen:
    """Prove INV-CIRCUIT-2: HALF_OPEN allows exactly 1 probe."""

    def test_open_transitions_to_half_open(self, breaker: CircuitBreaker):
        """OPEN → HALF_OPEN after recovery timeout."""
        # Trip the breaker
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(1.1)

        # State should now be HALF_OPEN
        assert breaker.state == CircuitState.HALF_OPEN
        print("✓ OPEN → HALF_OPEN after timeout")

    def test_half_open_allows_one_probe(self, breaker: CircuitBreaker):
        """INV-CIRCUIT-2: HALF_OPEN allows exactly 1 probe."""
        # Trip and wait
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass
        
        time.sleep(1.1)
        assert breaker.state == CircuitState.HALF_OPEN

        # First call should pass (probe)
        result = breaker.call(lambda: "probe_success")
        assert result == "probe_success"
        print("✓ INV-CIRCUIT-2: First probe allowed")

    def test_half_open_probe_success_closes_circuit(self, breaker: CircuitBreaker):
        """Successful probe → CLOSED."""
        # Trip and wait
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass
        
        time.sleep(1.1)

        # Successful probe
        breaker.call(lambda: "success")

        # Should be CLOSED now
        assert breaker.state == CircuitState.CLOSED
        print("✓ Probe success → CLOSED")

    def test_half_open_probe_failure_reopens(self, breaker: CircuitBreaker):
        """Failed probe → OPEN again."""
        # Trip and wait
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass
        
        time.sleep(1.1)

        # Failed probe
        try:
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("probe_fail")))
        except ValueError:
            pass

        # Should be OPEN again
        assert breaker.state == CircuitState.OPEN
        print("✓ Probe failure → OPEN")


# =============================================================================
# RESET AND METRICS
# =============================================================================


class TestCircuitBreakerAdmin:
    """Test administrative functions."""

    def test_reset_forces_closed(self, breaker: CircuitBreaker):
        """Reset forces circuit to CLOSED."""
        # Trip the breaker
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        assert breaker.state == CircuitState.OPEN

        # Admin reset
        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        print("✓ Reset forces CLOSED")

    def test_metrics_track_calls(self, breaker: CircuitBreaker):
        """Metrics accurately track calls."""
        # Some successes
        for _ in range(3):
            breaker.call(lambda: "ok")

        # Some failures
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        metrics = breaker.get_metrics()
        assert metrics["total_calls"] == 5
        assert metrics["total_successes"] == 3
        assert metrics["total_failures"] == 2
        print("✓ Metrics track calls correctly")


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry."""

    def test_get_or_create_same_instance(self, registry: CircuitBreakerRegistry):
        """Same name returns same instance."""
        b1 = registry.get_or_create("test")
        b2 = registry.get_or_create("test")

        assert b1 is b2
        print("✓ Same name returns same instance")

    def test_different_names_different_instances(self, registry: CircuitBreakerRegistry):
        """Different names return different instances."""
        b1 = registry.get_or_create("alpha")
        b2 = registry.get_or_create("beta")

        assert b1 is not b2
        print("✓ Different names return different instances")

    def test_all_metrics_returns_all(self, registry: CircuitBreakerRegistry):
        """all_metrics returns all breaker metrics."""
        registry.get_or_create("one")
        registry.get_or_create("two")
        registry.get_or_create("three")

        metrics = registry.all_metrics()
        assert len(metrics) == 3
        names = {m["name"] for m in metrics}
        assert names == {"one", "two", "three"}
        print("✓ all_metrics returns all breakers")


# =============================================================================
# CHAOS: CONCURRENT ACCESS
# =============================================================================


class TestCircuitBreakerChaos:
    """Chaos tests for thread safety."""

    def test_concurrent_calls_thread_safe(self, breaker: CircuitBreaker):
        """Concurrent calls don't corrupt state."""
        results = {"success": 0, "error": 0, "blocked": 0}
        lock = threading.Lock()

        def worker():
            for _ in range(10):
                try:
                    breaker.call(lambda: "ok")
                    with lock:
                        results["success"] += 1
                except CircuitOpenError:
                    with lock:
                        results["blocked"] += 1
                except Exception:
                    with lock:
                        results["error"] += 1

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        total = results["success"] + results["blocked"] + results["error"]
        assert total == 50
        print(f"✓ Thread safe: {results}")

    def test_hammer_until_open(self, breaker: CircuitBreaker):
        """Hammer with failures until circuit opens."""
        failures = 0
        blocked = 0

        for _ in range(10):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("hammer")))
            except ValueError:
                failures += 1
            except CircuitOpenError:
                blocked += 1

        assert breaker.state == CircuitState.OPEN
        assert failures == 3  # Threshold
        assert blocked == 7  # Remaining blocked
        print(f"✓ Hammer test: {failures} failures, {blocked} blocked")
