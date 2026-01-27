"""
LLM Backends — Ollama + Claude
==============================

Backend implementations for LLM client.

BACKENDS:
- OllamaBackend: Local Gemma via Ollama (default)
- ClaudeBackend: Claude API fallback

COGNITIVE ARBITRAGE:
- Simple parsing: Gemma (fast, cheap, always-on)
- Nuanced judgment: Claude (expensive, when needed)
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

# =============================================================================
# BASE BACKEND
# =============================================================================


@dataclass
class BackendResponse:
    """Response from LLM backend."""

    content: str
    model: str
    tokens_used: int
    raw_response: dict[str, Any] | None = None


class LLMBackend(ABC):
    """Abstract base for LLM backends."""

    @abstractmethod
    def complete(self, prompt: str, system: str | None = None) -> BackendResponse:
        """Generate completion."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available."""
        pass


# =============================================================================
# OLLAMA BACKEND (Gemma)
# =============================================================================


class OllamaBackend(LLMBackend):
    """
    Ollama backend for local models.

    Default for simple parsing tasks (cognitive arbitrage).
    Supports: gemma3:4b, glm4, inquisitor, etc.
    """

    def __init__(
        self,
        model: str = "gemma3:4b",
        base_url: str = "http://localhost:11434",
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize Ollama backend.

        Args:
            model: Ollama model name
            base_url: Ollama API URL
            timeout: Request timeout
        """
        self._model = model
        self._base_url = base_url
        self._timeout = timeout

    def complete(self, prompt: str, system: str | None = None) -> BackendResponse:
        """
        Generate completion via Ollama.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            BackendResponse
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temp for structured output
                "num_predict": 1024,
            },
        }

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data.get("message", {}).get("content", "")
        tokens = data.get("eval_count", 0) + data.get("prompt_eval_count", 0)

        return BackendResponse(
            content=content,
            model=self._model,
            tokens_used=tokens,
            raw_response=data,
        )

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self._base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False


# =============================================================================
# CLAUDE BACKEND
# =============================================================================


class ClaudeBackend(LLMBackend):
    """
    Claude API backend.

    Used for nuanced judgment when Gemma isn't sufficient.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "claude-sonnet-4-20250514",
        timeout: float = 60.0,
    ) -> None:
        """
        Initialize Claude backend.

        Args:
            api_key: Anthropic API key (or from env)
            model: Claude model name
            timeout: Request timeout
        """
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model
        self._timeout = timeout
        self._base_url = "https://api.anthropic.com/v1"

    def complete(self, prompt: str, system: str | None = None) -> BackendResponse:
        """
        Generate completion via Claude API.

        Args:
            prompt: User prompt
            system: Optional system prompt

        Returns:
            BackendResponse
        """
        if not self._api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        payload: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system:
            payload["system"] = system

        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(
                f"{self._base_url}/messages",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Extract content from Claude response
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")

        tokens = data.get("usage", {})
        total_tokens = tokens.get("input_tokens", 0) + tokens.get("output_tokens", 0)

        return BackendResponse(
            content=content,
            model=self._model,
            tokens_used=total_tokens,
            raw_response=data,
        )

    def is_available(self) -> bool:
        """Check if Claude API is configured."""
        return bool(self._api_key)
