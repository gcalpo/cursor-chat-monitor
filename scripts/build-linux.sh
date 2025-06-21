#!/bin/bash
# Linux Build Script for cursor-chat-monitor
# Handles complete build process including virtual environment setup

set -e  # Exit on any error

echo "🐧 Linux Build Script for cursor-chat-monitor"
echo "=============================================="

# Check if we're on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script is for Linux only. Current OS: $OSTYPE"
    echo "💡 Use build-macos.sh for macOS or build-windows.bat for Windows"
    exit 1
fi

# Get Linux distribution info
echo "🔍 Detecting Linux distribution..."
if [ -f /etc/os-release ]; then
    source /etc/os-release
    echo "✅ Running on: $PRETTY_NAME"
else
    echo "✅ Running on: Linux (unknown distribution)"
fi

# Check Python version
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "💡 Install Python 3.8+ using your package manager:"
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-venv python3-pip"
    echo "   RHEL/CentOS/Fedora: sudo dnf install python3 python3-venv python3-pip"
    echo "   Arch: sudo pacman -S python python-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Check minimum Python version (3.8+)
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✅ Python version meets requirements (3.8+)"
else
    echo "❌ Python 3.8+ required, found $PYTHON_VERSION"
    echo "💡 Upgrade Python using your package manager"
    exit 1
fi

# Check for python3-venv
echo "🔍 Checking for python3-venv..."
if python3 -c "import venv" 2>/dev/null; then
    echo "✅ python3-venv available"
else
    echo "❌ python3-venv not available"
    echo "💡 Install python3-venv:"
    echo "   Ubuntu/Debian: sudo apt install python3-venv"
    echo "   RHEL/CentOS/Fedora: sudo dnf install python3-venv"
    echo "   Arch: python3-venv should be included with python"
    exit 1
fi

# Check for pip
echo "🔍 Checking for pip..."
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip not available"
    echo "💡 Install pip:"
    echo "   Ubuntu/Debian: sudo apt install python3-pip"
    echo "   RHEL/CentOS/Fedora: sudo dnf install python3-pip"
    echo "   Arch: sudo pacman -S python-pip"
    exit 1
else
    echo "✅ pip available"
fi

# Check for development tools (optional but recommended)
echo "🔍 Checking for development tools..."
if command -v gcc &> /dev/null; then
    echo "✅ GCC compiler available"
else
    echo "⚠️  GCC compiler not found"
    echo "💡 Install build tools if build fails:"
    echo "   Ubuntu/Debian: sudo apt install build-essential"
    echo "   RHEL/CentOS/Fedora: sudo dnf groupinstall 'Development Tools'"
    echo "   Arch: sudo pacman -S base-devel"
fi

# Check for system libraries that might be needed
echo "🔍 Checking for system dependencies..."

# Check for X11 development libraries (for potential GUI features)
if pkg-config --exists x11 2>/dev/null; then
    echo "✅ X11 libraries available"
else
    echo "⚠️  X11 development libraries not found"
    echo "💡 Install if build fails:"
    echo "   Ubuntu/Debian: sudo apt install libx11-dev"
    echo "   RHEL/CentOS/Fedora: sudo dnf install libX11-devel"
    echo "   Arch: sudo pacman -S libx11"
fi

# Check for systemd (for service integration)
if command -v systemctl &> /dev/null; then
    echo "✅ systemd available"
else
    echo "⚠️  systemd not found - service integration may be limited"
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📁 Virtual environment found"
    read -p "🔄 Remove existing venv and create fresh? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🧹 Removing existing virtual environment..."
        rm -rf venv
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Dependencies installed from requirements.txt"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Check Linux-specific dependencies
echo "🔍 Checking Linux-specific dependencies..."

# Check for psutil (should be in requirements.txt but verify)
python -c "import psutil" 2>/dev/null && echo "✅ psutil available" || {
    echo "❌ psutil missing"
    echo "📦 Installing psutil..."
    pip install psutil
}

# Check for pyatspi (optional)
python -c "import pyatspi" 2>/dev/null && echo "✅ pyatspi available (accessibility features enabled)" || {
    echo "⚠️  pyatspi not available - some accessibility features may be limited"
    echo "💡 Install with: pip install pyatspi"
    echo "💡 Or system package:"
    echo "   Ubuntu/Debian: sudo apt install python3-pyatspi"
    echo "   RHEL/CentOS/Fedora: sudo dnf install python3-pyatspi"
    read -p "🤔 Install pyatspi now? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install pyatspi || echo "⚠️  pyatspi installation failed, continuing without it"
    fi
}

# Install PyInstaller if not present
python -c "import PyInstaller" 2>/dev/null && echo "✅ PyInstaller available" || {
    echo "❌ PyInstaller missing"
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
}

# Check for UPX (optional, for smaller executables)
if command -v upx &> /dev/null; then
    echo "✅ UPX available (executable compression enabled)"
else
    echo "ℹ️  UPX not found (executable will be larger)"
    echo "💡 Install UPX for smaller executables:"
    echo "   Ubuntu/Debian: sudo apt install upx-ucl"
    echo "   RHEL/CentOS/Fedora: sudo dnf install upx"
    echo "   Arch: sudo pacman -S upx"
fi

# Run the Linux-specific build
echo ""
echo "🚀 Starting Linux build process..."
echo "================================="
python build_linux.py

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Linux build completed successfully!"
    echo "====================================="
    echo ""
    echo "📁 Build output in ./dist/:"
    if [ -d "dist" ]; then
        ls -la dist/
    fi
    echo ""
    echo "🚀 Next steps:"
    echo "   cd dist/"
    echo "   ./install.sh                    # Install on this system"
    echo "   ./cursor-chat-monitor --help    # Test the executable"
    echo ""
    echo "📖 See dist/README.md for detailed installation and usage instructions"
    echo ""
    echo "💡 Service management:"
    echo "   ./cursor-chat-monitor-service start    # Start service"
    echo "   ./cursor-chat-monitor-service enable   # Enable on boot"
else
    echo ""
    echo "❌ Build failed!"
    echo "💡 Check the error messages above for details"
    echo "💡 Common issues:"
    echo "   - Missing development tools: install build-essential (Ubuntu) or Development Tools (RHEL)"
    echo "   - Missing system libraries: check the warnings above"
    echo "   - Python version too old: upgrade to Python 3.8+"
    exit 1
fi 