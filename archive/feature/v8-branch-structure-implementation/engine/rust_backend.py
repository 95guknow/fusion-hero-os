# -*- coding: utf-8 -*-
"""Optionales Rust-Backend für den QUBO-Solver (PyO3-Extension `rust_engine`).

Lädt das kompilierte Rust-Modul. Ist es nicht gebaut, bleibt ``AVAILABLE = False``
und der Aufrufer fällt auf den numba-Kernel zurück (import-sicher, kein Crash).

Bauen (sobald eine Rust-Toolchain vorhanden ist):
    pip install maturin
    cd rust_engine_crate && maturin build --release   # erzeugt ein Wheel (kein venv nötig)
    pip install target/wheels/rust_engine-*.whl

Die Matrix wird als numpy-Array (Buffer-Protokoll) übergeben, NICHT als Python-Liste —
das Entpacken jedes Elements als eigenes PyObject wäre für große n der Flaschenhals.
"""
from __future__ import annotations

import os
import time

import numpy as np

try:  # pragma: no cover - reine Verfügbarkeitsprüfung
    import rust_engine as _re

    # Nur als verfügbar werten, wenn es WIRKLICH die kompilierte Extension ist
    # (ein gleichnamiger Quellordner würde sonst als Namespace-Package „verfügbar" wirken).
    AVAILABLE = hasattr(_re, "parallel_anneal")
except Exception:  # noqa: BLE001
    _re = None
    AVAILABLE = False


def parallel_anneal_rust(Q, steps=8000, T0=2.0, n_restarts=None, n_samples=60, base_seed=0):
    """Multi-Start SA über das Rust-Backend; liefert denselben Dict-Vertrag wie
    engine.mainframe.parallel_anneal (Schlüssel: solution, energy, energies,
    best_restart, traces, trace_steps, n_restarts, workers, runtime_seconds, backend)."""
    if not AVAILABLE:
        raise RuntimeError("Rust-Backend nicht verfügbar — Modul 'rust_engine' ist nicht gebaut.")

    Q = np.ascontiguousarray(np.asarray(Q, dtype=np.float64))
    n = int(Q.shape[0])
    if n_restarts is None:
        n_restarts = os.cpu_count() or 4

    t0 = time.time()
    best_x, best_e, energies, best_restart, traces = _re.parallel_anneal(
        Q, n, int(steps), float(T0),
        int(n_restarts), int(n_samples), int(base_seed),
    )
    runtime = time.time() - t0

    trace_steps = np.linspace(0, max(steps - 1, 0), n_samples).astype(np.int64).tolist()
    return {
        "solution": np.asarray(best_x, dtype=np.int64),
        "energy": float(best_e),
        "energies": [float(e) for e in energies],
        "best_restart": int(best_restart),
        "traces": [[float(v) for v in tr] for tr in traces],
        "trace_steps": trace_steps,
        "n_restarts": int(n_restarts),
        "workers": os.cpu_count() or 1,
        "runtime_seconds": runtime,
        "backend": "rust",
    }
