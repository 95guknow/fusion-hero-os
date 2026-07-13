#!/usr/bin/env python3
import json
from pathlib import Path

pairs = [
    {
        "prompt": "Was ist die Heroismus Edition 0.6 und 0.7?",
        "response": "Kritische Gesamtedition des Heroik-Korpus. 0.6: Redaktionsprinzipien, Leitthese, Kap1 Genese 1.4.-1.7.2026, Kap2 Fusion OS Architektur. 0.7: + Mapping Philosophie-Technik, versions/ Archiv. Keine Vorgaben ueberschreiben.",
    },
    {
        "prompt": "Mapping Heroismus Edition: Sisyphos-Zyklus und 4D-Matrix?",
        "response": "Edition: Self-Update+Rollback+Audit. Matrix: beta-Rueckfall als Geodaetische Info, Heilungs-Spirale. Kontrollierte Level-Drops = Sisyphos mit Netto-Gewinn. Modell, kein Satz.",
    },
    {
        "prompt": "Psycholyse in Heroismus Edition und MER?",
        "response": "Edition: Evolver+Peer-Review, dialektische Loewen-Aufloesung. Ostern 2026 6-Tage Psycholyse als Genese. Matrix: gerichtete Psycholyse=alpha2 psi>phi; ungerichtet erhoeht Im. Schritt 4 Kooperation=Stamm.",
    },
    {
        "prompt": "Layer 6 w bis Layer 0 in Psychiatrie-MER?",
        "response": "L6w=Z* Attraktor. L4=Langzeit-Rekonstruktion. L3=beta-Audit. L2=alpha1/2/3. L1=PeerReview+FormalMath. L0=Krisenplan, Schicht-Ue-Warnung. Aus Heroismus Kap2 Architektur.",
    },
    {
        "prompt": "Leitthese Heroismus Edition und 4D-Matrix?",
        "response": "Edition untersucht nicht ob Heroik wahr ist, sondern wie Korpus unter Intensitaet entsteht. Matrix: Landkarte+Geltung, nicht Wahrheitsbeweis. Rekonstruktivistisch doppelt: Dokument rekonstruiert Rekonstruktion v2-v7.",
    },
]

p = Path(r"C:\Users\Admin\fusion-hero-os\03_Code\internal_llm\data.jsonl")
existing = {json.loads(l).get("prompt", "") for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}
added = 0
with p.open("a", encoding="utf-8") as f:
    for row in pairs:
        if row["prompt"] not in existing:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            added += 1
print(json.dumps({"added": added}))