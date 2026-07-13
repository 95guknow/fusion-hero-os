"""Provider package for Universal LLM Router v8.4+.

Clean abstraction so the router stays slim and new providers (local models, QUBO-optimized, etc.) can be added without touching routing logic.
"""

from __future__ import annotations

from .base import BaseLLMProvider, LLMResult

from .claude_provider import ClaudeProvider

from .grok_provider import GrokProvider

from .everyapi_provider import EveryAPIProvider

from .internal_provider import InternalFallbackProvider

__all__ = [
    "BaseLLMProvider",
    "LLMResult",
    "ClaudeProvider",
    "GrokProvider",
    "EveryAPIProvider",
    "InternalFallbackProvider",
]
