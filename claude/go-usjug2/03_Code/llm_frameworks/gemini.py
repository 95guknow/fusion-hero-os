# -*- coding: utf-8 -*-
"""Gemini / Google LLM Framework."""
from __future__ import annotations

import os
from typing import List, Tuple

try:
    import requests
except ImportError:
    requests = None  # type: ignore

from .base import LLMFramework, get_http_session


class GeminiFramework(LLMFramework):
    provider_id = "gemini"
    display_name = "Gemini (Google)"
    api_kind = "gemini"

    def api_key_env_vars(self):
        return ("GOOGLE_API_KEY", "GEMINI_API_KEY")

    def base_url(self):
        return os.getenv(
            "FUSION_GEMINI_BASE",
            "https://generativelanguage.googleapis.com/v1beta",
        )

    def default_model(self):
        return os.getenv("FUSION_GEMINI_MODEL", "gemini-2.0-flash")

    def aliases(self):
        return ("gemini", "google", "antigravity")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        if requests is None:
            raise RuntimeError("requests nicht installiert")
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("GOOGLE_API_KEY oder GEMINI_API_KEY nicht gesetzt")

        user_text = "\n\n".join(m["content"] for m in messages if m["role"] == "user")
        url = (
            f"{self.base_url().rstrip('/')}/models/{self.model}:generateContent"
            f"?key={api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 2048},
        }
        sess = get_http_session("gemini", self.base_url())
        post = sess.post if sess else requests.post
        resp = post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        text = "".join(p.get("text", "") for p in parts)
        return text, data


framework = GeminiFramework()