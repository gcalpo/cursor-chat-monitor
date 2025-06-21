#!/usr/bin/env python3
"""
macOS-specific build script for cursor-chat-monitor

Creates a standalone macOS application with proper app bundle structure
and native macOS service integration.
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
    """Ensure we're running on macOS"""
    if sys.platform != 'darwin':
        print(f"❌ This script is for macOS only. Current platform: {sys.platform}")
        return False
    print(f"✅ Building on macOS: {os.uname().sysname} {os.uname().release}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking macOS-specific dependencies...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("📦 PyInstaller not found, installing...")
        if not run_command("pip3 install pyinstaller", "Installing PyInstaller"):
            return False
    
    # Check macOS-specific dependencies
    try:
        import Cocoa
        print("✅ PyObjC Cocoa framework found")
    except ImportError:
        print("❌ PyObjC Cocoa framework not found. Install with: pip3 install pyobjc-framework-Cocoa")
        return False
    
    try:
        import ApplicationServices
        print("✅ PyObjC ApplicationServices framework found")
    except ImportError:
        print("❌ PyObjC ApplicationServices framework not found. Install with: pip3 install pyobjc-framework-ApplicationServices")
        return False
    
    return True

def create_build_directory():
    """Create build directory structure"""
    os.makedirs('build/macos', exist_ok=True)
    os.makedirs('build/macos/templates', exist_ok=True)
    print("✅ Created build directory structure")

def create_spec_file():
    """Create macOS-specific PyInstaller spec file"""
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
        'platforms.macos',
        'Cocoa',
        'ApplicationServices',
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
        'platforms.windows',
        'platforms.linux',
        'pywin32',
        'pyttsx3',
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
)

# Create app bundle for macOS
app = BUNDLE(
    exe,
    name='cursor-chat-monitor.app',
    icon=None,
    bundle_identifier='com.cursor.chat.monitor',
)
'''
    
    with open('build/macos/cursor_chat_monitor.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created macOS PyInstaller spec file")

def create_launchd_plist():
    """Create macOS LaunchAgent plist for system service"""
    plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cursor.chat.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cursor-chat-monitor</string>
        <string>--daemon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/cursor-chat-monitor.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cursor-chat-monitor-error.log</string>
    <key>WorkingDirectory</key>
    <string>/usr/local/bin</string>
</dict>
</plist>
'''
    
    with open('build/macos/templates/com.cursor.chat.monitor.plist', 'w') as f:
        f.write(plist_content)
    print("✅ Created LaunchAgent plist")

def create_service_wrapper():
    """Create macOS service wrapper script"""
    wrapper_content = '''#!/bin/bash
# macOS service wrapper for cursor-chat-monitor

BINARY="/usr/local/bin/cursor-chat-monitor"
PLIST_FILE="$HOME/Library/LaunchAgents/com.cursor.chat.monitor.plist"
SERVICE_NAME="com.cursor.chat.monitor"

case "$1" in
    start)
        echo "Starting cursor-chat-monitor service..."
        if [ -f "$PLIST_FILE" ]; then
            launchctl load "$PLIST_FILE"
            echo "Service started"
        else
            echo "Service plist not found at $PLIST_FILE"
            echo "Run install.sh first"
            exit 1
        fi
        ;;
    stop)
        echo "Stopping cursor-chat-monitor service..."
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        echo "Service stopped"
        ;;
    restart)
        echo "Restarting cursor-chat-monitor service..."
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        sleep 1
        launchctl load "$PLIST_FILE"
        echo "Service restarted"
        ;;
    status)
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "Service is running"
            launchctl list | grep "$SERVICE_NAME"
        else
            echo "Service is not running"
        fi
        ;;
    console)
        echo "Running cursor-chat-monitor in console mode..."
        exec "$BINARY" --debug
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|console}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the background service"
        echo "  stop    - Stop the background service"
        echo "  restart - Restart the background service"
        echo "  status  - Show service status"
        echo "  console - Run in foreground with debug output"
        exit 1
        ;;
esac
'''
    
    with open('build/macos/templates/service-wrapper.sh', 'w') as f:
        f.write(wrapper_content)
    print("✅ Created macOS service wrapper")

