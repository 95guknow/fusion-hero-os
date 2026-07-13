# -*- coding: utf-8 -*-
"""Voice-Journal-Pipeline.

Nimmt Sprach-Transkripte (vom Handy) entgegen, klassifiziert sie thematisch
per lokalem Keyword-Scoring (kein LLM, keine Cloud) und arbeitet sie in ein
Tages-Tagebuch (Markdown) ein.

Datenfluss:
    Handy (STT)  ->  POST /journal/note (server.py)  ->  ingest_note()
                 ->  journal/data/YYYY-MM-DD.json    (kanonischer Store)
                 ->  journal/tagebuch/YYYY-MM-DD.md  (gerendert, pro Ingest neu)

Offline-Weg: Transkript-Dateien (JSONL) in journal/inbox/ ablegen und
`python -m journal.pipeline` ausfuehren.

Alles unterhalb der MANUELL-Markierung im Markdown bleibt beim Neu-Rendern
erhalten — dort kann der Maintainer von Hand weiterschreiben.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"

MANUAL_MARKER = "<!-- MANUELL: alles unterhalb dieser Zeile bleibt bei Neu-Renderings erhalten -->"


@dataclass
class Note:
    note_id: str
    ts: str          # ISO-8601, lokale Zeit
    text: str
    source: str
    theme: str

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.note_id, "ts": self.ts, "text": self.text,
                "source": self.source, "theme": self.theme}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _note_id(text: str) -> str:
    return hashlib.sha1(_normalize(text).encode("utf-8")).hexdigest()[:16]


class JournalPipeline:
    def __init__(self, base_dir: Optional[Path] = None,
                 config_path: Optional[Path] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else BASE_DIR
        self.data_dir = self.base_dir / "data"
        self.inbox_dir = self.base_dir / "inbox"
        self.diary_dir = self.base_dir / "tagebuch"
        cfg_file = Path(config_path) if config_path else CONFIG_PATH
        cfg = yaml.safe_load(cfg_file.read_text(encoding="utf-8"))
        self.themes: List[Dict[str, Any]] = cfg["themes"]
        self.fallback_theme: str = cfg["fallback_theme"]
        self.day_segments: List[Dict[str, Any]] = cfg["day_segments"]

    # ---------------- Klassifikation ----------------

    def classify(self, text: str) -> str:
        """Keyword-Scoring: Thema mit den meisten Treffern; bei 0 Treffern Fallback.

        Bei Gleichstand gewinnt das zuerst konfigurierte Thema.
        """
        norm = _normalize(text)
        best_theme = self.fallback_theme
        best_score = 0
        for theme in self.themes:
            score = sum(1 for kw in theme["keywords"] if kw in norm)
            if score > best_score:
                best_score = score
                best_theme = theme["name"]
        return best_theme

    def segment_for(self, ts: datetime) -> str:
        """Tagesabschnitt (Morgen/Mittag/...) fuer einen Zeitpunkt."""
        h = ts.hour
        for seg in self.day_segments:
            start, end = seg["start"], seg["end"]
            if start < end:
                if start <= h < end:
                    return seg["name"]
            else:  # wickelt ueber Mitternacht (z.B. 23-5)
                if h >= start or h < end:
                    return seg["name"]
        return self.day_segments[0]["name"]

    # ---------------- Ingest ----------------

    def ingest_note(self, text: str, ts: Optional[str] = None,
                    source: str = "phone") -> Dict[str, Any]:
        """Eine Notiz aufnehmen: klassifizieren, im Tages-Store ablegen, Tagebuch rendern.

        Rueckgabe: Note-Dict + "duplicate": True, wenn der Text an dem Tag schon da war.
        """
        text = text.strip()
        if not text:
            raise ValueError("Leere Notiz")
        when = datetime.fromisoformat(ts) if ts else datetime.now()
        note = Note(
            note_id=_note_id(text),
            ts=when.replace(microsecond=0).isoformat(),
            text=text,
            source=source,
            theme=self.classify(text),
        )
        day = when.date()
        store = self._load_day(day)
        duplicate = any(n["id"] == note.note_id for n in store["notes"])
        if not duplicate:
            store["notes"].append(note.to_dict())
            self._save_day(day, store)
            self.render_day(day)
        result = note.to_dict()
        result["duplicate"] = duplicate
        return result

    def process_inbox(self) -> Dict[str, int]:
        """Alle JSONL-Dateien in inbox/ einarbeiten und nach inbox/processed/ verschieben.

        Zeilenformat: {"text": "...", "ts": "2026-07-05T14:30:00", "source": "..."}
        (ts und source optional). Fehlerhafte Zeilen werden gezaehlt und uebersprungen.
        """
        stats = {"ingested": 0, "duplicates": 0, "errors": 0, "files": 0}
        if not self.inbox_dir.is_dir():
            return stats
        processed_dir = self.inbox_dir / "processed"
        for f in sorted(self.inbox_dir.glob("*.jsonl")):
            stats["files"] += 1
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    res = self.ingest_note(rec["text"], ts=rec.get("ts"),
                                           source=rec.get("source", "inbox"))
                    if res["duplicate"]:
                        stats["duplicates"] += 1
                    else:
                        stats["ingested"] += 1
                except (json.JSONDecodeError, KeyError, ValueError):
                    stats["errors"] += 1
            processed_dir.mkdir(parents=True, exist_ok=True)
            f.rename(processed_dir / f.name)
        return stats

    # ---------------- Rendering ----------------

    def render_day(self, day: date) -> Path:
        """Tagebuch-Markdown fuer einen Tag aus dem Store rendern.

        Der manuelle Teil (alles nach MANUAL_MARKER) einer bestehenden Datei
        wird unveraendert uebernommen.
        """
        store = self._load_day(day)
        notes = sorted(store["notes"], key=lambda n: n["ts"])

        theme_order = [t["name"] for t in self.themes] + [self.fallback_theme]
        by_theme: Dict[str, List[Dict[str, Any]]] = {}
        for n in notes:
            by_theme.setdefault(n["theme"], []).append(n)

        lines = [f"# Tagebuch {day.isoformat()}", "",
                 f"_{len(notes)} Erkenntnis(se), automatisch aus Sprachnotizen einsortiert._",
                 ""]
        for theme in theme_order:
            entries = by_theme.pop(theme, None)
            if not entries:
                continue
            lines.append(f"## {theme}")
            for n in entries:
                t = datetime.fromisoformat(n["ts"])
                seg = self.segment_for(t)
                lines.append(f"- **{t.strftime('%H:%M')}** ({seg}) {n['text']}")
            lines.append("")
        # unbekannte Themen (z.B. nach Config-Aenderung) nicht verschlucken
        for theme, entries in by_theme.items():
            lines.append(f"## {theme}")
            for n in entries:
                t = datetime.fromisoformat(n["ts"])
                lines.append(f"- **{t.strftime('%H:%M')}** ({self.segment_for(t)}) {n['text']}")
            lines.append("")

        manual_part = ""
        out_path = self.diary_dir / f"{day.isoformat()}.md"
        if out_path.exists():
            old = out_path.read_text(encoding="utf-8")
            if MANUAL_MARKER in old:
                manual_part = old.split(MANUAL_MARKER, 1)[1]
        lines.append(MANUAL_MARKER)
        content = "\n".join(lines) + manual_part
        if not content.endswith("\n"):
            content += "\n"
        self.diary_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        return out_path

    # ---------------- Store ----------------

    def _day_store_path(self, day: date) -> Path:
        return self.data_dir / f"{day.isoformat()}.json"

    def _load_day(self, day: date) -> Dict[str, Any]:
        p = self._day_store_path(day)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {"date": day.isoformat(), "notes": []}

    def _save_day(self, day: date, store: Dict[str, Any]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._day_store_path(day).write_text(
            json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    stats = JournalPipeline().process_inbox()
    print(f"Inbox verarbeitet: {stats}")
