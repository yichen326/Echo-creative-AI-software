# -*- coding: utf-8 -*-
"""修正启动脚本：.bat 必须是纯 ASCII + CRLF，否则 cmd 会解析错乱。"""
import os

ROOT = r"E:\人工智能作业\大作业"

START_BAT = (
    "@echo off\r\n"
    "rem Echo - one click launcher. Keep this file ASCII-only and CRLF.\r\n"
    "cd /d \"%~dp0\"\r\n"
    "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0start.ps1\"\r\n"
    "if errorlevel 1 pause\r\n"
    "exit /b\r\n"
)

STOP_BAT = (
    "@echo off\r\n"
    "rem Echo - stop the background server.\r\n"
    "cd /d \"%~dp0\"\r\n"
    "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0stop.ps1\"\r\n"
    "if errorlevel 1 pause\r\n"
    "exit /b\r\n"
)

STOP_PS1 = (
    "$procs = Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" |\r\n"
    "  Where-Object { $_.CommandLine -like '*run.py*' }\r\n"
    "if ($procs) {\r\n"
    "  $procs | ForEach-Object {\r\n"
    "    Write-Host (\"Stopping PID \" + $_.ProcessId)\r\n"
    "    Stop-Process -Id $_.ProcessId -Force\r\n"
    "  }\r\n"
    "} else {\r\n"
    "  Write-Host 'Echo is not running.'\r\n"
    "}\r\n"
    "Start-Sleep -Seconds 1\r\n"
)

for name, text in (("start.bat", START_BAT), ("stop.bat", STOP_BAT), ("stop.ps1", STOP_PS1)):
    p = os.path.join(ROOT, name)
    with open(p, "w", encoding="ascii", newline="") as f:
        f.write(text)
    b = open(p, "rb").read()
    crlf = b.count(b"\r\n")
    lf = b.count(b"\n") - crlf
    nonascii = sum(1 for c in b if c > 127)
    print("%-10s CRLF=%d LF-only=%d non-ascii=%d" % (name, crlf, lf, nonascii))
