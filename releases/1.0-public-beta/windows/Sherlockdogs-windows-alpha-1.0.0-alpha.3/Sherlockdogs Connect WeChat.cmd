@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\connect_wechat.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0connect_wechat.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Sherlockdogs Connect WeChat failed. Run "3 OneClick Repair.cmd" first, or "4 OneClick Report.cmd" to send evidence.
pause
exit /b 1
