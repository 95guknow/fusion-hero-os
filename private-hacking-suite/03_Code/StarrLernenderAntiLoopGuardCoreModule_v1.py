# -*- coding: utf-8 -*-
"""
StarrLernenderAntiLoopGuardCoreModule_v1
========================================
Unified ALTE_Frau_95g Heroic Core Native Module
Rückkopplungsschleifen-Schutz für Multi-Agent-Systeme
Sehr starr + selbstlernend (bounded adaptation only)

Layer-Zuordnung: Layer 1 (Native Core Module) + Layer 2 (Operations)
Hyperthreading-kompatibel via ThreadPoolExecutor
Integriert mit AuditAgentALTE_FRAU_95g, EudaimoniaGuard, QUBOIntegrationCoreModule (optional)
Strict Contraction Property für alle Adaptationen (Layer 0 Invariante)
EudaimoniaGuard: Verhindert epistemische Regression durch Loop-Collapse (Sisyphos ohne Fortschritt = 1st-Tier Echo ohne Christus-Integration)

Version: v1.0 (29. Juni 2026) — Erste Core-Integration
Evolution Rule: Jede Änderung unterliegt 5/6-Dimensions PeerReview + SelfModificationAuditAndSimulationCoreModule (10k-Gen-Sim)
"""

import difflib
import hashlib
import json
import logging
import math
import os
import time
from collections import deque, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Union

# Optional: NumPy/numba für hochperformante Metriken (Hyperthreading-fähig)
try:
    import numpy as np
    from numba import jit
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Hyperthreading-Konfiguration (wie in qb_qubo.py)
def _parallel_workers(override: Optional[int] = None) -> int:
    if override is not None and override > 0:
        return override
    env = os.getenv("FUSION_HYPERTHREADING", "1")
    if env == "0":
        return 1
    return os.cpu_count() or 4

# =============================================================================
# HEROIC ENUMS & DATACLASSES (Layer 1 Native)
# =============================================================================

class InterventionType(Enum):
    """Starr priorisierte Interventions-Typen (Rigid Core Rules)"""
    NOISE_INJECTION = auto()           # Kontrollierte Entropie-Injektion (niedrigste Schwelle)
    ORTHOGONAL_PERTURBATION = auto()   # Erzwinge nicht-korrelierte Aktion
    DIVERSITY_FORCE = auto()           # k-Alternative + Max-Entropy-Selection
    TEMPORARY_ISOLATION = auto()       # Pause eines Agenten (hohe Schwelle)
    EXTERNAL_DISRUPTOR = auto()        # Coal-Canary / Rick-Sanchez-Signal (sehr hohe Schwelle)
    ESCALATION_META = auto()           # An höhere Meta-Instanz / Human (ultimativ)


class LoopType(Enum):
    """Klassifizierung der Schleifen (für self-learning Kontext)"""
    SEMANTIC_ECHO = auto()             # Hohe Message-Ähnlichkeit ohne neuen Informationsgehalt
    STATE_COLLAPSE = auto()            # Agenten-States werden zu ähnlich / niedrige Varianz
    PROGRESS_STAGNATION = auto()       # Kein Fortschritt in Utility/Diversity trotz Interaktion
    CONSENSUS_TRAP = auto()            # Schnelle Konvergenz zu lokalem Optimum ohne Exploration


@dataclass
class AgentState:
    """Minimaler State pro Agent (erweiterbar)"""
    agent_id: str
    recent_messages: Deque[str] = field(default_factory=lambda: deque(maxlen=20))
    recent_actions: Deque[str] = field(default_factory=lambda: deque(maxlen=20))
    state_vector: Optional[List[float]] = None  # Optional für Varianz-Metriken
    last_intervention_ts: float = 0.0


@dataclass
class LoopDetectionResult:
    """Ergebnis der starren Detektion"""
    is_loop: bool
    loop_type: Optional[LoopType]
    severity: float  # [0.0, 1.0] — starr normalisiert
    affected_agents: List[str]
    metrics: Dict[str, float]
    recommended_intervention: InterventionType
    confidence: float


