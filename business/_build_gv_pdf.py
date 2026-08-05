# -*- coding: utf-8 -*-
"""Bob der Baumeister: Gesellschaftsvertrag Senfkorn Holding GmbH — ENTWURF PDF."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1] if (Path(__file__).name != "build_gesellschaftsvertrag_pdf.py") else Path.cwd()
# script will live in business/ or scripts/
OUT_DIR = Path(r"C:\Users\Admin\fusion-hero-os\business")
OUT_PDF = OUT_DIR / "Senfkorn_Holding_GmbH_Gesellschaftsvertrag_ENTWURF.pdf"
OUT_MD = OUT_DIR / "Senfkorn_Holding_GmbH_Gesellschaftsvertrag_ENTWURF.md"

# Fonts (Windows)
for name, path in (
    ("Body", r"C:\Windows\Fonts\arial.ttf"),
    ("BodyBold", r"C:\Windows\Fonts\arialbd.ttf"),
    ("BodyItalic", r"C:\Windows\Fonts\ariali.ttf"),
):
    pdfmetrics.registerFont(TTFont(name, path))

TODAY = date.today().isoformat()
GOLD = HexColor("#b8860b")
DARK = HexColor("#1a1a1a")
MUTED = HexColor("#444444")
WARN_BG = HexColor("#fff3cd")
WARN_BORDER = HexColor("#856404")


def styles():
    ss = getSampleStyleSheet()
    ss.add(
        ParagraphStyle(
            name="DocTitle",
            fontName="BodyBold",
            fontSize=16,
            leading=20,
            alignment=TA_CENTER,
            textColor=DARK,
            spaceAfter=4,
        )
    )
    ss.add(
        ParagraphStyle(
            name="DocSub",
            fontName="Body",
            fontSize=12,
            leading=15,
            alignment=TA_CENTER,
            textColor=MUTED,
            spaceAfter=12,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Warn",
            fontName="Body",
            fontSize=8.5,
            leading=11,
            alignment=TA_JUSTIFY,
            textColor=HexColor("#664d03"),
            spaceBefore=4,
            spaceAfter=10,
        )
    )
    ss.add(
        ParagraphStyle(
            name="ParaH",
            fontName="BodyBold",
            fontSize=11,
            leading=14,
            textColor=DARK,
            spaceBefore=14,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            name="BodyJ",
            fontName="Body",
            fontSize=10,
            leading=13.5,
            alignment=TA_JUSTIFY,
            textColor=DARK,
            spaceAfter=4,
        )
    )
    ss.add(
        ParagraphStyle(
            name="BodyL",
            fontName="Body",
            fontSize=10,
            leading=13.5,
            alignment=TA_LEFT,
            textColor=DARK,
            leftIndent=12,
            spaceAfter=2,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Footer",
            fontName="Body",
            fontSize=8,
            leading=10,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
    )
    ss.add(
        ParagraphStyle(
            name="Sig",
            fontName="Body",
            fontSize=9,
            leading=12,
            textColor=DARK,
            spaceBefore=6,
        )
    )
    return ss


def p(text: str, style: str, S) -> Paragraph:
    return Paragraph(text.replace("\n", "<br/>"), S[style])


def section(title: str, body_blocks: list, S) -> list:
    out = [p(title, "ParaH", S)]
    out.extend(body_blocks)
    return out


def build_story(S):
    story = []
    story.append(p("Gesellschaftsvertrag", "DocTitle", S))
    story.append(p("der", "DocSub", S))
    story.append(p("<b>Senfkorn Holding GmbH</b>", "DocTitle", S))
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8))

    warn = (
        "<b>ENTWURF · Bob der Baumeister / Arbeitsfassung · kein Notarakt · keine Beurkundung · "
        "kein Handelsregisterstand.</b> Dieses Dokument ist eine <b>private Arbeitsvorlage</b> "
        "zur Vorbereitung einer GmbH-Gründung. Es ersetzt keine notarielle Beratung oder Beurkundung "
        f"(§ 2 GmbHG). Stand der Vorlage: {TODAY}. Platzhalter und aus dem öffentlichen Impressum "
        "übernommene Angaben (Sitz Hoyerswerda, Name) sind <b>zu prüfen und freizugeben</b>. "
        "Abweichung zum Live-Impressum: dort „Senfkorn Holding UG“ — dieser Entwurf wählt bewusst "
        "die Rechtsform <b>GmbH</b> (Stammkapital EUR 25.000)."
    )
    story.append(p(warn, "Warn", S))
    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED, spaceAfter=10))

    # § 1
    story += section(
        "§ 1 Firma, Sitz, Dauer",
        [
            p("(1) Die Gesellschaft führt die Firma „Senfkorn Holding GmbH“.", "BodyJ", S),
            p(
                "(2) Sitz der Gesellschaft ist <b>Hoyerswerda</b> "
                "(Vorschlag aus öffentlichem Impressum; endgültig vom Notar/Gründer festzulegen).",
                "BodyJ",
                S,
            ),
            p("(3) Die Gesellschaft ist auf unbestimmte Zeit errichtet.", "BodyJ", S),
        ],
        S,
    )

    # § 2
    story += section(
        "§ 2 Gegenstand des Unternehmens",
        [
            p(
                "(1) Gegenstand des Unternehmens ist das Halten und Verwalten von Beteiligungen an in- und "
                "ausländischen Unternehmen, insbesondere an der <b>Senfkorn UG (haftungsbeschränkt)</b> und "
                "weiteren operativen sowie kapitalverwaltenden Einheiten, sowie das Halten, die Verwaltung und "
                "Lizenzierung von geistigen Eigentumsrechten (IP).",
                "BodyJ",
                S,
            ),
            p(
                "(2) Zu den geistigen Eigentumsrechten zählen insbesondere Marken-, Domain-, Software- und "
                "Konzeptrechte rund um die Senfkorn-Angebote, einschließlich, aber nicht abschließend:",
                "BodyJ",
                S,
            ),
            p("a) „Fusion Hero OS“,", "BodyL", S),
            p("b) die sog. „heroische Mathematik“ im Senfkorn-Kontext,", "BodyL", S),
            p("c) Konzepte und Architekturen für „WIR Mesh“,", "BodyL", S),
            p(
                "d) Quantizer-Konzepte (z. B. String-Quantizer, Sinnquanten-Registry, M→N-Quant-DB),",
                "BodyL",
                S,
            ),
            p(
                "e) weitere im internen IP-Register aufgeführte Schutz- und Nutzungsrechte.",
                "BodyL",
                S,
            ),
            p("(3) Die Gesellschaft kann zur Erfüllung ihres Gegenstands insbesondere:", "BodyJ", S),
            p(
                "a) Management-, Beratungs- und IP-Lizenzleistungen gegenüber verbundenen Unternehmen erbringen,",
                "BodyL",
                S,
            ),
            p("b) Beteiligungen erwerben, halten, verwalten und veräußern,", "BodyL", S),
            p(
                "c) Darlehen gewähren und aufnehmen, soweit sie dem Unternehmensgegenstand dienen,",
                "BodyL",
                S,
            ),
            p(
                "d) alle sonstigen Geschäfte tätigen, die mit dem Gesellschaftszweck unmittelbar oder "
                "mittelbar zusammenhängen.",
                "BodyL",
                S,
            ),
        ],
        S,
    )

    # § 3
    story += section(
        "§ 3 Stammkapital",
        [
            p(
                "(1) Das Stammkapital der Gesellschaft beträgt <b>EUR 25.000</b> "
                "(in Worten: fünfundzwanzigtausend Euro).",
                "BodyJ",
                S,
            ),
            p("(2) Das Stammkapital wird wie folgt übernommen:", "BodyJ", S),
            p(
                "a) <b>Stephan Hagen Urban</b>, Krabatweg 27, 02977 Hoyerswerda "
                "(Angabe gemäß öffentlichem Impressum — <b>Gründerangabe freigeben</b>), "
                "übernimmt einen Geschäftsanteil mit einem Nennbetrag von <b>EUR 25.000</b>.",
                "BodyL",
                S,
            ),
            p(
                "(3) Das Stammkapital ist in voller Höhe in bar zu erbringen, sofern im Gründungsprotokoll "
                "nichts Abweichendes vorgesehen ist.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 4
    story += section(
        "§ 4 Geschäftsanteile",
        [
            p("(1) Die Geschäftsanteile sind in Nennbeträgen ausgewiesen.", "BodyJ", S),
            p(
                "(2) Jeder Euro des Nennbetrags eines Geschäftsanteils gewährt eine Stimme in der "
                "Gesellschafterversammlung, soweit gesetzlich nichts anderes bestimmt ist.",
                "BodyJ",
                S,
            ),
            p(
                "(3) Die Abtretung von Geschäftsanteilen bedarf zu ihrer Wirksamkeit der Zustimmung der "
                "Gesellschafterversammlung (Vinkulierung). Die Zustimmung bedarf der Mehrheit der abgegebenen "
                "Stimmen und ist notariell zu beurkunden, soweit das Gesetz dies verlangt.",
                "BodyJ",
                S,
            ),
            p(
                "(4) Die Teilung und Zusammenlegung von Geschäftsanteilen ist mit Zustimmung der "
                "Gesellschafterversammlung zulässig.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 5
    story += section(
        "§ 5 Geschäftsführung und Vertretung",
        [
            p("(1) Die Gesellschaft hat einen oder mehrere Geschäftsführer.", "BodyJ", S),
            p(
                "(2) Ist nur ein Geschäftsführer bestellt, vertritt er die Gesellschaft allein. "
                "Sind mehrere Geschäftsführer bestellt, so wird die Gesellschaft durch zwei Geschäftsführer "
                "gemeinschaftlich oder durch einen Geschäftsführer in Gemeinschaft mit einem Prokuristen vertreten, "
                "sofern die Gesellschafterversammlung nicht Einzelvertretungsbefugnis erteilt.",
                "BodyJ",
                S,
            ),
            p(
                "(3) Zum Geschäftsführer wird bestellt: <b>Stephan Hagen Urban</b>, Anschrift wie § 3 Abs. 2 "
                "(Vorschlag — freigeben). Ihm wird Einzelvertretungsbefugnis erteilt.",
                "BodyJ",
                S,
            ),
            p(
                "(4) Der Geschäftsführer ist von den Beschränkungen des § 181 BGB befreit "
                "(Insichgeschäft / Doppelvertretung) — <b>[ja — Vorschlag; Notar/Gesellschafter bestätigen]</b>.",
                "BodyJ",
                S,
            ),
            p(
                "(5) Die Gesellschafterversammlung kann weitere Geschäftsführer bestellen und abberufen sowie "
                "den Umfang der Vertretungs- und Geschäftsführungsbefugnis regeln.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 6
    story += section(
        "§ 6 Gesellschafterversammlung",
        [
            p(
                "(1) Die Angelegenheiten der Gesellschaft werden, soweit nicht die Geschäftsführung zuständig ist, "
                "durch Beschlussfassung der Gesellschafter geordnet.",
                "BodyJ",
                S,
            ),
            p(
                "(2) Die Gesellschafterversammlung ist insbesondere zuständig für: Feststellung des Jahresabschlusses, "
                "Verwendung des Ergebnisses, Bestellung und Abberufung von Geschäftsführern, Entlastung, "
                "Maßnahmen der Kapitalbeschaffung und -herabsetzung, Satzungsänderungen, Auflösung der Gesellschaft, "
                "Zustimmung zur Abtretung von Geschäftsanteilen.",
                "BodyJ",
                S,
            ),
            p(
                "(3) Die Einberufung erfolgt durch die Geschäftsführung unter Angabe der Tagesordnung mit einer "
                "Frist von mindestens einer Woche in Textform (z. B. E-Mail), soweit das Gesetz nichts anderes bestimmt.",
                "BodyJ",
                S,
            ),
            p(
                "(4) Die Gesellschafterversammlung ist beschlussfähig, wenn die anwesenden oder vertretenen "
                "Stimmen mindestens die Hälfte des Stammkapitals vertreten. Beschlüsse werden mit einfacher Mehrheit "
                "der abgegebenen Stimmen gefasst, soweit Gesetz oder dieser Vertrag keine größere Mehrheit vorsehen.",
                "BodyJ",
                S,
            ),
            p(
                "(5) Bei der Ein-Personen-Gesellschaft gelten die gesetzlichen Erleichterungen; Beschlüsse sind "
                "unverzüglich zu protokollieren und zu unterzeichnen.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 7
    story += section(
        "§ 7 Geschäftsjahr, Jahresabschluss",
        [
            p("(1) Das Geschäftsjahr ist das Kalenderjahr.", "BodyJ", S),
            p(
                "(2) Das erste Geschäftsjahr ist ein Rumpfgeschäftsjahr; es beginnt mit der Eintragung der "
                "Gesellschaft in das Handelsregister und endet am 31. Dezember desselben Kalenderjahres.",
                "BodyJ",
                S,
            ),
            p(
                "(3) Die Geschäftsführung hat den Jahresabschluss (Bilanz, Gewinn- und Verlustrechnung sowie "
                "Anhang) und — soweit gesetzlich erforderlich — den Lagebericht innerhalb der gesetzlichen Fristen "
                "aufzustellen und den Gesellschaftern vorzulegen.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 8
    story += section(
        "§ 8 Ergebnisverwendung",
        [
            p(
                "(1) Über die Verwendung des Jahresergebnisses beschließt die Gesellschafterversammlung.",
                "BodyJ",
                S,
            ),
            p(
                "(2) Solange die gesetzlichen Rücklagenvorschriften und eine etwaige gesellschaftsvertragliche "
                "Rücklagenpolitik dies erfordern, ist vor Ausschüttungen hierauf Rücksicht zu nehmen.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 9
    story += section(
        "§ 9 Einziehung von Geschäftsanteilen",
        [
            p(
                "(1) Die Einziehung von Geschäftsanteilen ist mit Zustimmung des betroffenen Gesellschafters "
                "oder aus wichtigem Grund ohne dessen Zustimmung zulässig.",
                "BodyJ",
                S,
            ),
            p(
                "(2) Ein wichtiger Grund liegt insbesondere vor bei: Eröffnung des Insolvenzverfahrens über das "
                "Vermögen des Gesellschafters, Pfändung des Geschäftsanteils, wenn sie nicht binnen drei Monaten "
                "aufgehoben wird, grober Verletzung gesellschaftsrechtlicher Pflichten.",
                "BodyJ",
                S,
            ),
            p(
                "(3) Die Abfindung bemisst sich mangels abweichender Vereinbarung nach dem Verkehrswert des "
                "Geschäftanteils zum Zeitpunkt des Einziehungsbeschlusses; das Nähere kann die "
                "Gesellschafterversammlung regeln. <i>[Abfindungsformel mit Steuerberater/Notar schärfen.]</i>",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 10
    story += section(
        "§ 10 Bekanntmachungen",
        [
            p(
                "Bekanntmachungen der Gesellschaft erfolgen im Bundesanzeiger, soweit gesetzlich nichts anderes "
                "bestimmt ist.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 11
    story += section(
        "§ 11 Gründungsaufwand",
        [
            p(
                "Die Gesellschaft trägt die mit der Gründung verbundenen Kosten (Notar, Gericht, Bekanntmachungen) "
                "bis zu einem Gesamtbetrag von <b>EUR 2.500</b> "
                "(Höchstbetrag — bei Bedarf anpassen).",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 12
    story += section(
        "§ 12 Salvatorische Klausel",
        [
            p(
                "(1) Sollten einzelne Bestimmungen dieses Vertrags unwirksam oder undurchführbar sein oder werden, "
                "bleibt die Wirksamkeit der übrigen Bestimmungen unberührt.",
                "BodyJ",
                S,
            ),
            p(
                "(2) An die Stelle der unwirksamen oder undurchführbaren Bestimmung soll diejenige wirksame und "
                "durchführbare Regelung treten, deren Wirkungen der wirtschaftlichen Zielsetzung am nächsten kommen, "
                "die die Gesellschafter mit der unwirksamen bzw. undurchführbaren Bestimmung verfolgt haben. "
                "Die vorstehenden Bestimmungen gelten entsprechend für den Fall, dass sich der Vertrag als lückenhaft erweist.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    # § 13
    story += section(
        "§ 13 Schlussbestimmungen",
        [
            p(
                "(1) Änderungen dieses Vertrags bedürfen der notariellen Beurkundung, soweit gesetzlich vorgeschrieben.",
                "BodyJ",
                S,
            ),
            p(
                "(2) Gerichtsstand für alle Streitigkeiten aus diesem Vertrag ist — soweit zulässig — der Sitz der "
                "Gesellschaft.",
                "BodyJ",
                S,
            ),
            p(
                "(3) Es gilt das Recht der Bundesrepublik Deutschland.",
                "BodyJ",
                S,
            ),
        ],
        S,
    )

    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceBefore=8, spaceAfter=10))
    story.append(p("<b>Hinweis zur IP- und Konzernstruktur (nicht satzungsersetzend)</b>", "ParaH", S))
    story.append(
        p(
            "Operative Tätigkeiten und öffentliche Anbieterkennzeichnung können bei verbundenen Unternehmen "
            "(z. B. Senfkorn UG (haftungsbeschränkt)) verbleiben. Die Holding hält und lizenziert IP und "
            "Beteiligungen gemäß § 2. Abgrenzung Impressum / Domain / GitHub-Organisationen ist gesondert "
            "in der Governance- und IP-Dokumentation zu führen.",
            "BodyJ",
            S,
        )
    )

    story.append(Spacer(1, 20))
    story.append(p("<b>Unterschriften (nur nach notarieller Beurkundung maßgeblich)</b>", "ParaH", S))
    story.append(Spacer(1, 16))
    story.append(
        p(
            "Ort, Datum: ____________________________ &nbsp;&nbsp;&nbsp; "
            "Gründer / Gesellschafter: ____________________________",
            "Sig",
            S,
        )
    )
    story.append(Spacer(1, 20))
    story.append(
        p(
            "Notar: ____________________________ &nbsp;&nbsp;&nbsp; "
            "Urkundenrolle Nr.: ____________________________",
            "Sig",
            S,
        )
    )

    story.append(Spacer(1, 24))
    story.append(
        p(
            f"<i>Bob der Baumeister · Fusion Hero OS / Senfkorn Arbeitsvorlage · {TODAY} · "
            "Datei: Senfkorn_Holding_GmbH_Gesellschaftsvertrag_ENTWURF.pdf</i>",
            "Footer",
            S,
        )
    )
    return story


def add_page_elements(canvas, doc):
    canvas.saveState()
    # watermark
    canvas.setFont("Body", 40)
    canvas.setFillColor(Color(0.85, 0.1, 0.1, alpha=0.12))
    canvas.translate(A4[0] / 2, A4[1] / 2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "ENTWURF — KEIN NOTARAKT")
    canvas.rotate(-45)
    canvas.translate(-A4[0] / 2, -A4[1] / 2)
    # footer page number
    canvas.setFillColor(MUTED)
    canvas.setFont("Body", 8)
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, f"Senfkorn Holding GmbH — Gesellschaftsvertrag ENTWURF · Seite {doc.page}")
    canvas.restoreState()


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    S = styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=1.8 * cm,
        bottomMargin=2.0 * cm,
        title="Gesellschaftsvertrag Senfkorn Holding GmbH (ENTWURF)",
        author="Senfkorn / Bob der Baumeister — Arbeitsvorlage",
        subject="ENTWURF — keine Beurkundung",
    )
    doc.build(build_story(S), onFirstPage=add_page_elements, onLaterPages=add_page_elements)
    print("PDF:", OUT_PDF, "bytes=", OUT_PDF.stat().st_size)

    # also markdown twin
    OUT_MD.write_text(
        f"""# Gesellschaftsvertrag der Senfkorn Holding GmbH

> **ENTWURF · {TODAY} · kein Notarakt · keine Beurkundung**  
> Bob der Baumeister / Arbeitsvorlage. PDF: `{OUT_PDF.name}`

*(Volltext entspricht dem PDF-Inhalt; zur Beurkundung Notar aufsuchen.)*
""",
        encoding="utf-8",
    )
    print("MD stub:", OUT_MD)


if __name__ == "__main__":
    main()
