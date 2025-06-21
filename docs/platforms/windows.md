# Windows Setup Guide

Complete guide for installing and running Cursor Chat Monitor on Windows.

## 📋 System Requirements

- **Windows 10 or later (64-bit recommended)**
- **Cursor IDE installed and running**
- **PowerShell or Command Prompt access**

## 🚀 Quick Installation

### Option 1: Standalone Executable (Recommended)

```cmd
REM Download or build from source
git clone https://github.com/your-repo/cursor-chat-monitor
cd cursor-chat-monitor
python scripts/build_windows.py

REM Run installer as Administrator
cd dist
install.bat

REM Verify installation
cursor-chat-monitor.exe --platform-info
cursor-chat-monitor-service.bat status
```

### Option 2: Python Source Installation

```cmd
REM Clone repository
git clone https://github.com/your-repo/cursor-chat-monitor
cd cursor-chat-monitor

REM Create virtual environment
python -m venv venv
venv\Scripts\activate

REM Install dependencies
pip install -r requirements.txt

REM Test installation
python cursor_chat_monitor.py --platform-info
```

## 🔧 Prerequisites Setup

### Python Dependencies (Source Installation)

```cmd
REM Install Python 3.8+ from python.org
REM Verify installation
python --version
pip --version

REM Install Windows-specific packages
pip install pywin32 pyttsx3
```

### Visual C++ Redistributables

Some Windows systems may need Visual C++ Redistributables:

```cmd
REM Download from Microsoft or install via chocolatey
choco install vcredist2019

REM Or download directly from Microsoft
REM https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads
```

## 🎵 Audio Configuration

### Text-to-Speech Setup

Windows uses the built-in Speech API via pyttsx3:

```cmd
REM Test TTS system
powershell -c "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('Test')"

REM List available voices
powershell -c "Add-Type -AssemblyName System.Speech; [System.Speech.Synthesis.SpeechSynthesizer]::new().GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }"
```

### Voice Configuration

Create `%USERPROFILE%\.cursor_chat_monitor` with Windows-specific settings:

```json
{
  "VOICE_NAME": "Microsoft David Desktop",
  "SPEECH_RATE": 175,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "trouble connecting to the model provider"
  ],
  "GENERATING_TEXTS": ["generating"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500
}
```

**Common Windows Voice Names:**

- `Microsoft David Desktop` (Male)
- `Microsoft Zira Desktop` (Female)
- `Microsoft Mark Desktop` (Male)
- `Microsoft Hazel Desktop` (Female)

## 🔧 Service Management

### Windows Service Integration

The Windows version integrates with the Windows Service Control Manager for proper background service management.

**Service Installation:**

```cmd
REM Install Windows Service (run as Administrator)
cursor-chat-monitor-service.bat install

REM Service registration location
HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\CursorChatMonitor
```

### Service Commands

```cmd
REM Start service
cursor-chat-monitor-service.bat start

REM Stop service
cursor-chat-monitor-service.bat stop

REM Check service status
cursor-chat-monitor-service.bat status

REM Restart service
cursor-chat-monitor-service.bat restart

REM View service logs
cursor-chat-monitor-service.bat logs

REM Uninstall service
cursor-chat-monitor-service.bat uninstall

REM Run in console mode for debugging
cursor-chat-monitor-service.bat console
```

### Manual Service Management

```cmd
REM Using Windows Service Control (sc) command
sc start CursorChatMonitor
sc stop CursorChatMonitor
sc query CursorChatMonitor
sc delete CursorChatMonitor

REM Using PowerShell
powershell -c "Get-Service CursorChatMonitor"
powershell -c "Start-Service CursorChatMonitor"
powershell -c "Stop-Service CursorChatMonitor"
```

## 🐛 Troubleshooting

### Common Issues

#### Service Won't Start

```cmd
REM Check service status
sc query CursorChatMonitor
sc queryex CursorChatMonitor

REM Check service configuration
sc qc CursorChatMonitor

REM View Windows Event Logs
eventvwr.msc
REM Navigate to: Windows Logs -> Application

REM Check specific service events
wevtutil qe Application /q:"*[System[Provider[@Name='CursorChatMonitor']]]" /f:text /rd:true /c:10
```

#### Permission Issues

```cmd
REM Run Command Prompt as Administrator
REM Right-click Command Prompt -> "Run as administrator"

REM Check if user has service installation privileges
net localgroup administrators

REM Grant user "Log on as a service" right (if needed)
secpol.msc
REM Navigate to: Security Policy -> Local Policies -> User Rights Assignment
```

#### Cursor Not Detected

```cmd
REM Check if Cursor is running
tasklist | findstr /i cursor

REM Get detailed process information
wmic process where "name like '%cursor%'" get processid,name,commandline

REM Check window titles
powershell -c "Get-Process | Where-Object {$_.MainWindowTitle -like '*cursor*'} | Select-Object Name,MainWindowTitle"
```

#### TTS Not Working

```cmd
REM Test TTS manually
powershell -c "$tts = New-Object -ComObject SAPI.SpVoice; $tts.Speak('Test message')"

REM Check audio devices
powershell -c "Get-WmiObject -Class Win32_SoundDevice | Select-Object Name,Status"

REM Test Windows Speech Platform
powershell -c "Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak('Hello Windows')"
```