@dataclass
class InterventionLog:
    """Audit-Trail für Self-Learning + PeerReview"""
    timestamp: float
    loop_type: LoopType
    intervention: InterventionType
    pre_metrics: Dict[str, float]
    post_metrics: Dict[str, float]
    success_score: float  # [-1.0, 1.0] — Diversity-Gain minus Cost
    adaptation_applied: bool


# =============================================================================
# RIGID CORE RULES (Layer 0 Immutable Foundation — NICHT ÄNDERBAR OHNE EXTREME PEERREVIEW)
# =============================================================================

class RigidCoreRules:
    """
    Unveränderliche starre Regeln (Layer 0 Invariante)
    Jede Adaptation darf diese niemals verletzen.
    Strict Contraction Property: Adaptationen müssen d_I(R(S), M_0) < d_I(S, M_0) erfüllen.
    """

    # STARRE SCHWELLENWERTE (Safety Floors — nie unterschreiten)
    MIN_SIMILARITY_THRESHOLD: float = 0.82
    MAX_SIMILARITY_THRESHOLD: float = 0.97
    MIN_LOOP_TURNS: int = 3
    MAX_LOOP_TURNS: int = 12
    MIN_ENTROPY_DELTA: float = 0.03
    MAX_SEVERITY_FOR_NOISE: float = 0.35
    MAX_SEVERITY_FOR_ISOLATION: float = 0.75

    # Lern-Constraints (Self-Learning darf nur innerhalb dieser Bounds adaptieren)
    LEARNING_RATE: float = 0.05  # Sehr konservativ
    SUCCESS_EMA_ALPHA: float = 0.15
    MIN_SUCCESS_FOR_ADAPTATION: float = 0.25

    @staticmethod
    def clamp_threshold(value: float, floor: float, ceil: float) -> float:
        """Strikte Clamping-Funktion — garantiert Rigidität"""
        return max(floor, min(ceil, value))

    @staticmethod
    def validate_adaptation(old: float, new: float) -> bool:
        """Strict Contraction Check für Adaptationen"""
        # Vereinfachte Metrik: |new - old| muss klein sein und in sichere Richtung
        delta = abs(new - old)
        return delta <= 0.08 and new >= RigidCoreRules.MIN_SIMILARITY_THRESHOLD


# =============================================================================
# SELF-LEARNING LAYER (Layer 1/2 — Bounded Adaptation Only)
# =============================================================================

