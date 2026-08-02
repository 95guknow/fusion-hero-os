# -*- coding: utf-8 -*-
"""Einzahlung Stammkapital + Handelsregister — Arbeitsanleitung Coev Step 3.
Operator: =====stephanhagenurban1 <3 · ENTWURF / keine Rechtsberatung.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent
PDF = OUT / "Senfkorn_Holding_Einzahlung_HR_COEV_Step3.pdf"
MD = OUT / "Senfkorn_Holding_Einzahlung_HR_COEV_Step3.md"

for n, p in (
    ("Body", r"C:\Windows\Fonts\arial.ttf"),
    ("BodyBold", r"C:\Windows\Fonts\arialbd.ttf"),
):
    pdfmetrics.registerFont(TTFont(n, p))

TODAY = date.today().isoformat()
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
GOLD, DARK, MUTED = HexColor("#9a7b0a"), HexColor("#111111"), HexColor("#333333")
OP = "=====stephanhagenurban1 <3"
G = "Stephan Hagen Urban"
ADR = "Krabatweg 27, 02977 Hoyerswerda"
FIRMA = "Senfkorn Holding GmbH"
KAP = "25.000,00"
SITZ = "Hoyerswerda"


def styles():
    ss = getSampleStyleSheet()
    base = dict(fontName="Body", textColor=DARK)
    for name, kw in [
        ("T", dict(fontName="BodyBold", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=3)),
        ("TS", dict(fontSize=10, leading=13, alignment=TA_CENTER, textColor=MUTED, spaceAfter=8)),
        ("W", dict(fontSize=8, leading=10.5, alignment=TA_JUSTIFY, textColor=HexColor("#5c4a00"), spaceAfter=8)),
        ("H", dict(fontName="BodyBold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=5)),
        ("B", dict(fontSize=9.5, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=3)),
        ("L", dict(fontSize=9.5, leading=12.5, leftIndent=10, spaceAfter=2)),
        ("M", dict(fontName="BodyBold", fontSize=9, leading=12, textColor=HexColor("#0d47a1"), spaceBefore=6, spaceAfter=4)),
        ("F", dict(fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=MUTED)),
        ("SM", dict(fontSize=8, leading=10.5, alignment=TA_JUSTIFY, textColor=MUTED, spaceAfter=2)),
    ]:
        ss.add(ParagraphStyle(name=name, **{**base, **kw}))
    return ss


def P(t, st, S):
    return Paragraph(t, S[st])


def chrome(c, doc):
    c.saveState()
    c.setFont("Body", 28)
    c.setFillColor(Color(0.75, 0.08, 0.08, alpha=0.09))
    c.translate(A4[0] / 2, A4[1] / 2)
    c.rotate(48)
    c.drawCentredString(0, 0, "ENTWURF — EINZAHLUNG / HR")
    c.rotate(-48)
    c.translate(-A4[0] / 2, -A4[1] / 2)
    c.setFillColor(MUTED)
    c.setFont("Body", 7)
    c.drawCentredString(A4[0] / 2, 1.1 * cm, f"{FIRMA} · Step 3 Einzahlung/HR · {OP} · S. {doc.page}")
    c.restoreState()


def story(S):
    out = [
        P("Einzahlung Stammkapital &amp; Handelsregister", "T", S),
        P(f"{FIRMA} · Coev Step 3", "TS", S),
        P(f"Operator {OP.replace('<', '&lt;')} · {TODAY} · Bob der Baumeister", "TS", S),
        HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceAfter=6),
        P(
            f"<b>Arbeitsanleitung · keine Rechts- oder Steuerberatung · kein Notarakt.</b> "
            f"Beschreibt den typischen Ablauf <b>nach</b> der notariellen Beurkundung bis zur "
            f"Eintragung der GmbH. Details und Formulare hängen von Notar, Bank und Registergericht ab. "
            f"Operator: <b>{OP.replace('<', '&lt;')}</b> · UTC {NOW}.",
            "W",
            S,
        ),
        P("0. Einordnung im Coev-Stack", "H", S),
    ]
    stack = [
        ["#", "Baustein", "Status"],
        ["1", "Notar-Vorbereitungspaket", "bereit (PDF)"],
        ["2", "GV COEV-MAX + IP-Lizenz ENTWURF", "bereit (PDF)"],
        ["3", "Einzahlung + HR (dieses Dokument)", "JETZT"],
        ["4", "Notar-Beurkundung", "extern / offen"],
        ["5", "Bank: Konto + EUR 25.000 Einzahlung", "dieses Step"],
        ["6", "Registergericht: Eintragung", "dieses Step"],
        ["7", "IP-Lizenz unterzeichnen + Impressum", "nach Eintragung"],
    ]
    rows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(stack)]
    t = Table(rows, colWidths=[1.0 * cm, 9.5 * cm, 5.8 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e8eef8")),
                ("BACKGROUND", (0, 3), (-1, 3), HexColor("#e8f5e9")),
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
        P("1. Stammdaten (Vorschlag — mit Notar/Bank abgleichen)", "H", S),
    ]
    master = [
        ["Feld", "Wert (Arbeitsstand)"],
        ["Firma", FIRMA],
        ["Sitz", SITZ],
        ["Stammkapital", f"EUR {KAP} (bar, voll)"],
        ["Gesellschafter / GF", f"{G}"],
        ["Adresse", ADR],
        ["Rechtsform", "GmbH (nicht UG)"],
        ["Gegenstand (Kurz)", "Holding: Beteiligungen + IP-Lizenzierung"],
    ]
    mrows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(master)]
    mt = Table(mrows, colWidths=[4.5 * cm, 11.8 * cm])
    mt.setStyle(
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
        mt,
        Spacer(1, 6),
        P("2. Phase A — Nach der Beurkundung, vor der Eintragung", "H", S),
        P(
            "(1) Der Notar fertigt die Gründungsurkunde und reicht in der Regel die Anmeldung zum "
            "Handelsregister elektronisch ein (oder steuert den Ablauf). Die GmbH <b>existiert im "
            "Rechtsverkehr als GmbH erst mit Eintragung</b>.",
            "B",
            S,
        ),
        P(
            "(2) Parallel: <b>Geschäftskonto</b> für die (künftige) Gesellschaft eröffnen. Viele Banken "
            "benötigen beglaubigte/notarielle Gründungsunterlagen und Ausweis des Geschäftsführers. "
            "Fragen Sie den Notar, welche Bank in der Region GmbH-Gründungen routiniert begleitet.",
            "B",
            S,
        ),
        P(
            "(3) <b>Einzahlung des Stammkapitals:</b> EUR 25.000,00 in bar (Überweisung) auf das "
            "Gesellschaftskonto. Verwendungszweck klar kennzeichnen, z. B.:",
            "B",
            S,
        ),
        P(
            f"<i>„Stammeinlage {FIRMA} — Geschäftsanteil Nr. 1 — {G} — EUR 25.000,00“</i>",
            "L",
            S,
        ),
        P(
            "(4) Einzahler ist der übernehmende Gesellschafter. Das Geld muss zur freien Verfügung der "
            "Geschäftsführung stehen (keine verdeckte Rückzahlung / keine unzulässige Belastung).",
            "B",
            S,
        ),
        P(
            "(5) <b>Bankbestätigung / Kontoauszug</b> beschaffen: Nachweis, dass der Betrag gutgeschrieben "
            "ist. Form und Wortlaut oft vom Notar oder Registergericht vorgegeben — Vorlage der Bank "
            "„Bestätigung über Einzahlung der Stammeinlage“ anfordern.",
            "B",
            S,
        ),
        P("3. Phase B — Handelsregister", "H", S),
        P(
            f"(1) Zuständig ist das Registergericht am Sitz der Gesellschaft (Arbeitsstand Sitz: "
            f"<b>{SITZ}</b> — zuständiges Amtsgericht / Registergericht mit Notar klären).",
            "B",
            S,
        ),
        P(
            "(2) Typische Einreichungen (über Notar / EGVP): Anmeldung der Gesellschaft, Satzung/"
            "Gesellschaftsvertrag, Gesellschafterliste, GF-Bestellung und Vertretungsregelung, "
            "Versicherung des Geschäftsführers, Nachweis der Einzahlung, ggf. weitere Anlagen.",
            "B",
            S,
        ),
        P(
            "(3) <b>Geschäftsführer-Versicherung</b> (inhaltlich, nicht abschließend): keine "
            "Bestellungshindernisse (§ 6 Abs. 2 GmbHG u. a.), korrekte Angaben — Wortlaut vom Notar.",
            "B",
            S,
        ),
        P(
            "(4) Nach Eintragung: <b>HRB-Nummer</b>, genauer Firmenwortlaut und Sitz aus dem Registerauszug "
            "übernehmen — das ist die maßgebliche öffentliche Identität der GmbH.",
            "B",
            S,
        ),
        P(
            "(5) Kosten: Notar + Gericht + Bank. Orientierung (nicht verbindlich): Gründungskosten-Cap "
            "im GV-Entwurf EUR 3.500 Gesellschaftsanteil; tatsächliche Rechnung kann abweichen.",
            "B",
            S,
        ),
        P("4. Checkliste Einzahlung (Checkbox)", "H", S),
        P("□ Notarielle Beurkundung erfolgt / Termin datum: _______________", "L", S),
        P("□ Bank für Geschäftskonto gewählt: _______________", "L", S),
        P("□ Konto eröffnet (IBAN): _______________", "L", S),
        P("□ EUR 25.000,00 überwiesen (Datum / Referenz): _______________", "L", S),
        P("□ Bankbestätigung / Auszug vorliegen (Datei/Ordner): _______________", "L", S),
        P("□ Nachweis an Notar übermittelt (Datum): _______________", "L", S),
        P("□ Registeranmeldung eingereicht (Datum): _______________", "L", S),
        P("□ Eintragung bekannt (HRB / Datum): _______________", "L", S),
        P("□ Registerauszug archiviert (Business-Ordner / Vault)", "L", S),
        P("5. Checkliste nach Eintragung (sofort)", "H", S),
        P("□ IP-Lizenz Holding → Senfkorn UG unterzeichnen (ENTWURF bereits vorbereitet)", "L", S),
        P("□ Impressum / 95guknow.github.io an Registerstand anpassen (GmbH vs. UG klären)", "L", S),
        P("□ Geschäftsbriefe / Footer: Firma, Sitz, HRB, GF (§ 35a GmbHG / HGB)", "L", S),
        P("□ Finanzamt: steuerliche Erfassung / Fragebogen (Steuerberater)", "L", S),
        P("□ Beteiligung an operativer UG dokumentieren (falls/ sobald geplant)", "L", S),
        P("□ Interne Coev-Matrix + GitHub-Governance aktualisieren", "L", S),
        P("□ Meister-Hasch / Public-Visuals: nur nach Copyright-Freigabe", "L", S),
        P("6. Muster-Verwendungszweck &amp; Ablage", "H", S),
        P(
            f"<b>Überweisung:</b> Empfänger = {FIRMA} (sobald Konto auf Firma läuft) · "
            f"Betrag EUR {KAP} · Verwendungszweck wie oben.<br/>"
            f"<b>Ablagepfad Vorschlag:</b> <font face='Courier'>business/register/</font> "
            f"(Beurkundung, Banknachweis, HR-Auszug, IP-Lizenz_signed).",
            "B",
            S,
        ),
        P("7. Risiken / typische Stolpersteine (kurz)", "H", S),
        P(
            "• Einzahlung <b>vor</b> Konto auf den richtigen Rechtsträger — mit Bank/Notar abstimmen "
            "(Gründungsstadium / treuhänderische Konten je nach Praxis).<br/>"
            "• Rücküberweisung an Gesellschafter kurz nach Einzahlung ohne Rechtsgrund (verdeckte "
            "Einlagenrückgewähr) vermeiden.<br/>"
            "• Abweichung Firma/Sitz/Adresse zwischen Urkunde, Bank und Register.<br/>"
            "• Public-Impressum weiter „Holding UG“, während GmbH schon eingetragen ist — Coev-Bruch.",
            "B",
            S,
        ),
        P("8. Ehrliche Grenze", "H", S),
        P(
            "Dieses Step-3-Dokument ist <b>operative Vollständigkeit der Checkliste</b>, nicht "
            "Registerrecht oder Bankrecht. 100&nbsp;% Legalität der GmbH: Beurkundung + freie "
            "Verfügbarkeit der Einlage + Eintragung. Für Formulare und Fristen: Notar, Bank, ggf. "
            "Rechtsanwalt/Steuerberater.",
            "B",
            S,
        ),
        Spacer(1, 12),
        P(
            f"Operator: {OP.replace('<', '&lt;')} · Coev Step 3 · {TODAY} · {PDF.name}",
            "F",
            S,
        ),
    ]
    return out


def main():
    S = styles()
    doc = SimpleDocTemplate(
        str(PDF),
        pagesize=A4,
        leftMargin=1.9 * cm,
        rightMargin=1.9 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.7 * cm,
        title=f"Einzahlung HR {FIRMA}",
        author="stephanhagenurban1 / Bob der Baumeister",
    )
    doc.build(story(S), onFirstPage=chrome, onLaterPages=chrome)
    (OUT / "register").mkdir(exist_ok=True)
    (OUT / "register" / "README.md").write_text(
        f"""# register/ — Nachweise Einzahlung &amp; HR

