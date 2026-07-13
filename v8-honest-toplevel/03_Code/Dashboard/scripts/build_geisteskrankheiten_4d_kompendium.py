#!/usr/bin/env python3
"""Build v7 with Kompendium V3.3 Schreibstil-Rahmen and PDF-Gestaltung."""
from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KNOWLEDGE = ROOT / "03_Code" / "core" / "knowledge"
SCRIPTS = ROOT / "03_Code" / "Dashboard" / "scripts"
MASTERARCHIV = Path(r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch")
DESKTOP = Path(r"C:\Users\Admin\Desktop")

V7_FULL = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.md"
V7_ALT = KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v7_vollstaendig.md"
RAHMEN = KNOWLEDGE / "Geisteskrankheiten_4D_Kompendium_Rahmen.md"
OUT_MD = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v7_Kompendium.md"
OUT_PDF = MASTERARCHIV / "Geisteskrankheiten_4D_Matrix_v7_Kompendium.pdf"
DESKTOP_MD = DESKTOP / "Geisteskrankheiten_4D_Matrix_v7_Kompendium.md"
DESKTOP_PDF = DESKTOP / "Geisteskrankheiten_4D_Matrix_v7_Kompendium.pdf"
INDEX_PATH = KNOWLEDGE / "geisteskrankheiten_4d_v7_kompendium.json"


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _v7_body() -> str:
    if V7_FULL.exists():
        return _read(V7_FULL)
    if V7_ALT.exists():
        return _read(V7_ALT)
    raise FileNotFoundError("v7 full not found")


def _merge() -> str:
    rahmen = _read(RAHMEN)
    body = _v7_body()
    # Drop duplicate top title from v7 if present
    if body.startswith("# Geisteskrankheiten"):
        first_hr = body.find("\n---\n")
        if first_hr > 0 and first_hr < 800:
            body = body[first_hr + 5 :]
    return rahmen.rstrip() + "\n\n---\n\n" + body.lstrip()


def main() -> None:
    import sys

    sys.path.insert(0, str(SCRIPTS))
    from kompendium_pdf_renderer import render_kompendium_pdf
    from mer_diagram_generator import generate_all

    MASTERARCHIV.mkdir(parents=True, exist_ok=True)
    generate_all()
    merged = _merge()
    OUT_MD.write_text(merged, encoding="utf-8")
    (KNOWLEDGE / "Geisteskrankheiten_4D_Matrix_v7_Kompendium.md").write_text(merged, encoding="utf-8")

    render_kompendium_pdf(
        merged,
        OUT_PDF,
        title="Geisteskrankheiten in der 4D-Matrix",
        subtitle="MER · KLINIK · RAUM · PHILOSOPHIE",
        tagline="Wie Mythos, Philosophie und Mathematik die psychiatrische Landkarte vervollständigen",
        version="v7 · Kompendium-Duktus · mit Abbildungen",
    )

    shutil.copy2(OUT_MD, DESKTOP_MD)
    shutil.copy2(OUT_PDF, DESKTOP_PDF)

    idx = {
        "id": "geisteskrankheiten_4d_v7_kompendium",
        "version": "7.0-kompendium",
        "style_reference": r"C:\Users\Admin\Downloads\Kompendium_der_Heroik_V3_3-1.pdf",
        "updated_ts": time.time(),
        "files": {"md": str(OUT_MD), "pdf": str(OUT_PDF)},
        "desktop": {"md": str(DESKTOP_MD), "pdf": str(DESKTOP_PDF)},
        "chars": len(merged),
    }
    INDEX_PATH.write_text(json.dumps(idx, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "md": str(OUT_MD),
                "pdf": str(OUT_PDF),
                "desktop_md": str(DESKTOP_MD),
                "desktop_pdf": str(DESKTOP_PDF),
                "chars": len(merged),
                "style": "Kompendium_der_Heroik_V3_3",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()