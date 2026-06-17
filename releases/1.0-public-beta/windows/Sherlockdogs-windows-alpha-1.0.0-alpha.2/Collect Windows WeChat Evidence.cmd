@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\collect_windows_wechat_evidence.ps1"
if not exist "%SCRIPT%" set "SCRIPT=%~dp0collect_windows_wechat_evidence.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
echo Windows WeChat DB smoke evidence generated.
pause
exit /b 0
:fail
echo Evidence is not ready yet. Forward a #2 item to yourself in WeChat, wait for Windows WeChat to receive it, then rerun this command.
pause
exit /b 1
