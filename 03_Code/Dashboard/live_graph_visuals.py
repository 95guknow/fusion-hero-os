# -*- coding: utf-8 -*-
"""Live GraphAPI snapshot for landing-page dual visualization.

Heroic + formal-mathematical graphs from real connectors, frameworks,
inject slots, quanta — code honesty: dry-run vs live-ready labeled.
"""
from __future__ import annotations

import math
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]
DASH = Path(__file__).resolve().parent


def _safe_import_graph() -> Dict[str, Any]:
    try:
        from fusion_hero_os.connectors.graph_api import status_all

        return status_all()
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200], "connectors": {}}


def _frameworks() -> Dict[str, Any]:
    try:
        from llm_frameworks import connector_status, list_frameworks

        return {
            "names": list_frameworks(),
            "status": connector_status(),
        }
    except Exception as exc:
        return {"names": [], "error": str(exc)[:160]}


def _inject() -> Dict[str, Any]:
    try:
        from kernel.inject.inject_host import get_inject_host

        return get_inject_host().status()
    except Exception as exc:
        return {"active_count": 0, "error": str(exc)[:160]}


def _quanta() -> List[Dict[str, Any]]:
    path = ROOT / "docs" / "architecture" / "quantenvektoren.yaml"
    if not path.is_file():
        return []
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        q = data.get("quanta") or {}
        out = []
        for i, (qid, meta) in enumerate(q.items()):
            if not isinstance(meta, dict):
                continue
            lang = meta.get("language") or {}
            out.append(
                {
                    "id": qid,
                    "name": meta.get("name") or qid,
                    "language": (lang.get("primary") if isinstance(lang, dict) else None)
                    or "python3",
                    "phase": meta.get("phase"),
                    "index": i,
                }
            )
        return out
    except Exception:
        return []


def build_live_graph_snapshot() -> Dict[str, Any]:
    """Nodes + edges for dual visual modes."""
    graph = _safe_import_graph()
    fws = _frameworks()
    inj = _inject()
    quanta = _quanta()
    connectors = graph.get("connectors") or {}
    if not isinstance(connectors, dict):
        connectors = {}

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

    # Core hub
    nodes.append(
        {
            "id": "hub",
            "label": "GraphAPI Hub",
            "kind": "hub",
            "group": "core",
            "live": bool(graph.get("fusion_graph_live")),
            "weight": 1.4,
        }
    )
    nodes.append(
        {
            "id": "mainframe",
            "label": "Mainframe :8000",
            "kind": "surface",
            "group": "core",
            "live": True,
            "weight": 1.2,
        }
    )
    edges.append({"source": "mainframe", "target": "hub", "kind": "control", "w": 1.0})

    # Connectors (GraphAPI arts)
    live_n = 0
    token_n = 0
    for cid, meta in connectors.items():
        if not isinstance(meta, dict):
            continue
        mode = str(meta.get("mode") or "DRY-RUN")
        if mode == "LIVE_READY":
            live_n += 1
        if meta.get("token_present"):
            token_n += 1
        nid = f"c:{cid}"
        nodes.append(
            {
                "id": nid,
                "label": cid,
                "kind": "connector",
                "group": "graph",
                "skill": meta.get("skill_module"),
                "mode": mode,
                "live": mode == "LIVE_READY",
                "weight": 0.9 if mode == "LIVE_READY" else 0.55,
            }
        )
        edges.append(
            {
                "source": "hub",
                "target": nid,
                "kind": "connector",
                "w": 0.9 if mode == "LIVE_READY" else 0.4,
                "mode": mode,
            }
        )

    # LLM frameworks
    for name in fws.get("names") or []:
        nid = f"fw:{name}"
        nodes.append(
            {
                "id": nid,
                "label": str(name),
                "kind": "framework",
                "group": "intelligence",
                "live": True,
                "weight": 0.85,
            }
        )
        edges.append({"source": "hub", "target": nid, "kind": "framework", "w": 0.7})

    # Inject slots / quanta
    for q in quanta:
        nid = f"q:{q['id']}"
        nodes.append(
            {
                "id": nid,
                "label": q.get("name") or q["id"],
                "kind": "quantum",
                "group": "quantum",
                "language": q.get("language"),
                "live": True,
                "weight": 1.0,
            }
        )
        edges.append({"source": "mainframe", "target": nid, "kind": "quantum", "w": 0.65})

    for s in inj.get("slots") or []:
        if not isinstance(s, dict):
            continue
        qid = s.get("quantum_id")
        sid = f"inj:{s.get('name') or qid}"
        nodes.append(
            {
                "id": sid,
                "label": s.get("name") or f"slot{qid}",
                "kind": "inject",
                "group": "kernel",
                "live": bool(s.get("active")),
                "weight": 0.75,
            }
        )
        edges.append({"source": "mainframe", "target": sid, "kind": "inject", "w": 0.5})

    # Layout seeds (circle + rings) for clients
    layout = _layout_nodes(nodes)

    t = time.time()
    return {
        "ok": True,
        "ts": t,
        "platform": os.getenv("FUSION_PLATFORM_VERSION") or "13.0.0",
        "graph_api": {
            "fusion_graph_live": graph.get("fusion_graph_live"),
            "policy": graph.get("policy"),
            "connector_count": len(connectors),
            "live_ready": live_n,
            "token_present": token_n,
            "dry_or_missing": max(0, len(connectors) - live_n),
        },
        "frameworks": {
            "count": len(fws.get("names") or []),
            "names": fws.get("names") or [],
        },
        "inject": {
            "active_count": inj.get("active_count", 0),
            "language_primary": inj.get("language_primary"),
            "epoch": inj.get("epoch"),
        },
        "quanta_count": len(quanta),
        "nodes": nodes,
        "edges": edges,
        "layout": layout,
        "modes": {
            "heroic": {
                "title": "Heroisch — was passiert",
                "palette": ["#00d4aa", "#f59e0b", "#7c3aed", "#ef4444", "#22d3ee"],
                "webm": "/static/visuals/live_graph_heroic.webm",
            },
            "formal": {
                "title": "Formalmathematisch — was passiert",
                "palette": ["#0f172a", "#334155", "#0ea5e9", "#64748b", "#e2e8f0"],
                "webm": "/static/visuals/live_graph_formal.webm",
            },
        },
        "geltung": "live_snapshot=Satz for structure; connector LIVE only if token+FUSION_GRAPH_LIVE",
    }


