"""
Configuration management for cursor chat monitor
"""
import json
import os
import sys
from typing import Dict, Any, Optional, List


# Platform-specific voice configurations
PLATFORM_VOICE_CONFIGS = {
    "windows": {
        "default_voice": "Microsoft David Desktop",
        "default_speech_rate": 175,
        "speech_rate_range": (100, 300),
        "speech_rate_presets": [150, 175, 200, 225, 250]
    },
    "macos": {
        "default_voice": "Daniel",
        "default_speech_rate": 175,
        "speech_rate_range": (100, 300),
        "speech_rate_presets": [150, 175, 200, 225, 250]
    },
    "linux": {
        "default_voice": "default",
        "default_speech_rate": 175,
        "speech_rate_range": (100, 300),
        "speech_rate_presets": [150, 175, 200, 225, 250]
    }
}


def get_platform_name() -> str:
    """Get current platform name for voice configuration"""
    if sys.platform == "win32":
        return "windows"
    elif sys.platform == "darwin":
        return "macos"
    elif sys.platform.startswith("linux"):
        return "linux"
    else:
        return "unknown"


def get_platform_voice_config() -> Dict[str, Any]:
    """Get voice configuration for current platform"""
    platform = get_platform_name()
    return PLATFORM_VOICE_CONFIGS.get(platform, PLATFORM_VOICE_CONFIGS["windows"])


# Default configuration - can be overridden by external config file
def get_default_config() -> Dict[str, Any]:
    """Get default configuration with platform-specific voice settings"""
    platform_voice_config = get_platform_voice_config()
    platform = get_platform_name()
    
    # Set platform-specific defaults for window title announcement mode
    if platform == "windows":
        window_title_announce_mode = "next-to-last"
    else:
        window_title_announce_mode = "last"
    
    return {
        # Texts to monitor for (case-insensitive)
        "AWAITING_USER_ACTION_TEXTS": [
            "resume the conversation",
            "Connection failed",
            "trouble connecting to the model provider",
            "File is being edited by another chat",
        ],
        
        # Texts to monitor for completion (case-insensitive, special handling: alert when count goes from >0 to 0)
        "GENERATING_TEXTS": [
            "generating"
        ],
        
        # Default scan interval in milliseconds
        "DEFAULT_SCAN_INTERVAL_MS": 1500,
        
        # Maximum depth to search in accessibility tree
        "MAX_SEARCH_DEPTH": 50,
        
        # Maximum depth to search within chat sidebar (DEPRECATED - no longer used)
        # Sidebar searches now traverse the entire tree without depth limits
        "SIDEBAR_DEPTH_LIMIT": 20,
        
        # Voice alert settings (platform-specific defaults)
        "VOICE_NAME": platform_voice_config["default_voice"],
        "SPEECH_RATE": platform_voice_config["default_speech_rate"],
        
        # Platform-specific voice configuration
        "PLATFORM_VOICE_CONFIG": platform_voice_config,
        
        # Window title announcement mode: 'full', 'first', 'last', or 'next-to-last'
        "WINDOW_TITLE_ANNOUNCE_MODE": window_title_announce_mode,  # Options: 'full', 'first', 'last', 'next-to-last'
        
        # Replace periods with spaces in announcement (default: True)
        "REPLACE_PERIODS_IN_ANNOUNCEMENT": True,
        
        # Announce when generating starts (count goes from 0 to >0)
        "ANNOUNCE_GENERATING_STARTED": True,
        
        # Debounce time for 'generating started' alert (seconds). 0 disables debouncing.
        "GENERATING_STARTED_DEBOUNCE_SECONDS": 10,
        
        # Debounce time for 'generating complete' alert (seconds). 
        # If generation resumes within this time, completion alert is suppressed.
        # This prevents multiple alerts during long thinking tasks with subtasks.
        "GENERATING_COMPLETE_DEBOUNCE_SECONDS": 5,
        
        # Log file names
        "MONITOR_LOG_FILE": "cursor_resume_monitor.log",
        
        # Enable logging to file (default: False)
        "LOG_TO_FILE": False,
        
        # Debug mode default
        "DEFAULT_DEBUG_MODE": False
    }


# Legacy support - keep the old DEFAULT_CONFIG for backward compatibility
DEFAULT_CONFIG = get_default_config()


