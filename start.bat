@echo off
rem Echo - one click launcher. Keep this file ASCII-only and CRLF.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 pause
exit /b
