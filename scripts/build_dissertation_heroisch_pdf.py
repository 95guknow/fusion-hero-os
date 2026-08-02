# -*- coding: utf-8 -*-
"""Baut `dissertation_heroisch.pdf` aus dem Dissertations-Monolithen.

Quelle:  docs/dissertation/DISSERTATION_ASCENSION_MONOLITH_v14.md
Ziel:    docs/dissertation/dissertation_heroisch.pdf

Gestaltung nach der verbindlichen Designvorlage V3.3
(docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md) und den Layer-Farbtoken des
Projekts (design-tokens/tokens.json):

    L0 MasterSeed / Foundation  #f5c542   -> Saetze, Fixpunkt, Meister
    L1 Operative                #00ffd5   -> Spezifikationen, Held
    L2 Ascension                #a855f7   -> Modelle, heroische Exkurse, Operator

Schluesselbild: docs/dissertation/assets/ascensionOS_big_ALPHA.png (eigenes Werk).
Das Bild `meister_hasch.png` wird bewusst NICHT eingebunden: es traegt einen
eingebetteten Copyright-Vermerk Dritter und wurde am 2026-07-20 zurueckgezogen
(siehe docs/dissertation/MEISTER_HASCH_PUBLIC.md). Der Meister-Hasch-Rahmen
erscheint ausschliesslich als Text.

Ehrlicher Status: Mathematik wird per Unicode-Ersetzung gesetzt, nicht ueber eine
LaTeX-Engine. Die Formeln dieses Werkes sind einfach genug, dass die Ersetzung
verlustfrei ist; komplexere Notation wuerde hier NICHT korrekt gesetzt.

Abhaengigkeiten: markdown, weasyprint.
Aufruf:  python scripts/build_dissertation_heroisch_pdf.py
"""

from __future__ import annotations

import argparse
import html as html_mod
import re
import sys
from datetime import date
from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "dissertation" / "DISSERTATION_ASCENSION_MONOLITH_v14.md"
OUT = ROOT / "docs" / "dissertation" / "dissertation_heroisch.pdf"
COVER = ROOT / "docs" / "dissertation" / "assets" / "ascensionOS_big_ALPHA.png"

# Layer-Token aus design-tokens/tokens.json (Werte hier gespiegelt, damit das
# Skript ohne npm-Build laeuft; Quelle bleibt tokens.json).
L0 = "#f5c542"   # MasterSeed / Foundation
L1 = "#00ffd5"   # Operative
L2 = "#a855f7"   # Ascension

# Kanonische Signatur — Expansion des Signatur-Triggers aus identity-fixpoint.md.
# Der Trigger selbst wird hier bewusst NICHT eingesetzt; nur seine Expansion.
SIGNATUR = (
    "Vorgelegt von Stephan Hagen Urban. Es beginnt nicht mit einem Abschluss, "
    "sondern mit einem Fixed-Point im heroischen Raum: |Ψ⟩_h → |ω⟩."
)

