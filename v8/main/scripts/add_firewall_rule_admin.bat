@echo off
REM Fusion Hero OS - Firewall rule for Dashboard port 8000 (requires UAC / Administrator)
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File ""%~dp0add_firewall_rule.ps1""' -Wait"
pause