#!/bin/bash
# Universal Build Script for cursor-chat-monitor
# Detects platform and runs appropriate build script

echo "🌍 Universal Build Script for cursor-chat-monitor"
echo "================================================="

# Function to detect platform
detect_platform() {
    case "$OSTYPE" in
        darwin*)
            echo "macOS"
            ;;
        linux-gnu*)
            echo "Linux"
            ;;
        msys* | cygwin* | win32*)
            echo "Windows"
            ;;
        *)
            echo "Unknown"
            ;;
    esac
}

# Function to show help
show_help() {
    echo "Universal build script for cursor-chat-monitor"
    echo ""
    echo "Usage:"
    echo "  ./build-all.sh           # Auto-detect platform and build"
    echo "  ./build-all.sh --help    # Show this help"
    echo "  ./build-all.sh --force-platform PLATFORM  # Force specific platform"
    echo ""
    echo "Supported platforms:"
    echo "  macOS     - Run build-macos.sh"
    echo "  Linux     - Run build-linux.sh"
    echo "  Windows   - Run build-windows.bat (requires bash environment)"
    echo ""
    echo "Platform-specific scripts:"
    echo "  ./build-macos.sh         # macOS only"
    echo "  ./build-linux.sh         # Linux only"
    echo "  build-windows.bat        # Windows only (run in cmd)"
}

# Parse command line arguments
FORCE_PLATFORM=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --force-platform)
            FORCE_PLATFORM="$2"
            shift 2
            ;;
        *)
            echo "❌ Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Detect platform
if [ -n "$FORCE_PLATFORM" ]; then
    PLATFORM="$FORCE_PLATFORM"
    echo "🔧 Platform forced to: $PLATFORM"
else
    PLATFORM=$(detect_platform)
    echo "🔍 Detected platform: $PLATFORM"
fi

# Run appropriate build script
case "$PLATFORM" in
    macOS)
        if [ -f "build-macos.sh" ]; then
            echo "🚀 Running macOS build script..."
            chmod +x build-macos.sh
            ./build-macos.sh
        else
            echo "❌ build-macos.sh not found"
            exit 1
        fi
        ;;
    Linux)
        if [ -f "build-linux.sh" ]; then
            echo "🚀 Running Linux build script..."
            chmod +x build-linux.sh
            ./build-linux.sh
        else
            echo "❌ build-linux.sh not found"
            exit 1
        fi
        ;;
    Windows)
        if [ -f "build-windows.bat" ]; then
            echo "🚀 Running Windows build script..."
            echo "⚠️  Note: Running Windows batch file in bash environment"
            echo "💡 For best results, run build-windows.bat directly in cmd.exe"
            # Try to run the batch file through cmd if available
            if command -v cmd.exe &> /dev/null; then
                cmd.exe /c build-windows.bat
            elif command -v cmd &> /dev/null; then
                cmd /c build-windows.bat
            else
                echo "❌ Cannot run Windows batch file in this environment"
                echo "💡 Please run build-windows.bat directly in Windows Command Prompt"
                exit 1
            fi
        else
            echo "❌ build-windows.bat not found"
            exit 1
        fi
        ;;
    Unknown)
        echo "❌ Unsupported platform: $OSTYPE"
        echo ""
        echo "Supported platforms:"
        echo "  - macOS (darwin)"
        echo "  - Linux (linux-gnu)"
        echo "  - Windows (msys/cygwin/win32)"
        echo ""
        echo "💡 You can force a platform with --force-platform:"
        echo "   ./build-all.sh --force-platform macOS"
        echo "   ./build-all.sh --force-platform Linux"
        echo "   ./build-all.sh --force-platform Windows"
        exit 1
        ;;
    *)
        echo "❌ Invalid platform: $PLATFORM"
        echo "💡 Valid platforms: macOS, Linux, Windows"
        exit 1
        ;;
esac

echo ""
echo "🎉 Universal build completed!"
echo "Check the messages above for platform-specific results." 