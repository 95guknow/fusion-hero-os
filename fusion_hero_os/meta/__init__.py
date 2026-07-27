"""Meta-neural network vertical slice for Fusion Hero OS.

This package implements a privacy-by-default, consent-scoped "meta-neural
network": a typed, versioned multidimensional property graph plus a working
memory space, a Hebbian association memory, coupling/convergence analysis and
a bridge to the existing classical QUBO/Ising solver.

Honesty note
------------
"Meta-neural" / "fractal" here is a *graph architecture metaphor*. Nothing in
this package is a claim of consciousness, sentience or biological cognition,
and the QUBO bridge is *classical* optimisation (simulated annealing) — it is
not quantum computing.

Everything is local-only and fails closed: no ingest, association update,
optimisation or persistence happens without an explicit, unexpired consent
grant naming a purpose. Private personal data is resolved only through the
:class:`~fusion_hero_os.meta.vault.VaultResolver` boundary and never enters
graph snapshots or logs.
"""

from __future__ import annotations

__all__ = [
    "consent",
    "vault",
    "graph",
    "working_memory",
    "hebbian",
    "coupling",
    "qubo_bridge",
    "pipeline",
    "schemas",
]

SCHEMA_VERSION = "1.0.0"
