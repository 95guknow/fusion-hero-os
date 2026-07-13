# -*- coding: utf-8 -*-
"""Fusion Hero OS GUI — kanonisches Repo-Paket."""
from gui.config import GUI_VERSION, API_BASE, WORKSPACE_URL, BACKEND_URL
from gui.fusion_gui import get_gui_status
from gui.theme_3d import inject_theme, THEME_VERSION
from gui.interactions import inject_drag_script, set_action_refs, async_action
from gui.era_design import ERA_EFFICIENCY, ERA_VISUAL, THEME_VERSION, era_meta
from gui.web_scripts import INTERACTION_VERSION, drag_script

__all__ = [
    "GUI_VERSION", "API_BASE", "WORKSPACE_URL", "BACKEND_URL",
    "get_gui_status", "inject_theme", "THEME_VERSION",
    "inject_drag_script", "set_action_refs", "async_action",
    "INTERACTION_VERSION", "drag_script",
    "ERA_VISUAL", "ERA_EFFICIENCY", "era_meta",
]