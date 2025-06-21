"""
Linux-specific implementation using AT-SPI (Assistive Technology Service Provider Interface)
"""
import sys
import subprocess
import logging
from typing import List, Dict, Any
from .base import AppAccessor, WindowElement, AlertSystem, PlatformConfig

# Linux-specific imports
try:
    import pyatspi
    ATSPI_AVAILABLE = True
except ImportError:
    ATSPI_AVAILABLE = False


class LinuxWindowElement(WindowElement):
    """Linux-specific window element using AT-SPI"""
    
    def __init__(self, window_id: str, title: str, atspi_window):
        super().__init__(window_id, title)
        self.atspi_window = atspi_window
        self.logger = logging.getLogger(__name__)
    
    def get_text_content(self, max_depth: int = 30) -> List[str]:
        """Extract all text content from this Linux window element"""
        texts = []
        
        try:
            # Get all text from the AT-SPI tree
            self._extract_text_recursive(self.atspi_window, texts, 0, max_depth)
            
        except Exception as e:
            self.logger.debug(f"Error extracting text from Linux window: {e}")
        
        return texts
    
    def _extract_text_recursive(self, obj, texts, current_depth, max_depth):
        """Recursively extract text from AT-SPI objects"""
        if current_depth > max_depth:
            return
        
        try:
            # Try to get text content
            if hasattr(obj, 'getText') and obj.getText:
                text = obj.getText(0, -1)
                if text and len(text.strip()) > 2:
                    texts.append(text.strip())
            
            # Get name/description
            if hasattr(obj, 'name') and obj.name:
                if len(obj.name.strip()) > 2:
                    texts.append(obj.name.strip())
            
            if hasattr(obj, 'description') and obj.description:
                if len(obj.description.strip()) > 2:
                    texts.append(obj.description.strip())
            
            # Recurse into children
            if hasattr(obj, 'getChildCount'):
                for i in range(obj.getChildCount()):
                    try:
                        child = obj.getChildAtIndex(i)
                        self._extract_text_recursive(child, texts, current_depth + 1, max_depth)
                    except:
                        continue
                        
        except Exception as e:
            self.logger.debug(f"Error in AT-SPI text extraction at depth {current_depth}: {e}")


class LinuxAppAccessor(AppAccessor):
    """Linux-specific app accessor using AT-SPI"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.target_app = None
    
    def check_prerequisites(self) -> bool:
        """Check if Linux-specific prerequisites are met"""
        if not ATSPI_AVAILABLE:
            print("❌ AT-SPI not available. Install pyatspi: pip install pyatspi")
            return False
        
        if not sys.platform.startswith('linux'):
            print("❌ This implementation is designed for Linux only")
            return False
        
        # Check if AT-SPI is running
        try:
            desktop = pyatspi.Registry.getDesktop(0)
            if not desktop:
                print("❌ AT-SPI desktop not accessible")
                return False
        except Exception as e:
            print(f"❌ AT-SPI not accessible: {e}")
            return False
        
        return True
    
    def find_target_app(self, app_name: str = "cursor") -> bool:
        """Find and connect to Cursor application on Linux"""
        try:
            desktop = pyatspi.Registry.getDesktop(0)
            
            for app in desktop:
                if app and hasattr(app, 'name') and app.name:
                    if app_name.lower() in app.name.lower():
                        self.target_app = app
                        self.logger.debug(f"Found Cursor application: {app.name}")
                        return True
            
            self.logger.debug("Cursor application not found on Linux")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding Cursor on Linux: {e}")
            return False
    
    def get_windows(self) -> List[LinuxWindowElement]:
        """Get all accessible Cursor windows on Linux"""
        windows = []
        
        if not self.target_app:
            return windows
        
        try:
            # Find windows (frames) in the application
            for i in range(self.target_app.getChildCount()):
                try:
                    child = self.target_app.getChildAtIndex(i)
                    if child and hasattr(child, 'getRole'):
                        # Look for window/frame objects
                        if child.getRole() == pyatspi.ROLE_FRAME or child.getRole() == pyatspi.ROLE_WINDOW:
                            title = getattr(child, 'name', f'Window {i+1}')
                            window_id = f"window_{i}_{title}"
                            
                            window_element = LinuxWindowElement(window_id, title, child)
                            windows.append(window_element)
                            self.logger.debug(f"  Window {i+1}: {title}")
                            
                except Exception as e:
                    self.logger.debug(f"Error processing child {i}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error getting Linux windows: {e}")
        
        return windows


class LinuxAlertSystem(AlertSystem):
    """Linux-specific alert system using espeak and notify-send"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.tts_available = self._check_tts_availability()
        self.notifications_available = self._check_notifications_availability()
    
    def _check_tts_availability(self) -> bool:
        """Check if TTS is available (espeak, festival, etc.)"""
        try:
            subprocess.run(['espeak', '--version'], capture_output=True, check=True)
            return True
        except:
            try:
                subprocess.run(['festival', '--version'], capture_output=True, check=True)
                return True
            except:
                return False
    
    def _check_notifications_availability(self) -> bool:
        """Check if notify-send is available"""
        try:
            subprocess.run(['notify-send', '--version'], capture_output=True, check=True)
            return True
        except:
            return False
    
    def play_audio_alert(self, message: str, voice_config: Dict[str, Any]) -> None:
        """Play audio alert using espeak or festival"""
        if not self.tts_available:
            self.logger.warning("TTS not available on Linux")
            return
        
        try:
            # Try espeak first
            rate = voice_config.get("SPEECH_RATE", 175)
            espeak_rate = int(rate * 1.2)  # Convert to espeak rate
            
            result = subprocess.run([
                'espeak', 
                '-s', str(espeak_rate),
                message
            ], capture_output=True)
            
            if result.returncode == 0:
                self.logger.info(f"🔊 Audio alert played: {message}")
            else:
                # Fallback to festival
                subprocess.run(['festival', '--tts'], input=message, text=True, check=False)
                self.logger.info(f"🔊 Audio alert played via festival: {message}")
                
        except Exception as e:
            self.logger.error(f"Error playing audio alert on Linux: {e}")
    
    def show_notification(self, title: str, message: str) -> None:
        """Show system notification using notify-send"""
        if not self.notifications_available:
            self.logger.debug("Notifications not available on Linux")
            return
        
        try:
            subprocess.run([
                'notify-send', 
                title, 
                message,
                '--expire-time=5000'  # 5 seconds
            ], check=False)
            self.logger.debug(f"Notification shown: {title} - {message}")
        except Exception as e:
            self.logger.debug(f"Could not show notification on Linux: {e}")


class LinuxPlatformConfig(PlatformConfig):
    """Linux-specific platform configuration"""
    
    def __init__(self):
        super().__init__()
        self.supports_accessibility = True  # Via AT-SPI
        self.supports_tts = True  # Via espeak/festival
        self.supports_notifications = True  # Via notify-send
        self.required_permissions = []  # Usually no special permissions needed
        self.optional_dependencies = ["pyatspi"] 