# -*- coding: utf-8 -*-
"""
entwicklungsquant_bus.py — HAUPTKNOTEN: Interkonnektivität der Knoten via Entwicklungsquanten
=============================================================================================
Verbindet die einzelnen Knoten (automation_scheduler, conversation_context,
qubo-cache, faden_store, resource_coupler, ...) zu einem ko-entwickelnden Netz.
Der Austausch passiert NICHT kontinuierlich, sondern in diskreten Einheiten:
ENTWICKLUNGSQUANTEN — die kleinste Einheit von Ko-Entwicklung, die von Knoten zu
Knoten propagiert.

Kernidee (ehrlich, kein Quantenmechanik-Überclaim):
  * Ein Entwicklungsquant trägt eine gebündelte, quantisierte "Entwicklungs-
    Magnitude" von einem Quell- zu Ziel-Knoten (typisiert: strength_update,
    plan_change, cache_hit, tier_change, resource_pressure, ...).
  * Empfängt ein Knoten ein Quant, reagiert er (Kopplungsregeln) mit eigenen
    Quanten kleinerer Magnitude (Gewicht < 1). So propagiert ein Anstoß durchs
    Netz und die Knoten ko-entwickeln sich.
  * "Quant" = diskret: Magnituden werden auf Vielfache eines Minimal-Quants
    gerundet; unter einem Quant propagiert NICHTS mehr (keine Endlos-Ausbreitung).
  * ENTWICKLUNGS-FIXPUNKT: das Netz konvergiert garantiert, weil (a) Kopplung < 1
    -> Kontraktion (Banach) und (b) Quantisierung -> endliche Terminierung.
    Divergenz (Spektralradius >= 1) wird erkannt und gemeldet, nicht verschleiert.

"Quant" ist eine DISKRETE-EINHEIT-Metapher (angelehnt an die quantisierte
Kognition der QPT-Module des Repos), NICHT wörtliche Quantenmechanik.

Aufruf:  python entwicklungsquant_bus.py     # Demo: 5 Knoten ko-entwickeln bis Fixpunkt
"""
from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple


# --------------------------------------------------------------------------- #
#  Das Entwicklungsquant — diskrete Einheit der Ko-Entwicklung                 #
# --------------------------------------------------------------------------- #
@dataclass
class Entwicklungsquant:
    quant_id: str
    source: str                 # Quell-Knoten
    target: str                 # Ziel-Knoten ('*' = Broadcast)
    quant_type: str             # strength_update | plan_change | cache_hit | tier_change | resource_pressure | ...
    magnitude: float            # quantisierte Entwicklungs-Magnitude
    layer: int = 0              # Layer 0-6 (Repo-Schichtenkonzept)
    hops: int = 0               # wie viele Knoten schon durchlaufen
    ts: float = field(default_factory=time.time)
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quant_id": self.quant_id, "source": self.source, "target": self.target,
            "quant_type": self.quant_type, "magnitude": round(self.magnitude, 4),
            "layer": self.layer, "hops": self.hops,
        }


def quantize(magnitude: float, quant_size: float) -> float:
    """Auf Vielfache von quant_size runden (diskrete Entwicklungs-Einheit)."""
    if quant_size <= 0:
        return magnitude
    return round(magnitude / quant_size) * quant_size


# (on_type, emit_type, to_node['*'=broadcast], weight)  — eine Kopplungsregel
Reaction = Tuple[str, str, str, float]


@dataclass
class NodeSpec:
    name: str
    reactions: List[Reaction] = field(default_factory=list)
    # Live-Knoten: statt deklarativer Reaktionen ein echter Handler, der reale
    # Methoden aufruft und selbst bus.emit(...) mit realen Magnituden macht.
    handler: Optional[Callable[["EntwicklungsquantBus", "Entwicklungsquant"], None]] = None
    live: bool = False


