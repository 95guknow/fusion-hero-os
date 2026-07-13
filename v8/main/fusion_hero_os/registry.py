"""Zentrale Modul-Registry für Fusion Hero OS.

Ersetzt das bisherige Muster verstreuter

    try:
        from .heroic_math_engine import HeroicMatrixEngine
    except ImportError:
        HeroicMatrixEngine = None

Blöcke (drei Kopien davon lagen in core/__init__.py) durch eine einzige
deklarative Tabelle plus einen Loader. Der wichtigste Unterschied zum alten
Muster: ein echter Bug im Modul (z. B. ein SyntaxError oder eine fehlerhafte
Modul-Ebene-Berechnung) wird NICHT mehr mit einem fehlenden optionalen
Dependency verwechselt. Beide Fälle kollabierten vorher gleichermaßen zu
``None`` — das macht Fehler bei der Fehlersuche unsichtbar. Hier werden sie
als unterschiedliche Status geführt und geloggt.

Nutzung:

    from fusion_hero_os.registry import get_registry

    registry = get_registry()
    registry.load_all()
    mainframe = registry.get("engine.mainframe")   # wirft ModuleUnavailableError statt None

Für einen schnellen Statusüberblick:

    python -m fusion_hero_os.registry
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("fusion_hero_os.registry")


class ModuleStatus(str, Enum):
    NOT_LOADED = "not_loaded"
    LOADED = "loaded"
    STUB = "stub"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


class ModuleUnavailableError(RuntimeError):
    """Wird von ``Registry.get()`` geworfen, wenn ein Teilsystem angefragt wird,
    das nicht geladen werden konnte. Ersetzt das stille Durchreichen von ``None``,
    das später zu schwer nachvollziehbaren ``AttributeError``s an ganz anderer
    Stelle im Code führt.
    """


@dataclass
class ModuleSpec:
    name: str
    import_path: str
    description: str
    required: bool = False
    stub: bool = False  # Paket existiert nur als Platzhalter (kein echter Code)

    status: ModuleStatus = field(default=ModuleStatus.NOT_LOADED, init=False)
    module: Any = field(default=None, init=False, repr=False)
    error: Optional[str] = field(default=None, init=False)


DEFAULT_MODULES: List[ModuleSpec] = [
    ModuleSpec(
        "engine.mainframe", "fusion_hero_os.engine.mainframe",
        "QUBO-Solver (Parallel Simulated Annealing) + Audit-Layer — von app.py direkt genutzt",
        required=True,
    ),
    ModuleSpec(
        "orchestration.agents", "fusion_hero_os.orchestration.agents",
        "Multi-Agenten-System (MessageBus, TaskQueue, Supervisor) — von app.py direkt genutzt",
        required=True,
    ),
    ModuleSpec(
        "engine.mining_qubo", "fusion_hero_os.engine.mining_qubo",
        "Profit-Switching-QUBO für Ressourcenoptimierung",
    ),
    ModuleSpec(
        "engine.rust_backend", "fusion_hero_os.engine.rust_backend",
        "PyO3-Rust-Backend (experimentell, benötigt gebauten rust_engine_crate)",
    ),
    ModuleSpec(
        "core.cec", "fusion_hero_os.core.cec",
        "CoEvolutionaryClosure",
    ),
    ModuleSpec(
        "core.rhe", "fusion_hero_os.core.rhe",
        "RustHybridEmbodiment",
    ),
    ModuleSpec(
        "core.psycholysis_trigger", "fusion_hero_os.core.psycholysis_trigger",
        "PsycholysisTrigger",
    ),
    ModuleSpec(
        "core.math", "fusion_hero_os.core.heroic_math_engine",
        "Mathematischer Kern (Matrizen, Stabilität, Fusionsoperationen)",
    ),
    ModuleSpec(
        "core.orchestrator", "fusion_hero_os.core.heroic_core_orchestrator",
        "Layer 0/4/5 Orchestrator (MasterSeed, PMS Evidence Spine, QuadCoreBridge)",
    ),
    ModuleSpec(
        "core.dashboard.orchestration", "fusion_hero_os.core.dashboard.orchestration",
        "Dashboard-Agentenkoordination (DashboardOrchestrator) — bislang von nichts referenziert",
    ),
    ModuleSpec(
        "core.dashboard.workspace", "fusion_hero_os.core.dashboard.workspace",
        "Dashboard Workspace/State-Handling — bislang von nichts referenziert",
    ),
    ModuleSpec(
        "methodology.connectors", "fusion_hero_os.methodology.connectors",
        "Externe Service-Connectoren (GitHub, Drive, Vercel, ... — Dry-Run per Default)",
    ),
    ModuleSpec(
        "methodology.core_modules", "fusion_hero_os.methodology.core_modules",
        "Service-Wrapper Kernmodule",
    ),
    ModuleSpec(
        "methodology.knowledge", "fusion_hero_os.methodology.knowledge",
        "Wissensbasis-Zugriff",
    ),
    ModuleSpec(
        "modules.alte_frau_95g", "fusion_hero_os.modules.alte_frau_95g",
        "Heroic Core Foundation (noch kein eigener Code, nur Platzhalter)",
        stub=True,
    ),
    ModuleSpec(
        "modules.mainframe_laden", "fusion_hero_os.modules.mainframe_laden",
        "Permanent Auto-Load (noch kein eigener Code, nur Platzhalter)",
        stub=True,
    ),
    ModuleSpec(
        "modules.skill_creator", "fusion_hero_os.modules.skill_creator",
        "Dynamische Skill-Evolution (noch kein eigener Code, nur Platzhalter)",
        stub=True,
    ),
    ModuleSpec(
        "core.dispatcher", "fusion_hero_os.core.dispatcher",
        "Zentraler Dispatcher: registriert BaseModule-Instanzen, routet dispatch()/dispatch_many()",
    ),
    ModuleSpec(
        "modules.core_modules", "fusion_hero_os.modules",
        "BaseModule-Adapter (SelfModify, PeerReview, FormalMathematics, AutomaticArchiving, "
        "Weltraudaimonia, MER, ConversationContext, LiveProcessTracking, GenerationalEvolution, "
        "QUBOIntegration) — siehe fusion_hero_os.core.dispatcher.build_default_dispatcher()",
    ),
]


class Registry:
    """Lädt und verwaltet die Teilsysteme von Fusion Hero OS."""

    def __init__(self, specs: Optional[List[ModuleSpec]] = None):
        self._specs: Dict[str, ModuleSpec] = {s.name: s for s in (specs or DEFAULT_MODULES)}

    def load(self, name: str) -> ModuleSpec:
        spec = self._specs[name]

        if spec.status is not ModuleStatus.NOT_LOADED:
            return spec  # bereits (er-)geladen bzw. Ergebnis vorliegend

        if spec.stub:
            spec.status = ModuleStatus.STUB
            return spec

        try:
            spec.module = importlib.import_module(spec.import_path)
            spec.status = ModuleStatus.LOADED
        except ImportError as exc:
            # Fehlendes optionales Dependency oder (noch) nicht gebautes Modul
            # (z.B. engine.rust_backend ohne kompilierte Rust-Extension).
            spec.status = ModuleStatus.UNAVAILABLE
            spec.error = str(exc)
            logger.warning("Modul %r (%s) nicht verfügbar: %s", name, spec.import_path, exc)
            if spec.required:
                raise
        except Exception as exc:  # noqa: BLE001 — bewusst breit, s. Docstring oben
            # Ein echter Bug im Modul selbst, keine fehlende Abhängigkeit.
            # Wird lautstark geloggt statt still zu None zu kollabieren.
            spec.status = ModuleStatus.FAILED
            spec.error = str(exc)
            logger.error(
                "Modul %r (%s) ist beim Import fehlgeschlagen: %s",
                name, spec.import_path, exc, exc_info=True,
            )
            if spec.required:
                raise

        return spec

    def load_all(self) -> Dict[str, ModuleSpec]:
        for name in self._specs:
            self.load(name)
        return dict(self._specs)

    def get(self, name: str) -> Any:
        """Gibt das geladene Modul zurück oder wirft ``ModuleUnavailableError``.

        Absichtlich kein stilles ``None`` — Aufrufer sollen entweder ein
        funktionierendes Modul bekommen oder sofort einen aussagekräftigen
        Fehler, statt später an einer ``AttributeError`` auf ``None`` zu
        scheitern.
        """
        if name not in self._specs:
            raise KeyError(f"Unbekanntes Modul: {name!r}")
        spec = self.load(name)
        if spec.status is not ModuleStatus.LOADED:
            raise ModuleUnavailableError(
                f"{name!r} ({spec.import_path}) ist nicht verfügbar "
                f"(status={spec.status.value}, error={spec.error})"
            )
        return spec.module

    def try_get(self, name: str) -> Optional[Any]:
        """Wie ``get()``, gibt aber ``None`` statt zu werfen — für Aufrufstellen,
        die einen optionalen Bestandteil bewusst überspringen wollen.
        """
        try:
            return self.get(name)
        except ModuleUnavailableError:
            return None

    def status_report(self) -> List[Dict[str, Any]]:
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


_default_registry: Optional[Registry] = None


def get_registry() -> Registry:
    """Gibt die geteilte Standard-Registry-Instanz zurück (Singleton je Prozess)."""
    global _default_registry
    if _default_registry is None:
        _default_registry = Registry()
    return _default_registry


def load_all() -> Dict[str, ModuleSpec]:
    return get_registry().load_all()


def get(name: str) -> Any:
    return get_registry().get(name)


def status_report() -> List[Dict[str, Any]]:
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
