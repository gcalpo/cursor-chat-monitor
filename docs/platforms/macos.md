# macOS Setup Guide

Complete guide for installing and running Cursor Chat Monitor on macOS.

## 📋 System Requirements

- **macOS 10.14 (Mojave) or later**
- **Cursor IDE installed and running**
- **Terminal access** (for installation and configuration)

## 🚀 Quick Installation

### Option 1: Standalone Executable (Recommended)

```bash
# Download or build from source
git clone https://github.com/your-repo/cursor-chat-monitor
cd cursor-chat-monitor
python3 scripts/build_macos.py

# System-wide installation (recommended)
cd dist/
sudo ./install.sh

# User-only installation
./install.sh --user

# Verify installation
cursor-chat-monitor --platform-info
which cursor-chat-monitor-service
```

### Option 2: Python Source Installation

```bash
# Clone repository
git clone https://github.com/your-repo/cursor-chat-monitor
cd cursor-chat-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Test installation
python3 cursor_chat_monitor.py --platform-info
```

## 🔐 Required Permissions

### Accessibility Permissions (Required)

macOS requires explicit accessibility permissions for the monitor to read Cursor's content.

**Method 1: Automated Setup**

```bash
# Open System Preferences directly to accessibility settings
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
```

**Method 2: Manual Setup**

1. Open **System Preferences** → **Security & Privacy** → **Privacy**
2. Click **Accessibility** in the left sidebar
3. Click the lock icon and enter your password
4. Click the **+** button
5. Navigate to and select **Terminal** (or your terminal app)
6. Enable the checkbox for Terminal

**Verification:**

```bash
# Check accessibility permissions
sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT service, client, allowed FROM access WHERE service='kTCCServiceAccessibility';"
```

## 🎵 Audio Configuration

### Voice Selection

```bash
# List all available voices
say -v "?"

# Test a specific voice
say -v Daniel "Cursor monitor test message"

# Popular voice options
say -v Alex "Test message"      # Default male voice
say -v Victoria "Test message"  # Female voice
say -v Daniel "Test message"    # British male voice
say -v Fiona "Test message"     # Scottish female voice
```

### Configuration File

Create `~/.cursor_chat_monitor` with macOS-specific settings:

```json
{
  "VOICE_NAME": "Daniel",
  "SPEECH_RATE": 175,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "trouble connecting to the model provider"
  ],
  "GENERATING_TEXTS": ["generating"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500
}
```

## 🔧 Service Management

### LaunchAgent Integration

The macOS version integrates with the native LaunchAgent system for proper background service management.

**Service Installation** (done automatically by installer):

```bash
# LaunchAgent plist location
~/Library/LaunchAgents/com.cursor.chat.monitor.plist

# Log file location
~/Library/Logs/cursor-chat-monitor.log
```

### Service Commands

```bash
# Start service
cursor-chat-monitor-service start

# Stop service
cursor-chat-monitor-service stop

# Check service status
cursor-chat-monitor-service status

# Restart service
cursor-chat-monitor-service restart

# View service logs
cursor-chat-monitor-service logs

# Run in foreground for debugging
cursor-chat-monitor-service console

# Enable auto-start on login
cursor-chat-monitor-service enable

# Disable auto-start
cursor-chat-monitor-service disable
```

### Manual LaunchAgent Management

```bash
# Load LaunchAgent manually
launchctl load ~/Library/LaunchAgents/com.cursor.chat.monitor.plist

# Unload LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.cursor.chat.monitor.plist

# Check LaunchAgent status
launchctl list | grep cursor.chat.monitor

# View detailed LaunchAgent info
launchctl print gui/$(id -u)/com.cursor.chat.monitor
```

## 🐛 Troubleshooting

### Common Issues

#### Permission Denied Errors

```bash
# Reset accessibility permissions (requires restart)
sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "DELETE FROM access WHERE service='kTCCServiceAccessibility';"

# Check current permissions
sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db \
  "SELECT * FROM access WHERE service='kTCCServiceAccessibility';"
```

