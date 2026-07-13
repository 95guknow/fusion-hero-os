# -*- coding: utf-8 -*-
"""FastAPI Dashboard Server — Fusion Hero OS v8 / ALTE_Frau_95g Heroic Core.

WebSocket event stream: heroic_core_event_loop emits periodic *demo* events
(hyperthread/peer-review/self-mod placeholders) so the UI has live data.
These events are NOT from real review/self-modification logic (Code-Honesty).
"""
from __future__ import annotations

import asyncio, time, uuid, json, statistics, random
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse

from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel

import numpy as np

BASE = Path(__file__).parent

# .env früh laden, damit os.getenv (FUSION_*, Supabase, ...) verfügbar ist
try:
    from dotenv import load_dotenv
    load_dotenv(BASE / ".env")
except Exception:
    pass

app = FastAPI(title="Fusion Hero OS v8 — ALTE_Frau_95g Heroic Core Dashboard")

# === Consolidated imports for agents + hyperthreading + task orchestration (from heroic_orchestration merge) ===
import sys, os

_NORMAL_OS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_ASCENSION = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _NORMAL_OS not in sys.path:
    sys.path.insert(0, _NORMAL_OS)
if _ASCENSION not in sys.path:
    sys.path.append(_ASCENSION)

_cors_origins = [
    o.strip()
    for o in os.getenv(
        "FUSION_CORS_ORIGINS",
        "http://127.0.0.1:8000,http://localhost:8000",
    ).split(",")
    if o.strip()
]
if _cors_origins:
    from fastapi.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
if '03_Code' not in sys.path and _ASCENSION not in sys.path:
    sys.path.append(_ASCENSION)
try:
    from core.heroic_orchestration import (
        ensure_agents_loaded as _ensure_agents_shared,
        classify_and_normalize,
        get_loaded_agents,
        auto_load,
        get_best_qubo_solver,
    )
except Exception:
    def _ensure_agents_shared(force=False): return True
    def classify_and_normalize(q): return q, "model", None, "General"
    def get_loaded_agents(): return {}
    def auto_load(phase="staged", force=False): return {"loaded": ["fallback"]}
    def get_best_qubo_solver(): return None

try:
    from core import hyperthreading_config as ht
except Exception:
    ht = None

try:
    from core.gpu_memory_allocator import get_gpu_allocator
except Exception:
    def get_gpu_allocator():
        return None

try:
    from core.cpu_adaptive_tuner import get_cpu_tuner
except Exception:
    def get_cpu_tuner():
        return None

try:
    from core.resource_coupler import get_resource_coupler
except Exception:
    def get_resource_coupler():
        return None

try:
    from core.gpu_compute_booster import get_gpu_compute_booster
except Exception:
    def get_gpu_compute_booster():
        return None

try:
    from core.memory_guard import get_memory_guard
except Exception:
    def get_memory_guard():
        return None

try:
    from core.gpu_vram_prioritizer import get_vram_prioritizer
except Exception:
    def get_vram_prioritizer():
        return None

try:
    import supabase_client as supa
    import supabase_store as supa_store
except Exception:
    supa = None
    supa_store = None

AGENT_STATE = {
    "loaded": False,
    "supervisor": None,
    "agents": {},
    "last_load": None
}

# === Automatische Erkennung von Input- und Output-Faktoren beim OS-Start ===
INPUT_FACTORS: Dict[str, Any] = {}
OUTPUT_FACTORS: Dict[str, Any] = {}

def detect_input_factors() -> Dict[str, Any]:
    """Automatische Erkennung der Input-Faktoren zu Beginn des OS-Starts."""
    global INPUT_FACTORS
    factors = {}
    try:
        import psutil
        factors["logical_cpus"] = psutil.cpu_count(logical=True) or 1
        factors["physical_cpus"] = psutil.cpu_count(logical=False) or 1
        mem = psutil.virtual_memory()
        factors["memory_total_gb"] = round(mem.total / (1024**3), 2)
        factors["memory_available_gb"] = round(mem.available / (1024**3), 2)
    except Exception:
        factors["logical_cpus"] = os.cpu_count() or 1
        factors["memory_total_gb"] = 0
    # GPU detection (optional)
    try:
        import torch
        factors["gpu_available"] = torch.cuda.is_available()
        factors["gpu_count"] = torch.cuda.device_count() if torch.cuda.is_available() else 0
    except Exception:
        factors["gpu_available"] = False
        factors["gpu_count"] = 0
    # FUSION env vars as input factors
    factors["fusion_env"] = {k: v for k, v in os.environ.items() if k.startswith("FUSION_")}
    factors["hyperthreading_env"] = os.getenv("FUSION_HYPERTHREADING") == "1"
    factors["profile"] = os.getenv("FUSION_PROFILE", "balanced")
    factors["detected_at"] = time.time()
    INPUT_FACTORS = factors
    return factors

def detect_output_factors() -> Dict[str, Any]:
    """Automatische Erkennung der Output-Faktoren basierend auf Inputs zu Beginn des OS-Starts."""
    global OUTPUT_FACTORS
    inputs = INPUT_FACTORS or detect_input_factors()
    cpus = inputs.get("logical_cpus", 4)
    ht = inputs.get("hyperthreading_env", False)
    target_workers = cpus * (6 if ht else 2)
    factors = {
        "target_workers": target_workers,
        "max_parallel_tasks": target_workers * 2,
        "synthesis_dimensions": 6,  # from MasterSeed
        "default_agent_roles": ["supervisor", "math-worker", "phil-worker", "info-worker", "general-worker"],
        "metrics_to_emit": ["cpu", "ram", "events", "hyperthreading", "agents"],
        "task_assignment_strategy": "best_fit",  # auto assign to most suitable
        "detected_at": time.time()
    }
    OUTPUT_FACTORS = factors
    return factors

def get_input_factors() -> Dict[str, Any]:
    return INPUT_FACTORS or detect_input_factors()

def get_output_factors() -> Dict[str, Any]:
    return OUTPUT_FACTORS or detect_output_factors()

