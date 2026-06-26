@echo off
setlocal
cd /d "%~dp0"
call "Export Windows Evidence.cmd"
exit /b %ERRORLEVEL%
