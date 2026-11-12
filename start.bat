@echo off
rem Echo - one click launcher (ASCII only, safe for any console code page)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0启动.ps1"
if errorlevel 1 pause
exit /b
