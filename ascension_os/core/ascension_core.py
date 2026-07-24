# -*- coding: utf-8 -*-
"""
AscensionOS v9.6 - Substantielles AscensionCore (Coevolutionaer integriert)

Dieses AscensionCore ist die zentrale Heimat fuer:
- Alle grounded epistemischen Komponenten (Sisyphos, FailClosed, Psycholysis, MasterSeed)
- Den GenerationalEvolutionEngine (Inside-Out Evolution)
- Den UnifiedHeroicLLMCore
- Die CoEvolutionaryClosure (CEC, v9.3)
- Den PersistentSisyphosCycle (v9.4)
- Den Stage9AscensionTracker, PsycholyseProtocolLogger, SisyphosOscillationVisualizer
  und QUBOAscensionOptimizer (v9.5 - "Next Evolution Steps" aus
  ASCENSION_EXPANSION_v8.md / 00_AscensionOS_Zusammenfuehrung_v8.md, vormals
  nur als Text/Referenz ohne Code)
- Das HarmonisierungsCoreModule und Geisterjagdmodul (v9.6 - Self-Mod-Vorschlag
  aus Core_Update_ALTE_Frau_95g_V4_Integration_2026-06-22.md, Kompendium der
  Heroik Teil III: Harmonisierungs-Operation H, Alignment-Satz/Banach-Fixpunkt)

Wiederhergestellt in der v8.3-Konsolidierung: Die Datei war durch
Delta-Fragmente (5cd32ab, 781269f) ersetzt worden; Basis ist der letzte
vollstaendige v9.2-Stand (8f747dc) plus die CEC- und
PersistentSisyphos-Erweiterungen, jetzt korrekt ausformuliert.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from ..consent_gate import AscensionConsentGate
    from fusion_hero_os.meta.consent import ConsentError
except Exception:  # pragma: no cover - meta slice / gate unavailable
    AscensionConsentGate = None

    class ConsentError(RuntimeError):
        pass

try:
    from fusion_hero_os.core.universal_llm_router import (
        get_unified_llm_core,
        UnifiedHeroicLLMCore,
        SisyphosCycle,
        FailClosed,
    )
    from fusion_hero_os.core.psycholysis_trigger import PsycholysisTrigger
    from fusion_hero_os.core.heroic_core import MasterSeed
except Exception:
    UnifiedHeroicLLMCore = None
    PsycholysisTrigger = None
    SisyphosCycle = None
    FailClosed = None
    MasterSeed = None
    get_unified_llm_core = None

try:
    from ..evolution.generational_engine import GenerationalEvolutionEngine
except Exception:
    GenerationalEvolutionEngine = None

try:
    from .coevolutionary_closure import get_coevolutionary_closure, CoEvolutionaryClosure
except Exception:
    CoEvolutionaryClosure = None
    get_coevolutionary_closure = None

try:
    from .persistent_sisyphos import PersistentSisyphosCycle
except Exception:
    PersistentSisyphosCycle = None

try:
    from .stage9_tracker import Stage9AscensionTracker
except Exception:
    Stage9AscensionTracker = None

try:
    from .psycholyse_protocol_logger import PsycholyseProtocolLogger
except Exception:
    PsycholyseProtocolLogger = None

try:
    from .sisyphos_oscillation_visualizer import SisyphosOscillationVisualizer
except Exception:
    SisyphosOscillationVisualizer = None

try:
    from .qubo_ascension_optimizer import QUBOAscensionOptimizer
except Exception:
    QUBOAscensionOptimizer = None

try:
    from .harmonisierung_module import HarmonisierungsCoreModule
except Exception:
    HarmonisierungsCoreModule = None

try:
    from .geisterjagd_module import Geisterjagdmodul
except Exception:
    Geisterjagdmodul = None

try:
    from .exposure_practice_module import ExposurePracticeModule
except Exception:
    ExposurePracticeModule = None


class AscensionCore:
    """
    Das substantielle AscensionCore v9.7.

    Coevolutionaer aufgebaut:
    - Haelt alle zentralen grounded Komponenten
    - Integriert den GenerationalEvolutionEngine tief
    - Ist ueber die CoEvolutionaryClosure (CEC) mit anderen Tracks verbunden
    - Fuehrt den persistenten, stateful Sisyphos-Zyklus
    - Schaetzt die Naeherung an Stage9 (heuristisch, siehe stage9_tracker.py)
    - Loggt Psycholyse-Sessions mit Pflicht-Status-Tags
    - Visualisiert die Sisyphos-Oszillation (ASCII + SVG, keine neue Dependency)
    - Loest die Devil-vs-Christus-QUBO-Trajektorie ueber den bestehenden Solver
    - Harmonisiert zwei Zustaende ueber H={b.q}.{q.b} mit Narzissmus-Filter (v9.6)
    - Jagt "Geister" (latente Zustaende) zu einem manifesten Fixpunkt (v9.6)
    - Simulierter Uebungspartner fuer soziale Expositionsuebung, kein Dritter
      beteiligt (v9.7, siehe exposure_practice_module.py)
    """

    def __init__(self, consent_gate: "AscensionConsentGate" = None):
        self.version = "9.10-aspirational"

        # Consent gate (v10): personal-data operations fail closed unless an
        # AscensionConsentGate bound to a live meta ConsentStore is supplied.
        self._consent_gate = consent_gate

        # Grounded Core Components
        self.llm: Optional["UnifiedHeroicLLMCore"] = (
            get_unified_llm_core() if get_unified_llm_core else None
        )
        self.sisyphos: Optional["SisyphosCycle"] = (
            getattr(self.llm, "sisyphos", None) if self.llm else None
        )
        self.psycholysis: Optional["PsycholysisTrigger"] = (
            getattr(self.llm, "psycholysis", None) if self.llm else None
        )
        self.fail_closed = FailClosed
        self.masterseed: Optional["MasterSeed"] = None  # wird bei Bedarf injiziert

        # Generational Evolution Engine (tief integriert)
        self.evolution_engine: Optional["GenerationalEvolutionEngine"] = None
        if GenerationalEvolutionEngine:
            self.evolution_engine = GenerationalEvolutionEngine(ascension_core=self)

        # CoevolutionaryClosure Integration (v9.3)
        self.cec: Optional["CoEvolutionaryClosure"] = None
        if get_coevolutionary_closure:
            self.cec = get_coevolutionary_closure()

        # Persistent Sisyphos (v9.4)
        self.persistent_sisyphos: Optional["PersistentSisyphosCycle"] = None
        if PersistentSisyphosCycle:
            self.persistent_sisyphos = PersistentSisyphosCycle()

        # Stage9-Tracker, Psycholyse-Logger, Oszillations-Visualizer (v9.5)
        # - alle konsumieren persistent_sisyphos statt eigenen Zustand zu duplizieren.
        self.stage9_tracker: Optional["Stage9AscensionTracker"] = None
        if Stage9AscensionTracker:
            self.stage9_tracker = Stage9AscensionTracker(sisyphos=self.persistent_sisyphos)

        self.psycholyse_logger: Optional["PsycholyseProtocolLogger"] = None
        if PsycholyseProtocolLogger:
            self.psycholyse_logger = PsycholyseProtocolLogger(sisyphos=self.persistent_sisyphos)

        self.oscillation_visualizer: Optional["SisyphosOscillationVisualizer"] = None
        if SisyphosOscillationVisualizer:
            self.oscillation_visualizer = SisyphosOscillationVisualizer(sisyphos=self.persistent_sisyphos)

        # Harmonisierung + Geisterjagd (v9.6) - eigenstaendig, arbeiten auf
        # uebergebenen Zustandsvektoren statt auf persistent_sisyphos.
        self.harmonisierung: Optional["HarmonisierungsCoreModule"] = None
        if HarmonisierungsCoreModule:
            try:
                self.harmonisierung = HarmonisierungsCoreModule()
            except ImportError:
                self.harmonisierung = None  # BanachContractionSeed nicht importierbar

        self.geisterjagd: Optional["Geisterjagdmodul"] = Geisterjagdmodul() if Geisterjagdmodul else None

        # Expositions-Uebungspartner (v9.7) - nutzt self.llm fuer Antworten
        self.exposure_practice: Optional["ExposurePracticeModule"] = None
        if ExposurePracticeModule:
            self.exposure_practice = ExposurePracticeModule(llm=self.llm)

        self.mode = "ASCENSION"

    # ------------------------------------------------------------------
    # Consent (v10) — fail closed
    # ------------------------------------------------------------------

    def _require_consent(self, purpose: Any, *, action: str) -> None:
        """Gate a personal-data operation; raise ConsentError if not granted.

        Fails closed: without a configured :class:`AscensionConsentGate` no
        personal-data operation is authorised.
        """
        if self._consent_gate is None:
            raise ConsentError(
                f"personal-data operation {action!r} denied: no consent gate "
                f"configured (fail closed). Construct AscensionCore(consent_gate=...) "
                f"with a live meta ConsentStore grant."
            )
        self._consent_gate.require(purpose, action=action)

    # ------------------------------------------------------------------
    # Sisyphos
    # ------------------------------------------------------------------

    def get_sisyphos_state(self) -> Dict[str, Any]:
        if self.sisyphos:
            return self.sisyphos.get_state()
        return {}

    def step_sisyphos(self, load: float, notes: str = ""):
        """Persistenter Sisyphos-Schritt (v9.4) mit Historie."""
        self._require_consent("persistence", action="ascension.step_sisyphos")
        if self.persistent_sisyphos:
            return self.persistent_sisyphos.step(load, notes)
        return None

    def get_sisyphos_history(self, last_n: int = 10):
        if self.persistent_sisyphos:
            return self.persistent_sisyphos.get_history(last_n)
        return []

    # ------------------------------------------------------------------
    # Stage9 + Psycholyse + Oszillation + QUBO (v9.5)
    # ------------------------------------------------------------------

    def get_stage9_status(self) -> Dict[str, Any]:
        """Heuristische Naeherung an 'Stage 9 / Kosmozentrisch', siehe stage9_tracker.py."""
        if not self.stage9_tracker:
            return {"status": "Stage9AscensionTracker nicht verfuegbar"}
        return self.stage9_tracker.check_ascension()

    def log_psycholyse_session(self, protocol_type: str, status: str, **kwargs: Any) -> Optional[Dict[str, Any]]:
        """Loggt eine Psycholyse-Session mit Pflicht-Status-Tag (siehe VALID_STATUS_TAGS)."""
        self._require_consent("persistence", action="ascension.log_psycholyse_session")
        if not self.psycholyse_logger:
            return None
        from dataclasses import asdict
        entry = self.psycholyse_logger.log_session(protocol_type, status, **kwargs)
        self.notify_coevolutionary_change(
            "ascension_core", "psycholyse_session", {"session_id": entry.session_id, "status": status}
        )
        return asdict(entry)

    def get_oscillation_report(self, last_n: int = 40) -> Dict[str, Any]:
        """Sisyphos-Oszillationsbericht (Sparkline + Kennzahlen), siehe sisyphos_oscillation_visualizer.py."""
        if not self.oscillation_visualizer:
            return {"status": "SisyphosOscillationVisualizer nicht verfuegbar"}
        from dataclasses import asdict
        return asdict(self.oscillation_visualizer.build_report(last_n=last_n))

    def run_qubo_ascension_optimization(self, n_checkpoints: int = 12, steps: int = 4000) -> Dict[str, Any]:
        """Loest die Devil-vs-Christus-QUBO-Trajektorie, siehe qubo_ascension_optimizer.py."""
        if not QUBOAscensionOptimizer:
            return {"status": "QUBOAscensionOptimizer nicht verfuegbar (qb_qubo/numpy fehlt?)"}
        from dataclasses import asdict
        optimizer = QUBOAscensionOptimizer(n_checkpoints=n_checkpoints)
        result = optimizer.solve(steps=steps)
        summary = asdict(result)
        self.notify_coevolutionary_change("ascension_core", "qubo_ascension_optimization", {"energy": result.energy})
        return summary

    def run_sisyphos_simulation(self, generations: int = 200, n_runs: int = 8) -> Dict[str, Any]:
        """Nicht-persistente Oszillations-Simulation (bis 10k Generationen), siehe evolution/sisyphos_simulator.py."""
        try:
            from ..evolution.sisyphos_simulator import simulate
        except Exception:
            return {"status": "sisyphos_simulator nicht verfuegbar"}
        result = simulate(generations=generations, n_runs=n_runs)
        return {
            "generations": result["generations"],
            "n_runs": result["n_runs"],
            "sustainable_fraction": result["sustainable_fraction"],
            "avg_final_satisfaction": result["avg_final_satisfaction"],
            "avg_reversal_count": result["avg_reversal_count"],
        }

    # ------------------------------------------------------------------
    # Harmonisierung + Geisterjagd (v9.6)
    # ------------------------------------------------------------------

    def run_harmonization(self, state_a: Any, state_b: Any,
                           participant_labels: Any = ("A", "B")) -> Dict[str, Any]:
        """Vierschritt-Harmonisierung zweier Zustaende, siehe harmonisierung_module.py."""
        if not self.harmonisierung:
            return {"status": "HarmonisierungsCoreModule nicht verfuegbar"}
        from dataclasses import asdict
        result = self.harmonisierung.harmonize(state_a, state_b, participant_labels=tuple(participant_labels))
        proposal = self.harmonisierung.propose_self_modification(result)
        self.notify_coevolutionary_change(
            "ascension_core", "harmonization",
            {"zufriedenheitsquant": result.zufriedenheitsquant, "final_gap": result.final_gap},
        )
        return {"result": asdict(result), "self_modification_proposal": proposal}

    def run_geisterjagd(self, latent_state: Any, A: Any, c: Any) -> Dict[str, Any]:
        """Jagt einen 'Geist' (latenten Zustand) zu einem manifesten Fixpunkt, siehe geisterjagd_module.py."""
        if not self.geisterjagd:
            return {"status": "Geisterjagdmodul nicht verfuegbar"}
        from dataclasses import asdict
        result = self.geisterjagd.hunt(latent_state, A, c)
        return asdict(result)

    # ------------------------------------------------------------------
    # Expositions-Uebungspartner (v9.7) - kein Dritter beteiligt
    # ------------------------------------------------------------------

    def start_exposure_session(self, scenario: str = "dating_app_opener",
                                difficulty: str = "mittel") -> Dict[str, Any]:
        self._require_consent("association", action="ascension.start_exposure_session")
        if not self.exposure_practice:
            return {"status": "ExposurePracticeModule nicht verfuegbar"}
        from dataclasses import asdict
        return asdict(self.exposure_practice.start_session(scenario=scenario, difficulty=difficulty))

    def exposure_respond(self, session_id: int, user_message: str) -> Dict[str, Any]:
        self._require_consent("association", action="ascension.exposure_respond")
        if not self.exposure_practice:
            return {"status": "ExposurePracticeModule nicht verfuegbar"}
        session = next((s for s in self.exposure_practice.sessions if s.session_id == session_id), None)
        if not session:
            return {"error": f"Session {session_id} nicht gefunden"}
        reply = self.exposure_practice.respond(session, user_message)
        return {"reply": reply, "turn_count": len(session.turns)}

    def end_exposure_session(self, session_id: int, shutdown_occurred: bool,
                              self_rated_anxiety: Optional[float] = None, notes: str = "") -> Dict[str, Any]:
        self._require_consent("association", action="ascension.end_exposure_session")
        if not self.exposure_practice:
            return {"status": "ExposurePracticeModule nicht verfuegbar"}
        session = next((s for s in self.exposure_practice.sessions if s.session_id == session_id), None)
        if not session:
            return {"error": f"Session {session_id} nicht gefunden"}
        from dataclasses import asdict
        result = self.exposure_practice.end_session(
            session, shutdown_occurred, self_rated_anxiety=self_rated_anxiety, notes=notes
        )
        return asdict(result)

    def get_exposure_progress(self, last_n: Optional[int] = None) -> Dict[str, Any]:
        if not self.exposure_practice:
            return {"status": "ExposurePracticeModule nicht verfuegbar"}
        return self.exposure_practice.get_progress(last_n=last_n)

    # ------------------------------------------------------------------
    # Status + Coevolution
    # ------------------------------------------------------------------

    def get_ascension_status(self) -> Dict[str, Any]:
        status = {
            "version": self.version,
            "mode": self.mode,
            "llm_available": self.llm is not None,
            "sisyphos_available": self.sisyphos is not None,
            "persistent_sisyphos_available": self.persistent_sisyphos is not None,
            "evolution_engine_available": self.evolution_engine is not None,
            "stage9_tracker_available": self.stage9_tracker is not None,
            "psycholyse_logger_available": self.psycholyse_logger is not None,
            "oscillation_visualizer_available": self.oscillation_visualizer is not None,
            "qubo_ascension_optimizer_available": QUBOAscensionOptimizer is not None,
            "harmonisierung_available": self.harmonisierung is not None,
            "geisterjagd_available": self.geisterjagd is not None,
            "exposure_practice_available": self.exposure_practice is not None,
        }

        if self.sisyphos:
            status.update(self.get_sisyphos_state())

        if self.evolution_engine and self.evolution_engine.generations:
            status["evolution_summary"] = self.evolution_engine.get_evolution_summary()

        if self.cec:
            status["cec_status"] = self.cec.get_status()

        if self.stage9_tracker:
            status["stage9"] = self.get_stage9_status()

        return status

    def notify_coevolutionary_change(self, source: str, change_type: str,
                                     payload: Dict[str, Any]) -> None:
        """Propagiert eine Aenderung in die CoEvolutionaryClosure (v9.3)."""
        if self.cec:
            self.cec.notify_change(source, change_type, payload)

    # ------------------------------------------------------------------
    # Evolution + LLM + MasterSeed
    # ------------------------------------------------------------------

    def run_generation(self, generations: int = 5) -> Dict[str, Any]:
        """Fuehrt Inside-Out Generationen aus (coevolutionaer)."""
        if not self.evolution_engine:
            return {"status": "GenerationalEvolutionEngine nicht verfuegbar"}

        current_state = {
            **self.get_sisyphos_state(),
            "fail_closed_active": True,
            "ascension_mode_active": True,
            "cross_layer_integration": 0.8,
        }

        results = self.evolution_engine.run_generations(current_state, generations=generations)
        summary = {
            "generations_run": len(results),
            "summary": self.evolution_engine.get_evolution_summary(),
        }
        self.notify_coevolutionary_change("ascension_core", "generation_run", summary)
        return summary

    def ask(self, prompt: str, context: str = "ascension") -> Any:
        """Ascension-spezifische LLM-Anfrage (falls LLM verfuegbar)."""
        self._require_consent("association", action="ascension.ask")
        if self.llm:
            return self.llm.ask(prompt, context=context)
        return None

    def register_masterseed(self, masterseed: "MasterSeed") -> None:
        self.masterseed = masterseed


_ascension_core_instance: Optional[AscensionCore] = None


def get_ascension_core() -> AscensionCore:
    global _ascension_core_instance
    if _ascension_core_instance is None:
        _ascension_core_instance = AscensionCore()
    return _ascension_core_instance
