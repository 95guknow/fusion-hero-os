# Fusion-Hero-OS Core - v8

"""
ALTE_Frau_95g Heroic Core

Enthält die zentralen Core-Module:
- CoEvolutionaryClosure (CEC)
- RustHybridEmbodiment (RHE)
- PsycholysisTrigger
- HeroicMathEngine (mathematische Kernkomponenten)
- HeroicCoreOrchestrator (Layer 0/4/5 Integration + Fail-Closed Bridge)

Teil der 02_architecture Schicht.

Alle Submodule werden über :mod:`fusion_hero_os.registry` geladen statt über
verstreute, dreifach kopierte try/except-Importe. Ist ein Submodul nicht
verfügbar, bleibt das zugehörige Attribut hier ``None`` (Rückwärtskompatibilität
für bestehenden Code); der tatsächliche Grund (fehlendes Dependency vs. echter
Fehler im Modul) steht in ``fusion_hero_os.registry.get_registry().status_report()``.
"""

from fusion_hero_os.registry import get_registry

__version__ = "v8"

__all__ = [
    "__version__",
    "global_cec",
    "global_rhe",
    "PsycholysisTrigger",
    "HeroicMatrixEngine",
    "StableCoreLattice",
    "RepairedStructureIP",
    "global_heroic_math",
    "MasterSeed",
    "PMSEvidenceSpine",
    "QuadCoreBridge",
    "bootstrap_v8_system",
]

_registry = get_registry()

_cec = _registry.try_get("core.cec")
global_cec = getattr(_cec, "global_cec", None)

_rhe = _registry.try_get("core.rhe")
global_rhe = getattr(_rhe, "global_rhe", None)

_psycholysis = _registry.try_get("core.psycholysis_trigger")
PsycholysisTrigger = getattr(_psycholysis, "PsycholysisTrigger", None)

_math = _registry.try_get("core.math")
HeroicMatrixEngine = getattr(_math, "HeroicMatrixEngine", None)
StableCoreLattice = getattr(_math, "StableCoreLattice", None)
RepairedStructureIP = getattr(_math, "RepairedStructureIP", None)
global_heroic_math = getattr(_math, "global_heroic_math", None)

_orchestrator = _registry.try_get("core.orchestrator")
MasterSeed = getattr(_orchestrator, "MasterSeed", None)
PMSEvidenceSpine = getattr(_orchestrator, "PMSEvidenceSpine", None)
QuadCoreBridge = getattr(_orchestrator, "QuadCoreBridge", None)
bootstrap_v8_system = getattr(_orchestrator, "bootstrap_v8_system", None)
