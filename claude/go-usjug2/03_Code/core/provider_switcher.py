# provider_switcher.py — Automatischer LLM-Anbieterwechsler

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

_DEFAULT_ORDER = ("llama-local", "claude-science", "grok-intern", "fusion-hero")
_active_backend: Optional[str] = None
_last_switch_ts: float = 0.0


def is_auto_enabled() -> bool:
    return os.getenv("FUSION_PROVIDER_AUTO", "1") == "1"


def provider_order() -> List[str]:
    raw = os.getenv("FUSION_PROVIDER_ORDER", ",".join(_DEFAULT_ORDER))
    order = [p.strip() for p in raw.split(",") if p.strip()]
    return order or list(_DEFAULT_ORDER)


def _llama_ok() -> bool:
    try:
        from local_llama import get_local_llama

        llama = get_local_llama()
        if not llama.active:
            return False
        port = int(os.getenv("FUSION_LLAMA_SERVER_PORT", "8081"))
        import httpx

        r = httpx.get(f"http://127.0.0.1:{port}/health", timeout=1.5)
        return r.status_code < 500
    except Exception:
        try:
            from local_llama import get_local_llama

            return get_local_llama().active
        except Exception:
            return False


def _grok_ok() -> bool:
    # Grok-intern = Skill-Bridge im Dashboard; immer erreichbar wenn Backend läuft
    return True


def _fusion_ok() -> bool:
    return True


def _claude_science_ok() -> bool:
    try:
        from claude_science import is_available

        return is_available()
    except Exception:
        return os.getenv("FUSION_CLAUDE_SCIENCE", "1") == "1"


def _check(provider: str) -> bool:
    if provider == "llama-local":
        return _llama_ok()
    if provider == "claude-science":
        return _claude_science_ok()
    if provider == "grok-intern":
        return _grok_ok()
    if provider == "fusion-hero":
        return _fusion_ok()
    return False


def select_provider_for_role(role: str = "agent", task: Optional[Dict[str, Any]] = None) -> str:
    """Agent → Llama, Anti-Agent → Grok."""
    try:
        from agent_backend_router import backend_for_role, is_dual_agent_enabled

        if is_dual_agent_enabled():
            backend = backend_for_role(role, task)
            global _active_backend, _last_switch_ts
            if _check(backend):
                if _active_backend != backend:
                    _last_switch_ts = time.time()
                _active_backend = backend
                os.environ["FUSION_LLM_BACKEND"] = backend
                return backend
    except Exception:
        pass
    return select_provider(force_probe=True)


def select_provider_for_query(query: str, force_probe: bool = False) -> str:
    """Wählt Anbieter — Science/Heroik-Wissenschaft → claude-science (API oder Fallback)."""
    try:
        from claude_science import should_use_claude_science

        use, reason = should_use_claude_science(query)
        if use and reason in ("science_domain", "heroic_science") and _claude_science_ok():
            global _active_backend, _last_switch_ts
            if _active_backend != "claude-science":
                _last_switch_ts = time.time()
            _active_backend = "claude-science"
            os.environ["FUSION_LLM_BACKEND"] = "claude-science"
            return "claude-science"
    except Exception:
        pass
    return select_provider(force_probe=force_probe)


def select_provider(force_probe: bool = False) -> str:
    """Wählt den besten verfügbaren Anbieter (Prioritätsliste + Fallback)."""
    global _active_backend, _last_switch_ts

    if not is_auto_enabled():
        fixed = os.getenv("FUSION_LLM_BACKEND", "llama-local")
        _active_backend = fixed
        return fixed

    forced = os.getenv("FUSION_LLM_BACKEND", "").strip()
    if forced and not force_probe:
        if _check(forced):
            _active_backend = forced
            return forced

    for name in provider_order():
        if _check(name):
            if _active_backend != name:
                _last_switch_ts = time.time()
            _active_backend = name
            os.environ["FUSION_LLM_BACKEND"] = name
            return name

    _active_backend = "fusion-hero"
    os.environ["FUSION_LLM_BACKEND"] = "fusion-hero"
    return "fusion-hero"


def status() -> Dict[str, Any]:
    order = provider_order()
    checks = {name: _check(name) for name in order}
    active = select_provider(force_probe=True)
    return {
        "auto_enabled": is_auto_enabled(),
        "active_backend": active,
        "order": order,
        "availability": checks,
        "last_switch_ts": _last_switch_ts or None,
        "fixed_override": os.getenv("FUSION_LLM_BACKEND") if not is_auto_enabled() else None,
    }