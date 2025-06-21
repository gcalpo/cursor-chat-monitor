#!/usr/bin/env python3
"""
Linux-specific build script for cursor-chat-monitor

Creates a standalone Linux application with systemd service integration
and proper package manager support.
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
    """Ensure we're running on Linux"""
    if not sys.platform.startswith('linux'):
        print(f"❌ This script is for Linux only. Current platform: {sys.platform}")
        return False
    
    # Get Linux distribution info
    try:
        with open('/etc/os-release', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith('PRETTY_NAME='):
                    distro = line.split('=')[1].strip().strip('"')
                    print(f"✅ Building on Linux: {distro}")
                    break
    except FileNotFoundError:
        print(f"✅ Building on Linux: {os.uname().sysname} {os.uname().release}")
    
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking Linux-specific dependencies...")
    
    try:
        import PyInstaller
        print(f"✅ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("📦 PyInstaller not found, installing...")
        if not run_command("pip3 install pyinstaller", "Installing PyInstaller"):
            return False
    
    # Check Linux-specific dependencies (optional)
    try:
        import pyatspi
        print("✅ pyatspi found (AT-SPI accessibility)")
    except ImportError:
        print("⚠️  pyatspi not found - some accessibility features may be limited")
        print("   Install with: pip3 install pyatspi")
    
    return True

def create_build_directory():
    """Create build directory structure"""
    os.makedirs('build/linux', exist_ok=True)
    os.makedirs('build/linux/templates', exist_ok=True)
    print("✅ Created build directory structure")

def create_spec_file():
    """Create Linux-specific PyInstaller spec file"""
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
        'platforms.linux',
        'psutil',
        'subprocess',
        'threading',
        'json',
        'pathlib',
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
        'platforms.windows',
        'Cocoa',
        'ApplicationServices',
        'pywin32',
        'pyttsx3',
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
'''
    
    with open('build/linux/cursor_chat_monitor.spec', 'w') as f:
        f.write(spec_content)
    print("✅ Created Linux PyInstaller spec file")

def create_systemd_service():
    """Create systemd service unit file"""
    service_content = '''[Unit]
Description=Cursor Chat Monitor Service
Documentation=https://github.com/cursor-chat-monitor
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cursor-chat-monitor --daemon
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
User=cursor-monitor
Group=cursor-monitor
WorkingDirectory=/var/lib/cursor-monitor
StandardOutput=journal
StandardError=journal
SyslogIdentifier=cursor-chat-monitor

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/var/lib/cursor-monitor /var/log/cursor-monitor
PrivateDevices=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

[Install]
WantedBy=multi-user.target
'''
    
    with open('build/linux/templates/cursor-chat-monitor.service', 'w') as f:
        f.write(service_content)
    print("✅ Created systemd service unit")

def create_user_service():
    """Create user-level systemd service"""
    user_service_content = '''[Unit]
Description=Cursor Chat Monitor (User Service)
Documentation=https://github.com/cursor-chat-monitor
After=graphical-session.target
Wants=graphical-session.target

[Service]
Type=simple
ExecStart=%h/.local/bin/cursor-chat-monitor --daemon
Restart=always
RestartSec=5
Environment=DISPLAY=:0
Environment=HOME=%h

[Install]
WantedBy=default.target
'''
    
    with open('build/linux/templates/cursor-chat-monitor-user.service', 'w') as f:
        f.write(user_service_content)
    print("✅ Created user systemd service unit")

def create_service_wrapper():
    """Create Linux service wrapper script"""
    wrapper_content = '''#!/bin/bash
# Linux service wrapper for cursor-chat-monitor

BINARY="/usr/local/bin/cursor-chat-monitor"
USER_BINARY="$HOME/.local/bin/cursor-chat-monitor"
SERVICE_NAME="cursor-chat-monitor"
USER_SERVICE_NAME="cursor-chat-monitor-user"

# Check if we have system service or user service
if systemctl --quiet is-enabled "$SERVICE_NAME" 2>/dev/null; then
    SERVICE_TYPE="system"
    SERVICE="$SERVICE_NAME"
elif systemctl --user --quiet is-enabled "$USER_SERVICE_NAME" 2>/dev/null; then
    SERVICE_TYPE="user"
    SERVICE="$USER_SERVICE_NAME"
else
    SERVICE_TYPE="user"
    SERVICE="$USER_SERVICE_NAME"
fi

case "$1" in
    start)
        echo "Starting cursor-chat-monitor service ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            sudo systemctl start "$SERVICE"
        else
            systemctl --user start "$SERVICE"
        fi
        echo "Service started"
        ;;
    stop)
        echo "Stopping cursor-chat-monitor service ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            sudo systemctl stop "$SERVICE"
        else
            systemctl --user stop "$SERVICE"
        fi
        echo "Service stopped"
        ;;
    restart)
        echo "Restarting cursor-chat-monitor service ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            sudo systemctl restart "$SERVICE"
        else
            systemctl --user restart "$SERVICE"
        fi
        echo "Service restarted"
        ;;
    status)
        echo "Checking cursor-chat-monitor service status ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            systemctl status "$SERVICE"
        else
            systemctl --user status "$SERVICE"
        fi
        ;;
    enable)
        echo "Enabling cursor-chat-monitor service ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            sudo systemctl enable "$SERVICE"
        else
            systemctl --user enable "$SERVICE"
        fi
        echo "Service enabled (will start on boot)"
        ;;
    disable)
        echo "Disabling cursor-chat-monitor service ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            sudo systemctl disable "$SERVICE"
        else
            systemctl --user disable "$SERVICE"
        fi
        echo "Service disabled"
        ;;
    console)
        echo "Running cursor-chat-monitor in console mode..."
        if [ -x "$USER_BINARY" ]; then
            exec "$USER_BINARY" --debug
        elif [ -x "$BINARY" ]; then
            exec "$BINARY" --debug
        else
            echo "Binary not found"
            exit 1
        fi
        ;;
    logs)
        echo "Showing cursor-chat-monitor service logs ($SERVICE_TYPE)..."
        if [ "$SERVICE_TYPE" = "system" ]; then
            journalctl -u "$SERVICE" -f
        else
            journalctl --user -u "$SERVICE" -f
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|enable|disable|console|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the service"
        echo "  stop    - Stop the service"
        echo "  restart - Restart the service"
        echo "  status  - Show service status"
        echo "  enable  - Enable service (start on boot)"
        echo "  disable - Disable service"
        echo "  console - Run in foreground with debug output"
        echo "  logs    - Show service logs (follow mode)"
        exit 1
        ;;
