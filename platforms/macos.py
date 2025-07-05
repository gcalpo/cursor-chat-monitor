"""
macOS-specific implementation using PyObjC and Accessibility APIs
"""
import sys
import subprocess
import logging
from typing import List, Dict, Any, Optional
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
        kAXIdentifierAttribute,
        AXIsProcessTrusted
    )
    ACCESSIBILITY_AVAILABLE = True
except ImportError as e:
    ACCESSIBILITY_AVAILABLE = False

# Global cache for chat sidebar elements on a per-window basis
# Key: window_id, Value: ax_element
MACOS_CHAT_SIDEBAR_CACHE = {}

def get_cached_chat_sidebar(window_id):
    """Get cached chat sidebar element for a window ID if it exists and is still valid."""
    if window_id in MACOS_CHAT_SIDEBAR_CACHE:
        cached_data = MACOS_CHAT_SIDEBAR_CACHE[window_id]
        sidebar_element = cached_data.get('element')
        expected_class_list = cached_data.get('class_list')
        expected_depth = cached_data.get('depth')
        
        # Verify the element is still valid using stable attributes
        try:
            error_code, role = AXUIElementCopyAttributeValue(sidebar_element, kAXRoleAttribute, None)
            if error_code == kAXErrorSuccess and role == 'AXGroup':
                # Check if class list matches (more stable than ChromeAXNodeId)
                error_code, current_class_list = AXUIElementCopyAttributeValue(sidebar_element, 'AXDOMClassList', None)
                if (error_code == kAXErrorSuccess and 
                    current_class_list == expected_class_list):
                    logging.getLogger(__name__).debug(f"Using cached chat sidebar element for window {window_id} (classes: {current_class_list})")
                    return sidebar_element
                else:
                    # If class list doesn't match, try basic role validation
                    logging.getLogger(__name__).debug(f"Class list changed, but element still valid as AXGroup for window {window_id}")
                    return sidebar_element
        except Exception:
            pass
        # Element is no longer valid, remove from cache
        logging.getLogger(__name__).debug(f"Cached chat sidebar element for window {window_id} is no longer valid, removing from cache")
        del MACOS_CHAT_SIDEBAR_CACHE[window_id]
    return None

def cache_chat_sidebar(window_id, sidebar_element, depth=None):
    """Cache the chat sidebar element and its stable attributes for a window ID."""
    # Get stable attributes for identification
    class_list = None
    try:
        error_code, class_list = AXUIElementCopyAttributeValue(sidebar_element, 'AXDOMClassList', None)
        if error_code != kAXErrorSuccess:
            class_list = None
    except Exception:
        class_list = None
    
    MACOS_CHAT_SIDEBAR_CACHE[window_id] = {
        'element': sidebar_element,
        'class_list': class_list,
        'depth': depth
    }
    logging.getLogger(__name__).debug(f"Cached chat sidebar element for window {window_id} (classes: {class_list}, depth: {depth})")

def clear_chat_sidebar_cache(window_id=None):
    """Clear the chat sidebar cache for a specific window ID or all windows."""
    if window_id is not None:
        if window_id in MACOS_CHAT_SIDEBAR_CACHE:
            del MACOS_CHAT_SIDEBAR_CACHE[window_id]
            logging.getLogger(__name__).debug(f"Cleared cached chat sidebar element for window {window_id}")
    else:
        MACOS_CHAT_SIDEBAR_CACHE.clear()
        logging.getLogger(__name__).debug("Cleared all cached chat sidebar elements")

