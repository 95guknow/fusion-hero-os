#!/usr/bin/env python3
"""Ingest v4 training pairs for Geisteskrankheiten 4D Matrix."""
import json
from pathlib import Path

pairs = [
    {
        "prompt": "Wie haengt I(Z) mit der heroischen Mathematik S(psi) zusammen?",
        "response": "Modell-Bruecke: I(Z)=Summe |Delta| entspricht ||Im(psi)||. S(psi)=||Re(psi)||^2 - lambda||Im(psi)||^2. Hohes I(Z) = hoher imaginaerer Anteil. Heilung senkt Im via psi>phi (Habituation mit Umkehr).",
    },
    {
        "prompt": "Was ist psi>phi in der 4D-Matrix Psychiatrie?",
        "response": "Habituation mit Umkehr des imaginaeren Raums. alpha2 Kalibrieren: Im(psi)-Im(phi) senkt I(Z). Jede Spiegelung (Stamm, Therapeut) ist eine psi>phi-Operation. alpha3: Sisyphos-Zyklen mit Netto-Gewinn senken d(Z,Z*).",
    },
    {
        "prompt": "Erklaere q1b1 und b2q2 fuer Zwangsstoerung und ADHS.",
        "response": "OCD: b2q2 (Ritual binär) -> q1b1 via EX/RP. ADHS: q1b1 (Impuls quantisiert) -> b2q2 (externe Struktur). [q,b]!=0: Interventionsreihenfolge zaehlt.",
    },
    {
        "prompt": "Wie mappt die heroische Informatik Layer-Architektur auf Psychiatrie?",
        "response": "L0 Fundament=Krisenplan/Epistemik. L1=PeerReview+Evidenz A/B/C. L2=alpha1/2/3 konkret. L3=Rueckfall-Audit. L4=Langzeit-Rekonstruktion Z*. Stoerung=Layer-Vermischung (z.B. GAD=L4 auf L0).",
    },
    {
        "prompt": "Was ist QUBO-Triage in der MER 4D-Matrix?",
        "response": "Modell: E(x)=x^T Q x, x_i=Achse behandeln. QUBO findet Naeherungs-Optimum welche Intervention d(Z,Z*) am effizientesten senkt. Entspricht Heilungs-Gradient (groesster |Wert| zuerst) plus Kopplungsgesetz.",
    },
    {
        "prompt": "Neurotheologie Newberg: was traegt fuer die 4D-Matrix, was nicht?",
        "response": "Traegt (Bedingt): Meditation deaktiviert DMN messbar; DMN-Hyperaktivitaet korreliert mit G+ Gruelen. Nicht: weitere Zeitdimension (Fragment). Substanz umgeht Psycholyse (ausserhalb MER-Pfad). Gerichtete Psycholyse senkt Im, ungerichtet erhoeht Im.",
    },
    {
        "prompt": "Wann ist Meditation in der 4D-Matrix kontraindiziert?",
        "response": "Aktive Schizophrenie, Manie, akute Suizidalitaet ohne alpha1. PTBS nur nach S-Stabilisierung mit Stamm. OCD: nur mit EX/RP, nicht freies Meditieren (Schleifengesetz). GAD/Depression stabil: MBCT/MBSR nach alpha1.",
    },
    {
        "prompt": "Was sind die v4 Bewegungsgesetze Ergaenzungen?",
        "response": "Verinnerlichungsgesetz: gerichtete Psycholyse senkt Im. DMN-Gesetz: DMN-Hyperaktivitaet stabilisiert G+-Gruelen. [q,b]!=0: Achsen-Reihenfolge nicht vertauschbar. Stamm liefert phi fuer psi>phi.",
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