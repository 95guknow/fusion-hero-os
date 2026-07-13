#!/usr/bin/env python3
"""PDF-Renderer im Stil des Kompendium der Heroik V3.3 (LibreOffice/Writer-Layout)."""
from __future__ import annotations

import re
from html import escape
from pathlib import Path
from typing import List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics import renderPDF

try:
    from svglib.svglib import svg2rlg

    _HAS_SVG = True
except ImportError:
    _HAS_SVG = False

GRAPHICS_DIR = Path(__file__).resolve().parents[2] / "core" / "knowledge" / "graphics"

# Abschnittsnummer → Diagramm-Dateien (ohne .svg), nach Kapitelüberschrift
SECTION_FIGURES: dict[str, list[str]] = {
    "11": ["01_4d_raum_ueberblick"],
    "20": ["02_pi_kg_koerper_geist", "03_pi_sn_seele_natur", "04_schattenhuelle_iz"],
    "21": ["05_bipolar_limit_cycle", "06_ptbs_trauma_attraktor"],
    "14": ["07_dreiphasen_alpha", "09_memetisch_mimetisch"],
    "24": ["08_gesamt_pipeline"],
    "28": ["08_gesamt_pipeline"],
}

# Kompendium V3.3 Farben (Writer-Export, dezent)
PRIMARY = HexColor("#1C2526")
ACCENT = HexColor("#5C4A2A")
MUTED = HexColor("#555555")
RULE = HexColor("#999999")
CREAM = HexColor("#FDFAF5")

DOC_SHORT = "Geisteskrankheiten in der 4D-Matrix"
DOC_VERSION = "v7"
DOC_EDITION = "V3.3-Duktus · Juli 2026"


def _styles():
    base = getSampleStyleSheet()
    s = {}

    s["title"] = ParagraphStyle(
        "KTitle",
        fontName="Times-Bold",
        fontSize=28,
        leading=34,
        alignment=TA_CENTER,
        textColor=PRIMARY,
        spaceAfter=8,
    )
    s["subtitle"] = ParagraphStyle(
        "KSubtitle",
        fontName="Times-Roman",
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceAfter=6,
    )
    s["tagline"] = ParagraphStyle(
        "KTagline",
        fontName="Times-Italic",
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        textColor=ACCENT,
        spaceAfter=4,
    )
    s["part"] = ParagraphStyle(
        "KPart",
        fontName="Times-Bold",
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=PRIMARY,
        spaceBefore=30,
        spaceAfter=20,
    )
    s["part_sub"] = ParagraphStyle(
        "KPartSub",
        fontName="Times-Italic",
        fontSize=12,
        leading=16,
        alignment=TA_CENTER,
        textColor=MUTED,
        spaceAfter=24,
    )
    s["h1"] = ParagraphStyle(
        "KH1",
        fontName="Times-Bold",
        fontSize=16,
        leading=20,
        textColor=PRIMARY,
        spaceBefore=18,
        spaceAfter=10,
    )
    s["h2"] = ParagraphStyle(
        "KH2",
        fontName="Times-Bold",
        fontSize=13,
        leading=17,
        textColor=ACCENT,
        spaceBefore=14,
        spaceAfter=8,
    )
    s["h3"] = ParagraphStyle(
        "KH3",
        fontName="Times-Bold",
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=6,
    )
    s["body"] = ParagraphStyle(
        "KBody",
        fontName="Times-Roman",
        fontSize=10.5,
        leading=15,
        alignment=TA_JUSTIFY,
        textColor=PRIMARY,
        spaceAfter=8,
        firstLineIndent=14,
    )
    s["body_ni"] = ParagraphStyle(
        "KBodyNI",
        parent=s["body"],
        firstLineIndent=0,
    )
    s["quote"] = ParagraphStyle(
        "KQuote",
        fontName="Times-Italic",
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=MUTED,
        leftIndent=24,
        rightIndent=24,
        spaceBefore=10,
        spaceAfter=10,
        backColor=CREAM,
        borderPadding=8,
    )
    s["toc"] = ParagraphStyle(
        "KTOC",
        fontName="Times-Roman",
        fontSize=10.5,
        leading=14,
        textColor=PRIMARY,
        leftIndent=0,
    )
    s["toc_sub"] = ParagraphStyle(
        "KTOCSub",
        fontName="Times-Roman",
        fontSize=9.5,
        leading=13,
        textColor=MUTED,
        leftIndent=18,
    )
    s["footer_meta"] = ParagraphStyle(
        "KFooterMeta",
        fontName="Times-Italic",
        fontSize=8,
        alignment=TA_CENTER,
        textColor=MUTED,
    )
    s["code"] = ParagraphStyle(
        "KCode",
        fontName="Courier",
        fontSize=7.5,
        leading=9,
        textColor=PRIMARY,
        leftIndent=12,
        spaceBefore=6,
        spaceAfter=6,
    )
    s["table_cell"] = ParagraphStyle(
        "KTable",
        fontName="Times-Roman",
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY,
    )
    s["table_header"] = ParagraphStyle(
        "KTableH",
        fontName="Times-Bold",
        fontSize=8.5,
        leading=11,
        textColor=PRIMARY,
    )
    return s


