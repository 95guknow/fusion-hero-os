import streamlit as st

st.set_page_config(page_title="Zentrale Probleme", page_icon="🧠", layout="wide")
st.title("Quant auf zentrale Probleme der 4D-Matrix")

st.markdown("Wähle eines der wichtigsten Probleme aus der Matrix. Du erhältst den sinnvollen Projektnamen, die 4-Schritt-Quant-Anwendung sowie Mimetik- und Memetik-Checks.")

problems = {
    "Quantenarme Sättigungsdepression (Hospitalismus 2.0)": {
        "original": "Endogene / Strukturelle Depression",
        "steps": [
            "Erkennen: Materiell überversorgt, sozial/emotional unterversorgt. Mangel vor allem in Sicherheit + Stamm + Sinn.",
            "Hinterfragen: Warum fühle ich mich leer, obwohl äußerlich alles da ist? Viele 'Lösungen' sind mimetisch.",
            "Verinnerlichen: Der Mangel ist real und strukturell. Er lässt sich nicht wegkonsumieren.",
            "Kooperieren: Nicht 'mehr Therapie', sondern Aufbau eines Stamms mit echten Verstehensmomenten."
        ],
        "mimetik": "Hoch — viele moderne Depressionslösungen imitieren Nähe und Sinn, ohne sie zu geben.",
        "memetik": "Sehr hoch — die Idee 'Ich bin depressiv, weil mir etwas fehlt, das ich kaufen kann' verbreitet sich extrem gut."
    },
    "Mimetischer Größenwahn / Surrogat-Selbst": {
        "original": "Narzisstische Persönlichkeitsstörung (CEO-Narzissmus)",
        "steps": [
            "Erkennen: Stark aufgeblähtes Selbstbild bei stark reduzierter affektiver Bindungsfähigkeit.",
            "Hinterfragen: Der enorme Bestätigungshunger kommt meist aus früherem Mangel an echtem Gesehenwerden.",
            "Verinnerlichen: Das grandiose Selbst ist ein Surrogat-Selbst – mächtig, aber extrem fragil.",
            "Kooperieren: Braucht echte, demütigende Begegnungen mit Menschen, die nicht spiegeln."
        ],
        "mimetik": "Sehr hoch — Grandioses Auftreten imitiert Stärke und Erfolg, ist aber oft Abwehr gegen tiefe Scham.",
        "memetik": "Extrem hoch in Social Media, Startup-Welt und Influencer-Kultur."
    },
    "Quanten-oszillierende Bindungsstörung": {
        "original": "Borderline / Emotionale Instabilität",
        "steps": [
            "Erkennen: Extreme Schwankungen zwischen Idealisierung und Entwertung.",
            "Hinterfragen: Die Oszillation ist ein Schutzmechanismus gegen die Angst, wirklich gesehen zu werden.",
            "Verinnerlichen: Die Instabilität ist ein überlebter Versuch mit frühem Bindungsmangel umzugehen.",
            "Kooperieren: Braucht einen verlässlichen Stamm. Der Liebesquant muss langsam und verlässlich aufgebaut werden."
        ],
        "mimetik": "Hoch — viele Beziehungen sind stark mimetisch (Partner als Spiegel oder Retter).",
        "memetik": "Hoch in bestimmten 'trauma-informed' Subkulturen."
    },
    "Bindungslose Machtstrategie": {
        "original": "Antisoziale Persönlichkeitsstörung / Psychopathie",
        "steps": [
            "Erkennen: Geringe affektive Empathie + hohe instrumentelle Intelligenz.",
            "Hinterfragen: Diese Haltung ist oft das Ergebnis früher massiver Enttäuschung oder Gewalt.",
            "Verinnerlichen: Die Strategie zerstört langfristig jede echte Bindung und damit den Liebesquant.",
            "Kooperieren: Sehr schwer. Braucht meist starken äußeren Rahmen + einen nicht-manipulierbaren Menschen."
        ],
        "mimetik": "Hoch — viele 'erfolgreiche' Machtstrategien imitieren Rationalität und Stärke.",
        "memetik": "Sehr hoch in manchen Business- und Sigma-Male-Milieus."
    },
    "Chemischer Surrogat-Quant": {
        "original": "Substanzabhängigkeit (funktionale Formen)",
        "steps": [
            "Erkennen: Die Substanz erzeugt künstlich Zustände, die eigentlich durch echte Beziehung oder sinnvolle Tätigkeit entstehen sollten.",
            "Hinterfragen: Die Substanz ist ein hoch-effizientes Surrogat für den Liebesquant und/oder den Sinn-Quant.",
            "Verinnerlichen: Jede dauerhaft genutzte Substanz verhindert langfristig die Entwicklung echter Quanten.",
            "Kooperieren: Der Ausstieg braucht fast immer einen Stamm. Der Liebesquant muss die Funktion der Substanz übernehmen."
        ],
        "mimetik": "Extrem hoch — die Substanz imitiert Gefühle und Zustände, die eigentlich relational oder existenziell entstehen.",
        "memetik": "Sehr hoch — besonders bei 'funktionalen' Suchtformen, die kulturell toleriert oder gefeiert werden."
    }
}

choice = st.selectbox("Wähle ein zentrales Problem:", list(problems.keys()))

if choice:
    p = problems[choice]
    st.subheader(choice)
    st.caption(f"Ursprüngliche Bezeichnung: {p['original']}")

    st.markdown("### Quant-Anwendung (4 Schritte)")
    for i, step in enumerate(p["steps"], 1):
        st.markdown(f"**{i}.** {step}")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Mimetik-Check**")
        st.info(p["mimetik"])
    with col2:
        st.markdown("**Memetik-Check**")
        st.warning(p["memetik"])

    if st.button("Diesen Bericht als Markdown herunterladen"):
        content = f"""# {choice}

**Ursprüngliche Bezeichnung:** {p['original']}

### Quant-Anwendung

{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(p['steps'])])}

### Mimetik-Check
{p['mimetik']}

### Memetik-Check
{p['memetik']}
"""
        st.download_button(
            label="Download .md",
            data=content,
            file_name=f"problem_{choice[:30].replace(' ', '_')}.md",
            mime="text/markdown"
        )
