# llama_subagent_tester.py — Subagent-Tracks für lokales Llama (status, CLI, QUBO, Generate)

from __future__ import annotations

import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

_LLM_ROOT = Path(__file__).resolve().parent.parent / "internal_llm"
_CONFIG = _LLM_ROOT / "output" / "heroic_llama_config.json"
_MODEL = _LLM_ROOT / "models" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf"

_TEST_PROMPTS = {
    "ping": "[model] Antworte nur mit einem Wort: OK",
    "qubo": "[model] Was ist QUBO in einem Satz?",
    "heroic": "[cond] Banach-Kontraktion kurz erklären.",
}


def _workers(task_weight: str = "heavy") -> int:
    try:
        from resource_workflow import recommend_workers

        return max(1, recommend_workers(task_weight).get("recommended_workers", 1))
    except Exception:
        return 1


def _skip_generate() -> bool:
    if os.getenv("FUSION_LLAMA_SUBAGENT_SKIP_GENERATE", "0") == "1":
        return True
    try:
        from resource_workflow import snapshot

        snap = snapshot()
        ram = snap.get("ram_pct") or 0
        llama = any("llama" in (p.get("name") or "").lower() for p in snap.get("heavy_procs", []))
        if ram >= float(os.getenv("FUSION_RAM_SOFT_PCT", "78")) or llama:
            return True
    except Exception:
        pass
    return False


