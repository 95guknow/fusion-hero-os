"""Fusion Hero OS — Multimodal-Archiv-Protokoll (MAP) v1.0.

Allgemeine Multimodalitaet nach dem Muster der grossen Provider — ehrlich
umgesetzt fuer dieses Repo: KEIN Modell-Training. Das Protokoll macht drei
Dinge, alle maschinell pruefbar:

  1. DURCHGEHEN  — Archiv-Sweep: klassifiziert jede Datei der Archiv-Wurzeln
     nach Modalitaet (text, code, pdf, image, audio, video, data, bundle)
     und baut ein Inventar mit Hash, Groesse, mtime.
  2. EXTRAHIEREN — je Modalitaet der beste verfuegbare lokale Extraktor:
     Text/Code direkt; PDF via pypdf (Seiten + Textausbeute); Bild via PIL
     (Format + Dimensionen). Fehlt ein Extraktor, steht ehrlich
     'extractor_missing' im Eintrag — nie stiller Erfolg.
  3. ROUTEN      — mappt jede Modalitaet auf die dafuer noetige
     Provider-Faehigkeit und prueft je Framework aus llm_frameworks.yaml,
     ob der Zugang LIVE ist (Key-Umgebungsvariable gesetzt) oder nur
     konfiguriert. Key-WERTE werden nie gelesen oder ausgegeben — nur
     gesetzt/nicht-gesetzt.

Inventar-Rescans laufen ueber das Quanten-Wörterbuch (mtime-Signatur):
wiederholte Aufrufe sind praktisch kostenlos, solange sich die Archive
nicht aendern.

Nutzung:
    python -m fusion_hero_os.core.multimodal_protocol            # Zusammenfassung
    python -m fusion_hero_os.core.multimodal_protocol --scan     # Inventar schreiben
    python -m fusion_hero_os.core.multimodal_protocol --routing  # Zugangs-/Routing-Matrix
    python -m fusion_hero_os.core.multimodal_protocol --check    # Gate: Inventar baubar
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# Archiv-Wurzeln, die das Protokoll durchgeht (legacy_sources bewusst nicht:
# Fremd-Snapshots, siehe IMPORT_MANIFEST.md).
ARCHIVE_ROOTS = (
    "04_Buch_und_Archiv",
    "06_Master_Archive",
    "docs",
    "archive",
    "memes",
    "03_VR_Assets",
    "visual_seeds",
    "tts",
)

EXCLUDED_DIR_NAMES = {"__pycache__", "node_modules", ".git", ".svelte-kit"}

MODALITY_BY_EXT: dict[str, str] = {
    ".md": "text", ".txt": "text", ".rst": "text", ".toc": "text",
    ".html": "text", ".xml": "text",
    ".py": "code", ".rs": "code", ".js": "code", ".ts": "code",
    ".svelte": "code", ".sh": "code", ".ps1": "code", ".bat": "code", ".c": "code",
    ".json": "data", ".yaml": "data", ".yml": "data", ".jsonl": "data",
    ".csv": "data", ".spec": "data",
    ".pdf": "pdf",
    ".jpg": "image", ".jpeg": "image", ".png": "image", ".webp": "image",
    ".gif": "image",
    # SVG ist XML, kein Rasterbild. Als "image" gefuehrt landete es bei
    # PIL.Image.open und scheiterte dort zwangslaeufig ("cannot identify image
    # file") — das Archiv-Inventar brach an jeder SVG-Datei ab. Als Text ist es
    # sowohl extrahierbar als auch richtig geroutet: ein Sprachmodell liest
    # SVG-Quelle direkt, waehrend "vision" erst eine Rasterung braeuchte.
    ".svg": "text",
    ".mp3": "audio", ".wav": "audio", ".ogg": "audio", ".flac": "audio", ".m4a": "audio",
    ".mp4": "video", ".mkv": "video", ".webm": "video", ".mov": "video",
    ".zip": "bundle", ".tar": "bundle", ".gz": "bundle", ".7z": "bundle",
}

# Modalitaet -> benoetigte Provider-Faehigkeit (Routing-Ziel).
CAPABILITY_BY_MODALITY: dict[str, str] = {
    "text": "text-generation",
    "code": "text-generation",
    "data": "text-generation",
    "pdf": "text-generation",       # nach lokaler Extraktion
    "image": "vision",
    "audio": "audio-transcription",
    "video": "video-understanding",
    "bundle": "none (erst entpacken)",
    "other": "none (unklassifiziert)",
}

# Welche Faehigkeiten die konfigurierten Frameworks laut ihrer Modellfamilien
# abdecken. Bewusst konservativ; 'vision' nur wo Standard-Modelle es koennen.
FRAMEWORK_CAPABILITIES: dict[str, list[str]] = {
    "grok": ["text-generation", "vision"],
    "claude": ["text-generation", "vision"],
    "gpt": ["text-generation", "vision", "audio-transcription"],
    "gemini": ["text-generation", "vision", "audio-transcription", "video-understanding"],
    "openrouter": ["text-generation", "vision"],
    "ollama": ["text-generation"],
}

_HASH_CAP_BYTES = 8 * 1024 * 1024  # Hash liest max. 8 MB je Datei (Archiv-PDFs sind klein)


@dataclass
class InventoryEntry:
    path: str
    modality: str
    size_bytes: int
    sha256: str
    extraction: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stufe 1+2: Durchgehen + Extrahieren
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read(_HASH_CAP_BYTES))
    return h.hexdigest()


def _extract_text(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        return {"status": "ok", "chars": len(text), "lines": text.count("\n") + 1}
    except Exception as e:
        return {"status": "error", "error": str(e)[:120]}


def _extract_pdf(path: Path) -> dict[str, Any]:
    try:
        import logging
        from pypdf import PdfReader
        # pypdf repariert leicht defekte Trailer selbst, meldet das aber laut;
        # die Reparatur ist fuer das Inventar irrelevant -> nur echte Fehler.
        logging.getLogger("pypdf").setLevel(logging.ERROR)
    except ImportError:
        return {"status": "extractor_missing", "hint": "pip install pypdf"}
    try:
        reader = PdfReader(str(path))
        chars = 0
        for page in reader.pages:
            chars += len(page.extract_text() or "")
        return {"status": "ok", "pages": len(reader.pages), "chars": chars,
                "text_extractable": chars > 0}
    except Exception as e:
        return {"status": "error", "error": str(e)[:120]}


def _extract_image(path: Path) -> dict[str, Any]:
    try:
        from PIL import Image
    except ImportError:
        return {"status": "extractor_missing", "hint": "pip install Pillow"}
    try:
        with Image.open(path) as img:
            return {"status": "ok", "format": img.format,
                    "width": img.width, "height": img.height}
    except Exception as e:
        return {"status": "error", "error": str(e)[:120]}


def _mutagen_info(path: Path) -> dict[str, Any]:
    """Shared audio/video metadata extraction via mutagen.

    mutagen auto-detects the container and reads its own tag/info format;
    it covers every declared audio extension (mp3/wav/ogg/flac/m4a) and the
    QuickTime-family video containers (mp4/mov) via mutagen.mp4, but not
    Matroska/WebM (mkv/webm) - those come back honestly as
    'unsupported_container' rather than a fabricated success.
    """
    try:
        import mutagen
    except ImportError:
        return {"status": "extractor_missing", "hint": "pip install mutagen"}
    try:
        f = mutagen.File(str(path))
    except Exception as e:
        return {"status": "error", "error": str(e)[:120]}
    if f is None:
        return {"status": "unsupported_container", "container": path.suffix.lower().lstrip(".")}
    info = f.info
    out: dict[str, Any] = {
        "status": "ok",
        "duration_seconds": round(getattr(info, "length", 0.0), 3),
    }
    for attr in ("bitrate", "sample_rate", "channels"):
        val = getattr(info, attr, None)
        if val is not None:
            out[attr] = val
    return out


def _extract_audio(path: Path) -> dict[str, Any]:
    return _mutagen_info(path)


def _extract_video(path: Path) -> dict[str, Any]:
    return _mutagen_info(path)


_EXTRACTORS = {
    "text": _extract_text,
    "code": _extract_text,
    "data": _extract_text,
    "pdf": _extract_pdf,
    "image": _extract_image,
    "audio": _extract_audio,
    "video": _extract_video,
}


def classify(path: Path) -> str:
    return MODALITY_BY_EXT.get(path.suffix.lower(), "other")


def _iter_archive_files():
    for root_name in ARCHIVE_ROOTS:
        root = REPO_ROOT / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_DIR_NAMES for part in path.parts):
                continue
            yield path


def build_inventory() -> list[InventoryEntry]:
    entries: list[InventoryEntry] = []
    for path in _iter_archive_files():
        rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        modality = classify(path)
        extractor = _EXTRACTORS.get(modality)
        extraction = extractor(path) if extractor else {"status": "extractor_missing",
                                                        "hint": f"kein lokaler Extraktor fuer '{modality}'"}
        entries.append(InventoryEntry(
            path=rel, modality=modality,
            size_bytes=path.stat().st_size,
            sha256=_sha256(path),
            extraction=extraction,
        ))
    return entries


def _archive_signature() -> str:
    count, max_mtime = 0, 0.0
    for path in _iter_archive_files():
        count += 1
        mt = path.stat().st_mtime
        if mt > max_mtime:
            max_mtime = mt
    return f"{count}:{max_mtime:.6f}"


def build_inventory_cached() -> list[InventoryEntry]:
    """Inventar ueber das Quanten-Wörterbuch (Rescan nur bei Archiv-Aenderung)."""
    try:
        from fusion_hero_os.core.quantum_dictionaries import get_quantum_dictionary
    except Exception:
        return build_inventory()
    qd = get_quantum_dictionary("multimodal-inventory", max_entries=4)
    return qd.get_or_compute("archive-inventory", build_inventory,
                             signature=_archive_signature())


# ---------------------------------------------------------------------------
# Stufe 3: Routen (Zugaenge pruefen, ohne Key-Werte zu lesen)
# ---------------------------------------------------------------------------

def _load_frameworks() -> dict[str, dict[str, Any]]:
    try:
        import yaml
        data = yaml.safe_load((REPO_ROOT / "llm_frameworks.yaml").read_text(encoding="utf-8"))
        return (data or {}).get("frameworks", {}) or {}
    except Exception:
        return {}


def provider_access_status() -> dict[str, dict[str, Any]]:
    """Je Framework: live (Key-Env gesetzt) oder configured_no_key.

    Ollama gilt als live-faehig ohne Key (lokal); ob der Daemon laeuft,
    prueft weiterhin der Router zur Laufzeit (kein Netzwerkzwang hier).
    """
    status: dict[str, dict[str, Any]] = {}
    for name, spec in _load_frameworks().items():
        key_envs = spec.get("api_key_env") or []
        if isinstance(key_envs, str):
            key_envs = [key_envs]
        has_key = any(os.environ.get(env, "").strip() for env in key_envs)
        keyless_local = not key_envs  # z.B. ollama
        status[name] = {
            "display_name": spec.get("display_name", name),
            "capabilities": FRAMEWORK_CAPABILITIES.get(name, ["text-generation"]),
            "key_env_vars": key_envs,
            "access": "live" if (has_key or keyless_local) else "configured_no_key",
        }
    return status


def routing_matrix() -> dict[str, dict[str, Any]]:
    """Modalitaet -> Faehigkeit -> Provider (live zuerst, dann konfiguriert)."""
    providers = provider_access_status()
    matrix: dict[str, dict[str, Any]] = {}
    for modality, capability in CAPABILITY_BY_MODALITY.items():
        live = [n for n, p in providers.items()
                if capability in p["capabilities"] and p["access"] == "live"]
        configured = [n for n, p in providers.items()
                      if capability in p["capabilities"] and p["access"] != "live"]
        matrix[modality] = {
            "required_capability": capability,
            "live_providers": sorted(live),
            "configured_no_key": sorted(configured),
            "servable_now": bool(live) if not capability.startswith("none") else False,
        }
    return matrix


# ---------------------------------------------------------------------------
# Bericht
# ---------------------------------------------------------------------------

def summary(entries: list[InventoryEntry]) -> dict[str, Any]:
    by_modality: dict[str, dict[str, Any]] = {}
    for e in entries:
        slot = by_modality.setdefault(e.modality, {"files": 0, "bytes": 0,
                                                   "extracted_ok": 0, "extractor_missing": 0,
                                                   "errors": 0})
        slot["files"] += 1
        slot["bytes"] += e.size_bytes
        st = e.extraction.get("status")
        if st == "ok":
            slot["extracted_ok"] += 1
        elif st == "extractor_missing":
            slot["extractor_missing"] += 1
        else:
            slot["errors"] += 1
    return {
        "protocol": "Multimodal-Archiv-Protokoll v1.0",
        "archive_roots": list(ARCHIVE_ROOTS),
        "total_files": len(entries),
        "by_modality": by_modality,
        "routing": routing_matrix(),
    }


def to_dict(entries: list[InventoryEntry]) -> dict[str, Any]:
    d = summary(entries)
    d["inventory"] = [vars(e) for e in entries]
    return d


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Multimodal-Archiv-Protokoll")
    parser.add_argument("--scan", action="store_true",
                        help="Inventar nach docs/v8/multimodal_inventory.json schreiben")
    parser.add_argument("--routing", action="store_true", help="Routing-Matrix anzeigen")
    parser.add_argument("--check", action="store_true", help="Gate: Inventar baubar, keine Lesefehler")
    parser.add_argument("--json", action="store_true", help="Voll-JSON nach stdout")
    args = parser.parse_args(argv)

    entries = build_inventory_cached()
    info = summary(entries)

    if args.json:
        print(json.dumps(to_dict(entries), indent=2, ensure_ascii=False))
        return 0

    if args.scan:
        out = REPO_ROOT / "docs" / "v8" / "multimodal_inventory.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(to_dict(entries), indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        print(f"[MAP] Inventar geschrieben: {out}")

    if args.routing:
        for modality, route in info["routing"].items():
            print(f"[MAP] {modality:8s} -> {route['required_capability']:22s} "
                  f"live={route['live_providers'] or '-'} "
                  f"konfiguriert={route['configured_no_key'] or '-'}")

    print(f"[MAP] Dateien={info['total_files']} "
          + " ".join(f"{m}={s['files']}" for m, s in sorted(info["by_modality"].items())))

    if args.check:
        errors = [e for e in entries if e.extraction.get("status") == "error"]
        for e in errors[:10]:
            print(f"[MAP][FEHLER] {e.path}: {e.extraction.get('error')}")
        if errors:
            print(f"[MAP][FATAL] {len(errors)} Dateien mit Extraktionsfehlern.")
            return 1
        print("[MAP] --check bestanden: Inventar vollstaendig, keine Extraktionsfehler.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
