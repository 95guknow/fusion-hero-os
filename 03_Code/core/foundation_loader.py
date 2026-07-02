# foundation_loader.py — resolve heroic-core-foundation path once

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Callable, Dict, Optional

_CORE = Path(__file__).resolve().parent
_REPO_ROOT = _CORE.parent.parent

_CACHED_PATH: Optional[Path] = None


def get_foundation_path() -> Optional[Path]:
    """Return the first existing foundation package directory, or None."""
    global _CACHED_PATH
    if _CACHED_PATH is not None:
        return _CACHED_PATH if _CACHED_PATH.exists() else None

    candidates = [
        _REPO_ROOT / "01_Framework" / "heroic-core-foundation",
        Path(r"C:\Users\Admin\heroic-core-foundation"),
    ]
    for candidate in candidates:
        if candidate.exists() and (candidate / "foundation.py").exists():
            _CACHED_PATH = candidate
            return candidate
    return None


def ensure_foundation_on_path() -> Optional[Path]:
    """Insert foundation package on sys.path if found. Returns resolved path or None."""
    path = get_foundation_path()
    if path is not None and str(path) not in sys.path:
        sys.path.insert(0, str(path))
    return path


def load_check_foundation_gate() -> Callable[..., Any]:
    """Import and return check_foundation_gate after ensuring path is set."""
    if ensure_foundation_on_path() is None:
        raise ImportError("heroic-core-foundation not found")
    from foundation import check_foundation_gate  # type: ignore

    return check_foundation_gate


def foundation_report_to_dict(report: Any) -> Dict[str, Any]:
    """Serialize FoundationReport (or similar) for JSON/API consumers."""
    if isinstance(report, dict):
        return report
    if hasattr(report, "__dataclass_fields__"):
        return asdict(report)
    return {"passed": bool(getattr(report, "passed", False))}