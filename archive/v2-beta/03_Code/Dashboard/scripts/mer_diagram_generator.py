#!/usr/bin/env python3
"""Präzise MER-Diagramme als SVG — wissenschaftlich, Kompendium-Farben, heroische Philosophie."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Tuple

OUT_DIR = Path(__file__).resolve().parents[2] / "core" / "knowledge" / "graphics"

# Kompendium / heroische Philosophie Palette
C_PRIMARY = "#1E3A5F"
C_ACCENT = "#C9A227"
C_CREAM = "#FDFAF5"
C_TEXT = "#1C2526"
C_MUTED = "#555555"
C_GRID = "#CCCCCC"
C_REAL = "#1E3A5F"
C_IMAG = "#8B4513"
C_ZSTAR = "#C9A227"
C_REGION = {
    "R1": "#6B8E9F",
    "R2": "#C0392B",
    "R3": "#7D6B8A",
    "R4": "#8E6B4A",
    "R5": "#9B59B6",
    "R6": "#2C3E50",
    "R7": "#16A085",
    "R8": "#D35400",
}


def _svg_header(w: int, h: int, title: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <rect width="100%" height="100%" fill="{C_CREAM}"/>
  <text x="{w//2}" y="28" text-anchor="middle" font-family="Georgia, Times, serif" font-size="14" font-weight="bold" fill="{C_PRIMARY}">{title}</text>
'''


def _svg_footer() -> str:
    return (
        f'  <text x="12" y="{_last_h-8}" font-family="Georgia, serif" font-size="8" fill="{C_MUTED}">'
        f'MER 4D-Matrix · Modell · kein DSM-Ersatz · Kompendium-Duktus</text>\n</svg>'
    )


_last_h = 400


def _save(name: str, body: str, w: int, h: int, title: str) -> Path:
    global _last_h
    _last_h = h
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{name}.svg"
    path.write_text(_svg_header(w, h, title) + body + _svg_footer(), encoding="utf-8")
    return path


def diagram_4d_overview() -> Path:
    w, h = 520, 340
    body = f'''
  <g transform="translate(260,175)">
    <!-- Achsen K/G/S/N als Tetraeder-Projektion (schematisch) -->
    <line x1="0" y1="80" x2="0" y2="-90" stroke="{C_PRIMARY}" stroke-width="2" marker-end="url(#arr)"/>
    <text x="8" y="-95" font-family="Georgia" font-size="11" fill="{C_PRIMARY}">K Körper</text>
    <line x1="-100" y1="40" x2="110" y2="-30" stroke="{C_ACCENT}" stroke-width="2" marker-end="url(#arr)"/>
    <text x="115" y="-35" font-family="Georgia" font-size="11" fill="{C_ACCENT}">G Geist</text>
    <line x1="-90" y1="-50" x2="95" y2="55" stroke="{C_MUTED}" stroke-width="2" marker-end="url(#arr)"/>
    <text x="100" y="65" font-family="Georgia" font-size="11" fill="{C_MUTED}">S Seele</text>
    <line x1="70" y1="-70" x2="-75" y2="60" stroke="#7D6B8A" stroke-width="2" marker-end="url(#arr)"/>
    <text x="-95" y="75" font-family="Georgia" font-size="11" fill="#7D6B8A">N Natur</text>
    <circle cx="0" cy="0" r="8" fill="{C_ZSTAR}" stroke="{C_PRIMARY}" stroke-width="1.5"/>
    <text x="14" y="5" font-family="Georgia" font-size="10" font-weight="bold" fill="{C_ZSTAR}">Z* (0,0,0,0)</text>
    <circle cx="-35" cy="25" r="6" fill="{C_REAL}"/>
    <text x="-75" y="30" font-family="Georgia" font-size="9" fill="{C_REAL}">Z_real</text>
    <circle cx="25" cy="-20" r="6" fill="none" stroke="{C_IMAG}" stroke-width="2"/>
    <text x="35" y="-18" font-family="Georgia" font-size="9" fill="{C_IMAG}">Z_wahrgen.</text>
    <line x1="-35" y1="25" x2="25" y2="-20" stroke="{C_IMAG}" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#arr)"/>
    <text x="0" y="55" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_MUTED}">Δ = Z_wahr − Z_real · I(Z)=Σ|Δ|</text>
  </g>
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="{C_PRIMARY}"/>
    </marker>
  </defs>
  <text x="260" y="310" text-anchor="middle" font-family="Georgia" font-size="10" fill="{C_TEXT}">
    d(Z,Z*) = |K|+|G|+|S|+|N| · Attraktor der Rekonstruktion (Bedingt)
  </text>
'''
    return _save("01_4d_raum_ueberblick", body, w, h, "Der vierdimensionale MER-Ursachenraum Z = (K, G, S, N)")


def _axis_plane(
    name: str,
    title: str,
    x_label: str,
    y_label: str,
    points: List[Tuple[str, float, float, str]],
    regions: List[Tuple[str, float, float, str]],
) -> Path:
    w, h = 500, 420
    ox, oy = 80, h - 70
    pw, ph = 360, 300

    def px(v: float) -> float:
        return ox + (v + 1) / 2 * pw

    def py(v: float) -> float:
        return oy - (v + 1) / 2 * ph

    body = f'''
  <!-- Achsen -->
  <line x1="{ox}" y1="{oy}" x2="{ox+pw}" y2="{oy}" stroke="{C_GRID}" stroke-width="1"/>
  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-ph}" stroke="{C_GRID}" stroke-width="1"/>
  <line x1="{ox}" y1="{py(0)}" x2="{ox+pw}" y2="{py(0)}" stroke="{C_PRIMARY}" stroke-width="1.5" stroke-dasharray="6,4"/>
  <line x1="{px(0)}" y1="{oy}" x2="{px(0)}" y2="{oy-ph}" stroke="{C_PRIMARY}" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="{ox+pw//2}" y="{oy+22}" text-anchor="middle" font-family="Georgia" font-size="11" fill="{C_ACCENT}">{x_label}</text>
  <text x="{ox-12}" y="{oy-ph//2}" text-anchor="middle" font-family="Georgia" font-size="11" fill="{C_PRIMARY}" transform="rotate(-90,{ox-12},{oy-ph//2})">{y_label}</text>
  <text x="{px(0)}" y="{py(0)-8}" text-anchor="middle" font-family="Georgia" font-size="10" font-weight="bold" fill="{C_ZSTAR}">Z*</text>
  <text x="{px(-0.9)}" y="{oy+12}" font-family="Georgia" font-size="8" fill="{C_MUTED}">−</text>
  <text x="{px(0.85)}" y="{oy+12}" font-family="Georgia" font-size="8" fill="{C_MUTED}">+</text>
  <text x="{ox-18}" y="{py(-0.85)}" font-family="Georgia" font-size="8" fill="{C_MUTED}">−</text>
  <text x="{ox-18}" y="{py(0.85)}" font-family="Georgia" font-size="8" fill="{C_MUTED}">+</text>
'''
    for label, xv, yv, col in regions:
        body += f'  <text x="{px(xv)}" y="{py(yv)}" font-family="Georgia" font-size="8" fill="{col}" opacity="0.7">{label}</text>\n'

    for label, xv, yv, col in points:
        body += f'  <circle cx="{px(xv)}" cy="{py(yv)}" r="5" fill="{col}"/>\n'
        body += f'  <text x="{px(xv)+8}" y="{py(yv)+4}" font-family="Georgia" font-size="8" fill="{C_TEXT}">{label}</text>\n'

    return _save(name, body, w, h, title)


def diagram_pi_kg() -> Path:
    return _axis_plane(
        "02_pi_kg_koerper_geist",
        "Projektion Π_KG — Körper × Geist",
        "G Geist  →",
        "K Körper ↑",
        [
            ("GAD", 0.7, 0.6, C_REGION["R2"]),
            ("Manie", 0.85, 0.8, C_REGION["R2"]),
            ("Panik", 0.1, 0.75, C_REGION["R2"]),
            ("OCD", 0.75, 0.5, C_REGION["R4"]),
            ("ADHS", 0.65, 0.35, C_REGION["R2"]),
            ("Depression", -0.3, -0.5, C_REGION["R1"]),
            ("Substanz", -0.2, 0.4, C_REGION["R8"]),
            ("Vermeidung", -0.5, -0.3, C_REGION["R3"]),
        ],
        [("R₂ Hoch-G/K", 0.6, 0.55, C_REGION["R2"]), ("R₁ Niedrig", -0.5, -0.5, C_REGION["R1"])],
    )


def diagram_pi_sn() -> Path:
    return _axis_plane(
        "03_pi_sn_seele_natur",
        "Projektion Π_SN — Seele × Natur",
        "S Seele  →",
        "N Natur ↑",
        [
            ("Depression", -0.6, -0.7, C_REGION["R1"]),
            ("PTBS", -0.5, 0.2, C_REGION["R6"]),
            ("Autismus", -0.3, -0.2, C_REGION["R7"]),
            ("Borderline S+", 0.7, -0.2, C_REGION["R5"]),
            ("Borderline S−", -0.7, -0.2, C_REGION["R5"]),
            ("Schizophrenie", -0.4, -0.5, C_REGION["R1"]),
        ],
        [("R₆ Trauma", -0.45, 0.15, C_REGION["R6"]), ("R₁ Niedrig-N", -0.55, -0.65, C_REGION["R1"])],
    )


def diagram_schattenhuelle() -> Path:
    w, h = 480, 300
    body = f'''
  <g transform="translate(240,150)">
    <line x1="-160" y1="60" x2="160" y2="60" stroke="{C_GRID}"/>
    <line x1="0" y1="-90" x2="0" y2="90" stroke="{C_GRID}"/>
    <circle cx="0" cy="0" r="6" fill="{C_ZSTAR}"/>
    <text x="12" y="4" font-family="Georgia" font-size="9" fill="{C_ZSTAR}">Z*</text>
    <circle cx="-40" cy="35" r="7" fill="{C_REAL}"/>
    <text x="-95" y="40" font-family="Georgia" font-size="10" fill="{C_REAL}">● Z_real (K− Untergewicht)</text>
    <circle cx="50" cy="-45" r="7" fill="none" stroke="{C_IMAG}" stroke-width="2.5"/>
    <text x="65" y="-42" font-family="Georgia" font-size="10" fill="{C_IMAG}">○ Z_wahrgen. („fett")</text>
    <line x1="-40" y1="35" x2="50" y2="-45" stroke="{C_IMAG}" stroke-width="2" marker-end="url(#arr2)"/>
    <text x="5" y="-5" font-family="Georgia" font-size="9" font-weight="bold" fill="{C_IMAG}">Δ · I(Z) hoch</text>
    <rect x="-170" y="75" width="340" height="45" fill="white" stroke="{C_ACCENT}" stroke-width="0.5" rx="4"/>
    <text x="0" y="95" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_TEXT}">Masking: ● nahe Z*, ○ tief → hohes I bei moderatem d</text>
    <text x="0" y="110" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_MUTED}">Rekonstruktivismus (D4): α₂ kalibriert Δ Schicht für Schicht</text>
  </g>
  <defs><marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{C_IMAG}"/></marker></defs>
'''
    return _save("04_schattenhuelle_iz", body, w, h, "Die Schattenhülle I(Z) — Z_real und Z_wahrgenommen")


def diagram_bipolar_cycle() -> Path:
    w, h = 500, 320
    ox, oy = 70, h - 60
    pw, ph = 380, 220
    # Ellipse path for limit cycle
    body = f'''
  <line x1="{ox}" y1="{oy}" x2="{ox+pw}" y2="{oy}" stroke="{C_GRID}"/>
  <line x1="{ox}" y1="{oy}" x2="{ox}" y2="{oy-ph}" stroke="{C_GRID}"/>
  <text x="{ox+pw//2}" y="{oy+18}" text-anchor="middle" font-family="Georgia" font-size="10" fill="{C_ACCENT}">G Geist</text>
  <text x="{ox-8}" y="{oy-ph//2}" text-anchor="middle" font-family="Georgia" font-size="10" fill="{C_PRIMARY}" transform="rotate(-90,{ox-8},{oy-ph//2})">K Körper</text>
  <ellipse cx="{ox+pw*0.55}" cy="{oy-ph*0.45}" rx="120" ry="75" fill="none" stroke="{C_REGION['R5']}" stroke-width="2" stroke-dasharray="8,5"/>
  <circle cx="{ox+pw*0.75}" cy="{oy-ph*0.2}" r="6" fill="{C_REGION['R2']}"/>
  <text x="{ox+pw*0.78}" y="{oy-ph*0.15}" font-family="Georgia" font-size="9" fill="{C_TEXT}">Manie ★</text>
  <circle cx="{ox+pw*0.35}" cy="{oy-ph*0.75}" r="6" fill="{C_REGION['R1']}"/>
  <text x="{ox+pw*0.38}" y="{oy-ph*0.68}" font-family="Georgia" font-size="9" fill="{C_TEXT}">Depression</text>
  <path d="M {ox+pw*0.72} {oy-ph*0.25} Q {ox+pw*0.6} {oy-ph*0.5} {ox+pw*0.4} {oy-ph*0.7}" fill="none" stroke="{C_ACCENT}" stroke-width="1.5" marker-end="url(#arr3)"/>
  <text x="{ox+pw*0.5}" y="35" text-anchor="middle" font-family="Georgia" font-size="11" font-weight="bold" fill="{C_PRIMARY}">Bipolar I — Limit-Cycle in Π_KG</text>
  <text x="{ox+pw*0.5}" y="52" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_MUTED}">Heilung: Zyklus schrumpft · d_max pro Periode sinkt · q-Flug mit b-Abschluss</text>
  <defs><marker id="arr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{C_ACCENT}"/></marker></defs>
'''
    return _save("05_bipolar_limit_cycle", body, w, h, "Trajektorie Z(t) — Bipolar I")


def diagram_ptbs_attraktor() -> Path:
    w, h = 500, 300
    body = f'''
  <text x="250" y="55" text-anchor="middle" font-family="Georgia" font-size="10" fill="{C_MUTED}">Alltag nahe Z* — Trigger → Trauma-Loch</text>
  <circle cx="120" cy="150" r="10" fill="{C_ZSTAR}"/>
  <text x="120" y="175" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_ZSTAR}">Z* Alltag</text>
  <circle cx="350" cy="100" r="12" fill="{C_REGION['R6']}"/>
  <text x="350" y="125" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_TEXT}">Flashback</text>
  <path d="M 130 145 Q 200 80 340 105" fill="none" stroke="{C_REGION['R6']}" stroke-width="2.5" marker-end="url(#arr4)"/>
  <text x="235" y="95" font-family="Georgia" font-size="9" fill="{C_REGION['R6']}">Trigger ↖</text>
  <path d="M 340 115 Q 250 180 130 155" fill="none" stroke="{C_MUTED}" stroke-width="1.5" stroke-dasharray="5,4" marker-end="url(#arr5)"/>
  <text x="235" y="200" font-family="Georgia" font-size="9" fill="{C_MUTED}">Recovery (I oft verzerrt)</text>
  <rect x="60" y="220" width="380" height="55" fill="white" stroke="{C_PRIMARY}" rx="4"/>
  <text x="250" y="240" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_TEXT}">α₁ S-Safe vor α₂ · EMDR formt Trauma-Geometrie um</text>
  <text x="250" y="258" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_MUTED}">[q,b]≠0: Reihenfolge S→G→K nicht vertauschen</text>
  <defs>
    <marker id="arr4" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{C_REGION['R6']}"/></marker>
    <marker id="arr5" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="{C_MUTED}"/></marker>
  </defs>
'''
    return _save("06_ptbs_trauma_attraktor", body, w, h, "Trajektorie Z(t) — PTBS (Trauma-Attraktor)")


def diagram_alpha_phases() -> Path:
    w, h = 520, 280
    phases = [
        ("α₁ Stabilisieren", "d nicht steigen", "Krisenplan · L0", C_PRIMARY),
        ("α₂ Kalibrieren", "I(Z) senken", "ψ▷φ · DMN*", C_ACCENT),
        ("α₃ Rekonstruieren", "d → Z*", "Stamm · Quant", C_REGION["R7"]),
    ]
    body = ""
    x0 = 40
    for i, (name, goal, tools, col) in enumerate(phases):
        x = x0 + i * 155
        body += f'''
  <rect x="{x}" y="70" width="140" height="100" fill="white" stroke="{col}" stroke-width="2" rx="6"/>
  <text x="{x+70}" y="95" text-anchor="middle" font-family="Georgia" font-size="11" font-weight="bold" fill="{col}">{name}</text>
  <text x="{x+70}" y="115" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_TEXT}">{goal}</text>
  <text x="{x+70}" y="135" text-anchor="middle" font-family="Georgia" font-size="8" fill="{C_MUTED}">{tools}</text>
'''
        if i < 2:
            body += f'  <polygon points="{x+145},120 {x+155},115 {x+145},110" fill="{C_ACCENT}"/>\n'
    body += f'''
  <text x="260" y="200" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_IMAG}">β-Rückfall = Geodätische Information (Sisyphos-Zyklus)</text>
  <text x="260" y="218" text-anchor="middle" font-family="Georgia" font-size="8" fill="{C_MUTED}">*DMN-Kalibrierung Bedingt · nicht bei akuter Psychose</text>
  <text x="260" y="248" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_TEXT}">Vierschritt A.10: Erkennen → Hinterfragen → Verinnerlichen → Kooperation (Stamm)</text>
'''
    return _save("07_dreiphasen_alpha", body, w, h, "Dreiphasen-Modell α₁ · α₂ · α₃ (MER-Rekonstruktion)")


def diagram_schichten_pipeline() -> Path:
    w, h = 520, 360
    layers = [
        ("Edition 0.7", "Transparenz · Audit", "#5C4A2A"),
        ("Dissertation Ü/S/F", "Epistemische Hygiene", "#7D6B8A"),
        ("Philosophie A.1–12", "Concept Space D1–D8", "#1E3A5F"),
        ("4D-Matrix Z,I(Z)", "K/G/S/N · Regionen", "#16A085"),
        ("Π_KG · Π_SN", "Trajektorien Z(t)", "#C9A227"),
    ]
    body = ""
    y = 55
    for i, (name, sub, col) in enumerate(layers):
        body += f'''
  <rect x="80" y="{y}" width="360" height="42" fill="{col}" opacity="0.15" stroke="{col}" stroke-width="1.5" rx="4"/>
  <text x="100" y="{y+18}" font-family="Georgia" font-size="11" font-weight="bold" fill="{col}">{name}</text>
  <text x="100" y="{y+34}" font-family="Georgia" font-size="9" fill="{C_MUTED}">{sub}</text>
'''
        if i < len(layers) - 1:
            body += f'  <line x1="260" y1="{y+42}" x2="260" y2="{y+52}" stroke="{C_ACCENT}" stroke-width="2"/>\n'
            body += f'  <polygon points="255,{y+52} 265,{y+52} 260,{y+58}" fill="{C_ACCENT}"/>\n'
        y += 52
    body += f'''
  <text x="260" y="330" text-anchor="middle" font-family="Georgia" font-size="9" font-style="italic" fill="{C_TEXT}">
    „Kompass, kein Programm" — areteisch, rekonstruktivistisch (A.6, D4)
  </text>
'''
    return _save("08_gesamt_pipeline", body, w, h, "Integrative Architektur — Edition · Philosophie · MER")


def diagram_memetisch_mimetisch() -> Path:
    w, h = 480, 300
    body = f'''
  <rect x="180" y="50" width="120" height="36" fill="{C_CREAM}" stroke="{C_PRIMARY}" rx="4"/>
  <text x="240" y="73" text-anchor="middle" font-family="Georgia" font-size="10" fill="{C_TEXT}">Symptom besser?</text>
  <line x1="240" y1="86" x2="120" y2="130" stroke="{C_PRIMARY}"/>
  <line x1="240" y1="86" x2="240" y2="130" stroke="{C_PRIMARY}"/>
  <line x1="240" y1="86" x2="360" y2="130" stroke="{C_PRIMARY}"/>
  <text x="80" y="125" font-family="Georgia" font-size="8" fill="{C_MUTED}">Ja</text>
  <text x="225" y="125" font-family="Georgia" font-size="8" fill="{C_MUTED}">Ja</text>
  <text x="370" y="125" font-family="Georgia" font-size="8" fill="{C_MUTED}">Nein</text>
  <rect x="40" y="140" width="150" height="50" fill="white" stroke="{C_REGION['R7']}" rx="4"/>
  <text x="115" y="162" text-anchor="middle" font-family="Georgia" font-size="9" font-weight="bold" fill="{C_REGION['R7']}">d gesunken?</text>
  <text x="115" y="178" text-anchor="middle" font-family="Georgia" font-size="8" fill="{C_TEXT}">→ memetisch α₃</text>
  <rect x="165" y="140" width="150" height="50" fill="white" stroke="{C_IMAG}" rx="4"/>
  <text x="240" y="162" text-anchor="middle" font-family="Georgia" font-size="9" font-weight="bold" fill="{C_IMAG}">nur I gesunken?</text>
  <text x="240" y="178" text-anchor="middle" font-family="Georgia" font-size="8" fill="{C_TEXT}">→ mimetisch (Surrogat)</text>
  <rect x="290" y="140" width="150" height="50" fill="white" stroke="{C_REGION['R2']}" rx="4"/>
  <text x="365" y="162" text-anchor="middle" font-family="Georgia" font-size="9" font-weight="bold" fill="{C_REGION['R2']}">β-Rückfall</text>
  <text x="365" y="178" text-anchor="middle" font-family="Georgia" font-size="8" fill="{C_TEXT}">Achse analysieren</text>
  <text x="240" y="230" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_MUTED}">Hospitalismus 2.0: Likes senken I, nicht d auf S</text>
  <text x="240" y="250" text-anchor="middle" font-family="Georgia" font-size="9" fill="{C_TEXT}">Rekonstruktivismus: Z_real muss sich bewegen</text>
'''
    return _save("09_memetisch_mimetisch", body, w, h, "Entscheidungsbaum — memetische vs. mimetische Heilung")


def generate_all() -> Dict[str, Path]:
    fns = [
        diagram_4d_overview,
        diagram_pi_kg,
        diagram_pi_sn,
        diagram_schattenhuelle,
        diagram_bipolar_cycle,
        diagram_ptbs_attraktor,
        diagram_alpha_phases,
        diagram_schichten_pipeline,
        diagram_memetisch_mimetisch,
    ]
    return {fn.__name__: fn() for fn in fns}


if __name__ == "__main__":
    import json
    paths = generate_all()
    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))