_ROMAN = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV",
]
_CHAPTER_WORDS = [
    "Erstes", "Zweites", "Drittes", "Viertes", "Fünftes", "Sechstes",
    "Siebtes", "Achtes", "Neuntes", "Zehntes", "Elftes", "Zwölftes",
    "Dreizehntes", "Vierzehntes", "Fünfzehntes", "Sechzehntes",
    "Siebzehntes", "Achtzehntes", "Neunzehntes", "Zwanzigstes",
    "Einundzwanzigstes", "Zweiundzwanzigstes", "Dreiundzwanzigstes",
    "Vierundzwanzigstes", "Fünfundzwanzigstes", "Sechsundzwanzigstes",
    "Siebenundzwanzigstes", "Achtundzwanzigstes", "Neunundzwanzigstes",
    "Dreißigstes",
]


def _chapter_label(n: int, title: str) -> str:
    if n < len(_CHAPTER_WORDS):
        return f"{_CHAPTER_WORDS[n]} Kapitel: {title}"
    return f"Kapitel {n + 1}: {title}"


def _clean_inline(text: str) -> str:
    text = text.replace("**", "")
    text = text.replace("`", "")
    replacements = {
        "ψ": "ψ", "▷": "▷", "∘": "∘", "ℋ": "ℋ", "Π": "Π", "λ": "λ",
        "±": "±", "↔": "↔", "→": "→", "∴": "∴", "ω": "ω", "ₙ": "ₙ",
        "₁": "₁", "₂": "₂", "₃": "₃", "₄": "₄", "₅": "₅",
        "₆": "₆", "₇": "₇", "₈": "₈", "—": "—",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return escape(text)


def _part_for_section(num: str) -> Optional[Tuple[str, str]]:
    try:
        n = int(num)
    except ValueError:
        return None
    if n <= 10:
        return ("I", "MER · Klinische Grundlegung")
    if n <= 15:
        return ("II", "Raum · Erklärung · Lösung")
    if n <= 19:
        return ("III", "Mathematik · Informatik · Neurotheologie")
    if n <= 21:
        return ("IV", "Visualisierung · Trajektorien")
    if n <= 24:
        return ("V", "Dissertation · Heroische Philosophie")
    if n <= 29:
        return ("VI", "Heroismus Edition · Gesamtarchitektur")
    return None


class _KompendiumCanvas:
    def __init__(self, short_title: str, version: str):
        self.short = short_title
        self.version = version
        self._page = 0

    def __call__(self, canvas, doc):
        self._page += 1
        if self._page <= 1:
            return
        canvas.saveState()
        w, h = A4
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(0.4)
        canvas.line(2.2 * cm, h - 1.5 * cm, w - 2.2 * cm, h - 1.5 * cm)
        canvas.setFont("Times-Italic", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawCentredString(
            w / 2, h - 1.25 * cm,
            f"{self.short} · {DOC_EDITION}",
        )
        canvas.line(2.2 * cm, 1.6 * cm, w - 2.2 * cm, 1.6 * cm)
        canvas.setFont("Times-Roman", 9)
        canvas.drawCentredString(w / 2, 1.2 * cm, f"{self.short} · {self.version} · {self._page}")
        canvas.restoreState()


def _parse_table(lines: List[str], styles) -> Table:
    rows = []
    for line in lines:
        if set(line.replace("|", "").replace(" ", "")) <= {"-", ":"}:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return Spacer(1, 4)
    header = rows[0]
    data = rows[1:] if len(rows) > 1 else []
    tbl_data = [
        [Paragraph(_clean_inline(c), styles["table_header"]) for c in header]
    ]
    for row in data:
        padded = row + [""] * (len(header) - len(row))
        tbl_data.append(
            [Paragraph(_clean_inline(c), styles["table_cell"]) for c in padded[: len(header)]]
        )
    col_w = (16.5 * cm) / max(len(header), 1)
    t = Table(tbl_data, colWidths=[col_w] * len(header), repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CREAM),
                ("TEXTCOLOR", (0, 0), (-1, 0), PRIMARY),
                ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.25, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


class _SVGFigure(Flowable):
    """SVG-Diagramm für präzise wissenschaftliche Abbildungen."""

    def __init__(self, svg_path: Path, max_width: float = 16.0 * cm):
        super().__init__()
        self._path = svg_path
        self._drawing = None
        self._dw = max_width
        self._dh = 8 * cm
        if _HAS_SVG and svg_path.exists():
            d = svg2rlg(str(svg_path))
            if d and d.width and d.height:
                scale = min(max_width / d.width, (10 * cm) / d.height)
                d.width = d.width * scale
                d.height = d.height * scale
                d.scale(scale, scale)
                self._drawing = d
                self._dw = d.width
                self._dh = d.height

    def wrap(self, aW, aH):
        return self._dw, self._dh

    def draw(self):
        if self._drawing:
            renderPDF.draw(self._drawing, self.canv, 0, 0)


def _insert_figures(sec_num: str, styles) -> list:
    """Fügt Abbildungen nach Kapitelüberschrift ein."""
    out: list = []
    for stem in SECTION_FIGURES.get(sec_num, []):
        svg = GRAPHICS_DIR / f"{stem}.svg"
        if not svg.exists():
            continue
        out.append(Spacer(1, 0.2 * cm))
        out.append(_SVGFigure(svg))
        cap = stem.replace("_", " ").title()
        out.append(
            Paragraph(
                f"<i>Abbildung — {escape(cap)}. Modell, kein DSM-Ersatz.</i>",
                styles["footer_meta"],
            )
        )
        out.append(Spacer(1, 0.3 * cm))
    return out


def _collect_headings(md: str) -> List[Tuple[int, str]]:
    out = []
    for line in md.splitlines():
        if line.startswith("## "):
            out.append((2, line[3:].strip()))
        elif line.startswith("### "):
            out.append((3, line[4:].strip()))
    return out


def render_kompendium_pdf(
    md_text: str,
    output_path: Path,
    *,
    title: str = "Geisteskrankheiten in der 4D-Matrix",
    subtitle: str = "MER · KLINIK · RAUM · PHILOSOPHIE",
    tagline: str = "Einordnung nach Ursachdimension mit imaginärem Raum — im Duktus des Kompendiums der Heroik",
    author: str = "Fusion Hero OS Team",
    version: str = DOC_VERSION,
    include_toc: bool = True,
) -> None:
    styles = _styles()
    story: list = []
    last_part: Optional[str] = None
    h2_count = 0

    # —— Titelseite ——
    story.append(Spacer(1, 3.5 * cm))
    story.append(Paragraph(escape(title), styles["title"]))
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(escape(subtitle), styles["subtitle"]))
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph(escape(tagline), styles["tagline"]))
    story.append(Spacer(1, 1.2 * cm))
    story.append(Paragraph(escape(author), styles["subtitle"]))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(f"{DOC_EDITION} · Ausführliche MER-Fassung", styles["tagline"]))
    story.append(Spacer(1, 1.5 * cm))
    story.append(
        Paragraph(
            "Teil I · MER und klinische Grundlegung<br/>"
            "Teil II · Raum, Erklärung und Lösung<br/>"
            "Teil III · Mathematik, Informatik, Neurotheologie<br/>"
            "Teil IV · Visualisierung und Trajektorien<br/>"
            "Teil V · Dissertation und heroische Philosophie<br/>"
            "Teil VI · Heroismus Edition und Gesamtarchitektur",
            styles["tagline"],
        )
    )
    story.append(PageBreak())

    if include_toc:
        story.append(Paragraph("Inhalt", styles["h1"]))
        story.append(Spacer(1, 0.3 * cm))
        for level, text in _collect_headings(md_text)[:80]:
            clean = re.sub(r"^§?\d+\s*[—–-]\s*", "", text)
            clean = re.sub(r"^#+\s*", "", clean)
            if level == 2:
                story.append(Paragraph(_clean_inline(clean), styles["toc"]))
            else:
                story.append(Paragraph(_clean_inline(clean), styles["toc_sub"]))
        story.append(PageBreak())

    lines = md_text.splitlines()
    i = 0
    in_code = False
    code_buf: List[str] = []
    table_buf: List[str] = []

    def flush_table():
        nonlocal table_buf
        if table_buf:
            story.append(_parse_table(table_buf, styles))
            story.append(Spacer(1, 0.2 * cm))
            table_buf = []

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_buf), styles["code"]))
                code_buf = []
                in_code = False
            else:
                flush_table()
                in_code = True
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        if line.startswith("|"):
            table_buf.append(line)
            i += 1
            continue
        flush_table()

        if not line.strip():
            story.append(Spacer(1, 0.15 * cm))
            i += 1
            continue

        if line.startswith("# ") and i < 3:
            i += 1
            continue

        if line.startswith("## "):
            title_text = line[3:].strip()
            m = re.match(r"^(\d+)\s*[—–-]\s*(.+)$", title_text)
            if m:
                sec_num, sec_title = m.group(1), m.group(2)
                part_info = _part_for_section(sec_num)
                if part_info and part_info[0] != last_part:
                    last_part = part_info[0]
                    story.append(PageBreak())
                    idx = _ROMAN.index(part_info[0]) if part_info[0] in _ROMAN else 0
                    story.append(Paragraph(part_info[0], styles["part"]))
                    story.append(Paragraph(part_info[1], styles["part_sub"]))
                    story.append(HRFlowable(width="60%", thickness=0.6, color=ACCENT, hAlign="CENTER"))
                    story.append(Spacer(1, 0.4 * cm))
                story.append(
                    Paragraph(_clean_inline(_chapter_label(h2_count, sec_title)), styles["h1"])
                )
                story.extend(_insert_figures(sec_num, styles))
                h2_count += 1
            else:
                story.append(Paragraph(_clean_inline(title_text), styles["h1"]))
            i += 1
            continue

        if line.startswith("### "):
            story.append(Paragraph(_clean_inline(line[4:].strip()), styles["h2"]))
            i += 1
            continue

        if line.startswith(">"):
            story.append(Paragraph(_clean_inline(line.lstrip("> ").strip()), styles["quote"]))
            i += 1
            continue

        if line.strip() == "---":
            story.append(Spacer(1, 0.25 * cm))
            story.append(HRFlowable(width="100%", thickness=0.3, color=RULE))
            story.append(Spacer(1, 0.25 * cm))
            i += 1
            continue

        if line.startswith("> **v") and "Erweiterung" in line:
            i += 1
            continue

        # Fließtext: Kompendium-Duktus für kurze technische Zeilen
        body = _clean_inline(line)
        if body.startswith("- ") or body.startswith("* "):
            body = "→ " + body[2:]
            story.append(Paragraph(body, styles["body_ni"]))
        else:
            story.append(Paragraph(body, styles["body"]))

        i += 1

    flush_table()

    story.append(PageBreak())
    story.append(Paragraph("Schluss: Zur Lesart — vier Arten von Aussagen", styles["h1"]))
    story.append(Spacer(1, 0.2 * cm))
    for row in [
        ("Satz", "bewiesen oder mit zitierbarer Quelle — selten in der klinischen Matrix."),
        ("Bedingt", "gilt unter expliziten Annahmen (z.B. Banach unter λ&lt;1)."),
        ("Modell", "heuristische Landkarte — der Normalfall dieser Ausgabe."),
        ("Fragment", "offen, unvollständig — ehrlich markiert, nicht vertuschen."),
    ]:
        story.append(
            Paragraph(
                f"<b>{row[0]}.</b> {row[1]}",
                styles["body_ni"],
            )
        )
    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "<i>Weder bloße Metaphorik noch ein fertiges Lehrgebäude. Ein ehrlicher Zwischenstand.</i> "
            "— Kompendium der Heroik V3.3, übertragen auf die MER-Psychiatrie.",
            styles["quote"],
        )
    )
    story.append(Spacer(1, 1 * cm))
    story.append(
        Paragraph(f"— Ende · {title} · {version} —", styles["footer_meta"])
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=title,
        author=author,
    )
    doc.build(story, onFirstPage=_KompendiumCanvas(DOC_SHORT, version), onLaterPages=_KompendiumCanvas(DOC_SHORT, version))