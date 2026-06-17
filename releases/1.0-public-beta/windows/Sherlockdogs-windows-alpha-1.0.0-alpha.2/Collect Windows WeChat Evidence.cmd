@echo off
setlocal
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ". '%USERPROFILE%\.sherlockdogs\config.ps1'; & $env:PYTHON_BIN '%~dp0scripts\collect_windows_wechat_db_evidence.py' --write"
if errorlevel 1 goto fail
echo Windows WeChat DB smoke evidence generated.
pause
exit /b 0
:fail
echo Evidence is not ready yet. Forward a #2 item to yourself in WeChat, wait for Windows WeChat to receive it, then rerun this command.
pause
exit /b 1
