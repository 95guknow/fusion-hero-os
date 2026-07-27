"""MCP / context fill governor — keep utilization in [40%, 70%] when possible.

Uses Sinnkongruenz autocompression when over target, and optional archive
refill when under floor. Designed for MCP tool-context and chat windows.

Env:
  FUSION_MCP_CONTEXT_WINDOW   default 128000
  FUSION_MCP_FILL_MIN         default 0.40
  FUSION_MCP_FILL_MAX         default 0.70
  FUSION_MCP_FILL_TARGET      default 0.55 (hysteresis midpoint)
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from collections.abc import Sequence

from fusion_hero_os.core.sinnkongruenz_compressor import (
    MessageUnit,
    compress_to_budget,
)

__all__ = [
    "FillBand",
    "FillState",
    "McpFillGovernor",
    "get_mcp_fill_governor",
    "govern_messages",
]

_STATE = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os"))) / "mcp_fill"


@dataclass
class FillBand:
    window_tokens: int = 128_000
    fill_min: float = 0.40
    fill_max: float = 0.70
    fill_target: float = 0.55

    @classmethod
    def from_env(cls) -> FillBand:
        return cls(
            window_tokens=int(os.getenv("FUSION_MCP_CONTEXT_WINDOW", "128000")),
            fill_min=float(os.getenv("FUSION_MCP_FILL_MIN", "0.40")),
            fill_max=float(os.getenv("FUSION_MCP_FILL_MAX", "0.70")),
            fill_target=float(os.getenv("FUSION_MCP_FILL_TARGET", "0.55")),
        )

    @property
    def min_tokens(self) -> int:
        return int(self.window_tokens * self.fill_min)

    @property
    def max_tokens(self) -> int:
        return int(self.window_tokens * self.fill_max)

    @property
    def target_tokens(self) -> int:
        return int(self.window_tokens * self.fill_target)


@dataclass
class FillState:
    tokens: int
    fill_pct: float
    band: str  # below | in_band | above
    action: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tokens": self.tokens,
            "fill_pct": round(self.fill_pct, 4),
            "band": self.band,
            "action": self.action,
            "detail": self.detail,
        }


class McpFillGovernor:
    """Keep MCP/context fill between 40% and 70% with Sinnkongruenz compression."""

    def __init__(self, band: FillBand | None = None) -> None:
        self.band = band or FillBand.from_env()
        self._archive: list[MessageUnit] = []
        self._last: FillState | None = None
        _STATE.mkdir(parents=True, exist_ok=True)

    def measure(self, units: Sequence[MessageUnit]) -> FillState:
        tok = sum(u.tokens for u in units)
        pct = tok / max(1, self.band.window_tokens)
        if pct < self.band.fill_min:
            band = "below"
        elif pct > self.band.fill_max:
            band = "above"
        else:
            band = "in_band"
        return FillState(tokens=tok, fill_pct=pct, band=band, action="measure")

    def govern(
        self,
        units: Sequence[MessageUnit],
        *,
        intent: str = "",
        archive: Sequence[MessageUnit] | None = None,
    ) -> dict[str, Any]:
        """Return governed unit list + fill state.

        above max → compress to target (sharp Sinnkongruenz)
        below min → refill from archive (highest congruence first) toward target
        in band → noop
        """
        units_list = list(units)
        if archive is not None:
            self._archive = list(archive)

        st = self.measure(units_list)
        result_units = units_list
        action = "noop"
        compress_meta: dict[str, Any] = {}

        if st.band == "above":
            # lossless Sinnkongruenz compress toward target (no info loss)
            budget = self.band.target_tokens
            compress_meta = compress_to_budget(
                units_list,
                max_tokens=budget,
                intent=intent,
                summarize_dropped=True,
                lossless=True,
            )
            result_units = compress_meta["units"]
            # offloaded full bodies stay in reversible archive + optional local archive list
            for off in compress_meta.get("offload_index") or []:
                sha = off.get("sha")
                if sha:
                    try:
                        from fusion_hero_os.core.sinnkongruenz_compressor import (
                            rehydrate_from_archive,
                        )

                        full = rehydrate_from_archive(sha)
                        if full is not None:
                            self._archive.append(full)
                    except Exception:
                        pass
            action = "compress_sinnkongruenz_lossless"
            st = self.measure(result_units)
            st.action = action
            st.detail = {
                "tokens_before": compress_meta.get("tokens_before"),
                "tokens_after": compress_meta.get("tokens_after"),
                "dropped": 0,
                "offloaded": compress_meta.get("offloaded"),
                "information_loss": False,
                "lossless": True,
                "reversible": True,
                "budget": budget,
                "phases": compress_meta.get("phases"),
            }
        elif st.band == "below" and self._archive:
            # refill high-congruence archive until target (or archive empty)
            need = self.band.target_tokens - st.tokens
            from fusion_hero_os.core.sinnkongruenz_compressor import score_unit

            ranked = sorted(
                enumerate(self._archive),
                key=lambda iv: score_unit(
                    iv[1], intent=intent, index=iv[0], n=len(self._archive)
                ),
                reverse=True,
            )
            added = 0
            added_tok = 0
            for _, u in ranked:
                if added_tok >= need:
                    break
                # avoid duplicates by content prefix
                if any((u.content or "")[:80] == (x.content or "")[:80] for x in result_units):
                    continue
                result_units.append(u)
                added += 1
                added_tok += u.tokens
            action = "refill_archive" if added else "below_no_archive_fit"
            st = self.measure(result_units)
            st.action = action
            st.detail = {"added_units": added, "added_tokens": added_tok, "need": need}
        else:
            st.action = "hold_in_band"
            action = st.action

        self._last = st
        self._persist(st, intent)
        return {
            "ok": True,
            "units": result_units,
            "fill": st.to_dict(),
            "band_config": {
                "window_tokens": self.band.window_tokens,
                "fill_min": self.band.fill_min,
                "fill_max": self.band.fill_max,
                "fill_target": self.band.fill_target,
                "min_tokens": self.band.min_tokens,
                "max_tokens": self.band.max_tokens,
                "target_tokens": self.band.target_tokens,
            },
            "compress": {
                k: compress_meta[k]
                for k in ("tokens_before", "tokens_after", "dropped", "action")
                if k in compress_meta
            },
            "intent": intent[:200],
            "policy": "maintain_fill_40_70_sinnkongruenz",
        }

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "last": self._last.to_dict() if self._last else None,
            "band": {
                "window_tokens": self.band.window_tokens,
                "fill_min": self.band.fill_min,
                "fill_max": self.band.fill_max,
                "fill_target": self.band.fill_target,
            },
            "archive_units": len(self._archive),
        }

    def _persist(self, st: FillState, intent: str) -> None:
        path = _STATE / "last_fill.json"
        path.write_text(
            json.dumps(
                {"ts": time.time(), "intent": intent[:200], "fill": st.to_dict()},
                indent=2,
            ),
            encoding="utf-8",
        )


_GOV: McpFillGovernor | None = None


def get_mcp_fill_governor() -> McpFillGovernor:
    global _GOV
    if _GOV is None:
        _GOV = McpFillGovernor()
    return _GOV


def govern_messages(
    messages: Sequence[dict[str, Any]],
    *,
    intent: str = "",
) -> dict[str, Any]:
    """Convenience: list[{role,content}] → governed list + fill stats."""
    units = [
        MessageUnit(
            role=str(m.get("role") or "user"),
            content=str(m.get("content") or ""),
            meta=dict(m.get("meta") or {}),
        )
        for m in messages
    ]
    out = get_mcp_fill_governor().govern(units, intent=intent)
    out["messages"] = [
        {"role": u.role, "content": u.content, "meta": u.meta} for u in out["units"]
    ]
    return out
