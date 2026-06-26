@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\uninstall.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0uninstall.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Uninstall Sherlockdogs failed.
pause
exit /b 1
