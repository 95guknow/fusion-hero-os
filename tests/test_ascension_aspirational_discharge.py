# -*- coding: utf-8 -*-
"""Ueberfuehrt aspirationale Ascension-Module in belegte Struktur.

Der AscensionCore traegt die Version "9.10-aspirational" — eine zutreffende
Selbstauskunft: der Track enthielt Module, deren Anspruch ueber ihren belegten
Stand hinausreichte. Diese Datei entlaedt einen Teil dieser Aspiration, indem
sie die STRUKTURELLEN Eigenschaften von harmonisierung_module und
geisterjagd_module pruefbar macht.

Was hier NICHT getestet wird und auch nicht getestet werden kann:
  * dass q/b reales fliessendes/schneidendes Denken abbilden (Modell),
  * dass "Geister" reale latente LLM-Aktivierungen sind (Modell — die Module
    sagen das selbst in ihren Docstrings),
  * dass die Harmonisierung reale zwischenmenschliche Dynamik beschreibt.
Diese Ebenen bleiben Modell. Ein Test, der so taete, waere genau die
Badge-Ontologie, die V3.3 §9 als Fail-Kriterium nennt.

Konvention: Knoten, die in proof_registry.yaml zitiert werden, sind NICHT
parametrisiert — der Registry-Checker prueft die nackte Node-ID gegen die
pytest-Collection.
"""

from __future__ import annotations

import numpy as np
import pytest

from ascension_os.core.geisterjagd_module import Geisterjagdmodul
from ascension_os.core.harmonisierung_module import HarmonisierungsCoreModule


def _contraction(n: int = 3, factor: float = 0.5):
    """Eine garantierte Kontraktion: A = factor*I mit factor < 1."""
    return factor * np.eye(n), np.ones(n)


# ==========================================================================
# Geisterjagd — Kontraktion, Konvergenz und Nothing-Bereitschaft
# ==========================================================================

def test_geisterjagd_returns_nothing_when_map_is_not_a_contraction() -> None:
    """Keine Kontraktion => Nothing, nicht vorgetaeuschte Konvergenz.

    Dies ist die operative Form der Nothing-Bereitschaft: Das Modul darf an
    der Stelle, an der ein Ergebnis erwartet wird, keines liefern.
    """
    jaeger = Geisterjagdmodul()
    for bad_factor in (1.0, 1.5, 3.0):
        A = bad_factor * np.eye(3)
        result = jaeger.hunt(np.array([1.0, 2.0, 3.0]), A, np.zeros(3))
        assert result.converged is False, f"faelschlich konvergiert bei {bad_factor}"
        assert result.manifest is None
        assert result.contraction_factor is None
        assert result.steps == 0
        assert result.initial_distance is None
        assert result.final_distance is None


def test_geisterjagd_converges_and_reduces_distance_under_contraction() -> None:
    """Kontraktion => Konvergenz, und der Endabstand ist echt kleiner."""
    jaeger = Geisterjagdmodul()
    A, c = _contraction()
    for start in ([10.0, -4.0, 7.0], [0.5, 0.5, 0.5], [-100.0, 100.0, 0.0]):
        result = jaeger.hunt(np.array(start), A, c)
        assert result.converged is True
        assert result.manifest is not None
        assert result.contraction_factor is not None
        assert result.contraction_factor < 1.0
        assert result.initial_distance is not None
        assert result.final_distance is not None
        assert result.final_distance < result.initial_distance
        assert result.final_distance == pytest.approx(0.0, abs=1e-6)


def test_geisterjagd_reaches_same_fixpoint_from_any_start() -> None:
    """Banach: der Grenzwert haengt nicht vom Startpunkt ab."""
    jaeger = Geisterjagdmodul()
    A, c = _contraction()
    starts = [[10.0, -4.0, 7.0], [0.0, 0.0, 0.0], [-50.0, 3.0, 99.0]]
    results = jaeger.hunt_multiple([np.array(s) for s in starts], A, c)

    assert all(r.converged for r in results)
    reference = np.asarray(results[0].manifest, dtype=float)
    for r in results[1:]:
        assert np.allclose(np.asarray(r.manifest, dtype=float), reference, atol=1e-6)


