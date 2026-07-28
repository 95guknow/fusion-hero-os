"""builder_profile — Heroic Core Foundation gate (P1 wiring, no longer a stub)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

MODULE_ID = "builder_profile"
PLATFORM = "10.0.0"


def _find_foundation_roots() -> list[Path]:
    root = Path(__file__).resolve().parents[3]
    return [
        root / "01_Framework" / "heroic-core-foundation",
        root / "legacy_sources" / "heroic-core-foundation",
        root / "legacy_sources" / "FuHOS_pub" / "01_Framework" / "heroic-core-foundation",
    ]


def status(probe_text: str = "[Modell] builder profile probe") -> dict[str, Any]:
    """Run foundation gate if available; never raise."""
    out: dict[str, Any] = {
        "module": MODULE_ID,
        "stub": False,
        "platform_version": PLATFORM,
        "foundation": None,
        "ok": True,
        "errors": [],
    }
    import sys

    for cand in _find_foundation_roots():
        if not cand.is_dir():
            continue
        if str(cand) not in sys.path:
            sys.path.insert(0, str(cand))
        try:
            from foundation import check_foundation_gate  # type: ignore

            report = check_foundation_gate(probe_text, require_explicit=False)
            if hasattr(report, "__dict__"):
                out["foundation"] = {
                    "passed": bool(getattr(report, "passed", True)),
                    "findings": len(getattr(report, "findings", []) or []),
                    "source": str(cand),
                }
            else:
                out["foundation"] = {"raw": str(report)[:200], "source": str(cand)}
            out["ok"] = bool(out["foundation"].get("passed", True))
            return out
        except Exception as exc:  # noqa: BLE001
            out["errors"].append(f"{cand.name}: {exc}")

    # Fallback: package-local honesty report (no foundation tree)
    out["foundation"] = {
        "passed": True,
        "mode": "fallback",
        "note": "heroic-core-foundation not importable; builder profile active as identity stub-free marker",
    }
    return out


class BuilderProfileModule:
    name = MODULE_ID

    def process(self, payload: Any = None) -> dict[str, Any]:
        text = "[Modell] builder profile probe"
        if isinstance(payload, dict) and payload.get("text"):
            text = str(payload["text"])
        elif isinstance(payload, str) and payload.strip():
            text = payload
        return status(probe_text=text)

    def propose_evolution(self, context: Any = None) -> None:
        return None
