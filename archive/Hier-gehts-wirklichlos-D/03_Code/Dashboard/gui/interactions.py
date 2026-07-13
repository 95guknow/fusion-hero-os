# -*- coding: utf-8 -*-
"""Fusion GUI — Interaktivität, Tastenkürzel, Busy-State, Drag-Hilfen."""
from __future__ import annotations

import functools
from typing import Any, Callable, Coroutine, Optional

from nicegui import ui

from gui.web_scripts import GUI_POSITIONS_KEY, INTERACTION_VERSION, drag_script

DRAG_SCRIPT = drag_script(GUI_POSITIONS_KEY)
_DRAG_QUEUE: list[tuple[str, str, int, int]] = []


def inject_drag_script() -> None:
    ui.add_body_html(
        f"<script id='fusion-drag-{INTERACTION_VERSION}'>{DRAG_SCRIPT}</script>"
    )


def register_draggable(
    element_id: str,
    handle: str = ".fusion-layer-handle",
    x: int = 12,
    y: int = 12,
) -> None:
    """Plug-and-play: Element-ID registrieren — Boot-Skript initialisiert nach DOM."""
    _DRAG_QUEUE.append((element_id, handle, x, y))


def init_panel_drag(
    panel_id: str,
    handle: str = ".fusion-task-handle",
    x: int = 0,
    y: int = 0,
) -> None:
    register_draggable(panel_id, handle, x, y)


def safe_run_javascript(js: str) -> None:
    """JS nur wenn ein NiceGUI-Client verbunden ist — verhindert core.loop-Crashes."""
    try:
        from nicegui import context
        if context.client is None:
            return
        ui.run_javascript(js)
    except Exception:
        pass


def inject_drag_boot() -> None:
    """Alle registrierten Panels/Layer + data-fusion-drag Attribute aktivieren."""
    inits = ";".join(
        f"fusionInitDraggable('{eid}','{hdl}',{x},{y},'{GUI_POSITIONS_KEY}')"
        for eid, hdl, x, y in _DRAG_QUEUE
    )
    scan = f"fusionScanDragLayers('{GUI_POSITIONS_KEY}');"
    body = inits + (";" if inits else "") + scan
    ui.add_body_html(
        f"<script id='fusion-drag-boot-{INTERACTION_VERSION}'>"
        f"(function boot(){{"
        f"if(typeof fusionInitDraggable!=='function'){{setTimeout(boot,50);return;}}"
        f"{body};"
        f"}})();</script>"
    )


def reset_panel_positions() -> None:
    ui.run_javascript(f"fusionResetGuiLayout('{GUI_POSITIONS_KEY}');")
    ui.notify("GUI-Layout zurückgesetzt (Panels + Layer)", type="info")


_busy = False
_action_refs: dict = {}


def set_action_refs(refs: dict) -> None:
    global _action_refs
    _action_refs = refs


def is_busy() -> bool:
    return _busy


def async_action(
    *btn_keys: str,
    busy_msg: str = "Arbeitet…",
    notify_block: bool = True,
) -> Callable:
    """Decorator: sperrt parallele Aktionen, deaktiviert Buttons, Status-Feedback."""

    def decorator(fn: Callable[..., Coroutine]) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            global _busy
            if _busy:
                if notify_block:
                    ui.notify("Bitte warten — Aktion läuft noch", type="warning")
                return None
            _busy = True
            btns = [_action_refs[k] for k in btn_keys if _action_refs.get(k)]
            bar = _action_refs.get("status_bar")
            try:
                for b in btns:
                    b.disable()
                if bar:
                    bar.text = busy_msg
                    bar.classes(replace="text-xs text-[#fbbf24]")
                return await fn(*args, **kwargs)
            finally:
                _busy = False
                for b in btns:
                    b.enable()

        return wrapper

    return decorator


async def copy_to_clipboard(text: str) -> None:
    import json
    ui.run_javascript(f"navigator.clipboard.writeText({json.dumps(text)});")
    ui.notify("In Zwischenablage kopiert", type="positive")


def bind_enter(submit_fn: Callable, element) -> None:
    element.on("keydown.enter", submit_fn)


def job_status_class(status: str) -> str:
    return {
        "done": "fusion-job--done",
        "running": "fusion-job--run",
        "queued": "fusion-job--queue",
        "error": "fusion-job--err",
    }.get(status, "fusion-job--queue")


def format_job_row(job: dict) -> str:
    jid = (job.get("job_id") or "?")[:8]
    kind = job.get("kind", "?")
    status = (job.get("status") or "queued").upper()
    cls = job_status_class(job.get("status", "queued"))
    return (
        f'<div class="fusion-job-row {cls}" data-job="{job.get("job_id","")}" '
        f'title="Klicken für Details">'
        f'<span class="fusion-job-id">{jid}</span>'
        f'<span class="fusion-job-kind">{kind}</span>'
        f'<span class="fusion-job-st">{status}</span></div>'
    )