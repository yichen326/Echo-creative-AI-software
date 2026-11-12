@echo off
rem Echo - stop the background server started by start.bat
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$p = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -like '*run.py*' }; if ($p) { $p | ForEach-Object { Write-Host ('Stopping PID ' + $_.ProcessId); Stop-Process -Id $_.ProcessId -Force } } else { Write-Host 'No Echo server is running.' }; Start-Sleep -Seconds 1"
exit /b
