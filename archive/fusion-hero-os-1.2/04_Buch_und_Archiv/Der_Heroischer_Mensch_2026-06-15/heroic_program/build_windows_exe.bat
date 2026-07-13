@echo off
echo ==========================================
echo   Der heroische Mensch - Einfacher Build
echo ==========================================
echo.
echo Wechsle in den richtigen Ordner...
cd /d "%~dp0"

echo.
echo Baue die .exe Datei...
pyinstaller --onefile --name "Der_Heroische_Mensch" --add-data "data;data" main.py

echo.
echo ==========================================
echo   Fertig! Die .exe liegt im Ordner "dist"
echo ==========================================
pause

@echo off
echo ============================================
echo   Der heroische Mensch - .exe Builder
echo ============================================
echo.

REM Virtuelle Umgebung aktivieren, falls vorhanden
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Installiere / Aktualisiere PyInstaller...
pip install pyinstaller --quiet

echo.
echo Baue die .exe Datei...
pyinstaller --onefile --name "Der_Heroische_Mensch" --add-data "data;data" --add-data "exports;exports" main.py

echo.
echo ============================================
echo   Build abgeschlossen!
echo   Die .exe befindet sich im Ordner: dist\
echo ============================================
pause
