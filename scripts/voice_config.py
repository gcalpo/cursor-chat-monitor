#!/usr/bin/env python3
"""
Voice configuration utility for cursor chat monitor
Lists available voices and helps configure voice settings
"""
import sys
import os
import json
import subprocess
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import list_available_voices, get_platform_name, PLATFORM_VOICE_CONFIGS, get_system_voices, get_platform_voice_config


def list_system_voices():
    """List voices available on the current system"""
    platform = get_platform_name()
    
    print(f"🔍 Detecting voices for {platform.upper()}...")
    
    voices = get_system_voices()
    
    if voices:
        print(f"✅ Found {len(voices)} system voices:")
        for i, voice in enumerate(voices[:20], 1):  # Show first 20
            print(f"   {i:2d}. {voice}")
        if len(voices) > 20:
            print(f"   ... and {len(voices) - 20} more")
    else:
        print("❌ No system voices found")
    
    return voices


def create_config_file(voice_name=None, speech_rate=None, use_platform_defaults=False):
    """Create a config file with specified voice settings"""
    platform = get_platform_name()
    config_path = Path.home() / ".cursor_chat_monitor"
    
    # Get default config
    from core.config import get_default_config
    config = get_default_config()
    
    # Update voice settings based on parameters
    if use_platform_defaults:
        config["VOICE_NAME"] = "PLATFORM_DEFAULT"
        config["SPEECH_RATE"] = "PLATFORM_DEFAULT"
        print(f"🎤 Using platform-specific defaults for {platform.upper()}")
    else:
        if voice_name:
            config["VOICE_NAME"] = voice_name
        if speech_rate:
            config["SPEECH_RATE"] = speech_rate
    
    # Write config file
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"✅ Configuration saved to: {config_path}")
        
        # Show what will be used
        if config["VOICE_NAME"] == "PLATFORM_DEFAULT":
            platform_config = get_platform_voice_config()
            print(f"   Voice: {platform_config['default_voice']} (platform default)")
            print(f"   Speech Rate: {platform_config['default_speech_rate']} WPM (platform default)")
        else:
            print(f"   Voice: {config['VOICE_NAME']}")
            print(f"   Speech Rate: {config['SPEECH_RATE']} WPM")
            
    except Exception as e:
        print(f"❌ Error saving config: {e}")


def test_voice(voice_name=None, speech_rate=None):
    """Test the voice configuration"""
    platform = get_platform_name()
    
    # Use defaults if not specified
    if not voice_name:
        voice_name = PLATFORM_VOICE_CONFIGS[platform]["default_voice"]
    if not speech_rate:
        speech_rate = PLATFORM_VOICE_CONFIGS[platform]["default_speech_rate"]
    
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
            subprocess.run([
                'say', 
                '-v', voice_name,
                '-r', str(speech_rate),
                test_message
            ], check=True)
        elif platform == "linux":
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


def show_platform_info():
    """Show detailed platform voice information"""
    platform = get_platform_name()
    platform_config = get_platform_voice_config()
    
    print(f"🖥️  Platform: {platform.upper()}")
    print(f"🎤 Default Voice: {platform_config['default_voice']}")
    print(f"🎤 Default Speech Rate: {platform_config['default_speech_rate']} WPM")
    print(f"🎤 Speech Rate Range: {platform_config['speech_rate_range']}")
    print(f"🎤 Speech Rate Presets: {platform_config['speech_rate_presets']}")
    
    # Show current config if it exists
    config_path = Path.home() / ".cursor_chat_monitor"
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                current_config = json.load(f)
            print(f"\n📁 Current Configuration:")
            print(f"   Voice: {current_config.get('VOICE_NAME', 'Not set')}")
            print(f"   Speech Rate: {current_config.get('SPEECH_RATE', 'Not set')}")
        except Exception as e:
            print(f"   Error reading config: {e}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🎤 Cursor Chat Monitor - Voice Configuration Utility")
        print()
        print("Usage:")
        print("  python voice_config.py list                    - List available voices")
        print("  python voice_config.py system                  - List system voices")
        print("  python voice_config.py test [voice] [rate]     - Test voice configuration")
        print("  python voice_config.py config [voice] [rate]   - Create config file")
        print("  python voice_config.py platform                - Show platform info")
        print("  python voice_config.py default                 - Create config with platform defaults")
        print()
        print("Examples:")
        print("  python voice_config.py list")
        print("  python voice_config.py system")
        print("  python voice_config.py test 'Microsoft David Desktop' 175")
        print("  python voice_config.py config 'Daniel' 200")
        print("  python voice_config.py default                 # Use platform defaults")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_available_voices()
    elif command == "system":
        list_system_voices()
    elif command == "platform":
        show_platform_info()
    elif command == "test":
        voice_name = sys.argv[2] if len(sys.argv) > 2 else None
        speech_rate = int(sys.argv[3]) if len(sys.argv) > 3 else None
        test_voice(voice_name, speech_rate)
    elif command == "config":
        voice_name = sys.argv[2] if len(sys.argv) > 2 else None
        speech_rate = int(sys.argv[3]) if len(sys.argv) > 3 else None
        create_config_file(voice_name, speech_rate)
    elif command == "default":
        create_config_file(use_platform_defaults=True)
    else:
        print(f"❌ Unknown command: {command}")
        print("Use 'list', 'system', 'test', 'config', 'platform', or 'default'")


if __name__ == "__main__":
    main() 