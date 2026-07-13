# -*- coding: utf-8 -*-
"""Tests fuer journal/pipeline.py (Klassifikation, Dedup, Rendering, Inbox)."""
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from journal.pipeline import JournalPipeline, MANUAL_MARKER


@pytest.fixture
def pipe(tmp_path):
    return JournalPipeline(base_dir=tmp_path)


def test_classify_keywords(pipe):
    assert pipe.classify("Der QUBO Solver hat einen Bug im Test") == "Projekt & Code"
    assert pipe.classify("Bin heute total müde, Kopfschmerz seit dem Sport") == "Gesundheit & Koerper"
    assert pipe.classify("Neue Idee: Hypothese zur Energie-Landschaft") == "Ideen & Erkenntnisse"


def test_classify_fallback(pipe):
    assert pipe.classify("xyzzy blubb") == "Sonstiges"


def test_classify_most_hits_wins(pipe):
    # "idee" (1x Ideen) vs. "code"+"bug"+"test" (3x Projekt) -> Projekt gewinnt
    text = "idee: der code hat einen bug, test schreiben"
    assert pipe.classify(text) == "Projekt & Code"


def test_segment_wraps_midnight(pipe):
    assert pipe.segment_for(datetime(2026, 7, 5, 23, 30)) == "Nacht"
    assert pipe.segment_for(datetime(2026, 7, 5, 2, 0)) == "Nacht"
    assert pipe.segment_for(datetime(2026, 7, 5, 8, 0)) == "Morgen"
    assert pipe.segment_for(datetime(2026, 7, 5, 15, 0)) == "Nachmittag"


def test_ingest_creates_store_and_diary(pipe):
    res = pipe.ingest_note("QUBO Bug gefunden im Solver", ts="2026-07-05T14:30:00")
    assert res["theme"] == "Projekt & Code"
    assert res["duplicate"] is False
    store = json.loads((pipe.data_dir / "2026-07-05.json").read_text(encoding="utf-8"))
    assert len(store["notes"]) == 1
    md = (pipe.diary_dir / "2026-07-05.md").read_text(encoding="utf-8")
    assert "## Projekt & Code" in md
    assert "**14:30** (Nachmittag) QUBO Bug gefunden im Solver" in md


def test_ingest_dedup_same_day(pipe):
    pipe.ingest_note("QUBO Bug gefunden", ts="2026-07-05T10:00:00")
    res = pipe.ingest_note("  qubo   bug GEFUNDEN ", ts="2026-07-05T11:00:00")
    assert res["duplicate"] is True
    store = json.loads((pipe.data_dir / "2026-07-05.json").read_text(encoding="utf-8"))
    assert len(store["notes"]) == 1


def test_ingest_empty_raises(pipe):
    with pytest.raises(ValueError):
        pipe.ingest_note("   ")


def test_manual_section_preserved(pipe):
    pipe.ingest_note("Erste Idee notiert", ts="2026-07-05T09:00:00")
    diary = pipe.diary_dir / "2026-07-05.md"
    content = diary.read_text(encoding="utf-8")
    diary.write_text(content + "\nMein handgeschriebener Absatz.\n", encoding="utf-8")
    pipe.ingest_note("Zweiter Gedanke: neue Hypothese", ts="2026-07-05T10:00:00")
    md = diary.read_text(encoding="utf-8")
    assert "Mein handgeschriebener Absatz." in md
    assert md.index(MANUAL_MARKER) < md.index("Mein handgeschriebener Absatz.")
    assert "Zweiter Gedanke" in md


def test_process_inbox(pipe):
    pipe.inbox_dir.mkdir(parents=True)
    lines = [
        json.dumps({"text": "Termin beim Arzt planen", "ts": "2026-07-05T08:00:00"}),
        json.dumps({"text": "Termin beim Arzt planen", "ts": "2026-07-05T08:00:00"}),  # Duplikat
        "kein json",
        json.dumps({"ohne_text": True}),
    ]
    (pipe.inbox_dir / "drop.jsonl").write_text("\n".join(lines), encoding="utf-8")
    stats = pipe.process_inbox()
    assert stats == {"ingested": 1, "duplicates": 1, "errors": 2, "files": 1}
    assert not (pipe.inbox_dir / "drop.jsonl").exists()
    assert (pipe.inbox_dir / "processed" / "drop.jsonl").exists()


def test_notes_sorted_by_time_in_render(pipe):
    pipe.ingest_note("Abends: commit gemacht", ts="2026-07-05T20:00:00")
    pipe.ingest_note("Morgens: code review", ts="2026-07-05T08:00:00")
    md = (pipe.diary_dir / "2026-07-05.md").read_text(encoding="utf-8")
    assert md.index("08:00") < md.index("20:00")