#### Service Won't Start

```bash
# Check LaunchAgent syntax
plutil -lint ~/Library/LaunchAgents/com.cursor.chat.monitor.plist

# View LaunchAgent details
launchctl print gui/$(id -u)/com.cursor.chat.monitor

# Check for errors in service logs
tail -f ~/Library/Logs/cursor-chat-monitor.log

# Restart with debug mode
cursor-chat-monitor-service console --debug
```

#### Cursor Not Detected

```bash
# Check if Cursor is running
ps aux | grep -i cursor

# List all applications with AppleScript
osascript -e 'tell application "System Events" to get name of every process'

# Debug accessibility tree
osascript -e 'tell application "System Events" to get name of every process whose name contains "cursor"'
```

#### TTS Not Working

```bash
# Test system TTS
say "Test message"

# Check audio output
system_profiler SPAudioDataType

# Test with different voice
say -v "?" | head -5
say -v Alex "Test message"

# Check volume settings
osascript -e "get volume settings"
```

### Diagnostic Commands

```bash
# Comprehensive system check
cursor-chat-monitor --platform-info

# Check macOS version
sw_vers

# Verify Python environment (if using source)
which python3
python3 --version

# Check accessibility framework status
/System/Library/CoreServices/Applications/Directory\ Utility.app/Contents/MacOS/Directory\ Utility &

# View system console logs
log show --predicate 'process == "cursor-chat-monitor"' --last 1h

# Stream live system logs
log stream --predicate 'process == "cursor-chat-monitor"'
```

### Log Analysis

```bash
# Service logs
tail -f ~/Library/Logs/cursor-chat-monitor.log
tail -f ~/.cursor-chat-monitor-service.log

# LaunchAgent logs
tail -f ~/Library/Logs/com.cursor.chat.monitor.log

# System console logs (requires admin)
sudo log show --predicate 'process == "cursor-chat-monitor"'

# Search for specific errors
grep -i error ~/Library/Logs/cursor-chat-monitor.log
grep -i "permission denied" ~/Library/Logs/cursor-chat-monitor.log
grep -i "accessibility" ~/Library/Logs/cursor-chat-monitor.log
```

## 🔧 Advanced Configuration

### Custom LaunchAgent Configuration

Edit `~/Library/LaunchAgents/com.cursor.chat.monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cursor.chat.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cursor-chat-monitor</string>
        <string>--daemon</string>
        <string>--config</string>
        <string>/Users/[username]/.cursor_chat_monitor</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/[username]/Library/Logs/cursor-chat-monitor.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/[username]/Library/Logs/cursor-chat-monitor-error.log</string>
</dict>
</plist>
```

### Environment Variables

```bash
# Set in ~/.zshrc or ~/.bash_profile
export CURSOR_MONITOR_CONFIG="$HOME/.cursor_chat_monitor"
export CURSOR_MONITOR_DEBUG=1
export CURSOR_MONITOR_LOG_LEVEL="DEBUG"
```

## 📱 Integration with macOS Features

### Notification Center Integration (Future Enhancement)

The current version uses audio alerts, but can be extended to support macOS notifications:

```bash
# Example notification (not yet implemented)
osascript -e 'display notification "Cursor needs attention" with title "Cursor Monitor"'
```

### Spotlight Integration

```bash
# Make cursor-chat-monitor searchable in Spotlight
sudo mdutil -i on /usr/local/bin/
```

### Activity Monitor

```bash
# Monitor resource usage
top -pid $(pgrep cursor-chat-monitor)

# Check memory usage
ps -o pid,ppid,pcpu,pmem,comm -p $(pgrep cursor-chat-monitor)
```

## 🆘 Getting Help

- **Accessibility Issues**: Check [Apple's Accessibility Documentation](https://developer.apple.com/accessibility/)
- **LaunchAgent Problems**: See [Apple's LaunchAgent Guide](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- **General Issues**: Return to [Main Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**macOS-specific implementation** using PyObjC and Cocoa Accessibility APIs for robust window monitoring and native TTS integration.