**Firma:** {FIRMA}  
**Operator:** {OP}  
**Step-3-PDF:** `../{PDF.name}`

## Ablage (nach Erhalt)

| Datei | Inhalt |
|-------|--------|
| `01_beurkundung.pdf` | notarielle Gründungsurkunde |
| `02_bank_kontoeroeffnung.pdf` | Kontoeröffnung |
| `03_einzahlung_nachweis.pdf` | Überweisung / Bankbestätigung EUR 25.000 |
| `04_hr_anmeldung.pdf` | Registeranmeldung / Eingangsbestätigung |
| `05_hr_auszug.pdf` | Handelsregisterauszug nach Eintragung |
| `06_ip_lizenz_signed.pdf` | unterzeichnete IP-Lizenz Holding→UG |

*Ordner leer bis echte Dokumente vorliegen.*
""",
        encoding="utf-8",
    )
    MD.write_text(
        f"# Einzahlung + HR — Coev Step 3\n\nOperator: `{OP}`  \nPDF: `{PDF}`  \n{NOW}\n",
        encoding="utf-8",
    )
    ops = Path.home() / ".fusion" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    (ops / "einzahlung_hr_step3_ack.json").write_text(
        f'{{"phrase":"{OP}","step":3,"at":"{NOW}","pdf":"{PDF.as_posix()}"}}\n',
        encoding="utf-8",
    )
    print("PDF", PDF, PDF.stat().st_size)
    print("DIR", OUT / "register")


if __name__ == "__main__":
    main()
