#!/usr/bin/env python3
"""
Cursor Multi-Text Monitor (Cross-Platform)
Monitors all Cursor IDE windows for multiple target texts
and plays audio alert when count increases in any window.

Supports macOS, Windows, and Linux through platform abstraction.

Usage: python3 cursor_chat_monitor.py [--interval=5] [--config=config.json]
       
Config file priority:
1. --config argument (if provided)
2. ~/.cursor_chat_monitor (if exists)
3. Default configuration
"""

import sys
import argparse
from core.config import load_config, DEFAULT_CONFIG, validate_config
from core.monitor import CrossPlatformMonitor
from platforms import get_current_platform


def main():
    """Main entry point for the cursor chat monitor"""
    parser = argparse.ArgumentParser(
        description="Monitor Cursor IDE for multiple target texts (Cross-Platform)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Platform Support:
  Current Platform: {get_current_platform()}
  
  macOS:    Uses Accessibility APIs (requires permissions)
  Windows:  Uses Win32 APIs and pyttsx3
  Linux:    Uses AT-SPI and espeak/festival

Examples:
  python3 cursor_chat_monitor.py
  python3 cursor_chat_monitor.py --interval-ms=2000 --debug
  python3 cursor_chat_monitor.py --config=my_config.json
        """
    )
    
    parser.add_argument(
        "--interval-ms", 
        type=int, 
        help=f"Scan interval in milliseconds (default: from config or {DEFAULT_CONFIG['DEFAULT_SCAN_INTERVAL_MS']})"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode to show extracted text"
    )
    parser.add_argument(
        "--config", 
        type=str, 
        help="Path to JSON configuration file (default: looks for ~/.cursor_chat_monitor)"
    )
    parser.add_argument(
        "--platform-info",
        action="store_true",
        help="Show platform information and exit"
    )
    
    args = parser.parse_args()
    
    # Show platform info if requested
    if args.platform_info:
        print(f"🖥️  Current Platform: {get_current_platform()}")
        print(f"🐍 Python Version: {sys.version}")
        print(f"📁 Python Executable: {sys.executable}")
        
        # Try to get platform implementations to show capabilities
        try:
            from platforms import get_platform_implementations
            app_accessor, alert_system = get_platform_implementations()
            print(f"✅ Platform implementation: {app_accessor.get_platform_name()}")
            print(f"🔊 Alert system: {alert_system.get_platform_name()}")
        except Exception as e:
            print(f"❌ Platform implementation error: {e}")
        
        return 0
    
    # Load configuration
    config = load_config(args.config)
    
    # Validate configuration
    if not validate_config(config):
        print("❌ Configuration validation failed")
        return 1
    
    # Create monitor
    try:
        monitor = CrossPlatformMonitor(
            config=config,
            interval_ms=args.interval_ms,
            debug=args.debug
        )
    except Exception as e:
        print(f"❌ Failed to create monitor: {e}")
        return 1
    
    # Check prerequisites
    if not monitor.check_prerequisites():
        print("❌ Prerequisites not met")
        return 1
    
    # Run monitoring
    try:
        monitor.run_monitoring()
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Monitor error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 