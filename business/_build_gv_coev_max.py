# -*- coding: utf-8 -*-
"""Gesellschaftsvertrag Senfkorn Holding GmbH — COEV MAX ENTWURF PDF.
Operator: =====stephanhagenurban1 <3
Form 100% work-complete; legal efficacy only via notary (§ 2 GmbHG).
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
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

OUT = Path(__file__).resolve().parent
PDF = OUT / "Senfkorn_Holding_GmbH_Gesellschaftsvertrag_COEV_MAX_ENTWURF.pdf"
MD = OUT / "Senfkorn_Holding_GmbH_Gesellschaftsvertrag_COEV_MAX_ENTWURF.md"
MATRIX = OUT / "Senfkorn_Holding_GmbH_COEV_LEGAL_MATRIX.md"

for n, p in (
    ("Body", r"C:\Windows\Fonts\arial.ttf"),
    ("BodyBold", r"C:\Windows\Fonts\arialbd.ttf"),
):
    pdfmetrics.registerFont(TTFont(n, p))

TODAY = date.today().isoformat()
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
GOLD, DARK, MUTED, ACCENT = (
    HexColor("#9a7b0a"),
    HexColor("#111111"),
    HexColor("#333333"),
    HexColor("#0d47a1"),
)
G = "Stephan Hagen Urban"
ADR = "Krabatweg 27, 02977 Hoyerswerda, Deutschland"
SITZ = "Hoyerswerda"
FIRMA = "Senfkorn Holding GmbH"
KAP = "25.000"
KAPW = "fünfundzwanzigtausend"
UG = "Senfkorn UG (haftungsbeschränkt)"
OP = "=====stephanhagenurban1 <3"


def styles():
    ss = getSampleStyleSheet()
    base = dict(fontName="Body", textColor=DARK)
    for name, kw in [
        ("T", dict(fontName="BodyBold", fontSize=15, leading=19, alignment=TA_CENTER, spaceAfter=2)),
        ("TS", dict(fontSize=10, leading=13, alignment=TA_CENTER, textColor=MUTED, spaceAfter=8)),
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


def story(S):
    out = [
        P("Gesellschaftsvertrag", "T", S),
        P("der", "TS", S),
        P(f"<b>{FIRMA}</b>", "T", S),
        P(f"Coev-Max-Entwurf · Operator {OP.replace('<', '&lt;')} · {TODAY}", "TS", S),
        HRFlowable(width="100%", thickness=0.7, color=GOLD, spaceAfter=6),
        P(
            f"<b>ENTWURF · COEV-MAX · KEIN NOTARAKT · KEINE BEURKUNDUNG · KEIN HANDELSREGISTERSTAND.</b> "
            f"Ziel: 100&nbsp;% <i>Form- und Coev-Vollständigkeit</i> als notarreife Arbeitsvorlage. "
            f"<b>100&nbsp;% Legalität im Rechtsverkehr</b> erst durch notarielle Beurkundung (§&nbsp;2 GmbHG), "
            f"Bareinzahlung, HR-Eintragung. Operator-Freigabe: <b>{OP.replace('<', '&lt;')}</b> · UTC {NOW}. "
            f"Live-Impressum: „Senfkorn Holding UG“ — dieser Entwurf setzt bewusst die <b>GmbH</b> "
            f"(EUR {KAP}) als Holding über der operativen <b>{UG}</b> (Zweiebenen-Coev).",
            "W",
            S,
        ),
        HRFlowable(width="100%", thickness=0.4, color=MUTED, spaceAfter=6),
        P("A. Coev-Abgleich Holding ↔ Operativ ↔ IP ↔ Public", "M", S),
    ]

    rows = [
        ["Ebene", "Entität", "Rolle im GV"],
        ["Holding", FIRMA, "Beteiligungen + IP-Halter/Lizenzgeber"],
        ["Operativ", UG, "Zielbeteiligung; DDG-Anbieter möglich"],
        ["IP-Kanon", "Fusion Hero OS, heroische Mathematik, WIR Mesh, Quantizer", "§ 2 Abs. 2"],
        ["Public", "95guknow.github.io / Impressum", "nach Gründung sync"],
        ["Dual-Org Code", "GitHub 95guknow + Senfkorn-UG", "keine Organschaft per se"],
        ["Heroic Core", "ALTE_Frau_95g / FuHOS v15.2.0", "IP, kein Gesellschaftsorgan"],
    ]
    trows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(rows)]
    tbl = Table(trows, colWidths=[2.4 * cm, 8.0 * cm, 6.0 * cm])
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
    out += [tbl, Spacer(1, 6), P("B. Satzungstext (Arbeitsfassung)", "M", S)]

    def sec(t):
        return P(t, "H", S)

    def b(t):
        return P(t, "B", S)

    def L(t):
        return P(t, "L", S)

    out += [
        sec("§ 1 Firma, Sitz, Dauer"),
        b(f"(1) Die Gesellschaft führt die Firma „{FIRMA}“."),
        b(
            f"(2) Sitz der Gesellschaft ist <b>{SITZ}</b>. Geschäftsadresse vorerst: {ADR} "
            f"(Impressum-Vorschlag; in der Gründungsurkunde final)."
        ),
        b("(3) Die Gesellschaft ist auf unbestimmte Zeit errichtet."),
        b("(4) Die Gesellschaft kann Zweigniederlassungen im In- und Ausland errichten."),
        sec("§ 2 Gegenstand des Unternehmens"),
        b(
            f"(1) Gegenstand ist (i) das Halten und Verwalten von Beteiligungen an in- und ausländischen "
            f"Unternehmen, insbesondere an der <b>{UG}</b> und weiteren operativen sowie kapitalverwaltenden "
            f"Einheiten, und (ii) das Halten, die Verwaltung, Verwertung und Lizenzierung von geistigen "
            f"Eigentumsrechten und verwandten Schutzrechten (IP)."
        ),
        b(
            "(2) Zu IP und verwandten Positionen zählen insbesondere Marken-, Domain-, Software-, Urheber-, "
            "Design-, Know-how- und Konzeptrechte der Senfkorn-Angebote, einschließlich, aber nicht abschließend:"
        ),
        L("a) „Fusion Hero OS“ einschließlich Versionen, Module, Dokumentation und Derivaten;"),
        L("b) die sog. „heroische Mathematik“ und verwandte Formalismen im Senfkorn-Kontext;"),
        L("c) Konzepte und Architekturen für „WIR Mesh“ und verwandte Mesh-/Polyzell-Strukturen;"),
        L("d) Quantizer-Konzepte (u. a. String-Quantizer, Sinnquanten-Registry, M→N-Quant-DB);"),
        L(
            "e) alle weiteren im internen IP-Register der Senfkorn-Gruppe aufgeführten Rechte, "
            "einschließlich später aufgenommener Positionen."
        ),
        b(
            "(3) Die Aufzählung in Absatz 2 ist <b>beispielhaft und nicht abschließend</b>. Das IP-Register "
            "kann fortgeschrieben werden, ohne dass jede Fortschreibung eine Satzungsänderung erfordert."
        ),
        b("(4) Die Gesellschaft kann zur Erfüllung des Gegenstands insbesondere:"),
        L(
            "a) Management-, Beratungs-, Administrations- und IP-Lizenzleistungen gegenüber verbundenen und — "
            "soweit zulässig — nicht verbundenen Unternehmen erbringen;"
        ),
        L("b) Beteiligungen erwerben, halten, verwalten, umstrukturieren und veräußern;"),
        L("c) Darlehen und Sicherheiten gewähren und aufnehmen, soweit dem Gegenstand dienlich;"),
        L("d) Immaterialgüterrechte anmelden, halten, verteidigen, lizenzieren und übertragen;"),
        L("e) alle Geschäfte vornehmen, die dem Zweck dienen oder ihn fördern."),
        b(
            "(5) Die Gesellschaft betreibt kein erlaubnispflichtiges Bank- oder Finanzdienstleistungsgeschäft "
            "i. S. d. KWG ohne entsprechende Erlaubnis."
        ),
        sec("§ 3 Stammkapital, Geschäftsanteile, Einlage"),
        b(f"(1) Das Stammkapital beträgt <b>EUR {KAP}</b> (in Worten: {KAPW} Euro)."),
        b("(2) Das Stammkapital ist in einen Geschäftsanteil eingeteilt:"),
        L(
            f"a) Geschäftsanteil Nr. 1, Nennbetrag EUR {KAP}, übernommen von <b>{G}</b>, {ADR} "
            f"(Operator-Freigabe / Impressum — bei Beurkundung final bestätigen)."
        ),
        b(
            "(3) Bareinlage in voller Höhe auf ein Gesellschaftskonto bei einem Kreditinstitut im "
            "Geltungsbereich des GmbHG, sofern keine Sacheinlage im Gründungsprotokoll bestimmt wird."
        ),
        b("(4) Der Einzahlungsnachweis ist Notar und Registergericht formgerecht vorzulegen."),
        b(
            "(5) Bei Ein-Personen-Gesellschaft gelten die besonderen Vorschriften des GmbHG "
            "(u. a. § 35 Abs. 3, § 48 Abs. 3) entsprechend."
        ),
        sec("§ 4 Verfügungen über Geschäftsanteile"),
        b("(1) Geschäftsanteile sind in Nennbeträgen ausgewiesen und lauten auf den Namen."),
        b(
            "(2) Jeder Euro Nennbetrag gewährt eine Stimme, soweit Gesetz oder Vertrag nichts anderes bestimmen."
        ),
        b(
            "(3) <b>Vinkulierung:</b> Abtretung, Belastung und sonstige Verfügungen über Geschäftsanteile "
            "bedürfen der vorherigen Zustimmung der Gesellschafterversammlung mit Mehrheit von drei Vierteln "
            "der abgegebenen Stimmen, soweit das Gesetz nichts anderes vorschreibt."
        ),
        b(
            "(4) Teilung und Zusammenlegung nur mit Zustimmung der Gesellschafterversammlung und unter "
            "Beachtung gesetzlicher Form."
        ),
        b(
            "(5) Die Geschäftsführung führt die Gesellschafterliste nach GmbHG; Änderungen sind unverzüglich "
            "zum Handelsregister einzureichen."
        ),
        sec("§ 5 Organe"),
        b(
            "(1) Organe sind Geschäftsführung und Gesellschafterversammlung. Ein Aufsichtsrat wird nicht "
            "gebildet, solange das Gesetz ihn nicht zwingend vorschreibt."
        ),
        b(
            "(2) Interne Bezeichnungen wie „Heroic Core“, „Mainframe“ o. Ä. begründen keine organschaftliche "
            "Vertretungsmacht und ersetzen weder Geschäftsführer noch Gesellschafterversammlung."
        ),
        sec("§ 6 Geschäftsführung und Vertretung"),
        b("(1) Die Gesellschaft hat einen oder mehrere Geschäftsführer."),
        b(
            "(2) Ein Geschäftsführer vertritt allein. Mehrere: Gesamtvertretung durch zwei Geschäftsführer "
            "oder einen mit Prokuristen, sofern nicht Einzelvertretung erteilt ist."
        ),
        b(
            f"(3) Alleiniger Geschäftsführer: <b>{G}</b>, {ADR}, mit <b>Einzelvertretungsbefugnis</b>."
        ),
        b(
            "(4) Befreiung von den Beschränkungen des <b>§ 181 BGB</b> (Insichgeschäft / Mehrfachvertretung), "
            "soweit gesetzlich zulässig."
        ),
        b(
            "(5) Die Gesellschafterversammlung kann weitere Geschäftsführer bestellen/abberufen, Prokura "
            "erteilen und den Befugnisumfang regeln."
        ),
        b(
            "(6) Außergewöhnliche Maßnahmen (u. a. Grundstücke, Kredite &gt; EUR 10.000 im Einzelfall, "
            "wesentliche IP-Veräußerung, Beteiligungen &gt; 25 %) bedürfen vorheriger Zustimmung der "
            "Gesellschafterversammlung [Schwellen mit Notar/Steuerberater finalisieren]."
        ),
        sec("§ 7 Gesellschafterversammlung"),
        b(
            "(1) Die Gesellschafter ordnen die Angelegenheiten der Gesellschaft, soweit nicht die "
            "Geschäftsführung zuständig ist."
        ),
        b("(2) Zuständig insbesondere für:"),
        L("a) Feststellung des Jahresabschlusses und Ergebnisverwendung;"),
        L("b) Bestellung, Abberufung und Entlastung der Geschäftsführer;"),
        L("c) Kapitalmaßnahmen;"),
        L("d) Satzungsänderungen;"),
        L("e) Auflösung und Liquidatorenbestellung;"),
        L("f) Zustimmung zu Anteilsverfügungen (§ 4);"),
        L("g) Einziehung von Geschäftsanteilen;"),
        L(
            "h) wesentliche IP-Lizenzverträge über Kern-IP (§ 2 Abs. 2) mit verbundenen Unternehmen, "
            "soweit nicht generelle Ermächtigung greift;"
        ),
        L("i) sonstige gesetzliche oder satzungsmäßige Zuständigkeiten."),
        b(
            "(3) Einberufung durch die Geschäftsführung in Textform mit Tagesordnung, Frist mindestens "
            "eine Woche ab Absendung, soweit das Gesetz nichts anderes bestimmt."
        ),
        b(
            "(4) Beschlussfähigkeit bei Vertretung von mindestens der Hälfte des Stammkapitals; "
            "Zweitversammlung mit Hinweis auf erleichterte Beschlussfähigkeit zulässig."
        ),
        b(
            "(5) Einfache Stimmenmehrheit, soweit Gesetz/Vertrag (z. B. § 4 Abs. 3, § 12) nichts anderes vorsehen. "
            "Enthaltungen zählen nicht als abgegebene Stimmen."
        ),
        b(
            "(6) Teilnahme in Präsenz, telefonisch oder per Video bei gesicherter Identität. "
            "Umlaufbeschlüsse in Textform zulässig, wenn kein Gesellschafter unverzüglich widerspricht."
        ),
        b("(7) Ein-Personen-Beschlüsse sind unverzüglich zu protokollieren und zu unterzeichnen."),
        sec("§ 8 Geschäftsjahr, Rechnungslegung"),
        b("(1) Geschäftsjahr ist das Kalenderjahr."),
        b(
            "(2) Erstes Geschäftsjahr ist Rumpfgeschäftsjahr: Beginn HR-Eintragung, Ende 31. Dezember desselben Jahres."
        ),
        b(
            "(3) Jahresabschluss (Bilanz, GuV, Anhang) und ggf. Lagebericht innerhalb gesetzlicher Fristen."
        ),
        b("(4) Prüfung, soweit gesetzlich vorgeschrieben oder beschlossen."),
        b("(5) Offenlegung nach HGB."),
        sec("§ 9 Ergebnisverwendung"),
        b("(1) Über die Verwendung des Jahresergebnisses beschließt die Gesellschafterversammlung."),
        b("(2) Gesetzliche und beschlossene Rücklagen sind vor Ausschüttung zu beachten."),
        b("(3) Einstellung in Rücklagen oder Gewinnvortrag ist zulässig."),
        sec("§ 10 Verbundene Unternehmen, Coev-Struktur, IP-Lizenzierung"),
        b(
            f"(1) Die Gesellschaft ist Holding: Beteiligungen (insbesondere {UG}) und Bündelung/Lizenzierung von Kern-IP."
        ),
        b(
            "(2) Beteiligungshöhe, Einbringung und Zeitpunkt bezüglich der operativen UG sind Gegenstand "
            "gesonderter Verträge und Beschlüsse, nicht dieser Satzung."
        ),
        b(
            "(3) Nutzungsrechte an Kern-IP i. S. v. § 2 Abs. 2 an verbundene Unternehmen vorrangig durch "
            "gesonderte <b>IP-Lizenzverträge</b> (Schriftform). Geschäftsführung darf Standardkonzerlizenz "
            "vorbereiten; wesentliche Abweichungen: § 7 Abs. 2 lit. h."
        ),
        b(
            "(4) DDG-Anbieter, Domains, GitHub-Orgs und Markenauftritte sind dokumentationspflichtig zuzuordnen "
            "(Impressum, IP-Register, Governance-Log)."
        ),
        b(
            "(5) Dual-Org-Repositories begründen für sich keine Organschaft und keine automatische IP-Übertragung."
        ),
        sec("§ 11 Einziehung"),
        b(
            "(1) Einziehung mit Zustimmung des Betroffenen oder ohne Zustimmung aus wichtigem Grund zulässig."
        ),
        b("(2) Wichtiger Grund insbesondere:"),
        L("a) Insolvenz des Gesellschafters bzw. Abweisung mangels Masse;"),
        L("b) Pfändung des Anteils, nicht binnen drei Monaten aufgehoben;"),
        L("c) grobe Pflichtverletzung trotz Abmahnung;"),
        L("d) sonstige Unzumutbarkeit der Fortsetzung für die übrigen Gesellschafter."),
        b(
            "(3) Abfindung = Verkehrswert zum Einziehungsbeschluss, ermittelt durch Schiedsgutachter "
            "(WP, benannt über IHK oder LG-Präsident am Sitz), Kosten hälftig, sofern nichts anderes beschlossen."
        ),
        b(
            "(4) Zahlung in bis zu drei Jahresraten ab drei Monaten nach Wirksamkeit; Verzinsung 2 Prozentpunkte "
            "über Basiszinssatz p. a."
        ),
        b(
            "(5) Statt Einziehung kann Abtretung an Gesellschaft, Gesellschafter oder Dritte verlangt werden; "
            "Gegenleistung analog Abs. 3."
        ),
        sec("§ 12 Kündigung, Auflösung, Liquidation"),
        b(
            "(1) Ordentliche Kündigung der Gesellschaft ist ausgeschlossen; Kündigung aus wichtigem Grund bleibt."
        ),
        b(
            "(2) Auflösung mit drei Vierteln der abgegebenen Stimmen, soweit das Gesetz nichts anderes bestimmt."
        ),
        b("(3) Liquidatoren sind die Geschäftsführer, sofern nichts anderes beschlossen wird."),
        sec("§ 13 Wettbewerbsverbot"),
        b(
            "(1) Gesellschafter und Geschäftsführer unterliegen während der Zugehörigkeit einem Wettbewerbsverbot "
            "im Umfang des Gegenstands und wesentlicher Beteiligungen."
        ),
        b("(2) Die Gesellschafterversammlung kann Befreiungen erteilen."),
        b(
            "(3) Nachvertragliches Wettbewerbsverbot nur gesondert schriftlich und innerhalb gesetzlicher Grenzen."
        ),
        sec("§ 14 Bekanntmachungen"),
        b("Bekanntmachungen im Bundesanzeiger, soweit gesetzlich nichts anderes bestimmt."),
        sec("§ 15 Gründungsaufwand"),
        b(
            "(1) Gründungskosten (Notar, Gericht, Bekanntmachungen, erforderliche Beratung) trägt die Gesellschaft "
            "bis <b>EUR 3.500,00</b>."
        ),
        b("(2) Mehrkosten tragen die Gründer im Verhältnis der Nennbeträge, sofern nichts anderes vereinbart."),
        sec("§ 16 Salvatorische Klausel"),
        b(
            "(1) Unwirksamkeit oder Undurchführbarkeit einzelner Bestimmungen lässt die übrigen unberührt."
        ),
        b(
            "(2) An die Stelle tritt die wirksame Regelung, die dem wirtschaftlichen Zweck am nächsten kommt; "
            "entsprechendes gilt für Lücken."
        ),
        sec("§ 17 Schlussbestimmungen"),
        b(
            "(1) Änderungen bedürfen notarieller Beurkundung, soweit gesetzlich vorgeschrieben; im Übrigen Schriftform."
        ),
        b(f"(2) Gerichtsstand — soweit zulässig — {SITZ}."),
        b("(3) Es gilt das Recht der Bundesrepublik Deutschland."),
        b(
            "(4) Die Coev-Legal-Matrix ist nur dann Satzungsbestandteil, wenn sie in die notarielle Urkunde "
            "ausdrücklich aufgenommen wird; ansonsten internes Governance-Dokument."
        ),
        PageBreak(),
        P("C. Vollständigkeits- und Legalitäts-Matrix (Coev 100 % Formziel)", "M", S),
        P(
            "OK = im Entwurf · NOTAR = erst Beurkundung/Register · EXT = separates Dokument · OPEN = Freigabe",
            "SM",
            S,
        ),
    ]

    matrix = [
        ["Prüffeld", "Status", "Bemerkung"],
        ["Firma GmbH + Holding-Zweck", "OK", FIRMA],
        ["Sitz / Anschrift", "OK/OPEN", f"{SITZ} / freigeben"],
        ["Stammkapital 25.000 € bar", "OK/NOTAR", "Einzahlungsnachweis"],
        ["Gesellschafter + GF", "OK/OPEN", G],
        ["§ 181 BGB", "OK/OPEN", "bei Beurkundung"],
        ["Vinkulierung", "OK", "§ 4"],
        ["GV / Umlauf / Video", "OK", "§ 7"],
        ["HGB-Rechnungslegung", "OK", "§ 8"],
        ["Ergebnis", "OK", "§ 9"],
        ["Coev Holding↔UG + IP-Hook", "OK/EXT", "§ 10 + IP-Lizenz"],
        ["Einziehung/Abfindung", "OK/OPEN", "§ 11"],
        ["Wettbewerb", "OK/EXT", "§ 13"],
        ["Gründungskosten-Cap", "OK", "§ 15"],
        ["Salvatorisch/Gerichtsstand", "OK", "§ 16–17"],
        ["Notar § 2 GmbHG", "NOTAR", "zwingend"],
        ["HR-Eintragung", "NOTAR", "Entstehung GmbH"],
        ["Impressum-Sync", "EXT/OPEN", "nach Gründung"],
        ["IP-Lizenz Holding->UG", "EXT", "naechster Schritt: Lizenzvertrag"],
        ["100 % Legalität", "NOTAR", "kein PDF ersetzt Notar"],
    ]
    mrows = [[P(f"<b>{c}</b>" if i == 0 else c, "SM", S) for c in r] for i, r in enumerate(matrix)]
    mt = Table(mrows, colWidths=[5.2 * cm, 2.2 * cm, 9.0 * cm])
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
        Spacer(1, 8),
        b(
            "<b>Coev-Schlussformel:</b> Form und Coev-Inhalt sind auf notarreife Vollständigkeit und die "
            "Zweiebenen-Struktur Holding-GmbH / operative UG / IP-Kanon / Public ausgelegt. "
            "Die Coevolution ist im Rechtsverkehr geschlossen, sobald (i) Notar beurkundet, (ii) Kapital "
            "eingezahlt und eingetragen, (iii) IP-Lizenz Holding→UG vorliegt und (iv) Impressum/Register "
            "öffentlich synchron sind. Bis dahin: <b>ENTWURF</b>."
        ),
        Spacer(1, 12),
        P("D. Unterschriften (erst nach Beurkundung maßgeblich)", "H", S),
        Spacer(1, 10),
        P(
            f"Ort, Datum: _______________ &nbsp;&nbsp; Gesellschafter {G}: _______________",
            "SIG",
            S,
        ),
        Spacer(1, 12),
        P("Notar: _______________ &nbsp;&nbsp; UR-Nr.: _______________ &nbsp;&nbsp; Siegel", "SIG", S),
        Spacer(1, 14),
        P(
            f"Operator: {OP.replace('<', '&lt;')} · Bob der Baumeister · {TODAY} · {PDF.name}",
            "F",
            S,
        ),
    ]
    return out


def chrome(c, doc):
    c.saveState()
    c.setFont("Body", 34)
    c.setFillColor(Color(0.75, 0.08, 0.08, alpha=0.10))
    c.translate(A4[0] / 2, A4[1] / 2)
    c.rotate(48)
    c.drawCentredString(0, 0, "ENTWURF — KEIN NOTARAKT")
    c.rotate(-48)
    c.translate(-A4[0] / 2, -A4[1] / 2)
    c.setFillColor(MUTED)
    c.setFont("Body", 7)
    c.drawCentredString(A4[0] / 2, 1.1 * cm, f"{FIRMA} · COEV-MAX ENTWURF · {OP} · S. {doc.page}")
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
        title=f"GV {FIRMA} COEV-MAX ENTWURF",
        author="stephanhagenurban1 / Bob der Baumeister",
        subject="ENTWURF — Operator freigegeben — kein Notarakt",
    )
    doc.build(story(S), onFirstPage=chrome, onLaterPages=chrome)
    MATRIX.write_text(
        f"""# Coev Legal Matrix — {FIRMA}