# --- Paletten ---------------------------------------------------------------
# "tag"    = heller Satz fuer Druck und Einreichung
# "nacht"  = Freunde-der-Nacht-Edition, gebaut aus den Dark-Token des Projekts
#            (color.bg.void/base, color.fg.primary/muted in tokens.json)
PALETTES = {
    "tag": {
        "page_bg": "#ffffff", "text": "#14161c", "text_strong": "#0b0d12",
        "head": "#0d0f14", "head2": "#1c2029", "head3": "#2a2f3a",
        "rule": "#dfe3ea", "table_border": "#d6dae2", "table_zebra": "#fafbfc",
        "th_bg": "#12151d", "th_fg": "#f2f5fa", "code_bg": "#f1f3f6",
        "pre_bg": "#0e1118", "pre_fg": "#dbe3ef", "math_bg": "#fbfcfd",
        "quote_bg": "#faf7fe", "runner": "#6b7280", "link": "#1f4f8f",
        "m_satz_bg": "#fdf3d4", "m_satz_fg": "#7a5b06",
        "m_def_bg": "#eef1f6", "m_def_fg": "#33415c", "m_def_bd": "#9aa7bd",
        "m_bed_bg": "#fdeede", "m_bed_fg": "#8a4b12", "m_bed_bd": "#e0a86a",
        "m_mod_bg": "#f3e9fd", "m_mod_fg": "#6b2fa8",
        "m_frg_bg": "#f0f1f3", "m_frg_fg": "#55595f", "m_frg_bd": "#b7bcc4",
        "m_spec_bg": "#e0fbf5", "m_spec_fg": "#056657", "m_spec_bd": "#4fd8c0",
    },
    "nacht": {
        "page_bg": "#0a0a0f", "text": "#d7dde8", "text_strong": "#f2f5fa",
        "head": "#f5f7fb", "head2": "#e6ebf3", "head3": "#cfd6e2",
        "rule": "#242a36", "table_border": "#262c39", "table_zebra": "#101018",
        "th_bg": "#161c28", "th_fg": "#f2f5fa", "code_bg": "#161b25",
        "pre_bg": "#05070c", "pre_fg": "#cfe0f2", "math_bg": "#0d1018",
        "quote_bg": "#130f1d", "runner": "#7b8798", "link": "#7fc4ff",
        "m_satz_bg": "#2a2208", "m_satz_fg": "#f7d774",
        "m_def_bg": "#1a1f2b", "m_def_fg": "#b9c6dc", "m_def_bd": "#3c465a",
        "m_bed_bg": "#2b1c0c", "m_bed_fg": "#f0b978", "m_bed_bd": "#7d5426",
        "m_mod_bg": "#221534", "m_mod_fg": "#d5b3fb",
        "m_frg_bg": "#191c22", "m_frg_fg": "#a2a9b5", "m_frg_bd": "#3a404b",
        "m_spec_bg": "#052b26", "m_spec_fg": "#6ff0d8", "m_spec_bd": "#12776a",
    },
}

# --- Mathematik: LaTeX-Fragmente -> Unicode ---------------------------------
# Nur die im Monolithen tatsaechlich verwendeten Konstrukte.
_MATH_MAP = [
    (r"\lVert", "‖"), (r"\rVert", "‖"), (r"\lvert", "|"), (r"\rvert", "|"),
    (r"\bigl", ""), (r"\bigr", ""), (r"\left", ""), (r"\right", ""),
    (r"\le", "≤"), (r"\ge", "≥"), (r"\neq", "≠"), (r"\in", "∈"),
    (r"\subset", "⊂"), (r"\cdot", "·"), (r"\circ", "∘"), (r"\to", "→"),
    (r"\mapsto", "↦"), (r"\qquad", "    "), (r"\quad", "  "),
    (r"\text", ""), (r"\operatorname", ""), (r"\,", " "), (r"\;", " "),
    (r"\!", ""), (r"\ ", " "),
]
_SUB = {"0": "₀", "1": "₁", "2": "₂", "I": "ᵢ", "i": "ᵢ", "j": "ⱼ", "n": "ₙ"}
_SUP = {"T": "ᵀ", "n": "ⁿ", "2": "²"}


def _mathify(expr: str) -> str:
    """Uebersetzt ein LaTeX-Fragment in gesetzte Unicode-Mathematik."""
    s = expr
    for a, b in _MATH_MAP:
        s = s.replace(a, b)
    # \frac{a}{b} -> a/b
    s = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"(\1)/(\2)", s)
    # Hoch-/Tiefstellung mit einzelnen Zeichen
    s = re.sub(r"\^\{?([Tn2])\}?", lambda m: _SUP.get(m.group(1), "^" + m.group(1)), s)
    s = re.sub(r"_\{?([012Iijn])\}?", lambda m: _SUB.get(m.group(1), "_" + m.group(1)), s)
    s = s.replace("\\", "").replace("{", "").replace("}", "")
    return re.sub(r"[ \t]+", " ", s).strip()


def preprocess_math(md_text: str) -> str:
    """Ersetzt \\[..\\] (Block) und \\( .. \\) (inline) durch HTML-Platzhalter."""
    def block(m: re.Match) -> str:
        return f"\n\nMATHBLOCKOPEN{_mathify(m.group(1))}MATHBLOCKCLOSE\n\n"

    def inline(m: re.Match) -> str:
        return f"MATHINLINEOPEN{_mathify(m.group(1))}MATHINLINECLOSE"

    md_text = re.sub(r"\\\[(.+?)\\\]", block, md_text, flags=re.S)
    md_text = re.sub(r"\\\((.+?)\\\)", inline, md_text, flags=re.S)
    return md_text


