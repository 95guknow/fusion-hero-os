# Interne LLM-Trainingsumgebung

Lokales Fine-Tuning mit `llama-cpp-python`, LoRA/QLoRA und GGUF-Modellen.

## Voraussetzungen

- Python 3.10+
- Windows/macOS/Linux
- Optional: CUDA-fähige GPU für schnelleres Training

## Installation

```powershell
pip install -r requirements.txt
```

## Training vorbereiten

1. Lege dein GGUF-Modell in `model_path` in `config.yaml` ein (oder lass es `null` für den Dummy-Lauf).
2. Passe `data.jsonl` an deine Domäne an.

Format:

```json
{"prompt": "Frage", "response": "Antwort"}
```

## Training starten

```powershell
python train.py
```

Mit eigener Konfiguration:

```powershell
python train.py --config mein_config.yaml
```

## Speicherbedarf

- CPU-only: `estimated_total_gb` aus `train.py` beachten.
- Q4_K_M + LoRA rank 8 reicht für 7B-Modelle auf Consumer-Hardware (8GB RAM/VRAM).

## LoRA vs Full Fine-Tuning

- **LoRA/QLoRA**: Niedrig-rangige Adapter, wenig VRAM/RAM, schnell.
- **Full Fine-Tuning**: Nur für sehr kleine Modelle oder große GPUs empfehlenswert.
