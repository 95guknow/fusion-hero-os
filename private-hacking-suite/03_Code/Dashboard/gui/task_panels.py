# -*- coding: utf-8 -*-
"""Verschiebbare Task-Subbildschirme für Dashboard-Interaktivität."""
from __future__ import annotations

from typing import Any, Callable, Coroutine, Dict, Optional

from nicegui import ui

from gui.interactions import init_panel_drag, job_status_class


def build_task_layer(
    refs: Dict[str, Any],
    *,
    on_quick_load: Callable[[], Coroutine],
    on_quick_benchmark: Callable[[], Coroutine],
    on_quick_status: Callable[[], Coroutine],
    on_quick_grok: Callable[[], None],
    on_reset_layout: Callable[[], None],
) -> None:
    """Fusioniert schwebende Panels in den Dashboard-Tab (ersetzt nichts)."""
    with ui.element("div").props("id=fusion-task-layer").classes("fusion-task-layer"):
        _panel_jobs(refs)
        _panel_quick(
            refs,
            on_quick_load=on_quick_load,
            on_quick_benchmark=on_quick_benchmark,
            on_quick_status=on_quick_status,
            on_quick_grok=on_quick_grok,
            on_reset_layout=on_reset_layout,
        )
        _panel_hints(refs)

    init_panel_drag("fusion-panel-jobs", ".fusion-task-handle", 12, 12)
    init_panel_drag("fusion-panel-quick", ".fusion-task-handle", 12, 200)
    init_panel_drag("fusion-panel-hints", ".fusion-task-handle", 12, 380)


def _panel_jobs(refs: dict) -> None:
    with ui.element("div").props("id=fusion-panel-jobs").classes("fusion-task-panel"):
        with ui.row().classes("fusion-task-handle w-full items-center gap-2"):
            ui.icon("drag_indicator").classes("text-[#64748b] text-sm")
            ui.label("Worker-Jobs").classes("fusion-task-title flex-grow")
            refs["job_badge"] = ui.badge("0", color="teal")
        refs["job_list"] = ui.column().classes("fusion-job-list w-full gap-0")


def _panel_quick(
    refs: dict,
    *,
    on_quick_load: Callable[[], Coroutine],
    on_quick_benchmark: Callable[[], Coroutine],
    on_quick_status: Callable[[], Coroutine],
    on_quick_grok: Callable[[], None],
    on_reset_layout: Callable[[], None],
) -> None:
    with ui.element("div").props("id=fusion-panel-quick").classes("fusion-task-panel"):
        with ui.row().classes("fusion-task-handle w-full items-center gap-2"):
            ui.icon("drag_indicator").classes("text-[#64748b] text-sm")
            ui.label("Schnellaktionen").classes("fusion-task-title flex-grow")
        with ui.row().classes("fusion-quick-grid w-full"):
            ui.button("Laden", on_click=on_quick_load).props("no-caps dense").classes(
                "fusion-btn-primary flex-1"
            )
            ui.button("Bench", on_click=on_quick_benchmark).props("no-caps dense").classes(
                "fusion-btn-secondary flex-1"
            )
            ui.button("Status", on_click=on_quick_status).props("no-caps dense").classes(
                "fusion-btn-ghost flex-1"
            )
            ui.button("Grok", on_click=on_quick_grok).props("no-caps dense").classes(
                "fusion-btn-accent flex-1"
            )
        ui.button("Layout reset", on_click=on_reset_layout).props("no-caps flat dense").classes(
            "w-full mt-1 text-[#64748b] text-xs"
        )


def _panel_hints(refs: dict) -> None:
    with ui.element("div").props("id=fusion-panel-hints").classes("fusion-task-panel fusion-task-panel--compact"):
        with ui.row().classes("fusion-task-handle w-full items-center gap-2"):
            ui.icon("drag_indicator").classes("text-[#64748b] text-sm")
            ui.label("Tastenkürzel").classes("fusion-task-title flex-grow")
        ui.html(
            '<div class="fusion-hint-list">'
            '<div><kbd>Ctrl</kbd>+<kbd>B</kbd> Sidebar</div>'
            '<div><kbd>Ctrl</kbd>+<kbd>R</kbd> Refresh</div>'
            '<div><kbd>Ctrl</kbd>+<kbd>Enter</kbd> Senden</div>'
            '<div><kbd>1</kbd>–<kbd>7</kbd> Tabs wechseln</div>'
            '<div>Layer &amp; Panels per Griff ziehen</div>'
            "</div>"
        )


def render_job_list(
    refs: dict,
    jobs: list[dict],
    on_job_click: Optional[Callable[[str], Coroutine]] = None,
) -> None:
    container = refs.get("job_list")
    if container is None:
        return
    active = sum(1 for j in jobs if j.get("status") in ("queued", "running"))
    badge = refs.get("job_badge")
    if badge:
        badge.set_text(str(active) if active else str(len(jobs)))
    container.clear()
    with container:
        if not jobs:
            ui.label("Keine Jobs").classes("fusion-label-muted text-xs px-2 py-1")
            return
        for job in jobs[:10]:
            jid = job.get("job_id", "")
            kind = job.get("kind", "?")
            status = (job.get("status") or "queued").upper()
            cls = job_status_class(job.get("status", "queued"))

            def _make_click(job_id: str):
                async def _handler():
                    if on_job_click:
                        await on_job_click(job_id)
                return _handler

            row = ui.row().classes(f"fusion-job-row {cls} w-full items-center gap-2 cursor-pointer")
            if on_job_click:
                row.on("click", _make_click(jid))
            with row:
                ui.label(jid[:8]).classes("fusion-job-id")
                ui.label(kind).classes("fusion-job-kind flex-grow")
                ui.label(status).classes("fusion-job-st")