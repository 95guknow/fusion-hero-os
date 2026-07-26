# -*- coding: utf-8 -*-
"""
Activate Fusion Hero OS v12.0.0 — full operative surface.

Pins platform env, verifies VERSION/package consistency, loads package registry,
and (if Dashboard :8000 is up) triggers load-all + full autoload + interconnect
capture + route/mainframe probes.

Usage:
  python scripts/activate_v10.py
  python scripts/activate_v10.py --no-http
  python scripts/activate_v10.py --base http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
PLATFORM = "13.0.0"
MANIFEST = (
    Path.home() / ".fusion" / "mesh" / "coordination" / "v12_activation.json"
)

# Env that define "everything on v10"
ENV_DEFAULTS: Dict[str, str] = {
    "FUSION_PLATFORM_VERSION": PLATFORM,
    "FUSION_VERSION": PLATFORM,
    "FUSION_ALL_MODULES": "1",
    "FUSION_AUTO_LOAD": "1",
    "FUSION_HYPERTHREADING": "1",
    "FUSION_PROCESS_EXCLUSIVITY": "1",
    "FUSION_MAINFRAME_SITE": "1",
    "FUSION_GROK_INTERCONNECT": "1",
    "FUSION_ROUTE_TABLE": "1",
    "FUSION_RACE_GUARD": "1",
    "FUSION_DISSERTATION_AS_OS": "1",
    "FUSION_V33_DESIGN": "1",
    "PYTHONPATH": os.pathsep.join(
        [
            str(ROOT),
            str(ROOT / "03_Code"),
            str(ROOT / "03_Code" / "Dashboard"),
            os.environ.get("PYTHONPATH", ""),
        ]
    ).strip(os.pathsep),
}


def _apply_env(force: bool = True) -> Dict[str, str]:
    applied = {}
    for k, v in ENV_DEFAULTS.items():
        if force or not os.environ.get(k):
            os.environ[k] = v
            applied[k] = v
    # Ensure repo root first on path
    for p in (str(ROOT), str(ROOT / "03_Code"), str(ROOT / "03_Code" / "Dashboard")):
        if p not in sys.path:
            sys.path.insert(0, p)
    return applied


def _read_version_file() -> str:
    p = ROOT / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.exists() else ""


def _http_json(
    method: str,
    url: str,
    body: Optional[dict] = None,
    timeout: float = 120.0,
) -> Tuple[int, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, {"raw": raw[:500]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw) if raw else {"error": str(e)}
        except json.JSONDecodeError:
            return e.code, {"error": str(e), "raw": raw[:500]}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def verify_local() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "platform_target": PLATFORM,
        "version_file": _read_version_file(),
        "package_version": None,
        "registry": None,
        "core_imports": {},
        "ok": False,
        "errors": [],
    }
    if out["version_file"] != PLATFORM:
        out["errors"].append(
            f"VERSION file is {out['version_file']!r}, expected {PLATFORM!r}"
        )

    try:
        import fusion_hero_os as fhos

        out["package_version"] = getattr(fhos, "__version__", None)
        if out["package_version"] != PLATFORM:
            out["errors"].append(
                f"fusion_hero_os.__version__={out['package_version']!r}"
            )
    except Exception as e:  # noqa: BLE001
        out["errors"].append(f"import fusion_hero_os: {e}")

    # Core surfaces that must import on v10
    for label, path in (
        ("route_table", "fusion_hero_os.core.grok_route_table"),
        ("interconnect", "fusion_hero_os.core.grok_interconnect"),
        ("race_guard", "fusion_hero_os.core.race_guard"),
        ("math_engine", "fusion_hero_os.core.heroic_math_engine"),
        ("dispatcher", "fusion_hero_os.core.dispatcher"),
        ("layer_registry", "fusion_hero_os.core.layer_registry"),
        ("engine_mainframe", "fusion_hero_os.engine.mainframe"),
        ("methodology", "fusion_hero_os.methodology.core_modules"),
        ("pseudo_inhouse_ai", "fusion_hero_os.core.pseudo_inhouse_ai"),
    ):
        try:
            __import__(path)
            out["core_imports"][label] = "ok"
        except Exception as e:  # noqa: BLE001
            out["core_imports"][label] = f"FAIL: {e}"
            out["errors"].append(f"import {path}: {e}")

    # Registry load (best-effort) — full v10 module set
    try:
        from fusion_hero_os.registry import load_all, status_report

        load_all()
        rows = status_report()
        out["registry"] = {
            "modules": len(rows),
            "loaded": sum(1 for r in rows if r.get("status") == "loaded"),
            "failed": sum(1 for r in rows if r.get("status") in ("failed", "unavailable")),
            "report": rows,
        }
    except Exception as e:  # noqa: BLE001
        out["registry"] = f"note: {e}"

    out["ok"] = len(out["errors"]) == 0
    return out


def activate_http(base: str) -> Dict[str, Any]:
    base = base.rstrip("/")
    steps: List[Dict[str, Any]] = []

    def step(name: str, method: str, path: str, body: Optional[dict] = None, timeout: float = 180.0):
        code, data = _http_json(method, base + path, body, timeout=timeout)
        ok = 200 <= code < 300
        entry = {"name": name, "path": path, "http": code, "ok": ok}
        if isinstance(data, dict):
            # keep small summary
            for k in ("status", "ok", "phase", "health_score", "platform", "version"):
                if k in data:
                    entry[k] = data[k]
            if "error" in data:
                entry["error"] = str(data["error"])[:200]
            if name == "routes" and "entrypoints" in data:
                entry["entrypoints"] = data["entrypoints"]
            if name == "interconnect" and "summary" in data:
                entry["summary"] = data["summary"]
        else:
            entry["data_type"] = type(data).__name__
        steps.append(entry)
        return ok

    # light health first
    step("health_light", "GET", "/api/health?light=true", timeout=10)
    step("load_all", "POST", "/api/load-all?force=true", None, timeout=180)
    step(
        "autoload_full",
        "POST",
        "/api/autoload/run",
        {
            "phase": "full",
            "force": True,
            "sync": True,
            "attach_meta": True,
        },
        timeout=300,
    )
    step("autoload_status", "GET", "/api/autoload/status", timeout=30)
    step("modules", "GET", "/api/modules", timeout=30)
    step("grok_status", "GET", "/api/grok/status", timeout=60)
    step("interconnect", "GET", "/api/grok/interconnect?refresh=true", timeout=90)
    step("routes", "GET", "/api/grok/routes", timeout=15)
    step("route_ide", "GET", "/api/grok/route?intent=ide", timeout=15)
    step("mainframe_site", "GET", "/api/mainframe/site/status", timeout=30)
    step("mainframe_hub", "GET", "/mainframe", timeout=15)
    step("control_plane", "GET", "/mainframe/grok", timeout=15)

    ok_n = sum(1 for s in steps if s.get("ok"))
    return {
        "base": base,
        "steps": steps,
        "ok_count": ok_n,
        "step_count": len(steps),
        "ok": ok_n >= 3,  # health + some surfaces; full may partially fail
    }


def write_activation_banner(path: Path, report: dict) -> None:
    """Write a short status md under dissertation anhaenge for the build trail."""
    lines = [
        "# v10 Activation Record",
        "",
        f"**Platform:** `{PLATFORM}`",
        f"**UTC:** {report.get('activated_at')}",
        f"**Local OK:** {report.get('local', {}).get('ok')}",
        f"**HTTP OK:** {report.get('http', {}).get('ok')}",
        "",
        "Env pins: FUSION_PLATFORM_VERSION, FUSION_ALL_MODULES, FUSION_AUTO_LOAD, "
        "FUSION_HYPERTHREADING, FUSION_DISSERTATION_AS_OS, FUSION_V33_DESIGN, …",
        "",
        "Regenerate: `python scripts/activate_v10.py`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Activate Fusion Hero OS v12.0.0")
    ap.add_argument("--base", default=os.environ.get("FUSION_DASHBOARD_URL", "http://127.0.0.1:8000"))
    ap.add_argument("--no-http", action="store_true", help="Skip Dashboard HTTP activation")
    ap.add_argument("--json", action="store_true", help="Print full JSON report")
    args = ap.parse_args()

    t0 = time.time()
    applied = _apply_env(force=True)
    local = verify_local()
    http: Dict[str, Any] = {"skipped": True}
    if not args.no_http:
        http = activate_http(args.base)

    report = {
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "platform": PLATFORM,
        "env_applied": applied,
        "local": local,
        "http": http,
        "duration_sec": round(time.time() - t0, 2),
        "dissertation_as_os": True,
        "v33_design_mandatory": True,
    }

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    banner = ROOT / "docs" / "dissertation" / "anhaenge" / "A00_v12_activation.md"
    write_activation_banner(banner, report)

    # Console summary
    print(f"=== Fusion Hero OS v{PLATFORM} activation ===")
    print(f"VERSION file: {local.get('version_file')}  package: {local.get('package_version')}")
    print(f"local ok: {local.get('ok')}  errors: {len(local.get('errors') or [])}")
    for e in local.get("errors") or []:
        print(f"  ! {e}")
    for k, v in (local.get("core_imports") or {}).items():
        print(f"  import {k}: {v}")
    if http.get("skipped"):
        print("http: skipped")
    else:
        print(
            f"http: {http.get('ok_count')}/{http.get('step_count')} ok @ {http.get('base')}"
        )
        for s in http.get("steps") or []:
            mark = "OK " if s.get("ok") else "XX "
            print(f"  {mark}{s.get('http')} {s.get('name')}")
    print(f"manifest: {MANIFEST}")
    print(f"duration: {report['duration_sec']}s")

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))

    # Non-zero only if local package pin fails hard
    if local.get("version_file") != PLATFORM:
        return 2
    if local.get("package_version") and local.get("package_version") != PLATFORM:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
