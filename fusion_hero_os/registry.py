"""Zentrale Modul-Registry für Fusion Hero OS (v8.4 erweitert).

Der Universal LLM Router ist jetzt als offizielles Core-Modul registriert.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger("fusion_hero_os.registry")


class ModuleStatus(str, Enum):
    NOT_LOADED = "not_loaded"
    LOADED = "loaded"
    STUB = "stub"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class ModuleUnavailableError(RuntimeError):
    """Wird von ``Registry.get()`` geworfen, wenn ein Teilsystem angefragt wird,
    das nicht geladen werden konnte.
    """


@dataclass
class ModuleSpec:
    name: str
    import_path: str
    description: str
    required: bool = False
    stub: bool = False

    status: ModuleStatus = field(default=ModuleStatus.NOT_LOADED, init=False)
    module: Any = field(default=None, init=False, repr=False)
    error: str | None = field(default=None, init=False)


DEFAULT_MODULES: list[ModuleSpec] = [
    ModuleSpec(
        "engine.mainframe", "fusion_hero_os.engine.mainframe",
        "QUBO-Solver (Parallel Simulated Annealing) + Audit-Layer",
        required=True,
    ),
    ModuleSpec(
        "orchestration.agents", "fusion_hero_os.orchestration.agents",
        "Multi-Agenten-System (MessageBus, TaskQueue, Supervisor)",
        required=True,
    ),
    ModuleSpec(
        "core.orchestrator", "fusion_hero_os.core.heroic_core_orchestrator",
        "Layer 0/4/5 Orchestrator (MasterSeed, PMS, QuadCoreBridge + LLM Router)",
        required=True,
    ),
    # NEU in v8.4: explizite Registrierung des Universal LLM Routers
    ModuleSpec(
        "core.llm_router",
        "fusion_hero_os.core.universal_llm_router",
        "Universal LLM Router v8.4 (Claude + Grok + EveryAPI + Internal Fallback mit Heroic Context + Provider-Abstraktion)",
    ),
    # NEU in v8.3-Konsolidierung: Layer-Registry (alle Layer aus fusion_unified.yaml)
    ModuleSpec(
        "core.layer_registry",
        "fusion_hero_os.core.layer_registry",
        "Layer-Registry v8.3 (Status aller Layer inkl. kernel/ascension/tarnkappe/android/knowledge)",
    ),
    ModuleSpec(
        "core.math", "fusion_hero_os.core.heroic_math_engine",
        "Mathematischer Kern (Matrizen, Stabilität, Fusionsoperationen)",
    ),
    ModuleSpec(
        "core.dispatcher", "fusion_hero_os.core.dispatcher",
        "Zentraler Dispatcher für BaseModule-Instanzen",
    ),
    ModuleSpec(
        "core.cec", "fusion_hero_os.core.cec", "CoEvolutionaryClosure"),
    ModuleSpec(
        "core.pure_core_coevolution",
        "fusion_hero_os.core.pure_core_coevolution",
        "Pure-Core Langzeit-Coevolution (formale Math + Algorithmen = Core; Rest = fremde Stärken)",
    ),
    ModuleSpec(
        "core.rhe", "fusion_hero_os.core.rhe", "RustHybridEmbodiment"),
    ModuleSpec(
        "core.psycholysis_trigger", "fusion_hero_os.core.psycholysis_trigger", "PsycholysisTrigger"),
    ModuleSpec(
        "core.dashboard.orchestration", "fusion_hero_os.core.dashboard.orchestration", "Dashboard Orchestration"),
    ModuleSpec(
        "core.dashboard.workspace", "fusion_hero_os.core.dashboard.workspace", "Dashboard Workspace"),
    ModuleSpec(
        "methodology.connectors", "fusion_hero_os.methodology.connectors", "Externe Service-Connectoren"),
    ModuleSpec(
        "methodology.core_modules", "fusion_hero_os.methodology.core_modules", "Service-Wrapper Kernmodule"),
    ModuleSpec(
        "methodology.knowledge", "fusion_hero_os.methodology.knowledge", "Wissensbasis-Zugriff"),
    ModuleSpec(
        "modules.builder_profile",
        "fusion_hero_os.modules.builder_profile",
        "Heroic Core Foundation gate (wired P1)",
    ),
    ModuleSpec(
        "modules.mainframe_laden",
        "fusion_hero_os.modules.mainframe_laden",
        "Permanent Auto-Load / registry load_all (wired P1)",
    ),
    ModuleSpec(
        "modules.skill_creator",
        "fusion_hero_os.modules.skill_creator",
        "Dynamische Skill-Evolution proposals (wired P1)",
    ),
    ModuleSpec(
        "modules.core_modules", "fusion_hero_os.modules", "BaseModule-Adapter"),
    ModuleSpec(
        "core.poly_mesh_router",
        "fusion_hero_os.core.poly_mesh_router",
        "Poly-Mesh sole router (L0–L3 placement)",
    ),
    ModuleSpec(
        "core.poly_mesh_orchestrator",
        "fusion_hero_os.core.poly_mesh_orchestrator",
        "Poly-Mesh orchestration waves",
    ),
    ModuleSpec(
        "core.inference_scheduler_qubo",
        "fusion_hero_os.core.inference_scheduler_qubo",
        "QUBO inference scheduler (MCP tools)",
    ),
    ModuleSpec(
        "core.mugen_tsuky_chan",
        "fusion_hero_os.core.mugen_tsuky_chan",
        "mugen-tsuky.chan protocol facade (clear propagation; obfuscated body)",
    ),
    ModuleSpec(
        "core.schwerkraftserver",
        "fusion_hero_os.core.schwerkraftserver",
        "Schwerkraftserver dual multi-model control + git history poly-mesh ingest",
    ),
    ModuleSpec(
        "core.comaedchen_identity",
        "fusion_hero_os.core.comaedchen_identity",
        "Comädchen × alte-frau95g identity (pr0-chan, free TTS/Voidol-class corpus)",
    ),
    ModuleSpec(
        "engine.mining_qubo", "fusion_hero_os.engine.mining_qubo", "Profit-Switching-QUBO"),
    ModuleSpec(
        "engine.rust_backend", "fusion_hero_os.engine.rust_backend", "PyO3-Rust-Backend"),
    ModuleSpec(
        "core.meister_hasch_optimize",
        "fusion_hero_os.core.meister_hasch_optimize",
        "Meister Hasch Fable5+Mythos5 bifocal optimize (Hypertarnkappe cloak + Hyperpanzerknacker lab probe)",
    ),
    ModuleSpec(
        "core.nibelungen_mythos",
        "fusion_hero_os.core.nibelungen_mythos",
        "Siegfried-Moment + Nibelungen-Saga + Grimm KHM Vollkatalog (Mythos organ, public-safe)",
    ),
    ModuleSpec(
        "core.poly_fa_write_gate",
        "fusion_hero_os.core.poly_fa_write_gate",
        "Poly-FA write gate: desktop-only structure writes, on-request, multi-factor (person hears/speaks full)",
    ),
    ModuleSpec(
        "core.dauer_eupression",
        "fusion_hero_os.core.dauer_eupression",
        "Dauer-Eupression: continuous good-pressure along dauer_eupression_deps.yaml (Eupression∥Eudaimon)",
    ),
    ModuleSpec(
        "core.autoload_controller",
        "fusion_hero_os.core.autoload_controller",
        "Autoload Controller status (post-reboot prepare/load orchestration)",
    ),
]


class Registry:
    """Lädt und verwaltet die Teilsysteme von Fusion Hero OS."""

    def __init__(self, specs: list[ModuleSpec] | None = None):
        self._specs: dict[str, ModuleSpec] = {s.name: s for s in (specs or DEFAULT_MODULES)}

    def load(self, name: str) -> ModuleSpec:
        spec = self._specs[name]

        if spec.status is not ModuleStatus.NOT_LOADED:
            return spec

        if spec.stub:
            spec.status = ModuleStatus.STUB
            return spec

        try:
            spec.module = importlib.import_module(spec.import_path)
            spec.status = ModuleStatus.LOADED
        except ImportError as exc:
            spec.status = ModuleStatus.UNAVAILABLE
            spec.error = str(exc)
            logger.warning("Modul %r (%s) nicht verfügbar: %s", name, spec.import_path, exc)
            if spec.required:
                raise
        except Exception as exc:  # noqa: BLE001
            spec.status = ModuleStatus.FAILED
            spec.error = str(exc)
            logger.error("Modul %r (%s) ist beim Import fehlgeschlagen: %s", name, spec.import_path, exc, exc_info=True)
            if spec.required:
                raise

        return spec

    def load_all(self) -> dict[str, ModuleSpec]:
        for name in self._specs:
            self.load(name)
        return dict(self._specs)

    def get(self, name: str) -> Any:
        if name not in self._specs:
            raise KeyError(f"Unbekanntes Modul: {name!r}")
        spec = self.load(name)
        if spec.status is not ModuleStatus.LOADED:
            raise ModuleUnavailableError(
                f"{name!r} ({spec.import_path}) ist nicht verfügbar (status={spec.status.value}, error={spec.error})"
            )
        return spec.module

    def try_get(self, name: str) -> Any | None:
        try:
            return self.get(name)
        except ModuleUnavailableError:
            return None

    def status_report(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "import_path": s.import_path,
                "status": s.status.value,
                "required": s.required,
                "description": s.description,
                "error": s.error,
            }
            for s in self._specs.values()
        ]


_default_registry: Registry | None = None


def get_registry() -> Registry:
    global _default_registry
    if _default_registry is None:
        _default_registry = Registry()
    return _default_registry


def load_all() -> dict[str, ModuleSpec]:
    return get_registry().load_all()


def get(name: str) -> Any:
    return get_registry().get(name)


def status_report() -> list[dict[str, Any]]:
    return get_registry().status_report()


def _print_status_report() -> None:
    registry = get_registry()
    registry.load_all()
    rows = registry.status_report()
    name_w = max(len(r["name"]) for r in rows)
    status_w = max(len(r["status"]) for r in rows)
    print(f"{'MODULE':<{name_w}}  {'STATUS':<{status_w}}  REQUIRED  DESCRIPTION")
    for r in rows:
        req = "yes" if r["required"] else "no"
        print(f"{r['name']:<{name_w}}  {r['status']:<{status_w}}  {req:<8}  {r['description']}")
        if r["error"]:
            print(f"{'':<{name_w}}  -> {r['error']}")


if __name__ == "__main__":
    _print_status_report()
