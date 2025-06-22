# Configuration Guide

Complete guide for configuring Cursor Chat Monitor across all platforms.

## 📋 Configuration Overview

Cursor Chat Monitor uses JSON configuration files with intelligent priority resolution:

1. **`--config=path/to/config.json`** (command line argument) - Highest priority
2. **`~/.cursor_chat_monitor`** (user home directory) - Default location
3. **Built-in defaults** - Fallback configuration

## 🔧 Configuration File Locations

### Platform-Specific Locations

| Platform    | Configuration File Location          |
| ----------- | ------------------------------------ |
| **macOS**   | `~/.cursor_chat_monitor`             |
| **Windows** | `%USERPROFILE%\.cursor_chat_monitor` |
| **Linux**   | `~/.cursor_chat_monitor`             |

### Creating Configuration Files

```bash
# macOS/Linux
touch ~/.cursor_chat_monitor

# Windows (Command Prompt)
echo. > %USERPROFILE%\.cursor_chat_monitor

# Windows (PowerShell)
New-Item -Path "$env:USERPROFILE\.cursor_chat_monitor" -ItemType File
```

## 📝 Complete Configuration Schema

### Example Configuration File

```json
{
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "trouble connecting to the model provider",
    "File is being edited by another chat"
  ],
  "GENERATING_TEXTS": ["generating", "thinking", "processing"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500,
  "MAX_SEARCH_DEPTH": 30,

  "VOICE_NAME": "Daniel",
  "SPEECH_RATE": 175,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,

  "ANNOUNCE_GENERATING_STARTED": true,
  "GENERATING_STARTED_DEBOUNCE_SECONDS": 10,

  "MONITOR_LOG_FILE": "cursor_resume_monitor.log",
  "LOG_TO_FILE": false,
  "DEFAULT_DEBUG_MODE": false
}
```

## ⚙️ Configuration Options Reference

### Text Detection Settings

#### `AWAITING_USER_ACTION_TEXTS`

- **Type**: Array of strings
- **Default**: `["resume the conversation", "Connection failed", "trouble connecting to the model provider", "File is being edited by another chat"]`
- **Description**: Text patterns that trigger alerts when their count increases
- **Example**:
  ```json
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "Model temporarily unavailable",
    "Rate limit exceeded"
  ]
  ```

#### `GENERATING_TEXTS`

- **Type**: Array of strings
- **Default**: `["generating"]`
- **Description**: Text patterns that indicate AI generation in progress
- **Example**:
  ```json
  "GENERATING_TEXTS": [
    "generating",
    "thinking...",
    "processing your request"
  ]
  ```

#### `DEFAULT_SCAN_INTERVAL_MS`

- **Type**: Integer (milliseconds)
- **Default**: `1500`
- **Range**: `500` - `10000` (recommended)
- **Description**: How often to scan Cursor windows for text changes
- **Performance Impact**: Lower values = more responsive but higher CPU usage

#### `MAX_SEARCH_DEPTH`

- **Type**: Integer
- **Default**: `30`
- **Range**: `10` - `100`
- **Description**: Maximum depth to traverse accessibility tree
- **Performance Impact**: Higher values = more thorough but slower scanning

### Audio Configuration

#### `VOICE_NAME`

- **Type**: String
- **Default**: Platform-specific (see below)
- **Description**: Voice to use for text-to-speech announcements
- **Special Value**: `"PLATFORM_DEFAULT"` - Automatically uses platform-specific default voice
- **Platform Defaults**:
  - **Windows**: `"Microsoft David Desktop"` (Male)
  - **macOS**: `"Daniel"` (British male)
  - **Linux**: `"default"` (System default)

**Configuration Examples**:

```json
// Use platform-specific default (recommended)
"VOICE_NAME": "PLATFORM_DEFAULT"

// Override with specific voice
"VOICE_NAME": "Microsoft Zira Desktop"    // Windows
"VOICE_NAME": "Victoria"                  // macOS
"VOICE_NAME": "en+f3"                     // Linux
```

**Platform Voice Options**:

```json
// macOS
"VOICE_NAME": "Daniel"        // British male
"VOICE_NAME": "Alex"          // Default male
"VOICE_NAME": "Victoria"      // Female

// Windows
"VOICE_NAME": "Microsoft David Desktop"   // Male
"VOICE_NAME": "Microsoft Zira Desktop"    // Female

// Linux (espeak)
"VOICE_NAME": "en+f3"         // Female English
"VOICE_NAME": "en+m3"         // Male English
```

#### `SPEECH_RATE`

- **Type**: Integer (words per minute) or String
- **Default**: Platform-specific (see below)
- **Range**: `50` - `300`
- **Description**: Speed of text-to-speech announcements
- **Special Value**: `"PLATFORM_DEFAULT"` - Automatically uses platform-specific default rate
- **Platform Defaults**:
  - **All Platforms**: `175` WPM
