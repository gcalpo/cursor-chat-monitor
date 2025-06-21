"""
Configuration management for cursor chat monitor
"""
import json
import os
from typing import Dict, Any


# Default configuration - can be overridden by external config file
DEFAULT_CONFIG = {
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
    "MAX_SEARCH_DEPTH": 30,
    
    # Voice alert settings
    "VOICE_NAME": "Daniel",
    "SPEECH_RATE": 175,        # Words per minute (100-300 recommended)
    
    # Window title announcement mode: 'full', 'first', or 'last'
    "WINDOW_TITLE_ANNOUNCE_MODE": "last",  # Options: 'full', 'first', 'last'
    
    # Replace periods with spaces in announcement (default: True)
    "REPLACE_PERIODS_IN_ANNOUNCEMENT": True,
    
    # Announce when generating starts (count goes from 0 to >0)
    "ANNOUNCE_GENERATING_STARTED": True,
    
    # Debounce time for 'generating started' alert (seconds). 0 disables debouncing.
    "GENERATING_STARTED_DEBOUNCE_SECONDS": 10,
    
    # Log file names
    "MONITOR_LOG_FILE": "cursor_resume_monitor.log",
    
    # Enable logging to file (default: False)
    "LOG_TO_FILE": False,
    
    # Debug mode default
    "DEFAULT_DEBUG_MODE": False
}


def load_config(config_file_path: str = None) -> Dict[str, Any]:
    """Load configuration from file if provided, otherwise look for ~/.cursor_chat_monitor, or use defaults"""
    config = DEFAULT_CONFIG.copy()
    
    # If no config file specified, look for default config in user's home directory
    if not config_file_path:
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
            
            # Validate critical configuration values
            if not isinstance(config.get("AWAITING_USER_ACTION_TEXTS"), list):
                print("⚠️  AWAITING_USER_ACTION_TEXTS must be a list, using default")
                config["AWAITING_USER_ACTION_TEXTS"] = DEFAULT_CONFIG["AWAITING_USER_ACTION_TEXTS"]
            
            if not isinstance(config.get("GENERATING_TEXTS"), list):
                print("⚠️  GENERATING_TEXTS must be a list, using default")
                config["GENERATING_TEXTS"] = DEFAULT_CONFIG["GENERATING_TEXTS"]
                
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