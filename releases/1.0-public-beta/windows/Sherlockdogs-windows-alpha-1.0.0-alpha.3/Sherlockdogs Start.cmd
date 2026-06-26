@echo off
setlocal
cd /d "%~dp0packaging\windows-beta"
powershell -NoProfile -ExecutionPolicy Bypass -File preflight.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
if errorlevel 1 goto fail
powershell -NoProfile -ExecutionPolicy Bypass -File doctor.ps1 -Report
if errorlevel 1 goto fail
echo Sherlockdogs installed. Next: run "Sherlockdogs Connect WeChat.cmd". It can use an existing decrypted DB folder or try the local decrypt helper.
pause
exit /b 0
:fail
echo Sherlockdogs start failed. Run "OneClick Codex Help.cmd" first, or "Doctor Sherlockdogs.cmd" for diagnostics.
pause
exit /b 1
