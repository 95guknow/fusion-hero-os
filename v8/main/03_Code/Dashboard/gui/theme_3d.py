# -*- coding: utf-8 -*-
"""Fusion Hero OS — Theme-Injection (2026 Look · 1996-core Effizienz)."""
from __future__ import annotations

from nicegui import ui

from gui.era_design import THEME_VERSION, workspace_css

THEME_CSS = workspace_css()


def inject_theme() -> None:
    """Fusioniert Era-Theme in den Workspace-Head."""
    ui.add_head_html(f"<style id='fusion-theme-{THEME_VERSION}'>{THEME_CSS}</style>")


def metric_bar_html(bar_id: str, label: str, fill_class: str, pct: float = 0) -> str:
    pct = max(0, min(100, pct))
    return (
        f'<div class="fusion-metric-block">'
        f'<div class="fusion-metric-label"><span>{label}</span>'
        f'<span id="{bar_id}-pct">{pct:.0f}%</span></div>'
        f'<div class="fusion-metric-track">'
        f'<div id="{bar_id}-fill" class="fusion-metric-fill {fill_class}" '
        f'style="width:{pct:.1f}%"></div></div></div>'
    )


def update_metric_bar(bar_id: str, pct: float) -> None:
    pct = max(0, min(100, pct))
    ui.run_javascript(
        f"var f=document.getElementById('{bar_id}-fill');"
        f"var p=document.getElementById('{bar_id}-pct');"
        f"if(f)f.style.width='{pct:.1f}%';"
        f"if(p)p.textContent='{pct:.0f}%';"
    )