def postprocess_math(html_text: str) -> str:
    html_text = html_text.replace("MATHBLOCKOPEN", '<div class="math-block">')
    html_text = html_text.replace("MATHBLOCKCLOSE", "</div>")
    html_text = html_text.replace("MATHINLINEOPEN", '<span class="math-inline">')
    html_text = html_text.replace("MATHINLINECLOSE", "</span>")
    # Von markdown in <p> eingewickelte Bloecke wieder ausschaelen
    return re.sub(r"<p>\s*(<div class=\"math-block\">.*?</div>)\s*</p>",
                  r"\1", html_text, flags=re.S)


def mark_registers(html_text: str) -> str:
    """Faerbt die Geltungsmarken und Register-Einschuebe ein."""
    classes = {
        "Satz": "g-satz", "Definition": "g-def", "Bedingt": "g-bedingt",
        "Modell": "g-modell", "Fragment": "g-fragment",
        "Spezifikation": "r-spec", "Heroischer Exkurs": "r-exkurs",
        "Herleitung aus dem Nichts": "r-herleitung",
    }

    def repl(m: re.Match) -> str:
        inner = m.group(1)
        key = next((k for k in sorted(classes, key=len, reverse=True)
                    if inner.startswith(k)), None)
        if key is None:
            return m.group(0)
        return f'<span class="mark {classes[key]}">[{inner}]</span>'

    return re.sub(r"\[([^\[\]]{2,40})\]", repl, html_text)