- **Platform Notes**:
  - macOS: Uses `say` command rate parameter
  - Windows: Uses pyttsx3 rate setting
  - Linux: Uses espeak speed parameter

**Configuration Examples**:

```json
// Use platform-specific default (recommended)
"SPEECH_RATE": "PLATFORM_DEFAULT"

// Override with specific rate
"SPEECH_RATE": 200
```

#### `WINDOW_TITLE_ANNOUNCE_MODE`

- **Type**: String
- **Default**: `"next to last"` (Windows), `"last"` (macOS/Linux)
- **Options**: `"full"`, `"first"`, `"last"`, `"next to last"`
- **Description**: How to announce window titles in audio alerts
- **Examples**:
  ```json
  // Window title: "main.py — Cursor"
  "full":        "main.py — Cursor"
  "first":       "main.py"
  "last":        "Cursor"
  "next to last": "main.py"
  ```

#### `REPLACE_PERIODS_IN_ANNOUNCEMENT`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Replace periods with spaces in audio announcements for better speech clarity

### Alert Behavior

#### `ANNOUNCE_GENERATING_STARTED`

- **Type**: Boolean
- **Default**: `true`
- **Description**: Play audio alert when AI generation starts (not just when it needs user action)

#### `GENERATING_STARTED_DEBOUNCE_SECONDS`

- **Type**: Integer (seconds)
- **Default**: `10`
- **Range**: `5` - `60`
- **Description**: Minimum time between "generation started" alerts for the same window

### Logging Configuration

#### `MONITOR_LOG_FILE`

- **Type**: String (file path)
- **Default**: `"cursor_resume_monitor.log"`
- **Description**: Log file name or path (relative to user home if not absolute)
- **Examples**:
  ```json
  "MONITOR_LOG_FILE": "cursor_monitor.log"                    // Home directory
  "MONITOR_LOG_FILE": "/var/log/cursor-chat-monitor.log"      // Absolute path
  "MONITOR_LOG_FILE": "logs/cursor_monitor.log"               // Relative subdirectory
  ```

#### `LOG_TO_FILE`

- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable file logging (automatically enabled in daemon mode)

#### `DEFAULT_DEBUG_MODE`

- **Type**: Boolean
- **Default**: `false`
- **Description**: Enable debug output by default (shows extracted text and detailed operations)

## 🎯 Platform-Specific Configuration

### Unified Configuration (Recommended)

The configuration system now supports platform-specific defaults using `"PLATFORM_DEFAULT"` placeholders. This allows one configuration file to work across all platforms:

```json
{
  "_comment": "Unified configuration that works on all platforms",
  "_comment2": "Voice settings automatically use platform-specific defaults",
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "trouble connecting to the model provider",
    "File is being edited by another chat"
  ],
  "GENERATING_TEXTS": ["generating"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500,
  "MAX_SEARCH_DEPTH": 30,
  "VOICE_NAME": "PLATFORM_DEFAULT",
  "SPEECH_RATE": "PLATFORM_DEFAULT",
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "ANNOUNCE_GENERATING_STARTED": true,
  "GENERATING_STARTED_DEBOUNCE_SECONDS": 10
}
```

**Platform Defaults Applied:**
- **Windows**: `"Microsoft David Desktop"` voice at `175` WPM
- **macOS**: `"Daniel"` voice at `175` WPM  
- **Linux**: `"default"` voice at `175` WPM

### Platform-Specific Overrides

You can still override the platform defaults with specific values:

#### macOS Configuration

```json
{
  "VOICE_NAME": "Victoria",
  "SPEECH_RATE": 200,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "DEFAULT_SCAN_INTERVAL_MS": 1500,
  "MAX_SEARCH_DEPTH": 30
}
```

**macOS Voice Options:**

```bash
# List all available voices
say -v "?"

# Test voices
say -v Daniel "Test message"     # British male
say -v Alex "Test message"       # Default male
say -v Victoria "Test message"   # Female
say -v Fiona "Test message"      # Scottish female
```

#### Windows Configuration

```json
{
  "VOICE_NAME": "Microsoft Zira Desktop",
  "SPEECH_RATE": 180,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "DEFAULT_SCAN_INTERVAL_MS": 2000,
  "MAX_SEARCH_DEPTH": 25
}
```

**Windows Voice Options:**

```cmd
REM List available voices
powershell -c "Add-Type -AssemblyName System.Speech; [System.Speech.Synthesis.SpeechSynthesizer]::new().GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"

REM Common voices:
REM "Microsoft David Desktop" (Male)
REM "Microsoft Zira Desktop" (Female)
REM "Microsoft Mark Desktop" (Male)
REM "Microsoft Hazel Desktop" (Female)
```

#### Linux Configuration

