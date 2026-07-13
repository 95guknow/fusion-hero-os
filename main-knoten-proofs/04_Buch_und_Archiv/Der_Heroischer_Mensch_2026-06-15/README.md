# Der heroische Mensch — Gesamtpaket (Stand 15. Juni 2026)

Dieses Archiv enthält alle erarbeiteten Versionen auf dem neuesten Stand.

## Inhalt

### 1. CLI_Version (Standalone .exe)
- `heroic_program/` — Vollständiges interaktives CLI-Programm
- `README_BUILD_EXE.md` — Anleitung zum Erstellen der Windows-.exe
- `build_windows_exe.bat` — Automatisches Build-Skript

**So baust du die .exe:**
1. Ordner auf Windows kopieren
2. `build_windows_exe.bat` ausführen
3. Fertige `.exe` liegt in `dist/`

### 2. Web_Version (Moderne Streamlit-App)
- `web_app/` — Vollständige Webapplikation mit 5 Modulen + Philosophischer Knotenanalyse
- Integrierte Cross-Module-Funktionen (Stufe 2)
- Erstes Dashboard (Stufe 3 Ansatz)

**Starten:**
```bash
cd Web_Version/web_app
pip install -r requirements.txt
streamlit run app.py
```

### 3. Dokumentation
- `Zwischenbericht_Stufe1_Stufe2.md` — Entwicklungsstand und nächste Schritte

## Empfehlung

- Für **einfache Nutzung ohne Browser** → CLI-Version → `.exe` bauen
- Für **moderne, vernetzte Nutzung** → Web-Version (empfohlen)

Entwickelt iterativ in 3 Stufen (Grundlage → Integration → Fortgeschrittene Features).
