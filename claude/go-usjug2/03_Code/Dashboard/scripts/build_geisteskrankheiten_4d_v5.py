#!/usr/bin/env python3
"""Merge v4 full + v5 visual/trajectory extension, export PDF, update index."""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "03_Code" / "core" / "knowledge"
MASTERARCHIV = Path(r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch")

V4_FULL = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
V4_FULL_ALT = KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v4_vollstaendig.md"
V5_EXT = KNOWLEDGE / "Geisteskrankheiten_4D_Visual_Trajektorien_v5.md"
OUT_MD = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
OUT_PDF = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.pdf"
INDEX_PATH = KNOWLEDGE / "geisteskrankheiten_4d_v5.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _v4_source() -> str:
    if V4_FULL.exists():
        return _read(V4_FULL)
    if V4_FULL_ALT.exists():
        return _read(V4_FULL_ALT)
    raise FileNotFoundError("v4 full document not found")


def _merge() -> str:
    v4 = _v4_source()
    v5 = _read(V5_EXT)
    if "*Ende v4" in v4:
        v4 = v4.split("*Ende v4")[0].rstrip()
    header = (
        "\n\n---\n\n"
        "> **v5-Erweiterung:** §§20–21 — 2D-Projektionen (Π_KG, Π_SN), "
        "Schattenhülle in 2D, Einzelfall-Trajektorien für 10 Störungen.\n\n"
    )
    v5_body = v5
    for strip in (
        "# Geisteskrankheiten in der 4D-Matrix — v5 Visualisierung\n"
        "### 2D-Raumdiagramme · Einzelfall-Trajektorien Z(t)\n\n"
        "> Ergänzt v4 (§§16–19). MER-Rahmen unverändert.\n"
        "> **Stand:** 1. Juli 2026\n\n---\n\n",
    ):
        v5_body = v5_body.replace(strip, "", 1)
    return v4 + header + v5_body


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
            .replace("Π", "Pi")
            .replace("±", "+/-")
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
        "id": "geisteskrankheiten_4d_v5",
        "version": "5.0",
        "source": "v4 + visual_pi_KG_SN + einzelfall_trajektorien",
        "updated_ts": time.time(),
        "files": {
            "v4_full": str(V4_FULL),
            "v5_extension": "Geisteskrankheiten_4D_Visual_Trajektorien_v5.md",
            "full": str(OUT_MD),
            "pdf": str(OUT_PDF),
        },
        "new_sections": [
            "20_2d_projektionen_Pi_KG_Pi_SN",
            "21_einzelfall_trajektorien_10_faelle",
        ],
        "key_concepts": [
            "Pi_KG Koerper-Geist-Ebene",
            "Pi_SN Seele-Natur-Ebene",
            "Z_real vs Z_wahrgenommen 2D",
            "Limit-Cycle Bipolar",
            "Sprungfeld Borderline",
            "Trauma-Attraktor PTBS",
            "OCD lokale Schleife",
            "Heilungs-Spirale alpha beta",
        ],
        "case_studies": [
            "bipolar_I",
            "borderline",
            "ptbs",
            "ocd",
            "depression_endogen",
            "schizophrenie",
            "adhs",
            "anorexie",
            "substanz",
            "autismus_masking",
        ],
        "chars": chars,
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    MASTERARCHIV.mkdir(parents=True, exist_ok=True)
    merged = _merge()
    OUT_MD.write_text(merged, encoding="utf-8")
    KNOWLEDGE_COPY = KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
    KNOWLEDGE_COPY.write_text(merged, encoding="utf-8")
    pdf_ok = _write_pdf(merged, OUT_PDF)
    _write_index(len(merged))
    print(
        json.dumps(
            {
                "ok": True,
                "md": str(OUT_MD),
                "pdf": str(OUT_PDF) if pdf_ok else None,
                "pdf_ok": pdf_ok,
                "index": str(INDEX_PATH),
                "chars": len(merged),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()