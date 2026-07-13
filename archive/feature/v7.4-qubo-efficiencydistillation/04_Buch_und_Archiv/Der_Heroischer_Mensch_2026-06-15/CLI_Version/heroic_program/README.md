# Der heroische Mensch — Interaktives Programm

Einzelnes ausführbares Programm, das **Theorie** und **praktische Anwendung** des Werks vereint.

## Features

- Vollständiger Concept Space (4 Ebenen)
- Alle wichtigen Philosophen seit Jesus verorten & verstehen
- **Geführter Quant-Modus** mit Multiple-Choice-Fragen (max. 5 Optionen pro Schritt)
- Einfache, klare Menüführung
- Erweiterbar und modular

## Schnellstart (Python)

```bash
python main.py
```

## Windows .exe erstellen

Siehe Datei: **README_BUILD_EXE.md**

Kurzversion:
```cmd
pip install pyinstaller
pyinstaller --onefile --name "HeroischerMensch" main.py
```

Die fertige `.exe` findest du dann in `dist\HeroischerMensch.exe`

## Dateien im Paket

- `main.py` — Das Hauptprogramm
- `data/philosophers_nodes.json` — Strukturierte Datenbank aller Knoten
- `build_windows_exe.bat` — Einfacher Build-Helfer für Windows
- `README_BUILD_EXE.md` — Detaillierte Anleitung für den .exe-Build

## Philosophie des Programms

- Eine einzige ausführbare Datei soll reichen
- Theorie und Anwendung gehören zusammen
- Bei Unklarheiten führt das Programm mit klaren Multiple-Choice-Fragen
- Datenbank-basiert (JSON) → leicht erweiterbar

---

Der Stein rollt weiter.