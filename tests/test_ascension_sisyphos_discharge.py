# -*- coding: utf-8 -*-
"""Discharge der Sisyphos-Schicht: was an ihr scharf beweisbar ist.

Belegt die STRUKTURELLEN Invarianten von PersistentSisyphosCycle,
sisyphos_simulator und MasterSeedContractionEnforcer. Zwei der hier
bewiesenen Saetze sind Redundanz-Befunde: Bedingungen im Code, die keine
Wirkung haben, weil eine andere sie bereits impliziert. Sie werden
festgehalten, nicht stillschweigend wegoptimiert — ein Test, der eine
Redundanz fixiert, verhindert, dass eine spaetere Aenderung sie unbemerkt
zu einer echten Bedingung macht.

Was hier NICHT behauptet wird:
  * dass "Last" und "Zufriedenheit" reale psychische Groessen messen (Modell),
  * dass die Nachhaltigkeitsschwelle 0.85 empirisch begruendet ist
    (Modell — sie ist gesetzt, nicht gemessen),
  * dass der Enforcer eine Kontraktion *erzwingt* (er detektiert ihre
    Verletzung auf Hash-Ebene; der Unterschied steht in der Dissertation 1.3).

Konvention: In proof_registry.yaml zitierte Knoten sind NICHT parametrisiert
— der Registry-Checker prueft die nackte Node-ID gegen die pytest-Collection.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ascension_os.core.coevolutionary_closure import MasterSeedContractionEnforcer
from ascension_os.core.persistent_sisyphos import PersistentSisyphosCycle
from ascension_os.evolution import sisyphos_simulator as sim


def _cycle(tmp_path: Path, **kw) -> PersistentSisyphosCycle:
    """Immer gegen tmp_path — nie gegen data/sisyphos_history.json."""
    return PersistentSisyphosCycle(
        persistence_path=str(tmp_path / "hist.json"), **kw
    )


# ==========================================================================
# PersistentSisyphosCycle — Klemmung, Formel, Historie
# ==========================================================================

def test_sisyphos_load_is_clamped_to_unit_interval(tmp_path: Path) -> None:
    """Jede Eingabe landet in [0, 1] — auch weit ausserhalb liegende."""
    c = _cycle(tmp_path)
    for raw, expected in (
        (-5.0, 0.0), (-0.001, 0.0), (0.0, 0.0),
        (0.5, 0.5), (1.0, 1.0), (1.001, 1.0), (99.0, 1.0),
    ):
        state = c.step(raw)
        assert state["load"] == pytest.approx(expected), f"load {raw} -> {state['load']}"
        assert 0.0 <= state["load"] <= 1.0


def test_sisyphos_satisfaction_follows_the_declared_formula(tmp_path: Path) -> None:
    """satisfaction = 1 - 0.7 * load, exakt, fuer geklemmte Last."""
    c = _cycle(tmp_path)
    for raw in (0.0, 0.25, 0.5, 0.85, 1.0, -3.0, 7.0):
        state = c.step(raw)
        assert state["satisfaction"] == pytest.approx(1.0 - 0.7 * state["load"])


def test_sisyphos_satisfaction_floor_is_unreachable(tmp_path: Path) -> None:
    """Der max(0, ...)-Schutz greift nie: aus load <= 1 folgt satisfaction >= 0.3.

    Redundanz-Befund. Die Klemmung der Last macht die Nullklemmung der
    Zufriedenheit wirkungslos. Festgehalten, damit eine spaetere Aenderung
    des Faktors 0.7 (auf > 1.0) nicht unbemerkt eine echte Klemmung
    einfuehrt, die vorher nie aktiv war.
    """
    c = _cycle(tmp_path)
    for raw in (-10.0, 0.0, 0.5, 1.0, 50.0):
        state = c.step(raw)
        assert state["satisfaction"] >= 0.3 - 1e-12
        assert state["satisfaction"] > 0.0


def test_sisyphos_sustainability_reduces_to_the_load_bound(tmp_path: Path) -> None:
    """is_sustainable <=> load < 0.85. Die Zufriedenheitsbedingung ist redundant.

    is_sustainable prueft (satisfaction > 0.4) UND (load < 0.85).
    Aus satisfaction = 1 - 0.7*load folgt: satisfaction > 0.4 <=> load < 6/7
    (~0.857). Da 0.85 < 6/7, impliziert die Lastbedingung die
    Zufriedenheitsbedingung — sie ist wirkungslos.

    Zweiter Redundanz-Befund, aus demselben Grund festgehalten wie der erste.
    """
    c = _cycle(tmp_path)
    for raw in (0.0, 0.4, 0.8, 0.8499, 0.85, 0.8501, 0.857, 0.9, 1.0):
        state = c.step(raw)
        assert state["is_sustainable"] == (state["load"] < 0.85), (
            f"Aequivalenz verletzt bei load={state['load']}"
        )
    # Das kritische Fenster ist [0.85, 6/7) ~ [0.85, 0.8571): dort ist die
    # Zufriedenheit noch > 0.4, die Last aber schon zu hoch. Genau hier zeigt
    # sich, dass die Lastbedingung bindet und die Zufriedenheitsbedingung nicht.
    state = c.step(0.855)
    assert state["satisfaction"] > 0.4
    assert state["is_sustainable"] is False
    # Oberhalb von 6/7 faellt auch die Zufriedenheit unter die Schwelle —
    # beide Bedingungen sind dann verletzt, die Aequivalenz gilt weiterhin.
    state = c.step(0.86)
    assert state["satisfaction"] < 0.4
    assert state["is_sustainable"] is False


def test_sisyphos_history_is_bounded_and_drops_oldest(tmp_path: Path) -> None:
    """max_history begrenzt die Historie; der aelteste Eintrag faellt zuerst."""
    c = _cycle(tmp_path, max_history=5)
    for i in range(12):
        c.step(i / 20.0, notes=f"n{i}")

    assert len(c.history) == 5
    hist = c.get_history()
    assert [h["notes"] for h in hist] == [f"n{i}" for i in range(7, 12)]
    # Zykluszaehler zaehlt ALLE Schritte, nicht nur die behaltenen.
    assert c.cycle_count == 12
    assert c.get_current_state()["total_cycles_recorded"] == 5


def test_sisyphos_cycle_count_is_strictly_monotone(tmp_path: Path) -> None:
    """Jeder Schritt erhoeht den Zaehler um genau eins."""
    c = _cycle(tmp_path)
    counts = [c.step(0.5)["cycle_count"] for _ in range(6)]
    assert counts == [1, 2, 3, 4, 5, 6]


def test_sisyphos_survives_a_save_load_roundtrip(tmp_path: Path) -> None:
    """Zustand und Historie ueberleben einen Neustart aus der Datei."""
    path = tmp_path / "hist.json"
    c1 = PersistentSisyphosCycle(persistence_path=str(path))
    for raw in (0.2, 0.6, 0.9):
        c1.step(raw, notes=f"L{raw}")
    before = c1.get_current_state()

    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["cycle_count"] == 3

    c2 = PersistentSisyphosCycle(persistence_path=str(path))
    after = c2.get_current_state()
    assert after["cycle_count"] == before["cycle_count"]
    assert after["load"] == pytest.approx(before["load"])
    assert after["satisfaction"] == pytest.approx(before["satisfaction"])
    assert [h["notes"] for h in c2.get_history()] == ["L0.2", "L0.6", "L0.9"]


# ==========================================================================
# sisyphos_simulator — Schranken, Determinismus, Formelkonsistenz
# ==========================================================================

def test_simulator_rejects_out_of_range_arguments() -> None:
    """MAX_GENERATIONS und n_runs >= 1 werden erzwungen."""
    with pytest.raises(ValueError):
        sim.simulate(generations=sim.MAX_GENERATIONS + 1, n_runs=1)
    with pytest.raises(ValueError):
        sim.simulate(generations=10, n_runs=0)


def test_simulator_is_deterministic_for_a_fixed_seed() -> None:
    """Gleicher base_seed => bitgleiche Ergebnisse. Ohne das ist nichts reproduzierbar."""
    a = sim.simulate(generations=50, n_runs=4, base_seed=1234)
    b = sim.simulate(generations=50, n_runs=4, base_seed=1234)
    assert a == b
    c = sim.simulate(generations=50, n_runs=4, base_seed=9999)
    assert c != a


def test_simulator_satisfaction_matches_the_persistent_cycle(tmp_path: Path) -> None:
    """Simulation und echter Zyklus benutzen dieselbe Formel.

    Waeren die Formeln verschieden, waere jede Simulationsaussage ueber den
    realen Zyklus wertlos. Der Modul-Docstring behauptet die Gleichheit
    ("identisch zu SisyphosCycle.step") — hier wird sie geprueft.
    """
    real = _cycle(tmp_path)
    for load in (0.0, 0.3, 0.5, 0.77, 1.0):
        run = sim._run_one(seed=0, generations=1, load_fn=lambda s, p, r: load,
                           initial_load=load)
        assert run.satisfactions[0] == pytest.approx(real.step(load)["satisfaction"])


def test_simulator_loads_stay_in_unit_interval() -> None:
    """Der Default-Random-Walk verlaesst [0, 1] nicht."""
    res = sim.simulate(generations=300, n_runs=4, base_seed=7)
    assert 0.0 <= res["avg_final_satisfaction"] <= 1.0
    assert 0.0 <= res["sustainable_fraction"] <= 1.0


def test_simulator_reversal_count_ignores_micro_noise() -> None:
    """Richtungswechsel unterhalb min_delta zaehlen nicht als Umkehr."""
    run = sim.SimRun(seed=0, loads=[0.5, 0.505, 0.5, 0.505], satisfactions=[])
    assert run.reversal_count(min_delta=0.02) == 0
    run2 = sim.SimRun(seed=0, loads=[0.1, 0.5, 0.1, 0.5], satisfactions=[])
    assert run2.reversal_count(min_delta=0.02) == 2


# ==========================================================================
# MasterSeedContractionEnforcer — Detektion, nicht Erzwingung
# ==========================================================================

def test_enforcer_detects_hash_mismatch_and_counts_it() -> None:
    """Abweichung => False, Zaehler steigt, letzte Verletzung wird festgehalten."""
    e = MasterSeedContractionEnforcer()
    assert e.enforce("abc", "abc") is True
    assert e.violation_count == 0

    assert e.enforce("abc", "def", context="test") is False
    assert e.violation_count == 1
    assert e.last_violation is not None
    assert e.last_violation["expected"] == "def"
    assert e.last_violation["actual"] == "abc"
    assert e.last_violation["context"] == "test"

    e.enforce("x", "y")
    assert e.violation_count == 2


def test_enforcer_normalises_case_and_whitespace() -> None:
    """Hashes gelten als gleich trotz Rand-Whitespace und Gross-/Kleinschreibung."""
    e = MasterSeedContractionEnforcer()
    assert e.enforce("  ABC  ", "abc") is True
    assert e.enforce("AbC", "aBc") is True
    assert e.violation_count == 0
