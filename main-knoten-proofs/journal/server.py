# -*- coding: utf-8 -*-
"""HTTP-Ingest-Server fuer das Voice-Journal.

Kleiner, eigenstaendiger FastAPI-Server — absichtlich NICHT ins grosse
Dashboard-app.py eingebaut, damit er unabhaengig laufen kann (z.B. dauerhaft
als Hintergrunddienst, waehrend das Dashboard nur bei Bedarf laeuft).

Start (im Repo-Root):
    set JOURNAL_TOKEN=<geheimes-token>
    python -m uvicorn journal.server:app --host 0.0.0.0 --port 8787

Sicherheit: Jeder Request braucht den Header `X-Journal-Token`, der mit der
Umgebungsvariable JOURNAL_TOKEN uebereinstimmen muss. Ohne gesetztes
JOURNAL_TOKEN nimmt der Server nichts an (kein stiller unauthentifizierter
Betrieb).
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from journal.pipeline import JournalPipeline

app = FastAPI(title="Voice-Journal Ingest")
_pipeline = JournalPipeline()


class NoteIn(BaseModel):
    text: str
    ts: Optional[str] = None      # ISO-8601; fehlt er, gilt die Serverzeit
    source: str = "phone"


def _check_token(token: Optional[str]) -> None:
    expected = os.getenv("JOURNAL_TOKEN")
    if not expected:
        raise HTTPException(503, "JOURNAL_TOKEN ist auf dem Server nicht gesetzt — Ingest deaktiviert.")
    if token != expected:
        raise HTTPException(401, "Ungueltiges oder fehlendes X-Journal-Token.")


@app.post("/journal/note")
def add_note(note: NoteIn, x_journal_token: Optional[str] = Header(default=None)):
    _check_token(x_journal_token)
    try:
        result = _pipeline.ingest_note(note.text, ts=note.ts, source=note.source)
    except ValueError as e:
        raise HTTPException(422, str(e))
    return result


@app.get("/journal/today", response_class=PlainTextResponse)
def get_today(x_journal_token: Optional[str] = Header(default=None)):
    _check_token(x_journal_token)
    path = _pipeline.diary_dir / f"{date.today().isoformat()}.md"
    if not path.exists():
        return f"# Tagebuch {date.today().isoformat()}\n\n(noch keine Eintraege)\n"
    return path.read_text(encoding="utf-8")


@app.get("/journal/health")
def health():
    return {"ok": True, "token_configured": bool(os.getenv("JOURNAL_TOKEN"))}
