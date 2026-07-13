# -*- coding: utf-8 -*-
"""
entwicklungsquant_live.py — Live-Verdrahtung der realen Knoten an den Bus
=========================================================================
Meldet die ECHTEN Knoten dieser Session am entwicklungsquant_bus an (und wieder
ab). Statt der Demo-Reaktionen (Magnitude × fixes Gewicht) lesen die Live-Handler
REALE (read-only) Zustände der Knoten und leiten daraus die Quanten-Magnitude ab.

Konvergenz bleibt garantiert: jede emittierte Magnitude ist auf
`eingehend × Kopplung × (0.5 + 0.5·signal) ≤ eingehend × Kopplung < eingehend`
gedeckelt — das reale Signal moduliert NUR innerhalb der Kontraktions-Schranke.
So können reale Zustände das Netz mitentwickeln, ohne die Banach-Konvergenz zu
brechen.

Ehrlich:
  * Die Signale sind READ-ONLY (kein Schreiben in reale Stores; nur Zählungen wie
    pending-Tasks, subagent_count, Faden-Anzahl, CPU-Last).
  * Import jedes realen Knotens ist defensiv (try/except); fehlt einer, nimmt der
    Handler ein neutrales Fallback-Signal (0.5) — der Knoten bleibt angemeldet,
    das Netz bleibt konsistent.
  * an-/abmelden = bus.register(..., live=True) / bus.deregister(name).

Aufruf:  python entwicklungsquant_live.py    # Live-Demo: anmelden -> Fixpunkt -> abmelden
"""
from __future__ import annotations

import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent
_DASH = _CORE.parent / "Dashboard"
for _p in (_CORE, _DASH):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from entwicklungsquant_bus import EntwicklungsquantBus  # noqa: E402

LIVE_COUPLING = 0.5


def _safe(fn, default: float = 0.5) -> float:
    try:
        v = float(fn())
        return max(0.0, min(1.0, v))
    except Exception:
        return default


# --- reale, READ-ONLY Signale (0..1) ---------------------------------------- #
def sig_scheduler() -> float:
    from automation_scheduler_node import get_node
    return min(1.0, len(get_node().pending()) / 10.0)


def sig_context() -> float:
    from conversation_context_core import get_context
    return min(1.0, get_context().status().get("subagent_count", 0) / 12.0)


def sig_faden() -> float:
    from faden_store import get_faden_store
    return min(1.0, len(get_faden_store()._threads) / 50.0)


def sig_cache() -> float:
    return 0.5  # qubo-cache ist zustandslos (pro Problem instanziiert)


def sig_resource() -> float:
    try:
        import psutil
        return psutil.cpu_percent(interval=0.05) / 100.0
    except Exception:
        return 0.5


def resource_pressure_magnitude() -> float:
    """Anfangs-Impuls aus realer CPU-Last (4..12)."""
    return 4.0 + 8.0 * _safe(sig_resource, 0.5)


def _make_handler(name, rules, coupling, signal_fn):
    def handler(bus, q):
        outs = rules.get(q.quant_type)
        if not outs:
            return
        sig = _safe(signal_fn)
        # gedeckelt: ≤ eingehend × coupling < eingehend  -> Kontraktion bleibt
        mag = q.magnitude * coupling * (0.5 + 0.5 * sig)
        for (etype, target) in outs:
            bus.emit(name, target, etype, mag, layer=q.layer,
                     payload={"via": q.quant_id, "node": name, "sig": round(sig, 3)})
    return handler


# Reaktionsregeln der realen Knoten: {trigger_type: [(emit_type, target), ...]}
_LIVE = {
    "resource_coupler": ({"resource_pressure": [("cost_update", "automation_scheduler")]}, sig_resource),
    "automation_scheduler": ({
        "resource_pressure": [("plan_change", "conversation_context"), ("plan_change", "qubo_cache")],
        "cost_update": [("plan_change", "conversation_context")],
    }, sig_scheduler),
    "conversation_context": ({
        "plan_change": [("strength_update", "faden_store")],
        "tier_change": [("strength_update", "automation_scheduler")],
    }, sig_context),
    "qubo_cache": ({"plan_change": [("cache_hit", "automation_scheduler")]}, sig_cache),
    "faden_store": ({"strength_update": [("tier_change", "conversation_context")]}, sig_faden),
}


def wire_live(bus: EntwicklungsquantBus, coupling: float = LIVE_COUPLING):
    """Meldet alle realen Knoten am Bus an (mit Live-Handlern)."""
    for name, (rules, sfn) in _LIVE.items():
        # Reaktionen NUR für die Kanten-/Spektralradius-Metrik (Handler führt real aus).
        reactions = [(trig, etype, target, coupling * 0.75)
                     for trig, outs in rules.items() for (etype, target) in outs]
        bus.register(name, reactions=reactions, handler=_make_handler(name, rules, coupling, sfn), live=True)
    return bus.registered()


def unwire(bus: EntwicklungsquantBus, name: str) -> bool:
    return bus.deregister(name)


# ==================================================================
if __name__ == "__main__":
    import json

    print("=" * 74)
    print("  LIVE-Verdrahtung: reale Knoten am entwicklungsquant_bus")
    print("=" * 74)

    bus = EntwicklungsquantBus(quant_size=0.25, min_quant=0.25)
    registered = wire_live(bus)
    print(f"\n[ANMELDEN] Live-Knoten: {registered}")
    conn = bus.connectivity()
    print(f"[KONNEKTIVITÄT] Kanten={conn['kanten']}  Spektralradius={conn['spektralradius']}  "
          f"Kontraktion={conn['kontraktion']}")

    mag = resource_pressure_magnitude()
    print(f"\n[ANSTOSS] resource_pressure aus realer CPU-Last -> Magnitude {round(mag, 3)}")
    bus.emit("resource_coupler", "*", "resource_pressure", magnitude=mag, layer=3)
    res = bus.run_until_fixpoint()
    print(f"[KO-ENTWICKLUNG] Fixpunkt={res['fixpunkt_erreicht']} nach {res['ticks']} Ticks, "
          f"Energie={res['entwicklungs_energie_gesamt']}, Quanten={res['quanten_total']}")
    print(f"  Entwicklung je realem Knoten: {json.dumps(res['entwicklung_je_knoten'], ensure_ascii=False)}")

    # ABMELDEN eines Knotens -> Netz adaptiert
    print("\n[ABMELDEN] faden_store abmelden ...")
    unwire(bus, "faden_store")
    bus.reset()  # Metriken für den sauberen 2. Lauf zurücksetzen
    bus2_registered = bus.registered()
    bus.emit("resource_coupler", "*", "resource_pressure", magnitude=mag, layer=3)
    res2 = bus.run_until_fixpoint()
    print(f"  Verbleibende Knoten: {bus2_registered}")
    print(f"  Ko-Entwicklung ohne faden_store: {json.dumps(res2['entwicklung_je_knoten'], ensure_ascii=False)}")
    print(f"  -> faden_store nicht mehr beteiligt: {'faden_store' not in res2['entwicklung_je_knoten']}")
    print("=" * 74)
