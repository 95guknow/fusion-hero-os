# -*- coding: utf-8 -*-
"""Regressionstests: SA-Optimizer in 03_Code/internal_llm (Claim SA-SINGLE-EVAL).

Verankert den Metropolis-Fix vom 2026-07-05: Delta wird gegen den gemerkten
current_score gerechnet, score_fn wird pro Schritt EXAKT einmal aufgerufen
(vorher: Doppel-Aufruf + Vergleich gegen best_score — teuer und inkonsistent
bei LLM-Bewertungen).
"""
import importlib.util
import sys
from pathlib import Path

_OPT_PATH = (
    Path(__file__).resolve().parent.parent / "03_Code" / "internal_llm" / "heroic_llama_optimizer.py"
)

spec = importlib.util.spec_from_file_location("heroic_llama_optimizer_test", _OPT_PATH)
opt = importlib.util.module_from_spec(spec)
# Registrierung VOR exec_module: @dataclass loest sys.modules[cls.__module__] auf.
sys.modules[spec.name] = opt
spec.loader.exec_module(opt)


def test_sa_calls_score_fn_exactly_once_per_step():
    calls = [0]

    def score(p):
        calls[0] += 1
        return -(p["temperature"] - 0.4) ** 2

    steps = 40
    opt.simulated_annealing_params(score, steps=steps)
    assert calls[0] == steps + 1  # 1x Initialzustand + 1x pro Schritt


def test_sa_best_score_is_max_of_all_evaluations():
    """best_score darf nie schlechter sein als der Startwert und muss dem
    Maximum aller tatsaechlich bewerteten Kandidaten entsprechen."""
    seen = []

    def score(p):
        s = -(p["temperature"] - 0.4) ** 2 - (p["top_p"] - 0.85) ** 2
        seen.append(s)
        return s

    result = opt.simulated_annealing_params(score, steps=60)
    assert abs(result["score"] - max(seen)) < 1e-12
    assert result["score"] >= seen[0]


def test_sa_result_contains_all_three_params_within_bounds():
    result = opt.simulated_annealing_params(lambda p: 0.0, steps=10)
    assert 0.1 <= result["temperature"] <= 1.2
    assert 0.5 <= result["top_p"] <= 1.0
    assert 1.0 <= result["repeat_penalty"] <= 1.5
