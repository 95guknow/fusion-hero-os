# -*- coding: utf-8 -*-
"""Windows-Substrat Performance-Tuner — autonom, fusioniert (ersetzt nichts)."""
from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

POWER_GUIDS = {
    "high": "8c5e7f7e-e703-41f1-9c47-9b9e12d2b3d3",
    "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
    "saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
}
_HIGH_NAME_HINTS = ("höchstleistung", "hchstleistung", "high performance", "ultimate", "ryzent high")
_BALANCED_NAME_HINTS = ("ausbalanciert", "balanced", "ryzent balanced")

_LAST_SCAN: Dict[str, Any] = {}
_LAST_APPLY: Dict[str, Any] = {}


@dataclass
class TuneAction:
    id: str
    applied: bool
    detail: str
    skipped_reason: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


def _run_ps(script: str, timeout: int = 15) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out.strip()
    except Exception as exc:
        return -1, str(exc)


def _list_power_schemes() -> List[dict]:
    code, out = _run_ps("powercfg /list")
    schemes: List[dict] = []
    if code != 0:
        return schemes
    for line in out.splitlines():
        line = line.strip()
        if not line or "GUID" not in line:
            continue
        active = "*" in line
        try:
            guid = line.split("GUID des Energieschemas:")[-1].split("(")[0].strip()
            name = line.split("(")[-1].rstrip(") *").strip()
        except Exception:
            continue
        schemes.append({"name": name, "guid": guid.lower(), "active": active})
    return schemes


def _active_power_scheme() -> dict:
    schemes = _list_power_schemes()
    for s in schemes:
        if s.get("active"):
            return s
    code, out = _run_ps(
        "(Get-CimInstance Win32_PowerPlan | Where-Object {$_.IsActive}).ElementName + '|' + "
        "(Get-CimInstance Win32_PowerPlan | Where-Object {$_.IsActive}).InstanceID"
    )
    if code == 0 and "|" in out:
        name, guid = out.split("|", 1)
        return {"name": name.strip(), "guid": guid.strip().lower()}
    return {"name": "unknown", "guid": "", "raw": out}


def _resolve_high_performance_guid() -> str:
    for s in _list_power_schemes():
        nm = (s.get("name") or "").lower()
        if any(h in nm for h in _HIGH_NAME_HINTS):
            return s["guid"]
    return POWER_GUIDS["high"]


def _fusion_backend_pids() -> List[dict]:
    code, out = _run_ps(
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine -match 'uvicorn app:app' } | "
        "Select-Object ProcessId, @{n='MB';e={[math]::Round($_.WorkingSetSize/1MB,1)}}, "
        "@{n='cmd';e={$_.CommandLine}} | ConvertTo-Json -Compress"
    )
    if code != 0 or not out:
        return []
    try:
        import json
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        return [
            {"pid": int(d["ProcessId"]), "mb": d.get("MB"), "cmd": d.get("cmd", "")[:200]}
            for d in data
        ]
    except Exception:
        return []


def scan_windows_perf() -> dict:
    """Diagnose RAM, Power, Fusion-Prozesse, Druck."""
    import psutil

    vm = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.15)
    power = _active_power_scheme()
    backends = _fusion_backend_pids()
    own_pid = os.getpid()

    top_mem: List[dict] = []
    try:
        for proc in sorted(
            psutil.process_iter(["pid", "name", "memory_info"]),
            key=lambda p: (p.info.get("memory_info") or type("x", (), {"rss": 0})()).rss,
            reverse=True,
        )[:8]:
            mi = proc.info.get("memory_info")
            if mi:
                top_mem.append({
                    "name": proc.info.get("name"),
                    "pid": proc.info.get("pid"),
                    "mb": round(mi.rss / (1024 ** 2), 1),
                })
    except Exception:
        pass

    ram_pct = vm.percent
    pressure = "low"
    if ram_pct >= 85:
        pressure = "critical"
    elif ram_pct >= 70:
        pressure = "high"
    elif ram_pct >= 55:
        pressure = "medium"

    scan = {
        "ts": time.time(),
        "ram_gb_total": round(vm.total / (1024 ** 3), 2),
        "ram_gb_free": round(vm.available / (1024 ** 3), 2),
        "ram_percent": round(ram_pct, 1),
        "cpu_percent": round(cpu, 1),
        "logical_cpus": os.cpu_count() or 0,
        "power_plan": power,
        "power_saver_active": (
            POWER_GUIDS["saver"] in power.get("guid", "")
            or "energiespar" in (power.get("name") or "").lower()
        ),
        "power_schemes": _list_power_schemes(),
        "fusion_backends": backends,
        "duplicate_backends": len(backends) > 1,
        "own_pid": own_pid,
        "memory_pressure": pressure,
        "top_memory": top_mem,
        "recommendations": _recommendations(ram_pct, power, backends),
    }
    global _LAST_SCAN
    _LAST_SCAN = scan
    return scan


