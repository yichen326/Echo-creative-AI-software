# -*- coding: utf-8 -*-
"""让一键启动的中文输出不乱码：bat 切 UTF-8 代码页，ps1 设控制台编码。"""
import io
import os

ROOT = r"E:\人工智能作业\大作业"

START_BAT = (
    "@echo off\r\n"
    "rem Echo - one click launcher. Keep this file ASCII-only and CRLF.\r\n"
    "chcp 65001 >nul 2>&1\r\n"
    "cd /d \"%~dp0\"\r\n"
    "powershell -NoProfile -ExecutionPolicy Bypass -File \"%~dp0start.ps1\"\r\n"
    "if errorlevel 1 pause\r\n"
    "exit /b\r\n"
)
with open(os.path.join(ROOT, "start.bat"), "w", encoding="ascii", newline="") as f:
    f.write(START_BAT)

p = os.path.join(ROOT, "start.ps1")
s = io.open(p, encoding="utf-8-sig").read()
if "[Console]::OutputEncoding" not in s:
    s = s.replace(
        '$ErrorActionPreference = "Continue"',
        '$ErrorActionPreference = "Continue"\r\ntry { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }',
        1,
    )
io.open(p, "w", encoding="utf-8-sig", newline="").write(s)
print("patched: start.bat chcp 65001, start.ps1 console utf8")
