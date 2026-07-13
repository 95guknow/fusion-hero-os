"""Geometrie für Timespace Token Management."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple


class Timescale(str, Enum):
    """Zeitskalen für Multi-Scale-Fidelity (3x-Regel pro Skala)."""

    MICRO = "micro"    # Einzel-Turn / Im-Spike
    MESO = "meso"      # Session / Stage
    MACRO = "macro"    # Roadmap / MasterSeed


@dataclass(frozen=True)
class TimespaceCoordinate:
    """2D-Zeit-Raum-Punkt mit optionaler Zeitskala."""

    time_index: float
    space_depth: float
    timescale: Timescale = Timescale.MESO

    def distance_to(self, other: "TimespaceCoordinate") -> float:
        scale_weight = {
            Timescale.MICRO: 1.2,
            Timescale.MESO: 1.0,
            Timescale.MACRO: 0.85,
        }
        w = scale_weight.get(self.timescale, 1.0)
        return w * math.hypot(
            self.time_index - other.time_index,
            self.space_depth - other.space_depth,
        )


@dataclass
class TimespaceManifold:
    """
    Layer-bewusste Mannigfaltigkeit: Ursprung pro Layer, Kompressionsradius pro Skala.
    """

    layer_origins: Dict[int, TimespaceCoordinate]
    compression_radius: Dict[Timescale, float]

    @classmethod
    def default(cls) -> "TimespaceManifold":
        return cls(
            layer_origins={
                0: TimespaceCoordinate(0.0, 0.0, Timescale.MACRO),
                1: TimespaceCoordinate(0.5, 0.5, Timescale.MESO),
                2: TimespaceCoordinate(1.0, 1.5, Timescale.MESO),
                3: TimespaceCoordinate(2.0, 2.5, Timescale.MICRO),
            },
            compression_radius={
                Timescale.MICRO: 2.5,
                Timescale.MESO: 4.0,
                Timescale.MACRO: 6.0,
            },
        )

    def origin_for_depth(self, space_depth: float) -> TimespaceCoordinate:
        layer = min(self.layer_origins.keys(), key=lambda k: abs(k - space_depth))
        return self.layer_origins[layer]

    def geometric_priority(self, coord: TimespaceCoordinate) -> float:
        origin = self.origin_for_depth(coord.space_depth)
        dist = coord.distance_to(origin)
        radius = self.compression_radius.get(coord.timescale, 4.0)
        if dist >= radius:
            return max(0.2, 1.0 - (dist - radius) * 0.12)
        return 1.0 + (radius - dist) * 0.06

    def neighbor_compression(self, tracks: List[Tuple[str, TimespaceCoordinate]]) -> Dict[str, float]:
        """Tracks in dichter Nachbarschaft teilen Kompressionsdruck."""
        pressure: Dict[str, float] = {name: 1.0 for name, _ in tracks}
        for i, (name_a, coord_a) in enumerate(tracks):
            for name_b, coord_b in tracks[i + 1:]:
                if coord_a.distance_to(coord_b) < 1.0:
                    pressure[name_a] *= 0.92
                    pressure[name_b] *= 0.92
        return pressure