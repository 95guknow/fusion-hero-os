"""
Psycholysis Breakthrough Trigger - v8.1

Optionaler, versionierbarer Trigger fuer dialektische Aufloesung
im CriticalMetaAnalysisCoreModule.

v8.1 setzt die GitHub-Updates vom 2026-07-05 um (docs/v8/architecture/
FULL_OS_Themenfelder_Integration_April_Mai_Juni_v8.md, Roadmap Punkt 2 +
GROK_DEEP_RESEARCH_EXPORT Abschnitt 3):
  * Echter ISO-Timestamp statt "now"-Platzhalter.
  * VERPFLICHTENDE somatische Integrationsphase: eine Session kann erst
    abgeschlossen werden, wenn alle Checklist-Punkte geloggt sind
    (Registry-Claim PSYCHOLYSE-SOMATIC-PFLICHT, per Test verankert).

EHRLICHKEITS-HINWEIS: Dies ist eine Logging-/Protokollstruktur. Die
Checklist-Punkte stammen aus der Integrationsliteratur, die der Grok-Export
zitiert (somatic tracking, movement, breathwork, nature connection); das
Modul erhebt keine Wirksamkeits-Claims und ersetzt keine therapeutische
Begleitung.

Teil der 02_architecture / 04_execution Schicht.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

# Somatische Integrations-Checklist (Quelle: Grok-Export Abschnitt 3 —
# Gorman et al., Bourzat & Hunter, THRIVE-Modell).
SOMATIC_CHECKLIST = (
    "somatic_tracking",    # Koerperwahrnehmung / Interozeption protokollieren
    "movement",            # Bewegung / Fitness
    "breathwork",          # Atemarbeit
    "nature_connection",   # Naturkontakt
)


class PsycholysisTrigger:
    """Trigger fuer kontrollierte Psycholyse-Prozesse mit Pflicht-Somatikphase."""

    def __init__(self, threshold: float = 0.75):
        self.threshold = threshold
        self.history = []

    def should_trigger(self, coherence_score: float, load_level: float) -> bool:
        """Entscheidet, ob eine Psycholyse ausgeloest werden sollte."""
        return coherence_score < self.threshold or load_level > 0.8

    def trigger(self, context: dict) -> Dict[str, Any]:
        """Startet eine Session inkl. offener somatischer Integrationsphase."""
        session = {
            "triggered": True,
            "context": context,
            "timestamp": datetime.now().replace(microsecond=0).isoformat(),
            "somatic_phase": {item: False for item in SOMATIC_CHECKLIST},
            "somatic_log": [],
            "completed_at": None,
        }
        self.history.append(session)
        return session

    def log_somatic_practice(self, session: Dict[str, Any], item: str,
                             note: str = "") -> None:
        """Einen Checklist-Punkt als durchgefuehrt loggen (mit Zeit + Notiz)."""
        if item not in session["somatic_phase"]:
            raise ValueError(f"Unbekannter Checklist-Punkt: {item!r} "
                             f"(erlaubt: {', '.join(SOMATIC_CHECKLIST)})")
        session["somatic_phase"][item] = True
        session["somatic_log"].append({
            "item": item,
            "note": note,
            "ts": datetime.now().replace(microsecond=0).isoformat(),
        })

    def complete_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Session abschliessen — NUR moeglich, wenn die somatische Phase
        vollstaendig ist (verpflichtend laut v8-Integrationsdokument)."""
        missing = [k for k, done in session["somatic_phase"].items() if not done]
        if missing:
            raise ValueError(
                "Somatische Integrationsphase unvollstaendig — offene Punkte: "
                + ", ".join(missing))
        session["completed_at"] = datetime.now().replace(microsecond=0).isoformat()
        return session
