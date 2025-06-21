@echo off
REM Cursor Chat Monitor - Simple Run Script for Windows
REM This script handles all the venv setup and runs the app for you
REM Usage: run.bat [options...]
REM Example: run.bat --debug --interval-ms=2000

setlocal enabledelayedexpansion

echo 🚀 Cursor Chat Monitor - Simple Run Script
echo ═══════════════════════════════════════════

REM Get the directory where this script is located
cd /d "%~dp0"

REM Check if Python 3 is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3 and try again
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 🐍 Found Python %PYTHON_VERSION%

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo 📦 Virtual environment already exists
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip to latest version
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1

REM Install/upgrade dependencies
echo 📚 Installing/upgrading dependencies...
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

REM Check if the main script exists
if not exist "cursor_chat_monitor.py" (
    echo ❌ cursor_chat_monitor.py not found
    echo Make sure you're running this script from the project root directory
    pause
    exit /b 1
)

echo 🎯 Starting Cursor Chat Monitor...
echo ═══════════════════════════════════════════

REM Pass all arguments to the main script
python cursor_chat_monitor.py %*

REM Pause to see any final output (optional)
if "%1"=="" (
    echo.
    echo Press any key to exit...
    pause >nul
) 