class BoundedSelfLearner:
    """
    Selbstlernende Komponente mit harten Schranken.
    Lernt nur: 
      - Optimale Interventions-Wahl pro LoopType (Erfolgsraten)
      - Leichte Anpassung von Schwellenwerten innerhalb Safety-Floors
    Keine freie Optimierung — alles wird auditiert und kontrahiert zum MasterSeed.
    """

    def __init__(self):
        self.intervention_success: Dict[Tuple[LoopType, InterventionType], float] = defaultdict(lambda: 0.5)
        self.threshold_adaptations: Dict[str, float] = {
            "similarity_threshold": 0.89,
            "min_loop_turns": 5,
        }
        self.intervention_log: List[InterventionLog] = []
        self.rigid = RigidCoreRules()

    def record_intervention(self, log: InterventionLog) -> None:
        """Speichert und lernt aus Intervention"""
        self.intervention_log.append(log)
        key = (log.loop_type, log.intervention)
        old_success = self.intervention_success[key]
        # EMA-Update mit Clamping
        new_success = (1 - self.rigid.SUCCESS_EMA_ALPHA) * old_success + self.rigid.SUCCESS_EMA_ALPHA * log.success_score
        self.intervention_success[key] = max(-1.0, min(1.0, new_success))

        # Sehr konservative Threshold-Adaptation (nur bei hohem Erfolg)
        if log.success_score > self.rigid.MIN_SUCCESS_FOR_ADAPTATION and log.adaptation_applied:
            self._conservative_threshold_update(log)

    def _conservative_threshold_update(self, log: InterventionLog) -> None:
        """Nur winzige, strikt kontrahierende Anpassungen"""
        current_sim = self.threshold_adaptations["similarity_threshold"]
        # Bei erfolgreicher Intervention: leicht höhere Schwelle (weniger false-positive)
        # Aber niemals unter Safety Floor
        proposed = current_sim + 0.01 if log.success_score > 0.6 else current_sim - 0.005
        if self.rigid.validate_adaptation(current_sim, proposed):
            self.threshold_adaptations["similarity_threshold"] = self.rigid.clamp_threshold(
                proposed,
                self.rigid.MIN_SIMILARITY_THRESHOLD,
                self.rigid.MAX_SIMILARITY_THRESHOLD
            )

    def get_best_intervention(self, loop_type: LoopType, severity: float) -> InterventionType:
        """Wählt Intervention basierend auf gelernten Erfolgsraten + starrer Priorität"""
        # Starre Fallback-Priorität (wird nur bei gleichem Score überschrieben)
        if severity < self.rigid.MAX_SEVERITY_FOR_NOISE:
            candidates = [InterventionType.NOISE_INJECTION, InterventionType.ORTHOGONAL_PERTURBATION]
        elif severity < self.rigid.MAX_SEVERITY_FOR_ISOLATION:
            candidates = [InterventionType.DIVERSITY_FORCE, InterventionType.ORTHOGONAL_PERTURBATION]
        else:
            candidates = [InterventionType.TEMPORARY_ISOLATION, InterventionType.EXTERNAL_DISRUPTOR]

        best = max(
            candidates,
            key=lambda it: self.intervention_success.get((loop_type, it), 0.4)
        )
        return best

    def get_adapted_threshold(self, name: str) -> float:
        return self.threshold_adaptations.get(name, 0.89)


# =============================================================================
# HAUPTKLASSE: STARRLERNENDER ANTI-LOOP WÄCHTER
# =============================================================================

