# -*- coding: utf-8 -*-
"""Tests fuer den Triple-Yin-Yang-Modus in n Dimensionen.

Deckt die Satz-Ebene aus dem Modul-Docstring von
ascension_os.core.yin_yang_manifold ab. Die Modell- und Fragment-Ebene
(Wahl der Paare, Deutung der Kreuzkopplung) wird bewusst NICHT getestet —
sie ist nicht testbar, und ein Test, der so tut, waere unehrlich.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from ascension_os.core.qubo_ascension_optimizer import build_devil_christus_qubo
from ascension_os.core.yin_yang_manifold import (
    TRIPLE_CANON,
    ManifoldSpec,
    PolePair,
    build_yin_yang_qubo,
    describe,
    energy,
    incoherence_is_dominated,
)

DEVIL_CHRISTUS = (PolePair("devil_christus", "devil", "christus"),)


# --------------------------------------------------------------------------
# Struktur (Satz)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n_pairs,n", [(1, 1), (1, 12), (3, 12), (5, 7)])
def test_dimension_is_two_k_n(n_pairs: int, n: int) -> None:
    """Dimension des Zustandsraums ist exakt 2*k*n."""
    spec = ManifoldSpec(n_pairs=n_pairs, n_checkpoints=n)
    assert spec.dimension == 2 * n_pairs * n

    pairs = tuple(PolePair(f"p{i}", "yin", "yang") for i in range(n_pairs))
    Q = build_yin_yang_qubo(n, pairs=pairs)
    assert Q.shape == (2 * n_pairs * n, 2 * n_pairs * n)


@pytest.mark.parametrize("n", [1, 2, 12, 25])
def test_q_is_symmetric(n: int) -> None:
    """Q ist symmetrisch — mit und ohne Kreuzkopplung."""
    for coupling in (0.0, 0.75):
        Q = build_yin_yang_qubo(n, cross_pair_coupling=coupling)
        assert np.allclose(Q, Q.T), f"unsymmetrisch bei coupling={coupling}"


def test_indices_are_unique_and_cover_the_space() -> None:
    """Die Index-Abbildung ist eine Bijektion auf {0..2kn-1}."""
    spec = ManifoldSpec(n_pairs=3, n_checkpoints=4)
    seen = [
        spec.index(p, pole, i)
        for p in range(spec.n_pairs)
        for pole in ("yin", "yang")
        for i in range(spec.n_checkpoints)
    ]
    assert sorted(seen) == list(range(spec.dimension))


def test_index_rejects_bad_input() -> None:
    spec = ManifoldSpec(n_pairs=2, n_checkpoints=3)
    with pytest.raises(ValueError):
        spec.index(0, "neutral", 0)
    with pytest.raises(IndexError):
        spec.index(2, "yin", 0)
    with pytest.raises(IndexError):
        spec.index(0, "yin", 3)


def test_build_rejects_empty_and_degenerate_input() -> None:
    with pytest.raises(ValueError):
        build_yin_yang_qubo(0)
    with pytest.raises(ValueError):
        build_yin_yang_qubo(4, pairs=())


# --------------------------------------------------------------------------
# Reproduktion des zweipoligen Falls (Satz) — kein Fork der Semantik
# --------------------------------------------------------------------------

@pytest.mark.parametrize("n", [1, 2, 5, 12, 30])
def test_single_pair_reproduces_devil_christus_bitwise(n: int) -> None:
    """k=1 liefert bitgenau die bestehende Devil-vs-Christus-Matrix."""
    expected = build_devil_christus_qubo(n)
    got = build_yin_yang_qubo(n, pairs=DEVIL_CHRISTUS)
    assert got.shape == expected.shape
    assert np.array_equal(got, expected)


def test_single_pair_reproduces_with_custom_parameters() -> None:
    """Auch mit abweichenden Parametern bleibt die Reproduktion exakt."""
    kwargs = dict(
        base_bias=2.5,
        incoherence_penalty=4.0,
        lock_in_penalty=0.25,
        oscillation_tail_fraction=0.5,
    )
    expected = build_devil_christus_qubo(9, **kwargs)
    got = build_yin_yang_qubo(9, pairs=DEVIL_CHRISTUS, **kwargs)
    assert np.array_equal(got, expected)


def test_pairs_are_block_diagonal_without_coupling() -> None:
    """Ohne Kreuzkopplung ist Q die blockdiagonale Summe der Einzelpaare."""
    n = 6
    Q = build_yin_yang_qubo(n, cross_pair_coupling=0.0)
    block = build_yin_yang_qubo(n, pairs=DEVIL_CHRISTUS)
    size = 2 * n
    for p in range(len(TRIPLE_CANON)):
        s = p * size
        assert np.array_equal(Q[s:s + size, s:s + size], block)
    # Ausserhalb der Bloecke ist alles null.
    mask = np.ones_like(Q, dtype=bool)
    for p in range(len(TRIPLE_CANON)):
        s = p * size
        mask[s:s + size, s:s + size] = False
    assert not Q[mask].any()


def test_cross_pair_coupling_only_touches_adjacent_yang_poles() -> None:
    """Die Kopplung wirkt genau dort, wo sie deklariert ist — sonst nirgends."""
    n = 4
    base = build_yin_yang_qubo(n, cross_pair_coupling=0.0)
    coupled = build_yin_yang_qubo(n, cross_pair_coupling=1.0)
    delta = coupled - base
    spec = ManifoldSpec(n_pairs=len(TRIPLE_CANON), n_checkpoints=n)

    expected_nonzero = set()
    for p in range(spec.n_pairs - 1):
        for i in range(n):
            a = spec.index(p, "yang", i)
            b = spec.index(p + 1, "yang", i)
            expected_nonzero.add((a, b))
            expected_nonzero.add((b, a))

    got_nonzero = {(int(i), int(j)) for i, j in zip(*np.nonzero(delta))}
    assert got_nonzero == expected_nonzero


# --------------------------------------------------------------------------
# Inkohaerenz-Schranke (Satz)
# --------------------------------------------------------------------------

def test_incoherence_bound_predicate() -> None:
    assert incoherence_is_dominated(12, base_bias=1.0, incoherence_penalty=2.0)
    assert not incoherence_is_dominated(12, base_bias=2.0, incoherence_penalty=2.0)
    assert not incoherence_is_dominated(12, base_bias=3.0, incoherence_penalty=2.0)


@pytest.mark.parametrize("n", [1, 3, 8])
def test_incoherent_state_is_strictly_more_expensive(n: int) -> None:
    """Unter der Schranke ist 'beide Pole aktiv' strikt teurer als 'nur Yang'.

    Geprueft an JEDEM Paar und JEDEM Checkpoint, mit sonst leerem Zustand.
    """
    base_bias, penalty = 1.0, 2.0
    assert incoherence_is_dominated(n, base_bias, penalty)
    Q = build_yin_yang_qubo(
        n, base_bias=base_bias, incoherence_penalty=penalty
    )
    spec = ManifoldSpec(n_pairs=len(TRIPLE_CANON), n_checkpoints=n)

    for p in range(spec.n_pairs):
        for i in range(n):
            both = np.zeros(spec.dimension, dtype=int)
            both[spec.index(p, "yin", i)] = 1
            both[spec.index(p, "yang", i)] = 1

            only_yang = both.copy()
            only_yang[spec.index(p, "yin", i)] = 0

            assert energy(Q, both) > energy(Q, only_yang), (
                f"Inkohaerenz nicht bestraft bei Paar {p}, Checkpoint {i}"
            )


def test_incoherence_penalty_appears_in_energy_exactly_once() -> None:
    """Die Strafe schlaegt mit genau `incoherence_penalty` zu Buche."""
    n = 1  # t = 0, daher kein Bias-Anteil
    penalty = 3.0
    Q = build_yin_yang_qubo(n, incoherence_penalty=penalty)
    spec = ManifoldSpec(n_pairs=len(TRIPLE_CANON), n_checkpoints=n)

    both = np.zeros(spec.dimension, dtype=int)
    both[spec.index(0, "yin", 0)] = 1
    both[spec.index(0, "yang", 0)] = 1
    assert energy(Q, both) == pytest.approx(penalty)


def test_empty_state_has_zero_energy() -> None:
    Q = build_yin_yang_qubo(7)
    assert energy(Q, np.zeros(Q.shape[0], dtype=int)) == pytest.approx(0.0)


# --------------------------------------------------------------------------
# Selbstauskunft
# --------------------------------------------------------------------------

def test_describe_reports_triple_mode_and_geltung() -> None:
    d = describe()
    assert d["mode"] == "triple"
    assert d["n_pairs"] == 3
    assert d["dimension"] == 2 * 3 * 12
    assert [p["name"] for p in d["pairs"]] == [
        "qb", "impression_expression", "devil_christus"
    ]
    # Die Selbstauskunft muss die Geltung mitliefern, nicht nur die Struktur.
    assert "Satz" in d["geltung"]["structure"]
    assert "Modell" in d["geltung"]["pair_choice"]
    assert "Fragment" in d["geltung"]["cross_pair_coupling"]


def test_describe_reports_n_fold_for_other_sizes() -> None:
    pairs = tuple(PolePair(f"p{i}", "yin", "yang") for i in range(5))
    assert describe(pairs=pairs, n_checkpoints=3)["mode"] == "5-fold"


def test_brute_force_ground_state_is_coherent_for_small_instance() -> None:
    """Auf einer kleinen Instanz enthaelt der Grundzustand keine Inkohaerenz."""
    n = 2
    pairs = DEVIL_CHRISTUS
    Q = build_yin_yang_qubo(n, pairs=pairs)
    dim = 2 * len(pairs) * n
    spec = ManifoldSpec(n_pairs=len(pairs), n_checkpoints=n)

    best = min(itertools.product([0, 1], repeat=dim), key=lambda x: energy(Q, x))
    for i in range(n):
        assert not (best[spec.index(0, "yin", i)] and best[spec.index(0, "yang", i)])