def load_config(config_file_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from file if provided, otherwise look for ~/.cursor_chat_monitor, or use defaults"""
    config = get_default_config()
    
    # If no config file specified, look for default config in user's home directory
    if config_file_path is None:
        default_config_path = os.path.expanduser("~/.cursor_chat_monitor")
        if os.path.exists(default_config_path):
            config_file_path = default_config_path
            print(f"📁 Found default config file: {config_file_path}")
    
    if config_file_path:
        if not os.path.exists(config_file_path):
            print(f"⚠️  Config file not found: {config_file_path}")
            print("📝 Using default configuration")
            return config
        
        try:
            with open(config_file_path, 'r') as f:
                external_config = json.load(f)
            
            # Merge external config with defaults
            config.update(external_config)
            print(f"✅ Configuration loaded from: {config_file_path}")
            
            # Handle platform-specific voice defaults
            platform_voice_config = get_platform_voice_config()
            
            # Replace PLATFORM_DEFAULT placeholders with actual platform defaults
            if config.get("VOICE_NAME") == "PLATFORM_DEFAULT":
                config["VOICE_NAME"] = platform_voice_config["default_voice"]
                print(f"🎤 Using platform default voice: {config['VOICE_NAME']}")
            
            if config.get("SPEECH_RATE") == "PLATFORM_DEFAULT":
                config["SPEECH_RATE"] = platform_voice_config["default_speech_rate"]
                print(f"🎤 Using platform default speech rate: {config['SPEECH_RATE']} WPM")
            
            # Validate critical configuration values
            if not isinstance(config.get("AWAITING_USER_ACTION_TEXTS"), list):
                print("⚠️  AWAITING_USER_ACTION_TEXTS must be a list, using default")
                config["AWAITING_USER_ACTION_TEXTS"] = get_default_config()["AWAITING_USER_ACTION_TEXTS"]
            
            if not isinstance(config.get("GENERATING_TEXTS"), list):
                print("⚠️  GENERATING_TEXTS must be a list, using default")
                config["GENERATING_TEXTS"] = get_default_config()["GENERATING_TEXTS"]
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in config file: {e}")
            print("📝 Using default configuration")
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            print("📝 Using default configuration")
    else:
        print("📝 No config file found, using default configuration")
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration values"""
    required_keys = [
        "AWAITING_USER_ACTION_TEXTS",
        "GENERATING_TEXTS",
        "DEFAULT_SCAN_INTERVAL_MS"
    ]
    
    for key in required_keys:
        if key not in config:
            print(f"❌ Missing required config key: {key}")
            return False
    
    # Type validations
    if not isinstance(config["AWAITING_USER_ACTION_TEXTS"], list):
        print("❌ AWAITING_USER_ACTION_TEXTS must be a list")
        return False
    
    if not isinstance(config["GENERATING_TEXTS"], list):
        print("❌ GENERATING_TEXTS must be a list")
        return False
    
    if not isinstance(config["DEFAULT_SCAN_INTERVAL_MS"], (int, float)):
        print("❌ DEFAULT_SCAN_INTERVAL_MS must be a number")
        return False
    
    return True


def list_available_voices() -> Dict[str, Any]:
    """List all available voices for the current platform (default highlighted)"""
    platform = get_platform_name()
    voice_config = PLATFORM_VOICE_CONFIGS.get(platform, {})
    
    print(f"🎤 Available voices for {platform.upper()}:")
    print(f"   Default voice: {voice_config.get('default_voice', 'Unknown')}")
    print(f"   Default speech rate: {voice_config.get('default_speech_rate', 'Unknown')} WPM")
    print(f"   Speech rate range: {voice_config.get('speech_rate_range', 'Unknown')}")
    print(f"   Speech rate presets: {voice_config.get('speech_rate_presets', 'Unknown')}")
    
    # Dynamically detect system voices
    print("\n   System voices:")
    system_voices = get_system_voices()
    if system_voices:
        for i, voice in enumerate(system_voices, 1):
            if voice == voice_config.get('default_voice'):
                print(f"     {i:2d}. {voice} (default)")
            else:
                print(f"     {i:2d}. {voice}")
        print(f"\n✅ Found {len(system_voices)} system voices")
    else:
        print("     No system voices detected")
    
    return voice_config


def show_platform_voice_info() -> Dict[str, Any]:
    """Show detailed platform voice information"""
    platform = get_platform_name()
    platform_config = get_platform_voice_config()
    
    print(f"🖥️  Platform: {platform.upper()}")
    print(f"🎤 Default Voice: {platform_config['default_voice']}")
    print(f"🎤 Default Speech Rate: {platform_config['default_speech_rate']} WPM")
    print(f"🎤 Speech Rate Range: {platform_config['speech_rate_range']}")
    print(f"🎤 Speech Rate Presets: {platform_config['speech_rate_presets']}")
    
    # Show current config if it exists
    config_path = os.path.expanduser("~/.cursor_chat_monitor")
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                current_config = json.load(f)
            print(f"\n📁 Current Configuration:")
            voice_name = current_config.get('VOICE_NAME', 'Not set')
            speech_rate = current_config.get('SPEECH_RATE', 'Not set')
            
            if voice_name == "PLATFORM_DEFAULT":
                print(f"   Voice: {platform_config['default_voice']} (platform default)")
            else:
                print(f"   Voice: {voice_name}")
                
            if speech_rate == "PLATFORM_DEFAULT":
                print(f"   Speech Rate: {platform_config['default_speech_rate']} WPM (platform default)")
            else:
                print(f"   Speech Rate: {speech_rate} WPM")
        except Exception as e:
            print(f"   Error reading config: {e}")
    
    return platform_config


def get_system_voices() -> List[str]:
    """Get available voices from the current system"""
    platform = get_platform_name()
    
    if platform == "windows":
        return get_system_voices_windows()
    elif platform == "macos":
        return get_system_voices_macos()
    elif platform == "linux":
        return get_system_voices_linux()
    else:
        return []


def get_system_voices_windows() -> List[str]:
    """Get available voices from Windows SAPI"""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        return [voice.name for voice in voices]
    except Exception as e:
        print(f"⚠️  Could not get Windows voices: {e}")
        return []


def get_system_voices_macos() -> List[str]:
    """Get available voices from macOS"""
    try:
        import subprocess
        result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True)
        if result.returncode == 0:
            voices = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    # Parse voice name from output like "Daniel    en_US    # Hello, my name is Daniel"
                    parts = line.split()
                    if len(parts) >= 1:
                        voices.append(parts[0])
            return voices
    except Exception as e:
        print(f"⚠️  Could not get macOS voices: {e}")
    return []


def get_system_voices_linux() -> List[str]:
    """Get available voices from Linux espeak"""
    try:
        import subprocess
        result = subprocess.run(['espeak', '--voices'], capture_output=True, text=True)
        if result.returncode == 0:
            voices = []
            for line in result.stdout.split('\n'):
                if line.strip() and not line.startswith('Pty'):
                    # Parse voice name from output
                    parts = line.split()
                    if len(parts) >= 2:
                        voices.append(parts[1])
            return voices
    except Exception as e:
        print(f"⚠️  Could not get Linux voices: {e}")
    return [] 