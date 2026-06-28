# -*- coding: utf-8 -*-
"""
core_modules.py — Lauffaehige Methoden-Module der Heroic Methodology
=====================================================================

Dieses Modul giesst jene konzeptuellen Bausteine aus ``HEROIC_SKILL.md`` in
echte, importsichere Python-Klassen, die *noch nicht* in
``heroic_core_mainframe.py`` codiert sind. Die im Mainframe bereits
vorhandenen Module (SelfModifyCoreModule, GenerationalEvolutionProtocolCoreModule,
CriticalMetaAnalysisCoreModule, QUBO-Engine) werden hier bewusst NICHT
dupliziert.

Implementiert:
    - PeerReviewCoreModule             (5-Dimensionen-Review ueber Text)
    - ErkenntnisprozessCoreModule      (5-stufige Zustandsmaschine)
    - FormalMathematicsCoreModule      (Klassifikation Satz/Bedingt/Modell/Fragment)
    - V3.3StructureCoreModule          (Synthese + 6 Boegen + Anhang)
    - AutomaticArchivingCoreModule     (00_Uebersicht.md + ZIP-Plan, ohne Schreiben)
    - RoadmapCoreModule                (Meilensteine + Abhaengigkeiten + naechster Schritt)

Harte Regeln:
    * Importsicher: keine Top-Level-Seiteneffekte, keine Netzwerkaufrufe,
      kein ``ui.run()``. Die Demo liegt hinter ``if __name__ == "__main__"``.
    * Keine echten Aussenwirkungen: AutomaticArchivingCoreModule erzeugt nur
      einen *Plan* (Text + Dateiliste), schreibt und zippt nichts.
    * Reines Python (Standardbibliothek). ``numpy`` wird nur optional fuer den
      Haus-RNG geladen und ist nicht erforderlich.

Hausstil: deutsche Docstrings, ``rng = np.random.default_rng(7)`` falls vorhanden.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

# --- Optionaler Haus-RNG (numpy ist optional; Modul laeuft auch ohne) -------
try:  # pragma: no cover - reine Verfuegbarkeitsweiche
    import numpy as _np

    rng = _np.random.default_rng(7)
    _HAS_NUMPY = True
except Exception:  # numpy nicht installiert -> Modul bleibt nutzbar
    rng = None
    _HAS_NUMPY = False


# ===========================================================================
# 1) PeerReviewCoreModule — 5-Dimensionen-Review
# ===========================================================================
class PeerReviewCoreModule:
    """Verbindlicher 5-Dimensionen-Review-Raster fuer nicht-triviale Outputs.

    Prueft einen Text heuristisch (Regex-Treffer, abgeleitet aus ``app.py``
    ``review()``) gegen die fuenf Review-Dimensionen aus ``HEROIC_SKILL.md``:
    Evidenz/Quellen, Logische Kette, Alternativen, Implikationen, Risiken/Luecken.

    Der Score ist eine *Abdeckungs*-Heuristik (wieviele Dimensionen mindestens
    einen Marker enthalten), kein inhaltliches Qualitaetsurteil. Das ist
    bewusst konservativ und sollte nicht als Beweis von Vollstaendigkeit
    missdeutet werden (vgl. CriticalMetaAnalysis: Modell, nicht Satz).
    """

    # (Dimensionsname, Regex-Marker) — bewusst nah an app.py gehalten.
    DIMENSIONS: List[Tuple[str, str]] = [
        ("1 Evidenz/Quellen", r"(quelle|source|ref|http|doi|zitat|beleg)"),
        ("2 Logische Kette", r"(→|=>|daher|because|weil|therefore|deshalb|folgt|somit)"),
        ("3 Alternativen", r"(alternativ|gegenargument|jedoch|stattdessen|abwägung|andererseits)"),
        ("4 Implikationen", r"(implikation|folge|handlungsempfehl|nächst|next step|empfehlung)"),
        ("5 Risiken/Lücken", r"(risik|unsicher|lücke|tbd|todo|offen|annahme)"),
    ]

    def review(self, text: str) -> Dict[str, object]:
        """Fuehrt den 5-Dimensionen-Review ueber ``text`` aus.

        Rueckgabe-Dict:
            ``dimensions`` : Liste aus {name, hit, markers} pro Dimension
            ``score``      : Anzahl abgedeckter Dimensionen (0..5)
            ``max_score``  : 5
            ``coverage``   : score/5 als Float
            ``passed``     : True ab >= 4 abgedeckten Dimensionen
        """
        t = text or ""
        dims: List[Dict[str, object]] = []
        for name, pattern in self.DIMENSIONS:
            found = re.findall(pattern, t, flags=re.I)
            dims.append(
                {
                    "name": name,
                    "hit": bool(found),
                    "markers": sorted({m.lower() for m in found if isinstance(m, str)}),
                }
            )
        score = sum(1 for d in dims if d["hit"])
        return {
            "dimensions": dims,
            "score": score,
            "max_score": len(self.DIMENSIONS),
            "coverage": score / len(self.DIMENSIONS),
            "passed": score >= 4,
        }

    def report(self, text: str) -> str:
        """Formatiert das Review-Ergebnis als lesbaren Textreport."""
        res = self.review(text)
        lines = [
            "5-Dimensionen-Review",
            f"Abdeckung: {res['score']}/{res['max_score']} "
            f"({res['coverage'] * 100:.0f}%) — "
            f"{'bestanden' if res['passed'] else 'unvollstaendig'}",
            "",
        ]
        for d in res["dimensions"]:
            mark = "✓" if d["hit"] else "○"
            extra = f"  [{', '.join(d['markers'])}]" if d["markers"] else ""
            lines.append(f"  {mark} {d['name']}{extra}")
        return "\n".join(lines)


# ===========================================================================
# 2) ErkenntnisprozessCoreModule — 5-stufige Zustandsmaschine
# ===========================================================================
@dataclass
class _Stage:
    nummer: int
    titel: str
    beschreibung: str
    erledigt: bool = False


class ErkenntnisprozessCoreModule:
    """5-stufiger Erkenntnisprozess als einfache Zustandsmaschine.

    Stufen (aus ``HEROIC_SKILL.md``):
        1 Scoping & Hypothesen-Formulierung
        2 Systematische Quellen- & Datenerhebung
        3 Evidenz-Auswertung & Muster-Erkennung
        4 Multi-Perspektiven-Kritik & Stress-Test
        5 Integrierte Synthese & Handlungsempfehlungen

    ``advance()`` markiert die aktuelle Stufe als erledigt und rueckt eine
    Stufe weiter. ``current_stage()`` liefert die aktuell offene Stufe,
    ``report()`` einen Zwischenbericht im Format der Methodik.
    """

    _STUFEN: List[Tuple[str, str]] = [
        ("Scoping & Hypothesen-Formulierung",
         "Scope definieren, erste Hypothesen zu Luecken/Asymmetrien, Meta-Review der Scoping-Qualitaet."),
        ("Systematische Quellen- & Datenerhebung",
         "Interne Artefakte und externe Quellen systematisch erheben, Evidenz mit Qualitaetseinschaetzung."),
        ("Evidenz-Auswertung & Muster-Erkennung",
         "Muster, Asymmetrien und Luecken identifizieren; Pflicht: interne kritische Pruefung."),
        ("Multi-Perspektiven-Kritik & Stress-Test",
         "Ergebnisse gegen alternative Designs und alle 5 Dimensionen stress-testen."),
        ("Integrierte Synthese & Handlungsempfehlungen",
         "Synthese + sofort nutzbares Konzept/Update, mit optionalem Self-Modification-Vorschlag."),
    ]

    def __init__(self, thema: str = "(unbenannt)") -> None:
        self.thema = thema
        self.stages: List[_Stage] = [
            _Stage(i + 1, t, b) for i, (t, b) in enumerate(self._STUFEN)
        ]
        self._index = 0  # Index der aktuell offenen Stufe (0..5; 5 == fertig)

    def current_stage(self) -> Optional[_Stage]:
        """Liefert die aktuell offene Stufe oder ``None``, wenn abgeschlossen."""
        if self.is_complete():
            return None
        return self.stages[self._index]

    def advance(self, notiz: str = "") -> Optional[_Stage]:
        """Schliesst die aktuelle Stufe ab und rueckt weiter.

        ``notiz`` wird (falls gesetzt) der erledigten Stufe an die
        Beschreibung angehaengt. Gibt die *neue* aktuelle Stufe zurueck
        (oder ``None``, wenn der Prozess damit abgeschlossen ist).
        """
        if self.is_complete():
            return None
        stage = self.stages[self._index]
        stage.erledigt = True
        if notiz:
            stage.beschreibung += f"  | Notiz: {notiz}"
        self._index += 1
        return self.current_stage()

    def is_complete(self) -> bool:
        """True, wenn alle fuenf Stufen abgeschlossen sind."""
        return self._index >= len(self.stages)

    def report(self) -> str:
        """Erzeugt einen Zwischenbericht im Methodik-Format."""
        done = sum(1 for s in self.stages if s.erledigt)
        cur = self.current_stage()
        kopf = (
            f"Zwischenbericht — Stufe {min(done + 1, len(self.stages))}/{len(self.stages)}"
            if not self.is_complete()
            else f"Abschlussbericht — {len(self.stages)}/{len(self.stages)} Stufen erledigt"
        )
        lines = [kopf, f"Thema: {self.thema}", ""]
        for s in self.stages:
            mark = "✓" if s.erledigt else ("▶" if (cur and s is cur) else "○")
            lines.append(f"  {mark} Stufe {s.nummer}: {s.titel}")
        if cur:
            lines += ["", f"Naechste Operation: {cur.beschreibung}"]
        return "\n".join(lines)


# ===========================================================================
# 3) FormalMathematicsCoreModule — Geltungskategorien
# ===========================================================================
@dataclass
class FormalClassification:
    """Ergebnis der Geltungs-Klassifikation einer formalen Aussage."""

    kategorie: str            # Satz | Bedingt | Modell | Fragment
    begruendung: str
    aussage: str


class FormalMathematicsCoreModule:
    """Etikettiert eine formale Aussage als Satz/Bedingt/Modell/Fragment.

    Geltungskategorien (aus ``HEROIC_SKILL.md``):
        - **Satz**     — bewiesen, mit zitierbarer Quelle oder vollstaendigem Beweis.
        - **Bedingt**  — gilt unter explizit genannten Annahmen.
        - **Modell**   — strukturelle Analogie / Heuristik; keine Beweiskraft.
        - **Fragment** — unvollstaendig, offen markiert.

    Die Klassifikation erfolgt heuristisch ueber Schluesselwoerter und
    optionale explizite Flags. Sie ist selbst ein *Modell* (kein Satz):
    sie erkennt Sprachsignale, nicht mathematische Wahrheit.
    """

    _BEWIESEN = r"(bewiesen|q\.?e\.?d\.?|beweis|theorem|satz von|quelle:|doi|laut \[)"
    _BEDINGT = r"(annahme|unter der voraussetzung|sei |gegeben|falls |wenn .* dann|gilt unter|sofern)"
    _MODELL = r"(modell|analog|heuristik|wie ein|metapher|vereinfach|naeherung|näherung|so etwas wie)"
    _FRAGMENT = r"(tbd|todo|unvollstaendig|unvollständig|offen|\.\.\.|fragment|noch zu)"

    def classify(
        self,
        aussage: str,
        bewiesen: Optional[bool] = None,
        annahmen: Optional[List[str]] = None,
    ) -> FormalClassification:
        """Klassifiziert ``aussage`` in eine der vier Geltungskategorien.

        Explizite Flags haben Vorrang vor der Textheuristik:
            ``bewiesen=True``          -> Satz
            ``annahmen=[...]`` (nicht leer) -> Bedingt
        Andernfalls entscheidet die Schluesselwort-Heuristik in der
        Prioritaet Fragment > Satz > Bedingt > Modell (Default: Fragment,
        wenn keine Beweis-/Annahme-Signale vorliegen).
        """
        t = aussage or ""

        if bewiesen is True:
            return FormalClassification("Satz", "Explizit als bewiesen markiert.", t)
        if annahmen:
            return FormalClassification(
                "Bedingt", f"Gilt unter Annahmen: {', '.join(annahmen)}.", t
            )

        if re.search(self._FRAGMENT, t, re.I):
            return FormalClassification("Fragment", "Offen/unvollstaendig markiert.", t)
        if re.search(self._BEWIESEN, t, re.I):
            return FormalClassification("Satz", "Beweis-/Quellensignal erkannt.", t)
        if re.search(self._BEDINGT, t, re.I):
            return FormalClassification("Bedingt", "Annahme-/Bedingungssignal erkannt.", t)
        if re.search(self._MODELL, t, re.I):
            return FormalClassification("Modell", "Analogie-/Heuristiksignal erkannt.", t)

        # Konservativer Default: ohne Beweis bleibt es offen.
        return FormalClassification(
            "Fragment", "Kein Beweis-, Annahme- oder Modellsignal — bleibt offen.", t
        )

    def report(self, aussage: str, **kwargs) -> str:
        """Liefert eine kurze Etikettierung als Text."""
        c = self.classify(aussage, **kwargs)
        return f"[{c.kategorie}] {c.aussage!r} — {c.begruendung}"


# ===========================================================================
# 4) V3.3StructureCoreModule — Synthese + 6 Boegen + Anhang
# ===========================================================================
class V3_3StructureCoreModule:
    """Erzeugt das V3.3-Gliederungsskelett fuer laengere Texte.

    Schema (aus ``HEROIC_SKILL.md``):
        Synthese (Ueberblick + Kernthesen)
          Bogen 1 .. Bogen 6
        Anhang (Quellen, Begriffe, Hilfsmaterial)

    Reines Geruest: liefert eine strukturierte Datenrepraesentation
    (``skeleton``) sowie ein Markdown-Rendering (``render_markdown``).
    Es wird nichts auf die Platte geschrieben.
    """

    ANZAHL_BOEGEN = 6

    def skeleton(self, titel: str, bogen_titel: Optional[List[str]] = None) -> Dict[str, object]:
        """Baut das Gliederungs-Dict fuer ``titel``.

        ``bogen_titel`` kann optional die 6 Bogentitel vorgeben; fehlende
        werden mit Platzhaltern aufgefuellt, ueberzaehlige ignoriert.
        """
        titel = (titel or "(ohne Titel)").strip()
        vorgaben = list(bogen_titel or [])
        boegen = []
        for i in range(self.ANZAHL_BOEGEN):
            bt = vorgaben[i] if i < len(vorgaben) else f"Bogen {i + 1} — (Platzhalter)"
            boegen.append({"nummer": i + 1, "titel": bt, "inhalt": ""})
        return {
            "titel": titel,
            "synthese": {"ueberblick": "", "kernthesen": []},
            "boegen": boegen,
            "anhang": {"quellen": [], "begriffe": [], "hilfsmaterial": []},
        }

    def render_markdown(self, titel: str, bogen_titel: Optional[List[str]] = None) -> str:
        """Rendert das Skelett als Markdown-Geruest."""
        sk = self.skeleton(titel, bogen_titel)
        lines = [
            f"# {sk['titel']}",
            "",
            "## Synthese (Ueberblick + Kernthesen)",
            "_Ueberblick:_ ",
            "_Kernthesen:_ ",
            "",
        ]
        for b in sk["boegen"]:
            lines += [f"## {b['titel']}", "", ""]
        lines += [
            "## Anhang",
            "- Quellen: ",
            "- Begriffe: ",
            "- Hilfsmaterial: ",
        ]
        return "\n".join(lines)


# Praktischer Alias, da Bezeichner nicht mit Ziffer beginnen duerfen.
V33StructureCoreModule = V3_3StructureCoreModule


# ===========================================================================
# 5) AutomaticArchivingCoreModule — Uebersicht + ZIP-Plan (ohne Schreiben)
# ===========================================================================
@dataclass
class ArchivePlan:
    """Plan-Objekt fuer eine Archivierung — beschreibt, schreibt aber nichts."""

    zip_name: str
    uebersicht_md: str
    files_to_zip: List[str]
    index: List[str]


class AutomaticArchivingCoreModule:
    """Plant die Archivierung ("alles zu einem zusammenfuehren").

    WICHTIG — keine Aussenwirkung: dieses Modul schreibt KEINE Datei und
    erzeugt KEIN ZIP. Es liefert ausschliesslich einen ``ArchivePlan`` mit
    dem Text fuer ``00_Uebersicht.md``, der vorgeschlagenen ZIP-Bezeichnung
    (mit Datum) und der Liste der einzubeziehenden Dateien. Das tatsaechliche
    Schreiben/Zippen ist Aufgabe des aufrufenden Codes nach Bestaetigung.
    """

    def build_plan(
        self,
        titel: str,
        artefakte: List[str],
        entscheidungen: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        offene_punkte: Optional[List[str]] = None,
        chronologie: Optional[List[str]] = None,
        heute: Optional[date] = None,
    ) -> ArchivePlan:
        """Erzeugt den Archivierungs-Plan (ohne Schreiben/Zippen)."""
        heute = heute or date.today()
        datum = heute.strftime("%Y-%m-%d")
        slug = re.sub(r"[^a-z0-9]+", "_", (titel or "archiv").lower()).strip("_") or "archiv"
        zip_name = f"{datum}_{slug}.zip"

        def _liste(items: Optional[List[str]], leer: str) -> str:
            items = items or []
            if not items:
                return f"- {leer}"
            return "\n".join(f"- {x}" for x in items)

        uebersicht = "\n".join(
            [
                "# 00_Uebersicht",
                "",
                f"Titel: {titel}",
                f"Datum: {datum}",
                "",
                "## Was ist passiert (chronologisch)",
                _liste(chronologie, "(keine Chronologie erfasst)"),
                "",
                "## Getroffene Entscheidungen",
                _liste(entscheidungen, "(keine Entscheidungen erfasst)"),
                "",
                "## Vorliegende Outputs",
                _liste(outputs, "(keine Outputs erfasst)"),
                "",
                "## Offene Punkte",
                _liste(offene_punkte, "(keine offenen Punkte)"),
                "",
                "## Enthaltene Artefakte",
                _liste(artefakte, "(keine Artefakte)"),
            ]
        )

        # 00_Uebersicht.md liegt als erster Eintrag im geplanten Archiv.
        files = ["00_Uebersicht.md"] + list(artefakte)
        index = [f"{i:02d}. {name}" for i, name in enumerate(files)]
        return ArchivePlan(
            zip_name=zip_name,
            uebersicht_md=uebersicht,
            files_to_zip=files,
            index=index,
        )


# ===========================================================================
# 6) RoadmapCoreModule — Meilensteine + Abhaengigkeiten
# ===========================================================================
@dataclass
class Milestone:
    """Ein Roadmap-Meilenstein mit Abhaengigkeiten und Status."""

    key: str
    titel: str
    deps: List[str] = field(default_factory=list)
    done: bool = False


class RoadmapCoreModule:
    """Verwaltet Meilensteine, Abhaengigkeiten und naechste Schritte.

    Verbindet kurze Aufgaben mit langfristigen Zielen (Layer 4). Erlaubt das
    Hinzufuegen von Meilensteinen mit Vorgaenger-Abhaengigkeiten, das Abhaken
    erledigter Meilensteine und die Abfrage des/der naechsten ausfuehrbaren
    Schritte(s) — also jener offenen Meilensteine, deren Abhaengigkeiten
    bereits erledigt sind.
    """

    def __init__(self) -> None:
        self._milestones: Dict[str, Milestone] = {}

    def add(self, key: str, titel: str, deps: Optional[List[str]] = None) -> Milestone:
        """Fuegt einen Meilenstein hinzu (Abhaengigkeiten als Liste von keys)."""
        if key in self._milestones:
            raise ValueError(f"Meilenstein '{key}' existiert bereits.")
        m = Milestone(key=key, titel=titel, deps=list(deps or []))
        self._milestones[key] = m
        return m

    def complete(self, key: str) -> None:
        """Markiert einen Meilenstein als erledigt."""
        if key not in self._milestones:
            raise KeyError(f"Unbekannter Meilenstein: '{key}'")
        self._milestones[key].done = True

    def _deps_erfuellt(self, m: Milestone) -> bool:
        return all(self._milestones.get(d) and self._milestones[d].done for d in m.deps)

    def next_steps(self) -> List[Milestone]:
        """Liefert alle offenen Meilensteine mit erfuellten Abhaengigkeiten."""
        return [
            m
            for m in self._milestones.values()
            if not m.done and self._deps_erfuellt(m)
        ]

    def next_step(self) -> Optional[Milestone]:
        """Liefert den ersten ausfuehrbaren naechsten Schritt (oder ``None``)."""
        steps = self.next_steps()
        return steps[0] if steps else None

    def report(self) -> str:
        """Erzeugt einen Roadmap-Statusreport."""
        if not self._milestones:
            return "Roadmap: (leer)"
        lines = ["Roadmap-Status:"]
        for m in self._milestones.values():
            mark = "✓" if m.done else ("▶" if self._deps_erfuellt(m) else "⏸")
            dep_str = f" (braucht: {', '.join(m.deps)})" if m.deps else ""
            lines.append(f"  {mark} {m.key}: {m.titel}{dep_str}")
        nxt = self.next_step()
        lines.append("")
        lines.append(f"Naechster Schritt: {nxt.key + ' — ' + nxt.titel if nxt else '(keiner offen/bereit)'}")
        return "\n".join(lines)


# ===========================================================================
# Selbsttest-Demo (nur bei direktem Aufruf)
# ===========================================================================
def _selbsttest() -> None:
    """Kurzer Selbsttest aller Module — gibt nur auf stdout aus."""
    print("=" * 68)
    print("core_modules.py — Selbsttest")
    print(f"numpy verfuegbar: {_HAS_NUMPY}")
    print("=" * 68)

    print("\n--- PeerReviewCoreModule ---")
    pr = PeerReviewCoreModule()
    probe = (
        "Laut Quelle [1] folgt daher X. Alternativ waere Y denkbar, jedoch "
        "schwaecher. Naechster Schritt: Z. Offen bleibt das Risiko R."
    )
    print(pr.report(probe))

    print("\n--- ErkenntnisprozessCoreModule ---")
    ep = ErkenntnisprozessCoreModule("Demo-Analyse")
    print(f"Aktuell: Stufe {ep.current_stage().nummer} — {ep.current_stage().titel}")
    ep.advance("Scope fixiert")
    ep.advance()
    print(ep.report())
    print(f"abgeschlossen? {ep.is_complete()}")

    print("\n--- FormalMathematicsCoreModule ---")
    fm = FormalMathematicsCoreModule()
    print(fm.report("Dies ist bewiesen, siehe doi:10.1000/x", bewiesen=True))
    print(fm.report("Sei n eine Primzahl, dann gilt ...", annahmen=["n prim"]))
    print(fm.report("Das Gehirn arbeitet analog wie ein Computer."))
    print(fm.report("Wir vermuten etwas, TBD."))

    print("\n--- V3.3StructureCoreModule ---")
    v33 = V3_3StructureCoreModule()
    md = v33.render_markdown("Kompendium der Methodik", ["Grundlagen", "Module"])
    print(md.splitlines()[0], "...", f"({len(md.splitlines())} Zeilen, 6 Boegen)")
    sk = v33.skeleton("X")
    print(f"Boegen im Skelett: {len(sk['boegen'])}")

    print("\n--- AutomaticArchivingCoreModule ---")
    arch = AutomaticArchivingCoreModule()
    plan = arch.build_plan(
        "Session 2026",
        artefakte=["app.py", "heroic_core_mainframe.py", "core_modules.py"],
        entscheidungen=["ECharts statt plotly", "numba nogil + ThreadPool"],
        outputs=["core_modules.py"],
        offene_punkte=["Connector-Tests"],
        chronologie=["Module geplant", "Module codiert"],
        heute=date(2026, 6, 28),
    )
    print(f"ZIP-Plan: {plan.zip_name}  (NICHT geschrieben)")
    print(f"Dateien im Plan: {plan.files_to_zip}")
    print("Index:", "; ".join(plan.index))

    print("\n--- RoadmapCoreModule ---")
    rm = RoadmapCoreModule()
    rm.add("m1", "Module schreiben")
    rm.add("m2", "Tests schreiben", deps=["m1"])
    rm.add("m3", "Release", deps=["m2"])
    print("Vor Abschluss:", rm.next_step().key)
    rm.complete("m1")
    print(rm.report())

    print("\n" + "=" * 68)
    print("Selbsttest abgeschlossen — alle Module instanziiert und ausgefuehrt.")


if __name__ == "__main__":
    # Windows-Konsole (cp1252) vertraegt die Unicode-Marker (✓/○/▶) nicht;
    # stdout auf UTF-8 umstellen, falls moeglich. Nur Demo, kein Importeffekt.
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Python 3.7+
    except Exception:
        pass
    _selbsttest()
