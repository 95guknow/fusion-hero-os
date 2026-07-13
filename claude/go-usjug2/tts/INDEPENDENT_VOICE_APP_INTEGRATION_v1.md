# Independent Voice Layer – Integration into the Fusion Hero OS Dashboard App (v1)

## Ziel
Die Sprachausgabe (TTS) läuft **vollständig unabhängig** vom Text-Output. Das System kann:
- Nur Stimme ausgeben (ohne Text)
- Nur Text ausgeben
- Beides parallel und synchronisiert
- Full-Duplex: Du sprichst, während ich rede

## Aktueller App-Status (Dashboard)
Die App lebt hauptsächlich in:
- `03_Code/Dashboard/app.py` (Flask/FastAPI + WebSocket-fähig)
- `fusion_hero_os/core/` + `orchestration/agents.py`
- GUI in `03_Code/Dashboard/gui/` + `static/`

## Integrations-Architektur

### 1. TTS Router (neu)
- Neuer zentraler Router in `tts/tts_router.py`
- Entscheidet: Text → Voice? Voice-only? Beides?
- Nutzt Intent Bus (bereits im Core vorhanden)
- QUBO-optimierte Parameter: Geschwindigkeit, Pausenlänge, Betonung, Voice-Selection pro Agent

### 2. Audio Pipeline (entkoppelt)
- Separater WebSocket-Endpunkt `/ws/voice` (neben dem Text-Channel)
- Server-seitig: Streaming-TTS (z.B. Piper lokal, Coqui, oder Edge-TTS als Fallback)
- Client-seitig: Browser AudioContext oder native App-Player
- Keine Blockierung des Text-Kanals

### 3. Master Core Connection
- `heroic_core_orchestrator.py` + `dynamic_orchestration_core.py` erweitern um Voice-Intent
- Jeder Agent (Masterinstanz, QUBO-Optimizer, ASR-Spezialist, Manifest Guardian etc.) kann eigene Voice-Profile haben (Multi-Voice)
- Sisyphos-Zyklus + Eudaimonia-Status beeinflussen Stimme (z.B. ruhiger bei hoher Last)

### 4. UI-Integration (Dashboard)
Neue Controls in `gui/layer_panels.py` oder `gui/interactions.py`:
- Toggle "Voice-Only Mode"
- "Mute Text Output"
- Per-Agent Voice-Selector + Volume
- Real-time Waveform-Visualizer für ausgehende Stimme
- Full-Duplex-Indicator ("Du sprichst – ich höre zu")

### 5. QUBO für Stimme
Erweiterung des bestehenden QUBO-Solvers:
- Variablen: pause_tolerance, prosody_weight, tts_speed, voice_id
- Fitness-Funktion testet gegen echte disfluente Aufnahmen (deine Ähs + Pausen)
- Ziel: Minimale Abbrüche + natürlicher Redefluss

## Umsetzungs-Phasen
1. TTS Router + separater WS-Endpunkt (1-2 Tage)
2. QUBO-Stimmen-Optimierung + Voice-Profile (2-3 Tage)
3. UI-Controls + Waveform (1 Tag)
4. Full-Duplex-Testing mit deiner echten Spracherkennung (1 Tag)
5. Integration in MasterSeed + Horcrux-Sync (1 Tag)

## Nächste Schritte (vorschlag)
- Soll ich sofort `tts/tts_router.py` + WebSocket-Handler als Code-Skelett pushen?
- Oder zuerst die Voice-Profile für die wichtigsten Agenten definieren?
- Oder direkt Patches für `app.py` und `gui/` machen?

**Status:** Bereit für Integration in die laufende App. Alles cross-contamination-bereinigt und mit dem bestehenden Heroic Core + QUBO + Agenten-Struktur kompatibel.