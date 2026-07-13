@echo off
echo === PC to Phone Audio Bridge (with Auto Compensation) ===
echo.
echo Options:
echo   1. python bridge.py --calibrate     (measure delay automatically)
echo   2. python bridge.py --phone-ip 192.168.1.42 --compensate 50
echo.
set /p PHONE_IP=Enter phone IP (or leave for interactive): 
if "%PHONE_IP%"=="" (
    python bridge.py
) else (
    set DEVICE=Stereo Mix (Realtek Audio)
    echo Using device: %DEVICE%
    python bridge.py --phone-ip %PHONE_IP% --device "%DEVICE%"
)
pause
