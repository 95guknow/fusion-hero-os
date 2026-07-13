#!/usr/bin/env python3
"""Merge v5 full + v6 dissertation/philosophy extension, PDF, index, desktop copy."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "03_Code" / "core" / "knowledge"
MASTERARCHIV = Path(r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch")
DESKTOP = Path(r"C:\Users\Admin\Desktop")

V5_FULL = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
V5_FULL_ALT = KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v5_vollstaendig.md"
V6_EXT = KNOWLEDGE / "Geisteskrankheiten_4D_Dissertation_Philosophie_v6.md"
OUT_MD = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.md"
OUT_PDF = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.pdf"
DESKTOP_MD = DESKTOP / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.md"
DESKTOP_PDF = DESKTOP / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.pdf"
INDEX_PATH = KNOWLEDGE / "geisteskrankheiten_4d_v6.json"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _v5_source() -> str:
    if V5_FULL.exists():
        return _read(V5_FULL)
    if V5_FULL_ALT.exists():
        return _read(V5_FULL_ALT)
    raise FileNotFoundError("v5 full document not found")


def _merge() -> str:
    v5 = _v5_source()
    v6 = _read(V6_EXT)
    if "*Ende v5" in v5:
        v5 = v5.split("*Ende v5")[0].rstrip()
    header = (
        "\n\n---\n\n"
        "> **v6-Erweiterung:** §§22–24 — Dissertation (Schicht S/F/Ü), "
        "Heroische Philosophie (A.1–A.12, Concept Space D1–D8), integrative Landkarte.\n\n"
    )
    strip = (
        "# Geisteskrankheiten in der 4D-Matrix — v6 Dissertation & Heroische Philosophie\n"
        "### Schicht S/F/Ü · Concept Space · Fundament A.1–A.12\n\n"
        "> Ergänzt v5 (Visualisierung, Trajektorien). Quellen: Dissertation "
        "Von der Bescheidenheit zur Autorität (Urban, 23.06.2026), "
        "Der heroische Mensch (Masterstruktur), Concept Space of Philosophy.\n"
        "> **Geltungsdisziplin:** Dissertation-Kern — epistemische Hygiene vor Autoritätsgeste. "
        "Jede Brücke ist **Modell** oder **Bedingt**, sofern nicht als Satz/Fragment markiert.\n"
        "> **Stand:** 1. Juli 2026\n\n---\n\n"
    )
    v6_body = v6.replace(strip, "", 1)
    return v5 + header + v6_body


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
            .replace("Π", "Pi")
            .replace("±", "+/-")
            .replace("↔", "<->")
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


def main() -> None:
    MASTERARCHIV.mkdir(parents=True, exist_ok=True)
    merged = _merge()
    OUT_MD.write_text(merged, encoding="utf-8")
    (KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.md").write_text(merged, encoding="utf-8")
    pdf_ok = _write_pdf(merged, OUT_PDF)
    shutil.copy2(OUT_MD, DESKTOP_MD)
    if pdf_ok:
        shutil.copy2(OUT_PDF, DESKTOP_PDF)
    index = {
        "id": "geisteskrankheiten_4d_v6",
        "version": "6.0",
        "source": "v5 + dissertation + heroische_philosophie",
        "updated_ts": time.time(),
        "sources": [
            "Von der Bescheidenheit zur Autoritaet (Dissertation Urban 2026-06-23)",
            "Der heroische Mensch Masterstruktur",
            "Concept_Space_of_Philosophy_v1.md",
        ],
        "new_sections": [
            "22_dissertation_schichten_SFU",
            "23_concept_space_philosophie",
            "24_integrative_landkarte",
        ],
        "chars": len(merged),
        "desktop": {"md": str(DESKTOP_MD), "pdf": str(DESKTOP_PDF) if pdf_ok else None},
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "md": str(OUT_MD),
                "pdf": str(OUT_PDF) if pdf_ok else None,
                "desktop_md": str(DESKTOP_MD),
                "desktop_pdf": str(DESKTOP_PDF) if pdf_ok else None,
                "chars": len(merged),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()