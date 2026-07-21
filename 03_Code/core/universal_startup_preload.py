# -*- coding: utf-8 -*-
"""
Universal Startup Preload — ALLES beim Start laden.

Verbindliche Default-Regel (FUSION_PRELOAD_ALL=1, nicht deaktivierbar ohne
explizites FUSION_PRELOAD_ALL=0):

  • LLM-Frameworks (Registry + Status)
  • Graph/MCP-Connectoren (graph_api hub)
  • Kreuznetz (framework_cross_mesh)
  • Agent-Router + Triade (agent / anti / quantizer)
  • String-Quantisierer
  • Module-Registry load_all
  • Integration Hub Status
  • Autoload-Controller mark_ready

Aufruf:
  from universal_startup_preload import preload_all
  report = preload_all()
"""
from __future__ import annotations

import os
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

__all__ = [
    "preload_all",
    "is_preload_enabled",
    "last_report",
    "ensure_paths",
]

_LAST: Dict[str, Any] = {}
_IN_PROGRESS = False
_ROOT = Path(__file__).resolve().parents[2]  # fusion-hero-os
_CODE = Path(__file__).resolve().parents[1]  # 03_Code
_CORE = Path(__file__).resolve().parent
_DASH = _CODE / "Dashboard"


def is_preload_enabled() -> bool:
    # Explicit opt-out only
    return os.getenv("FUSION_PRELOAD_ALL", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def ensure_paths() -> List[str]:
    added: List[str] = []
    for p in (_ROOT, _CODE, _CORE, _DASH, Path.home() / "private-hacking-suite"):
        s = str(p)
        if p.exists() and s not in sys.path:
            sys.path.insert(0, s)
            added.append(s)
    os.environ.setdefault("FUSION_HERO_ROOT", str(_ROOT))
    os.environ.setdefault("FUSION_AUTO_LOAD", "1")
    os.environ.setdefault("FUSION_ALL_MODULES", "1")
    os.environ.setdefault("FUSION_DUAL_AGENT", "1")
    os.environ.setdefault("FUSION_QUANTIZER_AGENT", "1")
    os.environ.setdefault("FUSION_ORCH_DUAL_AGENT", "1")
    # Full boot by default (user directive: everything loaded at start)
    if os.getenv("FUSION_BOOT_PHASE", "").strip() == "":
        os.environ["FUSION_BOOT_PHASE"] = "full"
    return added


def _step(name: str, fn: Callable[[], Any], report: Dict[str, Any]) -> None:
    t0 = time.time()
    entry: Dict[str, Any] = {"name": name, "ok": False}
    try:
        out = fn()
        entry["ok"] = True
        if isinstance(out, dict):
            # keep compact
            entry["summary"] = {
                k: out[k]
                for k in list(out.keys())[:12]
                if k not in ("edges", "nodes", "segments", "raw", "heuristic_grid")
            }
            if "error" in out and out.get("error"):
                entry["ok"] = False
                entry["error"] = str(out["error"])[:300]
        else:
            entry["summary"] = {"result_type": type(out).__name__}
    except Exception as exc:
        entry["ok"] = False
        entry["error"] = str(exc)[:400]
        entry["trace"] = traceback.format_exc()[-500:]
    entry["ms"] = round((time.time() - t0) * 1000, 1)
    report["steps"].append(entry)
    status = "OK" if entry["ok"] else "FAIL"
    print(f"[Preload] {status} {name} ({entry['ms']}ms)" + (
        f" — {entry.get('error','')[:80]}" if not entry["ok"] else ""
    ), flush=True)


def preload_all(*, force: bool = False, skip_autoloader: bool = False) -> Dict[str, Any]:
    """Load connectors, modules, frameworks, quantizer, mesh — at process start."""
    global _LAST, _IN_PROGRESS
    ensure_paths()
    report: Dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "module": "universal_startup_preload",
        "enabled": is_preload_enabled(),
        "force": force,
        "steps": [],
        "ok": False,
    }
    if _IN_PROGRESS and not force:
        report["skipped"] = True
        report["reason"] = "reentrant_guard"
        report["ok"] = bool(_LAST.get("ok"))
        return report if not _LAST else {**_LAST, "reentrant": True}
    if not is_preload_enabled() and not force:
        report["skipped"] = True
        report["reason"] = "FUSION_PRELOAD_ALL=0"
        _LAST = report
        return report
    _IN_PROGRESS = True
    try:
        return _preload_all_body(report, force=force, skip_autoloader=skip_autoloader)
    finally:
        _IN_PROGRESS = False


