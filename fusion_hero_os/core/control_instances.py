"""
Multi-model control instances — force highest accuracy on each.

Each control instance = independent model/provider with temperature=0,
verifier protocol, structured accuracy score. Results are compared for
consensus. Internal instance always runs.

Geltung: Spezifikation (orchestration) · model answers = external/bedingt.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "03_Code")):
    if p not in sys.path:
        sys.path.insert(0, p)

__all__ = [
    "ControlResult",
    "ControlReport",
    "run_control_panel",
    "status",
    "list_instances",
]

ACCURACY_SYSTEM = """You are a CONTROL INSTANCE on Fusion Hero OS v10.
FORCE MAXIMUM ACCURACY. temperature semantics: be deterministic, careful, cite uncertainty.
Do NOT invent facts. Prefer "unknown" over guesswork.
Answer in JSON only:
{
  "answer": "<precise answer or unknown>",
  "confidence": 0-100,
  "accuracy_self": 0-100,
  "uncertainty": ["..."],
  "checks": ["verification step performed", "..."],
  "geltung": "Satz|Bedingt|Modell|Fragment|Unbekannt",
  "notes": "<short>"
}
No markdown fences. No prose outside JSON.
"""


@dataclass
class ControlResult:
    instance_id: str
    provider: str
    label: str
    ok: bool
    answer: str = ""
    confidence: float = 0.0
    accuracy_self: float = 0.0
    geltung: str = "Unbekannt"
    latency_ms: float = 0.0
    source: str = ""
    model: str = ""
    error: str | None = None
    raw_text: str = ""
    checks: list[str] = field(default_factory=list)
    temperature: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ControlReport:
    ok: bool
    prompt: str
    instances_run: int
    instances_ok: int
    consensus: dict[str, Any]
    results: list[ControlResult]
    accuracy_force: dict[str, Any]
    generated_at: str
    platform: str = "10.0.0"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["results"] = [r.to_dict() if hasattr(r, "to_dict") else r for r in self.results]
        return d


def _load_cfg() -> dict[str, Any]:
    path = ROOT / "control_instances.yaml"
    if not path.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _load_dotenv(cfg: dict[str, Any] | None = None) -> list[str]:
    """Load operator API keys into env without logging values."""
    cfg = cfg or _load_cfg()
    sl = cfg.get("secret_load") or {}
    if not sl.get("enabled", True):
        return []
    loaded: list[str] = []
    paths = list(sl.get("dotenv_paths") or [".env", ".env.local"])
    for rel in paths:
        if str(rel).startswith("~"):
            path = Path(os.path.expanduser(rel))
        else:
            path = ROOT / rel
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if not key:
                    continue
                if not (os.environ.get(key) or "").strip():
                    os.environ[key] = val
            loaded.append(path.name)
        except Exception:
            continue
    return loaded


def list_instances() -> list[dict[str, Any]]:
    cfg = _load_cfg()
    return list(cfg.get("instances") or [])


def status() -> dict[str, Any]:
    cfg = _load_cfg()
    dotenv = _load_dotenv(cfg)
    acc = cfg.get("accuracy_force") or {}
    live = []
    try:
        from llm_frameworks.registry import get_framework

        for inst in list_instances():
            pid = inst.get("provider")
            if pid == "internal":
                live.append({**inst, "configured": True, "live": True})
                continue
            fw = get_framework(str(pid))
            conf = bool(fw and fw.configured()) if fw else False
            # ollama: configured without key; live probe separate
            if pid == "ollama":
                conf = True
            model = inst.get("model_override") or (fw.model if fw else "")
            live.append(
                {
                    **inst,
                    "configured": conf,
                    "live": conf or bool(inst.get("always")),
                    "resolved_model": model,
                }
            )
    except Exception as e:  # noqa: BLE001
        live = [{"error": str(e)[:120]}]
    def _slots(pid: str) -> int:
        return sum(1 for i in live if str(i.get("provider")) == pid)

    multi_slots = {
        "gemini": _slots("gemini"),
        "grok": _slots("grok"),
        "claude": _slots("claude"),
        "gpt": _slots("gpt"),
        "groq": _slots("groq"),
        "openrouter": _slots("openrouter"),
        "openrouter_free": _slots("openrouter_free"),
        "huggingface": _slots("huggingface"),
        "nvidia": _slots("nvidia"),
        "github_models": _slots("github_models"),
        "cloudflare_ai": _slots("cloudflare_ai"),
        "ollama": _slots("ollama"),
        "internal": _slots("internal"),
    }
    # Key membrane (names only — never values)
    key_names = [
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "XAI_API_KEY",
        "GROK_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "GROQ_API_KEY",
        "HUGGINGFACE_API_KEY",
        "NVIDIA_API_KEY",
        "GITHUB_TOKEN",
        "CLOUDFLARE_API_TOKEN",
    ]
    key_membrane = {
        k: bool((os.environ.get(k) or "").strip()) for k in key_names
    }
    keys_set = sum(1 for v in key_membrane.values() if v)
    configured_n = sum(1 for i in live if i.get("configured"))
    return {
        "ok": True,
        "version": cfg.get("version"),
        "accuracy_force": acc,
        "temperature": float(acc.get("temperature", 0.0)),
        "instances": live,
        "instance_count": len(live),
        "gemini_control_slots": multi_slots["gemini"],
        "multi_slots": multi_slots,
        "configured_count": configured_n,
        "key_membrane": key_membrane,
        "keys_set_count": keys_set,
        "cloud_live": keys_set > 0 and configured_n > 4,
        "p0_blocker": (
            None
            if keys_set > 0
            else "Cloud LLM keys empty — multi-model control is skeleton only (ollama+internal)"
        ),
        "dotenv_loaded": dotenv,
        "principle": cfg.get("principle"),
        "policy": "pseudo_inhouse_only",
        "freemium": False,
    }


def _parse_json_answer(text: str) -> dict[str, Any]:
    text = (text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return {"answer": text[:2000], "confidence": 40, "accuracy_self": 40}
    return {"answer": text[:2000], "confidence": 35, "accuracy_self": 35}


def _invoke_accuracy(
    provider: str,
    prompt: str,
    *,
    temperature: float = 0.0,
    max_tokens: int = 2048,
    timeout: int = 120,
    model_override: str | None = None,
) -> tuple[bool, str, str, float, str | None, str]:
    """Returns ok, text, model, latency_ms, error, source."""
    t0 = time.time()
    if provider == "internal":
        # deterministic local control — no freemium, structured honesty
        payload = {
            "answer": "internal_control: external model not used; verify against code/docs",
            "confidence": 50,
            "accuracy_self": 55,
            "uncertainty": ["no external model"],
            "checks": ["internal_stub", "geltung_reminder"],
            "geltung": "Fragment",
            "notes": "Always-on control instance for fail-closed honesty",
        }
        return True, json.dumps(payload, ensure_ascii=False), "fusion-hero-internal", (time.time() - t0) * 1000, None, "internal"

    try:
        from llm_frameworks.registry import get_framework
        from llm_frameworks.base import openai_chat, anthropic_chat, ROLE_SYSTEM
    except Exception as e:  # noqa: BLE001
        return False, "", "", (time.time() - t0) * 1000, str(e), "import_error"

    fw = get_framework(provider)
    if fw is None:
        return False, "", "", (time.time() - t0) * 1000, f"unknown provider {provider}", "missing"

    model = (model_override or "").strip() or fw.model

    if not fw.configured() and provider != "ollama":
        return False, "", model, (time.time() - t0) * 1000, "not configured", "skip"

    system = ACCURACY_SYSTEM + "\n" + ROLE_SYSTEM.get("verifier", "")
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                f"CONTROL TASK (max accuracy, temperature={temperature}, model={model}):\n"
                f"{prompt}\n\nRespond with the JSON schema only."
            ),
        },
    ]
    try:
        # Prefer direct high-accuracy path for openai-compatible
        if fw.api_kind == "openai" and fw.get_api_key():
            text, raw = openai_chat(
                fw.base_url(),
                fw.get_api_key() or "",
                model,
                messages,
                timeout,
                provider=provider,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return True, text, model, (time.time() - t0) * 1000, None, "api_temp0"
        if fw.api_kind == "anthropic" and fw.get_api_key():
            text, raw = anthropic_chat(
                fw.base_url(),
                fw.get_api_key() or "",
                model,
                messages,
                system,
                timeout,
            )
            return True, text, model, (time.time() - t0) * 1000, None, "api_anthropic"
        if provider == "ollama" or fw.api_kind == "local":
            # force ollama temperature 0 via options in framework — custom call
            try:
                import requests

                host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
                payload = {
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.0, "top_p": 1.0},
                }
                r = requests.post(f"{host}/api/chat", json=payload, timeout=timeout)
                r.raise_for_status()
                text = r.json().get("message", {}).get("content", "")
                return True, text, model, (time.time() - t0) * 1000, None, "ollama_temp0"
            except Exception as e:  # noqa: BLE001
                return False, "", model, (time.time() - t0) * 1000, str(e)[:200], "ollama_fail"
        if fw.api_kind == "gemini" and fw.get_api_key():
            try:
                import requests

                api_key = fw.get_api_key()
                url = (
                    f"{fw.base_url().rstrip('/')}/models/{model}:generateContent"
                    f"?key={api_key}"
                )
                user_text = messages[-1]["content"]
                body = {
                    "system_instruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user", "parts": [{"text": user_text}]}],
                    "generationConfig": {
                        "temperature": 0.0,
                        "topP": 1.0,
                        "maxOutputTokens": max_tokens,
                    },
                }
                r = requests.post(url, json=body, timeout=timeout)
                r.raise_for_status()
                parts = r.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
                text = "".join(p.get("text", "") for p in parts)
                return True, text, model, (time.time() - t0) * 1000, None, "gemini_temp0"
            except Exception as e:  # noqa: BLE001
                return False, "", model, (time.time() - t0) * 1000, str(e)[:200], "gemini_fail"
        # fallback invoke (may not be temp 0)
        from llm_frameworks.registry import invoke

        res = invoke(provider, prompt, role="verifier", timeout=timeout)
        return (
            bool(res.ok),
            res.response or "",
            res.model,
            res.latency_ms,
            res.error,
            res.source + "_fallback",
        )
    except Exception as e:  # noqa: BLE001
        return False, "", "", (time.time() - t0) * 1000, str(e)[:300], "error"


def _answer_key(answer: str) -> str:
    a = re.sub(r"\s+", " ", (answer or "").strip().lower())
    return hashlib.sha256(a.encode("utf-8")).hexdigest()[:16]


def _consensus(results: list[ControlResult], band: float = 15.0) -> dict[str, Any]:
    ok_results = [r for r in results if r.ok and r.answer]
    if not ok_results:
        return {
            "agreement": False,
            "majority_answer": None,
            "mean_confidence": 0.0,
            "mean_accuracy_self": 0.0,
            "clusters": 0,
            "note": "no successful control instances",
        }
    clusters: dict[str, list[ControlResult]] = {}
    for r in ok_results:
        k = _answer_key(r.answer)
        clusters.setdefault(k, []).append(r)
    best_key = max(clusters.keys(), key=lambda k: len(clusters[k]))
    majority = clusters[best_key]
    maj_answer = majority[0].answer
    mean_c = sum(r.confidence for r in ok_results) / len(ok_results)
    mean_a = sum(r.accuracy_self for r in ok_results) / len(ok_results)
    agreement = len(majority) >= max(1, (len(ok_results) + 1) // 2)
    scores = [r.accuracy_self for r in ok_results]
    tight = (max(scores) - min(scores)) <= band if scores else False
    return {
        "agreement": agreement,
        "score_band_tight": tight,
        "majority_size": len(majority),
        "majority_answer": maj_answer[:2000],
        "mean_confidence": round(mean_c, 2),
        "mean_accuracy_self": round(mean_a, 2),
        "clusters": len(clusters),
        "instance_ids_majority": [r.instance_id for r in majority],
    }


def run_control_panel(
    prompt: str,
    *,
    providers: list[str] | None = None,
    force_all_configured: bool = True,
) -> ControlReport:
    """Run all (or selected) control instances with max accuracy."""
    cfg = _load_cfg()
    _load_dotenv(cfg)
    acc = cfg.get("accuracy_force") or {}
    temperature = float(acc.get("temperature", 0.0))
    max_tokens = int(acc.get("max_tokens", 2048))
    timeout = int(acc.get("timeout_sec", 120))
    band = float((cfg.get("consensus") or {}).get("score_band", 15))

    instances = list_instances()
    if providers:
        want = set(providers)
        instances = [i for i in instances if i.get("provider") in want or i.get("id") in want]

    results: list[ControlResult] = []
    for inst in instances:
        pid = str(inst.get("provider") or "")
        iid = str(inst.get("id") or pid)
        label = str(inst.get("label") or pid)
        always = bool(inst.get("always"))
        model_override = inst.get("model_override")
        if not model_override and inst.get("model_env"):
            model_override = os.getenv(str(inst["model_env"]), "").strip() or None
        ok, text, model, lat, err, source = _invoke_accuracy(
            pid,
            prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
            model_override=str(model_override) if model_override else None,
        )
        if not ok and not always and source in ("skip", "missing", "not configured"):
            results.append(
                ControlResult(
                    instance_id=iid,
                    provider=pid,
                    label=label,
                    ok=False,
                    error=err or source,
                    source=source,
                    model=model,
                    temperature=temperature,
                    latency_ms=lat,
                )
            )
            continue
        parsed = _parse_json_answer(text) if ok else {}
        answer = str(parsed.get("answer") or (text[:2000] if ok else ""))
        conf = float(parsed.get("confidence") or 0)
        acc_s = float(parsed.get("accuracy_self") or conf or 0)
        geltung = str(parsed.get("geltung") or "Unbekannt")
        raw_checks = parsed.get("checks")
        check_items: list[Any] = list(raw_checks) if isinstance(raw_checks, list) else []
        results.append(
            ControlResult(
                instance_id=iid,
                provider=pid,
                label=label,
                ok=ok and bool(answer),
                answer=answer,
                confidence=conf,
                accuracy_self=acc_s,
                geltung=geltung,
                latency_ms=lat,
                source=source,
                model=model,
                error=err,
                raw_text=(text or "")[:4000],
                checks=[str(c) for c in check_items],
                temperature=temperature,
            )
        )

    cons = _consensus(results, band=band)
    report = ControlReport(
        ok=any(r.ok for r in results),
        prompt=prompt,
        instances_run=len(results),
        instances_ok=sum(1 for r in results if r.ok),
        consensus=cons,
        results=results,
        accuracy_force={
            "temperature": temperature,
            "top_p": 1.0,
            "max_tokens": max_tokens,
            "timeout_sec": timeout,
        },
        generated_at=datetime.now(UTC).isoformat(),
    )

    # persist private operator report
    out = Path.home() / ".fusion" / "control" / "last_control_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    # public-safe summary (no huge raw)
    pub = {
        "generated_at": report.generated_at,
        "instances_run": report.instances_run,
        "instances_ok": report.instances_ok,
        "consensus": cons,
        "accuracy_force": report.accuracy_force,
        "results": [
            {
                "instance_id": r.instance_id,
                "provider": r.provider,
                "ok": r.ok,
                "confidence": r.confidence,
                "accuracy_self": r.accuracy_self,
                "geltung": r.geltung,
                "model": r.model,
                "source": r.source,
                "latency_ms": r.latency_ms,
                "error": r.error,
                "answer_preview": (r.answer or "")[:240],
            }
            for r in results
        ],
    }
    docs = ROOT / "docs" / "control"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "last_control_report.summary.json").write_text(
        json.dumps(pub, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Multi-model control instances (max accuracy)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--prompt", default="", help="Control task prompt")
    ap.add_argument("--providers", default="", help="comma list filter")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    prompt = args.prompt or (
        "Verify: In Fusion Hero OS ops vocabulary, does deploy mean private, "
        "push mean public, and merge mean both via dual timeline? "
        "Answer precisely with geltung."
    )
    providers = [p.strip() for p in args.providers.split(",") if p.strip()] or None
    report = run_control_panel(prompt, providers=providers)
    print(
        json.dumps(
            {
                "ok": report.ok,
                "instances_ok": report.instances_ok,
                "instances_run": report.instances_run,
                "consensus": report.consensus,
                "accuracy_force": report.accuracy_force,
                "results": [
                    {
                        "id": r.instance_id,
                        "provider": r.provider,
                        "ok": r.ok,
                        "accuracy_self": r.accuracy_self,
                        "confidence": r.confidence,
                        "geltung": r.geltung,
                        "source": r.source,
                        "error": r.error,
                        "answer_preview": (r.answer or "")[:160],
                    }
                    for r in report.results
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
