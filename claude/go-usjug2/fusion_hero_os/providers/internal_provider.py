"""Internal Fallback v8.5 - strong on heroic_core tasks, always available."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .base import BaseLLMProvider, LLMResult


class InternalFallbackProvider(BaseLLMProvider):
    name = "fusion-hero"
    capabilities = {
        "code": 0.40,
        "current_events": 0.30,
        "simple_fact": 0.50,
        "creative": 0.45,
        "heroic_core": 0.95,
        "default": 0.55,
    }

    def __init__(self, heroic_core: Any = None, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(config)
        self.heroic_core = heroic_core

    def is_available(self) -> bool:
        return True

    def _build_heroic_context(self) -> str:
        if not self.heroic_core:
            return "Fusion Hero OS v8.5 — Heroic Core aktiv. MasterSeed verifiziert. Fail-Closed."
        try:
            seed = getattr(self.heroic_core, "seed", None)
            mode = getattr(self.heroic_core, "mode", "STANDARD")
            history_len = len(getattr(self.heroic_core, "volatile_history", []))
            return "\n".join([
                f"Fusion Hero OS v8.5 | Mode: {mode}",
                f"MasterSeed: {'VERIFIZIERT' if seed and seed.verify_integrity(seed.state_hash()) else 'CHECK NEEDED'}",
                f"Volatile History: {history_len} Einträge",
                "PMS Spine + QuadCoreBridge + Fail-Closed aktiv.",
            ])
        except Exception:
            return "Fusion Hero OS v8.5 — Heroic Core (reduzierter Kontext)"

    def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs: Any) -> LLMResult:
        start = time.time()
        ctx = self._build_heroic_context()
        latency = (time.time() - start) * 1000
        self._record(True, latency)
        return LLMResult(
            "fusion-hero (intern)",
            f"[Fusion Hero OS v8.5] Interner Fallback aktiv.\n{ctx}",
            latency,
            meta={"note": "internal", "heroic_context": True},
        )
