# Linux Setup Guide

Complete guide for installing and running Cursor Chat Monitor on Linux distributions.

## 📋 System Requirements

- **Modern Linux distribution** (Ubuntu 18.04+, Fedora 30+, etc.)
- **X11 or Wayland display server**
- **AT-SPI accessibility framework**
- **Cursor IDE installed and running**

## 🚀 Quick Installation

### Option 1: Standalone Executable (Recommended)

```bash
# Download or build from source
git clone https://github.com/your-repo/cursor-chat-monitor
cd cursor-chat-monitor
python3 scripts/build_linux.py

# System-wide installation
cd dist/
sudo ./install.sh

# User installation (alternative)
./install.sh --user

# Verify installation
cursor-chat-monitor --platform-info
systemctl --user status cursor-chat-monitor
```

### Option 2: Python Source Installation

```bash
# Clone repository
git clone https://github.com/your-repo/cursor-chat-monitor
cd cursor-chat-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt

# Test installation
python3 cursor_chat_monitor.py --platform-info
```

## 🔧 Distribution-Specific Setup

### Ubuntu/Debian Setup

```bash
# Update package lists
sudo apt update

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv at-spi2-core espeak espeak-data

# Install full AT-SPI stack
sudo apt install -y libatk-adaptor libgail-common python3-pyatspi gir1.2-atspi-2.0

# Start AT-SPI service
sudo systemctl start at-spi-dbus-bus
sudo systemctl enable at-spi-dbus-bus

# For user session
systemctl --user start at-spi-dbus-bus
systemctl --user enable at-spi-dbus-bus

# Configure accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true
export GTK_MODULES=gail:atk-bridge

# Install TTS and audio tools
sudo apt install -y pulseaudio-utils alsa-utils

# Install additional TTS voices (optional)
sudo apt install -y espeak-data-* festival festvox-*

# Test audio output
speaker-test -c 2 -t wav -l 1
```

### Fedora/RHEL/CentOS Setup

```bash
# Install required packages
sudo dnf install -y python3 python3-pip at-spi2-core at-spi2-atk python3-pyatspi
sudo dnf install -y espeak espeak-data pulseaudio-utils

# For older CentOS/RHEL, use yum
sudo yum install -y python3 python3-pip at-spi2-core espeak espeak-data

# Start services
sudo systemctl start at-spi-dbus-bus
sudo systemctl enable at-spi-dbus-bus

# Enable accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true

# Test TTS
echo "Fedora TTS test" | espeak
```

### Arch Linux Setup

```bash
# Install packages
sudo pacman -S python python-pip at-spi2-core at-spi2-atk python-atspi espeak espeak-data

# AUR packages (if needed)
yay -S python-pyatspi-git

# Start AT-SPI service
systemctl --user start at-spi-dbus-bus
systemctl --user enable at-spi-dbus-bus

# Enable accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true

# Test setup
echo "Arch Linux test" | espeak
```

### openSUSE Setup

```bash
# Install packages
sudo zypper install python3 python3-pip at-spi2-core python3-pyatspi espeak espeak-data

# Start services
sudo systemctl start at-spi-dbus-bus
sudo systemctl enable at-spi-dbus-bus

# Enable accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true
```

## 🎵 Audio Configuration

### Text-to-Speech Setup

Linux supports multiple TTS engines:

```bash
# Test espeak (primary)
echo "Testing espeak TTS" | espeak -s 150 -v en

# Test festival (fallback)
echo "Testing festival TTS" | festival --tts

# List available espeak voices
espeak --voices

# Test specific voice
echo "Hello from espeak" | espeak -v en+f3 -s 160

# Install additional voices
sudo apt install espeak-data-* festvox-*  # Ubuntu/Debian
sudo dnf install espeak-data-*            # Fedora
```

### Audio System Configuration

```bash
# Check PulseAudio status
pulseaudio --check -v

# Test audio output
pactl info
aplay -l

# Set default audio device (if multiple)
pactl set-default-sink alsa_output.pci-0000_00_1b.0.analog-stereo

# Test audio with speaker-test
speaker-test -c 2 -t wav -l 1
```

### Configuration File

Create `~/.cursor_chat_monitor` with Linux-specific settings:

```json
{
  "VOICE_NAME": "en+f3",
  "SPEECH_RATE": 150,
  "WINDOW_TITLE_ANNOUNCE_MODE": "last",
  "REPLACE_PERIODS_IN_ANNOUNCEMENT": true,
  "AWAITING_USER_ACTION_TEXTS": [
    "resume the conversation",
    "Connection failed",
    "trouble connecting to the model provider"
  ],
  "GENERATING_TEXTS": ["generating"],
  "DEFAULT_SCAN_INTERVAL_MS": 1500,
  "TTS_ENGINE": "espeak"
}
```

