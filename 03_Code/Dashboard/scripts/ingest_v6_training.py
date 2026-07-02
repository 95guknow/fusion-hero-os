#!/usr/bin/env python3
import json
from pathlib import Path

pairs = [
    {
        "prompt": "Was bedeuten Schicht S, F und Ue in der 4D-Matrix Psychiatrie?",
        "response": "S=MER-Substanz (K/G/S/N, Hospitalismus, qob). F=Formalisierung (psi>phi, Geltungskategorien). Ue=Warnschicht: Entkategorisierung, Modal-Kollaps, mimetische statt memetische Heilung. Matrix bleibt S+F, Ue ist Selbstkritik.",
    },
    {
        "prompt": "Wie haengt Hospitalismus 2.0 mit der 4D-Matrix zusammen?",
        "response": "Quantenarmut bei Mengenueberfluss (Spitz/A.4): S- Surrogat (Likes, Follower), d moderat aber Zufriedenheitsquant minimal. Therapie ohne Stamm = mimetisch. Heilung: echtes Verstandenwerden senkt d auf S-Achse.",
    },
    {
        "prompt": "Concept Space D4 Rekonstruktivismus und I(Z)?",
        "response": "Rekonstruktivismus: weder naiver Realismus noch reiner Konstruktivismus. Z_real vs Z_wahrgenommen = alpha2 Kalibrierung. Memetisch = Z_real bewegt sich. Mimetisch = nur Narrativ/I aendert sich.",
    },
    {
        "prompt": "A.3 Ebenenvermischung Person Stamm System in der Psychiatrie?",
        "response": "Person ohne Stamm = Narzissmus G+ S-. Stamm im System = Borderline-Idealisierung Therapeut. System im Stamm = Diagnose als Identitaet/Stigma. Heilung: jede Logik an ihren Ort, QUBO-Triage.",
    },
    {
        "prompt": "Vierschritt A.10 und MER-Behandlungsphasen?",
        "response": "1 Erkennen=alpha1, 2 Hinterfragen=alpha2 I senken, 3 Verinnerlichen=alpha3 d senken, 4 Kooperation=Stamm-Validierung. Ohne Schritt 4 bleibt Heilung stumm. Ungerichtete Psycholyse = Passion ohne Anlass.",
    },
    {
        "prompt": "Was verbietet die Dissertation der 4D-Matrix-Anwendung?",
        "response": "Entkategorisierung (Evidenz streichen), Modal-Kollaps (Modell als Diagnose), Selbst-Mythologisierung, Monumentalisierung, Phoenix-Mode (Symptom ohne d-Senkung). Bescheidenheit vor Autoritaet.",
    },
]

p = Path(r"C:\Users\Admin\fusion-hero-os\03_Code\internal_llm\data.jsonl")
existing = set()
for line in p.read_text(encoding="utf-8").splitlines():
    if line.strip():
        existing.add(json.loads(line).get("prompt", ""))
added = 0
with p.open("a", encoding="utf-8") as f:
    for row in pairs:
        if row["prompt"] not in existing:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            added += 1
print(json.dumps({"added": added, "total_new_pairs": len(pairs)}))