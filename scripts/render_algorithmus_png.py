#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rendert den Gesamtalgorithmus als hochaufloesendes, beschriftetes PNG.

Die Zahlen im Bild sind **nicht** eingetippt, sondern werden aus den echten
Reports gelesen:

* ``docs/ops/KONNEKTOR_VOLLAUTOMAT.latest.json`` — Layergroessen, Distanzen,
  Geister, Axiome
* ``docs/ops/SPRACHBINDUNG.latest.json`` — Sprachverteilung und Luecken

Damit veraltet das Bild nicht still: fehlt ein Report, sagt das Skript es,
statt Platzhalterzahlen zu malen.

Aufruf:
    python3 scripts/render_algorithmus_png.py [--dpi 200] [--out PFAD] [--svg]

PNG ist der Standard (hohe Aufloesung, ueberall darstellbar). ``--svg``
legt zusaetzlich eine Vektorfassung daneben — verlustfrei zoombar.

Geltung: Darstellung = Satz, soweit die Reports es sind (sie tragen ihre
eigene Geltungsmarke mit).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import matplotlib

matplotlib.use("Agg")  # kein Display in CI/Container
import matplotlib.patches as mpatches  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
VOLLAUTOMAT = ROOT / "docs" / "ops" / "KONNEKTOR_VOLLAUTOMAT.latest.json"
SPRACHEN = ROOT / "docs" / "ops" / "SPRACHBINDUNG.latest.json"
STANDARD_OUT = ROOT / "docs" / "architecture" / "ALGORITHMUS_GESAMT.png"

# Farbwelt: bewusst zurueckhaltend, Kontrast ueber Helligkeit statt Buntheit.
BG = "#0e1116"
FG = "#e6edf3"
DIM = "#8b949e"
LINE = "#30363d"
AKZENT = {
    "laden": "#3fb950",      # bottom-up
    "verarbeiten": "#58a6ff",  # top-down
    "ausgabe": "#d29922",    # Geister
    "sprache": "#bc8cff",    # Sprachschichtung
    "warn": "#f85149",
}

LAYER_ORDER = [
    "L6_masterseed", "L5_projektion", "L4_intent", "L3_internalisierung",
    "L2_bindung", "L1_verkoerperung", "L0_fundament",
]
LADEN_ORDER = ["L0_state", "L1_registries", "L2_connectors", "L3_links", "L4_remotes"]


def _load(path: Path) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _kasten(ax, x, y, w, h, text, *, farbe, fs=11, fett=False, alpha=0.14, ha="left"):
    ax.add_patch(mpatches.FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.006,rounding_size=0.012",
        facecolor=farbe, edgecolor=farbe, alpha=alpha, linewidth=1.6,
    ))
    tx = x + 0.012 if ha == "left" else x + w / 2
    ax.text(tx, y + h / 2, text, color=FG, fontsize=fs, va="center", ha=ha,
            fontweight="bold" if fett else "normal", linespacing=1.5)


def _pfeil(ax, x1, y1, x2, y2, farbe, lw=2.0, stil="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=stil, color=farbe, lw=lw,
                                shrinkA=2, shrinkB=2))


def _titel(ax, x, y, nummer, text, farbe):
    ax.text(x, y, nummer, color=farbe, fontsize=20, fontweight="bold", va="center")
    ax.text(x + 0.028, y, text, color=FG, fontsize=15, fontweight="bold", va="center")


