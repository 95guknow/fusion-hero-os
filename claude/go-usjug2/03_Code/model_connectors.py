# -*- coding: utf-8 -*-
"""
Fusion Hero OS v8 — Multi-Provider Model Connectors.
Backward-compatible facade over 03_Code/llm_frameworks/ (je LLM ein eigenes Framework).
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

_CODE_DIR = Path(__file__).resolve().parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

from llm_frameworks import (
    TRINITY_LLMS,
    connector_status as _framework_status,
    extract_json,
    filter_llm_pool,
    invoke as _invoke,
    normalize_provider,
    pick_thinker_model,
    pick_verifier_model,
)
from llm_frameworks.base import FrameworkResult

MODEL_ALIASES = {
    "grok": "grok", "xai": "grok", "grok-intern": "grok",
    "claude": "claude", "anthropic": "claude",
    "gpt": "gpt", "openai": "gpt", "chatgpt": "gpt",
    "gemini": "gemini", "google": "gemini", "antigravity": "gemini",
    "openrouter": "openrouter", "router": "openrouter",
    "ollama": "ollama", "llama": "ollama", "llama-local": "ollama",
}


@dataclass
class ConnectorResult:
    model: str
    role: str
    response: str
    provider: str
    ok: bool
    latency_ms: float = 0.0
    error: Optional[str] = None
    source: str = "api"
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _normalize_model(model: str) -> str:
    return normalize_provider(model)


def _to_connector_result(fr: FrameworkResult) -> ConnectorResult:
    return ConnectorResult(
        model=fr.provider_id,
        role=fr.role,
        response=fr.response,
        provider=fr.provider_id,
        ok=fr.ok,
        latency_ms=fr.latency_ms,
        error=fr.error,
        source=fr.source,
        raw=fr.raw,
    )


def connector_status() -> Dict[str, Any]:
    status = _framework_status()
    providers = {
        pid: info.get("api_key_set", False) or info.get("configured", False)
        for pid, info in status.get("frameworks", {}).items()
    }
    return {
        "providers": providers,
        "available": status.get("available", []),
        "any_live": status.get("any_live", False),
        "frameworks": status.get("frameworks", {}),
        "trinity": list(TRINITY_LLMS),
    }


def invoke_model(
    model: str,
    prompt: str,
    role: str = "worker",
    context: Optional[Dict] = None,
    timeout: Optional[int] = None,
) -> ConnectorResult:
    """Ruft ein Modell über das jeweilige LLM-Framework auf."""
    fr = _invoke(model, prompt, role=role, context=context, timeout=timeout)
    return _to_connector_result(fr)


# Re-exports für bestehenden Code
__all__ = [
    "TRINITY_LLMS",
    "MODEL_ALIASES",
    "ConnectorResult",
    "connector_status",
    "extract_json",
    "filter_llm_pool",
    "invoke_model",
    "pick_thinker_model",
    "pick_verifier_model",
]