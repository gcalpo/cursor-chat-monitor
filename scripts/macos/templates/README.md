# Cursor Chat Monitor - macOS Edition

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
