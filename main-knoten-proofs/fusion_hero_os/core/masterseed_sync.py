# -*- coding: utf-8 -*-
"""MasterSeed-Sync — gegenseitige Optimierung als BEWIESENER Satz.

Anforderung (User-Direktive 2026-07-04): "Syncs mit anderen MasterSeeds
sollen sich immer gegenseitig optimieren." Dieses Modul macht daraus einen
Satz mit Implementierung statt einer Behauptung:

SATZ (Monotonie der gegenseitigen Synchronisation):
    Seien A und B Sync-Zustaende mit Elite-Fitness f_A, f_B und intakter
    Seed-Integritaet. Nach mutual_sync(A, B) gilt:
        f_A' = f_B' = max(f_A, f_B),
    insbesondere f_A' >= f_A und f_B' >= f_B — BEIDE Seiten werden besser
    oder bleiben gleich, keine Seite wird jemals schlechter. Zusaetzlich
    bleibt die Identitaet beider Instanzen erhalten (seed_state_hash
    unveraendert): Wissen wird geteilt, Identitaet nicht ueberschrieben.

BEWEIS: Der Sync ersetzt auf jeder Seite die Elite durch die Elite mit der
hoeheren Fitness (max-Auswahl, Elitismus). max(f_A, f_B) >= f_A und
max(f_A, f_B) >= f_B per Definition von max. Die Seed-Felder werden im
gesamten Ablauf nie geschrieben, also bleibt state_hash beider Seiten
identisch. QED.

FAIL-CLOSED: Ist die Integritaet einer Seite verletzt (state_hash passt
nicht zum Seed), wird der Sync mit ValueError verweigert — ein manipulierter
Partner kann den anderen nicht "optimieren".

Fuer Evolutions-Instanzen (GenerationalEvolutionProtocolCoreModule) gilt der
Satz ueber den Elitismus: sync_evolutions() bewertet das Fremd-Genom auf dem
EIGENEN Ziel-QUBO, nimmt es in die Population auf und behaelt die besten mu.
Dadurch ist best_fitness beider Seiten nach dem Sync monoton nicht-fallend —
unabhaengig davon, ob das Fremd-Genom auf dem eigenen Ziel gut oder schlecht
ist (schlechte Kandidaten fallen durch die Selektion, koennen die Elite aber
nie verdraengen).

Identity-Preservation-Score (messbar definiert, ersetzt die frueher
unbelegte Selbstauskunft "Score: 100"): Anteil der protokollierten
Operationen, nach denen der Seed-Hash unveraendert war, skaliert auf 0..100.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, List, Tuple

from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed


@dataclass
class SyncState:
    """Sync-faehiger Zustand einer MasterSeed-Instanz.

    seed bleibt bei jedem Sync unveraendert (Identitaet); elite_payload/
    elite_fitness sind das teilbare Wissen (z. B. bestes Solver-Genom).
    """
    seed: MasterSeed
    elite_payload: Any
    elite_fitness: float
    sync_log: List[dict] = field(default_factory=list)

    def state_hash(self) -> str:
        return self.seed.state_hash()


def mutual_sync(a: SyncState, b: SyncState) -> Tuple[SyncState, SyncState]:
    """Gegenseitig optimierender Sync (Satz oben; fail-closed bei Manipulation).

    Rueckgabe: (a', b') mit elite_fitness' = max(f_a, f_b) auf BEIDEN Seiten
    und unveraenderten Seeds. Wirft ValueError, wenn eine Seite die
    Integritaetspruefung nicht besteht.
    """
    for name, s in (("A", a), ("B", b)):
        if not s.seed.verify_integrity(s.state_hash()):
            raise ValueError(f"FAIL_CLOSED: Sync verweigert — Integritaet von Seite {name} verletzt.")
    if not (isinstance(a.elite_fitness, (int, float)) and isinstance(b.elite_fitness, (int, float))):
        raise ValueError("FAIL_CLOSED: Elite-Fitness beider Seiten muss numerisch sein.")

    if a.elite_fitness >= b.elite_fitness:
        best_payload, best_fitness, source = a.elite_payload, float(a.elite_fitness), "A"
    else:
        best_payload, best_fitness, source = b.elite_payload, float(b.elite_fitness), "B"

    entry = {"event": "mutual_sync", "adopted_from": source, "fitness": best_fitness}
    a2 = replace(a, elite_payload=best_payload, elite_fitness=best_fitness,
                 sync_log=a.sync_log + [dict(entry, pre_fitness=float(a.elite_fitness),
                                             seed_hash=a.state_hash())])
    b2 = replace(b, elite_payload=best_payload, elite_fitness=best_fitness,
                 sync_log=b.sync_log + [dict(entry, pre_fitness=float(b.elite_fitness),
                                             seed_hash=b.state_hash())])

    # Nachbedingungen des Satzes werden zur Laufzeit erzwungen (Defense-in-Depth):
    assert a2.elite_fitness >= a.elite_fitness and b2.elite_fitness >= b.elite_fitness
    assert a2.state_hash() == a.state_hash() and b2.state_hash() == b.state_hash()
    return a2, b2


def sync_evolutions(evo_a, evo_b) -> dict:
    """Gegenseitig optimierender Sync zweier Evolutions-Instanzen (Elitismus).

    Jede Seite bewertet das beste Genom der anderen auf ihrem EIGENEN
    Ziel-QUBO, nimmt es als Kandidaten in die Population auf und behaelt die
    besten mu. Garantie (Elitismus, siehe Modul-Docstring): best_fitness
    beider Seiten ist danach >= vorher.
    """
    for evo in (evo_a, evo_b):
        if evo.population is None:
            evo._init_population()

    pre_a, pre_b = evo_a.best_fitness, evo_b.best_fitness
    genome_a = dict(evo_a.population[0][0])
    genome_b = dict(evo_b.population[0][0])

    for evo, foreign in ((evo_a, genome_b), (evo_b, genome_a)):
        candidate = evo._clip(dict(foreign))
        evo.population.append((candidate, evo._fitness(candidate)))
        evo.population.sort(key=lambda gf: gf[1], reverse=True)
        evo.population = evo.population[: evo.mu]
        evo.best_genome, evo.best_fitness = evo.population[0]

    assert evo_a.best_fitness >= pre_a and evo_b.best_fitness >= pre_b, \
        "Elitismus verletzt — Sync haette nie verschlechtern duerfen"
    return {
        "a": {"pre": pre_a, "post": evo_a.best_fitness},
        "b": {"pre": pre_b, "post": evo_b.best_fitness},
        "mutual_improvement": (evo_a.best_fitness >= pre_a) and (evo_b.best_fitness >= pre_b),
    }


def identity_preservation_score(state: SyncState) -> float:
    """Messbar definierter Identity-Preservation-Score in [0, 100].

    100 genau dann, wenn JEDER protokollierte Sync den Seed-Hash unveraendert
    gelassen hat (Vergleich gegen den aktuellen state_hash). Ersetzt die
    fruehere unbelegte Selbstauskunft "Identity Preservation Score: 100"
    durch eine nachrechenbare Groesse.
    """
    if not state.sync_log:
        return 100.0  # keine Operationen -> Identitaet trivialerweise erhalten
    current = state.state_hash()
    preserved = sum(1 for e in state.sync_log if e.get("seed_hash") == current)
    return 100.0 * preserved / len(state.sync_log)
