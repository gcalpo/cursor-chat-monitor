# Cursor Chat Monitor

A mature, production-ready cross-platform tool for monitoring Cursor IDE conversations across multiple windows in real-time. Supports **macOS**, **Windows**, and **Linux** with both interactive console mode and background service operation.

## 🖥️ Platform Support

| Platform    | Status             | Technology         | Quick Start Guide                          |
| ----------- | ------------------ | ------------------ | ------------------------------------------ |
| **macOS**   | ✅ Fully Supported | Accessibility APIs | [macOS Guide](docs/platforms/macos.md)     |
| **Windows** | ✅ Beta Support    | Win32 APIs         | [Windows Guide](docs/platforms/windows.md) |
| **Linux**   | ✅ Beta Support    | AT-SPI             | [Linux Guide](docs/platforms/linux.md)     |

## ✨ Key Features

- **🌍 True cross-platform** - Works seamlessly on macOS, Windows, and Linux
- **🪟 Multi-window monitoring** - Detects content across all open Cursor windows
- **⚡ Real-time chat detection** - Continuous monitoring with configurable intervals
- **🔊 Platform-native audio alerts** - High-quality text-to-speech notifications
- **🔧 Service mode** - Background daemon operation with full lifecycle management
- **📦 Standalone executables** - No Python dependencies required on target systems
- **🎛️ Highly configurable** - Extensive customization via JSON config files

## 🚀 Quick Start

### Simple Run Scripts (Development/Source Mode)

For the easiest experience, use one of the provided run scripts that handle all virtual environment setup automatically:

```bash
# Cross-platform Python script (recommended)
python3 run.py

# Unix/Linux/macOS shell script
./run.sh

# Windows batch script
run.bat

# All scripts support passing arguments to the main app
python3 run.py --debug --interval-ms=2000
./run.sh --platform-info
run.bat --config=my_config.json
```

### Choose Your Platform

Select your operating system for detailed setup instructions:

- **[📱 macOS Setup Guide](docs/platforms/macos.md)** - Complete macOS installation and configuration
- **[🪟 Windows Setup Guide](docs/platforms/windows.md)** - Windows installation and service setup
- **[🐧 Linux Setup Guide](docs/platforms/linux.md)** - Linux distribution-specific instructions

### Manual Usage (Advanced)

```bash
# Check platform support
python3 cursor_chat_monitor.py --platform-info

# Start monitoring (interactive mode)
python3 cursor_chat_monitor.py

# Start as background service
python3 cursor_chat_monitor.py --daemon

# Use custom configuration
python3 cursor_chat_monitor.py --config=my_config.json --debug
```

### Service Management

Each platform provides native service integration:

- **macOS**: LaunchAgent with `cursor-chat-monitor-service start/stop/status`
- **Windows**: Windows Service with Service Control Manager integration
- **Linux**: systemd with `systemctl --user start/stop cursor-chat-monitor`

See platform-specific guides for detailed service management instructions.

## 📚 Documentation

### 🎯 User Guides

- **[Installation Guide](docs/INSTALLATION.md)** - Complete installation instructions for all platforms
- **[Service Management](docs/SERVICE_MANAGEMENT.md)** - Running as background service
- **[Configuration Guide](docs/CONFIGURATION.md)** - JSON configuration and customization
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### 🔧 Platform-Specific Guides

- **[macOS Guide](docs/platforms/macos.md)** - macOS-specific setup, permissions, and LaunchAgent
- **[Windows Guide](docs/platforms/windows.md)** - Windows installation, service, and diagnostics
- **[Linux Guide](docs/platforms/linux.md)** - Distribution-specific setup and systemd integration

### 🏗️ Developer Documentation

- **[Build Guide](docs/BUILD.md)** - Building from source and creating distributions
- **[Architecture Overview](docs/ARCHITECTURE.md)** - Technical implementation details
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Development setup and contribution guidelines

## 🏗️ Architecture

The application uses a sophisticated, modular cross-platform architecture:

```
cursor-chat-monitor/
├── platforms/           # Platform-specific implementations
│   ├── macos.py        # macOS Accessibility APIs
│   ├── windows.py      # Windows Win32 APIs
│   └── linux.py        # Linux AT-SPI
├── core/               # Cross-platform logic
│   ├── monitor.py      # Main monitoring engine
│   └── config.py       # Configuration management
├── scripts/            # Build and deployment
└── docs/               # Comprehensive documentation
    ├── platforms/      # Platform-specific guides
    ├── INSTALLATION.md # Installation instructions
    └── ...            # Additional documentation
```

## ⚙️ Configuration

The monitor supports comprehensive JSON configuration with intelligent priority:

1. `--config=path/to/config.json` (command line argument)
2. `~/.cursor_chat_monitor` (user home directory)
3. Built-in defaults

**Example configuration:**

```json
{
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed"
  ],
  "GENERATING_TEXTS": ["generating"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500,
  "VOICE_NAME": "Daniel",
  "SPEECH_RATE": 175
}
```

See the [Configuration Guide](docs/CONFIGURATION.md) for complete details.

## 🔧 Installation Options

### Standalone Executables (Recommended)

- **No Python required** on target systems
- **Native service integration** for each platform
- **One-click installation** with automated setup

### Source Installation

- **Development flexibility** with full source access
- **Custom modifications** and debugging capabilities
- **Cross-platform Python environment**

See the [Installation Guide](docs/INSTALLATION.md) for detailed instructions.

## 🚨 Need Help?

- **Quick Issues**: Check the [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- **Platform Problems**: See your [Platform-Specific Guide](docs/platforms/)
- **Service Issues**: Review [Service Management](docs/SERVICE_MANAGEMENT.md)
- **Configuration**: Consult the [Configuration Guide](docs/CONFIGURATION.md)

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](docs/CONTRIBUTING.md) for:

- Development environment setup
- Code organization and standards
- Testing procedures
- Pull request guidelines

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built by Claude Sonnet 4** - Enterprise-grade cross-platform monitoring with professional deployment capabilities.
