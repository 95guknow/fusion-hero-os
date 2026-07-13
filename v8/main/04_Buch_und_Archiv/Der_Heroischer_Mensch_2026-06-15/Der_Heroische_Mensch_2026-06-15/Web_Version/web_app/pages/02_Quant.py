import streamlit as st

st.set_page_config(page_title="Quant-Modus", page_icon="⚡", layout="wide")
st.title("Mächtiger Quant-Modus mit Rückkopplung")

st.markdown("Echtes iteratives Arbeiten mit Rückkopplungsschleife.")

if "quant_iterations" not in st.session_state:
    st.session_state.quant_iterations = []

# STUFE 2: Preload von "Eigenes Problem"
preload = st.session_state.get("preloaded_quant", None)
if preload:
    st.info(f"Vorbereiteter Bereich aus 'Eigenes Problem': **{preload['field']}**")
    if st.button("Vorbereitete Daten übernehmen"):
        st.session_state["preloaded_field"] = preload["field"]
        del st.session_state["preloaded_quant"]
        st.rerun()

if st.button("Neue Session starten"):
    st.session_state.quant_iterations = []
    if "preloaded_field" in st.session_state:
        del st.session_state["preloaded_field"]
    st.rerun()

st.divider()

iteration_num = len(st.session_state.quant_iterations) + 1
st.subheader(f"Iteration {iteration_num}")

default_field = st.session_state.get("preloaded_field", "Sicherheit & Stabilität")

with st.form(key=f"q{iteration_num}"):
    field = st.selectbox("Bereich", [
        "Körper & Embodiment", "Sicherheit & Stabilität",
        "Paarbindung / Romantische Liebe (Liebesquant)",
        "Freundschaft & Stamm (Liebesquant)",
        "Bewährung & Leistung", "Ausdruck & Kreativität",
        "Sinn & spirituelle Verbindung"
    ], index=0 if default_field not in ["Körper & Embodiment", "Sicherheit & Stabilität", "Paarbindung / Romantische Liebe (Liebesquant)", "Freundschaft & Stamm (Liebesquant)", "Bewährung & Leistung", "Ausdruck & Kreativität", "Sinn & spirituelle Verbindung"] else 
    ["Körper & Embodiment", "Sicherheit & Stabilität", "Paarbindung / Romantische Liebe (Liebesquant)", "Freundschaft & Stamm (Liebesquant)", "Bewährung & Leistung", "Ausdruck & Kreativität", "Sinn & spirituelle Verbindung"].index(default_field))

    is_love = "Liebesquant" in field
    lq = st.select_slider("Liebesquant", ["Sehr niedrig","Niedrig","Mittel","Hoch","Sehr hoch"], value="Mittel") if is_love else None
    state = st.select_slider("Zustand", ["Sehr schlecht","Eher schlecht","Mittel","Eher gut","Sehr gut"], value="Mittel")
    blocker = st.selectbox("Blockade", ["Zu wenig echte Verstehensmomente", "Fehlendes Wissen", "Emotionale Blockade", "Äußere Umstände", "Fehlender Stamm"])

    if st.form_submit_button("Iteration abschließen"):
        st.session_state.quant_iterations.append({
            "nr": iteration_num, "field": field, "state": state,
            "liebesquant": lq, "blocker": blocker
        })
        if "preloaded_field" in st.session_state:
            del st.session_state["preloaded_field"]
        st.success(f"Iteration {iteration_num} gespeichert.")
        st.rerun()

if st.session_state.quant_iterations:
    st.divider()
    st.subheader("Gespeicherte Iterationen")
    for it in st.session_state.quant_iterations:
        with st.expander(f"Iteration {it['nr']} — {it['field']}"):
            st.write(f"**Zustand:** {it['state']}")
            if it.get("liebesquant"): st.write(f"**Liebesquant:** {it['liebesquant']}")
            st.write(f"**Blockade:** {it['blocker']}")

    if st.button("Gesamte Session exportieren"):
        content = "# Quant-Session\n\n"
        for it in st.session_state.quant_iterations:
            content += f"## Iteration {it['nr']}\n- **Bereich:** {it['field']}\n- **Zustand:** {it['state']}\n"
            if it.get("liebesquant"): content += f"- **Liebesquant:** {it['liebesquant']}\n"
            content += f"- **Blockade:** {it['blocker']}\n\n"
        st.download_button("Download .md", content, f"quant_session_{len(st.session_state.quant_iterations)}.md")
