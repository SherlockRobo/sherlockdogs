@echo off
setlocal
cd /d "%~dp0packaging\windows-beta"
powershell -NoProfile -ExecutionPolicy Bypass -File connect_wechat.ps1
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Sherlockdogs Connect WeChat failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
