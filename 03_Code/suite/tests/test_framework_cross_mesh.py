"""Tests: Framework Kreuzvernetzung (full cross mesh)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CODE = ROOT / "03_Code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from framework_cross_mesh import (  # noqa: E402
    build_cross_mesh,
    cross_mesh_status,
    full_mesh_edges,
    route_via_mesh,
)


def test_full_mesh_edges_complete():
    edges = full_mesh_edges(["a", "b", "c"], "t")
    # 3 nodes → 3 undirected pairs → 6 directed
    assert len(edges) == 6


def test_build_cross_mesh_fully_connected():
    mesh = build_cross_mesh()
    assert mesh["counts"]["frameworks"] >= 6
    assert mesh["fully_connected_frameworks"] is True
    assert mesh["counts"]["edges"] > 100
    assert "quantizer" in [a["id"] for a in mesh["agents"]]


def test_routes_one_hop_between_frameworks():
    mesh = build_cross_mesh()
    fws = mesh["frameworks"]
    if len(fws) < 2:
        return
    r = route_via_mesh(fws[0], fws[1], mesh)
    assert r["ok"] is True
    assert r["hops"] == 1


def test_agent_triad_connected():
    r = route_via_mesh("agent", "quantizer")
    assert r["ok"] is True
    assert r["hops"] == 1


def test_cross_mesh_status_ok():
    st = cross_mesh_status()
    assert st["ok"] is True
    assert st["cross_mesh"] is True
    assert st["fully_connected_frameworks"] is True
