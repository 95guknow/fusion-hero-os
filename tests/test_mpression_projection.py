# -*- coding: utf-8 -*-
"""Tests fuer mpression_projection: Projektionsverlust via bewiesenem
K17-Orthogonalprojektor. Proof-Registry-Anker: MPRESSION-PROJECTION-LOSS."""

from __future__ import annotations

import numpy as np

from ascension_os.core.mpression_projection import MpressionResult, measure_mpression

# Unterraum = x/y-Ebene im R^3 (Spaltenvektoren als Basis-Kandidaten).
XY_PLANE = [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]


def test_loss_is_zero_when_vector_lies_in_subspace():
    result = measure_mpression([2.0, -3.0, 0.0], XY_PLANE)
    assert isinstance(result, MpressionResult)
    assert result.loss < 1e-9
    assert result.relative_loss < 1e-9


def test_loss_is_positive_for_orthogonal_component():
    result = measure_mpression([1.0, 2.0, 3.0], XY_PLANE)
    assert result is not None
    # Verlust ist exakt die z-Komponente (orthogonal zur x/y-Ebene).
    assert abs(result.loss - 3.0) < 1e-9


def test_pythagoras_identity_holds():
    """||v||^2 == ||Pv||^2 + ||v-Pv||^2 — folgt aus K17 (Satz)."""
    rng = np.random.default_rng(17)
    for _ in range(10):
        v = rng.normal(size=5)
        basis = rng.normal(size=(5, 2))
        result = measure_mpression(v, basis)
        assert result is not None
        assert result.pythagoras_residual < 1e-9


def test_relative_loss_is_between_zero_and_one():
    """Nicht-Expansivitaet (K17d): ||Pv|| <= ||v|| => relative_loss in [0,1]."""
    rng = np.random.default_rng(42)
    for _ in range(10):
        v = rng.normal(size=4)
        basis = rng.normal(size=(4, 2))
        result = measure_mpression(v, basis)
        assert result is not None
        assert 0.0 <= result.relative_loss <= 1.0 + 1e-12


def test_zero_vector_has_zero_relative_loss_without_division_error():
    result = measure_mpression([0.0, 0.0, 0.0], XY_PLANE)
    assert result is not None
    assert result.loss < 1e-12
    assert result.relative_loss == 0.0
