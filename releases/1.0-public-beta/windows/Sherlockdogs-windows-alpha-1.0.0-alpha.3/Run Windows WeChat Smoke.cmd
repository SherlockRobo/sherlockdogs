@echo off
setlocal
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
  echo Sherlockdogs Windows WeChat smoke may need Administrator permission to prepare the local WeChat DB.
  echo Windows will ask for permission now.
  set "SDOGS_CMD=%~f0"
  set "SDOGS_CWD=%~dp0"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath $env:SDOGS_CMD -WorkingDirectory $env:SDOGS_CWD -Verb RunAs"
  exit /b 0
)
set "SCRIPT=%~dp0packaging\windows-beta\windows_wechat_smoke.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0windows_wechat_smoke.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
echo Windows WeChat DB smoke passed.
pause
exit /b 0
:fail
echo Windows WeChat DB smoke failed. Run "3 OneClick Repair.cmd" first, or "4 OneClick Report.cmd" to send evidence.
pause
exit /b 1