def build_css(p: dict, edition: str) -> str:
    runner = ("Ascension als Betriebsform · Dissertation · Fusion Hero OS v14.0.0"
              + (" · Freunde der Nacht" if edition == "nacht" else ""))
    return f"""
@page {{
  size: A4; margin: 22mm 20mm 20mm 20mm;
  background: {p['page_bg']};
  @top-center {{
    content: "{runner}";
    font-family: "DejaVu Sans", sans-serif; font-size: 7.5pt;
    color: {p['runner']}; padding-bottom: 3mm;
  }}
  @bottom-center {{
    content: counter(page); font-family: "DejaVu Sans", sans-serif;
    font-size: 8.5pt; color: {p['runner']}; padding-top: 3mm;
  }}
}}
@page :first {{ margin: 0; @top-center {{ content: "" }} @bottom-center {{ content: "" }} }}
@page cover {{ margin: 0; }}

html {{ font-size: 10.6pt; background: {p['page_bg']}; }}
body {{
  font-family: "DejaVu Serif", Georgia, serif; line-height: 1.62;
  color: {p['text']}; background: {p['page_bg']}; hyphens: auto;
  text-align: justify;
}}

/* ---------- Titelseite ---------- */
.cover {{ page: cover; height: 297mm; background: #05060c; color: #e9edf5;
         position: relative; page-break-after: always; }}
.cover img {{ width: 100%; display: block; }}
.cover-body {{ padding: 14mm 20mm 0 20mm; }}
.cover .kicker {{ font-family: "DejaVu Sans", sans-serif; font-size: 9pt;
  letter-spacing: .28em; text-transform: uppercase; color: {L1}; margin-bottom: 6mm; }}
.cover h1 {{ font-size: 27pt; line-height: 1.16; margin: 0 0 4mm 0;
  color: {L0}; border: none; text-align: left;
  page-break-before: avoid; page-break-after: avoid; }}
.cover h2 {{ font-size: 13.5pt; font-weight: normal; line-height: 1.42;
  color: #c7cedb; margin: 0 0 12mm 0; border: none; text-align: left;
  page-break-before: avoid; page-break-after: avoid; }}
.cover .rule {{ height: 2.5pt; width: 62mm; margin-bottom: 11mm;
  background: linear-gradient(90deg, {L0} 0%, {L1} 55%, {L2} 100%); }}
.cover .meta {{ font-family: "DejaVu Sans", sans-serif; font-size: 9.2pt;
  line-height: 1.85; color: #98a2b4; text-align: left; }}
.cover .meta b {{ color: #e9edf5; font-weight: normal; }}
.cover .foot {{ position: absolute; bottom: 13mm; left: 20mm; right: 20mm;
  font-family: "DejaVu Sans", sans-serif; font-size: 8pt; color: #6a7285;
  border-top: .5pt solid #232838; padding-top: 4mm; text-align: left; }}

.cover .sig {{ font-family: "DejaVu Serif", Georgia, serif; font-size: 9pt;
  font-style: italic; line-height: 1.6; color: #aab3c4; margin-top: 9mm;
  padding-left: 4mm; border-left: 1.5pt solid {L0}; text-align: left; }}

/* ---------- Ueberschriften ---------- */
h1 {{ font-size: 19pt; margin: 0 0 6mm 0; padding-bottom: 3mm; color: {p['head']};
     border-bottom: 2.5pt solid {L0}; page-break-before: always;
     page-break-after: avoid; text-align: left; }}
h1.nobreak {{ page-break-before: avoid; }}
h2 {{ font-size: 13.6pt; margin: 8mm 0 3mm 0; color: {p['head2']};
     page-break-after: avoid; text-align: left; }}
h3 {{ font-size: 11.4pt; margin: 6mm 0 2mm 0; color: {p['head3']};
     page-break-after: avoid; text-align: left; }}
h4 {{ font-size: 10.4pt; margin: 5mm 0 2mm 0; color: {p['head3']};
     page-break-after: avoid; text-align: left; }}
h1 + h2 {{ margin-top: 2mm; }}
p {{ margin: 0 0 3.1mm 0; orphans: 2; widows: 2; }}

/* ---------- Geltungsmarken ---------- */
.mark {{ font-family: "DejaVu Sans", sans-serif; font-size: 7.6pt;
  font-weight: bold; letter-spacing: .05em; padding: .5mm 1.6mm;
  border-radius: 1mm; white-space: nowrap; }}
.g-satz     {{ background: {p['m_satz_bg']}; color: {p['m_satz_fg']}; border: .5pt solid {L0}; }}
.g-def      {{ background: {p['m_def_bg']}; color: {p['m_def_fg']}; border: .5pt solid {p['m_def_bd']}; }}
.g-bedingt  {{ background: {p['m_bed_bg']}; color: {p['m_bed_fg']}; border: .5pt solid {p['m_bed_bd']}; }}
.g-modell   {{ background: {p['m_mod_bg']}; color: {p['m_mod_fg']}; border: .5pt solid {L2}; }}
.g-fragment {{ background: {p['m_frg_bg']}; color: {p['m_frg_fg']}; border: .5pt solid {p['m_frg_bd']}; }}
.r-spec       {{ background: {p['m_spec_bg']}; color: {p['m_spec_fg']}; border: .5pt solid {p['m_spec_bd']}; }}
.r-exkurs     {{ background: {p['m_mod_bg']}; color: {p['m_mod_fg']}; border: .5pt solid {L2}; }}
.r-herleitung {{ background: {p['m_satz_bg']}; color: {p['m_satz_fg']}; border: .5pt solid {L0}; }}

/* ---------- Mathematik ---------- */
.math-block {{ font-family: "DejaVu Serif", Georgia, serif; font-style: italic;
  font-size: 11.4pt; text-align: center; margin: 4.5mm 0; padding: 3mm 4mm;
  background: {p['math_bg']}; border-left: 2pt solid {L0}; page-break-inside: avoid; }}
.math-inline {{ font-style: italic; }}

/* ---------- Tabellen ---------- */
table {{ width: 100%; border-collapse: collapse; margin: 4mm 0;
  font-family: "DejaVu Sans", sans-serif; font-size: 8.3pt;
  page-break-inside: avoid; text-align: left; }}
th {{ background: {p['th_bg']}; color: {p['th_fg']}; font-weight: bold; text-align: left;
  padding: 1.9mm 2.4mm; border: .4pt solid {p['th_bg']}; }}
td {{ padding: 1.7mm 2.4mm; border: .4pt solid {p['table_border']}; vertical-align: top;
  text-align: left; }}
tr:nth-child(even) td {{ background: {p['table_zebra']}; }}

/* ---------- Code / Zitate / Listen ---------- */
pre {{ background: {p['pre_bg']}; color: {p['pre_fg']}; padding: 3.4mm 4mm; font-size: 8.2pt;
  font-family: "DejaVu Sans Mono", monospace; line-height: 1.5;
  border-left: 2.5pt solid {L1}; page-break-inside: avoid;
  white-space: pre-wrap; text-align: left; }}
code {{ font-family: "DejaVu Sans Mono", monospace; font-size: 8.6pt;
  background: {p['code_bg']}; padding: .3mm 1mm; border-radius: .8mm; }}
pre code {{ background: none; padding: 0; color: inherit; font-size: 8.2pt; }}
blockquote {{ margin: 4mm 0; padding: 2.5mm 4mm; border-left: 2.5pt solid {L2};
  background: {p['quote_bg']}; font-style: italic; page-break-inside: avoid; }}
blockquote p {{ margin: 0; }}
ul, ol {{ margin: 0 0 3.1mm 0; padding-left: 6mm; }}
li {{ margin-bottom: 1.1mm; }}
hr {{ border: none; border-top: .5pt solid {p['rule']}; margin: 6mm 0; }}
a {{ color: {p['link']}; text-decoration: none; }}
strong {{ color: {p['text_strong']}; }}
"""


