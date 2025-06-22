#!/usr/bin/env python3
"""
Debug script to test Windows window detection with both Win32 and UI Automation
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

# Recursive text extraction using Win32 APIs
def extract_text_recursive(hwnd, texts, visited, current_depth, max_depth=None):
    if max_depth is not None and current_depth > max_depth:
        return
    if hwnd in visited:
        return
    visited.add(hwnd)
    try:
        window_text = win32gui.GetWindowText(hwnd)
        if window_text:  # Remove length filter to see all text
            texts.append(f"[Win32] {window_text} (depth: {current_depth})")
    except Exception as e:
        pass
    # Recurse into child windows
    try:
        def enum_child_proc(child_hwnd, _):
            extract_text_recursive(child_hwnd, texts, visited, current_depth + 1, max_depth)
            return True
        win32gui.EnumChildWindows(hwnd, enum_child_proc, None)
    except Exception as e:
        pass

# Recursive text extraction using UI Automation
def extract_uia_text(element, texts, current_depth, max_depth=None):
    if max_depth is not None and current_depth > max_depth:
        return
    
    try:
        # Get various text properties - expanded list
        for prop_name in ['Name', 'AutomationId', 'ClassName', 'HelpText', 'LocalizedControlType', 'ControlType']:
            try:
                value = getattr(element, prop_name, None)
                if value and isinstance(value, str) and value.strip():
                    texts.append(f"[UIA] {value.strip()} (depth: {current_depth})")
            except:
                pass
        
        # Also try to get the element's text content directly
        try:
            if hasattr(element, 'GetText'):
                text_content = element.GetText()
                if text_content and isinstance(text_content, str) and text_content.strip():
                    texts.append(f"[UIA Text] {text_content.strip()} (depth: {current_depth})")
        except:
            pass
        
        # Get children and recurse
        try:
            children = element.GetChildren()
            for child in children:
                extract_uia_text(child, texts, current_depth + 1, max_depth)
        except:
            pass
            
    except Exception as e:
        pass

# TRACE PATH TO CHAT SIDEBAR
def trace_path_to_chat_sidebar(root_element, max_depth=None):
    """Trace the exact path to the chat sidebar element and show the element tree"""
    from collections import deque
    
    # Use a queue for BFS: (element, depth, path)
    queue = deque([(root_element, 0, [])])
    element_count = 0
    
    print("🔍 Tracing path to chat sidebar...")
    print("=" * 60)
    
    while queue and element_count < 10000:  # Safety limit
        current_element, depth, path = queue.popleft()
        
        if max_depth is not None and depth > max_depth:
            continue
            
        element_count += 1
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            
            # Debug: Log every 100th element to see what we're processing
            if element_count % 100 == 0:
                print(f"   Processing element #{element_count} at depth {depth}: {class_name}")
                if automation_id:
                    print(f"      AutomationId: {automation_id}")
                if name:
                    print(f"      Name: {name}")
            
            # Create current element info
            current_info = {
                'depth': depth,
                'automation_id': automation_id,
                'name': name,
                'class_name': class_name,
                'element_count': element_count
            }
            
            # Check if this is the chat sidebar
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            # Debug: Log potential matches
            if ('aichat' in automation_id.lower() or 'workbench' in automation_id.lower() or 
                'chat' in name.lower() or 'panel' in automation_id.lower()):
                print(f"   🔍 Potential match at element #{element_count} (depth {depth}):")
                print(f"      ClassName: {class_name}")
                print(f"      AutomationId: {automation_id}")
                print(f"      Name: {name}")
                print(f"      Is chat sidebar: {is_chat_sidebar}")
            
            if is_chat_sidebar:
                print(f"🎯 FOUND CHAT SIDEBAR at element #{element_count} (depth {depth})")
                print(f"   AutomationId: {automation_id}")
                print(f"   Name: {name}")
                print(f"   ClassName: {class_name}")
                print()
                print("📋 PATH TO CHAT SIDEBAR:")
                print("=" * 40)
                
                # Show the complete path
                for i, path_element in enumerate(path):
                    print(f"   {i+1}. Depth {path_element['depth']}: {path_element['class_name']}")
                    if path_element['automation_id']:
                        print(f"      AutomationId: {path_element['automation_id']}")
                    if path_element['name']:
                        print(f"      Name: {path_element['name']}")
                    print()
                
                print(f"   🎯 TARGET: {class_name}")
                if automation_id:
                    print(f"      AutomationId: {automation_id}")
                if name:
                    print(f"      Name: {name}")
                
                # Show statistics
                print()
                print("📊 STATISTICS:")
                print(f"   • Elements processed: {element_count}")
                print(f"   • Path length: {len(path)} elements")
                print(f"   • Target depth: {depth}")
                
                return path + [current_info]
            
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
    print(f"   • Total elements processed: {element_count}")
    return None

# BREADTH-FIRST SEARCH VERSION: Early chat sidebar detection (NO DEPTH LIMIT)
def extract_uia_text_bfs(root_element, texts, max_depth=None, found_chat_sidebar=False, element_count=0):
    """Breadth-first search implementation for UI Automation text extraction - NO DEPTH LIMIT"""
    # Remove depth limit for comprehensive search
    max_depth = None
    
    # Use a queue for BFS: (element, depth)
    queue = deque([(root_element, 0)])
    
    # Statistics tracking
    stats = {
        'total_elements': 0,
        'elements_before_sidebar': 0,
        'max_depth_reached': 0,
        'depth_counts': {},  # Count elements at each depth
        'sidebar_found': False,
        'agent_elements_found': 0,
        'start_time': time.time()
    }
    
    while queue and stats['total_elements'] < 50000:  # Increased safety limit
        element, current_depth = queue.popleft()
        
        if max_depth is not None and current_depth > max_depth:
            continue
            
        stats['total_elements'] += 1
        stats['max_depth_reached'] = max(stats['max_depth_reached'], current_depth)
        stats['depth_counts'][current_depth] = stats['depth_counts'].get(current_depth, 0) + 1
        
        try:
            # Check for chat sidebar identifiers early
            automation_id = getattr(element, 'AutomationId', '')
            name = getattr(element, 'Name', '')
            
            # Early detection of chat sidebar
            if not stats['sidebar_found']:
                if ('aichat' in automation_id.lower() or 
                    'workbench.panel.aichat' in automation_id or
                    'chat' in name.lower() and 'panel' in automation_id.lower()):
                    stats['sidebar_found'] = True
                    stats['elements_before_sidebar'] = stats['total_elements']
                    texts.append(f"[BFS] Found chat sidebar: {automation_id} (depth: {current_depth}) after {stats['total_elements']} elements")
            
            # If we found the chat sidebar, focus our search there
            if stats['sidebar_found']:
                # Get various text properties - focused on agent detection
                for prop_name in ['Name', 'AutomationId', 'HelpText']:
                    try:
                        value = getattr(element, prop_name, None)
                        if value and isinstance(value, str) and value.strip():
                            # Look specifically for agent-related content
                            if 'agent' in value.lower():
                                texts.append(f"[BFS AGENT] {value.strip()} (depth: {current_depth})")
                                stats['agent_elements_found'] += 1
                            else:
                                texts.append(f"[BFS] {value.strip()} (depth: {current_depth})")
                    except:
                        pass
                
                # Also try to get the element's text content directly
                try:
                    if hasattr(element, 'GetText'):
                        text_content = element.GetText()
                        if text_content and isinstance(text_content, str) and text_content.strip():
                            if 'agent' in text_content.lower():
                                texts.append(f"[BFS AGENT Text] {text_content.strip()} (depth: {current_depth})")
                                stats['agent_elements_found'] += 1
                            else:
                                texts.append(f"[BFS Text] {text_content.strip()} (depth: {current_depth})")
                except:
                    pass
            else:
                # Before finding chat sidebar, only log high-level elements
                if current_depth <= 3:
                    for prop_name in ['Name', 'AutomationId']:
                        try:
                            value = getattr(element, prop_name, None)
                            if value and isinstance(value, str) and value.strip():
                                texts.append(f"[BFS SEARCHING] {value.strip()} (depth: {current_depth})")
                        except:
                            pass
            
            # Add children to queue for next level (BFS)
            try:
                children = element.GetChildren()
                for child in children:
                    queue.append((child, current_depth + 1))
            except:
                pass
                
        except Exception as e:
            pass
    
    stats['end_time'] = time.time()
    stats['duration'] = stats['end_time'] - stats['start_time']
    
    return stats['sidebar_found'], stats

# OPTIMIZED VERSION: Early chat sidebar detection with element counting
def extract_uia_text_optimized(element, texts, current_depth, max_depth=None, found_chat_sidebar=False, element_count=0):
    if max_depth is not None and current_depth > max_depth:
        return found_chat_sidebar, element_count
    
    element_count += 1
    
    try:
        # Check for chat sidebar identifiers early
        automation_id = getattr(element, 'AutomationId', '')
        name = getattr(element, 'Name', '')
        
        # Early detection of chat sidebar
        if not found_chat_sidebar:
            if ('aichat' in automation_id.lower() or 
                'workbench.panel.aichat' in automation_id or
                'chat' in name.lower() and 'panel' in automation_id.lower()):
                texts.append(f"[OPTIMIZED] Found chat sidebar: {automation_id} (depth: {current_depth}) after {element_count} elements")
                found_chat_sidebar = True
        
        # If we found the chat sidebar, focus our search there
        if found_chat_sidebar:
            # Get various text properties - focused on agent detection
            for prop_name in ['Name', 'AutomationId', 'HelpText']:
                try:
                    value = getattr(element, prop_name, None)
                    if value and isinstance(value, str) and value.strip():
                        # Look specifically for agent-related content
                        if 'agent' in value.lower():
                            texts.append(f"[OPTIMIZED AGENT] {value.strip()} (depth: {current_depth})")
                        else:
                            texts.append(f"[OPTIMIZED] {value.strip()} (depth: {current_depth})")
                except:
                    pass
            
            # Also try to get the element's text content directly
            try:
                if hasattr(element, 'GetText'):
                    text_content = element.GetText()
                    if text_content and isinstance(text_content, str) and text_content.strip():
                        if 'agent' in text_content.lower():
                            texts.append(f"[OPTIMIZED AGENT Text] {text_content.strip()} (depth: {current_depth})")
                        else:
                            texts.append(f"[OPTIMIZED Text] {text_content.strip()} (depth: {current_depth})")
            except:
                pass
        else:
            # Before finding chat sidebar, only log high-level elements
            if current_depth <= 3:
                for prop_name in ['Name', 'AutomationId']:
                    try:
                        value = getattr(element, prop_name, None)
                        if value and isinstance(value, str) and value.strip():
                            texts.append(f"[SEARCHING] {value.strip()} (depth: {current_depth})")
                    except:
                        pass
        
        # Get children and recurse
        try:
            children = element.GetChildren()
            for child in children:
                found_chat_sidebar, element_count = extract_uia_text_optimized(child, texts, current_depth + 1, max_depth, found_chat_sidebar, element_count)
                if found_chat_sidebar and current_depth > 15:  # Early termination after finding agent
                    break
        except:
            pass
            
    except Exception as e:
        pass
    
    return found_chat_sidebar, element_count

def enum_windows_proc(hwnd, windows):
    if win32gui.IsWindowVisible(hwnd):
        window_text = win32gui.GetWindowText(hwnd)
        if window_text and "cursor" in window_text.lower():
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() == "cursor.exe":
                        windows.append((hwnd, window_text, pid))
                        print(f"Found Cursor window: '{window_text}' (PID: {pid}, HWND: {hwnd})")
                except Exception as e:
                    print(f"Skipping window '{window_text}' (PID: {pid}): {e}")
            except Exception as e:
                print(f"Error getting process info for window '{window_text}': {e}")
    return True

# TARGETED TRAVERSAL: Only traverse specific element types needed to reach sidebar
def extract_uia_text_targeted(root_element, texts, max_depth=None):
    """Traverse only specific element types needed to reach the chat sidebar."""
    from collections import deque
    
    # Use a queue for BFS: (element, depth)
    queue = deque([(root_element, 0)])
    element_count = 0
    
    print("🎯 TARGETED TRAVERSAL: Only specific element types")
    print("=" * 60)
    
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
            
            # Check if this is the chat sidebar
            is_chat_sidebar = ('aichat' in automation_id.lower() or 
                              'workbench.panel.aichat' in automation_id or
                              'chat' in name.lower() and 'panel' in automation_id.lower())
            
            if is_chat_sidebar:
                print(f"🎯 FOUND CHAT SIDEBAR at element #{element_count} (depth {depth})")
                print(f"   AutomationId: {automation_id}")
                print(f"   Name: {name}")
                print(f"   ClassName: {class_name}")
                print(f"   ControlType: {control_type}")
                print(f"   LocalizedType: {localized_type}")
                
                # Extract all text from sidebar and its descendants with depth limit of 15
                _extract_text_from_sidebar(current_element, texts, 15)
                return True
            
            # Only traverse children of specific element types that are needed for the path
            should_traverse = False
            
            # Always traverse these types (they're in the path to sidebar)
            if (class_name == 'Chrome_RenderWidgetHostHWND' or
                control_type.lower() in ['groupcontrol', 'windowcontrol', 'panecontrol', 'documentcontrol'] or
                localized_type.lower() in ['group', 'window', 'pane', 'document']):
                should_traverse = True
            
            # Also traverse elements with specific AutomationId patterns that might be in the path
            if automation_id and ('workbench' in automation_id.lower() or 
                                 'panel' in automation_id.lower() or
                                 'status' in automation_id.lower()):
                should_traverse = True
            
            # Debug: Log what we're traversing
            if should_traverse and element_count % 50 == 0:
                print(f"   Traversing element #{element_count} at depth {depth}: {class_name} [{control_type or localized_type}]")
                if automation_id:
                    print(f"      AutomationId: {automation_id}")
                if name:
                    print(f"      Name: {name}")
            
            # Add children to queue only if we should traverse this element type
            if should_traverse:
                try:
                    children = current_element.GetChildren()
                    for child in children:
                        queue.append((child, depth + 1))
                except:
                    pass
                    
        except Exception as e:
            pass
    
    print(f"❌ Chat sidebar not found in targeted traversal")
    print(f"   • Total elements processed: {element_count}")
    return False

def _extract_text_from_sidebar(current_element, texts, max_depth):
    """Extract all text from the sidebar and its descendants."""
    from collections import deque
    queue = deque([(current_element, 0)])
    
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

# GLOBAL SEARCH FOR CHAT SIDEBAR AND AGENT BUTTON

def trace_global_path_to_sidebar_and_agent(max_depth=40):
    import uiautomation as auto
    from collections import deque
    root = auto.GetRootControl()
    queue = deque([(root, 0, [])])
    element_count = 0
    found_sidebar = False
    found_agent_button = False
    sidebar_path = None
    agent_button_path = None
    print("\n🌐 GLOBAL SEARCH: Tracing path to chat sidebar and Agent button...")
    print("=" * 60)
    while queue and element_count < 50000 and (not found_sidebar or not found_agent_button):
        current_element, depth, path = queue.popleft()
        if depth > max_depth:
            continue
        element_count += 1
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            name = getattr(current_element, 'Name', '')
            class_name = getattr(current_element, 'ClassName', '')
            control_type = getattr(current_element, 'ControlTypeName', '') if hasattr(current_element, 'ControlTypeName') else ''
            localized_type = getattr(current_element, 'LocalizedControlType', '') if hasattr(current_element, 'LocalizedControlType') else ''
            # Path info
            current_info = {
                'depth': depth,
                'automation_id': automation_id,
                'name': name,
                'class_name': class_name,
                'control_type': control_type,
                'localized_type': localized_type,
                'element_count': element_count
            }
            # Check for chat sidebar
            is_chat_sidebar = (
                'aichat' in automation_id.lower() or
                'workbench.panel.aichat' in automation_id or
                ('chat' in name.lower() and 'panel' in automation_id.lower())
            )
            if is_chat_sidebar and not found_sidebar:
                found_sidebar = True
                sidebar_path = path + [current_info]
                print(f"\n🎯 FOUND CHAT SIDEBAR at element #{element_count} (depth {depth})")
                print(f"   AutomationId: {automation_id}")
                print(f"   Name: {name}")
                print(f"   ClassName: {class_name}")
                print(f"   ControlType: {control_type}")
                print(f"   LocalizedType: {localized_type}")
                print("\n📋 PATH TO CHAT SIDEBAR:")
                for i, e in enumerate(sidebar_path):
                    print(f"   {i+1}. Depth {e['depth']}: {e['class_name']} [{e['control_type'] or e['localized_type']}]")
                    if e['automation_id']:
                        print(f"      AutomationId: {e['automation_id']}")
                    if e['name']:
                        print(f"      Name: {e['name']}")
                print()
            # Check for Agent button
            is_agent_button = (
                'agent' in name.lower() and
                (control_type.lower() == 'button' or localized_type.lower() == 'button')
            )
            if is_agent_button and not found_agent_button:
                found_agent_button = True
                agent_button_path = path + [current_info]
                print(f"\n🎯 FOUND AGENT BUTTON at element #{element_count} (depth {depth})")
                print(f"   Name: {name}")
                print(f"   ClassName: {class_name}")
                print(f"   ControlType: {control_type}")
                print(f"   LocalizedType: {localized_type}")
                print(f"   AutomationId: {automation_id}")
                print("\n📋 PATH TO AGENT BUTTON:")
                for i, e in enumerate(agent_button_path):
                    print(f"   {i+1}. Depth {e['depth']}: {e['class_name']} [{e['control_type'] or e['localized_type']}]")
                    if e['automation_id']:
                        print(f"      AutomationId: {e['automation_id']}")
                    if e['name']:
                        print(f"      Name: {e['name']}")
                print()
            # Add children
            current_path = path + [current_info]
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1, current_path))
            except:
                pass
        except Exception as e:
            pass
    if not found_sidebar:
        print("❌ Chat sidebar not found in the global UI tree")
    if not found_agent_button:
        print("❌ Agent button not found in the global UI tree")
    print(f"   • Total elements processed: {element_count}")

def find_sidebar_element(root_element):
    """Find the chat sidebar element by its AutomationId."""
    from collections import deque
    
    queue = deque([root_element])
    
    while queue:
        current_element = queue.popleft()
        
        try:
            automation_id = getattr(current_element, 'AutomationId', '')
            
            # Check if this is the chat sidebar
            if ('aichat' in automation_id.lower() or 
                'workbench.panel.aichat' in automation_id):
                return current_element
            
            # Add children to queue
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append(child)
            except:
                pass
                
        except Exception as e:
            pass
    
    return None

def trace_path_to_connection_failed_from_sidebar(sidebar_element, max_depth=None):
    """Trace the path from chat sidebar to elements containing 'Connection failed'."""
    from collections import deque
    
    print("🔍 Tracing path from chat sidebar to 'Connection failed'...")
    print("=" * 60)
    
    # Use a queue for BFS: (element, depth, path)
    queue = deque([(sidebar_element, 0, [])])
    element_count = 0
    connection_failed_elements = []
    
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
            
            # Check if this element contains "Connection failed"
            contains_connection_failed = False
            connection_failed_text = ""
            
            # Check various text properties
            for prop_name in ['Name', 'AutomationId', 'HelpText']:
                try:
                    value = getattr(current_element, prop_name, None)
                    if value and isinstance(value, str) and 'connection failed' in value.lower():
                        contains_connection_failed = True
                        connection_failed_text = value
                        break
                except:
                    pass
            
            # Also check direct text content
            if not contains_connection_failed:
                try:
                    if hasattr(current_element, 'GetText'):
                        text_content = current_element.GetText()
                        if text_content and isinstance(text_content, str) and 'connection failed' in text_content.lower():
                            contains_connection_failed = True
                            connection_failed_text = text_content
                except:
                    pass
            
            if contains_connection_failed:
                print(f"🎯 FOUND 'Connection failed' at element #{element_count} (depth {depth})")
                print(f"   Text: {connection_failed_text}")
                print(f"   ClassName: {class_name}")
                print(f"   ControlType: {control_type}")
                print(f"   LocalizedType: {localized_type}")
                print(f"   AutomationId: {automation_id}")
                
                # Store the path to this element
                current_info = {
                    'depth': depth,
                    'class_name': class_name,
                    'control_type': control_type,
                    'localized_type': localized_type,
                    'automation_id': automation_id,
                    'name': name,
                    'text': connection_failed_text
                }
                
                connection_failed_elements.append({
                    'element_count': element_count,
                    'depth': depth,
                    'path': path + [current_info],
                    'text': connection_failed_text
                })
                
                print(f"\n📋 PATH TO 'Connection failed':")
                print("=" * 40)
                for i, e in enumerate(path + [current_info]):
                    print(f"   {i+1}. Depth {e['depth']}: {e['class_name']} [{e['control_type'] or e['localized_type']}]")
                    if e['automation_id']:
                        print(f"      AutomationId: {e['automation_id']}")
                    if e['name']:
                        print(f"      Name: {e['name']}")
                print()
            
            # Add current element to path
            current_info = {
                'depth': depth,
                'class_name': class_name,
                'control_type': control_type,
                'localized_type': localized_type,
                'automation_id': automation_id,
                'name': name
            }
            
            # Add children to queue for next level (BFS)
            try:
                children = current_element.GetChildren()
                for child in children:
                    queue.append((child, depth + 1, path + [current_info]))
            except:
                pass
                
        except Exception as e:
            pass
    
    print(f"📊 STATISTICS:")
    print(f"   • Total elements processed: {element_count}")
    print(f"   • 'Connection failed' elements found: {len(connection_failed_elements)}")
    
    if connection_failed_elements:
        print(f"   • Element types traversed to reach 'Connection failed':")
        element_types = set()
        for elem in connection_failed_elements:
            for path_elem in elem['path']:
                elem_type = path_elem['control_type'] or path_elem['localized_type'] or path_elem['class_name']
                if elem_type:
                    element_types.add(elem_type)
        
        for elem_type in sorted(element_types):
            print(f"      - {elem_type}")
    
    return connection_failed_elements

def main():
    print("🔍 Testing optimized traversal strategies...")
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
        
        # Test 1: Original method (for comparison)
        print("\n  🧪 Test 1: Original traversal method")
        start_time = time.time()
        texts_original = []
        visited = set()
        extract_text_recursive(hwnd, texts_original, visited, 0, 30)
        
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                extract_uia_text(uia_element, texts_original, 0, 30)
        except Exception as e:
            print(f"    UIA Error: {e}")
        
        original_time = time.time() - start_time
        agent_found_original = any("agent" in t.lower() for t in texts_original)
        print(f"    Time: {original_time:.3f}s, Elements: {len(texts_original)}, Agent found: {agent_found_original}")
        
        # Test 2: Optimized method
        print("\n  🚀 Test 2: Optimized traversal method")
        start_time = time.time()
        texts_optimized = []
        total_elements_processed = 0
        
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                found_chat_sidebar, total_elements_processed = extract_uia_text_optimized(uia_element, texts_optimized, 0, 30, False, 0)
        except Exception as e:
            print(f"    UIA Error: {e}")
        
        optimized_time = time.time() - start_time
        agent_found_optimized = any("agent" in t.lower() for t in texts_optimized)
        print(f"    Time: {optimized_time:.3f}s, Elements: {len(texts_optimized)}, Total processed: {total_elements_processed}, Agent found: {agent_found_optimized}")
        
        # Test 3: Breadth-First Search method
        print("\n  🔄 Test 3: Breadth-First Search method")
        start_time = time.time()
        texts_bfs = []
        bfs_stats = {}
        
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                found_chat_sidebar_bfs, bfs_stats = extract_uia_text_bfs(uia_element, texts_bfs, None, False, 0)
        except Exception as e:
            print(f"    UIA Error: {e}")
        
        bfs_time = time.time() - start_time
        agent_found_bfs = any("agent" in t.lower() for t in texts_bfs)
        print(f"    Time: {bfs_time:.3f}s, Elements: {len(texts_bfs)}, Total processed: {bfs_stats.get('total_elements', 0)}, Agent found: {agent_found_bfs}")
        
        # Test 4: Trace path to chat sidebar
        print("\n  🛤️  Test 4: Trace path to chat sidebar")
        start_time = time.time()
        
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                path_to_sidebar = trace_path_to_chat_sidebar(uia_element, None)
        except Exception as e:
            print(f"    UIA Error: {e}")
        
        trace_time = time.time() - start_time
        print(f"    Time: {trace_time:.3f}s")
        
        # Detailed BFS Statistics
        if bfs_stats:
            print(f"    📊 BFS Statistics:")
            print(f"      • Elements before sidebar: {bfs_stats.get('elements_before_sidebar', 0)}")
            print(f"      • Max depth reached: {bfs_stats.get('max_depth_reached', 0)}")
            print(f"      • Agent elements found: {bfs_stats.get('agent_elements_found', 0)}")
            print(f"      • BFS duration: {bfs_stats.get('duration', 0):.3f}s")
            
            # Show depth distribution (top 10 depths)
            depth_counts = bfs_stats.get('depth_counts', {})
            if depth_counts:
                print(f"      • Depth distribution (top 10):")
                sorted_depths = sorted(depth_counts.items(), key=lambda x: x[1], reverse=True)[:10]
                for depth, count in sorted_depths:
                    print(f"        Depth {depth}: {count} elements")
        
        # Performance comparison
        if original_time > 0:
            speedup_optimized = original_time / optimized_time
            speedup_bfs = original_time / bfs_time
            print(f"    🎯 Speedup (Optimized): {speedup_optimized:.2f}x faster")
            print(f"    🎯 Speedup (BFS): {speedup_bfs:.2f}x faster")
        
        # Show key findings from all methods
        print("\n  📋 Key findings:")
        
        # Original method findings
        agent_elements_original = [t for t in texts_original if "agent" in t.lower()]
        print(f"    Original method: {len(agent_elements_original)} agent elements found")
        
        # Optimized method findings
        chat_sidebar_found_optimized = False
        agent_elements_optimized = []
        
        for t in texts_optimized:
            if "Found chat sidebar" in t:
                print(f"    Optimized: {t}")
                chat_sidebar_found_optimized = True
            elif "OPTIMIZED AGENT" in t:
                agent_elements_optimized.append(t)
        
        if agent_elements_optimized:
            print(f"    Optimized: {len(agent_elements_optimized)} agent elements found")
        else:
            print("    Optimized: ❌ No agent elements found")
        
        # BFS method findings
        chat_sidebar_found_bfs = False
        agent_elements_bfs = []
        
        for t in texts_bfs:
            if "Found chat sidebar" in t:
                print(f"    BFS: {t}")
                chat_sidebar_found_bfs = True
            elif "BFS AGENT" in t:
                agent_elements_bfs.append(t)
        
        if agent_elements_bfs:
            print(f"    BFS: {len(agent_elements_bfs)} agent elements found")
        else:
            print("    BFS: ❌ No agent elements found")
        
        # Test 5: Global search for chat sidebar and Agent button
        if i == 0:  # Only run once for the first window
            trace_global_path_to_sidebar_and_agent()
        
        # Test 6: Targeted traversal (only specific element types)
        print("\n  🎯 Test 6: Targeted traversal (only specific element types)")
        start_time = time.time()
        texts_targeted = []
        sidebar_found = False
        sidebar_element = None
        
        try:
            uia_element = auto.ControlFromHandle(hwnd)
            if uia_element:
                sidebar_found = extract_uia_text_targeted(uia_element, texts_targeted, 30)
                # If we found the sidebar, trace the path to "Connection failed"
                if sidebar_found:
                    # Find the sidebar element again for tracing
                    sidebar_element = find_sidebar_element(uia_element)
                    if sidebar_element:
                        print("\n  🔍 Test 7: Trace path from sidebar to 'Connection failed'")
                        trace_path_to_connection_failed_from_sidebar(sidebar_element, 20)
        except Exception as e:
            print(f"    UIA Error: {e}")
        
        targeted_time = time.time() - start_time
        connection_failed_found = any("connection failed" in t.lower() for t in texts_targeted)
        if connection_failed_found:
            print(f"    FOUND 'Connection failed' in window!")
            for t in texts_targeted:
                if "connection failed" in t.lower():
                    print(f"      → {t}")
        else:
            print(f"    'Connection failed' not found in window.")
        print(f"    Time: {targeted_time:.3f}s, Elements: {len(texts_targeted)}")
        
        # Performance comparison
        if original_time > 0:
            speedup_targeted = original_time / targeted_time
            print(f"    🎯 Speedup (Targeted): {speedup_targeted:.2f}x faster")
        
        print()

if __name__ == "__main__":
    main() 