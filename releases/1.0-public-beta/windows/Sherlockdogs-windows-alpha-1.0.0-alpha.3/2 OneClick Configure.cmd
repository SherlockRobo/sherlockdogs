@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\oneclick_configure.ps1"
if not exist "%SCRIPT%" goto missing
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
pause
exit /b 0
:missing
echo OneClick Configure script is missing.
pause
exit /b 1
:fail
echo OneClick Configure failed. Run "3 OneClick Repair.cmd" or "4 OneClick Report.cmd".
pause
exit /b 1
