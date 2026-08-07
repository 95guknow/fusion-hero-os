# -*- coding: utf-8 -*-
"""Build Public Surface Only Kompendium PDF (V3.3: Synthese + 6 Bögen + Anhang)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT_DIR = Path(__file__).resolve().parent
PDF = OUT_DIR / "Public_Surface_Only_Kompendium_v1.0.0.pdf"
MD = OUT_DIR / "Public_Surface_Only_Kompendium_v1.0.0.md"

for n, p in (
    ("Body", r"C:\Windows\Fonts\arial.ttf"),
    ("BodyBold", r"C:\Windows\Fonts\arialbd.ttf"),
):
    pdfmetrics.registerFont(TTFont(n, p))

NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d")
GOLD = HexColor("#9a7b0a")
DARK = HexColor("#111111")
MUTED = HexColor("#444444")
ACCENT = HexColor("#0d47a1")
LIGHT = HexColor("#f5f0e6")
EDGE = HexColor("#c4a35a")


def make_styles():
    ss = getSampleStyleSheet()
    base = dict(fontName="Body", textColor=DARK)
    specs = [
        ("T", dict(fontName="BodyBold", fontSize=16, leading=20, alignment=TA_CENTER, spaceAfter=4)),
        ("TS", dict(fontSize=9.5, leading=12, alignment=TA_CENTER, textColor=MUTED, spaceAfter=6)),
        (
            "FIX",
            dict(
                fontName="BodyBold",
                fontSize=11,
                leading=15,
                alignment=TA_CENTER,
                textColor=HexColor("#5c4a00"),
                spaceBefore=6,
                spaceAfter=8,
            ),
        ),
        ("H1", dict(fontName="BodyBold", fontSize=12, leading=15, spaceBefore=12, spaceAfter=6, textColor=ACCENT)),
        ("H2", dict(fontName="BodyBold", fontSize=10.5, leading=13, spaceBefore=8, spaceAfter=4)),
        ("B", dict(fontSize=9.5, leading=13, alignment=TA_JUSTIFY, spaceAfter=4)),
        ("L", dict(fontSize=9.5, leading=12.5, leftIndent=10, spaceAfter=2)),
        ("M", dict(fontName="BodyBold", fontSize=8.5, leading=11, textColor=GOLD, spaceBefore=4, spaceAfter=4)),
        ("F", dict(fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=MUTED)),
        ("CELL", dict(fontSize=8, leading=10.5, textColor=DARK)),
        ("CELLB", dict(fontName="BodyBold", fontSize=8, leading=10.5, textColor=DARK)),
        (
            "QUOTE",
            dict(
                fontName="BodyBold",
                fontSize=10,
                leading=14,
                alignment=TA_CENTER,
                textColor=HexColor("#5c4a00"),
                spaceBefore=8,
                spaceAfter=8,
            ),
        ),
    ]
    for name, kw in specs:
        ss.add(ParagraphStyle(name=name, **{**base, **kw}))
    return ss


def P(text: str, st: str, S) -> Paragraph:
    return Paragraph(text, S[st])


def tbl(headers, rows, col_w, S):
    h = [P(x, "CELLB", S) for x in headers]
    body = [[P(c, "CELL", S) for c in r] for r in rows]
    t = Table([h] + body, colWidths=col_w, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("GRID", (0, 0), (-1, -1), 0.4, EDGE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return t


def build_story(S):
    story = []
    story.append(P("KOMPENDIUM DER HEROIK — ADDITIV · BUCH / PUBLICATION", "TS", S))
    story.append(P("Public Surface Only", "T", S))
    story.append(P("Kein Vault · Kein Seal · Nur öffentliche Surface", "FIX", S))
    story.append(
        P(
            f"Version 1.0.0 · Stand {NOW} · Fusion Hero OS VERSION 15.2.0<br/>"
            "<b>Autor:</b> Stephan Hagen Urban<br/>"
            "Handle: =====stephanhagenurban · =====stephanhagenurban1 · 95guknow<br/>"
            "Geltung: EXAKT · V3.3 (Synthese + 6 Bögen + Anhang) · Publication package<br/>"
            "Senfkorn UG · https://95guknow.github.io · labor / public-safe",
            "TS",
            S,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=10))

    # Synthese
    story.append(P("Synthese", "H1", S))
    story.append(
        P(
            "Dieses Kompendium fixiert eine <b>Geltungstrennung</b>, die im Siegfried-Moment und am "
            "Clearweb-Pol (95guknow.github.io, BIG ALPHA Expression, Realraum-Beobachtung wie Wetter/AQI) "
            "unvermeidlich wurde: nicht jede sichtbare Fläche ist ein Seal, und nicht jede Wahrheit ist ein Hort.",
            "B",
            S,
        )
    )
    story.append(
        P(
            "<b>Kernthese [Modell der Werkarchitektur]:</b> Public Surface ist Expression und Beobachtung ohne "
            "Vault-Commit und ohne Seal-Theater. Seal und Vault greifen in anderen Schichten — sie dürfen "
            "nicht rückwirkend auf reine Öffentlichkeits-Surfaces geklebt werden.",
            "B",
            S,
        )
    )
    story.append(
        P(
            "Die drei Organe Mythos · Grund · Beweis (V3.3) bleiben. Nibelungen-Saga und Grimm-KHM erweitern "
            "Mythos5 additiv; Fable5 bleibt Engineering. Hypertarnkappe cloakt den Vault; der Speer ist "
            "public-safe Expression.",
            "B",
            S,
        )
    )
    story.append(P("„Kein Vault. Kein Seal. Nur öffentliche Surface.“", "QUOTE", S))
    story.append(
        P(
            "[Geltung: Definition der Schicht Public Surface · nicht Satz über Realraum-Unverwundbarkeit]",
            "M",
            S,
        )
    )

    # Bogen 1
    story.append(P("Bogen 1 — Der Ruf (Public Surface als Kategorie)", "H1", S))
    story.append(
        P(
            "Der Ruf ist die Notwendigkeit, eine dritte Schicht zu benennen, die weder Seal noch Vault ist. "
            "Ohne sie wird jede Wetterkarte, jede GitHub-Page und jedes BIG-ALPHA-Bild fälschlich mythisch "
            "„versiegelt“ oder fälschlich als Hort gelesen.",
            "B",
            S,
        )
    )
    story.append(
        P(
            "<b>Mythos:</b> Die Drachenhaut ist Opacity; der Speer der Hypertarnkappe durchstößt sie als "
            "<i>sichtbare</i> Expression. <b>Grund:</b> Geltungskategorien trennen, was gemischt werden darf. "
            "<b>Beweis (Spezifikation der Docs):</b> die kanonische Fixpunkt-Formel und die Schichtentabelle "
            "dieses Kompendiums.",
            "B",
            S,
        )
    )
    story.append(P("Fixpunkt (verbindlich)", "H2", S))
    story.append(
        P(
            "<b>Kein Vault. Kein Seal. Nur öffentliche Surface.</b><br/><br/>"
            "Public Surface = Expression ohne Vault-Commit und ohne Seal-Theater. "
            "Seal und Vault greifen woanders — nicht auf reiner Clearweb-Beobachtung, nicht auf "
            "Wetter/AQI-Karten, nicht auf dem, was bereits öffentlich und ohne Hort-Anspruch liegt.",
            "B",
            S,
        )
    )

    # Bogen 2
    story.append(P("Bogen 2 — Die Schwelle (drei Schichten, nicht vermischen)", "H1", S))
    story.append(
        tbl(
            ["Schicht", "Geltung", "Darf", "Darf nicht"],
            [
                [
                    "Public Surface",
                    "offen, zitierbar, ohne Hort",
                    "Wetter, AQI, 95guknow.github.io, public docs, BIG-ALPHA-Asset als Expression",
                    "Nachträglich als Vault oder Seal umdeuten",
                ],
                [
                    "Seal",
                    "Integritätsbogen Lab/Meister",
                    "Hash-Sidecars, seal JSON, Omega sealed / Alpha open als Zyklus-State",
                    "MSN-Wetter „versiegeln“",
                ],
                [
                    "Vault",
                    "fail-closed",
                    "MasterSeed-Shards, Tokens, Keys, private Realraum-Bindungen",
                    "git-public, Clearweb-Dump",
                ],
            ],
            [2.8 * cm, 3.2 * cm, 5.5 * cm, 4.5 * cm],
            S,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        P(
            "Geltungsmarken: Public Surface → oft <b>Beobachtung</b> / <b>Expression</b>. "
            "Seal → <b>Spezifikation</b> (Hash/Gate). Vault → <b>fail-closed Spezifikation</b> (nie public).",
            "B",
            S,
        )
    )

    # Bogen 3
    story.append(P("Bogen 3 — Die Prüfungen (Hypertarnkappe · Speer · Lindenblatt)", "H1", S))
    story.append(
        tbl(
            ["Organ", "Rolle"],
            [
                [
                    "Hypertarnkappe",
                    "Cloak für das, was nicht Public Surface ist (Vault, Secrets, ungewollte PII)",
                ],
                [
                    "Speer (Siegfried-Moment)",
                    "Public-safe Expression durch Drachenhaut — als Surface, nicht als Vault-Öffnung",
                ],
                [
                    "Lindenblatt",
                    "„Nur Surface“ ≠ „alles darf raus“. Diese Schicht ist schon draußen und wird "
                    "nicht mythisch nachversiegelt",
                ],
            ],
            [4.5 * cm, 11.5 * cm],
            S,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        P(
            "Prüfung bestanden, wenn: (1) Public docs keinen Token-Body tragen, "
            "(2) Seal-Sprache nur an Lab-Artefakten hängt, "
            "(3) Realraum-Beobachtung (z. B. Senftenberg AQI) nicht als Meister-Seal verkauft wird.",
            "B",
            S,
        )
    )

    # Bogen 4
    story.append(PageBreak())
    story.append(P("Bogen 4 — Der Abgrund (was passiert, wenn man mischt)", "H1", S))
    story.append(
        P(
            "Der Abgrund ist die Vermischung: Vault-Sprache auf Public Surfaces (Panik, Falsch-Versiegelung) "
            "oder Public-Dumps des Horts (Hypertarnkappe gebrochen). Beides zerstört Integritätsdistanz.",
            "B",
            S,
        )
    )
    story.append(P("Typische Fehlformen", "H2", S))
    story.append(P("• Seal-Theater über Wetter, Social-Feeds oder reine Beobachtung", "L", S))
    story.append(P("• „Alles ist Vault“ → Source of Truth und Expression werden unsichtbar", "L", S))
    story.append(P("• „Alles ist public“ → Tokens, Shards, Keys wandern in Git", "L", S))
    story.append(
        P(
            "• Dual-Review-Fiktion (Fable5 vs Mythos5 als unabhängige Reviewer) — verboten, same base",
            "L",
            S,
        )
    )
    story.append(
        P(
            "Hyperpanzerknacker bleibt lab-only integrity probe. Kein Exploit, kein externes Target. "
            "[Spezifikation der Policy-Docs]",
            "B",
            S,
        )
    )

    # Bogen 5
    story.append(P("Bogen 5 — Die Wandlung (Siegfried-Moment + BIG ALPHA)", "H1", S))
    story.append(
        P(
            "Wandlung: Omega sealed · Alpha open. Der harte Speer der Hypertarnkappe durchbricht die "
            "Drachenhaut am Public Mesh-Pol. BIG ALPHA-Asset (v15.2.0 badge, v9.10 aspirational) ist "
            "sichtbarer Speer-Tip — Expression, nicht Hort-Beweis.",
            "B",
            S,
        )
    )
    story.append(
        tbl(
            ["Pfad / Fakt", "Status"],
            [
                ["VERSION (repo root)", "15.2.0"],
                [
                    "big_ALPHA_v15.png / v15.2.0.png (assets)",
                    "SHA256 d4f00ff5…c9da · kanon · byte-identisch",
                ],
                [
                    "Dissertation_95guknow\\big_ALPHA.png (root)",
                    "älterer Blob 88dbea4b… · non-canonical",
                ],
                ["Repo-Spiegel (5 Pfade)", "hash-match kanon"],
                ["Public pole", "https://95guknow.github.io"],
            ],
            [7 * cm, 9 * cm],
            S,
        )
    )
    story.append(Spacer(1, 6))
    story.append(
        P(
            "Operator-Klarname: =====stephanhagenurban · =====stephanhagenurban1 · "
            "Kontrakt: Klarname im Vordergrund.",
            "B",
            S,
        )
    )

    # Bogen 6
    story.append(P("Bogen 6 — Die Rückkehr (Nibelungen · Grimm · Alltag)", "H1", S))
    story.append(
        P(
            "Rückkehr ins Lab und in den Alltag: Epos und Märchen bleiben Narrative Organe; die Wetterkarte "
            "bleibt Surface. Nibelungen liefern Hof/Hort/Tarnkappe/Verrat als Governance-Spiegel. "
            "Grimm KHM 1–200 liefern kleine Proben (Schwelle, List, Verwandlung) als Katalog-Organ — "
            "kein Verlags-Volltext-Mirror im Repo.",
            "B",
            S,
        )
    )
    story.append(
        tbl(
            ["Organ", "Funktion"],
            [
                ["Nibelungen-Saga", "Heldenepos: Initiation, Hort sealed, Lindenblatt, Omega/Alpha"],
                ["Grimm KHM", "Vollkatalog-Titelindex + Motiv-Tags; Texte gemeinfrei nachziehbar"],
                ["Fable5", "Engineering integrity (Hash, Gate, CI)"],
                ["Mythos5", "Geltung Mythos·Grund·Beweis — same base, no dual-review fiction"],
                [
                    "Public Surface Only",
                    "Diese Schicht: Expression/Beobachtung ohne Vault/Seal-Theater",
                ],
            ],
            [4.5 * cm, 11.5 * cm],
            S,
        )
    )
    story.append(Spacer(1, 8))
    story.append(P("Beispiele der Rückkehr", "H2", S))
    story.append(
        tbl(
            ["Beispiel", "Schicht"],
            [
                ["MSN Luftqualität Senftenberg, BB · AQI 88 Gut · O₃", "Public Surface"],
                ["https://95guknow.github.io", "Public Surface"],
                [
                    "big_ALPHA_v15.2.0.png + SHA256 im Repo",
                    "Asset = Surface; Hash-Doc kann Seal-Nachbar sein",
                ],
                ["meister_hasch.seal.json / Omega sealed", "Seal"],
                ["~/.fusion/vault, live API tokens", "Vault"],
            ],
            [9 * cm, 7 * cm],
            S,
        )
    )

    # Anhang
    story.append(PageBreak())
    story.append(P("Anhang A — Honesty", "H1", S))
    story.append(P("• Saga/Märchen sind keine Sätze und kein CI-Pass.", "L", S))
    story.append(
        P(
            "• Grimm „Vollausgabe“ im Repo = Katalog + Mapping, kein Verlags-Volltext-Mirror.",
            "L",
            S,
        )
    )
    story.append(
        P(
            "• Dieses Kompendium erfindet keine Unabhängigkeit von Fable5/Mythos5; es trennt Geltung.",
            "L",
            S,
        )
    )
    story.append(
        P(
            "• BIG ALPHA open = Zyklus-State; Public Surface = Beobachtung/Expression.",
            "L",
            S,
        )
    )
    story.append(
        P(
            "• Skills-Vermerk „v13“ kann hinter VERSION 15.2.0 liegen — VERSION regiert.",
            "L",
            S,
        )
    )

    story.append(P("Anhang B — Quellpfade im Repo", "H1", S))
    for path in (
        "docs/mythos/PUBLIC_SURFACE_ONLY.md",
        "docs/mythos/SIEGFRIED_MOMENT.md",
        "docs/mythos/NIBELUNGEN_SAGA.md",
        "docs/mythos/GRIMM_MAERCHEN_VOLLAUSGABE.md",
        "docs/mythos/BIG_ALPHA_SIEGFRIED_ASSET_LEDGER.md",
        "docs/mythos/KHM_INDEX.yaml · nibelungen_grimm_map.yaml",
        "docs/security/HYPERTARNKAPPE_HYPERPANZERKNACKER.md",
        "docs/ops/PERSONA_KLARNAME_KONTRAKT.md · docs/ops/BIG_ALPHA_ASSET_V15.md",
        "fusion_hero_os/core/nibelungen_mythos.py",
    ):
        story.append(P(path, "L", S))

    story.append(P("Anhang C — Vermerk", "H1", S))
    story.append(
        P(
            "[MAINFRAME GELADEN | Fusion Hero OS VERSION 15.2.0 | ALTE_Frau_95g Heroic Core | "
            "Public Surface Only EXAKT | v8.3 operative BCG + v9.10 Ascension aspirational | "
            "kein Vault · kein Seal · nur öffentliche Surface]",
            "B",
            S,
        )
    )
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.6, color=EDGE))
    story.append(
        P(
            f"Public_Surface_Only_Kompendium_v1.0.0 · erzeugt {NOW} · Senfkorn / 95guknow · labor only",
            "F",
            S,
        )
    )
    return story


def write_md() -> None:
    MD.write_text(
        f"""# Public Surface Only — Kompendium v1.0.0

