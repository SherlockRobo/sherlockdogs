@echo off
setlocal
cd /d "%~dp0"
set "SCRIPT=%~dp0packaging\windows-beta\oneclick_codex_help.ps1"
if not exist "%SCRIPT%" goto missing
powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%"
if errorlevel 1 goto fail
pause
exit /b 0
:missing
echo OneClick Codex Help script is missing.
pause
exit /b 1
:fail
echo OneClick Codex Help finished with warnings or failed. Send the opened evidence folder back to the operator.
pause
exit /b 1
