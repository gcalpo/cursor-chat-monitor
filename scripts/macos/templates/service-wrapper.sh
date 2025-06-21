#!/bin/bash
# macOS service wrapper for cursor-chat-monitor

BINARY="/usr/local/bin/cursor-chat-monitor"
PLIST_FILE="$HOME/Library/LaunchAgents/com.cursor.chat.monitor.plist"
SERVICE_NAME="com.cursor.chat.monitor"

case "$1" in
    start)
        echo "Starting cursor-chat-monitor service..."
        if [ -f "$PLIST_FILE" ]; then
            launchctl load "$PLIST_FILE"
            echo "Service started"
        else
            echo "Service plist not found at $PLIST_FILE"
            echo "Run install.sh first"
            exit 1
        fi
        ;;
    stop)
        echo "Stopping cursor-chat-monitor service..."
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        echo "Service stopped"
        ;;
    restart)
        echo "Restarting cursor-chat-monitor service..."
        launchctl unload "$PLIST_FILE" 2>/dev/null || true
        sleep 1
        launchctl load "$PLIST_FILE"
        echo "Service restarted"
        ;;
    status)
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "Service is running"
            launchctl list | grep "$SERVICE_NAME"
        else
            echo "Service is not running"
        fi
        ;;
    console)
        echo "Running cursor-chat-monitor in console mode..."
        exec "$BINARY" --debug
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|console}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the background service"
        echo "  stop    - Stop the background service"
        echo "  restart - Restart the background service"
        echo "  status  - Show service status"
        echo "  console - Run in foreground with debug output"
        exit 1
        ;;
esac
