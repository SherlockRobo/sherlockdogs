@echo off
setlocal
cd /d "%~dp0packaging\windows-beta"
powershell -NoProfile -ExecutionPolicy Bypass -File preflight.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File doctor.ps1 -Report
if errorlevel 1 goto fail
echo Sherlockdogs installed. Next: open IOS_SHORTCUTS_GUIDE.md and bind a phone share action to your synced Inbox.
pause
exit /b 0
:fail
echo Sherlockdogs start failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