def create_installer_script():
    """Create macOS installer script"""
    installer_content = '''#!/bin/bash
# macOS installation script for cursor-chat-monitor

set -e

echo "🍎 Installing cursor-chat-monitor for macOS..."
echo "==============================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is for macOS only"
    exit 1
fi

# Create directories
sudo mkdir -p /usr/local/bin
mkdir -p "$HOME/Library/LaunchAgents"

# Install binaries
echo "📦 Installing binaries..."
sudo cp cursor-chat-monitor /usr/local/bin/
sudo cp cursor-chat-monitor-service /usr/local/bin/
sudo chmod +x /usr/local/bin/cursor-chat-monitor*

# Install service plist
echo "⚙️  Installing LaunchAgent..."
cp com.cursor.chat.monitor.plist "$HOME/Library/LaunchAgents/"

# Install config template
echo "📄 Installing configuration template..."
if [ ! -f "$HOME/.cursor_chat_monitor" ]; then
    cp .cursor_chat_monitor "$HOME/.cursor_chat_monitor"
    echo "   Configuration template installed to ~/.cursor_chat_monitor"
else
    echo "   Configuration file already exists, skipping"
fi

echo ""
echo "✅ Installation completed!"
echo ""
echo "🚀 Quick start:"
echo "   cursor-chat-monitor --help                    # Show help"
echo "   cursor-chat-monitor --debug                   # Test run"
echo "   cursor-chat-monitor-service start             # Start service"
echo ""
echo "⚠️  IMPORTANT: Grant accessibility permissions:"
echo "   1. Open System Preferences > Security & Privacy > Privacy"
echo "   2. Select 'Accessibility' from the left sidebar"
echo "   3. Add and enable Terminal (or your terminal app)"
echo ""
echo "📖 See README.md for detailed usage instructions"
'''
    
    with open('build/macos/templates/install.sh', 'w') as f:
        f.write(installer_content)
    print("✅ Created macOS installer script")

def create_readme():
    """Create macOS-specific README"""
    readme_content = '''# Cursor Chat Monitor - macOS Edition

A standalone macOS application for monitoring Cursor chat conversations.

## Quick Start

```bash
# Test the application
./cursor-chat-monitor --help
./cursor-chat-monitor --debug

# Install as system service
./cursor-chat-monitor-service start
```

## Features

- **Native macOS Integration**: Uses Cocoa and ApplicationServices frameworks
- **LaunchAgent Service**: Integrates with macOS service management
- **Accessibility API**: Monitors application windows and UI changes
- **Background Operation**: Runs silently in the background

## System Requirements

- macOS 10.14 (Mojave) or later
- Accessibility permissions for monitoring applications

## Installation

Run the installer script:

```bash
./install.sh
```

This will:
- Copy binaries to `/usr/local/bin/`
- Install LaunchAgent plist for service management
- Set up default configuration file

## Permissions Setup

⚠️ **Critical**: Grant accessibility permissions:

1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Select **Accessibility** from the left sidebar
3. Click the lock icon and enter your password
4. Add **Terminal** (or your terminal application) to the list
5. Ensure it's checked/enabled

## Usage

### Manual Run

```bash
cursor-chat-monitor --help           # Show all options
cursor-chat-monitor --debug          # Run with debug output
cursor-chat-monitor --interval-ms=1000  # Custom scan interval
cursor-chat-monitor --daemon         # Run as background daemon
```

### Service Management

```bash
cursor-chat-monitor-service start    # Start background service
cursor-chat-monitor-service stop     # Stop service
cursor-chat-monitor-service restart  # Restart service
cursor-chat-monitor-service status   # Check service status
cursor-chat-monitor-service console  # Run in foreground
```

### Configuration

Edit `~/.cursor_chat_monitor` to customize:

```json
{
    "scan_interval_ms": 2000,
    "output_directory": "~/cursor-chat-logs",
    "debug_mode": false,
    "app_names": ["Cursor"],
    "notification_enabled": true
}
```

## Troubleshooting

### Permission Issues

**"cursor-chat-monitor" cannot be opened because the developer cannot be verified**

Right-click the executable and select "Open", then confirm.

Or remove the quarantine attribute:
```bash
xattr -d com.apple.quarantine cursor-chat-monitor cursor-chat-monitor-service
```

### Service Issues

Check service logs:
```bash
tail -f /tmp/cursor-chat-monitor.log
tail -f /tmp/cursor-chat-monitor-error.log
```

### Accessibility Permissions

Verify permissions are granted:
```bash
cursor-chat-monitor --debug
```

If you see permission errors, revisit the Permissions Setup section above.

## Uninstallation

```bash
# Stop and remove service
cursor-chat-monitor-service stop
rm ~/Library/LaunchAgents/com.cursor.chat.monitor.plist

# Remove binaries
sudo rm /usr/local/bin/cursor-chat-monitor*

# Remove config (optional)
rm ~/.cursor_chat_monitor
```

## Technical Details

- **Platform**: macOS-specific implementation using PyObjC
- **Service Type**: LaunchAgent (user-level service)
- **Permissions**: Requires Accessibility API access
- **Architecture**: Universal binary (Intel + Apple Silicon)

For issues or questions, see the main project documentation.
'''
    
    with open('build/macos/templates/README.md', 'w') as f:
        f.write(readme_content)
    print("✅ Created macOS README")

