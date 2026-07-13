#!/usr/bin/env python3
"""
Heroic Highest Layer (Layer 4) — Generationale Ordnung
Pure logic implementation. No VR. No visuals. No containers.

Load with:
    from highest_layer import load
    hl = load()
"""

from __future__ import annotations
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to integrate with foundation if present (Layer 0)
try:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "heroic-core-foundation"))
    from foundation import check_foundation_gate, FoundationReport
    FOUNDATION_AVAILABLE = True
except Exception:
    FOUNDATION_AVAILABLE = False
    FoundationReport = Any  # type: ignore

# ---------------- Data Models ----------------

@dataclass
class Milestone:
    id: str
    title: str
    description: str = ""
    target_layer: str = "any"
    dependencies: List[str] = field(default_factory=list)
    status: str = "planned"   # planned | in_progress | done | blocked
    evidence: List[str] = field(default_factory=list)
    created: float = field(default_factory=time.time)

    def to_dict(self):
        return asdict(self)

@dataclass
class Snapshot:
    version: str
    timestamp: float
    state: Dict[str, Any]
    checksum: str = ""

    def to_dict(self):
        d = asdict(self)
        return d

@dataclass
class GenerationResult:
    generation: int
    fitness: float
    track_fitness: Dict[str, float]
    improvements: List[str]
    snapshot_id: Optional[str] = None

# ---------------- Core Classes ----------------

class Roadmap:
    """Strategic roadmap management (clean, no visual milestones)."""

    def __init__(self):
        self.version = "1.0"
        self.milestones: Dict[str, Milestone] = {}
        self._seed_default_roadmap()

    def _seed_default_roadmap(self):
        defaults = [
            Milestone("m1", "Establish Layer 0 Foundation", "Immutable base rules + enforcement", "0", [], "done"),
            Milestone("m2", "Implement Highest Layer (Layer 4)", "Roadmap + Generational protocol, ohne VR", "4", ["m1"], "in_progress"),
            Milestone("m3", "Cross-layer Consistency Audit", "Ensure all layers respect Foundation", "any", ["m1", "m2"]),
            Milestone("m4", "Long-term Snapshot & Rollback System", "Reliable generational versioning", "4"),
            Milestone("m5", "Publication Path (Book + Open Reference)", "Clean heroic methodology dissemination", "external", ["m3"]),
        ]
        for m in defaults:
            self.milestones[m.id] = m

    def add_milestone(self, milestone: Milestone):
        self.milestones[milestone.id] = milestone

    def get_active(self) -> List[Milestone]:
        return [m for m in self.milestones.values() if m.status in ("planned", "in_progress")]

    def advance(self, milestone_id: str, status: str = "done"):
        if milestone_id in self.milestones:
            self.milestones[milestone_id].status = status

    def to_dict(self):
        return {
            "version": self.version,
            "milestones": [m.to_dict() for m in self.milestones.values()]
        }

class EvolutionTrack:
    """Single parallel evolution track (pure data + scoring)."""

    def __init__(self, name: str, focus: str):
        self.name = name
        self.focus = focus
        self.history: List[float] = []

    def score(self, context: Dict[str, Any]) -> float:
        # Base fitness from 5-Dim proxy + track-specific signal
        base = context.get("five_dim_fitness", 0.6)
        if self.name == "Technical Core Optimization":
            extra = 0.1 if context.get("traceability", 0) > 0.7 else 0
        elif self.name == "Roadmap & Publishing Strategy":
            extra = 0.15 if context.get("roadmap_progress", 0) > 0.5 else 0
        elif self.name == "Self-Modification Efficiency":
            extra = 0.1 if context.get("recent_improvements", 0) > 0 else 0
        else:
            extra = 0.05
        score = min(1.0, base + extra)
        self.history.append(score)
        return score