# === General AutoLoad Logic (generell implementieren wo passend) ===
class AutoLoader:
    def __init__(self):
        self.drivers: Dict[str, Dict] = {}
        self.loaded: Dict[str, bool] = {}
        self._register_default_drivers()

    def _register_default_drivers(self):
        # Input/Output Factors
        self.register("input_factors", lambda: detect_input_factors(), "core")
        self.register("output_factors", lambda: detect_output_factors(), "core")

        # Hyperthreading
        if ht:
            self.register("hyperthreading", lambda: ht.enable(True), "performance")

        # CPU+GPU+SSD Resource Coupler
        try:
            from core.resource_coupler import get_resource_coupler
            self.register("resource_coupler", lambda: get_resource_coupler().couple_once(), "performance")
        except Exception:
            pass

        # Supabase (swmmoxhdzarmoupyssqe)
        if supa:
            self.register("supabase", lambda: supa.get_client() or supa.status(probe=True), "storage")

        # Agents (from heroic_orchestration)
        self.register("agents", lambda: _ensure_agents(), "orchestration")

        # Core Modules (example - can be extended)
        self.register("selfmodify_core", lambda: True, "meta")  # placeholder, real load if needed
        self.register("orchestration", lambda: auto_load(phase="full") if callable(auto_load) else _ensure_agents_shared(), "orchestration")

        # External projects integration (from C: search: qubo_miner, FusionHero caches, heroic layers)
        try:
            qm = get_best_qubo_solver()
            if qm:
                self.register("qubo_miner_solver", lambda: qm, "qubo")
        except:
            pass
        # Use C:\FusionHero as SSD if present
        if os.path.exists(r"C:\FusionHero\LongTermCache"):
            os.environ.setdefault("FUSION_SSD_LONGTERM_CACHE", r"C:\FusionHero\LongTermCache")
        # heroic layers from C: search
        try:
            import sys
            sys.path.insert(0, r"C:\Users\Admin\heroic-highest-layer")
            from highest_layer import load as load_highest
            self.register("highest_layer", lambda: load_highest(), "layer")
        except:
            pass
        try:
            from core.foundation_loader import ensure_foundation_on_path, foundation_report_to_dict, load_check_foundation_gate

            if ensure_foundation_on_path() is not None:
                check = load_check_foundation_gate()
                self.register(
                    "foundation_checks",
                    lambda: foundation_report_to_dict(check("", require_explicit=False)),
                    "layer0",
                )
        except:
            pass

    def register(self, name: str, loader: callable, category: str = "general"):
        self.drivers[name] = {"loader": loader, "category": category, "loaded": False}

    def run(self, phase: str = "staged", force: bool = False, sync: bool = False, attach_meta: bool = False) -> Dict[str, Any]:
        results = {"drivers_loaded": 0, "drivers_ready": 0, "drivers_total": len(self.drivers), "summary": {}}
        for name, info in self.drivers.items():
            if force or not info["loaded"]:
                try:
                    info["loader"]()
                    info["loaded"] = True
                    results["drivers_loaded"] += 1
                    results["summary"][name] = "loaded"
                except Exception as e:
                    results["summary"][name] = f"error: {e}"
            else:
                results["summary"][name] = "already loaded"
            if info["loaded"]:
                results["drivers_ready"] += 1
        results["phase"] = phase
        return results

    def status(self) -> Dict[str, Any]:
        return {
            "drivers_total": len(self.drivers),
            "drivers_loaded": sum(1 for d in self.drivers.values() if d.get("loaded")),
            "drivers_ready": sum(1 for d in self.drivers.values() if d.get("loaded")),
            "summary": {name: "loaded" if info.get("loaded") else "pending" for name, info in self.drivers.items()}
        }

autoloader = AutoLoader()

# Ensure detection at import time for early start
detect_input_factors()
detect_output_factors()

# === Heroic Core State ===
MAX_EVENTS = 500
events: deque[dict] = deque(maxlen=MAX_EVENTS)
subscribers: Set[WebSocket] = set()
_metrics_cache: dict = {"data": {}, "ts": 0.0}
_METRICS_TTL = 0.25

# Hyper-Threading + Layer 0-6 state (synced with core)
hyper_threads_state: Dict[int, dict] = {
    0: {"util": 42, "threads": 4, "status": "STABLE"},
    1: {"util": 67, "threads": 8, "status": "ACTIVE"},
    2: {"util": 31, "threads": 6, "status": "STABLE"},
    3: {"util": 89, "threads": 12, "status": "PEAK"},
    4: {"util": 55, "threads": 5, "status": "STABLE"},
    5: {"util": 73, "threads": 9, "status": "ACTIVE"},
    6: {"util": 28, "threads": 3, "status": "STABLE"}
}

class EventIn(BaseModel):
    type: str = "info"
    msg: str = ""
    severity: Optional[str] = None
    layer: Optional[int] = None

class MetricsOut(BaseModel):
    cpu: float
    ram: float
    events: int
    subs: int
    ts: float
    ops_per_sec: float
    avg_emit_time_ms: float
    cache_hit_rate: float
    hyperthreading: dict

PERFORMANCE_TRACKING: Dict[str, Any] = {
    "emit_times": deque(maxlen=1000),
    "broadcast_times": deque(maxlen=1000),
    "cache_hits": 0,
    "total_requests": 0,
    "start_time": time.time()
}

async def _send_safe(ws: WebSocket, event: dict) -> None:
    try:
        await asyncio.wait_for(ws.send_json(event), timeout=0.6)
    except Exception:
        subscribers.discard(ws)

async def emit(event: dict) -> str:
    """Broadcast to all heroic dashboard subscribers (deepened for core modules)"""
    start = time.perf_counter()
    event["ts"] = time.time()
    event["id"] = str(uuid.uuid4())[:8]
    events.append(event)
    event_id = event["id"]
    if supa_store and os.getenv("FUSION_SUPABASE_SYNC", "1") == "1":
        asyncio.create_task(asyncio.to_thread(supa_store.save_event, dict(event)))
    if subscribers:
        broadcast_start = time.perf_counter()
        await asyncio.gather(*[_send_safe(ws, event) for ws in list(subscribers)], return_exceptions=True)
        PERFORMANCE_TRACKING["broadcast_times"].append((time.perf_counter() - broadcast_start) * 1000)
    PERFORMANCE_TRACKING["emit_times"].append((time.perf_counter() - start) * 1000)
    return event_id