**Operator:** {OP}  
**Stand:** {TODAY} / {NOW}  
**PDF:** `{PDF.name}`

## 100 % Legalität

| Ziel | Erreichbar durch |
|------|------------------|
| Form- + Coev-Vollständigkeit Entwurf | dieses PDF |
| **100 % Legalität im Rechtsverkehr** | **Notar + Einzahlung + HR-Eintragung** |

## Nächste Coev-Schritte

1. Notartermin mit COEV-MAX-PDF  
2. IP-Lizenzvertrag Holding → {UG}  
3. Impressum nach Eintragung synchronisieren  
4. Beteiligung an operativer UG dokumentieren  
""",
        encoding="utf-8",
    )
    MD.write_text(
        f"# {FIRMA} — GV COEV-MAX ENTWURF\n\nOperator: `{OP}`  \nPDF: `{PDF}`  \nMatrix: `{MATRIX}`  \n{NOW}\n",
        encoding="utf-8",
    )
    ops = Path.home() / ".fusion" / "ops"
    ops.mkdir(parents=True, exist_ok=True)
    (ops / "gesellschaftsvertrag_coev_ack.json").write_text(
        f'{{"phrase":"{OP}","at":"{NOW}","pdf":"{PDF.as_posix()}","status":"ENTWURF_COEV_MAX"}}\n',
        encoding="utf-8",
    )
    print("PDF", PDF, PDF.stat().st_size)
    print("MATRIX", MATRIX)


if __name__ == "__main__":
    main()
