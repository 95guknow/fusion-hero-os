import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Knotenkarte & Analyse", page_icon="🗺️", layout="wide")
st.title("Interaktive Knotenkarte & Philosophische Knotenanalyse")

DATA_PATH = Path(__file__).parent.parent / "data" / "philosophers_nodes.json"
nodes = []
if DATA_PATH.exists():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        nodes = json.load(f).get("nodes", [])

tab1, tab2, tab3, tab4 = st.tabs(["Suche", "Timeline", "Cluster", "Philosophische Knotenanalyse"])

with tab1:
    term = st.text_input("Suchbegriff")
    if term and nodes:
        results = [n for n in nodes if term.lower() in n.get('name','').lower() or term.lower() in n.get('era','').lower()]
        for n in results[:10]:
            with st.expander(f"{n['name']} ({n['period']})"):
                st.write(n.get('relevance', ''))

with tab2:
    st.info("Timeline nach Epochen mit Sinnstrahlen (wie zuvor implementiert)")

with tab3:
    st.info("Geographische Cluster (wie zuvor implementiert)")

with tab4:
    st.subheader("Philosophische Knotenanalyse")
    if nodes:
        selected = st.selectbox("Philosophen wählen", [f"{n['name']} ({n['period']})" for n in nodes])
        node = next((n for n in nodes if f"{n['name']} ({n['period']})" == selected), None)

        if node:
            st.markdown(f"### {node['name']}")
            st.caption(node.get('era', ''))
            st.info(node.get('relevance', ''))

            # Stufe 2/3: Speichern für Dashboard
            if st.button("Diese Analyse merken"):
                st.session_state["last_knotenanalyse"] = node['name']
                st.success("Für Dashboard gespeichert.")

            if st.button("Quant-Vorschlag basierend auf diesem Denker generieren"):
                st.session_state["preloaded_quant"] = {
                    "field": "Sinn & spirituelle Verbindung",
                    "problem_description": f"Einfluss von {node['name']}",
                    "suggested_name": f"Rezeption von {node['name']}"
                }
                st.success("Vorbereitet für Quant-Modus.")
                st.switch_page("pages/02_Quant.py")
    else:
        st.warning("Keine Daten gefunden.")
