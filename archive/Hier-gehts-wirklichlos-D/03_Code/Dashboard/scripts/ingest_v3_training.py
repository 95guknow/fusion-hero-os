import json
from pathlib import Path

pairs = [
    {
        "prompt": "Wo liegt Depression (endogen) im 4D-Raum Z=(K,G,S,N)?",
        "response": "Z=(-,-,-,-), Region R1 Niedrig-N, d=4. Tiefe Senke auf allen Achsen. I(Z) mittel: 'es wird nie besser'. Hebel: N->K dann S.",
    },
    {
        "prompt": "Was sind die 8 Raumregionen der Geisteskrankheiten-4D-Matrix?",
        "response": "R1 Niedrig-N, R2 Hoch-G/K, R3 S-Defizit, R4 G-Uebersteuerung, R5 Oszillationsbahn, R6 Trauma-Attraktor, R7 N-Entwicklung, R8 K-Surrogat.",
    },
    {
        "prompt": "Erklaere I(Z) als Schattenhuelle im MER-Raum.",
        "response": "Delta = Z_wahrgenommen - Z_real. I(Z)=Summe |Delta|. Hohes I bei moderatem d = Masking. Memetische Heilung senkt d, mimetische nur I.",
    },
    {
        "prompt": "Welche drei Phasen hat der MER-Loesungsansatz fuer Geisteskrankheiten?",
        "response": "alpha1 Stabilisieren, alpha2 Kalibrieren (I senken), alpha3 Rekonstruieren (d Richtung Z*). beta-Rueckfall = Geodaetische Info.",
    },
    {
        "prompt": "Wie ist Borderline im 4D-Raum verortet und was ist der Loesungspfad?",
        "response": "Z=(+,+-,-,-), Region R5. Loesung: DBT, Schematherapie, S stabilisieren, verlaesslicher Stamm. Keine Idealisierung/Entwertung im Buendnis.",
    },
    {
        "prompt": "Was besagt das Stigma-Gesetz im psychiatrischen MER-Raum?",
        "response": "Externes Delta verschiebt Z_wahrgenommen ohne Z_real zu aendern. I steigt. Besonders N-Achse: Charakter statt Biologie.",
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
print(json.dumps({"added": added}))