"""
Windows-specific implementation using Win32 APIs and UI Automation
"""
import sys
import logging
from typing import List, Dict, Any
from .base import AppAccessor, WindowElement, AlertSystem, PlatformConfig

# Windows-specific imports
try:
    import win32gui
    import win32con
    import win32process
    import pyttsx3
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class WindowsWindowElement(WindowElement):
    """Windows-specific window element using Win32 APIs"""
    
    def __init__(self, window_id: str, title: str, hwnd):
        super().__init__(window_id, title)
        self.hwnd = hwnd
        self.logger = logging.getLogger(__name__)
    
    def get_text_content(self, max_depth: int = 30) -> List[str]:
        """Extract all text content from this Windows window element"""
        texts = []
        
        try:
            # Get window text
            window_text = win32gui.GetWindowText(self.hwnd)
            if window_text:
                texts.append(window_text)
            
            # Enumerate child windows to get more text
            def enum_child_proc(hwnd, texts):
                try:
                    child_text = win32gui.GetWindowText(hwnd)
                    if child_text and len(child_text) > 2:
                        texts.append(child_text)
                except:
                    pass
                return True
            
            win32gui.EnumChildWindows(self.hwnd, enum_child_proc, texts)
            
        except Exception as e:
            self.logger.debug(f"Error extracting text from Windows window: {e}")
        
        return texts


class WindowsAppAccessor(AppAccessor):
    """Windows-specific app accessor using Win32 APIs"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.target_windows = []
    
    def check_prerequisites(self) -> bool:
        """Check if Windows-specific prerequisites are met"""
        if not WIN32_AVAILABLE:
            print("❌ Win32 APIs not available. Install pywin32: pip install pywin32")
            return False
        
        if sys.platform != 'win32':
            print("❌ This implementation is designed for Windows only")
            return False
        
        return True
    
    def find_target_app(self, app_name: str = "cursor") -> bool:
        """Find and connect to Cursor application on Windows"""
        try:
            found_windows = []
            
            def enum_windows_proc(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if window_text and app_name.lower() in window_text.lower():
                        # Get process info to ensure it's the main process
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            windows.append((hwnd, window_text, pid))
                        except:
                            pass
                return True
            
            win32gui.EnumWindows(enum_windows_proc, found_windows)
            
            if found_windows:
                self.target_windows = found_windows
                self.logger.debug(f"Found {len(found_windows)} Cursor windows on Windows")
                return True
            
            self.logger.debug("No Cursor windows found on Windows")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding Cursor on Windows: {e}")
            return False
    
    def get_windows(self) -> List[WindowsWindowElement]:
        """Get all accessible Cursor windows on Windows"""
        windows = []
        
        try:
            for i, (hwnd, title, pid) in enumerate(self.target_windows):
                window_id = f"window_{i}_{title}"
                window_element = WindowsWindowElement(window_id, title, hwnd)
                windows.append(window_element)
                self.logger.debug(f"  Window {i+1}: {title} (PID: {pid})")
                
        except Exception as e:
            self.logger.error(f"Error getting Windows windows: {e}")
        
        return windows


class WindowsAlertSystem(AlertSystem):
    """Windows-specific alert system using pyttsx3"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.tts_engine = pyttsx3.init()
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            self.tts_engine = None
    
    def play_audio_alert(self, message: str, voice_config: Dict[str, Any]) -> None:
        """Play audio alert using pyttsx3 TTS"""
        if not self.tts_engine:
            self.logger.error("TTS engine not available")
            return
        
        try:
            # Configure TTS settings
            rate = voice_config.get("SPEECH_RATE", 175)
            self.tts_engine.setProperty('rate', rate)
            
            # Set voice if specified
            voice_name = voice_config.get("VOICE_NAME")
            if voice_name:
                voices = self.tts_engine.getProperty('voices')
                for voice in voices:
                    if voice_name.lower() in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
            
            self.tts_engine.say(message)
            self.tts_engine.runAndWait()
            self.logger.info(f"🔊 Audio alert played: {message}")
            
        except Exception as e:
            self.logger.error(f"Error playing audio alert on Windows: {e}")
    
    def show_notification(self, title: str, message: str) -> None:
        """Show system notification on Windows (placeholder)"""
        try:
            # Could use win32api or plyer for notifications
            # For now, just log
            self.logger.info(f"Notification: {title} - {message}")
        except Exception as e:
            self.logger.debug(f"Could not show notification on Windows: {e}")


class WindowsPlatformConfig(PlatformConfig):
    """Windows-specific platform configuration"""
    
    def __init__(self):
        super().__init__()
        self.supports_accessibility = True  # Via Win32 APIs
        self.supports_tts = True
        self.supports_notifications = False  # Not implemented yet
        self.required_permissions = []  # No special permissions needed
        self.optional_dependencies = ["pywin32", "pyttsx3"] 