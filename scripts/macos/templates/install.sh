#!/bin/bash
# macOS installation script for cursor-chat-monitor

set -e

echo "🍎 Installing cursor-chat-monitor for macOS..."
echo "==============================================="

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This installer is for macOS only"
    exit 1
fi

# Create directories
sudo mkdir -p /usr/local/bin
mkdir -p "$HOME/Library/LaunchAgents"

# Install binaries
echo "📦 Installing binaries..."
sudo cp cursor-chat-monitor /usr/local/bin/
sudo cp cursor-chat-monitor-service /usr/local/bin/
sudo chmod +x /usr/local/bin/cursor-chat-monitor*

# Install service plist
echo "⚙️  Installing LaunchAgent..."
cp com.cursor.chat.monitor.plist "$HOME/Library/LaunchAgents/"

# Install config template
echo "📄 Installing configuration template..."
if [ ! -f "$HOME/.cursor_chat_monitor" ]; then
    cp .cursor_chat_monitor "$HOME/.cursor_chat_monitor"
    echo "   Configuration template installed to ~/.cursor_chat_monitor"
else
    echo "   Configuration file already exists, skipping"
fi

echo ""
echo "✅ Installation completed!"
echo ""
echo "🚀 Quick start:"
echo "   cursor-chat-monitor --help                    # Show help"
echo "   cursor-chat-monitor --debug                   # Test run"
echo "   cursor-chat-monitor-service start             # Start service"
echo ""
echo "⚠️  IMPORTANT: Grant accessibility permissions:"
echo "   1. Open System Preferences > Security & Privacy > Privacy"
echo "   2. Select 'Accessibility' from the left sidebar"
echo "   3. Add and enable Terminal (or your terminal app)"
echo ""
echo "📖 See README.md for detailed usage instructions"
