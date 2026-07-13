"""EveryAPI provider v8.5 - good for simple_fact / general tasks."""

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None

from .base import BaseLLMProvider, LLMResult


class EveryAPIProvider(BaseLLMProvider):
    name = "everyapi"
    capabilities = {
        "code": 0.55,
        "current_events": 0.60,
        "simple_fact": 0.88,
        "creative": 0.65,
        "heroic_core": 0.50,
        "default": 0.70,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.api_key = os.getenv("EVERYAPI_KEY")
        self.base_url = os.getenv("EVERYAPI_BASE_URL", "https://api.everyapi.com/v1/chat")
        self.model = os.getenv("EVERYAPI_MODEL", "general")

    def is_available(self) -> bool:
        return bool(self.api_key and requests)

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> LLMResult:
        if not self.is_available():
            return LLMResult(self.name, "", success=False, error="EveryAPI not configured")
        start = time.time()
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            payload = {"model": self.model, "message": prompt, "max_tokens": kwargs.get("max_tokens", 2048)}
            r = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
            if r.status_code == 200:
                data = r.json()
                text = data.get("response") or data.get("text") or str(data)
                latency = (time.time() - start) * 1000
                self._record(True, latency)
                return LLMResult("everyapi", text, latency, meta={"endpoint": self.base_url})
            else:
                latency = (time.time() - start) * 1000
                self._record(False, latency, f"HTTP {r.status_code}")
                return LLMResult(self.name, "", latency, success=False, error=f"HTTP {r.status_code}")
        except Exception as e:
            latency = (time.time() - start) * 1000
            self._record(False, latency, str(e))
            return LLMResult(self.name, "", latency, success=False, error=str(e)[:300])