def _recommendations(ram_pct: float, power: dict, backends: List[dict]) -> List[str]:
    rec: List[str] = []
    if POWER_GUIDS["saver"] in power.get("guid", ""):
        rec.append("Energiesparplan aktiv → Hohe Leistung empfohlen")
    if ram_pct >= 75:
        rec.append(f"RAM {ram_pct:.0f}% — Allocator drosselt Worker")
    if len(backends) > 1:
        rec.append(f"{len(backends)} uvicorn-Backends — Duplikat beenden")
    if not rec:
        rec.append("Substrat OK — keine kritischen Hebel")
    return rec


def _resolve_balanced_guid() -> str:
    for s in _list_power_schemes():
        nm = (s.get("name") or "").lower()
        if any(h in nm for h in _BALANCED_NAME_HINTS):
            return s["guid"]
    return POWER_GUIDS["balanced"]


def _set_power_balanced() -> TuneAction:
    power = _active_power_scheme()
    bal_guid = _resolve_balanced_guid()
    if bal_guid in power.get("guid", ""):
        return TuneAction("power_balanced", False, power.get("name", ""), "bereits aktiv")
    code, out = _run_ps(f"powercfg /setactive {bal_guid}")
    if code == 0:
        return TuneAction("power_balanced", True, "Ausbalanciert / 2-3 Leistung")
    return TuneAction("power_balanced", False, out, "powercfg fehlgeschlagen")


def apply_windows_performance_level(ratio: float = 2 / 3) -> dict:
    """Windows-Substrat an Leistungsstufe anpassen (nicht an /api/performance/set gekoppelt)."""
    ratio = max(0.1, min(1.0, float(ratio)))
    if ratio >= 0.9:
        action = _set_power_high()
    elif ratio >= 0.55:
        action = _set_power_balanced()
    else:
        code, out = _run_ps(f"powercfg /setactive {POWER_GUIDS['saver']}")
        action = TuneAction(
            "power_saver", code == 0, "Energiesparmodus" if code == 0 else out,
        )
    return {
        "performance_ratio": ratio,
        "action": action.to_dict(),
        "power_plan": _active_power_scheme(),
    }


def _set_power_high() -> TuneAction:
    power = _active_power_scheme()
    high_guid = _resolve_high_performance_guid()
    if high_guid in power.get("guid", ""):
        return TuneAction("power_high", False, power.get("name", ""), "bereits aktiv")
    if "energiespar" not in (power.get("name") or "").lower() and POWER_GUIDS["saver"] not in power.get("guid", ""):
        if "ausbalanciert" in (power.get("name") or "").lower() or "balanced" in (power.get("name") or "").lower():
            pass
    code, out = _run_ps(f"powercfg /setactive {high_guid}")
    if code == 0:
        return TuneAction("power_high", True, "Hohe Leistung aktiviert")
    return TuneAction("power_high", False, out, "powercfg fehlgeschlagen")


def _dedupe_backends(keep_pid: Optional[int] = None) -> TuneAction:
    backends = _fusion_backend_pids()
    if len(backends) <= 1:
        return TuneAction("dedupe_backend", False, "ein Backend", "nicht nötig")

    own = keep_pid or os.getpid()
    # Eigenen Prozess nie beenden; echte Worker (>=10 MB) vor Launcher-Hüllen (<10 MB)
    if any(b["pid"] == own for b in backends):
        keep = own
    else:
        heavy = [b for b in backends if (b.get("mb") or 0) >= 10]
        keep = (heavy or backends)[0]["pid"]

    killed = []
    for b in backends:
        if b["pid"] == keep:
            continue
        # Vom API-Server aus: nur leichte Duplikat-Hüllen oder Fremd-Interpreter beenden
        if b["pid"] == own:
            continue
        if b["pid"] == keep:
            continue
        is_shell = (b.get("mb") or 0) < 10
        is_foreign = "venv" not in (b.get("cmd") or "").lower() and keep == own
        if not is_shell and not is_foreign:
            continue
        code, _ = _run_ps(f"Stop-Process -Id {b['pid']} -Force -ErrorAction SilentlyContinue")
        if code == 0:
            killed.append(b["pid"])

    if killed:
        return TuneAction("dedupe_backend", True, f"behalten {keep}, beendet {killed}")
    return TuneAction("dedupe_backend", False, "keine sicheren Duplikate", "übersprungen")


