#!/usr/bin/env python3
import json
from pathlib import Path

pairs = [
    {
        "prompt": "Welche Abbildungen gibt es zur MER 4D-Matrix?",
        "response": "9 SVG-Diagramme: 01 4D-Raum, 02 Pi_KG, 03 Pi_SN, 04 Schattenhuelle I(Z), 05 Bipolar Limit-Cycle, 06 PTBS Attraktor, 07 alpha1-3, 08 Gesamt-Pipeline, 09 memetisch/mimetisch. Code-generiert, Kompendium-Farben, Modell kein DSM-Ersatz.",
    },
    {
        "prompt": "Was zeigt die Projektion Pi_KG?",
        "response": "Koerper x Geist: K vertikal, G horizontal. Z* im Ursprung. Stoerungspunkte GAD/Manie R2 NO, Depression R1 SW, OCD Schleife R4, Panik K+ Spitze. Skala -1/0/+1.",
    },
    {
        "prompt": "Abbildung Schattenhuelle I(Z)?",
        "response": "Z_real (voller Kreis) vs Z_wahrgenommen (leerer Kreis). Pfeil Delta. Anorexie: K invertiert. Masking: real nahe Z*, wahrgenommen tief. Rekonstruktivismus D4 = alpha2 kalibriert Delta.",
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