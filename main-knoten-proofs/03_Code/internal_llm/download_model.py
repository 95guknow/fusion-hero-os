#!/usr/bin/env python3
"""Llama GGUF Modell herunterladen (Llama-3.2-1B-Instruct Q4_K_M)."""

from __future__ import annotations

import sys
from pathlib import Path

MODELS_DIR = Path(__file__).parent / "models"
REPO = "bartowski/Llama-3.2-1B-Instruct-GGUF"
FILENAME = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"


def main() -> int:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target = MODELS_DIR / FILENAME
    if target.exists() and target.stat().st_size > 100_000_000:
        print(f"[*] Modell bereits vorhanden: {target}")
        print(f"    Größe: {target.stat().st_size / (1024**2):.0f} MB")
        return 0

    print(f"[*] Lade {REPO}/{FILENAME} ...")
    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=REPO,
            filename=FILENAME,
            local_dir=str(MODELS_DIR),
        )
        print(f"[*] Fertig: {path}")
        return 0
    except Exception as exc:
        print(f"[!] Download fehlgeschlagen: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())