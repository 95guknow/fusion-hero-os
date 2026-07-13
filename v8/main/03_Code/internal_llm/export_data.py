#!/usr/bin/env python3
"""Export Fusion Hero OS + Heroic Core knowledge into JSONL training data."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).parent
OUT = ROOT / "data.jsonl"
MAX_CHUNK = 1200
MAX_RESPONSE = 800

SOURCES = [
    Path(r"C:\Users\Admin\fusion-hero-os"),
    Path(r"C:\Users\Admin\heroic-core-foundation"),
    Path(r"C:\Users\Admin\.grok\skills\fusion-hero-os"),
]

SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", ".venv",
    "06_Master_Archive", "99_archive", "04_Buch_und_Archiv",
    ".fusion-hero-os", "static", "templates",
}
SKIP_EXT = {".pyc", ".png", ".jpg", ".gif", ".ico", ".pdf", ".zip", ".exe", ".dll", ".lock"}


def iter_files(base: Path) -> Iterator[Path]:
    if not base.exists():
        return
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in SKIP_EXT:
            continue
        if path.suffix.lower() in {".md", ".py", ".json", ".yaml", ".yml", ".txt"}:
            yield path


def chunk_text(text: str, size: int = MAX_CHUNK) -> list[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= size:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            cut = text.rfind("\n\n", start, end)
            if cut > start + size // 2:
                end = cut
        part = text[start:end].strip()
        if part:
            chunks.append(part)
        start = end
    return chunks


def samples_from_markdown(path: Path, text: str) -> list[dict]:
    rel = str(path)
    title = path.stem.replace("_", " ")
    samples: list[dict] = []
    sections = re.split(r"\n(?=#{1,3}\s)", text)
    if len(sections) <= 1:
        for chunk in chunk_text(text):
            samples.append({
                "prompt": f"Was steht in {title} (Fusion Hero OS / Heroic Core)?",
                "response": chunk[:MAX_RESPONSE],
                "source": rel,
            })
        return samples
    for section in sections:
        section = section.strip()
        if len(section) < 40:
            continue
        header = section.split("\n", 1)[0].lstrip("#").strip()
        body = section.split("\n", 1)[1].strip() if "\n" in section else ""
        if not body:
            continue
        for chunk in chunk_text(body, 900):
            samples.append({
                "prompt": f"Erkläre aus {title}: {header}",
                "response": chunk[:MAX_RESPONSE],
                "source": rel,
            })
    return samples


def samples_from_python(path: Path, text: str) -> list[dict]:
    rel = str(path)
    doc = ast.get_docstring(ast.parse(text)) or ""
    doc = doc.strip()
    if not doc:
        return []
    name = path.stem
    samples = [{
        "prompt": f"Wofür ist das Modul {name} in Fusion Hero OS?",
        "response": doc[:MAX_RESPONSE],
        "source": rel,
    }]
    for match in re.finditer(r"^def (\w+)\([^)]*\):\s*(?:\n\s+\"\"\"(.*?)\"\"\")?", text, re.M | re.S):
        fn, fn_doc = match.group(1), (match.group(2) or "").strip()
        if fn_doc and len(fn_doc) > 30:
            samples.append({
                "prompt": f"Was macht {name}.{fn}()?",
                "response": fn_doc[:MAX_RESPONSE],
                "source": rel,
            })
    return samples


def samples_from_json_yaml(path: Path, text: str) -> list[dict]:
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    return [{
        "prompt": f"Beschreibe die Konfiguration in {path.name}.",
        "response": text[:MAX_RESPONSE],
        "source": str(path),
    }]


def export_all() -> list[dict]:
    seen: set[tuple[str, str]] = set()
    all_samples: list[dict] = []

    for base in SOURCES:
        for path in iter_files(base):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if len(text.strip()) < 30:
                continue
            ext = path.suffix.lower()
            if ext == ".md":
                items = samples_from_markdown(path, text)
            elif ext == ".py":
                try:
                    items = samples_from_python(path, text)
                except SyntaxError:
                    items = samples_from_markdown(path, text)
            elif ext in {".json", ".yaml", ".yml"}:
                items = samples_from_json_yaml(path, text)
            else:
                items = samples_from_markdown(path, text)

            for item in items:
                key = (item["prompt"], item["response"][:200])
                if key in seen:
                    continue
                seen.add(key)
                all_samples.append({
                    "prompt": item["prompt"],
                    "response": item["response"],
                    "source": item.get("source", str(path)),
                })
    return all_samples


def main() -> None:
    samples = export_all()
    with open(OUT, "w", encoding="utf-8") as f:
        for row in samples:
            f.write(json.dumps({
                "prompt": row["prompt"],
                "response": row["response"],
            }, ensure_ascii=False) + "\n")
    meta = OUT.with_suffix(".meta.json")
    meta.write_text(json.dumps({
        "count": len(samples),
        "sources": [str(s) for s in SOURCES if s.exists()],
        "output": str(OUT),
    }, indent=2), encoding="utf-8")
    print(f"[*] Exportiert: {len(samples)} Beispiele -> {OUT}")
    print(f"[*] Meta: {meta}")


if __name__ == "__main__":
    main()