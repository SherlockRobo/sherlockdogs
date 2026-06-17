@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\export_windows_evidence.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0export_windows_evidence.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
echo Windows evidence export folder is on your Desktop.
pause
exit /b 0
:fail
echo Export failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