esac
'''
    
    with open('build/linux/templates/service-wrapper.sh', 'w') as f:
        f.write(wrapper_content)
    print("✅ Created Linux service wrapper")

def create_installer_script():
    """Create Linux installer script"""
    installer_content = '''#!/bin/bash
# Linux installation script for cursor-chat-monitor

set -e

echo "🐧 Installing cursor-chat-monitor for Linux..."
echo "=============================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This installer is for Linux only"
    exit 1
fi

# Detect if we should install system-wide or user-local
INSTALL_SYSTEM=false
if [ "$EUID" -eq 0 ]; then
    echo "📋 Running as root - will install system-wide"
    INSTALL_SYSTEM=true
elif command -v sudo >/dev/null 2>&1; then
    echo "📋 Sudo available - can install system-wide"
    read -p "Install system-wide? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        INSTALL_SYSTEM=true
    fi
fi

if [ "$INSTALL_SYSTEM" = true ]; then
    echo "📦 Installing system-wide..."
    
    # Create system directories
    sudo mkdir -p /usr/local/bin
    sudo mkdir -p /etc/systemd/system
    sudo mkdir -p /var/lib/cursor-monitor
    sudo mkdir -p /var/log/cursor-monitor
    
    # Create service user
    if ! id "cursor-monitor" &>/dev/null; then
        sudo useradd -r -s /bin/false -d /var/lib/cursor-monitor cursor-monitor
        echo "   Created service user: cursor-monitor"
    fi
    
    # Install binaries
    sudo cp cursor-chat-monitor /usr/local/bin/
    sudo cp cursor-chat-monitor-service /usr/local/bin/
    sudo chmod +x /usr/local/bin/cursor-chat-monitor*
    sudo chown root:root /usr/local/bin/cursor-chat-monitor*
    
    # Install systemd service
    sudo cp cursor-chat-monitor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    # Set permissions
    sudo chown cursor-monitor:cursor-monitor /var/lib/cursor-monitor
    sudo chown cursor-monitor:cursor-monitor /var/log/cursor-monitor
    
    echo "   Installed to /usr/local/bin/"
    echo "   Service unit: /etc/systemd/system/cursor-chat-monitor.service"
    
