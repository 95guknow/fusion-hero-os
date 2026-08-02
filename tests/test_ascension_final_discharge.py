# -*- coding: utf-8 -*-
"""Abschluss der Entladung: QUBO-Matrix, Evolutions-Fitness, Consent-Vollstaendigkeit.

Die letzten drei Module des ascension_os-Tracks. Der dritte Test ist der
sicherheitsrelevante: Er belegt per AST, dass JEDE personenbezogene Methode
auf AscensionCore tatsaechlich durch _require_consent laeuft — er bestaetigt
also keine Rechnung, sondern schliesst eine Luecke aus. Ein einzelner
vergessener Aufruf wuerde das fail-closed-Versprechen aus 2.4 aushebeln, ohne
dass ein Verhaltenstest es zwingend bemerkt.

Was hier NICHT behauptet wird:
  * dass die Fitness-Gewichte (+20 sustainable, +15 ascension_mode, ...)
    begruendet sind — sie sind gesetzt, nicht gemessen (MODELL),
  * dass die Devil/Christus-Trajektorie reale Dynamik abbildet (MODELL, so im
    Modul deklariert),
  * irgendetwas ueber die Loesungsguete des Solvers — der ist hier gar nicht
    beteiligt.

Konvention: In proof_registry.yaml zitierte Knoten sind NICHT parametrisiert.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

import numpy as np
import pytest

import ascension_os.core.qubo_ascension_optimizer as qopt
from ascension_os.core.ascension_core import AscensionCore
from ascension_os.core.qubo_ascension_optimizer import build_devil_christus_qubo
from ascension_os.evolution.generational_engine import GenerationalEvolutionEngine

# Methoden, die personenbezogene oder verhaltensnahe Daten beruehren.
# Quelle: Modul-Docstring von ascension_os/consent_gate.py (Sisyphos-Last,
# Psycholyse-Logs, Expositions-Transkripte) plus die LLM-Anfrage.
PERSONAL_DATA_METHODS = {
    "step_sisyphos",
    "log_psycholyse_session",
    "start_exposure_session",
    "exposure_respond",
    "end_exposure_session",
    "ask",
}


# ==========================================================================
# QUBO-Matrixkonstruktion (ohne Solver)
# ==========================================================================

def test_devil_christus_matrix_is_symmetric_and_correctly_sized() -> None:
    """Q ist symmetrisch mit Kantenlaenge 2n — der Solver-Kontrakt."""
    for n in (1, 2, 5, 12, 30):
        Q = build_devil_christus_qubo(n)
        assert Q.shape == (2 * n, 2 * n), f"falsche Groesse bei n={n}"
        assert np.allclose(Q, Q.T), f"unsymmetrisch bei n={n}"


def test_devil_christus_incoherence_penalty_sits_on_the_pole_pairs() -> None:
    """Die Strafe steht genau auf (d_i, c_i) — und dort in voller Hoehe."""
    n, penalty = 6, 2.0
    Q = build_devil_christus_qubo(n, incoherence_penalty=penalty)
    for i in range(n):
        d, c = i, n + i
        assert Q[d, c] + Q[c, d] == pytest.approx(penalty)
    # Keine Strafe zwischen Polen VERSCHIEDENER Checkpoints.
    assert Q[0, n + 1] == pytest.approx(0.0)
    assert Q[1, n + 0] == pytest.approx(0.0)


def test_devil_christus_bias_moves_from_devil_to_christus_over_time() -> None:
    """Devil wird teurer, Christus billiger — monoton ueber die Checkpoints.

    Das ist die einzige inhaltliche Aussage der Matrix: eine gerichtete
    Trajektorie. Sie ist hier als Monotonie der Diagonalen geprueft, nicht
    als Behauptung ueber reale Entwicklung (MODELL, siehe Modul-Docstring).
    """
    n = 10
    Q = build_devil_christus_qubo(n, base_bias=1.0)
    devil = [Q[i, i] for i in range(n)]
    christus = [Q[n + i, n + i] for i in range(n)]

    assert all(a <= b for a, b in zip(devil, devil[1:])), "Devil nicht monoton teurer"
    assert all(a >= b for a, b in zip(christus, christus[1:])), "Christus nicht monoton billiger"
    assert devil[0] == pytest.approx(0.0) and christus[0] == pytest.approx(0.0)
    assert devil[-1] > 0.0 > christus[-1]


def test_devil_christus_lock_in_penalty_only_in_the_oscillation_tail() -> None:
    """Die Lock-in-Strafe wirkt ausschliesslich im deklarierten Schwanzbereich."""
    n = 10
    ohne = build_devil_christus_qubo(n, lock_in_penalty=0.0)
    mit = build_devil_christus_qubo(n, lock_in_penalty=0.5, oscillation_tail_fraction=0.3)
    delta = mit - ohne

    tail_start = int(n * 0.7)
    for i, j in zip(*np.nonzero(delta)):
        i, j = int(i), int(j)
        cp_i = i % n
        cp_j = j % n
        assert min(cp_i, cp_j) >= tail_start, (
            f"Lock-in ausserhalb des Schwanzes bei Checkpoints {cp_i}/{cp_j}"
        )


def test_optimizer_fails_fast_without_the_solver() -> None:
    """Ohne qb_qubo wird der Optimizer nicht gebaut — kein stiller Fallback.

    In dieser Umgebung fehlt numba und damit qb_qubo. Das Modul taeuscht
    keinen Solver vor, sondern verweigert die Konstruktion mit ImportError.
    Ist der Solver vorhanden, muss die Konstruktion umgekehrt gelingen.
    """
    if qopt.qb_qubo is None:
        with pytest.raises(ImportError):
            qopt.QUBOAscensionOptimizer(n_checkpoints=4)
    else:
        assert qopt.QUBOAscensionOptimizer(n_checkpoints=4).n_checkpoints == 4


# ==========================================================================
# GenerationalEvolutionEngine — beschraenkte Fitness, wachsende Historie
# ==========================================================================

def test_evolution_fitness_is_bounded_for_arbitrary_input() -> None:
    """Der Score verlaesst [0, 100] nie — auch bei absurden Zustaenden nicht."""
    e = GenerationalEvolutionEngine()
    for state in (
        {},
        {"is_sustainable": True, "satisfaction": 1.0, "load": 0.0,
         "fail_closed_active": True, "masterseed_integrity": True,
         "ascension_mode_active": True},
        {"is_sustainable": False, "satisfaction": 0.0, "load": 1.0},
        {"satisfaction": 99.0, "load": -50.0},
        {"satisfaction": -99.0, "load": 99.0},
    ):
        score = e.evaluate_fitness(state)
        assert 0.0 <= score <= 100.0, f"Fitness {score} ausserhalb [0,100] fuer {state}"


def test_evolution_fitness_is_deterministic() -> None:
    """Gleicher Zustand, gleicher Score — keine versteckte Zufaelligkeit."""
    e = GenerationalEvolutionEngine()
    state = {"is_sustainable": True, "satisfaction": 0.7, "load": 0.3}
    assert len({e.evaluate_fitness(state) for _ in range(5)}) == 1


def test_evolution_generations_accumulate_and_are_numbered() -> None:
    """Jede Generation wird fortlaufend nummeriert und abgelegt."""
    e = GenerationalEvolutionEngine()
    state = {"is_sustainable": True, "satisfaction": 0.6, "load": 0.4}
    nums = [e.run_generation(state).number for _ in range(4)]
    assert nums == [1, 2, 3, 4]
    assert len(e.generations) == 4
    assert e.current_generation == 4


def test_evolution_always_proposes_at_least_one_improvement() -> None:
    """Auch im Bestzustand bleibt ein Vorschlag — kein 'fertig'."""
    e = GenerationalEvolutionEngine()
    perfect = {
        "is_sustainable": True, "satisfaction": 1.0, "load": 0.1,
        "fail_closed_active": True, "ascension_mode_active": True,
    }
    assert len(e.propose_improvements(perfect)) >= 1
    assert len(e.propose_improvements({})) >= 1


# ==========================================================================
# AscensionCore — Vollstaendigkeit des Consent-Gatings (AST)
# ==========================================================================

def _methods_calling_require_consent() -> set[str]:
    """Liest den Quelltext von AscensionCore und sammelt alle Methoden,
    die self._require_consent(...) aufrufen."""
    source = inspect.getsource(AscensionCore)
    tree = ast.parse(source)
    cls = tree.body[0]
    assert isinstance(cls, ast.ClassDef)

    gated = set()
    for node in cls.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for inner in ast.walk(node):
            if (
                isinstance(inner, ast.Call)
                and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == "_require_consent"
            ):
                gated.add(node.name)
                break
    return gated


def test_every_personal_data_method_is_consent_gated() -> None:
    """Jede personenbezogene Methode ruft _require_consent — keine Ausnahme.

    Dies ist der eigentliche Sicherheitsbeleg des Tracks. Er bestaetigt keine
    Rechnung, sondern schliesst eine Luecke aus: Eine einzige vergessene
    Absicherung wuerde das fail-closed-Versprechen (Dissertation 2.4)
    aushebeln, ohne dass ein Verhaltenstest sie zwingend bemerkt — man muesste
    genau die vergessene Methode aufrufen.
    """
    gated = _methods_calling_require_consent()
    missing = PERSONAL_DATA_METHODS - gated
    assert not missing, (
        f"Ungeschuetzte personenbezogene Methoden: {sorted(missing)}. "
        "Jede von ihnen umgeht das Consent-Gate."
    )


def test_personal_data_methods_still_exist_under_these_names() -> None:
    """Die Waechterliste zeigt auf echte Methoden — kein Schutz von Phantomen.

    Ohne diesen Test koennte eine Umbenennung den obigen Test gruen lassen,
    waehrend die umbenannte Methode ungeschuetzt weiterlaeuft.
    """
    for name in PERSONAL_DATA_METHODS:
        assert callable(getattr(AscensionCore, name, None)), (
            f"{name} existiert nicht mehr — Waechterliste veraltet"
        )


def test_core_without_gate_denies_personal_data_operations() -> None:
    """Fail closed im Verhalten, nicht nur in der Struktur."""
    core = AscensionCore()
    assert core._consent_gate is None
    with pytest.raises(Exception) as exc:
        core._require_consent("persistence", action="test")
    assert "consent" in str(exc.value).lower()


def test_non_personal_methods_are_not_gated() -> None:
    """Statusabfragen bleiben frei — das Gate ist zweckgebunden, nicht pauschal."""
    gated = _methods_calling_require_consent()
    for name in ("get_ascension_status", "get_sisyphos_state", "get_stage9_status"):
        assert name not in gated, (
            f"{name} ist unnoetig gegated — eine reine Statusabfrage "
            "sollte keinen Grant verlangen"
        )
