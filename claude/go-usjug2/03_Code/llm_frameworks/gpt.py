# -*- coding: utf-8 -*-
"""GPT / OpenAI LLM Framework."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, openai_chat


class GPTFramework(LLMFramework):
    provider_id = "gpt"
    display_name = "GPT (OpenAI)"
    api_kind = "openai"

    def api_key_env_vars(self):
        return ("OPENAI_API_KEY",)

    def base_url(self):
        return os.getenv("FUSION_GPT_BASE", "https://api.openai.com/v1")

    def default_model(self):
        return os.getenv("FUSION_GPT_MODEL", "gpt-4o-mini")

    def aliases(self):
        return ("gpt", "openai", "chatgpt")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY nicht gesetzt")
        return openai_chat(
            self.base_url(), api_key, self.model, messages, timeout, provider="gpt"
        )


framework = GPTFramework()