import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PDF_FILE = r"C:\Users\Admin\Desktop\ALTE_Frau_95g_Beste_Version\Formale_Mathematik_Heroisches_Epos_2026-06-23.pdf"
OUTPUT_DIR = r"C:\Users\Admin\Desktop\ALTE_Frau_95g_Beste_Version\02_Mathematik\extracted"


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def extract_pdf_text() -> str:
    try:
        from pdfminer.high_level import extract_text
        print("[PDF] pdfminer erkannt, extrahiere Text ...")
        text = extract_text(PDF_FILE)
        if not text.strip():
            return "[PDF] Kein Text extrahiert (PDF ist wahrscheinlich gescannt)."
        return text
    except Exception as exc:
        return f"[PDF] Extraktion fehlgeschlagen: {exc}\nTraceback: {sys.exc_info()[2]}"


def save_result(filename: str, content: str) -> str:
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(content)
    return out_path


def main():
    ensure_dir(OUTPUT_DIR)
    print("[PDF] Starte Extraktion ...")
    text = extract_pdf_text()
    saved = save_result("Formale_Mathematik.txt", text)
    print(f"[PDF] Ergebnis gespeichert: {saved}")
    print(f"[PDF] Laenge: {len(text)} Zeichen")


if __name__ == "__main__":
    main()
