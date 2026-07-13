# -*- coding: utf-8 -*-
"""Fusion Hero OS v8 — Base LLM Framework."""
from __future__ import annotations

import json
import os
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests
except ImportError:
    requests = None  # type: ignore

DEFAULT_TIMEOUT = int(os.getenv("FUSION_MODEL_TIMEOUT", "90"))
DEFAULT_MAX_TOKENS = int(os.getenv("FUSION_MODEL_MAX_TOKENS", "2048"))

ROLE_SYSTEM = {
    "thinker": (
        "Du bist der THINKER in einer TRINITY-Orchestrierung (Fusion Hero OS v8). "
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

_HTTP_SESSIONS: Dict[str, Any] = {}


@dataclass
class FrameworkResult:
    provider_id: str
    model: str
    role: str
    response: str
    ok: bool
    latency_ms: float = 0.0
    error: Optional[str] = None
    source: str = "api"
    api_key_set: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def resolve_api_key(*env_names: str) -> Optional[str]:
    for name in env_names:
        val = os.getenv(name, "").strip()
        if val:
            return val
    return None


def extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None
    return None


def get_http_session(provider: str, base: str):
    if requests is None:
        return None
    key = f"{provider}:{base.rstrip('/')}"
    if key not in _HTTP_SESSIONS:
        sess = requests.Session()
        sess.headers.update({"Connection": "keep-alive"})
        _HTTP_SESSIONS[key] = sess
    return _HTTP_SESSIONS[key]


def openai_chat(
    base: str,
    api_key: str,
    model: str,
    messages: List[dict],
    timeout: int,
    provider: str = "openai",
    extra_headers: Optional[dict] = None,
) -> Tuple[str, dict]:
    if requests is None:
        raise RuntimeError("requests nicht installiert — pip install requests")
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
        "max_tokens": DEFAULT_MAX_TOKENS,
    }
    sess = get_http_session(provider, base)
    post = sess.post if sess else requests.post
    resp = post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]
    return content, data


def anthropic_chat(
    base: str,
    api_key: str,
    model: str,
    messages: List[dict],
    system: str,
    timeout: int,
) -> Tuple[str, dict]:
    if requests is None:
        raise RuntimeError("requests nicht installiert — pip install requests")
    url = f"{base.rstrip('/')}/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    user_parts = [m["content"] for m in messages if m["role"] == "user"]
    payload = {
        "model": model,
        "max_tokens": DEFAULT_MAX_TOKENS,
        "system": system,
        "messages": [{"role": "user", "content": "\n\n".join(user_parts)}],
    }
    sess = get_http_session("anthropic", base)
    post = sess.post if sess else requests.post
    resp = post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    blocks = data.get("content") or []
    text = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
    return text, data


class LLMFramework(ABC):
    """Einzelnes LLM-Framework — je Provider ein eigenständiges Modul."""

    provider_id: str = "base"
    display_name: str = "Base LLM"
    api_kind: str = "openai"  # openai | anthropic | gemini | local

    def __init__(self):
        self._model = self.default_model()

    @abstractmethod
    def api_key_env_vars(self) -> Tuple[str, ...]:
        """Environment variable names for API key lookup."""

    @abstractmethod
    def base_url(self) -> str:
        pass

    @abstractmethod
    def default_model(self) -> str:
        pass

    def aliases(self) -> Tuple[str, ...]:
        return (self.provider_id,)

    def get_api_key(self) -> Optional[str]:
        return resolve_api_key(*self.api_key_env_vars())

    def has_api_key(self) -> bool:
        return bool(self.get_api_key())

    def configured(self) -> bool:
        return self.has_api_key() or self.api_kind == "local"

    @property
    def model(self) -> str:
        env_key = f"FUSION_{self.provider_id.upper()}_MODEL"
        return os.getenv(env_key, self._model)

    def status(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "api_kind": self.api_kind,
            "model": self.model,
            "base_url": self.base_url(),
            "api_key_set": self.has_api_key(),
            "configured": self.configured(),
            "env_vars": list(self.api_key_env_vars()),
            "aliases": list(self.aliases()),
        }

    def _local_fallback(self, role: str, prompt: str, context: Optional[dict]) -> str:
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
                    f"[{self.provider_id}/{role}] Lokale Synthese — API-Key fehlt. "
                    f"Anfrage: {prompt[:300]}"
                ),
                "score": 62,
                "gaps": [f"Kein API-Key für {self.provider_id}"],
                "confidence": "low",
            }, ensure_ascii=False)
        hint = f" Fokus: {focus}" if focus else ""
        return f"[{self.provider_id}] Worker-Track ({routing}){hint}: {prompt[:400]}"

    def invoke(
        self,
        prompt: str,
        role: str = "worker",
        context: Optional[Dict] = None,
        timeout: Optional[int] = None,
    ) -> FrameworkResult:
        role = (role or "worker").lower()
        if role not in ROLE_SYSTEM:
            role = "worker"
        system = ROLE_SYSTEM[role]
        t0 = time.perf_counter()

        if not self.configured():
            text = self._local_fallback(role, prompt, context)
            return FrameworkResult(
                provider_id=self.provider_id,
                model=self.model,
                role=role,
                response=text,
                ok=True,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                source="local_fallback",
                api_key_set=False,
            )

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]
        try:
            text, raw = self._chat(messages, system, timeout or DEFAULT_TIMEOUT)
            return FrameworkResult(
                provider_id=self.provider_id,
                model=self.model,
                role=role,
                response=text,
                ok=True,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                source="api",
                api_key_set=True,
                raw={"model_id": self.model, "provider": self.provider_id},
            )
        except Exception as exc:
            fb = self._local_fallback(role, prompt, context)
            return FrameworkResult(
                provider_id=self.provider_id,
                model=self.model,
                role=role,
                response=fb,
                ok=False,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                error=str(exc),
                source="error_fallback",
                api_key_set=self.has_api_key(),
            )

    @abstractmethod
    def _chat(
        self,
        messages: List[dict],
        system: str,
        timeout: int,
    ) -> Tuple[str, dict]:
        pass