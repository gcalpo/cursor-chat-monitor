#!/bin/bash
# macOS Build Script for cursor-chat-monitor
# Handles complete build process including virtual environment setup

set -e  # Exit on any error

echo "🍎 macOS Build Script for cursor-chat-monitor"
echo "=============================================="

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only. Current OS: $OSTYPE"
    echo "💡 Use build-linux.sh for Linux or build-windows.bat for Windows"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    echo "💡 Install Python 3.8+ from https://python.org or use homebrew: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Check minimum Python version (3.8+)
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "✅ Python version meets requirements (3.8+)"
else
    echo "❌ Python 3.8+ required, found $PYTHON_VERSION"
    exit 1
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

# Check macOS-specific dependencies
echo "🔍 Checking macOS-specific dependencies..."

# Check for PyObjC frameworks
python -c "import Cocoa" 2>/dev/null && echo "✅ PyObjC Cocoa framework available" || {
    echo "❌ PyObjC Cocoa framework missing"
    echo "📦 Installing PyObjC Cocoa framework..."
    pip install pyobjc-framework-Cocoa
}

python -c "import ApplicationServices" 2>/dev/null && echo "✅ PyObjC ApplicationServices framework available" || {
    echo "❌ PyObjC ApplicationServices framework missing"
    echo "📦 Installing PyObjC ApplicationServices framework..."
    pip install pyobjc-framework-ApplicationServices
}

# Install PyInstaller if not present
python -c "import PyInstaller" 2>/dev/null && echo "✅ PyInstaller available" || {
    echo "❌ PyInstaller missing"
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
}

# Check for Xcode Command Line Tools (needed for some native dependencies)
if ! xcode-select -p &> /dev/null; then
    echo "⚠️  Xcode Command Line Tools not found"
    echo "💡 Install with: xcode-select --install"
    read -p "🤔 Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run the macOS-specific build
echo ""
echo "🚀 Starting macOS build process..."
echo "================================="
python build_macos.py

# Check if build was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 macOS build completed successfully!"
    echo "======================================"
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
    echo "⚠️  Remember to grant accessibility permissions in System Preferences!"
else
    echo ""
    echo "❌ Build failed!"
    echo "💡 Check the error messages above for details"
    exit 1
fi 