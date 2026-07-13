# Interner LLM-Inference-Param-Optimizer (v1)

Optimiert **Generation-Parameter** (temperature, top_p, repeat_penalty) für ein
lokales GGUF-Modell via `llama-cpp-python` — mit dem Heroic-Algorithmus
(QUBO-Beispielauswahl + Simulated Annealing über die Parameter).

**Ehrlicher Scope:** Dies ist KEIN Fine-Tuning. Es werden keine Modellgewichte
verändert, kein LoRA/QLoRA trainiert und keine Adapter erzeugt. `train.py`
heißt aus historischen Gründen so; der Modus `heroic` ist ein
Inference-Param-Optimizer (gemessene F1-Verbesserung im Audit: ~2 %,
siehe `docs`-Audit heroic_qubo_annealing_v1).

## Voraussetzungen

- Python 3.10+
- Windows/macOS/Linux
- Optional: CUDA-fähige GPU für schnellere Inferenz während der Bewertung

## Installation

```powershell
pip install -r requirements.txt
```

## Lauf vorbereiten

1. Lege dein GGUF-Modell in `model_path` in `config.yaml` ein (oder lass es `null` für den Dummy-Lauf).
2. Passe `data.jsonl` an deine Domäne an (dient als Bewertungs-Datensatz, nicht als Trainingsdaten).

Format:

```json
{"prompt": "Frage", "response": "Antwort"}
```

## Optimierung starten

```powershell
python train.py
```

Mit eigener Konfiguration:

```powershell
python train.py --config mein_config.yaml
```

## Speicherbedarf

- CPU-only: `estimated_total_gb` aus `train.py` beachten.
- Q4_K_M reicht für 7B-Modelle auf Consumer-Hardware (8GB RAM/VRAM), da nur inferiert wird.

## Wenn du echtes Fine-Tuning willst

LoRA/QLoRA-Training ist mit diesem Modul **nicht** möglich. Dafür braucht es
einen separaten Stack (z. B. `peft` + `transformers` auf den unquantisierten
Gewichten, oder `llama.cpp`-Finetune-Tooling). Sobald das existiert, hier
verlinken — bis dahin gilt: dieses Verzeichnis optimiert nur Inference-Parameter.