def create_config_template():
    """Create default configuration template"""
    config_content = '''{
    "scan_interval_ms": 2000,
    "output_directory": "~/cursor-chat-logs",
    "debug_mode": false,
    "app_names": ["Cursor"],
    "notification_enabled": true,
    "platform_specific": {
        "macos": {
            "use_accessibility_api": true,
            "monitor_window_focus": true,
            "bundle_identifiers": ["com.todesktop.230313mzl4w4u92"]
        }
    }
}'''
    
    with open('build/macos/templates/default_config.json', 'w') as f:
        f.write(config_content)
    print("✅ Created macOS config template")

def build_executable():
    """Build the macOS executable"""
    print("🚀 Building macOS executable...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("🧹 Cleaned previous dist directory")
    
    if os.path.exists('build/output'):
        shutil.rmtree('build/output')
        print("🧹 Cleaned previous build output")
    
    # Run PyInstaller
    cmd = "pyinstaller --clean build/macos/cursor_chat_monitor.spec"
    return run_command(cmd, "Building with PyInstaller")

def copy_distribution_files():
    """Copy all distribution files to dist directory"""
    print("📦 Copying distribution files...")
    
    # Copy service wrapper
    shutil.copy('build/macos/templates/service-wrapper.sh', 'dist/cursor-chat-monitor-service')
    os.chmod('dist/cursor-chat-monitor-service', 0o755)
    
    # Copy installer
    shutil.copy('build/macos/templates/install.sh', 'dist/install.sh')
    os.chmod('dist/install.sh', 0o755)
    
    # Copy README
    shutil.copy('build/macos/templates/README.md', 'dist/README.md')
    
    # Copy config template
    shutil.copy('build/macos/templates/default_config.json', 'dist/.cursor_chat_monitor')
    
    # Copy LaunchAgent plist
    shutil.copy('build/macos/templates/com.cursor.chat.monitor.plist', 'dist/com.cursor.chat.monitor.plist')
    
    print("✅ Distribution files copied")

def main():
    """Main build process for macOS"""
    print("🍎 Building cursor-chat-monitor for macOS")
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
    create_launchd_plist()
    create_service_wrapper()
    create_installer_script()
    create_readme()
    create_config_template()
    
    # Build executable
    if not build_executable():
        sys.exit(1)
    
    # Copy distribution files
    copy_distribution_files()
    
    print("=" * 50)
    print("🎉 macOS build completed successfully!")
    print("")
    print("📁 Distribution files in ./dist/:")
    print("   cursor-chat-monitor.app/         - macOS app bundle")
    print("   cursor-chat-monitor              - Command-line executable")
    print("   cursor-chat-monitor-service      - Service wrapper")
    print("   install.sh                       - Installation script")
    print("   README.md                        - macOS-specific instructions")  
    print("   .cursor_chat_monitor             - Config template")
    print("   com.cursor.chat.monitor.plist    - LaunchAgent plist")
    print("")
    print("🚀 To install: cd dist && ./install.sh")
    print("💡 To test: cd dist && ./cursor-chat-monitor --help")
    print("⚠️  Remember to grant accessibility permissions!")

if __name__ == "__main__":
    main() 