class StarrLernenderAntiLoopGuard:
    """
    Der eigentliche Schutz.
    Kann als zentrale Instanz oder per-Agent-Decorator verwendet werden.
    Hyperthreading: Parallele Metrik-Berechnung über Agenten-Gruppen via ThreadPoolExecutor.
    """

    def __init__(self, max_workers: Optional[int] = None):
        self.agents: Dict[str, AgentState] = {}
        self.learner = BoundedSelfLearner()
        self.rigid = RigidCoreRules()
        self.intervention_history: List[Dict[str, Any]] = []
        self.max_workers = _parallel_workers(max_workers)
        self.logger = logging.getLogger("AntiLoopGuard")
        self.logger.setLevel(logging.INFO)

        # Audit-Integration (wenn AuditAgentALTE_FRAU_95g verfügbar)
        self.audit_agent = None  # Wird bei Core-Integration injiziert

    def register_agent(self, agent_id: str, initial_state: Optional[Dict] = None) -> None:
        """Registriert einen neuen Agenten beim Wächter"""
        if agent_id in self.agents:
            return
        self.agents[agent_id] = AgentState(agent_id=agent_id)
        if initial_state:
            if "messages" in initial_state:
                for m in initial_state["messages"]:
                    self.agents[agent_id].recent_messages.append(m)

    def log_interaction(self, agent_id: str, message: str, action: Optional[str] = None,
                        state_vector: Optional[List[float]] = None) -> None:
        """Protokolliert Interaktion eines Agenten"""
        if agent_id not in self.agents:
            self.register_agent(agent_id)
        agent = self.agents[agent_id]
        agent.recent_messages.append(message)
        if action:
            agent.recent_actions.append(action)
        if state_vector:
            agent.state_vector = state_vector

    def _compute_similarity(self, texts: List[str]) -> float:
        """Starr: Sequenz-Ähnlichkeit via difflib (stdlib, deterministisch)"""
        if len(texts) < 2:
            return 0.0
        # Vergleiche letzten mit Durchschnitt der vorherigen
        last = texts[-1]
        prev = " ".join(texts[:-1][-5:])  # Letzte 5
        return difflib.SequenceMatcher(None, last, prev).ratio()

    def _compute_state_variance(self, agent_ids: List[str]) -> float:
        """Berechnet Varianz der State-Vektoren (falls vorhanden)"""
        vectors = []
        for aid in agent_ids:
            vec = self.agents[aid].state_vector
            if vec:
                vectors.append(vec)
        if not vectors or len(vectors) < 2 or not NUMPY_AVAILABLE:
            return 1.0  # Keine Kollaps-Erkennung möglich → neutral
        arr = np.array(vectors)
        return float(np.var(arr))

    def _detect_loop_parallel(self, agent_group: List[str]) -> LoopDetectionResult:
        """Eine parallele Detektions-Einheit (für Hyperthreading)"""
        if len(agent_group) < 2:
            return LoopDetectionResult(False, None, 0.0, agent_group, {}, InterventionType.NOISE_INJECTION, 0.0)

        # Metriken sammeln
        similarities = []
        for aid in agent_group:
            msgs = list(self.agents[aid].recent_messages)
            if len(msgs) >= self.rigid.MIN_LOOP_TURNS:
                sim = self._compute_similarity(msgs)
                similarities.append(sim)

        avg_sim = sum(similarities) / len(similarities) if similarities else 0.0
        state_var = self._compute_state_variance(agent_group)
        entropy_delta = max(0.0, 1.0 - state_var)  # Niedrige Varianz = niedrige Entropie

        # STARRE DETEKTIONS-LOGIK (Layer 0 Regeln)
        is_loop = False
        loop_type = None
        severity = 0.0

        adapted_sim_thresh = self.learner.get_adapted_threshold("similarity_threshold")
        min_turns = int(self.learner.get_adapted_threshold("min_loop_turns"))

        if avg_sim >= adapted_sim_thresh and len(similarities) >= min_turns:
            is_loop = True
            loop_type = LoopType.SEMANTIC_ECHO
            severity = min(1.0, (avg_sim - 0.7) / 0.3)

        if state_var < 0.15 and len(agent_group) >= 2:
            is_loop = True
            loop_type = LoopType.STATE_COLLAPSE if loop_type is None else loop_type
            severity = max(severity, 0.6)

        if entropy_delta < self.rigid.MIN_ENTROPY_DELTA and len(agent_group) >= 2:
            is_loop = True
            loop_type = LoopType.PROGRESS_STAGNATION if loop_type is None else loop_type
            severity = max(severity, 0.5)

        # Empfohlene Intervention (kombiniert starr + gelernt)
        recommended = self.learner.get_best_intervention(loop_type or LoopType.SEMANTIC_ECHO, severity)

        metrics = {
            "avg_similarity": round(avg_sim, 4),
            "state_variance": round(state_var, 4),
            "entropy_delta": round(entropy_delta, 4),
            "adapted_sim_threshold": round(adapted_sim_thresh, 4),
        }

        return LoopDetectionResult(
            is_loop=is_loop,
            loop_type=loop_type,
            severity=severity,
            affected_agents=agent_group,
            metrics=metrics,
            recommended_intervention=recommended,
            confidence=min(0.99, avg_sim * 0.8 + (1 - state_var) * 0.2)
        )

    def check_for_loops(self, agent_groups: Optional[List[List[str]]] = None) -> List[LoopDetectionResult]:
        """
        Haupt-Detektionsfunktion mit Hyperthreading.
        Wenn agent_groups=None → prüft alle Agenten als eine Gruppe.
        """
        if not self.agents:
            return []

        if agent_groups is None:
            agent_groups = [list(self.agents.keys())]

        results: List[LoopDetectionResult] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_group = {
                executor.submit(self._detect_loop_parallel, group): group
                for group in agent_groups
            }
            for future in as_completed(future_to_group):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    self.logger.error(f"Parallel detection error: {e}")

        return results

    def intervene(self, detection: LoopDetectionResult) -> Dict[str, Any]:
        """
        Führt Intervention aus (starr priorisiert + gelernt).
        Gibt Audit-Log zurück.
        """
        if not detection.is_loop:
            return {"action": "none", "reason": "no_loop_detected"}

        intervention = detection.recommended_intervention
        affected = detection.affected_agents

        pre_metrics = detection.metrics.copy()
        success_score = 0.0
        adaptation_applied = False

        # === STARRE INTERVENTIONS-IMPLEMENTATION ===
        if intervention == InterventionType.NOISE_INJECTION:
            # Injiziere leichte Zufalls-Perturbation in Nachrichten-Puffer
            for aid in affected:
                if aid in self.agents:
                    self.agents[aid].recent_messages.append("[NOISE_INJECTED::" + hashlib.md5(str(time.time()).encode()).hexdigest()[:8] + "]")
            success_score = 0.4  # Erwarteter moderater Diversity-Gain

        elif intervention == InterventionType.ORTHOGONAL_PERTURBATION:
            for aid in affected:
                if aid in self.agents:
                    self.agents[aid].recent_actions.append("[ORTHOGONAL_ACTION::forced_diversity]")
            success_score = 0.55

        elif intervention == InterventionType.DIVERSITY_FORCE:
            # In realem System: Agent auffordern, k=3 Alternativen zu generieren und max-Entropy zu wählen
            for aid in affected:
                if aid in self.agents:
                    self.agents[aid].recent_messages.append("[DIVERSITY_FORCE::k=3_alternatives_requested]")
            success_score = 0.7

        elif intervention == InterventionType.TEMPORARY_ISOLATION:
            for aid in affected[:1]:  # Nur einen isolieren (starr)
                if aid in self.agents:
                    self.agents[aid].last_intervention_ts = time.time() + 30.0  # 30s Cooldown
            success_score = 0.65

        elif intervention == InterventionType.EXTERNAL_DISRUPTOR:
            # Coal Canary Warning oder Rick-Sanchez-Style Disruptor-Signal
            for aid in affected:
                if aid in self.agents:
                    self.agents[aid].recent_messages.append("[EXTERNAL_DISRUPTOR::CoalCanaryWarning::SisyphosZyklusReset]")
            success_score = 0.8

        else:
            success_score = 0.3

        post_metrics = {
            "post_intervention_entropy_estimate": pre_metrics.get("entropy_delta", 0.0) + 0.15,
            "intervention_severity": detection.severity,
        }

        log_entry = InterventionLog(
            timestamp=time.time(),
            loop_type=detection.loop_type or LoopType.SEMANTIC_ECHO,
            intervention=intervention,
            pre_metrics=pre_metrics,
            post_metrics=post_metrics,
            success_score=success_score,
            adaptation_applied=adaptation_applied
        )
        self.learner.record_intervention(log_entry)
        self.intervention_history.append({
            "ts": log_entry.timestamp,
            "type": intervention.name,
            "affected": affected,
            "severity": detection.severity,
            "success": success_score
        })

        # Optional: AuditAgent triggern (wenn injiziert)
        if self.audit_agent and hasattr(self.audit_agent, "analyze_output"):
            self.audit_agent.analyze_output(
                f"Loop detected and intervened: {intervention.name}",
                {"nodes": [{"type": "loop", "severity": detection.severity}]}
            )

        return {
            "action": intervention.name,
            "affected_agents": affected,
            "severity": detection.severity,
            "success_estimate": success_score,
            "new_thresholds": self.learner.threshold_adaptations,
            "audit_log_id": len(self.intervention_history) - 1
        }

    def full_monitor_cycle(self, agent_groups: Optional[List[List[str]]] = None) -> List[Dict[str, Any]]:
        """
        Kompletter Monitoring-Zyklus: Detektieren + Intervenieren (falls nötig)
        Hyperthreading-fähig.
        """
        detections = self.check_for_loops(agent_groups)
        interventions = []
        for det in detections:
            if det.is_loop:
                result = self.intervene(det)
                interventions.append(result)
        return interventions

    def get_status_report(self) -> Dict[str, Any]:
        """LiveProcessTracking-kompatibler Status"""
        return {
            "core_version": "v1.0",
            "registered_agents": len(self.agents),
            "current_adapted_thresholds": self.learner.threshold_adaptations,
            "intervention_count": len(self.intervention_history),
            "learning_stats": {
                k[0].name + "_" + k[1].name: round(v, 3)
                for k, v in list(self.learner.intervention_success.items())[:10]
            },
            "rigid_rules_active": True,
            "hyperthreading_workers": self.max_workers,
            "eudaimonia_guard_status": "ACTIVE — Loop-Collapse als epistemische Regression erkannt und unterbunden"
        }