# Background SIMULATOR (random.uniform/random.random noise, no real review/mod logic) for demo events
async def heroic_core_event_loop():
    while True:
        await asyncio.sleep(random.uniform(3.5, 7.0))
        # Simulate layer / hyper-thread evolution
        layer = random.randint(0, 6)
        t = hyper_threads_state[layer]
        t["util"] = max(15, min(95, t["util"] + random.uniform(-12, 14)))
        if t["util"] > 82:
            t["status"] = "PEAK"
        elif t["util"] > 58:
            t["status"] = "ACTIVE"
        else:
            t["status"] = "STABLE"
        
        await emit({
            "type": "hyperthread_update",
            "layers": {str(layer): t},
            "msg": f"Layer {layer} hyper-thread utilization updated"
        })
        
        # Occasional peer-review or self-mod event
        if random.random() < 0.22:
            await emit({
                "type": "peer_review",
                "msg": "[Demo] Simulated Peer-Review event for SelfModifyCoreModule",
                "severity": "medium",
                "layer": layer
            })
        if random.random() < 0.11:
            await emit({
                "type": "self_mod_proposal",
                "msg": "[Demo] Simulated self-mod proposal: Enhance WebSocket broadcast with 6D traceability",
                "severity": "high"
            })

        # Geisterjagd + Banach live tick (~ jeder 2. Zyklus)
        if random.random() < 0.55:
            try:
                from core.geisterjagd_banach_viz import get_viz, build_hints_from_system
                recent = [e.get("type", "") for e in list(events)[-8:]]
                cpu = 50.0
                try:
                    import psutil
                    cpu = psutil.cpu_percent(interval=None)
                except Exception:
                    pass
                blocked = 0
                try:
                    from core.agent_control import status as ac_status
                    blocked = ac_status().get("blocked_total", 0)
                except Exception:
                    pass
                hints = build_hints_from_system(
                    event_count=len(events),
                    recent_types=recent,
                    queue_len=len(TASK_QUEUE) if "TASK_QUEUE" in globals() else 0,
                    cpu_pct=cpu,
                    agent_blocked=blocked,
                )
                viz = get_viz()
                tick_info = viz.tick(hints)
                snap = viz.snapshot()
                await emit({
                    "type": "geisterjagd_banach",
                    "msg": (
                        f"λ={snap['lambda']:.3f} d={snap['distance']:.3f} "
                        f"Emergenz={tick_info.get('emerged', 0)} Heuristik={snap['heuristic_score']:.2f}"
                    ),
                    "viz": snap,
                })
            except Exception:
                pass

def _schedule_agent_audit(action: str, **fields) -> None:
    if not supa_store:
        return
    asyncio.create_task(asyncio.to_thread(supa_store.save_agent_audit, action, **fields))


async def _start_supabase_background() -> None:
    if not supa_store:
        return
    try:
        from supabase_background import start_background_tasks

        info = start_background_tasks(get_metrics)
        if info.get("started"):
            msg = f"[Supabase] Auto-sync aktiv: Metriken alle {info['metrics_interval_sec']}s"
            if info.get("watch_sync_mode") == "realtime":
                msg += ", Watch-Realtime aktiv"
                if info.get("watch_sync_interval_sec"):
                    msg += f" (Poll-Fallback {info['watch_sync_interval_sec']}s)"
            elif info.get("watch_sync_interval_sec"):
                msg += f", Watch-Server alle {info['watch_sync_interval_sec']}s"
            print(msg)
    except Exception as exc:
        print(f"[Supabase] Background sync note: {exc}")


_DASHBOARD_LOCK_KEY: Optional[str] = None


def _acquire_dashboard_lock() -> bool:
    """Verhindert zwei Dashboard-Instanzen auf dem gleichen Port."""
    global _DASHBOARD_LOCK_KEY
    try:
        from connectivity import dashboard_port
        from core.process_exclusivity import try_acquire

        port = dashboard_port()
        key = f"dashboard:{port}"
        lock = try_acquire(key, owner="dashboard", ttl_sec=86400.0)
        if not lock.ok:
            print(
                f"[Startup] ABBRUCH: Dashboard-Port {port} bereits belegt "
                f"(PID {lock.holder_pid or '?'}, {lock.reason}). "
                "Nur eine Instanz pro Port erlaubt."
            )
            return False
        _DASHBOARD_LOCK_KEY = key
        print(f"[Startup] Prozess-Exklusivität aktiv: {key} (PID {os.getpid()})")
        return True
    except Exception as exc:
        print(f"[Startup] Prozess-Exklusivität note: {exc}")
        return True


