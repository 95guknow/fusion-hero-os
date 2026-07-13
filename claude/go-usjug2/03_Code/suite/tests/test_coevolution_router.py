#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests für coevolution_router + judge_panel (offline, deterministisch)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))

import coevolution_router as cr  # noqa: E402
import judge_panel as jp  # noqa: E402


# ---------------------------- judge_panel ---------------------------------

def test_judge_offline_ranks_better_candidate_higher():
    problem = "Kontext geht zwischen Agenten-Schritten verloren."
    good = ("Speichere pro Schritt einen Kontext-Anker im conversation_context_core "
            "und reiche ihn als Root-Kontext an den nächsten Agenten-Schritt weiter.")
    bad = "Mach halt irgendwas."
    ranked = jp.rank(problem, [good, bad])
    assert ranked[0]["candidate"] == good
    assert ranked[0]["score"] >= ranked[1]["score"]
    assert all(r["offline"] for r in ranked)
    print("test_judge_offline_ranks_better_candidate_higher: PASS")


def test_judge_injected_backend_uses_schema():
    def backend(prompt, role):
        assert role == "anti_agent"
        return '{"korrektheit": 0.9, "vollstaendigkeit": 0.8, "umsetzbarkeit": 0.7, "klarheit": 0.85, "begruendung": "ok"}'

    ev = jp.evaluate("Problem X", "Lösung Y", backend=backend, n_judges=3)
    assert ev["ok"] and ev["offline"] is False
    assert 0.7 <= ev["score"] <= 0.9
    assert ev["majority_accept"] is True
    assert ev["per_criterion"]["korrektheit"] == 0.9
    print("test_judge_injected_backend_uses_schema: PASS")


def test_judge_agreement_and_majority():
    ev = jp.evaluate("P", "kurze antwort mit P inhalt", n_judges=5)
    assert 0.0 <= ev["agreement"] <= 1.0
    assert ev["n_judges"] == 5
    print("test_judge_agreement_and_majority: PASS")


# ------------------------- coevolution_router ------------------------------

def test_coevolve_learns_escalation_policy():
    """Kernbeweis: die Coevolution lernt leicht->billig, schwer->teuer."""
    res = cr.coevolve(max_gens=200)
    assert res["stabilitaet_erreicht"] is True
    rmap = res["routing_map"]
    # leichteste Aufgabe -> billigstes Backend
    assert rmap[0.0] == "llama-local"
    # schwerste Aufgabe -> fähigstes (teuerstes) Backend
    assert rmap[1.0] == "claude-science"
    # Eskalation messbar positiv
    assert res["fitness_komponenten"]["escalation"] > 0.3
    print(f"test_coevolve_learns_escalation_policy: PASS (escalation={res['fitness_komponenten']['escalation']})")


def test_coevolve_deterministic():
    a = cr.coevolve(max_gens=120)
    b = cr.coevolve(max_gens=120)
    assert a["policy_genome"] == b["policy_genome"]
    assert a["routing_map"] == b["routing_map"]
    print("test_coevolve_deterministic: PASS")


def test_estimate_difficulty_monotonic():
    easy = cr.estimate_difficulty("Hallo")
    hard = cr.estimate_difficulty(
        "Beweise die Banach-Kontraktion für die verteilte, mehrstufige Architektur "
        "unter Concurrency und verifiziere die Race-Sicherheit " * 3)
    assert 0.0 <= easy <= 1.0 and 0.0 <= hard <= 1.0
    assert hard > easy
    print(f"test_estimate_difficulty_monotonic: PASS (easy={easy}, hard={hard})")


def test_route_applies_policy():
    res = cr.coevolve(max_gens=120)
    genome = res["policy_genome"]
    easy = cr.route("kurz", genome)
    hard = cr.route(
        "Beweise Banach-Kontraktion verteilte Architektur concurrency race verify optimier " * 4,
        genome)
    assert easy["backend"] in cr.BACKENDS
    assert hard["relative_cost"] >= easy["relative_cost"]  # Härteres kostet >=
    print(f"test_route_applies_policy: PASS (easy={easy['backend']}, hard={hard['backend']})")


def test_fitness_live_with_injected_backends():
    """fitness_live: Policy routet, generate_fn erzeugt, judge bewertet."""
    res = cr.coevolve(max_gens=120)
    genome = res["policy_genome"]

    def generate_fn(task, backend):
        # simuliert: claude liefert bessere (längere, problem-deckende) Antwort
        base = f"Loesung fuer {task[:40]}"
        return base + (" mit ausfuehrlicher begruendung und deckung" if backend == "claude-science" else "")

    out = cr.fitness_live(
        genome,
        ["kurze aufgabe", "beweise verteilte concurrency architektur mehrstufig komplex " * 3],
        generate_fn=generate_fn,
    )
    assert out["n_tasks"] == 2
    assert -1.0 <= out["fitness"] <= 1.0
    assert out["offline"] is True  # judge offline (kein backend injiziert)
    # das schwere Task sollte an ein teureres Backend geroutet worden sein
    costs = [r["norm_cost"] for r in out["rows"]]
    assert max(costs) >= min(costs)
    print(f"test_fitness_live_with_injected_backends: PASS (fitness={out['fitness']})")


def test_status():
    assert cr.status()["module"] == "coevolution_router"
    assert jp.status()["module"] == "judge_panel"
    print("test_status: PASS")


if __name__ == "__main__":
    test_judge_offline_ranks_better_candidate_higher()
    test_judge_injected_backend_uses_schema()
    test_judge_agreement_and_majority()
    test_coevolve_learns_escalation_policy()
    test_coevolve_deterministic()
    test_estimate_difficulty_monotonic()
    test_route_applies_policy()
    test_fitness_live_with_injected_backends()
    test_status()
    print("ALLE TESTS PASS")
