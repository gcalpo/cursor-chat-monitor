"""
Windows-specific implementation using Win32 APIs and UI Automation
"""
import sys
import logging
import os

# Configure logging BEFORE importing uiautomation
logging.getLogger('uiautomation').setLevel(logging.CRITICAL)
logging.getLogger('comtypes').setLevel(logging.CRITICAL)

# Temporarily suppress stdout/stderr during uiautomation import
class SuppressOutput:
    def __enter__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stderr.close()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

from typing import List, Dict, Any
from .base import AppAccessor, WindowElement, AlertSystem, PlatformConfig

# Windows-specific imports
try:
    import win32gui
    import win32con
    import win32process
    import pyttsx3
    import psutil
    
    # Import uiautomation with suppressed output
    with SuppressOutput():
        import uiautomation as auto
    
    # Disable verbose UI Automation logging
    auto.OPERATION_WAIT_TIME = 0
    
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


class WindowsWindowElement(WindowElement):
    """Windows-specific window element using Win32 APIs and UI Automation"""
    
    def __init__(self, window_id: str, title: str, hwnd):
        super().__init__(window_id, title)
        self.hwnd = hwnd
        self.logger = logging.getLogger(__name__)
    
    def get_text_content(self, max_depth: int = 30, sidebar_depth_limit: int = 20) -> List[str]:
        """Extract all text content from this Windows window element using optimized targeted traversal."""
        texts = []
        visited = set()

        # Method 1: Win32 API extraction (for traditional controls)
        def extract_text_recursive(hwnd, current_depth):
            if current_depth > max_depth or hwnd in visited:
                return
            visited.add(hwnd)
            try:
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:
                    texts.append(window_text)
            except Exception as e:
                pass
            # Recurse into child windows
            try:
                def enum_child_proc(child_hwnd, _):
                    extract_text_recursive(child_hwnd, current_depth + 1)
                    return True
                win32gui.EnumChildWindows(hwnd, enum_child_proc, None)
            except Exception as e:
                pass

        try:
            extract_text_recursive(self.hwnd, 0)
        except Exception as e:
            self.logger.debug(f"Error in Win32 text extraction: {e}")

        # Method 2: Optimized UI Automation extraction using targeted traversal
        try:
            uia_element = auto.ControlFromHandle(self.hwnd)
            if uia_element:
                self._extract_text_targeted(uia_element, texts, max_depth, sidebar_depth_limit)
        except Exception as e:
            self.logger.debug(f"Error in UI Automation text extraction: {e}")

        return texts

    def _extract_text_targeted(self, root_element, texts, max_depth, sidebar_depth_limit):
        """Hybrid targeted traversal: fast path through all container types, fallback to broader container traversal."""
        from collections import deque
        
        # --- Fast Path: Recursively search all container type children at each level ---
        def fast_path_sidebar_search(element, depth):
            if max_depth is not None and depth > max_depth:
                return None
            try:
                automation_id = getattr(element, 'AutomationId', '')
                if 'aichat' in automation_id.lower() or 'workbench.panel.aichat' in automation_id:
                    return element
                
                # Define all container types that can be in the sidebar path
                container_types = [
                    'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
                    'group', 'pane', 'window', 'document'
                ]
                
                class_name = getattr(element, 'ClassName', '')
                control_type = getattr(element, 'ControlTypeName', '') if hasattr(element, 'ControlTypeName') else ''
                localized_type = getattr(element, 'LocalizedControlType', '') if hasattr(element, 'LocalizedControlType') else ''
                
                # Check if this element is a container type we should descend into
                is_container = (class_name == 'Chrome_RenderWidgetHostHWND' or
                               control_type.lower() in container_types or
                               localized_type.lower() in container_types)
                
                if is_container:
                    children = element.GetChildren()
                    for child in children:
                        found = fast_path_sidebar_search(child, depth + 1)
                        if found:
                            return found
            except Exception:
                pass
            return None

        sidebar_element = fast_path_sidebar_search(root_element, 0)
        if sidebar_element:
            self.logger.debug(f"[FAST PATH] Found chat sidebar with AutomationId: {getattr(sidebar_element, 'AutomationId', '')}")
            self._extract_text_from_sidebar(sidebar_element, texts, sidebar_depth_limit)
            return True

        # --- Fallback: Broader container traversal (current logic) ---
        queue = deque([(root_element, 0)])
        element_count = 0
        while queue and element_count < 10000:  # Safety limit
            current_element, depth = queue.popleft()
            if max_depth is not None and depth > max_depth:
                continue
            element_count += 1
            try:
                automation_id = getattr(current_element, 'AutomationId', '')
                name = getattr(current_element, 'Name', '')
                class_name = getattr(current_element, 'ClassName', '')
                control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
                localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
                is_chat_sidebar = ('aichat' in automation_id.lower() or 
                                  'workbench.panel.aichat' in automation_id or
                                  'chat' in name.lower() and 'panel' in automation_id.lower())
                if is_chat_sidebar:
                    self.logger.debug(f"[FALLBACK] Found chat sidebar with AutomationId: {automation_id}")
                    self._extract_text_from_sidebar(current_element, texts, sidebar_depth_limit)
                    return True
                # Traverse all container types seen in the sidebar path
                should_traverse = False
                container_types = [
                    'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
                    'group', 'pane', 'window', 'document'
                ]
                if (class_name == 'Chrome_RenderWidgetHostHWND' or
                    control_type.lower() in container_types or
                    localized_type.lower() in container_types or
                    ('workbench.panel.aichat' in automation_id.lower())):
                    should_traverse = True
                if should_traverse:
                    try:
                        children = current_element.GetChildren()
                        for child in children:
                            queue.append((child, depth + 1))
                    except:
                        pass
            except Exception:
                pass
        self.logger.debug(f"Chat sidebar not found in targeted traversal (processed {element_count} elements)")
        return False

    def _extract_text_from_sidebar(self, sidebar_element, texts, max_depth):
        """Extract all text from the sidebar and its descendants with depth limit."""
        from collections import deque
        queue = deque([(sidebar_element, 0)])
        
        while queue:
            current_element, depth = queue.popleft()
            if max_depth is not None and depth > max_depth:
                continue
            
            try:
                # Get various text properties
                for prop_name in ['Name', 'AutomationId', 'ClassName', 'HelpText', 'LocalizedControlType', 'ControlType']:
                    try:
                        value = getattr(current_element, prop_name, None)
                        if value and isinstance(value, str) and value.strip():
                            texts.append(value.strip())
                    except:
                        pass
                
                # Also try to get the element's text content directly
                try:
                    if hasattr(current_element, 'GetText'):
                        text_content = current_element.GetText()
                        if text_content and isinstance(text_content, str) and text_content.strip():
                            texts.append(text_content.strip())
                except:
                    pass
                
                # Add children
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1))
            except Exception as e:
                pass


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
                        try:
                            _, pid = win32process.GetWindowThreadProcessId(hwnd)
                            # Check process name using psutil
                            try:
                                proc = psutil.Process(pid)
                                if proc.name().lower() == "cursor.exe":
                                    windows.append((hwnd, window_text, pid))
                            except Exception as e:
                                pass  # Could not get process name, skip
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
    
    def __init__(self, sidebar_depth_limit: int = 20):
        super().__init__()
        self.supports_accessibility = True  # Via Win32 APIs
        self.supports_tts = True
        self.supports_notifications = False  # Not implemented yet
        self.required_permissions = []  # No special permissions needed
        self.optional_dependencies = ["pywin32", "pyttsx3"]
        self.sidebar_depth_limit = sidebar_depth_limit  # Configurable depth limit for sidebar traversal 