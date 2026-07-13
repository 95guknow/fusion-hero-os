# -*- coding: utf-8 -*-
"""Property-Tests fuer fusion_hero_os/core/quantum_cognition.py (QPT-Saetze).

Jeder Test verankert einen im Modul-Docstring BEWIESENEN Satz per
Zufalls-Sweep mit 0 erlaubten Verletzungen (Registry-IDs QPT-*).
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from fusion_hero_os.core.quantum_cognition import (
    BeliefState,
    TwoLevelOscillator,
    interference_term,
    order_effect,
    projector_from_vectors,
    qq_equality_residual,
)

rng = np.random.default_rng(20260705)


def _random_state(n):
    return rng.normal(size=n) + 1j * rng.normal(size=n)


def _random_unitary(n):
    Q, R = np.linalg.qr(rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n)))
    return Q @ np.diag(np.diag(R) / np.abs(np.diag(R)))


def _random_projector(n, k=None):
    k = k or int(rng.integers(1, n))
    return projector_from_vectors(rng.normal(size=(n, k)) + 1j * rng.normal(size=(n, k)))


def _complete_partition(n, n_blocks):
    """Vollstaendige orthogonale Projektor-Familie aus einer Zufalls-Basis."""
    V = _random_unitary(n)
    cuts = sorted(rng.choice(range(1, n), size=n_blocks - 1, replace=False)) if n_blocks > 1 else []
    blocks, start = [], 0
    for c in list(cuts) + [n]:
        cols = V[:, start:c]
        blocks.append(cols @ cols.conj().T)
        start = c
    return blocks


# ---- QPT-BORN-COMPLETENESS -------------------------------------------------

def test_born_rule_probabilities_sum_to_one_property_sweep():
    for _ in range(300):
        n = int(rng.integers(2, 8))
        m = int(rng.integers(1, n + 1))
        partition = _complete_partition(n, m)
        s = BeliefState(_random_state(n))
        probs = [s.prob(P) for P in partition]
        assert all(p >= -1e-12 for p in probs)
        assert abs(sum(probs) - 1.0) < 1e-9


def test_collapse_renormalizes_and_zero_prob_raises():
    P = projector_from_vectors(np.array([[1.0], [0.0]]))
    s = BeliefState(np.array([0.6, 0.8]))
    c = s.collapse(P)
    assert abs(np.linalg.norm(c.psi) - 1.0) < 1e-12
    orth = BeliefState(np.array([0.0, 1.0]))
    with pytest.raises(ValueError):
        orth.collapse(P)


def test_non_projector_is_rejected():
    s = BeliefState(np.array([1.0, 0.0]))
    with pytest.raises(ValueError):
        s.prob(np.array([[0.0, 1.0], [0.0, 0.0]]))  # nicht hermitesch
    with pytest.raises(ValueError):
        s.prob(np.array([[0.5, 0.0], [0.0, 0.5]]))  # hermitesch, nicht idempotent


# ---- QPT-QQ-EQUALITY ---------------------------------------------------------

def test_qq_equality_holds_for_all_states_and_projectors_property_sweep():
    """SATZ: QQ-Residuum = 0 fuer beliebige Zustaende/Projektoren (0 Verletzungen)."""
    for _ in range(500):
        n = int(rng.integers(2, 8))
        residual = qq_equality_residual(_random_state(n),
                                        _random_projector(n), _random_projector(n))
        assert abs(residual) < 1e-9


def test_individual_order_effects_are_generally_nonzero_control():
    """Kontrolle (Nicht-Trivialitaet): einzelne Ordnungseffekte sind haeufig != 0,
    obwohl ihre QQ-Summe exakt 0 ist — genau das ist der Gehalt des Satzes."""
    nonzero = 0
    trials = 200
    for _ in range(trials):
        n = int(rng.integers(2, 8))
        if abs(order_effect(_random_state(n), _random_projector(n), _random_projector(n))) > 1e-6:
            nonzero += 1
    assert nonzero > trials // 3, "Ordnungseffekte fast nie sichtbar — Sweep zu schwach"


# ---- QPT-ORDER-COMMUTE -------------------------------------------------------

def test_commuting_projectors_have_zero_order_effect_property_sweep():
    """SATZ: [P_A,P_B]=0 => Ordnungseffekt exakt 0 fuer jeden Zustand."""
    for _ in range(300):
        n = int(rng.integers(2, 8))
        V = _random_unitary(n)
        mask_a = rng.integers(0, 2, size=n).astype(float)
        mask_b = rng.integers(0, 2, size=n).astype(float)
        P_A = V @ np.diag(mask_a) @ V.conj().T
        P_B = V @ np.diag(mask_b) @ V.conj().T
        assert abs(order_effect(_random_state(n), P_A, P_B)) < 1e-9


# ---- QPT-INTERFERENZ-ZERLEGUNG ------------------------------------------------

def test_interference_decomposition_is_exact_property_sweep():
    """SATZ: delta = 2 sum_{i<j} Re<F P_i psi, F P_j psi> (unabhaengig nachgerechnet)."""
    for _ in range(300):
        n = int(rng.integers(2, 8))
        m = int(rng.integers(1, n + 1))
        partition = _complete_partition(n, m)
        F = _random_projector(n)
        psi = _random_state(n)
        psi_n = psi / np.linalg.norm(psi)
        delta = interference_term(psi, F, partition)
        xs = [F @ P @ psi_n for P in partition]
        cross = 2.0 * sum(np.real(np.vdot(xs[i], xs[j]))
                          for i in range(len(xs)) for j in range(i + 1, len(xs)))
        assert abs(delta - cross) < 1e-9


def test_interference_vanishes_when_final_commutes_with_partition():
    """ZUSATZ-SATZ: F kommutiert mit allen P_i => delta = 0 (klassischer Grenzfall)."""
    for _ in range(200):
        n = int(rng.integers(3, 8))
        V = _random_unitary(n)
        m = int(rng.integers(2, n + 1))
        # Partition UND F aus derselben Eigenbasis -> alles kommutiert
        cuts = sorted(rng.choice(range(1, n), size=m - 1, replace=False))
        partition, start = [], 0
        for c in list(cuts) + [n]:
            cols = V[:, start:c]
            partition.append(cols @ cols.conj().T)
            start = c
        mask = rng.integers(0, 2, size=n).astype(float)
        F = V @ np.diag(mask) @ V.conj().T
        assert abs(interference_term(_random_state(n), F, partition)) < 1e-9


# ---- QPT-2LEVEL-OSZILLATION ----------------------------------------------------

def test_two_level_closed_form_matches_spectral_and_is_unitary_property_sweep():
    for _ in range(300):
        omega = float(rng.uniform(-5, 5))
        t = float(rng.uniform(-10, 10))
        osc = TwoLevelOscillator(omega)
        U1, U2 = osc.unitary(t), osc.unitary_via_spectral(t)
        assert np.linalg.norm(U1 - U2) < 1e-9                       # zwei Rechenwege
        assert np.linalg.norm(U1 @ U1.conj().T - np.eye(2)) < 1e-9  # unitaer


def test_two_level_transition_probability_is_sin_squared():
    for _ in range(300):
        omega = float(rng.uniform(-5, 5))
        t = float(rng.uniform(-10, 10))
        osc = TwoLevelOscillator(omega)
        evolved = osc.evolve(np.array([1.0, 0.0]), t)
        p_num = abs(evolved.psi[1]) ** 2
        assert abs(p_num - osc.transition_probability(t)) < 1e-9
        assert abs(np.linalg.norm(evolved.psi) - 1.0) < 1e-12