## 🔧 Service Management

### systemd Integration

The Linux version integrates with systemd for proper service management.

**Service Installation** (done automatically by installer):

```bash
# User service
~/.config/systemd/user/cursor-chat-monitor.service

# System service
/etc/systemd/system/cursor-chat-monitor.service
```

### Service Commands (User Service)

```bash
# Start service
cursor-chat-monitor-service start
systemctl --user start cursor-chat-monitor

# Stop service
cursor-chat-monitor-service stop
systemctl --user stop cursor-chat-monitor

# Check service status
cursor-chat-monitor-service status
systemctl --user status cursor-chat-monitor

# Restart service
cursor-chat-monitor-service restart
systemctl --user restart cursor-chat-monitor

# Enable auto-start on login
cursor-chat-monitor-service enable
systemctl --user enable cursor-chat-monitor

# Disable auto-start
cursor-chat-monitor-service disable
systemctl --user disable cursor-chat-monitor

# View service logs
cursor-chat-monitor-service logs
journalctl --user -u cursor-chat-monitor -f
```

### System-Wide Service (requires sudo)

```bash
# System service management
sudo systemctl start cursor-chat-monitor
sudo systemctl enable cursor-chat-monitor
sudo systemctl status cursor-chat-monitor

# View system service logs
sudo journalctl -u cursor-chat-monitor -f
```

## 🖥️ Desktop Environment Configuration

### GNOME Configuration

```bash
# Enable accessibility
gsettings set org.gnome.desktop.interface toolkit-accessibility true

# Check AT-SPI status
gsettings get org.gnome.desktop.interface toolkit-accessibility

# Additional GNOME accessibility settings
gsettings set org.gnome.desktop.a11y always-show-universal-access-status true

# Environment variables for GNOME
export ACCESSIBILITY_ENABLED=1
export GTK_MODULES=gail:atk-bridge
```

### KDE Plasma Configuration

```bash
# Enable accessibility in KDE
kwriteconfig5 --file kaccessrc --group Basic Settings --key Enable true

# Check KDE accessibility
kreadconfig5 --file kaccessrc --group "Basic Settings" --key Enable

# Set Qt accessibility
export QT_ACCESSIBILITY=1
```

### XFCE Configuration

```bash
# Enable accessibility in XFCE
xfconf-query -c accessibility -p /EnabledAssistiveTechnologies -s true

# Check XFCE settings
xfconf-query -c accessibility -l
```

### Check Current Desktop Environment

```bash
# Identify desktop environment
echo $XDG_CURRENT_DESKTOP
echo $DESKTOP_SESSION
echo $GDMSESSION

# Common values:
# GNOME, KDE, XFCE, Unity, Cinnamon, MATE, etc.
```

## 🐛 Troubleshooting

### Common Issues

#### AT-SPI Service Not Running

```bash
# Check AT-SPI service status
systemctl --user status at-spi-dbus-bus

# Start AT-SPI manually
systemctl --user start at-spi-dbus-bus
systemctl --user enable at-spi-dbus-bus

# Check D-Bus accessibility services
busctl --user list | grep org.a11y

# Debug AT-SPI registry
dbus-send --session --print-reply \
  --dest=org.a11y.atspi.Registry \
  /org/a11y/atspi/registry \
  org.a11y.atspi.Registry.GetApplications
```

#### Cursor Not Detected

```bash
# Check if Cursor is running
ps aux | grep -i cursor

# Check X11 windows
xwininfo -tree -root | grep -i cursor

# For Wayland
swaymsg -t get_tree | grep -i cursor

# Check accessibility tree
python3 -c "
import pyatspi
desktop = pyatspi.Registry.getDesktop(0)
for app in desktop:
    if 'cursor' in app.name.lower():
        print(f'Found: {app.name}')
"
```

#### TTS Not Working

```bash
# Test TTS engines
echo "Testing espeak" | espeak -s 150
echo "Testing festival" | festival --tts

# Check audio system
pactl info
aplay -l

# Test audio output
speaker-test -c 2 -t wav -l 1

# Check volume levels
amixer get Master
pactl list sinks

# Debug audio issues
pulseaudio --kill
pulseaudio --start
```

#### Permission Issues

```bash
# Check user groups
groups $USER

# Add user to audio group (if needed)
sudo usermod -a -G audio $USER

# Check accessibility permissions
ls -la /var/lib/at-spi/
```

### Diagnostic Commands

