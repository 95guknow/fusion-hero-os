# geisterjagd_banach_viz.py — Live-Visualisierung Geisterjagd + Banach-Kontraktion
#
# Geisterjagd: latente Aktivierungen (Heuristik) → manifeste Emergenz (Phoenix_Mode)
# Banach:      s_{n+1} = s* + λ(s_n - s*),  λ < 1  ⇒  d_n → 0

from __future__ import annotations

import math
import os
import random
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional

_rng = random.Random(7)


@dataclass
class Ghost:
    id: str
    latent_x: float
    latent_y: float
    activation: float
    manifest: bool = False
    manifest_x: float = 0.5
    manifest_y: float = 0.5
    age: int = 0
    label: str = ""


class GeisterjagdBanachViz:
    """Heuristik-gesteuerte Emergenz + Banach-Kontraktion zum Fixpunkt Z*."""

    def __init__(self, lambda_contract: float = 0.74, ghost_capacity: int = 24) -> None:
        self.lambda_contract = max(0.1, min(0.99, lambda_contract))
        self.s_star = [0.0, 0.0]
        self.s_n = [2.2, 1.6]
        self.distances: Deque[float] = deque(maxlen=120)
        self.lambda_history: Deque[float] = deque(maxlen=120)
        self.ghosts: List[Ghost] = []
        self.ghost_capacity = ghost_capacity
        self.emergence_log: Deque[Dict[str, Any]] = deque(maxlen=40)
        self.heuristic_grid: List[List[float]] = [[0.0] * 8 for _ in range(8)]
        self.tick_count = 0
        self.emergence_total = 0
        self.heuristic_score = 0.5
        self.emergence_rate = 0.0
        self.manifest_threshold = 0.62
        self._last_ts = time.time()

        for _ in range(6):
            self._spawn_ghost()

    def _spawn_ghost(self) -> Ghost:
        g = Ghost(
            id=uuid.uuid4().hex[:6],
            latent_x=_rng.uniform(0.08, 0.92),
            latent_y=_rng.uniform(0.08, 0.42),
            activation=_rng.uniform(0.05, 0.35),
            label=_rng.choice(["prompt", "latent", "session", "trace", "phoenix"]),
        )
        self.ghosts.append(g)
        if len(self.ghosts) > self.ghost_capacity:
            self.ghosts.pop(0)
        return g

    def _distance(self) -> float:
        return math.hypot(self.s_n[0] - self.s_star[0], self.s_n[1] - self.s_star[1])

    def _heuristic_field_update(self, hints: Dict[str, Any]) -> None:
        """8×8 Heuristik-Feld aus System-Signalen (Events, Queue, CPU)."""
        base = float(hints.get("heuristic_score", self.heuristic_score))
        events = float(hints.get("event_rate", 0.3))
        queue = float(hints.get("queue_pressure", 0.2))
        for r in range(8):
            for c in range(8):
                wave = math.sin((self.tick_count + r * 0.7 + c * 0.5) * 0.18)
                cell = 0.35 * base + 0.25 * events + 0.15 * queue + 0.12 * wave
                self.heuristic_grid[r][c] = max(0.0, min(1.0, cell))
        self.heuristic_score = base

    def _banach_step(self, hints: Dict[str, Any]) -> None:
        lam = float(hints.get("lambda", self.lambda_contract))
        lam = max(0.15, min(0.95, lam))
        self.lambda_contract = lam

        # Heuristik-Störung (Emergenz-Impuls) vor Kontraktion
        noise = float(hints.get("heuristic_noise", 0.04))
        hx = _rng.uniform(-noise, noise) * (1.0 + hints.get("event_rate", 0.2))
        hy = _rng.uniform(-noise, noise) * (1.0 + hints.get("queue_pressure", 0.2))

        sx, sy = self.s_star
        nx = sx + lam * (self.s_n[0] - sx) + hx
        ny = sy + lam * (self.s_n[1] - sy) + hy
        self.s_n = [nx, ny]

        d = self._distance()
        self.distances.append(round(d, 5))
        self.lambda_history.append(round(lam, 4))

    def _geisterjagd_step(self, hints: Dict[str, Any]) -> int:
        emerged = 0
        threshold = self.manifest_threshold - 0.08 * float(hints.get("event_rate", 0.2))
        threshold = max(0.45, min(0.85, threshold))

        for g in self.ghosts:
            g.age += 1
            r = int(g.latent_y * 7.99)
            c = int(g.latent_x * 7.99)
            field_val = self.heuristic_grid[r][c]
            # Heuristik-Akkumulation → Emergenz
            delta = 0.06 * field_val + 0.03 * self.heuristic_score
            if hints.get("recent_peer_review"):
                delta += 0.04
            if hints.get("recent_self_mod"):
                delta += 0.05
            g.activation = max(0.0, min(1.0, g.activation + delta - 0.012))

            if not g.manifest and g.activation >= threshold:
                g.manifest = True
                g.manifest_x = 0.15 + 0.7 * field_val
                g.manifest_y = 0.55 + _rng.uniform(0.0, 0.38)
                emerged += 1
                self.emergence_total += 1
                self.emergence_log.appendleft({
                    "ghost_id": g.id,
                    "activation": round(g.activation, 3),
                    "label": g.label,
                    "tick": self.tick_count,
                    "ts": time.time(),
                })

        if _rng.random() < 0.18 + 0.12 * hints.get("event_rate", 0.2):
            self._spawn_ghost()

        window = max(1, min(20, len(self.emergence_log)))
        self.emergence_rate = emerged / window if emerged else max(0.0, self.emergence_rate * 0.92)
        return emerged

    def tick(self, hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        hints = dict(hints or {})
        self.tick_count += 1
        self._heuristic_field_update(hints)
        self._banach_step(hints)
        emerged = self._geisterjagd_step(hints)
        self._last_ts = time.time()

        return {
            "emerged": emerged,
            "distance": self.distances[-1] if self.distances else self._distance(),
            "lambda": self.lambda_contract,
            "heuristic_score": round(self.heuristic_score, 4),
            "ghosts_manifest": sum(1 for g in self.ghosts if g.manifest),
            "ghosts_latent": sum(1 for g in self.ghosts if not g.manifest),
        }

    def snapshot(self) -> Dict[str, Any]:
        d = self._distance()
        return {
            "module": "geisterjagd_banach_viz",
            "formula_banach": "s_{n+1} = s* + λ(s_n − s*)",
            "formula_geisterjagd": "latente Aktivierung → manifest (Heuristik-Feld)",
            "lambda": round(self.lambda_contract, 4),
            "lambda_ok": self.lambda_contract < 1.0,
            "s_star": list(self.s_star),
            "s_n": [round(v, 5) for v in self.s_n],
            "distance": round(d, 5),
            "distances": list(self.distances),
            "lambda_history": list(self.lambda_history),
            "heuristic_score": round(self.heuristic_score, 4),
            "emergence_rate": round(self.emergence_rate, 4),
            "emergence_total": self.emergence_total,
            "manifest_threshold": round(self.manifest_threshold, 3),
            "tick": self.tick_count,
            "ts": self._last_ts,
            "heuristic_grid": self.heuristic_grid,
            "ghosts": [
                {
                    "id": g.id,
                    "latent": [round(g.latent_x, 4), round(g.latent_y, 4)],
                    "manifest_pos": [round(g.manifest_x, 4), round(g.manifest_y, 4)] if g.manifest else None,
                    "activation": round(g.activation, 4),
                    "manifest": g.manifest,
                    "age": g.age,
                    "label": g.label,
                }
                for g in self.ghosts
            ],
            "emergence_log": list(self.emergence_log)[:12],
            "orbit_trail": self._orbit_trail(),
        }

    def _orbit_trail(self, n: int = 48) -> List[List[float]]:
        """Banach-Orbit für Canvas (rückwärts simuliert aus aktuellem Zustand)."""
        trail: List[List[float]] = []
        sx, sy = self.s_star
        x, y = self.s_n[0], self.s_n[1]
        lam = self.lambda_contract
        for _ in range(n):
            trail.append([round(x, 4), round(y, 4)])
            x = sx + (x - sx) / lam if lam > 0.01 else sx
            y = sy + (y - sy) / lam if lam > 0.01 else sy
        return list(reversed(trail))


_viz: Optional[GeisterjagdBanachViz] = None


def get_viz() -> GeisterjagdBanachViz:
    global _viz
    if _viz is None:
        try:
            lam = float(os.getenv("FUSION_BANACH_LAMBDA", "0.74"))
        except Exception:
            lam = 0.74
        _viz = GeisterjagdBanachViz(lambda_contract=lam)
    return _viz


def build_hints_from_system(
    *,
    event_count: int = 0,
    recent_types: Optional[List[str]] = None,
    queue_len: int = 0,
    cpu_pct: float = 50.0,
    agent_blocked: int = 0,
) -> Dict[str, Any]:
    """Leitet Live-Heuristik aus Dashboard-Systemzustand ab."""
    recent = recent_types or []
    event_rate = min(1.0, event_count / 80.0)
    queue_pressure = min(1.0, queue_len / 12.0)
    cpu_factor = min(1.0, cpu_pct / 100.0)

    heuristic_noise = 0.02 + 0.06 * event_rate + 0.03 * queue_pressure
    heuristic_score = 0.35 + 0.25 * (1.0 - cpu_factor) + 0.2 * event_rate
    if agent_blocked > 0:
        heuristic_score -= 0.05 * agent_blocked

    lam = 0.82 - 0.12 * event_rate - 0.08 * queue_pressure
    lam = max(0.55, min(0.88, lam))

    return {
        "event_rate": event_rate,
        "queue_pressure": queue_pressure,
        "heuristic_noise": heuristic_noise,
        "heuristic_score": max(0.1, min(0.95, heuristic_score)),
        "lambda": lam,
        "recent_peer_review": "peer_review" in recent,
        "recent_self_mod": "self_mod_proposal" in recent,
    }


