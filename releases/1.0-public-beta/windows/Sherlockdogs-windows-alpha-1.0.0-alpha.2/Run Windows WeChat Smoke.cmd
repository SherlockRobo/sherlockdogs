@echo off
setlocal
cd /d "%~dp0packaging\windows-beta"
powershell -NoProfile -ExecutionPolicy Bypass -File windows_wechat_smoke.ps1
if errorlevel 1 goto fail
echo Windows WeChat DB smoke passed.
pause
exit /b 0
:fail
echo Windows WeChat DB smoke failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
