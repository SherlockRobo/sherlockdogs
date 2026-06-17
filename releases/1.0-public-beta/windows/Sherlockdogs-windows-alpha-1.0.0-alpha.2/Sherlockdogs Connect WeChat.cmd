@echo off
setlocal
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
  echo Sherlockdogs needs Administrator permission once to read the running Windows WeChat key.
  echo Windows will ask for permission now.
  set "SDOGS_CMD=%~f0"
  set "SDOGS_CWD=%~dp0"
  powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath $env:SDOGS_CMD -WorkingDirectory $env:SDOGS_CWD -Verb RunAs"
  exit /b 0
)
set "SCRIPT=%~dp0packaging\windows-beta\connect_wechat.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0connect_wechat.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
pause
exit /b 0
:fail
echo Sherlockdogs Connect WeChat failed. Run "Doctor Sherlockdogs.cmd" and send the latest diagnostics report.
pause
exit /b 1
