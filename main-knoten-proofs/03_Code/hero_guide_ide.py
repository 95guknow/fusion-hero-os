# -*- coding: utf-8 -*-
"""
HERO-GUIDE: Die Geltungs-Werkbank und Schnittstelle des Kerns mit sich selbst.
Modul zur Projektions-Auflösung und Verhinderung epistemischer Inflation.
"""
from __future__ import annotations

import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class GeltungsKategorie(Enum):
    """Die fünf epistemischen Kategorien zur Markierung von Aussagen."""
    SATZ = "Satz (bewiesen)"
    BEDINGT = "Bedingt (Beweis ausstehend / Parameterabhängig)"
    MODELL = "Modell (Heuristische Verortung)"
    FRAGMENT = "Fragment (Unfertiges Konzept)"
    METAPHER_ALS_BEWEIS = "Metapher-als-Beweis (Autorität ohne Prämisse)"


_KATEGORIE_MAP = {k.name: k for k in GeltungsKategorie}
_KATEGORIE_VALUE_MAP = {k.value: k for k in GeltungsKategorie}


def parse_kategorie(name_or_value: str) -> GeltungsKategorie:
    key = (name_or_value or "").strip()
    if key in _KATEGORIE_MAP:
        return _KATEGORIE_MAP[key]
    if key in _KATEGORIE_VALUE_MAP:
        return _KATEGORIE_VALUE_MAP[key]
    return GeltungsKategorie.FRAGMENT


class Behauptung:
    def __init__(
        self,
        text: str,
        suggerierte_kategorie: GeltungsKategorie,
        praemissen: Optional[List[str]] = None,
    ):
        self.text = text
        self.suggerierte_kategorie = suggerierte_kategorie
        self.praemissen = praemissen if praemissen else []
        self.wahre_kategorie: Optional[GeltungsKategorie] = None
        self.aufgeloest = False
        self.kommentar = ""

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "suggerierte_kategorie": self.suggerierte_kategorie.name,
            "suggerierte_kategorie_label": self.suggerierte_kategorie.value,
            "wahre_kategorie": self.wahre_kategorie.name if self.wahre_kategorie else None,
            "wahre_kategorie_label": self.wahre_kategorie.value if self.wahre_kategorie else None,
            "praemissen": list(self.praemissen),
            "aufgeloest": self.aufgeloest,
            "kommentar": self.kommentar,
        }


