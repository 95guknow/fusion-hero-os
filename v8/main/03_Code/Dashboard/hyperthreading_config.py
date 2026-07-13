# -*- coding: utf-8 -*-
"""Re-Export — kanonische Implementierung in core.hyperthreading_config."""
from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parents[1] / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from hyperthreading_config import (  # noqa: E402,F401
    disable,
    enable,
    get_virtual_gpu_ht_cache,
    is_hyperthreading_enabled,
    logical_cpu_count,
    parallel_workers,
    status,
)