def render(dpi: int, out: Path, auch_svg: bool = False) -> int:
    va = _load(VOLLAUTOMAT)
    sp = _load(SPRACHEN)

    fehlend = [p.name for p, d in ((VOLLAUTOMAT, va), (SPRACHEN, sp)) if d is None]
    if fehlend:
        print(f"[FEHLER] Report fehlt: {', '.join(fehlend)}", file=sys.stderr)
        print("  Erst erzeugen:", file=sys.stderr)
        print("    python3 -m fusion_hero_os.core.konnektor_vollautomat", file=sys.stderr)
        print("    python3 -m fusion_hero_os.core.translate_controller", file=sys.stderr)
        return 1

    lay = va["verarbeiten"]
    groessen = lay["groessen"]
    dist = lay["distanz_zum_masterseed"]
    counts = va["counts"]
    schichten = va["laden"]["schichten"]

    fig = Figure(figsize=(26, 17), facecolor=BG)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor(BG)

    # ---------------- Kopf ----------------
    ax.text(0.5, 0.972, "FUSION HERO OS — Gesamtalgorithmus", color=FG,
            fontsize=30, fontweight="bold", ha="center")
    ax.text(0.5, 0.947,
            "Erinnerungen bottom-up laden  ·  top-down verarbeiten  ·  Geister manifestiert ausgeben",
            color=DIM, fontsize=15, ha="center")
    ax.text(0.5, 0.928,
            f"Platform {va['platform_version']}  ·  Sicht: {va.get('sicht', '?')}  ·  "
            f"Modus: {va['automatisierung']['modus']}  ·  Stand {va['generated_at'][:10]}",
            color=DIM, fontsize=12, ha="center", style="italic")
    ax.plot([0.03, 0.97], [0.912, 0.912], color=LINE, lw=1.4)

    # ---------------- 1 · LADEN (bottom-up) ----------------
    c = AKZENT["laden"]
    _titel(ax, 0.035, 0.878, "1", "LADEN DER ERINNERUNGEN — bottom-up", c)
    ax.text(0.035, 0.855, "Keine Schicht wird angefasst, bevor die darunterliegende geladen ist.",
            color=DIM, fontsize=11.5)

    lh, lg = 0.036, 0.0125
    y0 = 0.815
    detail = {
        "L0_state": "Erinnerung des letzten Laufs (~/.fusion)",
        "L1_registries": f"{len(schichten['L1_registries']['sources'])} Registries gelesen",
        "L2_connectors": f"{schichten['L2_connectors']['gesamt']} Konnektoren extrahiert",
        "L3_links": f"{schichten['L3_links']['gesamt']} Links, {schichten['L3_links']['offen']} offen",
        "L4_remotes": f"{schichten['L4_remotes']['mit_health_path']} mit health_path · kein Probe",
    }
    for i, name in enumerate(LADEN_ORDER):
        y = y0 - i * (lh + lg)
        _kasten(ax, 0.035, y, 0.255, lh,
                f"{name}\n{detail[name]}", farbe=c, fs=10.5)
        if i:
            _pfeil(ax, 0.163, y + lh + 0.001, 0.163, y + lh + lg - 0.001, c, lw=2.2)
    ax.text(0.298, y0 - 2 * (lh + lg) + lh / 2, "▲\nbottom\nup", color=c, fontsize=13,
            ha="center", va="center", fontweight="bold", linespacing=1.4)

    # ---------------- 2 · VERARBEITEN (top-down) ----------------
    c = AKZENT["verarbeiten"]
    _titel(ax, 0.365, 0.878, "2", "VERARBEITEN — top-down (Gott-Layering v11)", c)
    ax.text(0.365, 0.855,
            "L6ω ↠ L0 · jede Schicht filtert ausschließlich die darüberliegende.",
            color=DIM, fontsize=11.5)

    gesamt = max(1, groessen[LAYER_ORDER[0]])
    bh, bg = 0.0335, 0.0105
    yv = 0.815
    xmitte = 0.508
    maxw = 0.265
    for i, name in enumerate(LAYER_ORDER):
        y = yv - i * (bh + bg)
        anteil = groessen[name] / gesamt
        w = max(0.075, maxw * anteil)
        x = xmitte - w / 2
        _kasten(ax, x, y, w, bh, "", farbe=c, alpha=0.16)
        ax.text(xmitte, y + bh / 2, f"{name}   n={groessen[name]}",
                color=FG, fontsize=10.5, ha="center", va="center", fontweight="bold")
        ax.text(0.655, y + bh / 2, f"d={dist[name]:.4f}", color=DIM, fontsize=10,
                ha="left", va="center", family="monospace")
        if i:
            _pfeil(ax, xmitte, y + bh + bg - 0.001, xmitte, y + bh + 0.001, c, lw=2.2)
    ax.text(0.335, yv - 3 * (bh + bg), "▼\ntop\ndown", color=c, fontsize=13,
            ha="center", va="center", fontweight="bold", linespacing=1.4)
    # Spaltenkopf tief genug, damit er nicht in die Ueberschrift von Block 3 laeuft
    ax.text(0.655, yv + bh + 0.006, "Distanz d", color=DIM, fontsize=9.5,
            family="monospace")

    # Axiome
    ya = yv - len(LAYER_ORDER) * (bh + bg) - 0.012
    ax.text(0.365, ya, "Axiome", color=FG, fontsize=12, fontweight="bold")
    for j, (k, v) in enumerate(lay["axiome"].items()):
        yy = ya - 0.024 - j * 0.021
        ok = bool(v)
        ax.text(0.368, yy, "✓" if ok else "✗",
                color=AKZENT["laden"] if ok else AKZENT["warn"],
                fontsize=13, fontweight="bold", va="center")
        ax.text(0.388, yy, k.replace("_", " "), color=DIM, fontsize=10.5, va="center")

    # ---------------- 3 · AUSGABE (Geister) ----------------
    c = AKZENT["ausgabe"]
    _titel(ax, 0.715, 0.878, "3", "AUSGABE — Geister manifestiert", c)
    ax.text(0.715, 0.855,
            "Wer beim Abstieg herausfällt, wird sichtbar. manifest=False gibt es nicht.",
            color=DIM, fontsize=11.5)

    klassen: Dict[str, int] = {}
    for g in va["geister"]:
        klassen[g["klasse"]] = klassen.get(g["klasse"], 0) + 1
    yg = 0.815
    gh = 0.0295
    maxn = max(klassen.values()) if klassen else 1
    # Label links, Balken in eigener Spur, Zahl in fester Spalte — sonst
    # ueberdeckt ein langer Klassenname den Balken und die Zahl wandert.
    x_label, x_bar, x_num, bar_max = 0.715, 0.858, 0.966, 0.072
    for i, (k, n) in enumerate(sorted(klassen.items(), key=lambda kv: -kv[1])):
        y = yg - i * (gh + 0.008)
        w = max(0.008, bar_max * (n / maxn))
        _kasten(ax, x_bar, y + gh * 0.22, w, gh * 0.56, "", farbe=c, alpha=0.30)
        ax.text(x_label, y + gh / 2, k, color=FG, fontsize=10.5, va="center")
        ax.text(x_num, y + gh / 2, str(n), color=c, fontsize=11.5,
                va="center", ha="right", fontweight="bold", family="monospace")

    yz = yg - len(klassen) * (gh + 0.008) - 0.014
    _kasten(ax, 0.715, yz - 0.052, 0.245, 0.052,
            f"{counts['geister']} Geister  ·  {counts['geister_latent']} latent\n"
            f"{counts['geister_echte_befunde']} echte Befunde",
            farbe=c, fs=12, fett=True, alpha=0.10)

    # ---------------- 4 · Dry-Run-Tor ----------------
    c4 = AKZENT["warn"]
    yt = 0.372
    _kasten(ax, 0.715, yt, 0.245, 0.062,
            "TOR:  live  =  Flag  ∧  Token\n"
            f"sonst would_execute = false   ({va['automatisierung']['ausgefuehrt']} ausgeführt)",
            farbe=c4, fs=11.5, alpha=0.10)

    # ---------------- 5 · Sprachschichtung ----------------
    c = AKZENT["sprache"]
    ax.plot([0.03, 0.97], [0.335, 0.335], color=LINE, lw=1.4)
    _titel(ax, 0.035, 0.302, "4", "SPRACHSCHICHTUNG — je Modul die optimale Sprache", c)
    ax.text(0.035, 0.279,
            "Kern maschinennah, aufbauende Elemente in der Sprache mit der niedrigsten Schwelle.",
            color=DIM, fontsize=11.5)

    ist = sp["counts"]["ist"]
    soll = sp["counts"]["soll"]
    ebenen = [
        ("asm", "Wahrheit der Hooks — Slot-Tabelle, Dispatch, Boot", "gelinkt, nicht importiert"),
        ("c", "dünner freestanding Glue — console, smp", "link"),
        ("rust", "rechenheiße Kerne (Signal: Code braucht numba/@jit)", "pyo3_cdylib"),
        ("python", "Steuerung, Konnektoren, Ops — niedrigste Schwelle", "nativ"),
        ("js", "öffentliche Oberfläche", "http"),
    ]
    ys = 0.232
    eh = 0.038
    for i, (name, rolle, bindung) in enumerate(ebenen):
        y = ys - i * (eh + 0.009)
        _kasten(ax, 0.035, y, 0.60, eh, "", farbe=c, alpha=0.13)
        ax.text(0.048, y + eh / 2, name.upper(), color=c, fontsize=13,
                fontweight="bold", va="center")
        ax.text(0.115, y + eh / 2, rolle, color=FG, fontsize=11, va="center")
        ax.text(0.655, y + eh / 2, f"ist {ist.get(name, 0):>5}   soll {soll.get(name, 0):>5}",
                color=DIM, fontsize=10.5, va="center", family="monospace")
        ax.text(0.80, y + eh / 2, f"Bindung: {bindung}", color=DIM, fontsize=10.5, va="center")
    # Durchgehende Klammer statt Einzelstriche zwischen den Ebenen: die kurzen
    # Segmente sahen wie Artefakte aus.
    y_oben = ys + eh
    y_unten = ys - (len(ebenen) - 1) * (eh + 0.009)
    ax.plot([0.028, 0.028], [y_unten, y_oben], color=c, lw=1.8, alpha=0.55)
    ax.text(0.020, (y_oben + y_unten) / 2, "Schwelle\nniedriger  ▼", color=c, fontsize=9.5,
            rotation=90, ha="center", va="center", linespacing=1.4, alpha=0.8)

    yc = ys - len(ebenen) * (eh + 0.009) - 0.010
    _kasten(ax, 0.035, yc - 0.046, 0.925, 0.046,
            f"TRANSLATE-CONTROLLER   ·   {sp['counts']['module_gesamt']} Module   ·   "
            f"{sp['counts']['abweichungen']} Abweichungen — davon {sp['counts']['gebunden']} durch Bindung geschlossen, "
            f"{sp['counts']['luecken']} offen   ·   übersetzt nichts: er ordnet zu, bindet und verfolgt",
            farbe=c, fs=12.5, fett=True, alpha=0.10)

    # ---------------- Fuss ----------------
    ax.plot([0.03, 0.97], [0.038, 0.038], color=LINE, lw=1.2)
    ax.text(0.035, 0.019,
            "Erzeugt aus den echten Reports (KONNEKTOR_VOLLAUTOMAT.latest.json · SPRACHBINDUNG.latest.json) — "
            "keine Zahl ist eingetippt.",
            color=DIM, fontsize=10.5)
    ax.text(0.965, 0.019, "scripts/render_algorithmus_png.py", color=DIM,
            fontsize=10.5, ha="right", family="monospace")

    out.parent.mkdir(parents=True, exist_ok=True)
    ziele = [out]
    if auch_svg and out.suffix.lower() != ".svg":
        ziele.append(out.with_suffix(".svg"))

    for ziel in ziele:
        if ziel.suffix.lower() == ".svg":
            # Vektor: dpi ist bedeutungslos, dafuer verlustfrei zoombar.
            # svg.fonttype='path' wandelt Text in Pfade — der Text ist dann
            # nicht mehr markierbar, dafuer sieht die Datei ueberall gleich
            # aus, auch ohne die verwendeten Schriften.
            with matplotlib.rc_context({"svg.fonttype": "path"}):
                fig.savefig(ziel, format="svg", facecolor=BG)
            print(f"[OK] {ziel.relative_to(ROOT)}  Vektor, verlustfrei zoombar  "
                  f"({ziel.stat().st_size / 1024:.0f} KiB)")
        else:
            fig.savefig(ziel, dpi=dpi, facecolor=BG)
            px = (int(fig.get_figwidth() * dpi), int(fig.get_figheight() * dpi))
            print(f"[OK] {ziel.relative_to(ROOT)}  {px[0]}x{px[1]} px  @{dpi} dpi  "
                  f"({ziel.stat().st_size / 1024:.0f} KiB)")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Gesamtalgorithmus als Bild rendern (PNG oder SVG).")
    ap.add_argument("--dpi", type=int, default=200,
                    help="Aufloesung; 200 ergibt ~5200x3400 px (Standard)")
    ap.add_argument("--out", type=Path, default=STANDARD_OUT,
                    help="Zielpfad; Endung .svg erzeugt Vektor statt Raster")
    ap.add_argument("--svg", action="store_true",
                    help="zusaetzlich eine .svg neben die .png legen "
                         "(verlustfrei zoombar)")
    a = ap.parse_args(argv)
    return render(a.dpi, a.out, auch_svg=a.svg)


if __name__ == "__main__":
    raise SystemExit(main())
