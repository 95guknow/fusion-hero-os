# -*- coding: utf-8 -*-
"""GUI-Konfiguration — einheitlich fuer Repo, Workspace, Backend."""
from __future__ import annotations

import os
from pathlib import Path

GUI_VERSION = "v1.2"
GUI_LAYER = "HeroicCoreGUI"
REPO_ROOT = Path(__file__).resolve().parents[3]
DASHBOARD = Path(__file__).resolve().parents[1]
TEMPLATES = DASHBOARD / "templates"
STATIC = DASHBOARD / "static"

BACKEND_HOST = os.getenv("FUSION_BACKEND_HOST", "127.0.0.1")
BACKEND_PORT = int(os.getenv("FUSION_BACKEND_PORT", "8000"))
WORKSPACE_HOST = os.getenv("FUSION_WORKSPACE_HOST", "0.0.0.0")
WORKSPACE_PORT = int(os.getenv("FUSION_WORKSPACE_PORT", "8080"))

BACKEND_URL = f"http://{BACKEND_HOST}:{BACKEND_PORT}"
WORKSPACE_URL = f"http://127.0.0.1:{WORKSPACE_PORT}"
API_BASE = BACKEND_URL

SIGNAL_LAYER_DEFAULT = os.getenv("FUSION_GUI_SIGNAL", "pulse")
SIGNAL_CLIENT_ID = "fusion-workspace"