class GenerationalEvolutionProtocol:
    """Highest layer evolutionary engine. Lightweight, standalone, ohne VR."""

    DEFAULT_TRACKS = [
        "Technical Core Optimization",
        "Roadmap & Publishing Strategy",
        "Self-Modification Efficiency",
        "Cross-Layer Coherence",
    ]

    def __init__(self, roadmap: Roadmap):
        self.roadmap = roadmap
        self.tracks: Dict[str, EvolutionTrack] = {
            name: EvolutionTrack(name, name) for name in self.DEFAULT_TRACKS
        }
        self.current_generation = 0
        self.snapshots: List[Snapshot] = []
        self.last_fitness: float = 0.5

    def _compute_context(self) -> Dict[str, Any]:
        active = len(self.roadmap.get_active())
        done = len([m for m in self.roadmap.milestones.values() if m.status == "done"])
        total = len(self.roadmap.milestones)
        return {
            "five_dim_fitness": 0.65 + (done / max(1, total)) * 0.25,
            "traceability": 0.8,
            "roadmap_progress": done / max(1, total),
            "recent_improvements": min(3, self.current_generation // 20),
            "generation": self.current_generation,
        }

    def run_cycle(self, generations: int = 100) -> List[GenerationResult]:
        results = []
        for _ in range(generations):
            self.current_generation += 1
            ctx = self._compute_context()

            track_scores = {}
            for name, track in self.tracks.items():
                track_scores[name] = track.score(ctx)

            overall = sum(track_scores.values()) / max(1, len(track_scores))

            improvements = []
            if overall > self.last_fitness + 0.03:
                improvements.append(f"Improved overall fitness to {overall:.3f}")
            if ctx["roadmap_progress"] > 0.6:
                improvements.append("Roadmap advancing — consider promoting next milestone")

            snap_id = None
            if self.current_generation % 50 == 0:
                snap = self._create_snapshot()
                snap_id = snap.version
                self.snapshots.append(snap)

            result = GenerationResult(
                generation=self.current_generation,
                fitness=overall,
                track_fitness=track_scores,
                improvements=improvements,
                snapshot_id=snap_id
            )
            results.append(result)
            self.last_fitness = overall

        return results

    def _create_snapshot(self) -> Snapshot:
        state = {
            "generation": self.current_generation,
            "roadmap": self.roadmap.to_dict(),
            "track_summary": {n: t.history[-5:] for n, t in self.tracks.items()},
        }
        version = f"gen-{self.current_generation}-{uuid.uuid4().hex[:6]}"
        snap = Snapshot(
            version=version,
            timestamp=time.time(),
            state=state
        )
        return snap

    def get_status(self) -> Dict[str, Any]:
        return {
            "current_generation": self.current_generation,
            "last_fitness": round(self.last_fitness, 4),
            "active_milestones": len(self.roadmap.get_active()),
            "snapshots": len(self.snapshots),
            "tracks": list(self.tracks.keys()),
            "foundation_gate_available": FOUNDATION_AVAILABLE,
        }

    def propose_evolution(self) -> Dict[str, Any]:
        """Produce a candidate improvement package (must still pass Foundation + review)."""
        ctx = self._compute_context()
        proposals = []
        if ctx["roadmap_progress"] > 0.75:
            proposals.append("Promote Cross-Layer Coherence milestone and add formal consistency audit module")
        proposals.append("Increase snapshot frequency for critical modules")
        return {
            "generation": self.current_generation,
            "fitness": self.last_fitness,
            "proposals": proposals,
            "note": "All proposals must be validated via Layer 0 foundation gate and 5-Dim review."
        }

# ---------------- Public Loader (the "laden" entrypoint) ----------------

class HighestLayer:
    """Top-level container for the highest layer. What you get when you `load()`."""

    def __init__(self):
        self.roadmap = Roadmap()
        self.protocol = GenerationalEvolutionProtocol(self.roadmap)
        self.loaded_at = time.time()
        self.meta = {
            "name": "Heroic Highest Layer",
            "version": "1.0",
            "mode": "ohne_vr",
            "constraints": ["no_visuals", "no_vr", "no_memes", "pure_logic", "foundation_gated"]
        }

    def load(self) -> "HighestLayer":
        # Idempotent — returns self
        return self

    def status(self) -> Dict[str, Any]:
        s = self.protocol.get_status()
        s.update({"meta": self.meta})
        return s

    def run_generation_cycle(self, generations: int = 100) -> List[Dict[str, Any]]:
        results = self.protocol.run_cycle(generations)
        return [asdict(r) for r in results]

    def propose(self) -> Dict[str, Any]:
        return self.protocol.propose_evolution()

    def get_roadmap(self) -> Dict[str, Any]:
        return self.roadmap.to_dict()

    def create_snapshot(self) -> Dict[str, Any]:
        snap = self.protocol._create_snapshot()
        self.protocol.snapshots.append(snap)
        return snap.to_dict()

def load() -> HighestLayer:
    """Official entry point: 'highest layer ohne vr laden'."""
    hl = HighestLayer()
    return hl.load()


# ---------------- MIT VR SUPPORT ----------------

@dataclass
class VRAsset:
    id: str
    type: str
    path: str
    description: str

class VRAssetManager:
    """Handles VR assets for mit VR mode (references only, no heavy loading here)."""

    def __init__(self):
        self.assets: Dict[str, VRAsset] = {}
        self.base = Path("03_VR_Assets")
        self._load_default_assets()

    def _load_default_assets(self):
        # Reference standard VR assets from the heroic core setup
        self.assets["vr_hero_equirectangular"] = VRAsset(
            "vr_mister_Contributor_hero_equirectangular",
            "equirectangular",
            str(self.base / "vr_mister_Contributor_hero_equirectangular.jpg"),
            "360° base for heroic VR immersion and generational scenes"
        )
        self.assets["evolution_texture"] = VRAsset(
            "heroic_evolution_fractal",
            "texture",
            str(self.base / "heroic_evolution_fractal.jpg"),
            "Visual mapping of fitness/generations in VR space"
        )

    def get(self, asset_id: str) -> Optional[VRAsset]:
        return self.assets.get(asset_id)

    def list_assets(self) -> List[Dict[str, str]]:
        return [{"id": a.id, "type": a.type, "description": a.description} for a in self.assets.values()]


class VRTrack(EvolutionTrack):
    """Visual / VR evolution track (active only in mit VR mode)."""

    def __init__(self):
        super().__init__("VR Visualization & Immersion", "Visual fidelity, asset coherence, immersive mapping of Layer 4 state")

    def score(self, context: Dict[str, Any]) -> float:
        base = super().score(context) if hasattr(super(), 'score') else context.get("five_dim_fitness", 0.6)
        visual_score = context.get("visual_coherence", 0.7)
        asset_usage = 0.8 if context.get("vr_assets_loaded", False) else 0.4
        return min(1.0, (base + visual_score + asset_usage) / 3)


class HighestLayerVR(HighestLayer):
    """Highest Layer loaded mit VR."""

    def __init__(self):
        super().__init__()
        self.vr_assets = VRAssetManager()
        self.protocol.tracks["VR Visualization & Immersion"] = VRTrack()
        self.meta = {
            "name": "Heroic Highest Layer",
            "version": "1.0",
            "mode": "mit_vr",
            "constraints": ["foundation_gated", "vr_assets", "visual_protocol", "logic_plus_visual"],
            "vr_protocol": "VR Visualization Protocol v1.0 (references 03_VR_Assets/)"
        }
        self.vr_active = True

    def get_vr_status(self) -> Dict[str, Any]:
        base = self.status()
        base["vr"] = {
            "assets": self.vr_assets.list_assets(),
            "vr_track_fitness": self.protocol.tracks.get("VR Visualization & Immersion").history[-1] if self.protocol.tracks.get("VR Visualization & Immersion").history else None,
            "visual_layer": "active (overlay + equirectangular mapping)"
        }
        return base

    def render_roadmap_visual(self) -> str:
        """Simple text-based visual of roadmap for VR context (can be fed to real renderer)."""
        lines = ["VR ROADMAP VISUAL (Layer 4):"]
        for m in self.roadmap.milestones.values():
            status_icon = "✓" if m.status == "done" else "◉" if m.status == "in_progress" else "○"
            lines.append(f"  {status_icon} {m.title} [{m.target_layer}]")
        lines.append("\n[VR] Map these to spherical nodes in 03_VR_Assets scenes.")
        return "\n".join(lines)

    def create_vr_snapshot(self) -> Dict[str, Any]:
        snap = self.create_snapshot()
        snap["vr"] = {
            "assets_referenced": list(self.vr_assets.assets.keys()),
            "visual_fitness": self.protocol.tracks.get("VR Visualization & Immersion").history[-1] if self.protocol.tracks.get("VR Visualization & Immersion").history else 0.65
        }
        return snap


def load_vr() -> HighestLayerVR:
    """Official entry point: 'highest layer mit vr laden'."""
    hl = HighestLayerVR()
    return hl

# ---------------- CLI ----------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Heroic Highest Layer (ohne VR)")
    parser.add_argument("--load", action="store_true", help="Load and print status")
    parser.add_argument("--cycle", type=int, default=0, help="Run N generations")
    parser.add_argument("--snapshot", action="store_true", help="Create a snapshot now")
    parser.add_argument("--propose", action="store_true", help="Generate evolution proposals")
    parser.add_argument("--vr", action="store_true", help="Load with VR (mit vr)")
    args = parser.parse_args()

    hl = load_vr() if args.vr else load()

    if args.load or (not args.cycle and not args.snapshot and not args.propose):
        print("=== Heroic Highest Layer (Layer 4) ===")
        status = hl.get_vr_status() if hasattr(hl, 'get_vr_status') else hl.status()
        print(json.dumps(status, indent=2, default=str))

    if args.cycle > 0:
        mode = "mit VR" if getattr(hl, 'vr_active', False) else "ohne VR"
        print(f"\nRunning {args.cycle} generations ({mode})...")
        results = hl.run_generation_cycle(args.cycle)
        print(f"Final fitness: {results[-1]['fitness']:.4f}")
        if results[-1].get("improvements"):
            print("Improvements:", results[-1]["improvements"])

    if args.snapshot:
        snap = hl.create_snapshot()
        print("\nSnapshot created:", snap["version"])

    if args.propose:
        p = hl.propose()
        print("\nEvolution proposals:")
        for prop in p.get("proposals", []):
            print(" -", prop)

if __name__ == "__main__":
    main()
