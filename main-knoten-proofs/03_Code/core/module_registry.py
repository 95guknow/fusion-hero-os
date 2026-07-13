# module_registry.py — zentrale Freigabe aller Fusion Hero OS Module

from __future__ import annotations

import importlib
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

_CORE = Path(__file__).parent
_DASH = _CORE.parent / "Dashboard"
_INTERNAL_LLM = _CORE.parent / "internal_llm"

_REGISTRY: Dict[str, Dict[str, Any]] = {}
_LOADED: Dict[str, bool] = {}


def _try_import(path: str, attr: Optional[str] = None) -> Any:
    if str(_CORE) not in sys.path:
        sys.path.insert(0, str(_CORE))
    try:
        mod = importlib.import_module(path)
        return getattr(mod, attr) if attr else mod
    except (ImportError, AttributeError) as exc:
        # Erwartbar: Modul/Attribut (noch) nicht vorhanden oder optionales
        # Dependency fehlt (z.B. Hardware-/GPU-Bibliothek).
        logger.warning("Modul %r nicht verfügbar (%s): %s", path, attr, exc)
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — echter Bug im Modul, nicht nur "fehlt"
        logger.error("Modul %r ist beim Laden fehlgeschlagen (%s): %s", path, attr, exc, exc_info=True)
        return {"error": str(exc)}


