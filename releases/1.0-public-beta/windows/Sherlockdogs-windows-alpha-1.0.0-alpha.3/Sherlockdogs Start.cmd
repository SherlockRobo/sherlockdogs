@echo off
setlocal
cd /d "%~dp0packaging\windows-beta"
powershell -NoProfile -ExecutionPolicy Bypass -File preflight.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File doctor.ps1 -Report
if errorlevel 1 goto fail
echo Sherlockdogs installed. Next: run "2 OneClick Configure.cmd". It chooses output paths and connects Windows WeChat.
pause
exit /b 0
:fail
echo Sherlockdogs start failed. Run "3 OneClick Repair.cmd" first, or "4 OneClick Report.cmd" to send evidence.
pause
exit /b 1