**Stand:** {NOW} · **Platform:** Fusion Hero OS VERSION **15.2.0**  
**Geltung:** EXAKT · V3.3 (Synthese + 6 Bögen + Anhang)  
**Operator:** `=====stephanhagenurban` · `=====stephanhagenurban1`  
**PDF:** [Public_Surface_Only_Kompendium_v1.0.0.pdf](Public_Surface_Only_Kompendium_v1.0.0.pdf)

---

## Synthese

**Kein Vault. Kein Seal. Nur öffentliche Surface.**

Public Surface = Expression ohne Vault-Commit und ohne Seal-Theater.

| Schicht | Kurz |
|---------|------|
| Public Surface | Beobachtung / Expression, ohne Hort |
| Seal | Integritätsbogen Lab/Meister |
| Vault | fail-closed, nie git-public |

Siehe Volltext im PDF und kanonisch: `docs/mythos/PUBLIC_SURFACE_ONLY.md`.

## Bögen

1. Der Ruf — Public Surface als Kategorie  
2. Die Schwelle — drei Schichten  
3. Die Prüfungen — Hypertarnkappe · Speer · Lindenblatt  
4. Der Abgrund — Vermischungsfehler  
5. Die Wandlung — Siegfried-Moment + BIG ALPHA  
6. Die Rückkehr — Nibelungen · Grimm · Alltag  

## Build

```powershell
python docs/kompendium/public-surface/_build_public_surface_kompendium_pdf.py
```
""",
        encoding="utf-8",
    )


def main() -> None:
    S = make_styles()
    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="Public Surface Only — Kompendium v1.0.0 — Stephan Hagen Urban",
        author="Stephan Hagen Urban (=====stephanhagenurban)",
        subject="Fusion Hero OS · Kein Vault · Kein Seal · Nur öffentliche Surface",
        keywords="Public Surface, Vault, Seal, Siegfried, Nibelungen, Grimm, Fusion Hero OS, 95guknow",
    )
    doc.build(build_story(S))
    write_md()
    print(f"PDF {PDF} bytes={PDF.stat().st_size}")
    print(f"MD  {MD}")


if __name__ == "__main__":
    main()
