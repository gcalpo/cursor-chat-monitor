# Building Platform-Specific Cursor Chat Monitor

This guide explains how to build platform-specific standalone executables of the cursor-chat-monitor that don't require Python to be installed on the target system.

## Supported Platforms

- **macOS** (10.14 Mojave or later)
- **Windows** (Windows 10 or later)
- **Linux** (Most distributions with systemd)

## Prerequisites

1. **Python 3.8+** installed on your build machine
2. **Virtual environment** set up with dependencies
3. **Platform-specific dependencies** (automatically checked)

## Universal Build (Recommended)

The universal build script automatically detects your platform and runs the appropriate build:

```bash
# 1. Set up virtual environment (if not already done)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Run the universal build script
python3 build.py
```

## Platform-Specific Builds

You can also run platform-specific builds directly:

### macOS Build

```bash
python3 build_macos.py
```

Creates a macOS app bundle with LaunchAgent service integration.

### Windows Build

```bash
python build_windows.py
```

Creates Windows executables with Windows Service integration.

### Linux Build

```bash
python3 build_linux.py
```

Creates Linux binaries with systemd service integration.

## Manual PyInstaller Build

If you prefer to run PyInstaller manually:

```bash
# Install PyInstaller
pip3 install pyinstaller

# Create the spec file
python3 -c "
import build_standalone
build_standalone.create_spec_file()
"

# Build the executable
pyinstaller --clean cursor_chat_monitor.spec

# Create service wrapper and other files
python3 -c "
import build_standalone
import os
os.makedirs('dist', exist_ok=True)
build_standalone.create_service_wrapper()
build_standalone.create_installer_script()
build_standalone.create_readme()
build_standalone.copy_config_template()
"
```

## Installation on Target System

### macOS Installation

```bash
# Quick install
cd dist/
./install.sh

# Manual install
sudo cp cursor-chat-monitor cursor-chat-monitor-service /usr/local/bin/
chmod +x /usr/local/bin/cursor-chat-monitor*
cp com.cursor.chat.monitor.plist ~/Library/LaunchAgents/
cp .cursor_chat_monitor ~/.cursor_chat_monitor
```

### Windows Installation

```cmd
REM Run as administrator
cd dist
install.bat

REM Manual install
copy cursor-chat-monitor.exe "C:\Program Files\CursorChatMonitor\"
copy cursor-chat-monitor-service.exe "C:\Program Files\CursorChatMonitor\"
copy cursor-chat-monitor-service.bat "C:\Program Files\CursorChatMonitor\"
copy .cursor_chat_monitor "%USERPROFILE%\.cursor_chat_monitor"
```

### Linux Installation

```bash
# Quick install
cd dist/
./install.sh

# Manual install (system-wide)
sudo cp cursor-chat-monitor cursor-chat-monitor-service /usr/local/bin/
sudo cp cursor-chat-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload

# Manual install (user)
mkdir -p ~/.local/bin ~/.config/systemd/user
cp cursor-chat-monitor cursor-chat-monitor-service ~/.local/bin/
cp cursor-chat-monitor-user.service ~/.config/systemd/user/
systemctl --user daemon-reload
```

## Usage Modes

### Console Mode (All Platforms)

```bash
# macOS/Linux
cursor-chat-monitor --help           # Show help
cursor-chat-monitor --debug          # Run with debug output
cursor-chat-monitor --interval-ms=2000  # Custom scan interval

# Windows
cursor-chat-monitor.exe --help       # Show help
cursor-chat-monitor.exe --debug      # Run with debug output
cursor-chat-monitor.exe --interval-ms=2000  # Custom scan interval
```

### Service Mode

#### macOS (LaunchAgent)

```bash
cursor-chat-monitor-service start    # Start background service
cursor-chat-monitor-service stop     # Stop service
cursor-chat-monitor-service restart  # Restart service
cursor-chat-monitor-service status   # Check status
cursor-chat-monitor-service console  # Run in foreground
```

#### Windows (Windows Service)

```cmd
cursor-chat-monitor-service.bat install    # Install Windows service
cursor-chat-monitor-service.bat start      # Start service
cursor-chat-monitor-service.bat stop       # Stop service
cursor-chat-monitor-service.bat restart    # Restart service
cursor-chat-monitor-service.bat status     # Check status
cursor-chat-monitor-service.bat console    # Run in foreground
cursor-chat-monitor-service.bat uninstall  # Remove service
```

#### Linux (systemd)