### Diagnostic Commands

```cmd
REM Comprehensive system check
cursor-chat-monitor.exe --platform-info

REM Check Windows version
ver
systeminfo | findstr /B "OS Name OS Version"

REM Check .NET Framework version
powershell -c "Get-ItemProperty 'HKLM:SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\' -Name Release"

REM Verify Python environment (if using source)
where python
python --version

REM Check installed packages
pip list | findstr "pywin32\|pyttsx3"
```

### Log Analysis

```cmd
REM Service logs
type %USERPROFILE%\.cursor-chat-monitor-service.log
type %PROGRAMDATA%\CursorChatMonitor\logs\service.log

REM Windows Event Viewer
eventvwr.msc
REM Navigate to: Windows Logs -> Application -> Filter Current Log -> Source: CursorChatMonitor

REM PowerShell log analysis
powershell -c "Get-EventLog -LogName Application -Source 'CursorChatMonitor' -Newest 10"

REM Search for errors
findstr /i "error" %USERPROFILE%\.cursor-chat-monitor-service.log
findstr /i "failed" %USERPROFILE%\.cursor-chat-monitor-service.log
findstr /i "exception" %USERPROFILE%\.cursor-chat-monitor-service.log
```

## 🔧 Advanced Configuration

### Registry Configuration

The Windows service stores configuration in the registry:

```cmd
REM View service registry keys
reg query "HKLM\SYSTEM\CurrentControlSet\Services\CursorChatMonitor"

REM Service parameters
reg query "HKLM\SYSTEM\CurrentControlSet\Services\CursorChatMonitor\Parameters"

REM Manual registry cleanup (if needed)
reg delete "HKLM\SYSTEM\CurrentControlSet\Services\CursorChatMonitor" /f
```

### Environment Variables

```cmd
REM Set environment variables
setx CURSOR_MONITOR_CONFIG "%USERPROFILE%\.cursor_chat_monitor"
setx CURSOR_MONITOR_DEBUG "1"
setx CURSOR_MONITOR_LOG_LEVEL "DEBUG"

REM View current environment
echo %CURSOR_MONITOR_CONFIG%
```

### Service Configuration File

Create `%PROGRAMDATA%\CursorChatMonitor\service.ini`:

```ini
[Service]
DisplayName=Cursor Chat Monitor
Description=Monitors Cursor IDE for conversation prompts requiring user attention
StartType=Automatic
Account=LocalSystem

[Logging]
LogLevel=INFO
LogFile=%USERPROFILE%\.cursor-chat-monitor-service.log
MaxLogSize=10MB

[Monitor]
ConfigFile=%USERPROFILE%\.cursor_chat_monitor
ScanInterval=1500
```

## 🔐 Security Considerations

### User Account Control (UAC)

```cmd
REM Check UAC status
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" /v EnableLUA

REM Run as administrator when needed
REM Right-click executable -> "Run as administrator"
```

### Firewall Configuration

```cmd
REM Add firewall exception (if needed for remote monitoring)
netsh advfirewall firewall add rule name="Cursor Chat Monitor" dir=in action=allow program="C:\Program Files\CursorChatMonitor\cursor-chat-monitor.exe"

REM Check current firewall rules
netsh advfirewall firewall show rule name="Cursor Chat Monitor"
```

## 🛠️ Windows-Specific Features

### Task Scheduler Integration

```cmd
REM Create scheduled task (alternative to Windows Service)
schtasks /create /tn "CursorChatMonitor" /tr "C:\Program Files\CursorChatMonitor\cursor-chat-monitor.exe --daemon" /sc onlogon /ru "%USERNAME%"

REM Start/stop scheduled task
schtasks /run /tn "CursorChatMonitor"
schtasks /end /tn "CursorChatMonitor"

REM Delete scheduled task
schtasks /delete /tn "CursorChatMonitor" /f
```

### Performance Monitoring

```cmd
REM Monitor resource usage
tasklist /fi "imagename eq cursor-chat-monitor.exe"

REM Performance counters
typeperf "\Process(cursor-chat-monitor)\% Processor Time" -sc 5

REM Memory usage
powershell -c "Get-Process cursor-chat-monitor | Select-Object Name,CPU,WorkingSet"
```

### Windows Integration

```cmd
REM Create desktop shortcut
powershell -c "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Cursor Chat Monitor.lnk'); $Shortcut.TargetPath = 'C:\Program Files\CursorChatMonitor\cursor-chat-monitor.exe'; $Shortcut.Save()"

REM Add to startup folder
copy "C:\Program Files\CursorChatMonitor\cursor-chat-monitor.exe" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\"
```

## 🆘 Getting Help

- **Windows Service Issues**: Check [Microsoft's Service Documentation](https://docs.microsoft.com/en-us/windows/win32/services/services)
- **TTS Problems**: See [Windows Speech Platform](<https://docs.microsoft.com/en-us/previous-versions/office/developer/speech-technologies/hh361683(v=office.14)>)
- **General Issues**: Return to [Main Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Windows-specific implementation** using pywin32 and Windows Speech API for robust window monitoring and native TTS integration.
