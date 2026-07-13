#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internes Llama-Training / Optimierung mit eigenem Heroic-Algorithmus.
Modi:
  - heroic (default): QUBO + Simulated Annealing via heroic_llama_optimizer
  - export: nur Daten exportieren
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from heroic_llama_optimizer import HeroicLlamaOptimizer, OptimizerConfig


def load_config(path: str) -> Dict[str, Any]:
    if not Path(path).exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Heroic Llama Optimizer")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).parent

    if args.download:
        from download_model import main as dl
        return dl()

    if args.export_only:
        from export_data import main as exp
        exp()
        return 0

    cfg_data = load_config(str(root / args.config))
    model_path = cfg_data.get("model_path")
    if not model_path:
        model_path = str(root / "models" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf")
    if not Path(model_path).exists():
        print("[!] Modell nicht gefunden. Starte Download...")
        from download_model import main as dl
        if dl() != 0:
            return 1
        model_path = str(root / "models" / "Llama-3.2-1B-Instruct-Q4_K_M.gguf")

    cfg_data["model_path"] = model_path
    opt_cfg = OptimizerConfig.from_dict(cfg_data)
    result = HeroicLlamaOptimizer(opt_cfg).optimize()
    print(json.dumps(result.get("metrics", {}), indent=2))
    os.environ["FUSION_LLM_BACKEND"] = "llama-local"
    print("[*] FUSION_LLM_BACKEND=llama-local — System nutzt jetzt lokales Llama")
    return 0


if __name__ == "__main__":
    sys.exit(main())