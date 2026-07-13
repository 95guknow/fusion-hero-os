#!/usr/bin/env python3
"""
Private Hacking Suite - Launcher
Einfacher Einstiegspunkt für die private Tools.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent

def list_modules():
    print("=== Private Hacking Suite ===")
    print("Verfügbare Bereiche:\n")
    areas = {
        "layers": "All 8 Coevo Layers (00_middle to 07_highest)",
        "qubo": "QUBO Miner / Solver / Optimizer (L2)",
        "gpu": "GPU Acceleration & Virtual HT (L3)",
        "llm": "Local LLM Backends & Training (L4)",
        "fusion": "Fusion Experiments & Bottleneck Tools (L5)",
        "audio-bridge": "PC to Phone Audio Bridge (play PC sound on phone)",
        "tools": "Benchmarks, Stress Tests, Heavy Jobs",
        "core": "Basis Utilities (qb_qubo, qg)"
    }
    for folder, desc in areas.items():
        path = ROOT / folder
        count = len(list(path.glob("*.py"))) if path.exists() else 0
        print(f"  {folder}/   ({count} py files) - {desc}")
    print("\nBeispiele:")
    print("  python qubo/main.py")
    print("  python fusion/fusion_status.py")
    print("  python gpu/fusion_gpu_check.py")
    print("  python llm/llama_cli_backend.py")
    print("  python llm/train.py --export-only")
    print("  python tools/stress_test_big_benchmark.py")
    print("  python -c \"from core.qb_qubo import springloop_energy, energy; print('Springloop ready')\"")
    print("  python process_layers.py   # alle 8 COEVOLUTIONÄR (ghosthunt + springloop hooked)")
    print("  python layers/00_middle/middle_out.py  # sprich wir exprimieren middleout")
    print("  python ghosthunting/run_ghosthunt.py          # go ghosthunting")
    print("  python ghosthunting/run_ghosthunt.py --springloop  # with springloop energy")
    print("  python tests/run_all.py  # run all tests")
    print("  cd audio-bridge ; start.bat  # PC audio to phone (edit DEVICE in bat)")

if __name__ == "__main__":
    list_modules()
    print("\nStarte direkt ein Modul oder nutze die Ordner.")
