@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
title CommandScout - Tactical Syntax & Scaffolding Studio v2.0
cd /d "%~dp0"
cls

echo ======================================================================
echo              COMMANDSCOUT: TACTICAL SYNTAX & SCAFFOLDING
echo            Linux/Kali + Windows/PowerShell 7 + Android/ADB
echo ======================================================================
echo.

:: Portable Python runtime detection
set "PY_EXEC="
if exist "%PY_BIN%" set "PY_EXEC=%PY_BIN%"
if not defined PY_EXEC if exist "C:\Users\daddy\miniconda3\python.exe" set "PY_EXEC=C:\Users\daddy\miniconda3\python.exe"
if not defined PY_EXEC where py.exe >nul 2>&1 && set "PY_EXEC=py.exe -3"
if not defined PY_EXEC where python.exe >nul 2>&1 && set "PY_EXEC=python.exe"

if not defined PY_EXEC (
    echo [ERROR] No Python runtime found on system PATH or Miniconda!
    echo Please install Python 3.10+ or set the PY_BIN environment variable.
    pause
    exit /b 1
)

echo [*] Starting CommandScout with: %PY_EXEC%
%PY_EXEC% "%~dp0command_scout.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] CommandScout exited with code: %ERRORLEVEL%
    pause
)
