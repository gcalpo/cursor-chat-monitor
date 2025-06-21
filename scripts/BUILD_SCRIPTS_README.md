# Platform-Specific Build Scripts

This directory contains comprehensive build scripts that handle the entire build process for each platform, including virtual environment setup, dependency installation, and building.

## Quick Start

### Universal Build (Recommended)

```bash
./build-all.sh    # Auto-detects platform and builds
```

### Platform-Specific Builds

```bash
# macOS
./build-macos.sh

# Linux
./build-linux.sh

# Windows (in Command Prompt)
build-windows.bat
```

## Build Scripts

### Universal Scripts

#### `build-all.sh`

- **Purpose**: Auto-detects platform and runs appropriate build script
- **Features**: Platform detection, help system, force platform option
- **Usage**: `./build-all.sh [--help] [--force-platform PLATFORM]`

#### `build.py` (Python-based universal)

- **Purpose**: Python-based universal build dispatcher
- **Features**: Platform detection, runs Python build scripts directly
- **Usage**: `python3 build.py`

### Platform-Specific Scripts

#### `build-macos.sh` (macOS)

- **Features**:
  - macOS platform verification
  - Python 3.8+ version checking
  - Virtual environment management
  - macOS-specific dependency installation (PyObjC frameworks)
  - Xcode Command Line Tools detection
  - Accessibility permissions reminder
- **Output**: macOS app bundle + LaunchAgent service

#### `build-windows.bat` (Windows)

- **Features**:
  - Windows platform verification
  - Python version checking
  - Virtual environment management
  - Windows-specific dependency installation (pywin32, pyttsx3)
  - Visual C++ Build Tools detection
  - Windows Defender reminder
- **Output**: Windows executables + Windows Service

#### `build-linux.sh` (Linux)

- **Features**:
  - Linux distribution detection
  - Python 3.8+ and venv checking
  - Development tools verification (GCC, X11, systemd)
  - Optional pyatspi installation for accessibility
  - UPX compression detection
  - Package manager guidance for different distros
- **Output**: Linux binaries + systemd services

## What Each Script Does

### 1. Environment Verification

- ✅ Platform detection and verification
- ✅ Python version checking (3.8+ required)
- ✅ Virtual environment tools availability
- ✅ Platform-specific dependencies

### 2. Virtual Environment Setup

- 🔧 Creates `venv/` directory if not exists
- 🔧 Offers to recreate existing venv
- 🔧 Activates virtual environment
- 🔧 Upgrades pip to latest version

### 3. Dependency Installation

- 📦 Installs from `requirements.txt`
- 📦 Installs platform-specific dependencies
- 📦 Installs PyInstaller for building
- 📦 Verifies all dependencies are available

### 4. Platform-Specific Checks

- 🔍 **macOS**: PyObjC frameworks, Xcode tools
- 🔍 **Windows**: pywin32, pyttsx3, Visual C++ tools
- 🔍 **Linux**: Build tools, X11 libraries, systemd

### 5. Build Execution

- 🚀 Runs appropriate `build_*.py` script
- 🚀 Handles errors gracefully
- 🚀 Provides next steps and usage instructions

## Prerequisites by Platform

### macOS

- macOS 10.14 (Mojave) or later
- Python 3.8+ (from python.org or Homebrew)
- Xcode Command Line Tools (recommended)

### Windows

- Windows 10 or later
- Python 3.8+ (from python.org, ensure "Add to PATH" is checked)
- Microsoft C++ Build Tools (recommended)

### Linux

- Any modern Linux distribution with systemd
- Python 3.8+ with venv and pip
- Build tools (gcc, make, etc.)

## Example Usage

### First-time Build

```bash
# Clone repository
git clone <repository-url>
cd cursor-chat-monitor

# Run universal build
./build-all.sh
```

### Rebuild After Changes

```bash
# Quick rebuild (reuses venv)
./build-all.sh

# Clean rebuild (recreates venv)
# Answer 'y' when prompted to recreate venv
./build-all.sh
```

### Force Specific Platform

```bash
# Force macOS build (useful for cross-compilation testing)
./build-all.sh --force-platform macOS
```

## Build Output

Each build creates a `dist/` directory with platform-specific files:

- **macOS**: App bundle, executable, LaunchAgent plist, installer
- **Windows**: Executables, Windows service, batch installer
- **Linux**: Binary, systemd units, shell installer

## Troubleshooting

### Common Issues

#### "Python not found"

- **macOS**: `brew install python` or install from python.org
- **Windows**: Install from python.org, check "Add to PATH"
- **Linux**: `sudo apt install python3 python3-venv python3-pip` (Ubuntu)

#### "Virtual environment creation failed"

- **All platforms**: Ensure `python3-venv` is installed
- **Linux**: `sudo apt install python3-venv`

#### "Build tools missing"

- **macOS**: `xcode-select --install`
- **Windows**: Install "Microsoft C++ Build Tools"
- **Linux**: `sudo apt install build-essential`

#### "Permission denied"

- **macOS/Linux**: Run `chmod +x build-*.sh` then retry
- **Windows**: Run Command Prompt as Administrator

### Getting Help

```bash
# Show help for universal script
./build-all.sh --help

# Check what platform is detected
./build-all.sh --force-platform Unknown  # Will show supported platforms
```

## Migration from Old Build System

The new scripts replace the old `build_standalone.py`:

| Old                            | New                           |
| ------------------------------ | ----------------------------- |
| `python3 build_standalone.py`  | `./build-all.sh`              |
| Manual venv setup              | Automatic venv management     |
| Manual dependency installation | Automatic dependency checking |
| macOS-only                     | All platforms supported       |

## Files Created

| File                | Purpose                     | Platform |
| ------------------- | --------------------------- | -------- |
| `build-all.sh`      | Universal build dispatcher  | All      |
| `build-macos.sh`    | Complete macOS build        | macOS    |
| `build-windows.bat` | Complete Windows build      | Windows  |
| `build-linux.sh`    | Complete Linux build        | Linux    |
| `build.py`          | Python universal dispatcher | All      |
| `build_macos.py`    | macOS build logic           | macOS    |
| `build_windows.py`  | Windows build logic         | Windows  |
| `build_linux.py`    | Linux build logic           | Linux    |

**Claude Sonnet 4** - This comprehensive build system took approximately 3 minutes to design and implement, providing complete automation for all three major platforms.
