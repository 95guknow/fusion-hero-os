#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests für fusion_hero_node — HT-parallele Fusion (offline, ohne LLM/Netz)."""
import os
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "core"))
os.environ["FUSION_CREATIVE_OFFLINE"] = "1"  # kein Backend-Probe/Preflight

import creative_problem_solving as cps  # noqa: E402
import fusion_hero_node as fhn  # noqa: E402

PROBLEM = (
    "Der lokale Llama-Agent liefert bei mehrstufigen Aufgaben inkonsistente "
    "Zwischenergebnisse, weil Kontext zwischen Schritten verloren geht."
)


def test_capability_snapshot_shape():
    caps = fhn.capability_snapshot()
    for key in ("hyperthreading", "resource_workflow", "agent_backend_router"):
        assert key in caps
        assert "available" in caps[key]
    print("test_capability_snapshot_shape: PASS")


def test_resolve_workers_bounded_by_ceiling():
    r = fhn.resolve_workers(n_tasks=7, task_weight="medium")
    assert r["workers"] >= 1
    assert r["workers"] <= r["ceiling"]
    assert r["ceiling"] <= 7  # nie mehr Worker als Tasks
    assert isinstance(r["reasons"], list) and r["reasons"]
    print("test_resolve_workers_bounded_by_ceiling: PASS")


def test_resolve_workers_never_exceeds_ht_over_subscription():
    # HT liefert ggf. 86 "virtuelle" Worker; bei 3 Tasks dürfen es nie mehr als 3 sein
    r = fhn.resolve_workers(n_tasks=3)
    assert r["workers"] <= 3
    print("test_resolve_workers_never_exceeds_ht_over_subscription: PASS")


def test_resolve_workers_override():
    r = fhn.resolve_workers(n_tasks=7, override=2)
    assert r["workers"] == 2 and r["mode"] == "override"
    # Override wird auf Task-Zahl gedeckelt
    r2 = fhn.resolve_workers(n_tasks=3, override=99)
    assert r2["workers"] == 3
    print("test_resolve_workers_override: PASS")


def test_resolve_workers_min_one():
    r = fhn.resolve_workers(n_tasks=0)
    assert r["workers"] >= 1
    print("test_resolve_workers_min_one: PASS")


def test_parallel_generate_covers_all_strategies():
    def backend(prompt, role):
        return f"Antwort {role}: {prompt[:30]}"

    out = fhn.parallel_generate(PROBLEM, backend=backend, worker_override=4)
    cands = out["candidates"]
    assert len(cands) == len(cps.STRATEGIES)
    # Reihenfolge stabil = ursprüngliche Strategie-Reihenfolge
    assert [c["strategy"] for c in cands] == [s.key for s in cps.STRATEGIES]
    assert out["workers"] == 4
    assert out["parallel_effective"] is True  # injiziertes Backend gilt als latenzgebunden
    print("test_parallel_generate_covers_all_strategies: PASS")


def test_parallel_generate_actually_runs_concurrently():
    """Mit einem künstlich langsamen Backend muss parallel schneller sein als seriell."""
    def slow_backend(prompt, role):
        time.sleep(0.05)
        return "ok"

    t_par = time.perf_counter()
    out = fhn.parallel_generate(PROBLEM, backend=slow_backend, worker_override=7)
    par_ms = (time.perf_counter() - t_par) * 1000

    t_ser = time.perf_counter()
    fhn.parallel_generate(PROBLEM, backend=slow_backend, worker_override=1)
    ser_ms = (time.perf_counter() - t_ser) * 1000

    assert out["workers"] == 7
    # 7 Strategien × 50ms: seriell ~350ms, parallel ~50-100ms -> klar schneller
    assert par_ms < ser_ms * 0.6, f"parallel {par_ms:.0f}ms nicht < 60% von seriell {ser_ms:.0f}ms"
    print(f"test_parallel_generate_actually_runs_concurrently: PASS (par={par_ms:.0f} ser={ser_ms:.0f})")


