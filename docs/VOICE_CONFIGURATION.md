# Voice Configuration Guide

The Cursor Chat Monitor supports platform-specific voice configurations with dynamic voice detection and customizable settings.

## Quick Start

### List Available Voices
```bash
# List configured voices for your platform
python cursor_chat_monitor.py --voices

# List all system voices (more comprehensive)
python scripts/voice_config.py system
```

### Test Voice Configuration
```bash
# Test with default voice
python cursor_chat_monitor.py --test-voice

# Test with specific voice
python cursor_chat_monitor.py --test-voice "Microsoft David Desktop"
```

### Configure Voice Settings
```bash
# Create config file with custom voice
python scripts/voice_config.py config "Daniel" 200

# Test voice before configuring
python scripts/voice_config.py test "Victoria" 175
```

## Platform-Specific Voice Options

### Windows
**Default Voice:** Microsoft David Desktop  
**Default Speech Rate:** 175 WPM

**Voice Detection:** Automatically detects available SAPI voices using pyttsx3

**Speech Rate Range:** 100-300 WPM  
**Preset Rates:** 150, 175, 200, 225, 250 WPM

### macOS
**Default Voice:** Daniel  
**Default Speech Rate:** 175 WPM

**Voice Detection:** Automatically detects available voices using the `say` command

**Speech Rate Range:** 100-300 WPM  
**Preset Rates:** 150, 175, 200, 225, 250 WPM

### Linux
**Default Voice:** default  
**Default Speech Rate:** 175 WPM

**Voice Detection:** Automatically detects available espeak voices

**Speech Rate Range:** 100-300 WPM  
**Preset Rates:** 150, 175, 200, 225, 250 WPM

## Configuration File

Voice settings are stored in your configuration file (`~/.cursor_chat_monitor` by default):

```json
{
    "VOICE_NAME": "Microsoft David Desktop",
    "SPEECH_RATE": 175,
    "PLATFORM_VOICE_CONFIG": {
        "default_voice": "Microsoft David Desktop",
        "default_speech_rate": 175,
        "speech_rate_range": [100, 300],
        "speech_rate_presets": [150, 175, 200, 225, 250]
    }
}
```

**Note:** The `available_voices` list has been removed. Voices are now detected dynamically from the system.

## Advanced Voice Configuration

### Voice Configuration Utility

The `scripts/voice_config.py` utility provides advanced voice management:

```bash
# List configured voices
python scripts/voice_config.py list

# List all system voices
python scripts/voice_config.py system

# Test voice configuration
python scripts/voice_config.py test "Victoria" 200

# Create configuration file
python scripts/voice_config.py config "Daniel" 175
```

### Discovering System Voices

Each platform has different methods for discovering available voices:

**Windows:**
```powershell
# List all SAPI voices
Add-Type -AssemblyName System.Speech
(New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }
```

**macOS:**
```bash
# List all available voices
say -v '?'
```

**Linux:**
```bash
# List espeak voices
espeak --voices

# List festival voices (if installed)
festival --tts --prolog '(voice.list)'
```

## Troubleshooting

### Voice Not Found
If a voice name is not found, try:
1. List system voices: `python scripts/voice_config.py system`
2. Use exact voice name from system list
3. Check platform-specific voice requirements

### Speech Rate Issues
- Windows: Rate is in words per minute (WPM)
- macOS: Rate is in words per minute (WPM)
- Linux: Rate is converted to espeak format (WPM × 1.2)

### Platform-Specific Issues

**Windows:**
- Ensure `pyttsx3` is installed: `pip install pyttsx3`
- Check Windows Speech settings in Control Panel

**macOS:**
- Ensure `say` command is available (built-in)
- Check System Preferences > Accessibility > Speech

**Linux:**
- Install espeak: `sudo apt-get install espeak` (Ubuntu/Debian)
- Install festival: `sudo apt-get install festival` (alternative)

## Custom Voice Presets

You can add custom voice presets by editing your configuration file:

```json
{
    "PLATFORM_VOICE_CONFIG": {
        "speech_rate_presets": [150, 175, 200, 225, 250, 300]
    }
}
```

## Integration with Monitor

The voice configuration is automatically used by the monitor:

```bash
# Run monitor with current voice settings
python cursor_chat_monitor.py

# Run with custom config file
python cursor_chat_monitor.py --config=my_voice_config.json
```

The monitor will use the `VOICE_NAME` and `SPEECH_RATE` settings from your configuration file for all audio alerts. 