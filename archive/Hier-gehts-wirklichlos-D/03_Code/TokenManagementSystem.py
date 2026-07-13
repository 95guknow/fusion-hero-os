#!/usr/bin/env python3
"""
Token Management System (TMS) v1.0
Coevolutionär mit Quantenkognitions-Modell, Spiral Dynamics, Quantenbiologie und Theologie
Motto: Ein Meme/Transformation darf 3x so viele Token verwenden für höhere Fidelity ohne Simplifizierung.
Adaptive Ressourcenverteilung basierend auf Transformationskosten (S(ψ), Im-Spannung, Tiefe).
Ziel: Adaptive Reaktion auf Fluktuationen und Verlagerung von Flaschenhälsen durch dynamische Kompression/Expansion.
Hyperthreaded, Self-Modifying, PeerReview-traceable.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import math
from enum import Enum

class TransformationType(Enum):
    HABITUATION = "habituation"          # qualitative Im-Umkehr
    DROP_RECOVERY = "drop_recovery"      # kontrollierter Sturz + Erholung (Sisyphos)
    PSYCHOLYSE = "psycholyse"            # dialektische Auflösung
    MEME_SYNTHESIS = "meme_synthesis"    # Theorie-Kommunikation (3x Token Regel)
    COEVOLUTION_SYNTHESIS = "coevolution_synthesis"  # volle multi-skalige Integration

@dataclass
class ResourceState:
    stability: float          # S(ψ) Proxy
    latent_tension: float     # |Im| Proxy
    depth: int                # Transformations-Tiefe
    fluctuation_severity: float  # Aktuelle Schwankung (z.B. Im-Spike oder Stage-Drop)
    bottleneck_risk: float    # Geschätzte Flaschenhals-Verlagerung

class TokenManagementSystem:
    """
    Dynamisches Token-Management-System.
    Kosten einer Transformation = f(S, |Im|, Tiefe, Fluktuation)
    Allocation: Invers zu Kosten + Fidelity-Multiplier (bis 3x für hochwertige Meme/Theorie-Transformationen)
    Adaptive Kompression: Bei steigendem Bottleneck-Risiko werden sekundäre Tracks komprimiert.
    """

    def __init__(self, base_tokens: int = 10000, fidelity_multiplier: float = 3.0):
        self.base_tokens = base_tokens
        self.fidelity_multiplier = fidelity_multiplier  # 3x für hohe Fidelity (Meme-Regel)
        self.allocation_log: List[Dict] = []
        self.self_modify_history: List[str] = []

    def calculate_transformation_cost(self, state: ResourceState, t_type: TransformationType) -> float:
        """
        Kosten einer Ressource/Transformation.
        Höhere Kosten = teurer in Token.
        """
        base_cost = (1.0 - state.stability) * 10 + state.latent_tension * 5 + state.depth * 2
        fluctuation_penalty = state.fluctuation_severity * 8
        bottleneck_penalty = state.bottleneck_risk * 12

        # Theologie-inspiriert: Höhere Tiefe (Internalisierung) erhöht Kosten, aber auch Wert
        if t_type in [TransformationType.HABITUATION, TransformationType.PSYCHOLYSE]:
            base_cost *= 1.3  # Internalisierungs-Aufwand

        # Meme/ Coevolution: Hoher Wert → potenziell höhere Kosten, aber 3x Fidelity erlaubt
        if t_type in [TransformationType.MEME_SYNTHESIS, TransformationType.COEVOLUTION_SYNTHESIS]:
            base_cost *= 0.8  # Wird durch Fidelity-Multiplier kompensiert

        total_cost = base_cost + fluctuation_penalty + bottleneck_penalty
        return max(1.0, total_cost)  # Mindestkosten

    def allocate_tokens(self, states: Dict[str, ResourceState], 
                        priorities: Optional[Dict[str, float]] = None) -> Dict[str, int]:
        """
        Verteilte Ressourcen (Tokens) adaptiv.
        - Basis: Invers zu Kosten
        - Fidelity-Boost: Bis 3x für hochwertige Transformationen (Meme-Regel)
        - Adaptive Kompression: Bei hohem Bottleneck-Risiko werden niedrig-priorisierte Tracks reduziert
        """
        if priorities is None:
            priorities = {name: 1.0 for name in states}

        costs = {}
        for name, state in states.items():
            # Standard-Kosten für die primäre Transformation (angenommen HABITUATION als Default)
            t_type = TransformationType.HABITUATION
            if "meme" in name.lower() or "synthesis" in name.lower():
                t_type = TransformationType.MEME_SYNTHESIS
            elif "coevolution" in name.lower():
                t_type = TransformationType.COEVOLUTION_SYNTHESIS
            elif "drop" in name.lower() or "sisyphos" in name.lower():
                t_type = TransformationType.DROP_RECOVERY

            costs[name] = self.calculate_transformation_cost(state, t_type)

        total_cost = sum(costs.values())
        if total_cost == 0:
            total_cost = 1.0

        allocations = {}
        for name, cost in costs.items():
            # Basis-Allocation (invers zu Kosten)
            base_share = (1.0 / cost) / (sum(1.0 / c for c in costs.values())) * self.base_tokens

            # Fidelity-Multiplier (bis 3x für hochwertige Tracks)
            fidelity = self.fidelity_multiplier if priorities.get(name, 1.0) > 1.5 else 1.0
            allocated = int(base_share * fidelity * priorities.get(name, 1.0))

            # Adaptive Kompression bei hohem Bottleneck-Risiko
            if states[name].bottleneck_risk > 0.7:
                compression_factor = max(0.3, 1.0 - states[name].bottleneck_risk)
                allocated = int(allocated * compression_factor)

            allocations[name] = max(10, allocated)  # Mindest-Token

        # Normalisierung auf Gesamtbudget (mit Puffer für Fluktuationen)
        total_allocated = sum(allocations.values())
        if total_allocated > self.base_tokens * 1.2:
            scale = (self.base_tokens * 1.2) / total_allocated
            allocations = {k: max(10, int(v * scale)) for k, v in allocations.items()}

        self._log_allocation(allocations, costs, states)
        return allocations

    def _log_allocation(self, allocations: Dict[str, int], costs: Dict[str, float], states: Dict[str, ResourceState]):
        entry = {
            "allocations": allocations,
            "costs": costs,
            "avg_fluctuation": sum(s.fluctuation_severity for s in states.values()) / len(states),
            "bottleneck_shift_detected": any(s.bottleneck_risk > 0.6 for s in states.values())
        }
        self.allocation_log.append(entry)
        if len(self.allocation_log) > 50:
            self.allocation_log.pop(0)

    def detect_and_adapt_to_bottleneck_shift(self, current_states: Dict[str, ResourceState]) -> Dict[str, float]:
        """
        Erkennt Verlagerung von Flaschenhälsen und schlägt neue Prioritäten vor.
        """
        new_priorities = {}
        for name, state in current_states.items():
            if state.bottleneck_risk > 0.65 or state.fluctuation_severity > 0.5:
                new_priorities[name] = 2.5  # Hohe Priorität für betroffene Tracks
            else:
                new_priorities[name] = 1.0
        return new_priorities

    def evolve_cost_function(self, feedback: Dict):
        """
        Self-Modification: Passt die Kostenfunktion basierend auf Feedback an (z.B. aus PeerReview oder realen Runs).
        """
        if feedback.get("too_much_compression"):
            self.fidelity_multiplier = min(4.0, self.fidelity_multiplier * 1.1)
            self.self_modify_history.append("Increased fidelity_multiplier due to excessive compression")
        if feedback.get("wasted_tokens_on_low_value"):
            self.fidelity_multiplier = max(1.5, self.fidelity_multiplier * 0.9)
            self.self_modify_history.append("Decreased fidelity_multiplier for efficiency")

# Beispiel-Nutzung im Core-Kontext
if __name__ == "__main__":
    tms = TokenManagementSystem(base_tokens=8000, fidelity_multiplier=3.0)

    # Simulierte aktuelle States (z.B. aus Quantenkognitions-Modell + Spiral Dynamics + Quantum Bio Monitoring)
    states = {
        "quantenkognition_habituation": ResourceState(stability=0.75, latent_tension=0.4, depth=3, fluctuation_severity=0.3, bottleneck_risk=0.2),
        "sisyphos_oscillation": ResourceState(stability=0.6, latent_tension=0.7, depth=2, fluctuation_severity=0.6, bottleneck_risk=0.55),
        "coevolution_synthesis": ResourceState(stability=0.85, latent_tension=0.25, depth=5, fluctuation_severity=0.15, bottleneck_risk=0.1),
        "meme_theory_communication": ResourceState(stability=0.9, latent_tension=0.15, depth=4, fluctuation_severity=0.1, bottleneck_risk=0.05),
    }

    priorities = tms.detect_and_adapt_to_bottleneck_shift(states)
    allocations = tms.allocate_tokens(states, priorities)

    print("=== Token Management System v1.0 ===")
    print(f"Priorities (adaptive): {priorities}")
    print(f"Allocations: {allocations}")
    print(f"Total allocated: {sum(allocations.values())} / {tms.base_tokens}")
    print("Bottleneck shift handling active. 3x Fidelity for high-value transformations enabled.")