# -*- coding: utf-8 -*-
"""OpenRouter LLM Framework — Multi-Model Gateway."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class OpenRouterFramework(LLMFramework):
    provider_id = "openrouter"
    display_name = "OpenRouter"
    api_kind = "openai"

    ROUTE_MAP = {
        "grok": "x-ai/grok-2-latest",
        "claude": "anthropic/claude-3.5-sonnet",
        "gpt": "openai/gpt-4o-mini",
        "gemini": "google/gemini-2.0-flash-001",
    }

    def api_key_env_vars(self):
        return ("OPENROUTER_API_KEY",)

    def base_url(self):
        return os.getenv("FUSION_OPENROUTER_BASE", "https://openrouter.ai/api/v1")

    def default_model(self):
        return os.getenv("FUSION_OPENROUTER_MODEL", "openai/gpt-4o-mini")

    def aliases(self):
        return ("openrouter", "router")

    def route_for(self, target: str) -> str:
        return self.ROUTE_MAP.get(target, self.default_model())

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY nicht gesetzt")
        extra = {
            "HTTP-Referer": os.getenv("FUSION_OPENROUTER_REF", "https://fusion-hero-os.local"),
            "X-Title": "Fusion Hero OS v8",
        }
        return openai_chat(
            self.base_url(),
            api_key,
            self.model,
            messages,
            timeout,
            provider="openrouter",
            extra_headers=extra,
        )


framework = OpenRouterFramework()