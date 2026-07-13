import streamlit as st

st.set_page_config(
    page_title="Der heroische Mensch",
    page_icon="🪨",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.4rem; font-weight: 700; }
    .subtle { color: #666; font-size: 0.95rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-header">Der heroische Mensch</p>', unsafe_allow_html=True)
st.markdown('<p class="subtle">Interaktive Webapplikation — Moderne Version 2026</p>', unsafe_allow_html=True)

st.divider()

# === Erweitertes Dashboard (Stufe 2 + 3) ===
st.markdown("### Projekt-Überblick")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Quant-Session**")
    if "quant_iterations" in st.session_state and st.session_state.quant_iterations:
        st.success(f"{len(st.session_state.quant_iterations)} Iterationen")
        if st.button("Quant-Modus öffnen", key="dash_quant"):
            st.switch_page("pages/02_Quant.py")
    else:
        st.info("Keine aktive Session")

with col2:
    st.markdown("**Letzte Problem-Analyse**")
    if "last_problem_analysis" in st.session_state:
        st.success(st.session_state["last_problem_analysis"]["name"][:50])
        if st.button("Zur Analyse", key="dash_problem"):
            st.switch_page("pages/05_Eigenes_Problem.py")
    else:
        st.info("Noch keine Analyse")

with col3:
    st.markdown("**Knotenanalyse**")
    if "last_knotenanalyse" in st.session_state:
        st.success(st.session_state["last_knotenanalyse"][:50])
        if st.button("Zur Knotenanalyse", key="dash_knoten"):
            st.switch_page("pages/03_Knotenkarte.py")
    else:
        st.info("Noch keine Knotenanalyse")

st.divider()

st.markdown("""
### Module

Nutze das linke Menü, um zwischen den Modulen zu wechseln.  
Die Module sind zunehmend miteinander vernetzt (Daten, Kontext und Vorschläge werden übertragen).
""")
