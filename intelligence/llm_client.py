"""
LLM Client — Unified Interface
==============================

Unified interface for LLM backends with:
- Schema validation
- Retry logic
- Fallback (Gemma → Claude)

COGNITIVE ARBITRAGE:
- Try Gemma first (cheap, fast)
- Fall back to Claude if needed (nuanced)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .backends import ClaudeBackend, LLMBackend, OllamaBackend

# =============================================================================
# EXCEPTIONS
# =============================================================================


class LLMError(Exception):
    """Base exception for LLM errors."""

    pass


class LLMParseError(LLMError):
    """Failed to parse LLM output."""

    pass


class LLMValidationError(LLMError):
    """LLM output failed schema validation."""

    pass


class LLMUnavailableError(LLMError):
    """No LLM backend available."""

    pass


# =============================================================================
# RESPONSE
# =============================================================================


@dataclass
class LLMResponse:
    """Response from LLM client."""

    content: str
    parsed: dict[str, Any] | None = None
    model: str = ""
    tokens_used: int = 0
    backend: str = ""
    retries: int = 0
    errors: list[str] = field(default_factory=list)


# =============================================================================
# LLM CLIENT
# =============================================================================


class LLMClient:
    """
    Unified LLM client with cognitive arbitrage.

    Usage:
        client = LLMClient()
        response = client.complete_json(prompt, schema)
        if response.parsed:
            use(response.parsed)
    """

    def __init__(
        self,
        primary: LLMBackend | None = None,
        fallback: LLMBackend | None = None,
        enable_fallback: bool = True,
    ) -> None:
        """
        Initialize LLM client.

        Args:
            primary: Primary backend (default: Ollama/Gemma)
            fallback: Fallback backend (default: Claude)
            enable_fallback: Whether to use fallback on failure
        """
        self._primary = primary or OllamaBackend()
        self._fallback = fallback or ClaudeBackend()
        self._enable_fallback = enable_fallback

    def complete(
        self,
        prompt: str,
        system: str | None = None,
    ) -> LLMResponse:
        """
        Generate completion.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            LLMResponse
        """
        errors: list[str] = []

        # Try primary backend
        if self._primary.is_available():
            try:
                result = self._primary.complete(prompt, system)
                return LLMResponse(
                    content=result.content,
                    model=result.model,
                    tokens_used=result.tokens_used,
                    backend="primary",
                )
            except Exception as e:
                errors.append(f"Primary failed: {e}")

        # Try fallback
        if self._enable_fallback and self._fallback.is_available():
            try:
                result = self._fallback.complete(prompt, system)
                return LLMResponse(
                    content=result.content,
                    model=result.model,
                    tokens_used=result.tokens_used,
                    backend="fallback",
                    errors=errors,
                )
            except Exception as e:
                errors.append(f"Fallback failed: {e}")

        raise LLMUnavailableError(f"No backend available: {errors}")

    def complete_json(
        self,
        prompt: str,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        retries: int = 2,
    ) -> LLMResponse:
        """
        Generate JSON completion with validation.

        Args:
            prompt: User prompt (should request JSON output)
            schema: Optional JSON schema for validation
            system: Optional system prompt
            retries: Number of retries on parse/validation failure

        Returns:
            LLMResponse with parsed JSON
        """
        errors: list[str] = []

        for attempt in range(retries + 1):
            try:
                response = self.complete(prompt, system)
                parsed = self._extract_json(response.content)

                if schema:
                    self._validate_schema(parsed, schema)

                return LLMResponse(
                    content=response.content,
                    parsed=parsed,
                    model=response.model,
                    tokens_used=response.tokens_used,
                    backend=response.backend,
                    retries=attempt,
                    errors=errors,
                )

            except LLMParseError as e:
                errors.append(f"Attempt {attempt + 1}: Parse error - {e}")
            except LLMValidationError as e:
                errors.append(f"Attempt {attempt + 1}: Validation error - {e}")
            except LLMUnavailableError:
                raise
            except Exception as e:
                errors.append(f"Attempt {attempt + 1}: {e}")

        raise LLMParseError(f"Failed after {retries + 1} attempts: {errors}")

    def _extract_json(self, content: str) -> dict[str, Any]:
        """
        Extract JSON from LLM response.

        Handles:
        - Raw JSON
        - JSON in markdown code blocks
        - JSON with leading/trailing text
        """
        # Try direct parse
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting from code block
        code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if code_block:
            try:
                return json.loads(code_block.group(1).strip())
            except json.JSONDecodeError:
                pass

        # Try finding JSON object
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise LLMParseError(f"Could not extract JSON from: {content[:200]}...")

    def _validate_schema(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
    ) -> None:
        """
        Validate data against schema.

        Simple validation - checks required fields exist.
        """
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field_name in required:
            if field_name not in data:
                raise LLMValidationError(f"Missing required field: {field_name}")

        # Type checking for known fields
        for field_name, field_schema in properties.items():
            if field_name not in data:
                continue

            value = data[field_name]
            expected_type = field_schema.get("type")

            if expected_type == "string" and not isinstance(value, str):
                raise LLMValidationError(
                    f"Field {field_name} should be string, got {type(value)}"
                )
            elif expected_type == "number" and not isinstance(value, (int, float)):
                raise LLMValidationError(
                    f"Field {field_name} should be number, got {type(value)}"
                )
            elif expected_type == "array" and not isinstance(value, list):
                raise LLMValidationError(
                    f"Field {field_name} should be array, got {type(value)}"
                )

    def is_available(self) -> bool:
        """Check if any backend is available."""
        return self._primary.is_available() or (
            self._enable_fallback and self._fallback.is_available()
        )

    def available_backends(self) -> list[str]:
        """List available backends."""
        available = []
        if self._primary.is_available():
            available.append("primary")
        if self._enable_fallback and self._fallback.is_available():
            available.append("fallback")
        return available
