# -*- coding: utf-8 -*-
"""IP-Lizenzvertrag Senfkorn Holding GmbH → Senfkorn UG (haftungsbeschränkt) — ENTWURF.
Operator: =====stephanhagenurban1 <3
Coev zu Gesellschaftsvertrag COEV-MAX § 10.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parent
PDF = OUT / "Senfkorn_IP_Lizenzvertrag_Holding_zu_UG_ENTWURF.pdf"
MD = OUT / "Senfkorn_IP_Lizenzvertrag_Holding_zu_UG_ENTWURF.md"
HASCH = Path(r"C:\Users\Admin\fusion-hero-os\journal\meister_hasch.png")

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
ACCENT = HexColor("#0d47a1")

LIZENZGEBER = "Senfkorn Holding GmbH"
LIZENZNEHMER = "Senfkorn UG (haftungsbeschränkt)"
VERTRETER = "Stephan Hagen Urban"
ADR = "Krabatweg 27, 02977 Hoyerswerda, Deutschland"
OP = "=====stephanhagenurban1 <3"


def styles():
    ss = getSampleStyleSheet()
    base = dict(fontName="Body", textColor=DARK)
    for name, kw in [
        ("T", dict(fontName="BodyBold", fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=2)),
        ("TS", dict(fontSize=10, leading=13, alignment=TA_CENTER, textColor=MUTED, spaceAfter=6)),
        ("W", dict(fontSize=8, leading=10.5, alignment=TA_JUSTIFY, textColor=HexColor("#5c4a00"), spaceAfter=8)),
        ("H", dict(fontName="BodyBold", fontSize=10.5, leading=13, spaceBefore=10, spaceAfter=4)),
        ("B", dict(fontSize=9.5, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=3)),
        ("L", dict(fontSize=9.5, leading=12.5, leftIndent=12, spaceAfter=1.5)),
        ("M", dict(fontName="BodyBold", fontSize=9, leading=12, textColor=ACCENT, spaceBefore=6, spaceAfter=4)),
        ("F", dict(fontSize=7.5, leading=9.5, alignment=TA_CENTER, textColor=MUTED)),
        ("SIG", dict(fontSize=9, leading=12, spaceBefore=4)),
        ("SM", dict(fontSize=7.5, leading=10, alignment=TA_JUSTIFY, textColor=MUTED, spaceAfter=2)),
    ]:
        ss.add(ParagraphStyle(name=name, **{**base, **kw}))
    return ss


def P(t, st, S):
    return Paragraph(t, S[st])


def b(t, S):
    return P(t, "B", S)


def L(t, S):
    return P(t, "L", S)


def sec(t, S):
    return P(t, "H", S)


def story(S):
    out = []
    # optional brand mark — private business path only
    if HASCH.is_file():
        try:
            img = Image(str(HASCH), width=2.2 * cm, height=2.2 * cm, hAlign="CENTER")
            out.append(img)
            out.append(Spacer(1, 4))
            out.append(P("<i>Meister Hasch · Senfkorn Visual (privat / ENTWURF)</i>", "TS", S))
        except Exception:
            pass

    out += [
        P("IP-Lizenzvertrag", "T", S),
        P("(Arbeitsfassung / ENTWURF)", "TS", S),
        P(f"<b>{LIZENZGEBER}</b>", "T", S),
        P("— als Lizenzgeber —", "TS", S),
        P("und", "TS", S),
        P(f"<b>{LIZENZNEHMER}</b>", "T", S),
        P("— als Lizenznehmer —", "TS", S),
        P(f"Coev zu GV Holding § 10 · Operator {OP.replace('<', '&lt;')} · {TODAY}", "TS", S),
        HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceAfter=6),
        P(
            f"<b>ENTWURF · KEIN NOTARAKT · KEIN REGISTERSTAND · KEINE AUTOMATISCHE RECHTSWIRKSAMKEIT.</b> "
            f"Dieses Dokument ist eine <b>private Arbeitsvorlage</b> zur Coevolution mit dem "
            f"Gesellschaftsvertrag der {LIZENZGEBER} (COEV-MAX). Wirksamkeit erst durch "
            f"Unterzeichnung beider Parteien (nach wirksamer Existenz der Holding-GmbH) und — soweit "
            f"gewünscht — anwaltliche Prüfung. Operator-Freigabe: <b>{OP.replace('<', '&lt;')}</b> · UTC {NOW}. "
            f"Abbildung „Meister Hasch“ dient nur der internen Markenidentität im Business-Ordner; "
            f"sie ist <b>kein</b> Lizenzgegenstand und nicht für Public-Pfade freigegeben, solange "
            f"Copyright-/Publikationsregeln im Repo etwas anderes vorsehen.",
            "W",
            S,
        ),
        HRFlowable(width="100%", thickness=0.4, color=MUTED, spaceAfter=6),
        P("0. Parteien und Coev-Kontext", "M", S),
    ]

    rows = [
        ["Rolle", "Partei", "Vertretung (Vorschlag)"],
        ["Lizenzgeber", LIZENZGEBER, f"{VERTRETER} (GF, nach Gründung)"],
        ["Lizenznehmer", LIZENZNEHMER, f"{VERTRETER} (GF)"],
        ["Anschrift (Vorschlag)", ADR, "wie Impressum — freigeben"],
        ["Satzungshook", "Holding-GV § 10", "IP-Lizenz an verbundene UG"],
        ["IP-Kanon", "Fusion Hero OS · heroische Mathematik · WIR Mesh · Quantizer", "§ 2 dieses Vertrags"],
    ]
    trows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(rows)]
    tbl = Table(trows, colWidths=[3.2 * cm, 8.5 * cm, 4.8 * cm])
    tbl.setStyle(
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
    out += [tbl, Spacer(1, 6)]

    out += [
        sec("§ 1 Vertragsgegenstand und Begriffsbestimmungen", S),
        b(
            "(1) Der Lizenzgeber räumt dem Lizenznehmer die nach Maßgabe dieses Vertrags näher bestimmten "
            "Nutzungsrechte an den in § 2 bezeichneten Schutzgegenständen (nachfolgend „Lizenz-IP“) ein.",
            S,
        ),
        b(
            "(2) „Verbundenes Unternehmen“ meint Unternehmen im Sinne der §§ 15 ff. AktG analog, insbesondere "
            "solche, an denen der Lizenzgeber mehrheitlich beteiligt ist oder die unter einheitlicher Leitung stehen.",
            S,
        ),
        b(
            "(3) „Kern-IP“ meint die in § 2 Abs. 1 lit. a–e genannten Gegenstände einschließlich ihrer "
            "Dokumentation, Spezifikationen, Markenzeichen und zugehörigen Know-how-Unterlagen, soweit sie "
            "im IP-Register des Lizenzgebers geführt werden.",
            S,
        ),
        b(
            "(4) „Weiterentwicklung“ meint Änderungen, Verbesserungen, Anpassungen, Forks, Module und "
            "abgeleitete Werke am Lizenz-IP, unabhängig vom Speichermedium (einschließlich Git-Repositories).",
            S,
        ),
        sec("§ 2 Lizenz-IP (Katalog)", S),
        b(
            "(1) Gegenstand der Lizenz ist das Kern-IP, einschließlich, aber nicht abschließend:",
            S,
        ),
        L("a) „Fusion Hero OS“ (Software, Module, Dokumentation, Konfigurationen, Versionen und Derivate);", S),
        L("b) „heroische Mathematik“ und verwandte Formalismen im Senfkorn-Kontext;", S),
        L("c) „WIR Mesh“ und verwandte Mesh-/Polyzell-Architekturen und -Konzepte;", S),
        L(
            "d) Quantizer-Konzepte (u. a. String-Quantizer, Sinnquanten-Registry, M→N-Quant-DB) und Register;",
            S,
        ),
        L(
            "e) Marken-, Domain-, Konzept- und Know-how-Rechte der Senfkorn-Gruppe, soweit im internen "
            "IP-Register dem Lizenzgeber zugeordnet;",
            S,
        ),
        L(
            "f) weitere, vom Lizenzgeber schriftlich (Textform genügt) in das Lizenz-IP aufgenommene Positionen.",
            S,
        ),
        b(
            "(2) Nicht Gegenstand dieses Vertrags sind: (i) Rechte Dritter, (ii) Open-Source-Komponenten "
            "unter fremden Lizenzen (diese bleiben unter ihren jeweiligen Bedingungen nutzbar), "
            "(iii) personenbezogene Daten Dritter, (iv) die Bilddatei „meister_hasch.png“ und verwandte "
            "Visuals, soweit sie gesonderten Copyright-/Publikationsregeln unterliegen — deren Nutzung "
            "bedarf einer <b>separaten Visual-Freigabe</b>.",
            S,
        ),
        b(
            "(3) Das IP-Register des Lizenzgebers ist maßgeblich für die fortlaufende Konkretisierung des "
            "Lizenz-IP. Der Lizenzgeber stellt dem Lizenznehmer auf Anfrage eine aktuelle Auszugskopie zu.",
            S,
        ),
        sec("§ 3 Lizenzumfang", S),
        b(
            "(1) Der Lizenzgeber räumt dem Lizenznehmer ein <b>nicht ausschließliches</b>, "
            "<b>nicht übertragbares</b> (außer nach § 9), <b>räumlich unbeschränktes</b> und "
            "<b>inhaltlich auf den Unternehmensgegenstand des Lizenznehmers begrenztes</b> Recht ein, "
            "das Lizenz-IP zu nutzen.",
            S,
        ),
        b("(2) Die Nutzung umfasst insbesondere das Recht:", S),
        L("a) das Lizenz-IP zu speichern, zu laden, auszuführen und intern zu betreiben;", S),
        L("b) das Lizenz-IP zu analysieren, zu testen und weiterzuentwickeln;", S),
        L(
            "c) das Lizenz-IP in Produkten, Diensten, Dokumentationen und öffentlichen Auftritten des "
            "Lizenznehmers zu verwenden, soweit nicht Visual-Sperren (§ 2 Abs. 2) entgegenstehen;",
            S,
        ),
        L(
            "d) Unterlizenzen an Endnutzer nur in Form standardisierter EULA/ToS zu erteilen, die die "
            "Rechte des Lizenzgebers wahren und keine weitergehende Übertragung von Kern-IP bewirken;",
            S,
        ),
        L(
            "e) Repositories unter den Organisationen des Lizenznehmers und freigegebenen Dual-Org-Pfaden "
            "zu führen, ohne dass dadurch IP-Inhaberschaft übergeht.",
            S,
        ),
        b(
            "(3) <b>Nicht</b> gestattet ist ohne vorherige schriftliche Zustimmung des Lizenzgebers:",
            S,
        ),
        L("a) die Übertragung der Inhaberschaft am Kern-IP;", S),
        L("b) die Einräumung ausschließlicher Rechte an Dritte am Kern-IP;", S),
        L("c) die Verwendung des Lizenz-IP für rechtswidrige Zwecke;", S),
        L(
            "d) die Veröffentlichung sensibler interner Schlüssel, Vaults, PII oder als intern markierter Artefakte.",
            S,
        ),
        sec("§ 4 Inhaberschaft und Weiterentwicklungen", S),
        b(
            "(1) Alle Rechte am Lizenz-IP verbleiben beim Lizenzgeber, soweit dieser Vertrag nichts anderes bestimmt.",
            S,
        ),
        b(
            "(2) <b>Weiterentwicklungen</b> durch den Lizenznehmer am Kern-IP stehen im Zweifel dem "
            "<b>Lizenzgeber</b> zu (Arbeitgeber-/Konzern-IP-Logik analog). Der Lizenznehmer erhält daran "
            "automatisch eine Lizenz im Umfang dieses Vertrags.",
            S,
        ),
        b(
            "(3) Abweichende Zuordnung einzelner Module kann im IP-Register oder durch gesonderte "
            "schriftliche Vereinbarung geregelt werden (z. B. rein operative Markenauftritte der UG).",
            S,
        ),
        b(
            "(4) Dual-Org-Code (z. B. GitHub 95guknow und Senfkorn-UG) ändert für sich genommen weder "
            "Inhaberschaft noch diesen Lizenzumfang.",
            S,
        ),
        sec("§ 5 Lizenzgebühr", S),
        b(
            "(1) Bis zu einer abweichenden schriftlichen Vereinbarung ist die Lizenz für verbundene Unternehmen "
            "<b>konzernintern unentgeltlich</b> (Null-Royalties), soweit steuer- und gesellschaftsrechtlich zulässig.",
            S,
        ),
        b(
            "(2) Die Parteien können eine marktübliche Vergütung, Umlage oder Konzernverrechnung "
            "nachträglich vereinbaren (Textform). Steuerliche Organschaft oder Verrechnungspreisregeln "
            "bleiben unberührt und sind mit dem Steuerberater abzustimmen.",
            S,
        ),
        b(
            "(3) Externe (nicht verbundene) Unterlizenzen oder Vertrieb an Dritte können gesonderte "
            "Gebühren auslösen, die vorab schriftlich festzulegen sind.",
            S,
        ),
        sec("§ 6 Pflichten des Lizenznehmers", S),
        b("(1) Der Lizenznehmer wird das Lizenz-IP nur im vereinbarten Umfang nutzen.", S),
        b(
            "(2) Der Lizenznehmer kennzeichnet öffentliche Anbieterseiten und Impressen wahrheitsgemäß "
            "und stimmt sie mit dem Lizenzgeber ab, sobald die Holding eingetragen ist.",
            S,
        ),
        b(
            "(3) Sicherheits-, PII-, Consent- und Copyright-Regeln des Fusion-Hero-OS-/Senfkorn-Kanons "
            "sind einzuhalten (fail-closed wo so spezifiziert).",
            S,
        ),
        b(
            "(4) Der Lizenznehmer informiert den Lizenzgeber unverzüglich über behauptete Rechtsverletzungen "
            "Dritter und über bekannt gewordene Sicherheitsvorfälle mit Bezug zum Lizenz-IP.",
            S,
        ),
        sec("§ 7 Pflichten und Gewährleistung des Lizenzgebers", S),
        b(
            "(1) Der Lizenzgeber sichert zu, dass er — nach Maßgabe der bei Vertragsbeginn bekannten Lage — "
            "berechtigt ist, die eingeräumten Rechte zu vergeben. Spezielle Rechtsmängelhaftung für "
            "Open-Source-Bestandteile Dritter wird ausgeschlossen, soweit gesetzlich zulässig.",
            S,
        ),
        b(
            "(2) Das Lizenz-IP wird „wie besehen“ (as is) überlassen, soweit nicht zwingendes Recht entgegensteht. "
            "Insbesondere werden keine Zusicherungen für ununterbrochene Verfügbarkeit oder Eignung für "
            "einen bestimmten wirtschaftlichen Erfolg übernommen.",
            S,
        ),
        b(
            "(3) Zwingende gesetzliche Ansprüche (z. B. bei Vorsatz, grober Fahrlässigkeit, Verletzung von "
            "Leben/Körper/Gesundheit, Produkthaftung) bleiben unberührt.",
            S,
        ),
        sec("§ 8 Haftung", S),
        b(
            "(1) Die Parteien haften unbeschränkt bei Vorsatz und grober Fahrlässigkeit sowie nach zwingendem Recht.",
            S,
        ),
        b(
            "(2) Bei leichter Fahrlässigkeit haften sie nur bei Verletzung wesentlicher Vertragspflichten "
            "(Kardinalpflichten) und begrenzt auf den vorhersehbaren, vertragstypischen Schaden, "
            "soweit gesetzlich zulässig.",
            S,
        ),
        b(
            "(3) Eine Haftung für mittelbare Schäden und entgangenen Gewinn ist — außer bei Vorsatz/grober "
            "Fahrlässigkeit — ausgeschlossen, soweit gesetzlich zulässig.",
            S,
        ),
        sec("§ 9 Unterlizenzierung und Übertragung", S),
        b(
            "(1) Unterlizenzen an Endnutzer nur gemäß § 3 Abs. 2 lit. d.",
            S,
        ),
        b(
            "(2) Die Abtretung dieses Vertrags durch den Lizenznehmer bedarf der vorherigen Zustimmung "
            "des Lizenzgebers in Textform, außer bei Konzernumwandlungen innerhalb verbundener Unternehmen.",
            S,
        ),
        b(
            "(3) Der Lizenzgeber darf Rechte und Pflichten im Rahmen von Holding-Umstrukturierungen "
            "auf Rechtsnachfolger übertragen; der Lizenznehmer ist zu informieren.",
            S,
        ),
        sec("§ 10 Laufzeit und Kündigung", S),
        b(
            "(1) Der Vertrag beginnt am Tag der Unterzeichnung beider Parteien, frühestens jedoch mit "
            "wirksamer Existenz des Lizenzgebers (HR-Eintragung der Holding-GmbH).",
            S,
        ),
        b(
            "(2) Der Vertrag läuft auf unbestimmte Zeit.",
            S,
        ),
        b(
            "(3) Ordentliche Kündigung mit einer Frist von sechs Monaten zum Monatsende in Textform.",
            S,
        ),
        b(
            "(4) Außerordentliche Kündigung aus wichtigem Grund ohne Frist, insbesondere bei wesentlicher "
            "Vertragsverletzung trotz Abmahnung oder bei Verlust der Unternehmensverbindung im Sinne "
            "verbundenes Unternehmen ohne Nachfolgeregelung.",
            S,
        ),
        b(
            "(5) Bei Beendigung enden die Nutzungsrechte; der Lizenznehmer darf angemessene "
            "Übergangsfristen (max. 90 Tage) zur Migration nutzen, soweit der Lizenzgeber nicht "
            "widerspricht. Zwingende Aufbewahrungspflichten bleiben unberührt.",
            S,
        ),
        sec("§ 11 Geheimhaltung", S),
        b(
            "(1) Nicht öffentliche Informationen zum Lizenz-IP und zu den Vertragsbedingungen sind vertraulich "
            "zu behandeln, soweit nicht gesetzliche Offenlegungspflichten entgegenstehen.",
            S,
        ),
        b(
            "(2) Die Geheimhaltung gilt für die Vertragslaufzeit und drei Jahre danach.",
            S,
        ),
        sec("§ 12 Schlussbestimmungen", S),
        b(
            "(1) Änderungen bedürfen der Textform, soweit nicht notarielle Form gesetzlich vorgeschrieben ist.",
            S,
        ),
        b(
            "(2) Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts.",
            S,
        ),
        b(
            "(3) Gerichtsstand — soweit zulässig — ist der Sitz des Lizenzgebers, hilfsweise Hoyerswerda.",
            S,
        ),
        b(
            "(4) Salvatorische Klausel: Unwirksame Bestimmungen berühren die übrigen nicht; an ihre Stelle "
            "tritt die wirksame Regelung, die dem wirtschaftlichen Zweck am nächsten kommt.",
            S,
        ),
        b(
            "(5) Anlagen: A) Auszug IP-Register (bei Unterzeichnung beizufügen), B) optional Visual-Freigabe "
            "Meister Hasch, C) Verweis Gesellschaftsvertrag Holding COEV-MAX.",
            S,
        ),
        PageBreak(),
        P("Anlage — Coev-Checkliste IP-Lizenz", "M", S),
    ]

    matrix = [
        ["Prüffeld", "Status", "Bemerkung"],
        ["Parteien Holding + UG", "OK/OPEN", "Holding muss existieren"],
        ["Kern-IP-Katalog § 2", "OK", "align GV Holding § 2"],
        ["Nicht-ausschließliche Lizenz", "OK", "§ 3"],
        ["Weiterentwicklungen → Holding", "OK/OPEN", "§ 4 — Notar/Anwalt prüfen"],
        ["Konzern-Null-Royalties", "OK/OPEN", "§ 5 — Steuerberater"],
        ["Open Source Dritter", "OK", "§ 2 Abs. 2 ausgenommen"],
        ["Visual Meister Hasch", "EXT", "separate Freigabe"],
        ["Dual-Org GitHub", "OK", "keine IP-Übertragung per se"],
        ["Haftungsgrenzen", "OK/OPEN", "§ 8 — Anwalt"],
        ["Laufzeit / Kündigung", "OK", "§ 10"],
        ["100 % Legalität", "SIGN/LEGAL", "Unterschrift + Beratung"],
    ]
    mrows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(matrix)]
    mt = Table(mrows, colWidths=[5.0 * cm, 2.4 * cm, 9.0 * cm])
    mt.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HexColor("#e8eef8")),
                ("GRID", (0, 0), (-1, -1), 0.3, HexColor("#bbb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )
    out += [
        mt,
        Spacer(1, 10),
        b(
            "<b>Coev-Schlussformel:</b> Dieser IP-Lizenzentwurf schließt den in der Holding-Satzung "
            f"(§ 10) vorgesehenen Hook. Zusammen mit dem Gesellschaftsvertrag COEV-MAX bildet er die "
            f"dokumentarische Brücke {LIZENZGEBER} → {LIZENZNEHMER}. Rechtsverbindlich erst mit "
            f"wirksamer Holding und Unterschriften beider Seiten.",
            S,
        ),
        Spacer(1, 14),
        P("Unterschriften (nach Gründung / Prüfung)", "H", S),
        Spacer(1, 10),
        P(
            f"<b>Lizenzgeber</b><br/>{LIZENZGEBER}<br/>vertreten durch {VERTRETER}<br/><br/>"
            f"Ort, Datum: _______________<br/>Unterschrift: _______________",
            "SIG",
            S,
        ),
        Spacer(1, 14),
        P(
            f"<b>Lizenznehmer</b><br/>{LIZENZNEHMER}<br/>vertreten durch {VERTRETER}<br/><br/>"
            f"Ort, Datum: _______________<br/>Unterschrift: _______________",
            "SIG",
            S,
        ),
        Spacer(1, 16),
        P(
            f"Operator: {OP.replace('<', '&lt;')} · Bob der Baumeister · {TODAY} · {PDF.name}",
            "F",
            S,
        ),
    ]
    return out


def chrome(c, doc):
    c.saveState()
    c.setFont("Body", 32)
    c.setFillColor(Color(0.75, 0.08, 0.08, alpha=0.10))
    c.translate(A4[0] / 2, A4[1] / 2)
    c.rotate(48)
    c.drawCentredString(0, 0, "ENTWURF — IP-LIZENZ")
    c.rotate(-48)
    c.translate(-A4[0] / 2, -A4[1] / 2)
    c.setFillColor(MUTED)
    c.setFont("Body", 7)
    c.drawCentredString(
        A4[0] / 2,
        1.1 * cm,
        f"IP-Lizenz {LIZENZGEBER} → {LIZENZNEHMER} · ENTWURF · {OP} · S. {doc.page}",
    )
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
        title="IP-Lizenzvertrag Holding zu UG ENTWURF",
        author="stephanhagenurban1 / Bob der Baumeister",
        subject="ENTWURF — Coev zu Holding-GV § 10",
    )
    doc.build(story(S), onFirstPage=chrome, onLaterPages=chrome)
    MD.write_text(
        f"# IP-Lizenzvertrag {LIZENZGEBER} → {LIZENZNEHMER}\n\n"
        f"Operator: `{OP}`  \nPDF: `{PDF}`  \n{NOW}\n\n"
        f"**ENTWURF.** Meister-Hasch-Visual nur intern; nicht Public ohne Freigabe.\n",
        encoding="utf-8",
    )
    ops = Path.home() / ".fusion" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    (ops / "ip_lizenz_coev_ack.json").write_text(
        f'{{"phrase":"{OP}","at":"{NOW}","pdf":"{PDF.as_posix()}","hasch":"{HASCH.as_posix() if HASCH.is_file() else "missing"}"}}\n',
        encoding="utf-8",
    )
    print("PDF", PDF, PDF.stat().st_size)
    print("HASCH", HASCH.is_file(), HASCH)


if __name__ == "__main__":
    main()
