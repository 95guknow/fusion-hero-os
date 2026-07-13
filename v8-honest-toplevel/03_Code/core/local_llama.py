# local_llama.py — Lokales Llama nach Heroic-Training + QUBO-Inference-Bridge

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

_LLM_ROOT = Path(__file__).parent.parent / "internal_llm"
_CONFIG = _LLM_ROOT / "output" / "heroic_llama_config.json"
_MODEL = _LLM_ROOT / "models" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
_FALLBACK_MODEL = Path(r"C:\Users\Admin\internal_llm\models\Llama-3.2-1B-Instruct-Q4_K_M.gguf")


class LocalLlama:
    def __init__(self) -> None:
        self.config: Dict[str, Any] = {}
        self.active = False
        self._reload()

    def _reload(self) -> None:
        if _CONFIG.exists():
            try:
                self.config = json.loads(_CONFIG.read_text(encoding="utf-8"))
                self.active = True
            except Exception:
                self.config = {}
                self.active = False
        else:
            self.active = _MODEL.exists() or _FALLBACK_MODEL.exists()

    def _model_path(self) -> str:
        cfg_path = self.config.get("model_path")
        if cfg_path and Path(cfg_path).exists():
            return str(cfg_path)
        if _MODEL.exists():
            return str(_MODEL)
        if _FALLBACK_MODEL.exists():
            return str(_FALLBACK_MODEL)
        raise FileNotFoundError("Kein Llama-GGUF-Modell gefunden")

    def status(self) -> Dict[str, Any]:
        self._reload()
        gen = self.config.get("generation", {})
        out: Dict[str, Any] = {
            "active": self.active,
            "backend": os.getenv("FUSION_LLM_BACKEND", "llama-local" if self.active else "grok-intern"),
            "model_path": self._model_path() if self.active else None,
            "config_path": str(_CONFIG) if _CONFIG.exists() else None,
            "algorithm": self.config.get("algorithm", "heroic_qubo_annealing_v1"),
            "generation": gen,
            "gpu_layers": int(os.getenv("FUSION_LLAMA_GPU_LAYERS", "25")),
        }
        try:
            from qubo_llama_bridge import status as qubo_status
            out["qubo"] = qubo_status()
        except Exception as exc:
            out["qubo"] = {"enabled": False, "error": str(exc)}
        return out

    def _raw_generate(self, prompt: str, system: Optional[str] = None,
                      gen_override: Optional[Dict[str, Any]] = None) -> str:
        if str(_LLM_ROOT) not in sys.path:
            sys.path.insert(0, str(_LLM_ROOT))
        from llama_cli_backend import generate as cli_generate  # type: ignore

        cfg = self.config
        gen = dict(gen_override or cfg.get("generation", {}))
        sys_prompt = system or cfg.get(
            "system_prompt",
            "Du bist ALTE_Frau_95g Heroic Core — Fusion Hero OS v8. "
            "QUBO, q/b-Beziehung, Hyperthreading.",
        )
        full = f"<|system|>\n{sys_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n"
        model = self._model_path()
        text = cli_generate(
            model, full, gen,
            max_tokens=int(os.getenv("FUSION_MODEL_MAX_TOKENS", "256")),
        )
        for stop in ("<|user|>", "<|system|>"):
            if stop in text:
                text = text.split(stop, 1)[0]
        return text.strip()

    def generate(self, prompt: str, system: Optional[str] = None,
                 use_qubo: Optional[bool] = None) -> str:
        """Generierung mit optionaler QUBO-Augmentierung (Standard: an wenn FUSION_LLAMA_QUBO=1)."""
        qubo_on = use_qubo
        if qubo_on is None:
            qubo_on = os.getenv("FUSION_LLAMA_QUBO", "1") == "1"
        if qubo_on:
            try:
                from qubo_llama_bridge import generate_with_qubo, is_enabled
                if is_enabled():
                    result = generate_with_qubo(
                        lambda p, s, g: self._raw_generate(p, s, g),
                        prompt,
                        system,
                        self.config.get("generation", {}),
                    )
                    self._last_qubo_meta = result
                    return result.get("response", "")
            except Exception:
                pass
        self._last_qubo_meta = None
        return self._raw_generate(prompt, system)

    def generate_qubo(self, prompt: str, system: Optional[str] = None) -> Dict[str, Any]:
        """Explizite QUBO+Llama-Synthese mit vollem Metadaten-Block."""
        from qubo_llama_bridge import generate_with_qubo

        return generate_with_qubo(
            lambda p, s, g: self._raw_generate(p, s, g),
            prompt,
            system,
            self.config.get("generation", {}),
        )

    @property
    def last_qubo_meta(self) -> Optional[Dict[str, Any]]:
        return getattr(self, "_last_qubo_meta", None)


_llama: LocalLlama | None = None


def get_local_llama() -> LocalLlama:
    global _llama
    if _llama is None:
        _llama = LocalLlama()
    return _llama


def default_model_pool(query: str = "") -> list:
    llama = get_local_llama()
    pool = ["grok-intern", "fusion-hero"]
    q_lower = (query or "").lower()
    try:
        from qubo_llama_bridge import is_qubo_query
        if is_qubo_query(query):
            return ["llama-local", "qb-qubo", "fusion-hero", "grok-intern"]
    except Exception:
        if "qubo" in q_lower or "q/b" in q_lower:
            return ["llama-local", "qb-qubo", "fusion-hero", "grok-intern"]
    try:
        from claude_science import is_science_query
        if is_science_query(query):
            return ["claude-science", "llama-local", "fusion-hero", "grok-intern"]
    except Exception:
        pass
    if llama.active or os.getenv("FUSION_LLM_BACKEND") == "llama-local":
        return ["llama-local", "claude-science", "fusion-hero", "grok-intern"]
    return ["claude-science"] + pool