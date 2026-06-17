@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "packaging\windows-beta\collect_windows_wechat_evidence.ps1"
if errorlevel 1 goto fail
echo Windows WeChat DB smoke evidence generated.
pause
exit /b 0
:fail
echo Evidence is not ready yet. Forward a #2 item to yourself in WeChat, wait for Windows WeChat to receive it, then rerun this command.
pause
exit /b 1
