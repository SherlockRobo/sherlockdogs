@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\configure_nutstore_inbox.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0configure_nutstore_inbox.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
echo.
pause
exit /b 0
:fail
echo Configure Nutstore Inbox failed.
pause
exit /b 1
