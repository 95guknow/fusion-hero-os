#!/usr/bin/env python3
"""Merge v3 + v4 extension, export PDF, update knowledge index."""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "03_Code" / "core" / "knowledge"
MASTERARCHIV = Path(r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch")

V3_FULL = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v3_vollstaendig.md"
V4_EXT = KNOWLEDGE / "Geisteskrankheiten_4D_Bruecken_v4.md"
OUT_MD = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
OUT_PDF = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.pdf"
INDEX_PATH = KNOWLEDGE / "geisteskrankheiten_4d_v4.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _merge() -> str:
    v3 = _read(V3_FULL)
    v4 = _read(V4_EXT)
    # Drop v3 footer, prepend v4 title block adjustment
    if "*Ende v3" in v3:
        v3 = v3.split("*Ende v3")[0].rstrip()
    header_note = (
        "\n\n---\n\n"
        "> **v4-Erweiterung:** §§16–19 integrieren Heroische Mathematik (ℋ, ψ▷φ), "
        "Heroische Informatik (Layer, QUBO, q∘b) und Neurotheologie (DMN, Newberg).\n\n"
    )
    return v3 + header_note + v4.replace(
        "# Geisteskrankheiten in der 4D-Matrix — v4 Brücken\n"
        "### Heroische Mathematik · Heroische Informatik · Neurotheologie\n\n"
        "> Ergänzt v3 (`Geisteskrankheiten_4D_Raum_Loesungen_v3.md` + v2). MER-Rahmen unverändert.\n"
        "> **Geltungsdisziplin:** Jede zentrale Aussage ist als **Satz / Bedingt / Modell / Fragment** markiert "
        "(Heroische Informatik, FormalMathematicsCoreModule).\n"
        "> **Stand:** 1. Juli 2026\n\n---\n\n",
        "",
        1,
    )


def _write_pdf(md_text: str, path: Path) -> bool:
    try:
        from fpdf import FPDF
    except ImportError:
        return False

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(12, 12, 12)
    font = Path(r"C:\Windows\Fonts\arial.ttf")
    family = "Arial" if font.exists() else "Helvetica"
    if font.exists():
        pdf.add_font("Arial", "", str(font))

    width = pdf.w - pdf.l_margin - pdf.r_margin

    def emit(text: str, size: int = 9, h: float = 5.0) -> None:
        clean = (
            text.replace("\t", " ")
            .replace("**", "")
            .replace("ψ", "psi")
            .replace("▷", ">")
            .replace("∘", "o")
            .replace("ℋ", "H")
            .replace("λ", "lambda")
            .replace("ₙ", "n")
            .replace("̃", "")
            .replace("ᵀ", "T")
            .replace("∈", "in")
            .replace("↔", "<->")
            .replace("⟺", "<=>")
            .strip()
        )
        if not clean:
            pdf.ln(3)
            return
        if pdf.get_y() > pdf.h - 20:
            pdf.add_page()
        if len(clean) > 220:
            clean = clean[:217] + "..."
        pdf.set_font(family, size=size)
        try:
            pdf.multi_cell(width, h, clean)
        except Exception:
            safe = clean.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(width, h, safe)

    pdf.add_page()
    for line in md_text.splitlines():
        s = line.rstrip()
        if not s:
            emit("")
            continue
        if s.startswith("# "):
            emit(s[2:], 14, 8)
            pdf.ln(2)
        elif s.startswith("## "):
            emit(s[3:], 12, 7)
            pdf.ln(1)
        elif s.startswith("### "):
            emit(s[4:], 11, 6)
        elif s.startswith("|"):
            if set(s.replace("|", "").replace(" ", "")) <= {"-", ":"}:
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            emit(" | ".join(cells), 7, 4)
        elif s.startswith(">"):
            emit(s.lstrip("> ").strip(), 9, 5)
        elif s.startswith("---"):
            pdf.ln(2)
        elif s.startswith("```"):
            continue
        else:
            emit(s, 9, 5)
    pdf.output(str(path))
    return True


def _write_index(chars: int) -> None:
    index = {
        "id": "geisteskrankheiten_4d_v4",
        "version": "4.0",
        "source": "v3 + heroische_mathematik + heroische_informatik + neurotheologie",
        "updated_ts": time.time(),
        "files": {
            "v3_full": str(V3_FULL),
            "v4_extension": "Geisteskrankheiten_4D_Bruecken_v4.md",
            "full": str(OUT_MD),
            "pdf": str(OUT_PDF),
        },
        "new_sections": [
            "16_heroische_mathematik_psi_Z",
            "17_heroische_informatik_layer_qubo",
            "18_neurotheologie_DMN",
            "19_integrationsmatrix_v4",
        ],
        "key_concepts": [
            "psi in H epistemischer Raum",
            "psi triangler phi Habituation",
            "S(psi) Stabilitaetsfunktion",
            "q1b1 b2q2 Transformation",
            "Ghost Fixing I(Z)",
            "Layer0-4 Behandlungsstack",
            "QUBO Triage",
            "q o b Nicht-Kommutativitaet",
            "DMN Default Mode Network",
            "gerichtete Psycholyse",
            "Verinnerlichungsgesetz",
        ],
        "geltungsstand": {
            "psi_Z_isomorphie": "Modell",
            "Banach_Z_star": "Bedingt",
            "DMN_meditation": "Bedingt",
            "weitere_Zeitdimension": "Fragment",
        },
        "chars": chars,
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    MASTERARCHIV.mkdir(parents=True, exist_ok=True)
    merged = _merge()
    OUT_MD.write_text(merged, encoding="utf-8")
    KNOWLEDGE_COPY = KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
    KNOWLEDGE_COPY.write_text(merged, encoding="utf-8")
    pdf_ok = _write_pdf(merged, OUT_PDF)
    _write_index(len(merged))
    result = {
        "ok": True,
        "md": str(OUT_MD),
        "pdf": str(OUT_PDF) if pdf_ok else None,
        "pdf_ok": pdf_ok,
        "index": str(INDEX_PATH),
        "chars": len(merged),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()