class HeroGuideWorkbench:
    """Geltungs-Werkbank — dreistufige Projektions-Auflösung vor Graph-Persistenz."""

    def __init__(self, knowledge_graph=None):
        self.knowledge_graph = knowledge_graph
        self.audit_log: List[dict] = []

    def projektions_aufloesung(
        self,
        behauptung: Behauptung,
        praemissen_erfuellt: bool,
        fehlende_praemisse: str = "",
    ) -> Behauptung:
        """
        1. Die Projektion benennen.
        2. Die Prämissen prüfen.
        3. Zurücknehmen und neu klassifizieren.
        """
        projektion = behauptung.suggerierte_kategorie

        if projektion == GeltungsKategorie.SATZ:
            if not praemissen_erfuellt:
                behauptung.wahre_kategorie = GeltungsKategorie.BEDINGT
                behauptung.kommentar = (
                    f"Projektion aufgelöst: Autorität als 'Satz' nicht gedeckt. "
                    f"Fehlende Prämisse: {fehlende_praemisse or 'unbekannt'}."
                )
            else:
                behauptung.wahre_kategorie = GeltungsKategorie.SATZ
                behauptung.kommentar = "Beweis bestätigt. Prämisse deckt die Aussage."

        elif projektion == GeltungsKategorie.METAPHER_ALS_BEWEIS:
            behauptung.wahre_kategorie = GeltungsKategorie.FRAGMENT
            behauptung.kommentar = "Scheinprojektion aufgelöst. Reduziert auf Metapher/Fragment."

        elif projektion == GeltungsKategorie.BEDINGT and not praemissen_erfuellt:
            behauptung.wahre_kategorie = GeltungsKategorie.FRAGMENT
            behauptung.kommentar = (
                f"Bedingung nicht erfüllt — Downgrade zu Fragment. "
                f"{fehlende_praemisse}".strip()
            )

        else:
            behauptung.wahre_kategorie = projektion
            behauptung.kommentar = "Epistemische Markierung korrekt (Bescheidenheit gewahrt)."

        behauptung.aufgeloest = True
        self._log_audit(behauptung)

        if self.knowledge_graph:
            self._schreibe_in_graph(behauptung)

        return behauptung

    def resolve_from_payload(self, payload: dict, *, persist: bool = False) -> dict:
        """API-Helfer: Dict → Auflösung → Dict."""
        beh = Behauptung(
            text=str(payload.get("text", "")).strip(),
            suggerierte_kategorie=parse_kategorie(str(payload.get("kategorie", "FRAGMENT"))),
            praemissen=list(payload.get("praemissen") or []),
        )
        if not beh.text:
            return {"ok": False, "error": "Leere Behauptung"}

        original_graph = self.knowledge_graph
        if persist:
            from knowledge_graph import get_knowledge_graph
            self.knowledge_graph = get_knowledge_graph()
        elif not persist:
            self.knowledge_graph = None

        try:
            result = self.projektions_aufloesung(
                beh,
                praemissen_erfuellt=bool(payload.get("praemissen_erfuellt", False)),
                fehlende_praemisse=str(payload.get("fehlende_praemisse", "")),
            )
        finally:
            self.knowledge_graph = original_graph

        out = result.to_dict()
        out["ok"] = True
        out["persisted"] = bool(persist and result.wahre_kategorie)
        out["graph_blocked"] = result.wahre_kategorie == GeltungsKategorie.METAPHER_ALS_BEWEIS
        return out

    def _log_audit(self, behauptung: Behauptung) -> None:
        eintrag = {
            "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
            "claim": behauptung.text,
            "drift": (
                f"{behauptung.suggerierte_kategorie.value} -> "
                f"{behauptung.wahre_kategorie.value if behauptung.wahre_kategorie else '?'}"
            ),
            "note": behauptung.kommentar,
        }
        self.audit_log.append(eintrag)

    def _schreibe_in_graph(self, behauptung: Behauptung) -> None:
        """Speichert nur korrekt markierte Aussagen — Metapher-als-Beweis blockiert."""
        if behauptung.wahre_kategorie in (
            GeltungsKategorie.SATZ,
            GeltungsKategorie.BEDINGT,
            GeltungsKategorie.MODELL,
            GeltungsKategorie.FRAGMENT,
        ):
            self.knowledge_graph.add_node(
                behauptung.text,
                category=behauptung.wahre_kategorie.name,
                meta={
                    "praemissen": behauptung.praemissen,
                    "kommentar": behauptung.kommentar,
                    "suggested": behauptung.suggerierte_kategorie.name,
                },
            )


_workbench_singleton: Optional[HeroGuideWorkbench] = None


def get_workbench(*, with_graph: bool = True) -> HeroGuideWorkbench:
    global _workbench_singleton
    if _workbench_singleton is None:
        graph = None
        if with_graph:
            from knowledge_graph import get_knowledge_graph
            graph = get_knowledge_graph()
        _workbench_singleton = HeroGuideWorkbench(graph)
    return _workbench_singleton


def status() -> dict:
    wb = get_workbench(with_graph=True)
    return {
        "module": "HERO-GUIDE Geltungs-Werkbank",
        "kategorien": [k.name for k in GeltungsKategorie],
        "audit_entries": len(wb.audit_log),
        "graph_attached": wb.knowledge_graph is not None,
    }


if __name__ == "__main__":
    class DummyGraph:
        def add_node(self, text, category, meta=None):
            pass

    werkbank = HeroGuideWorkbench(knowledge_graph=DummyGraph())

    b1 = Behauptung(
        text="Alignment als Banach-Kontraktion in der Heroik",
        suggerierte_kategorie=GeltungsKategorie.SATZ,
        praemissen=["lambda < 1"],
    )
    werkbank.projektions_aufloesung(b1, praemissen_erfuellt=False, fehlende_praemisse="lambda < 1 ist unbewiesen")

    b2 = Behauptung(
        text="Identität: q1b1 * b2q2 = q2b2 * b1q1",
        suggerierte_kategorie=GeltungsKategorie.SATZ,
        praemissen=["Austauschsymmetrie"],
    )
    werkbank.projektions_aufloesung(
        b2, praemissen_erfuellt=False, fehlende_praemisse="Generisch falsch, nur als Bedingung gültig"
    )