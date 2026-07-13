# -*- coding: utf-8 -*-
"""
Qdrant-Lösungs-Cache für qb_qubo.py — Warm-Start via Ähnlichkeitssuche.

Idee: Statt jede QUBO-Instanz Q kalt zu lösen (simulated_annealing ab
Zufalls-Startvektor), wird Q als Vektor (oberes Dreieck inkl. Diagonale)
in Qdrant abgelegt. Eine neue, geometrisch nahe Instanz Q' übernimmt die
gespeicherte Lösung x als Startpunkt für local_search() (Energie-Delta-
Refinement, O(n) pro Bit-Flip) statt komplett neu zu starten.

Lokal/in-memory (kein Server, keine Persistenz) — QdrantClient(location=":memory:").
Jede Problemgröße n bekommt ihre eigene Collection ("qubo_cache_n{n}"), da
Qdrant-Collections eine feste Vektordimension verlangen und QUBO-Instanzen
unterschiedlicher Größe nicht direkt vergleichbar sind.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from qb_qubo import simulated_annealing, local_search  # echte Solver (kanonische Version)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    _QDRANT_AVAILABLE = True
    _IMPORT_ERROR = ""
except Exception as e:  # pragma: no cover - nur ohne qdrant-client
    QdrantClient = None  # type: ignore
    _QDRANT_AVAILABLE = False
    _IMPORT_ERROR = str(e)


def is_available() -> bool:
    return _QDRANT_AVAILABLE


def encode_Q(Q: np.ndarray) -> list:
    """Flacht die symmetrische QUBO-Matrix auf das obere Dreieck (inkl. Diagonale) ab.
    Eindeutige, redundanzfreie Repräsentation, da Q stets symmetrisch ist."""
    n = Q.shape[0]
    iu = np.triu_indices(n)
    return Q[iu].astype(np.float64).tolist()


class QuboSolutionCache:
    """Ähnlichkeitsbasierter Lösungs-Cache für qb_qubo-Instanzen (lokal, in-memory).

    distance_threshold: maximale euklidische Distanz zwischen den oberen-Dreieck-
    Vektoren zweier Q-Matrizen, bis zu der eine gecachte Lösung als Warm-Start
    übernommen wird. Muss zur Problemskala passen (z.B. make_Q(scale=1.0) ~ N(0,1)
    je Eintrag) — kein universeller Default, sondern bewusst ein Parameter.
    """

    def __init__(self, distance_threshold: float = 1.5, location: str = ":memory:"):
        if not _QDRANT_AVAILABLE:
            raise RuntimeError(f"qdrant-client nicht verfügbar: {_IMPORT_ERROR}")
        self.client = QdrantClient(location=location)
        self.distance_threshold = distance_threshold
        self._known_collections: set = set()
        self._next_id: Dict[int, int] = {}

    def _collection_for(self, n: int) -> str:
        name = f"qubo_cache_n{n}"
        if name not in self._known_collections:
            if not self.client.collection_exists(name):
                dim = n * (n + 1) // 2
                self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=dim, distance=Distance.EUCLID),
                )
            self._known_collections.add(name)
            self._next_id.setdefault(n, 0)
        return name

    def lookup(self, Q: np.ndarray) -> Optional[Dict[str, Any]]:
        """Sucht die nächste bekannte Q-Instanz. None, wenn Cache leer oder zu weit weg."""
        n = Q.shape[0]
        collection = self._collection_for(n)
        result = self.client.query_points(
            collection_name=collection, query=encode_Q(Q), limit=1, with_payload=True
        )
        if not result.points:
            return None
        best = result.points[0]
        if best.score > self.distance_threshold:
            return None
        return {
            "distance": best.score,
            "x": np.array(best.payload["x"], dtype=np.int64),
            "energy": best.payload["energy"],
            "point_id": best.id,
        }

    def store(self, Q: np.ndarray, x: np.ndarray, e: float) -> None:
        n = Q.shape[0]
        collection = self._collection_for(n)
        point_id = self._next_id[n]
        self._next_id[n] += 1
        self.client.upsert(
            collection_name=collection,
            points=[PointStruct(
                id=point_id,
                vector=encode_Q(Q),
                payload={"x": np.asarray(x).tolist(), "energy": float(e)},
            )],
        )

    def solve_with_cache(
        self, Q: np.ndarray, sa_steps: int = 4000, sa_T0: float = 2.0, refine_iters: int = 200
    ) -> Tuple[np.ndarray, float, Dict[str, Any]]:
        """Löst Q; nutzt bei Cache-Treffer einen Warm-Start statt Kaltstart.

        Treffer: x0 = gecachte Lösung einer nahen Instanz -> local_search(Q, x0).
        Fehltreffer: simulated_annealing(Q) ab Zufallsstart (teuer, vollständig).
        Beide Pfade speichern ihr Ergebnis im Cache für künftige Treffer.
        """
        hit = self.lookup(Q)
        if hit is not None:
            x, e = local_search(Q, hit["x"], iters=refine_iters)
            meta = {
                "cache_hit": True,
                "distance": hit["distance"],
                "source_point_id": hit["point_id"],
                "prior_energy": hit["energy"],
            }
        else:
            x, e = simulated_annealing(Q, steps=sa_steps, T0=sa_T0)
            meta = {"cache_hit": False}
        self.store(Q, x, e)
        return x, e, meta


# ==================================================================
if __name__ == "__main__":
    import time as _time
    from qb_qubo import make_Q

    print("=" * 60)
    print("  Qdrant-Lösungs-Cache für qb_qubo  —  Demo (lokal, in-memory)")
    print("=" * 60)

    if not is_available():
        print(f"qdrant-client nicht verfügbar: {_IMPORT_ERROR}")
        sys.exit(1)

    cache = QuboSolutionCache(distance_threshold=2.5)
    n = 14
    rng_demo = np.random.default_rng(42)

    # [1] Kaltstart: erste Instanz, kein Cache-Treffer möglich
    Q1 = make_Q(n, scale=1.0)
    t0 = _time.perf_counter()
    x1, e1, meta1 = cache.solve_with_cache(Q1, sa_steps=4000)
    t1 = (_time.perf_counter() - t0) * 1000
    print(f"\n[1] Instanz A (kalt):                  {t1:7.2f} ms  E={e1:9.4f}  meta={meta1}")

    # [2] Leicht gestörte Instanz (Q1 + kleines Rauschen) -> sollte Cache-Treffer sein
    noise = rng_demo.normal(0, 0.05, size=Q1.shape)
    noise = (noise + noise.T) / 2.0
    Q2 = Q1 + noise
    t0 = _time.perf_counter()
    x2, e2, meta2 = cache.solve_with_cache(Q2, refine_iters=200)
    t2 = (_time.perf_counter() - t0) * 1000
    print(f"[2] Instanz B (A + kleines Rauschen):   {t2:7.2f} ms  E={e2:9.4f}  meta={meta2}")

    # [3] Referenz: Instanz B komplett kalt lösen (ohne Cache) zum Vergleich
    t0 = _time.perf_counter()
    _, e2_cold = simulated_annealing(Q2, steps=4000)
    t2_cold = (_time.perf_counter() - t0) * 1000
    print(f"[3] Instanz B (Referenz, kalt, kein Cache): {t2_cold:7.2f} ms  E={e2_cold:9.4f}")

    # [4] Unabhängige, neue Instanz -> sollte wieder Cache-Fehltreffer sein
    Q3 = make_Q(n, scale=1.0)
    t0 = _time.perf_counter()
    x3, e3, meta3 = cache.solve_with_cache(Q3, sa_steps=4000)
    t3 = (_time.perf_counter() - t0) * 1000
    print(f"[4] Instanz C (unabhängig, neu):        {t3:7.2f} ms  E={e3:9.4f}  meta={meta3}")

    if t2 > 0:
        print(f"\nWarm-Start (B via Cache) vs. Kaltstart (B Referenz): {t2_cold / t2:.1f}x schneller")
        print(f"Hinweis: lokale Suche (Warm-Start) findet ein lokales Minimum nahe x1,")
        print(f"         nicht notwendigerweise das globale Optimum von Q2.")
    print("=" * 60)
