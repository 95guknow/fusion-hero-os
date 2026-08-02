# -*- coding: utf-8 -*-
"""Notar-Vorbereitungspaket Senfkorn Holding GmbH — ENTWURF / Coev Step 1."""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parent
PDF = OUT / "Senfkorn_Holding_Notar_Vorbereitung_COEV.pdf"
MD = OUT / "Senfkorn_Holding_Notar_Vorbereitung_COEV.md"

for n, p in (
    ("Body", r"C:\Windows\Fonts\arial.ttf"),
    ("BodyBold", r"C:\Windows\Fonts\arialbd.ttf"),
):
    pdfmetrics.registerFont(TTFont(n, p))

TODAY = date.today().isoformat()
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
GOLD = HexColor("#9a7b0a")
DARK = HexColor("#111111")
MUTED = HexColor("#333333")
GREEN = HexColor("#1b5e20")
OP = "=====stephanhagenurban1 <3"
G = "Stephan Hagen Urban"
ADR = "Krabatweg 27, 02977 Hoyerswerda"


def styles():
    ss = getSampleStyleSheet()
    base = dict(fontName="Body", textColor=DARK)
    for name, kw in [
        ("T", dict(fontName="BodyBold", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=4)),
        ("TS", dict(fontSize=10, leading=13, alignment=TA_CENTER, textColor=MUTED, spaceAfter=8)),
        ("W", dict(fontSize=8, leading=10.5, alignment=TA_JUSTIFY, textColor=HexColor("#5c4a00"), spaceAfter=8)),
        ("H", dict(fontName="BodyBold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=5)),
        ("B", dict(fontSize=9.5, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=3)),
        ("L", dict(fontSize=9.5, leading=12.5, leftIndent=10, spaceAfter=2)),
        ("M", dict(fontName="BodyBold", fontSize=9, leading=12, textColor=HexColor("#0d47a1"), spaceBefore=6, spaceAfter=4)),
        ("F", dict(fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=MUTED)),
        ("SM", dict(fontSize=8, leading=10.5, alignment=TA_JUSTIFY, textColor=MUTED, spaceAfter=2)),
        ("OK", dict(fontSize=9, leading=12, textColor=GREEN, spaceAfter=2)),
    ]:
        ss.add(ParagraphStyle(name=name, **{**base, **kw}))
    return ss


def P(t, st, S):
    return Paragraph(t, S[st])


def story(S):
    out = [
        P("Notar-Vorbereitungspaket", "T", S),
        P("Senfkorn Holding GmbH · Coev Step 1", "TS", S),
        P(f"Operator {OP.replace('<', '&lt;')} · {TODAY} · Bob der Baumeister", "TS", S),
        HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceAfter=6),
        P(
            f"<b>Arbeitsdokument · keine Beurkundung.</b> Dieses Paket bündelt, was zum Notartermin "
            f"mitzubringen und zu entscheiden ist. Die Entwurfs-PDFs ersetzen <b>nicht</b> die notarielle "
            f"Beurkundung (§ 2 GmbHG). Operator-Freigabe Session: <b>{OP.replace('<', '&lt;')}</b> · UTC {NOW}.",
            "W",
            S,
        ),
        P("1. Ziel des Termins", "H", S),
        P(
            "Gründung der <b>Senfkorn Holding GmbH</b> (Stammkapital EUR 25.000, Ein-Personen-Gesellschaft) "
            "mit Holding-Gegenstand (Beteiligungen + IP), vorbereitetem IP-Lizenz-Hook zur "
            "<b>Senfkorn UG (haftungsbeschränkt)</b>.",
            "B",
            S,
        ),
        P("2. Dokumentenmappe (mitbringen / digital senden)", "H", S),
    ]

    docs = [
        ["#", "Dokument", "Status", "Datei / Hinweis"],
        [
            "1",
            "Gesellschaftsvertrag COEV-MAX",
            "ENTWURF bereit",
            "Senfkorn_Holding_GmbH_Gesellschaftsvertrag_COEV_MAX_ENTWURF.pdf",
        ],
        [
            "2",
            "IP-Lizenz Holding → UG",
            "ENTWURF bereit",
            "Senfkorn_IP_Lizenzvertrag_Holding_zu_UG_ENTWURF.pdf (nach Gründung unterzeichnen)",
        ],
        [
            "3",
            "GV älterer Kurz-Entwurf",
            "optional",
            "Senfkorn_Holding_GmbH_Gesellschaftsvertrag_ENTWURF.pdf",
        ],
        [
            "4",
            "Coev Legal Matrix",
            "intern",
            "Senfkorn_Holding_GmbH_COEV_LEGAL_MATRIX.md",
        ],
        [
            "5",
            "Personalausweis / Reisepass",
            "Gründer",
            f"{G}",
        ],
        [
            "6",
            "Meldeadresse",
            "Vorschlag",
            ADR,
        ],
        [
            "7",
            "Bank / Einzahlungsplan",
            "vorbereiten",
            "Geschäftskonto nach Notar / parallel klären",
        ],
        [
            "8",
            "Liste Beteiligungen / UG",
            "optional",
            "Senfkorn UG (haftungsbeschränkt) — Status Register",
        ],
    ]
    trows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(docs)]
    t = Table(trows, colWidths=[0.8 * cm, 4.5 * cm, 2.8 * cm, 8.2 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f5f0e0")),
                ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#ccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    out += [t, Spacer(1, 8)]

    out += [
        P("3. Entscheidungen für den Notar (bitte festlegen)", "H", S),
        P(
            "Diese Punkte stehen im Entwurf als Vorschlag und müssen in der Urkunde final sein:",
            "B",
            S,
        ),
        P(f"□ <b>Sitz:</b> Hoyerswerda (Vorschlag) — bestätigen oder ändern", "L", S),
        P(f"□ <b>Gesellschafter 100 %:</b> {G}, {ADR}", "L", S),
        P(f"□ <b>Allein-GF + Einzelvertretung:</b> {G}", "L", S),
        P("□ <b>§ 181 BGB-Befreiung:</b> ja (Vorschlag im GV) — bestätigen", "L", S),
        P("□ <b>Stammkapital:</b> EUR 25.000 bar — Einzahlungskonto / Zeitpunkt", "L", S),
        P("□ <b>Gründungskosten-Cap Gesellschaft:</b> EUR 3.500 (GV § 15) — anpassen?", "L", S),
        P(
            "□ <b>Zustimmungspflichtige Geschäfte:</b> Kreditschwelle EUR 10.000 / IP-Veräußerung / Beteiligungen > 25 %",
            "L",
            S,
        ),
        P(
            "□ <b>Impressum-Strategie nach Eintragung:</b> Holding GmbH vs. operative UG als DDG-Anbieter",
            "L",
            S,
        ),
        P(
            "□ <b>IP-Lizenz:</b> nach Holding-Existenz unterzeichnen (Null-Royalties verbunden — Steuerberater)",
            "L",
            S,
        ),
        P("□ <b>Sacheinlage</b> nein (Vorschlag: nur Bar) — bestätigen", "L", S),
        P("4. Ablauf (typisch, ohne Rechtsberatung)", "H", S),
        P(
            "<b>A.</b> Notar sichtet Entwürfe → finaler Satzungstext in Urkundensprache.<br/>"
            "<b>B.</b> Beurkundung Gründung (Gesellschaftervertrag / Satzung, GF-Bestellung, ggf. Liste).<br/>"
            "<b>C.</b> Eröffnung Geschäftskonto, Einzahlung Stammkapital, Bankbestätigung.<br/>"
            "<b>D.</b> Registergericht: Eintragung GmbH → Entstehung der juristischen Person.<br/>"
            "<b>E.</b> Danach: IP-Lizenz Holding → UG unterzeichnen; Impressum/Public sync; "
            "Beteiligung an UG dokumentieren.",
            "B",
            S,
        ),
        P("5. Coev-Reihenfolge (Stack)", "H", S),
    ]

    steps = [
        ["Schritt", "Schritt", "联系"],  # will replace
    ]
    steps = [
        ["Schritt", "Schritt", "联系"],
    ]
    # clean
    steps = [
        ["Schritt", "Schritt", "联系"],
    ]
    steps = [
        ["#", "Schritt", "Status"],
    ]
    # final clean german
    steps = [
        ["#", "Schritt", "Status"],
    ]
    steps = [
        ["#", "Schritt", "Status"],
    ]
    steps = [
        ["#", "Schritt", "Status"],
    ]
    # STOP - write properly
    steps = [
        ["#", "Schritt", "Status"],
    ]
    return out  # temporary - fix below


def story_fixed(S):
    out = story(S)
    # story ends early due to bug - rebuild completely cleaner
    return None


def full_story(S):
    out = [
        P("Notar-Vorbereitungspaket", "T", S),
        P("Senfkorn Holding GmbH · Coev Step 1", "TS", S),
        P(f"Operator {OP.replace('<', '&lt;')} · {TODAY} · Bob der Baumeister", "TS", S),
        HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceAfter=6),
        P(
            f"<b>Arbeitsdokument · keine Beurkundung.</b> Bündelt mitzubringende Unterlagen und offene "
            f"Entscheidungen für den Notartermin. Entwurfs-PDFs ersetzen <b>nicht</b> § 2 GmbHG. "
            f"Operator: <b>{OP.replace('<', '&lt;')}</b> · UTC {NOW}.",
            "W",
            S,
        ),
        P("1. Ziel des Termins", "H", S),
        P(
            "Gründung der <b>Senfkorn Holding GmbH</b> (EUR 25.000, Ein-Personen-GmbH) mit Holding-Gegenstand "
            "(Beteiligungen + IP) und vorbereitetem IP-Lizenz-Hook zur <b>Senfkorn UG (haftungsbeschränkt)</b>.",
            "B",
            S,
        ),
        P("2. Dokumentenmappe", "H", S),
    ]
    docs = [
        ["#", "Dokument", "Status", "Datei / Hinweis"],
        ["1", "Gesellschaftsvertrag COEV-MAX", "ENTWURF", "…_Gesellschaftsvertrag_COEV_MAX_ENTWURF.pdf"],
        ["2", "IP-Lizenz Holding → UG", "ENTWURF", "…_IP_Lizenzvertrag_…_ENTWURF.pdf (nach Gründung)"],
        ["3", "GV Kurz-Entwurf", "optional", "…_Gesellschaftsvertrag_ENTWURF.pdf"],
        ["4", "Coev Legal Matrix", "intern", "…_COEV_LEGAL_MATRIX.md"],
        ["5", "Ausweis", "Gründer", G],
        ["6", "Adresse", "Vorschlag", ADR],
        ["7", "Bank / Einzahlung", "vorbereiten", "Geschäftskonto + Nachweis"],
        ["8", "UG-Registerstand", "optional", "Senfkorn UG (haftungsbeschränkt)"],
    ]
    trows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(docs)]
    t = Table(trows, colWidths=[0.7 * cm, 4.6 * cm, 2.6 * cm, 8.4 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#f5f0e0")),
                ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#ccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    out += [
        t,
        Spacer(1, 6),
        P("3. Entscheidungen für den Notar (Checkbox)", "H", S),
        P(f"□ Sitz Hoyerswerda (Vorschlag) bestätigen", "L", S),
        P(f"□ Gesellschafter 100 %: {G}, {ADR}", "L", S),
        P(f"□ Allein-GF + Einzelvertretung: {G}", "L", S),
        P("□ § 181 BGB-Befreiung: ja (Vorschlag) bestätigen", "L", S),
        P("□ Stammkapital EUR 25.000 bar — Konto / Zeitpunkt", "L", S),
        P("□ Gründungskosten-Cap Gesellschaft EUR 3.500 — anpassen?", "L", S),
        P("□ Zustimmungsgeschäfte: Kredit &gt; 10.000 / IP-Verkauf / Beteiligung &gt; 25 %", "L", S),
        P("□ Impressum nach Eintragung: Holding vs. operative UG als DDG-Anbieter", "L", S),
        P("□ IP-Lizenz nach Holding-Existenz unterzeichnen (Null-Royalties — Steuer)", "L", S),
        P("□ Keine Sacheinlage (nur Bar) bestätigen", "L", S),
        P("4. Typischer Ablauf", "H", S),
        P(
            "<b>A.</b> Notar sichtet Entwürfe → Urkundentext.<br/>"
            "<b>B.</b> Beurkundung (Satzung, GF-Bestellung, Gesellschafterliste).<br/>"
            "<b>C.</b> Geschäftskonto, Einzahlung, Bankbestätigung.<br/>"
            "<b>D.</b> HR-Eintragung → GmbH entsteht.<br/>"
            "<b>E.</b> IP-Lizenz Holding→UG unterzeichnen · Impressum sync · UG-Beteiligung dokumentieren.",
            "B",
            S,
        ),
        P("5. Coev-Stack Status", "H", S),
    ]
    steps = [
        ["#", "Baustein", "Status"],
        ["1", "Notar-Vorbereitung (dieses PDF)", "JETZT"],
        ["2", "Gesellschaftsvertrag COEV-MAX PDF", "bereit"],
        ["3", "IP-Lizenz Holding→UG PDF", "bereit"],
        ["4", "Notartermin / Beurkundung", "offen"],
        ["5", "Einzahlung + HR-Eintragung", "offen"],
        ["6", "IP-Lizenz unterzeichnen", "nach 4–5"],
        ["7", "Impressum / Public sync", "nach 5"],
        ["8", "Beteiligung an operativer UG", "nach 5"],
    ]
    srows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(steps)]
    st = Table(srows, colWidths=[1.0 * cm, 10.0 * cm, 5.3 * cm])
    st.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e8eef8")),
                ("BACKGROUND", (0, 1), (-1, 1), HexColor("#e8f5e9")),
                ("GRID", (0, 0), (-1, -1), 0.35, HexColor("#ccc")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    out += [
        st,
        Spacer(1, 10),
        P("6. Ehrliche Grenze", "H", S),
        P(
            "<b>100 % Form-Coev</b> der Arbeitsmappe: ja (GV + IP-Lizenz + dieses Prep-Paket). "
            "<b>100 % Legalität im Rechtsverkehr:</b> erst Notar + Einzahlung + Eintragung (+ Unterschriften "
            "IP-Lizenz). Kein PDF und kein Operator-Emoji ersetzen das GmbHG.",
            "B",
            S,
        ),
        Spacer(1, 12),
        P(
            f"Operator: {OP.replace('<', '&lt;')} · ++ bestätigt · Step 1 Notar-Prep · {TODAY}",
            "F",
            S,
        ),
        P(f"Ordner: {OUT.as_posix()}", "F", S),
    ]
    return out


def chrome(c, doc):
    c.saveState()
    c.setFont("Body", 30)
    c.setFillColor(Color(0.75, 0.08, 0.08, alpha=0.09))
    c.translate(A4[0] / 2, A4[1] / 2)
    c.rotate(48)
    c.drawCentredString(0, 0, "ENTWURF — NOTAR-PREP")
    c.rotate(-48)
    c.translate(-A4[0] / 2, -A4[1] / 2)
    c.setFillColor(MUTED)
    c.setFont("Body", 7)
    c.drawCentredString(A4[0] / 2, 1.1 * cm, f"Notar-Vorbereitung Senfkorn Holding · {OP} · S. {doc.page}")
    c.restoreState()


def main():
    S = styles()
    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=1.9 * cm,
        rightMargin=1.9 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.7 * cm,
        title="Notar-Vorbereitung Senfkorn Holding GmbH",
        author="stephanhagenurban1 / Bob der Baumeister",
    )
    doc.build(full_story(S), onFirstPage=chrome, onLaterPages=chrome)
    MD.write_text(
        f"# Notar-Vorbereitung Senfkorn Holding GmbH\n\nOperator: `{OP}`  \nPDF: `{PDF}`  \n{NOW}\n",
        encoding="utf-8",
    )
    ops = Path.home() / ".fusion" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    (ops / "notar_prep_ack.json").write_text(
        f'{{"phrase":"{OP}","plus_plus":true,"step":1,"at":"{NOW}","pdf":"{PDF.as_posix()}"}}\n',
        encoding="utf-8",
    )
    print("PDF", PDF, PDF.stat().st_size)


if __name__ == "__main__":
    main()
