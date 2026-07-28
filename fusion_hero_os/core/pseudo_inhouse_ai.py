"""
Pseudo-Inhouse AI Hub — local facade only (no freemium product surface).

Callers use one in-house surface; optional external backends are *membranes*
(Ollama, OpenRouter, Groq, Gemini, HF, Cloudflare, NVIDIA, GitHub Models).
Policy: freemium=false. SaaS is never source-of-truth for MasterSeed / placement.

Geltung: Spezifikation (routing code) · membrane availability = Bedingt/extern.
"""
from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
_CODE = ROOT / "03_Code"
for p in (str(ROOT), str(_CODE), str(_CODE / "Dashboard")):
    if p not in sys.path:
        sys.path.insert(0, p)

__all__ = [
    "PseudoInhouseResult",
    "status",
    "catalog",
    "complete",
    "list_models",
    "DEFAULT_CHAIN",
]

DEFAULT_CHAIN = (
    "ollama",
    "openrouter_free",
    "groq",
    "gemini",
    "huggingface",
    "cloudflare_ai",
    "nvidia",
    "github_models",
    "internal",
)

SYSTEM_PREFIX = (
    "Du antwortest über den Fusion Hero OS v10 Pseudo-Inhouse AI Hub. "
    "Keine Freemium-Produktoberfläche. Externe Dienste sind nur Membranen; "
    "Inhouse-Wahrheit liegt im Mainframe."
)


@dataclass
class PseudoInhouseResult:
    ok: bool
    provider: str
    model: str
    response: str
    latency_ms: float = 0.0
    source: str = "api"
    tried: list[str] = field(default_factory=list)
    error: str | None = None
    inhouse: bool = True
    free_tier: bool = True
    platform: str = "10.0.0"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def openai_chat_completion(self) -> dict[str, Any]:
        """OpenAI-compatible chat.completion shape for local tools."""
        return {
            "id": f"chatcmpl-fusion-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": f"fusion-inhouse/{self.provider}:{self.model}",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": self.response},
                    "finish_reason": "stop" if self.ok else "error",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "fusion": {
                "provider": self.provider,
                "tried": self.tried,
                "latency_ms": self.latency_ms,
                "ok": self.ok,
                "pseudo_inhouse": True,
            },
        }


def _load_yaml_catalog() -> dict[str, Any]:
    path = ROOT / "llm_free_services.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def catalog() -> dict[str, Any]:
    data = _load_yaml_catalog()
    return {
        "ok": True,
        "platform": "10.0.0",
        "principle": data.get("principle"),
        "placement": data.get("placement", "L1"),
        "facade": data.get("facade"),
        "chain": data.get("chain") or list(DEFAULT_CHAIN),
        "services": data.get("services") or {},
        "roles": data.get("roles") or {},
        "anti_patterns": data.get("anti_patterns") or [],
        "local_truth": data.get("local_truth", "inhouse"),
    }


def _framework_status() -> dict[str, Any]:
    try:
        from llm_frameworks.registry import all_status, FREE_CHAIN, connector_status

        return {
            "frameworks": all_status(),
            "free_chain": list(FREE_CHAIN),
            "connector": connector_status(),
        }
    except Exception as e:  # noqa: BLE001
        return {"error": str(e), "frameworks": {}}


