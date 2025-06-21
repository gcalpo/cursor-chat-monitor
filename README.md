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

### Option 1: Precompiled Binaries (Recommended)

**For most users, we recommend using the precompiled standalone executables that require no Python installation:**

#### Download and Install

1. **Choose your platform** and download the appropriate precompiled binary:
   - **[📱 macOS Binary](docs/platforms/macos.md#option-1-standalone-executable-recommended)** - Universal binary (Intel + Apple Silicon)
   - **[🪟 Windows Binary](docs/platforms/windows.md#option-1-standalone-executable-recommended)** - Windows 10+ compatible
   - **[🐧 Linux Binary](docs/platforms/linux.md#option-1-standalone-executable-recommended)** - Most distributions supported

2. **Install and run** using platform-specific instructions in the guides above

#### Quick Usage Examples

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

#### Service Management

Each platform provides native service integration:

- **macOS**: LaunchAgent with `cursor-chat-monitor-service start/stop/status`
- **Windows**: Windows Service with Service Control Manager integration
- **Linux**: systemd with `systemctl --user start/stop cursor-chat-monitor`

**💡 Benefits of precompiled binaries:**
- ✅ **No Python installation required**
- ✅ **Native service integration** for each platform
- ✅ **One-click installation** with automated setup
- ✅ **Production-ready** with proper permissions and configurations

### Option 2: Run from Source (Development)

**For developers or users who prefer to run from source code:**

#### Simple Run Scripts

Use one of the provided run scripts that handle all virtual environment setup automatically:

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

#### Manual Usage (Advanced)

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

**💡 For Windows Users:** If you don't have Python installed, the [Windows Guide](docs/platforms/windows.md) includes comprehensive Python 3 installation instructions with troubleshooting steps.

### Choose Your Platform

Select your operating system for detailed setup instructions:

- **[📱 macOS Setup Guide](docs/platforms/macos.md)** - Complete macOS installation and configuration
- **[🪟 Windows Setup Guide](docs/platforms/windows.md)** - Windows installation, Python setup, and service configuration
- **[🐧 Linux Setup Guide](docs/platforms/linux.md)** - Linux distribution-specific instructions

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

The monitor supports comprehensive JSON configuration with intelligent priority and **platform-specific defaults**:

1. `--config=path/to/config.json` (command line argument)
2. `~/.cursor_chat_monitor` (user home directory)
3. Built-in platform-specific defaults

**Unified Configuration (Works on all platforms):**

```json
{
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed"
  ],
  "GENERATING_TEXTS": ["generating"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500,
  "VOICE_NAME": "PLATFORM_DEFAULT",
  "SPEECH_RATE": "PLATFORM_DEFAULT"
}
```

**Platform Defaults Applied:**
- **Windows**: `"Microsoft David Desktop"` voice at `175` WPM
- **macOS**: `"Daniel"` voice at `175` WPM  
- **Linux**: `"default"` voice at `175` WPM

**Custom Configuration:**

```json
{
  "VOICE_NAME": "Microsoft Zira Desktop",  // Override platform default
  "SPEECH_RATE": 200,                      // Override platform default
  "DEFAULT_SCAN_INTERVAL_MS": 1000,
  "MAX_SEARCH_DEPTH": 25
}
```

See the [Configuration Guide](docs/CONFIGURATION.md) for complete details and platform-specific options.

## 🔧 Installation Options

### Precompiled Binaries (Primary Recommendation)

**For most users, precompiled standalone executables provide the best experience:**

- **🚀 Zero setup required** - No Python installation needed on target systems
- **🔧 Native service integration** - Platform-specific service management for each OS
- **⚡ One-click installation** - Automated setup with proper permissions and configurations
- **🛡️ Production-ready** - Tested and optimized for each platform
- **📦 Self-contained** - All dependencies bundled (~50MB per platform)

**Download and installation guides:**
- **[macOS Binary Installation](docs/platforms/macos.md#option-1-standalone-executable-recommended)**
- **[Windows Binary Installation](docs/platforms/windows.md#option-1-standalone-executable-recommended)**
- **[Linux Binary Installation](docs/platforms/linux.md#option-1-standalone-executable-recommended)**

### Source Installation (Developer Option)

**For developers, contributors, or users who need custom modifications:**

- **🔧 Development flexibility** - Full source access and debugging capabilities
- **⚙️ Custom modifications** - Ability to modify and extend functionality
- **🐍 Cross-platform Python environment** - Standard Python development workflow
- **📚 Learning opportunity** - Understand the codebase and architecture

**See the [Build Guide](docs/BUILD.md) for creating your own precompiled binaries.**

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
