# v8_core_bridge.py — Brücke zu root core/ (heroic_math_engine, heroic_core_orchestrator)

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ROOT_CORE = _REPO_ROOT / "core"
_LOADED: Dict[str, Any] = {}


def _load_root_module(module_name: str, filename: str):
    if module_name in _LOADED:
        return _LOADED[module_name]
    path = _ROOT_CORE / filename
    if not path.exists():
        raise FileNotFoundError(f"v8 core module not found: {path}")
    spec = importlib.util.spec_from_file_location(f"fusion_v8_{module_name}", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"fusion_v8_{module_name}"] = mod
    spec.loader.exec_module(mod)
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