# --------------------------------------------------------------------------- #
#  Der Interkonnektivitäts-Bus                                                 #
# --------------------------------------------------------------------------- #
class EntwicklungsquantBus:
    def __init__(self, quant_size: float = 0.25, min_quant: float = 0.25, max_ticks: int = 500) -> None:
        self.quant_size = quant_size
        self.min_quant = max(min_quant, quant_size)  # unter einem Quant: kein Transport
        self.max_ticks = max_ticks
        self.nodes: Dict[str, NodeSpec] = {}
        self.queue: Deque[Entwicklungsquant] = deque()
        self.log: List[Entwicklungsquant] = []
        self.received: Dict[str, float] = defaultdict(float)   # Entwicklung je Knoten
        self.edges: Dict[Tuple[str, str], float] = defaultdict(float)  # (src,dst)->Σweight (Konnektivität)

    def register(self, name: str, reactions: Optional[List[Reaction]] = None,
                 handler: Optional[Callable] = None, live: bool = False) -> None:
        self.nodes[name] = NodeSpec(name=name, reactions=list(reactions or []), handler=handler, live=live)
        for (on_t, emit_t, to, w) in (reactions or []):
            # Kante src=name -> dst (aggregierte Kopplung) für die Konnektivitäts-Metrik
            targets = [to] if to != "*" else [n for n in self.nodes if n != name]
            for d in targets:
                self.edges[(name, d)] += w

    def deregister(self, name: str) -> bool:
        """Knoten abmelden: entfernt Knoten + seine Kanten aus dem Netz."""
        if name not in self.nodes:
            return False
        del self.nodes[name]
        for key in [k for k in self.edges if k[0] == name or k[1] == name]:
            del self.edges[key]
        return True

    def registered(self) -> List[str]:
        return sorted(self.nodes.keys())

    def reset(self) -> None:
        """Metriken/Log/Queue zurücksetzen (Netzstruktur + Knoten bleiben)."""
        self.queue.clear()
        self.log.clear()
        self.received.clear()

    def emit(self, source: str, target: str, quant_type: str,
             magnitude: float, layer: int = 0, payload: Optional[Dict[str, Any]] = None) -> Optional[Entwicklungsquant]:
        mag = quantize(magnitude, self.quant_size)
        if mag < self.min_quant:   # unter einem Entwicklungsquant -> propagiert nicht
            return None
        q = Entwicklungsquant(
            quant_id=uuid.uuid4().hex[:8], source=source, target=target,
            quant_type=quant_type, magnitude=mag, layer=layer, payload=payload or {},
        )
        self.queue.append(q)
        return q

    def _deliver(self, q: Entwicklungsquant) -> List[Entwicklungsquant]:
        """Zustellen + Reaktionen des Ziel-Knotens erzeugen (kleinere Quanten)."""
        targets = [q.target] if q.target != "*" else [n for n in self.nodes if n != q.source]
        produced: List[Entwicklungsquant] = []
        for tname in targets:
            node = self.nodes.get(tname)
            if not node:
                continue
            self.received[tname] += q.magnitude
            if node.handler is not None:
                # Live-Knoten: echter Handler ruft reale Methoden + emittiert selbst.
                try:
                    node.handler(self, q)
                except Exception:
                    pass
                continue
            for (on_t, emit_t, to, w) in node.reactions:
                if on_t != q.quant_type:
                    continue
                child = self.emit(tname, to, emit_t, q.magnitude * w, layer=q.layer, payload={"via": q.quant_id})
                if child is not None:
                    child.hops = q.hops + 1
                    produced.append(child)
        return produced

    def tick(self) -> float:
        """Ein Entwicklungsschritt: alle aktuell anstehenden Quanten zustellen.
        Gibt die in diesem Tick zugestellte Gesamt-Magnitude zurück (Entwicklungs-Energie)."""
        batch = list(self.queue)
        self.queue.clear()
        energy = 0.0
        for q in batch:
            energy += q.magnitude
            self.log.append(q)
            self._deliver(q)
        return energy

    def run_until_fixpoint(self, eps: float = 1e-9) -> Dict[str, Any]:
        """Ticken bis Entwicklungs-Fixpunkt (keine Quanten mehr) oder max_ticks."""
        trace: List[float] = []
        t = 0
        while self.queue and t < self.max_ticks:
            t += 1
            e = self.tick()
            trace.append(round(e, 4))
        return {
            "fixpunkt_erreicht": len(self.queue) == 0,
            "ticks": t,
            "entwicklungs_energie_gesamt": round(sum(trace), 4),
            "energie_pro_tick": trace,
            "quanten_total": len(self.log),
            "entwicklung_je_knoten": {k: round(v, 3) for k, v in sorted(self.received.items(), key=lambda x: -x[1])},
        }

    # --- Konnektivitäts-/Stabilitäts-Analyse ---
    def connectivity(self) -> Dict[str, Any]:
        import numpy as np

        names = sorted(self.nodes.keys())
        idx = {n: i for i, n in enumerate(names)}
        M = np.zeros((len(names), len(names)), dtype=np.float64)
        for (s, d), w in self.edges.items():
            if s in idx and d in idx:
                M[idx[s], idx[d]] += w
        eig = np.abs(np.linalg.eigvals(M)) if len(names) else np.array([0.0])
        spectral_radius = float(np.max(eig)) if len(eig) else 0.0
        n = len(names)
        possible = n * (n - 1)
        density = (sum(1 for (s, d) in self.edges if s != d) / possible) if possible else 0.0
        return {
            "knoten": names,
            "kanten": len(self.edges),
            "dichte": round(density, 3),
            "spektralradius": round(spectral_radius, 4),
            "kontraktion": spectral_radius < 1.0,  # <1 => Ko-Entwicklung konvergiert (Banach)
            "hinweis": "Spektralradius < 1 => Netz ist kontrahierend => Entwicklungs-Fixpunkt garantiert.",
        }


