"""
macOS-specific implementation using PyObjC and Accessibility APIs
"""
import sys
import subprocess
import logging
from typing import List, Dict, Any
from .base import AppAccessor, WindowElement, AlertSystem, PlatformConfig

# macOS-specific imports (PyObjC)
try:
    from AppKit import NSWorkspace
    from ApplicationServices import (
        AXUIElementCreateApplication, 
        AXUIElementCopyAttributeValue,
        kAXErrorSuccess,
        kAXTitleAttribute,
        kAXValueAttribute,
        kAXRoleAttribute,
        kAXChildrenAttribute,
        kAXDescriptionAttribute,
        AXIsProcessTrusted
    )
    ACCESSIBILITY_AVAILABLE = True
except ImportError as e:
    ACCESSIBILITY_AVAILABLE = False


class MacOSWindowElement(WindowElement):
    """macOS-specific window element using Accessibility APIs"""
    
    def __init__(self, window_id: str, title: str, ax_element):
        super().__init__(window_id, title)
        self.ax_element = ax_element
        self.logger = logging.getLogger(__name__)
    
    def get_text_content(self, max_depth: int = 50, sidebar_depth_limit: int = 20) -> List[str]:
        """Extract all text content from this macOS window element with deeper traversal for chat content"""
        return self._get_all_text_elements(self.ax_element, max_depth, 0, sidebar_depth_limit)
    
    def _get_all_text_elements(self, element, max_depth: int = 50, current_depth: int = 0, sidebar_depth_limit: int = 20) -> List[str]:
        """Extract all text from accessibility elements using breadth-first search for better performance"""
        from collections import deque
        
        texts = []
        seen_texts = set()  # Track seen texts to avoid duplicates
        queue = deque([(element, 0)])  # (element, depth)
        
        while queue:
            current_element, depth = queue.popleft()
            
            if depth > max_depth:
                continue
            
            try:
                # Try to get value first (for text fields, static text, etc.)
                error_code, value = AXUIElementCopyAttributeValue(current_element, kAXValueAttribute, None)
                if error_code == kAXErrorSuccess and value and isinstance(value, str):
                    value = value.strip()
                    if value and len(value) > 2 and value not in seen_texts:  # Ignore very short strings
                        texts.append(value)
                        seen_texts.add(value)
                
                # Try to get title
                error_code, title = AXUIElementCopyAttributeValue(current_element, kAXTitleAttribute, None)
                if error_code == kAXErrorSuccess and title and isinstance(title, str):
                    title = title.strip()
                    if title and len(title) > 2 and title not in seen_texts:
                        texts.append(title)
                        seen_texts.add(title)
                
                # Try to get description
                error_code, desc = AXUIElementCopyAttributeValue(current_element, kAXDescriptionAttribute, None)
                if error_code == kAXErrorSuccess and desc and isinstance(desc, str):
                    desc = desc.strip()
                    if desc and len(desc) > 2 and desc not in seen_texts:
                        texts.append(desc)
                        seen_texts.add(desc)
                
                # Add children to queue for next level processing (breadth-first)
                error_code, children = AXUIElementCopyAttributeValue(current_element, kAXChildrenAttribute, None)
                if error_code == kAXErrorSuccess and children:
                    for child in children:
                        queue.append((child, depth + 1))
            
            except Exception as e:
                self.logger.debug(f"Error accessing accessibility element at depth {depth}: {e}")
        
        return texts


class MacOSAppAccessor(AppAccessor):
    """macOS-specific app accessor using Accessibility APIs"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def check_prerequisites(self) -> bool:
        """Check if macOS-specific prerequisites are met"""
        if not ACCESSIBILITY_AVAILABLE:
            print("❌ Accessibility APIs not available")
            return False
        
        if sys.platform != 'darwin':
            print("❌ This implementation is designed for macOS only")
            return False
        
        if not AXIsProcessTrusted():
            print("❌ No accessibility permissions granted")
            print("💡 Go to System Preferences > Security & Privacy > Accessibility")
            print("   and add Terminal (or your Python interpreter) to the list")
            return False
        
        return True
    
    def find_target_app(self, app_name: str = "cursor") -> bool:
        """Find and connect to Cursor application on macOS"""
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            # Target main Cursor process (ignore helpers)
            for app in running_apps:
                if app.localizedName() == 'Cursor' and 'helper' not in app.localizedName().lower():
                    self.target_pid = app.processIdentifier()
                    self.target_app = AXUIElementCreateApplication(self.target_pid)
                    self.logger.debug(f"Connected to main Cursor process (PID: {self.target_pid})")
                    return True
            
            self.logger.debug("Main Cursor process not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Error finding Cursor: {e}")
            return False
    
    def get_windows(self) -> List[MacOSWindowElement]:
        """Get all accessible Cursor windows on macOS"""
        windows = []
        
        try:
            error_code, ax_windows = AXUIElementCopyAttributeValue(self.target_app, "AXWindows", None)
            
            if error_code == kAXErrorSuccess and ax_windows:
                self.logger.debug(f"Found {len(ax_windows)} windows")
                
                for i, ax_window in enumerate(ax_windows):
                    # Get window title
                    error_code, title = AXUIElementCopyAttributeValue(ax_window, kAXTitleAttribute, None)
                    window_title = title if error_code == kAXErrorSuccess else f"Untitled Window {i+1}"
                    
                    # Create unique window ID
                    window_id = f"window_{i}_{window_title}"
                    
                    window_element = MacOSWindowElement(window_id, window_title, ax_window)
                    windows.append(window_element)
                    
                    self.logger.debug(f"  Window {i+1}: {window_title}")
            else:
                self.logger.debug(f"No windows found (error: {error_code})")
            
        except Exception as e:
            self.logger.error(f"Error getting windows: {e}")
        
        return windows


class MacOSAlertSystem(AlertSystem):
    """macOS-specific alert system using 'say' command"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def play_audio_alert(self, message: str, voice_config: Dict[str, Any]) -> None:
        """Play audio alert using macOS 'say' command"""
        try:
            subprocess.run([
                'say', 
                '-v', voice_config.get("VOICE_NAME", "Daniel"),
                '-r', str(voice_config.get("SPEECH_RATE", 175)),
                message
            ], check=False)
            self.logger.info(f"🔊 Audio alert played: {message}")
        except Exception as e:
            self.logger.error(f"Error playing audio alert: {e}")
    
    def show_notification(self, title: str, message: str) -> None:
        """Show system notification using osascript (optional)"""
        try:
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            subprocess.run(['osascript', '-e', script], check=False)
            self.logger.debug(f"Notification shown: {title} - {message}")
        except Exception as e:
            self.logger.debug(f"Could not show notification: {e}")


class MacOSPlatformConfig(PlatformConfig):
    """macOS-specific platform configuration"""
    
    def __init__(self):
        super().__init__()
        self.supports_accessibility = True
        self.supports_tts = True
        self.supports_notifications = True
        self.required_permissions = ["Accessibility"]
        self.optional_dependencies = ["pyobjc-framework-Cocoa", "pyobjc-framework-ApplicationServices"] 