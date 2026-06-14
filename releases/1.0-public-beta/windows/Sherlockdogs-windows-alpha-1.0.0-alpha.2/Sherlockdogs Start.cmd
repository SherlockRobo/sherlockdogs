@echo off
setlocal
cd /d "%~dp0packaging\windows-beta"
powershell -NoProfile -ExecutionPolicy Bypass -File preflight.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File doctor.ps1 -Report
if errorlevel 1 goto fail
echo Sherlockdogs installed. Run "Configure Nutstore Inbox.cmd" if you have not bound your Nutstore folder yet.
pause
exit /b 0
:fail
echo Sherlockdogs start failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
