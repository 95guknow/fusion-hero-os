# -*- coding: utf-8 -*-
"""Fusion Hero OS v8 — LLM Framework Registry."""
from __future__ import annotations

from typing import Dict, List, Optional

from .base import FrameworkResult, LLMFramework
from . import grok, claude, gpt, gemini, openrouter, ollama

TRINITY_LLMS = ("grok", "claude", "gpt")

_FRAMEWORKS: Dict[str, LLMFramework] = {}
_ALIAS_MAP: Dict[str, str] = {}


def _register(fw: LLMFramework) -> None:
    _FRAMEWORKS[fw.provider_id] = fw
    for alias in fw.aliases():
        _ALIAS_MAP[alias.lower()] = fw.provider_id


_register(grok.framework)
_register(claude.framework)
_register(gpt.framework)
_register(gemini.framework)
_register(openrouter.framework)
_register(ollama.framework)


def normalize_provider(name: str) -> str:
    key = (name or "grok").strip().lower()
    return _ALIAS_MAP.get(key, key)


def get_framework(provider: str) -> Optional[LLMFramework]:
    pid = normalize_provider(provider)
    return _FRAMEWORKS.get(pid)


def list_frameworks() -> List[str]:
    return list(_FRAMEWORKS.keys())


def all_status() -> Dict[str, dict]:
    return {pid: fw.status() for pid, fw in _FRAMEWORKS.items()}


def connector_status() -> Dict[str, object]:
    statuses = all_status()
    available = [pid for pid, s in statuses.items() if s.get("configured")]
    return {
        "frameworks": statuses,
        "available": available,
        "trinity": list(TRINITY_LLMS),
        "any_live": any(s.get("api_key_set") for s in statuses.values()),
        "count": len(_FRAMEWORKS),
    }


def invoke(
    provider: str,
    prompt: str,
    role: str = "worker",
    context: Optional[dict] = None,
    timeout: Optional[int] = None,
) -> FrameworkResult:
    fw = get_framework(provider)
    if fw is None:
        fb = grok.framework._local_fallback(role, prompt, context)
        return FrameworkResult(
            provider_id=provider,
            model="unknown",
            role=role,
            response=fb,
            ok=False,
            error=f"Unbekannter Provider: {provider}",
            source="unknown_provider",
        )
    return fw.invoke(prompt, role=role, context=context, timeout=timeout)


def filter_llm_pool(pool: List[str], max_models: Optional[int] = None) -> List[str]:
    cap = max_models or 3
    env = __import__("os").getenv("FUSION_TRINITY_MAX_MODELS", "").strip()
    if env:
        cap = max(1, int(env))
    normed: List[str] = []
    for raw in pool or []:
        norm = normalize_provider(raw)
        if norm in _FRAMEWORKS and norm not in normed:
            normed.append(norm)
    if not normed:
        normed = list(TRINITY_LLMS)
    prefer = [m for m in TRINITY_LLMS if m in normed]
    rest = [m for m in normed if m not in prefer]
    return (prefer + rest)[: max(1, cap)]


def pick_thinker_model(pool: List[str]) -> str:
    if "llama-local" in pool or "ollama" in pool:
        return "ollama"
    for pref in ("claude", "gpt", "grok"):
        if pref in pool:
            return pref
    return pool[0] if pool else "ollama"


def pick_verifier_model(pool: List[str], thinker: str) -> str:
    for pref in ("grok",):
        if pref in pool:
            return pref
    for pref in ("grok", "claude", "gpt"):
        if pref in pool and pref != thinker and pref != "ollama":
            return pref
    return "grok"