def _load_code_module(module: str, attr: Optional[str] = None) -> Any:
    code_root = _CORE.parent
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    try:
        mod = importlib.import_module(module)
        return getattr(mod, attr) if attr else mod
    except (ImportError, AttributeError) as exc:
        logger.warning("Code-Modul %r nicht verfügbar (%s): %s", module, attr, exc)
        return {"error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — echter Bug im Modul, nicht nur "fehlt"
        logger.error("Code-Modul %r ist beim Laden fehlgeschlagen (%s): %s", module, attr, exc, exc_info=True)
        return {"error": str(exc)}


def _register(
    name: str,
    layer: int,
    category: str,
    loader: Callable[[], Any],
    description: str = "",
) -> None:
    _REGISTRY[name] = {
        "name": name,
        "layer": layer,
        "category": category,
        "description": description,
        "loader": loader,
        "enabled": os.getenv("FUSION_ALL_MODULES", "1") == "1",
    }


def _build_registry() -> None:
    if _REGISTRY:
        return

    _register("hyperthreading", 1, "performance",
              lambda: _try_import("hyperthreading_config", "enable")(True),
              "Hyperthreading + virtuelle GPU-Threads")
    _register("gpu_allocator", 1, "performance",
              lambda: _try_import("gpu_memory_allocator", "get_gpu_allocator")().rebalance_once(),
              "Adaptiver VRAM-Allocator")
    _register("cpu_tuner", 1, "performance",
              lambda: _try_import("cpu_adaptive_tuner", "get_cpu_tuner")().tune_once(),
              "CPU Last+Temperatur Tuner")
    _register("resource_coupler", 1, "performance",
              lambda: _try_import("resource_coupler", "get_resource_coupler")().couple_once(),
              "CPU+GPU+SSD Kopplung")
    _register("gpu_compute_booster", 1, "performance",
              lambda: _try_import("gpu_compute_booster", "get_gpu_compute_booster")().boost_once(),
              "GPU SM-Auslastung via llama-server")
    _register("virtual_gpu_ht", 1, "performance",
              lambda: _try_import("virtual_gpu_hyperthreading", "get_virtual_gpu_ht_cache")().status(),
              "Virtuelle Hyper-Threads auf VRAM")
    _register("ssd_cache", 1, "storage",
              lambda: _try_import("ssd_longterm_cache", "SSDLongTermCache")().status(),
              "SSD Long-Term Cache")
    _register("heroic_orchestration", 2, "orchestration",
              lambda: _try_import("heroic_orchestration", "ensure_agents_loaded")(True),
              "Agenten + QUBO + Klassifikation")
    _register("dynamic_orchestration", 2, "orchestration",
              lambda: _try_import("dynamic_orchestration_core", "DynamicOrchestrationCoreModule")(),
              "Multi-Model Orchestrierung")
    _register("selfmodify_core", 3, "meta",
              lambda: _try_import("SelfModifyCoreModule", "SelfModifyCoreModule")(),
              "Self-Modification Proposals")
    _register("critical_meta", 3, "meta",
              lambda: _try_import("CriticalMetaAnalysisCoreModule", "CriticalMetaAnalysisCoreModule")(),
              "Epistemische Meta-Analyse")
    _register("generational_evolution", 3, "meta",
              lambda: _try_import("GenerationalEvolutionProtocolCoreModule", "GenerationalEvolutionProtocolCoreModule")(),
              "Generational Evolution Protocol")
    _register("google_sync", 2, "sync",
              lambda: _try_import("google_multi_account_sync_core", "GoogleMultiAccountSyncCoreModule")(),
              "Google Multi-Account Sync")
    _register("classical", 2, "math",
              lambda: _try_import("classical"),
              "Klassische Mathematik-Module")
    _register("agent_control", 2, "orchestration",
              lambda: _try_import("agent_control", "status")(),
              "Globale Agenten-Kontrolle (Multi-Strategie)")
    _register("geisterjagd_banach_viz", 2, "viz",
              lambda: _try_import("geisterjagd_banach_viz", "get_viz")().snapshot(),
              "Geisterjagd + Banach-Kontraktion Visualisierung")
    _register("heroic_science_audit", 2, "science",
              lambda: _try_import("heroic_science_audit", "status")(),
              "Heroik-Wissenschaft Audit (Claude Science)")
    _register("qubo_llama_bridge", 2, "llm",
              lambda: _try_import("qubo_llama_bridge", "status")(),
              "QUBO-Logik in lokales Llama (Inference + Synthese)")
    _register("first_install_bootstrap", 0, "substrate",
              lambda: {
                  "pending": _try_import("first_install_bootstrap", "is_first_install_pending")(),
              },
              "Einmalige Erstinstallation aller Dienste")
    _register("local_llama", 2, "llm",
              lambda: _try_import("local_llama", "get_local_llama")().status(),
              "Lokales Llama (Heroic Optimizer)")
    _register("llama_subagent_tester", 2, "llm",
              lambda: _try_import("llama_subagent_tester", "status")(),
              "Subagent-Tracks: Llama Status/CLI/QUBO/Generate-Tests")
    _register("agent_backend_router", 2, "orchestration",
              lambda: _try_import("agent_backend_router", "status")(),
              "Agent→Llama, Anti-Agent→Grok Routing")
    _register("conversation_context_core", 1, "orchestration",
              lambda: _try_import("conversation_context_core", "status")(),
              "Adaptives Kontextfenster + Banach-Rückkopplung zum Start-Kontext")
    _register("provider_switcher", 2, "orchestration",
              lambda: _try_import("provider_switcher", "select_provider")(force_probe=True),
              "Automatischer LLM-Anbieterwechsler")
    _register("claude_science", 2, "science",
              lambda: _try_import("claude_science", "status")(),
              "Claude Science Workbench (Anthropic API)")
    _register("parallel_internal_optimizer", 2, "orchestration",
              lambda: _try_import("parallel_internal_optimizer", "run")(),
              "Parallele Intern-Optimierung (Hyperthreading-Tracks)")
    _register("windows_substrate", 0, "substrate",
              lambda: _try_import("windows_substrate", "get_substrate")().status(),
              "Windows Meta-Layer + Cyber Layer")
    _register("supabase", 2, "storage",
              lambda: _load_supabase(),
              "Supabase Persistenz swmmoxhdzarmoupyssqe")
    _register("resource_workflow", 1, "performance",
              lambda: _try_import("resource_workflow", "status")(),
              "RAM/CPU-bewusste Worker-Empfehlung für Subagents")
    _register("heroic_math_engine", 2, "math",
              lambda: _try_import("v8_core_bridge", "math_status")(),
              "v8 Heroic Math Engine (root core/)")
    _register("heroic_core_orchestrator", 2, "orchestration",
              lambda: _try_import("v8_core_bridge", "orchestrator_status")(),
              "v8 Layer 0/4/5 Orchestrator (root core/)")
    _register("medienserver", 2, "sync",
              lambda: _try_import("medienserver_bridge", "status")(),
              "Grok Medienserver (Google Drive G:)")
    _register("hero_guide", 0, "layer0",
              lambda: _load_code_module("hero_guide_ide", "status")(),
              "HERO-GUIDE Geltungs-Werkbank")
    _register("audit_agent", 0, "layer0",
              lambda: _load_code_module("audit_agent", "status")(),
              "Executable Audit Agent")
    _register("knowledge_graph", 1, "science",
              lambda: _load_code_module("knowledge_graph", "get_knowledge_graph")().status(),
              "Epistemischer Wissensgraph")
    def _anti_loop():
        cls = _load_code_module("StarrLernenderAntiLoopGuardCoreModule_v1", "StarrLernenderAntiLoopGuard")
        if isinstance(cls, dict):
            return cls
        inst = cls()
        return {
            "module": "anti_loop_guard",
            "agents": len(getattr(inst, "agents", {})),
            "max_workers": getattr(inst, "max_workers", None),
        }

    _register("anti_loop_guard", 3, "meta", _anti_loop, "StarrLernender Anti-Loop Guard")

    def _token_mgmt():
        cls = _load_code_module("TokenManagementSystem", "TokenManagementSystem")
        if isinstance(cls, dict):
            return cls
        inst = cls()
        return {
            "module": "token_management",
            "base_tokens": getattr(inst, "base_tokens", None),
            "allocation_log_len": len(getattr(inst, "allocation_log", [])),
        }

    _register("token_management", 2, "orchestration", _token_mgmt, "Token Management System")

    if str(_DASH) not in sys.path:
        sys.path.insert(0, str(_DASH))

    def _foundation():
        from foundation_loader import ensure_foundation_on_path, foundation_report_to_dict, load_check_foundation_gate

        if ensure_foundation_on_path() is None:
            return {"passed": False, "error": "heroic-core-foundation not found"}
        check = load_check_foundation_gate()
        report = check("[Modell] foundation probe", require_explicit=False)
        return foundation_report_to_dict(report)

    _register("foundation_gate", 0, "layer0", _foundation, "Heroic Core Foundation Gate")

    def _highest_layer():
        # Konfigurierbar statt hartkodiert: FUSION_HIGHEST_LAYER_PATH überschreibt
        # den Default, damit dieses Modul nicht nur auf einer bestimmten Maschine
        # mit exakt diesem Home-Verzeichnis funktioniert.
        default_path = Path.home() / "heroic-highest-layer"
        p = Path(os.getenv("FUSION_HIGHEST_LAYER_PATH", str(default_path)))
        if not p.exists():
            return {"error": f"heroic-highest-layer nicht gefunden unter {p} "
                              f"(FUSION_HIGHEST_LAYER_PATH setzen, falls anderer Pfad)"}
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
        from highest_layer import load  # type: ignore
        return load().status()

    _register("highest_layer", 4, "layer4", _highest_layer, "Heroic Highest Layer Roadmap")


def _load_supabase() -> Any:
    if str(_DASH) not in sys.path:
        sys.path.insert(0, str(_DASH))
    import supabase_client as sc  # type: ignore
    return sc.status(do_probe=True)


def list_modules() -> List[Dict[str, Any]]:
    _build_registry()
    out = []
    for name, info in _REGISTRY.items():
        out.append({
            "name": name,
            "layer": info["layer"],
            "category": info["category"],
            "description": info["description"],
            "enabled": info["enabled"],
            "loaded": _LOADED.get(name, False),
        })
    return sorted(out, key=lambda x: (x["layer"], x["name"]))


def load_module(name: str) -> Dict[str, Any]:
    _build_registry()
    info = _REGISTRY.get(name)
    if not info:
        return {"status": "error", "error": f"unknown module: {name}"}
    try:
        result = info["loader"]()
        _LOADED[name] = True
        return {"status": "ok", "module": name, "result": _safe(result)}
    except Exception as exc:
        return {"status": "error", "module": name, "error": str(exc)}


def load_all(force: bool = False) -> Dict[str, Any]:
    _build_registry()
    results: Dict[str, Any] = {"loaded": [], "errors": [], "ts": time.time()}
    for name, info in _REGISTRY.items():
        if not info["enabled"] and not force:
            continue
        if _LOADED.get(name) and not force:
            results["loaded"].append(name)
            continue
        r = load_module(name)
        if r.get("status") == "ok":
            results["loaded"].append(name)
        else:
            results["errors"].append({name: r.get("error")})
    results["count"] = len(results["loaded"])
    results["total"] = len(_REGISTRY)
    return results


def _safe(obj: Any) -> Any:
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _safe(v) for k, v in list(obj.items())[:30]}
    if isinstance(obj, (list, tuple)):
        return [_safe(x) for x in obj[:20]]
    if hasattr(obj, "status") and callable(obj.status):
        try:
            return obj.status()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {"type": type(obj).__name__}
    return str(obj)[:200]


