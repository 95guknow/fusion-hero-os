#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests für creative_problem_solving (offline, ohne LLM/Netz)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
os.environ["FUSION_CREATIVE_OFFLINE"] = "1"  # kein Backend-Probe im Test

import creative_problem_solving as cps  # noqa: E402

PROBLEM = (
    "Der lokale Llama-Agent liefert bei mehrstufigen Aufgaben inkonsistente "
    "Zwischenergebnisse, weil Kontext zwischen Schritten verloren geht."
)


def test_diversify_covers_all_strategies():
    frames = cps.diversify(PROBLEM)
    assert len(frames) == len(cps.STRATEGIES)
    keys = {f["strategy"] for f in frames}
    assert keys == {s.key for s in cps.STRATEGIES}
    for f in frames:
        assert PROBLEM in f["prompt"], f"Problem fehlt im Prompt von {f['strategy']}"
    print("test_diversify_covers_all_strategies: PASS")


def test_diversify_empty_and_subset():
    assert cps.diversify("") == []
    frames = cps.diversify(PROBLEM, ["inversion", "analogy", "gibt_es_nicht"])
    assert [f["strategy"] for f in frames] == ["inversion", "analogy"]
    print("test_diversify_empty_and_subset: PASS")


def test_generate_with_injected_backend():
    def backend(prompt, role):
        assert role == "agent"
        return f"Antwort auf: {prompt[:40]}"

    cands = cps.generate(PROBLEM, backend=backend, strategy_keys=["inversion", "decomposition"])
    assert len(cands) == 2
    assert all(c["backend"] == "injected" for c in cands)
    assert all(c["response"].startswith("Antwort auf:") for c in cands)
    print("test_generate_with_injected_backend: PASS")


def test_lexical_novelty_bounds():
    same = "kontext anker pro schritt speichern"
    assert cps.lexical_novelty(same, [same]) == 0.0
    disjoint = cps.lexical_novelty("alpha beta gamma", ["delta epsilon zeta"])
    assert disjoint == 1.0
    assert cps.lexical_novelty("irgendwas", []) == 1.0
    print("test_lexical_novelty_bounds: PASS")


def test_problem_coverage():
    full = cps.problem_coverage(PROBLEM, PROBLEM)
    assert full == 1.0
    none = cps.problem_coverage("völlig anderes thema xyz", PROBLEM)
    assert none < 0.2
    print("test_problem_coverage: PASS")


def test_anneal_select_deterministic():
    def backend(prompt, role):
        return f"Loesung {abs(hash(prompt)) % 997} fuer Kontextverlust im Agent"

    cands = cps.score_candidates(cps.generate(PROBLEM, backend=backend), PROBLEM)
    sel_a = cps.anneal_select(cands, k=3, seed=42)
    sel_b = cps.anneal_select(cands, k=3, seed=42)
    assert [c["strategy"] for c in sel_a] == [c["strategy"] for c in sel_b]
    assert len(sel_a) == 3
    # sortiert nach Score absteigend
    scores = [c["score"] for c in sel_a]
    assert scores == sorted(scores, reverse=True)
    print("test_anneal_select_deterministic: PASS")


def test_anneal_select_small_pool():
    cands = cps.score_candidates(
        cps.generate(PROBLEM, backend=lambda p, r: "x", strategy_keys=["inversion"]), PROBLEM
    )
    sel = cps.anneal_select(cands, k=5)
    assert len(sel) == 1
    assert cps.anneal_select([], k=3) == []
    print("test_anneal_select_small_pool: PASS")


def test_solve_creative_offline_end_to_end():
    res = cps.solve_creative(PROBLEM, with_critique=True, persist=False)
    assert res["ok"] is True
    assert res["offline"] is True  # kein Backend erreichbar -> Stub
    assert res["critique"] is None  # Kritik wird offline übersprungen
    assert len(res["portfolio"]) == cps._PORTFOLIO_SIZE
    assert "lexikalisch" in res["honesty"].lower() or "heuristik" in res["honesty"].lower()
    for c in res["portfolio"]:
        assert "[offline-stub]" in c["response"]
    print("test_solve_creative_offline_end_to_end: PASS")


def test_solve_creative_empty_problem():
    res = cps.solve_creative("", persist=False)
    assert res["ok"] is False
    print("test_solve_creative_empty_problem: PASS")


def test_critique_with_injected_backend():
    def backend(prompt, role):
        assert role == "anti_agent"
        assert "[anti-agent]" in prompt
        return "Schwächste Annahme: ..."

    out = cps.critique_top(PROBLEM, {"title": "Inversion", "response": "Ansatz X"}, backend=backend)
    assert out["ok"] is True
    assert "Annahme" in out["critique"]
    print("test_critique_with_injected_backend: PASS")


def test_status():
    st = cps.status()
    assert st["module"] == "creative_problem_solving"
    assert len(st["strategies"]) == len(cps.STRATEGIES)
    print("test_status: PASS")


if __name__ == "__main__":
    test_diversify_covers_all_strategies()
    test_diversify_empty_and_subset()
    test_generate_with_injected_backend()
    test_lexical_novelty_bounds()
    test_problem_coverage()
    test_anneal_select_deterministic()
    test_anneal_select_small_pool()
    test_solve_creative_offline_end_to_end()
    test_solve_creative_empty_problem()
    test_critique_with_injected_backend()
    test_status()
    print("ALLE TESTS PASS")
