"""Core-Module, die den :class:`~fusion_hero_os.core.base_module.BaseModule`
-Vertrag implementieren und über den Dispatcher ansprechbar sind.

``builder_profile/``, ``mainframe_laden/``, ``skill_creator/`` sind
eigenständige, noch unimplementierte Platzhalter-Pakete (siehe README.md in
diesem Ordner) und bewusst NICHT Teil von :data:`ALL_CORE_MODULES` — sie
haben keinen Code, der den BaseModule-Vertrag erfüllen könnte.
"""

from __future__ import annotations

from typing import List, Type

from fusion_hero_os.core.base_module import BaseModule
from fusion_hero_os.modules.automatic_archiving import AutomaticArchivingCoreModule
from fusion_hero_os.modules.code_review import PeerReviewCoreModule
from fusion_hero_os.modules.conversation_context import ConversationContextCoreModule
from fusion_hero_os.modules.formal_mathematics import FormalMathematicsCoreModule
from fusion_hero_os.modules.generational_evolution import (
    GenerationalEvolutionProtocolCoreModule,
)
from fusion_hero_os.modules.live_process_tracking import LiveProcessTrackingCoreModule
from fusion_hero_os.modules.mer import MERModule
from fusion_hero_os.modules.qubo_integration import QUBOIntegrationCoreModule
from fusion_hero_os.modules.self_modify import SelfModifyCoreModule
from fusion_hero_os.modules.weltraudaimonia import WeltraudaimoniaModule
from fusion_hero_os.modules.heroic_llm_ea import HeroicLLMEAOrchestrator
from fusion_hero_os.modules.image_orchestrator import HeroicImageOrchestrator
from fusion_hero_os.modules.timespace_token import TimespaceTokenCoreModule
from fusion_hero_os.modules.phone_link import PhoneLinkCoreModule
from fusion_hero_os.modules.hero_autoupdate import HeroAutoupdateCoreModule

#: Alle Core-Module, die :func:`fusion_hero_os.core.dispatcher.build_default_dispatcher`
#: standardmäßig registriert.
ALL_CORE_MODULES: list[type[BaseModule]] = [
    SelfModifyCoreModule,
    PeerReviewCoreModule,
    FormalMathematicsCoreModule,
    AutomaticArchivingCoreModule,
    WeltraudaimoniaModule,
    MERModule,
    ConversationContextCoreModule,
    LiveProcessTrackingCoreModule,
    GenerationalEvolutionProtocolCoreModule,
    QUBOIntegrationCoreModule,
    HeroicLLMEAOrchestrator,
    HeroicImageOrchestrator,
    TimespaceTokenCoreModule,
    PhoneLinkCoreModule,
    HeroAutoupdateCoreModule,
]

__all__ = [
    "ALL_CORE_MODULES",
    "AutomaticArchivingCoreModule",
    "ConversationContextCoreModule",
    "FormalMathematicsCoreModule",
    "GenerationalEvolutionProtocolCoreModule",
    "LiveProcessTrackingCoreModule",
    "MERModule",
    "PeerReviewCoreModule",
    "QUBOIntegrationCoreModule",
    "SelfModifyCoreModule",
    "WeltraudaimoniaModule",
    "HeroicLLMEAOrchestrator",
    "HeroicImageOrchestrator",
    "TimespaceTokenCoreModule",
    "PhoneLinkCoreModule",
    "HeroAutoupdateCoreModule",
]
