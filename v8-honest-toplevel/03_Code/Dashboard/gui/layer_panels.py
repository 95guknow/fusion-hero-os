# -*- coding: utf-8 -*-
"""Verschiebbare Stack-Layer (Meta · Cyber · Substrat · Fusion) — plug & play."""
from __future__ import annotations

from typing import Any, Dict

from nicegui import ui

from gui.interactions import register_draggable


def build_stack_layers(refs: Dict[str, Any]) -> None:
    """Schwebende Layer-Panels im Dashboard — fusioniert, ersetzt Sidebar nicht."""
    with ui.element("div").props("id=fusion-stack-layers").classes("fusion-stack-layers"):
        _layer_panel(
            refs,
            layer_id="fusion-layer-substrat",
            title="Windows-Substrat",
            accent="fusion-layer--substrat",
            x=12,
            y=520,
            ref_key="layer_substrat",
            hint="Host · Power · RAM",
        )
        _layer_panel(
            refs,
            layer_id="fusion-layer-meta",
            title="Meta-Layer",
            accent="fusion-layer--meta",
            x=300,
            y=520,
            ref_key="layer_meta",
            hint="Fusion Hero OS über Windows",
        )
        _layer_panel(
            refs,
            layer_id="fusion-layer-cyber",
            title="Cyber Layer",
            accent="fusion-layer--cyber",
            x=588,
            y=520,
            ref_key="layer_cyber",
            hint="Optimierung · Signale",
        )
        _layer_panel(
            refs,
            layer_id="fusion-layer-fusion",
            title="Fusion Core",
            accent="fusion-layer--fusion",
            x=876,
            y=520,
            ref_key="layer_fusion",
            hint="Mainframe · Profil · Registry",
        )

    register_draggable("fusion-layer-substrat", ".fusion-layer-handle", 12, 520)
    register_draggable("fusion-layer-meta", ".fusion-layer-handle", 300, 520)
    register_draggable("fusion-layer-cyber", ".fusion-layer-handle", 588, 520)
    register_draggable("fusion-layer-fusion", ".fusion-layer-handle", 876, 520)


def _layer_panel(
    refs: dict,
    *,
    layer_id: str,
    title: str,
    accent: str,
    x: int,
    y: int,
    ref_key: str,
    hint: str,
) -> None:
    with ui.element("div").props(
        f"id={layer_id} data-fusion-drag={layer_id} "
        f"data-fusion-drag-x={x} data-fusion-drag-y={y}"
    ).classes(f"fusion-layer-panel fusion-drag-layer {accent}"):
        with ui.row().classes("fusion-layer-handle w-full items-center gap-2"):
            ui.icon("drag_indicator").classes("text-[#64748b] text-sm")
            ui.label(title).classes("fusion-layer-title flex-grow")
            ui.html('<span class="fusion-layer-plug">PnP</span>')
        ui.label(hint).classes("fusion-layer-hint")
        refs[ref_key] = ui.label("Initialisiere…").classes("fusion-layer-body")