# -*- coding: utf-8 -*-
"""Grok / xAI LLM Framework."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class GrokFramework(LLMFramework):
    provider_id = "grok"
    display_name = "Grok (xAI)"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("XAI_API_KEY", "GROK_API_KEY")

    def base_url(self):
        return os.getenv("FUSION_GROK_BASE", "https://api.x.ai/v1")

    def default_model(self):
        return os.getenv("FUSION_GROK_MODEL", "grok-2-latest")

    def aliases(self):
        return ("grok", "xai", "grok-intern")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("XAI_API_KEY oder GROK_API_KEY nicht gesetzt")
        return openai_chat(
            self.base_url(), api_key, self.model, messages, timeout, provider="grok"
        )


framework = GrokFramework()