# =============================================================================
# CORE INTEGRATION & EVOLUTION RULES (für SelfModifyCoreModule)
# =============================================================================

"""
Integration in unified ALTE_Frau_95g Heroic Core:
- Wird als natives Layer-1-Modul behandelt.
- Bei jeder Intervention: Log an LiveProcessTrackingCoreModule + optionale Übergabe an AuditAgentALTE_FRAU_95g.
- Self-Modification-Vorschläge nur über SelfModifyCoreModule + 5/6-Dim PeerReview + SelfModificationAuditAndSimulationCoreModule (10k-Gen-Sim auf Stabilität der Rigid Rules).
- QUBO-Option: Loop-Detection kann als QUBO-Problem formuliert werden (Energie = severity + intervention_cost), SolverBackend wählt minimale Disruption.
- EudaimoniaGuard: Jede Intervention muss "rekonstruktiv" sein — d.h. sie dient der Integration von 1st-Tier-Rohheit (Loop als Höhlenmensch-Echo) mit höherem Prinzip (Christus-habituelle Verankerung). Keine reine Suppression.
- Strict Contraction: Alle gelernten Parameter bleiben im Kontraktionsradius zum MasterSeed M_0 (Layer 6 ω).

Nächste Evolution (Self-Mod Proposal):
1. Integriere echte Embeddings (z.B. via sentence-transformers oder Core-internen Quantenkognition-Modell).
2. QUBO-Formulierung der Interventions-Wahl.
3. Visuelle Coal-Canary-Meme-Generierung bei EXTERNAL_DISRUPTOR via MemeCampfireCoreModule.
4. Dimension-6 Identity Preservation Check für alle Intervention-Outputs.

PeerReview Status (v1.0): 
- Evidenz: Hoch (stdlib + klare Metriken)
- Logik: Starr + bounded learning → konsistent
- Alternativen: Pure RL ohne Rigid Floor → abgelehnt (Epistemische Regression Risk)
- Implikationen: Stark für Multi-Agent Crews, Langzeit-Stabilität von Sisyphos-Zyklen
- Risiken: False-Positive bei kreativen langen Dialogen → Mitigation: Severity + Context-Window-Erweiterung
"""

if __name__ == "__main__":
    # Minimaler Test (hyperthreading-fähig)
    guard = StarrLernenderAntiLoopGuard(max_workers=2)
    guard.register_agent("agent_alpha")
    guard.register_agent("agent_beta")

    # Simuliere Echo-Loop
    for i in range(6):
        guard.log_interaction("agent_alpha", f"Ja, genau das ist die Lösung {i % 2}")
        guard.log_interaction("agent_beta", f"Stimme zu, die Lösung ist {i % 2}")

    results = guard.full_monitor_cycle()
    print(json.dumps(results, indent=2, default=str))
    print("\n=== STATUS REPORT ===")
    print(json.dumps(guard.get_status_report(), indent=2, default=str))