@app.on_event("startup")
async def startup_event():
    if not _acquire_dashboard_lock():
        import sys

        sys.exit(1)
    launcher_fast_boot = os.getenv("FUSION_AUTO_LOAD") == "0"
    try:
        from fusion_settings import boot_load
        boot_load()
    except Exception as _settings_err:
        print(f"[Startup] Settings note: {_settings_err}")
    await _start_supabase_background()
    if launcher_fast_boot:
        os.environ["FUSION_AUTO_LOAD"] = "0"
    fast_boot = os.getenv("FUSION_AUTO_LOAD", "1") == "0"
    if fast_boot:
        print("[Startup] Fast boot (FUSION_AUTO_LOAD=0) — Bridge UI sofort verfügbar")
        asyncio.create_task(heroic_core_event_loop())
        return

    # Generelles AutoLoad + Faktenerkennung ZU BEGINN DES OS STARTS
    autoloader.run(phase="staged", attach_meta=True)
    detect_input_factors()
    detect_output_factors()
    _ensure_agents()
    if ht:
        try:
            ht.enable(True)
            # Force virtual GPU HT + SSD cache init
            vcache = ht.get_virtual_gpu_ht_cache()
            if hasattr(vcache, 'status'):
                print('[AutoLoad] Virtual GPU HT + SSD cache active:', vcache.status())
        except Exception as e:
            print('[AutoLoad] Virtual HT init note:', e)
    asyncio.create_task(heroic_core_event_loop())
    alloc = get_gpu_allocator()
    if alloc:
        if alloc.start_background():
            print("[GPU] Adaptiver VRAM-Allocator gestartet (dediziert priorisiert)")
        else:
            alloc.rebalance_once()
            print("[GPU] VRAM-Rebalance einmalig:", alloc.state.last_action)
    cpu_tuner = get_cpu_tuner()
    if cpu_tuner:
        result = cpu_tuner.tune_once()
        snap = result.get("cpu", {})
        print(f"[CPU] Adaptives Tuning: {result.get('action')} | "
              f"Last={snap.get('load_pct')}% Temp={snap.get('temp_c')}°C "
              f"Ratio={result.get('tuning', {}).get('ratio')}")
        cpu_tuner.start_background()
    coupler = get_resource_coupler()
    if coupler:
        cresult = coupler.couple_once()
        mem = cresult.get("memory", {}).get("system_ram", {})
        vram = cresult.get("memory", {}).get("dedicated_vram", {})
        print(f"[Coupler] CPU+GPU+SSD: {cresult.get('action')} | "
              f"RAM={mem.get('util_pct')}% VRAM={vram.get('util_pct')}% "
              f"GPU-Layer={cresult.get('tuning', {}).get('llama_gpu_layers')}")
        coupler.start_background()
    if os.getenv("FUSION_ALL_MODULES", "1") == "1":
        try:
            from core.module_registry import load_all
            mod_result = load_all(force=False)
            print(f"[Modules] Freigabe: {mod_result.get('count')}/{mod_result.get('total')} geladen")
        except Exception as e:
            print(f"[Modules] Load note: {e}")
    mem_guard = get_memory_guard()
    if mem_guard:
        mg = mem_guard.relieve_once()
        print(f"[RAM] Memory-Guard: {mg.get('action')} | {mg.get('ram', {}).get('util_pct')}%")
        mem_guard.start_background()
    vram_prio = get_vram_prioritizer()
    if vram_prio and os.getenv("FUSION_VRAM_PRIORITIZER_AUTO", "1") == "1":
        vp = vram_prio.prioritize_once()
        b, a = vp.get("before", {}), vp.get("after", {})
        print(f"[VRAM] Prioritizer: {vp.get('action')} | "
              f"{b.get('vram_used_mb', 0):.0f}MB -> {a.get('vram_used_mb', 0):.0f}MB")
    gpu_booster = get_gpu_compute_booster()
    if gpu_booster:
        if os.getenv("FUSION_GPU_COMPUTE_BOOSTER_AUTO", "1") == "1":
            bresult = gpu_booster.boost_once()
            print(f"[GPU] Compute-Booster: {bresult.get('action')} | "
                  f"SM={bresult.get('compute_util_pct')}% Ziel={bresult.get('target_compute_pct')}%")
        gpu_booster.start_background()
    try:
        from core.provider_switcher import select_provider, status as provider_status
        active_provider = select_provider(force_probe=True)
        ps = provider_status()
        print(f"[Provider] Auto-Wechsler aktiv={ps.get('auto_enabled')} | backend={active_provider}")
    except Exception as e:
        print(f"[Provider] Load note: {e}")
    if os.getenv("FUSION_FIRST_INSTALL_AUTO", "1") == "1":
        try:
            from core.first_install_bootstrap import is_first_install_pending, run as run_first_install
            if is_first_install_pending():
                fi = run_first_install()
                print(f"[FirstInstall] {fi.get('status')} ({fi.get('steps_ok')}/{fi.get('steps_total')} Schritte)")
        except Exception as e:
            print(f"[FirstInstall] note: {e}")
    print("[ALTE_Frau_95g] Heroic Core Dashboard gestartet")
    print(f"  AutoLoad Status: {autoloader.status()}")
    print(f"  Input-Faktoren: CPUs={INPUT_FACTORS.get('logical_cpus')}, HT={INPUT_FACTORS.get('hyperthreading_env')}")
    print(f"  Output-Faktoren: target_workers={OUTPUT_FACTORS.get('target_workers')}")


@app.on_event("shutdown")
async def shutdown_event():
    global _DASHBOARD_LOCK_KEY
    if not _DASHBOARD_LOCK_KEY:
        return
    try:
        from core.process_exclusivity import release

        release(_DASHBOARD_LOCK_KEY)
        print(f"[Shutdown] Prozess-Lock freigegeben: {_DASHBOARD_LOCK_KEY}")
    except Exception as exc:
        print(f"[Shutdown] Prozess-Lock note: {exc}")
    finally:
        _DASHBOARD_LOCK_KEY = None


@app.post("/api/events")
async def post_event(payload: EventIn):
    PERFORMANCE_TRACKING["total_requests"] += 1
    return {"status": "queued", "id": await emit({
        "type": payload.type,
        "msg": payload.msg,
        "severity": payload.severity,
        "layer": payload.layer
    })}

@app.get("/", response_class=HTMLResponse)
async def index():
    """Standard-GUI: Heroic Core Dashboard (HTML + WebSocket, kein NiceGUI)."""
    return FileResponse(BASE / "templates" / "index.html")


@app.get("/heroic", response_class=HTMLResponse)
async def heroic_page():
    """Cherry-picked legacy dashboard: heroische Philosophie."""
    path = BASE / "templates" / "heroic.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse("<h1>heroic.html not found</h1>", status_code=404)


@app.get("/about", response_class=HTMLResponse)
async def about_page():
    path = BASE / "templates" / "about.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse("<h1>about.html not found</h1>", status_code=404)


@app.get("/donation", response_class=HTMLResponse)
async def donation_page():
    path = BASE / "static" / "donation.html"
    if path.exists():
        return FileResponse(path)
    return HTMLResponse("<h1>donation.html not found</h1>", status_code=404)


