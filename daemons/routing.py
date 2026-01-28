"""
Intent Routing — Route intents to workers
==========================================

S34: D1 FILE_SEAM_COMPLETION

Maps intent types to worker handlers.
HALT intents bypass queue and process immediately.

INVARIANTS:
- INV-D1-WATCHER-IMMUTABLE-1: Watcher may not modify intent payloads
- INV-D1-HALT-PRIORITY-1: HALT bypasses queue, processes immediately
"""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Protocol

import yaml

logger = logging.getLogger(__name__)


# =============================================================================
# INTENT TYPES
# =============================================================================


class IntentType(str, Enum):
    """Known intent types with routing behavior."""

    # Standard intents (queued)
    SCAN = "SCAN"
    HUNT = "HUNT"
    APPROVE = "APPROVE"
    QUERY_MEMORY = "QUERY_MEMORY"
    STATUS = "STATUS"
    CSE = "CSE"  # S34 D2: Canonical Signal Envelope

    # Priority intents (immediate)
    HALT = "HALT"

    # Unknown (quarantine)
    UNKNOWN = "UNKNOWN"

    @classmethod
    def from_string(cls, value: str) -> IntentType:
        """Parse intent type from string (case-insensitive)."""
        try:
            return cls(value.upper())
        except ValueError:
            return cls.UNKNOWN


# =============================================================================
# INTENT DATA
# =============================================================================


