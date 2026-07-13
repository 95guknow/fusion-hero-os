# -*- coding: utf-8 -*-
"""Halbverband-Eigenschaften des MasterSeed-Sync-Merges (Claim SYNC-SEMILATTICE).

Formalisierung aus der Gemini-Synthese v9 (docs/01_vision/GEMINI_SYNTHESIS_v9_REVIEW.md):
Der Sync-Operator S ist ein Join-Halbverband auf der Elite-Fitness — der Merge
(hier: max-Auswahl in mutual_sync) muss kommutativ, assoziativ und idempotent
sein. Das ist der CvRDT-Kern, der spaeter die Gossip-Konvergenz traegt.

EHRLICHER GELTUNGSBEREICH: Bewiesen wird hier der PAARWEISE Join. Die
N-Knoten-Gossip-Aussage (O(log n)-Konvergenz) ist damit NICHT bewiesen und
bleibt in proof_registry.yaml als OFFEN gefuehrt, bis ein Gossip-Modul mit
eigenem Property-Test existiert.
"""
import numpy as np

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
from fusion_hero_os.core.masterseed_sync import SyncState, mutual_sync

rng = np.random.default_rng(1234)


def _state(fitness: float) -> SyncState:
    return SyncState(seed=MasterSeed(), elite_payload={"f": fitness}, elite_fitness=fitness)


def test_join_is_commutative_property_sweep():
    """S(A,B) und S(B,A) liefern dieselbe Merge-Fitness (200 Zufallspaare)."""
    for _ in range(200):
        fa, fb = float(rng.uniform(-100, 100)), float(rng.uniform(-100, 100))
        a1, b1 = mutual_sync(_state(fa), _state(fb))
        a2, b2 = mutual_sync(_state(fb), _state(fa))
        assert a1.elite_fitness == b1.elite_fitness == a2.elite_fitness == b2.elite_fitness


def test_join_is_idempotent():
    """S(A,A) = A: Merge mit sich selbst veraendert nichts (keine Duplikat-Effekte)."""
    for f in (-3.5, 0.0, 7.25):
        a1, a2 = mutual_sync(_state(f), _state(f))
        assert a1.elite_fitness == a2.elite_fitness == f


def test_join_is_associative_via_pairwise_chaining():
    """(A⊔B)⊔C == A⊔(B⊔C): jede Paarungs-Reihenfolge endet beim globalen Max.

    Genau diese Ordnungsunabhaengigkeit ist die Eigenschaft, die ein spaeteres
    Gossip-Netz braucht: egal welche Paare zuerst reden, das Ergebnis ist gleich.
    """
    for _ in range(100):
        fs = [float(x) for x in rng.uniform(-100, 100, size=3)]
        target = max(fs)

        # Reihenfolge 1: (A,B) dann (AB, C)
        a, b, c = _state(fs[0]), _state(fs[1]), _state(fs[2])
        a, b = mutual_sync(a, b)
        a, c = mutual_sync(a, c)
        left = a.elite_fitness

        # Reihenfolge 2: (B,C) dann (A, BC)
        a2, b2, c2 = _state(fs[0]), _state(fs[1]), _state(fs[2])
        b2, c2 = mutual_sync(b2, c2)
        a2, b2 = mutual_sync(a2, b2)
        right = a2.elite_fitness

        assert left == right == target


def test_join_payload_follows_the_winning_fitness():
    """Der Merge uebernimmt das Payload der Gewinner-Elite, nicht nur die Zahl."""
    a, b = _state(1.0), _state(2.0)
    a2, b2 = mutual_sync(a, b)
    assert a2.elite_payload == b2.elite_payload == {"f": 2.0}