def _boost_own_priority() -> TuneAction:
    if os.getenv("FUSION_WIN_PRIORITY_BOOST", "1") == "0":
        return TuneAction("priority_boost", False, "", "FUSION_WIN_PRIORITY_BOOST=0")
    try:
        import psutil
        p = psutil.Process(os.getpid())
        if p.nice() == psutil.ABOVE_NORMAL_PRIORITY_CLASS:
            return TuneAction("priority_boost", False, "Above Normal", "bereits gesetzt")
        p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
        return TuneAction("priority_boost", True, "Backend → Above Normal")
    except Exception as exc:
        return TuneAction("priority_boost", False, str(exc), "nicht unterstützt")


def _set_substrate_env() -> TuneAction:
    """Nur Substrat-Encoding — keine Fusion-Leistungs-Env."""
    defaults = {
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
    }
    applied = []
    for key, val in defaults.items():
        if not os.getenv(key):
            os.environ[key] = val
            applied.append(key)
    if applied:
        return TuneAction("substrate_env", True, ", ".join(applied))
    return TuneAction("substrate_env", False, "Substrat-Env OK", "nicht nötig")


def apply_substrate_tuning(
    *,
    power: bool = True,
    dedupe: bool = False,
    priority: bool = True,
    env: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Windows-Substrat-Tuning — getrennt von Fusion-Leistung (/api/performance/set).
    Power: nur Energiesparmodus → Hohe Leistung (kein Drosseln bei Ausbalanciert).
    """
    scan = scan_windows_perf()
    actions: List[TuneAction] = []

    if dry_run:
        actions.append(TuneAction("dry_run", True, "keine Änderungen"))
    else:
        if env:
            actions.append(_set_substrate_env())
        if power and scan.get("power_saver_active"):
            actions.append(_set_power_high())
        elif power:
            actions.append(TuneAction(
                "power_substrate", False,
                scan["power_plan"].get("name", ""),
                "Substrat OK (kein Energiesparmodus)",
            ))
        if dedupe and scan.get("duplicate_backends"):
            actions.append(_dedupe_backends())
        elif dedupe:
            actions.append(TuneAction("dedupe_backend", False, "ein Backend", "nicht nötig"))
        if priority and scan.get("memory_pressure") != "critical":
            actions.append(_boost_own_priority())
        elif priority:
            actions.append(TuneAction(
                "priority_boost", False, "", "RAM kritisch — Priorität übersprungen",
            ))

    result = {
        "ts": time.time(),
        "scope": "windows_substrate",
        "fusion_performance_touched": False,
        "dry_run": dry_run,
        "scan": scan,
        "actions": [a.to_dict() for a in actions],
        "applied_count": sum(1 for a in actions if a.applied),
    }
    global _LAST_APPLY
    _LAST_APPLY = result
    try:
        from cyber_layer_windows import activate_cyber_layer
        cyber = activate_cyber_layer(result)
        result["cyber_layer"] = {
            "active": cyber.active,
            "score": cyber.optimization_score,
            "badge": cyber.visual.get("badge"),
        }
    except Exception as exc:
        result["cyber_layer"] = {"error": str(exc)}
    return result


def apply_windows_tuning(
    *,
    power: bool = True,
    dedupe: bool = True,
    priority: bool = True,
    env: bool = True,
    dry_run: bool = False,
) -> dict:
    """Vollständiges Windows-Tuning inkl. Dedupe (expliziter API-Aufruf)."""
    result = apply_substrate_tuning(
        power=power, dedupe=dedupe, priority=priority, env=env, dry_run=dry_run,
    )
    result["scope"] = "windows_substrate_full"
    return result


def substrate_status() -> dict:
    return {
        "scope": "windows_substrate",
        "last_scan": _LAST_SCAN or scan_windows_perf(),
        "last_apply": _LAST_APPLY,
        "power_guids": POWER_GUIDS,
        "capabilities": {
            "power_fix_saver": "Energiesparmodus → Hohe Leistung",
            "dedupe_backends": "Doppelte uvicorn-Instanzen bereinigen",
            "priority_boost": "Backend Above Normal (wenn RAM nicht kritisch)",
            "substrate_env": "PYTHONUTF8 / PYTHONIOENCODING",
        },
        "fusion_decoupled": True,
        "cyber_layer": _cyber_layer_brief(),
        "api": {
            "status": "/api/windows/substrate/status",
            "tune": "/api/windows/substrate/tune",
            "full_tune": "/api/windows/tune/apply",
            "cyber_status": "/api/windows/cyber-layer/status",
            "cyber_activate": "/api/windows/cyber-layer/activate",
        },
    }


def _cyber_layer_brief() -> dict:
    try:
        from cyber_layer_windows import get_cyber_layer_status
        c = get_cyber_layer_status(refresh=False)
        return {"active": c.active, "score": c.optimization_score, "badge": c.visual.get("badge")}
    except Exception:
        return {"active": False}


def tuner_status() -> dict:
    return substrate_status()