else
    echo "📦 Installing for current user..."
    
    # Create user directories
    mkdir -p "$HOME/.local/bin"
    mkdir -p "$HOME/.config/systemd/user"
    mkdir -p "$HOME/.local/share/cursor-monitor"
    
    # Install binaries
    cp cursor-chat-monitor "$HOME/.local/bin/"
    cp cursor-chat-monitor-service "$HOME/.local/bin/"
    chmod +x "$HOME/.local/bin/cursor-chat-monitor"*
    
    # Install user service
    cp cursor-chat-monitor-user.service "$HOME/.config/systemd/user/"
    systemctl --user daemon-reload
    
    echo "   Installed to ~/.local/bin/"
    echo "   Service unit: ~/.config/systemd/user/cursor-chat-monitor-user.service"
    
    # Add to PATH if needed
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "⚠️  Note: ~/.local/bin is not in your PATH"
        echo "   Add this to your ~/.bashrc or ~/.profile:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
    fi
fi

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
echo "   cursor-chat-monitor-service enable            # Enable on boot"
echo ""
echo "📖 See README.md for detailed usage instructions"
'''
    
    with open('build/linux/templates/install.sh', 'w') as f:
        f.write(installer_content)
    print("✅ Created Linux installer script")

def create_readme():
    """Create Linux-specific README"""
    readme_content = '''# Cursor Chat Monitor - Linux Edition

A standalone Linux application for monitoring Cursor chat conversations.

## Quick Start

```bash
# Test the application
./cursor-chat-monitor --help
./cursor-chat-monitor --debug

# Install and start service
./install.sh
cursor-chat-monitor-service start
cursor-chat-monitor-service enable  # Start on boot
```

## Features

- **Cross-Desktop Support**: Works with GNOME, KDE, XFCE, and other desktop environments
- **systemd Integration**: Full systemd service support (system and user services)
- **X11 and Wayland**: Compatible with both display servers
- **Background Operation**: Runs silently as a daemon

## System Requirements

- Linux distribution with systemd
- X11 or Wayland display server
- Python 3.8+ (for building only - not required for the standalone executable)

## Installation

### Automatic Installation

Run the installer script:

```bash
./install.sh
```

The installer will:
- Detect if you want system-wide or user installation
- Install binaries and service files
- Set up proper permissions
- Create configuration template

### Manual Installation

#### System-wide (requires root/sudo):

```bash
sudo cp cursor-chat-monitor cursor-chat-monitor-service /usr/local/bin/
sudo chmod +x /usr/local/bin/cursor-chat-monitor*
sudo cp cursor-chat-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
```

#### User installation:

```bash
mkdir -p ~/.local/bin ~/.config/systemd/user
cp cursor-chat-monitor cursor-chat-monitor-service ~/.local/bin/
chmod +x ~/.local/bin/cursor-chat-monitor*
cp cursor-chat-monitor-user.service ~/.config/systemd/user/
systemctl --user daemon-reload
```

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
cursor-chat-monitor-service start    # Start service
cursor-chat-monitor-service stop     # Stop service
cursor-chat-monitor-service restart  # Restart service
cursor-chat-monitor-service status   # Check service status
cursor-chat-monitor-service enable   # Enable on boot
cursor-chat-monitor-service disable  # Disable from boot
cursor-chat-monitor-service console  # Run in foreground
cursor-chat-monitor-service logs     # Show service logs
```

### Direct systemd Commands

#### System service:
```bash
sudo systemctl start cursor-chat-monitor
sudo systemctl enable cursor-chat-monitor
sudo systemctl status cursor-chat-monitor
journalctl -u cursor-chat-monitor -f
```

#### User service:
```bash
systemctl --user start cursor-chat-monitor-user
systemctl --user enable cursor-chat-monitor-user
systemctl --user status cursor-chat-monitor-user
journalctl --user -u cursor-chat-monitor-user -f
```

## Configuration

Edit `~/.cursor_chat_monitor` to customize:

```json
{
    "scan_interval_ms": 2000,
    "output_directory": "~/cursor-chat-logs",
    "debug_mode": false,
    "app_names": ["Cursor"],
    "notification_enabled": true,
    "platform_specific": {
        "linux": {
            "use_x11": true,
            "monitor_wayland": true,
            "window_managers": ["gnome", "kde", "xfce"]
        }
    }
}
```

## Desktop Environment Notes

### GNOME
- May require additional extensions for window monitoring
- Works best with X11 session

### KDE Plasma
- Full support for window monitoring
- Works with both X11 and Wayland

### XFCE
- Excellent compatibility
- All features supported

### Other DEs
- Most window managers supported
- Some features may be limited on minimal setups

## Troubleshooting

### Permission Issues

**Service fails to start:**
```bash
# Check service status
cursor-chat-monitor-service status

# Check logs
cursor-chat-monitor-service logs

