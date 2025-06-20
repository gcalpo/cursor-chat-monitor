# Cursor Chat Monitor

A macOS accessibility-based tool for monitoring Cursor IDE conversations across multiple windows in real-time.

## Features

- **Multi-window monitoring** - Detects content across all open Cursor windows
- **Real-time chat detection** - Continuous monitoring with configurable intervals
- **Smart content filtering** - AI-powered confidence scoring to identify relevant messages
- **JSON logging** - Structured output for integration with other tools

## Quick Start

### Prerequisites

1. Grant accessibility permissions to Terminal/Python in System Preferences
2. Ensure Cursor IDE is running with open windows

### Installation

```bash
# Clone and setup
git clone <repository-url>
cd cursor-chat-monitor
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Usage

```bash
# Continuous monitoring (default 10s intervals)
python3 cursor_chat_monitor.py

# Custom monitoring interval and output
python3 cursor_chat_monitor.py --interval=5 --output=chat_log.json
```

## Core Scripts

| Script                   | Purpose                                     |
| ------------------------ | ------------------------------------------- |
| `cursor_chat_monitor.py` | Continuous monitoring with real-time alerts |

## Sample Output

```
🔔 Found 1 new messages:
------------------------------------------------------------
🟢 Message 1 (Confidence: 0.95)
   Window: chat.py — Cursor
   Type: AXStaticText
   Content: Error: Invalid Python interpreter selected...
```

## Project Structure

```
cursor-chat-monitor/
├── .cursor_chat__monitor             # Configuration template
├── cursor_chat_monitor.py           # Main monitoring script
├── requirements.txt                 # Dependencies
├── PROJECT_PLAN.md                 # Project planning document
├── TASK_LIST.md                    # Task tracking
└── LICENSE                         # License file
```

## Configuration

The monitor can be configured using a JSON configuration file. The configuration priority is:

1. File specified with `--config=path/to/config.json` command line argument
2. `~/.cursor_chat_monitor` in your home directory (if it exists)
3. Default built-in configuration

### Creating a Configuration File

Copy the example configuration file to your home directory:

```bash
cp .cursor_chat_monitor ~/.cursor_chat_monitor
```

Or create a custom configuration file and specify it with `--config`:

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

| Option                                | Type    | Default                       | Description                                                 |
| ------------------------------------- | ------- | ----------------------------- | ----------------------------------------------------------- |
| `AWAITING_USER_ACTION_TEXTS`          | array   | See above                     | Texts to monitor for (triggers alerts when count increases) |
| `GENERATING_TEXTS`                    | array   | `["generating"]`              | Texts that indicate generation in progress                  |
| `DEFAULT_SCAN_INTERVAL_MS`            | number  | `1500`                        | Scan interval in milliseconds                               |
| `MAX_SEARCH_DEPTH`                    | number  | `30`                          | Maximum depth to search in accessibility tree               |
| `VOICE_NAME`                          | string  | `"Daniel"`                    | macOS voice name for audio alerts                           |
| `SPEECH_RATE`                         | number  | `175`                         | Speech rate in words per minute (100-300)                   |
| `WINDOW_TITLE_ANNOUNCE_MODE`          | string  | `"last"`                      | How to announce window titles: "full", "first", or "last"   |
| `REPLACE_PERIODS_IN_ANNOUNCEMENT`     | boolean | `true`                        | Replace periods with spaces in announcements                |
| `ANNOUNCE_GENERATING_STARTED`         | boolean | `true`                        | Play alert when generation starts                           |
| `GENERATING_STARTED_DEBOUNCE_SECONDS` | number  | `10`                          | Debounce time for "generating started" alerts               |
| `MONITOR_LOG_FILE`                    | string  | `"cursor_resume_monitor.log"` | Log file name                                               |
| `LOG_TO_FILE`                         | boolean | `false`                       | Enable file logging                                         |
| `DEFAULT_DEBUG_MODE`                  | boolean | `false`                       | Enable debug mode by default                                |

## Technical Notes

- **Platform**: macOS only (uses Accessibility APIs)
- **Performance**: Efficient element traversal with duplicate detection
- **Dependencies**: PyObjC for macOS accessibility integration

## Development

The `exploratory_scripts/` directory contains development scripts documenting the implementation process.

## License

See LICENSE file for details.
