#!/usr/bin/env python3
"""
Debug script to test the optimized hybrid Windows window traversal
"""
import win32gui
import win32process
import sys
import psutil
import uiautomation as auto
import logging
import time
from collections import deque

# Disable verbose UI Automation logging
auto.OPERATION_WAIT_TIME = 0
logging.getLogger('uiautomation').setLevel(logging.ERROR)

def enum_windows_proc(hwnd, windows):
    """Find Cursor windows"""
    if win32gui.IsWindowVisible(hwnd):
        window_text = win32gui.GetWindowText(hwnd)
        if window_text and "cursor" in window_text.lower():
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

def trace_path_to_aichat_url(root_element, max_depth=30):
    """Trace the path to the aichat element and output it like a URL."""
    from collections import deque
    
    # Use a queue for BFS: (element, depth, path)
    queue = deque([(root_element, 0, [])])
    element_count = 0
    
    while queue and element_count < 10000:  # Safety limit
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
            
            if is_chat_sidebar:
                # Build the URL-like path
                url_parts = []
                for path_element in path + [current_info]:
                    # Use the most descriptive identifier available
                    identifier = (path_element['automation_id'] or 
                                path_element['name'] or 
                                path_element['class_name'] or 
                                path_element['control_type'] or 
                                path_element['localized_type'] or 
                                'unknown')
                    
                    # Clean up the identifier for URL format
                    identifier = identifier.replace(' ', '_').replace('.', '_').replace('-', '_')
                    url_parts.append(identifier)
                
                # Construct the URL
                url_path = '/'.join(url_parts)
                print(f"🌐 URL Path to aichat: {url_path}")
                print(f"   Depth: {depth}")
                print(f"   Elements processed: {element_count}")
                
                # Also show the detailed path
                print(f"📋 Detailed path:")
                for i, path_element in enumerate(path + [current_info]):
                    print(f"   {i+1}. {path_element['class_name'] or 'unnamed'}")
                    if path_element['automation_id']:
                        print(f"      AutomationId: {path_element['automation_id']}")
                    if path_element['name']:
                        print(f"      Name: {path_element['name']}")
                    if path_element['control_type']:
                        print(f"      Type: {path_element['control_type']}")
                
                return url_path
            
            # Add current element to path
            current_path = path + [current_info]
            
            # Add children to queue for next level (BFS)
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1, current_path))
            except:
                pass
                
        except Exception as e:
            pass
    
    print("❌ Chat sidebar not found in the element tree")
    return None

def extract_uia_text_hybrid(root_element, texts, max_depth=30, sidebar_depth_limit=20):
    """Optimized hybrid traversal: fast path through all container types, fallback to broader container traversal."""
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
        print(f"[FAST PATH] Found chat sidebar with AutomationId: {getattr(sidebar_element, 'AutomationId', '')}")
        _extract_text_from_sidebar(sidebar_element, texts, sidebar_depth_limit)
        return True

    # --- Fallback: Broader container traversal ---
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
                print(f"[FALLBACK] Found chat sidebar with AutomationId: {automation_id}")
                _extract_text_from_sidebar(current_element, texts, sidebar_depth_limit)
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
    print(f"Chat sidebar not found in targeted traversal (processed {element_count} elements)")
    return False

def _extract_text_from_sidebar(sidebar_element, texts, max_depth):
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

def main():
    print("🔍 Testing optimized hybrid traversal strategy...")
    print("=" * 60)
    
    found_windows = []
    win32gui.EnumWindows(enum_windows_proc, found_windows)
    
    print(f"\n📊 Summary: Found {len(found_windows)} Cursor windows")
    print("=" * 60)
    
    for i, (hwnd, title, pid) in enumerate(found_windows):
        print(f"Window {i+1}:")
        print(f"  Title: {title}")
        print(f"  PID: {pid}")
        print(f"  HWND: {hwnd}")
        
        # Test: Optimized hybrid traversal method
        print("\n  🚀 Test: Optimized hybrid traversal method")
        start_time = time.time()
        texts = []
        
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                sidebar_found = extract_uia_text_hybrid(uia_element, texts, 30, 20)
                
                # Trace the URL path to aichat
                print("\n  🌐 Tracing URL path to aichat...")
                trace_path_to_aichat_url(uia_element, 30)
                
        except Exception as e:
            print(f"    UIA Error: {e}")
        
        traversal_time = time.time() - start_time
        connection_failed_found = any("connection failed" in t.lower() for t in texts)
        
        print(f"    Time: {traversal_time:.3f}s, Elements: {len(texts)}")
        
        if connection_failed_found:
            print(f"    ✅ FOUND 'Connection failed' in window!")
            for t in texts:
                if "connection failed" in t.lower():
                    print(f"      → {t}")
        else:
            print(f"    ❌ 'Connection failed' not found in window.")
        
        print()

if __name__ == "__main__":
    main() 