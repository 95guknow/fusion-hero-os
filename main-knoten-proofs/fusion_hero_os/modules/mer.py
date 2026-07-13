"""MERModule — Meaningful-Eudaimonia-Ratio-Index (projekt-interne Metrik).

"MER-Index" ist eine selbst definierte, projektinterne Kennzahl (keine
etablierte externe Größe) zur groben Selbsteinschätzung des Systemzustands
über drei dokumentierte Komponenten. ``optimize()`` ist eine einfache
Greedy-Priorisierung ("wo lohnt sich Verbesserung am meisten"), keine
Behauptung über reale Optimalität.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fusion_hero_os.core.base_module import BaseModule

#: (Komponentenname, Gewicht). Werte werden 0..1 erwartet.
DEFAULT_COMPONENTS: List[Tuple[str, float]] = [
    ("stability", 0.4),
    ("capacity", 0.3),
    ("alignment", 0.3),
]


class MERModule(BaseModule):
    """``process(payload)`` erwartet ``{"values": {komponente: 0..1, ...}}``
    und liefert den gewichteten MER-Index plus Komponenten-Aufschlüsselung.
    """

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        values = payload.get("values", {})
        components = [
            {"name": name, "weight": weight, "value": _clamp01(float(values.get(name, 0.0)))}
            for name, weight in DEFAULT_COMPONENTS
        ]
        weight_sum = sum(c["weight"] for c in components)
        index = sum(c["weight"] * c["value"] for c in components) / weight_sum if weight_sum else 0.0
        return {"mer_index": round(index, 4), "components": components}

    def optimize(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Priorisiert Komponenten nach ``weight * (1 - value)`` (Gewicht mal
        verbleibendem Spielraum) — die Komponente mit dem größten erwarteten
        Hebel auf den Gesamtindex steht zuerst. Reine Priorisierungsheuristik,
        kein Beweis eines optimalen Ergebnisses.
        """
        payload = payload or {}
        values = payload.get("values", {})
        ranked = []
        for name, weight in DEFAULT_COMPONENTS:
            value = _clamp01(float(values.get(name, 0.0)))
            headroom = 1.0 - value
            ranked.append({
                "name": name,
                "value": value,
                "headroom": round(headroom, 4),
                "priority": round(weight * headroom, 4),
            })
        ranked.sort(key=lambda r: r["priority"], reverse=True)
        return {"priority_order": ranked}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
