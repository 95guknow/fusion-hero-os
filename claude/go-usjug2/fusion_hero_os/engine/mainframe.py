# ... (bestehender Code oben bleibt)

# =====================================================================
# RUST BACKEND INTEGRATION (v9.1+)
# =====================================================================

_RUST_BACKEND = None
_RUST_AVAILABLE = False


def _load_rust_backend():
    """Versucht, das Rust-Backend zu laden. Gibt (module, available) zurück."""
    global _RUST_BACKEND, _RUST_AVAILABLE
    if _RUST_BACKEND is not None:
        return _RUST_BACKEND, _RUST_AVAILABLE

    candidates = [
        "fusion_hero_os.engine.rust_backend",
        "engine.rust_backend",
        "rust_backend",
    ]

    for name in candidates:
        try:
            mod = __import__(name, fromlist=["AVAILABLE", "parallel_anneal_rust"])
            if getattr(mod, "AVAILABLE", False):
                _RUST_BACKEND = mod
                _RUST_AVAILABLE = True
                print("[RUST] High-performance Rust backend loaded successfully.")
                return _RUST_BACKEND, True
        except Exception:
            continue

    _RUST_AVAILABLE = False
    return None, False


def get_rust_backend():
    """Public helper to access the Rust backend if available."""
    backend, available = _load_rust_backend()
    return backend if available else None


def is_rust_available() -> bool:
    _, available = _load_rust_backend()
    return available


# Ersetze die alte Rust-Import-Logik in parallel_anneal durch die neue saubere Version
# (Die Funktion parallel_anneal wird entsprechend angepasst - hier nur der relevante Teil gezeigt)

def parallel_anneal(Q, steps=8000, T0=2.0, n_restarts=None, n_samples=60,
                    base_seed=0, workers=None, backend="auto"):
    """Multi-Start Simulated Annealing mit verbesserter Rust-Integration."""

    if backend in ("rust", "auto"):
        rb, available = _load_rust_backend()
        if available and rb is not None:
            try:
                return rb.parallel_anneal_rust(
                    Q, steps=steps, T0=T0, n_restarts=n_restarts,
                    n_samples=n_samples, base_seed=base_seed
                )
            except Exception as e:
                print(f"[RUST] Backend call failed, falling back to numba: {e}")

        if backend == "rust":
            raise RuntimeError(
                "backend='rust' requested but Rust backend is not available. "
                "Build with: cd rust_engine && maturin develop --release"
            )

    # Fallback auf Numba (bestehende Implementierung)
    # ... (bestehender numba Code folgt hier)
    ...

# Optional: In QUBOIntegrationCoreModule einen sauberen Status-Report hinzufügen
def get_backend_status() -> dict:
    return {
        "rust_available": is_rust_available(),
        "numba_available": True,  # Numba ist Core-Dependency
        "active_backend": "rust" if is_rust_available() else "numba",
    }