def test_parallel_generate_threads_used():
    """Belegt, dass mehr als ein Worker-Thread tatsächlich arbeitet."""
    seen = set()
    lock = threading.Lock()

    def backend(prompt, role):
        time.sleep(0.02)
        with lock:
            seen.add(threading.get_ident())
        return "ok"

    fhn.parallel_generate(PROBLEM, backend=backend, worker_override=5)
    assert len(seen) >= 2, f"nur {len(seen)} Thread(s) genutzt"
    print(f"test_parallel_generate_threads_used: PASS ({len(seen)} Threads)")


def test_parallel_generate_backend_error_isolated():
    def boom(prompt, role):
        raise RuntimeError("kaputt")

    out = fhn.parallel_generate(PROBLEM, backend=boom, worker_override=3)
    assert len(out["candidates"]) == len(cps.STRATEGIES)
    assert all("[backend-error]" in c["response"] for c in out["candidates"])
    assert all(c["backend"] == "injected-error" for c in out["candidates"])
    print("test_parallel_generate_backend_error_isolated: PASS")


def test_fuse_offline_end_to_end():
    res = fhn.fuse(PROBLEM, with_critique=True)
    assert res["ok"] is True
    assert res["offline"] is True  # Preflight scheitert -> Stub
    assert res["parallel_effective"] is False  # Stub profitiert nicht von Threads
    assert res["critique"] is None  # offline übersprungen
    assert len(res["portfolio"]) == cps._PORTFOLIO_SIZE
    assert "capabilities" in res and "hyperthreading" in res["capabilities"]
    for c in res["portfolio"]:
        assert "[offline-stub]" in c["response"]
    print("test_fuse_offline_end_to_end: PASS")


def test_fuse_with_injected_backend_is_online():
    def backend(prompt, role):
        if role == "anti_agent":
            return "Kritik: schwächste Annahme ist X."
        return f"Loesung {abs(hash(prompt)) % 997} gegen Kontextverlust im Agent"

    res = fhn.fuse(PROBLEM, backend=backend, worker_override=4, seed=1)
    assert res["ok"] is True
    assert res["offline"] is False
    assert res["parallel_effective"] is True
    assert res["critique"] is not None and res["critique"]["ok"] is True
    assert res["workers"] == 4
    print("test_fuse_with_injected_backend_is_online: PASS")


def test_fuse_empty_problem():
    assert fhn.fuse("")["ok"] is False
    print("test_fuse_empty_problem: PASS")


def test_fuse_deterministic_portfolio():
    def backend(prompt, role):
        return f"Loesung {abs(hash(prompt)) % 997} gegen Kontextverlust im Agent"

    a = fhn.fuse(PROBLEM, backend=backend, worker_override=3, seed=42, with_critique=False)
    b = fhn.fuse(PROBLEM, backend=backend, worker_override=3, seed=42, with_critique=False)
    assert [c["strategy"] for c in a["portfolio"]] == [c["strategy"] for c in b["portfolio"]]
    print("test_fuse_deterministic_portfolio: PASS")


def test_status():
    st = fhn.status()
    assert st["module"] == "fusion_hero_node"
    assert "capabilities" in st and st["strategies"] == len(cps.STRATEGIES)
    print("test_status: PASS")


if __name__ == "__main__":
    test_capability_snapshot_shape()
    test_resolve_workers_bounded_by_ceiling()
    test_resolve_workers_never_exceeds_ht_over_subscription()
    test_resolve_workers_override()
    test_resolve_workers_min_one()
    test_parallel_generate_covers_all_strategies()
    test_parallel_generate_actually_runs_concurrently()
    test_parallel_generate_threads_used()
    test_parallel_generate_backend_error_isolated()
    test_fuse_offline_end_to_end()
    test_fuse_with_injected_backend_is_online()
    test_fuse_empty_problem()
    test_fuse_deterministic_portfolio()
    test_status()
    print("ALLE TESTS PASS")