def _track(name: str, fn: Callable[[], Any]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    try:
        result = fn()
        ok = bool(result.get("ok", True)) if isinstance(result, dict) else True
        return {
            "subagent": name,
            "ok": ok,
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
            "result": result,
        }
    except Exception as exc:
        return {
            "subagent": name,
            "ok": False,
            "duration_ms": round((time.perf_counter() - t0) * 1000, 1),
            "error": str(exc),
        }


def test_status() -> Dict[str, Any]:
    from local_llama import get_local_llama

    st = get_local_llama().status()
    return {
        "ok": st.get("active") or st.get("model_path") is not None,
        "active": st.get("active"),
        "backend": st.get("backend"),
        "model_path": st.get("model_path"),
        "qubo": st.get("qubo"),
    }


def test_model_file() -> Dict[str, Any]:
    paths = [_MODEL, Path(r"C:\Users\Admin\internal_llm\models\Llama-3.2-1B-Instruct-Q4_K_M.gguf")]
    found = next((str(p) for p in paths if p.exists()), None)
    return {"ok": found is not None, "model_path": found, "config_exists": _CONFIG.exists()}


def test_cli_binary() -> Dict[str, Any]:
    cli = Path(
        os.getenv(
            "LLAMA_CLI_PATH",
            r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages"
            r"\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-cli.exe",
        )
    )
    server = Path(os.getenv("LLAMA_SERVER_PATH", ""))
    return {
        "ok": cli.exists(),
        "llama_cli": str(cli),
        "cli_exists": cli.exists(),
        "server_path": str(server) if server else None,
        "server_exists": server.exists() if server else False,
    }


def test_llama_server_process() -> Dict[str, Any]:
    procs: List[Dict[str, Any]] = []
    try:
        import psutil

        for p in psutil.process_iter(["name", "pid", "memory_info"]):
            name = (p.info.get("name") or "").lower()
            if "llama-server" in name:
                rss = round((p.info.get("memory_info").rss or 0) / 1e6, 1)
                procs.append({"pid": p.info.get("pid"), "name": p.info.get("name"), "rss_mb": rss})
    except Exception as exc:
        return {"ok": False, "error": str(exc), "processes": []}
    return {"ok": True, "running": len(procs) > 0, "processes": procs}


def test_qubo_bridge() -> Dict[str, Any]:
    from qubo_llama_bridge import status as qubo_status, is_enabled

    st = qubo_status()
    return {"ok": True, "enabled": is_enabled(), "bridge": st}


def test_generate(label: str = "ping", use_qubo: bool = False) -> Dict[str, Any]:
    if _skip_generate():
        return {"ok": True, "skipped": True, "reason": "RAM/llama-server — Generate-Test übersprungen"}

    from local_llama import get_local_llama

    llama = get_local_llama()
    if not llama.active:
        return {"ok": False, "error": "llama not active"}
    prompt = _TEST_PROMPTS.get(label, _TEST_PROMPTS["ping"])
    if use_qubo:
        out = llama.generate_qubo(prompt)
        text = out.get("response", "")
        return {
            "ok": bool(text.strip()),
            "label": label,
            "qubo_applied": out.get("qubo_applied"),
            "response_len": len(text),
            "preview": text[:120],
        }
    text = llama.generate(prompt, use_qubo=False)
    return {
        "ok": bool(text.strip()),
        "label": label,
        "response_len": len(text),
        "preview": text[:120],
    }


def test_config_patch() -> Dict[str, Any]:
    if not _CONFIG.exists():
        return {"ok": False, "error": "config missing"}
    import json

    cfg = json.loads(_CONFIG.read_text(encoding="utf-8"))
    gen = cfg.get("generation") or {}
    ok = bool(cfg.get("system_prompt")) and bool(gen.get("temperature") is not None or gen)
    cfg.setdefault("subagent_tests", {})["last_track"] = "config_valid"
    cfg["subagent_tests"]["ts"] = time.time()
    _CONFIG.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": ok, "config": str(_CONFIG), "generation_keys": list(gen.keys())}


def all_subagents() -> Dict[str, Callable[[], Any]]:
    agents: Dict[str, Callable[[], Any]] = {
        "llama_status": test_status,
        "llama_model_file": test_model_file,
        "llama_cli_binary": test_cli_binary,
        "llama_server_process": test_llama_server_process,
        "llama_qubo_bridge": test_qubo_bridge,
        "llama_config_valid": test_config_patch,
    }
    if not _skip_generate():
        agents["llama_generate_ping"] = lambda: test_generate("ping", False)
        agents["llama_generate_qubo"] = lambda: test_generate("qubo", True)
    return agents


def _context_for_subagent(name: str, weight: str) -> Dict[str, Any]:
    try:
        from conversation_context_core import allocate_subagent, feedback, is_enabled

        if not is_enabled():
            return {}
        alloc = allocate_subagent(name, task_weight=weight)
        return {
            "window_id": alloc.get("subagent_window", {}).get("window_id"),
            "token_budget": alloc.get("allocation", {}).get("token_budget"),
            "prompt_block": alloc.get("prompt_block", "")[:400],
        }
    except Exception:
        return {}


def _feedback_track(track: Dict[str, Any]) -> None:
    try:
        from conversation_context_core import feedback, get_context, is_enabled

        if not is_enabled():
            return
        name = track.get("subagent", "llama_track")
        ctx = get_context()
        wins = [
            w for w in ctx.windows.values()
            if w.role == "subagent" and w.subagent_name == name
        ]
        if not wins:
            return
        wid = sorted(wins, key=lambda w: w.updated_ts)[-1].window_id
        summary = f"{name}: {'OK' if track.get('ok') else 'FAIL'}"
        res = track.get("result")
        if isinstance(res, dict) and res.get("preview"):
            summary += f" — {res['preview'][:80]}"
        feedback(wid, summary, {"track": name, "duration_ms": track.get("duration_ms")})
    except Exception:
        pass


def run(
    subagents: Optional[List[str]] = None,
    max_workers: Optional[int] = None,
    include_generate: Optional[bool] = None,
    seed_context: Optional[str] = None,
) -> Dict[str, Any]:
    """Führt Llama-Tests als parallele Subagent-Tracks aus (ressourcenbewusst)."""
    if include_generate is False:
        os.environ["FUSION_LLAMA_SUBAGENT_SKIP_GENERATE"] = "1"
    elif include_generate is True:
        os.environ.pop("FUSION_LLAMA_SUBAGENT_SKIP_GENERATE", None)

    catalog = all_subagents()
    selected = [s for s in (subagents or list(catalog.keys())) if s in catalog]
    weight = "heavy" if any("generate" in s for s in selected) else "medium"
    workers = max_workers or _workers(weight)
    started = time.time()
    results: List[Dict[str, Any]] = []

    context_meta: Dict[str, Any] = {}
    try:
        from conversation_context_core import init_root, is_enabled

        if is_enabled():
            context_meta = init_root(
                seed_context or "Llama Subagent Test-Session",
                {"task_weight": weight, "subagents": selected},
            )
    except Exception:
        pass

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {}
        for name in selected:
            ctx = _context_for_subagent(name, "light" if "generate" not in name else "heavy")
            futures[pool.submit(_track, name, catalog[name])] = (name, ctx)
        for fut in as_completed(futures):
            name, ctx = futures[fut]
            track = fut.result()
            if ctx:
                track["context_window"] = ctx
            _feedback_track(track)
            results.append(track)

    ok = sum(1 for r in results if r.get("ok"))
    skipped = sum(
        1 for r in results
        if isinstance(r.get("result"), dict) and r["result"].get("skipped")
    )
    out: Dict[str, Any] = {
        "status": "completed" if ok == len(results) else "partial",
        "module": "llama_subagent_tester",
        "subagents_ok": ok,
        "subagents_total": len(results),
        "subagents_skipped": skipped,
        "workers": workers,
        "generate_skipped_globally": _skip_generate(),
        "duration_ms": round((time.time() - started) * 1000, 1),
        "tracks": sorted(results, key=lambda x: x.get("subagent", "")),
    }
    if context_meta:
        out["start_context_window"] = context_meta.get("root")
        try:
            from conversation_context_core import status as ctx_status

            out["context_feedback"] = ctx_status().get("recent_feedback")
        except Exception:
            pass
    return out


def status() -> Dict[str, Any]:
    rec: Dict[str, Any] = {}
    try:
        from resource_workflow import recommend_workers

        rec = recommend_workers("heavy")
    except Exception:
        pass
    ctx: Dict[str, Any] = {}
    try:
        from conversation_context_core import is_enabled, status as ctx_status

        if is_enabled():
            ctx = ctx_status()
    except Exception:
        pass
    return {
        "module": "llama_subagent_tester",
        "available_subagents": list(all_subagents().keys()),
        "generate_would_skip": _skip_generate(),
        "resource_recommendation": rec,
        "context_window": ctx,
    }