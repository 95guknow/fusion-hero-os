# -*- coding: utf-8 -*-
"""Ollama / Llama-Local LLM Framework."""
from __future__ import annotations

import os
from typing import List, Tuple

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from .base import LLMFramework, get_http_session


class OllamaFramework(LLMFramework):
    provider_id = "ollama"
    display_name = "Ollama (Local Llama)"
    api_kind = "local"

    def api_key_env_vars(self):
        return ("OLLAMA_API_KEY",)  # optional, meist leer

    def base_url(self):
        return os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

    def default_model(self):
        return os.getenv("FUSION_OLLAMA_MODEL", "llama3.2")

    def aliases(self):
        return ("ollama", "llama", "llama-local", "local")

    def configured(self) -> bool:
        return True  # local, kein Key nötig

    def has_api_key(self) -> bool:
        return True

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        if requests is None:
            raise RuntimeError("requests nicht installiert")
        url = f"{self.base_url().rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.4},
        }
        sess = get_http_session("ollama", self.base_url())
        post = sess.post if sess else requests.post
        resp = post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        text = data.get("message", {}).get("content", "")
        return text, data


framework = OllamaFramework()