```bash
# Comprehensive system check
cursor-chat-monitor --platform-info

# Check Linux distribution
cat /etc/os-release
lsb_release -a

# Check display server
echo $XDG_SESSION_TYPE  # x11 or wayland
echo $WAYLAND_DISPLAY
echo $DISPLAY

# Check Python environment
which python3
python3 --version
pip3 list | grep -E "pyatspi|at-spi"

# Check accessibility framework
gsettings get org.gnome.desktop.interface toolkit-accessibility
echo $GTK_MODULES
echo $QT_ACCESSIBILITY

# Audio system diagnostics
pactl info
aplay -l
cat /proc/asound/cards
```

### Log Analysis

```bash
# Service logs (systemd)
journalctl --user -u cursor-chat-monitor -f
journalctl --user -u cursor-chat-monitor --since "today"

# User logs
tail -f ~/.cursor-chat-monitor-service.log
tail -f ~/.local/share/cursor-chat-monitor/logs/service.log

# System logs
sudo journalctl -u cursor-chat-monitor -f

# Search for specific errors
journalctl --user -u cursor-chat-monitor | grep -i error
grep -i "at-spi" ~/.cursor-chat-monitor-service.log
grep -i "accessibility" ~/.cursor-chat-monitor-service.log
grep -i "pyatspi" ~/.cursor-chat-monitor-service.log

# System accessibility logs
journalctl | grep -i "at-spi"
journalctl | grep -i "accessibility"
```

## 🔧 Advanced Configuration

### Custom systemd Service

Edit `~/.config/systemd/user/cursor-chat-monitor.service`:

```ini
[Unit]
Description=Cursor Chat Monitor
After=graphical-session.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cursor-chat-monitor --daemon --config=%h/.cursor_chat_monitor
Restart=always
RestartSec=10
Environment=DISPLAY=:0
Environment=GTK_MODULES=gail:atk-bridge
Environment=QT_ACCESSIBILITY=1
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
```

### Environment Configuration

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Cursor Chat Monitor environment
export CURSOR_MONITOR_CONFIG="$HOME/.cursor_chat_monitor"
export CURSOR_MONITOR_DEBUG=1
export CURSOR_MONITOR_LOG_LEVEL="DEBUG"

# Accessibility environment
export ACCESSIBILITY_ENABLED=1
export GTK_MODULES=gail:atk-bridge
export QT_ACCESSIBILITY=1
```

### Performance Tuning

```bash
# Check system resources
top -p $(pgrep cursor-chat-monitor)
htop -p $(pgrep cursor-chat-monitor)

# Memory usage
ps -o pid,ppid,pcpu,pmem,comm -p $(pgrep cursor-chat-monitor)

# I/O monitoring
sudo iotop -p $(pgrep cursor-chat-monitor)

# Network monitoring (if applicable)
sudo netstat -tulpn | grep cursor-chat-monitor
```

## 🛠️ Linux-Specific Features

### Desktop Integration

```bash
# Create .desktop file for application launcher
cat > ~/.local/share/applications/cursor-chat-monitor.desktop << EOF
[Desktop Entry]
Name=Cursor Chat Monitor
Comment=Monitor Cursor IDE conversations
Exec=/usr/local/bin/cursor-chat-monitor
Icon=cursor-chat-monitor
Terminal=false
Type=Application
Categories=Utility;Development;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

### Shell Integration

```bash
# Add aliases to ~/.bashrc or ~/.zshrc
alias ccm='cursor-chat-monitor'
alias ccm-start='cursor-chat-monitor-service start'
alias ccm-stop='cursor-chat-monitor-service stop'
alias ccm-status='cursor-chat-monitor-service status'
alias ccm-logs='cursor-chat-monitor-service logs'
```

### Automation Scripts

```bash
# Auto-start script for login
cat > ~/.config/autostart/cursor-chat-monitor.desktop << EOF
[Desktop Entry]
Type=Application
Name=Cursor Chat Monitor
Exec=/usr/local/bin/cursor-chat-monitor --daemon
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF
```

## 🆘 Getting Help

- **AT-SPI Issues**: Check [AT-SPI Documentation](https://www.freedesktop.org/wiki/Accessibility/AT-SPI2/)
- **systemd Problems**: See [systemd Service Guide](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- **Audio Issues**: Check [PulseAudio Documentation](https://www.freedesktop.org/wiki/Software/PulseAudio/)
- **General Issues**: Return to [Main Troubleshooting Guide](../TROUBLESHOOTING.md)

---

**Linux-specific implementation** using AT-SPI and pyatspi for robust window monitoring with espeak/festival TTS integration across multiple desktop environments.
