#!/usr/bin/env python3
"""
Windows-specific build script for cursor-chat-monitor

Creates a standalone Windows application with Windows Service integration
and proper Windows installer support.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_platform():
    """Ensure we're running on Windows"""
    if sys.platform != 'win32':
        print(f"❌ This script is for Windows only. Current platform: {sys.platform}")
        return False
    print(f"✅ Building on Windows: {os.name}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking Windows-specific dependencies...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("📦 PyInstaller not found, installing...")
        if not run_command("pip install pyinstaller", "Installing PyInstaller"):
            return False
    
    # Check Windows-specific dependencies
    try:
        import win32api
        print("✅ pywin32 found")
    except ImportError:
        print("❌ pywin32 not found. Install with: pip install pywin32")
        return False
    
    try:
        import pyttsx3
        print("✅ pyttsx3 found")
    except ImportError:
        print("❌ pyttsx3 not found. Install with: pip install pyttsx3")
        return False
    
    return True

def create_build_directory():
    """Create build directory structure"""
    os.makedirs('build/windows', exist_ok=True)
    os.makedirs('build/windows/templates', exist_ok=True)
    print("✅ Created build directory structure")

def create_spec_file():
    """Create Windows-specific PyInstaller spec file"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../cursor_chat_monitor.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../../core', 'core'),
        ('../../platforms', 'platforms'),
    ],
    hiddenimports=[
        'platforms.windows',
        'win32api',
        'win32gui',
        'win32process',
        'win32con',
        'pyttsx3',
        'pyttsx3.drivers',
        'pyttsx3.drivers.sapi5',
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'platforms.macos',
        'platforms.linux',
        'Cocoa',
        'ApplicationServices',
        'pyatspi',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='cursor-chat-monitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('build/windows/cursor_chat_monitor.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created Windows PyInstaller spec file")

def create_windows_service():
    """Create Windows service wrapper script"""
    service_content = '''import sys
import os
import win32serviceutil
import win32service
import win32event
import logging
from pathlib import Path

class CursorChatMonitorService(win32serviceutil.ServiceFramework):
    _svc_name_ = "CursorChatMonitor"
    _svc_display_name_ = "Cursor Chat Monitor Service"
    _svc_description_ = "Monitors Cursor chat conversations and logs them"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_alive = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_alive = False

    def SvcDoRun(self):
        import servicemanager
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        # Get the directory where the service executable is located
        service_dir = Path(sys.executable).parent
        monitor_exe = service_dir / "cursor-chat-monitor.exe"
        
        if not monitor_exe.exists():
            servicemanager.LogErrorMsg(f"Monitor executable not found: {monitor_exe}")
            return
        
        try:
            # Import and run the monitor
            sys.path.insert(0, str(service_dir))
            
            # Run the main monitor loop
            import subprocess
            process = subprocess.Popen([str(monitor_exe), "--daemon"])
            
            # Wait for stop signal
            win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)
            
            # Terminate the monitor process
            process.terminate()
            process.wait()
            
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {e}")

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(CursorChatMonitorService)
'''
    
    with open('build/windows/templates/windows_service.py', 'w') as f:
        f.write(service_content)
    print("✅ Created Windows service wrapper")

def create_service_wrapper():
    """Create Windows service management script"""
    wrapper_content = '''@echo off
REM Windows service wrapper for cursor-chat-monitor

set SERVICE_NAME=CursorChatMonitor
set BINARY=%~dp0cursor-chat-monitor.exe
set SERVICE_SCRIPT=%~dp0cursor-chat-monitor-service.exe

if "%1"=="install" goto install
if "%1"=="uninstall" goto uninstall
if "%1"=="start" goto start
if "%1"=="stop" goto stop
if "%1"=="restart" goto restart
if "%1"=="status" goto status
if "%1"=="console" goto console

:usage
echo Usage: %0 {install^|uninstall^|start^|stop^|restart^|status^|console}
echo.
echo Commands:
echo   install   - Install the Windows service
echo   uninstall - Remove the Windows service
echo   start     - Start the service
echo   stop      - Stop the service
echo   restart   - Restart the service
echo   status    - Show service status
echo   console   - Run in foreground with debug output
exit /b 1

:install
echo Installing cursor-chat-monitor Windows service...
if exist "%SERVICE_SCRIPT%" (
    "%SERVICE_SCRIPT%" install
    if %errorlevel% equ 0 (
        echo Service installed successfully
        echo You can now start it with: %0 start
    ) else (
        echo Failed to install service
    )
) else (
    echo Service script not found: %SERVICE_SCRIPT%
    exit /b 1
)
goto end

:uninstall
echo Uninstalling cursor-chat-monitor Windows service...
if exist "%SERVICE_SCRIPT%" (
    "%SERVICE_SCRIPT%" remove
    if %errorlevel% equ 0 (
        echo Service uninstalled successfully
    ) else (
        echo Failed to uninstall service
    )
) else (
    echo Service script not found: %SERVICE_SCRIPT%
    exit /b 1
)
goto end

:start
echo Starting cursor-chat-monitor service...
sc start "%SERVICE_NAME%"
if %errorlevel% equ 0 (
    echo Service started successfully
) else (
    echo Failed to start service
)
goto end

:stop
echo Stopping cursor-chat-monitor service...
sc stop "%SERVICE_NAME%"
if %errorlevel% equ 0 (
    echo Service stopped successfully
) else (
    echo Failed to stop service
)
goto end

:restart
echo Restarting cursor-chat-monitor service...
sc stop "%SERVICE_NAME%"
timeout /t 2 /nobreak >nul
sc start "%SERVICE_NAME%"
if %errorlevel% equ 0 (
    echo Service restarted successfully
) else (
    echo Failed to restart service
)
goto end

:status
echo Checking cursor-chat-monitor service status...
sc query "%SERVICE_NAME%"
goto end

:console
echo Running cursor-chat-monitor in console mode...
if exist "%BINARY%" (
    "%BINARY%" --debug
) else (
    echo Binary not found: %BINARY%
    exit /b 1
)
goto end

:end
'''
    
    with open('build/windows/templates/service-wrapper.bat', 'w') as f:
        f.write(wrapper_content)
    print("✅ Created Windows service wrapper")

def create_installer_script():
    """Create Windows installer script"""
    installer_content = '''@echo off
REM Windows installation script for cursor-chat-monitor

echo 🪟 Installing cursor-chat-monitor for Windows...
echo ===============================================

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ This installer requires administrator privileges
    echo Please run as administrator
    pause
    exit /b 1
)

REM Create program directory
set INSTALL_DIR=C:\\Program Files\\CursorChatMonitor
mkdir "%INSTALL_DIR%" 2>nul

REM Install binaries
echo 📦 Installing binaries...
copy cursor-chat-monitor.exe "%INSTALL_DIR%\\" >nul
copy cursor-chat-monitor-service.exe "%INSTALL_DIR%\\" >nul
copy cursor-chat-monitor-service.bat "%INSTALL_DIR%\\" >nul

REM Add to PATH
echo ⚙️  Adding to system PATH...
setx /M PATH "%PATH%;%INSTALL_DIR%"

REM Install config template
echo 📄 Installing configuration template...
set CONFIG_FILE=%USERPROFILE%\\.cursor_chat_monitor
if not exist "%CONFIG_FILE%" (
    copy .cursor_chat_monitor "%CONFIG_FILE%" >nul
    echo    Configuration template installed to %CONFIG_FILE%
) else (
    echo    Configuration file already exists, skipping
)

echo.
echo ✅ Installation completed!
echo.
echo 🚀 Quick start:
echo    cursor-chat-monitor --help                     # Show help
echo    cursor-chat-monitor --debug                    # Test run
echo    cursor-chat-monitor-service install            # Install Windows service
echo    cursor-chat-monitor-service start              # Start service
echo.
echo 📖 See README.md for detailed usage instructions
echo.
pause
'''
    
    with open('build/windows/templates/install.bat', 'w') as f:
        f.write(installer_content)
    print("✅ Created Windows installer script")

def create_readme():
    """Create Windows-specific README"""
    readme_content = '''# Cursor Chat Monitor - Windows Edition

A standalone Windows application for monitoring Cursor chat conversations.

## Quick Start

```cmd
# Test the application
cursor-chat-monitor.exe --help
cursor-chat-monitor.exe --debug

# Install and start Windows service
cursor-chat-monitor-service.bat install
cursor-chat-monitor-service.bat start
```

## Features

- **Native Windows Integration**: Uses Win32 API for window monitoring
- **Windows Service**: Integrates with Windows Service Manager
- **Text-to-Speech**: Optional audio notifications using Windows SAPI
- **Background Operation**: Runs silently in the background

## System Requirements

- Windows 10 or later (64-bit)
- No additional dependencies required

## Installation

### Automatic Installation

Right-click on `install.bat` and select "Run as administrator":

```cmd
install.bat
```

This will:
- Copy binaries to `C:\\Program Files\\CursorChatMonitor\\`
- Add directory to system PATH
- Set up default configuration file

### Manual Installation

1. Copy `cursor-chat-monitor.exe` and `cursor-chat-monitor-service.exe` to a directory
2. Add that directory to your system PATH
3. Copy `.cursor_chat_monitor` to your user home directory

## Usage

### Manual Run

```cmd
cursor-chat-monitor --help           # Show all options
cursor-chat-monitor --debug          # Run with debug output
cursor-chat-monitor --interval-ms=1000  # Custom scan interval
cursor-chat-monitor --daemon         # Run as background process
```

### Windows Service Management

```cmd
# Install the service
cursor-chat-monitor-service install

# Service control
cursor-chat-monitor-service start    # Start service
cursor-chat-monitor-service stop     # Stop service
cursor-chat-monitor-service restart  # Restart service
cursor-chat-monitor-service status   # Check service status

# Remove the service
cursor-chat-monitor-service uninstall

# Run in foreground
cursor-chat-monitor-service console
```

### Alternative Service Management

You can also use Windows Service Manager:

1. Open **Services** (`services.msc`)
2. Find "Cursor Chat Monitor Service"
3. Right-click for start/stop/restart options

## Configuration

Edit `%USERPROFILE%\\.cursor_chat_monitor` to customize:

```json
{
    "scan_interval_ms": 2000,
    "output_directory": "%USERPROFILE%\\cursor-chat-logs",
    "debug_mode": false,
    "app_names": ["Cursor"],
    "notification_enabled": true,
    "platform_specific": {
        "windows": {
            "use_win32_api": true,
            "enable_tts": false,
            "window_class_names": ["Chrome_WidgetWin_1"]
        }
    }
}
```

## Troubleshooting

### Installation Issues

**"Access denied" during installation:**
- Run `install.bat` as administrator
- Ensure Windows Defender isn't blocking the executable

**"Windows protected your PC" message:**
- Click "More info" then "Run anyway"
- The executable is not digitally signed

### Service Issues

**Service won't start:**
```cmd
# Check service status
cursor-chat-monitor-service status

# Check Windows Event Log
eventvwr.msc
# Navigate to Windows Logs > Application
# Look for CursorChatMonitor entries
```

**Service starts but doesn't work:**
```cmd
# Test in console mode first
cursor-chat-monitor-service console
```

### Performance Issues

**High CPU usage:**
- Increase `scan_interval_ms` in configuration
- Disable debug mode if enabled

## Uninstallation

### Service Removal

```cmd
cursor-chat-monitor-service stop
cursor-chat-monitor-service uninstall
```

### File Removal

1. Remove from Programs and Features, or
2. Manually delete:
   - `C:\\Program Files\\CursorChatMonitor\\` (requires admin)
   - `%USERPROFILE%\\.cursor_chat_monitor` (optional)

## Security Notes

- The application monitors window titles and UI elements
- No network connections are made (all data stays local)
- Service runs under Local System account
- Log files are stored in user's home directory

## Technical Details

- **Platform**: Windows-specific implementation using pywin32
- **Service Type**: Windows Service (can run without user login)
- **Architecture**: 64-bit Windows executable
- **Dependencies**: All bundled in standalone executable

For issues or questions, see the main project documentation.
'''
    
    with open('build/windows/templates/README.md', 'w') as f:
        f.write(readme_content)
    print("✅ Created Windows README")

def create_config_template():
    """Create default configuration template"""
    config_content = '''{
    "scan_interval_ms": 2000,
    "output_directory": "%USERPROFILE%\\\\cursor-chat-logs",
    "debug_mode": false,
    "app_names": ["Cursor"],
    "notification_enabled": true,
    "platform_specific": {
        "windows": {
            "use_win32_api": true,
            "enable_tts": false,
            "window_class_names": ["Chrome_WidgetWin_1"],
            "process_names": ["Cursor.exe"]
        }
    }
}'''
    
    with open('build/windows/templates/default_config.json', 'w') as f:
        f.write(config_content)
    print("✅ Created Windows config template")

def build_executable():
    """Build the Windows executable"""
    print("🚀 Building Windows executable...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("🧹 Cleaned previous dist directory")
    
    if os.path.exists('build/output'):
        shutil.rmtree('build/output')
        print("🧹 Cleaned previous build output")
    
    # Run PyInstaller
    cmd = "pyinstaller --clean build/windows/cursor_chat_monitor.spec"
    return run_command(cmd, "Building with PyInstaller")

def build_service_executable():
    """Build the Windows service executable"""
    print("🔧 Building Windows service executable...")
    
    # Create service spec
    service_spec = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['templates/windows_service.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'win32serviceutil',
        'win32service',
        'win32event',
        'servicemanager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='cursor-chat-monitor-service',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('build/windows/service.spec', 'w') as f:
        f.write(service_spec)
    
    cmd = "pyinstaller --clean build/windows/service.spec"
    return run_command(cmd, "Building Windows service executable")

def copy_distribution_files():
    """Copy all distribution files to dist directory"""
    print("📦 Copying distribution files...")
    
    # Copy service wrapper
    shutil.copy('build/windows/templates/service-wrapper.bat', 'dist/cursor-chat-monitor-service.bat')
    
    # Copy installer
    shutil.copy('build/windows/templates/install.bat', 'dist/install.bat')
    
    # Copy README
    shutil.copy('build/windows/templates/README.md', 'dist/README.md')
    
    # Copy config template
    shutil.copy('build/windows/templates/default_config.json', 'dist/.cursor_chat_monitor')
    
    print("✅ Distribution files copied")

def main():
    """Main build process for Windows"""
    print("🪟 Building cursor-chat-monitor for Windows")
    print("=" * 50)
    
    # Platform check
    if not check_platform():
        sys.exit(1)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    
    print(f"🐍 Python version: {sys.version}")
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Create build structure
    create_build_directory()
    
    # Create build files
    create_spec_file()
    create_windows_service()
    create_service_wrapper()
    create_installer_script()
    create_readme()
    create_config_template()
    
    # Build executables
    if not build_executable():
        sys.exit(1)
    
    if not build_service_executable():
        sys.exit(1)
    
    # Copy distribution files
    copy_distribution_files()
    
    print("=" * 50)
    print("🎉 Windows build completed successfully!")
    print("")
    print("📁 Distribution files in ./dist/:")
    print("   cursor-chat-monitor.exe          - Main executable")
    print("   cursor-chat-monitor-service.exe  - Windows service")
    print("   cursor-chat-monitor-service.bat  - Service wrapper")
    print("   install.bat                      - Installation script")
    print("   README.md                        - Windows-specific instructions")  
    print("   .cursor_chat_monitor             - Config template")
    print("")
    print("🚀 To install: Run install.bat as administrator")
    print("💡 To test: cursor-chat-monitor.exe --help")
    print("⚙️  Service: cursor-chat-monitor-service.bat install")

if __name__ == "__main__":
    main() 