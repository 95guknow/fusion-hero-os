import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Eigenes Problem", page_icon="💡", layout="wide")
st.title("Eigenes Problem analysieren")

problem = st.text_area("Dein Problem / Mangel", height=130)

if st.button("Analysieren", type="primary") and problem.strip():
    text = problem.lower()

    if any(w in text for w in ["beziehung", "liebe", "stamm", "einsam", "verstanden"]):
        name, mimetik, memetik, vorschlag, suggested_field = (
            "Liebesquant-Defizit / Mimetische Bindung", "Hoch", "Sehr hoch",
            "Fokussiere auf Qualität echter Verstehensmomente mit 1-2 Menschen.",
            "Paarbindung / Romantische Liebe (Liebesquant)"
        )
    elif any(w in text for w in ["erfolg", "leistung", "status", "wert"]):
        name, mimetik, memetik, vorschlag, suggested_field = (
            "Mimetischer Leistungs- und Statushunger", "Sehr hoch", "Extrem hoch",
            "Trenne Leistung klar von innerem Wert.",
            "Bewährung & Leistung"
        )
    else:
        name, mimetik, memetik, vorschlag, suggested_field = (
            "Struktureller Quantenmangel (unspezifisch)", "Mittel bis hoch", "Hoch",
            "Identifiziere das konkreteste Mangelfeld und wende den Quant an.",
            "Sicherheit & Stabilität"
        )

    # Speichere für Dashboard (Stufe 3)
    st.session_state["last_problem_analysis"] = {
        "name": name,
        "timestamp": datetime.now().isoformat()
    }

    st.success("Analyse abgeschlossen")
    st.markdown(f"### Vorgeschlagener Projektnamen\n**{name}**")

    col1, col2 = st.columns(2)
    with col1: st.metric("Mimetik", mimetik)
    with col2: st.metric("Memetik", memetik)

    st.info(vorschlag)

    # Stufe 2 Integration
    if st.button("Diese Analyse im Quant-Modus weiterführen"):
        st.session_state["preloaded_quant"] = {
            "field": suggested_field,
            "problem_description": problem,
            "suggested_name": name
        }
        st.success("Daten für Quant-Modus vorbereitet.")
        st.switch_page("pages/02_Quant.py")

    if st.button("Als Markdown herunterladen"):
        content = f"""# Analyse deines Problems

**Problem:** {problem}
**Name:** {name}
**Mimetik:** {mimetik} | **Memetik:** {memetik}

**Quant-Vorschlag:** {vorschlag}
"""
        st.download_button("Download", content, "problem_analyse.md")
