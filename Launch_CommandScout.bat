@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title CommandScout - Tactical Syntax & Scaffolding Studio
cd /d "%~dp0"
cls

echo ======================================================================
echo              COMMANDSCOUT: TACTICAL SYNTAX & SCAFFOLDING
echo            Linux & Kali Security + Windows & PowerShell Hub
echo ======================================================================
echo.

C:\Users\daddy\miniconda3\python.exe command_scout.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] CommandScout exited with code: %ERRORLEVEL%
    pause
)