def build_cover(today: str, edition: str) -> str:
    img = COVER.as_uri() if COVER.exists() else ""
    img_tag = f'<img src="{html_mod.escape(img)}" alt="AscensionOS BIG ALPHA">' if img else ""
    kicker = "Fusion Hero OS · Track Ascension · Monolith"
    if edition == "nacht":
        kicker += " · Freunde der Nacht"
    return f"""
<div class="cover">
  {img_tag}
  <div class="cover-body">
    <div class="kicker">{kicker}</div>
    <h1>Ascension als Betriebsform</h1>
    <h2>Autopoietische Selbstmodifikation unter invarianter Identität —
        eine Dissertation auf Basis des AscensionOS</h2>
    <div class="rule"></div>
    <div class="meta">
      <b>Stephan Hagen Urban</b><br>
      Fassung v14.0.0 · Stand {today}<br>
      Designvorlage: Kompendium der Heroik V3.3 (verbindlich)<br>
      Gegenstand: <b>ascension_os/</b> — Consent-Gate, AscensionCore, Sisyphos,
      Stage-9-Tracker, QUBO-Optimizer, Harmonisierung, Geisterjagd,
      M-pression, Root-Anchor, Hypercluster
    </div>
    <div class="sig">{SIGNATUR}</div>
  </div>
  <div class="foot">
    Schlüsselbild: ascensionOS_big_ALPHA.png (eigenes Werk des Projekts). Das
    Bild trägt den Versionsstempel seiner Entstehung (v12.0.0); maßgeblich ist
    der Stand im Text. — Das Asset meister_hasch.png ist wegen eines
    eingebetteten Copyright-Vermerks Dritter am 2026-07-20 zurückgezogen und
    hier bewusst nicht eingebunden; der Meister-Hasch-Rahmen erscheint
    ausschließlich als Text (Abschnitt 6.4).
  </div>
</div>
"""


def render(body: str, out: Path, edition: str, today: str) -> None:
    css = build_css(PALETTES[edition], edition)
    doc = (f"<!doctype html><html lang='de'><head><meta charset='utf-8'>"
           f"<title>Ascension als Betriebsform — Dissertation</title>"
           f"<style>{css}</style></head><body>"
           f"{build_cover(today, edition)}{body}</body></html>")
    out.parent.mkdir(parents=True, exist_ok=True)
    HTML(string=doc, base_url=str(ROOT)).write_pdf(str(out))
    print(f"[OK] {out.relative_to(ROOT)}  ({out.stat().st_size / 1024:.0f} KB)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=Path, default=SRC)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--edition", choices=["tag", "nacht", "beide"], default="beide",
                    help="tag = heller Satz · nacht = Freunde-der-Nacht-Edition")
    args = ap.parse_args()

    if not args.src.exists():
        print(f"[FAIL] Quelle fehlt: {args.src}", file=sys.stderr)
        return 1

    md_text = preprocess_math(args.src.read_text(encoding="utf-8"))
    body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )
    body = postprocess_math(body)
    body = mark_registers(body)
    # Erste Ueberschrift nicht auf eine eigene Seite umbrechen
    body = body.replace("<h1>", '<h1 class="nobreak">', 1)

    today = date.today().isoformat()
    editions = ["tag", "nacht"] if args.edition == "beide" else [args.edition]
    for ed in editions:
        out = args.out if ed == "tag" else args.out.with_name(
            args.out.stem + "_nacht" + args.out.suffix)
        render(body, out, ed, today)

    if not COVER.exists():
        print(f"[WARN] Schlüsselbild fehlt: {COVER}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
