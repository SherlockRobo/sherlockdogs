@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\configure_nutstore_inbox.ps1"
echo.
pause