@dataclass
class Intent:
    """Parsed intent with metadata."""

    intent_type: IntentType
    payload: dict[str, Any]
    timestamp: datetime
    session_id: str
    raw_yaml: str
    source_path: Path
    content_hash: str = ""

    def __post_init__(self) -> None:
        """Compute content hash for immutability verification."""
        if not self.content_hash:
            self.content_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute SHA256 of raw YAML content."""
        return hashlib.sha256(self.raw_yaml.encode()).hexdigest()

    def verify_immutable(self, current_yaml: str) -> bool:
        """
        Verify intent has not been modified.

        INV-D1-WATCHER-IMMUTABLE-1 enforcement.
        """
        current_hash = hashlib.sha256(current_yaml.encode()).hexdigest()
        return current_hash == self.content_hash


@dataclass
class RouteResult:
    """Result of routing an intent."""

    success: bool
    intent: Intent
    worker_name: str | None = None
    response_path: Path | None = None
    error: str | None = None
    processing_time_ms: float = 0.0


# =============================================================================
# WORKER HANDLER PROTOCOL
# =============================================================================


class WorkerHandler(Protocol):
    """Protocol for worker handlers."""

    def handle(self, intent: Intent) -> RouteResult:
        """Process an intent and return result."""
        ...


# =============================================================================
# INTENT ROUTER
# =============================================================================


class IntentRouter:
    """
    Routes intents to appropriate workers.

    INVARIANT: INV-D1-HALT-PRIORITY-1
    HALT intents bypass queue and process immediately.
    """

    def __init__(self) -> None:
        """Initialize router with empty handlers."""
        self._handlers: dict[IntentType, WorkerHandler] = {}
        self._halt_handler: WorkerHandler | None = None
        self._default_response_dir = Path(__file__).parent.parent / "responses"

    def register(self, intent_type: IntentType, handler: WorkerHandler) -> None:
        """
        Register a handler for an intent type.

        Args:
            intent_type: Type of intent to handle
            handler: Handler to invoke
        """
        if intent_type == IntentType.HALT:
            self._halt_handler = handler
        else:
            self._handlers[intent_type] = handler

        logger.info(f"Registered handler for {intent_type.value}")

    def register_function(
        self,
        intent_type: IntentType,
        func: Callable[[Intent], RouteResult],
    ) -> None:
        """
        Register a function as handler (convenience method).

        Args:
            intent_type: Type of intent to handle
            func: Function to invoke
        """

        class FunctionHandler:
            def __init__(self, fn: Callable[[Intent], RouteResult]) -> None:
                self._fn = fn

            def handle(self, intent: Intent) -> RouteResult:
                return self._fn(intent)

        self.register(intent_type, FunctionHandler(func))

    def is_priority(self, intent_type: IntentType) -> bool:
        """
        Check if intent type has priority (bypasses queue).

        INV-D1-HALT-PRIORITY-1: HALT is always priority.
        """
        return intent_type == IntentType.HALT

    def route(self, intent: Intent) -> RouteResult:
        """
        Route intent to appropriate handler.

        Args:
            intent: Parsed intent to route

        Returns:
            RouteResult with processing outcome
        """
        import time

        start = time.perf_counter_ns()

        # Check for HALT (priority)
        if intent.intent_type == IntentType.HALT:
            if self._halt_handler:
                logger.warning("HALT intent received — processing immediately")
                result = self._halt_handler.handle(intent)
                result.processing_time_ms = (time.perf_counter_ns() - start) / 1_000_000
                return result
            else:
                return RouteResult(
                    success=False,
                    intent=intent,
                    error="No HALT handler registered",
                )

        # Check for unknown type
        if intent.intent_type == IntentType.UNKNOWN:
            return RouteResult(
                success=False,
                intent=intent,
                error=f"Unknown intent type: {intent.payload.get('type', 'MISSING')}",
            )

        # Route to registered handler
        handler = self._handlers.get(intent.intent_type)
        if handler:
            try:
                result = handler.handle(intent)
                result.processing_time_ms = (time.perf_counter_ns() - start) / 1_000_000
                return result
            except Exception as e:
                logger.error(f"Handler error for {intent.intent_type.value}: {e}")
                return RouteResult(
                    success=False,
                    intent=intent,
                    worker_name=intent.intent_type.value,
                    error=str(e),
                )
        else:
            return RouteResult(
                success=False,
                intent=intent,
                error=f"No handler for intent type: {intent.intent_type.value}",
            )

    def get_registered_types(self) -> list[IntentType]:
        """Return list of registered intent types."""
        types = list(self._handlers.keys())
        if self._halt_handler:
            types.append(IntentType.HALT)
        return types


# =============================================================================
# INTENT PARSER
# =============================================================================


def parse_intent(path: Path) -> Intent | None:
    """
    Parse intent from YAML file.

    Args:
        path: Path to intent YAML file

    Returns:
        Parsed Intent or None if invalid
    """
    try:
        raw_yaml = path.read_text()
        data = yaml.safe_load(raw_yaml)

        if not isinstance(data, dict):
            logger.error(f"Invalid intent format (not a dict): {path}")
            return None

        intent_type = IntentType.from_string(data.get("type", ""))

        # Parse timestamp
        timestamp_str = data.get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(UTC)
        else:
            timestamp = datetime.now(UTC)

        return Intent(
            intent_type=intent_type,
            payload=data.get("payload", {}),
            timestamp=timestamp,
            session_id=data.get("session_id", "unknown"),
            raw_yaml=raw_yaml,
            source_path=path,
        )

    except yaml.YAMLError as e:
        logger.error(f"YAML parse error for {path}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to parse intent {path}: {e}")
        return None


# =============================================================================
# STUB HANDLERS (For testing / wiring)
# =============================================================================


def create_stub_handler(
    intent_type: IntentType,
    response_dir: Path | None = None,
) -> WorkerHandler:
    """
    Create a stub handler that writes a basic response.

    Used for wiring validation before real workers connected.
    """
    if response_dir is None:
        response_dir = Path(__file__).parent.parent / "responses"

    class StubHandler:
        def __init__(self, name: str, resp_dir: Path) -> None:
            self._name = name
            self._resp_dir = resp_dir

        def handle(self, intent: Intent) -> RouteResult:
            """Write stub response."""
            response_file = self._resp_dir / f"{self._name.lower()}_response.md"

            content = f"""---
type: {self._name}
intent_session: {intent.session_id}
processed_at: {datetime.now(UTC).isoformat()}
---

# {self._name} Response

Intent processed by stub handler.

**Payload:**
```yaml
{yaml.dump(intent.payload, default_flow_style=False)}
```

*This is a stub response. Real worker not yet connected.*
"""
            response_file.write_text(content)

            return RouteResult(
                success=True,
                intent=intent,
                worker_name=self._name,
                response_path=response_file,
            )

    return StubHandler(intent_type.value, response_dir)


def create_halt_handler() -> WorkerHandler:
    """
    Create the HALT handler (priority, immediate).

    This handler triggers the halt mechanism.
    """

    class HaltHandler:
        def handle(self, intent: Intent) -> RouteResult:
            """Trigger halt signal."""
            from governance.halt import HaltManager

            reason = intent.payload.get("reason", "HALT intent received")

            # Create halt manager and trigger
            manager = HaltManager(module_id="watcher_halt")
            result = manager.request_halt()

            logger.critical(f"HALT triggered: {reason} (latency: {result.latency_ms:.3f}ms)")

            return RouteResult(
                success=True,
                intent=intent,
                worker_name="HALT_HANDLER",
            )

    return HaltHandler()
