# -*- coding: utf-8 -*-
"""
Fusion Hero OS — Layer-4-Telemetrie-Dashboard v2.0 (De-Ghosting, axiomatisch verankert)

v1 dieser Datei war ein leerer 88-Byte-Stub — im Legacy Ghost Hunt 2026-07-16
als dokumentierter Geist inventarisiert (P3/Research). v2.0 fuellt den Geist
mit einem Dashboard, das AUSSCHLIESSLICH ECHTE Daten zeigt. Jedes Panel traegt
einen sichtbaren Axiom-Anker (Proof-Registry-Claim bzw. Geltungsmarke); die
Zufallsmetrik-Vorlage aus dem Gemini-Brainstorm 2026-07-24 (np.random als
"M-pression") wurde bewusst verworfen — simulierte Werte als Telemetrie
anzuzeigen waere epistemische Regression.

Ehrlicher Status:
  * P3/Research-Einstufung bleibt bestehen — dieses Artefakt ist kein
    Produkt-Dashboard (das ist app.py / hero-docs-server.py).
  * streamlit und plotly sind OPTIONALE Dependencies, bewusst NICHT in
    requirements.txt:  pip install streamlit plotly
  * Start:  streamlit run artifacts/fractal_ghost_hunt/streamlit_hyper4d_app.py

Panels und Axiom-Anker:
  1. Layer-Graph & Status   [Spezifikation]  Anker: LAYER-GRAPH-VOLLSTAENDIG
  2. n±2 Blind-Spot-Check   [Satz]           Anker: LAYER-DISTANCE-CROSSCHECK
  3. M-pression-Demo        [Satz + Modell]  Anker: K17, MPRESSION-PROJECTION-LOSS
  4. Root-Anchor-Handshake  [Satz]           Anker: ROOT-ANCHOR-TAMPER-DETECT
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    import streamlit as st
except ImportError:  # pragma: no cover - optionale Dependency
    raise SystemExit(
        "streamlit fehlt (optionale Dependency dieses Research-Artefakts).\n"
        "Installation: pip install streamlit plotly\n"
        "Start:        streamlit run artifacts/fractal_ghost_hunt/streamlit_hyper4d_app.py"
    )

try:
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover
    go = None

import numpy as np

from fusion_hero_os.core.layer_registry import get_all_layer_status
from fusion_hero_os.core.layer_distance_crosscheck import (
    build_adjacency,
    crosscheck_all,
    distance_n_neighbors,
)
from ascension_os.core.mpression_projection import measure_mpression
from ascension_os.core.root_anchor_handshake import RootAnchorHandshake

st.set_page_config(page_title="Fusion Hero OS | Layer-4-Telemetrie v2.0", layout="wide")

st.title("Fusion Hero OS — Layer-4-Telemetrie v2.0")
st.caption(
    "Axiom-Prinzip: jedes Panel zeigt NUR echte Daten und traegt seinen "
    "Proof-Registry-Anker. Keine simulierten Metriken. "
    "P3/Research-Artefakt — kein Produkt-Dashboard."
)

# ---------------------------------------------------------------------------
# Echte Daten laden (einmal pro Rerun; layer_registry ist offline/dateibasiert)
# ---------------------------------------------------------------------------
status = get_all_layer_status()
adjacency = build_adjacency(status.get("layer_edges") or [])
health = {
    lid: bool(s["present"] and s["config_ok"]) for lid, s in status["layers"].items()
}

# ---------------------------------------------------------------------------
# Panel 1 — Layer-Graph & Status  [Spezifikation | Anker: LAYER-GRAPH-VOLLSTAENDIG]
# ---------------------------------------------------------------------------
st.header("1 · Layer-Graph & Status")
st.caption("[Spezifikation] Anker: LAYER-GRAPH-VOLLSTAENDIG · Quelle: fusion_unified.yaml via layer_registry")

col_a, col_b, col_c = st.columns(3)
col_a.metric("Layer gesamt", status["layer_count"])
col_b.metric("Layer ok", status["layers_ok"])
col_c.metric("Overall", status["overall"])

if go is not None and adjacency:
    # Deterministisches Kreis-Layout: echte Knoten, echte Kanten, Health-Farbe.
    nodes = sorted(set(adjacency) | set(status["layers"].keys()))
    angle = {n: 2 * np.pi * i / len(nodes) for i, n in enumerate(nodes)}
    pos = {n: (float(np.cos(a)), float(np.sin(a))) for n, a in angle.items()}

    edge_x, edge_y = [], []
    seen = set()
    for a, nbrs in adjacency.items():
        for b in nbrs:
            key = frozenset((a, b))
            if key in seen:
                continue
            seen.add(key)
            edge_x += [pos[a][0], pos[b][0], None]
            edge_y += [pos[a][1], pos[b][1], None]

    node_x = [pos[n][0] for n in nodes]
    node_y = [pos[n][1] for n in nodes]
    node_color = ["#00c853" if health.get(n, False) else "#d50000" for n in nodes]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines",
                             line=dict(width=1, color="#888"), hoverinfo="none"))
    fig.add_trace(go.Scatter(
        x=node_x, y=node_y, mode="markers+text", text=nodes,
        textposition="top center",
        marker=dict(size=14, color=node_color), hoverinfo="text",
    ))
    fig.update_layout(showlegend=False, height=520,
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("plotly nicht installiert — Graph-Ansicht deaktiviert (Tabellen unten sind vollstaendig).")

with st.expander("Layer-Detailstatus (echt, aus layer_registry)"):
    st.json({lid: s for lid, s in status["layers"].items()})

# ---------------------------------------------------------------------------
# Panel 2 — n±2 Blind-Spot-Crosscheck  [Satz | Anker: LAYER-DISTANCE-CROSSCHECK]
# ---------------------------------------------------------------------------
st.header("2 · n±2 Blind-Spot-Crosscheck")
st.caption(
    "[Satz] Anker: LAYER-DISTANCE-CROSSCHECK · BFS-Distanzsemantik bewiesen; "
    "die Rationale 'skip-eine-Ebene faengt korrelierte blinde Flecken' ist Modell (A13 Bogen 3)."
)

candidates = crosscheck_all(adjacency, health)
if candidates:
    st.error(f"{len(candidates)} Blind-Spot-Kandidat(en) gefunden:")
    st.table([c.to_dict() for c in candidates])
else:
    st.success("Keine Blind-Spot-Kandidaten: kein Layer mit gesunder Distanz-1-Umgebung "
               "hat einen ungesunden Distanz-2-Nachbarn.")

origin = st.selectbox("Distanzmengen fuer Layer inspizieren", sorted(adjacency))
d1 = sorted(distance_n_neighbors(adjacency, origin, 1))
d2 = sorted(distance_n_neighbors(adjacency, origin, 2))
st.write({"origin": origin, "distanz_1": d1, "distanz_2": d2})

# ---------------------------------------------------------------------------
# Panel 3 — M-pression-Demo  [Satz + Modell | Anker: K17, MPRESSION-PROJECTION-LOSS]
# ---------------------------------------------------------------------------
st.header("3 · M-pression als Projektionsverlust (Demo)")
st.caption(
    "[Satz] Mathematik-Anker: K17 + MPRESSION-PROJECTION-LOSS. "
    "[Modell] Die EINGABEN hier sind synthetisch und nutzer-gesteuert — Demo der "
    "echten Rechnung, keine gemessene Intention."
)

c1, c2, c3 = st.columns(3)
vx = c1.slider("v · x-Komponente", -5.0, 5.0, 1.0, 0.1)
vy = c2.slider("v · y-Komponente", -5.0, 5.0, 2.0, 0.1)
vz = c3.slider("v · z-Komponente (orthogonal zum Unterraum)", -5.0, 5.0, 3.0, 0.1)

result = measure_mpression([vx, vy, vz], [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
if result is None:
    st.warning("K17-Orthogonalprojektor nicht importierbar — ehrlich: kein Ergebnis statt Fake-Wert.")
else:
    m1, m2, m3 = st.columns(3)
    m1.metric("Verlust ‖v − Pv‖", f"{result.loss:.4f}")
    m2.metric("Relativer Verlust", f"{result.relative_loss:.4f}")
    m3.metric("Pythagoras-Residuum", f"{result.pythagoras_residual:.2e}")
    st.caption(
        "Unterraum = x/y-Ebene. Der Verlust ist exakt |z| — die Komponente, "
        "die bei der Projektion latent→manifest nicht darstellbar ist."
    )

# ---------------------------------------------------------------------------
# Panel 4 — Root-Anchor-Handshake  [Satz | Anker: ROOT-ANCHOR-TAMPER-DETECT]
# ---------------------------------------------------------------------------
st.header("4 · Root-Anchor-Handshake (Live-Krypto)")
st.caption(
    "[Satz] Anker: ROOT-ANCHOR-TAMPER-DETECT · Echte Ed25519-Signatur, "
    "prozess-lokal. KEIN SSH, KEIN Netzwerk (A13 Bogen 4)."
)

if "anchor" not in st.session_state:
    st.session_state.anchor = RootAnchorHandshake()
anchor = st.session_state.anchor

claim_text = st.text_input("Manifest-Claim", value="healthy")
manifest = {"layer": "ascension", "claim": claim_text}
signature = anchor.sign(manifest)

st.code(f"public_key = {anchor.keypair.public_bytes_hex()}\n"
        f"signature  = {signature[:48]}...", language="text")

ok = anchor.verify(manifest, signature)
tampered = anchor.verify({**manifest, "claim": claim_text + "_tampered"}, signature)
h1, h2 = st.columns(2)
h1.metric("Verify (original)", "TRUE" if ok else "FALSE")
h2.metric("Verify (manipuliert)", "TRUE" if tampered else "FALSE")
if ok and not tampered:
    st.success("Integritaet nachgewiesen: Original verifiziert, Manipulation erkannt.")
else:
    st.error("Unerwartetes Verify-Ergebnis — widerspraeche ROOT-ANCHOR-TAMPER-DETECT, bitte melden.")

st.divider()
st.caption(
    "v2.0 · De-Ghosting des Stubs aus dem Legacy Ghost Hunt 2026-07-16 · "
    "Herkunft des Vokabulars: Gemini-Brainstorm 2026-07-24 · "
    "Kanon: docs/dissertation/anhaenge/A13_Brainstorm_Vokabular_Operationalisierung.md"
)
