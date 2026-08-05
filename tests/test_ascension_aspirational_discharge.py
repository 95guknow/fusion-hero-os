# -*- coding: utf-8 -*-
"""Aspirational → BEWIESEN: Discharge der scharf beweisbaren Invarianten aus
HarmonisierungsCoreModule + Geisterjagdmodul.

Heroische Base: BanachContractionSeed (K20, heroic_math_engine) — beide Module
sind *keine* parallele Mathematik, sondern Instanzen des bewiesenen affinen
Kontraktions-Spezialfalls.

Geltung:
  * BEWIESEN (pytest): Kontraktion, Nothing-Bereitschaft, Gap-Reduktion,
    Self-Mod nur bei Kontraktion, Fixpunkt-Eindeutigkeit.
  * MODELL (nicht Claim): psychologische Deutung von q/b, „Geister“ als LLM-Latenz.

Proof-Registry-Anker:
  ASC-HARMONISIERUNG-CONTRACTION, ASC-GEISTERJAGD-NOTHING-OR-FIXPOINT
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ascension_os.core.geisterjagd_module import GeisterjagdResult, Geisterjagdmodul
from ascension_os.core.harmonisierung_module import (
    HarmonisierungsCoreModule,
    HarmonizationResult,
)
from fusion_hero_os.core.heroic_math_engine import BanachContractionSeed


# ---------------------------------------------------------------------------
# HarmonisierungsCoreModule — H = ½(b∘q + q∘b) auf K20-Base
# ---------------------------------------------------------------------------


@pytest.fixture()
def harm(tmp_path: Path) -> HarmonisierungsCoreModule:
    return HarmonisierungsCoreModule(
        persistence_path=str(tmp_path / "harmonisierung_history.json")
    )


def test_harmonisierung_is_contraction_by_construction(harm: HarmonisierungsCoreModule):
    """Alpha in (0,1) ⇒ H ist Banach-Kontraktion (K20); is_contraction == True."""
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    r = harm.harmonize(a, b)
    assert isinstance(r, HarmonizationResult)
    assert r.is_contraction is True
    assert r.contraction_factor is not None
    assert 0.0 <= r.contraction_factor < 1.0


def test_harmonisierung_strictly_reduces_gap_when_states_differ(
    harm: HarmonisierungsCoreModule,
):
    """Kooperations-Kriterium: final_gap < initial_gap für ungleich startende Partner."""
    a = np.array([2.0, -1.0, 0.5])
    b = np.array([-1.0, 3.0, 0.0])
    r = harm.harmonize(a, b)
    assert r.initial_gap > 1e-9
    assert r.final_gap < r.initial_gap
    # Beide laufen auf denselben H-Fixpunkt → Gap → 0 (numerisch)
    assert r.final_gap < 1e-6


def test_harmonisierung_fixpoint_is_unique_k20_instance(
    harm: HarmonisierungsCoreModule,
):
    """Beide Startzustände konvergieren zum selben Fixpunkt (Eindeutigkeit K20)."""
    a = np.array([4.0, 0.0])
    b = np.array([0.0, 4.0])
    r = harm.harmonize(a, b)
    assert r.fixpoint is not None
    fp = np.asarray(r.fixpoint, dtype=np.float64)
    # Re-build H-seed und vergleiche geschlossene Form
    h_seed, _, _ = harm._build_h_seed(a, b)
    x_star = h_seed.fixpoint()
    assert np.allclose(fp, x_star, atol=1e-8)


def test_harmonisierung_self_mod_only_when_contraction(
    harm: HarmonisierungsCoreModule,
):
    """Evolution Rule: propose_self_modification nur bei is_contraction (Proposal-only)."""
    r = harm.harmonize([1.0, 0.0], [0.0, 1.0])
    prop = harm.propose_self_modification(r)
    assert prop["proposed"] is True
    assert prop["target"] == "PeerReviewCoreModule"
    # Negative path: synthetisches Resultat ohne Kontraktion
    fake = HarmonizationResult(
        timestamp="t",
        initial_gap=1.0,
        final_gap=1.0,
        noncommutativity_gap=0.0,
        is_contraction=False,
        contraction_factor=None,
        steps=0,
        zufriedenheitsquant=False,
        narzissmus_filter_passed={"A": False, "B": False},
        fixpoint=None,
    )
    denied = harm.propose_self_modification(fake)
    assert denied["proposed"] is False


def test_harmonisierung_alpha_out_of_range_rejected(tmp_path: Path):
    """Kontraktionsbedingung: alpha ∉ (0,1) → ValueError (kein Fake-Modul)."""
    with pytest.raises(ValueError):
        HarmonisierungsCoreModule(
            alpha_q=1.0,
            persistence_path=str(tmp_path / "h.json"),
        )
    with pytest.raises(ValueError):
        HarmonisierungsCoreModule(
            alpha_b=0.0,
            persistence_path=str(tmp_path / "h2.json"),
        )


# ---------------------------------------------------------------------------
# Geisterjagdmodul — Nothing oder Fixpunkt (K20 / fail-closed)
# ---------------------------------------------------------------------------


def test_geisterjagd_converges_under_contraction():
    """||A||_2 < 1 ⇒ converged, manifest ≈ x* = (I−A)^{-1}c."""
    A = 0.5 * np.eye(2)
    c = np.array([1.0, 1.0])
    seed = BanachContractionSeed(A, c)
    x_star = seed.fixpoint()
    result = Geisterjagdmodul().hunt([10.0, -5.0], A, c, tol=1e-9)
    assert isinstance(result, GeisterjagdResult)
    assert result.converged is True
    assert result.manifest is not None
    assert result.contraction_factor is not None
    assert result.contraction_factor < 1.0
    assert np.allclose(result.manifest, x_star, atol=1e-6)
    assert result.final_distance is not None
    assert result.final_distance < 1e-5


def test_geisterjagd_nothing_when_not_contraction():
    """||A||_2 ≥ 1 ⇒ Nothing: converged=False, manifest=None (kein Fake-Fixpunkt)."""
    A = 1.5 * np.eye(2)
    c = np.array([0.0, 0.0])
    result = Geisterjagdmodul().hunt([1.0, 1.0], A, c)
    assert result.converged is False
    assert result.manifest is None
    assert result.contraction_factor is None
    assert result.steps == 0


def test_geisterjagd_geometric_error_bound_via_k20():
    """Fehler ||y − x*|| ≤ q^k · ||z − x*|| (K20-Geometrie, nach iterate)."""
    A = 0.3 * np.eye(3)
    c = np.array([1.0, 2.0, 3.0])
    z = np.array([9.0, -4.0, 0.5])
    seed = BanachContractionSeed(A, c)
    x_star = seed.fixpoint()
    d0 = float(np.linalg.norm(z - x_star))
    result = Geisterjagdmodul().hunt(z, A, c, tol=1e-10)
    assert result.converged is True
    assert result.final_distance is not None
    # Bound: final ≤ q^steps * d0 (mit kleinem numerischem Spielraum)
    q = seed.q
    steps = result.steps
    bound = (q**steps) * d0 if steps > 0 else d0
    assert result.final_distance <= bound + 1e-8


def test_geisterjagd_hunt_multiple_all_or_nothing_consistent():
    """Mehrere Startgeister: alle konvergieren oder alle Nothing (gleiche (A,c))."""
    A_ok = 0.4 * np.eye(2)
    c = np.array([0.5, -0.5])
    zs = [[3.0, 0.0], [0.0, 3.0], [-2.0, 1.0]]
    results = Geisterjagdmodul().hunt_multiple(zs, A_ok, c)
    assert len(results) == 3
    assert all(r.converged for r in results)
    # gemeinsamer Fixpunkt
    fps = [tuple(np.round(r.manifest, 6)) for r in results]  # type: ignore[arg-type]
    assert len(set(fps)) == 1

    A_bad = 2.0 * np.eye(2)
    results_bad = Geisterjagdmodul().hunt_multiple(zs, A_bad, c)
    assert all(not r.converged and r.manifest is None for r in results_bad)


# ---------------------------------------------------------------------------
# Agentenstruktur — Code-Honesty (Prosa ≠ class)
# ---------------------------------------------------------------------------


def test_agent_structure_honesty_map_is_consistent():
    """Prosa-Rollen bleiben MODELL; existierende Klassen sind im Tree greifbar."""
    root = Path(__file__).resolve().parents[1]
    impact = root / "docs" / "dissertation" / "AGENT_STRUCTURE_AND_IMPACT_v13.md"
    legacy = root / "docs" / "DETAILED_AGENT_STRUCTURE_v1.md"
    assert impact.is_file(), "Impact/Honesty-Map muss existieren"
    assert legacy.is_file(), "Legacy Agent-Struktur-Doc muss erhalten bleiben (BCG)"

    text = impact.read_text(encoding="utf-8")
    # Muss echte Code-Anker nennen
    for token in (
        "BaseAgent",
        "AgentRegistry",
        "DynamicOrchestrationCoreModule",
        "HarmonisierungsCoreModule",
        "Geisterjagdmodul",
        "BanachContractionSeed",
    ):
        assert token in text, f"fehlender Anker: {token}"

    # Prosa-Rollen als nicht-implementiert markiert
    assert "KEINE class" in text or "keine class" in text.lower()

    # Reale Code-Anker als Dateien (kein Package-Import — vermeidet env-Deps)
    assert (root / "src" / "normal_os" / "agents" / "base.py").is_file()
    assert (root / "src" / "normal_os" / "agents" / "registry.py").is_file()
    base_src = (root / "src" / "normal_os" / "agents" / "base.py").read_text(
        encoding="utf-8", errors="ignore"
    )
    reg_src = (root / "src" / "normal_os" / "agents" / "registry.py").read_text(
        encoding="utf-8", errors="ignore"
    )
    assert "class BaseAgent" in base_src
    assert "class AgentRegistry" in reg_src

    # Prosa-Labels sind KEINE Klassen im Python-Tree (Stichprobe)
    prose_labels = ("Masterinstanz", "ManifestGuardian", "ASRAgent", "MemeVisualIdentityAgent")
    py_blobs: list[str] = []
    for p in root.rglob("*.py"):
        s = str(p)
        if any(x in s for x in (".git", "__pycache__", "archiv", "legacy_sources", "tests")):
            continue
        try:
            py_blobs.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            continue
    joined = "\n".join(py_blobs)
    for label in prose_labels:
        assert f"class {label}" not in joined, f"unerwartete class {label}"