# ==========================================================================
# Harmonisierung — Kontraktionsvorbedingung, Gap-Schluss, Narzissmus-Filter
# ==========================================================================

def test_harmonisierung_rejects_non_contracting_alphas() -> None:
    """Die Kontraktionsbedingung wird bei der Konstruktion erzwungen."""
    for bad in (0.0, 1.0, -0.5, 1.5):
        with pytest.raises(ValueError):
            HarmonisierungsCoreModule(alpha_q=bad)
        with pytest.raises(ValueError):
            HarmonisierungsCoreModule(alpha_b=bad)


def test_harmonisierung_is_always_a_contraction_and_closes_the_gap(tmp_path) -> None:
    """H ist per Konstruktion Kontraktion; der Abstand wird echt kleiner."""
    modul = HarmonisierungsCoreModule(
        persistence_path=str(tmp_path / "hist.json")
    )
    for a, b in (
        ([1.0, 0.0], [0.0, 1.0]),
        ([10.0, 10.0], [-10.0, -10.0]),
        ([3.0, 1.0, 4.0], [1.0, 5.0, 9.0]),
    ):
        r = modul.harmonize(np.array(a), np.array(b))
        assert r.is_contraction is True
        assert r.contraction_factor is not None and r.contraction_factor < 1.0
        assert r.final_gap < r.initial_gap
        # Beide Seiten laufen auf DENSELBEN Fixpunkt zu.
        assert r.final_gap == pytest.approx(0.0, abs=1e-6)
        assert r.fixpoint is not None


def test_harmonisierung_noncommutativity_is_strictly_positive(tmp_path) -> None:
    """b(q(x)) != q(b(x)) — Gesetz 2 in der gewaehlten Formalisierung.

    Der Kanon zitiert dieses Modul fuer die Nicht-Kommutativitaet von q∘b
    (Gesetz 2 / S14). Bis hierher war die Zitation ohne Test. Sie ist es
    jetzt nicht mehr.

    Geltung: Dies belegt die Ungleichheit IN DIESER Formalisierung. Dass sie
    konzeptuelles fliessendes vs. schneidendes Denken abbildet, bleibt Modell.
    """
    modul = HarmonisierungsCoreModule(
        alpha_q=0.8, alpha_b=0.4, persistence_path=str(tmp_path / "hist.json")
    )
    for a, b in (
        ([1.0, 0.0], [0.0, 1.0]),
        ([5.0, -3.0], [-2.0, 8.0]),
        ([1.0, 2.0, 3.0], [7.0, -1.0, 0.0]),
    ):
        r = modul.harmonize(np.array(a), np.array(b))
        assert r.noncommutativity_gap > 0.0, (
            f"q∘b faelschlich kommutativ fuer {a} / {b}"
        )


def test_harmonisierung_narcissism_filter_blocks_the_unmoved(tmp_path) -> None:
    """Bewegt sich niemand, ist es keine Harmonisierung, sondern Selbstbestaetigung.

    Zwei identische Zustaende sitzen bereits im Fixpunkt: keine Abweichung,
    Filter faellt durch, kein Zufriedenheitsquant.
    """
    modul = HarmonisierungsCoreModule(
        persistence_path=str(tmp_path / "hist.json")
    )
    same = np.array([2.0, 2.0])
    r = modul.harmonize(same, same.copy(), participant_labels=("A", "B"))

    assert set(r.narzissmus_filter_passed) == {"A", "B"}
    assert not any(r.narzissmus_filter_passed.values())
    assert r.zufriedenheitsquant is False

    # Gegenprobe: verschiedene Zustaende bewegen beide Seiten.
    r2 = modul.harmonize(np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    assert all(r2.narzissmus_filter_passed.values())
    assert r2.zufriedenheitsquant is True


def test_harmonisierung_records_history(tmp_path) -> None:
    """Jede Operation wird protokolliert — kein stilles Verwerfen."""
    modul = HarmonisierungsCoreModule(
        persistence_path=str(tmp_path / "hist.json")
    )
    before = len(modul.history)
    modul.harmonize(np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    modul.harmonize(np.array([2.0, 0.0]), np.array([0.0, 2.0]))
    assert len(modul.history) == before + 2
