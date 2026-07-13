# -*- coding: utf-8 -*-
"""Claude / Anthropic LLM Framework."""
from __future__ import annotations

import os
from typing import List, Tuple

from .base import LLMFramework, anthropic_chat


class ClaudeFramework(LLMFramework):
    provider_id = "claude"
    display_name = "Claude (Anthropic)"
    api_kind = "anthropic"

    def api_key_env_vars(self):
        return ("ANTHROPIC_API_KEY",)

    def base_url(self):
        return os.getenv("FUSION_CLAUDE_BASE", "https://api.anthropic.com")

    def default_model(self):
        return os.getenv("FUSION_CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    def aliases(self):
        return ("claude", "anthropic")

    def _chat(self, messages: List[dict], system: str, timeout: int) -> Tuple[str, dict]:
        api_key = self.get_api_key()
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY nicht gesetzt")
        return anthropic_chat(
            self.base_url(), api_key, self.model, messages, system, timeout
        )


framework = ClaudeFramework()