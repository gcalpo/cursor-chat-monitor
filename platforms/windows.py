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

from typing import List, Dict, Any, Optional
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

# Global cache for sidebar paths on a per-window handle basis
# Key: window_handle, Value: path_structure
GLOBAL_SIDEBAR_PATH_CACHE = {}

def get_cached_sidebar_path(window_handle):
    """Get cached sidebar path for a window handle if it exists."""
    if window_handle in GLOBAL_SIDEBAR_PATH_CACHE:
        path_structure = GLOBAL_SIDEBAR_PATH_CACHE[window_handle]
        logging.getLogger(__name__).debug(f"Using cached sidebar path for window handle {window_handle}")
        return path_structure
    return None

def cache_sidebar_path(window_handle, path_structure):
    """Cache the sidebar path for a window handle indefinitely."""
    GLOBAL_SIDEBAR_PATH_CACHE[window_handle] = path_structure
    logging.getLogger(__name__).debug(f"Cached sidebar path for window handle {window_handle} with {len(path_structure)} elements")

def clear_sidebar_path_cache(window_handle=None):
    """Clear the sidebar path cache for a specific window handle or all window handles."""
    if window_handle is not None:
        if window_handle in GLOBAL_SIDEBAR_PATH_CACHE:
            del GLOBAL_SIDEBAR_PATH_CACHE[window_handle]
            logging.getLogger(__name__).debug(f"Cleared cached sidebar path for window handle {window_handle}")
    else:
        GLOBAL_SIDEBAR_PATH_CACHE.clear()
        logging.getLogger(__name__).debug("Cleared all cached sidebar paths")

def get_sidebar_path_cache_stats():
    """Get statistics about the sidebar path cache."""
    return {
        'cached_windows': list(GLOBAL_SIDEBAR_PATH_CACHE.keys()),
        'cache_size': len(GLOBAL_SIDEBAR_PATH_CACHE),
        'cached_paths': {hwnd: len(path_structure) for hwnd, path_structure in GLOBAL_SIDEBAR_PATH_CACHE.items()}
    }

