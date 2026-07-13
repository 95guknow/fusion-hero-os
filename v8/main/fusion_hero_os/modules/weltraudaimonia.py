"""WeltraudaimoniaModule — projekt-interne Entscheidungs-Bewertungslinse.

WICHTIG: Dies ist eine In-App-Heuristik zur Priorisierung von Entscheidungen
innerhalb dieses Projekts — keine Behauptung über reale ethische Autorität,
Wirkung außerhalb der Anwendung oder objektive moralische Wahrheit. Der Name
("weltraum-/kosmisch skaliert") ist reine Produkt-/Framing-Sprache für eine
gewichtete Mehrkriterien-Bewertung, keine technische oder normative Aussage.

Die vier Standard-Achsen sind absichtlich einfach und überschreibbar
(``payload["weights"]``), damit die Metrik nachvollziehbar bleibt statt eine
Blackbox zu sein.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from fusion_hero_os.core.base_module import BaseModule

#: (Achsenname, Default-Gewicht, Kurzbeschreibung). Werte werden 0..1 erwartet.
DEFAULT_AXES: List[Tuple[str, float, str]] = [
    ("stakeholder_breadth", 0.25, "Wie viele/verschiedene Betroffene hat die Entscheidung?"),
    ("reversibility", 0.25, "Wie leicht ist sie rückgängig zu machen? (1 = leicht reversibel)"),
    ("time_horizon", 0.25, "Wie langfristig wirkt sie? (1 = sehr langfristig)"),
    ("evidence_quality", 0.25, "Wie gut ist sie evidenzbasiert? (1 = starke Evidenz)"),
]


class WeltraudaimoniaModule(BaseModule):
    """``process(payload)`` erwartet ``{"scores": {achse: 0..1, ...}, "weights": {...}?}``
    und liefert einen gewichteten Gesamtscore plus Achsen-Aufschlüsselung.
    """

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        scores = payload.get("scores", {})
        weight_overrides = payload.get("weights", {})

        axes_result = []
        weighted_total = 0.0
        weight_sum = 0.0
        for name, default_weight, description in DEFAULT_AXES:
            weight = float(weight_overrides.get(name, default_weight))
            value = _clamp01(float(scores.get(name, 0.0)))
            axes_result.append(
                {"name": name, "weight": weight, "value": value, "description": description}
            )
            weighted_total += weight * value
            weight_sum += weight

        final_score = weighted_total / weight_sum if weight_sum else 0.0
        return {
            "weltraudaimonia_score": round(final_score, 4),
            "axes": axes_result,
            "disclaimer": (
                "Projekt-interne heuristische Priorisierungsmetrik. "
                "Keine Aussage über reale ethische Autorität oder Wirkung."
            ),
        }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
