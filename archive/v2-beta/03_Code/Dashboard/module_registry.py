# -*- coding: utf-8 -*-
"""Fusion Hero OS — Unified Module, Function & Agent Registry."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from hyperthreading_config import is_hyperthreading_enabled, parallel_workers, status as ht_status
from agent_resource_allocator import get_resource_plan, pick_agent_pool
from fusion_profile import get_active_profile_name, profile_status
from boot_optimizer import medienserver_sync_needed, optimize_steps, boot_plan, FAST_BOOT_STEPS

ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = Path(__file__).resolve().parent
FOUNDATION_ROOT = Path(os.getenv("HEROIC_FOUNDATION", r"C:\Users\Admin\heroic-core-foundation"))
HIGHEST_LAYER_ROOT = Path(os.getenv("HEROIC_HIGHEST_LAYER", r"C:\Users\Admin\heroic-highest-layer"))
AGENTS_DIR = Path(os.getenv("FUSION_AGENTS_DIR", r"C:\Users\Admin\.config\kilo\agents"))
MEDIENSERVER = Path(os.getenv("FUSION_MEDIENSERVER", r"G:\Meine Ablage\Fusion_Hero_OS_v1.2"))

for p in (CODE_ROOT, DASHBOARD, FOUNDATION_ROOT, HIGHEST_LAYER_ROOT, ROOT):
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))


@dataclass
class AgentInfo:
    id: str
    name: str
    description: str
    mode: str = "subagent"
    loaded: bool = False
    path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ModuleInfo:
    id: str
    name: str
    layer: str
    status: str = "pending"
    endpoint: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class FusionRegistry:
    def __init__(self) -> None:
        self.mainframe = None
        self.google_sync = None
        self.orchestrator = None
        self.highest_layer = None
        self.foundation_available = False
        self.agents: Dict[str, AgentInfo] = {}
        self.modules: Dict[str, ModuleInfo] = {}
        self._boot_result: Optional[dict] = None
        self.hyperthreading_enabled = is_hyperthreading_enabled()
        self._resource_plan = None
        self._last_load_result: Optional[dict] = None
        self._catalog()

    def _catalog(self) -> None:
        catalog = [
            ("mainframe", "HEROIC Core Mainframe", "1", "/api/mainframe/status"),
            ("google_sync", "GoogleMultiAccountSync", "1", "/api/v12/sync"),
            ("orchestrator", "DynamicOrchestration", "1/2", "/api/v12/orchestrate"),
            ("foundation", "Heroic Core Foundation", "0", "/api/foundation/gate"),
            ("highest_layer", "Heroic Highest Layer", "4", "/api/layer4/status"),
            ("qubo", "QUBO Solver Engine", "2", "/api/qubo/solve"),
            ("peer_review", "5-Dim PeerReview", "1", "/api/mod/validate"),
            ("hero_guide", "HERO-GUIDE Geltungs-Werkbank", "0", "/api/hero-guide/status"),
            ("knowledge_graph", "Epistemischer Wissensgraph", "1", "/api/knowledge-graph/status"),
            ("medienserver", "Medienserver Sync", "archive", "/api/v12/sync"),
            ("grok", "Grok-intern Bridge", "1", "/api/grok/status"),
            ("meta_layer", "Windows Meta-Layer Host", "3", "/api/meta-layer/status"),
            ("resource_allocator", "Agent Resource Allocator", "3", "/api/resources/plan"),
            ("signal_network", "Layered Signal Network", "3", "/api/signal/status"),
            ("workspace_gui", "Fusion Hero Workspace GUI", "1", "/api/gui/status"),
            ("autoloader", "Treiber & Prozess AutoLoader", "0", "/api/autoload/status"),
        ]
        for mid, name, layer, endpoint in catalog:
            self.modules[mid] = ModuleInfo(id=mid, name=name, layer=layer, endpoint=endpoint)
        self._scan_agents()

    def _scan_agents(self) -> None:
        if not AGENTS_DIR.exists():
            return
        for path in sorted(AGENTS_DIR.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            mode = "subagent"
            desc = path.stem
            name = path.stem.replace("-", " ").title()
            m_mode = re.search(r"^mode:\s*(\S+)", text, re.M)
            m_desc = re.search(r"^description:\s*(.+)$", text, re.M)
            m_name = re.search(r'displayName:\s*["\']?([^"\'\n]+)', text)
            if m_mode:
                mode = m_mode.group(1).strip()
            if m_desc:
                desc = m_desc.group(1).strip()
            if m_name:
                name = m_name.group(1).strip()
            aid = path.stem
            self.agents[aid] = AgentInfo(
                id=aid, name=name, description=desc, mode=mode, path=str(path)
            )

    def _sync_medienserver(self, force: bool = False) -> dict:
        if not force and not medienserver_sync_needed():
            return {"status": "skipped", "reason": "sync_fresh", "needed": False}
        if not MEDIENSERVER.parent.exists():
            return {"status": "skipped", "reason": "Google Drive nicht verfuegbar"}
        script = ROOT / "sync_medienserver.ps1"
        if not script.exists():
            return {"status": "skipped", "reason": "sync_medienserver.ps1 fehlt"}
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "target": str(MEDIENSERVER),
            "output": (proc.stdout or proc.stderr)[-500:],
        }

    def load_all(
        self,
        boot_n: int = 12,
        boot_steps: int = 2000,
        force: bool = False,
        phase: str = "auto",
        sync_medienserver: Optional[bool] = None,
    ) -> dict:
        mf_loaded = bool(self.mainframe and self.modules.get("mainframe", ModuleInfo("", "", "")).status == "loaded")
        plan = boot_plan(mainframe_loaded=mf_loaded, force=force)
        if phase == "auto":
            phase = plan["phase"]
        if not force and phase == "cached" and self._last_load_result:
            return self._last_load_result

        effective_steps = optimize_steps(boot_steps, "fast" if phase == "staged" else phase)
        do_sync = sync_medienserver if sync_medienserver is not None else plan.get("sync", False)

        results: Dict[str, Any] = {
            "modules": {}, "agents": {}, "errors": [],
            "boot_plan": {**plan, "effective_steps": effective_steps, "sync": do_sync},
        }

        skip_mainframe = phase == "cached" or (mf_loaded and not force)
        if skip_mainframe and self._boot_result:
            results["modules"]["mainframe"] = self._boot_result
            self.modules["mainframe"].status = "loaded"
        else:
            try:
                import heroic_core_mainframe as hc
                hc.warmup_kernels()
                self.mainframe = hc.QUBOIntegrationCoreModule()
                Q = hc.make_Q(boot_n, submodular=False, scale=2.5)
                workers = parallel_workers()
                if self.hyperthreading_enabled:
                    out = self.mainframe.execute_parallel_run(
                        Q, steps=effective_steps or boot_steps, T0=2.5, n_restarts=workers,
                    )
                    results["modules"]["mainframe"] = {
                        "energy": round(float(out["energy"]), 6),
                        "runtime_ms": round(out["runtime_seconds"] * 1000, 2),
                        "generation": self.mainframe.evolution.generation,
                        "audit_hooks": list(self.mainframe.self_modify.audit_hooks.keys()),
                        "engine": "qb_qubo.classical_parallel",
                        "hyperthreading": True,
                        "workers": out["workers"],
                        "n_restarts": out["n_restarts"],
                        "cascade": ["pre_solve_audit", "parallel_execution", "post_solve_validation"],
                    }
                else:
                    cfg = hc.QUBOSolverConfig(
                        backend="simulated_annealing", steps=effective_steps or boot_steps, T0=2.5
                    )
                    res = self.mainframe.execute_secure_run(Q, config=cfg)
                    results["modules"]["mainframe"] = {
                        "energy": round(float(res.energy), 6),
                        "runtime_ms": round(res.runtime_seconds * 1000, 2),
                        "generation": self.mainframe.evolution.generation,
                        "audit_hooks": list(self.mainframe.self_modify.audit_hooks.keys()),
                        "engine": "qb_qubo.classical",
                        "hyperthreading": False,
                        "cascade": ["pre_solve_audit", "high_performance_execution", "post_solve_validation"],
                    }
                self.modules["mainframe"].status = "loaded"
                self._boot_result = results["modules"]["mainframe"]
            except Exception as exc:
                self.modules["mainframe"].status = "error"
                self.modules["mainframe"].error = str(exc)
                results["errors"].append(f"mainframe: {exc}")

        try:
            from google_multi_account_sync_core import GoogleMultiAccountSyncCoreModule
            self.google_sync = GoogleMultiAccountSyncCoreModule()
            self.google_sync.register_target("fusion-hero-os")
            if MEDIENSERVER.parent.exists():
                self.google_sync.register_target(str(MEDIENSERVER))
            sync = self.google_sync.sync_horkrux(
                "fusion-hero-os-v1.2", list(self.google_sync.sync_targets)
            )
            self.modules["google_sync"].status = "loaded"
            results["modules"]["google_sync"] = sync
        except Exception as exc:
            self.modules["google_sync"].status = "error"
            results["errors"].append(f"google_sync: {exc}")

        try:
            from dynamic_orchestration_core import DynamicOrchestrationCoreModule
            self.orchestrator = DynamicOrchestrationCoreModule()
            self.orchestrator.enable_hyperthreading(True)
            agent_list = [a.to_dict() for a in self.agents.values()]
            plan = get_resource_plan(agent_list, force=True)
            self.orchestrator.active_models = plan.model_pool
            self._resource_plan = plan
            self.modules["orchestrator"].status = "loaded"
            results["modules"]["orchestrator"] = {
                "hyperthreading": True,
                "agents_registered": len(self.agents),
                "model_pool": plan.model_pool,
                "orchestrator_workers": plan.orchestrator_workers,
            }
            self.modules["resource_allocator"].status = "loaded"
            results["modules"]["resource_allocator"] = plan.to_dict()
            self.modules["signal_network"].status = "loaded"
        except Exception as exc:
            self.modules["orchestrator"].status = "error"
            results["errors"].append(f"orchestrator: {exc}")

        try:
            from foundation import check_foundation_gate, scan_epistemic_hygiene
            self.foundation_available = True
            self.modules["foundation"].status = "loaded"
            results["modules"]["foundation"] = {"functions": ["check_foundation_gate", "scan_epistemic_hygiene"]}
        except Exception as exc:
            self.modules["foundation"].status = "error"
            results["errors"].append(f"foundation: {exc}")

        try:
            from highest_layer import load
            self.highest_layer = load()
            self.modules["highest_layer"].status = "loaded"
            milestones = list(self.highest_layer.roadmap.milestones.values())
            results["modules"]["highest_layer"] = {
                "milestones": len(milestones),
                "active": len(self.highest_layer.roadmap.get_active()),
                "generation": self.highest_layer.protocol.current_generation,
            }
        except Exception as exc:
            self.modules["highest_layer"].status = "error"
            self.modules["highest_layer"].error = str(exc)
            results["errors"].append(f"highest_layer: {exc}")

        self.modules["qubo"].status = "loaded" if self.mainframe else "pending"
        self.modules["peer_review"].status = "loaded"
        results["modules"]["qubo"] = {"engine": "mainframe" if self.mainframe else "fallback"}
        results["modules"]["peer_review"] = {"dimensions": 5}

        try:
            from hero_guide_ide import status as hero_guide_status
            from knowledge_graph import get_knowledge_graph
            self.modules["hero_guide"].status = "loaded"
            self.modules["knowledge_graph"].status = "loaded"
            results["modules"]["hero_guide"] = hero_guide_status()
            results["modules"]["knowledge_graph"] = get_knowledge_graph().status()
        except Exception as exc:
            self.modules["hero_guide"].status = "error"
            self.modules["knowledge_graph"].status = "error"
            results["errors"].append(f"hero_guide: {exc}")

        if do_sync:
            try:
                ms = self._sync_medienserver(force=force)
                self.modules["medienserver"].status = "loaded" if ms.get("status") == "success" else "standby"
                results["modules"]["medienserver"] = ms
            except Exception as exc:
                self.modules["medienserver"].status = "error"
                results["errors"].append(f"medienserver: {exc}")
        else:
            self.modules["medienserver"].status = "standby"
            results["modules"]["medienserver"] = {"status": "skipped", "reason": "deferred_boot_optimizer"}

        try:
            from grok_bridge import get_grok_bridge
            bridge = get_grok_bridge()
            self.modules["grok"].status = "loaded" if bridge.skill_loaded else "standby"
            results["modules"]["grok"] = {
                "agent": bridge.status().get("agent"),
                "skill_loaded": bridge.skill_loaded,
                "endpoints": bridge.status().get("endpoints"),
            }
        except Exception as exc:
            self.modules["grok"].status = "error"
            self.modules["grok"].error = str(exc)
            results["errors"].append(f"grok: {exc}")

        try:
            from gui.fusion_gui import get_gui_status
            self.modules["workspace_gui"].status = "loaded"
            results["modules"]["workspace_gui"] = get_gui_status()
        except Exception as exc:
            self.modules["workspace_gui"].status = "standby"
            self.modules["workspace_gui"].error = str(exc)
            results["errors"].append(f"workspace_gui: {exc}")

        try:
            from meta_layer_windows import get_meta_layer_status, set_internal_backend_context
            set_internal_backend_context(True)
            ml = get_meta_layer_status(light=True, mainframe_loaded=bool(self.mainframe))
            set_internal_backend_context(False)
            self.modules["meta_layer"].status = "loaded" if ml.attached else "standby"
            results["modules"]["meta_layer"] = {
                "attached": ml.attached,
                "substrate": ml.substrate.to_dict() if ml.substrate else {},
                "stack": ml.stack,
                "architecture": "Meta-Layer über Windows",
            }
        except Exception as exc:
            self.modules["meta_layer"].status = "error"
            self.modules["meta_layer"].error = str(exc)
            results["errors"].append(f"meta_layer: {exc}")

        try:
            from autoloader import autoload_status
            als = autoload_status()
            self.modules["autoloader"].status = "loaded"
            results["modules"]["autoloader"] = {
                "drivers": len(als.get("drivers", [])),
                "state_summary": (als.get("state") or {}).get("summary", {}),
            }
        except Exception as exc:
            self.modules["autoloader"].status = "standby"
            self.modules["autoloader"].error = str(exc)

        for aid, agent in self.agents.items():
            agent.loaded = True
            results["agents"][aid] = agent.to_dict()

        results["summary"] = {
            "loaded": sum(1 for m in self.modules.values() if m.status == "loaded"),
            "total_modules": len(self.modules),
            "total_agents": len(self.agents),
            "all_ok": len(results["errors"]) == 0,
            "hyperthreading": ht_status(),
            "boot_phase": phase,
        }
        self._last_load_result = results
        return results

    def set_hyperthreading(self, enabled: bool) -> dict:
        self.hyperthreading_enabled = enabled
        os.environ["FUSION_HYPERTHREADING"] = "1" if enabled else "0"
        if self.orchestrator:
            self.orchestrator.enable_hyperthreading(enabled)
        return ht_status()

    def list_modules(self) -> List[dict]:
        return [m.to_dict() for m in self.modules.values()]

    def list_agents(self, enrich_resources: bool = True) -> List[dict]:
        agents = [a.to_dict() for a in self.agents.values()]
        if not enrich_resources:
            return agents
        if self._resource_plan is not None:
            slot_map = {s.agent_id: s.to_dict() for s in self._resource_plan.agent_slots}
            for ag in agents:
                ag["resource_slot"] = slot_map.get(ag["id"])
            return agents
        plan = get_resource_plan(agents)
        slot_map = {s.agent_id: s.to_dict() for s in plan.agent_slots}
        for ag in agents:
            ag["resource_slot"] = slot_map.get(ag["id"])
        return agents

    def resource_plan(self, metrics: Optional[dict] = None, force: bool = False) -> dict:
        agents = [a.to_dict() for a in self.agents.values()]
        return get_resource_plan(agents, metrics=metrics, force=force).to_dict()

    def use_agent(self, agent_id: str, query: str) -> dict:
        agent = self.agents.get(agent_id)
        if not agent:
            return {"status": "error", "error": f"Agent '{agent_id}' nicht gefunden"}
        if self.orchestrator is None:
            return {"status": "error", "error": "Orchestrator nicht geladen — zuerst /api/load-all"}
        agent_list = [a.to_dict() for a in self.agents.values()]
        pool = pick_agent_pool(agent_id, agent_list)
        plan = get_resource_plan(agent_list)
        result = self.orchestrator.orchestrate(
            query=query,
            model_pool=pool,
            context={
                "agent": agent.to_dict(),
                "routing": "agent_dispatch",
                "orchestrator_workers": plan.orchestrator_workers,
                "resource_plan": plan.to_dict(),
            },
        )
        result["agent"] = agent.to_dict()
        result["synthesised_response"] = (
            f"[{agent.name}] {agent.description}\n\n"
            f"Query: {query}\n\n"
            f"Routed via DynamicOrchestration → {result.get('used_models', pool)}"
        )
        return result

    def layer4_status(self) -> dict:
        if not self.highest_layer:
            return {"loaded": False}
        milestones = list(self.highest_layer.roadmap.milestones.values())
        return {
            "loaded": True,
            "milestones": [m.to_dict() for m in milestones],
            "generation": self.highest_layer.protocol.current_generation,
            "status": self.highest_layer.status(),
        }

    def mainframe_pipeline_status(self) -> dict:
        if not self.mainframe:
            return {"loaded": False}
        mf = self.mainframe
        return {
            "loaded": True,
            "version": "v5.25",
            "generation": mf.evolution.generation,
            "audit_hooks": list(mf.self_modify.audit_hooks.keys()),
            "cascade": {
                "layer_1": "pre_solve_audit",
                "layer_2": "high_performance_execution",
                "layer_3": "post_solve_validation",
            },
            "modules": {
                "SelfModifyCoreModule": bool(mf.self_modify),
                "GenerationalEvolutionProtocolCoreModule": bool(mf.evolution),
                "CriticalMetaAnalysisCoreModule": bool(mf.meta_analyzer),
                "ClassicalBackend": bool(mf.backend),
                "ExecutableAuditAgent": bool(mf.audit_agent),
            },
            "solvers": list(mf.backend.solvers.keys()) if mf.backend else [],
            "engine": "qb_qubo.classical",
        }


_registry: Optional[FusionRegistry] = None


def get_registry() -> FusionRegistry:
    global _registry
    if _registry is None:
        _registry = FusionRegistry()
    return _registry