class MacOSWindowElement(WindowElement):
    """macOS-specific window element using Accessibility APIs"""
    
    def __init__(self, window_id: str, title: str, ax_element):
        super().__init__(window_id, title)
        self.ax_element = ax_element
        self.logger = logging.getLogger(__name__)
    
    def get_text_content(self, max_depth: int = 50, sidebar_depth_limit: int = 20) -> List[str]:
        """Extract all text content from this macOS window element with chat sidebar targeting"""
        texts = []
        
        # Check for cached chat sidebar element first
        cached_sidebar = get_cached_chat_sidebar(self.window_id)
        if cached_sidebar is not None:
            self.logger.debug(f"Using cached chat sidebar element for window {self.get_title()}")
            self._extract_text_from_chat_sidebar(cached_sidebar, texts, sidebar_depth_limit)
            return texts
        
        # No cached element found, need to find the chat sidebar
        chat_sidebar = self._find_and_cache_chat_sidebar(self.ax_element, max_depth)
        if chat_sidebar:
            # Verify we found a valid chat sidebar by checking for expected content
            if self._verify_chat_sidebar_content(chat_sidebar):
                self._extract_text_from_chat_sidebar(chat_sidebar, texts, sidebar_depth_limit)
            else:
                self.logger.debug("Found element but doesn't appear to be chat sidebar, trying fallback")
                # Clear invalid cache and try fallback
                clear_chat_sidebar_cache(self.window_id)
                chat_sidebar = self._find_chat_sidebar_fallback(self.ax_element, max_depth)
                if chat_sidebar:
                    self._extract_text_from_chat_sidebar(chat_sidebar, texts, sidebar_depth_limit)
                else:
                    self.logger.debug("Could not find chat sidebar, falling back to full window traversal")
                    texts = self._get_all_text_elements(self.ax_element, max_depth, 0, sidebar_depth_limit)
        else:
            self.logger.debug("Could not find chat sidebar with toolbar method, trying fallback")
            # Try fallback method
            chat_sidebar = self._find_chat_sidebar_fallback(self.ax_element, max_depth)
            if chat_sidebar:
                self._extract_text_from_chat_sidebar(chat_sidebar, texts, sidebar_depth_limit)
            else:
                self.logger.debug("Could not find chat sidebar, falling back to full window traversal")
                texts = self._get_all_text_elements(self.ax_element, max_depth, 0, sidebar_depth_limit)
        
        return texts
    
    def _find_and_cache_chat_sidebar(self, root_element, max_depth=50):
        """Find the chat sidebar element using 'Chat actions' toolbar → AXGroup parent strategy."""
        from collections import deque
        
        # Use a queue for BFS with path tracking: (element, depth, path)
        queue = deque([(root_element, 0, [root_element])])
        element_count = 0
        
        self.logger.debug("Searching for chat sidebar using 'Chat actions' toolbar strategy")
        
        while queue and element_count < 2000:  # Limit for performance
            current_element, depth, path = queue.popleft()
            
            if max_depth is not None and depth > max_depth:
                continue
                
            element_count += 1
            
            try:
                # Get element attributes
                error_code, role = AXUIElementCopyAttributeValue(current_element, kAXRoleAttribute, None)
                role = role if error_code == kAXErrorSuccess else ''
                
                error_code, description = AXUIElementCopyAttributeValue(current_element, kAXDescriptionAttribute, None)
                description = description if error_code == kAXErrorSuccess else ''
                
                # Look for "Chat actions" toolbar (our reliable anchor point)
                if role == 'AXToolbar' and description == 'Chat actions':
                    self.logger.debug(f"Found 'Chat actions' toolbar at depth {depth}")
                    
                    # Navigate up the path to find the nearest AXGroup parent
                    chat_sidebar, sidebar_depth = self._find_nearest_axgroup_parent(path)
                    if chat_sidebar:
                        self.logger.debug(f"Found chat sidebar at depth {sidebar_depth}")
                        
                        # Cache the chat sidebar element for future use
                        cache_chat_sidebar(self.window_id, chat_sidebar, sidebar_depth)
                        return chat_sidebar
                    else:
                        self.logger.debug("Found toolbar but no AXGroup parent found")
                
                # Add children to queue for next level (BFS)
                error_code, children = AXUIElementCopyAttributeValue(current_element, kAXChildrenAttribute, None)
                if error_code == kAXErrorSuccess and children:
                    for child in children:
                        child_path = path + [child]
                        queue.append((child, depth + 1, child_path))
                        
            except Exception as e:
                self.logger.debug(f"Error processing element at depth {depth}: {e}")
        
        self.logger.debug(f"No chat sidebar found after processing {element_count} elements")
        return None
    
    def _find_nearest_axgroup_parent(self, path):
        """Navigate up the path to find the nearest AXGroup parent."""
        # Start from the toolbar and go backwards through parents
        for i in range(len(path) - 2, -1, -1):  # Skip the toolbar itself (last element)
            parent_element = path[i]
            
            try:
                error_code, role = AXUIElementCopyAttributeValue(parent_element, kAXRoleAttribute, None)
                if error_code == kAXErrorSuccess and role == 'AXGroup':
                    self.logger.debug(f"Found AXGroup parent at depth {i}")
                    return parent_element, i
            except Exception:
                continue
        
        return None, None
    

    
    def _verify_chat_sidebar_content(self, sidebar_element):
        """Verify that the found element is actually a chat sidebar by checking for expected content."""
        try:
            # Look for chat-related elements within the sidebar (limited depth search)
            from collections import deque
            
            queue = deque([(sidebar_element, 0)])
            chat_indicators = 0
            elements_checked = 0
            
            while queue and elements_checked < 100:  # Limited search for performance
                current_element, depth = queue.popleft()
                
                if depth > 10:  # Shallow search only
                    continue
                
                elements_checked += 1
                
                try:
                    # Check for chat-related text content
                    for attr in [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute]:
                        error_code, value = AXUIElementCopyAttributeValue(current_element, attr, None)
                        if error_code == kAXErrorSuccess and value and isinstance(value, str):
                            value_lower = value.lower()
                            if any(indicator in value_lower for indicator in 
                                   ['chat', 'message', 'conversation', 'agent', 'assistant', 'model']):
                                chat_indicators += 1
                                if chat_indicators >= 2:  # Found enough indicators
                                    return True
                    
                    # Add children for next level
                    error_code, children = AXUIElementCopyAttributeValue(current_element, kAXChildrenAttribute, None)
                    if error_code == kAXErrorSuccess and children:
                        for child in children:
                            queue.append((child, depth + 1))
                
                except Exception:
                    continue
            
            # If we found some chat indicators, consider it valid
            return chat_indicators > 0
            
        except Exception as e:
            self.logger.debug(f"Error verifying chat sidebar content: {e}")
            return True  # If we can't verify, assume it's valid
    
    def _find_chat_sidebar_fallback(self, root_element, max_depth=50):
        """Fallback method to find chat sidebar using broader search patterns."""
        from collections import deque
        
        self.logger.debug("Using fallback chat sidebar detection method")
        
        queue = deque([(root_element, 0)])
        element_count = 0
        
        while queue and element_count < 2000:
            current_element, depth = queue.popleft()
            
            if max_depth is not None and depth > max_depth:
                continue
                
            element_count += 1
            
            try:
                # Get element attributes
                error_code, role = AXUIElementCopyAttributeValue(current_element, kAXRoleAttribute, None)
                role = role if error_code == kAXErrorSuccess else ''
                
                error_code, identifier = AXUIElementCopyAttributeValue(current_element, kAXIdentifierAttribute, None)
                identifier = identifier if error_code == kAXErrorSuccess else ''
                
                error_code, title = AXUIElementCopyAttributeValue(current_element, kAXTitleAttribute, None)
                title = title if error_code == kAXErrorSuccess else ''
                
                error_code, description = AXUIElementCopyAttributeValue(current_element, kAXDescriptionAttribute, None)
                description = description if error_code == kAXErrorSuccess else ''
                
                # Check if this looks like a chat sidebar using broader patterns
                is_chat_sidebar = (
                    role == 'AXGroup' and (
                        ('chat' in identifier.lower() if identifier else False) or
                        ('aichat' in identifier.lower() if identifier else False) or
                        ('workbench.panel.aichat' in identifier if identifier else False) or
                        ('chat' in title.lower() and 'panel' in identifier.lower() if title and identifier else False) or
                        ('ai chat' in title.lower() if title else False) or
                        ('chat' in description.lower() and 'panel' in description.lower() if description else False)
                    )
                )
                
                if is_chat_sidebar:
                    self.logger.debug(f"Found chat sidebar element with fallback method (identifier: {identifier})")
                    # Cache the chat sidebar element for future use
                    cache_chat_sidebar(self.window_id, current_element, depth)
                    return current_element
                
                # Add children to queue for next level (BFS)
                error_code, children = AXUIElementCopyAttributeValue(current_element, kAXChildrenAttribute, None)
                if error_code == kAXErrorSuccess and children:
                    for child in children:
                        queue.append((child, depth + 1))
                        
            except Exception as e:
                self.logger.debug(f"Error in fallback search at depth {depth}: {e}")
        
        self.logger.debug(f"No chat sidebar found with fallback method after processing {element_count} elements")
        return None
    
    def _extract_text_from_chat_sidebar(self, sidebar_element, texts, max_depth):
        """Extract all text from the chat sidebar and its descendants with depth limit."""
        from collections import deque
        
        seen_texts = set()  # Track seen texts to avoid duplicates
        queue = deque([(sidebar_element, 0)])
        elements_processed = 0
        
        self.logger.debug(f"Extracting text from chat sidebar with max_depth={max_depth}")
        
        while queue and elements_processed < 1000:  # Limit processing for performance
            current_element, depth = queue.popleft()
            elements_processed += 1
            
            if max_depth is not None and depth > max_depth:
                continue
            
            try:
                # Extract text from various attributes with priority order
                text_found = False
                
                # Priority 1: AXValue (most likely to contain actual chat content)
                error_code, value = AXUIElementCopyAttributeValue(current_element, kAXValueAttribute, None)
                if error_code == kAXErrorSuccess and value and isinstance(value, str):
                    value = value.strip()
                    if value and len(value) > 2 and value not in seen_texts:
                        texts.append(value)
                        seen_texts.add(value)
                        text_found = True
                
                # Priority 2: AXTitle (for buttons, labels, etc.)
                error_code, title = AXUIElementCopyAttributeValue(current_element, kAXTitleAttribute, None)
                if error_code == kAXErrorSuccess and title and isinstance(title, str):
                    title = title.strip()
                    if title and len(title) > 2 and title not in seen_texts:
                        texts.append(title)
                        seen_texts.add(title)
                        text_found = True
                
                # Priority 3: AXDescription (for accessibility descriptions)
                error_code, desc = AXUIElementCopyAttributeValue(current_element, kAXDescriptionAttribute, None)
                if error_code == kAXErrorSuccess and desc and isinstance(desc, str):
                    desc = desc.strip()
                    if desc and len(desc) > 2 and desc not in seen_texts:
                        texts.append(desc)
                        seen_texts.add(desc)
                        text_found = True
                
                # Add children to queue for next level
                error_code, children = AXUIElementCopyAttributeValue(current_element, kAXChildrenAttribute, None)
                if error_code == kAXErrorSuccess and children:
                    for child in children:
                        queue.append((child, depth + 1))
                        
            except Exception as e:
                self.logger.debug(f"Error extracting text from chat sidebar at depth {depth}: {e}")
        
        self.logger.debug(f"Extracted {len(texts)} text elements from chat sidebar (processed {elements_processed} elements)")
    
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
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the chat sidebar cache."""
        cache_details = {}
        for window_id, cached_data in MACOS_CHAT_SIDEBAR_CACHE.items():
            cache_details[window_id] = {
                'class_list': cached_data.get('class_list'),
                'depth': cached_data.get('depth'),
                'has_element': cached_data.get('element') is not None
            }
        
        return {
            'cached_windows': list(MACOS_CHAT_SIDEBAR_CACHE.keys()),
            'cache_size': len(MACOS_CHAT_SIDEBAR_CACHE),
            'cache_details': cache_details
        }
    
    def clear_cache(self, window_id: Optional[str] = None) -> None:
        """Clear the chat sidebar cache for a specific window ID or all windows."""
        clear_chat_sidebar_cache(window_id)
    
    def is_cached(self, window_id: str) -> bool:
        """Check if a window ID has a cached chat sidebar element."""
        return window_id in MACOS_CHAT_SIDEBAR_CACHE


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