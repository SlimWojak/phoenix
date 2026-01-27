"""
Phoenix Intelligence Module
===========================

LLM integration layer for cognitive arbitrage.

Components:
- LLMClient: Unified interface for LLM backends
- OllamaBackend: Local Gemma via Ollama (cheap, fast)
- ClaudeBackend: Claude API (nuanced fallback)

DESIGN:
- Simple parsing → Gemma (local)
- Nuanced judgment → Claude (API)
- Schema validation on all outputs
"""

from .backends import ClaudeBackend, OllamaBackend
from .llm_client import LLMClient, LLMError, LLMResponse

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMError",
    "OllamaBackend",
    "ClaudeBackend",
]
