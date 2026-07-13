"""BaseModule-Adapter für Timespace Token Management."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fusion_hero_os.core.base_module import BaseModule, ReviewCriterion, ReviewResult
from fusion_hero_os.modules.timespace_token.geometry import Timescale, TimespaceCoordinate
from fusion_hero_os.modules.timespace_token.manager import TimespaceTokenManager, TimespaceTrack

# ResourceState / TransformationType via Manager-Pfad
import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parents[3] / "03_Code"
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
from TokenManagementSystem import ResourceState, TransformationType  # noqa: E402


def _track_from_dict(raw: Dict[str, Any]) -> TimespaceTrack:
    coord = raw.get("coordinate", {})
    state = raw.get("state", {})
    t_type = raw.get("transformation", "habituation")
    try:
        transformation = TransformationType(t_type)
    except ValueError:
        transformation = TransformationType.HABITUATION
    return TimespaceTrack(
        name=str(raw["name"]),
        coordinate=TimespaceCoordinate(
            time_index=float(coord.get("time_index", 0)),
            space_depth=float(coord.get("space_depth", 0)),
            timescale=Timescale(coord.get("timescale", "meso")),
        ),
        state=ResourceState(
            stability=float(state.get("stability", 0.5)),
            latent_tension=float(state.get("latent_tension", 0.3)),
            depth=int(state.get("depth", 1)),
            fluctuation_severity=float(state.get("fluctuation_severity", 0.2)),
            bottleneck_risk=float(state.get("bottleneck_risk", 0.2)),
        ),
        transformation=transformation,
    )


class TimespaceTokenCoreModule(BaseModule):
    """``process(payload)`` mit actions: allocate | evolve | report."""

    def __init__(self) -> None:
        super().__init__()
        self._manager = TimespaceTokenManager()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        action = payload.get("action", "allocate")

        if action == "evolve":
            changes = self._manager.evolve_from_feedback(payload.get("feedback", {}))
            return {"action": "evolve", "changes": changes}

        tracks_raw: List[Dict[str, Any]] = payload.get("tracks", [])
        if not tracks_raw:
            return {"error": "tracks required", "action": action}

        tracks = [_track_from_dict(t) for t in tracks_raw]
        if payload.get("init"):
            init = payload["init"]
            self._manager = TimespaceTokenManager(
                base_tokens=int(init.get("base_tokens", 10000)),
                fidelity_multiplier=float(init.get("fidelity_multiplier", 3.0)),
                bottleneck_budget_slots=int(init.get("bottleneck_budget_slots", 3)),
            )

        report = self._manager.allocate_with_report(
            tracks, extra_priorities=payload.get("extra_priorities")
        )
        return {"action": "allocate", **report.to_dict()}

    def peer_review(self, target: Optional[Dict[str, Any]] = None) -> ReviewResult:
        return ReviewResult(
            module=self.name,
            criteria=[
                ReviewCriterion("Geometrie + Manifold", True, "TimespaceManifold.default()"),
                ReviewCriterion("QUBO-Bottleneck-Hint", True, "greedy + energy metric"),
                ReviewCriterion("3x-Fidelity-Regel", True, "Meme/Coevolution nahe Ursprung"),
                ReviewCriterion("Volle Zeitaum-Geometrie", False, "Konzept — 2D-Scaffold"),
            ],
        )