class WindowsWindowElement(WindowElement):
    """Windows-specific window element using Win32 APIs and UI Automation"""
    
    def __init__(self, window_id: str, title: str, hwnd, pid=None):
        super().__init__(window_id, title)
        self.hwnd = hwnd
        self.pid = pid  # Store PID for global caching
        self.logger = logging.getLogger(__name__)
        # Remove instance-level cache since we're using global cache now
    
    def get_text_content(self, max_depth: int = 30, sidebar_depth_limit: int = 20) -> List[str]:
        """Extract all text content from this Windows window element using optimized targeted traversal."""
        texts = []

        # Optimized UI Automation extraction using targeted traversal with fallback
        try:
            uia_element = auto.ControlFromHandle(self.hwnd)
            if uia_element:
                # Try targeted traversal first, fallback to hybrid if it fails
                if not self._extract_text_targeted_traversal(uia_element, texts, max_depth, sidebar_depth_limit):
                    self.logger.debug("Targeted traversal failed, falling back to hybrid traversal")
                    self._extract_text_targeted(uia_element, texts, max_depth, sidebar_depth_limit)
        except Exception as e:
            self.logger.debug(f"Error in UI Automation text extraction: {e}")

        return texts

    def _analyze_sidebar_path_structure(self, root_element, max_depth=30):
        """Analyze the actual path structure to the sidebar and return the optimal traversal sequence."""
        # Check global cache first if window handle is available
        if self.hwnd:
            cached_path = get_cached_sidebar_path(self.hwnd)
            if cached_path is not None:
                return cached_path
        
        from collections import deque
        
        # Define container types that can be in the sidebar path
        container_types = [
            'groupcontrol', 'panecontrol', 'windowcontrol', 'documentcontrol',
            'group', 'pane', 'window', 'document'
        ]
        
        # Use a queue for BFS: (element, depth, path)
        queue = deque([(root_element, 0, [])])
        element_count = 0
        sidebar_paths = []
        
        while queue and element_count < 2000:  # Reduced limit for faster analysis
            current_element, depth, path = queue.popleft()
            
            if max_depth is not None and depth > max_depth:
                continue
                
            element_count += 1
            
            try:
                automation_id = getattr(current_element, 'AutomationId', '')
                name = getattr(current_element, 'Name', '')
                class_name = getattr(current_element, 'ClassName', '')
                control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
                localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
                
                # Create current element info
                current_info = {
                    'depth': depth,
                    'automation_id': automation_id,
                    'name': name,
                    'class_name': class_name,
                    'control_type': control_type,
                    'localized_type': localized_type,
                    'element_count': element_count
                }
                
                # Check if this is the chat sidebar
                is_chat_sidebar = ('aichat' in automation_id.lower() or 
                                  'workbench.panel.aichat' in automation_id or
                                  'chat' in name.lower() and 'panel' in automation_id.lower())
                
                current_path = path + [current_info]
                
                if is_chat_sidebar:
                    sidebar_paths.append(current_path)
                    self.logger.debug(f"Found sidebar path #{len(sidebar_paths)} with {len(current_path)} elements")
                    # Stop after finding first sidebar path for speed
                    break
                
                # Only traverse container types that can be in the sidebar path
                should_traverse = False
                if (class_name == 'Chrome_RenderWidgetHostHWND' or
                    control_type.lower() in container_types or
                    localized_type.lower() in container_types):
                    should_traverse = True
                
                if should_traverse:
                    # Add children to queue for next level (BFS)
                    try:
                        children = current_element.GetChildren()
                        for child in children:
                            queue.append((child, depth + 1, current_path))
                    except:
                        pass
                    
            except Exception as e:
                pass
        
        if not sidebar_paths:
            self.logger.debug("No sidebar paths found during analysis")
            return None
        
        # Extract the path structure from the first found sidebar
        reference_path = []
        for elem in sidebar_paths[0]:
            reference_path.append({
                'class_name': elem['class_name'],
                'control_type': elem['control_type'],
                'automation_id': elem['automation_id'],
                'name': elem['name']
            })
        
        # Cache the path structure globally if window handle is available
        if self.hwnd:
            cache_sidebar_path(self.hwnd, reference_path)
        
        self.logger.debug(f"Analyzed {len(sidebar_paths)} sidebar paths, cached reference path with {len(reference_path)} elements")
        return reference_path

    def _extract_text_targeted_traversal(self, root_element, texts, max_depth=30, sidebar_depth_limit=20):
        """Targeted traversal based on analyzed sidebar path structure."""
        from collections import deque
        
        # First, analyze the path structure (with caching)
        path_structure = self._analyze_sidebar_path_structure(root_element, max_depth)
        
        if not path_structure:
            self.logger.debug("Could not determine sidebar path structure")
            return False
        
        # Targeted traversal based on path structure
        excluded_count = 0
        
        def targeted_sidebar_search(element, depth, path_index=0):
            nonlocal excluded_count
            
            if max_depth is not None and depth > max_depth:
                return None
            
            if path_index >= len(path_structure):
                return None
            
            try:
                automation_id = getattr(element, 'AutomationId', '')
                name = getattr(element, 'Name', '')
                class_name = getattr(element, 'ClassName', '')
                control_type = getattr(element, 'ControlTypeName', '') if hasattr(element, 'ControlTypeName') else ''
                
                # Check if this is the chat sidebar
                if ('aichat' in automation_id.lower() or 
                    'workbench.panel.aichat' in automation_id or
                    'chat' in name.lower() and 'panel' in automation_id.lower()):
                    return element
                
                # Get expected element from path structure
                expected_elem = path_structure[path_index]
                
                # Check if current element matches the expected path structure
                matches_structure = (
                    (expected_elem['class_name'] and class_name == expected_elem['class_name']) or
                    (expected_elem['control_type'] and control_type.lower() == expected_elem['control_type'].lower()) or
                    (expected_elem['automation_id'] and automation_id == expected_elem['automation_id'])
                )
                
                if matches_structure:
                    # This element matches our expected path, continue to next level
                    children = element.GetChildren()
                    for child in children:
                        found = targeted_sidebar_search(child, depth + 1, path_index + 1)
                        if found:
                            return found
                else:
                    # This element doesn't match our expected path, skip it
                    excluded_count += 1
                    
                    # Still check children but with same path_index (might be alternative path)
                    children = element.GetChildren()
                    for child in children:
                        found = targeted_sidebar_search(child, depth + 1, path_index)
                        if found:
                            return found
                            
            except Exception:
                pass
            return None

        sidebar_element = targeted_sidebar_search(root_element, 0, 0)
        
        if sidebar_element:
            self.logger.debug(f"Targeted traversal found chat sidebar (excluded {excluded_count} paths)")
            self._extract_text_from_sidebar(sidebar_element, texts, sidebar_depth_limit)
            return True
        
        self.logger.debug(f"Targeted traversal failed to find chat sidebar (excluded {excluded_count} paths)")
        return False

    def _extract_text_targeted(self, root_element, texts, max_depth, sidebar_depth_limit):
        """Hybrid targeted traversal: fast path through all container types, fallback to broader container traversal."""
        from collections import deque
        
        # Exclusion criteria for non-chat paths
        exclusion_keywords = [
            'explorer', 'outline', 'timeline', 'scm', 'debug', 'extensions', 
            'settings', 'problems', 'output', 'terminal', 'search', 'replace',
            'git', 'source', 'test', 'run', 'debugger', 'breakpoint',
            'callstack', 'variables', 'watch', 'evaluate', 'console',
            'tasks', 'bookmarks', 'snippets', 'references', 'implementations',
            'workbench.view', 'workbench.panel.output', 'workbench.panel.problems',
            'workbench.view.explorer', 'workbench.view.search', 'workbench.view.scm',
            'workbench.view.debug', 'workbench.view.extensions', 'cursor tab',
            'intermediate d3d window'
        ]
        
        # Prefix exclusions (elements starting with these prefixes)
        exclusion_prefixes = [
            'bubble-'
        ]
        
        def should_exclude_path(element):
            """Check if a path should be excluded based on exclusion criteria."""
            try:
                automation_id = getattr(element, 'AutomationId', '').lower()
                name = getattr(element, 'Name', '').lower()
                
                # Check for exclusion keywords
                for keyword in exclusion_keywords:
                    if keyword in automation_id or keyword in name:
                        return True
                
                # Check for exclusion prefixes
                for prefix in exclusion_prefixes:
                    if automation_id.startswith(prefix) or name.startswith(prefix):
                        return True
                
                # Additional exclusion patterns
                if any(pattern in automation_id for pattern in [
                    'workbench.view.', 'workbench.panel.output', 'workbench.panel.problems',
                    'workbench.view.explorer', 'workbench.view.search', 'workbench.view.scm'
                ]):
                    return True
                    
                return False
            except:
                return False
        
        # --- Fast Path: Recursively search all container type children at each level ---
        def fast_path_sidebar_search(element, depth):
            if max_depth is not None and depth > max_depth:
                return None
            try:
                automation_id = getattr(element, 'AutomationId', '')
                if 'aichat' in automation_id.lower() or 'workbench.panel.aichat' in automation_id:
                    return element
                
                # Check exclusion criteria
                if should_exclude_path(element):
                    return None
                
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
        excluded_count = 0
        
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
                
                # Check exclusion criteria before traversing
                if should_exclude_path(current_element):
                    excluded_count += 1
                    continue
                
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
        self.logger.debug(f"Chat sidebar not found in hybrid traversal (processed {element_count} elements, excluded {excluded_count} paths)")
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
                window_element = WindowsWindowElement(window_id, title, hwnd, pid)
                windows.append(window_element)
                self.logger.debug(f"  Window {i+1}: {title} (PID: {pid})")
                
        except Exception as e:
            self.logger.error(f"Error getting Windows windows: {e}")
        
        return windows
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the sidebar path cache."""
        return get_sidebar_path_cache_stats()
    
    def clear_cache(self, window_handle: Optional[int] = None) -> None:
        """Clear the sidebar path cache for a specific window handle or all window handles."""
        clear_sidebar_path_cache(window_handle)
    
    def is_cached(self, window_handle: int) -> bool:
        """Check if a window handle has a cached sidebar path."""
        return window_handle in GLOBAL_SIDEBAR_PATH_CACHE


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