```json
{
  "VOICE_NAME": "en+f3",
  "SPEECH_RATE": 150,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "DEFAULT_SCAN_INTERVAL_MS": 1800,
  "MAX_SEARCH_DEPTH": 35
}
```

**Linux Voice Options:**

```bash
# List espeak voices
espeak --voices

# Test voices
echo "Test message" | espeak -v en+f3 -s 150    # Female English
echo "Test message" | espeak -v en+m3 -s 150    # Male English
echo "Test message" | espeak -v en-us+f1 -s 150 # US Female
```

## 🚀 Use Case Examples

### High-Performance Setup

For systems with ample resources:

```json
{
  "DEFAULT_SCAN_INTERVAL_MS": 500,
  "MAX_SEARCH_DEPTH": 50,
  "SPEECH_RATE": 200,
  "DEFAULT_DEBUG_MODE": true,
  "LOG_TO_FILE": true
}
```

### Low-Resource Setup

For older systems or battery conservation:

```json
{
  "DEFAULT_SCAN_INTERVAL_MS": 3000,
  "MAX_SEARCH_DEPTH": 15,
  "SPEECH_RATE": 150,
  "DEFAULT_DEBUG_MODE": false,
  "LOG_TO_FILE": false
}
```

### Development/Debug Setup

For troubleshooting and development:

```json
{
  "DEFAULT_SCAN_INTERVAL_MS": 1000,
  "DEFAULT_DEBUG_MODE": true,
  "LOG_TO_FILE": true,
  "MONITOR_LOG_FILE": "debug_cursor_monitor.log",
  "SPEECH_RATE": 250
}
```

### Quiet/Minimal Setup

For minimal interruptions:

```json
{
  "ANNOUNCE_GENERATING_STARTED": false,
  "GENERATING_STARTED_DEBOUNCE_SECONDS": 30,
  "SPEECH_RATE": 120,
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "WINDOW_TITLE_ANNOUNCE_MODE": "first"
}
```

## 🔧 Advanced Configuration

### Environment Variables

You can override configuration via environment variables:

```bash
# macOS/Linux
export CURSOR_MONITOR_CONFIG="/path/to/custom/config.json"
export CURSOR_MONITOR_DEBUG=1
export CURSOR_MONITOR_LOG_LEVEL="DEBUG"

# Windows (Command Prompt)
set CURSOR_MONITOR_CONFIG=C:\path\to\custom\config.json
set CURSOR_MONITOR_DEBUG=1

# Windows (PowerShell)
$env:CURSOR_MONITOR_CONFIG = "C:\path\to\custom\config.json"
$env:CURSOR_MONITOR_DEBUG = "1"
```

### Runtime Configuration Updates

Some settings can be updated without restarting:

```bash
# Send SIGHUP to reload configuration (Unix systems)
kill -HUP $(pgrep cursor-chat-monitor)

# Or restart the service
cursor-chat-monitor-service restart
```

### Configuration Validation

```bash
# Validate configuration file
cursor-chat-monitor --config=my_config.json --validate-config

# Test configuration with dry run
cursor-chat-monitor --config=my_config.json --debug --dry-run
```

## 🛠️ Troubleshooting Configuration

### Common Configuration Issues

#### Invalid JSON Syntax

```bash
# Validate JSON syntax
python3 -m json.tool ~/.cursor_chat_monitor

# Fix common issues:
# - Missing commas between items
# - Trailing commas
# - Unquoted strings
# - Incorrect boolean values (use true/false, not True/False)
```

#### Voice Not Found

```bash
# macOS - List available voices
say -v "?"

# Windows - List voices
powershell -c "Add-Type -AssemblyName System.Speech; [System.Speech.Synthesis.SpeechSynthesizer]::new().GetInstalledVoices()"

# Linux - List espeak voices
espeak --voices
```

#### File Permission Issues

```bash
# Check file permissions
ls -la ~/.cursor_chat_monitor

# Fix permissions
chmod 644 ~/.cursor_chat_monitor

# Check directory permissions
ls -la ~/.cursor-chat-monitor/
```

### Configuration Debugging

```bash
# Show current configuration
cursor-chat-monitor --show-config

# Debug configuration loading
cursor-chat-monitor --debug --config=/path/to/config.json

# Test specific settings
cursor-chat-monitor --config=test_config.json --interval-ms=1000 --debug
```

## 📚 Configuration Best Practices

1. **Start with defaults** - Modify incrementally from working baseline
2. **Test changes** - Use debug mode to verify configuration changes
3. **Platform optimization** - Use platform-specific settings for best performance
4. **Backup configs** - Keep working configurations backed up
5. **Document changes** - Comment your configuration files (JSON doesn't support comments, but keep separate documentation)
6. **Validate syntax** - Always validate JSON before deploying
7. **Monitor performance** - Adjust scan intervals based on system performance

---

**Configuration system** designed for flexibility across platforms while maintaining sensible defaults for immediate usability.