# Test manually
cursor-chat-monitor --debug
```

### Display Server Issues

**Wayland limitations:**
- Some window monitoring features may be limited
- Try running in X11 session if available

**X11 permissions:**
```bash
# Ensure X11 access (usually automatic)
xhost +local:
```

### Performance Issues

**High CPU usage:**
- Increase `scan_interval_ms` in configuration
- Disable debug mode if enabled

## Uninstallation

### Service Removal

```bash
cursor-chat-monitor-service stop
cursor-chat-monitor-service disable

# System service
sudo systemctl disable cursor-chat-monitor
sudo rm /etc/systemd/system/cursor-chat-monitor.service
sudo systemctl daemon-reload

# User service  
systemctl --user disable cursor-chat-monitor-user
rm ~/.config/systemd/user/cursor-chat-monitor-user.service
systemctl --user daemon-reload
```

### File Removal

```bash
# System files
sudo rm /usr/local/bin/cursor-chat-monitor*

# User files
rm ~/.local/bin/cursor-chat-monitor*
rm ~/.cursor_chat_monitor  # optional
```

## Building from Source

If you need to build for a different architecture:

```bash
# Install dependencies
pip3 install -r requirements.txt

# Build
python3 build_linux.py
```

## Technical Details

- **Platform**: Linux-specific implementation
- **Service Type**: systemd (system or user service)
- **Display Servers**: X11 and Wayland support
- **Architecture**: Built for x86_64 (can be rebuilt for other architectures)

For issues or questions, see the main project documentation.
'''
    
    with open('build/linux/templates/README.md', 'w') as f:
        f.write(readme_content)
    print("✅ Created Linux README")

def create_config_template():
    """Create default configuration template"""
    config_content = '''{
    "scan_interval_ms": 2000,
    "output_directory": "~/cursor-chat-logs",
    "debug_mode": false,
    "app_names": ["Cursor"],
    "notification_enabled": true,
    "platform_specific": {
        "linux": {
            "use_x11": true,
            "monitor_wayland": true,
            "window_managers": ["gnome", "kde", "xfce"],
            "process_names": ["cursor", "Cursor"]
        }
    }
}'''
    
    with open('build/linux/templates/default_config.json', 'w') as f:
        f.write(config_content)
    print("✅ Created Linux config template")

def build_executable():
    """Build the Linux executable"""
    print("🚀 Building Linux executable...")
    
    # Clean previous builds
    if os.path.exists('dist'):
        shutil.rmtree('dist')
        print("🧹 Cleaned previous dist directory")
    
    if os.path.exists('build/output'):
        shutil.rmtree('build/output')
        print("🧹 Cleaned previous build output")
    
    # Run PyInstaller
    cmd = "pyinstaller --clean build/linux/cursor_chat_monitor.spec"
    return run_command(cmd, "Building with PyInstaller")

def copy_distribution_files():
    """Copy all distribution files to dist directory"""
    print("📦 Copying distribution files...")
    
    # Copy service wrapper
    shutil.copy('build/linux/templates/service-wrapper.sh', 'dist/cursor-chat-monitor-service')
    os.chmod('dist/cursor-chat-monitor-service', 0o755)
    
    # Copy installer
    shutil.copy('build/linux/templates/install.sh', 'dist/install.sh')
    os.chmod('dist/install.sh', 0o755)
    
    # Copy README
    shutil.copy('build/linux/templates/README.md', 'dist/README.md')
    
    # Copy config template
    shutil.copy('build/linux/templates/default_config.json', 'dist/.cursor_chat_monitor')
    
    # Copy systemd service files
    shutil.copy('build/linux/templates/cursor-chat-monitor.service', 'dist/cursor-chat-monitor.service')
    shutil.copy('build/linux/templates/cursor-chat-monitor-user.service', 'dist/cursor-chat-monitor-user.service')
    
    print("✅ Distribution files copied")

def main():
    """Main build process for Linux"""
    print("🐧 Building cursor-chat-monitor for Linux")
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
    create_systemd_service()
    create_user_service()
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
    print("🎉 Linux build completed successfully!")
    print("")
    print("📁 Distribution files in ./dist/:")
    print("   cursor-chat-monitor                    - Main executable")
    print("   cursor-chat-monitor-service            - Service wrapper")
    print("   install.sh                             - Installation script")
    print("   README.md                              - Linux-specific instructions")  
    print("   .cursor_chat_monitor                   - Config template")
    print("   cursor-chat-monitor.service            - System service unit")
    print("   cursor-chat-monitor-user.service       - User service unit")
    print("")
    print("🚀 To install: ./install.sh")
    print("💡 To test: ./cursor-chat-monitor --help")
    print("⚙️  Service: cursor-chat-monitor-service start")

if __name__ == "__main__":
    main() 