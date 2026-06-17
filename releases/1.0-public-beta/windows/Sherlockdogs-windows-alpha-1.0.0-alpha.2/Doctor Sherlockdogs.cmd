@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\doctor.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0doctor.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" -Report
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Doctor failed.
pause
exit /b 1
