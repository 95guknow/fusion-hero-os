"""Thin wrapper — canonical implementation lives in core.ghosthunt_hook."""
from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent.parent / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from ghosthunt_hook import ghosthunt_hook  # noqa: E402,F401