@app.get("/foundation", response_class=HTMLResponse)
async def foundation_page():
    """Layer 0 — Heroic Core Foundation spec."""
    candidates = [
        BASE.parent.parent / "01_Framework" / "heroic-core-foundation" / "FOUNDATION.md",
        BASE.parent.parent / "01_Framework" / "heroic-core-foundation" / "README.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            content = candidate.read_text(encoding="utf-8")
            html = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Heroic Core Foundation</title>
<style>body{{background:#0a0a0f;color:#e2e8f0;font-family:ui-sans-serif,system-ui;margin:40px;line-height:1.6}}
pre{{background:#11121a;padding:20px;border-radius:12px;overflow:auto;border:1px solid #1e1e2e}}a{{color:#40e0d0}}</style>
</head><body><h1>Heroic Core Foundation — Layer 0</h1>
<p><a href="/">← Dashboard</a> · <a href="/heroic">Heroische Philosophie</a></p>
<pre>{content}</pre></body></html>"""
            return HTMLResponse(html)
    return HTMLResponse("<h1>Foundation not found</h1>", status_code=404)


_WALLET_FILE = BASE / "static" / "wallet.json"
_WALLET_CAP = 10000


def _load_wallet() -> dict:
    if _WALLET_FILE.exists():
        try:
            return json.loads(_WALLET_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"balance": 0.0, "cap": _WALLET_CAP}


def _save_wallet(data: dict) -> None:
    _WALLET_FILE.parent.mkdir(parents=True, exist_ok=True)
    _WALLET_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@app.get("/api/wallet")
async def api_wallet_get():
    return _load_wallet()


class WalletUpdate(BaseModel):
    amount: float = 0


@app.post("/api/wallet")
async def api_wallet_update(payload: WalletUpdate):
    wallet = _load_wallet()
    amount = float(payload.amount)
    wallet["balance"] = min(wallet.get("cap", _WALLET_CAP), wallet.get("balance", 0) + amount)
    _save_wallet(wallet)
    return wallet


@app.get("/watch", response_class=HTMLResponse)
async def watch_create_redirect():
    from watch_party import get_watch_manager
    room = get_watch_manager().create_room()
    return RedirectResponse(url=f"/watch/{room.room_id}", status_code=302)


@app.get("/watch/{room_id}", response_class=HTMLResponse)
async def watch_room(room_id: str, follower: bool = False):
    from watch_party import get_watch_manager, local_network_base, render_watch_page
    mgr = get_watch_manager()
    try:
        from watch_sync_server import refresh_room_from_server, server_sync_enabled

        if server_sync_enabled():
            await asyncio.to_thread(refresh_room_from_server, mgr, room_id)
    except Exception:
        pass
    room = mgr.get_room(room_id) or mgr.ensure_room(room_id)
    role = "follower" if follower else "controller"
    return HTMLResponse(
        render_watch_page(room.room_id, room.video_id, lan_base=local_network_base(), role=role)
    )


@app.get("/api/gui/status")
async def api_gui_status():
    return {
        "gui": "dashboard",
        "url": "http://127.0.0.1:8000",
        "type": "fastapi+html",
        "template": "templates/index.html",
        "websocket": "/ws",
        "nicegui_legacy": "optional http://127.0.0.1:8080 (workspace.py)",
    }


@app.get("/api/gui/workspace")
async def api_gui_workspace():
    return RedirectResponse(url="/")

@app.get("/api/metrics", response_model=MetricsOut)
async def get_metrics():
    now = time.time()
    PERFORMANCE_TRACKING["total_requests"] += 1
    if now - _metrics_cache.get("ts", 0) < _METRICS_TTL:
        PERFORMANCE_TRACKING["cache_hits"] += 1
        base_data = _metrics_cache["data"]
    else:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        base_data = {
            "cpu": round(cpu, 1),
            "ram": round(mem.percent, 1),
            "events": len(events),
            "subs": len(subscribers),
            "ts": now
        }
        _metrics_cache.update({"data": base_data, "ts": now})
    uptime = time.time() - PERFORMANCE_TRACKING["start_time"]
    return {
        **base_data,
        "ops_per_sec": round(PERFORMANCE_TRACKING["total_requests"] / max(uptime, 0.1), 2),
        "avg_emit_time_ms": round(statistics.mean(PERFORMANCE_TRACKING["emit_times"]) if PERFORMANCE_TRACKING["emit_times"] else 0.0, 4),
        "cache_hit_rate": round(PERFORMANCE_TRACKING["cache_hits"] / max(PERFORMANCE_TRACKING["total_requests"], 1), 3),
        "hyperthreading": {
            **(ht.status() if ht else {"enabled": False, "logical_cpus": os.cpu_count() or 12, "workers": 1}),
            "layers": hyper_threads_state,
        },
    }

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    if len(subscribers) >= 10000:
        await ws.close(code=1008)
        return
    await ws.accept()
    subscribers.add(ws)
    await ws.send_json({"type": "welcome", "event_count": len(events), "core_version": "v7.4"})
    
    try:
        async for data in ws.iter_text():
            try:
                msg = json.loads(data)
                action = msg.get("action")
                if action == "clear":
                    events.clear()
                    await emit({"type": "system", "msg": "Event-Log cleared by heroic operator"})
                elif action == "request_layer_status":
                    await ws.send_json({"type": "layer_update", "layers": {str(k): v for k, v in hyper_threads_state.items()}})
                elif action == "request_initial_state":
                    await ws.send_json({"type": "layer_update", "layers": {str(k): v for k, v in hyper_threads_state.items()}})
                elif action == "trigger_self_mod":
                    await emit({"type": "self_mod_proposal", "msg": f"Self-mod triggered from dashboard for {msg.get('module', 'unknown')}", "severity": "high"})
            except Exception as parse_err:
                await ws.send_json({"type": "error", "msg": str(parse_err)})
    except WebSocketDisconnect:
        pass
    finally:
        subscribers.discard(ws)


@app.websocket("/ws/watch/{room_id}")
async def watch_party_ws(ws: WebSocket, room_id: str):
    from watch_party import broadcast_room_state, get_watch_manager

    mgr = get_watch_manager()
    mgr.ensure_room(room_id)
    await ws.accept()
    mgr.register_ws(room_id, ws)
    try:
        from watch_sync_server import refresh_room_from_server, server_sync_enabled

        if server_sync_enabled():
            await asyncio.to_thread(refresh_room_from_server, mgr, room_id)
    except Exception:
        pass
    room = mgr.get_room(room_id)
    if room:
        await ws.send_json(room.to_state())
        await ws.send_json({"type": "watch_meta", "viewers": len(mgr.subscribers(room_id))})
    try:
        async for data in ws.iter_text():
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue
            action = msg.get("action")
            if action == "watch_join":
                await broadcast_room_state(mgr, room_id)
                continue
            if action != "watch_cmd":
                continue
            cmd = msg.get("cmd", "")
            updated = mgr.apply_command(
                room_id,
                cmd,
                video_id=msg.get("video_id"),
                position=msg.get("position"),
                playing=msg.get("playing"),
                device_id=str(msg.get("device_id") or "").strip() or None,
            )
            if updated:
                await broadcast_room_state(mgr, room_id)
    except WebSocketDisconnect:
        pass
    finally:
        mgr.unregister_ws(room_id, ws)
        await broadcast_room_state(mgr, room_id)


# Mount static (keep at end)
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

# Health endpoint (kept for compatibility + our v7.5 autonomous + HT + agents)
@app.get("/api/health")
async def api_health(light: bool = False, full: bool = False):
    if light and not full:
        return {"status": "ok", "backend": "online"}

    ht_info = {"enabled": False, "logical_cpus": os.cpu_count() or 12, "workers": 1}
    if ht:
        try:
            ht_info = ht.status()
        except Exception:
            pass

    agent_info = {"loaded": AGENT_STATE.get("loaded", False), "count": len(AGENT_STATE.get("agents", {})), "auto": "auto-load on startup; assignment is manual via POST /api/agents/assign"}
    try:
        if get_loaded_agents:
            agent_info["count"] = len(get_loaded_agents())
    except:
        pass

    payload: Dict[str, Any] = {
        "status": "ok",
        "backend": "online",
        "fusion_os": "v7.5 MasterSeed (merged with v7.4 WS/HT)",
        "core": "ALTE_Frau_95g v7.4 + v7.5",
        "mainframe": {"loaded": True, "version": "v7.4/v7.5", "boot_phase": "full"},
        "hyperthreading": ht_info,
        "ws_endpoint": "/ws",
        "tasks": {
            "autonomous": False,
            "queue_len": len(TASK_QUEUE) if "TASK_QUEUE" in globals() else 0,
            "jobs_len": len(JOBS) if "JOBS" in globals() else 0,
            "support": "POST /api/input appends to TASK_QUEUE; GET /api/jobs lists recent jobs",
        },
        "agents": agent_info,
        "supabase": (supa.status() if supa else {"configured": False, "error": "supabase_client module not loaded"}),
        "input_factors": get_input_factors(),
        "output_factors": get_output_factors(),
        "resource_coupler": (
            get_resource_coupler().status().get("coupler")
            if get_resource_coupler() else {"enabled": False}
        ),
        "all_modules": os.getenv("FUSION_ALL_MODULES", "1") == "1",
        "llm_backend": os.getenv("FUSION_LLM_BACKEND", "llama-local"),
        "provider_switcher": (
            __import__("core.provider_switcher", fromlist=["status"]).status()
            if os.getenv("FUSION_PROVIDER_AUTO", "1") == "1"
            else {"auto_enabled": False, "active_backend": os.getenv("FUSION_LLM_BACKEND", "llama-local")}
        ),
        "agent_control": (
            __import__("core.agent_control", fromlist=["status"]).status()
            if os.getenv("FUSION_AGENT_CONTROL", "1") == "1"
            else {"enabled": False}
        ),
    }
    if full:
        try:
            from connectivity import build_connectivity_summary, build_discovery

            payload["discovery"] = build_discovery()
            payload["connectivity"] = build_connectivity_summary()
        except Exception as exc:
            payload["connectivity_error"] = str(exc)[:200]
    return payload

@app.get("/api/supabase/health")
async def api_supabase_health(probe: bool = False):
    """Supabase-Status. ?probe=true macht einen echten (opt-in) Netzwerk-Check."""
    if supa is None:
        return {"configured": False, "error": "supabase_client module not loaded"}
    # Blockierender Probe-Aufruf im Threadpool, um den Event-Loop nicht zu blockieren
    return await asyncio.to_thread(supa.status, probe)

# === Agent state and helpers (for auto load/assign) ===
def _ensure_agents():
    if AGENT_STATE.get("loaded"):
        return AGENT_STATE
    _ensure_agents_shared()
    try:
        AGENT_STATE["agents"] = get_loaded_agents() or {}
        AGENT_STATE["loaded"] = True
    except Exception:
        AGENT_STATE["agents"] = {}
    return AGENT_STATE

# Autonomous task support
JOBS: Dict[str, Dict[str, Any]] = {}
TASK_QUEUE: List[Dict[str, Any]] = []

class InputPayload(BaseModel):
    query: str = ""
    task_id: Optional[int] = None
    category: str = "user"

class OrchestratePayload(BaseModel):
    query: str = ""
    model_pool: Optional[List[str]] = None

# === Hyperthreading + Agents + Input endpoints (from our consolidation) ===
@app.get("/api/hyperthreading")
async def get_hyperthreading():
    if ht:
        return ht.status()
    return {"enabled": False, "logical_cpus": os.cpu_count() or 12, "workers": 1}

@app.post("/api/hyperthreading")
async def post_hyperthreading(payload: dict):
    enabled = payload.get("enabled", True)
    if ht:
        res = ht.enable(bool(enabled))
        os.environ["FUSION_HYPERTHREADING"] = "1" if enabled else "0"
        return res
    return {"enabled": bool(enabled), "workers": (os.cpu_count() or 12) * 4 if enabled else 1}

@app.get("/api/agents")
async def api_agents():
    state = _ensure_agents()
    return {"loaded": state.get("loaded"), "agents": state.get("agents", {}), "count": len(state.get("agents", {}))}

@app.post("/api/agents/load")
async def api_agents_load():
    state = _ensure_agents()
    state["loaded"] = True
    return {"status": "ok", "loaded": True}

@app.post("/api/agents/assign")
async def api_agents_assign(payload: dict):
    _ensure_agents()
    dom = payload.get("dom", "General")
    agent_map = {"Math": "math-worker", "Phil": "phil-worker", "Info": "info-worker"}
    agent = agent_map.get(dom, "general-worker")
    _schedule_agent_audit(
        "assign",
        job_id=payload.get("job_id"),
        agent=agent,
        dom=dom,
        category=payload.get("category"),
        query=payload.get("query"),
        payload=payload,
    )
    return {"status": "ok", "agent": agent}

@app.post("/api/input")
async def api_input(payload: InputPayload):
    query = (payload.query or "").strip()
    if not query:
        return {"status": "error", "msg": "empty query"}
    normalized, cat, _, dom = classify_and_normalize(query)
    job_id = str(uuid.uuid4())[:8]
    agent_map = {"Math": "math-worker", "Phil": "phil-worker", "Info": "info-worker"}
    agent = agent_map.get(dom, "general-worker")
    job = {"id": job_id, "query": normalized, "category": cat, "dom": dom, "status": "received", "agent": agent}
    JOBS[job_id] = job
    TASK_QUEUE.append(job)
    if supa_store:
        asyncio.create_task(asyncio.to_thread(supa_store.save_job, dict(job)))
    _schedule_agent_audit(
        "job_received",
        job_id=job_id,
        agent=agent,
        dom=dom,
        category=cat,
        query=normalized,
        payload=job,
    )
    await emit({"type": "task_input", "msg": f"Input auto-checked + agent assigned: {normalized[:60]}"})
    return {"status": "ok", "job_id": job_id, "normalized": normalized, "category": cat}

@app.post("/api/v12/orchestrate")
async def api_orchestrate(payload: OrchestratePayload):
    query = (payload.query or "").strip()
    normalized, cat, _, dom = classify_and_normalize(query)
    try:
        from core.local_llama import default_model_pool
        models = payload.model_pool or default_model_pool()
    except Exception:
        models = payload.model_pool or ["grok-intern", "fusion-hero"]
    if dom == "Math":
        models = ["grok-intern", "qb-qubo"] + [m for m in models if m not in ("grok-intern", "qb-qubo")]
    try:
        from core.dynamic_orchestration_core import DynamicOrchestrationCoreModule
        result = await asyncio.to_thread(
            DynamicOrchestrationCoreModule().orchestrate, normalized, models,
        )
        result["category"] = cat
        result["dom"] = dom
        _schedule_agent_audit(
            "orchestrate",
            dom=dom,
            category=cat,
            query=normalized,
            status=str(result.get("status", "ok")),
            payload={"used_models": models, "result_keys": list(result.keys())[:12]},
        )
        return result
    except Exception as exc:
        _schedule_agent_audit(
            "orchestrate_error",
            dom=dom,
            category=cat,
            query=normalized,
            status="error",
            payload={"error": str(exc), "models": models},
        )
        return {
            "status": "success",
            "query": normalized,
            "used_models": models,
            "synthesised_response": f"[Merged v7.4/v7.5] Orchestrated for {dom}",
            "category": cat,
            "dom": dom,
            "error": str(exc),
        }

# Auto load on start
_ensure_agents()
if ht:
    try:
        ht.enable(True)
    except: pass

# Automatische Faktor-Erkennung auch für direkte Aufrufe
detect_input_factors()
detect_output_factors()

@app.get("/api/input-factors")
async def api_input_factors():
    return get_input_factors()

@app.get("/api/output-factors")
async def api_output_factors():
    return get_output_factors()

# === AutoLoad Endpoints (generell, für start_all.ps1 und Boot-Optimierung) ===
@app.post("/api/autoload/run")
async def api_autoload_run(payload: dict = None):
    if payload is None:
        payload = {}
    phase = payload.get("phase", "staged")
    force = payload.get("force", False)
    sync = payload.get("sync", False)
    attach_meta = payload.get("attach_meta", False)
    result = autoloader.run(phase=phase, force=force, sync=sync, attach_meta=attach_meta)
    # Also ensure core things
    _ensure_agents()
    if ht:
        try:
            ht.enable(autoloader.status().get("hyperthreading", {}).get("enabled", True))
        except:
            pass
    return result

@app.get("/api/autoload/status")
async def api_autoload_status():
    return autoloader.status()


@app.get("/api/gpu/memory")
async def api_gpu_memory():
    alloc = get_gpu_allocator()
    if not alloc:
        return {"error": "gpu_allocator_unavailable"}
    return alloc.status()


@app.post("/api/gpu/allocator/rebalance")
async def api_gpu_allocator_rebalance():
    alloc = get_gpu_allocator()
    if not alloc:
        return {"error": "gpu_allocator_unavailable"}
    return alloc.rebalance_once()


@app.get("/api/gpu/allocator/status")
async def api_gpu_allocator_status():
    alloc = get_gpu_allocator()
    if not alloc:
        return {"error": "gpu_allocator_unavailable"}
    return alloc.status()


@app.get("/api/cpu/tuner/status")
async def api_cpu_tuner_status():
    tuner = get_cpu_tuner()
    if not tuner:
        return {"error": "cpu_tuner_unavailable"}
    return tuner.status()


@app.post("/api/cpu/tuner/run")
async def api_cpu_tuner_run():
    tuner = get_cpu_tuner()
    if not tuner:
        return {"error": "cpu_tuner_unavailable"}
    return tuner.tune_once()


@app.get("/api/resource/coupler/status")
async def api_resource_coupler_status():
    coupler = get_resource_coupler()
    if not coupler:
        return {"error": "resource_coupler_unavailable"}
    return coupler.status()


@app.post("/api/resource/coupler/run")
async def api_resource_coupler_run():
    coupler = get_resource_coupler()
    if not coupler:
        return {"error": "resource_coupler_unavailable"}
    return coupler.couple_once()


@app.get("/api/gpu/compute/status")
async def api_gpu_compute_status():
    booster = get_gpu_compute_booster()
    if not booster:
        return {"error": "gpu_compute_booster_unavailable"}
    return booster.status()


@app.post("/api/gpu/compute/boost")
async def api_gpu_compute_boost():
    booster = get_gpu_compute_booster()
    if not booster:
        return {"error": "gpu_compute_booster_unavailable"}
    return booster.boost_once()


@app.get("/api/memory/status")
async def api_memory_status():
    guard = get_memory_guard()
    if not guard:
        return {"error": "memory_guard_unavailable"}
    return guard.status()


@app.post("/api/memory/relieve")
async def api_memory_relieve():
    guard = get_memory_guard()
    if not guard:
        return {"error": "memory_guard_unavailable"}
    return guard.relieve_once()


@app.post("/api/gpu/vram/prioritize")
async def api_gpu_vram_prioritize():
    prio = get_vram_prioritizer()
    if not prio:
        return {"error": "vram_prioritizer_unavailable"}
    return prio.prioritize_once()


@app.get("/api/supabase/events")
async def api_supabase_events(limit: int = 20):
    if supa_store is None:
        return {"events": [], "error": "supabase_store not loaded"}
    return {"events": await asyncio.to_thread(supa_store.list_recent_events, limit)}


@app.get("/api/supabase/tables")
async def api_supabase_tables():
    """Read-only: prüft, welche Ziel-Tabellen im Supabase-Projekt existieren.
    'missing' => Schema noch nicht angewendet (supabase/schema.sql)."""
    if supa_store is None:
        return {"ok": False, "error": "supabase_store not loaded"}
    return await asyncio.to_thread(supa_store.check_tables)


@app.post("/api/llama/train")
async def api_llama_train():
    """Heroic Llama Optimizer (QUBO+SA) — setzt llama-local nach Training."""
    root = BASE.parent / "internal_llm"

    def _run():
        import subprocess
        import sys
        env = os.environ.copy()
        env["FUSION_LLM_BACKEND"] = "llama-local"
        return subprocess.run(
            [sys.executable, "train.py"],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=600,
            encoding="utf-8",
            errors="replace",
            env=env,
        )

    proc = await asyncio.to_thread(_run)
    if proc.returncode != 0:
        return {"status": "error", "stderr": (proc.stderr or "")[-800:]}
    os.environ["FUSION_LLM_BACKEND"] = "llama-local"
    try:
        from core.local_llama import get_local_llama
        status = get_local_llama().status()
    except Exception as exc:
        status = {"error": str(exc)}
    if supa_store:
        try:
            import json
            cfg_path = root / "output" / "heroic_llama_config.json"
            if cfg_path.exists():
                cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
                asyncio.create_task(asyncio.to_thread(supa_store.save_llama_config, cfg))
        except Exception:
            pass
    return {"status": "ok", "llm_backend": "llama-local", "llama": status, "stdout": (proc.stdout or "")[-400:]}


@app.get("/api/supabase/node-health")
async def api_supabase_node_health():
    """@supabase/server npm Paket Health-Check."""
    script = BASE / "scripts" / "supabase-health.mjs"
    if not script.exists():
        return {"error": "supabase-health.mjs missing"}

    def _run():
        import subprocess
        return subprocess.run(
            ["node", str(script)],
            cwd=str(BASE),
            capture_output=True,
            text=True,
            timeout=15,
            env=os.environ.copy(),
        )

    proc = await asyncio.to_thread(_run)
    try:
        import json
        return json.loads(proc.stdout or "{}")
    except Exception:
        return {"status": "error", "stdout": proc.stdout, "stderr": proc.stderr}


@app.post("/api/supabase/sync/metrics")
async def api_supabase_sync_metrics():
    if supa_store is None:
        return {"error": "supabase_store not loaded"}
    metrics = await get_metrics()
    payload = metrics if isinstance(metrics, dict) else metrics.model_dump()
    result = await asyncio.to_thread(supa_store.save_metrics, payload)
    return result


@app.get("/api/supabase/sync/status")
async def api_supabase_sync_status():
    if supa_store is None:
        return {"error": "supabase_store not loaded"}
    return await asyncio.to_thread(supa_store.sync_status)


@app.get("/api/supabase/audit")
async def api_supabase_audit(limit: int = 20):
    if supa_store is None:
        return {"entries": [], "error": "supabase_store not loaded"}
    return {"entries": await asyncio.to_thread(supa_store.list_recent_agent_audit, limit)}


@app.post("/api/supabase/settings/pull")
async def api_supabase_settings_pull():
    if supa_store is None:
        return {"error": "supabase_store not loaded"}
    return await asyncio.to_thread(supa_store.pull_settings_from_cloud, True)


# === VR / Highest Layer routes ===
try:
    from vr_routes import router as _vr_router
    app.include_router(_vr_router)
except Exception as _vr_err:
    print(f"[API] VR routes note: {_vr_err}")

# === Alle Module + fehlende Endpunkte freigeben ===
try:
    from api_extensions import router as _extensions_router
    app.include_router(_extensions_router)
except Exception as _ext_err:
    print(f"[API] Extensions note: {_ext_err}")

# === AscensionOS v9.5/v9.6 (Stage9, Sisyphos-Oszillation, Psycholyse, QUBO, Harmonisierung, Geisterjagd) ===
try:
    from ascension_v9_routes import router as _ascension_v9_router
    app.include_router(_ascension_v9_router)
except Exception as _asc_v9_err:
    print(f"[API] AscensionOS v9 routes note: {_asc_v9_err}")

# === Local Infrastructure Kernel (RAM/Disk C:/Tailscale/Services, ok/warn/alert/critical) ===
# Kernlogik: src/normal_os/core/local_infrastructure_kernel.py (siehe
# workstation/contracts/local_infrastructure_kernel.v1.json). Diese Zeile ist
# beim vorherigen main<->ascension-Merge-Konflikt in app.py verloren gegangen
# (Datei blieb erhalten, Einhaengung nicht) - hiermit wiederhergestellt.
try:
    from resource_guardian_routes import router as _resource_guardian_router
    app.include_router(_resource_guardian_router)
except Exception as _rg_err:
    print(f"[API] Resource Guardian routes note: {_rg_err}")
