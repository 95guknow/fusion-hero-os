# -*- coding: utf-8 -*-
"""mining_qubo.py — Profit-Switching als QUBO für den HEROIC-Core-Annealer.

==============================================================================
WAS DIESES MODUL IST (und was NICHT)
==============================================================================
Es optimiert **nicht** den Hash-Vorgang selbst. Kryptografisches Mining ist eine
Brute-Force-Suche über eine preimage-resistente Hashfunktion — sie hat keine
ausnutzbare Energielandschaft und ist damit kein QUBO-Problem. Würde QUBO eine
Nonce schneller finden, wäre die Hashfunktion gebrochen, nicht "optimiert".

Was sehr wohl ein QUBO-Problem ist: die **Betriebsentscheidung**, welche GPU zu
welcher Stunde welchen Algorithmus (Coin) schürft, um den Netto-Ertrag
(Revenue − Stromkosten) über das ganze Rig zu maximieren. Genau das formuliert
dieses Modul als ``x^T Q x`` und übergibt es an den vorhandenen
Parallel-Annealer (engine/mainframe.py).

Datenfluss:
    Excavator JSON-RPC  ->  Hashraten/Leistung je (GPU, Algo)
        |                       (ExcavatorConnector, DRY-RUN per Default)
        v
    estimate_profit_matrix      ->  profit[g, a]  in  €/Stunde
        |
        v
    build_profit_switching_qubo ->  Q  (One-Hot-Constraint + Profit)
        |
        v
    parallel_anneal (mainframe) ->  binäre Lösung x
        |
        v
    decode_assignment           ->  {GPU g: Algo a}

SICHERHEITS-LEITSATZ (wie methodology/connectors.py):
Der ExcavatorConnector öffnet ohne explizit injizierten Client **kein** Netzwerk
und schreibt **keine** Steuerbefehle. Ohne Client liefert jede Operation einen
strukturierten DRY-RUN-Plan. Import ist seiteneffektfrei.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

# Connector-Basisklasse aus dem Methodik-Paket wiederverwenden (gleicher Hausstil:
# Dry-Run per Default, Delegation nur bei injiziertem Client).
try:  # pragma: no cover - defensiv, im Projekt vorhanden
    from fusion_hero_os.methodology.connectors import BaseConnector
except ImportError:  # pragma: no cover - Fallback, falls als Skript aus engine/ gestartet
    BaseConnector = object  # type: ignore[assignment, misc]

# Deterministischer Modul-RNG im Hausstil (für Demo-Mockdaten).
rng = np.random.default_rng(7)


# ---------------------------------------------------------------------------
# 1) DATENQUELLE: Excavator JSON-RPC (DRY-RUN per Default)
# ---------------------------------------------------------------------------
class ExcavatorConnector(BaseConnector):  # type: ignore[misc]
    """Lese-Wrapper für die NiceHash-Excavator-JSON-RPC-Schnittstelle.

    Excavator stellt eine lokale JSON-RPC-API bereit (per Default
    ``127.0.0.1:4067``, newline-terminierte JSON-Nachrichten). Relevante
    Lese-Methoden:

        * ``info``                    — Version, Uptime
        * ``worker.list``             — laufende Worker je GPU/Algorithmus
        * ``algorithm.list``          — geladene Algorithmen + Speeds
        * ``algorithm.print.speeds``  — aktuelle Hashraten

    Steuer-Methoden (``worker.add``, ``worker.reset``, ``algorithm.add``) sind
    bewusst **nicht** als Bequem-Methoden ausgeführt: dieses Modul trifft die
    Switching-*Entscheidung*, führt sie aber nicht eigenmächtig aus. Ohne
    injizierten Client ist alles DRY-RUN.

    Der injizierte ``client`` muss lediglich ein Callable / Objekt sein, das
    ``call(method: str, params: list) -> dict`` beherrscht (z. B. ein dünner
    Socket-Wrapper). Diese Klasse öffnet selbst keinen Socket.
    """

    skill_module = "ExcavatorMiningConnector"

    def _call(self, method: str, params: Optional[Sequence[Any]] = None) -> Dict[str, Any]:
        """Plant/führt einen JSON-RPC-Lesecall aus (DRY-RUN ohne Client)."""
        params = list(params or [])
        if not getattr(self, "available", False):
            return {
                "connector": getattr(self, "name", "ExcavatorConnector"),
                "action": method,
                "args": {"params": params},
                "would_execute": False,
                "available": False,
                "note": (
                    "DRY-RUN: kein Excavator-Client injiziert — es wurde nichts "
                    "abgefragt. Injiziere einen Client mit call(method, params)."
                ),
            }
        client = self._client  # type: ignore[attr-defined]
        result = client.call(method, params) if hasattr(client, "call") else client(method, params)
        return {
            "connector": getattr(self, "name", "ExcavatorConnector"),
            "action": method,
            "args": {"params": params},
            "would_execute": True,
            "available": True,
            "result": result,
        }

    def info(self) -> Dict[str, Any]:
        """Versions-/Uptime-Info (Lese-Operation)."""
        return self._call("info")

    def speeds(self) -> Dict[str, Any]:
        """Aktuelle Hashraten je Worker/Algorithmus (Lese-Operation)."""
        return self._call("algorithm.print.speeds")

    def workers(self) -> Dict[str, Any]:
        """Laufende Worker je GPU (Lese-Operation)."""
        return self._call("worker.list")


# ---------------------------------------------------------------------------
# 2) ÖKONOMIE: Hashraten -> Profit-Matrix (€/Stunde je GPU×Algorithmus)
# ---------------------------------------------------------------------------
def estimate_profit_matrix(
    hashrate: np.ndarray,
    power_watt: np.ndarray,
    revenue_per_hash: Sequence[float],
    energy_cost_per_kwh: float = 0.30,
) -> np.ndarray:
    """Berechnet die Netto-Profit-Matrix ``profit[g, a]`` in €/Stunde.

    profit = Revenue − Stromkosten
           = hashrate[g,a] * revenue_per_hash[a]  −  power[g,a]/1000 * energy_cost

    Parameter
    ---------
    hashrate:        (G, A) Hashrate je GPU g auf Algorithmus a (z. B. H/s, MH/s —
                     Einheit muss zu ``revenue_per_hash`` passen).
    power_watt:      (G, A) Leistungsaufnahme je GPU g auf Algorithmus a (Watt).
    revenue_per_hash:(A,) erwarteter Ertrag je Hash-Einheit und Stunde für
                     Algorithmus a (€ pro Hashrate-Einheit pro Stunde). Bildet
                     Kurs × Block-Reward / Netz-Difficulty ab — die volatile
                     Größe, die du extern (Pool-API/WhatToMine) füllst.
    energy_cost_per_kwh: Strompreis in €/kWh.

    Rückgabe: (G, A) ``float64`` Netto-Profit pro Stunde.
    """
    hashrate = np.asarray(hashrate, dtype=np.float64)
    power_watt = np.asarray(power_watt, dtype=np.float64)
    rev = np.asarray(revenue_per_hash, dtype=np.float64)[None, :]  # (1, A) -> Broadcast
    revenue = hashrate * rev
    energy_cost = (power_watt / 1000.0) * energy_cost_per_kwh
    return revenue - energy_cost


# ---------------------------------------------------------------------------
# 3) QUBO-FORMULIERUNG: One-Hot-Zuweisung GPU -> Algorithmus
# ---------------------------------------------------------------------------
def build_profit_switching_qubo(
    profit: np.ndarray,
    penalty: Optional[float] = None,
) -> Tuple[np.ndarray, float]:
    """Baut die QUBO-Matrix Q für das Profit-Switching.

    Variablen: ``x[g, a] = 1`` <=> GPU g schürft Algorithmus a. Geflacht auf
    Index ``k = g*A + a`` (n = G*A binäre Variablen).

    Zielfunktion (Minimierung von ``x^T Q x``):

        minimiere   − Σ_{g,a} profit[g,a]·x[g,a]              (Profit maximieren)
        u.d.N.      Σ_a x[g,a] = 1   ∀g                       (genau ein Algo/GPU)

    Die Gleichheits-Nebenbedingung wird als Straf-Term eingebettet:

        P · (Σ_a x[g,a] − 1)²  =  P·[ −Σ_a x_a + 2·Σ_{a<b} x_a x_b + 1 ]

    Daraus folgt für die symmetrische Matrix (Energie = Σ_ij Q_ij x_i x_j):
        * Diagonale:        Q[k,k]   = −profit[g,a] − P
        * Gleiche GPU:      Q[k,k']  = Q[k',k] = +P   (a ≠ a')
    Der konstante ``+P``-Term je GPU verschiebt nur das Energie-Offset und ist
    für das argmin irrelevant.

    Penalty-Wahl: P muss größer sein als der größte mögliche Profit-Gewinn aus
    einer Constraint-Verletzung — der ist durch die Profit-*Spannweite*
    (max − min) beschränkt, NICHT durch ``max|profit|``. Zu hohe P erzeugen
    außerdem Energiebarrieren, die der Single-Bit-Flip-SA schwer überwindet
    (ein Algo-Wechsel = zwei Flips über einen bestraften Zwischenzustand).
    Empirisch robust über viele Rigs: ``P = (max − min) · 1.5``.

    Rückgabe: ``(Q, penalty)`` mit Q als (n, n) ``float64`` und dem genutzten P.
    """
    profit = np.asarray(profit, dtype=np.float64)
    if profit.ndim != 2:
        raise ValueError("profit muss die Form (G, A) haben.")
    G, A = profit.shape
    n = G * A

    if penalty is None:
        spread = float(np.max(profit) - np.min(profit))
        penalty = spread * 1.5 if spread > 0 else 1.0
    P = float(penalty)

    Q = np.zeros((n, n), dtype=np.float64)
    for g in range(G):
        for a in range(A):
            k = g * A + a
            # Linearteil: Profit (negativ, da Minimierung) + One-Hot-Linearterm (−P)
            Q[k, k] = -profit[g, a] - P
            # Quadratischer One-Hot-Term: +P auf jedes Paar derselben GPU
            for b in range(a + 1, A):
                kk = g * A + b
                Q[k, kk] = P
                Q[kk, k] = P
    return Q, P


def decode_assignment(solution: np.ndarray, G: int, A: int) -> Dict[int, int]:
    """Dekodiert die binäre Lösung zu ``{GPU g: Algorithmus a}``.

    Robust gegen leichte Constraint-Verletzungen: pro GPU wird der Algorithmus
    mit dem höchsten "Stimmen"-Wert gewählt (argmax über die A Bits). Bei exakt
    erfüllter One-Hot-Constraint ist das genau das gesetzte Bit.
    """
    x = np.asarray(solution, dtype=np.int64).reshape(G, A)
    return {g: int(np.argmax(x[g])) for g in range(G)}


def assignment_profit(assignment: Dict[int, int], profit: np.ndarray) -> float:
    """Summe des Netto-Profits (€/h) für eine konkrete GPU->Algo-Zuweisung."""
    profit = np.asarray(profit, dtype=np.float64)
    return float(sum(profit[g, a] for g, a in assignment.items()))


# ---------------------------------------------------------------------------
# 4) END-TO-END: Profit-Matrix -> Annealer -> Zuweisung
# ---------------------------------------------------------------------------
def optimize_switching(
    profit: np.ndarray,
    steps: int = 15000,
    T0: float = 1.5,
    n_restarts: Optional[int] = 32,
    penalty: Optional[float] = None,
) -> Dict[str, Any]:
    """Löst das Profit-Switching mit dem Parallel-Annealer aus mainframe.py.

    Greift auf ``parallel_anneal`` zu (Multi-Start-SA über alle Kerne) und gibt
    die dekodierte Zuweisung plus Kennzahlen zurück. Vergleicht zusätzlich mit
    der gierigen Baseline (je GPU lokal der beste Algo), um den Mehrwert der
    globalen Optimierung sichtbar zu machen — bei reinen Diagonal-Profiten ohne
    geteilte Ressourcen sind beide gleich; sobald du gekoppelte Constraints
    (Strom-/Temperatur-Budget) ergänzt, zieht der Annealer davon.
    """
    from fusion_hero_os.engine.mainframe import parallel_anneal

    profit = np.asarray(profit, dtype=np.float64)
    G, A = profit.shape
    Q, P = build_profit_switching_qubo(profit, penalty=penalty)

    out = parallel_anneal(Q, steps=steps, T0=T0, n_restarts=n_restarts)
    assignment = decode_assignment(out["solution"], G, A)

    # Gierige Baseline: je GPU der lokal beste Algorithmus.
    greedy = {g: int(np.argmax(profit[g])) for g in range(G)}

    return {
        "assignment": assignment,
        "profit_per_hour": assignment_profit(assignment, profit),
        "greedy_assignment": greedy,
        "greedy_profit_per_hour": assignment_profit(greedy, profit),
        "penalty": P,
        "energy": out["energy"],
        "runtime_seconds": out["runtime_seconds"],
        "n_restarts": out["n_restarts"],
    }


# ---------------------------------------------------------------------------
# 5) DEMO (nur bei direktem Aufruf; keine Netzwerk-/Schreib-Seiteneffekte)
# ---------------------------------------------------------------------------
def _mock_rig(G: int = 8, A: int = 4) -> Tuple[np.ndarray, np.ndarray, List[float]]:
    """Erzeugt ein deterministisches Mock-Rig (8 GPUs × 4 Algorithmen).

    Steht stellvertretend für das, was der ExcavatorConnector im LIVE-Betrieb
    liefern würde. Bewusst heterogen: nicht jede GPU ist auf jedem Algo gleich
    gut — dadurch ist die Zuweisung nicht trivial.
    """
    base = rng.uniform(20.0, 60.0, size=(G, A))        # Hashrate (MH/s, fiktiv)
    affinity = rng.uniform(0.7, 1.3, size=(G, A))      # GPU-spezifische Eignung je Algo
    hashrate = base * affinity
    power = rng.uniform(120.0, 260.0, size=(G, A))     # Watt je (GPU, Algo)
    revenue_per_hash = [0.012, 0.018, 0.009, 0.015]    # €/(MH/s)/h je Algo (volatil!)
    return hashrate, power, revenue_per_hash[:A]


def _demo() -> None:
    G, A = 8, 4
    algo_names = ["DaggerHashimoto", "KawPow", "Autolykos", "ZelHash"][:A]

    # 1) Datenquelle ist im Default DRY-RUN — nichts wird abgefragt.
    exc = ExcavatorConnector()
    print("=== Excavator-Connector (DRY-RUN, kein Client) ===")
    print(exc.speeds()["note"])

    # 2) Mock-Telemetrie (stünde im LIVE-Fall aus exc.speeds()/exc.workers()).
    hashrate, power, rev = _mock_rig(G, A)
    profit = estimate_profit_matrix(hashrate, power, rev, energy_cost_per_kwh=0.30)

    print("\n=== Profit-Matrix (€/h, Zeilen=GPU, Spalten=Algo) ===")
    print("           " + "  ".join(f"{nm[:8]:>8}" for nm in algo_names))
    for g in range(G):
        print(f"GPU{g}:  " + "  ".join(f"{profit[g, a]:8.3f}" for a in range(A)))

    # 3) QUBO bauen + mit dem Parallel-Annealer lösen.
    res = optimize_switching(profit, steps=6000)

    print("\n=== Optimierte Zuweisung (Annealer) ===")
    for g, a in res["assignment"].items():
        print(f"  GPU{g} -> {algo_names[a]}  ({profit[g, a]:+.3f} €/h)")
    print(f"\nGesamt-Profit (Annealer): {res['profit_per_hour']:.3f} €/h")
    print(f"Gesamt-Profit (Greedy):   {res['greedy_profit_per_hour']:.3f} €/h")
    print(f"QUBO-Energie:             {res['energy']:.3f}")
    print(f"Laufzeit:                 {res['runtime_seconds'] * 1000:.1f} ms "
          f"({res['n_restarts']} Restarts)")
    print(f"Penalty P:                {res['penalty']:.3f}")


if __name__ == "__main__":
    _demo()
