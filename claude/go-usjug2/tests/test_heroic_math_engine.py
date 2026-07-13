"""Ehrliche Regressionstests für core/heroic_math_engine.py.

Diese Tests behaupten NICHT, dass Knoten 16 (Reziprozität) oder Knoten 19
(Monotonie) universell bewiesene mathematische Gesetze sind - beide sind
laut Modul-Docstring als FRAGMENT bzw. MODELL eingestuft. Stattdessen wird
genau das verankert, was tatsächlich verifiziert wurde, damit ein künftiger
Edit nicht stillschweigend wieder in eine Überclaim-Behauptung zurückfällt.
"""
import numpy as np
import pytest

from fusion_hero_os.core.heroic_math_engine import HeroicMatrixEngine, RepairedStructureIP


def test_commutator_is_antisymmetric():
    """Knoten 1: [Q,B] = -[B,Q] ist reine lineare Algebra, keine Sonderbehauptung."""
    engine = HeroicMatrixEngine()
    comm_qb = engine.compute_commutator(engine.q_default, engine.b_default)
    comm_bq = engine.compute_commutator(engine.b_default, engine.q_default)
    assert np.allclose(comm_qb, -comm_bq)


def test_reciprocity_holds_only_in_trivial_case():
    """Knoten 16 (FRAGMENT): reziprok NUR wenn Q1==Q2 - keine universelle Reziprozität."""
    engine = HeroicMatrixEngine()
    m1 = np.array([[0.5, 0.2], [0.1, 0.9]])
    m2 = np.array([[0.8, -0.3], [0.4, 0.2]])

    assert engine.check_reciprocity_condition(m1, engine.b_default, m1, engine.b_default) is True

    # Auch mit zwei echten Rotationsmatrizen (nicht nur generischen) gilt es NICHT
    # für Q1 != Q2 - das ist der dokumentierte, verifizierte Fragment-Status.
    def rot(phi):
        return np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])

    assert engine.check_reciprocity_condition(m1, engine.b_default, m2, engine.b_default) is False
    assert engine.check_reciprocity_condition(rot(0.3), engine.b_default, rot(0.9), engine.b_default) is False


def test_monotonicity_documented_example_holds():
    """Knoten 19 (MODELL): das im Modul dokumentierte Beispiel muss weiterhin halten."""
    ip = RepairedStructureIP(lmbda=0.5, eta=1.5)
    psi, phi = complex(2.0, -1.0), complex(1.5, -0.5)
    s_psi, s_phi = ip.compute_stability(psi), ip.compute_stability(phi)
    s_fused = ip.compute_stability(ip.fusion_operator(psi, phi))
    assert s_fused >= max(s_psi, s_phi)


def test_monotonicity_is_not_a_universal_law():
    """Knoten 19 (MODELL): Verletzungsrate bleibt in einer erwartbaren Größenordnung.

    Kein Beweis für 0% - im Gegenteil, dieser Test verankert, dass es KEIN
    universelles Gesetz ist (per Sweep beobachtete Rate ~10-40%). Schlägt nur
    fehl, wenn sich das grundlegende Verhalten der Formel unerwartet ändert.
    """
    ip = RepairedStructureIP(lmbda=0.5, eta=1.5)
    rng = np.random.default_rng(42)
    tested = violations = 0
    for _ in range(500):
        p = complex(rng.uniform(-3, 3), rng.uniform(-3, 3))
        q = complex(rng.uniform(-3, 3), rng.uniform(-3, 3))
        if not ip.check_compatibility(p, q):
            continue
        tested += 1
        sp, sq = ip.compute_stability(p), ip.compute_stability(q)
        sf = ip.compute_stability(ip.fusion_operator(p, q))
        if sf < max(sp, sq) - 1e-9:
            violations += 1
    assert tested > 100, "Sweep sollte genug kompatible Paare finden, um aussagekräftig zu sein"
    rate = violations / tested
    assert 0.05 < rate < 0.60, (
        f"Verletzungsrate {rate:.1%} liegt außerhalb der erwarteten Fragment-Bandbreite - "
        "entweder wurde die Formel echt repariert (Docstring aktualisieren!) oder "
        "etwas anderes hat sich unerwartet geändert."
    )


def test_module_docstring_does_not_reclaim_all_four_nodes():
    """Wächter gegen Rückfall in die Überclaim-Formulierung.

    Die frühere Docstring-Zeile 'Repariert zentrale mathematische Schwächen
    (Knoten 16, 17, 19, 20)' behauptete alle vier als erledigt, obwohl nur
    Knoten 1/16/19 überhaupt Code haben (und davon nur mit Einschränkungen).
    Dieser Test schlägt fehl, falls diese Formulierung unbemerkt zurückkehrt.
    """
    import fusion_hero_os.core.heroic_math_engine as mod

    doc = (mod.__doc__ or "").lower()
    assert "repariert zentrale mathematische schwächen (knoten 16, 17, 19, 20)" not in doc
    assert "nicht implementiert" in doc, "Docstring sollte Knoten 17/20 explizit als offen kennzeichnen"
