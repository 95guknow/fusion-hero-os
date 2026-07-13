# -*- coding: utf-8 -*-
"""Eingabe-Gateway — nur Regeln + minimale Ausgabe. Keine schwere Verarbeitung."""
from __future__ import annotations

import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

from grok_bridge import get_grok_bridge

MAX_INPUT_LEN = 8000
MAX_CODE_LEN = 50000
ALLOWED_KINDS = frozenset({
    "chat", "command", "load_all", "mainframe", "benchmark", "sync", "qubo",
    "agent", "peer_review", "foundation", "profile", "meta_layer", "pipeline",
    "layer4", "hyperthreading", "orchestrate", "resources", "autoload",
    "substrate_tune", "windows_substrate", "hero_guide",
})

# Nur diese Intents bleiben synchron (Pulse/Status — keine Worker-Last)
SYNC_INTENTS = frozenset({"health", "signal_network"})


@dataclass
class InputAck:
    accepted: bool
    job_id: str
    kind: str
    ack: str
    intents: List[str] = field(default_factory=list)
    error: Optional[str] = None
    sync: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def _new_job_id() -> str:
    return str(uuid.uuid4())[:12]


def validate_input(kind: str, message: str = "", code: str = "", payload: Optional[dict] = None) -> Optional[str]:
    if kind not in ALLOWED_KINDS:
        return f"Unbekannte Eingabeart: {kind}"
    if len(message) > MAX_INPUT_LEN:
        return f"Nachricht zu lang (max {MAX_INPUT_LEN})"
    if len(code) > MAX_CODE_LEN:
        return f"Code zu lang (max {MAX_CODE_LEN})"
    if not message.strip() and not code.strip() and kind in ("chat", "command", "peer_review", "foundation", "hero_guide"):
        return "Leere Eingabe"
    if payload and len(str(payload)) > MAX_INPUT_LEN * 2:
        return "Payload zu gross"
    return None


def classify_message(message: str) -> List[str]:
    bridge = get_grok_bridge()
    return bridge._detect_intents(message)


def accept_input(
    kind: str = "command",
    message: str = "",
    code: str = "",
    payload: Optional[dict] = None,
    history: Optional[List[dict]] = None,
) -> InputAck:
    """Nimmt Eingabe an — gibt nur Ack + job_id zurueck."""
    err = validate_input(kind, message, code, payload)
    job_id = _new_job_id()
    if err:
        return InputAck(accepted=False, job_id=job_id, kind=kind, ack="", error=err)

    intents: List[str] = []
    if message.strip():
        intents = classify_message(message)
    if kind != "chat" and kind != "command":
        intents = [kind.replace("-", "_")] if kind not in intents else intents

    sync = bool(intents) and all(i in SYNC_INTENTS for i in intents) and kind in ("chat", "command")

    if sync:
        ack = "Status-Anfrage — minimale synchrone Antwort."
    elif intents:
        ack = f"Eingabe akzeptiert → Worker ({', '.join(intents[:3])})"
    else:
        ack = "Eingabe akzeptiert → Worker (verarbeitung)"

    return InputAck(
        accepted=True,
        job_id=job_id,
        kind=kind,
        ack=ack,
        intents=intents,
        sync=sync,
    )


def build_job_payload(
    ack: InputAck,
    message: str = "",
    code: str = "",
    payload: Optional[dict] = None,
    history: Optional[List[dict]] = None,
) -> dict:
    return {
        "job_id": ack.job_id,
        "kind": ack.kind,
        "message": message,
        "code": code,
        "payload": payload or {},
        "history": history or [],
        "intents": ack.intents,
        "queued_at": time.time(),
    }