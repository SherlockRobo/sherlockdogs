@echo off
setlocal
cd /d "%~dp0"
call "Sherlockdogs Start.cmd"
exit /b %ERRORLEVEL%
