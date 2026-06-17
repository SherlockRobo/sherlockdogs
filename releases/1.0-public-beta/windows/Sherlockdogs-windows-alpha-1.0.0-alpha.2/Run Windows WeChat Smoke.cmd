@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\windows_wechat_smoke.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0windows_wechat_smoke.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
echo Windows WeChat DB smoke passed.
pause
exit /b 0
:fail
echo Windows WeChat DB smoke failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
