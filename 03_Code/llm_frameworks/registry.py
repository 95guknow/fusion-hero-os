# -*- coding: utf-8 -*-
"""Fusion Hero OS v8 — LLM Framework Registry."""
from __future__ import annotations

from typing import Dict, List, Optional

from .base import FrameworkResult, LLMFramework
from . import grok, claude, gpt, gemini, openrouter, ollama, nvidia_nim
from . import groq, huggingface, cloudflare_ai, github_models, openrouter_free

TRINITY_LLMS = ("grok", "claude", "gpt")

# Pseudo-inhouse free chain (first available wins — see pseudo_inhouse_ai)
FREE_CHAIN = (
    "ollama",
    "openrouter_free",
    "groq",
    "gemini",
    "huggingface",
    "cloudflare_ai",
    "nvidia",
    "github_models",
)

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
_register(openrouter_free.framework)
_register(ollama.framework)
_register(nvidia_nim.framework)
_register(groq.framework)
_register(huggingface.framework)
_register(cloudflare_ai.framework)
_register(github_models.framework)


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
    free_ready = [
        pid
        for pid in FREE_CHAIN
        if pid in statuses and statuses[pid].get("configured")
    ]
    # Kreuzvernetzung: jeder Provider sieht alle Peers
    peers = {
        pid: [p for p in _FRAMEWORKS.keys() if p != pid]
        for pid in _FRAMEWORKS
    }
    return {
        "frameworks": statuses,
        "available": available,
        "trinity": list(TRINITY_LLMS),
        "free_chain": list(FREE_CHAIN),
        "free_ready": free_ready,
        "any_live": any(s.get("api_key_set") for s in statuses.values())
        or "ollama" in free_ready,
        "count": len(_FRAMEWORKS),
        "pseudo_inhouse": True,
        "cross_mesh": {
            "enabled": True,
            "mode": "complete_graph",
            "peers": peers,
            "undirected_pairs": len(_FRAMEWORKS) * max(0, len(_FRAMEWORKS) - 1) // 2,
            "endpoint": "/fusion/cross",
        },
    }


def cross_mesh_peers(provider: str) -> List[str]:
    """Alle anderen Frameworks als Kreuz-Nachbarn."""
    pid = normalize_provider(provider)
    return [p for p in _FRAMEWORKS.keys() if p != pid]


def free_ready_providers() -> List[str]:
    statuses = all_status()
    out: List[str] = []
    for pid in FREE_CHAIN:
        s = statuses.get(pid) or {}
        if s.get("configured") or pid == "ollama":
            # ollama always "configured"; probe separately for live
            out.append(pid)
    return out


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