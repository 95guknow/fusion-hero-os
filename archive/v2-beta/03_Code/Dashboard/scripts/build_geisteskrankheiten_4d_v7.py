#!/usr/bin/env python3
"""Merge v6 + v7 Heroismus Edition History; PDF; index; desktop."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "03_Code" / "core" / "knowledge"
MASTERARCHIV = Path(r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch")
DESKTOP = Path(r"C:\Users\Admin\Desktop")

V6_FULL = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.md"
V6_ALT = KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v6_vollstaendig.md"
V7_EXT = KNOWLEDGE / "Geisteskrankheiten_4D_Heroismus_Edition_v7.md"
OUT_MD = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.md"
OUT_PDF = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.pdf"
DESKTOP_MD = DESKTOP / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.md"
DESKTOP_PDF = DESKTOP / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.pdf"
INDEX_PATH = KNOWLEDGE / "geisteskrankheiten_4d_v7.json"
EDITION_SRC = KNOWLEDGE / "_heroismus_edition_history"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _v6() -> str:
    if V6_FULL.exists():
        return _read(V6_FULL)
    if V6_ALT.exists():
        return _read(V6_ALT)
    raise FileNotFoundError("v6 not found")


def _merge() -> str:
    v6 = _v6()
    v7 = _read(V7_EXT)
    if "*Ende v6" in v6:
        v6 = v6.split("*Ende v6")[0].rstrip()
    header = (
        "\n\n---\n\n"
        "> **v7-Erweiterung:** §§25–29 — Heroismus Kritische Gesamtedition 0.6–0.7, "
        "Genese April–Juli 2026, Mapping Philosophie ↔ Technik ↔ MER.\n\n"
    )
    strip = (
        "# Geisteskrankheiten in der 4D-Matrix — v7 Heroismus Edition History\n"
        "### Kritische Gesamtedition 0.6–0.7 · Genese · Philosophie ↔ Technik ↔ MER\n\n"
        "> Ergänzt v6 (Dissertation, Philosophie). Quelle: `Heroismus_Edition_History.zip` — "
        "Edition 0.6 (01.07.2026), Edition 0.7 (Mapping-Tabelle).\n"
        "> **Geltungsdisziplin:** Historische Rekonstruktion = **Modell**; "
        "Mapping-Tabelle = **Strukturvorschlag**, keine klinische Leitlinie.\n"
        "> **Stand:** 1. Juli 2026\n\n---\n\n"
    )
    return v6 + header + v7.replace(strip, "", 1)


def _write_pdf(md: str, path: Path) -> bool:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from kompendium_pdf_renderer import render_kompendium_pdf
        render_kompendium_pdf(md, path, version="v7")
        return True
    except Exception:
        pass
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
    w = pdf.w - pdf.l_margin - pdf.r_margin

    def emit(text: str, size: int = 9, h: float = 5.0) -> None:
        clean = (
            text.replace("\t", " ").replace("**", "")
            .replace("ψ", "psi").replace("▷", ">").replace("∘", "o")
            .replace("ω", "w").replace("Π", "Pi").replace("±", "+/-")
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
            pdf.multi_cell(w, h, clean)
        except Exception:
            pdf.multi_cell(w, h, clean.encode("latin-1", "replace").decode("latin-1"))

    pdf.add_page()
    for line in md.splitlines():
        s = line.rstrip()
        if not s:
            emit("")
        elif s.startswith("# "):
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
            emit(" | ".join(c.strip() for c in s.strip("|").split("|")), 7, 4)
        elif s.startswith(">"):
            emit(s.lstrip("> ").strip())
        elif s.startswith("---"):
            pdf.ln(2)
        elif s.startswith("```"):
            continue
        else:
            emit(s)
    pdf.output(str(path))
    return True


def main() -> None:
    MASTERARCHIV.mkdir(parents=True, exist_ok=True)
    merged = _merge()
    OUT_MD.write_text(merged, encoding="utf-8")
    (KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.md").write_text(merged, encoding="utf-8")
    pdf_ok = _write_pdf(merged, OUT_PDF)
    shutil.copy2(OUT_MD, DESKTOP_MD)
    if pdf_ok:
        shutil.copy2(OUT_PDF, DESKTOP_PDF)
    idx = {
        "id": "geisteskrankheiten_4d_v7",
        "version": "7.0",
        "source": "v6 + heroismus_edition_history_0.6_0.7",
        "updated_ts": time.time(),
        "edition_sources": {
            "zip": r"C:\Users\Admin\Downloads\Heroismus_Edition_History.zip",
            "extracted": str(EDITION_SRC),
            "v0.6": "Heroismus_v0.6_2026-07-01.pdf",
            "v0.7_current": "Heroismus_Kritische_Gesamtedition_current.pdf",
        },
        "new_sections": ["25_edition_history", "26_mapping_mer", "27_sieben_teile", "28_pipeline", "29_vermerk"],
        "chars": len(merged),
        "desktop": {"md": str(DESKTOP_MD), "pdf": str(DESKTOP_PDF) if pdf_ok else None},
    }
    INDEX_PATH.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": True, "chars": len(merged), "desktop_md": str(DESKTOP_MD), "pdf_ok": pdf_ok}, indent=2))


if __name__ == "__main__":
    main()