# -*- coding: utf-8 -*-
"""Regressionstests: MasterSeed-Syncs optimieren sich IMMER gegenseitig.

Beweist die Satz-Nachbedingungen aus fusion_hero_os/core/masterseed_sync.py
per Property-Sweep und verankert Fail-Closed + Identitaetserhalt im CI-Gate.
"""
import numpy as np
import pytest

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
from fusion_hero_os.core.masterseed_sync import (
    SyncState,
    identity_preservation_score,
    mutual_sync,
    sync_evolutions,
)

rng = np.random.default_rng(77)


def _state(fitness: float) -> SyncState:
    return SyncState(seed=MasterSeed(), elite_payload={"f": fitness}, elite_fitness=fitness)


def test_mutual_sync_never_degrades_either_side_property_sweep():
    """SATZ-Sweep: 300 Zufallspaare — beide Seiten monoton, Ergebnis = max."""
    for _ in range(300):
        fa, fb = float(rng.uniform(-50, 50)), float(rng.uniform(-50, 50))
        a2, b2 = mutual_sync(_state(fa), _state(fb))
        assert a2.elite_fitness >= fa
        assert b2.elite_fitness >= fb
        assert a2.elite_fitness == b2.elite_fitness == max(fa, fb)


def test_mutual_sync_preserves_identity_hashes():
    a, b = _state(1.0), _state(2.0)
    ha, hb = a.state_hash(), b.state_hash()
    a2, b2 = mutual_sync(a, b)
    assert a2.state_hash() == ha and b2.state_hash() == hb
    assert identity_preservation_score(a2) == 100.0
    assert identity_preservation_score(b2) == 100.0


def test_mutual_sync_fail_closed_on_tampered_side():
    a, b = _state(1.0), _state(2.0)
    # Seite B manipulieren: falscher Seed hinter unveraendertem Anspruch
    b.seed = MasterSeed(criticality_target=0.99)
    ok_hash_of_default = MasterSeed().state_hash()
    assert b.seed.verify_integrity(ok_hash_of_default) is False  # Manipulation erkennbar

    class Lying(SyncState):
        def state_hash(self):  # gibt bewusst den falschen (Default-)Hash aus
            return ok_hash_of_default

    lying = Lying(seed=b.seed, elite_payload=b.elite_payload, elite_fitness=b.elite_fitness)
    with pytest.raises(ValueError, match="FAIL_CLOSED"):
        mutual_sync(a, lying)


def test_identity_score_drops_below_100_after_tamper():
    a, b = _state(1.0), _state(2.0)
    a2, _ = mutual_sync(a, b)
    # nachtraegliche Identitaets-Manipulation: Log-Hash passt nicht mehr
    a2.seed = MasterSeed(criticality_target=0.5)
    assert identity_preservation_score(a2) < 100.0


def test_sync_evolutions_mutually_improves_both_sides():
    """Realer Solver-Sync: Elitismus garantiert Monotonie auf BEIDEN Seiten."""
    from fusion_hero_os.engine.mainframe import GenerationalEvolutionProtocolCoreModule

    evo_a = GenerationalEvolutionProtocolCoreModule(
        n=10, mu=3, lam=3, seed=1,
        init_genome={"steps": 300, "T0": 0.5, "n_restarts": 1})
    evo_b = GenerationalEvolutionProtocolCoreModule(
        n=10, mu=3, lam=3, seed=2,
        init_genome={"steps": 5000, "T0": 2.0, "n_restarts": 2})
    evo_a.run_generation()
    evo_b.run_generation()

    report = sync_evolutions(evo_a, evo_b)
    assert report["mutual_improvement"] is True
    assert report["a"]["post"] >= report["a"]["pre"]
    assert report["b"]["post"] >= report["b"]["pre"]
