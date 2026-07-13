# v8_core_bridge.py — Brücke zu fusion_hero_os.core (heroic_math_engine, heroic_core_orchestrator)

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ROOT_CORE = _REPO_ROOT / "fusion_hero_os" / "core"
_LOADED: Dict[str, Any] = {}


def _load_root_module(module_name: str, filename: str):
    """Lädt ein Modul aus fusion_hero_os.core über den normalen Python-Importmechanismus
    (statt der vorherigen manuellen ``spec_from_file_location``-Konstruktion), damit
    relative Importe innerhalb von fusion_hero_os (z.B. core -> registry) funktionieren.
    """
    if module_name in _LOADED:
        return _LOADED[module_name]
    path = _ROOT_CORE / filename
    if not path.exists():
        raise FileNotFoundError(f"v8 core module not found: {path}")
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    mod = importlib.import_module(f"fusion_hero_os.core.{module_name}")
    _LOADED[module_name] = mod
    return mod


def math_status() -> Dict[str, Any]:
    try:
        mod = _load_root_module("heroic_math_engine", "heroic_math_engine.py")
        engine = mod.HeroicMatrixEngine()
        comm = engine.compute_commutator(engine.q_default, engine.b_default)
        reciprocal = engine.check_reciprocity_condition(
            engine.q_default, engine.b_default, engine.q_default, engine.b_default
        )
        ip = mod.RepairedStructureIP(lmbda=0.5, eta=0.2)
        psi = complex(2.0, -1.0)
        stability = ip.compute_stability(psi)
        return {
            "ok": True,
            "module": "heroic_math_engine",
            "path": str(_ROOT_CORE / "heroic_math_engine.py"),
            "commutator_norm": float(abs(comm[0, 0]) + abs(comm[1, 1])),
            "reciprocity_self": reciprocal,
            "stability_sample": round(stability, 4),
        }
    except Exception as exc:
        return {"ok": False, "module": "heroic_math_engine", "error": str(exc)}


def orchestrator_status() -> Dict[str, Any]:
    try:
        mod = _load_root_module("heroic_core_orchestrator", "heroic_core_orchestrator.py")
        seed = mod.MasterSeed()
        spine = mod.PMSEvidenceSpine(executable_path=str(_REPO_ROOT / "pms_rust_kernel"))
        bridge = mod.QuadCoreBridge(spine)
        return {
            "ok": True,
            "module": "heroic_core_orchestrator",
            "path": str(_ROOT_CORE / "heroic_core_orchestrator.py"),
            "master_seed": {
                "criticality_target": seed.criticality_target,
                "strict_contraction": seed.strict_contraction_enforced,
            },
            "bridge_mode": bridge.mode,
            "pms_kernel_path": spine.kernel_path,
        }
    except Exception as exc:
        return {"ok": False, "module": "heroic_core_orchestrator", "error": str(exc)}


def run_math_verification() -> Dict[str, Any]:
    try:
        mod = _load_root_module("heroic_math_engine", "heroic_math_engine.py")
        mod.run_sandbox_verification()
        return {"ok": True, "verification": "sandbox_completed"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def bootstrap_orchestrator() -> Dict[str, Any]:
    try:
        mod = _load_root_module("heroic_core_orchestrator", "heroic_core_orchestrator.py")
        bridge = mod.bootstrap_v8_system()
        return {
            "ok": True,
            "bridge_mode": bridge.mode,
            "domains": ["MYTHOS", "GRUND", "BEWEIS", "GESTALT"],
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def _ensure_repo_path() -> None:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))


def ipc_status() -> Dict[str, Any]:
    """Kernel C↔Python IPC Bridge status (TCP / in-process)."""
    try:
        _ensure_repo_path()
        from fusion_hero_os.bridge.gateway import get_ipc_gateway

        return get_ipc_gateway().status()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def ipc_dispatch(module: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Dispatch a fusion_hero_os BaseModule via IPC gateway."""
    try:
        _ensure_repo_path()
        from fusion_hero_os.bridge.gateway import get_ipc_gateway

        return get_ipc_gateway().dispatch(module, payload)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def process_query(domain: str, operator_id: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        mod = _load_root_module("heroic_core_orchestrator", "heroic_core_orchestrator.py")
        spine = mod.PMSEvidenceSpine(executable_path=str(_REPO_ROOT / "pms_rust_kernel"))
        bridge = mod.QuadCoreBridge(spine)
        result = bridge.process_query(domain, operator_id, payload or {})
        if isinstance(result, dict):
            return {"ok": True, "domain": domain, "operator_id": operator_id, "result": result}
        return {"ok": True, "domain": domain, "operator_id": operator_id, "result": str(result)}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "domain": domain}