```bash
cursor-chat-monitor-service start    # Start service
cursor-chat-monitor-service stop     # Stop service
cursor-chat-monitor-service restart  # Restart service
cursor-chat-monitor-service status   # Check status
cursor-chat-monitor-service enable   # Enable on boot
cursor-chat-monitor-service disable  # Disable from boot
cursor-chat-monitor-service console  # Run in foreground
cursor-chat-monitor-service logs     # Show logs
```

### Direct Daemon Mode

```bash
# macOS/Linux
cursor-chat-monitor --daemon         # Run as daemon
cursor-chat-monitor --daemon --pid-file=/tmp/monitor.pid  # Custom PID file

# Windows
cursor-chat-monitor.exe --daemon     # Run as daemon
```

## Configuration

The standalone application uses the same configuration system:

1. `~/.cursor_chat_monitor` - User configuration file
2. Command-line arguments override config values
3. Built-in defaults as fallback

## Permissions

⚠️ **Important**: The standalone executable still requires accessibility permissions:

1. Open **System Preferences** > **Security & Privacy** > **Privacy**
2. Select **Accessibility** from the left sidebar
3. Click the lock icon and enter your password
4. Add **Terminal** (or your terminal application) to the list
5. Ensure it's checked/enabled

## Troubleshooting

### Build Issues

**PyInstaller not found:**

```bash
pip3 install pyinstaller
```

**Missing dependencies:**

```bash
pip3 install -r requirements.txt
```

**macOS notarization warnings:**
The executable is not signed/notarized. You may see security warnings. To run:

- Right-click the executable → "Open"
- Or: `xattr -d com.apple.quarantine cursor-chat-monitor`

### Runtime Issues

**Permission denied:**

```bash
chmod +x cursor-chat-monitor cursor-chat-monitor-service
```

**Accessibility permissions:**
Grant accessibility permissions in System Preferences (see above).

**Service won't start:**
Check log files:

```bash
tail -f ~/.cursor-chat-monitor-service.log
```

## Build Output Structure

The build creates a `dist/` directory with platform-specific files:

### macOS Distribution

```
dist/
├── cursor-chat-monitor.app/            # macOS app bundle
├── cursor-chat-monitor                 # Command-line executable
├── cursor-chat-monitor-service         # Service wrapper script
├── install.sh                          # Installation script
├── README.md                           # macOS-specific documentation
├── .cursor_chat_monitor                # Default configuration
└── com.cursor.chat.monitor.plist       # LaunchAgent plist
```

### Windows Distribution

```
dist/
├── cursor-chat-monitor.exe             # Main executable
├── cursor-chat-monitor-service.exe     # Windows service
├── cursor-chat-monitor-service.bat     # Service wrapper script
├── install.bat                         # Installation script
├── README.md                           # Windows-specific documentation
└── .cursor_chat_monitor                # Default configuration
```

### Linux Distribution

```
dist/
├── cursor-chat-monitor                 # Main executable
├── cursor-chat-monitor-service         # Service wrapper script
├── install.sh                          # Installation script
├── README.md                           # Linux-specific documentation
├── .cursor_chat_monitor                # Default configuration
├── cursor-chat-monitor.service         # System service unit
└── cursor-chat-monitor-user.service    # User service unit
```

## Customization

### Custom Icon

To add a custom icon to the executable:

1. Create an `.icns` file (macOS icon format)
2. Update `build_standalone.py`:
   ```python
   # In the spec file creation, change:
   icon=None,
   # To:
   icon='path/to/your/icon.icns',
   ```

### Exclude/Include Modules

Modify the `excludes` and `hiddenimports` lists in `build_standalone.py`:

```python
excludes=[
    'tkinter',      # GUI toolkit (not needed)
    'matplotlib',   # Plotting (not needed)
    # Add more modules to exclude
],
hiddenimports=[
    'platforms.macos',  # Our platform modules
    # Add more modules to force include
],
```

### Reduce Size

To create a smaller executable:

1. Use `--onefile` instead of `--onedir` (slower startup)
2. Enable UPX compression in the spec file
3. Exclude more unnecessary modules

## Cross-Platform Notes

This build process creates **macOS-only** executables. For other platforms:

- **Windows**: Use PyInstaller on Windows with `platforms.windows`
- **Linux**: Use PyInstaller on Linux with `platforms.linux`

The `build_standalone.py` script can be adapted for other platforms by modifying the PyInstaller spec file.
