# Der heroische Mensch — Windows .exe erstellen

## Voraussetzungen (auf Windows)

1. Python 3.10 oder 3.11 installiert
2. Git (optional, aber empfohlen)

## Schritt-für-Schritt Anleitung

### 1. Projekt herunterladen / kopieren

Kopiere den gesamten Ordner `heroic_program` auf deinen Windows-Rechner.

### 2. Virtuelle Umgebung erstellen (empfohlen)

Öffne PowerShell oder CMD im Ordner `heroic_program` und führe aus:

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Abhängigkeiten installieren

```powershell
pip install -r requirements.txt
pip install pyinstaller
```

### 4. .exe bauen

Führe die mitgelieferte Batch-Datei aus:

```powershell
build_windows_exe.bat
```

Oder manuell:

```powershell
pyinstaller --onefile --name "Der_Heroische_Mensch" main.py
```

### 5. Fertige .exe

Nach dem Build findest du die ausführbare Datei hier:

```
dist\Der_Heroische_Mensch.exe
```

Kopiere diese `.exe` an einen beliebigen Ort und starte sie per Doppelklick.

## Hinweise

- Die erste Ausführung kann etwas länger dauern (PyInstaller entpackt sich).
- Alle Daten (philosophers_nodes.json etc.) sind im `data`-Ordner enthalten und werden automatisch mit eingebunden.
- Die Anwendung läuft komplett offline.