def _ollama_live(timeout: float = 1.5) -> bool:
    try:
        import requests

        host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        r = requests.get(f"{host}/api/tags", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def status() -> dict[str, Any]:
    fw = _framework_status()
    frameworks = fw.get("frameworks") or {}
    ready: list[dict[str, Any]] = []
    for pid in DEFAULT_CHAIN:
        if pid == "internal":
            ready.append(
                {
                    "id": "internal",
                    "configured": True,
                    "live": True,
                    "kind": "local_fallback",
                }
            )
            continue
        s = frameworks.get(pid) or {}
        live = bool(s.get("configured"))
        if pid == "ollama":
            live = _ollama_live()
        ready.append(
            {
                "id": pid,
                "configured": bool(s.get("configured") or pid == "ollama"),
                "live": live,
                "api_key_set": bool(s.get("api_key_set")),
                "model": s.get("model"),
                "display_name": s.get("display_name") or pid,
            }
        )
    any_live = any(x.get("live") for x in ready if x["id"] != "internal")
    return {
        "ok": True,
        "platform": "10.0.0",
        "pseudo_inhouse": True,
        "any_external_live": any_live,
        "chain": list(DEFAULT_CHAIN),
        "providers": ready,
        "facade": {
            "openai": "/v1/chat/completions",
            "status": "/api/ai/inhouse/status",
            "chat": "/api/ai/inhouse/chat",
        },
        "framework_error": fw.get("error"),
        "freemium": False,
        "policy": "pseudo_inhouse_only",
        "honesty": (
            "Pseudo-inhouse only — no freemium SKUs. "
            "External backends are membranes with rate limits; "
            "not source-of-truth for MasterSeed."
        ),
    }


def list_models() -> dict[str, Any]:
    st = status()
    models = []
    for p in st.get("providers") or []:
        if not p.get("live") and p["id"] != "internal":
            continue
        mid = p.get("model") or p["id"]
        models.append(
            {
                "id": f"fusion-inhouse/{p['id']}",
                "object": "model",
                "owned_by": "fusion-hero-os",
                "provider": p["id"],
                "root_model": mid,
            }
        )
    models.append(
        {
            "id": "fusion-inhouse/auto",
            "object": "model",
            "owned_by": "fusion-hero-os",
            "provider": "auto",
            "root_model": "failover-chain",
        }
    )
    return {"object": "list", "data": models}


def _internal_complete(prompt: str, system: str) -> PseudoInhouseResult:
    t0 = time.time()
    text = (
        f"[Fusion Hero OS v10 · Pseudo-Inhouse Internal Fallback]\n"
        f"{system}\n---\n"
        f"Kein externer Free-Tier-Provider war live. "
        f"Antwort ist ein lokaler Stub, kein Frontier-Modell.\n\n"
        f"Prompt-Echo (gekürzt): {(prompt or '')[:800]}"
    )
    return PseudoInhouseResult(
        ok=True,
        provider="internal",
        model="fusion-hero-internal",
        response=text,
        latency_ms=(time.time() - t0) * 1000,
        source="internal",
        free_tier=True,
    )


def complete(
    prompt: str,
    *,
    system: str | None = None,
    provider: str | None = None,
    role: str = "worker",
    timeout: int | None = None,
) -> PseudoInhouseResult:
    """Complete via free chain (or forced provider). Always returns inhouse-shaped result."""
    sys_msg = (system or SYSTEM_PREFIX).strip()
    tried: list[str] = []
    chain: list[str]
    if provider and provider not in ("auto", "inhouse", "fusion-inhouse", "fusion"):
        # fusion-inhouse/groq → groq
        p = provider.replace("fusion-inhouse/", "").strip()
        chain = [p, "internal"]
    else:
        chain = list(DEFAULT_CHAIN)

    # Prefer ollama only if live
    if "ollama" in chain and not _ollama_live():
        chain = [c for c in chain if c != "ollama"] + (
            ["ollama"] if "ollama" in DEFAULT_CHAIN else []
        )
        # put ollama at end if not live so we don't waste time first
        if "ollama" in chain:
            chain = [c for c in chain if c != "ollama"]

    try:
        from llm_frameworks.registry import get_framework, invoke
    except Exception as e:  # noqa: BLE001
        r = _internal_complete(prompt, sys_msg)
        r.error = f"registry import: {e}"
        r.tried = tried
        return r

    for pid in chain:
        if pid == "internal":
            r = _internal_complete(prompt, sys_msg)
            r.tried = tried + ["internal"]
            return r
        tried.append(pid)
        fw = get_framework(pid)
        if fw is None:
            continue
        if pid == "ollama" and not _ollama_live():
            continue
        if not fw.configured() and pid != "ollama":
            continue
        try:
            result = invoke(
                pid,
                prompt,
                role=role,
                context={"system_extra": sys_msg},
                timeout=timeout,
            )
            if result.ok and (result.response or "").strip():
                return PseudoInhouseResult(
                    ok=True,
                    provider=result.provider_id,
                    model=result.model,
                    response=result.response,
                    latency_ms=result.latency_ms,
                    source=result.source,
                    tried=list(tried),
                    free_tier=True,
                )
        except Exception:  # noqa: BLE001
            continue

    r = _internal_complete(prompt, sys_msg)
    r.tried = tried + ["internal"]
    r.ok = True
    return r


def main() -> int:
    import json

    print(json.dumps(status(), indent=2, ensure_ascii=False)[:2000])
    r = complete("Sag in einem Satz: Pseudo-Inhouse Status.")
    print(json.dumps(r.to_dict(), indent=2, ensure_ascii=False)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
