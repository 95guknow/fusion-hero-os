# -*- coding: utf-8 -*-
"""Fusion GUI — Repo-Status, Pfade, Monitor-Integration."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from gui.config import (
    API_BASE, BACKEND_URL, DASHBOARD, GUI_LAYER, GUI_VERSION,
    REPO_ROOT, STATIC, TEMPLATES, WORKSPACE_URL, WORKSPACE_PORT,
)
from gui.era_design import era_meta
from gui.web_scripts import INTERACTION_VERSION


def get_gui_status() -> Dict[str, Any]:
    templates = [p.name for p in TEMPLATES.glob("*.html")] if TEMPLATES.exists() else []
    return {
        "module": GUI_LAYER,
        "version": GUI_VERSION,
        "repo_root": str(REPO_ROOT),
        "dashboard": str(DASHBOARD),
        "workspace_url": WORKSPACE_URL,
        "backend_url": BACKEND_URL,
        "api_base": API_BASE,
        "workspace_port": WORKSPACE_PORT,
        "entry": "workspace.py",
        "package": "gui/",
        "templates": templates,
        "static": STATIC.exists(),
        "surfaces": {
            "workspace": WORKSPACE_URL,
            "monitor": f"{BACKEND_URL}/",
            "heroic": f"{BACKEND_URL}/static" if STATIC.exists() else None,
        },
        "input_layer": "/api/input",
        "job_poll": "/api/jobs/{id}",
        "era": era_meta(),
        "interactions": {
            "version": INTERACTION_VERSION,
            "theme": "/api/gui/theme.css",
            "theme_static": "fusion_gui.css",
            "script": "fusion_gui.js",
            "drag_script": "fusion_drag.js",
            "storage_key": "fusion-monitor-panel-positions",
            "shortcuts": {
                "refresh": "Ctrl+R",
                "full_status": "Ctrl+Enter",
                "focus_panel": "1-3",
            },
            "panels": ["jobs", "quick", "hints", "output"],
            "quick_actions": ["load", "benchmark", "status", "grok"],
        },
    }


def workspace_script_path() -> Path:
    return DASHBOARD / "workspace.py"