def _layout_nodes(nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Deterministic polar layout by group."""
    groups: Dict[str, List[str]] = {}
    for n in nodes:
        g = str(n.get("group") or "other")
        groups.setdefault(g, []).append(n["id"])

    radii = {
        "core": 0.12,
        "graph": 0.42,
        "intelligence": 0.55,
        "quantum": 0.68,
        "kernel": 0.82,
        "other": 0.9,
    }
    layout: Dict[str, Dict[str, float]] = {}
    for g, ids in groups.items():
        r = radii.get(g, 0.75)
        n = max(len(ids), 1)
        for i, nid in enumerate(ids):
            ang = (2 * math.pi * i / n) - math.pi / 2
            if g == "core" and len(ids) <= 2:
                layout[nid] = {"x": 0.5 + (i - 0.5) * 0.12, "y": 0.5}
            else:
                layout[nid] = {
                    "x": 0.5 + r * 0.42 * math.cos(ang),
                    "y": 0.5 + r * 0.42 * math.sin(ang),
                }
    return layout


def render_webm_pair(out_dir: Path | None = None, frames: int = 48, fps: int = 12) -> Dict[str, Any]:
    """Render heroic + formal webm loops from current snapshot (Pillow + ffmpeg)."""
    out_dir = out_dir or (DASH / "static" / "visuals")
    out_dir.mkdir(parents=True, exist_ok=True)
    snap = build_live_graph_snapshot()
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        return {"ok": False, "error": f"Pillow required: {exc}"}

    w, h = 960, 540
    results = {}

    def _font(size: int):
        for p in (
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        ):
            if Path(p).is_file():
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    font = _font(16)
    font_sm = _font(12)
    font_lg = _font(22)

    layout = snap.get("layout") or {}
    nodes = snap.get("nodes") or []
    edges = snap.get("edges") or []

    def xy(nid: str, t: float, mode: str) -> Tuple[float, float]:
        base = layout.get(nid) or {"x": 0.5, "y": 0.5}
        # gentle orbit for live feel
        phase = hash(nid) % 1000 / 1000.0 * math.pi * 2
        amp = 0.012 if mode == "formal" else 0.02
        return (
            base["x"] + amp * math.cos(t * 2 + phase),
            base["y"] + amp * math.sin(t * 2 + phase),
        )

    def draw_frame(mode: str, fi: int) -> Image.Image:
        t = fi / max(frames, 1) * math.pi * 2
        if mode == "heroic":
            bg = (8, 8, 14)
            edge_c = (0, 212, 170, 90)
            hub_c = (245, 158, 11)
            text_c = (226, 232, 240)
            accent = (124, 58, 237)
            live_c = (0, 212, 170)
            dry_c = (100, 116, 139)
        else:
            bg = (248, 250, 252)
            edge_c = (14, 165, 233, 100)
            hub_c = (15, 23, 42)
            text_c = (15, 23, 42)
            accent = (2, 132, 199)
            live_c = (2, 132, 199)
            dry_c = (148, 163, 184)

        img = Image.new("RGB", (w, h), bg)
        dr = ImageDraw.Draw(img, "RGBA")

        # formal math grid / heroic glow field
        if mode == "formal":
            for gx in range(0, w, 40):
                dr.line([(gx, 0), (gx, h)], fill=(226, 232, 240), width=1)
            for gy in range(0, h, 40):
                dr.line([(0, gy), (w, gy)], fill=(226, 232, 240), width=1)
            # adjacency matrix hint
            dr.rectangle([w - 210, 12, w - 12, 140], outline=accent, width=1)
            dr.text((w - 200, 18), "A ∈ ℝ^{n×n}", fill=text_c, font=font_sm)
            dr.text((w - 200, 38), f"n = {len(nodes)}", fill=text_c, font=font_sm)
            dr.text((w - 200, 58), f"|E| = {len(edges)}", fill=text_c, font=font_sm)
            dr.text((w - 200, 78), "G=(V,E) live", fill=text_c, font=font_sm)
            ga = snap.get("graph_api") or {}
            dr.text(
                (w - 200, 98),
                f"live={ga.get('live_ready', 0)} dry={ga.get('dry_or_missing', 0)}",
                fill=text_c,
                font=font_sm,
            )
            # Banach contraction note
            lam = 0.74
            d0 = 1.0
            dn = d0 * (lam ** (fi % 12))
            dr.text((w - 200, 118), f"λ={lam}  dₙ≈{dn:.3f}", fill=accent, font=font_sm)
        else:
            # radial campfire glow
            cx, cy = w // 2, h // 2
            for r in range(180, 20, -20):
                alpha = max(10, 40 - r // 8)
                dr.ellipse(
                    [cx - r, cy - r, cx + r, cy + r],
                    outline=(245, 158, 11, alpha),
                )

        # edges
        for e in edges:
            s, tgt = e.get("source"), e.get("target")
            if s not in layout or tgt not in layout:
                continue
            x1, y1 = xy(s, t, mode)
            x2, y2 = xy(tgt, t, mode)
            p1 = (int(x1 * w), int(y1 * h))
            p2 = (int(x2 * w), int(y2 * h))
            col = edge_c
            if mode == "heroic" and e.get("mode") == "LIVE_READY":
                col = (0, 212, 170, 140)
            elif mode == "heroic" and e.get("kind") == "framework":
                col = (124, 58, 237, 100)
            dr.line([p1, p2], fill=col, width=2 if mode == "formal" else 2)

            # pulse along edge
            u = (math.sin(t * 3 + hash(s) % 7) + 1) / 2
            mx = int(p1[0] + (p2[0] - p1[0]) * u)
            my = int(p1[1] + (p2[1] - p1[1]) * u)
            r = 3 if mode == "formal" else 4
            dr.ellipse([mx - r, my - r, mx + r, my + r], fill=hub_c if mode == "formal" else (245, 158, 11))

        # nodes
        for n in nodes:
            nid = n["id"]
            x, y = xy(nid, t, mode)
            px, py = int(x * w), int(y * h)
            live = bool(n.get("live"))
            kind = n.get("kind")
            rad = 8 + int(6 * float(n.get("weight") or 0.5))
            if kind == "hub":
                rad = 16
                fill = hub_c
            elif kind == "connector":
                fill = live_c if live else dry_c
            elif kind == "framework":
                fill = accent
            elif kind == "quantum":
                fill = (239, 68, 68) if mode == "heroic" else (15, 23, 42)
            elif kind == "inject":
                fill = (34, 211, 238) if mode == "heroic" else (100, 116, 139)
            else:
                fill = live_c
            dr.ellipse([px - rad, py - rad, px + rad, py + rad], fill=fill, outline=text_c if mode == "formal" else None)
            label = str(n.get("label") or "")[:18]
            if kind in ("hub", "surface") or (mode == "formal" and kind == "quantum"):
                dr.text((px + rad + 3, py - 6), label, fill=text_c, font=font_sm)
            elif mode == "heroic" and kind == "connector" and live:
                dr.text((px + rad + 2, py - 5), "LIVE", fill=live_c, font=font_sm)

        # titles
        if mode == "heroic":
            title = "HEROISCH — GraphAPI · alle Künste · was passiert"
            dr.text((20, 14), title, fill=(245, 158, 11), font=font_lg)
            dr.text(
                (20, h - 36),
                f"connectors={snap['graph_api'].get('connector_count')}  "
                f"LIVE_READY={snap['graph_api'].get('live_ready')}  "
                f"frameworks={snap['frameworks'].get('count')}  "
                f"inject={snap['inject'].get('active_count')}  "
                f"quanta={snap.get('quanta_count')}",
                fill=(148, 163, 184),
                font=font_sm,
            )
            dr.text((20, h - 18), "ALTE_Frau_95g · Campfire Mesh · BIG ALPHA", fill=(0, 212, 170), font=font_sm)
        else:
            title = "FORMAL — G=(V,E) · A adjacency · contraction λ<1"
            dr.text((20, 14), title, fill=hub_c, font=font_lg)
            dr.text(
                (20, h - 36),
                f"|V|={len(nodes)}  |E|={len(edges)}  "
                f"live_ready={snap['graph_api'].get('live_ready')}  "
                f"token_present={snap['graph_api'].get('token_present')}",
                fill=(51, 65, 85),
                font=font_sm,
            )
            dr.text(
                (20, h - 18),
                "Geltung: Struktur=Satz · LIVE nur mit Token+FUSION_GRAPH_LIVE",
                fill=accent,
                font=font_sm,
            )
        return img

    import subprocess
    import tempfile
    import shutil

    for mode, name in (("heroic", "live_graph_heroic"), ("formal", "live_graph_formal")):
        tmp = Path(tempfile.mkdtemp(prefix=f"fhos_{mode}_"))
        try:
            for fi in range(frames):
                im = draw_frame(mode, fi)
                im.save(tmp / f"f_{fi:04d}.png")
            webm = out_dir / f"{name}.webm"
            # also mp4 fallback
            mp4 = out_dir / f"{name}.mp4"
            cmd = [
                "ffmpeg",
                "-y",
                "-framerate",
                str(fps),
                "-i",
                str(tmp / "f_%04d.png"),
                "-c:v",
                "libvpx-vp9",
                "-b:v",
                "1M",
                "-pix_fmt",
                "yuv420p",
                "-an",
                "-loop",
                "0",
                str(webm),
            ]
            r = subprocess.run(
                cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if r.returncode != 0:
                # fallback mp4 h264
                cmd2 = [
                    "ffmpeg",
                    "-y",
                    "-framerate",
                    str(fps),
                    "-i",
                    str(tmp / "f_%04d.png"),
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-an",
                    str(mp4),
                ]
                r2 = subprocess.run(
                    cmd2,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                results[mode] = {
                    "ok": r2.returncode == 0,
                    "path": str(mp4 if r2.returncode == 0 else webm),
                    "err": (r.stderr or r2.stderr)[-400:],
                }
            else:
                results[mode] = {"ok": True, "path": str(webm), "bytes": webm.stat().st_size}
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    return {"ok": all(v.get("ok") for v in results.values()), "outputs": results, "snapshot_meta": {
        "nodes": len(nodes),
        "edges": len(edges),
        "graph_api": snap.get("graph_api"),
    }}
