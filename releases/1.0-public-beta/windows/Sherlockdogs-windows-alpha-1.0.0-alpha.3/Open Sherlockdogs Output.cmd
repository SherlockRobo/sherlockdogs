@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\open_output.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0open_output.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Open Sherlockdogs Output failed.
pause
exit /b 1
