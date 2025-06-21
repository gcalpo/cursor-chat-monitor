@echo off
REM Windows Build Script for cursor-chat-monitor
REM Handles complete build process including virtual environment setup

setlocal enabledelayedexpansion

echo 🪟 Windows Build Script for cursor-chat-monitor
echo ==============================================

REM Check if we're on Windows
if not "%OS%"=="Windows_NT" (
    echo ❌ This script is for Windows only
    echo 💡 Use build-macos.sh for macOS or build-linux.sh for Linux
    exit /b 1
)

REM Check Python installation
echo 🐍 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo 💡 Install Python 3.8+ from https://python.org
    echo 💡 Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

REM Check minimum Python version (basic check - assumes format X.Y.Z)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 3.8+ required, found %PYTHON_VERSION%
    pause
    exit /b 1
)
echo ✅ Python version meets requirements (3.8+)

REM Check if virtual environment exists
if exist "venv" (
    echo 📁 Virtual environment found
    set /p RECREATE="🔄 Remove existing venv and create fresh? [y/N]: "
    if /i "!RECREATE!"=="y" (
        echo 🧹 Removing existing virtual environment...
        rmdir /s /q venv
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 🔧 Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ❌ Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo 📦 Upgrading pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Failed to upgrade pip, continuing...
)

REM Install dependencies
echo 📦 Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed from requirements.txt
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Check Windows-specific dependencies
echo 🔍 Checking Windows-specific dependencies...

REM Check for pywin32
python -c "import win32api" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pywin32 missing
    echo 📦 Installing pywin32...
    pip install pywin32
    if %errorlevel% neq 0 (
        echo ❌ Failed to install pywin32
        pause
        exit /b 1
    )
) else (
    echo ✅ pywin32 available
)

REM Check for pyttsx3
python -c "import pyttsx3" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pyttsx3 missing
    echo 📦 Installing pyttsx3...
    pip install pyttsx3
    if %errorlevel% neq 0 (
        echo ❌ Failed to install pyttsx3
        pause
        exit /b 1
    )
) else (
    echo ✅ pyttsx3 available
)

REM Check for PyInstaller
python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PyInstaller missing
    echo 📦 Installing PyInstaller...
    pip install pyinstaller
    if %errorlevel% neq 0 (
        echo ❌ Failed to install PyInstaller
        pause
        exit /b 1
    )
) else (
    echo ✅ PyInstaller available
)

REM Check for Visual C++ Build Tools (informational)
echo 🔍 Checking build environment...
cl >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Visual C++ compiler not found in PATH
    echo 💡 If build fails, install "Microsoft C++ Build Tools"
    echo 💡 Or Visual Studio with C++ development tools
    echo 🤔 Continuing anyway...
) else (
    echo ✅ Visual C++ compiler available
)

REM Run the Windows-specific build
echo.
echo 🚀 Starting Windows build process...
echo =================================
python build_windows.py

REM Check if build was successful
if %errorlevel% equ 0 (
    echo.
    echo 🎉 Windows build completed successfully!
    echo ====================================
    echo.
    echo 📁 Build output in .\dist\:
    if exist "dist" (
        dir /b dist\
    )
    echo.
    echo 🚀 Next steps:
    echo    cd dist
    echo    install.bat                           # Install on this system (run as admin^)
    echo    cursor-chat-monitor.exe --help        # Test the executable
    echo.
    echo 📖 See dist\README.md for detailed installation and usage instructions
    echo.
    echo ⚠️  Remember: You may need to allow the executable through Windows Defender
) else (
    echo.
    echo ❌ Build failed!
    echo 💡 Check the error messages above for details
    pause
    exit /b 1
)

echo.
pause 