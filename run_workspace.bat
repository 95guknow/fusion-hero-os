@echo off
REM Optional: NiceGUI Legacy-Workspace auf Port 8080
REM Standard-GUI ist das FastAPI Dashboard auf Port 8000 (run_backend.bat)
REM Nur starten mit: start_all.ps1 -NiceGUI
cd /d "%~dp003_Code\Dashboard"
"C:\Users\Admin\venv\Scripts\python.exe" workspace.py