def _preload_all_body(
    report: Dict[str, Any],
    *,
    force: bool,
    skip_autoloader: bool,
) -> Dict[str, Any]:
    global _LAST

    # ── 1) LLM frameworks ──────────────────────────────────────────────
    def _llm():
        from llm_frameworks import connector_status, list_frameworks
        st = connector_status()
        return {
            "frameworks": list_frameworks(),
            "count": st.get("count"),
            "available": st.get("available"),
            "trinity": st.get("trinity"),
            "cross_mesh": st.get("cross_mesh"),
            "any_live": st.get("any_live"),
        }

    _step("llm_frameworks", _llm, report)

    # ── 2) Graph / MCP connectors hub ──────────────────────────────────
    def _graph():
        try:
            from fusion_hero_os.connectors.graph_api import status_all, build_default_hub
            hub = build_default_hub()
            st = status_all()
            return {
                "hub": True,
                "connectors": list(st.keys()) if isinstance(st, dict) else st,
                "count": len(st) if isinstance(st, dict) else None,
            }
        except Exception:
            # fallback: unified yaml connector links
            import yaml
            p = _ROOT / "fusion_unified.yaml"
            data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
            links = data.get("connector_llm_links") or {}
            return {"hub": False, "connector_llm_links": list(links.keys()), "count": len(links)}

    _step("graph_connectors", _graph, report)

    # ── 3) Cross mesh ──────────────────────────────────────────────────
    def _cross():
        from framework_cross_mesh import build_cross_mesh, cross_mesh_status
        m = build_cross_mesh()
        st = cross_mesh_status()
        return {
            "fully_connected": m.get("fully_connected_frameworks"),
            "counts": m.get("counts"),
            "frameworks": m.get("frameworks"),
            "connectors": m.get("connectors"),
            "ok": st.get("ok"),
        }

    _step("framework_cross_mesh", _cross, report)

    # ── 4) Agent router + quantizer ────────────────────────────────────
    def _agents():
        from agent_backend_router import policy, status as abr_status
        from string_quantizer_agent import get_quantizer
        pol = policy()
        q = get_quantizer().status()
        return {
            "policy": pol,
            "router": {k: abr_status().get(k) for k in ("module", "llama_active", "grok_bridge", "dual_agent_enabled", "quantizer_agent_enabled") if k in abr_status() or True},
            "quantizer": q,
            "triad": pol.get("triad"),
        }

    _step("agent_triad_quantizer", _agents, report)

    # ── 4b) Sinnquanten + M→N DB Quantbau ──────────────────────────────
    def _sinn_m2n():
        from sinn_quanten_registry import status as sinn_status
        from m_to_n_quant_db import status as m2n_status
        return {
            "sinn": sinn_status(),
            "m_to_n": m2n_status(),
        }

    _step("sinn_quanten_m2n", _sinn_m2n, report)

    # ── 5) Integration hub ─────────────────────────────────────────────
    def _hub():
        from fusion_integration_hub import get_unified_status
        # light: avoid slow tailscale if needed
        u = get_unified_status()
        return {
            "version": u.get("version"),
            "health": u.get("health"),
            "llm_summary": u.get("llm_summary"),
            "mesh_summary": u.get("mesh_summary"),
            "cross_mesh_ok": bool((u.get("cross_mesh") or {}).get("ok") or (u.get("graph") or {}).get("cross_mesh")),
        }

    _step("fusion_integration_hub", _hub, report)

    # ── 6) Module registry ─────────────────────────────────────────────
    def _mods():
        # prefer Dashboard module_registry if available
        try:
            sys.path.insert(0, str(_DASH))
            from module_registry import get_registry
            reg = get_registry()
            res = reg.load_all(
                force=force,
                phase=os.getenv("FUSION_BOOT_PHASE", "full"),
            )
            return {
                "count": res.get("count") or res.get("summary", {}).get("loaded"),
                "total": res.get("total") or res.get("summary", {}).get("total"),
                "summary": res.get("summary"),
            }
        except Exception:
            from core.module_registry import load_all
            res = load_all(force=force)
            return res

    _step("module_registry", _mods, report)

    # ── 7) Dashboard autoloader catalog only (no re-run — avoids recursion) ─
    def _autoloader():
        if skip_autoloader:
            return {"skipped": True, "reason": "skip_autoloader"}
        # Prefer Dashboard autoloader catalog; never pull core.module_registry by accident
        if str(_DASH) not in sys.path:
            sys.path.insert(0, str(_DASH))
        try:
            import importlib
            al = importlib.import_module("autoloader")
            cat = al.catalog()
            return {
                "catalog_drivers": len(cat.get("drivers") or []),
                "auto_enabled": cat.get("auto_enabled"),
                "note": "catalog only — run_autoload via app/start_all",
            }
        except Exception as exc:
            return {"catalog_drivers": 0, "auto_enabled": True, "note": str(exc)[:200]}

    _step("dashboard_autoloader_catalog", _autoloader, report)

    # ── 8) Provider switcher ───────────────────────────────────────────
    def _provider():
        sys.path.insert(0, str(_DASH))
        try:
            from core.provider_switcher import select_provider, status as provider_status
        except Exception:
            from provider_switcher import select_provider, status as provider_status
        active = select_provider(force_probe=True)
        return {"active": active, **provider_status()}

    _step("provider_switcher", _provider, report)

    # ── 9) Autoload controller mark ready ──────────────────────────────
    def _ctrl():
        from fusion_hero_os.core.autoload_controller import mark_ready, status
        mark_ready(
            reason="universal_startup_preload",
            preload_steps=len(report["steps"]),
        )
        return status()

    _step("autoload_controller", _ctrl, report)

    # ── 10) Suite quantizer path warm ──────────────────────────────────
    def _suite():
        suite = Path(os.environ.get("FUSION_SUITE_ROOT", Path.home() / "private-hacking-suite"))
        return {
            "suite_exists": suite.is_dir(),
            "suite": str(suite),
            "tools": [p.name for p in (suite / "tools").glob("*.py")][:20] if (suite / "tools").is_dir() else [],
            "data_public": (suite / "data" / "public_raw").is_dir(),
        }

    _step("private_hacking_suite", _suite, report)

    ok_n = sum(1 for s in report["steps"] if s.get("ok"))
    report["ok"] = ok_n >= max(4, len(report["steps"]) // 2)
    report["steps_ok"] = ok_n
    report["steps_total"] = len(report["steps"])
    report["principle"] = "preload_all_at_start"
    _LAST = report

    # persist operator-local
    try:
        op = Path.home() / ".fusion" / "operator"
        op.mkdir(parents=True, exist_ok=True)
        import json
        (op / "last_preload.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
            encoding="utf-8",
        )
    except Exception:
        pass
    return report


def last_report() -> Dict[str, Any]:
    return dict(_LAST)


if __name__ == "__main__":
    import json
    force = "--force" in sys.argv
    r = preload_all(force=force)
    print(json.dumps({
        "ok": r.get("ok"),
        "steps_ok": r.get("steps_ok"),
        "steps_total": r.get("steps_total"),
        "steps": [{"name": s["name"], "ok": s["ok"], "ms": s["ms"], "error": s.get("error")} for s in r.get("steps", [])],
    }, indent=2, ensure_ascii=False))
    sys.exit(0 if r.get("ok") else 1)
