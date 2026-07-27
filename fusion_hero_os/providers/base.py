"""Abstract Base + unified LLMResult for all LLM providers in Fusion Hero OS v8.5.

Now with capability profiles so the router can do dynamic, non-fixed task assignment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class LLMResult:
    provider: str
    response: str
    latency_ms: float = 0.0
    fallback_chain: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "response": self.response,
            "latency_ms": self.latency_ms,
            "fallback_chain": self.fallback_chain,
            "meta": self.meta,
            "success": self.success,
            "error": self.error,
        }


class BaseLLMProvider(ABC):
    """Common contract. Now carries capability profile for dynamic assignment."""

    name: str = "base"
    # Capability scores [0.0 - 1.0] per category. Router uses these for dynamic non-fixed assignment.
    capabilities: dict[str, float] = field(default_factory=dict)

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self._request_count: int = 0
        self._failure_count: int = 0
        self._last_latency: float = 0.0
        self._last_error: str | None = None
        # Default capabilities (overridden in concrete providers)
        if not self.capabilities:
            self.capabilities = {
                "code": 0.6,
                "current_events": 0.5,
                "simple_fact": 0.7,
                "creative": 0.6,
                "heroic_core": 0.5,
                "default": 0.6,
            }

    @abstractmethod
    def is_available(self) -> bool:
        ...

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None, **kwargs: Any) -> LLMResult:
        ...

    def health(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.is_available(),
            "request_count": self._request_count,
            "failure_count": self._failure_count,
            "last_latency_ms": self._last_latency,
            "last_error": self._last_error,
            "capabilities": self.capabilities,
        }

    def _record(self, success: bool, latency_ms: float, error: str | None = None) -> None:
        self._request_count += 1
        self._last_latency = latency_ms
        if success:
            self._failure_count = max(0, self._failure_count - 1)
        else:
            self._failure_count += 1
            self._last_error = error[:200] if error else None