# ==================================================================
if __name__ == "__main__":
    import json

    print("=" * 74)
    print("  HAUPTKNOTEN: Interkonnektivität der Knoten via Entwicklungsquanten")
    print("=" * 74)

    bus = EntwicklungsquantBus(quant_size=0.25, min_quant=0.25)

    # Die realen Knoten dieser Session + ihre Kopplungsregeln (Reaktionen).
    # Gewichte < 1 -> Kontraktion. Ein Anstoß entwickelt das ganze Netz mit, klingt ab.
    bus.register("resource_coupler", [
        ("resource_pressure", "cost_update", "automation_scheduler", 0.6),
    ])
    bus.register("automation_scheduler", [
        ("resource_pressure", "plan_change", "*", 0.45),
        ("cost_update", "plan_change", "conversation_context", 0.4),
        ("strength_update", "plan_change", "faden_store", 0.35),
    ])
    bus.register("conversation_context", [
        ("plan_change", "strength_update", "automation_scheduler", 0.4),
        ("plan_change", "strength_update", "faden_store", 0.3),
        ("tier_change", "strength_update", "automation_scheduler", 0.3),
    ])
    bus.register("qubo_cache", [
        ("plan_change", "cache_hit", "automation_scheduler", 0.35),
    ])
    bus.register("faden_store", [
        ("strength_update", "tier_change", "conversation_context", 0.35),
    ])

    conn = bus.connectivity()
    print("\n[KONNEKTIVITÄT]")
    print(f"  Knoten={len(conn['knoten'])}  Kanten={conn['kanten']}  Dichte={conn['dichte']}")
    print(f"  Spektralradius={conn['spektralradius']}  Kontraktion={conn['kontraktion']}")
    print(f"  -> {conn['hinweis']}")

    # Anstoß: ein Ressourcendruck-Quant startet die Ko-Entwicklung
    print("\n[ANSTOSS] resource_coupler emittiert 'resource_pressure' (Magnitude 8.0)")
    bus.emit("resource_coupler", "*", "resource_pressure", magnitude=8.0, layer=3)

    res = bus.run_until_fixpoint()
    print("\n[KO-ENTWICKLUNG bis Entwicklungs-Fixpunkt]")
    print(f"  Fixpunkt erreicht: {res['fixpunkt_erreicht']} nach {res['ticks']} Ticks")
    print(f"  Entwicklungs-Energie gesamt: {res['entwicklungs_energie_gesamt']}  "
          f"(Quanten insgesamt: {res['quanten_total']})")
    print(f"  Energie pro Tick (klingt ab): {res['energie_pro_tick']}")
    print(f"  Entwicklung je Knoten: {json.dumps(res['entwicklung_je_knoten'], ensure_ascii=False)}")

    # Ehrliche Gegenprobe: zu starke Kopplung (Zyklus-Radius >= 1) DIVERGIERT.
    print("\n[GEGENPROBE] Kopplung künstlich verstärkt (1.1er-Zyklus) -> Spektralradius >= 1?")
    bus2 = EntwicklungsquantBus()
    bus2.register("A", [("x", "y", "B", 1.1)])
    bus2.register("B", [("y", "x", "A", 1.1)])
    c2 = bus2.connectivity()
    print(f"  Spektralradius={c2['spektralradius']}  Kontraktion={c2['kontraktion']} "
          f"-> {'konvergiert' if c2['kontraktion'] else 'DIVERGIERT (Kriterium greift, wird ehrlich geflaggt)'}")
    print("=" * 74)
