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
import signal
import os
from core.config import load_config, DEFAULT_CONFIG, validate_config
from core.monitor import CrossPlatformMonitor
from platforms import get_current_platform

# Global monitor instance for signal handling
monitor_instance = None

def is_running_from_source():
    """
    Detect if we're running from source code vs compiled executable.
    
    Returns:
        bool: True if running from source (.py file), False if compiled executable
    """
    # Check if we're frozen (compiled with PyInstaller, cx_Freeze, etc.)
    if getattr(sys, 'frozen', False):
        return False
    
    # Check if __file__ exists and points to a .py file
    if hasattr(sys.modules[__name__], '__file__'):
        script_path = sys.modules[__name__].__file__
        if script_path and script_path.endswith('.py'):
            return True
    
    # Check if sys.executable points to a Python interpreter
    if sys.executable:
        exe_name = os.path.basename(sys.executable).lower()
        if exe_name.startswith('python') or exe_name.startswith('python3'):
            return True
    
    # Default to False (assume compiled) for safety
    return False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global monitor_instance
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    if monitor_instance:
        monitor_instance.stop_monitoring()
    sys.exit(0)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGHUP'):
        signal.signal(signal.SIGHUP, signal_handler)

def main():
    """Main entry point for the cursor chat monitor"""
    global monitor_instance
    
    parser = argparse.ArgumentParser(
        description="Monitor Cursor IDE for multiple target texts (Cross-Platform)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Platform Support:
  Current Platform: {get_current_platform()}
  
  macOS:    Uses Accessibility APIs (requires permissions)
  Windows:  Uses Win32 APIs and pyttsx3
  Linux:    Uses AT-SPI and espeak/festival

Voice Configuration:
  --voices                    List all available voices for current platform (default highlighted)
  --voice-info               Show detailed platform voice information
  --test-voice [VOICE_NAME]   Test voice configuration

Examples:
  python3 cursor_chat_monitor.py
  python3 cursor_chat_monitor.py --interval-ms=2000 --debug
  python3 cursor_chat_monitor.py --config=my_config.json
  python3 cursor_chat_monitor.py --daemon
  python3 cursor_chat_monitor.py --voices
  python3 cursor_chat_monitor.py --voice-info
  python3 cursor_chat_monitor.py --test-voice "Microsoft David Desktop"
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
        "--no-debug", 
        action="store_true", 
        help="Explicitly disable debug mode (overrides auto-detection)"
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
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (background service)"
    )
    parser.add_argument(
        "--pid-file",
        type=str,
        help="Path to PID file for daemon mode (default: ~/.cursor-chat-monitor.pid)"
    )
    parser.add_argument(
        "--voices",
        action="store_true",
        help="List all available voices for current platform (default highlighted) and exit"
    )
    parser.add_argument(
        "--voice-info",
        action="store_true",
        help="Show detailed platform voice information and exit"
    )
    parser.add_argument(
        "--test-voice",
        nargs='?',
        const='',
        metavar='VOICE_NAME',
        help="Test voice configuration (optional: specify voice name)"
    )
    
    args = parser.parse_args()
    
    # Show platform info if requested
    if args.platform_info:
        print(f"🖥️  Current Platform: {get_current_platform()}")
        print(f"🐍 Python Version: {sys.version}")
        print(f"📁 Python Executable: {sys.executable}")
        
        # Show execution mode
        from_source = is_running_from_source()
        print(f"🚀 Execution Mode: {'Source Code' if from_source else 'Compiled Executable'}")
        
        # Try to get platform implementations to show capabilities
        try:
            from platforms import get_platform_implementations
            app_accessor, alert_system = get_platform_implementations()
            print(f"✅ Platform implementation: {app_accessor.get_platform_name()}")
            print(f"🔊 Alert system: {alert_system.get_platform_name()}")
        except Exception as e:
            print(f"❌ Platform implementation error: {e}")
        
        return 0
    
    # Handle voice-related commands
    if args.voices:
        from core.config import list_available_voices, get_platform_name
        print(f"🎤 Voice Configuration for {get_platform_name().upper()}")
        print("=" * 50)
        list_available_voices()
        print("\n💡 Use --test-voice to test a specific voice")
        print("💡 Use --voice-info for detailed platform information")
        return 0
    
    if args.voice_info:
        from core.config import show_platform_voice_info
        show_platform_voice_info()
        return 0
    
    if args.test_voice is not None:
        from core.config import get_platform_name, PLATFORM_VOICE_CONFIGS
        platform = get_platform_name()
        voice_config = PLATFORM_VOICE_CONFIGS.get(platform, {})
        
        # Use provided voice or default
        voice_name = args.test_voice if args.test_voice else voice_config.get("default_voice", "Unknown")
        speech_rate = voice_config.get("default_speech_rate", 175)
        
        test_message = "This is a test of the voice configuration for cursor chat monitor."
        print(f"🎤 Testing voice: {voice_name} at {speech_rate} WPM")
        print(f"   Message: '{test_message}'")
        
        try:
            if platform == "windows":
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('voice', voice_name)
                engine.setProperty('rate', speech_rate)
                engine.say(test_message)
                engine.runAndWait()
            elif platform == "macos":
                import subprocess
                subprocess.run([
                    'say', 
                    '-v', voice_name,
                    '-r', str(speech_rate),
                    test_message
                ], check=True)
            elif platform == "linux":
                import subprocess
                # Convert WPM to espeak rate (approximate)
                espeak_rate = int(speech_rate * 1.2)
                subprocess.run([
                    'espeak',
                    '-s', str(espeak_rate),
                    test_message
                ], check=True)
            
            print("✅ Voice test completed successfully")
        except Exception as e:
            print(f"❌ Voice test failed: {e}")
            print("💡 Try running: python scripts/voice_config.py system")
        
        return 0
    
    # Set up signal handlers for graceful shutdown
    setup_signal_handlers()
    
    # Handle daemon mode
    if args.daemon:
        pid_file = args.pid_file or os.path.expanduser("~/.cursor-chat-monitor.pid")
        
        # Check if already running
        if os.path.exists(pid_file):
            try:
                with open(pid_file, 'r') as f:
                    existing_pid = int(f.read().strip())
                
                # Check if process is still running
                try:
                    os.kill(existing_pid, 0)  # Signal 0 just checks if process exists
                    print(f"❌ Already running with PID {existing_pid}")
                    return 1
                except (OSError, ProcessLookupError):
                    # Process doesn't exist, remove stale PID file
                    os.remove(pid_file)
            except (ValueError, IOError):
                # Invalid PID file, remove it
                try:
                    os.remove(pid_file)
                except OSError:
                    pass
        
        # Write our PID
        try:
            with open(pid_file, 'w') as f:
                f.write(str(os.getpid()))
        except IOError as e:
            print(f"❌ Cannot create PID file {pid_file}: {e}")
            return 1
        
        # Set up cleanup on exit
        def cleanup_pid_file():
            try:
                if os.path.exists(pid_file):
                    os.remove(pid_file)
            except OSError:
                pass
        
        import atexit
        atexit.register(cleanup_pid_file)
    
    # Load configuration
    config = load_config(args.config)
    
    # Validate configuration
    if not validate_config(config):
        print("❌ Configuration validation failed")
        return 1
    
    # Determine debug mode based on execution context and arguments
    debug_mode = None
    if args.no_debug:
        # Explicitly disabled
        debug_mode = False
        debug_reason = "explicitly disabled with --no-debug"
    elif args.debug:
        # Explicitly enabled
        debug_mode = True
        debug_reason = "explicitly enabled with --debug"
    else:
        # Auto-detect based on execution context
        from_source = is_running_from_source()
        debug_mode = from_source
        debug_reason = f"auto-detected ({'source code' if from_source else 'compiled executable'})"
    
    # Override config default if we determined debug mode
    if debug_mode is not None:
        config["DEFAULT_DEBUG_MODE"] = debug_mode
    
    # Show debug mode status (only if not in daemon mode)
    if not args.daemon:
        print(f"🐛 Debug mode: {'ON' if debug_mode else 'OFF'} ({debug_reason})")
        if debug_mode:
            print("   💡 Use --no-debug to disable debug mode")
        else:
            print("   💡 Use --debug to enable debug mode")
    
    # Create monitor
    try:
        monitor_instance = CrossPlatformMonitor(
            config=config,
            interval_ms=args.interval_ms,
            debug=debug_mode,
            daemon_mode=args.daemon
        )
    except Exception as e:
        print(f"❌ Failed to create monitor: {e}")
        return 1
    
    # Check prerequisites
    if not monitor_instance.check_prerequisites():
        print("❌ Prerequisites not met")
        return 1
    
    # Run monitoring
    try:
        monitor_instance.run_monitoring()
    except KeyboardInterrupt:
        if not args.daemon:
            print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Monitor error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 