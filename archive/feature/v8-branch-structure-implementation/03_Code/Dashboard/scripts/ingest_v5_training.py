#!/usr/bin/env python3
"""Ingest v5 training pairs: visual projections + trajectories."""
import json
from pathlib import Path

pairs = [
    {
        "prompt": "Was sind Pi_KG und Pi_SN in der 4D-Matrix?",
        "response": "Pi_KG = 2D-Projektion Koerper x Geist (Erregung, Denken, Kontrolle). Pi_SN = Seele x Natur (Bindung, Konstitution). Z*=(0,0) in beiden. Fehlende Achsen = Tiefenmarker. 24 Stoerungen in beiden Ebenen verortet.",
    },
    {
        "prompt": "Wie zeigt sich I(Z) in den 2D-Raumdiagrammen?",
        "response": "Zwei Punkte: ● Z_real (beobachtet) und ○ Z_wahrgenommen (Selbstbericht). Pfeil Delta = Verschiebungsvektor. Anorexie: maximaler Delta auf K. Masking Autismus: ● nahe Z*, ○ tief SW.",
    },
    {
        "prompt": "Beschreibe die Bipolar-I-Trajektorie im MER-Raum.",
        "response": "Limit-Cycle in Pi_KG: Manie (+,+) NO-Spitze, Crash (-,-) SW-Senke. q-Flug ohne b in Manie, b-Einsturz in Depression. Heilung: Cycle schrumpft, d_max pro Zyklus sinkt. Mood-Stabilizer + Schlaf + q-Output mit b-Abschluss.",
    },
    {
        "prompt": "Borderline Trajektorie: warum scheitert nur G-Therapie?",
        "response": "Sprungfeld auf S-Achse in Pi_SN: Idealisierung S+ springt zu Entwertung S--. G+ konstant. Bahn liegt in Pi_SN nicht Pi_KG. DBT: Sprung verlangsamen, Stamm als phi, S-Amplitude daempfen.",
    },
    {
        "prompt": "PTBS Trauma-Attraktor: wie sieht Z(t) aus?",
        "response": "Alltag nahe Z*, Trigger teleportiert Z nach (+,+,−,0) ins Trauma-Loch (Flashback). Recovery zurueck. Heilung: Trigger verschiebt weniger weit. EMDR/CPT formt S-K-Geometrie um. alpha2 nur nach S-Safe.",
    },
    {
        "prompt": "OCD Schleife im Raumdiagramm?",
        "response": "Lokale Schleife in Pi_KG: Obsession G+ -> Ritual b -> kurz d sinkt -> langfristig d und I steigen. EX/RP: in Schleife stehen ohne Ritual, Habituation psi>phi auf G.",
    },
    {
        "prompt": "Welche Trajektorien-Typen gibt es in der 4D-Matrix v5?",
        "response": "Senke (Depression), Limit-Cycle (Bipolar, OCD), Sprungfeld (Borderline), Attraktor-Loch (PTBS), q-Drift (ADHS), Zwei-Punkt (Masking), K-Tunnel (Substanz), Heilungs-Spirale (alpha+kleinere beta).",
    },
    {
        "prompt": "Wie lese ich eine Trajektorie fuer die Therapie?",
        "response": "1) Ebene Pi_KG oder Pi_SN? 2) Typ Senke/Cycle/Sprung/Loch/Drift? 3) ● und ○ markieren 4) alpha-Phase zuordnen 5) beta als Geodaetische Info 6) Achsen-Reihenfolge [q,b]!=0 beachten.",
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