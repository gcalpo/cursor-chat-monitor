# Cursor Chat Monitor (Cross-Platform)

A cross-platform accessibility-based tool for monitoring Cursor IDE conversations across multiple windows in real-time. Now supports **macOS**, **Windows**, and **Linux**!

## 🖥️ Platform Support

| Platform    | Status             | Technology         | TTS Support     | Notes                              |
| ----------- | ------------------ | ------------------ | --------------- | ---------------------------------- |
| **macOS**   | ✅ Fully Supported | Accessibility APIs | `say` command   | Requires accessibility permissions |
| **Windows** | 🧪 Beta            | Win32 APIs         | pyttsx3         | No special permissions needed      |
| **Linux**   | 🧪 Beta            | AT-SPI             | espeak/festival | Requires AT-SPI running            |

## Features

- **🌍 Cross-platform** - Works on macOS, Windows, and Linux
- **🪟 Multi-window monitoring** - Detects content across all open Cursor windows
- **⚡ Real-time chat detection** - Continuous monitoring with configurable intervals
- **🔊 Audio alerts** - Platform-specific text-to-speech notifications
- **📝 JSON logging** - Structured output for integration with other tools
- **🎛️ Highly configurable** - Customizable via JSON config files

## Quick Start

### Prerequisites

#### macOS

1. Grant accessibility permissions to Terminal/Python in System Preferences
2. Ensure Cursor IDE is running with open windows

#### Windows (NOT YET TESTED)

1. Install required dependencies: `pip install pywin32 pyttsx3`
2. Ensure Cursor IDE is running

#### Linux (NOT YET TESTED)

1. Ensure AT-SPI is running: `sudo systemctl start at-spi-dbus-bus`
2. Install dependencies: `pip install pyatspi`
3. Install TTS: `sudo apt-get install espeak` (Ubuntu/Debian)

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd cursor-chat-monitor
python3 -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip3 install -r requirements.txt
```

### Usage

```bash
# Check platform support
python3 cursor_chat_monitor.py --platform-info

# Basic monitoring (default 1.5s intervals)
python3 cursor_chat_monitor.py

# Custom monitoring interval and debug mode
python3 cursor_chat_monitor.py --interval-ms=2000 --debug

# Use custom config file
python3 cursor_chat_monitor.py --config=my_config.json
```

## Architecture

The application uses a **modular, cross-platform architecture** with platform-specific implementations:

```
cursor-chat-monitor/
├── platforms/                    # Platform-specific implementations
│   ├── __init__.py              # Platform detection & factory
│   ├── base.py                  # Abstract base classes
│   ├── macos.py                 # macOS implementation (Accessibility APIs)
│   ├── windows.py               # Windows implementation (Win32 APIs)
│   └── linux.py                 # Linux implementation (AT-SPI)
├── core/                        # Cross-platform core logic
│   ├── __init__.py
│   ├── config.py                # Configuration management
│   └── monitor.py               # Main monitoring logic
├── cursor_chat_monitor.py       # Main entry point
├── requirements.txt             # Platform-specific dependencies
└── README.md                    # This file
```

## Configuration

The monitor can be configured using a JSON configuration file. The configuration priority is:

1. File specified with `--config=path/to/config.json` command line argument
2. `~/.cursor_chat_monitor` in your home directory (if it exists)
3. Default built-in configuration

### Creating a Configuration File

Create a configuration file in your home directory:

```bash
# Create default config
cp .cursor_chat_monitor ~/.cursor_chat_monitor
```

Or create a custom configuration file:

```json
{
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "trouble connecting to the model provider",
    "File is being edited by another chat"
  ],
  "GENERATING_TEXTS": ["generating"],
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

### Configuration Options

| Option                                | Type    | Default          | Description                                               |
| ------------------------------------- | ------- | ---------------- | --------------------------------------------------------- |
| `AWAITING_USER_ACTION_TEXTS`          | array   | See config       | Texts that trigger alerts when count increases            |
| `GENERATING_TEXTS`                    | array   | `["generating"]` | Texts that indicate generation in progress                |
| `DEFAULT_SCAN_INTERVAL_MS`            | number  | `1500`           | Scan interval in milliseconds                             |
| `MAX_SEARCH_DEPTH`                    | number  | `30`             | Maximum depth to search in accessibility tree             |
| `VOICE_NAME`                          | string  | `"Daniel"`       | Voice name for TTS (platform-specific)                    |
| `SPEECH_RATE`                         | number  | `175`            | Speech rate in words per minute                           |
| `WINDOW_TITLE_ANNOUNCE_MODE`          | string  | `"last"`         | How to announce window titles: "full", "first", or "last" |
| `REPLACE_PERIODS_IN_ANNOUNCEMENT`     | boolean | `true`           | Replace periods with spaces in announcements              |
| `ANNOUNCE_GENERATING_STARTED`         | boolean | `true`           | Play alert when generation starts                         |
| `GENERATING_STARTED_DEBOUNCE_SECONDS` | number  | `10`             | Debounce time for "generating started" alerts             |
| `LOG_TO_FILE`                         | boolean | `false`          | Enable file logging                                       |
| `DEFAULT_DEBUG_MODE`                  | boolean | `false`          | Enable debug mode by default                              |

## Platform-Specific Notes

### macOS

- **Permissions**: Must grant accessibility permissions in System Preferences
- **TTS**: Uses built-in `say` command with high-quality voices
- **Window Detection**: Full accessibility tree traversal for comprehensive text extraction

### Windows

- **Dependencies**: Requires `pywin32` and `pyttsx3`
- **TTS**: Uses Windows Speech API via pyttsx3
- **Window Detection**: Win32 API window enumeration and text extraction

### Linux

- **Dependencies**: Requires `pyatspi` and `espeak`/`festival`
- **TTS**: Uses espeak (primary) or festival (fallback)
- **Window Detection**: AT-SPI accessibility framework
- **Setup**: May need to start AT-SPI service: `systemctl --user start at-spi-dbus-bus`

## Development

### Adding Platform Support

To add support for a new platform:

1. Create `platforms/newplatform.py`
2. Implement `AppAccessor`, `WindowElement`, and `AlertSystem` classes
3. Add platform detection in `platforms/__init__.py`
4. Update `requirements.txt` with platform-specific dependencies

### Testing

```bash
# Run platform-specific tests
python3 -m pytest tests/

# Test platform detection
python3 cursor_chat_monitor.py --platform-info

# Debug mode for troubleshooting
python3 cursor_chat_monitor.py --debug
```

## Sample Output

```
🔍 Starting Cursor Multi-Text Monitor
🖥️  Platform: macOS
📊 Session ID: 20241201_143022
🎯 Target texts: ['resume the conversation', 'Connection failed']
🎯 Generating texts: ['generating']
⏱️  Scan interval: 1500 ms
🔊 Audio alerts: MacOS
🚀 Press Ctrl+C to stop
============================================================
🚨 ALERT: 'resume the conversation' count increased!
   Window: chat.py — Cursor
   Count: 0 → 1
   Time: 14:30:45
----------------------------------------
```

## Troubleshooting

### Permission Issues

- **macOS**: Enable accessibility permissions in System Preferences
- **Linux**: Ensure AT-SPI is running and your user has proper permissions

### Dependencies

- Use platform-specific package managers when pip fails
- Check `--platform-info` for detailed environment information

### Performance

- Adjust `DEFAULT_SCAN_INTERVAL_MS` for better performance vs. responsiveness
- Reduce `MAX_SEARCH_DEPTH` if experiencing slowdowns

## License

See LICENSE file for details.
