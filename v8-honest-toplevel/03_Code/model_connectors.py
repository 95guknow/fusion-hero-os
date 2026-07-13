# -*- coding: utf-8 -*-
"""Fusion Hero OS v1.2 — Multi-Provider Model Connectors."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    requests = None  # type: ignore

DEFAULT_TIMEOUT = int(os.getenv("FUSION_MODEL_TIMEOUT", "90"))
TRINITY_LLMS = ("grok", "claude", "gpt")
_HTTP_SESSIONS: Dict[str, Any] = {}

MODEL_ALIASES = {
    "grok": "grok",
    "xai": "grok",
    "claude": "claude",
    "anthropic": "claude",
    "gpt": "gpt",
    "openai": "gpt",
    "chatgpt": "gpt",
}

PROVIDER_DEFAULTS = {
    "grok": {
        "env": "XAI_API_KEY",
        "alt_env": ("GROK_API_KEY",),
        "base": "https://api.x.ai/v1",
        "model": os.getenv("FUSION_GROK_MODEL", "grok-2-latest"),
        "kind": "openai",
    },
    "claude": {
        "env": "ANTHROPIC_API_KEY",
        "base": "https://api.anthropic.com",
        "model": os.getenv("FUSION_CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
        "kind": "anthropic",
    },
    "gpt": {
        "env": "OPENAI_API_KEY",
        "base": "https://api.openai.com/v1",
        "model": os.getenv("FUSION_GPT_MODEL", "gpt-4o-mini"),
        "kind": "openai",
    },
}

OPENROUTER = {
    "env": "OPENROUTER_API_KEY",
    "base": "https://openrouter.ai/api/v1",
    "kind": "openai",
}

ROLE_SYSTEM = {
    "thinker": (
        "Du bist der THINKER in einer TRINITY-Orchestrierung (Fusion Hero OS v1.2). "
        "Zerlege die Nutzeranfrage in 2–4 fokussierte Teilaspekte. "
        "Antworte NUR als JSON: "
        '{"subtasks":[{"id":"t1","focus":"...","hint":"..."}],"strategy":"kurz"}'
    ),
    "worker": (
        "Du bist ein WORKER in einer TRINITY-Orchestrierung. "
        "Bearbeite NUR deinen zugewiesenen Fokus präzise und evidenzbasiert. "
        "Keine Meta-Kommentare über die Pipeline."
    ),
    "verifier": (
        "Du bist der VERIFIER in einer TRINITY-Orchestrierung. "
        "Prüfe Worker-Outputs auf Konsistenz, Lücken und Risiken. "
        "Antworte als JSON: "
        '{"synthesis":"...","score":0-100,"gaps":["..."],"confidence":"low|medium|high"}'
    ),
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
    key = (model or "grok").strip().lower()
    return MODEL_ALIASES.get(key, key)


def _api_key(*names: str) -> Optional[str]:
    for name in names:
        val = os.getenv(name, "").strip()
        if val:
            return val
    return None


def _provider_for(model: str) -> Tuple[str, dict]:
    norm = _normalize_model(model)
    if norm in PROVIDER_DEFAULTS:
        cfg = PROVIDER_DEFAULTS[norm]
        key = _api_key(cfg["env"], *cfg.get("alt_env", ()))
        if key:
            return norm, {**cfg, "api_key": key}
    or_key = _api_key(OPENROUTER["env"])
    if or_key:
        route = {
            "grok": "x-ai/grok-2-latest",
            "claude": "anthropic/claude-3.5-sonnet",
            "gpt": "openai/gpt-4o-mini",
        }.get(norm, model)
        return "openrouter", {
            **OPENROUTER,
            "api_key": or_key,
            "model": route,
            "kind": "openai",
        }
    return "local", {"kind": "local", "model": model}


def _trinity_cap(max_models: Optional[int] = None) -> int:
    if max_models is not None:
        return max(1, max_models)
    env = os.getenv("FUSION_TRINITY_MAX_MODELS", "").strip()
    if env:
        return max(1, int(env))
    try:
        from fusion_profile import get_profile_config
        return max(1, int(get_profile_config().get("trinity_max_models", 3)))
    except Exception:
        return 3


def filter_llm_pool(pool: List[str], max_models: Optional[int] = None) -> List[str]:
    """TRINITY nur echte LLMs — Agent-IDs aus Resource-Plan ausschließen."""
    cap = _trinity_cap(max_models)
    normed: List[str] = []
    for raw in pool or []:
        norm = _normalize_model(raw)
        if norm in PROVIDER_DEFAULTS and norm not in normed:
            normed.append(norm)
    if not normed:
        normed = list(TRINITY_LLMS)
    prefer = [m for m in TRINITY_LLMS if m in normed]
    rest = [m for m in normed if m not in prefer]
    return (prefer + rest)[: max(1, cap)]


def _get_http_session(provider: str, base: str):
    if requests is None:
        return None
    key = f"{provider}:{base.rstrip('/')}"
    if key not in _HTTP_SESSIONS:
        sess = requests.Session()
        sess.headers.update({"Connection": "keep-alive"})
        _HTTP_SESSIONS[key] = sess
    return _HTTP_SESSIONS[key]


def connector_status() -> Dict[str, Any]:
    providers: Dict[str, bool] = {}
    for name, cfg in PROVIDER_DEFAULTS.items():
        providers[name] = bool(_api_key(cfg["env"], *cfg.get("alt_env", ())))
    providers["openrouter"] = bool(_api_key(OPENROUTER["env"]))
    available = [m for m, ok in providers.items() if ok]
    return {
        "providers": providers,
        "available": available,
        "any_live": bool(available),
        "requests_installed": requests is not None,
        "http_sessions": len(_HTTP_SESSIONS),
    }


def extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _openai_chat(
    base: str,
    api_key: str,
    model: str,
    messages: List[dict],
    timeout: int,
    extra_headers: Optional[dict] = None,
    provider: str = "openai",
) -> Tuple[str, dict]:
    if requests is None:
        raise RuntimeError("requests nicht installiert")
    url = f"{base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": int(os.getenv("FUSION_MODEL_MAX_TOKENS", "1024")),
    }
    sess = _get_http_session(provider, base)
    post = sess.post if sess else requests.post
    resp = post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return content, data


def _anthropic_chat(
    base: str,
    api_key: str,
    model: str,
    messages: List[dict],
    system: str,
    timeout: int,
) -> Tuple[str, dict]:
    if requests is None:
        raise RuntimeError("requests nicht installiert")
    url = f"{base.rstrip('/')}/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    user_parts = []
    for msg in messages:
        if msg["role"] == "user":
            user_parts.append(msg["content"])
    payload = {
        "model": model,
        "max_tokens": int(os.getenv("FUSION_MODEL_MAX_TOKENS", "2048")),
        "system": system,
        "messages": [{"role": "user", "content": "\n\n".join(user_parts)}],
    }
    sess = _get_http_session("anthropic", base)
    post = sess.post if sess else requests.post
    resp = post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    blocks = data.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    return text, data


def _local_fallback(model: str, role: str, prompt: str, context: Optional[dict]) -> str:
    ctx = context or {}
    routing = ctx.get("routing", "orchestrate")
    focus = ctx.get("focus", "")
    if role == "thinker":
        return json.dumps({
            "subtasks": [
                {"id": "t1", "focus": "Kernanalyse", "hint": prompt[:200]},
                {"id": "t2", "focus": "Alternativen & Risiken", "hint": "Gegenpositionen prüfen"},
            ],
            "strategy": f"lokaler Thinker-Fallback ({routing})",
        }, ensure_ascii=False)
    if role == "verifier":
        return json.dumps({
            "synthesis": (
                f"[{model}/{role}] Lokale Synthese — API-Key fehlt. "
                f"Anfrage: {prompt[:300]}"
            ),
            "score": 62,
            "gaps": ["Kein Live-Connector — nur Struktur-Fallback"],
            "confidence": "low",
        }, ensure_ascii=False)
    hint = f" Fokus: {focus}" if focus else ""
    return (
        f"[{model}] Worker-Track ({routing}){hint}: "
        f"{prompt[:400]}"
    )


def invoke_model(
    model: str,
    prompt: str,
    role: str = "worker",
    context: Optional[Dict] = None,
    timeout: Optional[int] = None,
) -> ConnectorResult:
    """Ruft ein Modell mit Rollen-Prompt auf; fällt auf lokal zurück."""
    role = (role or "worker").lower()
    if role not in ROLE_SYSTEM:
        role = "worker"
    provider_name, cfg = _provider_for(model)
    t0 = time.perf_counter()
    system = ROLE_SYSTEM[role]

    if cfg.get("kind") == "local":
        text = _local_fallback(model, role, prompt, context)
        return ConnectorResult(
            model=model,
            role=role,
            response=text,
            provider="local",
            ok=True,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            source="local_fallback",
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]
    try:
        if cfg["kind"] == "anthropic":
            text, raw = _anthropic_chat(
                cfg["base"], cfg["api_key"], cfg["model"], messages, system,
                timeout or DEFAULT_TIMEOUT,
            )
        else:
            extra = {}
            if provider_name == "openrouter":
                extra["HTTP-Referer"] = os.getenv("FUSION_OPENROUTER_REF", "https://fusion-hero-os.local")
                extra["X-Title"] = "Fusion Hero OS v1.2"
            text, raw = _openai_chat(
                cfg["base"], cfg["api_key"], cfg["model"], messages,
                timeout or DEFAULT_TIMEOUT, extra_headers=extra or None,
                provider=provider_name,
            )
        return ConnectorResult(
            model=model,
            role=role,
            response=text,
            provider=provider_name,
            ok=True,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            source="api",
            raw={"model_id": cfg.get("model")},
        )
    except Exception as exc:
        fb = _local_fallback(model, role, prompt, context)
        return ConnectorResult(
            model=model,
            role=role,
            response=fb,
            provider=provider_name,
            ok=False,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            error=str(exc),
            source="error_fallback",
        )


def pick_thinker_model(pool: List[str]) -> str:
    """Agent/Thinker → Llama (lokal), sonst Trinity-Fallback."""
    if "llama-local" in pool:
        return "llama-local"
    for pref in ("claude", "gpt", "grok"):
        if pref in pool:
            return pref
    return pool[0] if pool else "llama-local"


def pick_verifier_model(pool: List[str], thinker: str) -> str:
    """Anti-Agent/Verifier → Grok."""
    for pref in ("grok", "grok-intern"):
        if pref in pool or pref == "grok-intern":
            return "grok"
    for pref in ("grok", "claude", "gpt"):
        if pref in pool and pref != thinker and pref != "llama-local":
            return pref
    return "grok"