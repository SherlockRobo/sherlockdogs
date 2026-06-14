@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0doctor.ps1" -Report
if errorlevel 1 pause
pause
