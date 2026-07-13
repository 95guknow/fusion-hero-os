"""Claude provider v8.5 with strong capability profile for dynamic assignment."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from .base import BaseLLMProvider, LLMResult


class ClaudeProvider(BaseLLMProvider):
    name = "claude"
    capabilities = {
        "code": 0.95,
        "current_events": 0.65,
        "simple_fact": 0.75,
        "creative": 0.88,
        "heroic_core": 0.82,
        "default": 0.80,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.client = Anthropic(api_key=self.api_key) if (Anthropic and self.api_key) else None

    def is_available(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> LLMResult:
        if not self.is_available():
            return LLMResult(self.name, "", success=False, error="Claude not configured")
        start = time.time()
        try:
            sys_prompt = system_prompt or "Du bist der native v8.5 Heroic Core Assistent."
            resp = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", 2048),
                system=sys_prompt,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text if resp.content else "[Claude: keine Antwort]"
            latency = (time.time() - start) * 1000
            self._record(True, latency)
            return LLMResult("claude (Anthropic)", text, latency, meta={"model": self.model, "capabilities_used": self.capabilities})
        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record(False, latency, str(e))
            return LLMResult(self.name, "", latency, success=False, error=str(e)[:300])