def resource_plan() -> Dict[str, Any]:
    _build_registry()
    import psutil
    cpus = psutil.cpu_count(logical=True) or 12
    mem = psutil.virtual_memory()
    plan = {
        "agents": {
            "supervisor": max(1, cpus // 6),
            "math-worker": max(1, cpus // 4),
            "phil-worker": max(1, cpus // 6),
            "info-worker": max(1, cpus // 6),
            "general-worker": max(2, cpus // 3),
        },
        "gpu": {
            "vram_target_ratio": float(os.getenv("FUSION_VRAM_TARGET_RATIO", "0.92")),
            "compute_target_pct": float(os.getenv("FUSION_GPU_COMPUTE_TARGET_PCT", "55")),
            "llama_gpu_layers": int(os.getenv("FUSION_LLAMA_GPU_LAYERS", "25")),
        },
        "cpu": {
            "performance_ratio": float(os.getenv("FUSION_PERFORMANCE_RATIO", "1.0")),
            "target_workers": cpus * 4,
        },
        "modules_enabled": sum(1 for m in _REGISTRY.values() if m["enabled"]),
        "modules_loaded": sum(1 for v in _LOADED.values() if v),
        "ram_available_gb": round(mem.available / (1024 ** 3), 2),
    }
    return plan


def signal_health(layer: str = "full") -> Dict[str, Any]:
    import psutil
    base = {
        "pulse": {"cpu": psutil.cpu_percent(), "ts": time.time()},
        "modules": {"loaded": sum(_LOADED.values()), "total": len(_REGISTRY) or 0},
    }
    if layer == "pulse":
        return base
    base["delta"] = {"ram": psutil.virtual_memory().percent, "profile": os.getenv("FUSION_PROFILE", "admin")}
    if layer == "delta":
        return base
    base["batch"] = resource_plan()
    if layer == "batch":
        return base
    base["full"] = list_modules()
    return base