"""TimespaceTokenManager — volle geometrische + TMS-Allokation."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from fusion_hero_os.modules.timespace_token.bottleneck import (
    build_competition_qubo,
    greedy_bottleneck_assignment,
    qubo_energy,
)
from fusion_hero_os.modules.timespace_token.geometry import (
    Timescale,
    TimespaceCoordinate,
    TimespaceManifold,
)

# TMS aus 03_Code (Repo-Root relativ) — einmaliger Pfad-Inject
_CODE = Path(__file__).resolve().parents[3] / "03_Code"
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from TokenManagementSystem import (  # noqa: E402
    ResourceState,
    TokenManagementSystem,
    TransformationType,
)


@dataclass
class TimespaceTrack:
    name: str
    coordinate: TimespaceCoordinate
    state: ResourceState
    transformation: TransformationType = TransformationType.HABITUATION


@dataclass
class AllocationReport:
    allocations: Dict[str, int]
    priorities: Dict[str, float]
    geometry: List[Dict[str, float]]
    qubo_energy: Optional[float] = None
    fidelity_applied: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allocations": self.allocations,
            "priorities": self.priorities,
            "geometry": self.geometry,
            "qubo_energy": self.qubo_energy,
            "fidelity_applied": self.fidelity_applied,
            "total_allocated": sum(self.allocations.values()),
        }


class TimespaceTokenManager:
    """
    Geometrische Token-Verteilung mit Multi-Scale-Fidelity und QUBO-Bottleneck-Hint.
    """

    FIDELITY_TYPES = {
        TransformationType.MEME_SYNTHESIS,
        TransformationType.COEVOLUTION_SYNTHESIS,
    }

    def __init__(
        self,
        base_tokens: int = 10000,
        fidelity_multiplier: float = 3.0,
        manifold: Optional[TimespaceManifold] = None,
        bottleneck_budget_slots: int = 3,
    ) -> None:
        self.tms = TokenManagementSystem(base_tokens=base_tokens, fidelity_multiplier=fidelity_multiplier)
        self.manifold = manifold or TimespaceManifold.default()
        self.bottleneck_budget_slots = bottleneck_budget_slots

    def _fidelity_boost(self, track: TimespaceTrack, geo_priority: float) -> float:
        """3x-Fidelity-Regel für Meme/Coevolution nahe am Layer-Ursprung."""
        if track.transformation not in self.FIDELITY_TYPES:
            return 1.0
        origin = self.manifold.origin_for_depth(track.coordinate.space_depth)
        if track.coordinate.distance_to(origin) <= self.manifold.compression_radius[track.coordinate.timescale]:
            return self.tms.fidelity_multiplier
        return 1.0

    def allocate(
        self,
        tracks: List[TimespaceTrack],
        extra_priorities: Optional[Dict[str, float]] = None,
    ) -> Dict[str, int]:
        return self.allocate_with_report(tracks, extra_priorities).allocations

    def allocate_with_report(
        self,
        tracks: List[TimespaceTrack],
        extra_priorities: Optional[Dict[str, float]] = None,
    ) -> AllocationReport:
        states = {t.name: t.state for t in tracks}
        adapt = self.tms.detect_and_adapt_to_bottleneck_shift(states)
        risks = {t.name: t.state.bottleneck_risk for t in tracks}
        qubo_prior = greedy_bottleneck_assignment(
            [t.name for t in tracks], risks, self.bottleneck_budget_slots
        )
        neighbor = self.manifold.neighbor_compression([(t.name, t.coordinate) for t in tracks])

        priorities: Dict[str, float] = {}
        fidelity_applied: Dict[str, bool] = {}
        for track in tracks:
            geo = self.manifold.geometric_priority(track.coordinate)
            fid = self._fidelity_boost(track, geo)
            fidelity_applied[track.name] = fid > 1.0
            extra = (extra_priorities or {}).get(track.name, 1.0)
            priorities[track.name] = (
                geo * adapt.get(track.name, 1.0) * qubo_prior.get(track.name, 1.0)
                * neighbor.get(track.name, 1.0) * extra * fid
            )

        q = build_competition_qubo([t.name for t in tracks], risks)
        assignment = [1 if priorities[t.name] >= 1.0 else 0 for t in tracks]
        energy = qubo_energy(q, assignment) if tracks else None

        allocations = self.tms.allocate_tokens(states, priorities)
        geometry = [
            {
                "name": t.name,
                "time_index": t.coordinate.time_index,
                "space_depth": t.coordinate.space_depth,
                "timescale": t.coordinate.timescale.value,
                "priority": priorities[t.name],
                "transformation": t.transformation.value,
            }
            for t in tracks
        ]
        return AllocationReport(
            allocations=allocations,
            priorities=priorities,
            geometry=geometry,
            qubo_energy=energy,
            fidelity_applied=fidelity_applied,
        )

    def evolve_from_feedback(self, feedback: Dict[str, Any]) -> List[str]:
        """Self-Modification via TMS + optional Manifold-Anpassung."""
        self.tms.evolve_cost_function(feedback)
        changes: List[str] = list(self.tms.self_modify_history[-2:])
        if feedback.get("expand_macro_radius"):
            for scale in self.manifold.compression_radius:
                if scale == Timescale.MACRO:
                    self.manifold.compression_radius[scale] = min(
                        8.0, self.manifold.compression_radius[scale] * 1.1
                    )
                    changes.append("expanded_macro_compression_radius")
        return changes