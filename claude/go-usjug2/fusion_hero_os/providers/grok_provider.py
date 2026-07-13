"""Grok provider v8.5 with real-time / current_events strength."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base import BaseLLMProvider, LLMResult


class GrokProvider(BaseLLMProvider):
    name = "grok"
    capabilities = {
        "code": 0.70,
        "current_events": 0.92,
        "simple_fact": 0.78,
        "creative": 0.75,
        "heroic_core": 0.65,
        "default": 0.72,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.api_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
        self.model = os.getenv("GROK_MODEL", "grok-2-1212")
        self.client = OpenAI(api_key=self.api_key, base_url="https://api.x.ai/v1") if (OpenAI and self.api_key) else None

    def is_available(self) -> bool:
        return self.client is not None

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> LLMResult:
        if not self.is_available():
            return LLMResult(self.name, "", success=False, error="Grok not configured")
        start = time.time()
        try:
            sys_prompt = system_prompt or "Du bist der native v8.5 Echtzeit-Assistent (Grok)."
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=kwargs.get("max_tokens", 2048),
                temperature=0.7,
            )
            text = resp.choices[0].message.content or "[Grok: keine Antwort]"
            latency = (time.time() - start) * 1000
            self._record(True, latency)
            return LLMResult("grok (xAI)", text, latency, meta={"model": self.model})
        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record(False, latency, str(e))
            return LLMResult(self.name, "", latency, success=False, error=str(e)[:300])
