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
"""

__version__ = "v8"

from .cec import global_cec as global_cec

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
try:
    from .rhe import global_rhe
except ImportError:
    global_rhe = None
try:
    from .psycholysis_trigger import PsycholysisTrigger
except ImportError:
    PsycholysisTrigger = None

# Neue mathematische Kernkomponente (v8)
try:
    from .heroic_math_engine import (
        HeroicMatrixEngine,
        StableCoreLattice,
        RepairedStructureIP,
        global_heroic_math
    )
except ImportError:
    HeroicMatrixEngine = None
    StableCoreLattice = None
    RepairedStructureIP = None
    global_heroic_math = None

# Heroic Core Orchestrator (Layer 0 + Layer 4/5 Bridge)
try:
    from .heroic_core_orchestrator import (
        MasterSeed,
        PMSEvidenceSpine,
        QuadCoreBridge,
        bootstrap_v8_system
    )
except ImportError:
    MasterSeed = None
    PMSEvidenceSpine = None
    QuadCoreBridge = None
    bootstrap_v8_system = None